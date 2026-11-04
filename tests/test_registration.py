"""
QuadFlow - Registration and Lifecycle Unit Tests
Validates add-on/extension registration, property lifecycle, and unregistration cleanliness.

Usage:
    blender --background --python quadflow_retopology/tests/test_registration.py
"""

import sys
import os
import bpy

# Ensure workspace root is in sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
pkg_dir = os.path.dirname(script_dir)
root_dir = os.path.dirname(pkg_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import quadflow_retopology as qf

print("=" * 60)
print("TEST: Extension Registration Lifecycle")
print(f"Blender Version: {bpy.app.version_string}")
print("=" * 60)

# Step 1: Initial Register
print("[STEP 1] Registering extension...")
qf.register()
assert hasattr(bpy.types.Scene, "quadflow_settings"), "Scene.quadflow_settings not found after register"
settings = bpy.context.scene.quadflow_settings
assert settings.target_quad_count == 2500, f"Unexpected default target_quad_count: {settings.target_quad_count}"
assert settings.use_symmetry is True, f"Unexpected default use_symmetry: {settings.use_symmetry}"
print("  ✓ Extension successfully registered, default properties verified.")

# Step 2: Unregister
print("[STEP 2] Unregistering extension...")
qf.unregister()
assert not hasattr(bpy.types.Scene, "quadflow_settings"), "Scene.quadflow_settings still exists after unregister"
print("  ✓ Extension successfully unregistered, properties cleaned.")

# Step 3: Re-register (idempotency & re-activation test)
print("[STEP 3] Re-registering extension...")
qf.register()
assert hasattr(bpy.types.Scene, "quadflow_settings"), "Scene.quadflow_settings missing after re-register"
print("  ✓ Extension successfully re-registered.")

print("=" * 60)
print("REGISTRATION TESTS COMPLETED SUCCESSFULLY!")
print("=" * 60)
