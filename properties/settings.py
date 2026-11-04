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

class AutoQuadSettings(PropertyGroup):
    """Configuration parameters for AutoQuad Remesher operations."""
    
    # Primary user controls
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
