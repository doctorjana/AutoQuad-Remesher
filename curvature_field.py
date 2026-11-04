"""
QuadFlow - Curvature Field & 4-RoSy Cross-Field Solver
Computes discrete differential geometry on BMesh surfaces to extract
principal curvature axes (k_min, k_max) and solves a smooth 4-rotational
symmetry (4-RoSy) direction field aligned with features and boundary loops.
"""

import math
import mathutils
from mathutils import Vector, Matrix

class CurvatureFieldSolver:
    """
    Evaluates discrete shape operators per vertex and face, and computes
    a smooth 4-RoSy cross-field across the mesh topology.
    """
    
    def __init__(self, bm, sharp_angle_threshold=math.radians(45.0), use_creases=True):
        self.bm = bm
        self.sharp_angle_threshold = sharp_angle_threshold
        self.use_creases = use_creases
        self.face_curvatures = {}    # face_index -> (k_min, k_max, dir_min, dir_max)
        self.face_cross_fields = {}  # face_index -> Vector (tangent direction 0..pi/2)
        self.feature_edges = set()   # set of edge indices identified as sharp/crease
        
    def identify_feature_edges(self):
        """Identifies sharp creases, boundary edges, and material seams."""
        self.bm.edges.ensure_lookup_table()
        self.feature_edges.clear()
        
        for edge in self.bm.edges:
            # Boundary edges are strict features
            if edge.is_boundary:
                self.feature_edges.add(edge.index)
                continue
                
            # Marked sharp or crease
            if self.use_creases and (not edge.smooth or edge.seam):
                self.feature_edges.add(edge.index)
                continue
                
            # Check dihedral angle between adjacent faces
            if len(edge.link_faces) == 2:
                f1, f2 = edge.link_faces
                angle = f1.normal.angle(f2.normal, 0.0)
                if angle >= self.sharp_angle_threshold:
                    self.feature_edges.add(edge.index)

    def compute_face_curvatures(self):
        """
        Estimates principal curvatures using normal variations between adjacent faces.
        For each face, projects neighbor normal deltas to approximate the Weingarten map.
        """
        self.bm.faces.ensure_lookup_table()
        
        for face in self.bm.faces:
            n = face.normal.normalized()
            center = face.calc_center_median()
            
            # Construct local orthonormal tangent frame (e1, e2, n)
            # Find an arbitrary vector non-parallel to n
            up = Vector((0.0, 0.0, 1.0)) if abs(n.z) < 0.9 else Vector((1.0, 0.0, 0.0))
            e1 = n.cross(up).normalized()
            e2 = n.cross(e1).normalized()
            
            # Accumulate directional curvature estimates from adjacent faces
            # II(v) = - <dv, dn> / <dv, dv>
            a_sum = 0.0  # II(e1, e1)
            b_sum = 0.0  # II(e1, e2)
            c_sum = 0.0  # II(e2, e2)
            weight_sum = 0.0
            
            for edge in face.edges:
                other_face = None
                for lf in edge.link_faces:
                    if lf != face:
                        other_face = lf
                        break
                
                if not other_face:
                    continue
                    
                other_center = other_face.calc_center_median()
                dv = other_center - center
                # Project dv into tangent plane
                dv_proj = dv - n * dv.dot(n)
                dist = dv_proj.length
                if dist < 1e-6:
                    continue
                
                v_unit = dv_proj / dist
                dn = other_face.normal - n
                # Directional normal curvature
                k_n = -dn.dot(v_unit) / dist
                
                # Decompose v_unit into (e1, e2)
                vx = v_unit.dot(e1)
                vy = v_unit.dot(e2)
                
                # Weight by inverse distance
                w = 1.0 / dist
                a_sum += w * (vx * vx) * k_n
                b_sum += w * (vx * vy) * k_n
                c_sum += w * (vy * vy) * k_n
                weight_sum += w
                
            if weight_sum > 1e-6:
                A = a_sum / weight_sum
                B = b_sum / weight_sum
                C = c_sum / weight_sum
            else:
                A, B, C = 0.0, 0.0, 0.0
                
            # Eigendecomposition of 2x2 symmetric Weingarten matrix:
            # [[A, B], [B, C]]
            tr = A + C
            det = A * C - B * B
            discriminant = max(0.0, (tr * tr) / 4.0 - det)
            sqrt_disc = math.sqrt(discriminant)
            
            k1 = tr / 2.0 + sqrt_disc  # Max principal curvature
            k2 = tr / 2.0 - sqrt_disc  # Min principal curvature
            
            # Calculate principal eigenvector direction in tangent plane
            if abs(B) > 1e-6:
                v1_x = k1 - C
                v1_y = B
            elif abs(A - C) > 1e-6:
                v1_x = 1.0 if A > C else 0.0
                v1_y = 0.0 if A > C else 1.0
            else:
                v1_x, v1_y = 1.0, 0.0
                
            len_v1 = math.hypot(v1_x, v1_y)
            if len_v1 > 1e-6:
                v1_x /= len_v1
                v1_y /= len_v1
            else:
                v1_x, v1_y = 1.0, 0.0
                
            dir_max = (e1 * v1_x + e2 * v1_y).normalized()
            dir_min = n.cross(dir_max).normalized()
            
            self.face_curvatures[face.index] = (k1, k2, dir_max, dir_min)

    def solve_4rosy_cross_field(self, smoothing_iterations=8):
        """
        Computes 4-RoSy (4-Rotational Symmetry) field aligned with principal
        curvatures, diffused across planar zones, and snapped to feature edges.
        """
        # Step 1: Initial field assignment from principal curvature or edge alignment
        initial_fields = {}
        for face in self.bm.faces:
            n = face.normal.normalized()
            k1, k2, dir_max, dir_min = self.face_curvatures.get(
                face.index, (0.0, 0.0, Vector((1, 0, 0)), Vector((0, 1, 0)))
            )
            
            # Check if any face edge is a feature edge
            has_feature = False
            for edge in face.edges:
                if edge.index in self.feature_edges:
                    edge_vec = (edge.verts[1].co - edge.verts[0].co).normalized()
                    # Tangent projection
                    edge_tangent = (edge_vec - n * edge_vec.dot(n)).normalized()
                    initial_fields[face.index] = edge_tangent
                    has_feature = True
                    break
                    
            if not has_feature:
                # Use direction of maximum curvature if curvature is significant
                curv_diff = abs(k1 - k2)
                if curv_diff > 0.05:
                    initial_fields[face.index] = dir_min  # Align edge loops along min curvature (fillet flow)
                else:
                    # Weak curvature, use default tangent
                    ref = Vector((0.0, 0.0, 1.0)) if abs(n.z) < 0.9 else Vector((1.0, 0.0, 0.0))
                    initial_fields[face.index] = n.cross(ref).normalized()

        # Step 2: Harmonic 4-RoSy diffusion across neighbors
        current_field = dict(initial_fields)
        
        for _ in range(smoothing_iterations):
            next_field = {}
            for face in self.bm.faces:
                # Keep fixed if on a strict feature edge
                is_feature_locked = any(e.index in self.feature_edges for e in face.edges)
                if is_feature_locked:
                    next_field[face.index] = current_field[face.index]
                    continue
                    
                n = face.normal.normalized()
                v_curr = current_field[face.index]
                accum_vec = Vector((0.0, 0.0, 0.0))
                weight_count = 0.0
                
                for edge in face.edges:
                    for neighbor in edge.link_faces:
                        if neighbor == face:
                            continue
                        
                        v_neigh = current_field[neighbor.index]
                        # Transport v_neigh to face's tangent plane
                        v_neigh_tangent = (v_neigh - n * v_neigh.dot(n))
                        if v_neigh_tangent.length < 1e-5:
                            continue
                        v_neigh_tangent.normalize()
                        
                        # 4-RoSy alignment: choose one of 4 orthogonal rotations of v_neigh_tangent
                        # that minimizes angular difference with v_curr
                        best_match = v_neigh_tangent
                        best_dot = -2.0
                        
                        ortho = n.cross(v_neigh_tangent).normalized()
                        candidates = [
                            v_neigh_tangent,
                            ortho,
                            -v_neigh_tangent,
                            -ortho
                        ]
                        
                        for cand in candidates:
                            dot = cand.dot(v_curr)
                            if dot > best_dot:
                                best_dot = dot
                                best_match = cand
                                
                        accum_vec += best_match
                        weight_count += 1.0
                        
                if weight_count > 0.0 and accum_vec.length > 1e-5:
                    smoothed = (v_curr * 0.4 + (accum_vec / weight_count) * 0.6).normalized()
                    next_field[face.index] = smoothed
                else:
                    next_field[face.index] = v_curr
                    
            current_field = next_field
            
        self.face_cross_fields = current_field
        return self.face_cross_fields
