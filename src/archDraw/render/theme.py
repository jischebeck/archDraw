from archDraw.core.elements import Node, Container

def get_icon(node_type: str) -> str:
    # Extract the service part, e.g. "CloudRun" from "gcp::compute::CloudRun"
    # or "analytics" from "databricks::analytics"
    parts = node_type.split("::")
    service = parts[-1].lower()
    
    try:
        from archDraw.assets.gcp_icons import ICONS as GCP_ICONS
    except ImportError:
        GCP_ICONS = {}

    try:
        from archDraw.assets.databricks_icons import ICONS as DATABRICKS_ICONS
    except ImportError:
        DATABRICKS_ICONS = {}
        
    if service in GCP_ICONS:
        return GCP_ICONS[service]
    if service in DATABRICKS_ICONS:
        return DATABRICKS_ICONS[service]
        
    for key in GCP_ICONS.keys():
        normalized_key = key.replace("gcp::", "").split("::")[-1].lower()
        if normalized_key.startswith(service) or service.startswith(normalized_key):
            return GCP_ICONS[key]

    for key in DATABRICKS_ICONS.keys():
        normalized_key = key.replace("databricks::", "").split("::")[-1].lower()
        if normalized_key.startswith(service) or service.startswith(normalized_key):
            return DATABRICKS_ICONS[key]
            
    return None

class DefaultTheme:
    """Strategy pattern for defining architecture diagram theme style parameters."""
    
    def get_node_params(self, node: Node) -> dict:
        params = {
            "width": 140,
            "height": 60,
            "fill_color": "#E8F0FE",
            "stroke_color": "#1A73E8",
            "stroke_width": 2,
            "rx": 6,
            "text_color": "#1A73E8",
            "text_size": 14,
            "font_weight": "bold",
            "is_icon": False,
            "icon_svg": None,
            "icon_size": 60
        }
        
        icon_svg = get_icon(node.node_type)
        if icon_svg:
            params.update({
                "width": 80,
                "height": 85,
                "is_icon": True,
                "icon_svg": icon_svg,
                "icon_size": 60,
                "text_size": 12,
                "text_color": "#3C4043"
            })
            
        # Semantic rendering: translate attributes/tags
        attrs = node.attributes

        # Stroke / border color: "color" or "border_color"
        if "color" in attrs:
            params["stroke_color"] = attrs["color"]
        if "border_color" in attrs:
            params["stroke_color"] = attrs["border_color"]

        # Fill color: "fill" or "fill_color"
        if "fill" in attrs:
            params["fill_color"] = attrs["fill"]
        if "fill_color" in attrs:
            params["fill_color"] = attrs["fill_color"]

        # Text color
        if "text_color" in attrs:
            params["text_color"] = attrs["text_color"]

        # Opacity
        if "opacity" in attrs:
            params["opacity"] = attrs["opacity"]
            
        # Special tags
        if "secure" in node.tags:
            params["stroke_color"] = "#E27218"
            params["fill_color"] = "#FFF2E6"
            
        return params

    def get_container_params(self, container: Container) -> dict:
        params = {
            "border_left": 15,
            "border_right": 15,
            "border_top": 40,
            "border_bottom": 15,
            "fill_color": "#F8F9FA",
            "stroke_color": "#5F6368",
            "stroke_width": 2,
            "stroke_dasharray": "6,4",
            "rx": 8,
            "text_color": "#3C4043",
            "text_size": 16,
            "font_weight": "bold",
            "opacity": "1"
        }
        
        attrs = container.attributes

        # Stroke / border color: "color" or "border_color"
        if "color" in attrs:
            params["stroke_color"] = attrs["color"]
        if "border_color" in attrs:
            params["stroke_color"] = attrs["border_color"]

        # Fill color: "fill" or "fill_color"
        if "fill" in attrs:
            params["fill_color"] = attrs["fill"]
        if "fill_color" in attrs:
            params["fill_color"] = attrs["fill_color"]

        # Text color
        if "text_color" in attrs:
            params["text_color"] = attrs["text_color"]

        # Opacity (0.0 – 1.0)
        if "opacity" in attrs:
            params["opacity"] = attrs["opacity"]

        # Border style override: "solid" removes dasharray, "dashed"/"dotted" set it
        if "border_style" in attrs:
            style = attrs["border_style"]
            if style == "solid":
                params["stroke_dasharray"] = ""
            elif style == "dashed":
                params["stroke_dasharray"] = "6,4"
            elif style == "dotted":
                params["stroke_dasharray"] = "2,3"

        # Border width
        if "border_width" in attrs:
            try:
                params["stroke_width"] = float(attrs["border_width"])
            except ValueError:
                pass

        return params