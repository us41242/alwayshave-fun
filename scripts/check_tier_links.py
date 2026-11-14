"""Every program tier page links to every other one (and --fix writes the line that does it).
Why: the pages were built one at a time and each linked only to the ones that already existed, so
on 2026-11-13 the Station page (the one Bing sends people to) had no link to Boyd, RW or Venetian,
and Boyd had two inbound links on the whole site. A new tier page goes in PAGES; the guard then
fails until --fix has rewritten the line everywhere.
  python3 scripts/check_tier_links.py [--fix]"""
import re, sys
R = "/Users/joshuaedrake/Documents/alwayshave-fun/guides/"
PAGES = [("caesars-diamond", "Caesars Diamond"), ("caesars-olympus", "Caesars Olympus"),
         ("mgm-gold-platinum", "MGM Gold and Platinum"), ("resorts-world-genting-rewards-tiers", "Resorts World Genting Rewards"),
         ("station-boarding-pass-tiers", "Station Boarding Pass"), ("venetian-rewards-tiers", "Venetian Rewards"),
         ("boyd-rewards-tiers", "Boyd Rewards")]
bad = 0
for slug, _ in PAGES:
    f = R + slug + "/index.html"; t = open(f).read()
    line = '<p id="all-tiers">Tier pages for the other programs: ' + " &middot; ".join(
        f'<a href="/{s}/">{n}</a>' for s, n in PAGES if s != slug) + ".</p>\n"
    if "--fix" in sys.argv:
        t = re.sub(r'<p id="all-tiers">.*?</p>\n', "", t)
        t, n = re.subn(r'(<p class="why"[^>]*>Sources)', lambda m: line + m.group(1), t)
        assert n == 1, f  # the Sources paragraph; the line sits right above it
        open(f, "w").write(t)
    elif line not in t:
        bad = 1; print("FAIL", slug, "is missing the current all-tiers line (run --fix)")
if not bad: print(f"ok: {len(PAGES)} tier pages each link to the other {len(PAGES)-1}")
sys.exit(bad)
