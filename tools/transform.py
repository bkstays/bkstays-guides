"""One-time import: TouchStay export -> property guide file + shared area library.
Applies the content cleanups (duplicates, pasted formatting junk, typos)."""
import json, re, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raw = json.load(open(os.path.join(ROOT, 'src/touchstay_raw.json')))
by = {c['t']: c for c in raw}


def slug(s):
    s = s.lower().replace('&', ' ').replace('+', ' ')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def item(x):
    o = {'title': x['t'], 'html': x.get('h', '')}
    if x.get('p'):
        o['photo'] = x['p'].split('/')[-1]
    if x.get('v'):
        o['video'] = x['v']
    if x.get('l'):
        o['loc'] = x['l']
    if x.get('m'):
        o['pin'] = x['m']
    return o


def groups(cat_title, drop=()):
    c = by[cat_title]
    out = []
    for s in c['s']:
        items = [item(x) for x in s['x'] if x['t'] not in drop]
        out.append({'title': s['t'], 'items': items})
    return out


def section(title, icon, groups_, sid=None):
    # one group whose title equals the section title -> untitled group
    for g in groups_:
        if g['title'] == title or len(groups_) == 1:
            g['title'] = ''
    return {'id': sid or slug(title), 'title': title, 'icon': icon, 'groups': groups_}


def strip_anchors(h, pred=lambda text, href: True):
    def rep(m):
        href, text = m.group(1) or '', m.group(2)
        return '' if pred(text, href) else m.group(0)
    return re.sub(r'<a(?: href="([^"]*)")?>(.*?)</a>', rep, h)


# ---------------- cleanups on raw items ----------------
def fix(cat, title, fn, sub=None):
    for s in by[cat]['s']:
        if sub and s['t'] != sub:
            continue
        for x in s['x']:
            if x['t'] == title:
                x['h'] = fn(x['h'])

# Welcome: duplicate "About Your Hosts" (keep the newer 6-year-old version)
w = by['Welcome and About Us!']['s'][0]['x']
w[:] = [x for i, x in enumerate(w) if not (x['t'] == 'About Your Hosts' and '5-year-old' in x['h'])]

# Early check-in internal link
fix('Check In + Arrival', '4:00 PM Check-in', lambda h: h.replace('href="992280#2193843"', 'href="#/info/check-in-arrival/early-check-in"'))
fix('Check Out + Departure', '10:00 AM Check-out', lambda h: h.replace('Please visit our Late Check Out Section', 'Please visit our <a href="#/info/check-out-departure/late-check-out">Late Check Out</a> section'))

# Fireplace: Loom share link -> embedded video
for x in by['Fireplace']['s'][0]['x']:
    x['h'] = x['h'].replace('<p>https://www.loom.com/share/78806b673d7a43a88a5db4781d146884</p>', '')
    x['h'] = x['h'].replace('<a href="tel:30-60-120">30-60-120</a>', '30-60-120')
    x['v'] = 'https://www.loom.com/embed/78806b673d7a43a88a5db4781d146884'

# ChatGPT citation chips / junk
fix('Beer and Wine', 'Cartecay River Brewing Co.', lambda h: re.sub(r'<p><a href="[^"]*">(Ellijay River House|Explore Georgia)</a></p>', '', h).replace(' | <a>cartecayriverbrewing.com</a>', ''))
fix('Beer and Wine', 'Out of the Blue Bottle Shop', lambda h: h[h.index('<p>'):])
fix('Dining Out Recommendations', 'Tapas and Tequila', lambda h: h[h.index('<p>'):])
for t in ['Ellijay Fire Station', 'Piedmont Mountainside Emergency Services', 'Ellijay Police Department']:
    fix('Emergency and Urgent Care', t, lambda h: re.sub(r'\s*\(\s*,?\s*\)', '', strip_anchors(h)).replace(' — via ellijay-ga.gov', ''))
fix('Emergency and Urgent Care', 'Ellijay Police Department',
    lambda h: h.replace('<p>Website: City of Ellijay official police page</p>', '<p>Website: <a href="https://ellijay-ga.gov/departments/police/">ellijay-ga.gov</a></p>'))
for t in ['Cohutta Overlook', 'Fort Mountain State Park']:
    fix('Nature + Parks', t, lambda h: strip_anchors(h, lambda text, href: '+' in text))
fix('Rules and Regulations', 'Damages', lambda h: h.replace('<p>o for any damages caused or extra cleaning measures needed beyond "normal post-stay conditions".</p>', ''))
for s in by['Rules and Regulations']['s']:
    for x in s['x']:
        if x['t'] == 'Confetti / Gllitter':
            x['t'] = 'Confetti / Glitter'
by['Shopping']['s'][0]['t'] = 'Local Shops'
# Cartecay River Experience listed twice inside Water Activities
wa = by['Water Activities']['s']
wa[1]['x'] = [x for x in wa[1]['x'] if x['t'] != 'Cartecay River Experience']

# ---------------- property guide ----------------
P = lambda t: groups(t)
house = [
    section('Add This Guide To Your Phone', 'smartphone', P('Add This Guide To Your Phone'), 'add-to-phone'),
    section('Welcome and About Us!', 'cloud-sun', P('Welcome and About Us!'), 'welcome'),
    section('Check In + Arrival', 'key-round', P('Check In + Arrival')),
    section('Check Out + Departure', 'hand', P('Check Out + Departure')),
    section('WiFi / Internet Details', 'wifi', P('WiFi / Internet Details'), 'wifi'),
    section('Contact Us / Book Again', 'phone', P('Contact Us / Book Again'), 'contact-us'),
    section('Cancellation Policy', 'circle-x', P('Cancellation Policy')),
    section('BBQ Grill + Propane', 'flame', [{'title': '', 'items': P('BBQ - Gas Grill')[0]['items'] + P('BBQ - Propane Tank(s)')[0]['items']}], 'bbq-grill'),
    section('Fireplace + Firepit', 'flame-kindling', [{'title': '', 'items': P('Fireplace')[0]['items'] + P('Firepit / Firewood')[0]['items']}], 'fireplace-firepit'),
    section('Hot Tub / Jacuzzi', 'bath', P('Hottub / Jacuzzi'), 'hot-tub'),
    section('Indoor Games + Fun', 'gamepad-2', P('Indoor Games + Fun')),
    section('Outdoor Games + Fun', 'target', P('Outdoor Games + Fun')),
    section('Playground', 'castle', P('Playground')),
    section('Kitchen, Supplies + Appliances', 'cooking-pot', P('Kitchen, Supplies + Appliances'), 'kitchen'),
    section('Laundry', 'washing-machine', P('Laundry')),
    section('Thermostat', 'thermometer', P('Thermostat(s)')),
    section("TV's + Streaming", 'tv', P("TV's + Streaming"), 'tv-streaming'),
    section('Trash + Garbage Disposal', 'trash-2', [{'title': '', 'items': P('Trash')[0]['items'] + P('Garbage Disposal')[0]['items']}], 'trash'),
    section('Rules and Regulations', 'book-open', P('Rules and Regulations'), 'rules'),
]

# ---------------- shared library (North Georgia: Blue Ridge / Ellijay) ----------------
lib_sections = [
    section('Dining Out', 'utensils', P('Dining Out Recommendations'), 'dining'),
    section('Beer and Wine', 'wine', P('Beer and Wine'), 'beer-wine'),
    section('Grocery and Pharmacy', 'shopping-cart', P('Grocery and Pharmacy'), 'grocery'),
    section('Hiking and Biking', 'mountain', P('Hiking and Biking'), 'hiking-biking'),
    section('Waterfalls', 'droplets', P('Waterfalls')),
    section('Nature + Parks', 'trees', P('Nature + Parks') + [{'title': 'Parks and Playgrounds', 'items': P('Parks and Playgrounds')[0]['items']}], 'nature-parks'),
    section('Water Activities', 'sailboat', P('Water Activities')),
    section('Take A Tour', 'train-front', P('Take A Tour'), 'tours'),
    section('Random Recommendations', 'map-pin', P('Random Recommendations'), 'random-recommendations'),
    section('Fishing', 'fish', P('Fishing')),
    section('Golf', 'flag', P('Golf')),
    section('Shopping', 'shopping-bag', P('Shopping')),
    section('Spas + Salons', 'sparkles', P('Spas + Salons'), 'spas-salons'),
    section('Weather', 'cloud-sun-rain', P('Weather')),
    section('Emergency and Urgent Care', 'siren', P('Emergency and Urgent Care'), 'emergency'),
]

library = {
    'id': 'north-georgia',
    'name': 'North Georgia Mountains (Blue Ridge / Ellijay)',
    'sections': {s['id']: s for s in lib_sections},
}

guide = {
    'slug': 'cherry-log-summit',
    'name': 'Cherry Log Summit',
    'welcome': 'Welcome!',
    'hostedBy': 'Hosted By Brandon & Katharina',
    'address': '259 Cherry Log Summit Drive, Cherry Log, GA 30522',
    'location': [34.805173, -84.383046],
    'cover': '1c36d71d5e142b9ba70bd517934fae6d.jpg',
    'coverDesktop': 'd4cc1701ec5068a6eac99b5b1229fd2e.jpg',
    'contact': {'phone': '404-358-1552', 'sms': '404-358-1552', 'email': ''},
    'gate': True,
    'library': 'north-georgia',
    # The Info grid, in order. Strings starting with "lib:" pull a section from the shared library.
    'layout': [
        {'heading': 'Your Stay', 'sections': ['add-to-phone', 'welcome', 'check-in-arrival', 'check-out-departure', 'wifi', 'contact-us', 'cancellation-policy']},
        {'heading': 'The Home', 'sections': ['bbq-grill', 'fireplace-firepit', 'hot-tub', 'indoor-games-fun', 'outdoor-games-fun', 'playground', 'kitchen', 'laundry', 'thermostat', 'tv-streaming', 'trash', 'rules']},
        {'heading': 'Explore the Area', 'sections': ['lib:dining', 'lib:beer-wine', 'lib:grocery', 'lib:hiking-biking', 'lib:waterfalls', 'lib:nature-parks', 'lib:water-activities', 'lib:tours', 'lib:random-recommendations', 'lib:fishing', 'lib:golf', 'lib:shopping', 'lib:spas-salons', 'lib:weather', 'lib:emergency']},
    ],
    'sections': {s['id']: s for s in house},
}

os.makedirs(os.path.join(ROOT, 'content/guides'), exist_ok=True)
os.makedirs(os.path.join(ROOT, 'content/library'), exist_ok=True)
json.dump(guide, open(os.path.join(ROOT, 'content/guides/cherry-log-summit.json'), 'w'), ensure_ascii=False, indent=1)
json.dump(library, open(os.path.join(ROOT, 'content/library/north-georgia.json'), 'w'), ensure_ascii=False, indent=1)
n = lambda secs: sum(len(g['items']) for s in secs for g in s['groups'])
print('house sections', len(house), 'items', n(house), '| library sections', len(lib_sections), 'items', n(lib_sections))
print([s['id'] for s in house])
