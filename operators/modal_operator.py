"""
QuadFlow - Interactive In-Viewport Modal Operator
Interactive retopology session with live GPU cross-field overlays and real-time surface relaxation.
"""

import math
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from ..core.curvature_field import CurvatureFieldSolver
from ..core.relaxation import SurfaceRelaxationEngine
from ..core.retopology_engine import run_retopology
from ..ui.gpu_drawing import register_draw_handlers, unregister_draw_handlers
from ..utils.validation import validate_mesh_object

class VIEW3D_OT_quadflow_modal(bpy.types.Operator):
    """Interactive In-Viewport Retopology with live GPU field overlays"""
    bl_idname = "view3d.quadflow_modal"
    bl_label = "Interactive Retopology"
    bl_options = {'REGISTER', 'UNDO'}
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_running = False
        self.phase_name = "1. Curvature & 4-RoSy Analysis"
        self.current_step = 0
        self.draw_lines_coords = []
        self.draw_lines_colors = []
        self.timer = None
        self.source_obj = None
        self.source_bm = None
        self.target_bm = None
        self.relaxation_engine = None
        self.is_auto_relaxing = False
        self.target_quad_count = 2500

    def invoke(self, context, event):
        if context.area.type != 'VIEW_3D':
            self.report({'WARNING'}, "QuadFlow: 3D Viewport area not found.")
            return {'CANCELLED'}
            
        obj = context.active_object
        is_valid, err_msg = validate_mesh_object(obj)
        if not is_valid:
            self.report({'ERROR'}, f"QuadFlow: {err_msg}")
            return {'CANCELLED'}
            
        settings = getattr(context.scene, "quadflow_settings", None)
        if not settings:
            self.report({'ERROR'}, "QuadFlow: Settings not found.")
            return {'CANCELLED'}
            
        self.source_obj = obj
        self.target_quad_count = settings.target_quad_count
        
        # Build source bmesh in world coordinates
        self.source_bm = bmesh.new()
        self.source_bm.from_mesh(obj.data)
        self.source_bm.transform(obj.matrix_world)
        self.source_bm.verts.ensure_lookup_table()
        self.source_bm.faces.ensure_lookup_table()
        src_bvh = BVHTree.FromBMesh(self.source_bm, epsilon=1e-5)
        
        # Step 1: Solve curvature and 4-RoSy field for in-viewport overlay lines
        self.phase_name = "1. Computing Curvature & 4-RoSy Cross Field"
        field_solver = CurvatureFieldSolver(
            self.source_bm,
            sharp_angle_threshold=math.radians(settings.hard_edge_angle),
            use_creases=settings.use_marked_creases
        )
        field_solver.identify_feature_edges()
        field_solver.compute_face_curvatures()
        cross_fields = field_solver.solve_4rosy_cross_field(smoothing_iterations=6)
        
        # Populate GPU draw lines for 4-RoSy needles
        self.draw_lines_coords.clear()
        self.draw_lines_colors.clear()
        
        needle_len = 0.03
        for face in self.source_bm.faces:
            if face.index % 2 == 0:
                c = face.calc_center_median()
                vec = cross_fields.get(face.index, Vector((1, 0, 0))) * needle_len
                ortho = face.normal.cross(vec).normalized() * needle_len
                
                # Cross needle 1 (cyan)
                self.draw_lines_coords.extend([c - vec, c + vec])
                self.draw_lines_colors.extend([(0.22, 0.74, 0.97, 0.8), (0.22, 0.74, 0.97, 0.8)])
                # Cross needle 2 (orange)
                self.draw_lines_coords.extend([c - ortho, c + ortho])
                self.draw_lines_colors.extend([(0.96, 0.62, 0.04, 0.8), (0.96, 0.62, 0.04, 0.8)])
                
        # Step 2: Generate clean quad topology
        self.phase_name = "2. Generating Clean Quad Topology"
        self.target_bm = run_retopology(context, obj, settings, src_bvh)
        
        # Step 3: Setup Relaxation Engine
        self.phase_name = "3. Live Surface Relaxation Ready"
        self.relaxation_engine = SurfaceRelaxationEngine(
            self.target_bm,
            src_bvh,
            symmetry_axis=settings.symmetry_axis,
            lock_symmetry=settings.use_symmetry
        )
        
        # Register Viewport Draw Handlers
        register_draw_handlers(self, context)
        
        self.is_running = True
        context.window_manager.modal_handler_add(self)
        self.timer = context.window_manager.event_timer_add(0.04, window=context.window)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()
        
        if event.type == 'ESC':
            self.cleanup(context)
            self.report({'INFO'}, "QuadFlow: In-viewport retopology cancelled")
            return {'CANCELLED'}
            
        elif event.type == 'RET' and event.value == 'PRESS':
            self.commit_quad_mesh(context)
            quads = len(self.target_bm.faces) if self.target_bm else 0
            self.cleanup(context)
            self.report({'INFO'}, f"QuadFlow: Generated {quads:,} clean quads")
            return {'FINISHED'}
            
        elif event.type == 'SPACE' and event.value == 'PRESS':
            self.is_auto_relaxing = not self.is_auto_relaxing
            self.phase_name = "Relaxing Quads Live..." if self.is_auto_relaxing else "Relaxation Paused"
            return {'RUNNING_MODAL'}
            
        elif event.type == 'TIMER':
            if self.is_auto_relaxing and self.relaxation_engine:
                self.current_step += 1
                self.relaxation_engine.step_relaxation()
                if self.current_step >= 30:
                    self.is_auto_relaxing = False
                    self.phase_name = "Relaxation Converged"
            return {'RUNNING_MODAL'}
            
        elif event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} and event.value == 'PRESS':
            delta = 250 if event.type == 'WHEELUPMOUSE' else -250
            self.target_quad_count = max(200, self.target_quad_count + delta)
            return {'RUNNING_MODAL'}
            
        return {'PASS_THROUGH'}

    def commit_quad_mesh(self, context):
        if not self.target_bm:
            return
        new_mesh_data = bpy.data.meshes.new(f"{self.source_obj.name}_QuadFlow")
        world_inv = self.source_obj.matrix_world.inverted()
        self.target_bm.transform(world_inv)
        self.target_bm.normal_update()
        self.target_bm.to_mesh(new_mesh_data)
        try:
            new_mesh_data.validate(clean_customdata=True)
        except Exception:
            pass
        new_mesh_data.update()
        for poly in new_mesh_data.polygons:
            poly.use_smooth = True
        
        new_obj = bpy.data.objects.new(f"{self.source_obj.name}_QuadFlow", new_mesh_data)
        new_obj.matrix_world = self.source_obj.matrix_world
        context.collection.objects.link(new_obj)
        
        bpy.ops.object.select_all(action='DESELECT')
        new_obj.select_set(True)
        context.view_layer.objects.active = new_obj

    def cleanup(self, context):
        self.is_running = False
        unregister_draw_handlers()
        
        if self.timer and context and hasattr(context, 'window_manager') and context.window_manager:
            try:
                context.window_manager.event_timer_remove(self.timer)
            except Exception:
                pass
            self.timer = None
            
        if self.source_bm:
            try:
                self.source_bm.free()
            except Exception:
                pass
            self.source_bm = None
            
        if self.target_bm:
            try:
                self.target_bm.free()
            except Exception:
                pass
            self.target_bm = None
            
        if context and hasattr(context, 'area') and context.area:
            context.area.tag_redraw()
