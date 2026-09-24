# ponytail: re-derives every number in the homepage tier table from the four
# primary-source rates. Catches the bug class that bit sessions 17-19: right
# arithmetic, wrong quantity. Run against the repo file or the live HTML.
import re, sys, html

# --- primary source: caesars.com/myrewards/earn-and-redeem, read 2026-09-23 ---
TC_PER_DOLLAR_SLOTS = 1/5      # "Earn 1 Tier Credit for every $5 ... reel slot machine"
TC_PER_DOLLAR_VP     = 1/10    # "Earn 1 Tier Credit for every $10 wagered through video poker"
DIAMOND_TC           = 15000   # "Diamond 15,000 - 24,999 Tier Credits"
DAY_BONUS_EARN       = 5000    # "5,000 Tier Credits + 10,000 Tier Credit Bonus / Earns Diamond Status in one day!"
DAY_BONUS_PAYS       = 10000
# --- other sources ---
SLOT_HOLD = 0.08               # reel-slot hold used by /casino-comps/#rated
VP_EDGE   = 1 - 0.9954         # 9/6 Jacks or Better optimal return, Shackleford
HANDS_HR  = 600                # estimate, labelled as such on the page

assert DAY_BONUS_EARN + DAY_BONUS_PAYS >= DIAMOND_TC, "one-day route does not actually reach Diamond"

def coin_in(tc, rate): return tc / rate
rows = [
    ("Reel slots, spread across the year",                      coin_in(DIAMOND_TC,    TC_PER_DOLLAR_SLOTS), SLOT_HOLD),
    ("Reel slots, 5,000 credits inside one promotional day",    coin_in(DAY_BONUS_EARN, TC_PER_DOLLAR_SLOTS), SLOT_HOLD),
    ("9/6 video poker played correctly, spread",                coin_in(DIAMOND_TC,    TC_PER_DOLLAR_VP),    VP_EDGE),
    ("9/6 video poker played correctly, one promotional day",   coin_in(DAY_BONUS_EARN, TC_PER_DOLLAR_VP),    VP_EDGE),
]

src = open(sys.argv[1], encoding='utf-8').read()
sec = src.split('id="tier-price"', 1)[1].split('<h2>Guides', 1)[0]
plain = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', sec)))

def money(x): return "${:,.0f}".format(x)
for label, ci, edge in rows:
    loss = ci * edge
    r = re.search(r'<tr><td>' + re.escape(label) + r'</td>.*?</tr>', sec, re.S)
    assert r, f"row missing: {label}"
    cells = re.findall(r'<td>(.*?)</td>', r.group(0))
    assert cells[1] == money(ci),   f"{label}: coin-in cell {cells[1]} != derived {money(ci)}"
    assert cells[3] == money(loss), f"{label}: loss cell {cells[3]} != derived {money(loss)}"
    print(f"ok  {label:<56} {cells[1]:>9} @ {cells[2]:<6} -> {cells[3]}")

# prose claims
ratio   = (coin_in(DIAMOND_TC, TC_PER_DOLLAR_VP) * VP_EDGE) / (coin_in(DIAMOND_TC, TC_PER_DOLLAR_SLOTS) * SLOT_HOLD)
edges   = SLOT_HOLD / VP_EDGE
hrs_low  = coin_in(DAY_BONUS_EARN, TC_PER_DOLLAR_VP) / (1.25 * HANDS_HR)
hrs_high = coin_in(DAY_BONUS_EARN, TC_PER_DOLLAR_VP) / (25.0 * HANDS_HR)
assert round(1/ratio) == 9,        f"'about a ninth' but 1/ratio = {1/ratio:.2f}"
assert round(edges)   == 17,       f"'seventeen times smaller' but edge ratio = {edges:.2f}"
assert round(hrs_low) == 67,       f"'about 67 hours' but {hrs_low:.1f}"
assert 3 < hrs_high < 3.5,         f"'a bit over three hours' but {hrs_high:.2f}"
assert "twice the coin-in" in plain and TC_PER_DOLLAR_SLOTS / TC_PER_DOLLAR_VP == 2
for s in ["about a ninth", "seventeen times smaller", "about 67 hours", "a bit over three hours",
          "1 Tier Credit per $5", "1 per $10", "15,000 Tier Credits", "adds 10,000"]:
    assert s in plain, f"prose claim missing/changed: {s}"
print(f"ok  prose: 1/{1/ratio:.1f} cost, {edges:.1f}x edge, {hrs_low:.0f}h @ $1.25, {hrs_high:.1f}h @ $25")
print("ALL CHECKS PASS")
