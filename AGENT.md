# Agent Validation & Contribution Guide

This document contains instructions for agents working on `archDraw` to validate their code changes, understand the repository structure, use utility scripts, and follow best practices.

For detailed design specs and algorithmic mechanics, see:
- [**Architecture & Design Specification**](file:///home/jan/Projects/archDraw/doc/spec.md)
- [**Layout & Routing Algorithm Specifications**](file:///home/jan/Projects/archDraw/doc/layout_algorithm.md)

---

## 1. Repository Structure

The `archDraw` codebase is organized as follows:
- [**`doc/`**](doc/): Architecture spec, DSL definitions, layout algorithm document, and showcase gallery.
- [**`src/archDraw/`**](src/archDraw/): Core source code.
  - [**`core/`**](src/archDraw/core/): AST representation and DSL parsing logic (lexer/parser).
  - [**`layout/`**](src/archDraw/layout/): Geometric calculations, gap resolver, and alignment engines.
  - [**`render/`**](src/archDraw/render/): SVG generation, theme styles, text-wrapping, and routing pathfinders.
- [**`tests/`**](tests/): Test suite containing parser and layout unit tests.

- [**`examples/`**](examples/): Reference `.archDraw` files and their compiled SVGs.
- [**`scripts/`**](scripts/): Development and automation utilities.

---

## 2. Utility Scripts

### A. Updating the Demo & Showcase (`update_demo`)
Whenever you update code that changes diagram layout, rendering, or parsing, regenerate the SVGs and demo webpage showcase:
```bash
# Run via wrapper
./scripts/update_demo
# Or run python script directly
.venv/bin/python scripts/update_demo.py
```
This recompiles all examples into SVGs and generates the gallery showcase at [`doc/demo.html`](doc/demo.html).

### B. Versioning & Changelog Bumping (`update_version.py`)
To bump the project version, update `pyproject.toml`, `__init__.py`, update `CHANGELOG.md`, and commit/tag the version bump automatically:
```bash
.venv/bin/python scripts/update_version.py <version> "[Changelog commit message]"
```
Example: `.venv/bin/python scripts/update_version.py 0.3.0 "Added alignment threshold heuristics"`

---

## 3. Best Practices for Efficiency & Testing

- **Write Minimal Code**: Focus on target layout engines or styles. Do not write complex overrides if they can be handled by adjusting existing gap passes or base geometry properties.
- **Create Minimal Test Cases**: When adding new functionality, write high-fidelity tests that isolate the feature using tiny inputs (1-2 nodes) rather than complete large diagrams. Check [`tests/test_layout.py`](tests/test_layout.py) for examples.
- **Run the Suite Regularly**: Always verify changes do not regress previous layout calculations by running `pytest`:
  ```bash
  .venv/bin/pytest
  ```

---

## 4. Automated CLI Debug Checks

When testing layout or routing modifications, you can run the `archdraw` command with the `--debug` flag. This will generate the output diagram and execute the QA debug checks (enclosure, overlaps, orthogonality, bends, and port blockages):

```bash
.venv/bin/python -m archDraw.cli examples/metadata_map.archDraw -o examples/metadata_map.svg --debug
```

### Checks Performed

1. **Node Enclosure Check**: Validates that all children lie strictly within the bounding boxes of their parent containers.
2. **Sibling Overlap Check**: Ensures no two siblings of the same parent intersect or overlap each other.
3. **Line Orthogonality Check**: Scans all path points to confirm that segments are strictly horizontal or vertical (detecting non-orthogonal segments or rounding wiggles).
4. **Bend Count Alert**: Alerts if any path has more than 2 bends, indicating potentially sub-optimal connection routing.
5. **Blocked Port Warning**: Analyzes exit/entry port cells for each connection, warning if the connection's paths are heavily blocked by layout obstacles.
