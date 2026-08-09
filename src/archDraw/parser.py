from textx import metamodel_from_str
from archDraw.core.elements import Node, Container

GRAMMAR = r"""
Model:
    'architecture' name=STRING '{'
        body*=ModelBodyElement
    '}'
;

ModelBodyElement:
    Directive | Element
;

Element:
    Container | Node | Connection
;

Container:
    type=ContainerType name=STRING ('as' alias=ID)? (attributes=Attributes)? '{'
        body*=ContainerBodyElement
    '}'
;

ContainerType:
    'box' | 'stack' | 'layer'
;

ContainerBodyElement:
    Directive | Element
;

Directive:
    name=ID ':' value=DirectiveValue
;

DirectiveValue:
    /[a-zA-Z0-9_-]+/
;

Node:
    type=NodeType name=STRING ('as' alias=ID)? (attributes=Attributes)?
;

NodeType:
    /[a-zA-Z_][a-zA-Z0-9_]*(::[a-zA-Z_][a-zA-Z0-9_]*)*/
;

Connection:
    source=ID arrow=ArrowType target=ID (':' label=STRING)? (attributes=Attributes)?
;

ArrowType:
    '-->' | '->' | '<->' | '<=>' | '==>' | '=>' | '~>'
;

Attributes:
    '[' attrs+=Attribute[','] ']'
;

Attribute:
    name=AttributeName '=' value=STRING
;

AttributeName:
    /[a-zA-Z_][a-zA-Z0-9_-]*/
;

Comment:
    /\/\/.*$/ | /\/\*[\s\S]*?\*\//
;
"""

class DSLConnection:
    def __init__(self, source: str, target: str, arrow: str, label: str = None, attributes: dict = None):
        self.source = source
        self.target = target
        self.arrow = arrow
        self.label = label
        self.attributes = attributes or {}

    def __repr__(self):
        return f"DSLConnection({self.source} {self.arrow} {self.target}, label={self.label}, attrs={self.attributes})"

def parse_dsl(dsl_content: str):
    """
    Parses DSL content and returns a tree of Container/Node objects and a list of DSLConnection objects.
    """
    # Create textX metamodel
    meta = metamodel_from_str(GRAMMAR, ignore_case=False)
    
    model = meta.model_from_str(dsl_content)
    
    connections = []
    symbol_table = {}

    def build_element(el, parent_container=None):
        if el.__class__.__name__ == 'Container':
            # Extract attributes
            attrs = {}
            if hasattr(el, 'attributes') and el.attributes:
                for attr in el.attributes.attrs:
                    attrs[attr.name] = attr.value

            # Create a Container
            layout_val = 'vertical'
            spacing_val = None
            alignment_val = None
            
            # Look for directives inside container body
            for item in el.body:
                if item.__class__.__name__ == 'Directive':
                    if item.name == 'layout':
                        if item.value in ('vertical', 'horizontal'):
                            layout_val = item.value
                    elif item.name == 'direction':
                        if item.value in ('left-right', 'right-left'):
                            layout_val = 'horizontal'
                        elif item.value in ('top-down', 'bottom-up'):
                            layout_val = 'vertical'
                    elif item.name in ('spacing', 'gap'):
                        spacing_val = int(item.value)
                    elif item.name in ('alignment', 'align'):
                        alignment_val = item.value

            # Extract from attributes
            if "spacing" in attrs:
                spacing_val = int(attrs["spacing"])
            elif "gap" in attrs:
                spacing_val = int(attrs["gap"])
            if "alignment" in attrs:
                alignment_val = attrs["alignment"]
            elif "align" in attrs:
                alignment_val = attrs["align"]

            # Create the Container instance
            container = Container(el.name, layout=layout_val, attributes=attrs, container_type=el.type)
            if spacing_val is not None:
                container.gap = spacing_val
            if alignment_val is not None:
                container.alignment = alignment_val
            else:
                container.alignment = 'left'

            
            # Register in symbol table if alias is provided
            alias = el.alias if el.alias else el.name
            container.alias = alias
            symbol_table[alias] = container
            
            if parent_container:
                parent_container.children.append(container)
            
            # Recurse container body
            for item in el.body:
                if item.__class__.__name__ in ('Container', 'Node', 'Connection'):
                    build_element(item, container)
                    
            return container

        elif el.__class__.__name__ == 'Node':
            # Extract attributes
            attrs = {}
            if hasattr(el, 'attributes') and el.attributes:
                for attr in el.attributes.attrs:
                    attrs[attr.name] = attr.value

            # Create a Node
            node = Node(el.name, node_type=el.type, attributes=attrs)
            alias = el.alias if el.alias else el.name
            node.alias = alias
            symbol_table[alias] = node
            
            if parent_container:
                parent_container.children.append(node)
            return node

        elif el.__class__.__name__ == 'Connection':
            attrs = {}
            if el.attributes:
                for attr in el.attributes.attrs:
                    attrs[attr.name] = attr.value
            
            conn = DSLConnection(
                source=el.source,
                target=el.target,
                arrow=el.arrow,
                label=el.label,
                attributes=attrs
            )
            connections.append(conn)
            return None

    # The root architecture block contains the elements. We represent it as a root Container.
    layout_val = 'vertical'
    spacing_val = None
    alignment_val = None
    for item in model.body:
        if item.__class__.__name__ == 'Directive':
            if item.name == 'layout':
                if item.value in ('vertical', 'horizontal'):
                    layout_val = item.value
            elif item.name == 'direction':
                if item.value in ('left-right', 'right-left'):
                    layout_val = 'horizontal'
                elif item.value in ('top-down', 'bottom-up'):
                    layout_val = 'vertical'
            elif item.name in ('spacing', 'gap'):
                spacing_val = int(item.value)
            elif item.name in ('alignment', 'align'):
                alignment_val = item.value

    root_container = Container(model.name, layout=layout_val)
    if spacing_val is not None:
        root_container.gap = spacing_val
    if alignment_val is not None:
        root_container.alignment = alignment_val
    else:
        root_container.alignment = 'left'
    
    # Process elements of the model
    for item in model.body:
        if item.__class__.__name__ in ('Container', 'Node', 'Connection'):
            build_element(item, root_container)

    return root_container, connections

def parse_dsl_file(filepath: str):
    """
    Parses archDraw DSL file and returns the root Container and a list of DSLConnection objects.
    """
    with open(filepath, "r") as f:
        content = f.read()
    return parse_dsl(content)
