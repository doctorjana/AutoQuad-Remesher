"""
QuadFlow - Extension Properties and Settings
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

class QuadFlowSettings(PropertyGroup):
    """Configuration parameters for QuadFlow retopology operations."""
    
    target_quad_count: IntProperty(
        name="Target Quads",
        description="Target quad polygon count for the retopologized mesh",
        default=2500,
        min=50,
        max=100000
    )
    
    adaptive_size: FloatProperty(
        name="Adaptive Size",
        description="Increases quad density in high-curvature areas (0.0 = uniform grid, 1.0 = highly adaptive)",
        default=0.65,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )
    
    curvature_influence: FloatProperty(
        name="Curvature Flow",
        description="Weight given to natural surface curvature vectors vs uniform grid",
        default=0.85,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )
    
    use_symmetry: BoolProperty(
        name="Symmetry",
        description="Enforces topological mirror symmetry and central seam alignment",
        default=True
    )
    
    symmetry_axis: EnumProperty(
        name="Symmetry Axis",
        description="Axis across which to enforce symmetry",
        items=[
            ('X', "X-Axis (Left / Right)", "Mirror along X axis"),
            ('Y', "Y-Axis (Front / Back)", "Mirror along Y axis"),
            ('Z', "Z-Axis (Top / Bottom)", "Mirror along Z axis"),
        ],
        default='X'
    )
    
    detect_hard_edges: BoolProperty(
        name="Detect Hard Edges",
        description="Automatically align quad flow along sharp angle edges",
        default=True
    )
    
    hard_edge_angle: FloatProperty(
        name="Crease Angle",
        description="Dihedral angle threshold to classify an edge as a sharp feature",
        default=45.0,
        min=15.0,
        max=90.0,
        unit='ROTATION'
    )
    
    use_marked_creases: BoolProperty(
        name="Use Marked Creases",
        description="Honor edges explicitly marked as Sharp or Seam",
        default=True
    )
    
    use_material_boundaries: BoolProperty(
        name="Material Boundaries",
        description="Guide quad loops along material assignment borders",
        default=False
    )
    
    guide_collection: PointerProperty(
        name="Guide Curves",
        type=bpy.types.Collection,
        description="Optional collection containing curve strokes to guide edge loops"
    )
    
    density_vertex_group: StringProperty(
        name="Density Weight Map",
        description="Name of Vertex Group driving local polygon density (0.25x to 4x)"
    )
    
    # In-Viewport Visualization options
    show_cross_field: BoolProperty(
        name="Show 4-RoSy Vectors",
        description="Render cross-field flow vectors in the 3D viewport using GPU shaders",
        default=True
    )
    
    show_streamlines: BoolProperty(
        name="Show Flow Loops",
        description="Render planned quad streamline guides in the 3D viewport",
        default=True
    )
    
    relaxation_steps: IntProperty(
        name="Relaxation Steps",
        description="Number of Laplacian smoothing and surface reprojection iterations",
        default=12,
        min=1,
        max=50
    )
