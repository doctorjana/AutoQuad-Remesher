"""
QuadFlow - Adaptive Quad Density Field
Calculates target edge length sizing across the 3D surface based on:
1. Geometric curvature (higher density in tight crevices/bevels)
2. Vertex Color or Vertex Group density painting (0.25x to 4x multiplier)
3. Smooth transition edge grading (prevents sudden size jumps)
"""

import math
from mathutils import Vector

class AdaptiveDensityField:
    """
    Computes a scalar target-length field h(x) across the BMesh surface.
    """
    
    def __init__(self, bm, target_quad_count=2500, adaptive_factor=0.65, grading_limit=1.4):
        self.bm = bm
        self.target_quad_count = max(100, target_quad_count)
        self.adaptive_factor = max(0.0, min(1.0, adaptive_factor))
        self.grading_limit = grading_limit
        self.face_target_sizes = {}
        
    def calculate_base_edge_length(self):
        """Calculates nominal edge length to hit the target quad count."""
        total_surface_area = sum(f.calc_area() for f in self.bm.faces)
        if total_surface_area <= 1e-8:
            return 0.1
        
        # In a pure quad mesh, total_area ≈ target_count * (edge_length^2)
        base_edge_len = math.sqrt(total_surface_area / float(self.target_quad_count))
        return max(base_edge_len, 1e-4)

    def evaluate_density_field(self, face_curvatures, vertex_weight_layer=None):
        """
        Combines curvature tensor magnitude and vertex painting to assign
        target edge length per face.
        """
        base_len = self.calculate_base_edge_length()
        raw_sizes = {}
        
        for face in self.bm.faces:
            k1, k2, _, _ = face_curvatures.get(face.index, (0.0, 0.0, None, None))
            # Curvature intensity measure: Frobenius norm of shape operator
            k_magnitude = math.sqrt(k1 * k1 + k2 * k2)
            
            # Curvature scaling: denser where curvature is high
            # scale drops when k_magnitude is large
            curvature_scale = 1.0 / (1.0 + self.adaptive_factor * 3.5 * k_magnitude)
            
            # Vertex weight / paint factor
            weight_factor = 1.0
            if vertex_weight_layer:
                # Average weight across face vertices
                weights = [v[vertex_weight_layer] for v in face.verts if vertex_weight_layer in v]
                if weights:
                    avg_w = sum(weights) / len(weights)
                    # Maps 0.0..1.0 weight to 4.0x density (0.25x size) .. 0.5x density (2.0x size)
                    # Quad Remesher convention: high weight = denser quads = smaller edge size
                    weight_factor = math.pow(0.5, (avg_w - 0.5) * 2.0)
            
            target_size = base_len * curvature_scale * weight_factor
            raw_sizes[face.index] = max(target_size, base_len * 0.15)
            
        # Smooth grading step: ensure neighboring faces do not exceed grading_limit ratio
        graded_sizes = dict(raw_sizes)
        for _ in range(4):
            for face in self.bm.faces:
                current_size = graded_sizes[face.index]
                for edge in face.edges:
                    for neighbor in edge.link_faces:
                        if neighbor == face:
                            continue
                        neigh_size = graded_sizes[neighbor.index]
                        max_allowed = neigh_size * self.grading_limit
                        if current_size > max_allowed:
                            current_size = max_allowed
                graded_sizes[face.index] = current_size
                
        self.face_target_sizes = graded_sizes
        return self.face_target_sizes

def calculate_optimal_quad_count(obj, bm=None):
    """
    Estimates the mathematically optimal target quad count for the given mesh
    to preserve all structural features and silhouettes without distortion or faceting.
    
    Integrates:
    - Dihedral edge curvature & angular turning energy
    - Sharp crease and boundary feature edge lengths
    - Ratio of curved surface area vs flat planar surfaces
    - Bounding dimensions and characteristic scale
    """
    if obj is None or obj.type != 'MESH':
        return 2500
        
    created_bm = False
    if bm is None:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        created_bm = True
        
    try:
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        
        dims = obj.dimensions
        char_size = max(dims.x, dims.y, dims.z, 1e-4)
        
        num_edges = len(bm.edges)
        if num_edges == 0:
            return 1000
            
        curved_edges = 0
        sharp_edges = 0
        flat_edges = 0
        total_turning = 0.0
        
        # Fast sampling for dense sculpts (>20k edges)
        stride = max(1, num_edges // 20000)
        for idx in range(0, num_edges, stride):
            edge = bm.edges[idx]
            if len(edge.link_faces) == 2:
                f1, f2 = edge.link_faces
                dot = max(-1.0, min(1.0, f1.normal.dot(f2.normal)))
                angle = math.acos(dot)
                l = edge.calc_length()
                if angle > math.radians(60.0):
                    sharp_edges += 1
                    total_turning += angle * l
                elif angle > math.radians(5.0):
                    curved_edges += 1
                    total_turning += angle * l
                else:
                    flat_edges += 1
            elif len(edge.link_faces) == 1:
                sharp_edges += 1
                total_turning += (math.pi / 2.0) * edge.calc_length()
                
        total_sample = curved_edges + sharp_edges + flat_edges
        curved_ratio = curved_edges / max(1, total_sample)
        
        total_turning *= stride
        turning_density = total_turning / char_size
        
        # Base quad count: planar surfaces need minimal count, curved needs nominal density
        base = 150.0 + (curved_ratio * 600.0)
        
        # Feature-driven curvature budget
        feature_budget = turning_density * (20.0 + curved_ratio * 40.0)
        
        estimated = base + feature_budget
        estimated = int(round(estimated / 50.0) * 50)
        return max(150, min(50000, estimated))
    finally:
        if created_bm:
            bm.free()
