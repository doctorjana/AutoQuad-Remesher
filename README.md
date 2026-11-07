# AutoQuad Remesher

[![Blender](https://img.shields.io/badge/Blender-4.2%20%7C%205.0%20%7C%205.2%2B-orange.svg)](https://www.blender.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-green.svg)]()
[![Manifest Validated](https://img.shields.io/badge/Extension%20Manifest-Passed-success.svg)]()

**AutoQuad Remesher** is a Blender add-on that automatically transforms complex 3D meshes into clean, high-quality quad topology while preserving surface details and sharp features. Designed for organic, hard-surface, and mechanical models, it makes professional automatic remeshing simple and efficient.

Developed by **Doctor Jana** for **Blender 4.2 LTS and newer** (including Blender 5.0 and 5.2+). It converts dense sculpts, photogrammetry 3D scans, CAD models, or uneven triangular meshes into production-ready quad geometry.

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
| [x] Optimal Quads (Auto)                 |
| Quality: 1.00                            |
| Adaptive Size: 0.65                      |
+------------------------------------------+
| ▼ Advanced Options                       |
|   [ ] Preprocess Mesh (Auto-repair)      |
|   [ ] Decimate Mesh                      |
|   [x] Remesh by Loose Parts              |
|   [x] Hide Original Mesh                 |
+------------------------------------------+
```

When you click **Remesh**, a responsive, asynchronous loading indicator is displayed while the algorithm executes. You can cancel at any time with <kbd>ESC</kbd>, and the source mesh is automatically hidden so you immediately see the clean quad result.

---

## Key Features

- **Zero-Guesswork Optimal Quads:** Automatically evaluates discrete dihedral turning energy, mean surface curvature, and surface area to compute the mathematically optimal quad budget without manual trial and error.
- **Quality Multiplier:** Easily scale target density up or down (e.g. `2.0x` for 2x denser quads on high-frequency sculpts, or `0.5x` for lightweight real-time assets).
- **In-Memory Loose Parts Extraction:** Automatically segments complex multi-part meshes (e.g., characters with eyes/teeth, mechanical assemblies, multi-shell 3D scans) in memory, calculates tailored budgets per component, remeshes each shell independently, and seamlessly recombines them into a single unified quad mesh.
- **Scale-Invariant Geometry Normalization:** Automatically conditions sub-meter metric scans (e.g. human anatomy, dental models, jewelry) into optimal numerical space, eliminating floating-point underflow and false non-manifold errors.
- **Non-Blocking Asynchronous UI:** Generator-driven modal event loop updates live progress percentages in the status bar and animates the sidebar spinner without freezing Blender ("Not Responding"). Supports instant cancellation via <kbd>ESC</kbd>.
- **Dual-Engine Architecture:**
  - **Native C++ Acceleration:** Fast, parameterization-guided solver generating 95%+ regular quads.
  - **Discrete Differential Geometry Fallback:** Pure Python / BMesh topological patch solver using discrete shape operators and Weingarten curvature estimation.
- **Preprocess Mesh (Make Manifold):** Integrated 3D-Print repair logic to clean up non-manifold elements, remove duplicate vertices, fill holes, delete loose/interior geometry, and fix inverted normals.
- **Non-Destructive Workflow:** Your original source model is 100% preserved and untouched; newly generated quads are output as a clean `<Name>_AutoQuad` object.
- **100% Self-Contained:** Zero external dependencies or manual Python environment setups required. Runs completely offline.

---

## Installation

### Via Blender Extensions (Blender 4.2+)
1. Download the latest release `.zip` from the [Releases](https://github.com/doctorjana/AutoQuad-Remesher/releases) page.
2. In Blender, open **Edit > Preferences > Get Extensions** (or **Add-ons**).
3. Click the top-right chevron menu **(∨)** and select **Install from Disk...**
4. Choose the zip file and confirm.
5. In the 3D Viewport, press **N** to open the sidebar and select the **AutoQuad** tab.

---

## Quick Start

1. Select your target mesh in **Object Mode**.
2. Press **N** to open the 3D Viewport sidebar and switch to the **AutoQuad** tab.
3. Enable **Optimal Quads (Auto)** or adjust **Target Quads** manually.
4. Click **Remesh**. The loading indicator will display live progress across parts, and your new quad mesh (`<Name>_AutoQuad`) will be created and activated with smooth shading.

---

## Automated Testing

AutoQuad includes an exhaustive 13-test automated regression suite:

```bash
# Validate extension manifest
blender --command extension validate .

# Run extension registration lifecycle tests
blender --background --python tests/test_registration.py

# Run geometry regression test suite
blender --background --python tests/test_regression.py
```

---

## License

This project is authored by **Doctor Jana** and licensed under the **GNU General Public License v3.0 or later** ([GPL-3.0-or-later](LICENSE)).
