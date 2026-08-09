import pyvips

def export_png(svg_content: str, output_path: str):
    """Converts an SVG string into a pixel-perfect PNG using pyvips entirely in-memory."""
    # Load the SVG content from buffer
    image = pyvips.Image.new_from_buffer(svg_content.encode("utf-8"), "")
    # Write the resulting image to the specified output path
    image.write_to_file(output_path)
