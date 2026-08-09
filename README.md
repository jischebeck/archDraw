# archDraw

A dual-interface architecture diagramming tool for generating clean, auto-laid-out architecture diagrams from a declarative DSL or a Python API.

![Version](https://img.shields.io/badge/version-0.2.0-blue)
![Python](https://img.shields.io/badge/python-%3E%3D3.8-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## What is archDraw?

archDraw lets you describe infrastructure diagrams in plain text and generates pixel-perfect SVG or PNG diagrams automatically. It handles layout, spacing, and orthogonal connection routing — no manual positioning needed.

- **Declarative DSL**: Write architecture diagrams as readable text files (`.archDraw`).
- **Python API**: Build diagrams programmatically using context managers and a fluent builder API.
- **Auto-layout**: Container sizing, child positioning, and connection routing are computed automatically.
- **Orthogonal routing**: Connections use A* pathfinding to avoid overlapping diagram elements.
- **Cloud provider icons**: Built-in GCP component library with official icons and colors.
- **Dual output**: SVG (vector, scalable) and PNG (raster, via `pyvips`).

---

## Why another text-to-diagram tool?

Traditional tools like **Mermaid** and **PlantUML** are fantastic for sequence diagrams, flowcharts, or simple graphs, but they are not optimized for IT architecture drawings. When building architectural maps, you typically want nested containers (like VPCs, subnets, layers, and stacks) to fill out the page in an optimal, rigid, and balanced way without overlapping or routing lines in chaotic, unreadable directions.

**archDraw** was specifically designed to:
- Enforce strict hierarchical grid layout structures (horizontal columns, vertical layers, and stacks).
- Keep connection routing clean and strictly orthogonal (VHV/HVH), avoiding the messy diagonal crossings common in graphviz-based engines.
- Ensure nested containers auto-size and stretch dynamically to align boundaries and maximize page space.

---

## Interactive Demo

A live HTML showcase of all examples is available at [doc/demo.html](doc/demo/demo.html).

---

## Installation

### Quick install (from GitHub)

```bash
pip install git+https://github.com/jischebeck/archDraw.git
```

### Install with test dependencies

```bash
pip install "git+https://github.com/jischebeck/archDraw.git#[dev]"
```

### From source (development)

Clone the repo and install in editable mode:

```bash
git clone https://github.com/jischebeck/archDraw.git
cd archDraw
pip install -e .
```

### PNG export dependency

For PNG output, `pyvips` requires the `libvips` system library:

```bash
# Ubuntu / Debian
sudo apt-get install libvips-dev

# macOS (Homebrew)
brew install vips
```

---

## Quick Start

Generate a diagram from the included example:

```bash
archdraw examples/pipeline.archDraw
# → generates examples/pipeline.svg
```

Open `examples/pipeline.svg` in a browser to view the result.

---

## Command Line Interface

### Basic usage

```bash
archdraw <input.archDraw>
```

### Options

| Flag | Description |
|---|---|
| `-o, --output <path>` | Output file path (SVG or PNG). If omitted, `<input>.svg` is used. |
| `-f, --format <svg\|png>` | Force output format (inferred from extension if omitted). |
| `-p, --padding <px>` | Canvas padding around the diagram (default: `50`). |
| `--grid` | Use grid-based obstacle-avoiding routing (default). |
| `--manhattan` | Use Manhattan (obstacle-ignoring) routing. |
| `-v, --version` | Print version and exit. |

### Examples

```bash
# Output SVG to a custom path
archdraw examples/pipeline.archDraw -o output.svg

# Output PNG
archdraw examples/pipeline.archDraw -o output.png

# Custom padding
archdraw examples/pipeline.archDraw -p 100 -o output.svg

# Force format from a `.txt` extension
archdraw examples/pipeline.archDraw -o output -f svg

# Help
archdraw --help
```

---

## DSL Syntax Reference

archDraw uses a declarative language called **ArchDSL**. Here's a quick overview:

### Structural Containers

```dsl
box "My Container" as alias {
    layout: horizontal       # or: vertical, grid
    direction: left-right    # or: top-down, bottom-up, right-left

    component "Service A" as svc_a
    component "Service B" as svc_b
}
```

### Supported Containers

| Directive | Purpose |
|---|---|
| `box` | Generic container with auto-sizing |
| `stack` | Strict vertical or horizontal partition |
| `layer` | Full-width/height partition inside a `stack` |

### Supported Node Types

`component`, `service`, `database`, `storage`, `queue`, `node`, `actor`

### Styling

```dsl
component "Auth" as auth [fill_color="#FFF2E6", border_color="#E27218", text_color="#333"]
```

Available style attributes: `fill_color`, `border_color`, `text_color`, `opacity`, `border_style` (`solid` | `dashed` | `dotted`), `border_width`, `fill` (alias), `color` (alias for border).

### Connections

```dsl
svc_a -> svc_b : "API Call"
svc_b => database : "Data Flow" [weight="bold"]
svc_a --> svc_c : "Async" [color="red", style="dashed"]
```

Connection types: `->` (control flow), `-->` (async), `=>` (data flow), `~>` (stream), `<->` (bidirectional).

### GCP Cloud Components

```dsl
gcp::compute::CloudRun "API Service" as api
gcp::analytics::BigQuery "Data Warehouse" as bq
gcp::storage::CloudStorage "Data Lake" as gcs
```

See [doc/ArchDSL_Specification.md](doc/ArchDSL_Specification.md) for the full DSL reference, all GCP services, and comprehensive examples.

---

## Python API

Build diagrams programmatically using a context-manager-based API:

```python
from archDraw import Node, Container, LayoutEngine, SVGRenderer, DefaultTheme

root = Container("My Architecture")
root.theme = DefaultTheme()
root.direction = "left-right"

svc_a = Node("Service A", shape="component")
svc_b = Node("Service B", shape="service")
db = Node("PostgreSQL", shape="database")

root.add(svc_a, svc_b, db)

# Layout
renderer = SVGRenderer(routing="grid")
LayoutEngine.calculate_bounds(root, renderer)
LayoutEngine.apply_offset(root, dx=50, dy=50)
LayoutEngine.validate_and_enclose(root)

# Export
renderer.export(root, "output.svg")
```

See `examples/basic_architecture.py` for a full working example.

---

## Examples

| Example | DSL File | Output |
|---|---|---|
| Pipeline Architecture | [pipeline.archDraw](examples/pipeline.archDraw) | [pipeline.svg](examples/pipeline.svg) |
| Capabilities Map | [capabilities_map.archDraw](examples/capabilities_map.archDraw) | [capabilities_map.svg](doc/demo/capabilities_map.svg) |
| Target Architecture | [target_dataarchitecture_map.archDraw](examples/target_dataarchitecture_map.archDraw) | [target_dataarchitecture_map.svg](examples/target_dataarchitecture_map.svg) |

---

## Testing

```bash
pytest
```

Visual regression tests use `pytest-snapshot` to compare SVG/PNG output against baselines.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

---

## License

MIT License. See [LICENSE](LICENSE).

---

## Contributors

- **Gemini / Antigravity**
- **Qwen / Pi**
