# QuadFlow Retopology

[![Blender](https://img.shields.io/badge/Blender-4.2%20%7C%205.0%20%7C%205.2%2B-orange.svg)](https://www.blender.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-green.svg)]()
[![Manifest Validated](https://img.shields.io/badge/Extension%20Manifest-Passed-success.svg)]()

**QuadFlow Retopology** is a professional, open-source automatic quad remeshing extension for **Blender 4.2 LTS and newer** (including Blender 5.0 and 5.2+). It converts dense sculpts, photogrammetry 3D scans, CAD imports, or non-uniform triangular meshes into clean, production-ready quad geometry.

---

## Key Features

- **Dual-Engine Architecture:**
  - **Native C++ Acceleration:** Leverages Blender's global integer-quantized parameterization solver for high-speed, continuous, 95%+ regular quad generation.
  - **Discrete Differential Geometry Fallback:** Pure Python / BMesh topological patch solver using discrete shape operators, Weingarten curvature estimation, and 4-RoSy harmonic diffusion.
- **In-Viewport GPU Visualization & HUD:**
  - Real-time 3D cross-needle visualization showing 4-RoSy principal curvature flow directions.
  - 2D status HUD in the 3D Viewport displaying phase progress and interactive shortcuts.
- **Topological Mirror Symmetry:**
  - Half-mesh bisection and reflection with **shared seam vertices** (zero seam vertex duplication, zero welding gaps).
- **Angle-Orthogonalized Relaxation:**
  - Tangential Laplacian smoothing combined with diagonal orthogonalization (driving corners to 90°) and high-poly BVH surface reprojection.
- **Adaptive Polygon Density:**
  - Curvature-adaptive sizing concentrating detail in crevices and sharp features while maintaining larger planar quads.
  - Optional vertex group weight painting ($0.25\times$ to $4.0\times$ local polygon scaling).
- **100% Self-Contained:**
  - Zero external Python dependencies or binary installations required. Runs locally without network connectivity.

---

## Interface Overview

```text
+------------------------------------------+
| Active: Suzanne_Subsurf                  |
| Polys: 7,872    | Vertices: 7,874        |
+------------------------------------------+
| [▶ Interactive Viewport Retopology]      |
| [⚡ One-Click Quad Remesh]                |
+------------------------------------------+
| ▼ Polygon Density                        |
|   Target Quads: 2500                     |
|   Adaptive Size: 0.65                    |
|   Density Group: [VertexGroup]           |
+------------------------------------------+
| ▼ Edge Flow & Curvature                  |
|   Curvature Flow: 0.85                   |
|   [x] Detect Hard Edges (Crease: 45°)    |
|   [x] Use Marked Creases                 |
+------------------------------------------+
| ▼ Symmetry                               |
|   [x] Symmetry: [ X ]  Y   Z             |
+------------------------------------------+
| ▼ In-Viewport Overlays                   |
|   [x] Show 4-RoSy Vectors                |
|   [x] Show Flow Loops                    |
|   Relaxation Steps: 12                   |
+------------------------------------------+
```

---

## Installation

### Via Blender Extensions (Blender 4.2+)
1. Download `quadflow_retopology-1.0.0.zip` from the [Releases](https://github.com/quadflow/quadflow_retopology/releases) page.
2. In Blender, go to **Edit > Preferences > Get Extensions** (or **Add-ons**).
3. Click the top-right chevron menu **(∨)** and choose **Install from Disk...**
4. Select `quadflow_retopology-1.0.0.zip` and confirm.
5. In the 3D Viewport, press **N** and open the **QuadFlow** sidebar panel.

Detailed instructions can be found in the [Installation Guide](docs/INSTALLATION.md).

---

## Usage Quick Guide

1. Select your target mesh in **Object Mode**.
2. Open the **QuadFlow** tab on the sidebar (**N** key).
3. Set your desired **Target Quads** (e.g., `2500`).
4. Click **One-Click Quad Remesh** for immediate generation, or **Interactive Viewport Retopology** for live GPU-guided feedback.

During interactive sessions:
- Press `[Space]` to start or pause live orthogonal relaxation.
- Scroll `[Mouse Wheel]` to adjust the target quad count dynamically.
- Press `[Enter]` to commit and generate the final mesh object.
- Press `[Esc]` to cancel cleanly without altering the scene.

See the complete [User Guide](docs/USAGE.md) for full parameter descriptions.

---

## System Requirements & Compatibility

- **Blender Version:** Blender 4.2 LTS, 5.0, 5.2+ (tested through Blender 5.2.2 LTS).
- **Operating Systems:** Windows 10/11, Linux (Ubuntu/Debian/Fedora/Arch), macOS (Intel & Apple Silicon).
- **Dependencies:** None. Operates 100% locally using standard Blender Python APIs (`bpy`, `bmesh`, `mathutils`, `gpu`).

---

## Running Automated Tests

All tests can be executed headlessly via Blender's CLI:

```bash
# Validate extension manifest
blender --command extension validate .

# Run extension registration lifecycle tests
blender --background --python tests/test_registration.py

# Run geometry regression benchmarks
blender --background --python tests/test_regression.py
```

---

## Documentation

- [User Guide](docs/USAGE.md)
- [Installation Guide](docs/INSTALLATION.md)
- [Developer Guide](docs/DEVELOPMENT.md)
- [Project Audit](PROJECT_AUDIT.md)
- [Changelog](CHANGELOG.md)
- [Contributing Guidelines](CONTRIBUTING.md)

---

## License

This project is licensed under the **GNU General Public License v3.0 or later** ([GPL-3.0-or-later](LICENSE)).
