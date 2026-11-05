# Changelog

All notable changes to the AutoQuad Remesher extension are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
