"""
QuadFlow - One-Click Batch Remesh Operator
Executes complete QuadFlow retopology in a single non-blocking action.
"""

import bpy
import bmesh
from mathutils.bvhtree import BVHTree

from ..core.retopology_engine import run_retopology
from ..utils.validation import validate_mesh_object

class VIEW3D_OT_quadflow_remesh(bpy.types.Operator):
    """Execute complete QuadFlow retopology pipeline with minimal poles"""
    bl_idname = "view3d.quadflow_remesh"
    bl_label = "One-Click Quad Remesh"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        is_valid, err_msg = validate_mesh_object(obj)
        if not is_valid:
            self.report({'ERROR'}, f"QuadFlow: {err_msg}")
            return {'CANCELLED'}
            
        settings = getattr(context.scene, "quadflow_settings", None)
        if not settings:
            self.report({'ERROR'}, "QuadFlow: Settings property group not found.")
            return {'CANCELLED'}
            
        src_bm = bmesh.new()
        src_bm.from_mesh(obj.data)
        src_bm.transform(obj.matrix_world)
        src_bvh = BVHTree.FromBMesh(src_bm, epsilon=1e-5)
        
        try:
            target_bm = run_retopology(context, obj, settings, src_bvh)
            if target_bm is None or len(target_bm.faces) == 0:
                self.report({'ERROR'}, "QuadFlow: Failed to generate quad geometry.")
                return {'CANCELLED'}
                
            new_mesh_data = bpy.data.meshes.new(f"{obj.name}_QuadFlow")
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
            
            new_obj = bpy.data.objects.new(f"{obj.name}_QuadFlow", new_mesh_data)
            new_obj.matrix_world = obj.matrix_world
            context.collection.objects.link(new_obj)
            
            bpy.ops.object.select_all(action='DESELECT')
            new_obj.select_set(True)
            context.view_layer.objects.active = new_obj
            
            quad_count = sum(1 for p in new_mesh_data.polygons if len(p.vertices) == 4)
            total_count = len(new_mesh_data.polygons)
            pct = (quad_count / max(1, total_count)) * 100.0
            self.report({'INFO'}, f"QuadFlow: Generated {quad_count:,} quads ({pct:.1f}% regular quad topology)")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"QuadFlow Error: {e}")
            return {'CANCELLED'}
        finally:
            if src_bm is not None:
                try:
                    src_bm.free()
                except Exception:
                    pass
            if 'target_bm' in locals() and target_bm is not None:
                try:
                    target_bm.free()
                except Exception:
                    pass
