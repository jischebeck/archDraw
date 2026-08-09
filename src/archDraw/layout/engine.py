from archDraw.core.elements import ArchElement, Node, Container
from archDraw.render.text import TextRenderer

def should_stretch(child, parent):
    return isinstance(child, Container)

class LayoutEngine:
    """Handles all mathematical bounding-box layout operations."""
    
    @staticmethod
    def calculate_bounds(element: ArchElement, renderer=None, chosen_idx: int = 0, connections=None, element_map=None, crossed_gaps=None, direct_gaps=None) -> list[tuple[float, float]]:
        """Bottom-up layout calculation. Returns [wrapped_size, unwrapped_size]."""
        if renderer is None:
            from archDraw.render.svg import SVGRenderer
            renderer = SVGRenderer()

        if element_map is None:
            element_map = {}
            def map_elements(el):
                if hasattr(el, "alias") and el.alias:
                    element_map[el.alias] = el
                element_map[el.name] = el
                for child in el.children:
                    map_elements(child)
            map_elements(element)

        # Multi-pass connection-aware layout routing check
        if connections and crossed_gaps is None:
            # 1. First-pass layout: dry run with base gaps
            LayoutEngine.calculate_bounds(element, renderer, chosen_idx, connections=None, element_map=element_map, crossed_gaps=set(), direct_gaps=set())
            
            # Save original coordinates
            orig_coords = {}
            def save_coords(el):
                orig_coords[el] = (el.x, el.y, el.width, el.height)
                for child in el.children:
                    save_coords(child)
            save_coords(element)
            
            # Assign coordinates for the dry run to position elements globally
            LayoutEngine.apply_offset(element, 0, 0)
            LayoutEngine.validate_and_enclose(element)
            
            # 2. Run mock routing to trace paths
            import re
            from archDraw.render.grid_routing import route_grid
            from archDraw.render.manhattan_routing import route_manhattan
            
            all_elements = list(set(element_map.values()))
            routed_points_by_conn = {}
            for conn in connections:
                src_el = element_map.get(conn.source)
                tgt_el = element_map.get(conn.target)
                if src_el and tgt_el:
                    src_pts = renderer.get_connection_endpoints(src_el)
                    tgt_pts = renderer.get_connection_endpoints(tgt_el)
                    if getattr(renderer, "routing", "grid") == "grid":
                        route = route_grid(src_el, tgt_el, src_pts, tgt_pts, all_elements)
                    else:
                        route = route_manhattan(src_el, tgt_el, src_pts, tgt_pts)
                    
                    path_pts = []
                    path_d = route.get("path_d", "")
                    for m in re.finditer(r'([ML])\s*([0-9.-]+)\s*([0-9.-]+)', path_d):
                        path_pts.append((float(m.group(2)), float(m.group(3))))
                    routed_points_by_conn[conn] = path_pts
            
            # 3. Detect which gaps are crossed/direct
            crossed_gaps = set()
            direct_gaps = set()
            
            def is_direct_sibling_connection(conn, el_a, el_b):
                a_names = {el_a.name, getattr(el_a, "alias", None)}
                b_names = {el_b.name, getattr(el_b, "alias", None)}
                return (conn.source in a_names and conn.target in b_names) or (conn.source in b_names and conn.target in a_names)

            containers = []
            def find_containers(el):
                if isinstance(el, Container):
                    containers.append(el)
                    for child in el.children:
                        find_containers(child)
            find_containers(element)
            
            for C in containers:
                if len(C.children) < 2:
                    continue
                
                bl_b, br_b, bt_b, bb_b = renderer.get_container_borders(C)
                bl = C.padding_left if C.has_explicit_padding else bl_b
                br = C.padding_right if C.has_explicit_padding else br_b
                bt_base = C.padding_top if C.has_explicit_padding else bt_b
                bb = C.padding_bottom if C.has_explicit_padding else bb_b

                has_icon = any(isinstance(child, Node) and ("::" in child.node_type or child.node_type.startswith("icon::")) for child in C.children)
                layout_mode = 'horizontal' if has_icon else C.layout
                
                for j in range(len(C.children) - 1):
                    child_a = C.children[j]
                    child_b = C.children[j+1]
                    
                    is_direct = False
                    for conn in connections:
                        if is_direct_sibling_connection(conn, child_a, child_b):
                            is_direct = True
                            break
                    if is_direct:
                        direct_gaps.add((id(C), j))
                        continue
                    
                    if layout_mode == 'vertical':
                        y_min = child_a.y + child_a.height + child_a.margin_bottom
                        y_max = child_b.y - child_b.margin_top
                        x_min = C.x
                        x_max = C.x + C.width
                    else: # horizontal
                        x_min = child_a.x + child_a.width + child_a.margin_right
                        x_max = child_b.x - child_b.margin_left
                        y_min = C.y
                        y_max = C.y + C.height
                        
                    for conn, pts in routed_points_by_conn.items():
                        for px, py in pts:
                            if layout_mode == 'vertical':
                                if (y_min + 1 <= py <= y_max - 1) and (x_min <= px <= x_max):
                                    crossed_gaps.add((id(C), j))
                                    break
                            else: # horizontal
                                if (x_min + 1 <= px <= x_max - 1) and (y_min <= py <= y_max):
                                    crossed_gaps.add((id(C), j))
                                    break

            # Restore original coordinates
            def restore_coords(el):
                el.x, el.y, el.width, el.height = orig_coords[el]
                for child in el.children:
                    restore_coords(child)
            restore_coords(element)

            # Re-run layout pass WITH the computed final gaps to position everything correctly
            LayoutEngine.calculate_bounds(element, renderer, chosen_idx, connections=None, element_map=element_map, crossed_gaps=crossed_gaps, direct_gaps=direct_gaps)
            LayoutEngine.apply_offset(element, 0, 0)
            LayoutEngine.validate_and_enclose(element)

            # --- Auto-Alignment Solver (Option B) ---
            # Run alignment check on the layout that uses correct final gaps and offsets
            parents = {}
            for el in all_elements:
                for child in el.children:
                    parents[child] = el

            def get_layout_orientation_local(s, t):
                path_s = []
                curr = s
                while curr in parents:
                    curr = parents[curr]
                    path_s.append(curr)
                path_s.reverse()
                
                path_t = []
                curr = t
                while curr in parents:
                    curr = parents[curr]
                    path_t.append(curr)
                path_t.reverse()
                
                lca = None
                common_idx = -1
                for i in range(min(len(path_s), len(path_t))):
                    if path_s[i] == path_t[i]:
                        lca = path_s[i]
                        common_idx = i
                    else:
                        break
                        
                if lca:
                    has_icon = any(isinstance(child, Node) and ("::" in child.node_type or child.node_type.startswith("icon::")) for child in lca.children)
                    lca_layout = 'horizontal' if has_icon else lca.layout
                    return lca_layout == 'vertical'
                
                v_sep_val = max(0, t.y - (s.y + s.height)) + max(0, s.y - (t.y + t.height))
                h_sep_val = max(0, t.x - (s.x + s.width)) + max(0, s.x - (t.x + t.width))
                if v_sep_val > 0 or h_sep_val > 0:
                    return v_sep_val >= h_sep_val
                return abs(s.y + s.height/2 - (t.y + t.height/2)) > abs(s.x + s.width/2 - (t.x + t.width/2))

            def get_alignment_budget(el, direction):
                p = parents.get(el)
                if not p:
                    return 80.0
                has_icon_p = any(isinstance(c, Node) and ("::" in c.node_type or c.node_type.startswith("icon::")) for c in p.children)
                p_layout = 'horizontal' if has_icon_p else p.layout
                if direction == 'horizontal':
                    if p_layout == 'vertical':
                        free_w = p.width - 30 - el.width
                        return max(80.0, free_w)
                else:
                    if p_layout == 'horizontal':
                        free_h = p.height - 55 - el.height
                        return max(80.0, free_h)
                return 80.0

            aligned_nodes = set()
            for conn in connections:
                src_el = element_map.get(conn.source)
                tgt_el = element_map.get(conn.target)
                if src_el and tgt_el and isinstance(src_el, Node) and isinstance(tgt_el, Node):
                    is_vertical = get_layout_orientation_local(src_el, tgt_el)
                    if is_vertical:
                        if not src_el.has_explicit_margin_left and not tgt_el.has_explicit_margin_left:
                            dx = (tgt_el.x + tgt_el.width/2) - (src_el.x + src_el.width/2)
                            if abs(dx) > 1e-3:
                                if dx > 0 and src_el not in aligned_nodes:
                                    if abs(dx) <= get_alignment_budget(src_el, 'horizontal'):
                                        src_el.margin_left += dx
                                        aligned_nodes.add(src_el)
                                elif dx < 0 and tgt_el not in aligned_nodes:
                                    if abs(dx) <= get_alignment_budget(tgt_el, 'horizontal'):
                                        tgt_el.margin_left += -dx
                                        aligned_nodes.add(tgt_el)
                    else:
                        if not src_el.has_explicit_margin_top and not tgt_el.has_explicit_margin_top:
                            dy = (tgt_el.y + tgt_el.height/2) - (src_el.y + src_el.height/2)
                            if abs(dy) > 1e-3:
                                if dy > 0 and src_el not in aligned_nodes:
                                    if abs(dy) <= get_alignment_budget(src_el, 'vertical'):
                                        src_el.margin_top += dy
                                        aligned_nodes.add(src_el)
                                elif dy < 0 and tgt_el not in aligned_nodes:
                                    if abs(dy) <= get_alignment_budget(tgt_el, 'vertical'):
                                        tgt_el.margin_top += -dy
                                        aligned_nodes.add(tgt_el)

            # Restore original coordinates once more
            restore_coords(element)
            
            # Re-run final layout bounds calculation with computed gaps and adjusted margins
            return LayoutEngine.calculate_bounds(element, renderer, chosen_idx, connections=connections, element_map=element_map, crossed_gaps=crossed_gaps, direct_gaps=direct_gaps)

        if isinstance(element, Node):
            sizes = renderer.get_node_size(element)
            idx = min(chosen_idx, len(sizes) - 1)
            element.width, element.height = sizes[idx]
            return sizes

        if isinstance(element, Container):
            child_sizes_list = {}
            for child in element.children:
                child_sizes_list[child] = LayoutEngine.calculate_bounds(child, renderer, chosen_idx, connections, element_map, crossed_gaps, direct_gaps)

            has_icon = any(isinstance(child, Node) and ("::" in child.node_type or child.node_type.startswith("icon::")) for child in element.children)
            layout_mode = 'horizontal' if has_icon else element.layout

            # Container name wrapping options
            title_options = TextRenderer.get_wrapping_options(element.name)
            wrapped_title = title_options[-1]
            unwrapped_title = title_options[0]

            bl_base, br_base, bt_base_val, bb_base = renderer.get_container_borders(element)
            bl = element.padding_left if element.has_explicit_padding else bl_base
            br = element.padding_right if element.has_explicit_padding else br_base
            bt_base = element.padding_top if element.has_explicit_padding else bt_base_val
            bb = element.padding_bottom if element.has_explicit_padding else bb_base

            # Calculate dynamic gaps based on connections crossing between child boundaries
            gaps = [element.gap] * (len(element.children) - 1)
            if direct_gaps is not None or crossed_gaps is not None:
                for j in range(len(element.children) - 1):
                    if direct_gaps and (id(element), j) in direct_gaps:
                        gaps[j] = 30
                    elif crossed_gaps and (id(element), j) in crossed_gaps:
                        gaps[j] = 15
            element.computed_gaps = gaps

            def compute_container_size(child_sizes, title_opt_default):
                temp_sizes = list(child_sizes)
                to_stretch = [i for i, child in enumerate(element.children) if should_stretch(child, element)]
                
                if to_stretch:
                    if layout_mode == 'vertical':
                        # Stretch width of child containers in vertical layout
                        max_w = max(temp_sizes[i][0] + element.children[i].margin_left + element.children[i].margin_right for i in to_stretch)
                        for i in to_stretch:
                            temp_sizes[i] = (max_w - element.children[i].margin_left - element.children[i].margin_right, temp_sizes[i][1])
                    elif layout_mode == 'horizontal':
                        # Stretch height of child containers in horizontal layout
                        max_h = max(temp_sizes[i][1] + element.children[i].margin_top + element.children[i].margin_bottom for i in to_stretch)
                        for i in to_stretch:
                            temp_sizes[i] = (temp_sizes[i][0], max_h - element.children[i].margin_top - element.children[i].margin_bottom)
                
                if not temp_sizes:
                    children_width = 150
                    children_height = 100
                else:
                    if layout_mode == 'vertical':
                        children_width = max(sz[0] + element.children[i].margin_left + element.children[i].margin_right for i, sz in enumerate(temp_sizes))
                        children_height = sum(sz[1] + element.children[i].margin_top + element.children[i].margin_bottom for i, sz in enumerate(temp_sizes)) + sum(gaps)
                    else:
                        children_width = sum(sz[0] + element.children[i].margin_left + element.children[i].margin_right for i, sz in enumerate(temp_sizes)) + sum(gaps)
                        children_height = max(sz[1] + element.children[i].margin_top + element.children[i].margin_bottom for i, sz in enumerate(temp_sizes))
                
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
                        max_child_width = max(element.children[i].width + element.children[i].margin_left + element.children[i].margin_right for i in to_stretch)
                        for i in to_stretch:
                            w_stretch = max_child_width - element.children[i].margin_left - element.children[i].margin_right
                            LayoutEngine.expand_container(element.children[i], w_stretch, element.children[i].height, renderer)
                            
                    # Find title wrapping and layout y offset
                    children_w = max(child.width + child.margin_left + child.margin_right for child in element.children) if element.children else 150
                    title_opt_chosen = unwrapped_title
                    for opt in title_options:
                        opt_w = max(len(l) for l in opt) * 10
                        if opt_w <= children_w:
                            title_opt_chosen = opt
                            break
                    bt_chosen = bt_base + (len(title_opt_chosen) - 1) * 15
                    element.bt_chosen = bt_chosen
                    
                    max_child_width = max(child.width + child.margin_left + child.margin_right for child in element.children) if element.children else 0
                    current_y = bt_chosen
                    
                    # Position and compute actual dimensions
                    for i, child in enumerate(element.children):
                        child_w_space = child.width + child.margin_left + child.margin_right
                        align_val = getattr(element, "alignment", "left")
                        if align_val == "center":
                            child.x = bl + child.margin_left + (max_child_width - child_w_space) / 2
                        elif align_val in ("right", "down", "bottom"):
                            child.x = bl + child.margin_left + (max_child_width - child_w_space)
                        else:
                            child.x = bl + child.margin_left
                        
                        child.y = current_y + child.margin_top
                        if i < len(element.children) - 1:
                            gap_val = gaps[i]
                            current_y += child.height + child.margin_top + child.margin_bottom + gap_val
                        else:
                            current_y += child.height + child.margin_top + child.margin_bottom
                    element.width = max_child_width + bl + br
                    element.height = current_y + bb

                elif layout_mode == 'horizontal':
                    if to_stretch:
                        max_child_height = max(element.children[i].height + element.children[i].margin_top + element.children[i].margin_bottom for i in to_stretch)
                        for i in to_stretch:
                            h_stretch = max_child_height - element.children[i].margin_top - element.children[i].margin_bottom
                            LayoutEngine.expand_container(element.children[i], element.children[i].width, h_stretch, renderer)
                            
                    # Find title wrapping and layout y offset
                    children_w = sum(child.width + child.margin_left + child.margin_right + (gaps[i] if i < len(gaps) else element.gap) for i, child in enumerate(element.children)) - (gaps[-1] if gaps else element.gap) if element.children else 150
                    title_opt_chosen = unwrapped_title
                    for opt in title_options:
                        opt_w = max(len(l) for l in opt) * 10
                        if opt_w <= children_w:
                            title_opt_chosen = opt
                            break
                    bt_chosen = bt_base + (len(title_opt_chosen) - 1) * 15
                    element.bt_chosen = bt_chosen
                    
                    max_child_height = max(child.height + child.margin_top + child.margin_bottom for child in element.children) if element.children else 0
                    current_x = bl
                    
                    # Position and compute actual dimensions
                    for i, child in enumerate(element.children):
                        child.x = current_x + child.margin_left
                        
                        child_h_space = child.height + child.margin_top + child.margin_bottom
                        align_val = getattr(element, "alignment", "left")
                        if align_val == "center":
                            child.y = bt_chosen + child.margin_top + (max_child_height - child_h_space) / 2
                        elif align_val in ("bottom", "down", "right"):
                            child.y = bt_chosen + child.margin_top + (max_child_height - child_h_space)
                        else:
                            child.y = bt_chosen + child.margin_top
                        
                        if i < len(element.children) - 1:
                            gap_val = gaps[i]
                            current_x += child.width + child.margin_left + child.margin_right + gap_val
                        else:
                            current_x += child.width + child.margin_left + child.margin_right
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

        bl_b, br_b, bt_b, bb_b = renderer.get_container_borders(element)
        bl = element.padding_left if element.has_explicit_padding else bl_b
        br = element.padding_right if element.has_explicit_padding else br_b
        bt_base = element.padding_top if element.has_explicit_padding else bt_b
        bb = element.padding_bottom if element.has_explicit_padding else bb_b

        title_options = TextRenderer.get_wrapping_options(element.name)
        title_opt = title_options[0]
        for opt in title_options:
            opt_w = max(len(l) for l in opt) * 10
            if opt_w <= (new_width - bl - br):
                title_opt = opt
                break
        bt_chosen = bt_base + (len(title_opt) - 1) * 15
        
        # If the container's title height decreased due to wider horizontal space,
        # we shrink the container's height accordingly to avoid empty space
        old_bt_chosen = getattr(element, "bt_chosen", bt_chosen)
        if old_bt_chosen > bt_chosen:
            new_height -= (old_bt_chosen - bt_chosen)
        element.bt_chosen = bt_chosen

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
                    LayoutEngine.expand_container(child, child_w - child.margin_left - child.margin_right, child.height, renderer)
                elif isinstance(child, Node) and child in [element.children[i] for i in to_stretch]:
                    child.width = child_w - child.margin_left - child.margin_right
                    
            if to_stretch and dh > 0:
                dh_each = dh / len(to_stretch)
                for i in to_stretch:
                    child = element.children[i]
                    LayoutEngine.expand_container(child, child.width, child.height + dh_each, renderer)
        else: # horizontal
            child_h = new_height - (bt_chosen + bb)
            for child in element.children:
                if isinstance(child, Container):
                    LayoutEngine.expand_container(child, child.width, child_h - child.margin_top - child.margin_bottom, renderer)
                elif isinstance(child, Node) and child in [element.children[i] for i in to_stretch]:
                    child.height = child_h - child.margin_top - child.margin_bottom
                    
            if to_stretch and dw > 0:
                dw_each = dw / len(to_stretch)
                for i in to_stretch:
                    child = element.children[i]
                    LayoutEngine.expand_container(child, child.width + dw_each, child.height, renderer)

        # Reposition all children
        gaps = getattr(element, "computed_gaps", [element.gap] * (len(element.children) - 1))
        if layout_mode == 'vertical':
            child_w = new_width - (bl + br)
            current_y = bt_chosen
            for i, child in enumerate(element.children):
                child_w_space = child.width + child.margin_left + child.margin_right
                align_val = getattr(element, "alignment", "left")
                if align_val == "center":
                    child.x = bl + child.margin_left + (child_w - child_w_space) / 2
                elif align_val in ("right", "down", "bottom"):
                    child.x = bl + child.margin_left + (child_w - child_w_space)
                else:
                    child.x = bl + child.margin_left
                child.y = current_y + child.margin_top
                gap_val = gaps[i] if i < len(gaps) else element.gap
                current_y += child.height + child.margin_top + child.margin_bottom + gap_val
        else:
            child_h = new_height - (bt_chosen + bb)
            current_x = bl
            for i, child in enumerate(element.children):
                child.x = current_x + child.margin_left
                child_h_space = child.height + child.margin_top + child.margin_bottom
                align_val = getattr(element, "alignment", "left")
                if align_val == "center":
                    child.y = bt_chosen + child.margin_top + (child_h - child_h_space) / 2
                elif align_val in ("bottom", "down", "right"):
                    child.y = bt_chosen + child.margin_top + (child_h - child_h_space)
                else:
                    child.y = bt_chosen + child.margin_top
                gap_val = gaps[i] if i < len(gaps) else element.gap
                current_x += child.width + child.margin_left + child.margin_right + gap_val

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