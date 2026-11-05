"""
AutoQuad Remesher - Standalone Make Manifold Operator
Allows users to test and run the 3D-Print Toolbox Make Manifold logic directly on any mesh.
"""

import bpy
from ..core.mesh_preprocessing import make_manifold
from ..utils.validation import validate_mesh_object

class VIEW3D_OT_autoquad_make_manifold(bpy.types.Operator):
    """Clean up and make the active mesh manifold using 3D-Print Toolbox repair logic"""
    bl_idname = "view3d.autoquad_make_manifold"
    bl_label = "Make Mesh Manifold"
    bl_description = "Clean up loose elements, interior faces, fill holes, and fix inverted normals"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        is_valid, err_msg = validate_mesh_object(obj)
        if not is_valid:
            self.report({'ERROR'}, f"AutoQuad: {err_msg}")
            return {'CANCELLED'}
            
        initial_verts = len(obj.data.vertices)
        initial_faces = len(obj.data.polygons)
        
        try:
            make_manifold(context, obj)
            obj.data.update()
            
            final_verts = len(obj.data.vertices)
            final_faces = len(obj.data.polygons)
            
            self.report(
                {'INFO'},
                f"AutoQuad: Mesh made manifold ({final_verts:,} verts, {final_faces:,} faces)"
            )
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"AutoQuad Make Manifold error: {e}")
            return {'CANCELLED'}
