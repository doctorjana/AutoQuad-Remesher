# Changelog

All notable changes to the AutoQuad Remesher extension are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- **Preprocess Mesh (Make Manifold):** Integrated the official Make Manifold repair algorithm from Blender's 3D-Print Toolbox (`object_print3d_utils`) under Advanced Options. Automatically deletes loose/interior elements, merges duplicate vertices, dissolves degenerate elements, fills boundary holes, and ensures consistent outward normals before remeshing.
- **Visual Loading Indicator:** When **Remesh** is clicked, a dynamic loading state (`Remeshing in progress...` with icon and wait cursor) is shown and clears automatically once the mesh generation completes.
- **Hide Original Mesh:** Added an option under Advanced Options (enabled by default) that automatically hides the source object upon successful remeshing.

## [1.0.0] - 2026-11-04

### Added
- Initial modular extension architecture for Blender 4.2+.
- Full BMesh discrete differential geometry patch engine.
- Headless automated regression and registration test suite.
