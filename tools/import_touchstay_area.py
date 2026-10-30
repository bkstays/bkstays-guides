"""Import TouchStay guides from a NEW area (not North Georgia).

Input (exported in the browser, see STANDARDS.md):
  src/ts2/<tsid>.json          house content (items identical to Cherry Log's TouchStay text are {"same":1})
  src/ts2/recs-<area>.json     that area's recommendations (deduped across homes in the area)
Output:
  content/library/<area>.json  shared area recommendations
  content/guides/<slug>.json   one per home (only the homes listed in HOMES; never touches other guides)
  src/import_report_<area>.md  proofreading notes
  src/import_photos_area.json  photo paths to download from hub.touchstay.com/media/cache/

Usage: python3 tools/import_touchstay_area.py
"""
import json, os, re, sys, copy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import import_touchstay as imp  # reuses the North Georgia importer's rules

HOMES = {
    # tsid: (slug, area, county text, view photo)
    'bjvNNoADYXaMF': ('bellaire-extraordinaire', 'northern-michigan', 'Antrim County, Michigan', 'bellaire-extraordinaire-view.jpg'),
    'bESkNh4rO48o7': ('das-himmel-haus', 'northern-michigan', 'Antrim County, Michigan', 'das-himmel-haus-view.jpg'),
    'bMSKv5OUNYgyb': ('iron-range-retreat', 'iron-range', 'St. Louis County, Minnesota', 'iron-range-retreat-view.jpg'),
    'b0J1X8XcmzfuW': ('havana-haven', 'south-florida', 'Broward County, Florida', 'havana-haven-view.jpg'),
}
ADDR = {  # from Hospitable (TouchStay's were incomplete / lower case)
    'bellaire-extraordinaire': '4872 Valley View Road, Bellaire, MI 49615',
    'das-himmel-haus': '6004 Heideldorf Lane, Bellaire, MI 49615',
    'iron-range-retreat': '5935 Voyageurs Trail, Biwabik, MN 55708',
    'havana-haven': '3627 Northeast 19th Avenue, Fort Lauderdale, FL 33308',
}
NAME = {'havana-haven': 'Havana Haven'}
AREAS = {
    'northern-michigan': ('Northern Michigan (Bellaire / Shanty Creek / Schuss)', 'recs-northern-michigan.json'),
    'iron-range': ("Minnesota's Iron Range (Biwabik / Giants Ridge)", 'recs-iron-range.json'),
    'south-florida': ('South Florida (Fort Lauderdale)', 'recs-havana.json'),
}
# TouchStay recommendation tile -> (library section id, title, icon, group to merge into)
LIB_MAP = {
    'Beer and Wine': ('beer-wine', 'Beer and Wine', 'wine'),
    'Dining Out Recommendations': ('dining', 'Dining Out', 'utensils'),
    'Emergency and Urgent Care': ('emergency', 'Emergency and Urgent Care', 'siren'),
    'Fishing': ('fishing', 'Fishing', 'fish'),
    'Golf': ('golf', 'Golf', 'flag'),
    'Grocery and Pharmacy': ('grocery', 'Grocery and Pharmacy', 'shopping-cart'),
    'Hiking and Biking': ('hiking-biking', 'Hiking and Biking', 'mountain'),
    'Nature + Parks': ('nature-parks', 'Nature + Parks', 'trees'),
    'Parks and Playgrounds': ('nature-parks', 'Nature + Parks', 'trees'),
    'Shopping': ('shopping', 'Shopping', 'shopping-bag'),
    'Spas + Salons': ('spas-salons', 'Spas + Salons', 'sparkles'),
    'Take A Tour': ('tours', 'Take A Tour', 'train-front'),
    'Water Activities': ('water-activities', 'Water Activities', 'sailboat'),
    'Weather': ('weather', 'Weather', 'cloud-sun-rain'),
    'Schuss Mountain': ('schuss-mountain', 'Schuss Mountain', 'mountain-snow'),
    'Shanty Creek Resort': ('shanty-creek', 'Shanty Creek Resort', 'star'),
    'Short’s Brewing Company Bellaire Pub': ('shorts-brewing', "Short's Brewing Company", 'beer'),
    'Giants Ridge Recreation Area': ('giants-ridge', 'Giants Ridge Recreation Area', 'mountain-snow'),
}
imp.SECTION_MAP.update({
    'Barrel Sauna': ('sauna', 'Barrel Sauna', 'heater', 'home'),
    'Voyageurs Retreat (The HOA - Neighborhood)': ('voyageurs-retreat', 'Voyageurs Retreat (HOA)', 'trees', 'home'),
})
imp.TEXT_FIXES += [('Barrell Sauna', 'Barrel Sauna')]

# Pictures that sat inside the TouchStay text (hub.touchstay.com/v3api/photo/<id> -> media/cache path)
SAUNA = ['0f/4f/0f4fb600698b3e46cd8da801e9f424c9.jpg', '9f/a1/9fa13818dfec6364b2badf43ae34e16b.jpg']
INLINE = {
    ('bellaire-extraordinaire', 'sauna', 'Barrel Sauna'): SAUNA,
    ('das-himmel-haus', 'sauna', 'Barrel Sauna'): SAUNA[::-1],
    ('bellaire-extraordinaire', 'fireplace-firepit', 'Fireplace'): ['aa/ff/aafff90909c933a811b916b52f867aeb.jpg'],
    ('iron-range-retreat', 'trash', 'Trash'): ['d6/05/d605103901fba299481901b9dffa7470.jpg'],
    ('iron-range-retreat', 'voyageurs-retreat', 'Sabin Lake Map'): ['d3/25/d325e75679c05552440a615d8c0fa490.jpg'],
    ('iron-range-retreat', 'voyageurs-retreat', 'Wynne Lake Map'): ['ee/37/ee37673bf93576f8e23c475de2c41806.jpg'],
}
LIB_INLINE = {'Giants Ridge Ridge Mountain Bike Trail Map': 'ac/08/ac08d03f0d37ab546f2a8e4e303f859d.jpg'}
LINKS = {'369271': 'bbq-grill', '428024': 'trash'}  # TouchStay category id -> our section

JUNK = [
    (r'[?&]utm_source=chatgpt\.com', ''),
    (r'\s*\(?\b[\w.-]+\.(?:com|org|net|gov)\+\d+\)?', ''),  # "tripadvisor.com+10" citation chips
]


def clean(h):
    for a, b in JUNK:
        h = re.sub(a, b, h)
    return h.replace('<p></p>', '').strip()


def photo(p):
    return p.split('/')[-1] if p else None


def build_library(area, photos):
    name, fn = AREAS[area]
    recs = json.load(open(os.path.join(ROOT, 'src/ts2', fn)))
    secs = {}
    for cat, c in recs.items():
        sid, title, icon = LIB_MAP[cat]
        sec = secs.setdefault(sid, {'id': sid, 'title': title, 'icon': icon, 'groups': []})
        subs = list(c['s'].items())
        for st, xs in subs:
            gt = st if (len(subs) > 1 or cat == 'Parks and Playgrounds') else ''
            if cat == 'Parks and Playgrounds':
                gt = 'Parks and Playgrounds'
            items = []
            for x in xs:
                it = {'title': x['t'].strip(), 'html': clean(x['h'])}
                if '<img>' in it['html']:
                    p = LIB_INLINE.get(it['title'])
                    it['html'] = it['html'].replace('<img>', f'</p><p><img src="../img/{photo(p)}" alt="">' if p else '')
                    if p:
                        photos.add(p)
                if x.get('p'):
                    it['photo'] = photo(x['p']); photos.add(x['p'])
                if x.get('l'):
                    it['loc'] = x['l']; it['pin'] = x.get('m') or 'outdoors'
                items.append(it)
            grp = next((g for g in sec['groups'] if g['title'] == gt), None)
            if grp:
                grp['items'] += [i for i in items if i['title'] not in {j['title'] for j in grp['items']}]
            else:
                sec['groups'].append({'title': gt, 'items': items})
    lib = {'id': area, 'name': name, 'sections': secs}
    json.dump(lib, open(os.path.join(ROOT, 'content/library', area + '.json'), 'w'), ensure_ascii=False, indent=1)
    return lib


def main():
    CLG = json.load(open(os.path.join(ROOT, 'content/guides/cherry-log-summit.json')))
    cur = {it['title']: it for s in CLG['sections'].values() for g in s['groups'] for it in g['items']}
    early, late = cur['Early Check In (Half Day Stay Option)'], cur['Late Check Out (Half Day Stay Option)']
    # Cherry Log items whose cleaned text is Cherry Log specific: use the home's own TouchStay text instead
    for t in ['Welcome to Cherry Log Summit!', 'Driving Directions', 'WIFI / Internet Details', 'Game Room Fun!', 'Trash']:
        imp.CL_ITEMS.pop(t, None)
    photos, libs, report = set(), {}, ['# Import report: new-area guides\n']
    for tsid, (slug, area, county, view) in HOMES.items():
        imp.SLUGS[tsid] = slug
        if area not in libs:
            libs[area] = build_library(area, photos)
        house = json.load(open(os.path.join(ROOT, 'src/ts2', tsid + '.json')))
        tmp = os.path.join(ROOT, 'src/ts', tsid + '.txt')
        open(tmp, 'w').write(json.dumps(json.dumps(house)))
        notes = []
        try:
            g, ph = imp.convert(tsid, notes)
        finally:
            os.remove(tmp)  # keep src/ts for the North Georgia importer only
        photos |= {p for p in ph if p}
        secs = g['sections']
        g['name'] = g['shortName'] = NAME.get(slug, g['name'])
        g['address'] = ADDR[slug]
        g['cover'] = g['coverDesktop'] = g['background'] = view
        g['library'] = area
        lib = libs[area]['sections']
        g['layout'][2]['sections'] = ['lib:' + k for k in lib]
        for s in secs.values():
            for grp in s['groups']:
                seen, keep = set(), []
                for it in grp['items']:
                    key = (it['title'], it['html'])
                    if key in seen:
                        notes.append(f'**{it["title"]}** was listed twice in TouchStay; kept one.')
                        continue
                    seen.add(key)
                    if it['title'] == 'Early Check In':
                        it.clear(); it.update(copy.deepcopy(early))
                    elif it['title'] == 'Late Check Out':
                        it.clear(); it.update(copy.deepcopy(late))
                    elif it['title'].startswith('Thank You - '):
                        it['title'] = 'Thank You'
                    elif it['title'] == 'Cards, Games + More' and not it.get('photo'):
                        it['photo'] = 'generic-chess-board.jpg'
                    elif it['title'] == 'Cancellation Policy':
                        it['html'] = it['html'].replace('Gilmer County, Georgia', county)
                    elif it['title'].startswith('Pet Policy') and 'nonshedding' in it['title']:
                        notes.append(f'**{it["title"]}**: still the old TouchStay wording (non-shedding only, TouchStay fee). Tell me the fee and whether to use the standard "Max 2 Dogs (with approval)" wording.')
                    elif it['title'].startswith('Pet Policy') and '$115' in it['html']:
                        notes.append(f'**{it["title"]}** uses the standard wording with a **$115** pet fee. Confirm the fee for this home.')
                    keep.append(it)
                grp['items'] = keep
        notes = [n for n in notes if 'oven-setting' not in n]
        for sec in secs.values():
            for grp in sec['groups']:
                for it in grp['items']:
                    for a, b in LINKS.items():
                        it['html'] = it['html'].replace(f'href="?categoryId={a}"', f'href="#/info/{b}"')
                    imgs = INLINE.get((slug, sec['id'], it['title']))
                    if imgs:
                        it['html'] = it['html'].replace('<p></p>', '').strip() + ''.join(
                            f'<p><img src="../img/{photo(p)}" alt=""></p>' for p in imgs)
                        photos.update(imgs)
        if 'trash' in secs:
            notes.append('**Trash**: check how pickup works at this home (the standard says "after each guest checks out").')
        g['libExtra'] = {}
        g.pop('libExtra')
        json.dump(g, open(os.path.join(ROOT, 'content/guides', slug + '.json'), 'w'), ensure_ascii=False, indent=1)
        report.append(f"\n## {g['name']}  (/{slug}/)  library: {area}")
        report += [f'- {n}' for n in dict.fromkeys(notes)]
    open(os.path.join(ROOT, 'src/import_report_area.md'), 'w').write('\n'.join(report) + '\n')
    json.dump(sorted(photos), open(os.path.join(ROOT, 'src/import_photos_area.json'), 'w'), indent=0)
    print('\n'.join(report)); print(len(photos), 'photos referenced')


if __name__ == '__main__':
    main()
