# ponytail: a page isn't shipped until llms.txt lists it (session 64 lesson: the card shipped without an entry).
# Every sitemap URL except the homepage must appear in llms.txt.
import re, sys
from pathlib import Path
R = Path(__file__).resolve().parent.parent
urls = re.findall(r"<loc>([^<]+)</loc>", (R / "sitemap.xml").read_text())
txt = (R / "llms.txt").read_text()
missing = [u for u in urls if u.rstrip("/") != "https://alwayshave.fun" and u not in txt]
assert urls and not missing, f"llms.txt missing: {missing}"
print(f"llms.txt lists all {len(urls)-1} non-home sitemap URLs")
