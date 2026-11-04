# GitHub Publishing & Release Instructions

This guide provides step-by-step instructions for publishing **QuadFlow Retopology** as a public open-source repository on GitHub.

---

## 1. Initial Git Repository Setup

If publishing from the local repository directory:

```bash
cd d:\Retopo\quadflow_retopology

# Verify git status
git status

# Add all files to staging
git add .

# Create initial commit
git commit -m "feat: initial release of QuadFlow Retopology as Blender 4.2+ Extension (v1.0.0)"
```

---

## 2. Linking to Remote GitHub Repository

1. Create a new public repository on GitHub (e.g. `quadflow-retopology` or `quadflow`).
   - Do **not** initialize with README, License, or .gitignore (these are already configured locally).
2. Link your local repository to the remote origin:

```bash
git remote add origin https://github.com/<your-username-or-org>/quadflow-retopology.git
git branch -M main
git push -u origin main
```

---

## 3. Creating a GitHub Release

1. On GitHub, navigate to **Releases > Create a new release**.
2. Set the release tag: `v1.0.0`.
3. Set the release title: `QuadFlow Retopology v1.0.0 - Production Release`.
4. Copy the release notes from [CHANGELOG.md](../CHANGELOG.md).
5. Attach the distribution binary:
   - File: `release/quadflow_retopology-1.0.0.zip`
6. Click **Publish release**.

---

## 4. Recommended Repository Topics & Settings

Under repository **About** on GitHub:
- **Description:** Curvature cross-field and topology-optimized quad remesher for Blender 4.2+
- **Website:** https://quadflow3d.org
- **Topics:** `blender`, `blender-addon`, `blender-extension`, `retopology`, `remesh`, `quad-mesh`, `computational-geometry`, `bmesh`, `python`
