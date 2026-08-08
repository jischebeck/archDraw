import math
from archDraw.core.elements import ArchElement

def route_manhattan(src: ArchElement, tgt: ArchElement, src_pts: dict, tgt_pts: dict) -> dict:
    """
    Computes orthogonal (Manhattan) route between source and target elements
    using the absolute shortest distance port pair among all 16 port combinations.
    """
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

    start_x, start_y = src_pts[best_src_port]
    end_x, end_y = tgt_pts[best_tgt_port]

    if best_src_port in ("left", "right") and best_tgt_port in ("left", "right"):
        # Horizontal-Vertical-Horizontal (HVH)
        mid_x = (start_x + end_x) / 2
        path_d = f"M {start_x} {start_y} H {mid_x} V {end_y} H {end_x}"
        label_x = mid_x
        label_y = (start_y + end_y) / 2
    elif best_src_port in ("top", "bottom") and best_tgt_port in ("top", "bottom"):
        # Vertical-Horizontal-Vertical (VHV)
        mid_y = (start_y + end_y) / 2
        path_d = f"M {start_x} {start_y} V {mid_y} H {end_x} V {end_y}"
        label_x = (start_x + end_x) / 2
        label_y = mid_y
    elif best_src_port in ("left", "right") and best_tgt_port in ("top", "bottom"):
        # Horizontal-Vertical (HV)
        path_d = f"M {start_x} {start_y} H {end_x} V {end_y}"
        label_x = end_x
        label_y = start_y
    else:
        # Vertical-Horizontal (VH)
        path_d = f"M {start_x} {start_y} V {end_y} H {end_x}"
        label_x = start_x
        label_y = end_y

    return {
        "path_d": path_d,
        "label_x": label_x,
        "label_y": label_y
    }
