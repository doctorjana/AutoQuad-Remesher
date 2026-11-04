"""
QuadFlow - Blender Version Compatibility Utilities
Provides transparent API compatibility across Blender 4.2+, 5.0+, and 5.2+.
"""

import bpy
import gpu

def get_line_smooth_shader():
    """
    Returns the appropriate built-in shader for anti-aliased 3D line drawing.
    """
    try:
        if bpy.app.version >= (4, 0, 0):
            return gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')
        return gpu.shader.from_builtin('UNIFORM_COLOR')
    except Exception:
        return gpu.shader.from_builtin('UNIFORM_COLOR')
