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
        if "color" in node.attributes:
            params["stroke_color"] = node.attributes["color"]
        if "fill" in node.attributes:
            params["fill_color"] = node.attributes["fill"]
            
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
            "font_weight": "bold"
        }
        
        if "color" in container.attributes:
            params["stroke_color"] = container.attributes["color"]
        if "fill" in container.attributes:
            params["fill_color"] = container.attributes["fill"]
            
        return params