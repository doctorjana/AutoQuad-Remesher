"""
QuadFlow - Regression and Functional Validation Test Suite
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

import quadflow_retopology as qf
from quadflow_retopology.core import (
    CurvatureFieldSolver,
    AdaptiveDensityField,
    QuadPatchExtractor,
    SurfaceRelaxationEngine,
    run_retopology,
)

print("=" * 60)
print("QUADFLOW REGRESSION TEST SUITE")
print(f"Blender Version: {bpy.app.version_string}")
print("=" * 60)

qf.register()

# -------------------------------------------------------------
# Test 1: Suzanne Monkey with Subdivision (Organic + Symmetry)
# -------------------------------------------------------------
print("\n[TEST 1] Testing organic symmetry mesh (Suzanne Subdivided)...")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_monkey_add(size=2.0)
test_obj = bpy.context.active_object
test_obj.name = "Test_Suzanne"

sub_mod = test_obj.modifiers.new("Subsurf", 'SUBSURF')
sub_mod.levels = 1
bpy.ops.object.modifier_apply(modifier="Subsurf")

settings = bpy.context.scene.quadflow_settings
settings.target_quad_count = 1000
settings.use_symmetry = True
settings.symmetry_axis = 'X'
settings.relaxation_steps = 10

t0 = time.perf_counter()
res = bpy.ops.view3d.quadflow_remesh()
dt = time.perf_counter() - t0
assert 'FINISHED' in res, f"Operator failed with result: {res}"

out_obj = bpy.context.active_object
assert out_obj != test_obj, "Output object should be newly generated"
assert out_obj.name == "Test_Suzanne_QuadFlow", f"Output name mismatch: {out_obj.name}"

out_mesh = out_obj.data
out_polys = len(out_mesh.polygons)
out_quads = sum(1 for p in out_mesh.polygons if len(p.vertices) == 4)
quad_ratio = (out_quads / max(1, out_polys)) * 100.0

print(f"  ✓ Total Polygons: {out_polys:,}")
print(f"  ✓ Pure Quads: {out_quads:,} ({quad_ratio:.1f}%)")
print(f"  ✓ Execution time: {dt:.4f}s")
assert quad_ratio >= 90.0, f"Expected quad dominance >= 90%, got {quad_ratio:.1f}%"

# Symmetry check: verify positive and negative vertices balance closely across the mirror plane
pos_x = sum(1 for v in out_mesh.vertices if v.co.x > 0.01)
neg_x = sum(1 for v in out_mesh.vertices if v.co.x < -0.01)
sym_diff = abs(pos_x - neg_x)
print(f"  ✓ Symmetry check: +X verts = {pos_x}, -X verts = {neg_x} (diff = {sym_diff})")
assert sym_diff <= 10, f"Symmetry imbalance exceeds tolerance: +X={pos_x} vs -X={neg_x} (diff={sym_diff})"

# -------------------------------------------------------------
# Test 2: UV Sphere (Curved Surface)
# -------------------------------------------------------------
print("\n[TEST 2] Testing closed curved surface (UV Sphere)...")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16)
sphere_obj = bpy.context.active_object

settings = bpy.context.scene.quadflow_settings
settings.target_quad_count = 1000
settings.use_symmetry = False
settings.relaxation_steps = 10

t0 = time.perf_counter()
res = bpy.ops.view3d.quadflow_remesh()
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
quad_bm = extractor.generate_quad_mesh(cross_fields, density_sizes, symmetry=True)

engine = SurfaceRelaxationEngine(quad_bm, src_bvh, symmetry_axis='X', lock_symmetry=True)
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

print("\n" + "=" * 60)
print("ALL REGRESSION AND FUNCTIONAL TESTS PASSED SUCCESSFULLY!")
print("=" * 60)
