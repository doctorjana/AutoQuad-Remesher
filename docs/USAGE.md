# AutoQuad Remesher - User Guide

**AutoQuad Remesher** by Doctor Jana turns dense sculpts, 3D scan data, or triangular meshes into clean quad-dominant geometry in a single click.

---

## Clean Interface Overview

The interface is located in the 3D Viewport Sidebar (**N** key) under the **AutoQuad** tab.

- **Active Mesh Information:** Displays the active object name, current polygon count, and vertex count.
- **Remesh Button:** Executes the remeshing pipeline. While processing, the button changes to a loading indicator (`Remeshing in progress...`) with a wait cursor, returning to normal once finished.
- **Target Quads:** Sets the target quad count (range: 50 to 100,000, default: `2500`).
- **Adaptive Size:** Curvature adaptation factor ($0.0$ to $1.0$, default: `0.65`). Higher values allocate more polygons to high-curvature areas (bevels, tight corners) while preserving larger quads on flat areas.
- **Advanced Options > Hide Original Mesh (Enabled by default):** Automatically hides the original high-poly source mesh upon generation so that only the new, clean quad mesh remains visible in the viewport.

---

## Step-by-Step Workflow

1. Select your model in **Object Mode**.
2. Press **N** to reveal the sidebar and click **AutoQuad**.
3. Set your desired **Target Quads** (e.g. `1200` for low-poly/game models, `5000` for detailed sculpts).
4. Click **Remesh**.
5. The loading indicator displays while processing. Once finished, your new quad mesh (`<Name>_AutoQuad`) is automatically selected and shaded smooth, and the original mesh is hidden.
