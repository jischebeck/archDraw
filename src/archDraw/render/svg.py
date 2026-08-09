import html
import re
from archDraw.core.elements import ArchElement, Node, Container
from archDraw.render.theme import DefaultTheme
from archDraw.render.text import TextRenderer
from archDraw.render.manhattan_routing import route_manhattan
from archDraw.render.grid_routing import route_grid

def embed_svg(svg_content: str, x: float, y: float, width: float, height: float) -> str:
    match = re.match(r'^<svg\b[^>]*>', svg_content)
    if match:
        opening_tag = match.group(0)
        viewbox_match = re.search(r'viewBox="[^"]*"', opening_tag)
        viewbox = viewbox_match.group(0) if viewbox_match else 'viewBox="0 0 512 512"'
        new_opening = f'<svg x="{x}" y="{y}" width="{width}" height="{height}" {viewbox}>'
        return new_opening + svg_content[len(opening_tag):]
    return svg_content

class SVGRenderer:
    """Generates the final SVG string from the laid-out IR."""
    def __init__(self, theme=None, routing="grid"):
        self.theme = theme or DefaultTheme()
        self.routing = routing

    def get_connection_endpoints(self, element: ArchElement) -> dict:
        """
        Returns potential connection endpoints for the element:
        - 'left': (x, y)
        - 'right': (x, y)
        - 'top': (x, y)
        - 'bottom': (x, y)
        """
        if isinstance(element, Node):
            params = self.theme.get_node_params(element)
            if params.get("is_icon"):
                icon_size = params.get("icon_size", 50)
                icon_x = element.x + (element.width - icon_size) / 2
                return {
                    "left": (icon_x, element.y + icon_size / 2),
                    "right": (icon_x + icon_size, element.y + icon_size / 2),
                    "top": (icon_x + icon_size / 2, element.y),
                    "bottom": (icon_x + icon_size / 2, element.y + icon_size)
                }
        
        return {
            "left": (element.x, element.y + element.height / 2),
            "right": (element.x + element.width, element.y + element.height / 2),
            "top": (element.x + element.width / 2, element.y),
            "bottom": (element.x + element.width / 2, element.y + element.height)
        }

    def get_node_size(self, node: Node) -> list[tuple[float, float]]:
        params = self.theme.get_node_params(node)
        base_width = params["width"]
        base_height = params["height"]
        
        wrapping_options = TextRenderer.get_wrapping_options(node.name)
        
        # Wrapped size: find the option with the fewest lines that fits within base_width
        # If none fit, fallback to the most wrapped option (last one)
        wrapped_lines = wrapping_options[-1]
        for opt in wrapping_options:
            opt_w = max(len(l) for l in opt) * 7.5
            if opt_w <= base_width:
                wrapped_lines = opt
                break
        
        # Unwrapped size: using the least wrapped option (first one)
        unwrapped_lines = wrapping_options[0]
        
        sizes = []
        for lines in [wrapped_lines, unwrapped_lines]:
            if params.get("is_icon"):
                subtitle = node.node_type.split("::")[-1] if "::" in node.node_type else ""
                sub_lines = [subtitle] if subtitle else []
                
                max_line_len = max([len(l) for l in lines] + [len(l) for l in sub_lines])
                w = max(base_width, max_line_len * 7.5)
                
                extra_lines = (len(lines) - 1) + len(sub_lines)
                h = base_height + extra_lines * 15
                sizes.append((w, h))
            else:
                max_line_len = max(len(l) for l in lines)
                w = max(base_width, max_line_len * 7.5)
                extra_lines = len(lines) - 1
                h = base_height + extra_lines * 15
                sizes.append((w, h))
                
        return sizes


    def get_container_borders(self, container: Container):
        params = self.theme.get_container_params(container)
        return (
            params["border_left"],
            params["border_right"],
            params["border_top"],
            params["border_bottom"]
        )

    def _render_element(self, element: ArchElement) -> str:
        if isinstance(element, Node):
            params = self.theme.get_node_params(element)
            
            if params.get("is_icon") and params.get("icon_svg"):
                icon_size = params["icon_size"]
                icon_x = element.x + (element.width - icon_size) / 2
                icon_y = element.y
                positioned_icon = embed_svg(params["icon_svg"], icon_x, icon_y, icon_size, icon_size)
                
                subtitle = element.node_type.split("::")[-1] if "::" in element.node_type else ""
                
                label_y = element.y + icon_size + 15
                
                # Determine how main title should wrap based on the allocated width
                lines = TextRenderer.choose_wrapping(element.name, element.width, element.height, char_width_factor=7.5)
                label_svg = TextRenderer.render_text(
                    element.name,
                    element.x + element.width / 2,
                    label_y,
                    element.width,
                    element.height,
                    params,
                    text_anchor="middle",
                    char_width_factor=7.5
                )
                
                subtitle_svg = ""
                if subtitle:
                    sub_y_start = label_y + len(lines) * 15
                    subtitle_svg = f"""
                    <text x="{element.x + element.width/2}" y="{sub_y_start}" 
                          font-family="sans-serif" font-size="10" fill="#70757A" 
                          font-weight="normal" text-anchor="middle">
                        <tspan x="{element.x + element.width/2}">{html.escape(subtitle)}</tspan>
                    </text>
                    """
                
                return f"""
                {positioned_icon}
                {label_svg}
                {subtitle_svg}
                """
            else:
                lines = TextRenderer.choose_wrapping(element.name, element.width, element.height, char_width_factor=7.5)
                start_y = element.y + element.height/2 + 5 - ((len(lines) - 1) * 7.5)
                
                label_svg = TextRenderer.render_text(
                    element.name,
                    element.x + element.width / 2,
                    start_y,
                    element.width,
                    element.height,
                    params,
                    text_anchor="middle",
                    char_width_factor=7.5
                )
                
                opacity_attr = f' opacity="{params["opacity"]}"' if params.get("opacity") and params["opacity"] != "1" else ""
                return f"""
                <rect x="{element.x}" y="{element.y}" width="{element.width}" height="{element.height}" 
                      fill="{params['fill_color']}" stroke="{params['stroke_color']}" stroke-width="{params['stroke_width']}" rx="{params['rx']}"{opacity_attr} />
                {label_svg}
                """
                
        elif isinstance(element, Container):
            params = self.theme.get_container_params(element)
            
            label_svg = TextRenderer.render_text(
                element.name,
                element.x + 15,
                element.y + 25,
                element.width - 30, # Account for left/right padding
                element.height,
                params,
                text_anchor="start",
                char_width_factor=10.0
            )
                
            children_svg = "".join([self._render_element(child) for child in element.children])
            stroke_dash = f'stroke-dasharray="{params["stroke_dasharray"]}"' if params.get("stroke_dasharray") else ""
            
            opacity_attr = f' opacity="{params["opacity"]}"' if params.get("opacity") and params["opacity"] != "1" else ""
            return f"""
            <rect x="{element.x}" y="{element.y}" width="{element.width}" height="{element.height}" 
                  fill="{params['fill_color']}" stroke="{params['stroke_color']}" stroke-width="{params['stroke_width']}" {stroke_dash} rx="{params['rx']}"{opacity_attr} />
            {label_svg}
            {children_svg}
            """

    def export(self, root: ArchElement, filename: str, connections=None):
        """Wraps the rendered elements in an SVG canvas and saves to disk."""
        svg_body = self._render_element(root)
        
        element_map = {}
        def find_elements(el: ArchElement):
            if hasattr(el, "alias") and el.alias:
                element_map[el.alias] = el
            element_map[el.name] = el
            for child in el.children:
                find_elements(child)
        find_elements(root)
        
        connection_svgs = []
        routed_points = set()
        if connections:
            def get_vertical_dist(c_val):
                s_el = element_map.get(c_val.source)
                t_el = element_map.get(c_val.target)
                if s_el and t_el:
                    return abs((s_el.y + s_el.height / 2) - (t_el.y + t_el.height / 2))
                return 999999
            sorted_connections = sorted(connections, key=get_vertical_dist)
            for conn in sorted_connections:
                src = element_map.get(conn.source)
                tgt = element_map.get(conn.target)
                if src and tgt:
                    src_pts = self.get_connection_endpoints(src)
                    tgt_pts = self.get_connection_endpoints(tgt)
                    if self.routing == "grid":
                        all_elements = list(set(element_map.values()))
                        route = route_grid(src, tgt, src_pts, tgt_pts, all_elements, routed_points)
                        if "grid_path" in route and route["grid_path"]:
                            routed_points.update(route["grid_path"])
                    else:
                        route = route_manhattan(src, tgt, src_pts, tgt_pts)
                    path_d = route["path_d"]
                    label_x = route["label_x"]
                    label_y = route["label_y"]
                    
                    label_svg = ""
                    if conn.label:
                        label_svg = f"""
                        <text x="{label_x}" y="{label_y - 5}" font-family="sans-serif" font-size="10" fill="#70757A" text-anchor="middle">
                            {html.escape(conn.label)}
                        </text>
                        """
                    
                    stroke_color = conn.attributes.get("color", "#70757A")
                    style_dash = 'stroke-dasharray="5,5"' if conn.attributes.get("style") == "dashed" else ""
                    
                    connection_svgs.append(f"""
                    <path d="{path_d}" fill="none"
                          stroke="{stroke_color}" stroke-width="2" marker-end="url(#arrow)" {style_dash} />
                    {label_svg}
                    """)
        
        connections_str = "\n".join(connection_svgs)
        canvas_width = root.width + 100
        canvas_height = root.height + 100
        
        final_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_width}" height="{canvas_height}">
            <defs>
                <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5"
                        markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                    <path d="M 0 1 L 10 5 L 0 9 z" fill="#70757A" />
                </marker>
            </defs>
            {svg_body}
            {connections_str}
        </svg>"""
        
        with open(filename, "w") as f:
            f.write(final_svg)