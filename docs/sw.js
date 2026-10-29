const V = '20261029235337';
const SHELL = ['./assets/app.css?v=20261029235337', './assets/app.js?v=20261029235337', './assets/icons.js?v=20261029235337', './assets/vendor/leaflet.css?v=20261029235337', './assets/vendor/leaflet.js?v=20261029235337', './assets/logo-dark.png', './assets/logo-light.png'];
self.addEventListener('install', (e) => { e.waitUntil(caches.open('shell-' + V).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k.startsWith('shell-') && k !== 'shell-' + V).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  const r = e.request;
  if (r.method !== 'GET') return;
  const u = new URL(r.url);
  // Pages: always try the network first so guests see edits right away; fall back to the saved copy offline.
  if (r.mode === 'navigate') {
    e.respondWith(fetch(r).then((res) => { const c = res.clone(); caches.open('pages').then((ca) => ca.put(r, c)); return res; })
      .catch(() => caches.match(r, { ignoreSearch: true })));
    return;
  }
  // Photos, app files, fonts and map tiles: serve from cache, fill the cache as we go.
  const cacheable = (u.origin === location.origin && (u.pathname.includes('/img/') || u.pathname.includes('/assets/')))
    || /fonts\.(googleapis|gstatic)\.com$/.test(u.hostname) || /tile\.openstreetmap\.org$/.test(u.hostname);
  if (!cacheable) return;
  const bucket = u.hostname.includes('openstreetmap') ? 'tiles' : 'static';
  e.respondWith(caches.match(r).then((hit) => hit || fetch(r).then((res) => {
    if (res.ok || res.type === 'opaque') { const c = res.clone(); caches.open(bucket).then((ca) => ca.put(r, c)); }
    return res;
  })));
});
