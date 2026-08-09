from .context import get_current_parent, _context

class ArchElement:
    """Base class for all architectural elements (IR)."""
    def __init__(self, name: str, attributes: dict = None):
        self.name = name
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.children = []
        self.attributes = attributes or {}
        self.tags = [t.strip() for t in self.attributes.get("tags", "").split(",") if t.strip()]
        self.alias = name
        
        # Parse CSS margins and paddings
        self.margin_left = self._parse_pixel(self.attributes.get("margin-left", self.attributes.get("marginLeft", 0)))
        self.margin_right = self._parse_pixel(self.attributes.get("margin-right", self.attributes.get("marginRight", 0)))
        self.margin_top = self._parse_pixel(self.attributes.get("margin-top", self.attributes.get("marginTop", 0)))
        self.margin_bottom = self._parse_pixel(self.attributes.get("margin-bottom", self.attributes.get("marginBottom", 0)))
        
        self.padding_left = self._parse_pixel(self.attributes.get("padding-left", self.attributes.get("paddingLeft", 0)))
        self.padding_right = self._parse_pixel(self.attributes.get("padding-right", self.attributes.get("paddingRight", 0)))
        self.padding_top = self._parse_pixel(self.attributes.get("padding-top", self.attributes.get("paddingTop", 0)))
        self.padding_bottom = self._parse_pixel(self.attributes.get("padding-bottom", self.attributes.get("paddingBottom", 0)))
        
        if "margin" in self.attributes:
            self._parse_shorthand_margin(self.attributes["margin"])
        if "padding" in self.attributes:
            self._parse_shorthand_padding(self.attributes["padding"])
            
        # Tracking flags for Auto-Alignment solver overrides
        self.has_explicit_margin_left = any(x in self.attributes for x in ("margin-left", "marginLeft", "margin"))
        self.has_explicit_margin_top = any(x in self.attributes for x in ("margin-top", "marginTop", "margin"))
        self.has_explicit_padding = any(x in self.attributes for x in ("padding", "padding-left", "padding-right", "padding-top", "padding-bottom", "paddingLeft", "paddingRight", "paddingTop", "paddingBottom"))

        # Automatically attach to parent context
        parent = get_current_parent()
        if parent is not None:
            parent.children.append(self)

    def _parse_pixel(self, val):
        if val is None:
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).strip().replace("px", "")
        try:
            return float(val_str)
        except ValueError:
            return 0.0

    def _parse_shorthand_margin(self, val):
        parts = [self._parse_pixel(p) for p in str(val).strip().split()]
        if len(parts) == 1:
            self.margin_top = self.margin_bottom = self.margin_left = self.margin_right = parts[0]
        elif len(parts) == 2:
            self.margin_top = self.margin_bottom = parts[0]
            self.margin_left = self.margin_right = parts[1]
        elif len(parts) == 3:
            self.margin_top = parts[0]
            self.margin_left = self.margin_right = parts[1]
            self.margin_bottom = parts[2]
        elif len(parts) >= 4:
            self.margin_top = parts[0]
            self.margin_right = parts[1]
            self.margin_bottom = parts[2]
            self.margin_left = parts[3]

    def _parse_shorthand_padding(self, val):
        parts = [self._parse_pixel(p) for p in str(val).strip().split()]
        if len(parts) == 1:
            self.padding_top = self.padding_bottom = self.padding_left = self.padding_right = parts[0]
        elif len(parts) == 2:
            self.padding_top = self.padding_bottom = parts[0]
            self.padding_left = self.padding_right = parts[1]
        elif len(parts) == 3:
            self.padding_top = parts[0]
            self.padding_left = self.padding_right = parts[1]
            self.padding_bottom = parts[2]
        elif len(parts) >= 4:
            self.padding_top = parts[0]
            self.padding_right = parts[1]
            self.padding_bottom = parts[2]
            self.padding_left = parts[3]

class Node(ArchElement):
    """A leaf element (e.g., Service, Database)."""
    def __init__(self, name: str, node_type: str = "default", attributes: dict = None):
        super().__init__(name, attributes)
        self.node_type = node_type

class Container(ArchElement):
    """A container (Box, Stack, Layer) that holds other elements."""
    def __init__(self, name: str, layout: str = "vertical", attributes: dict = None, container_type: str = "container"):
        super().__init__(name, attributes)
        self.layout = layout
        self.padding = 20
        self.title_height = 30
        self.gap = 15
        
        attrs = attributes or {}
        if "spacing" in attrs:
            self.gap = int(attrs["spacing"])
        elif "gap" in attrs:
            self.gap = int(attrs["gap"])
            
        self.alignment = attrs.get("alignment", attrs.get("align", "left"))
        self.container_type = container_type


    def __enter__(self):
        """Pushes this container onto the context stack."""
        if not hasattr(_context, 'stack'):
            _context.stack = []
        _context.stack.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Pops this container off the context stack."""
        _context.stack.pop()