Here is the finalized file structure and detailed architecture description for **archDraw**, incorporating all of your decisions.

---

### 1. Project File Structure

We will use a modern Python `src/` layout. This ensures the package is properly isolated during testing and prevents import path confusion.

```text
archDraw/
├── pyproject.toml               # Build config (deps: textX, pyvips, pytest, pytest-snapshot)
├── README.md                    # Project documentation
├── src/
│   └── archDraw/
│       ├── __init__.py          # Exposes the main Python API (with statements, Elements)
│       ├── cli.py               # CLI entrypoint (e.g., `archDraw build map.dsl`)
│       ├── exceptions.py        # Custom domain errors and textX exception wrappers
│       ├── parser.py            # textX grammar definition and AST compilation
│       ├── core/                # Core Intermediate Representation (IR)
│       │   ├── __init__.py
│       │   ├── elements.py      # Base Element, Node, and Container classes (Composite Pattern)
│       │   └── context.py       # Thread-local Context Manager stack for the Python API
│       ├── layout/              # Mathematical layout algorithms
│       │   ├── __init__.py
│       │   ├── engine.py        # Bottom-up bounding-box calculation logic
│       │   └── routing.py       # A* grid pathfinding for orthogonal edge routing
│       ├── render/              # Output generation
│       │   ├── __init__.py
│       │   ├── theme.py         # Strategy pattern for styles, colors, and fonts
│       │   ├── svg.py           # Maps coordinates and themes into raw SVG strings
│       │   └── export.py        # SVG to PNG conversion using pyvips
│       └── assets/              # Standard Library
│           ├── __init__.py
│           └── gcp_icons.py     # Pre-compiled dictionary mapping component names to SVG strings
└── tests/
    ├── __init__.py
    ├── conftest.py              # Pytest fixtures and snapshot configurations
    ├── test_parser.py           # Tests textX text-to-AST translation
    ├── test_layout.py           # Mathematical tests for container scaling
    ├── test_routing.py          # A* pathfinding edge cases (e.g., routing around obstacles)
    ├── test_visuals.py          # Visual regression tests using pytest-snapshot
    └── snapshots/               # Auto-generated image baseline files for visual diffing

```

---

### 2. Architecture Description

**Overview:**
archDraw is a dual-interface architecture diagramming tool. It functions as both a standalone CLI that parses a domain-specific text language (`.dsl`), and as a native Python library providing an object-oriented builder API. The engine translates structural constraints (boxes, stacks) into strict visual bounding coordinates, routes connections, and outputs deterministic SVG and PNG graphics.

**Stage 1: Input & Parsing Pipeline**
The engine supports two input vectors that converge into a single Abstract Syntax Tree (AST):

1. **Python API:** Uses Python Context Managers (`with` blocks) interacting with a thread-local `RenderContext`. This pushes and pops containers to a stack, building the tree programmatically.
2. **Text DSL:** Uses the `textX` meta-language engine. The raw text is parsed against a defined grammar.
*Error Handling:* If `textX` encounters a syntax error, the exception is caught in `exceptions.py` and wrapped into a human-readable `archDrawSyntaxError`, abstracting the compiler logic away from the end-user.

**Stage 2: Intermediate Representation (IR)**
Both input methods generate instances from the `core.elements` module. This module implements the **Composite Design Pattern**. `Node` (leaf) and `Container` (branch) share an `Element` interface. The IR holds semantic relationships (who is inside whom, who connects to whom) but possesses no spatial awareness at this stage.

**Stage 3: The Layout Engine (The Math)**
The `layout.engine` processes the IR in a two-pass algorithm:

1. **Bottom-Up Pass:** Calculates the intrinsic dimensions of inner elements and expands parent boxes to wrap around them perfectly, factoring in padding and grid directives.
2. **Top-Down Pass:** Applies global X/Y offsets, shifting every child relative to the final calculated position of its parent.
Following box layout, `layout.routing` applies a **Grid-based A* (A-Star) algorithm**. The canvas is mapped to a coarse grid; populated boxes are marked as obstacles, and the algorithm routes connections strictly along free grid cells to create neat, non-overlapping 90-degree orthogonal lines.

**Stage 4: Rendering & Theming**
To adhere to the Open-Closed Principle, structural coordinates are strictly separated from visual styling via the **Strategy Pattern**. The `render.svg` module loops through the positioned IR and passes elements to a `Theme` object. The `Theme` object injects standard styling and retrieves official GCP component vectors from the `assets.gcp_icons` compiled string module.

**Stage 5: Export**
The generated SVG string is passed to `pyvips`, a fast image processing library. `pyvips` generates a pixel-perfect PNG entirely in-memory using libvips.

---

### 3. Record of Architectural Decisions (ADR)

Here is the formal list of design decisions we made to reach this architecture:

1. **Dual Input Modes (Context Managers & textX):** * *Decision:* Support both native Python code via `with` statement blocks and a standalone text file parser.
* *Rationale:* Satisfies both developers who want to generate diagrams programmatically and architects who prefer writing clean, declarative markup text.


2. **In-House Layout Engine:**
* *Decision:* Build the bounding-box and routing algorithms natively in Python rather than relying on Graphviz or ELK.
* *Rationale:* Grants complete control over the rigid "boxes-within-boxes" aesthetic that traditional force-directed graph engines struggle with.


3. **A* Pathfinding for Edge Routing:**
* *Decision:* Implement orthogonal edge routing using A* pathfinding over a virtual grid.
* *Rationale:* Prevents arrows from unreadably slicing through diagram components, ensuring clean, right-angled paths between aliases.


4. **Separation of Concerns (Theme Pattern):**
* *Decision:* Decouple layout coordinates from visual styling using a `Theme` object and `RenderContext`.
* *Rationale:* Enables effortless addition of future themes (e.g., Dark Mode) or different render targets (e.g., Draw.io XML) without altering core logic.


5. **Visual Regression Testing:**
* *Decision:* Use `pytest-snapshot` for CI testing.
* *Rationale:* Validating complex 2D geometric layouts via standard code assertions is highly brittle. Comparing baseline SVG/PNG outputs ensures the layout algorithms don't visually regress.


6. **Asset Management via Compiled Module:**
* *Decision:* Convert the standard library SVGs (GCP icons) into Python strings within `gcp_icons.py`.
* *Rationale:* Removes the need for file I/O operations at runtime and solves package-data path resolution issues, making the library easier to distribute via PyPI.


7. **Scope Containment for MVP Assets:**
* *Decision:* Restrict custom external icons for the initial release; support only the built-in GCP Standard Library.
* *Rationale:* Reduces edge cases related to local file path resolution and mixed SVG viewbox scaling, accelerating the MVP timeline.


8. **Error Wrapping:**
* *Decision:* Implement a custom wrapper for `textX` exceptions.
* *Rationale:* Dramatically improves Developer Experience (DX) by providing domain-contextual error messages rather than raw parser stack traces.


9. **Rasterization Engine:**
* *Decision:* Adopt `pyvips` for SVG-to-PNG conversion.
* *Rationale:* Provides fast, spec-compliant rasterization using libvips, bypassing the need for heavy external dependencies like Playwright/Chromium.