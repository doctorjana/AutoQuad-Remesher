# QuadFlow Retopology - Developer Guide

This document describes the architectural layout, core geometric algorithms, and maintenance workflows for developers contributing to QuadFlow Retopology.

---

## Architecture Overview

```text
quadflow_retopology/
├── __init__.py                     # Centralized extension lifecycle & class registration
├── blender_manifest.toml           # Official Blender 4.2+ extension manifest
│
├── core/                           # Pure computation layer (zero UI dependency)
│   ├── __init__.py
│   ├── retopology_engine.py        # Central run_retopology() engine coordinator
│   ├── curvature_field.py          # Shape operator & 4-RoSy harmonic cross-field solver
│   ├── adaptive_density.py         # Scalar sizing field evaluation & grading
│   ├── patch_extractor.py          # Dual upsampling/decimating patch solver & dipole cancellation
│   └── relaxation.py               # Orthogonal Laplacian relaxation & BVH reprojection
│
├── operators/                      # Blender operator definitions
│   ├── __init__.py
│   ├── remesh_operator.py          # VIEW3D_OT_quadflow_remesh (Batch remeshing)
│   └── modal_operator.py           # VIEW3D_OT_quadflow_modal (Interactive viewport HUD)
│
├── properties/                     # Settings and data models
│   ├── __init__.py
│   └── settings.py                 # QuadFlowSettings PropertyGroup
│
├── ui/                             # UI layout and GPU viewport rendering
│   ├── __init__.py
│   ├── main_panel.py               # VIEW3D_PT_quadflow_main (N-Panel sidebar)
│   └── gpu_drawing.py              # 3D line batch shaders & 2D BLF status overlays
│
├── utils/                          # Common utilities
│   ├── __init__.py
│   ├── validation.py               # Mesh input verification guards
│   └── compatibility.py            # Cross-version Blender API shims
│
└── tests/                          # Automated headless verification
    ├── __init__.py
    ├── test_registration.py        # Lifecycle registration / unregistration tests
    └── test_regression.py          # Regression tests against baseline mesh outputs
```

---

## Core Algorithm Mechanics

### 1. Shape Operator & 4-RoSy Cross-Field (`core/curvature_field.py`)
- Evaluates discrete differential geometry per face.
- For each face $f$, creates an orthonormal tangent frame $(e_1, e_2, n)$ and projects normal deltas $\Delta n$ across adjacent faces to estimate the 2x2 Weingarten matrix $S$:
  $$S = \begin{bmatrix} A & B \\ B & C \end{bmatrix}$$
- Solves for principal eigenvalues $k_1, k_2$ and directional eigenvectors $v_1, v_2$.
- Initializes tangent vectors snapped to sharp creases, boundaries, or minimum curvature directions.
- Solves a harmonic 4-RoSy (4-Rotational Symmetry) field by minimizing angular differences over orthogonal rotations:
  $$v_{\text{cand}} \in \{v, n \times v, -v, -(n \times v)\}$$

### 2. Adaptive Sizing Field (`core/adaptive_density.py`)
- Calculates nominal edge length from total surface area and target quad budget:
  $$h_0 = \sqrt{\frac{\text{Total Surface Area}}{\text{Target Quads}}}$$
- Scales edge lengths locally based on curvature Frobenius norm $\sqrt{k_1^2 + k_2^2}$ and vertex group weight.
- Enforces an iterative grading step to prevent adjacent edge length ratios from exceeding $1.4\times$.

### 3. Topological Patch Engine (`core/patch_extractor.py`)
- **Bisecting:** Clamps centerline seam vertices strictly to mirror plane.
- **Budget Scaling:** Uses bidirectional upsampling (selective edge subdivision) and decimation (independent non-adjacent edge collapses).
- **Valence Regularization:** Flips edges in triangular networks to maximize valence-6 interior vertices (which form regular valence-4 quad junctions upon pairing).
- **Triangle-to-Quad Pairing:** Dissolves shared edges between triangular pairs scored by normal deviation and valence optimization.
- **Dipole Cleanup:** Dissolves valence-2 vertices and flips edges connecting 3-5 valence dipoles.
- **Topological Mirroring:** Mirrors vertices with shared seam vertices (zero duplicated centerline nodes).

### 4. Angle-Orthogonalized Relaxation (`core/relaxation.py`)
- Applies tangential Laplacian smoothing with boundary edge preservation.
- Pushes quad corner angles toward $90^\circ$ by minimizing diagonal orthogonal variance:
  $$d_2 \approx n \times d_1$$
- Snaps vertices back onto the reference high-poly surface using BVH tree nearest-point projection.

---

## Testing & Quality Control

Execute regression benchmarks before submitting any PR:

```bash
# 1. Validate manifest compliance
blender --command extension validate .

# 2. Run lifecycle unit tests
blender --background --python tests/test_registration.py

# 3. Run regression benchmarks
blender --background --python tests/test_regression.py
```

### Building the Release Package
To build the distribution ZIP archive:
```bash
blender --command extension build --output-dir ../release
```
