# BK Stays Guidebook Standards

These rules apply to every BK Stays guidebook. Brandon approved them on Cherry Log Summit (Oct 28, 2026).
Each property keeps its own photos, house tiles and wording. The layout, style and ordering rules below stay the same everywhere.

## Look and style (shared app, automatic for every guide)
- Black header and bottom bars. White tiles and cards. Figtree font.
- Pink (#FF66C4) only for small accents: active tab bar, item-title underline, dot on the contact button, selected-tile outline on desktop, section-heading dots. No pink buttons.
- BK Stays logo: light version in the header, cream logo card on the Home and sign-in screens.
- One photo with a view per property is the cover on Home (phone and desktop), the sign-in screen, and the darkened background behind the tiles and section pages. Set it with `cover`, `coverDesktop` and `background` in the guide file.
- Phone: 2-column tile grid.
- Desktop (960px and wider): TouchStay-style two panels over the background photo. Tiles on the left (2 columns), the selected section large on the right. Opening the Info tab starts on the first Your Stay tile.
- Item photos are capped in height on desktop. A collage can use `"photoFit": "full"` so it isn't cropped.
- Videos (Loom, etc.) show below the item text.
- Contact button (bottom right) opens Text us / Call us. Number comes from `contact` in the guide file. It will change to the new Quo number when Brandon has it.
- Name and email sign-in gate, asked once per device (`"gate": true`). Sign-ins go to the Netlify form `guest-signin`, then to the Google Sheet with a tab per property.

## Info grid order
**Your Stay**: this exact order (rows of two, left then right):
1. Add This Guide To Your Phone | Welcome
2. Check In + Arrival | Check Out + Departure
3. Rules and Regulations | Cancellation Policy
4. About Us | Contact Us / Book Again

**The Home**: tiles A–Z (`"sort": "az"`). Items inside each Home tile keep the order we chose.
**Explore the Area**: tiles A–Z, and inside every tile the sub-categories and places are A–Z too (`"sort": "az", "sortInside": true`). The build applies this automatically. A leading "The" is ignored when sorting, so The Pullman sorts under P.

## Section and content conventions
- **Welcome**: welcome message, then the host video titled **"Thank You"**.
- **About Us**: shared for all guides (`bk:about-us` in content/shared/bkstays.json). Family 2x2 collage and Brandon's approved copy (kids 6 and 3). Update it once and every guide changes.
- **Contact Us / Book Again**: no photos.
- **Add This Guide To Your Phone**: no photo.
- **Check Out + Departure**: no photos.
- **Rules > Jacuzzi**: no photo (the Hot Tub tile keeps its photo).
- **Trash**: collected after each guest checks out. Never say "every Monday".
- **Outdoor games tile**: named after the actual game (Cherry Log: "Cornhole / Bags"). Friendly-competition blurb plus the bring-inside and storage note.
- **Indoor Games**: list the arcade games or other specifics if the property has them. Generic stock photos are fine for Cards/Games (Unsplash free license only, never Unsplash+).
- **"Random Recommendations"** is called **"Things To Do"**.
- Hidden photos are kept as `photoHidden` so they can be restored.

## Content cleanup checklist (when importing each TouchStay guide)
- Merge duplicates (e.g. two "About Your Hosts", Trash listed twice, the same tour in two subgroups).
- Strip pasted ChatGPT and citation junk ("Explore Georgia" chips, "tripadvisor.com+10", utm_source=chatgpt.com).
- Fix typos. Fix internal links between sections.
- **Check every outside link.** Cucina Rustica's old domain had been taken over by a spam site.
- Confirm a restaurant is still open before keeping it. Brandon removed Blue Ridge Mountain BBQ from North Georgia.
- Copy every photo off TouchStay before the subscription ends.

## Where things live
- One file per property: `content/guides/<slug>.json`. Start new ones from `content/templates/guide-template.json`.
- Shared area recommendations: `content/library/<area>.json` (north-georgia so far; ski areas will get their own).
- Shared BK Stays sections: `content/shared/bkstays.json`.
- App: `app/app.js`, `app/app.css`. Build: `python3 tools/build.py`. Deploy `site/` to the Netlify site `bkstays-guides`.
- Live: https://bkstays-guides.netlify.app/<slug>/ (later guide.bkstays.com/<slug>/; old TouchStay links redirect via `oldLinks`).

## Importing more TouchStay guides
Pull each guide's house content in the browser (fetch `/v2api/wb/guide/<id>/` on guide.bkstays.com), save it to `src/ts/<id>.txt`, add the id and slug to `SLUGS` in `tools/import_touchstay.py`, then run it. It applies every rule above and writes `src/import_report.md` with what needs proofreading. Recommendations come from the shared library. A place that belongs to one home only goes in that guide's `libExtra`.
