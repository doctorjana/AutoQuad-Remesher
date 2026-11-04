"""
QuadFlow - 3D Viewport UI Panel
Main sidebar (N-Panel) interface in View3D > Sidebar > QuadFlow.
"""

import bpy
from bpy.types import Panel

class VIEW3D_PT_quadflow_main(Panel):
    """QuadFlow Main Sidebar Panel in 3D Viewport"""
    bl_label = "QuadFlow Retopology"
    bl_idname = "VIEW3D_PT_quadflow_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "QuadFlow"
    
    def draw(self, context):
        layout = self.layout
        settings = getattr(context.scene, "quadflow_settings", None)
        if not settings:
            layout.label(text="Settings not initialized", icon='ERROR')
            return
            
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
        row.label(text=f"Polys: {poly_count:,}")
        row.label(text=f"Vertices: {vert_count:,}")
        
        # Action Buttons
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
