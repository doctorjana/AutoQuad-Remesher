# GitHub Publishing & Release Instructions

Instructions for publishing **AutoQuad Remesher** to GitHub under user account `doctorjana`.

---

## 1. Local Git Commit

```bash
cd d:\Retopo\quadflow_retopology

git add .
git commit -m "feat(release): AutoQuad Remesher v1.1.0 by Doctor Jana"
```

---

## 2. Linking to Remote GitHub Repository

1. Create a repository on GitHub under: `https://github.com/doctorjana/autoquad_remesher`
2. Link and push your local branch:

```bash
git remote add origin https://github.com/doctorjana/autoquad_remesher.git
git branch -M main
git push -u origin main
```

---

## 3. GitHub Pages Setup

To enable the default GitHub Pages site:
1. On GitHub, navigate to **Settings > Pages**.
2. Under **Build and deployment > Source**, select **Deploy from a branch**.
3. Choose branch: `main` and folder: `/ (root)` or `/docs`.
4. Click **Save**.
5. Your GitHub Pages site will be live at:
   **https://doctorjana.github.io/autoquad_remesher/**

---

## 4. GitHub Release

1. Go to **Releases > Create a new release**.
2. Tag: `v1.1.0`.
3. Title: `AutoQuad Remesher v1.1.0`.
4. Attach `release/autoquad_remesher-1.1.0.zip`.
5. Click **Publish release**.
