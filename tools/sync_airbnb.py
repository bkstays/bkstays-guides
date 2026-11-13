"""Sync each home's website gallery to its Airbnb listing: same photos, same order, same captions.

Usage (from /home/claude):  python3 guide/tools/sync_airbnb.py [slug ...]
Writes site-src/abnb/<slug>.json (ordered [photo_id, caption] list) and downloads any new photos to
site-src/abnb/img/<photo_id>.jpg + -sm.jpg. Photos are cached by Airbnb photo id, so a reorder costs no downloads.
"""
import concurrent.futures as cf, io, json, os, re, subprocess, sys, time
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, 'site-src', 'abnb')
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
AIRBNB = {
    'cherry-log-summit': '708113353448031702', 'havana-haven': '764323028368805808', 'sky-high-drive': '831729313185138634',
    'best-of-blue-ridge': '906966347762988888', 'tidewater-2601': '1048090717656589874', 'mcstay-in-mccay': '869705930887815980',
    'bellaire-extraordinaire': '1260957758148042919', 'birdie-blue': '1388701037440736417', 'tails-trails-hideaway': '1415202578270342242',
    'iron-range': '1438042265985483959', 'mountain-clarity': '1495518569920747994', 'das-himmel-haus': '1544066353722814123',
    'ripshin-heights': '1628554911197890502', 'grace-and-ember': '1734291596786161127',
}


def media_items(html):
    for m in re.finditer(r'<script[^>]*>(.*?)</script>', html, re.S):
        try:
            stack = [json.loads(m.group(1))]
        except Exception:
            continue
        while stack:
            o = stack.pop()
            if isinstance(o, dict):
                mi = o.get('mediaItems')
                if isinstance(mi, list) and mi and isinstance(mi[0], dict) and mi[0].get('baseUrl'):
                    return mi
                stack.extend(o.values())
            elif isinstance(o, list):
                stack.extend(o)
    return []


def fetch(listing_id):
    for attempt in range(4):
        html = subprocess.run(['curl', '-sS', '-A', UA, f'https://www.airbnb.com/rooms/{listing_id}/photos'],
                              capture_output=True, text=True).stdout
        items = media_items(html)
        if items:
            return items
        time.sleep(5 + 5 * attempt)
    raise SystemExit(f'Could not read Airbnb photos for {listing_id}')


def download(job):
    url, out = job
    try:
        raw = subprocess.run(['curl', '-sSf', url + '?im_w=1440'], capture_output=True, timeout=120).stdout
        im = Image.open(io.BytesIO(raw)).convert('RGB')
        a = im.copy(); a.thumbnail((1290, 1290)); a.save(out, quality=82, optimize=True)
        b = im.copy(); b.thumbnail((700, 700)); b.save(out[:-4] + '-sm.jpg', quality=78, optimize=True)
    except Exception as e:
        return f'{url}: {e}'


def main(slugs):
    os.makedirs(os.path.join(SRC, 'img'), exist_ok=True)
    jobs = []
    for slug in slugs:
        items = fetch(AIRBNB[slug])
        photos = []
        for it in items:
            url = it['baseUrl'].split('?')[0]
            pid = re.sub(r'\.\w+$', '', url.rsplit('/', 1)[-1])
            photos.append([pid, re.sub(r'\s+', ' ', it.get('accessibilityLabel') or '').strip()])
            out = os.path.join(SRC, 'img', pid + '.jpg')
            if not os.path.exists(out):
                jobs.append((url, out))
        json.dump({'airbnb_id': AIRBNB[slug], 'synced': time.strftime('%Y-%m-%d'), 'photos': photos},
                  open(os.path.join(SRC, slug + '.json'), 'w'), indent=1)
        print(f'{slug}: {len(photos)} photos')
        time.sleep(1)
    errs = [e for e in cf.ThreadPoolExecutor(12).map(download, jobs) if e]
    print(f'{len(jobs)} new photos downloaded, {len(errs)} errors')
    for e in errs:
        print(' ', e)


if __name__ == '__main__':
    main(sys.argv[1:] or list(AIRBNB))
