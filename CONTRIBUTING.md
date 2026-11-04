# Contributing to QuadFlow Retopology

Thank you for your interest in contributing to QuadFlow Retopology!

QuadFlow is a free and open-source Blender Extension dedicated to providing high-quality, topology-optimized quad remeshing directly within Blender.

---

## Code of Conduct

Please read and adhere to our [Code of Conduct](CODE_OF_CONDUCT.md) in all project interactions.

---

## Development Setup

### 1. Prerequisites
- Blender 4.2 LTS or newer (tested through Blender 5.2+).
- Git.
- Python 3.10+ (bundled with Blender).

### 2. Clone the Repository
```bash
git clone https://github.com/quadflow/quadflow_retopology.git
cd quadflow_retopology
```

### 3. Local Installation for Development
You can test the extension in Blender without rebuilding a ZIP file:
1. Open Blender.
2. Go to **Edit > Preferences > File Paths**.
3. Under **Development**, enable **Developer Extras**.
4. In **Edit > Preferences > Extensions**, click the dropdown menu and add the repository directory as an Extension Repository.

Alternatively, link the directory into your Blender user extensions directory:
- Windows: `%APPDATA%\Blender Foundation\Blender\<version>\extensions\user_default\quadflow_retopology`
- Linux: `~/.config/blender/<version>/extensions/user_default/quadflow_retopology`
- macOS: `~/Library/Application Support/Blender/<version>/extensions/user_default/quadflow_retopology`

---

## Running the Automated Test Suite

All tests can be executed headlessly without opening the Blender GUI:

### Registration Lifecycle Tests
```bash
blender --background --python tests/test_registration.py
```

### Regression & Topology Validation Tests
```bash
blender --background --python tests/test_regression.py
```

### Official Extension Manifest Validation
```bash
blender --command extension validate .
```

---

## Code Organization & Guidelines

- **`core/`**: Mathematical algorithms, geometry processing, curvature calculations, and remeshing engines. Must remain strictly independent of Blender UI panels or layout widgets.
- **`properties/`**: Centralized property group definitions (`QuadFlowSettings`).
- **`operators/`**: Blender operators (`VIEW3D_OT_quadflow_remesh`, `VIEW3D_OT_quadflow_modal`).
- **`ui/`**: User interface panels and GPU drawing callbacks.
- **`utils/`**: Reusable validation and compatibility layers.
- **`tests/`**: Automated verification test cases.

### Rules for Contributions
1. **Preserve Algorithmic Determinism**: Any changes to `core/` geometry calculations must pass the regression benchmarks.
2. **Relative Imports**: All modules within the extension must use relative imports (e.g., `from ..core import run_retopology`).
3. **No External Python Dependencies**: The extension must remain 100% self-contained using Blender's standard API and Python standard library.
4. **Clean Resource Cleanup**: Always free temporary `bmesh` objects, remove draw handlers, and clean event timers inside `try...finally` blocks.

---

## Submitting Pull Requests

1. Fork the repository and create your feature branch: `git checkout -b feature/my-new-feature`.
2. Commit your changes: `git commit -am 'Add new feature'`.
3. Ensure all automated tests pass.
4. Push to the branch: `git push origin feature/my-new-feature`.
5. Open a Pull Request on GitHub with a description of the changes and test results.
