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
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

from .curvature_field import CurvatureFieldSolver
from .adaptive_density import AdaptiveDensityField
from .patch_extractor import QuadPatchExtractor
from .relaxation import SurfaceRelaxationEngine
from .mesh_preprocessing import make_manifold

def sanitize_working_mesh(bm, merge_dist=1e-4):
    """
    Cleans up topological defects that violate QuadriFlow's manifold requirements:
    1. Duplicate overlapping faces
    2. Interior multi-face edges (> 2 faces)
    3. Isolated wire edges (0 faces)
    4. Isolated loose vertices
    5. Zero-area faces (< 1e-7)
    6. Double vertices within merge distance
    7. Degenerate edges and faces
    8. Consistent outward face normals
    """
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    
    # 1. Remove duplicate faces
    seen = {}
    dup_faces = []
    for f in bm.faces:
        key = frozenset(v.index for v in f.verts)
        if key in seen:
            dup_faces.append(f)
        else:
            seen[key] = f
    if dup_faces:
        bmesh.ops.delete(bm, geom=dup_faces, context='FACES')
        bm.faces.ensure_lookup_table()
        
    # 2. Remove interior multi-face edges
    bm.edges.ensure_lookup_table()
    interior_faces = set()
    for e in bm.edges:
        if len(e.link_faces) > 2:
            for f in e.link_faces[2:]:
                interior_faces.add(f)
    if interior_faces:
        bmesh.ops.delete(bm, geom=list(interior_faces), context='FACES')
        bm.faces.ensure_lookup_table()
        
    # 3. Remove zero-area / degenerate faces
    bm.faces.ensure_lookup_table()
    zero_faces = [f for f in bm.faces if f.calc_area() < 1e-7]
    if zero_faces:
        bmesh.ops.delete(bm, geom=zero_faces, context='FACES')
        bm.faces.ensure_lookup_table()
        
    # 4. Remove loose wire edges (0 faces attached)
    bm.edges.ensure_lookup_table()
    wire_edges = [e for e in bm.edges if len(e.link_faces) == 0]
    if wire_edges:
        bmesh.ops.delete(bm, geom=wire_edges, context='EDGES')
        bm.edges.ensure_lookup_table()
        
    # 5. Remove loose vertices (0 edges and 0 faces)
    bm.verts.ensure_lookup_table()
    loose_verts = [v for v in bm.verts if len(v.link_edges) == 0 and len(v.link_faces) == 0]
    if loose_verts:
        bmesh.ops.delete(bm, geom=loose_verts, context='VERTS')
        bm.verts.ensure_lookup_table()
        
    # 6. Weld duplicate vertices and dissolve degenerate elements
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=merge_dist)
    bm.edges.ensure_lookup_table()
    bmesh.ops.dissolve_degenerate(bm, dist=merge_dist, edges=bm.edges[:])
    
    # 7. Make face normals consistently oriented
    try:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    except Exception:
        pass

def _run_quadriflow_op(settings, target_faces=None, preserve_boundary=True):
    """Executes native QuadriFlow remesh operator with safe property mapping."""
    op_props = bpy.ops.object.quadriflow_remesh.get_rna_type().properties.keys()
    kwargs = {}
    if 'mode' in op_props:
        kwargs['mode'] = 'FACES'
    if 'target_faces' in op_props:
        count = target_faces if target_faces is not None else getattr(settings, "target_quad_count", 2500)
        kwargs['target_faces'] = max(50, count)
    if 'use_mesh_symmetry' in op_props:
        kwargs['use_mesh_symmetry'] = getattr(settings, "use_symmetry", False)
    if 'use_preserve_sharp' in op_props:
        kwargs['use_preserve_sharp'] = getattr(settings, "detect_hard_edges", True)
    if 'use_preserve_boundary' in op_props:
        kwargs['use_preserve_boundary'] = preserve_boundary
    if 'smooth_normals' in op_props:
        kwargs['smooth_normals'] = True
    if 'seed' in op_props:
        kwargs['seed'] = 0
        
    try:
        res = bpy.ops.object.quadriflow_remesh(**kwargs)
        return 'FINISHED' in res
    except Exception as e:
        print(f"[AutoQuad] QuadriFlow pass (preserve_boundary={preserve_boundary}) notice: {e}")
        return False

def _condition_dense_mesh(temp_obj, max_faces=65000):
    """
    If the working guide mesh exceeds max_faces (e.g. 500k poly sculpts),
    applies a shape-preserving decimation to condition the guide surface
    for QuadriFlow's linear solver. Full original detail is preserved because
    the final quad mesh is projected back onto the full-resolution src_bvh.
    """
    poly_count = len(temp_obj.data.polygons)
    if poly_count > max_faces:
        ratio = max_faces / float(poly_count)
        dmod = temp_obj.modifiers.new('AutoQuad_Decimate', 'DECIMATE')
        dmod.ratio = ratio
        bpy.ops.object.modifier_apply(modifier='AutoQuad_Decimate')
        temp_obj.data.update()

def run_retopology_single_part(context, temp_obj, settings, target_faces=None, src_bvh=None):
    """
    Executes the complete retopology pipeline on a single manifold/connected working mesh object.
    Returns a bmesh.types.BMesh in world coordinates containing the regular quad geometry.
    """
    has_native = hasattr(bpy.ops.object, "quadriflow_remesh")
    quad_bm = None
    
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
        
    # Build reference BVH from working geometry (before decimation to keep full surface resolution)
    if getattr(settings, "preprocess_mesh", False) or src_bvh is None:
        src_bm_temp = bmesh.new()
        src_bm_temp.from_mesh(temp_obj.data)
        src_bm_temp.transform(temp_obj.matrix_world)
        src_bvh = BVHTree.FromBMesh(src_bm_temp, epsilon=1e-5)
        src_bm_temp.free()
        
    # -------------------------------------------------------------
    # Optional: Non-destructive User Decimate Pre-pass
    # -------------------------------------------------------------
    if getattr(settings, "use_decimate", False):
        dmod = temp_obj.modifiers.new('AutoQuad_UserDecimate', 'DECIMATE')
        d_mode = getattr(settings, "decimate_mode", 'COLLAPSE')
        ratio_val = getattr(settings, "decimate_ratio", 0.1)
        
        if d_mode == 'UNSUBDIV':
            dmod.decimate_type = 'UNSUBDIV'
            dmod.iterations = getattr(settings, "decimate_unsubdivide_iterations", 2)
        else:
            dmod.decimate_type = 'COLLAPSE'
            dmod.ratio = ratio_val
            
        orig_poly_count = len(temp_obj.data.polygons)
        bpy.ops.object.modifier_apply(modifier='AutoQuad_UserDecimate')
        temp_obj.data.update()
        
        # If unsubdivide did not reduce face count (e.g. non-grid topology), fallback to collapse
        if d_mode == 'UNSUBDIV' and len(temp_obj.data.polygons) >= orig_poly_count:
            dmod_fb = temp_obj.modifiers.new('AutoQuad_UserDecimate_FB', 'DECIMATE')
            dmod_fb.decimate_type = 'COLLAPSE'
            dmod_fb.ratio = ratio_val
            bpy.ops.object.modifier_apply(modifier='AutoQuad_UserDecimate_FB')
            temp_obj.data.update()
        
    # -------------------------------------------------------------
    # 1. Primary Engine: Native C++ QuadriFlow with Self-Healing Multi-Stage Recovery
    # -------------------------------------------------------------
    if has_native:
        # Stage A: Initial sanitization of working duplicate
        clean_bm = bmesh.new()
        clean_bm.from_mesh(temp_obj.data)
        sanitize_working_mesh(clean_bm, merge_dist=1e-4)
        clean_bm.to_mesh(temp_obj.data)
        clean_bm.free()
        temp_obj.data.update()
        
        # Stage B: Auto-condition ultra-dense sculpts (> 70k polygons)
        initial_polys = len(temp_obj.data.polygons)
        if initial_polys > 70000:
            _condition_dense_mesh(temp_obj, max_faces=65000)
            
        # Stage C: Multi-pass execution
        target_count = target_faces if target_faces is not None else getattr(settings, "target_quad_count", 2500)
        
        # Pass 1: Standard QuadriFlow with boundary preservation
        success = _run_quadriflow_op(settings, target_faces=target_count, preserve_boundary=True)
        
        # Pass 2: Retry without boundary preservation if Pass 1 failed
        if not success or len(temp_obj.data.polygons) == 0:
            success = _run_quadriflow_op(settings, target_faces=target_count, preserve_boundary=False)
            
        # Pass 3: Auto-heal manifold defects and retry
        if not success or len(temp_obj.data.polygons) == 0:
            try:
                make_manifold(context, temp_obj, fill_holes=False)
                temp_obj.data.update()
                success = _run_quadriflow_op(settings, target_faces=target_count, preserve_boundary=False)
            except Exception as e:
                print(f"[AutoQuad] Auto-heal pass 3 notice: {e}")
                
        # Pass 4: If still failing and mesh is still dense (> 35k), condition further
        if (not success or len(temp_obj.data.polygons) == 0) and len(temp_obj.data.polygons) > 35000:
            try:
                _condition_dense_mesh(temp_obj, max_faces=35000)
                make_manifold(context, temp_obj, fill_holes=False)
                temp_obj.data.update()
                success = _run_quadriflow_op(settings, target_faces=target_count, preserve_boundary=False)
            except Exception as e:
                print(f"[AutoQuad] Auto-heal pass 4 notice: {e}")
                
        # Pass 5: Seal open boundary tears and retry as watertight
        if not success or len(temp_obj.data.polygons) == 0:
            try:
                make_manifold(context, temp_obj, fill_holes=True)
                temp_obj.data.update()
                success = _run_quadriflow_op(settings, target_faces=target_count, preserve_boundary=False)
            except Exception as e:
                print(f"[AutoQuad] Auto-heal pass 5 notice: {e}")

        if success and len(temp_obj.data.polygons) > 0:
            quad_bm = bmesh.new()
            quad_bm.from_mesh(temp_obj.data)
            quad_bm.transform(temp_obj.matrix_world)

    # -------------------------------------------------------------
    # 2. Fallback Engine: Topological Patch Solver
    # -------------------------------------------------------------
    if quad_bm is None or len(quad_bm.faces) == 0:
        if quad_bm:
            quad_bm.free()
            quad_bm = None
            
        poly_count = len(temp_obj.data.polygons)
        if poly_count > 10000:
            print(f"[AutoQuad] Notice: Native solver was unable to process high-poly mesh ({poly_count:,} polygons). Aborting pure Python fallback to prevent system freeze.")
            return None
            
        src_bm_local = bmesh.new()
        src_bm_local.from_mesh(temp_obj.data)
        src_bm_local.transform(temp_obj.matrix_world)
        
        fallback_target = target_faces if target_faces is not None else getattr(settings, "target_quad_count", 2500)
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
            target_quad_count=fallback_target,
            adaptive_factor=settings.adaptive_size
        )
        density_sizes = density.evaluate_density_field(solver.face_curvatures)
        
        extractor = QuadPatchExtractor(
            src_bm_local,
            target_quad_count=fallback_target,
            symmetry_axis=getattr(settings, "symmetry_axis", 'X')
        )
        quad_bm = extractor.generate_quad_mesh(
            cross_fields,
            density_sizes,
            symmetry=getattr(settings, "use_symmetry", False)
        )
        src_bm_local.free()

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

def run_retopology(context, source_obj, settings, src_bvh=None, progress_cb=None):
    """
    Executes the complete AutoQuad retopology pipeline:
    1. Internally partitions the mesh into disconnected loose parts (connected components).
    2. Dynamically allocates target quad budgets per loose component.
    3. Remeshes each loose component individually while updating visual progress.
    4. Recombines all remeshed quad components into a unified quad mesh.
    
    Parameters:
        context: Blender context
        source_obj: Source mesh Object to remesh
        settings: AutoQuadSettings instance containing algorithm configuration
        src_bvh: Optional pre-built BVHTree in world space (constructed if None)
        progress_cb: Optional callback function progress_cb(current_part, total_parts, part_obj)
        
    Returns:
        bmesh.types.BMesh: A newly allocated BMesh in world coordinates containing
                           the retopologized regular quad geometry.
                           Caller is responsible for freeing the bmesh.
    """
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
        
    # Read source mesh into BMesh safely
    src_bm = bmesh.new()
    src_bm.from_mesh(source_obj.data)
    sanitize_working_mesh(src_bm, merge_dist=1e-7)
    src_bm.faces.ensure_lookup_table()
    src_bm.verts.ensure_lookup_table()
    
    # -------------------------------------------------------------
    # 1. Partition Connected Components (Loose Parts) in Memory
    # -------------------------------------------------------------
    num_faces = len(src_bm.faces)
    components = []
    
    if getattr(settings, "separate_loose_parts", True) and num_faces > 0:
        visited = [False] * num_faces
        for start_idx, start_face in enumerate(src_bm.faces):
            if visited[start_idx]:
                continue
            comp_faces = []
            queue = [start_face]
            visited[start_idx] = True
            while queue:
                curr = queue.pop()
                comp_faces.append(curr)
                for edge in curr.edges:
                    for neighbor in edge.link_faces:
                        n_idx = neighbor.index
                        if not visited[n_idx]:
                            visited[n_idx] = True
                            queue.append(neighbor)
            components.append(comp_faces)
    else:
        components = [list(src_bm.faces)]
        
    num_parts = len(components)
    
    # -------------------------------------------------------------
    # Case A: Single Part
    # -------------------------------------------------------------
    if num_parts <= 1:
        src_bm.free()
        
        # Create single isolated worker object
        temp_mesh = source_obj.data.copy()
        temp_mesh.name = f"{source_obj.name}_AutoQuad_Worker"
        worker_obj = bpy.data.objects.new(temp_mesh.name, temp_mesh)
        worker_obj.matrix_world = source_obj.matrix_world.copy()
        context.collection.objects.link(worker_obj)
        
        for o in bpy.data.objects:
            if o:
                try:
                    o.select_set(False)
                except Exception:
                    pass
        worker_obj.select_set(True)
        context.view_layer.objects.active = worker_obj
        
        if progress_cb:
            progress_cb(1, 1, worker_obj)
        if getattr(settings, "auto_target_quads", False):
            try:
                from .adaptive_density import calculate_optimal_quad_count
                settings.target_quad_count = calculate_optimal_quad_count(worker_obj)
            except Exception:
                pass
                
        try:
            quad_bm = run_retopology_single_part(
                context, worker_obj, settings,
                target_faces=settings.target_quad_count,
                src_bvh=src_bvh
            )
            return quad_bm
        finally:
            try:
                m = worker_obj.data
                bpy.data.objects.remove(worker_obj, do_unlink=True)
                bpy.data.meshes.remove(m, do_unlink=True)
            except Exception:
                pass
                
    # -------------------------------------------------------------
    # Case B: Multi-Part (Separated by Loose Parts in Memory)
    # -------------------------------------------------------------
    from .adaptive_density import calculate_multi_part_budgets
    budgets, target_total = calculate_multi_part_budgets(components, src_bm, settings)
            
    remeshed_bms = []
    
    try:
        for idx, (comp_faces, budget) in enumerate(zip(components, budgets)):
            part_num = idx + 1
            
            # Extract component geometry into a standalone worker object
            comp_bm = bmesh.new()
            v_map = {}
            for f in comp_faces:
                for v in f.verts:
                    if v not in v_map:
                        v_map[v] = comp_bm.verts.new(v.co)
            comp_bm.verts.ensure_lookup_table()
            for f in comp_faces:
                verts = [v_map[v] for v in f.verts]
                if len(set(verts)) >= 3:
                    try:
                        comp_bm.faces.new(verts)
                    except ValueError:
                        pass
            comp_bm.normal_update()
            
            worker_mesh = bpy.data.meshes.new(f"{source_obj.name}_Worker_{idx}")
            comp_bm.to_mesh(worker_mesh)
            comp_bm.free()
            worker_mesh.update()
            
            worker_obj = bpy.data.objects.new(f"{source_obj.name}_Worker_{idx}", worker_mesh)
            worker_obj.matrix_world = source_obj.matrix_world.copy()
            context.collection.objects.link(worker_obj)
            
            # Keep all existing objects (including source_obj) strictly deselected
            for o in bpy.data.objects:
                if o:
                    try:
                        o.select_set(False)
                    except Exception:
                        pass
            worker_obj.select_set(True)
            context.view_layer.objects.active = worker_obj
            
            if progress_cb:
                progress_cb(part_num, num_parts, worker_obj)
                
            status_msg = f"AutoQuad: Remeshing loose part {part_num}/{num_parts} ({len(worker_mesh.polygons):,} polys -> {budget:,} quads)..."
            if hasattr(settings, "processing_status"):
                settings.processing_status = f"Remeshing part {part_num}/{num_parts} ({budget:,} quads)..."
            if hasattr(context, "workspace") and context.workspace:
                try:
                    context.workspace.status_text_set(status_msg)
                except Exception:
                    pass
            if hasattr(context, "area") and context.area:
                try:
                    context.area.tag_redraw()
                except Exception:
                    pass
                    
            try:
                part_bm = run_retopology_single_part(
                    context, worker_obj, settings,
                    target_faces=budget,
                    src_bvh=None
                )
                if part_bm and len(part_bm.faces) > 0:
                    remeshed_bms.append(part_bm)
            finally:
                # Clean up worker object immediately after processing this part
                try:
                    bpy.data.objects.remove(worker_obj, do_unlink=True)
                    bpy.data.meshes.remove(worker_mesh, do_unlink=True)
                except Exception:
                    pass
                    
        # Combine all cleanly remeshed quad parts in memory
        if remeshed_bms:
            final_bm = bmesh.new()
            for qbm in remeshed_bms:
                v_map = {}
                for v in qbm.verts:
                    v_map[v] = final_bm.verts.new(v.co)
                final_bm.verts.ensure_lookup_table()
                for f in qbm.faces:
                    verts = [v_map[v] for v in f.verts]
                    if len(set(verts)) >= 3:
                        try:
                            final_bm.faces.new(verts)
                        except ValueError:
                            pass
                qbm.free()
                
            final_bm.verts.ensure_lookup_table()
            final_bm.faces.ensure_lookup_table()
            final_bm.normal_update()
            return final_bm
            
        return None
        
    finally:
        src_bm.free()
