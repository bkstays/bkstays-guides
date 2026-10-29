"""Re-download every photo referenced by the content files from the live site into site/img/."""
import json, glob, os, re, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = 'https://bkstays-guides.netlify.app/img/'
names = set()
for p in glob.glob(os.path.join(ROOT, 'content/**/*.json'), recursive=True):
    if '/templates/' in p: continue
    names |= set(re.findall(r'"(?:photo|photoHidden|cover|coverDesktop|background)":\s*"([^"]+\.(?:jpg|jpeg|png|webp))"', open(p, encoding='utf-8').read()))
os.makedirs(os.path.join(ROOT, 'site/img'), exist_ok=True)
for n in sorted(names):
    out = os.path.join(ROOT, 'site/img', n)
    if not os.path.exists(out):
        urllib.request.urlretrieve(LIVE + n, out)
print(len(names), 'photos present in site/img')
