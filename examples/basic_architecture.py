# Assuming your PYTHONPATH is set to the src/ directory
from archDraw import Container, Node, LayoutEngine, SVGRenderer, export_png

def main():
    print("Building Architecture IR...")

    # 1. Build IR using Context Managers
    with Container("Platform Architecture", layout="vertical") as root:
        with Container("Ingestion Layer", layout="horizontal"):
            Node("Web Frontend")
            Node("Mobile Gateway")
            
        with Container("Processing Core", layout="horizontal"):
            with Container("Stream Processing", layout="vertical"):
                Node("Kafka Topic")
                Node("Flink Job")
            
            with Container("Batch Processing", layout="vertical"):
                Node("Airflow Scheduler")
                Node("Hadoop Cluster")

    # 2. Run Layout Engine
    print("Calculating Layout...")
    LayoutEngine.calculate_bounds(root)
    LayoutEngine.apply_offset(root, dx=50, dy=50)

    # 3. Export SVG
    print("Exporting SVG...")
    renderer = SVGRenderer()
    renderer.export(root, "output.svg")
    print("Done. Output saved to 'output.svg'")

    # 4. Export PNG
    print("Exporting PNG...")
    with open("output.svg", "r") as f:
        svg_content = f.read()
    export_png(svg_content, "output.png")
    print("Done. Output saved to 'output.png'")

if __name__ == "__main__":
    main()