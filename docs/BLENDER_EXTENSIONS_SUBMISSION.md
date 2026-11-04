# Blender Extensions Platform Submission Checklist

This document details the checklist and verification steps required to submit **QuadFlow Retopology** to the official Blender Extensions platform ([extensions.blender.org](https://extensions.blender.org/)).

---

## 1. Compliance Checklist

| Category | Requirement | Status | Notes |
| :--- | :--- | :--- | :--- |
| **Manifest Format** | `blender_manifest.toml` present at root | **PASSED** | Follows schema version 1.0.0 |
| **Manifest Validation** | `blender --command extension validate` | **PASSED** | Validated with 0 errors |
| **Tagline Limit** | Tagline $\le 64$ characters | **PASSED** | Exactly 57 characters |
| **Allowed Tags** | Uses official taxonomy tags | **PASSED** | `Mesh`, `Modeling`, `Sculpt`, `UV` |
| **Blender Version** | `blender_version_min` $\ge$ 4.2.0 | **PASSED** | Set to `4.2.0` |
| **License** | Open source (GPL-3.0-or-later) | **PASSED** | SPDX: `GPL-3.0-or-later`, complete text included |
| **Network Access** | Offline by default | **PASSED** | No permissions requested; 100% local operation |
| **Self-Contained** | No external binary/pip downloads | **PASSED** | Zero external dependencies; standard Blender API only |
| **Packaging** | Built via official CLI tool | **PASSED** | Built with `blender --command extension build` |
| **Clean Lifecycle** | Complete register/unregister idempotency | **PASSED** | All properties, handlers, and classes cleaned |
| **Security** | No system tampering / unapproved subprocesses | **PASSED** | Pure memory geometry transformations |

---

## 2. Submission Procedure

1. **Create an Account:**
   - Log into [extensions.blender.org](https://extensions.blender.org/) using your Blender ID.
2. **Review Developer Guidelines:**
   - Review Blender's [Extension Approval Guidelines](https://docs.blender.org/manual/en/latest/advanced/extensions/index.html).
3. **Submit Package:**
   - Click **Submit Extension**.
   - Upload the distribution file: `release/quadflow_retopology-1.0.0.zip`.
   - The platform will validate `blender_manifest.toml` automatically.
4. **Provide Media & Assets:**
   - Upload promotional screenshots (16:9 ratio recommended).
   - Link the source repository: `https://github.com/quadflow/quadflow_retopology`.
   - Link the issue tracker: `https://github.com/quadflow/quadflow_retopology/issues`.
5. **Review Period:**
   - The Blender Extensions review team will inspect the source code, verify that no network requests are made, test installation/uninstallation, and approve the extension for the public catalog.
