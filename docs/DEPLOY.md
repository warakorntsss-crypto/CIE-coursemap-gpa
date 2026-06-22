# Deploy — CIE Course Map

Static frontend. Backend is a Google Apps Script Web App (already live); its `/exec` URL is set in
`data.js` (`GSHEET_API`). This whole folder is upload-ready — every file here is meant to be public.

Backend reminder: confirm `GSHEET_API` in `data.js` is the live `/exec` URL, and the Apps Script is
deployed with **Who has access: Anyone**. Run `setup()` once in the Sheet's Apps Script editor so the
`students` + `progress` tabs exist and have logins.

---

## Option A — GitHub Pages (this is the chosen host)
Repo: **CIE-coursemap-gpa**

1. Push this folder to the repo (already done by the build, root = these files).
2. GitHub → repo → **Settings → Pages** → Source: **Deploy from a branch** → Branch: `main` / `/ (root)` → Save.
3. Wait ~1 min → site at `https://<your-user>.github.io/CIE-coursemap-gpa/`.

Served over HTTPS, so PWA install ("Add to Home Screen") works.

## Option B — Netlify (drag & drop)
1. app.netlify.com → **Add new site → Deploy manually**.
2. Drag this whole `coursemaps-cie\` folder onto the page. Done — instant HTTPS URL.
3. Rename the site in **Site settings** if you want a nicer URL.

## Option C — Netlify CLI
```
npm i -g netlify-cli
netlify deploy --prod      # run from this folder; publish dir = .
```

---

## Files
`index.html` · `data.js` · `manifest.json` · `service-worker.js` · `icon-192.png` · `icon-512.png`
(Dev-only files — `serve.py`, `make_icons.py`, `APPS_SCRIPT.md`, `README.txt` — are intentionally NOT here.)

## After deploy
- First load caches the shell via the service worker. If you push an update and the old shell
  lingers, bump `CACHE` in `service-worker.js` (e.g. `-shell-v2`) or hard-reload once.
- The login is a plaintext-password column in the Sheet — fine for a class roster, **not** real
  security. Don't store anything sensitive.
