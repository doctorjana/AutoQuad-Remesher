"""
AutoQuad Remesher - Extension Properties and Settings
Defines the user-configurable settings and algorithm parameters.
"""

import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    IntProperty,
    FloatProperty,
    BoolProperty,
    EnumProperty,
    PointerProperty,
    StringProperty
)

def _update_auto_quads(self, context):
    if self.auto_target_quads and context and hasattr(context, "active_object"):
        obj = context.active_object
        if obj and obj.type == 'MESH':
            try:
                from ..core.adaptive_density import calculate_optimal_quad_count
                self.target_quad_count = calculate_optimal_quad_count(obj)
            except Exception:
                pass

class AutoQuadSettings(PropertyGroup):
    """Configuration parameters for AutoQuad Remesher operations."""
    
    # Primary user controls
    auto_target_quads: BoolProperty(
        name="Optimal Quads (Auto)",
        description="Automatically compute feature-preserving optimal quad count without manual input",
        default=False,
        update=_update_auto_quads
    )
    
    target_quad_count: IntProperty(
        name="Target Quads",
        description="Target quad polygon count for the remeshed geometry",
        default=2500,
        min=50,
        max=100000
    )
    
    adaptive_size: FloatProperty(
        name="Adaptive Size",
        description="Increases quad density in high-curvature areas (0.0 = uniform grid, 1.0 = adaptive)",
        default=0.65,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )
    
    # Advanced options
    show_advanced: BoolProperty(
        name="Advanced Options",
        description="Toggle display of advanced operational settings",
        default=False
    )
    
    preprocess_mesh: BoolProperty(
        name="Preprocess Mesh",
        description="Clean and repair non-manifold geometry before remeshing using 3D Print Toolbox Make Manifold logic",
        default=False
    )
    
    fill_holes_on_preprocess: BoolProperty(
        name="Fill Holes",
        description="Seal open boundary holes when preprocessing (uncheck to preserve open surfaces and cut openings)",
        default=False
    )
    
    use_decimate: BoolProperty(
        name="Decimate Mesh",
        description="Non-destructively decimate or unsubdivide the working guide mesh before remeshing",
        default=False
    )
    
    decimate_mode: EnumProperty(
        name="Decimate Method",
        description="Method used to decimate the working guide mesh",
        items=[
            ('COLLAPSE', "Collapse (Ratio)", "Collapses edges by ratio (default 0.1 / 10% remaining)"),
            ('UNSUBDIV', "Un-Subdivide", "Reverses grid subdivision levels on quad meshes"),
        ],
        default='COLLAPSE'
    )
    
    decimate_ratio: FloatProperty(
        name="Ratio",
        description="Target fraction of faces to keep (0.1 = keep 10% / decimate 90%)",
        default=0.1,
        min=0.001,
        max=1.0,
        subtype='FACTOR'
    )
    
    decimate_unsubdivide_iterations: IntProperty(
        name="Iterations",
        description="Number of grid subdivision levels to roll back",
        default=2,
        min=1,
        max=16
    )
    
    hide_original: BoolProperty(
        name="Hide Original Mesh",
        description="Hide the source mesh object automatically after remeshing is generated",
        default=True
    )
    
    # Operational state for loading indicator
    is_processing: BoolProperty(
        name="Is Processing",
        description="Active state indicator during remeshing calculation",
        default=False
    )
    
    # Internal algorithm defaults (symmetry completely disabled)
    use_symmetry: BoolProperty(
        name="Symmetry",
        description="Symmetry is disabled",
        default=False
    )
    
    symmetry_axis: EnumProperty(
        name="Symmetry Axis",
        items=[
            ('X', "X-Axis", "Mirror along X axis"),
            ('Y', "Y-Axis", "Mirror along Y axis"),
            ('Z', "Z-Axis", "Mirror along Z axis"),
        ],
        default='X'
    )
    
    detect_hard_edges: BoolProperty(default=True)
    hard_edge_angle: FloatProperty(default=45.0)
    use_marked_creases: BoolProperty(default=True)
    use_material_boundaries: BoolProperty(default=False)
    curvature_influence: FloatProperty(default=0.85)
    density_vertex_group: StringProperty(default="")
    relaxation_steps: IntProperty(default=10)
    show_cross_field: BoolProperty(default=False)
    show_streamlines: BoolProperty(default=False)

# Backward-compatibility alias
QuadFlowSettings = AutoQuadSettings
