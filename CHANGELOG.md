# Changelog

All notable changes to the QuadFlow Retopology extension are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-04

### Added
- Official Blender 4.2+ Extension format compliant with `blender_manifest.toml`.
- Clean modular package architecture separating `core`, `properties`, `operators`, `ui`, and `utils`.
- Independent `core/retopology_engine.py` coordinating both native C++ QuadriFlow acceleration and pure-Python discrete differential geometry fallback.
- In-viewport interactive modal operator (`VIEW3D_OT_quadflow_modal`) featuring:
  - GPU-accelerated 3D vector cross-needle visualization (`batch_for_shader`).
  - 2D status HUD displaying phase information, target quad budget, and keyboard commands (`blf`).
  - Interactive relaxation hotkey (`[Space]`) and polygon budget adjustments (`[Mouse Wheel]`).
- Robust input validation in `utils/validation.py` with descriptive error messaging for empty or non-mesh objects.
- Blender cross-version compatibility utilities in `utils/compatibility.py`.
- Comprehensive automated regression and lifecycle test suite in `tests/test_registration.py` and `tests/test_regression.py`.
- Comprehensive technical documentation (`INSTALLATION.md`, `USAGE.md`, `DEVELOPMENT.md`).

### Changed
- Refactored monolithic flat layout into cleanly bounded architectural packages.
- Validated extension manifest with official Blender CLI (`blender --command extension validate`).
- Preserved 100% mathematical and topological parity with baseline algorithms.

### Fixed
- Fixed manifest tagline exceeding the 64-character limit mandated by the Blender Extensions platform.
- Fixed manifest tags to strictly match official allowed taxonomy (`Mesh`, `Modeling`, `Sculpt`, `UV`).
- Eliminated destructive `sys.modules['numpy']` purging from extension initialization.
- Added strict `try...finally` resource cleanup for temporary bmeshes and draw handlers to eliminate memory leaks.
