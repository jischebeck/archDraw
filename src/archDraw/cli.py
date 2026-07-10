import argparse
import sys
import os
import html
from archDraw import parse_dsl_file, LayoutEngine, SVGRenderer, export_png

def main():
    parser = argparse.ArgumentParser(description="archDraw CLI - Generate architecture diagrams from DSL.")
    parser.add_argument("input", help="Path to the archDraw DSL file (.archDraw)")
    parser.add_argument("-o", "--output", help="Path to the output image file (SVG or PNG)")
    parser.add_argument("-f", "--format", choices=["svg", "png"], help="Output format (svg or png). If not specified, inferred from output file extension.")
    parser.add_argument("-p", "--padding", type=int, default=50, help="Border padding around the diagram (default: 50)")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # Parse DSL
    try:
        print(f"Parsing DSL: {args.input}...")
        root, connections = parse_dsl_file(args.input)
    except Exception as e:
        print(f"Error parsing DSL: {e}", file=sys.stderr)
        sys.exit(1)

    # Layout bounds
    print("Calculating layout dimensions...")
    renderer = SVGRenderer()
    LayoutEngine.calculate_bounds(root, renderer)
    LayoutEngine.apply_offset(root, dx=args.padding, dy=args.padding)

    # Determine output format and path
    output_path = args.output
    out_format = args.format

    if not output_path:
        base, _ = os.path.splitext(args.input)
        if out_format:
            output_path = f"{base}.{out_format}"
        else:
            output_path = f"{base}.svg"
            out_format = "svg"

    if not out_format:
        _, ext = os.path.splitext(output_path)
        out_format = ext.lower().replace(".", "")
        if out_format not in ("svg", "png"):
            print(f"Warning: Could not infer format from output extension '{ext}'. Defaulting to SVG.", file=sys.stderr)
            out_format = "svg"

    # Export
    print(f"Exporting to {out_format.upper()}: {output_path}...")
    try:
        if out_format == "svg":
            renderer.export(root, output_path, connections)
        elif out_format == "png":
            temp_svg = output_path + ".tmp.svg"
            renderer.export(root, temp_svg, connections)
            with open(temp_svg, "r") as f:
                svg_content = f.read()
            export_png(svg_content, output_path)
            if os.path.exists(temp_svg):
                os.remove(temp_svg)
        print("Done successfully.")
    except Exception as e:
        print(f"Error exporting diagram: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
