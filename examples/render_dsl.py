import os
from archDraw import parse_dsl_file, LayoutEngine, SVGRenderer, export_png

def main():
    dsl_file = os.path.join(os.path.dirname(__file__), "pipeline.archDraw")
    print(f"Parsing DSL file: {dsl_file}...")
    root, connections = parse_dsl_file(dsl_file)

    print("Calculating Layout...")
    renderer = SVGRenderer()
    LayoutEngine.calculate_bounds(root, renderer)
    LayoutEngine.apply_offset(root, dx=50, dy=50)

    print("Exporting SVG...")
    svg_filename = "pipeline_output.svg"
    renderer.export(root, svg_filename, connections)
    print(f"Done. SVG output saved to '{svg_filename}'")

    print("Exporting PNG...")
    with open(svg_filename, "r") as f:
        svg_content = f.read()
    png_filename = "pipeline_output.png"
    export_png(svg_content, png_filename)
    print(f"Done. PNG output saved to '{png_filename}'")

if __name__ == "__main__":
    main()
