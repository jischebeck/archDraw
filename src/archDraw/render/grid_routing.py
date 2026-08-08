import math
import heapq
from archDraw.core.elements import Node, Container

"""
GRID ROUTING RULES WITH PRIORITIES:
1. Priority 1 (Orthogonal Lines): Lines must consist only of horizontal or vertical segments.
2. Priority 2 (Port Exit Orthogonality & Minimal Length): Lines must start/end orthogonally from the ports with a minimum lead-in/lead-out length (20px) to prevent lines consisting only of an arrow.
3. Priority 3 (Obstacle Avoidance for Nodes): Lines must not cross the bounding box of any leaf Node.
4. Priority 4 (Container Textbox Avoidance): Lines must not cross the header textbox (top title_height area) of any Container.
5. Priority 5 (Same-Hierarchy Container Obstacle): Parallel/sibling containers at the same hierarchy level (except direct ancestors) must be treated as obstacles to avoid lines passing through them.
6. Priority 6 (Shortest Path): Within these constraints, the line length must be minimized.
7. Priority 7 (Port Center Preference): Lines should preferably start from the center or end at the center of the boundary side of a line, node, or box.
"""

def route_grid(src: Node, tgt: Node, src_pts: dict, tgt_pts: dict, all_elements: list) -> dict:
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

    def to_global(col, row):
        return min_x + col * step, min_y + row * step

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

    # 2. Identify obstacles based on Priorities
    obstacles = set()
    for el in all_elements:
        if el in allowed_ancestors:
            continue
        
        is_obstacle = False
        box_x, box_y, box_w, box_h = el.x, el.y, el.width, el.height
        
        # Rule 3: Leaf Nodes are obstacles (block exact node coordinates)
        if isinstance(el, Node):
            is_obstacle = True
            
        # Rule 4 & 5: Container logic
        elif isinstance(el, Container):
            # Rule 4: Container Textbox is always an obstacle
            title_h = getattr(el, "title_height", 30)
            start_c, start_r = to_grid(el.x, el.y)
            end_c, end_r = to_grid(el.x + el.width, el.y + title_h)
            for c in range(start_c, end_c + 1):
                for r in range(start_r, end_r + 1):
                    obstacles.add((c, r))
            
            # Rule 5: Sibling Container at the same hierarchy
            el_parent = parents.get(el)
            is_sibling = False
            for allowed in allowed_ancestors:
                if parents.get(allowed) == el_parent:
                    is_sibling = True
                    break
            
            if is_sibling:
                is_obstacle = True
                
        if is_obstacle:
            # Block the exact bounding box of the element
            start_c, start_r = to_grid(box_x, box_y)
            end_c, end_r = to_grid(box_x + box_w, box_y + box_h)
            for c in range(start_c, end_c + 1):
                for r in range(start_r, end_r + 1):
                    obstacles.add((c, r))

    # Find the port pair that has the shortest direct distance
    best_dist = float('inf')
    best_src_port = None
    best_tgt_port = None

    for s_port, s_pt in src_pts.items():
        for t_port, t_pt in tgt_pts.items():
            dist = math.hypot(s_pt[0] - t_pt[0], s_pt[1] - t_pt[1])
            if dist < best_dist:
                best_dist = dist
                best_src_port = s_port
                best_tgt_port = t_port

    start_gx, start_gy = src_pts[best_src_port]
    end_gx, end_gy = tgt_pts[best_tgt_port]

    # Enforce minimum lead-in / lead-out length (20px)
    lead_len = 20
    
    if best_src_port == "left":
        start_lead_x, start_lead_y = start_gx - lead_len, start_gy
    elif best_src_port == "right":
        start_lead_x, start_lead_y = start_gx + lead_len, start_gy
    elif best_src_port == "top":
        start_lead_x, start_lead_y = start_gx, start_gy - lead_len
    else: # bottom
        start_lead_x, start_lead_y = start_gx, start_gy + lead_len

    if best_tgt_port == "left":
        end_lead_x, end_lead_y = end_gx - lead_len, end_gy
    elif best_tgt_port == "right":
        end_lead_x, end_lead_y = end_gx + lead_len, end_gy
    elif best_tgt_port == "top":
        end_lead_x, end_lead_y = end_gx, end_gy - lead_len
    else: # bottom
        end_lead_x, end_lead_y = end_gx, end_gy + lead_len

    start_c, start_r = to_grid(start_lead_x, start_lead_y)
    end_c, end_r = to_grid(end_lead_x, end_lead_y)

    # 3. A* Search
    pq = []
    # Push initial state: (f_score, g_score, c, r, dc, dr, path_history)
    heapq.heappush(pq, (0, 0, start_c, start_r, 0, 0, [(start_c, start_r)]))
    
    visited = {} # (c, r, dc, dr) -> g_score
    found_path = None
    bend_penalty = 15 # High penalty for bending
    
    while pq:
        f, g, c, r, dc, dr, path = heapq.heappop(pq)
        
        if (c, r) == (end_c, end_r):
            found_path = path
            break
            
        state_key = (c, r, dc, dr)
        if state_key in visited and visited[state_key] <= g:
            continue
        visited[state_key] = g
        
        # Explore neighbors
        for ndc, ndr in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nc, nr = c + ndc, r + ndr
            
            # Bounds check
            if nc < 0 or nc >= cols or nr < 0 or nr >= rows:
                continue
                
            # Obstacle check (allow target cell)
            if (nc, nr) in obstacles and (nc, nr) != (end_c, end_r):
                continue
                
            # Calculate cost
            step_cost = 1
            if (dc != 0 or dr != 0) and (ndc != dc or ndr != dr):
                step_cost += bend_penalty
                
            ng = g + step_cost
            nh = abs(nc - end_c) + abs(nr - end_r)
            nf = ng + nh
            
            nkey = (nc, nr, ndc, ndr)
            if nkey not in visited or ng < visited[nkey]:
                heapq.heappush(pq, (nf, ng, nc, nr, ndc, ndr, path + [(nc, nr)]))

    # If no path found, fallback to direct line
    if not found_path:
        path_d = f"M {start_gx} {start_gy} L {end_gx} {end_gy}"
        return {
            "path_d": path_d,
            "label_x": (start_gx + end_gx) / 2,
            "label_y": (start_gy + end_gy) / 2
        }

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
        end_seq = [(grid_end_gx, end_gy), (grid_end_gx, end_gy), (end_gx, end_gy)]
    else:
        end_seq = [(grid_end_gx, end_gy), (end_gx, grid_end_gy), (end_gx, end_gy)]
        
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
        "label_y": label_y
    }
