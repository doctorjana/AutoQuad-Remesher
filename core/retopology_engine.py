"""
AutoQuad Remesher - Core Retopology Engine
Independent computation and geometry orchestration layer.
Coordinates:
1. Optional 3D-Print Toolbox Make Manifold preprocessing for non-manifold meshes.
2. Native C++ QuadriFlow remeshing with dynamic property compatibility.
3. Fallback discrete differential geometry topological patch solver.
4. Topological symmetry plane bisection and shared-seam mirroring (if requested).
5. Angle-orthogonalized surface relaxation with BVH raycast snapping.
"""

import math
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from .curvature_field import CurvatureFieldSolver
from .adaptive_density import AdaptiveDensityField
from .patch_extractor import QuadPatchExtractor
from .relaxation import SurfaceRelaxationEngine
from .mesh_preprocessing import make_manifold

def run_retopology(context, source_obj, settings, src_bvh=None):
    """
    Executes the complete AutoQuad retopology pipeline.
    
    Parameters:
        context: Blender context
        source_obj: Source mesh Object to remesh
        settings: AutoQuadSettings instance containing algorithm configuration
        src_bvh: Optional pre-built BVHTree in world space (constructed if None)
        
    Returns:
        bmesh.types.BMesh: A newly allocated BMesh in world coordinates containing
                           the retopologized regular quad geometry.
                           Caller is responsible for freeing the bmesh.
    """
    has_native = hasattr(bpy.ops.object, "quadriflow_remesh")
    quad_bm = None
    
    temp_obj = None
    temp_mesh = None
    
    try:
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            
        bpy.ops.object.select_all(action='DESELECT')
        source_obj.select_set(True)
        context.view_layer.objects.active = source_obj
        
        # Create non-destructive working duplicate
        temp_mesh = source_obj.data.copy()
        temp_mesh.name = f"{source_obj.name}_AutoQuad_Temp"
        temp_obj = bpy.data.objects.new(f"{source_obj.name}_AutoQuad_Temp", temp_mesh)
        temp_obj.matrix_world = source_obj.matrix_world.copy()
        context.collection.objects.link(temp_obj)
        
        bpy.ops.object.select_all(action='DESELECT')
        temp_obj.select_set(True)
        context.view_layer.objects.active = temp_obj
        
        # -------------------------------------------------------------
        # Optional: Make Manifold Preprocessing (3D Print Toolbox Logic)
        # -------------------------------------------------------------
        if getattr(settings, "preprocess_mesh", False):
            fill_holes_opt = getattr(settings, "fill_holes_on_preprocess", False)
            make_manifold(context, temp_obj, fill_holes=fill_holes_opt, preserve_curvature=True)
            temp_obj.data.update()
            
        # Build reference BVH from working geometry
        if getattr(settings, "preprocess_mesh", False) or src_bvh is None:
            src_bm_temp = bmesh.new()
            src_bm_temp.from_mesh(temp_obj.data)
            src_bm_temp.transform(temp_obj.matrix_world)
            src_bvh = BVHTree.FromBMesh(src_bm_temp, epsilon=1e-5)
            src_bm_temp.free()
            
        # -------------------------------------------------------------
        # 1. Primary Engine: Native C++ QuadriFlow
        # -------------------------------------------------------------
        if has_native:
            try:
                # Pre-clean geometry
                clean_bm = bmesh.new()
                clean_bm.from_mesh(temp_obj.data)
                bmesh.ops.remove_doubles(clean_bm, verts=clean_bm.verts[:], dist=1e-5)
                bmesh.ops.dissolve_degenerate(clean_bm, dist=1e-5, edges=clean_bm.edges[:])
                bmesh.ops.recalc_face_normals(clean_bm, faces=clean_bm.faces[:])
                clean_bm.to_mesh(temp_obj.data)
                clean_bm.free()
                temp_obj.data.update()
                
                # Dynamic RNA introspection for cross-version compatibility (Blender 4.2, 5.0, 5.2+)
                op_props = bpy.ops.object.quadriflow_remesh.get_rna_type().properties.keys()
                kwargs = {}
                if 'mode' in op_props:
                    kwargs['mode'] = 'FACES'
                if 'target_faces' in op_props:
                    kwargs['target_faces'] = max(50, settings.target_quad_count)
                if 'use_mesh_symmetry' in op_props:
                    kwargs['use_mesh_symmetry'] = getattr(settings, "use_symmetry", False)
                if 'use_preserve_sharp' in op_props:
                    kwargs['use_preserve_sharp'] = getattr(settings, "detect_hard_edges", True)
                if 'use_preserve_boundary' in op_props:
                    kwargs['use_preserve_boundary'] = True
                if 'smooth_normals' in op_props:
                    kwargs['smooth_normals'] = True
                if 'seed' in op_props:
                    kwargs['seed'] = 0
                    
                res = bpy.ops.object.quadriflow_remesh(**kwargs)
                if 'FINISHED' in res and len(temp_obj.data.polygons) > 0:
                    quad_bm = bmesh.new()
                    quad_bm.from_mesh(temp_obj.data)
            except Exception as e:
                print(f"[AutoQuad] Native Quadriflow engine notification: {e}")

        # -------------------------------------------------------------
        # 2. Fallback Engine: Topological Patch Solver
        # -------------------------------------------------------------
        if quad_bm is None or len(quad_bm.faces) == 0:
            if quad_bm:
                quad_bm.free()
                quad_bm = None
                
            src_bm_local = bmesh.new()
            src_bm_local.from_mesh(temp_obj.data)
            src_bm_local.transform(temp_obj.matrix_world)
            
            solver = CurvatureFieldSolver(
                src_bm_local,
                sharp_angle_threshold=math.radians(getattr(settings, "hard_edge_angle", 45.0)),
                use_creases=getattr(settings, "use_marked_creases", True)
            )
            solver.identify_feature_edges()
            solver.compute_face_curvatures()
            cross_fields = solver.solve_4rosy_cross_field(smoothing_iterations=6)
            
            density = AdaptiveDensityField(
                src_bm_local,
                target_quad_count=settings.target_quad_count,
                adaptive_factor=settings.adaptive_size
            )
            density_sizes = density.evaluate_density_field(solver.face_curvatures)
            
            extractor = QuadPatchExtractor(
                src_bm_local,
                target_quad_count=settings.target_quad_count,
                symmetry_axis=getattr(settings, "symmetry_axis", 'X')
            )
            quad_bm = extractor.generate_quad_mesh(
                cross_fields,
                density_sizes,
                symmetry=getattr(settings, "use_symmetry", False)
            )
            src_bm_local.free()

    finally:
        # Guaranteed cleanup of working duplicate
        if temp_obj is not None:
            try:
                bpy.data.objects.remove(temp_obj, do_unlink=True)
            except Exception:
                pass
        if temp_mesh is not None:
            try:
                bpy.data.meshes.remove(temp_mesh, do_unlink=True)
            except Exception:
                pass

    if quad_bm is None or len(quad_bm.faces) == 0:
        return None

    # -------------------------------------------------------------
    # 3. Topological Symmetry Enforcement (if enabled)
    # -------------------------------------------------------------
    if getattr(settings, "use_symmetry", False):
        axis_idx = 0 if settings.symmetry_axis == 'X' else (1 if settings.symmetry_axis == 'Y' else 2)
        plane_no = Vector((1.0, 0.0, 0.0)) if axis_idx == 0 else (
            Vector((0.0, 1.0, 0.0)) if axis_idx == 1 else Vector((0.0, 0.0, 1.0))
        )
        try:
            bmesh.ops.bisect_plane(
                quad_bm,
                geom=quad_bm.verts[:] + quad_bm.edges[:] + quad_bm.faces[:],
                plane_co=Vector((0.0, 0.0, 0.0)),
                plane_no=plane_no,
                clear_inner=True,
                clear_outer=False
            )
        except Exception:
            pass
            
        for v in quad_bm.verts:
            if v.is_boundary and abs(v.co[axis_idx]) < 0.02:
                v.co[axis_idx] = 0.0
                
        mirror_map = {}
        for v in list(quad_bm.verts):
            if abs(v.co[axis_idx]) <= 1e-5:
                v.co[axis_idx] = 0.0
                mirror_map[v] = v
            else:
                new_co = Vector(v.co)
                new_co[axis_idx] = -new_co[axis_idx]
                mirror_map[v] = quad_bm.verts.new(new_co)
                
        for face in list(quad_bm.faces):
            mirrored_verts = [mirror_map[v] for v in reversed(face.verts)]
            if len(set(mirrored_verts)) == len(face.verts):
                try:
                    quad_bm.faces.new(mirrored_verts)
                except ValueError:
                    pass
                    
        quad_bm.verts.ensure_lookup_table()
        quad_bm.edges.ensure_lookup_table()
        quad_bm.faces.ensure_lookup_table()

    # -------------------------------------------------------------
    # 4. Surface Reprojection & Orthogonal Relaxation
    # -------------------------------------------------------------
    relax_steps = getattr(settings, "relaxation_steps", 10)
    if relax_steps > 0 and src_bvh is not None:
        engine = SurfaceRelaxationEngine(
            quad_bm,
            src_bvh,
            symmetry_axis=getattr(settings, "symmetry_axis", 'X'),
            lock_symmetry=getattr(settings, "use_symmetry", False)
        )
        engine.run_multi_step_relaxation(iterations=relax_steps)

    quad_bm.verts.ensure_lookup_table()
    quad_bm.faces.ensure_lookup_table()
    try:
        bmesh.ops.recalc_face_normals(quad_bm, faces=quad_bm.faces[:])
    except Exception:
        pass
    quad_bm.normal_update()
    
    return quad_bm
