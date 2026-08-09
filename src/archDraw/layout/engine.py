from archDraw.core.elements import ArchElement, Node, Container
from archDraw.render.text import TextRenderer

def should_stretch(child, parent):
    return isinstance(child, Container)

class LayoutEngine:
    """Handles all mathematical bounding-box layout operations."""
    
    @staticmethod
    def calculate_bounds(element: ArchElement, renderer=None, chosen_idx: int = 0, connections=None, element_map=None) -> list[tuple[float, float]]:
        """Bottom-up layout calculation. Returns [wrapped_size, unwrapped_size]."""
        if renderer is None:
            from archDraw.render.svg import SVGRenderer
            renderer = SVGRenderer()

        if connections and element_map is None:
            element_map = {}
            def map_elements(el):
                if hasattr(el, "alias") and el.alias:
                    element_map[el.alias] = el
                element_map[el.name] = el
                for child in el.children:
                    map_elements(child)
            map_elements(element)

        if isinstance(element, Node):
            sizes = renderer.get_node_size(element)
            idx = min(chosen_idx, len(sizes) - 1)
            element.width, element.height = sizes[idx]
            return sizes

        if isinstance(element, Container):
            child_sizes_list = {}
            for child in element.children:
                child_sizes_list[child] = LayoutEngine.calculate_bounds(child, renderer, chosen_idx, connections, element_map)

            has_icon = any(isinstance(child, Node) and ("::" in child.node_type or child.node_type.startswith("icon::")) for child in element.children)
            layout_mode = 'horizontal' if has_icon else element.layout

            # Container name wrapping options
            title_options = TextRenderer.get_wrapping_options(element.name)
            wrapped_title = title_options[-1]
            unwrapped_title = title_options[0]

            bl, br, bt_base, bb = renderer.get_container_borders(element)

            # Calculate dynamic gaps based on connections crossing between child boundaries
            gaps = [element.gap] * (len(element.children) - 1)
            if connections and element_map and len(element.children) > 1:
                def get_descendants(el):
                    desc = {el}
                    for child in el.children:
                        desc.update(get_descendants(child))
                    return desc
                
                desc_sets = [get_descendants(child) for child in element.children]
                for j in range(len(element.children) - 1):
                    left_desc = set()
                    for k in range(j + 1):
                        left_desc.update(desc_sets[k])
                    
                    right_desc = set()
                    for m in range(j + 1, len(element.children)):
                        right_desc.update(desc_sets[m])
                        
                    crosses = False
                    for conn in connections:
                        src_el = element_map.get(conn.source)
                        tgt_el = element_map.get(conn.target)
                        if src_el and tgt_el:
                            if (src_el in left_desc and tgt_el in right_desc) or (tgt_el in left_desc and src_el in right_desc):
                                crosses = True
                                break
                    if crosses:
                        gaps[j] = element.gap + 35

            def compute_container_size(child_sizes, title_opt_default):
                temp_sizes = list(child_sizes)
                to_stretch = [i for i, child in enumerate(element.children) if should_stretch(child, element)]
                
                if to_stretch:
                    if layout_mode == 'vertical':
                        # Stretch width of child containers in vertical layout
                        max_w = max(temp_sizes[i][0] for i in to_stretch)
                        for i in to_stretch:
                            temp_sizes[i] = (max_w, temp_sizes[i][1])
                    elif layout_mode == 'horizontal':
                        # Stretch height of child containers in horizontal layout
                        max_h = max(temp_sizes[i][1] for i in to_stretch)
                        for i in to_stretch:
                            temp_sizes[i] = (temp_sizes[i][0], max_h)
                
                if not temp_sizes:
                    children_width = 150
                    children_height = 100
                else:
                    if layout_mode == 'vertical':
                        children_width = max(sz[0] for sz in temp_sizes)
                        children_height = sum(temp_sizes[i][1] for i in range(len(temp_sizes))) + sum(gaps)
                    else:
                        children_width = sum(temp_sizes[i][0] for i in range(len(temp_sizes))) + sum(gaps)
                        children_height = max(sz[1] for sz in temp_sizes)
                
                # Dynamically choose title wrap option based on children_width
                title_opt = title_opt_default
                for opt in title_options:
                    opt_w = max(len(l) for l in opt) * 10
                    if opt_w <= children_width:
                        title_opt = opt
                        break
                
                bt_val = bt_base + (len(title_opt) - 1) * 15
                w = children_width + bl + br
                h = children_height + bt_val + bb

                # Enforce min width/height based on container title length
                max_line_len = max(len(l) for l in title_opt)
                min_width = max_line_len * 10 + bl + br + 20
                min_height = bt_val + bb + 20
                w = max(w, min_width)
                h = max(h, min_height)
                return w, h

            # Compute wrapped size
            w_wrapped, h_wrapped = compute_container_size(
                [child_sizes_list[c][0] for c in element.children],
                wrapped_title
            )

            # Compute unwrapped size
            w_unwrapped, h_unwrapped = compute_container_size(
                [child_sizes_list[c][-1] for c in element.children],
                unwrapped_title
            )

            sizes = [(w_wrapped, h_wrapped), (w_unwrapped, h_unwrapped)]

            # Apply the chosen variation's size to the container
            sel_idx = min(chosen_idx, len(sizes) - 1)
            element.width, element.height = sizes[sel_idx]

            # Arrange children in the container based on the chosen variation
            if element.children:
                # Retrieve the children sizes under the chosen variation
                chosen_child_sizes = []
                for child in element.children:
                    c_sizes = child_sizes_list[child]
                    chosen_child_sizes.append(c_sizes[min(sel_idx, len(c_sizes) - 1)])
                
                # Apply base sizes to children
                for i, child in enumerate(element.children):
                    child.width, child.height = chosen_child_sizes[i]

                # Perform stretching
                to_stretch = [i for i, child in enumerate(element.children) if should_stretch(child, element)]
                
                if layout_mode == 'vertical':
                    if to_stretch:
                        max_child_width = max(element.children[i].width for i in to_stretch)
                        for i in to_stretch:
                            LayoutEngine.expand_container(element.children[i], max_child_width, element.children[i].height, renderer)
                            
                    # Find title wrapping and layout y offset
                    children_w = max(child.width for child in element.children) if element.children else 150
                    title_opt_chosen = unwrapped_title
                    for opt in title_options:
                        opt_w = max(len(l) for l in opt) * 10
                        if opt_w <= children_w:
                            title_opt_chosen = opt
                            break
                    bt_chosen = bt_base + (len(title_opt_chosen) - 1) * 15
                    current_x = bl
                    current_y = bt_chosen
                    
                    # Position and compute actual dimensions
                    max_child_width = 0
                    for i, child in enumerate(element.children):
                        child.x = current_x
                        child.y = current_y
                        if i < len(element.children) - 1:
                            gap_val = gaps[i]
                            current_y += child.height + gap_val
                        else:
                            current_y += child.height
                        max_child_width = max(max_child_width, child.width)
                    element.width = max_child_width + bl + br
                    element.height = current_y + bb

                elif layout_mode == 'horizontal':
                    if to_stretch:
                        max_child_height = max(element.children[i].height for i in to_stretch)
                        for i in to_stretch:
                            LayoutEngine.expand_container(element.children[i], element.children[i].width, max_child_height, renderer)
                            
                    # Find title wrapping and layout y offset
                    children_w = sum(child.width + (gaps[i] if i < len(gaps) else element.gap) for i, child in enumerate(element.children)) - (gaps[-1] if gaps else element.gap) if element.children else 150
                    title_opt_chosen = unwrapped_title
                    for opt in title_options:
                        opt_w = max(len(l) for l in opt) * 10
                        if opt_w <= children_w:
                            title_opt_chosen = opt
                            break
                    bt_chosen = bt_base + (len(title_opt_chosen) - 1) * 15
                    current_x = bl
                    current_y = bt_chosen
                    
                    # Position and compute actual dimensions
                    max_child_height = 0
                    for i, child in enumerate(element.children):
                        child.x = current_x
                        child.y = current_y
                        if i < len(element.children) - 1:
                            gap_val = gaps[i]
                            current_x += child.width + gap_val
                        else:
                            current_x += child.width
                        max_child_height = max(max_child_height, child.height)
                    element.width = current_x + br
                    element.height = max_child_height + bt_chosen + bb

                # Re-enforce container title min bounds on the final layout
                min_w = max(len(l) for l in title_opt_chosen) * 10 + bl + br + 20
                min_h = bt_chosen + bb + 20
                element.width = max(element.width, min_w)
                element.height = max(element.height, min_h)

            return sizes

    @staticmethod
    def expand_container(element: ArchElement, new_width: float, new_height: float, renderer=None):
        """Recursively stretches containers and realigns internal children."""
        if renderer is None:
            from archDraw.render.svg import SVGRenderer
            renderer = SVGRenderer()

        if not isinstance(element, Container):
            if isinstance(element, Node):
                element.width = max(element.width, new_width)
                element.height = max(element.height, new_height)
            return

        bl, br, bt_base, bb = renderer.get_container_borders(element)
        title_options = TextRenderer.get_wrapping_options(element.name)
        title_opt = title_options[0]
        for opt in title_options:
            opt_w = max(len(l) for l in opt) * 10
            if opt_w <= (new_width - bl - br):
                title_opt = opt
                break
        bt_chosen = bt_base + (len(title_opt) - 1) * 15

        has_icon = any(isinstance(child, Node) and ("::" in child.node_type or child.node_type.startswith("icon::")) for child in element.children)
        layout_mode = 'horizontal' if has_icon else element.layout

        dw = new_width - element.width
        dh = new_height - element.height
        
        element.width = new_width
        element.height = new_height

        if not element.children:
            return

        to_stretch = [i for i, child in enumerate(element.children) if should_stretch(child, element)]
        
        if layout_mode == 'vertical':
            child_w = new_width - (bl + br)
            for child in element.children:
                if isinstance(child, Container):
                    LayoutEngine.expand_container(child, child_w, child.height, renderer)
                elif isinstance(child, Node) and child in [element.children[i] for i in to_stretch]:
                    child.width = child_w
                    
            if to_stretch and dh > 0:
                dh_each = dh / len(to_stretch)
                for i in to_stretch:
                    child = element.children[i]
                    LayoutEngine.expand_container(child, child.width, child.height + dh_each, renderer)
        else: # horizontal
            child_h = new_height - (bt_chosen + bb)
            for child in element.children:
                if isinstance(child, Container):
                    LayoutEngine.expand_container(child, child.width, child_h, renderer)
                elif isinstance(child, Node) and child in [element.children[i] for i in to_stretch]:
                    child.height = child_h
                    
            if to_stretch and dw > 0:
                dw_each = dw / len(to_stretch)
                for i in to_stretch:
                    child = element.children[i]
                    LayoutEngine.expand_container(child, child.width + dw_each, child.height, renderer)

        # Reposition all children
        if layout_mode == 'vertical':
            current_x = bl
            current_y = bt_chosen
            for child in element.children:
                child.x = current_x
                child.y = current_y
                current_y += child.height + element.gap
        else:
            current_x = bl
            current_y = bt_chosen
            for child in element.children:
                child.x = current_x
                child.y = current_y
                current_x += child.width + element.gap

    @staticmethod
    def apply_offset(element: ArchElement, dx: int, dy: int):
        """Top-down pass: shifts elements to global coordinates."""
        element.x += dx
        element.y += dy
        for child in element.children:
            LayoutEngine.apply_offset(child, element.x, element.y)

    @staticmethod
    def validate_and_enclose(element: ArchElement):
        """
        Validates that all children lie entirely inside the boundaries of their parent container.
        If a child extends beyond the parent, the parent is expanded to enclose it.
        """
        if not isinstance(element, Container) or not element.children:
            return
            
        for child in element.children:
            LayoutEngine.validate_and_enclose(child)
            
        bl, br, bt, bb = 15, 15, 40, 15
        
        min_child_x = min(child.x for child in element.children)
        min_child_y = min(child.y for child in element.children)
        max_child_x = max(child.x + child.width for child in element.children)
        max_child_y = max(child.y + child.height for child in element.children)
        
        expected_min_x = element.x + bl
        expected_max_x = element.x + element.width - br
        expected_min_y = element.y + bt
        expected_max_y = element.y + element.height - bb
        
        if min_child_x < expected_min_x:
            diff = expected_min_x - min_child_x
            element.x -= diff
            element.width += diff
        if max_child_x > expected_max_x:
            diff = max_child_x - expected_max_x
            element.width += diff
            
        if min_child_y < expected_min_y:
            diff = expected_min_y - min_child_y
            element.y -= diff
            element.height += diff
        if max_child_y > expected_max_y:
            diff = max_child_y - expected_max_y
            element.height += diff