"""Clean-up of the Hospitable "space overview" text shown on the website home pages.

The source text comes from the Hospitable listings and is inconsistent from home to
home (Fire-pit / Firepit / Fire Pit, Hot Tub / Jacuzzi, "(sleep 2)", stray bullets,
filler lines). polish(slug, sections) returns cleaned [(heading, [paras], [items])].
"""
import re

# ---- global word fixes, applied to every heading, paragraph and item ----
SUBS = [
    (r'\b([Ff])ire[- ]?[Pp]it\b', lambda m: 'Fire Pit' if m.group(1) == 'F' else 'fire pit'),
    (r'\b([Ee])n[- ]?[Ss]uite\b', lambda m: m.group(1) + 'nsuite'),
    (r'\b(\d+)[ -]([Pp])erson\b', r'\1-\2erson'),
    (r'\b[Hh]ot [Tt]ub\b', 'Jacuzzi'),
    (r"\bSmore's\b", "S'mores"),
    (r'\bPack(?: and | & |-n-)Play\b', "Pack 'n Play"),
    (r'\bMs\. Pacman\b', 'Ms. Pac-Man'),
    (r'\bBig Game Buck Hunter\b', 'Big Buck Hunter'),
    (r'\bPlay-set\b', 'Playset'),
    (r'\bSection Couch\b', 'Sectional Couch'),
    (r'\bMerciers Orchards\b', 'Mercier Orchards'),
    (r'\bBearclaw\b', 'Bear Claw'),
    (r'\bMtn\b', 'Mountain'),
    (r'\bbtw\b', 'between'),
    (r'\bOled\b', 'OLED'),
    (r'\bFast High Speed\b', 'Fast High-Speed'),
    (r'\bHigh Speed\b', 'High-Speed'),
    (r'\bLow Level\b', 'Lower Level'),
    (r'\(sleep (\d+)\)', r'(Sleeps \1)'),
    (r'(\(Sleeps \d+\)) (?=[A-Z])', r'\1 - '),
    (r'\bhigh end\b', 'high-end'),
    (r'King Bed And Queen', 'King Bed and Queen'),
    (r'Smart TVs-Streaming', 'Smart TVs + Streaming'),
    (r'\bEtc$', 'etc.'),
    (r'\bhgih\b', 'high'),
    (r'\bwildlifes\b', 'wildlife'),
    (r'\+and\b', 'and'),
    (r',(?=[A-Za-z])', ', '),
    (r'\s{2,}', ' '),
]

# paragraphs that are filler on a website page
DROP_PARA = [r"^Don.t hesitate to reach out", r'^☆', r'^All these activities and more']

SMALL = {'And', 'With', 'Of', 'For', 'To', 'The', 'In', 'On', 'At'}

# ---- per-home fixes: exact item / paragraph text -> replacement (None drops it) ----
HOME = {
    'bellaire-extraordinaire': {
        'Jacuzzi: covered 7-person Jacuzzi': 'Jacuzzi: Covered 7-Person',
        '5 Nearby Amazing Resort Golf Courses': '5 Amazing Resort Golf Courses Nearby',
        'Regular Drip Coffee and Keurig Coffee + Mugs': None,
        'Coffee, Drink Bar, Keurig + Regular Drip Coffee': 'Coffee Bar - Keurig + Regular Drip Coffee',
        'Glassware, Bakeware, Flatware, Storage': 'Glassware, Bakeware, Flatware, Food Storage',
        'Children Plates, Bowls Silverware + High Chair': "Children's Plates, Bowls, Silverware + High Chair",
        'Laundry. Washer, Dryer, Detergent & Iron Board': 'Laundry - Washer, Dryer, Detergent + Ironing Board',
    },
    'birdie-blue': {
        'Master Bed: King Bed, Work Space, Ensuite Bath': 'Master Bedroom: King Bed, Workspace, Ensuite Bath',
    },
    'cherry-log-summit': {
        'Pet Friendly! Fenced-in Yard!': None,
        'Extra beds: 1 Queen Sleeper Sofas': 'Extra Bed: 1 Queen Sleeper Sofa',
        'Main Level: Queen, Shared Bath, 24” TV, Desk – Sleeps 2': 'Main Level: King, Shared Bath, 24” TV, Desk – Sleeps 2',
        'Lower Level: Queen + Twin Trundle, Shared Bath, 30” TV – Sleeps 4': 'Lower Level: 2 Queens, Shared Bath, 30” TV – Sleeps 4',
        'Bonus: Queen Pullout Sofa – Sleeps 2': 'Bonus (Lower Level): Queen Pullout Sofa – Sleeps 2',
        'Easy access to North GA spots': 'Easy Access to North Georgia Favorites',
        'Central Location between Blue Ridge & Ellijay': 'Central Location Between Blue Ridge & Ellijay',
        '”Very peaceful and enjoyable trip for all ages!”': '“Very peaceful and enjoyable trip for all ages!”',
        '”The kids loved the jacuzzi and game room"': '“The kids loved the jacuzzi and game room”',
        '”I enjoyed the views on the porch, and my husband loved the fire pit and location.”':
            '“I enjoyed the views on the porch, and my husband loved the fire pit and location.”',
        '“Our family had the best time. We enjoyed waking up with the sunrise and having a coffee”':
            '“Our family had the best time. We enjoyed waking up with the sunrise and having a coffee.”',
    },
    'das-himmel-haus': {
        'Bedroom 5 - Downstairs (Red ) - Shared 3rd Bath': 'Bedroom 5 - Downstairs (Red) - Shared 3rd Bath',
        'Cookware, bakeware, utensils, flatware,': 'Cookware, bakeware, utensils, flatware',
        '35 miles - Traverse (Airport)': '35 miles - Traverse City (Airport)',
        '1.5 miles - Golf / Schuss Mountain': '1.5 miles - Golf - Schuss Mountain',
        'Family-friendly and perfect for every group, the main level s a retreat for adults to unwind, and downstairs, the game room is perfect for kids and teens.':
            'Family-friendly and perfect for every group: the main level is a retreat for adults to unwind, and downstairs, the game room is perfect for kids and teens.',
    },
    'grace-and-ember': {
        'Private Home Gym - Peloton Bike & Rowing Machine': 'Private Home Gym - Peloton Bike + Rowing Machine',
        '3 Bathrooms, each with a private ensuite': '3 Bathrooms, Each a Private Ensuite',
        'Plates, Silverware, Bowls, Cups & Full Cookware •': 'Plates, Silverware, Bowls, Cups & Full Cookware',
        'Bathroom 2 (Retreat Sage) with Single Vanity and Tub/Shower Combination':
            'Bathroom 2 (Sage Retreat) with Single Vanity and Tub/Shower Combination',
        'Select dogs are welcome with prior approval. Please see below for details.':
            'Select dogs are welcome with prior approval.',
    },
    'havana-haven': {
        'Leatherbound Sofa and 2 Bright Accent chairs': 'Leatherbound Sofa and 2 Bright Accent Chairs',
        "Family Friendly; Pack 'n Play, High Chair": "Family-Friendly: Pack 'n Play + High Chair",
    },
    'iron-range': {
        'Bedroom 1 - King (Sleeps 2) Ensuite. Fireplace. Patio': 'Bedroom 1 - King (Sleeps 2) - Ensuite, Fireplace, Patio',
        'Bedroom 2 - King (Sleeps 2) Ensuite Bath. Lake View': 'Bedroom 2 - King (Sleeps 2) - Ensuite Bath, Lake View',
        'Bedroom 3 - King + Pullout Sofa (Sleeps 4). View': 'Bedroom 3 - King + Pullout Sofa (Sleeps 4) - Views',
        'Bedroom 4 - Queen (4) (Sleeps 8) Lounge Area. TV': 'Bedroom 4 - 4 Queens (Sleeps 8) - Lounge Area, TV',
        'Bedroom 5 - King (Sleeps 2) Lower Level. Desk. TV': 'Bedroom 5 - King (Sleeps 2) - Lower Level, Desk, TV',
        'Bedroom 6 - King (Sleeps 2) Lounge. Desk. TV': 'Bedroom 6 - King (Sleeps 2) - Lounge, Desk, TV',
        'Fire Pit - Large Stone Fire Pit Area w/ seating': 'Fire Pit - Large Stone Fire Pit Area w/ Seating',
        'Patio - Pergola with picnic table dining tables': 'Patio - Pergola with Picnic-Style Dining Tables',
        'Bath 4 - Downstairs (shared) - Shower, Tub Combo': 'Bath 4 - Downstairs (Shared) - Shower + Tub Combo',
    },
    'mountain-clarity': {
        '6-Person Jacuzzi for Ultimate Comfort': '6-Person Jacuzzi for Ultimate Relaxation',
        'Six-Person Jacuzzi for Ultimate Comfort': '6-Person Jacuzzi for Ultimate Relaxation',
        'Bed 4 - Lower Level - Queen Sofa Sleeper': 'Sofa Bed - Lower Level - Queen Sofa Sleeper',
    },
    'ripshin-heights': {
        'Serenberry Vineyards - 15.8 miles': None,   # closed
    },
    'sky-high-drive': {
        'Family-Friendly, Pack-n-Play,': "Family-Friendly, Pack 'n Play",
        "Family-Friendly, Pack 'n Play,": "Family-Friendly, Pack 'n Play",
        'Formal Dining Tables for Large Groups': None,   # repeats the line above it
        'Ensuite1: King Bed, Walk-In Closet, Roku TV, Ensuite': 'Ensuite 1: King Bed, Walk-In Closet, Roku TV, Ensuite',
    },
    'tails-trails-hideaway': {
        '2 Spacious King Bedrooms + Master Suite': '2 Spacious King Bedrooms, Including a Master Suite',
    },
    'tidewater-2601': {
        "After booking you will receive more communication including a lengthy Faq's section and a digital guidebook containing house rules, resort rules, parking requirements, and guest access etc.":
            "After booking, you'll receive a digital guidebook with house rules, resort rules, parking requirements and guest access details.",
        'This Reservation will come with passes to the resort facilities, beach access, parking and more.':
            'Your reservation comes with passes to the resort facilities, beach access, parking and more.',
    },
}

# items in these homes that are really sentences: shown as a paragraph under the list
SENTENCE_ITEMS = {'grace-and-ember'}

# split run-together items ("A* B* C")
SPLIT_STAR = re.compile(r'\*\s*')

MILES = re.compile(r'(?:^([\d.]+) miles? -)|(?:[-–] ([\d.]+) mi(?:les)?$)')


def _sub(t):
    for a, b in SUBS:
        t = re.sub(a, b, t)
    return t.strip()


def _dots_to_commas(t):
    # "King Bed. Closet. TV" -> "King Bed, Closet, TV" (not "St. Andrews" / "Ms. Pac-Man")
    if t.count('. ') == 0 or len(t) > 220 or t[:1] in '“"”':
        return t
    return re.sub(r'(?<!\bSt)(?<!\bMs)\. (?=[A-Z0-9(])', ', ', t)


def _heading(h):
    h = _sub(h)
    h = re.sub(r'\s*\+\s*', ' & ', h)
    h = h.replace(' And ', ' & ').replace('Gameroom', 'Game Room')
    if re.search(r'Activit|Attraction|Proximity', h):
        return 'Nearby Attractions'
    words = h.split(' ')
    return ' '.join(w.lower() if i and w in SMALL else w for i, w in enumerate(words))


def _miles(t):
    m = MILES.search(t)
    return float(m.group(1) or m.group(2)) if m else None


def polish(slug, secs):
    fix = HOME.get(slug, {})
    out, seen_items = [], set()
    for head, paras, items in secs:
        head = _heading(head) if head else ''
        P = []
        for p in paras:
            p = _sub(p)
            p = fix.get(p, p)
            if p is None or any(re.search(d, p) for d in DROP_PARA):
                continue
            P.append(p)
        I, tail = [], []
        for it in items:
            for piece in SPLIT_STAR.split(it):
                piece = _sub(piece).rstrip(',').strip()
                piece = fix.get(piece, piece)
                if not piece:
                    continue
                piece = _dots_to_commas(piece)
                piece = fix.get(piece, piece)
                if piece is None:
                    continue
                if slug in SENTENCE_ITEMS and len(piece) > 90 and not re.search(r' [-–] |: ', piece):
                    tail.append(piece if piece.endswith(('.', '!')) else piece + '.')
                    continue
                key = (head, piece.lower())
                if key in seen_items or (slug == 'tidewater-2601' and piece.startswith('Gulf World') and any(x.startswith('Gulf World') for x in I)):
                    continue
                seen_items.add(key)
                I.append(piece)
        if I and all(_miles(x) is not None for x in I):
            I.sort(key=_miles)
        P2 = P + []
        if P2 or I or tail:
            out.append((head, P2, I, tail))
    return out
