"""
QuadFlow - 3D Viewport UI Panel & Overlay Layouts
Creates the N-Panel tab 'QuadFlow' in the 3D Viewport with full parameters:
Target Quad Count, Adaptive Sizing, Symmetry, Feature Preservation,
and In-Viewport Interactive GPU buttons.
"""

import bpy
from bpy.types import Panel, PropertyGroup
from bpy.props import (
    IntProperty,
    FloatProperty,
    BoolProperty,
    EnumProperty,
    PointerProperty,
    StringProperty
)

class QuadFlowSettings(PropertyGroup):
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


class VIEW3D_PT_quadflow_main(Panel):
    """QuadFlow Main Sidebar Panel in 3D Viewport"""
    bl_label = "QuadFlow Retopology"
    bl_idname = "VIEW3D_PT_quadflow_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "QuadFlow"
    
    def draw(self, context):
        layout = self.layout
        settings = context.scene.quadflow_settings
        active_obj = context.active_object
        
        # Object validation header
        col = layout.column(align=True)
        if not active_obj or active_obj.type != 'MESH':
            col.label(text="Select a Mesh Object", icon='INFO')
            return
            
        mesh = active_obj.data
        poly_count = len(mesh.polygons)
        vert_count = len(mesh.vertices)
        
        box = layout.box()
        box.label(text=f"Active: {active_obj.name}", icon='MESH_DATA')
        row = box.row()
        row.label(text=f"Tris/Polys: {poly_count:,}")
        row.label(text=f"Vertices: {vert_count:,}")
        
        # Action Buttons: Big In-Viewport Interactive Trigger
        main_col = layout.column(align=True)
        main_col.scale_y = 1.35
        main_col.operator(
            "view3d.quadflow_modal",
            text="Interactive Viewport Retopology",
            icon='PLAY'
        )
        main_col.operator(
            "view3d.quadflow_remesh",
            text="One-Click Quad Remesh",
            icon='AUTO'
        )
        
        # Target Density Section
        layout.separator()
        box = layout.box()
        box.label(text="Polygon Density", icon='MOD_DECIM')
        col = box.column(align=True)
        col.prop(settings, "target_quad_count")
        col.prop(settings, "adaptive_size")
        col.prop_search(
            settings, "density_vertex_group",
            active_obj, "vertex_groups",
            text="Density Group",
            icon='GROUP_VERTEX'
        )
        
        # Edge Flow & Curvature Guidance
        box = layout.box()
        box.label(text="Edge Flow & Curvature", icon='DRIVER')
        col = box.column(align=True)
        col.prop(settings, "curvature_influence")
        col.prop(settings, "detect_hard_edges")
        if settings.detect_hard_edges:
            col.prop(settings, "hard_edge_angle")
        col.prop(settings, "use_marked_creases")
        col.prop(settings, "use_material_boundaries")
        col.prop(settings, "guide_collection")
        
        # Symmetry Section
        box = layout.box()
        box.label(text="Symmetry", icon='MOD_MIRROR')
        col = box.column(align=True)
        col.prop(settings, "use_symmetry")
        if settings.use_symmetry:
            col.prop(settings, "symmetry_axis", expand=True)
            
        # In-Viewport GPU Overlay toggles
        box = layout.box()
        box.label(text="In-Viewport Overlays", icon='SHADING_BBOX')
        col = box.column(align=True)
        col.prop(settings, "show_cross_field")
        col.prop(settings, "show_streamlines")
        col.prop(settings, "relaxation_steps")
