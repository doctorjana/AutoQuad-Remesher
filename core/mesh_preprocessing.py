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
                
                # If preserve_curvature: reconstruct sagittal curvature for non-planar holes
                ngons = [f for f in new_faces if len(f.verts) > 4]
                if preserve_curvature and ngons:
                    small_ngons = [f for f in ngons if len(f.verts) <= 16]
                    large_ngons = [f for f in ngons if len(f.verts) > 16]
                    
                    # For small holes (<= 16 verts): poke to add center vertex and inflate along normal
                    if small_ngons:
                        p_res = bmesh.ops.poke(bm, faces=small_ngons)
                        poke_verts = p_res.get('verts', [])
                        for pv in poke_verts:
                            b_neighbors = [edge.other_vert(pv) for edge in pv.link_edges]
                            if b_neighbors:
                                avg_b_pos = sum((v.co for v in b_neighbors), Vector((0, 0, 0))) / len(b_neighbors)
                                avg_b_norm = sum((v.normal for v in b_neighbors), Vector((0, 0, 0)))
                                if avg_b_norm.length > 1e-4:
                                    avg_b_norm.normalize()
                                else:
                                    avg_b_norm = Vector((0, 0, 1))
                                    
                                avg_radius = sum((v.co - avg_b_pos).length for v in b_neighbors) / len(b_neighbors)
                                pv.co = avg_b_pos + avg_b_norm * (avg_radius * 0.35)
                    
                    # For large holes (> 16 verts): triangulate with beauty layout to prevent extreme pole singularities
                    if large_ngons:
                        bmesh.ops.triangulate(bm, faces=large_ngons, quad_method='BEAUTY', ngon_method='BEAUTY')
                        
                # Triangulate any remaining high-order N-gons
                bm.faces.ensure_lookup_table()
                remaining_ngons = [f for f in bm.faces if len(f.verts) > 4]
                if remaining_ngons:
                    bmesh.ops.triangulate(bm, faces=remaining_ngons, quad_method='BEAUTY', ngon_method='BEAUTY')
                    
                # Post-hole cleanup: remove duplicate overlapping faces created during triangulation
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
                    
                # Remove any interior faces that share edges with >= 3 faces
                bm.edges.ensure_lookup_table()
                interior_faces = set()
                for e in bm.edges:
                    if len(e.link_faces) > 2:
                        for f in e.link_faces[2:]:
                            interior_faces.add(f)
                if interior_faces:
                    bmesh.ops.delete(bm, geom=list(interior_faces), context='FACES')
                    
            bmesh.update_edit_mesh(obj.data)
            
        # 7. Post-clean duplicate vertices and degenerate geometry
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=threshold)
        bpy.ops.mesh.dissolve_degenerate(threshold=threshold)
            
        # 7. Make all normals face consistently outwards
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        
    finally:
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
