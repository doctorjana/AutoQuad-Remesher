"""
AutoQuad Remesher - Mesh Preprocessing Utilities
Implements the Make Manifold cleanup logic from Blender's 3D-Print Toolbox (object_print3d_utils)
enhanced with curvature-preserving hole reconstruction and open-boundary preservation.
"""

import bpy
import bmesh
from mathutils import Vector

def make_manifold(context, obj, threshold=0.0001, fill_holes=False, sides=0, preserve_curvature=True):
    """
    Cleans up mesh problems (loose elements, interior faces, duplicate vertices,
    degenerate elements, and inverted normals) following the algorithm from Blender's
    3D-Print Toolbox (MESH_OT_print3d_clean_non_manifold) with smart curvature-preserving
    hole reconstruction.
    
    Parameters:
        context: Blender context
        obj: The mesh object to clean (a temporary working duplicate or active object)
        threshold: Merge distance for remove doubles and degenerate dissolve
        fill_holes: Whether to close boundary holes. When False (default), intentional
                    open boundaries (e.g. cut openings, open sleeves, eye sockets) are
                    preserved cleanly as valid manifold surfaces for remeshing.
        sides: Maximum number of sides for hole filling (0 = all holes)
        preserve_curvature: When filling holes on curved surfaces, inflates and smooths
                            new interior vertices to match the surrounding curvature
                            instead of leaving a flat sunken chord facet.
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
        
        # 6. Optional: Fix boundary holes (only if requested)
        if fill_holes:
            bm = bmesh.from_edit_mesh(obj.data)
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()
            
            b_edges = [e for e in bm.edges if e.is_boundary]
            if b_edges:
                fill_res = bmesh.ops.holes_fill(bm, edges=b_edges, sides=sides)
                new_faces = fill_res.get('faces', [])
                
                # If preserve_curvature: reconstruct sagittal height for large/non-planar holes
                ngons = [f for f in new_faces if len(f.verts) > 4]
                if preserve_curvature and ngons:
                    p_res = bmesh.ops.poke(bm, faces=ngons)
                    poke_verts = p_res.get('verts', [])
                    for pv in poke_verts:
                        b_neighbors = [edge.other_vert(pv) for edge in pv.link_edges]
                        if b_neighbors:
                            avg_b_pos = sum((v.co for v in b_neighbors), Vector((0, 0, 0))) / len(b_neighbors)
                            avg_b_norm = sum((v.normal for v in b_neighbors), Vector((0, 0, 0)))
                            if avg_b_norm.length > 1e-4:
                                avg_b_norm.normalize()
                            else:
                                avg_b_norm = avg_b_pos.normalized() if avg_b_pos.length > 1e-4 else Vector((0, 0, 1))
                                
                            r_origin = sum(v.co.length for v in b_neighbors) / len(b_neighbors)
                            dist_chord = avg_b_pos.length
                            if r_origin > dist_chord:
                                pv.co = avg_b_pos + avg_b_norm * (r_origin - dist_chord)
                                
                    poked_faces = p_res.get('faces', [])
                    poked_edges = list(set(e for f in poked_faces for e in f.edges if not e.is_boundary))
                    if poked_edges:
                        sub_res = bmesh.ops.subdivide_edges(bm, edges=poked_edges, cuts=1)
                        split_verts = [elem for elem in sub_res.get('geom_split', []) if isinstance(elem, bmesh.types.BMVert)]
                        for v in split_verts:
                            if v.co.length > 1e-4 and r_origin > 0:
                                v.co = v.co.normalized() * r_origin
                                
                # Triangulate any remaining high-order N-gons to prevent algorithm skew
                remaining_ngons = [f for f in bm.faces if len(f.verts) > 4]
                if remaining_ngons:
                    bmesh.ops.triangulate(bm, faces=remaining_ngons, quad_method='BEAUTY', ngon_method='BEAUTY')
                    
            bmesh.update_edit_mesh(obj.data)
            
        # 7. Make all normals face consistently outwards
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        
    finally:
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
