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
        
        # Automatically attach to parent context
        parent = get_current_parent()
        if parent is not None:
            parent.children.append(self)

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