/* BK Stays digital guidebook — one shared app for every property guide. */
(function () {
  'use strict';
  const G = JSON.parse(document.getElementById('guide-data').textContent);
  const ICONS = window.BK_ICONS || {};
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const icon = (n, cls = '') => `<svg class="i ${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[n] || ICONS['circle'] || ''}</svg>`;
  const IMG = (f) => `../img/${f}`;
  const store = {
    get(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* storage blocked */ } },
  };
  const GUEST_KEY = 'bk_guest_' + G.slug;
  const telHref = (n) => 'tel:' + String(n).replace(/[^\d+]/g, '');
  const smsHref = (n) => 'sms:' + String(n).replace(/[^\d+]/g, '');

  // ---------------- pin categories ----------------
  const CATS = {
    food: { label: 'Food', color: '#b4532a', icon: 'utensils', types: ['restaurants', 'coffee_shop', 'bars_and_nightlife'] },
    drinks: { label: 'Beer + Wine', color: '#6d3b7d', icon: 'wine', types: ['brewery_pub', 'vineyard'] },
    outdoors: { label: 'Outdoors', color: '#2f6b3f', icon: 'mountain', types: ['hiking', 'parks_and_nature', 'sightseeing', 'other', 'golfing', 'horse_riding'] },
    water: { label: 'Water', color: '#1f6a99', icon: 'sailboat', types: ['swimming', 'beaches', 'boating', 'watersports'] },
    fun: { label: 'Activities', color: '#a86f12', icon: 'ticket', types: ['entertainment_and_activities', 'adventure_activities', 'museums', 'resort_amenities', 'fitness_exercise'] },
    shops: { label: 'Shopping', color: '#4b5563', icon: 'shopping-bag', types: ['grocery_shopping', 'pharmacy', 'souvenirs', 'retail_therapy'] },
    wellness: { label: 'Spa', color: '#b0447e', icon: 'sparkles', types: ['spa_beauty', 'hairdresser'] },
    safety: { label: 'Emergency', color: '#b42318', icon: 'siren', types: ['police', 'medical_facilities'] },
  };
  const catOf = (pin) => Object.keys(CATS).find((k) => CATS[k].types.includes(pin)) || 'outdoors';

  // ---------------- content index ----------------
  const ALL = []; // {sid, sTitle, iid, item}
  Object.values(G.sections).forEach((s) => s.groups.forEach((g) => g.items.forEach((it) => ALL.push({ sid: s.id, sTitle: s.title, iid: it.id, item: it }))));
  const plain = (h) => { const d = document.createElement('div'); d.innerHTML = h || ''; return (d.textContent || '').replace(/\s+/g, ' ').trim(); };
  ALL.forEach((r) => { r.text = plain(r.item.html); });

  // ---------------- rich text post-processing ----------------
  function enrich(html) {
    const d = document.createElement('div');
    d.innerHTML = html || '';
    // autolink bare URLs in text nodes
    const walker = document.createTreeWalker(d, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((n) => {
      if (n.parentElement.closest('a')) return;
      if (!/https?:\/\/\S+/.test(n.nodeValue)) return;
      const span = document.createElement('span');
      span.innerHTML = esc(n.nodeValue).replace(/https?:\/\/[^\s<]+[^\s<.,)]/g, (u) => `<a href="${u}">${u}</a>`);
      n.replaceWith(...span.childNodes);
    });
    $$('a', d).forEach((a) => {
      const h = a.getAttribute('href') || '';
      if (h.startsWith('#')) return;
      if (/^https?:/.test(h)) { a.target = '_blank'; a.rel = 'noopener'; }
    });
    return d.innerHTML;
  }

  // ---------------- views / router ----------------
  const views = { home: $('#v-home'), info: $('#v-info'), section: $('#v-section'), map: $('#v-map'), search: $('#v-search') };
  const DESK = window.matchMedia('(min-width: 960px)');
  function show(name, navKey) {
    const split = DESK.matches && (name === 'info' || name === 'section');
    document.body.classList.toggle('split', split);
    Object.entries(views).forEach(([k, el]) => el.classList.toggle('active', k === name || (split && (k === 'info' || k === 'section'))));
    $$('.nav a').forEach((a) => a.classList.toggle('on', a.dataset.nav === (navKey || name)));
    document.body.classList.toggle('on-map', name === 'map');
    const pb = document.querySelector('.page-bg'); if (pb) pb.hidden = (name === 'home' || name === 'map');
  }

  const firstSection = () => (G.layout.find((g) => g.sections.length) || { sections: [] }).sections[0];
  function markTile(sid) {
    $$('#v-info .tile').forEach((t) => {
      const on = t.getAttribute('href') === '#/info/' + sid;
      t.classList.toggle('sel', on);
      if (on && DESK.matches) setTimeout(() => t.scrollIntoView({ block: 'nearest' }), 30);
    });
  }
  function route() {
    const parts = (location.hash.replace(/^#\/?/, '') || '').split('/').filter(Boolean).map(decodeURIComponent);
    const [top, a, b] = parts;
    if (!top) { show('home'); document.title = G.name + ' Guidebook'; return; }
    if (top === 'info' && a && G.sections[a]) { renderSection(a, b); show('section', 'info'); return; }
    if (top === 'info' && DESK.matches) { renderSection(firstSection()); show('section', 'info'); document.title = G.name + ' Guidebook'; return; }
    if (top === 'info') { markTile(null); show('info'); window.scrollTo(0, 0); document.title = G.name + ' Guidebook'; return; }
    if (top === 'map') { show('map'); openMap(a, b); return; }
    if (top === 'search') { show('search'); setTimeout(() => $('#q').focus(), 50); return; }
    location.hash = '#/';
  }

  // ---------------- home ----------------
  function renderHome() {
    const c = G.contact || {};
    const contact = [
      c.phone && `<a href="${telHref(c.phone)}" aria-label="Call us">${icon('phone')}</a>`,
      c.sms && `<a href="${smsHref(c.sms)}" aria-label="Text us">${icon('message-square')}</a>`,
      c.email && `<a href="mailto:${esc(c.email)}" aria-label="Email us">${icon('mail')}</a>`,
    ].filter(Boolean).join('');
    views.home.innerHTML = `
      <div class="cover" data-cover></div>
      <div class="home-inner">
        <div class="logo-card"><img src="../assets/logo-dark.png" alt="BK Stays"></div>
        <p class="welcome">${esc(G.welcome || 'Welcome!')}</p>
        <h1>${esc(G.name)}</h1>
        <p class="host">${esc(G.hostedBy || '')}</p>
        ${contact ? `<div class="home-contact">${contact}</div>` : ''}
        <a class="btn btn-light" href="#/info">Get Started</a>
      </div>`;
  }
  function setCovers() {
    const desk = window.matchMedia('(min-width: 900px)').matches && G.coverDesktop;
    $$('[data-cover]').forEach((el) => { el.style.backgroundImage = `url(${IMG(desk ? G.coverDesktop : G.cover)})`; });
    const bg = document.querySelector('.page-bg');
    if (bg) bg.style.backgroundImage = `url(${IMG(G.background || G.cover)})`;
  }

  // ---------------- header ----------------
  function head(title, back) {
    return `<div class="head">
      ${back ? `<a class="iconbtn" href="${back}" aria-label="Back">${icon('arrow-left')}</a>` : `<img class="logo" src="../assets/logo-light.png" alt="BK Stays">`}
      ${title ? `<div class="title">${esc(title)}</div>` : '<div class="spacer"></div>'}
      <button class="iconbtn" data-share aria-label="Share this guide">${icon('share-2')}</button>
      <button class="iconbtn" data-print aria-label="Print or save as PDF">${icon('printer')}</button>
    </div>`;
  }

  // ---------------- info grid ----------------
  function renderInfo() {
    const groups = G.layout.map((grp) => `
      ${grp.heading ? `<div class="grid-head">${esc(grp.heading)}</div>` : ''}
      <div class="tiles">${grp.sections.filter((id) => G.sections[id]).map((id) => {
        const s = G.sections[id];
        return `<a class="tile" href="#/info/${id}">${icon(s.icon)}<span>${esc(s.title)}</span></a>`;
      }).join('')}</div>`).join('');
    views.info.innerHTML = head('') + `<div class="wrap"><div id="install-slot"></div>${groups}</div>`;
    renderInstall();
  }

  // ---------------- section ----------------
  function renderSection(sid, focusIid) {
    const s = G.sections[sid];
    document.title = s.title + ' · ' + G.name;
    const single = s.groups.reduce((n, g) => n + g.items.length, 0) === 1;
    const body = s.groups.map((g) => `
      ${g.title ? `<div class="group-title">${esc(g.title)}</div>` : ''}
      ${g.items.map((it) => itemHTML(s, it, single || it.id === focusIid)).join('')}`).join('');
    views.section.innerHTML = head(s.title, '#/info') + `<div class="sec-wrap">${body}</div>`;
    $$('details.item', views.section).forEach((d) => {
      d.addEventListener('toggle', () => { if (d.open) loadVideo(d); });
      if (d.open) loadVideo(d);
    });
    if (focusIid) {
      const el = document.getElementById('it-' + focusIid);
      if (el) requestAnimationFrame(() => el.scrollIntoView({ block: 'start' }));
    } else { window.scrollTo(0, 0); views.section.scrollTop = 0; }
    markTile(sid);
  }
  function itemHTML(s, it, open) {
    const dir = it.loc ? `https://www.google.com/maps/dir/?api=1&destination=${it.loc[0]},${it.loc[1]}` : '';
    return `<details class="item" id="it-${it.id}" ${open ? 'open' : ''}>
      <summary>${it.photo ? `<img class="thumb" src="${IMG(it.photo)}" alt="" loading="lazy">` : ''}<span class="t">${esc(it.title)}</span>${icon('chevron-down', 'chev')}</summary>
      <div class="item-body">
        ${it.photo ? `<img class="photo${it.photoFit === 'full' ? ' full' : ''}" src="${IMG(it.photo)}" alt="" loading="lazy">` : ''}
        <div class="rich">${enrich(it.html)}</div>
        ${it.video ? `<div class="video" data-src="${esc(it.video)}"></div>` : ''}
        ${it.loc ? `<div class="item-actions">
          <a class="chip dark" href="#/map/${s.id}/${it.id}">${icon('map-pin')}View on map</a>
          <a class="chip" href="${dir}" target="_blank" rel="noopener">${icon('navigation')}Directions</a></div>` : ''}
      </div></details>`;
  }
  function loadVideo(d) {
    const v = $('.video[data-src]', d);
    if (!v || v.firstChild) return;
    v.innerHTML = `<iframe src="${v.dataset.src}" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen loading="lazy" title="Video"></iframe>`;
  }

  // ---------------- search ----------------
  function renderSearch() {
    views.search.innerHTML = head('Search') + `<div class="wrap">
      <div class="search-box"><label>${icon('search')}<input id="q" type="search" placeholder="Search the guide — wifi, hot tub, pizza…" autocomplete="off" enterkeyhint="search"></label></div>
      <div class="results" id="results"><div class="empty">Search everything in this guide.</div></div></div>`;
    $('#q').addEventListener('input', (e) => doSearch(e.target.value));
  }
  function doSearch(q) {
    const out = $('#results');
    q = q.trim();
    if (q.length < 2) { out.innerHTML = '<div class="empty">Search everything in this guide.</div>'; return; }
    const terms = q.toLowerCase().split(/\s+/);
    const hits = ALL.map((r) => {
      const t = r.item.title.toLowerCase(), x = r.text.toLowerCase(), st = r.sTitle.toLowerCase();
      if (!terms.every((w) => t.includes(w) || x.includes(w) || st.includes(w))) return null;
      const score = terms.reduce((n, w) => n + (t.includes(w) ? 10 : 0) + (st.includes(w) ? 4 : 0) + (x.includes(w) ? 1 : 0), 0);
      return { r, score };
    }).filter(Boolean).sort((a, b) => b.score - a.score).slice(0, 60);
    if (!hits.length) { out.innerHTML = `<div class="empty">No results for “${esc(q)}”.</div>`; return; }
    const re = new RegExp('(' + terms.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|') + ')', 'ig');
    const mark = (s) => esc(s).replace(re, '<mark>$1</mark>');
    out.innerHTML = hits.map(({ r }) => {
      const x = r.text, i = Math.max(0, x.toLowerCase().indexOf(terms[0]) - 50);
      const snip = (i > 0 ? '…' : '') + x.slice(i, i + 150) + (x.length > i + 150 ? '…' : '');
      return `<a href="#/info/${r.sid}/${r.iid}"><div class="r-sec">${esc(r.sTitle)}</div><div class="r-title">${mark(r.item.title)}</div><div class="r-snip">${mark(snip)}</div></a>`;
    }).join('');
  }

  // ---------------- map ----------------
  let map, layers = {}, markerById = {}, activeCat = 'all';
  function renderMapShell() {
    const chips = [`<button class="chip on" data-cat="all">All</button>`].concat(Object.entries(CATS)
      .filter(([k]) => ALL.some((r) => r.item.loc && catOf(r.item.pin) === k))
      .map(([k, c]) => `<button class="chip" data-cat="${k}" style="--c:${c.color}"><span class="dot"></span>${esc(c.label)}</button>`));
    views.map.innerHTML = head('Map') + `<div id="map"></div><div class="map-filters">${chips.join('')}</div>`;
    $$('.map-filters .chip').forEach((b) => b.addEventListener('click', () => filterMap(b.dataset.cat)));
  }
  function pinIcon(cat, home) {
    const c = home ? null : CATS[cat];
    return L.divIcon({
      className: '', iconSize: home ? [42, 42] : [34, 34], iconAnchor: home ? [21, 42] : [17, 34], popupAnchor: [0, home ? -40 : -32],
      html: `<div class="pin ${home ? 'home' : ''}" style="--c:${c ? c.color : '#111'}">${icon(home ? 'house' : c.icon)}</div>`,
    });
  }
  function openMap(sid, iid) {
    if (!window.L) return;
    if (!map) {
      map = L.map('map', { zoomControl: false, attributionControl: true }).setView(G.location, 11);
      L.control.zoom({ position: 'bottomleft' }).addTo(map);
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      }).addTo(map);
      const home = L.marker(G.location, { icon: pinIcon(null, true), zIndexOffset: 1000 }).addTo(map);
      home.bindPopup(`<div class="pop"><div class="pc"><div class="pt">${esc(G.name)}</div><div class="ps">${esc(G.address || '')}</div>
        <div class="item-actions"><a class="chip dark" target="_blank" rel="noopener" href="https://www.google.com/maps/dir/?api=1&destination=${G.location[0]},${G.location[1]}">${icon('navigation')}Directions</a></div></div></div>`);
      const byKey = {};
      ALL.filter((r) => r.item.loc).forEach((r) => {
        const key = r.item.title.toLowerCase() + r.item.loc.join(',');
        if (byKey[key]) { markerById[r.sid + '/' + r.iid] = byKey[key]; return; }
        const cat = catOf(r.item.pin);
        const m = L.marker(r.item.loc, { icon: pinIcon(cat) });
        m.bindPopup(`<div class="pop">${r.item.photo ? `<img src="${IMG(r.item.photo)}" alt="" loading="lazy">` : ''}<div class="pc">
          <div class="pt">${esc(r.item.title)}</div><div class="ps">${esc(r.sTitle)}</div>
          <div class="item-actions"><a class="chip dark" href="#/info/${r.sid}/${r.iid}">Details</a>
          <a class="chip" target="_blank" rel="noopener" href="https://www.google.com/maps/dir/?api=1&destination=${r.item.loc[0]},${r.item.loc[1]}">${icon('navigation')}Go</a></div></div></div>`);
        (layers[cat] = layers[cat] || L.layerGroup().addTo(map)).addLayer(m);
        byKey[key] = m;
        markerById[r.sid + '/' + r.iid] = m;
      });
      fitAll();
    }
    setTimeout(() => {
      map.invalidateSize();
      const m = sid && markerById[sid + '/' + iid];
      if (m) {
        if (activeCat !== 'all') filterMap('all');
        map.setView(m.getLatLng(), 15);
        m.openPopup();
      }
    }, 60);
  }
  function fitAll() {
    const pts = [G.location];
    Object.values(layers).forEach((lg) => { if (map.hasLayer(lg)) lg.eachLayer((m) => pts.push(m.getLatLng())); });
    map.fitBounds(L.latLngBounds(pts), { padding: [40, 40], maxZoom: 13 });
  }
  function filterMap(cat) {
    activeCat = cat;
    $$('.map-filters .chip').forEach((b) => b.classList.toggle('on', b.dataset.cat === cat));
    Object.entries(layers).forEach(([k, lg]) => {
      const on = cat === 'all' || cat === k;
      if (on && !map.hasLayer(lg)) map.addLayer(lg);
      if (!on && map.hasLayer(lg)) map.removeLayer(lg);
    });
    map.closePopup();
    fitAll();
  }

  // ---------------- contact sheet ----------------
  function openContact() {
    const c = G.contact || {};
    const rows = [
      c.sms && `<a class="row" href="${smsHref(c.sms)}"><span class="ic">${icon('message-square')}</span><span>Text us<small>${esc(c.sms)}</small></span></a>`,
      c.phone && `<a class="row" href="${telHref(c.phone)}"><span class="ic">${icon('phone')}</span><span>Call us<small>${esc(c.phone)}</small></span></a>`,
      c.email && `<a class="row" href="mailto:${esc(c.email)}"><span class="ic">${icon('mail')}</span><span>Email us<small>${esc(c.email)}</small></span></a>`,
    ].filter(Boolean).join('');
    const scrim = document.createElement('div');
    scrim.className = 'scrim';
    scrim.innerHTML = `<div class="sheet" role="dialog" aria-modal="true" aria-label="Contact your hosts">
      <h3>Contact your hosts</h3><p>We usually reply within minutes. For emergencies, dial 911.</p>${rows}
      <button class="close">Close</button></div>`;
    scrim.addEventListener('click', (e) => { if (e.target === scrim || e.target.classList.contains('close')) scrim.remove(); });
    document.body.appendChild(scrim);
  }

  // ---------------- share / print / toast ----------------
  function toast(msg) {
    const t = document.createElement('div');
    t.className = 'toast'; t.textContent = msg; document.body.appendChild(t);
    setTimeout(() => t.remove(), 2200);
  }
  async function share() {
    const url = location.origin + location.pathname;
    if (navigator.share) { try { await navigator.share({ title: G.name + ' Guidebook', url }); } catch (e) { /* cancelled */ } return; }
    try { await navigator.clipboard.writeText(url); toast('Link copied'); } catch (e) { prompt('Copy this link', url); }
  }
  let openedForPrint = [];
  window.addEventListener('beforeprint', () => { openedForPrint = $$('#v-section details.item:not([open])'); openedForPrint.forEach((d) => d.setAttribute('open', '')); });
  window.addEventListener('afterprint', () => { openedForPrint.forEach((d) => d.removeAttribute('open')); });
  document.addEventListener('click', (e) => {
    if (e.target.closest('[data-share]')) share();
    if (e.target.closest('[data-print]')) {
      if (!views.section.classList.contains('active')) toast('Open a section, then tap print to save it as a PDF');
      else window.print();
    }
  });

  // ---------------- add to home screen ----------------
  let deferredPrompt = null;
  window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); deferredPrompt = e; renderInstall(); });
  const standalone = () => window.matchMedia('(display-mode: standalone)').matches || navigator.standalone;
  function renderInstall() {
    const slot = $('#install-slot');
    if (!slot) return;
    if (standalone() || store.get('bk_install_dismissed')) { slot.innerHTML = ''; return; }
    const ios = /iphone|ipad|ipod/i.test(navigator.userAgent);
    if (!deferredPrompt && !ios) { slot.innerHTML = ''; return; }
    slot.innerHTML = `<div class="install">${icon('smartphone')}<div class="txt"><b>Add this guide to your phone</b>One tap to open it any time, even offline.</div>
      <button class="go">${deferredPrompt ? 'Add' : 'How?'}</button><button class="x" aria-label="Dismiss">${icon('x')}</button></div>`;
    $('.install .go', slot).addEventListener('click', async () => {
      if (deferredPrompt) { deferredPrompt.prompt(); await deferredPrompt.userChoice; deferredPrompt = null; renderInstall(); }
      else location.hash = '#/info/add-to-phone';
    });
    $('.install .x', slot).addEventListener('click', () => { store.set('bk_install_dismissed', 1); slot.innerHTML = ''; });
  }

  // ---------------- guest gate ----------------
  function submitGuest(g) {
    const body = new URLSearchParams({
      'form-name': 'guest-signin', property: G.name, property_slug: G.slug,
      first_name: g.first, last_name: g.last, email: g.email, signed_in_at: g.at, 'bot-field': '',
    });
    // Sign-ins go straight to the Google Sheet (Apps Script web app). Falls back to the old Netlify form.
    const url = G.signinUrl || 'https://bkstays-guides.netlify.app/__forms.html';
    return fetch(url, { method: 'POST', mode: 'no-cors', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: body.toString() })
      .then(() => { g.sent = true; store.set(GUEST_KEY, g); })
      .catch(() => { /* retried next visit */ });
  }
  function gate() {
    const g = store.get(GUEST_KEY);
    if (!G.gate || (g && g.email)) { if (g && !g.sent) submitGuest(g); return; }
    const el = document.createElement('div');
    el.className = 'gate';
    el.innerHTML = `<div class="cover" data-cover></div>
      <form class="gate-card" novalidate>
        <div class="logo-card"><img src="../assets/logo-dark.png" alt="BK Stays"></div>
        <h2>Welcome to ${esc(G.name)}</h2>
        <p class="sub">Enter your details to open your digital guidebook.</p>
        <div class="two">
          <div class="field"><label for="g-first">First name</label><input id="g-first" name="first" autocomplete="given-name" required></div>
          <div class="field"><label for="g-last">Last name</label><input id="g-last" name="last" autocomplete="family-name" required></div>
        </div>
        <div class="field"><label for="g-email">Email</label><input id="g-email" name="email" type="email" autocomplete="email" inputmode="email" required></div>
        <input class="hp" name="bot-field" tabindex="-1" autocomplete="off" aria-hidden="true">
        <div class="err" role="alert"></div>
        <button class="btn btn-dark" type="submit">Open Guidebook</button>
        <p class="fine">You'll only need to do this once on this device.</p>
      </form>`;
    document.body.appendChild(el);
    setCovers();
    $('form', el).addEventListener('submit', (e) => {
      e.preventDefault();
      const f = e.target;
      if (f['bot-field'].value) return;
      const first = f.first.value.trim(), last = f.last.value.trim(), email = f.email.value.trim();
      const err = $('.err', el);
      if (!first || !last) { err.textContent = 'Please enter your first and last name.'; return; }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) { err.textContent = 'Please enter a valid email address.'; return; }
      const g2 = { first, last, email, at: new Date().toISOString(), sent: false };
      store.set(GUEST_KEY, g2);
      submitGuest(g2);
      el.remove();
    });
  }

  // ---------------- boot ----------------
  if (G.background !== false) {
    const bg = document.createElement('div'); bg.className = 'page-bg'; bg.setAttribute('aria-hidden', 'true');
    document.body.prepend(bg); document.body.classList.add('bg-on');
  }
  renderHome(); renderInfo(); renderSearch(); renderMapShell(); setCovers();
  $('#fab').addEventListener('click', openContact);
  window.addEventListener('hashchange', route);
  DESK.addEventListener('change', route);
  window.addEventListener('resize', setCovers);
  route();
  gate();
  if ('serviceWorker' in navigator) window.addEventListener('load', () => navigator.serviceWorker.register('../sw.js').catch(() => {}));
})();
