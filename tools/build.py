"""Build the static guidebook site.

content/guides/*.json      one file per property (house sections + layout)
content/library/*.json     shared area recommendations, pulled in with "lib:<id>"
app/                       the shared app (css/js)
site/                      output that gets deployed (photos live in site/img)
"""
import json, os, re, shutil, time, html, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'site')
LUCIDE = os.path.join(ROOT, 'tools/node_modules/lucide-static/icons')
LEAFLET = os.path.join(ROOT, 'tools/node_modules/leaflet/dist')
VERSION = time.strftime('%Y%m%d%H%M%S')

UI_ICONS = ['arrow-left', 'share-2', 'printer', 'chevron-down', 'phone', 'message-square', 'mail', 'navigation',
            'map-pin', 'search', 'x', 'smartphone', 'house', 'info', 'map', 'utensils', 'wine', 'mountain',
            'sailboat', 'ticket', 'shopping-bag', 'sparkles', 'siren', 'circle']


def slug(s):
    s = s.lower().replace('&', ' ').replace('+', ' ').replace("'", '').replace('’', '')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def az(t):
    """Sort key for A-Z: case-insensitive, ignores punctuation and a leading 'The'/'A'."""
    t = re.sub(r"[^a-z0-9 ]", "", (t or '').lower()).strip()
    return re.sub(r'^(the|a)\s+', '', t)


def load(p):
    return json.load(open(p, encoding='utf-8'))


def resolve(guide):
    libs = {}
    if guide.get('library'):
        libs = load(os.path.join(ROOT, 'content/library', guide['library'] + '.json'))['sections']
    sections, layout, missing = {}, [], []
    for grp in guide['layout']:
        ids = []
        for ref in grp['sections']:
            if ref.startswith('bk:'):
                sid = ref[3:]
                s = load(os.path.join(ROOT, 'content/shared/bkstays.json'))['sections'].get(sid)
            elif ref.startswith('lib:'):
                sid = ref[4:]
                s = libs.get(sid)
            else:
                sid = ref
                s = guide['sections'].get(sid)
            if not s:
                missing.append(ref)
                continue
            s = json.loads(json.dumps(s))
            s['id'] = sid
            extra = (guide.get('libExtra') or {}).get(sid) if ref.startswith('lib:') else None
            if extra:
                # places that belong to this one home only (e.g. a store just down the street)
                s['groups'][0]['items'] += json.loads(json.dumps(extra))
            if grp.get('sortInside'):
                # STANDARD: in A-Z tile groups, places/topics inside each tile are A-Z,
                # and so are the sub-categories (untitled group stays first).
                for g in s['groups']:
                    g['items'].sort(key=lambda it: az(it['title']))
                s['groups'].sort(key=lambda g: (g['title'] != '', az(g['title'])))
            used = set()
            for g in s['groups']:
                for it in g['items']:
                    base = slug(it['title']) or 'item'
                    iid, n = base, 2
                    while iid in used:
                        iid, n = f'{base}-{n}', n + 1
                    used.add(iid)
                    it['id'] = iid
            sections[sid] = s
            ids.append(sid)
        if grp.get('sort') == 'az':
            ids.sort(key=lambda i: az(sections[i]['title']))
        layout.append({'heading': grp.get('heading', ''), 'sections': ids})
    if missing:
        raise SystemExit(f"{guide['slug']}: unknown sections {missing}")
    out = {k: v for k, v in guide.items() if k not in ('sections', 'layout', 'library', 'libExtra')}
    out['layout'] = layout
    out['sections'] = sections
    return out


def icons_js(names):
    d = {}
    for n in sorted(names):
        p = os.path.join(LUCIDE, n + '.svg')
        if not os.path.exists(p):
            raise SystemExit('missing icon ' + n)
        svg = open(p).read()
        inner = re.search(r'<svg[^>]*>(.*)</svg>', svg, re.S).group(1)
        d[n] = re.sub(r'\s+', ' ', inner).strip()
    return 'window.BK_ICONS=' + json.dumps(d) + ';'


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{name} Guidebook</title>
<meta name="description" content="Your digital guidebook for {name} — check-in, Wi-Fi, house info and local recommendations.">
<meta name="robots" content="noindex">
<meta name="theme-color" content="#0d0d0d">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="apple-mobile-web-app-title" content="{short}">
<meta property="og:title" content="{name} Guidebook">
<meta property="og:image" content="../img/{cover}">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" href="../assets/favicon.png">
<link rel="apple-touch-icon" href="../assets/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/vendor/leaflet.css?v={v}">
<link rel="stylesheet" href="../assets/app.css?v={v}">
</head>
<body>
<div id="app">
  <section class="view" id="v-home"></section>
  <section class="view" id="v-info"></section>
  <section class="view" id="v-section"></section>
  <section class="view" id="v-map"></section>
  <section class="view" id="v-search"></section>
</div>
<button class="fab" id="fab" aria-label="Contact your hosts"><svg class="i" viewBox="0 0 24 24" aria-hidden="true">{fab_icon}</svg></button>
<nav class="nav" aria-label="Guide">
  <a href="#/" data-nav="home"><svg class="i" viewBox="0 0 24 24" aria-hidden="true">{i_home}</svg>Home</a>
  <a href="#/info" data-nav="info"><svg class="i" viewBox="0 0 24 24" aria-hidden="true">{i_info}</svg>Info</a>
  <a href="#/map" data-nav="map"><svg class="i" viewBox="0 0 24 24" aria-hidden="true">{i_map}</svg>Map</a>
  <a href="#/search" data-nav="search"><svg class="i" viewBox="0 0 24 24" aria-hidden="true">{i_search}</svg>Search</a>
</nav>
<script type="application/json" id="guide-data">{data}</script>
<script src="../assets/icons.js?v={v}"></script>
<script src="../assets/vendor/leaflet.js?v={v}"></script>
<script src="../assets/app.js?v={v}"></script>
</body>
</html>
"""

FORMS = """<!doctype html><html><body>
<!-- Netlify Forms skeleton: registers the guest sign-in form. Field names must match app.js -->
<form name="guest-signin" data-netlify="true" netlify-honeypot="bot-field" hidden>
  <input type="hidden" name="form-name" value="guest-signin">
  <input name="property"><input name="property_slug">
  <input name="first_name"><input name="last_name"><input name="email" type="email">
  <input name="signed_in_at"><input name="bot-field">
</form>
</body></html>
"""

SW = """const V = '{v}';
const SHELL = ['./assets/app.css?v={v}', './assets/app.js?v={v}', './assets/icons.js?v={v}', './assets/vendor/leaflet.css?v={v}', './assets/vendor/leaflet.js?v={v}', './assets/logo-dark.png', './assets/logo-light.png'];
self.addEventListener('install', (e) => {{ e.waitUntil(caches.open('shell-' + V).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())); }});
self.addEventListener('activate', (e) => {{
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k.startsWith('shell-') && k !== 'shell-' + V).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
}});
self.addEventListener('fetch', (e) => {{
  const r = e.request;
  if (r.method !== 'GET') return;
  const u = new URL(r.url);
  // Pages: always try the network first so guests see edits right away; fall back to the saved copy offline.
  if (r.mode === 'navigate') {{
    e.respondWith(fetch(r).then((res) => {{ const c = res.clone(); caches.open('pages').then((ca) => ca.put(r, c)); return res; }})
      .catch(() => caches.match(r, {{ ignoreSearch: true }})));
    return;
  }}
  // Photos, app files, fonts and map tiles: serve from cache, fill the cache as we go.
  const cacheable = (u.origin === location.origin && (u.pathname.includes('/img/') || u.pathname.includes('/assets/')))
    || /fonts\\.(googleapis|gstatic)\\.com$/.test(u.hostname) || /tile\\.openstreetmap\\.org$/.test(u.hostname);
  if (!cacheable) return;
  const bucket = u.hostname.includes('openstreetmap') ? 'tiles' : 'static';
  e.respondWith(caches.match(r).then((hit) => hit || fetch(r).then((res) => {{
    if (res.ok || res.type === 'opaque') {{ const c = res.clone(); caches.open(bucket).then((ca) => ca.put(r, c)); }}
    return res;
  }})));
}});
"""


def main():
    os.makedirs(os.path.join(SITE, 'assets/vendor'), exist_ok=True)
    shutil.copy(os.path.join(ROOT, 'app/app.css'), os.path.join(SITE, 'assets/app.css'))
    shutil.copy(os.path.join(ROOT, 'app/app.js'), os.path.join(SITE, 'assets/app.js'))
    shutil.copy(os.path.join(LEAFLET, 'leaflet.css'), os.path.join(SITE, 'assets/vendor/leaflet.css'))
    shutil.copy(os.path.join(LEAFLET, 'leaflet.js'), os.path.join(SITE, 'assets/vendor/leaflet.js'))

    names = set(UI_ICONS)
    guides = []
    for p in sorted(glob.glob(os.path.join(ROOT, 'content/guides/*.json'))):
        g = resolve(load(p))
        sp = os.path.join(ROOT, 'content/settings.json')
        if os.path.exists(sp):
            for k, v in load(sp).items():
                g.setdefault(k, v)
        guides.append(g)
        names |= {s['icon'] for s in g['sections'].values()}
        # check photos exist
        for s in g['sections'].values():
            for grp in s['groups']:
                for it in grp['items']:
                    if it.get('photo') and not os.path.exists(os.path.join(SITE, 'img', it['photo'])):
                        print('  ! missing photo', it['photo'], 'in', s['title'])
    open(os.path.join(SITE, 'assets/icons.js'), 'w').write(icons_js(names))
    ic = json.loads(open(os.path.join(SITE, 'assets/icons.js')).read()[len('window.BK_ICONS='):-1])

    redirects = []
    for g in guides:
        d = os.path.join(SITE, g['slug'])
        os.makedirs(d, exist_ok=True)
        data = json.dumps(g, ensure_ascii=False).replace('</', '<\\/')
        page = PAGE.format(name=html.escape(g['name']), short=html.escape(g.get('shortName', g['name'])), slug=g['slug'],
                           cover=g['cover'], v=VERSION, data=data, fab_icon=ic['message-square'],
                           i_home=ic['house'], i_info=ic['info'], i_map=ic['map'], i_search=ic['search'])
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(page)
        manifest = {
            'name': g['name'] + ' Guidebook', 'short_name': g.get('shortName', g['name']),
            'start_url': './', 'scope': './', 'display': 'standalone',
            'background_color': '#0d0d0d', 'theme_color': '#0d0d0d',
            'icons': [{'src': '../assets/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
                      {'src': '../assets/icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any maskable'}],
        }
        json.dump(manifest, open(os.path.join(d, 'manifest.webmanifest'), 'w'), indent=1)
        for old in g.get('oldLinks', []):
            redirects.append(f"{old}  /{g['slug']}/  301")
            redirects.append(f"{old.rstrip('/')}/*  /{g['slug']}/  301")

    open(os.path.join(SITE, '__forms.html'), 'w').write(FORMS)
    open(os.path.join(SITE, '.nojekyll'), 'w').write('')
    # Old TouchStay links -> new guide (works on any static host, incl. GitHub Pages)
    olds = {}
    for g in guides:
        for old in g.get('oldLinks', []):
            gid = old.strip('/').split('/')[-1]
            olds[gid] = g['slug']
            d = os.path.join(SITE, 'guest', gid); os.makedirs(d, exist_ok=True)
            open(os.path.join(d, 'index.html'), 'w').write(
                f'<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex">'
                f'<meta http-equiv="refresh" content="0; url=../../{g["slug"]}/"><a href="../../{g["slug"]}/">Open guide</a>')
    open(os.path.join(SITE, '404.html'), 'w').write(
        '<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex"><title>BK Stays</title><script>'
        'var M=' + json.dumps(olds) + ';var p=location.pathname,m=p.match(/^(.*?)\\/guest\\/([A-Za-z0-9]+)/);'
        'if(m&&M[m[2]])location.replace(m[1]+"/"+M[m[2]]+"/");else location.replace("https://www.bkstays.com");'
        '</script>')
    open(os.path.join(SITE, 'sw.js'), 'w').write(SW.format(v=VERSION))
    open(os.path.join(SITE, 'index.html'), 'w').write(
        '<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex"><title>BK Stays Guidebooks</title>'
        '<meta http-equiv="refresh" content="0; url=https://www.bkstays.com"><a href="https://www.bkstays.com">bkstays.com</a>')
    open(os.path.join(SITE, '_redirects'), 'w').write('\n'.join(redirects) + '\n')
    open(os.path.join(SITE, '_headers'), 'w').write(
        "/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n"
        "/sw.js\n  Cache-Control: no-cache\n"
        "/*/index.html\n  Cache-Control: no-cache\n"
        "/assets/*\n  Cache-Control: public, max-age=86400\n"
        "/img/*\n  Cache-Control: public, max-age=2592000\n")
    for g in guides:
        print(f"built /{g['slug']}/  sections={len(g['sections'])}  items={sum(len(x['items']) for s in g['sections'].values() for x in s['groups'])}")
    print('version', VERSION)


if __name__ == '__main__':
    main()
