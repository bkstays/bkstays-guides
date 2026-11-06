"""One-off import (Nov 6 2026): McStay in McCay (north-georgia library; new places go to libExtra). Do not rerun once edited."""
import json, os, re, sys, copy
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import import_new_two_helpers as Hh
A, imp = Hh.A, Hh.imp
tsid, slug = 'bHs1hBkHgRifU', 'mcstay-in-mccay'
d = Hh.prep(tsid)
house, recs = Hh.house_recs(d, set(imp.SECTION_MAP))
lib = json.load(open(os.path.join(ROOT, 'content/library/north-georgia.json')))['sections']
key = lambda t: re.sub(r'[^a-z0-9]', '', t.lower().replace('’', "'"))
have = {key(i['title']) for s in lib.values() for g in s['groups'] for i in g['items']}
catmap = {'Parks and Playgrounds': 'nature-parks', 'Waterfalls': 'waterfalls', 'Random Recommendations': 'random-recommendations'}
extra, notes = {}, []
for c in recs:
    sid = catmap.get(c['t']) or A.LIB_MAP[c['t']][0]
    for s in c['s']:
        for x in s['x']:
            if key(x['t']) in have:
                continue
            it = {'title': x['t'].strip(), 'html': A.clean(x['h'])}
            if x.get('p'): it['photo'] = x['p'].split('/')[-1]
            if x.get('l'): it['loc'] = x['l']; it['pin'] = x.get('m') or 'outdoors'
            it['_group'] = s['t']; it['_p'] = x.get('p')
            extra.setdefault(sid, []).append(it)
tmp = os.path.join(ROOT, 'src/ts', tsid + '.txt')
imp.SLUGS[tsid] = slug
open(tmp, 'w').write(json.dumps(json.dumps(house)))
try:
    g, photos = imp.convert(tsid, notes)
finally:
    os.remove(tmp)
CLG = json.load(open(os.path.join(ROOT, 'content/guides/cherry-log-summit.json')))
cur = {it['title']: it for s in CLG['sections'].values() for gr in s['groups'] for it in gr['items']}
for s in g['sections'].values():
    for gr in s['groups']:
        for it in gr['items']:
            if it['title'] == 'Early Check In': it.clear(); it.update(copy.deepcopy(cur['Early Check In (Half Day Stay Option)']))
            elif it['title'] == 'Late Check Out': it.clear(); it.update(copy.deepcopy(cur['Late Check Out (Half Day Stay Option)']))
            elif it['title'].startswith('Thank You - '): it['title'] = 'Thank You'
            elif it['title'] == 'Cancellation Policy': it['html'] = it['html'].replace('Gilmer County, Georgia', 'Fannin County, Georgia')
g['address'] = '284 Lees Ride, McCaysville, GA 30555'
g['cover'] = g['coverDesktop'] = g['background'] = 'mcstay-in-mccay-view.jpg'
for sid, items in extra.items():
    for it in items:
        if it.get('_p'): photos.add(it['_p'])
        it.pop('_group'); it.pop('_p')
if extra: g['libExtra'] = extra
json.dump(g, open(os.path.join(ROOT, 'content/guides', slug + '.json'), 'w'), ensure_ascii=False, indent=1)
json.dump(sorted(p for p in photos if p), open(os.path.join(ROOT, 'src/import_photos_mcstay.json'), 'w'), indent=0)
print('notes:', notes)
print('new places (libExtra):', {k: [i['title'] for i in v] for k, v in extra.items()})
