import math
import heapq
from archDraw.core.elements import Node, Container

"""
GRID ROUTING RULES WITH PRIORITIES:
1. Priority 1 (Orthogonal Lines): Lines must consist only of horizontal or vertical segments.
2. Priority 2 (Port Exit Orthogonality & Minimal Length): Lines must start/end orthogonally from the ports with a minimum lead-in/lead-out length (20px) to prevent lines consisting only of an arrow.
3. Priority 3 (Obstacle Avoidance for Nodes): Lines must not cross the bounding box of any leaf Node.
4. Priority 4 (Container Textbox Avoidance): Lines must not cross the header textbox (top title_height area) of any Container horizontally, but may cross it vertically.
5. Priority 5 (Same-Hierarchy Container Obstacle): Parallel/sibling containers at the same hierarchy level (except direct ancestors) must be treated as obstacles to avoid lines passing through them.
6. Priority 6 (Shortest Path): Within these constraints, the line length must be minimized.
7. Priority 7 (Shorter Connections Preference): Lines prefer port positions that slide along boundaries to align with the target, minimizing horizontal/vertical offsets.
"""

# Fractional positions along the boundary and their associated alignment penalties
FRACTIONS = [
    (0.5, 0),       # Center (Weight 0)
    (0.375, 5),     # 3/8 (Weight 5)
    (0.625, 5),     # 5/8 (Weight 5)
    (0.25, 15),     # 1/4 (Weight 15)
    (0.75, 15),     # 3/4 (Weight 15)
    (0.125, 30),    # 1/8 (Weight 30)
    (0.875, 30)     # 7/8 (Weight 30)
]

def route_grid(src: Node, tgt: Node, src_pts: dict, tgt_pts: dict, all_elements: list, routed_points=None) -> dict:
    """
    Computes obstacle-avoiding orthogonal route using A* search on a discretized grid.
    """
    # 1. Grid parameters
    step = 10
    
    # Calculate bounding box of the whole canvas (plus margin)
    min_x = min(el.x for el in all_elements) - 100
    min_y = min(el.y for el in all_elements) - 100
    max_x = max(el.x + el.width for el in all_elements) + 100
    max_y = max(el.y + el.height for el in all_elements) + 100

    width = max_x - min_x
    height = max_y - min_y

    cols = int(math.ceil(width / step)) + 1
    rows = int(math.ceil(height / step)) + 1

    # Map global coordinates to grid coordinates
    def to_grid(gx, gy):
        return int(round((gx - min_x) / step)), int(round((gy - min_y) / step))

    # Build parent mapping
    parents = {}
    for el in all_elements:
        for child in el.children:
            parents[child] = el

    # Find ancestors
    def get_ancestors(element):
        anc = set()
        curr = element
        while curr in parents:
            curr = parents[curr]
            anc.add(curr)
        return anc

    src_ancestors = get_ancestors(src)
    tgt_ancestors = get_ancestors(tgt)
    allowed_ancestors = src_ancestors.union(tgt_ancestors).union({src, tgt})

    # 2. Identify obstacles and assign penalty costs (soft obstacles cost map)
    horizontal_obstacle_costs = {}
    vertical_obstacle_costs = {}
    
    # Rule 4: Container Textboxes are horizontal obstacles (Penalty: 3000)
    for el in all_elements:
        if isinstance(el, Container):
            title_h = getattr(el, "title_height", 30)
            start_c, start_r = to_grid(el.x, el.y)
            end_c, end_r = to_grid(el.x + el.width, el.y + title_h)
            for c in range(start_c, end_c + 1):
                for r in range(start_r, end_r + 1):
                    horizontal_obstacle_costs[(c, r)] = max(horizontal_obstacle_costs.get((c, r), 0), 3000)
    
    for el in all_elements:
        if el in allowed_ancestors:
            continue
        
        is_obstacle = False
        box_x, box_y, box_w, box_h = el.x, el.y, el.width, el.height
        
        # Rule 3: Leaf Nodes are obstacles for both directions
        if isinstance(el, Node):
            is_obstacle = True
            
        # Rule 5: Sibling Container at the same hierarchy
        elif isinstance(el, Container):
            el_parent = parents.get(el)
            is_sibling = False
            for allowed in allowed_ancestors:
                if parents.get(allowed) == el_parent:
                    is_sibling = True
                    break
            
            if is_sibling:
                is_obstacle = True
                
        if is_obstacle:
            # Block the exact bounding box for both directions (Node Penalty: 10000, Container Sibling Penalty: 5000)
            start_c, start_r = to_grid(box_x, box_y)
            end_c, end_r = to_grid(box_x + box_w, box_y + box_h)
            penalty = 10000 if isinstance(el, Node) else 5000
            for c in range(start_c, end_c + 1):
                for r in range(start_r, end_r + 1):
                    horizontal_obstacle_costs[(c, r)] = max(horizontal_obstacle_costs.get((c, r), 0), penalty)
                    vertical_obstacle_costs[(c, r)] = max(vertical_obstacle_costs.get((c, r), 0), penalty)

    # Add previously routed paths as obstacles with a high penalty (Penalty: 1500 to prevent crossing other lines)
    if routed_points:
        for pt in routed_points:
            horizontal_obstacle_costs[pt] = max(horizontal_obstacle_costs.get(pt, 0), 1500)
            vertical_obstacle_costs[pt] = max(vertical_obstacle_costs.get(pt, 0), 1500)

    # Evaluate port pairs and fractional candidates
    port_pairs = []
    is_nested = (src in src_ancestors) or (tgt in tgt_ancestors)
    src_center_x = src.x + src.width / 2
    src_center_y = src.y + src.height / 2
    tgt_center_x = tgt.x + tgt.width / 2
    tgt_center_y = tgt.y + tgt.height / 2
    is_vertical_conn = abs(src_center_y - tgt_center_y) > abs(src_center_x - tgt_center_x)

    for s_port in ("left", "right", "top", "bottom"):
        for t_port in ("left", "right", "top", "bottom"):
            for s_frac, s_pen in FRACTIONS:
                for t_frac, t_pen in FRACTIONS:
                    if s_port in ("top", "bottom"):
                        s_pt = (src.x + s_frac * src.width, src.y if s_port == "top" else src.y + src.height)
                    else:
                        s_pt = (src.x if s_port == "left" else src.x + src.width, src.y + s_frac * src.height)

                    if t_port in ("top", "bottom"):
                        t_pt = (tgt.x + t_frac * tgt.width, tgt.y if t_port == "top" else tgt.y + tgt.height)
                    else:
                        t_pt = (tgt.x if t_port == "left" else tgt.x + tgt.width, tgt.y + t_frac * tgt.height)

                    dist = math.hypot(s_pt[0] - t_pt[0], s_pt[1] - t_pt[1])
                    cost = dist + s_pen + t_pen

                    # Orientation preference penalty (force top/bottom for vertical connections)
                    if is_vertical_conn:
                        if s_port not in ("top", "bottom") or t_port not in ("top", "bottom"):
                            cost += 60
                    else:
                        if s_port not in ("left", "right") or t_port not in ("left", "right"):
                            cost += 60

                    # Penalty if the connection is shorter than the grid size (10px)
                    if dist < 10:
                        cost += 200

                    # Nesting penalty for horizontal outer container ports
                    if is_nested:
                        if isinstance(src, Container) and s_port in ("left", "right"):
                            cost += 80
                        if isinstance(tgt, Container) and t_port in ("left", "right"):
                            cost += 80

                    # Check if a direct 0-bend connection is possible (aligned and completely unblocked)
                    is_direct = False
                    if abs(s_pt[0] - t_pt[0]) < 1e-5 and s_port in ("top", "bottom") and t_port in ("top", "bottom"):
                        col = to_grid(s_pt[0], s_pt[1])[0]
                        row_start = to_grid(s_pt[0], min(s_pt[1], t_pt[1]))[1]
                        row_end = to_grid(s_pt[0], max(s_pt[1], t_pt[1]))[1]
                        blocked = False
                        for r in range(row_start, row_end + 1):
                            if vertical_obstacle_costs.get((col, r), 0) > 0:
                                blocked = True
                                break
                        if not blocked:
                            is_direct = True
                    elif abs(s_pt[1] - t_pt[1]) < 1e-5 and s_port in ("left", "right") and t_port in ("left", "right"):
                        row = to_grid(s_pt[0], s_pt[1])[1]
                        col_start = to_grid(min(s_pt[0], t_pt[0]), s_pt[1])[0]
                        col_end = to_grid(max(s_pt[0], t_pt[0]), s_pt[1])[0]
                        blocked = False
                        for c in range(col_start, col_end + 1):
                            if horizontal_obstacle_costs.get((c, row), 0) > 0:
                                blocked = True
                                break
                        if not blocked:
                            is_direct = True

                    if is_direct:
                        cost -= 1000 # Large preference bonus for direct connections

                    port_pairs.append((cost, s_port, s_pt, t_port, t_pt))
            
    port_pairs.sort(key=lambda x: x[0])
    
    best_src_port = None
    best_tgt_port = None
    best_s_pt = None
    best_t_pt = None
    lead_len = 0 

    for cost, s_port, s_pt, t_port, t_pt in port_pairs:
        sc, sr = to_grid(s_pt[0], s_pt[1])
        tc, tr = to_grid(t_pt[0], t_pt[1])

        # Check directional blockages for exit/entry grid cells
        s_blocked = False
        if s_port in ("left", "right"):
            if horizontal_obstacle_costs.get((sc, sr), 0) >= 5000:
                s_blocked = True
        else: # top, bottom
            if vertical_obstacle_costs.get((sc, sr), 0) >= 5000:
                s_blocked = True

        t_blocked = False
        if t_port in ("left", "right"):
            if horizontal_obstacle_costs.get((tc, tr), 0) >= 5000:
                t_blocked = True
        else: # top, bottom
            if vertical_obstacle_costs.get((tc, tr), 0) >= 5000:
                t_blocked = True

        if not s_blocked and not t_blocked:
            best_src_port = s_port
            best_tgt_port = t_port
            best_s_pt = s_pt
            best_t_pt = t_pt
            break

    # Fallback to shortest distance pair if all options are blocked
    if best_src_port is None:
        _, _, best_src_port, best_s_pt, best_tgt_port, best_t_pt = port_pairs[0]

    start_gx, start_gy = best_s_pt
    end_gx, end_gy = best_t_pt

    # Define lead-in / lead-out bounds precisely
    start_lead_x, start_lead_y = start_gx, start_gy
    end_lead_x, end_lead_y = end_gx, end_gy

    start_c, start_r = to_grid(start_lead_x, start_lead_y)
    end_c, end_r = to_grid(end_lead_x, end_lead_y)

    # Align grid coordinate conversion exactly with port lead-in coordinates to eliminate grid discretization wiggles
    def to_global(col, row):
        gx = min_x + col * step
        gy = min_y + row * step
        if col == start_c:
            gx = start_lead_x
        elif col == end_c:
            gx = end_lead_x
        if row == start_r:
            gy = start_lead_y
        elif row == end_r:
            gy = end_lead_y
        return gx, gy

    # --- 0-Bend Direct Connection Optimization ---
    if abs(start_gx - end_gx) < 1e-5:
        y_min = min(start_gy, end_gy)
        y_max = max(start_gy, end_gy)
        blocked = False
        col = to_grid(start_gx, start_gy)[0]
        row_start = to_grid(start_gx, y_min)[1]
        row_end = to_grid(start_gx, y_max)[1]
        for r in range(row_start, row_end + 1):
            if vertical_obstacle_costs.get((col, r), 0) > 0:
                blocked = True
                break
        if not blocked:
            return {
                "path_d": f"M {start_gx} {start_gy} L {end_gx} {end_gy}",
                "label_x": start_gx,
                "label_y": (start_gy + end_gy) / 2,
                "grid_path": [(col, r) for r in range(row_start, row_end + 1)]
            }

    if abs(start_gy - end_gy) < 1e-5:
        x_min = min(start_gx, end_gx)
        x_max = max(start_gx, end_gx)
        blocked = False
        row = to_grid(start_gx, start_gy)[1]
        col_start = to_grid(x_min, start_gy)[0]
        col_end = to_grid(x_max, start_gy)[0]
        for c in range(col_start, col_end + 1):
            if horizontal_obstacle_costs.get((c, row), 0) > 0:
                blocked = True
                break
        if not blocked:
            return {
                "path_d": f"M {start_gx} {start_gy} L {end_gx} {end_gy}",
                "label_x": (start_gx + end_gx) / 2,
                "label_y": start_gy,
                "grid_path": [(c, row) for c in range(col_start, col_end + 1)]
            }

    # Define strict start and end exit/entry directions
    dc, dr = 0, 0
    if best_src_port == "left":
        dc, dr = -1, 0
    elif best_src_port == "right":
        dc, dr = 1, 0
    elif best_src_port == "top":
        dc, dr = 0, -1
    else:
        dc, dr = 0, 1

    tdc, tdr = 0, 0
    if best_tgt_port == "left":
        tdc, tdr = 1, 0
    elif best_tgt_port == "right":
        tdc, tdr = -1, 0
    elif best_tgt_port == "top":
        tdc, tdr = 0, 1
    else:
        tdc, tdr = 0, -1

    # 3. A* Search
    pq = []
    # Push initial state: (f_score, g_score, c, r, dc, dr, path_history)
    heapq.heappush(pq, (0, 0, start_c, start_r, dc, dr, [(start_c, start_r)]))
    
    visited = {} # (c, r, dc, dr) -> g_score
    found_path = None
    bend_penalty = 150 # High penalty to strictly prioritize fewer bends over line length
    
    while pq:
        f, g, c, r, pdc, pdr, path = heapq.heappop(pq)
        
        if (c, r) == (end_c, end_r):
            found_path = path
            break
            
        state_key = (c, r, pdc, pdr)
        if state_key in visited and visited[state_key] <= g:
            continue
        visited[state_key] = g
        
        # Explore neighbors
        for ndc, ndr in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            # Enforce orthogonal exit from the source port
            if len(path) == 1 and (ndc, ndr) != (dc, dr):
                continue
                
            nc, nr = c + ndc, r + ndr
            
            # Bounds check
            if nc < 0 or nc >= cols or nr < 0 or nr >= rows:
                continue
                
            # Enforce orthogonal entry into the target port
            if (nc, nr) == (end_c, end_r) and (ndc, ndr) != (tdc, tdr):
                continue
                
            # Calculate cost (base step cost + directional obstacle penalty)
            step_cost = 1
            if (nc, nr) != (end_c, end_r):
                if ndc != 0:
                    step_cost += horizontal_obstacle_costs.get((nc, nr), 0)
                if ndr != 0:
                    step_cost += vertical_obstacle_costs.get((nc, nr), 0)
                    
            if (pdc != 0 or pdr != 0) and (ndc != pdc or ndr != pdr):
                step_cost += bend_penalty
                
            ng = g + step_cost
            nh = abs(nc - end_c) + abs(nr - end_r)
            nf = ng + nh
            
            nkey = (nc, nr, ndc, ndr)
            if nkey not in visited or ng < visited[nkey]:
                heapq.heappush(pq, (nf, ng, nc, nr, ndc, ndr, path + [(nc, nr)]))

    # If no path found, fallback to Manhattan routing (guaranteed orthogonal, ignores obstacles)
    if not found_path:
        from archDraw.render.manhattan_routing import route_manhattan
        return route_manhattan(src, tgt, src_pts, tgt_pts)

    # 4. Convert grid path back to global SVG path coordinates and simplify segments
    grid_points = [to_global(c, r) for c, r in found_path]
    grid_start_gx, grid_start_gy = grid_points[0]
    grid_end_gx, grid_end_gy = grid_points[-1]
    
    # Construct orthogonal start sequence
    start_seq = []
    if best_src_port in ("left", "right"):
        start_seq = [(start_gx, start_gy), (grid_start_gx, start_gy), (grid_start_gx, grid_start_gy)]
    else:
        start_seq = [(start_gx, start_gy), (start_gx, grid_start_gy), (grid_start_gx, grid_start_gy)]
        
    # Construct orthogonal end sequence
    end_seq = []
    if best_tgt_port in ("left", "right"):
        end_seq = [(grid_end_gx, grid_end_gy), (grid_end_gx, end_gy), (end_gx, end_gy)]
    else:
        end_seq = [(grid_end_gx, grid_end_gy), (end_gx, grid_end_gy), (end_gx, end_gy)]
        
    # Combine path
    global_points = start_seq + grid_points[1:-1] + end_seq
    
    # Remove consecutive duplicates
    deduped_points = []
    for pt in global_points:
        if not deduped_points or pt != deduped_points[-1]:
            deduped_points.append(pt)
    global_points = deduped_points
    
    # Simplify path into horizontal / vertical segments
    simplified = [global_points[0]]
    for i in range(1, len(global_points) - 1):
        prev = global_points[i - 1]
        curr = global_points[i]
        nxt = global_points[i + 1]
        
        # Check if direction changes
        cross_product = (curr[0] - prev[0]) * (nxt[1] - curr[1]) - (curr[1] - prev[1]) * (nxt[0] - curr[0])
        if abs(cross_product) > 1e-5:
            simplified.append(curr)
            
    simplified.append(global_points[-1])

    # 5. Middle segment clearance optimization (2-bend paths)
    vertical_obstacles = {pt for pt, cost in vertical_obstacle_costs.items() if cost >= 3000}
    horizontal_obstacles = {pt for pt, cost in horizontal_obstacle_costs.items() if cost >= 3000}

    def clamp(val, min_val, max_val):
        return max(min_val, min(val, max_val))

    if len(simplified) == 4:
        pt0, pt1, pt2, pt3 = simplified
        if abs(pt1[1] - pt2[1]) < 1e-5: # Horizontal middle segment
            col_start, _ = to_grid(min(pt1[0], pt2[0]), pt1[1])
            col_end, _ = to_grid(max(pt1[0], pt2[0]), pt1[1])
            mid_row = to_grid(pt1[0], pt1[1])[1]
            
            common_min_row = 0
            common_max_row = rows - 1
            
            for c in range(col_start, col_end + 1):
                top_limit = mid_row
                while top_limit > 0:
                    if vertical_obstacle_costs.get((c, top_limit - 1), 0) >= 3000:
                        break
                    top_limit -= 1
                bottom_limit = mid_row
                while bottom_limit < rows - 1:
                    if vertical_obstacle_costs.get((c, bottom_limit + 1), 0) >= 3000:
                        break
                    bottom_limit += 1
                common_min_row = max(common_min_row, top_limit)
                common_max_row = min(common_max_row, bottom_limit)
                
            if common_min_row <= common_max_row:
                # Target exact midpoint of start/end ports for an even vertical split
                ideal_y = (pt0[1] + pt3[1]) / 2
                ideal_row = to_grid(pt0[0], ideal_y)[1]
                opt_row = clamp(ideal_row, common_min_row, common_max_row)
                
                opt_y = to_global(col_start, opt_row)[1]
                pt1 = (pt1[0], opt_y)
                pt2 = (pt2[0], opt_y)
                simplified = [pt0, pt1, pt2, pt3]
                
        elif abs(pt1[0] - pt2[0]) < 1e-5: # Vertical middle segment
            _, row_start = to_grid(pt1[0], min(pt1[1], pt2[1]))
            _, row_end = to_grid(pt1[0], max(pt1[1], pt2[1]))
            mid_col = to_grid(pt1[0], pt1[1])[0]
            
            common_min_col = 0
            common_max_col = cols - 1
            
            for r in range(row_start, row_end + 1):
                left_limit = mid_col
                while left_limit > 0:
                    if horizontal_obstacle_costs.get((left_limit - 1, r), 0) >= 3000:
                        break
                    left_limit -= 1
                right_limit = mid_col
                while right_limit < cols - 1:
                    if horizontal_obstacle_costs.get((right_limit + 1, r), 0) >= 3000:
                        break
                    right_limit += 1
                common_min_col = max(common_min_col, left_limit)
                common_max_col = min(common_max_col, right_limit)
                
            if common_min_col <= common_max_col:
                # Target exact midpoint of start/end ports for an even horizontal split
                ideal_x = (pt0[0] + pt3[0]) / 2
                ideal_col = to_grid(ideal_x, pt0[1])[0]
                opt_col = clamp(ideal_col, common_min_col, common_max_col)
                
                opt_x = to_global(opt_col, row_start)[0]
                pt1 = (opt_x, pt1[1])
                pt2 = (opt_x, pt2[1])
                simplified = [pt0, pt1, pt2, pt3]

    # Build SVG path string
    path_d = f"M {simplified[0][0]} {simplified[0][1]}"
    for pt in simplified[1:]:
        path_d += f" L {pt[0]} {pt[1]}"

    # Label position at the center segment
    mid_idx = len(simplified) // 2
    if len(simplified) >= 2:
        label_x = (simplified[mid_idx - 1][0] + simplified[mid_idx][0]) / 2
        label_y = (simplified[mid_idx - 1][1] + simplified[mid_idx][1]) / 2
    else:
        label_x = (start_gx + end_gx) / 2
        label_y = (start_gy + end_gy) / 2

    return {
        "path_d": path_d,
        "label_x": label_x,
        "label_y": label_y,
        "grid_path": found_path
    }
