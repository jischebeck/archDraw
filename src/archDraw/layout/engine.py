from archDraw.core.elements import ArchElement, Node, Container
from archDraw.render.text import TextRenderer

def should_stretch(child, parent):
    return isinstance(child, Container)

class LayoutEngine:
    """Handles all mathematical bounding-box layout operations."""
    
    @staticmethod
    def calculate_bounds(element: ArchElement, renderer=None, chosen_idx: int = 0) -> list[tuple[float, float]]:
        """Bottom-up layout calculation. Returns [wrapped_size, unwrapped_size]."""
        if renderer is None:
            from archDraw.render.svg import SVGRenderer
            renderer = SVGRenderer()

        if isinstance(element, Node):
            sizes = renderer.get_node_size(element)
            idx = min(chosen_idx, len(sizes) - 1)
            element.width, element.height = sizes[idx]
            return sizes

        if isinstance(element, Container):
            child_sizes_list = {}
            for child in element.children:
                child_sizes_list[child] = LayoutEngine.calculate_bounds(child, renderer, chosen_idx)

            has_icon = any(isinstance(child, Node) and ("::" in child.node_type or child.node_type.startswith("icon::")) for child in element.children)
            layout_mode = 'horizontal' if has_icon else element.layout

            # Container name wrapping options
            title_options = TextRenderer.get_wrapping_options(element.name)
            wrapped_title = title_options[-1]
            unwrapped_title = title_options[0]

            bl, br, bt_base, bb = renderer.get_container_borders(element)

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
                        children_height = sum(sz[1] + element.gap for sz in temp_sizes) - element.gap
                    else:
                        children_width = sum(sz[0] + element.gap for sz in temp_sizes) - element.gap
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
                            element.children[i].width = max_child_width
                            
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
                    for child in element.children:
                        child.x = current_x
                        child.y = current_y
                        current_y += child.height + element.gap
                        max_child_width = max(max_child_width, child.width)
                    element.width = max_child_width + bl + br
                    element.height = current_y - element.gap + bb

                elif layout_mode == 'horizontal':
                    if to_stretch:
                        max_child_height = max(element.children[i].height for i in to_stretch)
                        for i in to_stretch:
                            element.children[i].height = max_child_height
                            
                    # Find title wrapping and layout y offset
                    children_w = sum(child.width + element.gap for child in element.children) - element.gap if element.children else 150
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
                    for child in element.children:
                        child.x = current_x
                        child.y = current_y
                        current_x += child.width + element.gap
                        max_child_height = max(max_child_height, child.height)
                    element.width = current_x - element.gap + br
                    element.height = max_child_height + bt_chosen + bb

                # Re-enforce container title min bounds on the final layout
                min_w = max(len(l) for l in title_opt_chosen) * 10 + bl + br + 20
                min_h = bt_chosen + bb + 20
                element.width = max(element.width, min_w)
                element.height = max(element.height, min_h)

            return sizes

    @staticmethod
    def apply_offset(element: ArchElement, dx: int, dy: int):
        """Top-down pass: shifts elements to global coordinates."""
        element.x += dx
        element.y += dy
        for child in element.children:
            LayoutEngine.apply_offset(child, element.x, element.y)