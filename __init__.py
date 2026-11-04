"""
QuadFlow Retopology - Professional Blender 4.2+ Extension Entry Point
A topology-optimized quad remesher using curvature cross-field algorithms,
adaptive quad density, and native in-viewport GPU visualization.
"""

bl_info = {
    "name": "QuadFlow Retopology",
    "author": "QuadFlow Core Team",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > QuadFlow",
    "description": "Curvature cross-field and topology-optimized quad remesher",
    "category": "Mesh",
    "doc_url": "https://quadflow3d.org",
}

import bpy
from .properties import QuadFlowSettings
from .ui import VIEW3D_PT_quadflow_main, unregister_draw_handlers
from .operators import (
    VIEW3D_OT_quadflow_modal,
    VIEW3D_OT_quadflow_remesh,
)

classes = (
    QuadFlowSettings,
    VIEW3D_PT_quadflow_main,
    VIEW3D_OT_quadflow_modal,
    VIEW3D_OT_quadflow_remesh,
)

def register():
    """Register all extension classes and scene properties."""
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.quadflow_settings = bpy.props.PointerProperty(type=QuadFlowSettings)

def unregister():
    """Cleanly unregister all extension classes, properties, and handlers."""
    # Safety cleanup for any active in-viewport draw callbacks
    unregister_draw_handlers()
    
    if hasattr(bpy.types.Scene, "quadflow_settings"):
        del bpy.types.Scene.quadflow_settings
        
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
