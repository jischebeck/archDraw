# Clean exposure of the library's primary components
__version__ = "0.1.0"

from .core.elements import Node, Container
from .layout.engine import LayoutEngine
from .render.svg import SVGRenderer
from .render.theme import DefaultTheme
from .render.export import export_png
from .parser import parse_dsl, parse_dsl_file

__all__ = ["__version__", "Node", "Container", "LayoutEngine", "SVGRenderer", "DefaultTheme", "export_png", "parse_dsl", "parse_dsl_file"]