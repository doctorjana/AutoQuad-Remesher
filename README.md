# AutoQuad Remesher

[![Blender](https://img.shields.io/badge/Blender-4.2%20%7C%205.0%20%7C%205.2%2B-orange.svg)](https://www.blender.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-green.svg)]()
[![Website](https://img.shields.io/badge/Website-GitHub%20Pages-blue.svg)](https://doctorjana.github.io/autoquad_remesher/)
[![Manifest Validated](https://img.shields.io/badge/Extension%20Manifest-Passed-success.svg)]()

**AutoQuad Remesher** is a streamlined, automatic quad remeshing extension for **Blender 4.2 LTS and newer** (including Blender 5.0 and 5.2+), developed by **Doctor Jana**. It converts dense sculpts, photogrammetry 3D scans, CAD models, or uneven triangular meshes into clean, production-ready quad geometry.

**Project Website & Documentation:** [https://doctorjana.github.io/autoquad_remesher/](https://doctorjana.github.io/autoquad_remesher/)

---

## Clean, Uncluttered Interface

AutoQuad Remesher provides a clean, single-click interface designed for speed and simplicity:

```text
+------------------------------------------+
| Active: Suzanne_Sculpt                   |
| Polys: 7,872    | Vertices: 7,874        |
+------------------------------------------+
| [⚡ Remesh]                               |
+------------------------------------------+
| Target Quads: 2500                       |
| Adaptive Size: 0.65                      |
+------------------------------------------+
| ▼ Advanced Options                       |
|   [ ] Preprocess Mesh (Auto-repair)      |
|   [x] Hide Original Mesh                 |
|   [🛠️ Make Mesh Manifold]                 |  <-- Standalone testing button
+------------------------------------------+
```

When you click **Remesh**, a dynamic loading indicator is displayed while the algorithm executes, and the source mesh is automatically hidden so you immediately see the clean quad result.

---

## Key Features

- **One-Click Remeshing:** Straightforward workflow with just one button and two core sliders: **Target Quads** and **Adaptive Size**.
- **Preprocess Mesh (Make Manifold):** Integrated 3D-Print Toolbox repair logic to clean up non-manifold elements, remove duplicate vertices, fill holes, delete loose/interior geometry, and fix inverted normals prior to remeshing.
- **Visual Loading Indicator:** Responsive feedback with progress state and wait cursor while the mesh is processed.
- **Auto-Hide Original Mesh:** Keeps your viewport clean by automatically hiding the high-poly source mesh upon generation (toggleable under Advanced Options).
- **Dual-Engine Architecture:**
  - **Native C++ Acceleration:** Fast, parameterization-guided solver generating 95%+ regular quads.
  - **Discrete Differential Geometry Fallback:** Pure Python / BMesh topological patch solver using discrete shape operators and Weingarten curvature estimation.
- **Adaptive Polygon Sizing:** Concentrates polygon density in crevices, bevels, and tight curves while maintaining larger quads across planar surfaces.
- **100% Self-Contained:** Zero external dependencies or manual Python environment setups required. Runs completely offline.

---

## Installation

### Via Blender Extensions (Blender 4.2+)
1. Download `autoquad_remesher-1.1.0.zip` from the [Releases](https://github.com/doctorjana/autoquad_remesher/releases) page.
2. In Blender, open **Edit > Preferences > Get Extensions** (or **Add-ons**).
3. Click the top-right chevron menu **(∨)** and select **Install from Disk...**
4. Choose `autoquad_remesher-1.1.0.zip` and confirm.
5. In the 3D Viewport, press **N** to open the sidebar and select the **AutoQuad** tab.

---

## Quick Start

1. Select your target mesh in **Object Mode**.
2. Press **N** to open the 3D Viewport sidebar and switch to the **AutoQuad** tab.
3. Adjust **Target Quads** (default: `2500`) and **Adaptive Size** (default: `0.65`).
4. Click **Remesh**. The loading indicator will display while the mesh is computed, and your new quad mesh (`<Name>_AutoQuad`) will be created and activated with smooth shading.

---

## Automated Testing

```bash
# Validate extension manifest
blender --command extension validate .

# Run extension registration lifecycle tests
blender --background --python tests/test_registration.py

# Run geometry regression tests
blender --background --python tests/test_regression.py
```

---

## License

This project is authored by **Doctor Jana** and licensed under the **GNU General Public License v3.0 or later** ([GPL-3.0-or-later](LICENSE)).
