"""
QuadFlow - Input Validation Utilities
Validates Blender objects, mesh geometry, and operational settings.
"""

def validate_mesh_object(obj):
    """
    Validates whether an object is a valid mesh suitable for retopology.
    
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    if obj is None:
        return False, "No active object selected. Please select a mesh object."
        
    if obj.type != 'MESH':
        return False, f"Selected object '{obj.name}' is of type '{obj.type}'. Only MESH objects are supported."
        
    if not obj.data:
        return False, f"Object '{obj.name}' has no mesh data."
        
    if len(obj.data.vertices) == 0:
        return False, f"Mesh '{obj.data.name}' has 0 vertices. Cannot retopologize an empty mesh."
        
    if len(obj.data.polygons) == 0:
        return False, f"Mesh '{obj.data.name}' has 0 faces. Cannot retopologize a mesh without faces."
        
    return True, ""
