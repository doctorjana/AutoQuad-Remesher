"""
AutoQuad Remesher - Regression and Functional Validation Test Suite
Compares remeshed topology against baseline characteristics across standard test meshes.

Usage:
    blender --background --python quadflow_retopology/tests/test_regression.py
"""

import sys
import os
import math
import time
import bpy
import bmesh
from mathutils.bvhtree import BVHTree

# Ensure workspace root is in sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
pkg_dir = os.path.dirname(script_dir)
root_dir = os.path.dirname(pkg_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import quadflow_retopology as aq
from quadflow_retopology.core import (
    CurvatureFieldSolver,
    AdaptiveDensityField,
    QuadPatchExtractor,
    SurfaceRelaxationEngine,
    run_retopology,
)

print("=" * 60)
print("AUTOQUAD REGRESSION TEST SUITE")
print(f"Blender Version: {bpy.app.version_string}")
print("=" * 60)

aq.register()

# -------------------------------------------------------------
# Test 1: Suzanne Monkey with Subdivision
# -------------------------------------------------------------
print("\n[TEST 1] Testing organic mesh (Suzanne Subdivided)...")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_monkey_add(size=2.0)
test_obj = bpy.context.active_object
test_obj.name = "Test_Suzanne"

sub_mod = test_obj.modifiers.new("Subsurf", 'SUBSURF')
sub_mod.levels = 1
bpy.ops.object.modifier_apply(modifier="Subsurf")

settings = bpy.context.scene.autoquad_settings
settings.target_quad_count = 1000
settings.hide_original = True

t0 = time.perf_counter()
res = bpy.ops.view3d.autoquad_remesh()
dt = time.perf_counter() - t0
assert 'FINISHED' in res, f"Operator failed with result: {res}"

out_obj = bpy.context.active_object
assert out_obj != test_obj, "Output object should be newly generated"
assert out_obj.name == "Test_Suzanne_AutoQuad", f"Output name mismatch: {out_obj.name}"
assert test_obj.hide_get() is True, "Original object should be hidden"

out_mesh = out_obj.data
out_polys = len(out_mesh.polygons)
out_quads = sum(1 for p in out_mesh.polygons if len(p.vertices) == 4)
quad_ratio = (out_quads / max(1, out_polys)) * 100.0

print(f"  ✓ Total Polygons: {out_polys:,}")
print(f"  ✓ Pure Quads: {out_quads:,} ({quad_ratio:.1f}%)")
print(f"  ✓ Original hidden: {test_obj.hide_get()}")
print(f"  ✓ Execution time: {dt:.4f}s")
assert quad_ratio >= 90.0, f"Expected quad dominance >= 90%, got {quad_ratio:.1f}%"

# -------------------------------------------------------------
# Test 2: UV Sphere (Curved Surface)
# -------------------------------------------------------------
print("\n[TEST 2] Testing closed curved surface (UV Sphere)...")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16)
sphere_obj = bpy.context.active_object

settings = bpy.context.scene.autoquad_settings
settings.target_quad_count = 1000
settings.hide_original = True

t0 = time.perf_counter()
res = bpy.ops.view3d.autoquad_remesh()
dt = time.perf_counter() - t0
assert 'FINISHED' in res, "Operator failed on UV Sphere"

sphere_out = bpy.context.active_object
sphere_mesh = sphere_out.data
s_polys = len(sphere_mesh.polygons)
s_quads = sum(1 for p in sphere_mesh.polygons if len(p.vertices) == 4)
s_ratio = (s_quads / max(1, s_polys)) * 100.0
print(f"  ✓ Sphere Polygons: {s_polys:,}, Quads: {s_quads:,} ({s_ratio:.1f}%) in {dt:.4f}s")
assert s_ratio >= 95.0, f"Expected sphere quads >= 95%, got {s_ratio:.1f}%"

# -------------------------------------------------------------
# Test 3: Fallback Pure Python Solver Path
# -------------------------------------------------------------
print("\n[TEST 3] Testing pure Python topological patch solver fallback...")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_monkey_add(size=2.0)
m_obj = bpy.context.active_object

src_bm = bmesh.new()
src_bm.from_mesh(m_obj.data)
src_bm.transform(m_obj.matrix_world)
src_bvh = BVHTree.FromBMesh(src_bm, epsilon=1e-5)

solver = CurvatureFieldSolver(src_bm, sharp_angle_threshold=math.radians(45.0), use_creases=True)
solver.identify_feature_edges()
solver.compute_face_curvatures()
cross_fields = solver.solve_4rosy_cross_field(smoothing_iterations=6)

density = AdaptiveDensityField(src_bm, target_quad_count=500, adaptive_factor=0.65)
density_sizes = density.evaluate_density_field(solver.face_curvatures)

extractor = QuadPatchExtractor(src_bm, target_quad_count=500, symmetry_axis='X')
quad_bm = extractor.generate_quad_mesh(cross_fields, density_sizes, symmetry=False)

engine = SurfaceRelaxationEngine(quad_bm, src_bvh, symmetry_axis='X', lock_symmetry=False)
engine.run_multi_step_relaxation(iterations=5)

fb_verts = len(quad_bm.verts)
fb_faces = len(quad_bm.faces)
fb_quads = sum(1 for f in quad_bm.faces if len(f.verts) == 4)
fb_pct = (fb_quads / max(1, fb_faces)) * 100.0

print(f"  ✓ Fallback Solver: {fb_verts} verts, {fb_faces} faces, {fb_quads} quads ({fb_pct:.1f}%)")
assert fb_faces > 0, "Fallback solver produced 0 faces"
assert fb_pct >= 65.0, f"Fallback solver quad percentage lower than baseline: {fb_pct:.1f}%"

src_bm.free()
quad_bm.free()

# -------------------------------------------------------------
# Test 4: Preprocess Mesh (3D Print Toolbox Make Manifold Repair)
# -------------------------------------------------------------
print("\n[TEST 4] Testing Preprocess Mesh (3D-Print Make Manifold repair)...")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add()
flawed_cube = bpy.context.active_object
flawed_cube.name = "Flawed_Mesh"

# Create non-manifold defect: delete face to create boundary hole, add loose vertex
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(flawed_cube.data)
bm.faces.ensure_lookup_table()
bm.faces.remove(bm.faces[0])
bm.verts.new((2.5, 2.5, 2.5))
bmesh.update_edit_mesh(flawed_cube.data)
bpy.ops.object.mode_set(mode='OBJECT')

settings = bpy.context.scene.autoquad_settings
settings.target_quad_count = 600
settings.preprocess_mesh = True
settings.fill_holes_on_preprocess = True
settings.hide_original = True

t0 = time.perf_counter()
res = bpy.ops.view3d.autoquad_remesh()
dt = time.perf_counter() - t0
assert 'FINISHED' in res, f"Operator failed with preprocess_mesh: {res}"

out_obj = bpy.context.active_object
assert out_obj.name == "Flawed_Mesh_AutoQuad", f"Unexpected name: {out_obj.name}"

bm_check = bmesh.new()
bm_check.from_mesh(out_obj.data)
is_manifold = all(e.is_manifold for e in bm_check.edges)
out_quads = sum(1 for f in bm_check.faces if len(f.verts) == 4)
total_f = len(bm_check.faces)
bm_check.free()

print(f"  ✓ Preprocessed Output: {total_f} faces, {out_quads} quads, is_manifold: {is_manifold} in {dt:.4f}s")
assert is_manifold is True, "Output mesh was expected to be manifold after preprocessing"
assert out_quads > 0, "Output mesh has 0 quads"
assert flawed_cube.hide_get() is True, "Source object should be hidden"

# -------------------------------------------------------------
# Test 5: Ultra-Dense Mesh Auto-Conditioning (> 80k polygons)
# -------------------------------------------------------------
print("\n[TEST 5] Testing Ultra-Dense Mesh Auto-Conditioning (> 80k polygons)...")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_uv_sphere_add(segments=320, ring_count=320)
dense_obj = bpy.context.active_object
dense_obj.name = "Dense_Sculpt"
initial_faces = len(dense_obj.data.polygons)
initial_verts = len(dense_obj.data.vertices)
print(f"  Input dense mesh: {initial_faces:,} polygons, {initial_verts:,} vertices")

settings = bpy.context.scene.autoquad_settings
settings.target_quad_count = 1500
settings.preprocess_mesh = False

t0 = time.perf_counter()
res = bpy.ops.view3d.autoquad_remesh()
dt = time.perf_counter() - t0
assert 'FINISHED' in res, f"Operator failed on dense mesh: {res}"

out_dense = bpy.context.active_object
assert out_dense.name == "Dense_Sculpt_AutoQuad", f"Unexpected name: {out_dense.name}"
out_dense_quads = sum(1 for f in out_dense.data.polygons if len(f.vertices) == 4)
total_dense_f = len(out_dense.data.polygons)
print(f"  ✓ Dense Mesh Output: {total_dense_f:,} faces, {out_dense_quads:,} quads in {dt:.4f}s")
assert total_dense_f > 0, "Dense remeshing produced 0 faces"
assert out_dense_quads >= int(total_dense_f * 0.95), "Dense output quad percentage lower than 95%"

print("\n" + "=" * 60)
print("ALL REGRESSION AND FUNCTIONAL TESTS PASSED SUCCESSFULLY!")
print("=" * 60)
