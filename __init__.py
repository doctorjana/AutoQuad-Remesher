"""
QuadFlow Retopology - Blender 4.2+ Extension Entry Point
A topology-optimized quad remesher using curvature cross-field algorithms,
adaptive quad density, and native in-viewport GPU visualization.
"""

bl_info = {
    "name": "QuadFlow Retopology",
    "author": "QuadFlow Core Team",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > QuadFlow",
    "description": "Curvature cross-field and topology-optimized quad remesher with in-viewport GPU visualization",
    "category": "Mesh",
    "doc_url": "https://quadflow3d.org",
}

import sys
# Defensive cleanup: remove contaminated third-party addon paths from sys.path
bad_paths = [p for p in sys.path if "kodama" in p.lower() or "kodama-requirements" in p.lower()]
if bad_paths:
    sys.path = [p for p in sys.path if p not in bad_paths]
    for k in list(sys.modules.keys()):
        if k.startswith("numpy"):
            del sys.modules[k]

import bpy
from .ui_panel import QuadFlowSettings, VIEW3D_PT_quadflow_main
from .operators import VIEW3D_OT_quadflow_modal, VIEW3D_OT_quadflow_remesh

classes = (
    QuadFlowSettings,
    VIEW3D_PT_quadflow_main,
    VIEW3D_OT_quadflow_modal,
    VIEW3D_OT_quadflow_remesh,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.quadflow_settings = bpy.props.PointerProperty(type=QuadFlowSettings)

def unregister():
    if hasattr(bpy.types.Scene, "quadflow_settings"):
        del bpy.types.Scene.quadflow_settings
        
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
