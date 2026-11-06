# Changelog

All notable changes to the AutoQuad Remesher extension are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-11-06

### Added
- **Optimal Quads Auto-Detection (Zero Guesswork):**
  - Added an `Optimal Quads (Auto)` toggle directly above Target Quads in the main sidebar panel.
  - Automatically analyzes the active 3D mesh's geometric complexity, integrating:
    - Dihedral edge curvature & angular turning energy
    - Sharp crease and boundary feature edge lengths
    - Ratio of curved surface area vs flat planar surfaces
    - Bounding dimensions and characteristic scale
  - Automatically calculates and applies the mathematically ideal polygon budget that preserves all curvature, features, and silhouettes without faceting or distortion.
  - When enabled, greys out the manual integer slider and dynamically displays the estimated optimal count.

## [1.2.5] - 2026-11-06

### Changed
- **Removed Floating Numeric Cursor Progress (`25.00`):**
  - Removed Blender's legacy `window_manager.progress_update(25)` calls from the remesh operator.
  - In Blender, `wm.progress_update()` renders an awkward floating numeric value (e.g. `25.00`) directly next to the cursor tip. Because QuadriFlow calculates in a single atomic C++ step, this value remained frozen at `25.00` during the entire remeshing process.
  - The cursor now remains a clean precision reticle (`'CROSSHAIR'`) without numerical clutter, while progress is indicated natively via the sidebar animated spinner and the bottom status bar (`AutoQuad: Remeshing quad topology in progress...`).

## [1.2.4] - 2026-11-06

### Added
- **Non-Destructive Decimate Option in Advanced Options:**
  - Added a `Decimate Mesh` toggle under Advanced Options (disabled by default).
  - Non-destructively applies a Decimate modifier to the internal working guide mesh prior to remeshing, while preserving the user's original object, modifiers, and high-resolution geometry completely untouched.
  - Supports both **Collapse** (default ratio `0.1` / 10% remaining) and **Un-Subdivide** (customizable iteration rollback) modes.
  - Automatically falls back to Collapse if Un-Subdivide is chosen on irregular, non-grid geometry.
  - Guarantees full sculpt fidelity: the original high-resolution un-decimated mesh BVH is preserved, allowing the surface projection engine to snap the newly generated quad vertices back to the exact high-detail surface.

## [1.2.3] - 2026-11-06

### Fixed
- **Ultra-Dense Sculpt Remeshing (500k+ Polygons):** Resolved `AutoQuad: Failed to generate quad geometry` on meshes with ~500,000+ polygons. QuadriFlow's integer linear system solver chokes and runs out of memory or hits matrix singularities when forced to process hundreds of thousands of micro-triangles directly. Added intelligent dense-mesh guide conditioning that decimate-conditions working geometry above 70,000 polygons to ~65,000 faces while retaining the full 500k-polygon BVH (`src_bvh`) for surface reprojection. All high-frequency surface sculpt details and silhouettes are 100% preserved.
- **Self-Healing Multi-Stage Solver Recovery:** Implemented a multi-pass automatic fallback pipeline when QuadriFlow returns cancelled or errors:
  1. Primary remesh with boundary preservation.
  2. Boundary-relaxed retry (`use_preserve_boundary=False`) for complex or self-intersecting boundary loops.
  3. Automated manifold repair and normal equalization pass.
  4. Adaptive decimate-conditioning pass for remaining micro-crevices.
  5. Watertight boundary sealing fallback pass.
- **Pre-Clean Topological Defect Sanitizer:** Added thorough removal of isolated wire edges (0 link faces), loose unattached vertices, zero-area sliver faces ($< 10^{-7}$), and duplicate faces before QuadriFlow validation. Prevents Blender's internal `mesh_is_manifold_consistent` check from immediately canceling execution.

## [1.2.2] - 2026-11-05

### Changed
- **Modernized Loading Feedback & Cursor Experience:**
  - Replaced the generic operating system `'WAIT'` spinning donut/hourglass cursor with Blender's precision modeling reticle cursor (`'CROSSHAIR'`), avoiding the appearance of a frozen or unresponsive application while retaining clean visual interactivity.
  - Upgraded the dynamic UI loading indicator in the 3D Viewport sidebar from the static `'TIME'` icon to Blender's animated `'PREVIEW_LOADING'` spinner icon.
  - Added native Blender Status Bar integration: updates the bottom status bar with `AutoQuad: Remeshing quad topology in progress...` during calculation and restores it cleanly upon completion.

## [1.2.1] - 2026-11-05

### Fixed
- **Duplicate Faces & Multi-Face Non-Manifold Edges on Dense Meshes:** Fixed an issue where hole filling and triangulation on high-vertex-count meshes created overlapping duplicate faces (causing edges to have 3 or 4 faces). This previously caused QuadriFlow to cancel with `The mesh needs to be manifold and have face normals that point in a consistent direction`, triggering an unintended slow Python fallback. Added automated post-hole duplicate face and interior multi-face edge pruning.
- **High-Valence Singularities on Dense Hole Loops:** Dense holes (>16 boundary vertices) are now triangulated with high-regularity beauty triangulation instead of high-valence 100-spoke center pokes that caused QuadriFlow field singularities and spiraling.
- **Arbitrary Mesh & Offset Origin Inflation:** Fixed sagitta curvature inflation in `make_manifold` so it uses local boundary centroids and average boundary radii instead of projecting toward the global origin `(0, 0, 0)`, preventing distortions on off-center or non-spherical sculpts.
- **Surface Relaxation Normal Alignment Guard:** In `SurfaceRelaxationEngine`, added a surface normal alignment check (`vert.normal.dot(normal) > 0.05`) during BVH snapping. Prevents vertices on high-density meshes from snapping across thin walls to back-facing surfaces (e.g. ears, eyelids, lips, clothing folds).
- **Pre-Remesh Geometry Sanitizer:** Added duplicate face and non-manifold multi-face edge stripping in the core retopology engine prior to invoking QuadriFlow, guaranteeing that dense sculpts remesh in seconds.

## [1.2.0] - 2026-11-05

### Fixed
- **Curvature-Preserving Hole Filling:** Fixed issue where deleting faces from a curved surface (such as a sphere) followed by Make Manifold created a flat, sunken chord facet of razor-thin sliver triangles that distorted remeshed geometry. Now intelligently pokes N-gons, subdivides radial edges, and inflates/smooths interior vertices outward along boundary normals to match the surrounding curvature and volume.
- **Open Boundary Preservation:** "Make Mesh Manifold" and "Preprocess Mesh" now preserve intentional open boundaries by default (`fill_holes=False`). Open surfaces (e.g. cut spheres, eye sockets, hollow domes, clothing) are now cleaned of true non-manifold defects (loose vertices/edges, interior faces, duplicates, degenerate elements) without destroying intentional openings.
- **Tangential Boundary Relaxation:** Fixed boundary shrinkage in `SurfaceRelaxationEngine` on open meshes by using tangential boundary smoothing instead of chord midpoint averaging, preventing boundary loops from puckering or shrinking inward during relaxation.

### Added
- **Seal Boundary Holes Toggle:** Added an explicit toggle in both the "Make Mesh Manifold" operator redo panel and under "Preprocess Mesh" in the UI allowing users to choose whether to keep open boundaries intact or seal them with curvature reconstruction.

## [1.1.0] - 2026-11-04

### Changed
- Rebranded extension name to **AutoQuad Remesher**.
- Updated author and maintainer to **Doctor Jana** (`https://github.com/doctorjana`).
- Linked official GitHub Pages site: `https://doctorjana.github.io/autoquad_remesher/`.
- Drastically streamlined UI: removed all unnecessary clutter to provide a clean, distraction-free workflow.
- Removed symmetry options completely.
- Removed edge flow and curvature parameters from the UI.
- Removed in-viewport overlays and interactive overlay toggles.

### Added
- **Make Mesh Manifold (Standalone Testing Button):** Added a dedicated "Make Mesh Manifold" button under Advanced Options allowing users to test, inspect, and run the 3D-Print Toolbox manifold repair routine directly on the active mesh object.
- **Preprocess Mesh (Make Manifold):** Integrated the official Make Manifold repair algorithm from Blender's 3D-Print Toolbox (`object_print3d_utils`) under Advanced Options. Automatically deletes loose/interior elements, merges duplicate vertices, dissolves degenerate elements, fills boundary holes, and ensures consistent outward normals before remeshing.
- **Visual Loading Indicator:** When **Remesh** is clicked, a dynamic loading state (`Remeshing in progress...` with icon and wait cursor) is shown and clears automatically once the mesh generation completes.
- **Hide Original Mesh:** Added an option under Advanced Options (enabled by default) that automatically hides the source object upon successful remeshing.

## [1.0.0] - 2026-11-04

### Added
- Initial modular extension architecture for Blender 4.2+.
- Full BMesh discrete differential geometry patch engine.
- Headless automated regression and registration test suite.
