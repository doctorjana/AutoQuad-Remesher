"""
AutoQuad Remesher - Remesh Operator with Interactive Loading Indicator
Executes complete quad remeshing pipeline with visual progress and cursor feedback.
"""

import bpy
import bmesh
from mathutils.bvhtree import BVHTree

from ..core.retopology_engine import run_retopology
from ..utils.validation import validate_mesh_object

class VIEW3D_OT_autoquad_remesh(bpy.types.Operator):
    """Execute AutoQuad remeshing pipeline"""
    bl_idname = "view3d.autoquad_remesh"
    bl_label = "Remesh"
    bl_options = {'REGISTER', 'UNDO'}
    
    _timer = None
    
    def invoke(self, context, event):
        obj = context.active_object
        is_valid, err_msg = validate_mesh_object(obj)
        if not is_valid:
            self.report({'ERROR'}, f"AutoQuad: {err_msg}")
            return {'CANCELLED'}
            
        settings = getattr(context.scene, "autoquad_settings", None)
        if settings is None:
            settings = getattr(context.scene, "quadflow_settings", None)
            
        if not settings:
            self.report({'ERROR'}, "AutoQuad: Settings not found.")
            return {'CANCELLED'}
            
        # If in headless / background mode, execute synchronously
        if getattr(bpy.app, "background", False):
            return self.execute(context)
            
        # In GUI mode: Activate UI loading indicator, precision cursor, and status text, then yield a frame for redraw
        settings.is_processing = True
        if hasattr(context, "area") and context.area:
            context.area.tag_redraw()
            
        if hasattr(context, "workspace") and context.workspace:
            try:
                context.workspace.status_text_set("AutoQuad: Remeshing quad topology in progress...")
            except Exception:
                pass

        if hasattr(context, "window") and context.window:
            try:
                context.window.cursor_modal_set('CROSSHAIR')
            except Exception:
                try:
                    context.window.cursor_set('CROSSHAIR')
                except Exception:
                    pass
                    
        self._timer = context.window_manager.event_timer_add(0.01, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'TIMER':
            if self._timer and context.window_manager:
                try:
                    context.window_manager.event_timer_remove(self._timer)
                except Exception:
                    pass
                self._timer = None
            return self.execute(context)
        return {'PASS_THROUGH'}
        
    def execute(self, context):
        obj = context.active_object
        is_valid, err_msg = validate_mesh_object(obj)
        if not is_valid:
            self.report({'ERROR'}, f"AutoQuad: {err_msg}")
            self._cleanup_loading(context)
            return {'CANCELLED'}
            
        settings = getattr(context.scene, "autoquad_settings", None)
        if settings is None:
            settings = getattr(context.scene, "quadflow_settings", None)
            
        if not settings:
            self.report({'ERROR'}, "AutoQuad: Settings property group not found.")
            self._cleanup_loading(context)
            return {'CANCELLED'}
            
        wm = getattr(context, "window_manager", None)
        if wm and hasattr(wm, "progress_begin"):
            try:
                wm.progress_begin(0, 100)
            except Exception:
                pass
                
        src_bm = bmesh.new()
        src_bm.from_mesh(obj.data)
        src_bm.transform(obj.matrix_world)
        src_bvh = BVHTree.FromBMesh(src_bm, epsilon=1e-5)
        target_bm = None
        
        try:
            if wm and hasattr(wm, "progress_update"):
                try:
                    wm.progress_update(25)
                except Exception:
                    pass
                    
            target_bm = run_retopology(context, obj, settings, src_bvh)
            if target_bm is None or len(target_bm.faces) == 0:
                self.report({'ERROR'}, "AutoQuad: Failed to generate quad geometry.")
                return {'CANCELLED'}
                
            if wm and hasattr(wm, "progress_update"):
                try:
                    wm.progress_update(75)
                except Exception:
                    pass
                    
            new_mesh_data = bpy.data.meshes.new(f"{obj.name}_AutoQuad")
            world_inv = obj.matrix_world.inverted()
            target_bm.transform(world_inv)
            target_bm.normal_update()
            target_bm.to_mesh(new_mesh_data)
            
            try:
                new_mesh_data.validate(clean_customdata=True)
            except Exception:
                pass
            new_mesh_data.update()
            
            for poly in new_mesh_data.polygons:
                poly.use_smooth = True
            
            new_obj = bpy.data.objects.new(f"{obj.name}_AutoQuad", new_mesh_data)
            new_obj.matrix_world = obj.matrix_world
            context.collection.objects.link(new_obj)
            
            # Hide original mesh if option is enabled
            if getattr(settings, "hide_original", True):
                try:
                    obj.hide_viewport = True
                    obj.hide_render = True
                    obj.hide_set(True)
                except Exception:
                    pass
            
            # Select and activate newly generated quad mesh
            bpy.ops.object.select_all(action='DESELECT')
            new_obj.select_set(True)
            context.view_layer.objects.active = new_obj
            
            quad_count = sum(1 for p in new_mesh_data.polygons if len(p.vertices) == 4)
            total_count = len(new_mesh_data.polygons)
            pct = (quad_count / max(1, total_count)) * 100.0
            self.report({'INFO'}, f"AutoQuad: Generated {quad_count:,} quads ({pct:.1f}% clean quad topology)")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"AutoQuad Error: {e}")
            return {'CANCELLED'}
        finally:
            if wm and hasattr(wm, "progress_end"):
                try:
                    wm.progress_end()
                except Exception:
                    pass
            if src_bm is not None:
                try:
                    src_bm.free()
                except Exception:
                    pass
            if target_bm is not None:
                try:
                    target_bm.free()
                except Exception:
                    pass
            self._cleanup_loading(context)

    def _cleanup_loading(self, context):
        """Restores cursor, clears status text, removes timer, and resets processing flag."""
        settings = getattr(context.scene, "autoquad_settings", None)
        if settings is None:
            settings = getattr(context.scene, "quadflow_settings", None)
        if settings:
            settings.is_processing = False
            
        if hasattr(context, "workspace") and context.workspace:
            try:
                context.workspace.status_text_set(None)
            except Exception:
                pass

        if self._timer and hasattr(context, "window_manager") and context.window_manager:
            try:
                context.window_manager.event_timer_remove(self._timer)
            except Exception:
                pass
            self._timer = None
            
        if hasattr(context, "window") and context.window:
            try:
                context.window.cursor_modal_restore()
            except Exception:
                try:
                    context.window.cursor_set('DEFAULT')
                except Exception:
                    pass
                    
        if hasattr(context, "area") and context.area:
            context.area.tag_redraw()


class VIEW3D_OT_quadflow_remesh(bpy.types.Operator):
    """Backward-compatibility operator alias for quadflow_remesh"""
    bl_idname = "view3d.quadflow_remesh"
    bl_label = "Remesh"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        return bpy.ops.view3d.autoquad_remesh('EXEC_DEFAULT')
