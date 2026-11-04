# QuadFlow Retopology - User Guide

QuadFlow Retopology turns dense sculpts, scan data, CAD imports, or triangular meshes into clean quad-dominant geometry.

---

## Quick Start

1. Select your target mesh in **Object Mode**.
2. Press **N** in the 3D Viewport to display the Sidebar.
3. Switch to the **QuadFlow** tab.
4. Set your **Target Quads** count (e.g. `2500`).
5. Choose an operation mode:
   - Click **One-Click Quad Remesh** for instant generation.
   - Click **Interactive Viewport Retopology** for live GPU-guided feedback.

---

## Operating Modes

### 1. One-Click Quad Remesh
Executes the full pipeline automatically and adds a new quad mesh object (`<ObjectName>_QuadFlow`) with smooth shading applied:
- Checks for hard creases and curvature alignment.
- Generates regularized quad topology.
- Applies topological mirror symmetry if enabled.
- Runs orthogonal Laplacian relaxation with high-poly BVH surface reprojection.

### 2. Interactive Viewport Retopology
Runs an interactive viewport session with real-time GPU feedback:
- **3D Cross-Field Vectors:** Displays cyan and orange needles indicating the principal 4-RoSy directions along surface curvature.
- **Top-Left HUD:** Displays phase, target quad budget, and iteration counters.
- **Keybindings during Interactive Session:**
  - `[Space]`: Toggle real-time auto-relaxation iterations.
  - `[Mouse Wheel Up / Down]`: Dynamically increase or decrease target quad density.
  - `[Enter]`: Commit and generate the final quad mesh.
  - `[Esc]`: Cancel the session without modifying the scene.

---

## Settings Reference

### Polygon Density
- **Target Quads:** Nominal number of quad polygons for the resulting mesh (50 to 100,000).
- **Adaptive Size:** Sizing variation factor ($0.0$ to $1.0$). At $0.0$, edge lengths are uniform. Higher values concentrate higher polygon density in high-curvature crevices, bevels, and detailed regions while maintaining larger quads on flat areas.
- **Density Group:** Optional vertex group name. Vertex painting from $0.0$ to $1.0$ scales local density from $0.25\times$ (large quads) to $4.0\times$ (dense quads).

### Edge Flow & Curvature
- **Curvature Flow:** Weight given to natural surface curvature vectors versus uniform grid layout.
- **Detect Hard Edges:** Automatically detects sharp surface creases and forces quad edge loops to align along them.
- **Crease Angle:** Dihedral angle threshold ($15^\circ$ to $90^\circ$, default $45^\circ$) for classifying an edge as sharp.
- **Use Marked Creases:** Preserves edges explicitly marked as Sharp or Seam in Blender Edit Mode.
- **Material Boundaries:** Aligns quad boundaries with different material assignments.
- **Guide Curves:** Optional collection of curve strokes to manually direct edge loop flow.

### Symmetry
- **Symmetry:** Enforces strict topological mirror symmetry.
- **Symmetry Axis:** Reflection plane (`X-Axis`, `Y-Axis`, or `Z-Axis`). Centerline vertices are clamped strictly to $0.0$, and positive/negative halves share identical topology with zero duplicate seam vertices.

### In-Viewport Overlays
- **Show 4-RoSy Vectors:** Toggles GPU cross-needle drawing during interactive sessions.
- **Show Flow Loops:** Toggles planned streamline preview.
- **Relaxation Steps:** Number of Laplacian smoothing and surface reprojection passes ($1$ to $50$, default $12$).
