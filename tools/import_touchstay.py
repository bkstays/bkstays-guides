"""Convert a TouchStay house-content export (src/ts/<id>.txt) into content/guides/<slug>.json,
applying the BK Stays standards (see STANDARDS.md). Recommendations come from the shared library.

Usage: python3 tools/import_touchstay.py            (imports every file in src/ts/)
Writes a review report to src/import_report.md
"""
import json, os, re, glob, copy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CL = json.load(open(os.path.join(ROOT, 'content/guides/cherry-log-summit.json')))
RAW = json.load(open(os.path.join(ROOT, 'src/touchstay_raw.json')))

SLUGS = {
    'bvHtviNLNRDb5': 'best-of-blue-ridge', 'byOsTtxW1Dg4m': 'birdie-blue', 'bk8kMF7mOFwWS': 'grace-and-ember',
    'bAgPFUecWLYsd': 'mountain-clarity', 'brn6WHgKF0LX7': 'ripshin-heights', 'bp0rSeK1Uo1m9': 'sky-high-lodge',
    'bO2wNF1FjHXm6': 'tails-and-trails-hideaway',
}

# Cherry Log's current (already-cleaned) wording for items that are word-for-word the same in TouchStay
CL_ITEMS = {}
for s in CL['sections'].values():
    for g in s['groups']:
        for it in g['items']:
            CL_ITEMS.setdefault(it['title'], it)
CL_ITEMS['Confetti / Gllitter'] = CL_ITEMS['Confetti / Glitter']
RAW_ITEMS = {x['t']: x for c in RAW for s in c['s'] for x in s['x']}

# TouchStay category -> (section id, title, icon, Info group)
SECTION_MAP = {
    'Add This Guide To Your Phone': ('add-to-phone', 'Add This Guide To Your Phone', 'smartphone', 'stay'),
    'Welcome and About Us!': ('welcome', 'Welcome', 'cloud-sun', 'stay'),
    'Check In + Arrival': ('check-in-arrival', 'Check In + Arrival', 'key-round', 'stay'),
    'Check Out + Departure': ('check-out-departure', 'Check Out + Departure', 'hand', 'stay'),
    'Cancellation Policy': ('cancellation-policy', 'Cancellation Policy', 'circle-x', 'stay'),
    'Contact Us / Book Again': ('contact-us', 'Contact Us / Book Again', 'phone', 'stay'),
    'Rules and Regulations': ('rules', 'Rules and Regulations', 'book-open', 'stay'),
    'WiFi / Internet Details': ('wifi', 'WiFi / Internet Details', 'wifi', 'home'),
    'BBQ - Gas Grill': ('bbq-grill', 'BBQ Grill + Propane', 'flame', 'home'),
    'BBQ - Propane Tank(s)': ('bbq-grill', 'BBQ Grill + Propane', 'flame', 'home'),
    'Fireplace': ('fireplace-firepit', 'Fireplace', 'flame-kindling', 'home'),
    'Firepit / Firewood': ('fireplace-firepit', 'Fireplace + Firepit', 'flame-kindling', 'home'),
    'Hottub / Jacuzzi': ('hot-tub', 'Hot Tub / Jacuzzi', 'bath', 'home'),
    'Indoor Games + Fun': ('indoor-games-fun', 'Indoor Games + Fun', 'gamepad-2', 'home'),
    'Outdoor Games + Fun': ('outdoor-games-fun', 'Cornhole / Bags', 'target', 'home'),
    'Kitchen, Supplies + Appliances': ('kitchen', 'Kitchen, Supplies + Appliances', 'cooking-pot', 'home'),
    'Laundry': ('laundry', 'Laundry', 'washing-machine', 'home'),
    'Thermostat(s)': ('thermostat', 'Thermostat', 'thermometer', 'home'),
    "TV's + Streaming": ('tv-streaming', "TV's + Streaming", 'tv', 'home'),
    'Trash': ('trash', 'Trash', 'trash-2', 'home'),
    'Garbage Disposal': ('trash', 'Trash + Garbage Disposal', 'trash-2', 'home'),
    'Elevator / Accessibility': ('accessibility', 'Elevator / Accessibility', 'accessibility', 'home'),
    'Pool': ('pool', 'Pool', 'waves', 'home'),
    'Coosawateee River Resort': ('resort', 'Coosawattee River Resort', 'star', 'home'),
    'Playground': ('playground', 'Playground', 'castle', 'home'),
}
NO_PHOTO_SECTIONS = {'add-to-phone', 'check-out-departure', 'contact-us'}
YOUR_STAY = ['add-to-phone', 'welcome', 'check-in-arrival', 'check-out-departure', 'rules', 'cancellation-policy', 'bk:about-us', 'contact-us']
EXPLORE = CL['layout'][2]['sections']

CORNHOLE_BLURB = CL['sections']['outdoor-games-fun']['groups'][0]['items'][0]['html'].split('</p>')[0] + '</p>'

TEXT_FIXES = [
    ('Gllitter', 'Glitter'), ('Receptable', 'Receptacle'), ('Shlage', 'Schlage'), ('before before', 'before'),
    ('<a href="tel:30-60-120">30-60-120</a>', '30-60-120'), ('Welcome to Grace and Ember !', 'Welcome to Grace and Ember!'),
    ('Welcome to the Mountain Clarity!', 'Welcome to Mountain Clarity!'),
    ('Trash is collected every Monday morning (varies on holidays).', 'Trash is collected after each guest checks out.'),
    ('Trash is collected after each checkout.', 'Trash is collected after each guest checks out.'),
    ('<ul type="disc">', '<ul>'), ('<ul type="circle">', '<ul>'),
]


def fmt_phone(p):
    d = re.sub(r'\D', '', p or '')
    return f'{d[:3]}-{d[3:6]}-{d[6:]}' if len(d) == 10 else p


def loom_embed(url):
    m = re.search(r'loom\.com/(?:share|embed)/([0-9a-f]{20,})', url)
    return f'https://www.loom.com/embed/{m.group(1)}' if m else None


def photo_name(p):
    return p.split('/')[-1] if p else None


def convert(tsid, notes):
    d = json.loads(json.loads(open(os.path.join(ROOT, 'src/ts', tsid + '.txt')).read()))
    meta = d['meta']
    name = meta['name']
    sections, order, photos = {}, {'stay': [], 'home': []}, set()

    def item_from(x, sid):
        if x.get('same'):
            base = CL_ITEMS.get(x['t'])
            if base is None:
                rx = RAW_ITEMS[x['t']]
                base = {'title': rx['t'], 'html': rx.get('h', '')}
            it = {'title': base['title'], 'html': base['html']}
            if base.get('video'):
                it['video'] = base['video']
        else:
            it = {'title': x['t'], 'html': x.get('h', '')}
        for a, b in TEXT_FIXES:
            it['html'] = it['html'].replace(a, b)
            it['title'] = it['title'].replace(a, b)
        # inline <iframe> (Loom) -> video below the text
        m = re.search(r'<p>\s*<iframe[^>]*src="([^"]+)"[^>]*></iframe>\s*</p>', it['html'])
        if m:
            it['video'] = loom_embed(m.group(1)) or m.group(1)
            it['html'] = it['html'].replace(m.group(0), '')
        # a single Loom link in the text -> also embed it as the video
        looms = re.findall(r'href="(https://www\.loom\.com/share/[^"]+)"', it['html'])
        if len(looms) == 1 and not it.get('video'):
            it['video'] = loom_embed(looms[0])
        if '<img' in it['html']:
            it['html'] = re.sub(r'<br><br><img[^>]*></div><div> </div><div><img[^>]*></div>', '</div>', it['html'])
            it['html'] = re.sub(r'<img[^>]*>', '', it['html'])
            notes.append(f'**{it["title"]}**: TouchStay had two oven-setting pictures inside the text that could not be copied. Send them if you want them back.')
        p = photo_name(x.get('p'))
        if p:
            hide = sid in NO_PHOTO_SECTIONS or (sid == 'rules' and it['title'] == 'Jacuzzi')
            it['photoHidden' if hide else 'photo'] = p
            photos.add(x['p'])
        if x.get('l'):
            it['loc'] = x['l']
        if x.get('m'):
            it['pin'] = x['m']
        return it

    for c in d['cats']:
        if c['t'] not in SECTION_MAP:
            notes.append(f'Unmapped TouchStay tile "{c["t"]}" was skipped.')
            continue
        sid, title, icon, grp = SECTION_MAP[c['t']]
        sec = sections.get(sid)
        if not sec:
            sec = sections[sid] = {'id': sid, 'title': title, 'icon': icon, 'groups': []}
            order[grp].append(sid)
        elif title != sec['title'] and title.endswith(('+ Firepit', '+ Garbage Disposal')):
            sec['title'] = title
        for s in c['s']:
            items = []
            for x in s['x']:
                if sid == 'welcome' and x['t'] == 'About Your Hosts':
                    continue  # replaced by the shared About Us tile
                items.append(item_from(x, sid))
            gt = s['t'] if (len(c['s']) > 1 or sid == 'resort') else ''
            if sec['groups'] and not gt and not sec['groups'][-1]['title']:
                sec['groups'][-1]['items'] += items
            else:
                sec['groups'].append({'title': gt, 'items': items})

    # --- property-specific fixes ---
    fp = sections.get('fireplace-firepit')
    if fp and any('Outdoor' in i['title'] for g in fp['groups'] for i in g['items']):
        fp['title'] = 'Fireplace + Firepit'
    if 'outdoor-games-fun' in sections:
        for g in sections['outdoor-games-fun']['groups']:
            for it in g['items']:
                if it['title'] == 'Cornhole Boards':
                    it['title'] = 'Cornhole / Bags'
                    it['html'] = CORNHOLE_BLURB + it['html']
    w = sections['welcome']['groups'][0]['items'][0]
    w['html'] = w['html'].replace('<strong>Welcome to the _________________!</strong>', f'<strong>Welcome to {name}!</strong>')
    if not w['title'].endswith('!'):
        w['title'] += '!'
    for g in sections.get('hot-tub', {'groups': []})['groups']:
        for it in g['items']:
            if not it['html'].strip():
                it['html'] = CL_ITEMS['Hot Tub / Jacuzzi']['html']
                notes.append('**Hot Tub / Jacuzzi** was blank in TouchStay, so I used the standard hot tub instructions. Check that they fit this tub.')
    if 'pool' in sections and 'resort' in sections:
        pool = sections['pool']
        resort_titles = {i['title'] for g in sections['resort']['groups'] for i in g['items']}
        before = sum(len(g['items']) for g in pool['groups'])
        for g in pool['groups']:
            g['items'] = [i for i in g['items'] if i['title'] not in resort_titles]
        if before != sum(len(g['items']) for g in pool['groups']):
            notes.append('**Pool**: removed the three resort pools listed twice (they stay under Coosawattee River Resort). Pool now holds the pool waiver.')
    allhtml = json.dumps(sections)
    if 'Monday and Thursday' in allhtml:
        notes.append('**Trash** says pickup is "every Monday and Thursday morning". Since this home is in the resort I left it. Change it to "after each guest checks out" if that is how it works.')
    if '1552' in allhtml:
        notes.append('The door code is visible in **Access Codes / Instructions** (same as TouchStay).')

    lib_extra = {}
    for e in d.get('extra', []):
        it = {'title': e['t'], 'html': e['h']}
        if e.get('p'):
            it['photo'] = photo_name(e['p']); photos.add(e['p'])
        if e.get('l'):
            it['loc'] = e['l']
        if e.get('m'):
            it['pin'] = e['m']
        key = {'Grocery and Pharmacy': 'grocery', 'Weather': 'weather'}[e['cat']]
        if key == 'weather':
            it['title'] = 'Ellijay'
        lib_extra.setdefault(key, []).append(it)
        notes.append(f'Added **{it["title"]}** to this guide\'s {key.title()} tile only (it is specific to this home).')

    phone = fmt_phone(next((c['value'] for c in meta['contacts'] if c['type'] == 'phone'), '404-358-1552'))
    addr = ', '.join(p.strip() for p in meta['addr'].split(','))
    addr = re.sub(r',\s*(GA|Georgia),\s*(\d{5})$', r', GA \2', addr)
    addr = re.sub(r'\b([a-z])', lambda m: m.group(1).upper(), addr) if addr.islower() or 'kismet' in addr else addr
    cover, desk = photo_name(meta['mob']), photo_name(meta['desk'])
    photos.update([meta['mob'], meta['desk']])
    home_order = [s for s in order['home']]
    guide = {
        'slug': SLUGS[tsid], 'name': name, 'shortName': name, 'welcome': 'Welcome!',
        'hostedBy': 'Hosted By Brandon & Katharina', 'address': addr,
        'location': [round(meta['loc'][0], 6), round(meta['loc'][1], 6)],
        'cover': cover, 'coverDesktop': desk, 'background': desk,
        'contact': {'phone': phone, 'sms': phone, 'email': ''}, 'gate': True,
        'library': 'north-georgia', 'oldLinks': [f'/guest/{tsid}/'],
        'layout': [
            {'heading': 'Your Stay', 'sections': [s for s in YOUR_STAY if s.startswith('bk:') or s in sections]},
            {'heading': 'The Home', 'sort': 'az', 'sections': home_order},
            {'heading': 'Explore the Area', 'sort': 'az', 'sortInside': True, 'sections': EXPLORE},
        ],
        'sections': sections,
    }
    if lib_extra:
        guide['libExtra'] = lib_extra
    missing = [s for s in YOUR_STAY if not s.startswith('bk:') and s not in sections]
    if missing:
        notes.append(f'Missing standard tiles: {missing}')
    return guide, photos


def main():
    report = ['# Import report: items to proofread\n']
    allphotos = set()
    for f in sorted(glob.glob(os.path.join(ROOT, 'src/ts/*.txt'))):
        tsid = os.path.basename(f)[:-4]
        notes = []
        g, ph = convert(tsid, notes)
        allphotos |= ph
        json.dump(g, open(os.path.join(ROOT, 'content/guides', g['slug'] + '.json'), 'w'), ensure_ascii=False, indent=1)
        report.append(f"\n## {g['name']}  (/{g['slug']}/)")
        report += [f'- {n}' for n in dict.fromkeys(notes)]
    open(os.path.join(ROOT, 'src/import_report.md'), 'w').write('\n'.join(report) + '\n')
    json.dump(sorted(allphotos), open(os.path.join(ROOT, 'src/import_photos.json'), 'w'), indent=0)
    print('\n'.join(report)); print(len(allphotos), 'photos referenced')


if __name__ == '__main__':
    main()
