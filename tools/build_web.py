"""Build the BK Stays website (static) into site/www/.

Sources:
  web/homes.json             the 14 homes (slug, Hospitable uuid + widget id, state, old Squarespace path)
  web/site.css               styles
  web/pages.json             editable copy for Home / About / Property Management / Contact
  ../site-src/hosp/<uuid>.json + img/<uuid>/NN.jpg   listing text + photos pulled from Hospitable
  ../site-src/sqimg/*.jpg    region + family photos from the old Squarespace site
All links are relative, so the site works at a sub-path (preview) and at the domain root.
Usage: python3 tools/build_web.py
"""
import json
import web_polish, os, re, shutil, html as H, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(os.path.dirname(ROOT), 'site-src')
OUT = os.path.join(ROOT, 'site', 'www')
W = os.path.join(ROOT, 'web')
sys.path.insert(0, os.path.join(ROOT, 'tools'))

HOMES = json.load(open(os.path.join(W, 'homes.json')))
PAGES = json.load(open(os.path.join(W, 'pages.json')))
WIDGET = 'https://booking.hospitable.com/widget/8715731b-a473-4708-8804-c3f364e378bb/'
SEARCH_ID = 'da3c3d43-a33e-46a8-9f62-91da48ab8f94'
STATES = {
    'georgia': ('Georgia', 'North Georgia Mountains', 'Cabins and condos around Blue Ridge, Ellijay and McCaysville.', 'region-georgia.jpg'),
    'michigan': ('Michigan', 'Northern Michigan', 'Lake-country homes at Shanty Creek in Bellaire.', 'region-michigan.jpg'),
    'florida': ('Florida', 'Florida Beaches', 'Pool homes and beachfront condos in Fort Lauderdale and Panama City Beach.', 'region-florida.jpg'),
    'minnesota': ('Minnesota', "Minnesota's Iron Range", 'A lake and ski retreat next to Giants Ridge.', 'region-minnesota.jpg'),
}
STATE_ORDER = ['georgia', 'florida', 'michigan', 'minnesota']
PHONE, PHONE_TEL, EMAIL = '(404) 358-1552', '+14043581552', 'brandon@bkstays.com'
SOCIAL = {'Instagram': 'https://www.instagram.com/bk_stays/', 'Facebook': 'https://www.facebook.com/profile.php?id=61551815370553',
          'LinkedIn': 'https://www.linkedin.com/company/bk-stays/'}
SKIP_CAPTION = 'right in the center of downtown'
SKIP_IMG = {'tails-trails-hideaway': {8}}  # guest review screenshot
FIXES = [('Barrell', 'Barrel'), ("Giant's Ridge", 'Giants Ridge'), ('Wifi', 'Wi-Fi'), ('WiFi', 'Wi-Fi'), ('Smart Tv\'s', 'Smart TVs'), ("TV's", 'TVs'), ("Tv's", 'TVs')]
WL = {'TV', 'TVS', 'HOA', 'BBQ', 'AC', 'GA', 'FL', 'MI', 'MN', 'USA', 'HDR', 'EV', 'US', 'PCB', 'BR', 'DIY', 'LED', 'HVAC', 'NBA', 'ATV'}

ICONS = {
    'Instagram': '<svg viewBox="0 0 24 24"><path d="M12 2.2c3.2 0 3.6 0 4.8.1 1.2.1 1.8.2 2.2.4.6.2 1 .5 1.4.9.4.4.7.8.9 1.4.2.4.4 1 .4 2.2.1 1.3.1 1.6.1 4.8s0 3.6-.1 4.8c-.1 1.2-.2 1.8-.4 2.2-.2.6-.5 1-.9 1.4-.4.4-.8.7-1.4.9-.4.2-1 .4-2.2.4-1.3.1-1.6.1-4.8.1s-3.6 0-4.8-.1c-1.2-.1-1.8-.2-2.2-.4-.6-.2-1-.5-1.4-.9-.4-.4-.7-.8-.9-1.4-.2-.4-.4-1-.4-2.2C2.2 15.6 2.2 15.2 2.2 12s0-3.6.1-4.8c.1-1.2.2-1.8.4-2.2.2-.6.5-1 .9-1.4.4-.4.8-.7 1.4-.9.4-.2 1-.4 2.2-.4C8.4 2.2 8.8 2.2 12 2.2zm0 4.6a5.2 5.2 0 1 0 0 10.4 5.2 5.2 0 0 0 0-10.4zm0 8.6a3.4 3.4 0 1 1 0-6.8 3.4 3.4 0 0 1 0 6.8zm5.4-9.9a1.2 1.2 0 1 0 0 2.4 1.2 1.2 0 0 0 0-2.4z"/></svg>',
    'Facebook': '<svg viewBox="0 0 24 24"><path d="M13.5 22v-8h2.7l.4-3.2h-3.1V8.8c0-.9.3-1.5 1.6-1.5h1.7V4.4c-.3 0-1.3-.1-2.5-.1-2.5 0-4.2 1.5-4.2 4.3v2.3H7.4V14h2.7v8h3.4z"/></svg>',
    'LinkedIn': '<svg viewBox="0 0 24 24"><path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9h4v12H3zM9 9h3.8v1.7h.1c.5-1 1.8-2 3.7-2 4 0 4.7 2.6 4.7 6V21h-4v-5.6c0-1.3 0-3-1.9-3s-2.1 1.4-2.1 2.9V21H9z"/></svg>',
    'phone': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/></svg>',
    'mail': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/></svg>',
    'pin': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/></svg>',
}


def esc(s):
    return H.escape(s or '', quote=True)


def fixcaps(text):
    def rep(m):
        w = m.group(0)
        if all(x in WL for x in re.split(r'[ \-/]', w)):
            return w
        return w[0] + w[1:].lower() if len(w) > 1 else w
    return re.sub(r'\b[A-Z][A-Z]{2,}\b(?:[ \-/][A-Z][A-Z]+\b)*', rep, text)


def clean(t):
    for a, b in FIXES:
        t = t.replace(a, b)
    return fixcaps(t.replace('\xa0', ' ')).strip()


def parse_overview(txt):
    """'★★ HEADING ★★' blocks with bullets / paragraphs -> [(heading, [paras], [bullets])]."""
    secs, cur = [], None
    for raw in (txt or '').splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r'^[★☆✦✧\*]+\s*(.+?)\s*[★☆✦✧\*]+$', line)
        if m and len(m.group(1)) < 60:
            cur = [clean(m.group(1)).title().replace("'S", "'s"), [], []]
            secs.append(cur)
            continue
        if cur is None:
            cur = ['', [], []]
            secs.append(cur)
        b = re.match(r'^(?:[•✹✔✓\-\*]|\d+\.)\s*(.+)$', line)
        if b:
            item = clean(b.group(1)).rstrip('.')
            if item:
                cur[2].append(item)
        else:
            cur[1].append(clean(line))
    return [s for s in secs if s[1] or s[2]]


def load_home(h):
    d = json.load(open(os.path.join(SRC, 'hosp', h['uuid'] + '.json')))
    cap = d.get('capacity') or {}
    addr = d.get('address_full') or d.get('address') or {}
    imgs = []
    for i, im in enumerate(d.get('images', [])[:24]):
        if i in SKIP_IMG.get(h['slug'], set()):
            continue
        if SKIP_CAPTION in (im.get('caption') or '') and h['slug'] != 'best-of-blue-ridge':
            continue
        src = os.path.join(SRC, 'hosp', 'img', h['uuid'], f'{i:02d}.jpg')
        if os.path.exists(src):
            imgs.append((i, re.sub(r'\s+', ' ', im.get('caption') or '').strip()))
    h.update({
        'city': addr.get('city', ''), 'st': addr.get('state', ''),
        'guests': cap.get('max'), 'bedrooms': cap.get('bedrooms'), 'beds': cap.get('beds'), 'baths': cap.get('bathrooms'),
        'summary': d.get('summary') or '', 'overview': parse_overview(d.get('space_overview')), 'imgs': imgs,
    })
    return h


def fmt_n(x):
    return ('%g' % x) if isinstance(x, (int, float)) else str(x or '')


def facts(h):
    out = []
    for n, w in [(h['guests'], 'guest'), (h['bedrooms'], 'bedroom'), (h['beds'], 'bed'), (h['baths'], 'bath')]:
        if n:
            out.append(f'{fmt_n(n)} {w}{"" if n == 1 else "s"}')
    return out


# ---------------------------------------------------------------- layout
def nav(p):
    groups = ''
    for st in STATE_ORDER:
        hs = [h for h in HOMES if h['state'] == st]
        groups += f'<div class="group">{STATES[st][0]}</div>' + ''.join(f'<a href="{p}{h["slug"]}/">{esc(h["name"])}</a>' for h in hs)
    return f'''<header class="top"><div class="wrap">
<a class="logo" href="{p}" aria-label="BK Stays home"><img src="{p}assets/logo-dark.png" alt="BK Stays vacation rentals" width="128" height="40"></a>
<nav class="nav" id="nav">
<div class="drop"><button type="button">Our Homes ▾</button><div class="drop-menu"><div class="inner"><a href="{p}homes/"><b>All homes</b></a>{groups}</div></div></div>
<a href="{p}about-us/">About Us</a>
<a href="{p}property-management/">Property Management</a>
<a href="{p}contact/">Contact</a>
<a class="btn pink sm" href="{p}#search">Book Now</a>
</nav>
<button class="menu-btn" aria-label="Menu" onclick="document.getElementById('nav').classList.toggle('open')"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M3 12h18M3 18h18"/></svg></button>
</div></header>'''


def footer(p):
    homes = ''.join(f'<a href="{p}{h["slug"]}/">{esc(h["name"])}</a>' for h in HOMES[:7])
    homes2 = ''.join(f'<a href="{p}{h["slug"]}/">{esc(h["name"])}</a>' for h in HOMES[7:])
    soc = ''.join(f'<a href="{u}" aria-label="{k}" target="_blank" rel="noopener">{ICONS[k]}</a>' for k, u in SOCIAL.items())
    return f'''<footer><div class="wrap"><div class="cols">
<div><a class="logo" href="{p}"><img src="{p}assets/logo-light.png" alt="BK Stays" width="134" height="42"></a>
<p>Modern comfort. Scenic retreats. Hosts who care.</p>
<a href="tel:{PHONE_TEL}">{PHONE}</a><a href="mailto:{EMAIL}">{EMAIL}</a><div class="social">{soc}</div></div>
<div><h4>Our Homes</h4>{homes}</div>
<div><h4>&nbsp;</h4>{homes2}</div>
<div><h4>BK Stays</h4><a href="{p}homes/">All homes</a><a href="{p}about-us/">About Us</a><a href="{p}property-management/">Property Management</a><a href="{p}contact/">Contact</a><a href="{p}follow-us/">Follow Us</a></div>
</div><div class="fine"><span>© BK Stays · Atlanta, Georgia</span><span>Book direct for our best rates.</span></div></div></footer>'''


def page(p, title, desc, body, extra_head='', body_cls='', og_img=''):
    og = f'<meta property="og:image" content="{og_img}">' if og_img else ''
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">{og}
<link rel="icon" type="image/png" href="{p}assets/favicon.png"><link rel="apple-touch-icon" href="{p}assets/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{p}site.css?v={VER}">{extra_head}
</head><body class="{body_cls}">
{nav(p)}
<main>{body}</main>
{footer(p)}
</body></html>'''


def card(h, p):
    img = f'{p}img/{h["slug"]}/{h["imgs"][0][0]:02d}-sm.jpg' if h['imgs'] else ''
    return f'''<a class="home" href="{p}{h["slug"]}/" data-state="{h["state"]}">
<div class="ph"><img src="{img}" alt="{esc(h["name"])}" loading="lazy"><span class="tag">{esc(h["city"])}, {esc(h["st"])}</span></div>
<div class="bd"><b>{esc(h["name"])}</b><span class="facts">{" · ".join(facts(h))}</span><span class="go">View home →</span></div></a>'''


def search_block():
    return f'''<section class="search-band" id="search"><div class="wrap"><div class="label">Find your dates</div></div>
<hospitable-direct-mps identifier="{SEARCH_ID}" type="custom" results-url="search/"></hospitable-direct-mps>
<script src="https://hospitable.b-cdn.net/direct-property-search-widget/hospitable-search-widget.prod.js"></script></section>'''


def write(rel, s):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w').write(s)


# ---------------------------------------------------------------- pages
def build_home():
    p = ''
    P = PAGES['home']
    dests = ''.join(f'''<a class="dest" href="{st}/"><img src="img/{STATES[st][3]}" alt="{STATES[st][1]}" loading="lazy">
<div class="t"><b>{STATES[st][1]}</b><span>{sum(1 for h in HOMES if h["state"] == st)} home{"s" if sum(1 for h in HOMES if h["state"] == st) > 1 else ""}</span></div></a>''' for st in STATE_ORDER)
    chips = '<button class="chip on" data-f="all">All</button>' + ''.join(f'<button class="chip" data-f="{st}">{STATES[st][0]}</button>' for st in STATE_ORDER)
    cards = ''.join(card(h, p) for h in HOMES)
    stats = ''.join(f'<div class="stat"><b>{esc(a)}</b><span>{esc(b)}</span></div>' for a, b in P['stats'])
    body = f'''<section class="hero"><div class="bg" style="background-image:url('img/{P["hero"]}')"></div><div class="wrap">
<span class="eyebrow" style="color:#fff">BK Stays · Vacation Rentals</span>
<h1>{esc(P["headline"])}</h1><p class="lead">{esc(P["lead"])}</p><div style="display:flex;gap:12px;flex-wrap:wrap"><a class="btn pink" href="#search">Check availability</a><a class="btn ghost" style="color:#fff;border-color:#fff" href="#homes">Browse homes</a></div></div></section>
{search_block()}
<section class="block dark tight"><div class="wrap"><div class="stats">{stats}</div></div></section>
<section class="block"><div class="wrap"><div class="section-head"><div><span class="eyebrow">Where we host</span><h2>Pick your kind of getaway</h2></div>
<p class="muted">Mountain cabins, lake houses and beach homes, each one hosted by our family.</p></div><div class="dests">{dests}</div></div></section>
<section class="block white" id="homes"><div class="wrap"><div class="section-head"><div><span class="eyebrow">Come stay with us</span><h2>Our homes</h2></div></div>
<div class="filters">{chips}</div><div class="homes">{cards}</div></div></section>
<section class="block"><div class="wrap split"><img class="portrait" src="img/about-family-2026.jpg" alt="Brandon, Katharina, Emmy and Leo" loading="lazy">
<div><span class="eyebrow">Meet your hosts</span><h2>{esc(P["hostsTitle"])}</h2><p>{esc(P["hostsText"])}</p><a class="btn" href="about-us/">Our story</a></div></div></section>
<section class="block white"><div class="wrap"><div class="section-head"><div><span class="eyebrow">Why book direct</span><h2>Book with us directly</h2></div></div>
<div class="features">{"".join(f'<div class="feature"><div class="ic">{i+1}</div><h3>{esc(t)}</h3><p>{esc(d)}</p></div>' for i, (t, d) in enumerate(P["direct"]))}</div></div></section>
<section class="block"><div class="wrap"><div class="cta"><div><h2>Own a vacation rental?</h2><p>We manage homes end to end, with a free property analysis to start.</p></div>
<a class="btn pink" href="property-management/">Property management</a></div></div></section>
<script>{FILTER_JS}</script>'''
    write('index.html', page(p, 'BK Stays | Vacation Rentals in Georgia, Florida, Michigan and Minnesota', P['lead'], body))


FILTER_JS = """document.querySelectorAll('.chip').forEach(function(c){c.addEventListener('click',function(){
document.querySelectorAll('.chip').forEach(function(x){x.classList.remove('on')});c.classList.add('on');var f=c.dataset.f;
document.querySelectorAll('.home').forEach(function(h){h.style.display=(f==='all'||h.dataset.state===f)?'':'none'});});});"""


def build_homes_index():
    p = '../'
    chips = '<button class="chip on" data-f="all">All</button>' + ''.join(f'<button class="chip" data-f="{st}">{STATES[st][0]}</button>' for st in STATE_ORDER)
    body = f'''<section class="page-hero"><div class="bg" style="background-image:url('{p}img/region-georgia.jpg')"></div><div class="wrap"><span class="eyebrow" style="color:#fff">Come stay with us</span><h1>All homes</h1>
<p class="lead">{len(HOMES)} homes across Georgia, Florida, Michigan and Minnesota.</p></div></section>
<section class="block"><div class="wrap"><div class="filters">{chips}</div><div class="homes">{"".join(card(h, p) for h in HOMES)}</div></div></section><script>{FILTER_JS}</script>'''
    write('homes/index.html', page(p, 'Our Homes | BK Stays', 'All BK Stays vacation rentals.', body))


def build_states():
    p = '../'
    for st in STATE_ORDER:
        name, title, blurb, img = STATES[st]
        hs = [h for h in HOMES if h['state'] == st]
        body = f'''<section class="page-hero"><div class="bg" style="background-image:url('{p}img/{img}')"></div><div class="wrap"><span class="eyebrow" style="color:#fff">{name}</span><h1>{title}</h1><p class="lead">{blurb}</p></div></section>
<section class="block"><div class="wrap"><div class="homes">{"".join(card(h, p) for h in hs)}</div></div></section>'''
        write(f'{st}/index.html', page(p, f'{title} Vacation Rentals | BK Stays', blurb, body))


def build_property(h):
    p = '../'
    imgs = h['imgs']
    first5 = imgs[:5]
    gal = ''.join(f'<button type="button" data-i="{n}"><img src="{p}img/{h["slug"]}/{i:02d}{"" if n == 0 else "-sm"}.jpg" alt="{esc(c[:120]) or esc(h["name"])}" {"" if n == 0 else "loading=lazy"}></button>' for n, (i, c) in enumerate(first5))
    data = json.dumps([[f'{p}img/{h["slug"]}/{i:02d}.jpg', c] for i, c in imgs])
    secs = ''
    for head, paras, items, tail in web_polish.polish(h['slug'], h['overview']):
        secs += (f'<h3>{esc(head)}</h3>' if head else '') + ''.join(f'<p>{esc(x)}</p>' for x in paras)
        if items:
            secs += ('<ul class="two">' if 'highlight' in head.lower() else '<ul>') + ''.join(f'<li>{esc(x)}</li>' for x in items) + '</ul>'
        secs += ''.join(f'<p class="after">{esc(x)}</p>' for x in tail)
    summary = ''.join(f'<p>{esc(clean(x))}</p>' for x in re.split(r'\n\s*\n', h['summary']) if x.strip() and not re.match(r'^-?\s*Hosted By|^Find the Best Rates|^Hosted by', x.strip(), re.I))
    if h.get('noWidget'):
        book = f'<div class="fallback"><p>Online booking for this home is coming soon. Message us and we\'ll check your dates.</p><a class="btn" href="{p}contact/">Check availability</a></div>'
    else:
        book = f'<iframe id="booking-iframe" sandbox="allow-top-navigation allow-scripts allow-same-origin allow-popups allow-forms" src="{WIDGET}{h["hid"]}" title="Book {esc(h["name"])}" loading="lazy"></iframe>'
    others = [o for o in HOMES if o['state'] == h['state'] and o['slug'] != h['slug']][:3] or [o for o in HOMES if o['slug'] != h['slug']][:3]
    fact_html = ''.join(f'<span class="fact">{f}</span>' for f in facts(h))
    body = f'''<div class="wrap">
<div class="gallery">{gal}<button type="button" class="all" data-i="0">See all {len(imgs)} photos</button></div>
<div class="prop-head"><div><span class="eyebrow">{esc(h["city"])}, {esc(h["st"])}</span><h1>{esc(h["name"])}</h1><div class="facts-row">{fact_html}</div></div>
<a class="btn pink" href="#book">Check availability</a></div>
<div class="prop-body"><div><div class="desc">{summary}</div><div class="amen">{secs}</div></div>
<aside class="book-box" id="book"><h3>Book direct</h3><p class="note">Pick your dates to see pricing and availability.</p>{book}
<div class="perks"><div>Best rate when you book with us directly</div><div>Message your hosts any time</div><div>Digital guidebook sent before check-in</div></div></aside></div>
</div>
<section class="block white"><div class="wrap"><div class="section-head"><h2>More homes you'll love</h2><a class="btn ghost sm" href="{p}homes/">All homes</a></div><div class="homes">{"".join(card(o, p) for o in others)}</div></div></section>
<div class="mobile-book"><div><b>{esc(h["name"])}</b><span class="muted">{" · ".join(facts(h)[:2])}</span></div><a class="btn pink sm" href="#book">Check dates</a></div>
<div class="lb" id="lb"><div class="bar"><span id="lbn"></span><button type="button" id="lbx">Close ✕</button></div>
<div class="stage"><button class="nav-l" type="button" id="lbp" aria-label="Previous">‹</button><img id="lbi" alt=""><button class="nav-r" type="button" id="lbnx" aria-label="Next">›</button></div><div class="cap" id="lbc"></div></div>
<script>(function(){{var D={data},i=0,lb=document.getElementById('lb'),im=document.getElementById('lbi'),cp=document.getElementById('lbc'),n=document.getElementById('lbn');
function show(k){{i=(k+D.length)%D.length;im.src=D[i][0];cp.textContent=D[i][1]||'';n.textContent=(i+1)+' / '+D.length;}}
document.querySelectorAll('.gallery button').forEach(function(b){{b.addEventListener('click',function(){{show(+b.dataset.i);lb.classList.add('open');document.body.style.overflow='hidden';}});}});
function close(){{lb.classList.remove('open');document.body.style.overflow='';}}
document.getElementById('lbx').onclick=close;document.getElementById('lbp').onclick=function(){{show(i-1)}};document.getElementById('lbnx').onclick=function(){{show(i+1)}};
document.addEventListener('keydown',function(e){{if(!lb.classList.contains('open'))return;if(e.key==='Escape')close();if(e.key==='ArrowLeft')show(i-1);if(e.key==='ArrowRight')show(i+1);}});
var x0=null;lb.addEventListener('touchstart',function(e){{x0=e.touches[0].clientX}});lb.addEventListener('touchend',function(e){{if(x0===null)return;var dx=e.changedTouches[0].clientX-x0;if(Math.abs(dx)>40)show(i+(dx<0?1:-1));x0=null;}});}})();</script>'''
    desc = re.sub(r'\s+', ' ', clean(h['summary']))[:155]
    write(f'{h["slug"]}/index.html', page(p, f'{h["name"]} | {h["city"]}, {h["st"]} | BK Stays', desc, body, body_cls='has-mb'))


def build_about():
    p = '../'
    A = PAGES['about']
    def mk(t):  # [bracketed] text is a draft placeholder Brandon still has to fill in
        return re.sub(r'\[([^\]]+)\]', r'<mark class="todo">\1</mark>', esc(t))
    def pic(f):
        if f.get('img'):
            return f'<img class="portrait" src="{p}img/{f["img"]}" alt="{esc(f.get("alt") or f["title"])}" loading="lazy">'
        return f'<div class="photo-todo"><span>{esc(f.get("photoNote", "Photo needed"))}</span></div>'
    favs = ''
    for k, f in enumerate(A['favorites']):
        favs += f'''<section class="block {"white" if k % 2 == 0 else ""}"><div class="wrap split {"flip" if k % 2 else ""}">{pic(f)}
<div><span class="eyebrow">{esc(f["eyebrow"])}</span><h2>{esc(f["title"])}</h2><p>{mk(f["text"])}</p><a class="btn" href="{p}{f["home"]}/">See {esc(f["homeName"])}</a></div></div></section>'''
    body = f'''<section class="about-hero"><div class="wrap"><div class="ah-text"><span class="eyebrow">About us</span><h1>{esc(A["heroTitle"])}</h1><p class="lead">{esc(A["heroLead"])}</p></div>
<div class="ah-photo"><img src="{p}img/{A["heroImg"]}" alt="Brandon, Katharina, Emmy and Leo"></div></div></section>
<section class="block white"><div class="wrap" style="max-width:820px"><span class="eyebrow">Our story</span><h2>{esc(A["title"])}</h2>{"".join(f"<p style='font-size:1.1rem'>{mk(x)}</p>" for x in A["story"])}</div></section>
{favs}
<section class="block"><div class="wrap"><div class="cta"><div><h2>Join us</h2><p>{esc(A["join"])}</p></div><a class="btn pink" href="{p}homes/">See our homes</a></div></div></section>'''
    write('about-us/index.html', page(p, 'About Us | BK Stays', A['story'][0], body))


def form_html(kind, p):
    if kind == 'pm':
        fields = '''<div class="row2"><label>Name<input name="name" required autocomplete="name"></label><label>Email<input type="email" name="email" required autocomplete="email"></label></div>
<label>Phone (optional)<input type="tel" name="phone" autocomplete="tel"></label>
<label>Link to your Airbnb or VRBO listing<input type="url" name="listing" required placeholder="https://"></label>
<label>Anything we should know? (optional)<textarea name="message"></textarea></label>'''
        subj = 'Free property analysis request'
    else:
        fields = '''<div class="row2"><label>Name<input name="name" required autocomplete="name"></label><label>Email<input type="email" name="email" required autocomplete="email"></label></div>
<label>Phone (optional)<input type="tel" name="phone" autocomplete="tel"></label>
<label>What can we help with?<select name="topic"><option>Booking a stay</option><option>Property Management</option><option>Investment Partnership</option><option>Something else</option></select></label>
<label>Message<textarea name="message" required></textarea></label>'''
        subj = 'Website message'
    return f'''<form class="form" data-subject="{subj}" onsubmit="return bkSend(this)">{fields}
<button class="btn pink" type="submit">Send</button><div class="ok">Thanks! Your email app should open with your message ready to send. If it doesn't, email us at {EMAIL}.</div></form>
<script>function bkSend(f){{var d=new FormData(f),b='';d.forEach(function(v,k){{if(v)b+=k.charAt(0).toUpperCase()+k.slice(1)+': '+v+'\\n';}});
location.href='mailto:{EMAIL}?subject='+encodeURIComponent(f.dataset.subject)+'&body='+encodeURIComponent(b);f.querySelector('.ok').style.display='block';return false;}}</script>'''


def build_pm():
    p = '../'
    M = PAGES['pm']
    stats = ''.join(f'<div class="stat"><b>{esc(a)}</b><span>{esc(b)}</span></div>' for a, b in M['stats'])
    svc = ''.join(f'<div class="feature"><h3>{esc(t)}</h3><p>{esc(d)}</p></div>' for t, d in M['services'])
    quotes = ''.join(f'<div class="quote"><div class="stars">★★★★★</div><p>“{esc(q)}”</p><cite>{esc(n)}</cite></div>' for q, n in M['quotes'])
    body = f'''<section class="page-hero"><div class="bg" style="background-image:url('{p}img/pm-hero.jpg')"></div><div class="wrap"><span class="eyebrow" style="color:#fff">Property management</span><h1>{esc(M["title"])}</h1><p class="lead">{esc(M["lead"])}</p><a class="btn pink" href="#analysis">Get a free property analysis</a></div></section>
<section class="block dark tight"><div class="wrap"><div class="stats">{stats}</div></div></section>
<section class="block"><div class="wrap"><div class="section-head"><div><span class="eyebrow">End to end</span><h2>What we do for owners</h2></div><p class="muted">{esc(M["whatLead"])}</p></div>
<ul class="checklist">{"".join(f"<li>{esc(x)}</li>" for x in M["what"])}</ul></div></section>
<section class="block white"><div class="wrap"><div class="section-head"><div><span class="eyebrow">Our services</span><h2>Why owners choose BK Stays</h2></div></div><div class="features">{svc}</div></div></section>
<section class="block"><div class="wrap"><div class="section-head"><div><span class="eyebrow">Owners say</span><h2>Make your property stand out</h2></div></div><div class="quotes">{quotes}</div></div></section>
<section class="block white" id="analysis"><div class="wrap split"><div><span class="eyebrow">Free property analysis</span><h2>Want your property analyzed for free?</h2><p>{esc(M["formLead"])}</p>
<p class="muted">Or call Brandon at <a href="tel:{PHONE_TEL}">{PHONE}</a>.</p></div>{form_html("pm", p)}</div></section>
<section class="block"><div class="wrap split flip"><img src="{p}img/pm-family.jpg" alt="Brandon and Katharina" loading="lazy"><div><span class="eyebrow">Meet your managers</span><h2>Meet Brandon and Katharina</h2>{"".join(f"<p>{esc(x)}</p>" for x in M["meet"])}</div></div></section>'''
    write('property-management/index.html', page(p, 'Vacation Rental Property Management | BK Stays', M['lead'], body))


def build_contact():
    p = '../'
    items = f'''<div class="contact-list">
<a class="contact-item" href="tel:{PHONE_TEL}"><span class="ic">{ICONS["phone"]}</span><span><b>{PHONE}</b><br><span class="muted">Call or text</span></span></a>
<a class="contact-item" href="mailto:{EMAIL}"><span class="ic">{ICONS["mail"]}</span><span><b>{EMAIL}</b><br><span class="muted">Email us any time</span></span></a>
<div class="contact-item"><span class="ic">{ICONS["pin"]}</span><span><b>Atlanta, Georgia</b><br><span class="muted">Homes in GA, FL, MI and MN</span></span></div></div>'''
    body = f'''<section class="block"><div class="wrap split" style="align-items:start"><div><span class="eyebrow">Contact</span><h1>Let's talk</h1>
<p class="muted">Questions about a stay, a booking, or having us manage your home? Reach out and we'll get right back to you.</p>{items}</div>{form_html("contact", p)}</div></section>'''
    write('contact/index.html', page(p, 'Contact | BK Stays', 'Contact BK Stays.', body))


def build_follow():
    p = '../'
    links = ''.join(f'<a class="contact-item" href="{u}" target="_blank" rel="noopener"><span class="ic">{ICONS[k]}</span><span><b>{k}</b><br><span class="muted">@bk_stays</span></span></a>' for k, u in SOCIAL.items())
    body = f'''<section class="block"><div class="wrap" style="max-width:640px"><span class="eyebrow">Follow us</span><h1>Follow along</h1><p class="muted">New homes, local tips and last-minute openings.</p><div class="contact-list">{links}</div></div></section>'''
    write('follow-us/index.html', page(p, 'Follow Us | BK Stays', 'Follow BK Stays on social media.', body))


def build_search():
    p = '../'
    body = f'''<section class="block"><div class="wrap"><span class="eyebrow">Available homes</span><h1>Your search</h1>
<hospitable-direct-mps identifier="{SEARCH_ID}" type="custom"></hospitable-direct-mps>
<script src="https://hospitable.b-cdn.net/direct-property-search-widget/hospitable-search-widget.prod.js"></script></div></section>'''
    write('search/index.html', page(p, 'Search | BK Stays', 'Available BK Stays homes.', body))


def add_guides():
    """Each home's guidebook at /<home>/guidebook/ (shares /assets, /img and /sw.js with the website)."""
    G = os.path.join(ROOT, 'site')
    fix = lambda t: re.sub(r'(?<![.\w])\.\./(img/|assets/|sw\.js)', r'../../\1', t).replace('<meta name="bk-base" content="../">', '<meta name="bk-base" content="../../">')
    for h in HOMES:
        src, dst = os.path.join(G, h['guide']), os.path.join(OUT, h['slug'], 'guidebook')
        os.makedirs(dst, exist_ok=True)
        for f in ['index.html', 'manifest.webmanifest']:
            open(os.path.join(dst, f), 'w').write(fix(open(os.path.join(src, f)).read()))
    for d in ['assets']:
        for root, _, files in os.walk(os.path.join(G, d)):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), G)
                os.makedirs(os.path.dirname(os.path.join(OUT, rel)), exist_ok=True)
                shutil.copy(os.path.join(root, f), os.path.join(OUT, rel))
    for f in os.listdir(os.path.join(G, 'img')):
        sp = os.path.join(G, 'img', f)
        if os.path.isfile(sp) and not os.path.exists(os.path.join(OUT, 'img', f)):
            shutil.copy(sp, os.path.join(OUT, 'img', f))
    shutil.copy(os.path.join(G, 'sw.js'), os.path.join(OUT, 'sw.js'))
    shutil.copy(os.path.join(G, '_headers'), os.path.join(OUT, '_headers'))


def build_redirects():
    lines = ['/home / 301', '/flortida /florida/ 301', '/new-dropdown /minnesota/ 301', '/services /property-management/ 301',
             '/social-media /follow-us/ 301', '/bkstays-properties /search/ 301', '/about-us /about-us/ 301',
             '/property-management /property-management/ 301', '/contact /contact/ 301', '/georgia /georgia/ 301', '/michigan /michigan/ 301']
    lines += [f'{h["old"]} /{h["slug"]}/ 301' for h in HOMES if h['old'] != '/' + h['slug']]
    lines += [f'{h["old"]}/guidebook /{h["slug"]}/guidebook/ 301' for h in HOMES if h['old'] != '/' + h['slug']]
    # old TouchStay guide links (guide.bkstays.com/guest/<id>/ is forwarded here by a Cloudflare rule)
    for h in HOMES:
        g = json.load(open(os.path.join(ROOT, 'content', 'guides', h['guide'] + '.json')))
        for old in g.get('oldLinks', []):
            lines.append(f'{old.rstrip("/")}/* /{h["slug"]}/guidebook/ 301')
            lines.append(f'{old.rstrip("/")} /{h["slug"]}/guidebook/ 301')
    open(os.path.join(OUT, '_redirects'), 'w').write('\n'.join(lines) + '\n')


VER = ''


def main():
    global VER, HOMES
    import time
    VER = time.strftime('%Y%m%d%H%M%S')
    if os.path.exists(OUT):
        keep_img = os.path.join(OUT, 'img')
        for f in os.listdir(OUT):
            if f != 'img':
                pth = os.path.join(OUT, f)
                shutil.rmtree(pth) if os.path.isdir(pth) else os.remove(pth)
    os.makedirs(OUT, exist_ok=True)
    HOMES = [load_home(h) for h in HOMES]
    # assets + images
    shutil.copy(os.path.join(W, 'site.css'), os.path.join(OUT, 'site.css'))
    os.makedirs(os.path.join(OUT, 'assets'), exist_ok=True)
    for f in ['logo-dark.png', 'logo-light.png', 'favicon.png', 'apple-touch-icon.png']:
        shutil.copy(os.path.join(ROOT, 'site', 'assets', f), os.path.join(OUT, 'assets', f))
    os.makedirs(os.path.join(OUT, 'img'), exist_ok=True)
    for f in os.listdir(os.path.join(SRC, 'sqimg')):
        shutil.copy(os.path.join(SRC, 'sqimg', f), os.path.join(OUT, 'img', f))
    for h in HOMES:
        d = os.path.join(OUT, 'img', h['slug'])
        os.makedirs(d, exist_ok=True)
        for i, _ in h['imgs']:
            for suf in ['', '-sm']:
                s = os.path.join(SRC, 'hosp', 'img', h['uuid'], f'{i:02d}{suf}.jpg')
                t = os.path.join(d, f'{i:02d}{suf}.jpg')
                if not os.path.exists(t):
                    shutil.copy(s, t)
    build_home(); build_homes_index(); build_states(); build_about(); build_pm(); build_contact(); build_follow(); build_search()
    for h in HOMES:
        build_property(h)
    add_guides()
    build_redirects()
    live = {h['slug'] for h in HOMES}
    for d in os.listdir(os.path.join(OUT, 'img')):
        if os.path.isdir(os.path.join(OUT, 'img', d)) and d not in live:
            shutil.rmtree(os.path.join(OUT, 'img', d))
    print('built website ->', OUT, len(HOMES), 'homes')


if __name__ == '__main__':
    main()
