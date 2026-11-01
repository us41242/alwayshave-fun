#!/usr/bin/env python3
"""Fail when a time-boxed claim on the site has passed its end date.

Why: 2026-10-31 the Binion's free-slot-play bonus expired and nothing on the
site knew. The only thing that caught it was a note in LOGBOOK.md. A promo
window, a tier year or a qualification deadline reads as true forever once
published; it leaves no trace in a log when it goes stale.

ponytail: a literal table, not a parser. Dated claims are rare enough to list
by hand, and the entry IS the reminder of what to go re-read.

Usage:  python3 scripts/check_dated_claims.py [--on YYYY-MM-DD]
Exit 1 if any claim is expired, or if the pinned text is no longer on the page
(that means the copy moved and the entry needs updating, not deleting).
When a claim expires: re-read the source, rewrite the copy as past tense with
what replaced it, then remove or re-date the entry here.
"""
import sys, datetime, pathlib

# (file, last day the claim is true, text that must be on the page, what to re-verify)
CLAIMS = [
    ("guides/players-cards-compared/index.html", "2026-12-31", "now through 2026-12-31",
     "MGM Daily Tier Status Accelerator window (mgmresorts.com/en/mgm-rewards)"),
    ("guides/mgm-gold-platinum/index.html", "2026-12-31", "through December 31, 2026",
     "MGM Daily Tier Status Accelerator window; page calculator already degrades, prose does not"),
    ("guides/caesars-olympus/index.html", "2026-12-31", "300,000 Tier Credits earned by December 31, 2026",
     "Caesars Olympus qualification window and the 2027 threshold"),
    ("index.html", "2026-12-31", "300,000 Tier Credits by December 31, 2026",
     "homepage ranked tier table repeats the Olympus deadline"),
    ("guides/resorts-world-genting-rewards-tiers/index.html", "2027-01-04", "January 4, 2027",
     "Genting Rewards tier year rolls over 2027-01-05; thresholds may change"),
]

def main(today):
    root = pathlib.Path(__file__).resolve().parent.parent
    bad = []
    for path, end, pin, what in CLAIMS:
        f = root / path
        text = f.read_text(encoding="utf-8")
        if pin not in text:
            bad.append(f"{path}: pinned text moved or changed: {pin!r} -> re-point this entry")
            continue
        last = datetime.date.fromisoformat(end)
        if today > last:
            bad.append(f"{path}: claim expired {end} ({(today - last).days} days ago) -> re-verify {what}")
    for b in bad:
        print("EXPIRED " + b)
    if bad:
        return 1
    soon = [c for c in CLAIMS if (datetime.date.fromisoformat(c[1]) - today).days <= 14]
    for path, end, _pin, what in soon:
        print(f"due in {(datetime.date.fromisoformat(end) - today).days}d  {path} ({end}): {what}")
    print(f"ok: {len(CLAIMS)} dated claims, none expired as of {today}")
    return 0

if __name__ == "__main__":
    day = datetime.date.today()
    if "--on" in sys.argv:
        day = datetime.date.fromisoformat(sys.argv[sys.argv.index("--on") + 1])
    sys.exit(main(day))
