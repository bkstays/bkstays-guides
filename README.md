# BK Stays digital guidebooks

Replacement for TouchStay. Live preview: https://bkstays-guides.netlify.app/cherry-log-summit/

- Netlify site: `bkstays-guides` (siteId b12d9bec-9d43-4cc5-85a7-ed9198edf960), team BK Stays
- Guest sign-in form: Netlify form `guest-signin` (formId 6ae12a71cb6d7ffdfcfd0dd0)
- Google Sheet for sign-ins: 1EBcElK82dHYkjC6uNNm_1siark4zUhy7EjJZ-rW9Hps (one tab per property)

## Layout
- `content/guides/<slug>.json` — one per property: name, cover, contact, `layout` (Info grid order), house sections. `oldLinks` = old TouchStay paths that redirect here.
- `content/library/north-georgia.json` — shared recommendations; a guide pulls a section with `"lib:<id>"` in its layout.
- `app/` — shared app (app.js, app.css). `site/img/` — photos (downloaded from TouchStay).
- `tools/build.py` — builds `site/` and applies the A-Z rules. **Read STANDARDS.md before building a new guide.**

## Edit + publish (GitHub Pages: free, no publish limits)
1. Edit the JSON (or app), run `python3 tools/build.py`.
2. Copy `site/` to `docs/` (drop `_redirects` and `_headers`, which are Netlify-only), commit and push to `main`. GitHub Pages serves `docs/`.
3. The old Netlify copy (bkstays-guides.netlify.app) is retired. Do not deploy there any more.

## Switch-over (later)
Point `guide.bkstays.com` (Squarespace DNS, CNAME `guide`) to `bkstays-guides.netlify.app` and add the domain in Netlify. Old TouchStay links (/guest/bZBh4TDr7xUIu/...) already redirect.

## Restoring in a new session
1. This GitHub repo (Bkstays/bkstays-guides) is the source of truth. Clone it and copy `docs/img/` to `site/img/`.
2. `cd tools && npm install leaflet@1.9.4 lucide-static`.
3. Photos are not in the zip. Pull them from the live site with
   `python3 tools/restore_photos.py` (photos hidden with photoHidden are only kept if they were deployed).
