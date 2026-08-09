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
import re
import csv
import json
import math
from datetime import datetime, timezone

BASE_URL = "https://alwayshave.fun"
OUT_DIR = "generated/fires"
INCIDENTS = "data/fires/incidents.json"
ARCHIVE = "data/fires/archive.json"
STATES = {"NV": "Nevada", "UT": "Utah", "AZ": "Arizona", "CO": "Colorado", "CA": "California"}
MIN_ACRES = 100
# Bar for an incident to earn its own permanent page. Small fires produce thin
# pages and churn; 1,000+ acres is the size that generates real search demand.
PAGE_MIN_ACRES = 1000
NEAR_KM = 100

PAGE_CSS = """  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #0c1117; color: #e6edf3; font-family: 'Inter', sans-serif; }
    a { color: inherit; }
    .wrap { max-width: 720px; margin: 0 auto; padding: 0 20px; }
    .nav { position: sticky; top: 0; background: rgba(12,17,23,.95); border-bottom: 1px solid #30363d; z-index: 100; padding: 14px 0; }
    .nav-inner { display: flex; align-items: center; gap: 12px; }
    .nav-logo { font-weight: 800; font-size: 1.1rem; text-decoration: none; color: #e6edf3; }
    .nav-sep { color: #30363d; }
    .nav-state { color: #8b949e; font-size: .9rem; }
    .hero { padding: 48px 0 32px; border-bottom: 1px solid #30363d; }
    .h1 { font-size: 2.4rem; font-weight: 900; line-height: 1.1; margin-bottom: 12px; }
    .stats { display: flex; gap: 12px; margin: 16px 0; flex-wrap: wrap; }
    .pill { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 8px 16px; font-size: .85rem; color: #8b949e; }
    .pill strong { color: #e6edf3; font-size: 1.1rem; }
    .intro { font-size: .95rem; color: #8b949e; line-height: 1.7; margin-top: 16px; }
    .section-title { font-size: 1rem; font-weight: 700; color: #8b949e; text-transform: uppercase; letter-spacing: .08em; padding: 28px 0 4px; }
    .faq { padding: 32px 0 40px; border-top: 1px solid #30363d; margin-top: 24px; }
    .faq h3 { font-size: .95rem; margin: 18px 0 4px; }
    .faq p { font-size: .88rem; color: #8b949e; line-height: 1.7; }
    footer { border-top: 1px solid #30363d; padding: 32px 0; font-size: .8rem; color: #6e7681; line-height: 2; text-align: center; }
    footer a { color: #8b949e; text-decoration: none; }
    footer a:hover { color: #e6edf3; }
  </style>"""


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


def incident_slug(inc):
    """Permanent per-incident URL key. Includes state + discovery year because
    fire names repeat across states and seasons, and hard rule 3 means a slug
    we publish once has to keep meaning the same fire forever."""
    name = re.sub(r"[^a-z0-9]+", "-", (inc.get("name") or "").lower()).strip("-")
    year = (inc.get("discovered") or inc.get("first_seen") or "")[:4] or "unknown"
    return f"{name}-fire-{(inc.get('state') or '').lower()}-{year}"


def load_archive():
    try:
        with open(ARCHIVE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def update_archive(data, archive):
    """Fold this run's feed into the permanent record.

    Every incident that has ever cleared PAGE_MIN_ACRES keeps its entry (and so
    its URL) forever. `active` flips false once it stops appearing in the feed —
    we do NOT claim it is out, only that NIFC stopped listing it (hard rule 4).
    """
    read_at = data.get("updated_at") or datetime.now(timezone.utc).isoformat()
    day = read_at[:10]
    seen = set()

    for inc in data.get("incidents", []):
        if inc.get("state") not in STATES or (inc.get("acres") or 0) < PAGE_MIN_ACRES:
            continue
        slug = incident_slug(inc)
        seen.add(slug)
        entry = archive.get(slug, {"first_seen": read_at, "history": []})
        entry.update({k: inc.get(k) for k in
                      ("name", "state", "acres", "containment_pct", "cause",
                       "lat", "lng", "personnel", "discovered")})
        entry["last_seen"] = read_at
        entry["active"] = True
        # One point per UTC day, latest read of that day wins — a real growth
        # curve, free, from data we already fetch 48 times a day.
        hist = [h for h in entry["history"] if h["date"] != day]
        hist.append({"date": day, "acres": int(inc.get("acres") or 0),
                     "containment_pct": inc.get("containment_pct")})
        entry["history"] = sorted(hist, key=lambda h: h["date"])
        archive[slug] = entry

    for slug, entry in archive.items():
        if slug not in seen:
            entry["active"] = False
    return archive


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

    # Fires big enough to have their own page get linked from the table — that
    # link is the only crawl path to them.
    title = f'{esc(inc.get("name", ""))} Fire'
    if (inc.get("acres") or 0) >= PAGE_MIN_ACRES:
        title = (f'<a href="/fires/{incident_slug(inc)}" style="color:#58a6ff;'
                 f'text-decoration:none">{title} →</a>')

    return f'''
    <div style="padding:16px 0;border-bottom:1px solid #30363d">
      <div style="display:flex;align-items:baseline;gap:12px;flex-wrap:wrap">
        <div style="font-weight:700;font-size:1.05rem">{title}</div>
        <div style="font-weight:800;color:#e6edf3">{acres:,} acres</div>
        <div style="font-weight:600;color:{contain_color(pct)}">{pct_str}</div>
      </div>
      <div style="font-size:.78rem;color:#8b949e;margin-top:4px">{" · ".join(b for b in bits if b)}</div>
      {near_html}
    </div>'''


def archive_html(archive, shown_slugs):
    """Link every incident page not already linked from the table above.
    Contained and dropped-off fires still have permanent pages; without this
    they would be reachable only from the sitemap."""
    rest = [(s, e) for s, e in archive.items()
            if s not in shown_slugs and e.get("name")]
    if not rest:
        return ""
    rest.sort(key=lambda x: -(x[1].get("acres") or 0))
    links = " · ".join(
        f'<a href="/fires/{s}" style="color:#58a6ff;text-decoration:none">{esc(e["name"])} Fire</a>'
        f' <span style="color:#6e7681">{int(e.get("acres") or 0):,} ac, '
        f'{STATES.get(e.get("state"), "")}</span>' for s, e in rest)
    return (f'<div class="section-title">Also tracked this season</div>'
            f'<p class="intro">Contained, or no longer listed on the NIFC active feed. '
            f'We keep the page and the daily record for each one.<br><br>{links}</p>')


def build_html(incidents, trails, updated_at, archive=None):
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
  {PAGE_CSS}
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
    {archive_html(archive or {}, {incident_slug(i) for i in incidents if (i.get("acres") or 0) >= PAGE_MIN_ACRES})}

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


def growth_html(history):
    """Daily acres/containment from our own 30-min reads. This is the part of an
    incident page nobody else publishes — NIFC gives a snapshot, not a curve."""
    if len(history) < 2:
        return ('<p class="intro">We have one day of readings on this fire so far. '
                'The daily record builds from here.</p>')
    rows = ""
    prev = None
    for h in history[-30:]:
        acres = h["acres"]
        delta = ""
        if prev is not None:
            d = acres - prev
            if d > 0:
                delta = f'<span style="color:#dc2626">+{d:,} ac</span>'
            elif d < 0:
                # NIFC revises mapped perimeters downward; say so, don't hide it.
                delta = f'<span style="color:#8b949e">{d:,} ac (remap)</span>'
            else:
                delta = '<span style="color:#6e7681">no change</span>'
        prev = acres
        pct = h.get("containment_pct")
        rows += (f'<tr><td style="padding:6px 14px 6px 0;color:#8b949e">{h["date"]}</td>'
                 f'<td style="padding:6px 14px 6px 0;font-weight:600">{acres:,}</td>'
                 f'<td style="padding:6px 14px 6px 0;color:{contain_color(pct)}">'
                 f'{0 if pct is None else int(pct)}%</td>'
                 f'<td style="padding:6px 0;font-size:.85rem">{delta}</td></tr>')
    return (f'<table style="border-collapse:collapse;font-size:.9rem;margin-top:8px">'
            f'<tr style="color:#6e7681;font-size:.75rem;text-transform:uppercase">'
            f'<td style="padding-right:14px">Date</td><td style="padding-right:14px">Acres</td>'
            f'<td style="padding-right:14px">Contained</td><td>Change</td></tr>{rows}</table>')


def build_incident_html(slug, e, trails):
    name = esc(e.get("name", ""))
    state_name = STATES.get(e.get("state"), "")
    acres = int(e.get("acres") or 0)
    pct = e.get("containment_pct")
    active = e.get("active")
    url = f"{BASE_URL}/fires/{slug}"
    try:
        stamp = datetime.fromisoformat(e["last_seen"]).strftime("%Y-%m-%d %H:%M UTC")
    except (KeyError, TypeError, ValueError):
        stamp = "unknown"
    days = days_burning(e.get("discovered"))

    title = (f"{name} Fire, {state_name} — {acres:,} Acres, "
             f"{0 if pct is None else int(pct)}% Contained | alwayshave.fun")
    desc = (f"Live size, containment, crews and nearby hiking trails for the {name} Fire in "
            f"{state_name}. Straight from the NIFC/WFIGS incident feed, re-read every 30 "
            f"minutes — last read {stamp}.")

    if active:
        status = (f'<p class="intro">The {name} Fire is on the current NIFC active-incident '
                  f'list at <strong>{acres:,} acres</strong> and '
                  f'<strong>{0 if pct is None else int(pct)}% contained</strong>'
                  + (f", {days} days after it was discovered on {fmt_date(e.get('discovered'))}"
                     if days is not None else "") + '.</p>')
    else:
        status = (f'<p class="intro"><strong>No longer on the NIFC active list.</strong> '
                  f'The last reading we recorded was {acres:,} acres at '
                  f'{0 if pct is None else int(pct)}% contained on {e.get("last_seen", "")[:10]}. '
                  f'Incidents drop off the feed when they are contained or declared out — the '
                  f'feed does not tell us which, so we do not guess. This page is kept as the '
                  f'record of what we read while it burned.</p>')

    facts = [("State", state_name),
             ("Size", f"{acres:,} acres"),
             ("Containment", f"{0 if pct is None else int(pct)}%"),
             ("Cause", (e.get("cause") or "not reported").title()),
             ("Discovered", fmt_date(e.get("discovered"))),
             ("Personnel assigned", f"{int(e['personnel']):,}" if e.get("personnel") else "not reported")]
    facts_html = "".join(
        f'<div style="padding:10px 0;border-bottom:1px solid #21262d;display:flex;'
        f'justify-content:space-between;font-size:.9rem"><span style="color:#8b949e">{k}</span>'
        f'<span style="font-weight:600">{esc(v)}</span></div>' for k, v in facts)

    near = nearby_trails(e, trails) if e.get("lat") and e.get("lng") else []
    if near:
        rows = "".join(
            f'<div style="padding:10px 0;border-bottom:1px solid #21262d;font-size:.9rem">'
            f'<a href="/{t["state"]}/{t["slug"]}" style="color:#58a6ff;text-decoration:none">'
            f'{esc(t["name"])}</a> <span style="color:#6e7681">— {d} km away, live AQI and '
            f'conditions</span></div>' for d, t in near)
        near_html = (f'<div class="section-title">Trails within {NEAR_KM} km</div>{rows}'
                     f'<p class="intro">Distance is not the whole question — smoke carries much '
                     f'further than fire, and trailheads and roads close well before flames reach '
                     f'them. Each trail page shows live AQI; check the managing agency and '
                     f'inciweb.nwcg.gov for closures before you drive.</p>')
    else:
        near_html = (f'<div class="section-title">Trails within {NEAR_KM} km</div>'
                     f'<p class="intro">None of the trails we track are within {NEAR_KM} km of '
                     f'this fire. Smoke still travels far beyond that, so check the AQI on '
                     f'whichever trail page you are headed for.</p>')

    schema = {"@context": "https://schema.org", "@graph": [
        {"@type": "Article", "@id": url, "headline": f"{e.get('name','')} Fire, {state_name}",
         "description": desc, "url": url, "dateModified": e.get("last_seen"),
         "datePublished": e.get("first_seen"),
         "publisher": {"@type": "Organization", "name": "alwayshave.fun", "url": BASE_URL}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL},
            {"@type": "ListItem", "position": 2, "name": "Active Wildfires",
             "item": f"{BASE_URL}/fires"},
            {"@type": "ListItem", "position": 3, "name": f"{e.get('name','')} Fire", "item": url}]}]}

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
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <link rel="canonical" href="{url}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:url" content="{url}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="alwayshave.fun">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{desc}">
  <script type="application/ld+json">{json.dumps(schema, separators=(",", ":"))}</script>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🔥</text></svg>">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
{PAGE_CSS}
</head>
<body>
  <nav class="nav">
    <div class="wrap">
      <div class="nav-inner">
        <a class="nav-logo" href="/">alwayshave.fun</a>
        <span class="nav-sep">/</span>
        <a href="/fires" class="nav-state" style="text-decoration:none">Active Wildfires</a>
        <span class="nav-sep">/</span>
        <span class="nav-state">{name} Fire</span>
      </div>
    </div>
  </nav>

  <div class="wrap">
    <div class="hero">
      <div class="h1">{name} Fire</div>
      <div class="stats">
        <div class="pill"><strong>{acres:,}</strong> acres</div>
        <div class="pill"><strong>{0 if pct is None else int(pct)}%</strong> contained</div>
        <div class="pill"><strong>{state_name}</strong></div>
      </div>
      {status}
      <p class="intro">Source: the federal NIFC/WFIGS Incident Locations feed, re-read every
      30 minutes. Last read <strong>{stamp}</strong>. Nothing on this page is estimated.</p>
    </div>

    <div class="section-title">The numbers</div>
    {facts_html}

    <div class="section-title">Day-by-day, as we read it</div>
    {growth_html(e.get("history", []))}

    {near_html}

    <div class="faq">
      <h3>What does &ldquo;{0 if pct is None else int(pct)}% contained&rdquo; mean here?</h3>
      <p>Containment is the share of the fire's perimeter that crews have a control line
      around — not how much of the fire is out. A 95% contained fire can still put up plenty of
      smoke; a 0% contained fire is still growing freely.</p>
      <h3>Where do these numbers come from?</h3>
      <p>The NIFC/WFIGS Incident Locations feed — the official interagency record used by fire
      managers. We re-read it every 30 minutes and stamp the read time. The day-by-day table is
      our own record of those reads; acres sometimes drop when a perimeter is remapped, and we
      label that rather than smoothing it out.</p>
      <h3>Can I still hike near it?</h3>
      <p>Check the managing agency and inciweb.nwcg.gov for closures first — they close roads and
      trailheads well ahead of the fire. Then check the live AQI on the trail page itself; smoke
      is usually what decides the day, not flames.</p>
    </div>

    <footer>
      <a href="/fires">← All active fires</a> &nbsp;·&nbsp;
      <a href="/">All Trails</a> &nbsp;·&nbsp;
      <a href="/{(e.get("state") or "").lower()}">{state_name}</a><br>
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

    archive = update_archive(data, load_archive())
    with open(ARCHIVE, "w", encoding="utf-8") as f:
        json.dump(archive, f, indent=1, sort_keys=True)

    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_html(incidents, trails, data.get("updated_at"), archive))
    print(f"  ✓ fires/index.html ({len(incidents)} active incidents)")

    for slug, entry in archive.items():
        os.makedirs(os.path.join(OUT_DIR, slug), exist_ok=True)
        with open(os.path.join(OUT_DIR, slug, "index.html"), "w", encoding="utf-8") as f:
            f.write(build_incident_html(slug, entry, trails))
    live = sum(1 for e in archive.values() if e.get("active"))
    print(f"  ✓ fires/{{incident}} pages: {len(archive)} total ({live} active)")


if __name__ == "__main__":
    main()
