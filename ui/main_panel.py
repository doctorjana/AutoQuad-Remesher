"""
AutoQuad Remesher - Clean 3D Viewport UI Panel
Streamlined, uncluttered interface in View3D > Sidebar > AutoQuad.
"""

import bpy
from bpy.types import Panel

class VIEW3D_PT_autoquad_main(Panel):
    """AutoQuad Remesher Sidebar Panel in 3D Viewport"""
    bl_label = "AutoQuad Remesher"
    bl_idname = "VIEW3D_PT_autoquad_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AutoQuad"
    
    def draw(self, context):
        layout = self.layout
        settings = getattr(context.scene, "autoquad_settings", None)
        if settings is None:
            settings = getattr(context.scene, "quadflow_settings", None)
            
        if not settings:
            layout.label(text="Settings not initialized", icon='ERROR')
            return
            
        active_obj = context.active_object
        
        # Object validation
        if not active_obj or active_obj.type != 'MESH':
            layout.label(text="Select a Mesh Object", icon='INFO')
            return
            
        mesh = active_obj.data
        poly_count = len(mesh.polygons)
        vert_count = len(mesh.vertices)
        
        # Target Mesh Information
        box = layout.box()
        box.label(text=f"Active: {active_obj.name}", icon='MESH_DATA')
        row = box.row()
        row.label(text=f"Polys: {poly_count:,}")
        row.label(text=f"Vertices: {vert_count:,}")
        
        layout.separator()
        
        # Remesh Button & Dynamic Loading Indicator
        if settings.is_processing:
            load_box = layout.box()
            load_row = load_box.row(align=True)
            load_row.scale_y = 1.6
            load_row.alignment = 'CENTER'
            load_row.label(text="Remeshing in progress...", icon='TIME')
        else:
            col = layout.column(align=True)
            col.scale_y = 1.5
            col.operator("view3d.autoquad_remesh", text="Remesh", icon='MOD_REMESH')
            
        layout.separator()
        
        # Clean Core Settings
        col = layout.column(align=True)
        col.prop(settings, "target_quad_count")
        col.prop(settings, "adaptive_size")
        
        # Advanced Options Collapsible Box
        layout.separator()
        adv_box = layout.box()
        adv_row = adv_box.row()
        adv_row.prop(
            settings,
            "show_advanced",
            icon='TRIA_DOWN' if settings.show_advanced else 'TRIA_RIGHT',
            text="Advanced Options",
            emboss=False
        )
        if settings.show_advanced:
            inner_col = adv_box.column()
            inner_col.prop(settings, "preprocess_mesh")
            inner_col.prop(settings, "hide_original")

# Backward-compatibility alias
VIEW3D_PT_quadflow_main = VIEW3D_PT_autoquad_main
