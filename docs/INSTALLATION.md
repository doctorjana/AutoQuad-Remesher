# Installation Guide

QuadFlow Retopology is engineered as an official Blender Extension for **Blender 4.2 LTS and newer** (including Blender 5.0, 5.2+).

---

## Method 1: Installing via Blender Extensions Interface (Recommended)

1. Download the release package: `quadflow_retopology-1.0.0.zip`.
2. Launch Blender 4.2 or newer.
3. Open **Edit > Preferences**.
4. Select the **Get Extensions** or **Add-ons** tab on the left.
5. In the top-right corner of the window:
   - Click the **down-arrow icon (∨)** next to the search bar.
   - Select **Install from Disk...**
6. Browse to the downloaded `quadflow_retopology-1.0.0.zip` file and select **Install from Disk**.
7. Ensure the checkmark next to **QuadFlow Retopology** is enabled.
8. In the 3D Viewport, press **N** to open the sidebar and click the **QuadFlow** tab.

---

## Method 2: Manual Directory Installation (For Developers)

1. Extract or clone the repository to your local drive.
2. Place the `quadflow_retopology` directory into your Blender user extensions folder:
   - **Windows:** `%APPDATA%\Blender Foundation\Blender\<version>\extensions\user_default\quadflow_retopology`
   - **Linux:** `~/.config/blender/<version>/extensions/user_default/quadflow_retopology`
   - **macOS:** `~/Library/Application Support/Blender/<version>/extensions/user_default/quadflow_retopology`
3. Restart Blender or reload scripts (**F3 > Reload Scripts**).
4. The extension will automatically be detected and active.

---

## Verifying the Installation

1. Select any mesh in the 3D Viewport (e.g. default Cube or Suzanne Monkey).
2. Press **N** to show the 3D Viewport sidebar and open the **QuadFlow** panel.
3. If the panel displays mesh polygon counts and action buttons (**Interactive Viewport Retopology** and **One-Click Quad Remesh**), installation is complete and ready.

---

## Uninstalling

1. Open **Edit > Preferences > Add-ons / Extensions**.
2. Search for `QuadFlow Retopology`.
3. Click the dropdown arrow next to the extension.
4. Click **Uninstall** or disable the checkbox.
