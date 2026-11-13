# ponytail: a page isn't shipped until llms.txt lists it (session 64 lesson: the card shipped without an entry).
# Every sitemap URL except the homepage must appear in llms.txt, and in README.md: the public GitHub
# repo page is the one off-site page that links here, and it sat at 6 of 16 pages from 09-13 to 11-12.
import re, sys
from pathlib import Path
R = Path(__file__).resolve().parent.parent
urls = re.findall(r"<loc>([^<]+)</loc>", (R / "sitemap.xml").read_text())
assert urls, "sitemap.xml has no URLs"
for name in ("llms.txt", "README.md"):
    txt = (R / name).read_text()
    # "(url)" / "url:" boundary so /caesars-diamond/ can't be satisfied by a longer URL sharing its prefix
    missing = [u for u in urls if u.rstrip("/") != "https://alwayshave.fun" and not re.search(re.escape(u) + r"(?![\w-])", txt)]
    assert not missing, f"{name} missing: {missing}"
    print(f"{name} lists all {len(urls)-1} non-home sitemap URLs")
