"""
AutoQuad Remesher - Responsive Asynchronous Remesh Operator
Executes complete quad remeshing pipeline using generator-driven modal stepping,
providing live status updates, animating the loading indicator, and allowing user cancellation via ESC.
"""

import bpy
import bmesh
from mathutils.bvhtree import BVHTree

from ..core.retopology_engine import run_retopology, run_retopology_steps
from ..utils.validation import validate_mesh_object


def _tag_redraw_all(context):
    """Tags redraw across all relevant viewport and UI areas."""
    if context and hasattr(context, "screen") and context.screen:
        for area in context.screen.areas:
            if area.type in {'VIEW_3D', 'PROPERTIES'}:
                area.tag_redraw()


class VIEW3D_OT_autoquad_remesh(bpy.types.Operator):
    """Execute AutoQuad remeshing pipeline"""
    bl_idname = "view3d.autoquad_remesh"
    bl_label = "Remesh"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None
    _step_gen = None
    _src_obj = None
    _src_bm = None
    _src_bvh = None

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

        # In headless / background mode (CLI tests), execute synchronously
        if getattr(bpy.app, "background", False):
            return self.execute(context)

        # In interactive GUI mode: initialize modal generator and visual indicators
        settings.is_processing = True
        settings.processing_status = "Analyzing geometry..."
        self._src_obj = obj

        # Build reference BVH for raycast relaxation / snapping
        self._src_bm = bmesh.new()
        self._src_bm.from_mesh(obj.data)
        self._src_bm.transform(obj.matrix_world)
        self._src_bvh = BVHTree.FromBMesh(self._src_bm, epsilon=1e-5)

        # Initialize generator state machine
        self._step_gen = run_retopology_steps(context, obj, settings, src_bvh=self._src_bvh)

        if hasattr(context, "workspace") and context.workspace:
            try:
                context.workspace.status_text_set("AutoQuad: Initializing... [ESC to Cancel]")
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

        # Timer ticks every 0.02s (~50Hz) to advance generator while allowing UI repaints
        self._timer = context.window_manager.event_timer_add(0.02, window=context.window)
        context.window_manager.modal_handler_add(self)
        _tag_redraw_all(context)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        # 1. User Cancellation
        if event.type == 'ESC':
            self._cleanup_all(context, cancelled=True)
            self.report({'INFO'}, "AutoQuad: Remeshing cancelled by user.")
            return {'CANCELLED'}

        # 2. Timer Event: Advance Pipeline State Machine
        if event.type == 'TIMER':
            if self._step_gen is None:
                self._cleanup_all(context)
                return {'CANCELLED'}

            try:
                stage, msg, step, total_steps, payload = next(self._step_gen)

                # Update settings for sidebar panel loading indicator
                settings = getattr(context.scene, "autoquad_settings", None)
                if settings is None:
                    settings = getattr(context.scene, "quadflow_settings", None)
                if settings:
                    settings.processing_status = msg

                # Update window status bar
                if hasattr(context, "workspace") and context.workspace:
                    try:
                        pct = int((step / max(1, total_steps)) * 100)
                        context.workspace.status_text_set(f"AutoQuad: {msg} ({pct}%) [ESC to Cancel]")
                    except Exception:
                        pass

                _tag_redraw_all(context)

                # Final stage reached: payload is the recombined BMesh
                if stage == "FINISHED":
                    target_bm = payload
                    return self._finish_remesh(context, target_bm)

            except StopIteration:
                self._cleanup_all(context)
                return {'FINISHED'}
            except Exception as e:
                self._cleanup_all(context, cancelled=True)
                self.report({'ERROR'}, f"AutoQuad Error: {e}")
                return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        """Synchronous execution fallback for headless / background CLI mode."""
        obj = context.active_object
        is_valid, err_msg = validate_mesh_object(obj)
        if not is_valid:
            self.report({'ERROR'}, f"AutoQuad: {err_msg}")
            return {'CANCELLED'}

        settings = getattr(context.scene, "autoquad_settings", None)
        if settings is None:
            settings = getattr(context.scene, "quadflow_settings", None)

        if not settings:
            self.report({'ERROR'}, "AutoQuad: Settings property group not found.")
            return {'CANCELLED'}

        self._src_obj = obj
        self._src_bm = bmesh.new()
        self._src_bm.from_mesh(obj.data)
        self._src_bm.transform(obj.matrix_world)
        self._src_bvh = BVHTree.FromBMesh(self._src_bm, epsilon=1e-5)

        try:
            target_bm = run_retopology(context, obj, settings, self._src_bvh)
            return self._finish_remesh(context, target_bm)
        except Exception as e:
            self._cleanup_all(context)
            self.report({'ERROR'}, f"AutoQuad Error: {e}")
            return {'CANCELLED'}

    def _finish_remesh(self, context, target_bm):
        """Finalizes and links the generated quad mesh object."""
        try:
            if target_bm is None or len(target_bm.faces) == 0:
                self.report(
                    {'ERROR'},
                    "AutoQuad: Unable to generate quad topology. "
                    "If your mesh has severe non-manifold tears, try enabling 'Preprocess Mesh' in Advanced Options."
                )
                return {'CANCELLED'}

            obj = self._src_obj or context.active_object
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

            # Hide original mesh if enabled
            settings = getattr(context.scene, "autoquad_settings", None)
            if settings and getattr(settings, "hide_original", True):
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

        finally:
            if target_bm is not None:
                try:
                    target_bm.free()
                except Exception:
                    pass
            self._cleanup_all(context)

    def _cleanup_all(self, context, cancelled=False):
        """Restores cursor, removes timer, clears status, and cleans up worker objects."""
        # 1. Reset settings indicators
        settings = getattr(context.scene, "autoquad_settings", None)
        if settings is None:
            settings = getattr(context.scene, "quadflow_settings", None)
        if settings:
            settings.is_processing = False
            if hasattr(settings, "processing_status"):
                settings.processing_status = "Remeshing in progress..."

        # 2. Reset workspace status text
        if hasattr(context, "workspace") and context.workspace:
            try:
                context.workspace.status_text_set(None)
            except Exception:
                pass

        # 3. Remove modal event timer
        if self._timer and hasattr(context, "window_manager") and context.window_manager:
            try:
                context.window_manager.event_timer_remove(self._timer)
            except Exception:
                pass
            self._timer = None

        # 4. Restore mouse cursor
        if hasattr(context, "window") and context.window:
            try:
                context.window.cursor_modal_restore()
            except Exception:
                try:
                    context.window.cursor_set('DEFAULT')
                except Exception:
                    pass

        # 5. Free source BMesh and BVH
        if self._src_bm is not None:
            try:
                self._src_bm.free()
            except Exception:
                pass
            self._src_bm = None
        self._src_bvh = None
        self._step_gen = None

        # 6. Clean up any lingering worker objects or meshes (especially on cancel)
        if self._src_obj:
            prefix = f"{self._src_obj.name}_"
            for ob in list(bpy.data.objects):
                if ob and ob.name.startswith(prefix) and ("Worker" in ob.name or "AutoQuad_Worker" in ob.name):
                    m = ob.data
                    try:
                        bpy.data.objects.remove(ob, do_unlink=True)
                        if m:
                            bpy.data.meshes.remove(m, do_unlink=True)
                    except Exception:
                        pass

        _tag_redraw_all(context)


class VIEW3D_OT_quadflow_remesh(bpy.types.Operator):
    """Backward-compatibility operator alias for quadflow_remesh"""
    bl_idname = "view3d.quadflow_remesh"
    bl_label = "Remesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return bpy.ops.view3d.autoquad_remesh('EXEC_DEFAULT')
