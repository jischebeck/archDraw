import os
import re
from archDraw import Container, Node, LayoutEngine, SVGRenderer, export_png
from archDraw.render.text import TextRenderer

def test_core_architecture_layout():
    # 1. Build IR using Context Managers (identical to the basic_architecture example)
    with Container("Platform Architecture", layout="vertical") as root:
        with Container("Ingestion Layer", layout="horizontal") as ingestion:
            web = Node("Web Frontend")
            mobile = Node("Mobile Gateway")
            
        with Container("Processing Core", layout="horizontal") as processing:
            with Container("Stream Processing", layout="vertical") as stream:
                kafka = Node("Kafka Topic")
                flink = Node("Flink Job")
            
            with Container("Batch Processing", layout="vertical") as batch:
                airflow = Node("Airflow Scheduler")
                hadoop = Node("Hadoop Cluster")

    # 2. Assert hierarchical structure is set up correctly
    assert len(root.children) == 2
    assert ingestion in root.children
    assert processing in root.children
    assert len(ingestion.children) == 2
    assert len(processing.children) == 2

    # 3. Run Layout Engine
    LayoutEngine.calculate_bounds(root)
    LayoutEngine.apply_offset(root, dx=50, dy=50)

    # 4. Assert layout coordinates and bounds
    # Root container offsets
    assert root.x == 50
    assert root.y == 50
    assert root.width > 0
    assert root.height > 0

    # Ingestion Layer container bounds/positions
    assert ingestion.x >= root.x
    assert ingestion.y >= root.y
    assert web.x >= ingestion.x
    assert mobile.x > web.x  # layout="horizontal" means mobile should be to the right of web

    # Stream Processing container (layout="vertical")
    assert flink.y > kafka.y  # layout="vertical" means flink should be below kafka

    # 5. Export SVG to verify renderer works
    renderer = SVGRenderer()
    output_filename = "test_output.svg"
    output_png = "test_output.png"
    try:
        renderer.export(root, output_filename)
        assert os.path.exists(output_filename)
        # Verify the file has some content
        with open(output_filename, "r") as f:
            content = f.read()
            assert "<svg" in content
            assert "</svg>" in content
            assert "Platform Architecture" in content
            assert "Ingestion Layer" in content
            assert "Processing Core" in content
            assert "Web Frontend" in content

        # 6. Export PNG using export_png and verify it generates a file
        export_png(content, output_png)
        assert os.path.exists(output_png)
        assert os.path.getsize(output_png) > 0
    finally:
        if os.path.exists(output_filename):
            os.remove(output_filename)
        if os.path.exists(output_png):
            os.remove(output_png)

def test_child_boundaries_within_parents():
    # 1. Build IR using Context Managers (identical to the basic_architecture example)
    with Container("Platform Architecture", layout="vertical") as root:
        with Container("Ingestion Layer", layout="horizontal") as ingestion:
            web = Node("Web Frontend")
            mobile = Node("Mobile Gateway")
            
        with Container("Processing Core", layout="horizontal") as processing:
            with Container("Stream Processing", layout="vertical") as stream:
                kafka = Node("Kafka Topic")
                flink = Node("Flink Job")
            
            with Container("Batch Processing", layout="vertical") as batch:
                airflow = Node("Airflow Scheduler")
                hadoop = Node("Hadoop Cluster")

    # 2. Run Layout Engine
    LayoutEngine.calculate_bounds(root)
    LayoutEngine.apply_offset(root, dx=50, dy=50)

    # 3. Helper to recursively verify that children fit inside their parents
    def assert_contained(element):
        for child in element.children:
            # Child's left edge should be >= parent's left edge
            assert child.x >= element.x, f"Child '{child.name}' left edge ({child.x}) is outside parent '{element.name}' ({element.x})"
            # Child's top edge should be >= parent's top edge
            assert child.y >= element.y, f"Child '{child.name}' top edge ({child.y}) is outside parent '{element.name}' ({element.y})"
            # Child's right edge should be <= parent's right edge
            assert child.x + child.width <= element.x + element.width, f"Child '{child.name}' right edge ({child.x + child.width}) is outside parent '{element.name}' ({element.x + element.width})"
            # Child's bottom edge should be <= parent's bottom edge
            assert child.y + child.height <= element.y + element.height, f"Child '{child.name}' bottom edge ({child.y + child.height}) is outside parent '{element.name}' ({element.y + element.height})"
            
            # Recurse
            assert_contained(child)

    assert_contained(root)

def test_gcp_symbols_layout_and_size():
    # 1. Create a container with both GCP nodes and non-GCP nodes to test size/layout
    with Container("Platform", layout="vertical") as root:
        gcp_node1 = Node("CloudRun App 1", node_type="gcp::compute::CloudRun")
        gcp_node2 = Node("CloudRun App 2", node_type="gcp::compute::CloudRun")
        regular_node = Node("Regular App", node_type="service")

    # Run layout bounds calculation first
    LayoutEngine.calculate_bounds(root)

    # Verify GCP nodes have size 80x130 (wrapped), regular node has 140x60
    assert gcp_node1.width == 80
    assert gcp_node1.height == 130
    assert gcp_node2.width == 80
    assert gcp_node2.height == 130
    assert regular_node.width == 140
    assert regular_node.height == 75

    # Create a separate container solely containing GCP symbols to test horizontal forced distribution
    with Container("GCP Box", layout="vertical") as gcp_box:
        node_a = Node("GCS", node_type="gcp::storage::CloudStorage")
        node_b = Node("BigQuery", node_type="gcp::analytics::BigQuery")

    LayoutEngine.calculate_bounds(gcp_box)
    LayoutEngine.apply_offset(gcp_box, dx=10, dy=10)

    # Verify that the GCP Box layout was forced to horizontal (left-to-right)
    # node_b should be placed to the right of node_a
    assert node_b.x >= node_a.x + node_a.width
    assert node_b.y == node_a.y

def test_databricks_and_attributes():
    # Verify parsing attributes/tags and translating colors
    regular_node = Node("Web Server", node_type="service", attributes={"color": "red"})
    secure_node = Node("DB Server", node_type="service", attributes={"tags": "secure"})
    db_node = Node("Databricks Node", node_type="databricks::analytics")
    camel_node = Node("Camel Node", node_type="service", attributes={
        "fillColor": "#ffe0b2",
        "strokeColor": "#ff9800",
        "fontColor": "#e65100"
    })
    camel_container = Container("Camel Box", attributes={
        "fillColor": "#fff3e0",
        "strokeColor": "#ff9800",
        "fontColor": "#e65100"
    })

    renderer = SVGRenderer()
    
    # Verify color translation
    reg_params = renderer.theme.get_node_params(regular_node)
    assert reg_params["stroke_color"] == "red"

    # Verify tags translation
    sec_params = renderer.theme.get_node_params(secure_node)
    assert sec_params["stroke_color"] == "#E27218"
    assert sec_params["fill_color"] == "#FFF2E6"

    # Verify camelCase color translation for node
    camel_params = renderer.theme.get_node_params(camel_node)
    assert camel_params["fill_color"] == "#ffe0b2"
    assert camel_params["stroke_color"] == "#ff9800"
    assert camel_params["text_color"] == "#e65100"

    # Verify camelCase color translation for container
    camel_container_params = renderer.theme.get_container_params(camel_container)
    assert camel_container_params["fill_color"] == "#fff3e0"
    assert camel_container_params["stroke_color"] == "#ff9800"
    assert camel_container_params["text_color"] == "#e65100"

    # Verify Databricks icon size
    LayoutEngine.calculate_bounds(db_node, renderer)
    assert db_node.width == 80
    assert db_node.height == 115

    # Verify subtitle text width bounds calculation
    long_sub_node = Node("App", node_type="gcp::compute::ExtremelyLongSubTitleGoesHere")
    LayoutEngine.calculate_bounds(long_sub_node, renderer)
    assert long_sub_node.width >= 140

def test_container_min_bounds():
    # Long title container to force text width limit bounds
    long_title = "This is an extremely long container title designed to test minimum size constraints"
    with Container(long_title) as root:
        Node("Short Node")

    renderer = SVGRenderer()
    LayoutEngine.calculate_bounds(root, renderer)

    # borders are left=15, right=15, top=40, bottom=15 (sum=80)
    # The title wraps dynamically based on child width, the chosen wrapped title max line len is 14.
    expected_min_width = 190
    assert root.width >= expected_min_width

def test_connection_lines_export(tmp_path):
    from archDraw.parser import DSLConnection
    
    with Container("Platform") as root:
        a = Node("Node A")
        b = Node("Node B")
        
    renderer = SVGRenderer(routing="manhattan")
    LayoutEngine.calculate_bounds(root, renderer)
    LayoutEngine.apply_offset(root, dx=10, dy=10)
    
    conn = DSLConnection(source="Node A", target="Node B", arrow="->", label="calls")
    
    output_file = tmp_path / "test_conn.svg"
    renderer.export(root, str(output_file), connections=[conn])
    
    with open(output_file, "r") as f:
        svg_content = f.read()
        
    # Check that path coordinates and label are exported correctly
    assert "<path" in svg_content
    assert 'marker-end="url(#arrow)"' in svg_content
    assert "calls" in svg_content

    # Test icon connection coordinates
    with Container("Platform") as root2:
        gcp_a = Node("GCP Node A", node_type="gcp::compute::CloudRun")
        gcp_b = Node("GCP Node B", node_type="gcp::compute::CloudRun")
        
    LayoutEngine.calculate_bounds(root2, renderer)
    LayoutEngine.apply_offset(root2, dx=10, dy=10)
    
    conn2 = DSLConnection(source="GCP Node A", target="GCP Node B", arrow="->")
    output_file2 = tmp_path / "test_conn_icons.svg"
    renderer.export(root2, str(output_file2), connections=[conn2])
    
    with open(output_file2, "r") as f:
        svg_content2 = f.read()
        
    # Get the path attributes (we expect HVH path)
    match = re.search(r'<path d="M ([^ ]+) ([^ ]+) H [^ ]+ V ([^ ]+) H ([^ ]+)"', svg_content2)
    assert match
    x1 = float(match.group(1))
    y1 = float(match.group(2))
    y2 = float(match.group(3))
    x2 = float(match.group(4))
    
    # Visual icon center-left is x2 = icon_x. Since icon_size=60,
    # icon_x = gcp_b.x + (gcp_b.width - 60)/2
    expected_x2 = gcp_b.x + (gcp_b.width - 60) / 2
    assert abs(x2 - expected_x2) < 0.01
    
    expected_y2 = gcp_b.y + 30  # icon_size/2
    assert abs(y2 - expected_y2) < 0.01

def test_text_renderer_wrapping():
    # Test wrapping option partition
    opts = TextRenderer.get_wrapping_options("GCP Code Example")
    # Verify that the unwrapped option is first and has length 1
    assert opts[0] == ["GCP Code Example"]
    # Verify that multiple split variations are present
    assert ["GCP", "Code", "Example"] in opts
    assert ["GCP Code", "Example"] in opts
    
    # Test choose_wrapping based on target size
    # Width = 100, which is enough to fit "GCP Code" (8 chars * 7.5 = 60) or "Example" (7 chars * 7.5 = 52.5) but not full string (16 chars * 7.5 = 120)
    chosen = TextRenderer.choose_wrapping("GCP Code Example", target_width=100, target_height=50, char_width_factor=7.5)
    assert chosen == ["GCP Code", "Example"] or chosen == ["GCP", "Code Example"]

def test_child_scaling_in_container():
    # Verify child containers in a vertical stack scale up to matching width
    with Container("Stack", layout="vertical") as stack:
        with Container("Layer 1") as layer1:
            Node("Some Node")
        with Container("Longer Layer Name") as layer2:
            Node("Some Extremely Long Node Name")
        
    renderer = SVGRenderer()
    LayoutEngine.calculate_bounds(stack, renderer)
    assert layer1.width == layer2.width
    
    # Verify child containers in a horizontal stack scale up to matching height
    with Container("Stack2", layout="horizontal") as stack2:
        with Container("Layer 3") as layer3:
            Node("Some Node")
        with Container("Longer Layer Name 2") as layer4:
            Node("Some Extremely Long Node Name 2")
        
    LayoutEngine.calculate_bounds(stack2, renderer)
    assert layer3.height == layer4.height

def test_grid_routing(tmp_path):
    from archDraw.parser import DSLConnection
    
    with Container("Platform") as root:
        a = Node("Node A")
        b = Node("Node B")
        
    renderer = SVGRenderer(routing="grid")
    LayoutEngine.calculate_bounds(root, renderer)
    LayoutEngine.apply_offset(root, dx=10, dy=10)
    
    conn = DSLConnection(source="Node A", target="Node B", arrow="->")
    output_file = tmp_path / "test_grid_conn.svg"
    renderer.export(root, str(output_file), connections=[conn])
    
    with open(output_file, "r") as f:
        svg_content = f.read()
        
    assert "<path" in svg_content
    assert " L " in svg_content

def test_validate_and_enclose():
    with Container("Parent") as parent:
        with Container("Child") as child:
            Node("Node A")
            
    renderer = SVGRenderer()
    LayoutEngine.calculate_bounds(parent, renderer)
    LayoutEngine.apply_offset(parent, dx=10, dy=10)
    
    # Manually force child outside of parent boundaries
    child.x = parent.x + parent.width + 10
    
    # Run validation loop
    LayoutEngine.validate_and_enclose(parent)
    
    # Parent must be expanded to enclose child
    assert parent.x + parent.width >= child.x + child.width + 15




