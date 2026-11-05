"""
AutoQuad Remesher - Professional Blender 4.2+ Extension Entry Point
An automatic curvature-guided quad remesher engineered for clean, regularized quad topology.
Author: Doctor Jana
"""

bl_info = {
    "name": "AutoQuad Remesher",
    "author": "Doctor Jana",
    "version": (1, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > AutoQuad",
    "description": "Automatic curvature-guided quad remesher",
    "category": "Mesh",
    "doc_url": "https://doctorjana.github.io/autoquad_remesher/",
}

import bpy
from .properties import AutoQuadSettings
from .ui import VIEW3D_PT_autoquad_main, unregister_draw_handlers
from .operators import (
    VIEW3D_OT_autoquad_remesh,
    VIEW3D_OT_quadflow_remesh,
    VIEW3D_OT_autoquad_make_manifold,
)

classes = (
    AutoQuadSettings,
    VIEW3D_PT_autoquad_main,
    VIEW3D_OT_autoquad_remesh,
    VIEW3D_OT_quadflow_remesh,
    VIEW3D_OT_autoquad_make_manifold,
)

def register():
    """Register all extension classes and scene properties."""
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.autoquad_settings = bpy.props.PointerProperty(type=AutoQuadSettings)
    # Compatibility alias for legacy scripts
    bpy.types.Scene.quadflow_settings = bpy.types.Scene.autoquad_settings

def unregister():
    """Cleanly unregister all extension classes, properties, and handlers."""
    unregister_draw_handlers()
    
    if hasattr(bpy.types.Scene, "autoquad_settings"):
        del bpy.types.Scene.autoquad_settings
    if hasattr(bpy.types.Scene, "quadflow_settings"):
        del bpy.types.Scene.quadflow_settings
        
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
