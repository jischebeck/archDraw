# archDraw

A dual-interface architecture diagramming tool.

## Installation

To install `archDraw` along with its dependencies:

```bash
pip install .
```

To install in editable mode for development:

```bash
pip install -e .
```

## Command Line Interface (CLI)

Once installed, you can use the `archdraw` command to compile DSL input files (`.archDraw`) into SVG or PNG diagrams.

### Basic Usage

Generate an SVG diagram (default):
```bash
archdraw examples/pipeline.archDraw
```
This generates `examples/pipeline.svg`.

### Specifying Output Path & Format

Compile to a custom PNG output:
```bash
archdraw examples/pipeline.archDraw -o output.png
```

Compile to a custom SVG output:
```bash
archdraw examples/pipeline.archDraw -o output.svg
```

Force a specific format (`svg` or `png`):
```bash
archdraw examples/pipeline.archDraw -o custom_file -f png
```

### Specifying Diagram Padding

Set custom canvas padding borders (default: 50):
```bash
archdraw examples/pipeline.archDraw -p 100 -o output.png
```

### CLI Help Options

To list all available arguments and flags:
```bash
archdraw --help
```
