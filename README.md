# BK Stays digital guidebooks

Replacement for TouchStay. Live: https://bkstays.github.io/bkstays-guides/cherry-log-summit/ (GitHub Pages, serves `docs/` on main)

- Old Netlify site `bkstays-guides` is retired. Do not deploy there.
- Guest sign-ins: Google Apps Script web app (tools/google-sheet-signin.gs, URL in content/settings.json) writes straight to the Sheet below.
- Google Sheet for sign-ins: 1EBcElK82dHYkjC6uNNm_1siark4zUhy7EjJZ-rW9Hps (one tab per property)

## Layout
- `content/guides/<slug>.json` — one per property: name, cover, contact, `layout` (Info grid order), house sections. `oldLinks` = old TouchStay paths that redirect here.
- `content/library/north-georgia.json` — shared recommendations; a guide pulls a section with `"lib:<id>"` in its layout.
- `app/` — shared app (app.js, app.css). `site/img/` — photos (downloaded from TouchStay).
- `tools/build.py` — builds `site/` and applies the A-Z rules. **Read STANDARDS.md before building a new guide.**

## Edit + publish
1. Edit the JSON (or app), run `python3 tools/build.py`.
2. Copy `site/` into `docs/`, then commit and push to main. Live in about a minute.

## Switch-over (later)
Point `guide.bkstays.com` (Squarespace DNS, CNAME `guide`) to `bkstays.github.io`, add `docs/CNAME` containing `guide.bkstays.com`, set the custom domain in GitHub Pages settings and turn on HTTPS. Old TouchStay links (/guest/bZBh4TDr7xUIu/...) already redirect.

## Restoring in a new session
1. Get the latest "BK Stays Guidebooks - project backup" zip from the chat and unzip into `/home/claude/guide`.
2. `cd tools && npm install leaflet@1.9.4 lucide-static`.
3. Photos are not in the zip. Pull them from the live site with
   `python3 tools/restore_photos.py` (photos hidden with photoHidden are only kept if they were deployed).
