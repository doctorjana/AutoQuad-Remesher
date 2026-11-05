"""
AutoQuad Remesher - Mesh Preprocessing Utilities
Implements the Make Manifold cleanup logic from Blender's 3D-Print Toolbox (object_print3d_utils).
"""

import bpy
import bmesh

def make_manifold(context, obj, threshold=0.0001, sides=0):
    """
    Cleans up mesh problems (loose elements, interior faces, duplicate vertices,
    degenerate elements, holes, non-manifold boundaries, and inverted normals)
    following the algorithm from Blender's 3D-Print Toolbox (MESH_OT_print3d_clean_non_manifold).
    
    Parameters:
        context: Blender context
        obj: The mesh object to clean (a temporary working duplicate)
        threshold: Merge distance for remove doubles and degenerate dissolve
        sides: Maximum number of sides for hole filling (0 = all holes)
    """
    mode_orig = context.mode
    try:
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj
        
        # 1. Setup environment: Edit mode, vertex selection, reveal all
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.reveal()
        
        # 2. Delete loose vertices, edges, faces
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete_loose(use_verts=True, use_edges=True, use_faces=True)
        
        # 3. Delete interior faces
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_interior_faces()
        bpy.ops.mesh.delete(type='FACE')
        
        # 4. Remove duplicate vertices (merge by distance)
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=threshold)
        
        # 5. Dissolve zero-area faces and zero-length edges
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.dissolve_degenerate(threshold=threshold)
        
        # 6. Fix non-manifold: iterative hole filling and deleting newly created non-manifold verts
        def get_elem_count():
            bm = bmesh.from_edit_mesh(obj.data)
            return len(bm.verts), len(bm.edges), len(bm.faces)
            
        bm_states = set()
        bm_states.add(get_elem_count())
        
        for _ in range(10):
            # Fill holes
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.fill_holes(sides=sides)
            
            # Delete newly generated non-manifold vertices
            bpy.ops.mesh.select_non_manifold(
                extend=False,
                use_wire=True,
                use_boundary=False,
                use_multi_face=False,
                use_non_contiguous=False,
                use_verts=True
            )
            bpy.ops.mesh.delete(type='VERT')
            
            bm_key = get_elem_count()
            if bm_key in bm_states:
                break
            bm_states.add(bm_key)
            
        # 7. Make all normals face consistently outwards
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        
    finally:
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
