# QuadFlow Retopology - Comprehensive Project Audit

**Document Date:** November 4, 2026  
**Audited Target:** `d:\Retopo\quadflow_retopology`  
**Blender Test Environment:** Blender 5.2.2 LTS (Windows x64) / Target Compatibility: Blender 4.2.0+  

---

## 1. Executive Summary

QuadFlow Retopology is an automatic quad remeshing tool for Blender 4.2+ designed to convert unstructured, dense, or uneven meshes into clean, quad-dominant geometry aligned with geometric curvature directions, with topological mirror symmetry and angle-orthogonalized surface relaxation.

The project currently consists of a flat collection of Python modules in the extension directory:
- `__init__.py`: Entry point and registration.
- `adaptive_density.py`: Sizing field calculation based on curvature and vertex weights.
- `curvature_field.py`: Weingarten map approximation, principal curvature axes, and 4-RoSy harmonic cross-field solver.
- `patch_extractor.py`: Triangle-to-quad conversion, bisection, upsampling/decimating, 3-5 dipole cancellation, topological mirroring with shared seam vertices.
- `relaxation.py`: Tangential Laplacian smoothing, quad angle orthogonalization, mirror coupling, BVH surface reprojection.
- `operators.py`: Modal interactive operator with GPU shaders (`batch_for_shader`), one-click batch operator, and orchestration function `generate_quad_topology`.
- `ui_panel.py`: PropertyGroup `QuadFlowSettings` and N-Panel `VIEW3D_PT_quadflow_main`.
- `blender_manifest.toml`: Extension manifest (currently fails official validation due to tagline exceeding 64 chars).

A complete backup has been preserved at `d:\Retopo\quadflow_original_backup/` before making any refactoring edits.

---

## 2. Algorithm Architecture & Execution Flow

### 2.1 Pipeline Stages

The remeshing pipeline follows a dual-engine architecture:
1. **Primary Acceleration Engine (Native C++ QuadriFlow):**
   - Creates a temporary working copy of the active mesh object.
   - Cleans geometry (removes double vertices, dissolves degenerate elements, recalculates normals).
   - Introspects available RNA properties on `bpy.ops.object.quadriflow_remesh` dynamically (supporting Blender 4.2, 5.0, 5.2+ without hardcoding incompatibilities).
   - Invokes QuadriFlow remeshing with target face count, symmetry, and sharp edge preservation.
   - Converts the result into a working `bmesh`.

2. **Fallback Topological Patch Solver (Pure Python / BMesh):**
   - Used if the native operator is unavailable or fails to generate polygons.
   - **Step A:** `CurvatureFieldSolver` builds local orthonormal tangent frames per face, projects neighbor normal deltas to estimate the 2x2 Weingarten matrix, performs eigendecomposition for principal directions ($k_1, k_2$, $v_1, v_2$), identifies feature edges (dihedral threshold & sharp marks), and diffuses a 4-RoSy cross-field across adjacent faces.
   - **Step B:** `AdaptiveDensityField` computes target edge length $h(x) = \sqrt{\text{area} / N}$, modulated by curvature magnitude and vertex group weights, graded via neighbor ratio clamping.
   - **Step C:** `QuadPatchExtractor` bisects along mirror plane if symmetry is enabled, scales resolution (selective subdivision of longest edges or non-adjacent edge collapse decimation), regularizes valence (flipping edges toward optimal valence-6 triangular nodes), pairs triangles into quads across multiple dihedral angle thresholds (35°, 60°, 85°), enforces 100% pure quad conversion on leftover triangles, dissolves valence-2 nodes, cancels 3-5 pole dipoles, mirrors positive half with shared seam vertices, and snaps to source BVH.

3. **Post-Processing (Both Paths):**
   - **Topological Symmetry Enforcement:** Bisects along mirror plane ($X, Y, Z$), snaps centerline vertices strictly to $0.0$, mirrors vertices and faces with shared seam vertices (zero welding artifacts, zero duplicate seam vertices).
   - **Angle-Orthogonalized Surface Relaxation (`SurfaceRelaxationEngine`):**
     - Tangential Laplacian smoothing.
     - Quad corner angle orthogonalization (diagonal cross-product driving corners toward 90° rectangles).
     - Symmetry reflection locking.
     - High-poly BVH surface raycast snapping.
   - **Normal Recalculation & Mesh Validation:** Recalculates normals and validates mesh data before linking to the collection.

4. **In-Viewport Interactive Modal Operator (`VIEW3D_OT_quadflow_modal`):**
   - Solves 4-RoSy vector cross field and builds GPU line batches (cyan and orange cross needles).
   - Registers 3D draw handler (`POST_VIEW`) and 2D status HUD (`POST_PIXEL` using `blf`).
   - Uses a modal timer loop allowing live interactive relaxation (`[Space]`), target density adjustment (`[Mouse Wheel]`), commit (`[Enter]`), and clean cancellation (`[Esc]`).

---

## 3. Implementation Inventory

| File | Primary Classes / Functions | Responsibility | Issues / Risks |
| :--- | :--- | :--- | :--- |
| `__init__.py` | `register()`, `unregister()` | Extension registration, sys.path hygiene | Ad-hoc `sys.path` stripping and `numpy` eviction can destabilize other addons; flat module imports |
| `blender_manifest.toml` | Manifest metadata | Blender 4.2+ extension declaration | `tagline` length is 93 chars (Blender validation limit is 64 chars) |
| `adaptive_density.py` | `AdaptiveDensityField` | Target edge length calculation, curvature & vertex weight modulation, grading | Direct dictionary lookups without lookup table guards |
| `curvature_field.py` | `CurvatureFieldSolver` | Shape operator, Weingarten matrix, 4-RoSy cross-field harmonic diffusion | None functional; should be isolated in `core/` |
| `patch_extractor.py` | `QuadPatchExtractor` | Subdivision upsampling, decimation, edge flipping, quad pairing, pole cleanup, BVH projection | Complex multi-pass; must remain untouched mathematically |
| `relaxation.py` | `SurfaceRelaxationEngine` | Laplacian tangential smoothing, quad orthogonalization, symmetry coupling, BVH snapping | Clean standalone geometry engine |
| `operators.py` | `generate_quad_topology`, `VIEW3D_OT_quadflow_modal`, `VIEW3D_OT_quadflow_remesh`, draw callbacks | Modal execution, batch execution, pipeline coordination, viewport drawing | Logic coupling: engine function `generate_quad_topology` is defined inside operator module |
| `ui_panel.py` | `QuadFlowSettings`, `VIEW3D_PT_quadflow_main` | Property group definition and sidebar panel | Settings and UI panel bundled together; should be separated into `properties/` and `ui/` |

---

## 4. Dependencies

- **Blender Built-ins:** `bpy`, `bmesh`, `mathutils` (`Vector`, `Matrix`), `mathutils.bvhtree` (`BVHTree`), `mathutils.kdtree` (`KDTree`), `gpu`, `gpu_extras.batch` (`batch_for_shader`), `blf`.
- **Python Standard Library:** `sys`, `math`, `time`.
- **External Dependencies:** **None.** (Zero external C libraries or PyPI packages required; 100% self-contained).

---

## 5. Important Algorithm Parameters

- `target_quad_count` (int, default: 2500, range: 50 - 100,000): Target face budget.
- `adaptive_size` (float, default: 0.65, range: 0.0 - 1.0): Curvature density scaling factor.
- `curvature_influence` (float, default: 0.85, range: 0.0 - 1.0): Alignment weighting.
- `use_symmetry` (bool, default: True): Enables mirror bisection and shared seam generation.
- `symmetry_axis` (enum: 'X', 'Y', 'Z', default: 'X'): Reflection plane.
- `detect_hard_edges` (bool, default: True): Edge crease detection.
- `hard_edge_angle` (float, default: 45.0°, range: 15° - 90°): Dihedral angle threshold.
- `use_marked_creases` (bool, default: True): Respects marked Sharp/Seam edges.
- `relaxation_steps` (int, default: 12, range: 1 - 50): Orthogonal Laplacian relaxation iterations.
- `density_vertex_group` (str): Optional vertex group driving local polygon sizing.

---

## 6. Baseline Verification & Metrics

Verified under **Blender 5.2.2 LTS headless**:

### 6.1 Native Quadriflow + Symmetry + Relaxation Path
| Test Model | Input Verts / Faces | Output Verts / Faces | Quads Count / % | Execution Time |
| :--- | :--- | :--- | :--- | :--- |
| **Suzanne (Subsurf 1)** | 2,012 / 1,968 | 1,076 / 1,070 | 1,022 (95.5%) | 0.4701s |
| **UV Sphere (32x16)** | 482 / 512 | 1,080 / 1,078 | 1,078 (100.0%) | 0.4184s |
| **Torus (Major 1, Minor 0.35)** | 576 / 576 | 1,042 / 1,042 | 1,042 (100.0%) | 0.4180s |

### 6.2 Pure Python Fallback Topological Patch Solver Path
| Test Model | Input Verts / Faces | Output Verts / Faces | Quads Count / % | Execution Time |
| :--- | :--- | :--- | :--- | :--- |
| **Suzanne (Base, 500 quads)** | 507 / 500 | 343 / 391 | 281 (71.9%) | 0.0732s |

---

## 7. Refactoring Strategy & Risks

### Risks & Mitigations
1. **Algorithm Integrity (Critical):**
   - *Risk:* Altering mathematical formulas, BVH tolerances, or vertex index mappings in `patch_extractor.py`, `curvature_field.py`, or `relaxation.py`.
   - *Mitigation:* Preserve all mathematical logic and algorithms verbatim. Extract engine logic out of `operators.py` into `core/retopology_engine.py` without modifying algorithmic steps. Run comparative regression benchmarks.
2. **Blender Extension Manifest Validation:**
   - *Risk:* Manifest validation fails when installing via `blender --command extension validate`.
   - *Mitigation:* Shorten `tagline` to $\le 64$ characters (`"Curvature cross-field and topology-optimized quad remesher"` = 57 chars).
3. **Global State & Draw Handler Leaks:**
   - *Risk:* Viewport draw handlers remaining active if modal operator encounters an unhandled exception.
   - *Mitigation:* Robust `try...finally` cleanup blocks and unregistration checks ensuring handlers and timers are purged.
4. **Environment Contamination in `__init__.py`:**
   - *Risk:* Indiscriminate removal of `sys.modules['numpy']` breaks Blender internal modules.
   - *Mitigation:* Eliminate the destructive sys.modules purge, replacing it with clean standard imports.

---

## 8. Target Modular Architecture Plan

```text
quadflow_retopology/
├── __init__.py                     # Clean centralized registration & extension lifecycle
├── blender_manifest.toml           # Validated Blender 4.2+ extension manifest
│
├── core/                           # Pure computation and geometry algorithms (independent of UI)
│   ├── __init__.py
│   ├── retopology_engine.py        # Central run_retopology() entry point & coordination
│   ├── curvature_field.py          # Shape operator & 4-RoSy harmonic cross-field solver
│   ├── adaptive_density.py         # Sizing field evaluation
│   ├── patch_extractor.py          # Triangle-to-quad engine, dipole cancellation & BVH projection
│   └── relaxation.py               # Angle-orthogonalized relaxation engine
│
├── operators/                      # Blender operators (modal and batch remeshing)
│   ├── __init__.py
│   ├── remesh_operator.py          # VIEW3D_OT_quadflow_remesh
│   └── modal_operator.py           # VIEW3D_OT_quadflow_modal (in-viewport interactive GPU HUD)
│
├── properties/                     # Data definitions and settings
│   ├── __init__.py
│   └── settings.py                 # QuadFlowSettings PropertyGroup
│
├── ui/                             # Native Blender layout panels and drawing
│   ├── __init__.py
│   ├── main_panel.py               # VIEW3D_PT_quadflow_main
│   └── gpu_drawing.py              # 3D cross needle and 2D HUD drawing callbacks
│
├── utils/                          # Shared helper functions
│   ├── __init__.py
│   ├── validation.py               # Mesh and object validation utilities
│   └── compatibility.py            # Blender 4.2/5.0/5.2 API compatibility helpers
│
└── tests/                          # Automated regression and lifecycle test suite
    ├── __init__.py
    ├── test_registration.py
    └── test_regression.py
```
