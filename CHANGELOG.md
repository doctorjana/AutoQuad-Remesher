# Changelog

All notable changes to the AutoQuad Remesher extension are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.7] - 2026-11-07

### Added
- **Automatic Scale Normalization for Metric / Sub-Meter Meshes:**
  - Resolved QuadriFlow C++ solver numerical underflow on real-world sub-meter meshes (e.g. human anatomy, medical CT scans, teeth, jewelry, and 3D photogrammetry).
  - QuadriFlow's native C++ solver uses hardcoded absolute geometric singularity tolerances ($\sim 10^{-4}$). In meshes modeled at real-world scale (e.g. 5cm to 15cm skull bones), micro-edges and suture margins triggered false `QUADRIFLOW_STATUS_NONMANIFOLD` rejections.
  - AutoQuad now dynamically normalizes sub-meter meshes ($d_{\max} < 0.5\text{m}$) into standard numerical space ($\sim 2.0$ units) before invoking QuadriFlow, and precisely transforms the resulting quad geometry back into true world space coordinates.
  - Verified on complex real-world `skull.obj` scan: achieved a 100% success rate across all 54 disconnected components (0 dropped parts, 12,883 quads, 100.0% clean regular quad topology in 18.66s).

## [1.3.6] - 2026-11-07

### Added
- **Generator-Driven Asynchronous Modal State Machine:**
  - Implemented `run_retopology_steps()` generator in `core/retopology_engine.py` yielding discrete execution states (`INITIALIZING`, `REMESHING_PART`, `COMBINING`, `FINISHED`).
  - Refactored `VIEW3D_OT_autoquad_remesh` modal operator into an asynchronous event loop state machine advancing on 0.02s (~50Hz) timer ticks.
  - Blender's main event loop now smoothly processes interface redrawing, cursor animations, and viewport repainting between parts and stages without freezing or triggering Windows "Application Not Responding".
- **Interactive User Cancellation:**
  - Added real-time cancellation via `ESC` key during active remeshing.
  - Automatically restores mouse cursor, clears status indicators, and purges any active worker objects without leaving leftover geometry.
- **Enhanced UI Feedback:**
  - Added live percentage and stage progress in both the sidebar panel and the workspace bottom status bar (`context.workspace.status_text_set`).
  - Added cancellation hint (`Press ESC to cancel`) in the sidebar loading box.

## [1.3.5] - 2026-11-06

### Added
- **Optimal Count Quality Multiplier (`Quality`):**
  - Added a dedicated `Quality` multiplier slider in the sidebar panel directly under `Optimal Quads (Auto)`.
  - Multiplies the auto-detected optimal quad count (default: `1.0x`, soft range: `0.25x` to `4.0x`, hard range: `0.1x` to `10.0x`).
  - Seamlessly scales polygon budgets: set `Quality` to `2.0` for 2x denser quads (ideal for high-frequency sculpts/wrinkles) or `0.5` for lightweight real-time / game-ready meshes.
  - Dynamically updates the displayed optimal target count in real time in the UI as the slider is adjusted.
  - Fully integrated with multi-part loose parts remeshing: scales both single-mesh and multi-component budgets proportionately across all parts while maintaining relative curvature and scale weighting.

## [1.3.4] - 2026-11-06

### Added
- **Per-Part Tailored Optimal Quad Budgets (Surface Area & Curvature Weighting):**
  - Integrated `calculate_multi_part_budgets()` and `calculate_component_curvature_complexity()` in `core/adaptive_density.py`.
  - When remeshing meshes partitioned into loose parts, AutoQuad now calculates distinct, geometrically tailored quad budgets for every individual component based on its unique surface area, dihedral turning energy, and feature curvature complexity factor $K$.
  - Solved the issue where scale-invariance caused small details (e.g. 0.2m rivets, eyes, or buttons) and large surfaces (e.g. 4.0m torso or walls) to receive nearly identical quad budgets.
  - Tiny/secondary parts now receive appropriate compact budgets (e.g. 60–150 quads) while large/curved components receive higher quad allocations (e.g. 2,000–4,000 quads), maintaining a harmonious, consistent quad edge length across the entire combined model.
  - Real-time progress updates now explicitly show the separate quad budget for each part: `Remeshing part {i}/{N} ({polys} polys -> {budget} quads)...`.

## [1.3.3] - 2026-11-06

### Fixed
- **Duplicate Face & Overlapping Geometry Protection:**
  - Added duplicate/degenerate face handling in `core/retopology_engine.py`.
  - Calling `bm.faces.new(...)` on meshes with duplicate faces, double-sided polygons, or inverted shared loops previously raised `ValueError: faces.new(...): face already exists`.
  - Added pre-partitioning defect sanitization with `sanitize_working_mesh(src_bm, merge_dist=1e-7)` to automatically prune duplicate faces, degenerate edges, zero-area polygons, and loose wire elements.
  - Wrapped all BMesh face creation operations in `try...except ValueError: pass` with `len(set(verts)) >= 3` validation to guarantee immunity against duplicate/collapsed faces.

## [1.3.2] - 2026-11-06

### Fixed
- **In-Memory Loose Parts Partitioning (Zero Split Parts & Source Preservation):**
  - Replaced native `mesh.separate(type='LOOSE')` in Edit mode with pure in-memory connected component BFS partitioning.
  - Calling `mesh.separate(type='LOOSE')` in Edit mode previously engaged Blender's multi-object editing if the source object was selected, which destructively fractured the original mesh into scene objects and left un-remeshed split parts in the user's outliner.
  - Now, the input mesh is partitioned into topological islands purely in BMesh memory without touching the user's object or switching modes.
  - Each loose component is remeshed sequentially via an ephemeral worker object that is immediately freed upon completion.
  - All remeshed quad components are recombined purely in memory into a single unified quad mesh (`{obj.name}_AutoQuad`).
  - **Guarantees:**
    1. Every single loose part is remeshed into clean quads.
    2. Zero split parts remain in the outliner or 3D viewport.
    3. The user's original object is 100% preserved and untouched.

## [1.3.1] - 2026-11-06

### Added
- **Remesh by Loose Parts (Connected Component Partitioning):**
  - Added a `Remesh by Loose Parts` toggle under Advanced Options (enabled by default).
  - Internally partitions any input mesh containing multiple disconnected islands / shells into isolated components using Blender's native C++ connected-component algorithm (`face_sets_create(mode='LOOSE_PARTS')` / `mesh.separate(type='LOOSE')`).
  - Resolves cross-shell topology distortion, mesh entanglement, and snapping errors (e.g., characters with separated eyeballs, teeth, armor plates, clothing layers, or multi-part CAD assemblies).
  - Remeshes each loose component independently with its own isolated BVH tree, preventing field cross-talk and cross-boundary vertex snapping.
  - Dynamically calculates polygon budgets per component:
    - If `Optimal Quads (Auto)` is enabled, calculates the exact curvature-energy budget individually per loose component.
    - If manual target quads is used, distributes the budget proportionally based on each component's relative surface area.
  - Automatically joins all cleanly remeshed quad parts back into a single unified object with preserved transforms, world positioning, and smooth shading.

### Changed
- **Dynamic Step-by-Step Progress & Loading Status:**
  - Real-time updates during multi-part remeshing:
    - Status bar displays: `AutoQuad: Remeshing loose part {i}/{N} ({polys} polys)...`
    - Sidebar animated loading box dynamically shows: `Remeshing part {i}/{N}...`
  - Clean automatic cleanup of processing state and status bar upon completion or cancellation.

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
