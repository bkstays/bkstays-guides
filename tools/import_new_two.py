"""One-off import (Nov 6 2026): Tidewater 2601 (new area panama-city-beach) and McStay in McCay (north-georgia).
Never touches other guides or the north-georgia library. Do not rerun once the guides are edited."""
import json, os, re, sys, copy, html as H
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import import_touchstay_area as A
imp = A.imp

COVERS = {'bUWuQjDRWBDP4': ('54/c4/54c4867d59e3e2b55116b691bdf4146f.jpg', 'ef/b0/efb0f6c397014e091a7ca56c5ac1573a.jpg'),
          'bHs1hBkHgRifU': ('fc/dd/fcdd387de1b35929acf0abfaf57e47a0.jpg', '95/0e/950eee0394266afe6aa9f487aeae77de.jpg')}

def norm(h):
    h = re.sub(r'\s+target="_blank"', '', h or '')
    h = h.replace('<br/>', '<br>').replace('\xa0', ' ').replace('&nbsp;', ' ')
    return re.sub(r'\s+', ' ', h).strip()

RAWN = {x['t'].strip(): norm(x.get('h', '')) for c in imp.RAW for s in c['s'] for x in s['x']}

def prep(tsid):
    d = json.load(open(os.path.join(ROOT, 'src/ts2', tsid + '.raw.json')))
    desk, mob = COVERS[tsid]
    d['meta'].update({'mob': mob, 'desk': desk, 'contacts': [{'type': 'phone', 'value': '4043581552'}]})
    for c in d['cats']:
        for s in c['s']:
            for x in s['x']:
                if RAWN.get(x['t'].strip()) == norm(x['h']) and x['h'].strip():
                    x['same'] = 1
    return d

def house_recs(d, house_cats):
    house = {'meta': d['meta'], 'cats': [c for c in d['cats'] if c['t'] in house_cats]}
    recs = [c for c in d['cats'] if c['t'] not in house_cats]
    return house, recs

# ---------- Tidewater ----------
imp.SECTION_MAP.update({
    'Beach Service': ('beach-service', 'Beach Chairs + Umbrellas', 'umbrella', 'home'),
    'Tidewater TV & WiFi': ('tidewater-tv', 'Tidewater TV + WiFi', 'tv', 'home'),
})
A.LIB_MAP.update({'Pier Park': ('pier-park', 'Pier Park', 'star'),
                  'Random Recommendations': ('random-recommendations', 'Things To Do', 'map-pin')})
A.AREAS['panama-city-beach'] = ('Panama City Beach, Florida', 'recs-panama-city-beach.json')
A.NAME['tidewater-2601'] = 'Tidewater 2601'
A.ADDR['tidewater-2601'] = '16819 Front Beach Road, Unit 2601, Panama City Beach, FL 32413'

tw = prep('bUWuQjDRWBDP4')
house, recs = house_recs(tw, set(imp.SECTION_MAP))
json.dump(house, open(os.path.join(ROOT, 'src/ts2/bUWuQjDRWBDP4.json'), 'w'), ensure_ascii=False, indent=1)
rj = {c['t']: {'i': c['i'], 's': {s['t']: s['x'] for s in c['s']}} for c in recs}
json.dump(rj, open(os.path.join(ROOT, 'src/ts2/recs-panama-city-beach.json'), 'w'), ensure_ascii=False, indent=1)
print('Tidewater rec tiles:', list(rj))

A.HOMES.clear()
A.HOMES['bUWuQjDRWBDP4'] = ('tidewater-2601', 'panama-city-beach', 'Bay County, Florida', 'tidewater-2601-view.jpg')
pet_before = A.PET_HTML
A.main()
os.rename(os.path.join(ROOT, 'src/import_report_area.md'), os.path.join(ROOT, 'src/import_report_tidewater.md'))
os.rename(os.path.join(ROOT, 'src/import_photos_area.json'), os.path.join(ROOT, 'src/import_photos_tidewater.json'))
