"""
QuadFlow - Viewport GPU Overlays and 2D HUD Drawing
Provides in-viewport visual feedback during interactive retopology:
1. 3D line drawing for 4-RoSy vector cross needles.
2. 2D HUD status overlay showing retopology phase, quad budget, and keyboard shortcuts.
"""

import bpy
import gpu
import blf
from gpu_extras.batch import batch_for_shader
from ..utils.compatibility import get_line_smooth_shader

_draw_handler_3d = None
_draw_handler_2d = None

def draw_callback_3d(operator, context):
    """Draws 3D GPU lines for 4-RoSy cross needles in the 3D Viewport."""
    if not operator.is_running or not hasattr(operator, 'draw_lines_coords') or not operator.draw_lines_coords:
        return
        
    shader = get_line_smooth_shader()
    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(2.0)
    
    try:
        batch = batch_for_shader(shader, 'LINES', {
            "pos": operator.draw_lines_coords,
            "color": operator.draw_lines_colors
        })
        shader.bind()
        batch.draw(shader)
    except Exception:
        pass
    finally:
        gpu.state.blend_set('NONE')


def draw_callback_2d(operator, context):
    """Renders 2D viewport HUD status text in the top-left corner of the 3D Viewport."""
    if not operator.is_running:
        return
        
    font_id = 0
    blf.size(font_id, 16)
    blf.color(font_id, 0.96, 0.62, 0.04, 1.0)
    
    x_pos = 30
    y_pos = context.region.height - 40
    
    blf.position(font_id, x_pos, y_pos, 0)
    blf.draw(font_id, "QUADFLOW: IN-VIEWPORT RETOPOLOGY (ACTIVE)")
    
    blf.size(font_id, 13)
    blf.color(font_id, 0.85, 0.88, 0.92, 1.0)
    y_pos -= 24
    blf.position(font_id, x_pos, y_pos, 0)
    blf.draw(
        font_id,
        f"Phase: {operator.phase_name}  |  Quads: ~{operator.target_quad_count:,}  |  Step: {operator.current_step}"
    )
    
    y_pos -= 20
    blf.color(font_id, 0.55, 0.62, 0.72, 1.0)
    blf.position(font_id, x_pos, y_pos, 0)
    blf.draw(font_id, "[Space] Auto-Relax Quads  |  [Enter] Commit Mesh  |  [Esc] Cancel  |  [Wheel] Density")


def register_draw_handlers(operator, context):
    """Registers the 3D and 2D viewport draw callbacks."""
    global _draw_handler_3d, _draw_handler_2d
    unregister_draw_handlers()
    _draw_handler_3d = bpy.types.SpaceView3D.draw_handler_add(
        draw_callback_3d, (operator, context), 'WINDOW', 'POST_VIEW'
    )
    _draw_handler_2d = bpy.types.SpaceView3D.draw_handler_add(
        draw_callback_2d, (operator, context), 'WINDOW', 'POST_PIXEL'
    )


def unregister_draw_handlers():
    """Safely removes active viewport draw callbacks."""
    global _draw_handler_3d, _draw_handler_2d
    if _draw_handler_3d is not None:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(_draw_handler_3d, 'WINDOW')
        except Exception:
            pass
        _draw_handler_3d = None
        
    if _draw_handler_2d is not None:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(_draw_handler_2d, 'WINDOW')
        except Exception:
            pass
        _draw_handler_2d = None
