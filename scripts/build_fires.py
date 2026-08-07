"""
build_fires.py — Generate /fires, the live active-wildfire page for our 5 states.

Reads data/fires/incidents.json (written by fetch_fires.py from the NIFC/WFIGS
feed every 30 min) and renders one table: every uncontained incident of 100+
acres in NV/UT/AZ/CO/CA, with acres, containment, personnel, discovery date,
and which of our trails sit within 100 km of it.

Why this page exists: the nightly r/Utah + r/arizona answers keep hand-building
this table from the same feed, and nobody publishes it in one place for the
Southwest. It renews itself every 30 minutes, which is the site's moat.
"""

import os
import csv
import json
import math
from datetime import datetime, timezone

BASE_URL = "https://alwayshave.fun"
OUT_DIR = "generated/fires"
INCIDENTS = "data/fires/incidents.json"
STATES = {"NV": "Nevada", "UT": "Utah", "AZ": "Arizona", "CO": "Colorado", "CA": "California"}
MIN_ACRES = 100
NEAR_KM = 100

PAGE_TITLE = "Active Wildfires in the Southwest — Live Acres & Containment | alwayshave.fun"
PAGE_DESC = ("Every active wildfire over 100 acres in Nevada, Utah, Arizona, Colorado, and "
             "California — acres, containment, and the hiking trails near each one. Straight "
             "from the NIFC/WFIGS incident feed, refreshed every 30 minutes.")


def haversine_km(lat1, lng1, lat2, lng2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def load_trails(path="seeds/trails.csv"):
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        next(f)  # seeds/trails.csv has a two-row header (group labels, then fields)
        for row in csv.DictReader(f):
            try:
                out.append({"name": row["name"], "slug": row["slug"],
                            "state": (row["state"] or "").lower(),
                            "lat": float(row["lat"]), "lng": float(row["lng"])})
            except (KeyError, TypeError, ValueError):
                continue
    return out


def active_incidents(data):
    """100+ acres, in our 5 states, not yet fully contained."""
    out = []
    for i in data.get("incidents", []):
        if (i.get("state") not in STATES
                or (i.get("acres") or 0) < MIN_ACRES
                or (i.get("containment_pct") or 0) >= 100):
            continue
        out.append(i)
    return out


def nearby_trails(inc, trails, limit=4):
    near = []
    for t in trails:
        d = haversine_km(inc["lat"], inc["lng"], t["lat"], t["lng"])
        if d <= NEAR_KM:
            near.append((round(d), t))
    near.sort(key=lambda x: x[0])
    return near[:limit]


def fmt_date(iso):
    if not iso:
        return "—"
    try:
        return datetime.fromisoformat(iso).strftime("%b %-d")
    except ValueError:
        return "—"


def days_burning(iso):
    if not iso:
        return None
    try:
        return (datetime.now(timezone.utc) - datetime.fromisoformat(iso)).days
    except ValueError:
        return None


def esc(v):
    return (str(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def contain_color(pct):
    if pct is None or pct == 0:
        return "#dc2626"
    if pct < 50:
        return "#ea580c"
    if pct < 90:
        return "#d97706"
    return "#65a30d"


def incident_html(inc, trails):
    acres = int(inc.get("acres") or 0)
    pct = inc.get("containment_pct")
    pct_str = "0% contained" if pct in (None, 0) else f"{int(pct)}% contained"
    days = days_burning(inc.get("discovered"))
    people = inc.get("personnel")
    bits = [f"{STATES.get(inc.get('state'), '')}"]
    if inc.get("cause"):
        bits.append(f"{esc(inc['cause']).lower()} cause")
    bits.append(f"discovered {fmt_date(inc.get('discovered'))}"
                + (f" ({days} days ago)" if days is not None else ""))
    if people:
        bits.append(f"{int(people):,} personnel assigned")

    near = nearby_trails(inc, trails)
    if near:
        links = " · ".join(
            f'<a href="/{t["state"]}/{t["slug"]}" style="color:#58a6ff;text-decoration:none">'
            f'{esc(t["name"])}</a> <span style="color:#6e7681">{d} km</span>'
            for d, t in near)
        near_html = (f'<div style="font-size:.78rem;color:#8b949e;margin-top:8px">'
                     f'Trails within {NEAR_KM} km — live conditions: {links}</div>')
    else:
        near_html = ('<div style="font-size:.78rem;color:#6e7681;margin-top:8px">'
                     f'No trails we track are within {NEAR_KM} km.</div>')

    return f'''
    <div style="padding:16px 0;border-bottom:1px solid #30363d">
      <div style="display:flex;align-items:baseline;gap:12px;flex-wrap:wrap">
        <div style="font-weight:700;font-size:1.05rem">{esc(inc.get("name", ""))} Fire</div>
        <div style="font-weight:800;color:#e6edf3">{acres:,} acres</div>
        <div style="font-weight:600;color:{contain_color(pct)}">{pct_str}</div>
      </div>
      <div style="font-size:.78rem;color:#8b949e;margin-top:4px">{" · ".join(b for b in bits if b)}</div>
      {near_html}
    </div>'''


def build_html(incidents, trails, updated_at):
    try:
        stamp = datetime.fromisoformat(updated_at).strftime("%Y-%m-%d %H:%M UTC")
    except (TypeError, ValueError):
        stamp = "unknown"
    page_url = f"{BASE_URL}/fires"
    total_acres = sum(int(i.get("acres") or 0) for i in incidents)
    uncontained = sum(1 for i in incidents if not i.get("containment_pct"))
    by_state = {}
    for i in incidents:
        by_state.setdefault(i["state"], []).append(i)

    if incidents:
        sections = ""
        for st in sorted(by_state, key=lambda s: -sum(int(i.get("acres") or 0) for i in by_state[s])):
            rows = "\n".join(incident_html(i, trails)
                             for i in sorted(by_state[st],
                                             key=lambda i: -(i.get("acres") or 0)))
            sections += (f'<div class="section-title">{STATES[st]} — {len(by_state[st])} active'
                         f'</div>{rows}')
    else:
        sections = ('<p class="intro">No wildfire over 100 acres is currently burning '
                    'uncontained in these five states. That is good news, and it is what the '
                    'NIFC feed says as of the timestamp above.</p>')

    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "CollectionPage", "@id": page_url, "name": PAGE_TITLE,
             "description": PAGE_DESC, "url": page_url, "dateModified": updated_at},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL},
                {"@type": "ListItem", "position": 2, "name": "Active Wildfires", "item": page_url},
            ]},
            {"@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": "Where does this wildfire data come from?",
                 "acceptedAnswer": {"@type": "Answer", "text": (
                     "Directly from the NIFC/WFIGS Incident Locations feed — the same official "
                     "interagency record used by fire managers. We refetch it every 30 minutes "
                     "and show the timestamp of the read. We do not estimate or interpolate "
                     "anything; if the feed is silent, this page says so.")}},
                {"@type": "Question", "name": "Is it safe to hike near an active wildfire?",
                 "acceptedAnswer": {"@type": "Answer", "text": (
                     "Proximity is only part of it — smoke travels far further than fire. Check "
                     "the trail's own page for live AQI, and check inciweb.nwcg.gov and the "
                     "managing agency for closures before you drive. Roads and trailheads close "
                     "well before the fire reaches them.")}},
                {"@type": "Question", "name": "What does percent contained mean?",
                 "acceptedAnswer": {"@type": "Answer", "text": (
                     "Containment is the share of the fire's perimeter that crews have a control "
                     "line around — not how much of the fire is out. A 95% contained fire can "
                     "still be putting up smoke; a 0% contained fire is still growing freely.")}},
            ]},
        ],
    }

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-SENVGVQJ6X"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-SENVGVQJ6X');
  </script>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{PAGE_TITLE}</title>
  <meta name="description" content="{PAGE_DESC}">
  <link rel="canonical" href="{page_url}">
  <meta property="og:title" content="{PAGE_TITLE}">
  <meta property="og:description" content="{PAGE_DESC}">
  <meta property="og:url" content="{page_url}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="alwayshave.fun">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{PAGE_TITLE}">
  <meta name="twitter:description" content="{PAGE_DESC}">
  <script type="application/ld+json">{json.dumps(schema, separators=(",", ":"))}</script>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🔥</text></svg>">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #0c1117; color: #e6edf3; font-family: 'Inter', sans-serif; }}
    a {{ color: inherit; }}
    .wrap {{ max-width: 720px; margin: 0 auto; padding: 0 20px; }}
    .nav {{ position: sticky; top: 0; background: rgba(12,17,23,.95); border-bottom: 1px solid #30363d; z-index: 100; padding: 14px 0; }}
    .nav-inner {{ display: flex; align-items: center; gap: 12px; }}
    .nav-logo {{ font-weight: 800; font-size: 1.1rem; text-decoration: none; color: #e6edf3; }}
    .nav-sep {{ color: #30363d; }}
    .nav-state {{ color: #8b949e; font-size: .9rem; }}
    .hero {{ padding: 48px 0 32px; border-bottom: 1px solid #30363d; }}
    .h1 {{ font-size: 2.4rem; font-weight: 900; line-height: 1.1; margin-bottom: 12px; }}
    .stats {{ display: flex; gap: 12px; margin: 16px 0; flex-wrap: wrap; }}
    .pill {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 8px 16px; font-size: .85rem; color: #8b949e; }}
    .pill strong {{ color: #e6edf3; font-size: 1.1rem; }}
    .intro {{ font-size: .95rem; color: #8b949e; line-height: 1.7; margin-top: 16px; }}
    .section-title {{ font-size: 1rem; font-weight: 700; color: #8b949e; text-transform: uppercase; letter-spacing: .08em; padding: 28px 0 4px; }}
    .faq {{ padding: 32px 0 40px; border-top: 1px solid #30363d; margin-top: 24px; }}
    .faq h3 {{ font-size: .95rem; margin: 18px 0 4px; }}
    .faq p {{ font-size: .88rem; color: #8b949e; line-height: 1.7; }}
    footer {{ border-top: 1px solid #30363d; padding: 32px 0; font-size: .8rem; color: #6e7681; line-height: 2; text-align: center; }}
    footer a {{ color: #8b949e; text-decoration: none; }}
    footer a:hover {{ color: #e6edf3; }}
  </style>
</head>
<body>
  <nav class="nav">
    <div class="wrap">
      <div class="nav-inner">
        <a class="nav-logo" href="/">alwayshave.fun</a>
        <span class="nav-sep">/</span>
        <span class="nav-state">Active Wildfires</span>
      </div>
    </div>
  </nav>

  <div class="wrap">
    <div class="hero">
      <div class="h1">🔥 Active Wildfires in the Southwest</div>
      <div class="stats">
        <div class="pill"><strong>{len(incidents)}</strong> active fires</div>
        <div class="pill"><strong>{total_acres:,}</strong> acres burning</div>
        <div class="pill"><strong>{uncontained}</strong> at 0% contained</div>
      </div>
      <p class="intro">
        Every wildfire over {MIN_ACRES} acres still burning in Nevada, Utah, Arizona, Colorado,
        and California, straight from the federal NIFC/WFIGS incident feed — acres, containment,
        crews, and which of the trails we track sit within {NEAR_KM} km of each one.
        Read at <strong>{stamp}</strong> and refreshed every 30 minutes.
        Fully contained incidents drop off this list.
        For live smoke, see <a href="https://fire.airnow.gov" rel="nofollow noopener" style="color:#58a6ff">fire.airnow.gov</a>;
        for closures, check the managing agency before you drive.
      </p>
    </div>

    {sections}

    <div class="faq">
      <h3>Where does this data come from?</h3>
      <p>The NIFC/WFIGS Incident Locations feed — the official interagency record. We refetch it
      every 30 minutes and stamp the read time. Nothing here is estimated; when the feed is
      silent, the page says so rather than showing an old number.</p>
      <h3>What does &ldquo;percent contained&rdquo; mean?</h3>
      <p>The share of the fire's perimeter crews have a control line around — not how much of it
      is out. A 95% contained fire can still make plenty of smoke; a 0% contained fire is still
      growing freely.</p>
      <h3>Is it safe to hike near one of these?</h3>
      <p>Distance is only half the question — smoke travels much further than fire, and roads and
      trailheads close well before flames reach them. Check the trail's page here for live AQI,
      then check the managing agency and inciweb.nwcg.gov for closures.</p>
    </div>

    <footer>
      <a href="/">← All Trails</a> &nbsp;·&nbsp;
      <a href="/nv">Nevada</a> &nbsp;·&nbsp;
      <a href="/ut">Utah</a> &nbsp;·&nbsp;
      <a href="/az">Arizona</a> &nbsp;·&nbsp;
      <a href="/co">Colorado</a> &nbsp;·&nbsp;
      <a href="/ca">California</a> &nbsp;·&nbsp;
      <a href="/dog-friendly">Dog-Friendly</a><br>
      Fire data: NIFC/WFIGS, read {stamp} &nbsp;·&nbsp; <a href="/">alwayshave.fun</a>
    </footer>
  </div>
</body>
</html>'''


def main():
    try:
        with open(INCIDENTS) as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        print(f"  build_fires: no incident data ({e}) — skipping")
        return

    incidents = active_incidents(data)
    trails = load_trails()
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_html(incidents, trails, data.get("updated_at")))
    print(f"  ✓ fires/index.html ({len(incidents)} active incidents)")


if __name__ == "__main__":
    main()
