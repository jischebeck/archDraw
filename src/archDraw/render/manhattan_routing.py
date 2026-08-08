from archDraw.core.elements import ArchElement

def route_manhattan(src: ArchElement, tgt: ArchElement, src_pts: dict, tgt_pts: dict) -> dict:
    """
    Computes orthogonal (Manhattan) route between source and target elements.
    Returns a dictionary with:
    - 'path_d': SVG path data (d attribute)
    - 'label_x': X coordinate for placing a connection label
    - 'label_y': Y coordinate for placing a connection label
    """
    # Compute center points
    cx1 = src.x + src.width / 2
    cy1 = src.y + src.height / 2
    cx2 = tgt.x + tgt.width / 2
    cy2 = tgt.y + tgt.height / 2

    dx = cx2 - cx1
    dy = cy2 - cy1

    # Choose ports based on relative direction
    if abs(dx) >= abs(dy):
        # Horizontal-Vertical-Horizontal (HVH)
        if dx >= 0:
            start_x, start_y = src_pts["right"]
            end_x, end_y = tgt_pts["left"]
        else:
            start_x, start_y = src_pts["left"]
            end_x, end_y = tgt_pts["right"]
        
        mid_x = (start_x + end_x) / 2
        path_d = f"M {start_x} {start_y} H {mid_x} V {end_y} H {end_x}"
        
        # Label at center of vertical segment
        label_x = mid_x
        label_y = (start_y + end_y) / 2
    else:
        # Vertical-Horizontal-Vertical (VHV)
        if dy >= 0:
            start_x, start_y = src_pts["bottom"]
            end_x, end_y = tgt_pts["top"]
        else:
            start_x, start_y = src_pts["top"]
            end_x, end_y = tgt_pts["bottom"]
            
        mid_y = (start_y + end_y) / 2
        path_d = f"M {start_x} {start_y} V {mid_y} H {end_x} V {end_y}"
        
        # Label at center of horizontal segment
        label_x = (start_x + end_x) / 2
        label_y = mid_y

    return {
        "path_d": path_d,
        "label_x": label_x,
        "label_y": label_y
    }
