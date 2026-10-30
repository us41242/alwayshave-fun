# ponytail: re-derives every cell of the homepage "cheapest status in Vegas"
# table from each program's own published rates, so the ranked table can never
# drift from the per-program pages. Same bug class as check_tier_table.py:
# right arithmetic, wrong quantity. Run against the repo file or live HTML.
#   python3 scripts/check_tier_routes.py index.html
import html, math, re, sys

VP_RETURN = 0.9954                 # 9/6 Jacks or Better, optimal play (Shackleford, wizardofodds.com)
VP_EDGE   = 1 - VP_RETURN

def money(x): return "${:,.0f}".format(math.floor(x + 0.5))   # half-up; Python's round() is half-even

# (tier label, threshold, video-poker credits per dollar of coin-in, non-gaming credits per $1)
# Rates read from each operator's own earn pages; dates and URLs are on the per-program page.
PROGRAMS = [
    ("Station Gold",          1_000,   1/1,    50),   # VP 1 credit/$1; hotel 50/$1
    ("Resorts World Elite",   3_000,   3/3.5,   5),   # VP 3 per $3.50; F&B, retail, spa 5/$1
    ("Venetian Sapphire",     3_000,   1/10,    2),   # VP 1 per $10; direct-booked resort spend 2/$1
    ("Station Platinum",     40_000,   1/1,    50),
    ("Resorts World Prime",  75_000,   3/3.5,   5),
    ("Venetian Ruby",        20_000,   1/10,    2),
]
CAESARS_VP, CAESARS_SPEND = 1/10, 1                   # VP 1 TC per $10; room/dining/spa 1 TC per $1
DAY_EARN, DAY_BONUS = 5_000, 10_000                   # Caesars daily Tier Credit bonus: earn 5,000, get 10,000
MGM_RATE, MGM_DAY_EARN, MGM_DAY_BONUS = 4, 40_000, 60_000

src = open(sys.argv[1], encoding="utf-8").read()
sec = src.split('id="cheapest-status"', 1)[1].split("<h2>Guides", 1)[0]
plain = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", sec)))

def row(label):
    m = re.search(r"<tr><td>(?:<a[^>]*>)?" + re.escape(label) + r"</a>?</td>(.*?)</tr>", sec, re.S)
    assert m, f"row missing: {label}"
    return [re.sub(r"<[^>]+>", "", c) for c in re.findall(r"<td[^>]*>(.*?)</td>", m.group(0))]

losses = []
for label, tc, vp_rate, spend_rate in PROGRAMS:
    coin_in, spend = tc / vp_rate, tc / spend_rate
    loss = coin_in * VP_EDGE
    cells = row(label)
    assert str(f"{tc:,}") in cells[1], f"{label}: threshold {tc:,} not in {cells[1]!r}"
    assert money(coin_in) in cells[2] and money(loss) in cells[2], f"{label}: {cells[2]!r} != {money(coin_in)} -> {money(loss)}"
    assert money(spend) in cells[3], f"{label}: no-gambling cell {cells[3]!r} != {money(spend)}"
    losses.append((loss, label))
    print(f"ok  {label:<22} {money(coin_in):>12} -> {money(loss):>7}   or {money(spend)} of spend")

# Caesars Diamond: one daily-bonus day earns DAY_EARN and is paid DAY_BONUS on top
assert DAY_EARN + DAY_BONUS >= 15_000, "one bonus day no longer reaches Diamond"
d_coin, d_spend = DAY_EARN / CAESARS_VP, 15_000 / CAESARS_SPEND
cells = row("Caesars Diamond")
assert money(d_coin) in cells[2] and money(d_coin * VP_EDGE) in cells[2], cells[2]
assert money(d_spend) in cells[3], cells[3]
losses.append((d_coin * VP_EDGE, "Caesars Diamond"))
print(f"ok  {'Caesars Diamond':<22} {money(d_coin):>12} -> {money(d_coin*VP_EDGE):>7}   or {money(d_spend)} of spend")

# Caesars Olympus: 300,000 TC, reached over 20 bonus days of 5,000 earned
DAYS = 20
assert DAYS * (DAY_EARN + DAY_BONUS) == 300_000, "20 bonus days no longer land exactly on Olympus"
o_coin = DAYS * DAY_EARN / CAESARS_VP
cells = row("Caesars Olympus")
assert "300,000" in cells[1] and f"{DAYS} daily-bonus days" in cells[2], cells
assert money(o_coin) in cells[2] and money(o_coin * VP_EDGE) in cells[2], cells[2]
assert money(300_000 / CAESARS_SPEND) in cells[3], cells[3]
losses.append((o_coin * VP_EDGE, "Caesars Olympus"))
print(f"ok  {'Caesars Olympus':<22} {money(o_coin):>12} -> {money(o_coin*VP_EDGE):>7}   or {money(300_000/CAESARS_SPEND)} of spend")

# MGM publishes no machine rate, so it must claim no play price at all
cells = row("MGM Gold")
assert "publishes no machine earn rate" in cells[2], cells[2]
assert money(75_000 / MGM_RATE) in cells[3], cells[3]
assert MGM_DAY_EARN + MGM_DAY_BONUS >= 75_000, "one Accelerator day no longer reaches Gold"
assert money(MGM_DAY_EARN / MGM_RATE) in cells[3], cells[3]
assert "Boyd Rewards, Wynn Rewards" in plain and "Not derivable" in plain
print(f"ok  {'MGM Gold':<22} {'no rate':>12}            or {money(75_000/MGM_RATE)} spread, {money(MGM_DAY_EARN/MGM_RATE)} in one day")

# the table claims to be ranked from cheapest
order = [l for _, l in losses]
table_order = re.findall(r"<tr><td>(?:<a[^>]*>)?([A-Z][^<]*?)</a>?</td>", sec)
ranked = sorted(losses)
assert [l for _, l in ranked] == [l for l in table_order if l in order], \
    f"table is not ranked cheapest-first: {table_order} vs {[l for _, l in ranked]}"

# prose claims that carry a number
hrs = lambda bet: 200_000 / bet / 600          # 600 hands/hour, the page's stated estimate
assert round(hrs(1.25)) == 267, hrs(1.25)
assert round(hrs(25)) == 13, hrs(25)
for s in ["about 267 hours", "about 13 at $25 a hand", "600 hands an hour", "0.46%",
          "50 status credits per hotel dollar", "$800 room bill", "$40,000 through a machine"]:
    assert s in plain, f"prose claim missing/changed: {s}"
print("ok  ranked cheapest-first; prose: 267 h @ $1.25, 13 h @ $25")
print("ALL CHECKS PASS")
