#!/usr/bin/env python3
"""Fail when a casino's published earn rates are overdue for re-verification.

Why: sibling of check_dated_claims.py. A dated claim expires on a known day;
an earn rate changes on a day nobody announces. Nothing on the site errors
when Caesars quietly moves 1 RC per $5 — the pages just become lies. The only
defense is a clock: every program's source gets re-read on a cadence, and
this script is the clock.

One entry per PROGRAM, not per claim: re-verifying means re-reading the whole
source anyway. Each dependent file carries one pin — the load-bearing rate
sentence — so if our own copy drifts, the registry fails loudly instead of
pointing at text that no longer exists. Full claim inventory per page lives in
the pages' own Sources sections.

ponytail: a literal table, 8 programs is not a parsing problem. No fetching —
casino sites block bots; re-verification is a human-shaped read of the source.

Usage:  python3 scripts/check_earn_rates.py [--on YYYY-MM-DD]
Exit 1 if any program is past due (last read > 180 days ago) or a pin moved.
When re-verifying: re-read every listed source, fix any changed rate on every
dependent file (calculators' JS constants too — grep the file for the old
number), update the page's Sources date, then update VERIFIED here.
NOTE: scripts/check_tier_routes.py hard-codes the same rates; update it when
a rate changes.
"""
import sys, datetime, pathlib

RECHECK_DAYS = 180
WARN_DAYS = 21

PC = "guides/players-cards-compared/index.html"

# (program, last source read YYYY-MM-DD, what to re-read, [(file, pin), ...])
PROGRAMS = [
    ("Caesars Rewards", "2026-09-24",
     "caesars.com/myrewards/earn-and-redeem (+ olympus page, benefits PDF, sportsbook RC exchange)", [
        ("guides/caesars-diamond/index.html",
         "Caesars earns 1 Tier Credit per $5 on reel slots and 1 per $10 on video poker"),
        ("guides/caesars-olympus/index.html",
         "Caesars pays 1 Reward Credit per $5, and 200 Reward Credits buy $1 of free play"),
        (PC, "$1 of free play per 200 Reward Credits, verified 2026-09-22"),
        ("guides/casino-comps/index.html",
         "pays 1 Reward Credit per $5 of slot coin-in and a Reward Credit spends at one cent"),
        ("index.html",
         "Caesars pays 1 Tier Credit per $5 on reel slots and 1 per $10 on video poker"),
     ]),
    ("MGM Rewards", "2026-10-11",
     "mgmresorts.com/en/mgm-rewards (earn, tiers, daily-tier-status-accelerator)", [
        ("guides/mgm-gold-platinum/index.html",
         "4 Tier Credits per $1 on hotel stays, dining, shows and spa"),
        (PC, "Points are worth one cent and Tier Credits are 4 per $1 on non-gaming spend"),
        ("index.html", "$18,750 of spend at 4 per $1"),
     ]),
    ("Station Boarding Pass", "2026-11-07",
     "stationcasinos.com/my-rewards-boarding-pass/ + Official Rules + 2026 Brochure PDF", [
        ("guides/station-boarding-pass-tiers/index.html",
         "Slots earn 3 credits per $1 and video poker earns 1. Hotel stays earn <b>50</b>"),
        ("guides/station-boarding-pass-tiers/index.html",
         "const PTS = { pari: 20, keno: 15, bingo: 5, slots: 1, sports: 1, vp: 0.5 };"),
        (PC, "Same 1-per-$1 slots, 1-per-$2 video poker, 1,000-to-the-dollar structure"),
        ("index.html", "it pays 50 status credits per hotel dollar"),
     ]),
    ("Venetian Rewards", "2026-10-13",
     "venetianlasvegas.com/venetian-rewards (terms-and-conditions, FAQ, benefits PDF)", [
        ("guides/venetian-rewards-tiers/index.html",
         "Slots earn 1 Tier Point per $4 of coin-in and video poker 1 per $10"),
        (PC, "1 Tier Point per $4 of slot coin-in, 1 per $10 on video poker, 2 per $1 of table theo"),
        ("index.html", "$1,500 of resort spend booked direct (2 per $1)"),
     ]),
    ("Resorts World Genting Rewards", "2026-10-14",
     "rwlasvegas.com/genting-rewards (earn-redeem, tier-benefits, disclaimer/terms)", [
        ("guides/resorts-world-genting-rewards-tiers/index.html",
         "Reel slots earn 3 points per $1 of coin-in and video poker 3 per $3.50"),
        (PC, "reel slots earn 3 Genting Points per $1 and video poker 3 per $3.50"),
        ("index.html", "$600 of dining, retail or spa (5 per $1)"),
     ]),
    ("Boyd Rewards", "2026-11-08",
     "rewards.boydgaming.com (points & tier credits, tier benefits, carryover, FAQ, program rules PDF)", [
        (PC, "One point per $1 of coin-in on reels, video reels and <b>keno</b>, per $2 on video poker"),
        ("guides/boyd-rewards-tiers/index.html",
         "const PT_VALUE = 1 / 1000, REEL_PER_PT = 1, VP_PER_PT = 2, TC_PRICE = 4.99;"),
        ("guides/boyd-rewards-tiers/index.html",
         "$4.99 of virtual coin purchases earns 1 Tier Credit</b> and <b>$0.99 earns 150 Boyd Points"),
        ("llms.txt", "1 per $1 reel/keno coin-in, 1 per $2 video poker, 1,000 = $1"),
     ]),
    ("Wynn Rewards", "2026-09-22",
     "wynnlasvegas.com/wynn-rewards", [
        (PC, "1 point per $5 on slots; video poker is 1 per $10 or 1 per $20"),
     ]),
    ("Binion's / Four Queens All Access", "2026-10-31",
     "binions.com/gaming/all_access + fourqueens.com/gaming/all_access + promo flyer slot", [
        (PC, "Slots earn 1 point per $5 and video poker 1 per $8"),
     ]),
]

def main(today):
    root = pathlib.Path(__file__).resolve().parent.parent
    bad = []
    for name, read, source, pins in PROGRAMS:
        for path, pin in pins:
            if pin not in (root / path).read_text(encoding="utf-8"):
                bad.append(f"{name}: pin moved in {path}: {pin!r} -> re-point this entry")
        due = datetime.date.fromisoformat(read) + datetime.timedelta(days=RECHECK_DAYS)
        if today > due:
            bad.append(f"{name}: last read {read}, {(today - due).days}d past due -> re-read {source}")
        elif (due - today).days <= WARN_DAYS:
            print(f"due in {(due - today).days}d  {name}: re-read {source}")
    for b in bad:
        print("STALE " + b)
    if bad:
        return 1
    n = sum(len(p[3]) for p in PROGRAMS)
    print(f"ok: {len(PROGRAMS)} programs, {n} pins, none past due as of {today}")
    return 0

if __name__ == "__main__":
    day = datetime.date.today()
    if "--on" in sys.argv:
        day = datetime.date.fromisoformat(sys.argv[sys.argv.index("--on") + 1])
    sys.exit(main(day))
