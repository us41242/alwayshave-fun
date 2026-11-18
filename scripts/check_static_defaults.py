# ponytail: every calculator ships its default answer in the static HTML, so no-JS readers
# (ChatGPT's fetcher, Bing's snippet) see numbers instead of blanks. This guard renders each page
# in headless Chrome and fails if any element's static text differs from what the page's own JS
# computes on load — the 2,125-vs-2,000 class of bug (11-16). Elements deliberately left empty
# (date-dependent cells: days left, period end) are skipped, and so is any container holding one.
# usage: python3 scripts/check_static_defaults.py page.html [...]
import sys, subprocess, re, html.parser, pathlib

CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
VOID = {'input', 'br', 'img', 'meta', 'link', 'hr', 'source', 'wbr', 'area', 'col', 'embed', 'param', 'track'}

class P(html.parser.HTMLParser):
    def __init__(s):
        super().__init__(); s.st = []; s.t = {}; s.kids = {}
    def handle_starttag(s, tag, a):
        if tag in VOID: return
        i = dict(a).get('id')
        if i:
            s.t.setdefault(i, '')
            for _, p in s.st:
                if p: s.kids.setdefault(p, []).append(i)
        s.st.append((tag, i))
    def handle_endtag(s, tag):
        while s.st and s.st.pop()[0] != tag: pass
    def handle_data(s, d):
        for _, i in s.st:
            if i: s.t[i] += d

def parse(h):
    p = P(); p.feed(h)
    return {k: re.sub(r'\s+', ' ', v).strip() for k, v in p.t.items()}, p.kids

bad = 0
for f in sys.argv[1:]:
    f = str(pathlib.Path(f).resolve())
    st, kids = parse(open(f).read())
    r = subprocess.run([CHROME, '--headless', '--disable-gpu', '--virtual-time-budget=3000', '--dump-dom', 'file://' + f],
                       capture_output=True, text=True, timeout=90).stdout
    rd, _ = parse(r)
    if not rd: print(f'FAIL {f}: Chrome rendered nothing'); bad += 1; continue
    n = 0
    for k, v in st.items():
        if not v or k not in rd or v == rd[k]: continue
        if any(not st.get(c) for c in kids.get(k, [])): continue  # holds a deliberately blank/JS-built cell
        print(f'FAIL {f} #{k}\n  static:   {v[:160]}\n  rendered: {rd[k][:160]}'); n += 1
    bad += n
    print(f'{"ok  " if not n else "FAIL"} {pathlib.Path(f).parent.name}: {sum(1 for v in st.values() if v)} static texts checked')
sys.exit(1 if bad else 0)
