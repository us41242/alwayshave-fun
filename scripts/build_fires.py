"""
build_fires.py — Generate /fires, the live active-wildfire page for our 5 states.

Reads data/fires/incidents.json (written by fetch_fires.py from the NIFC/WFIGS
feed every 30 min) and renders one table: every uncontained incident of 100+
acres in NV/UT/AZ/CO/CA, with acres, containment, personnel, discovery date,
and which of our trails sit within 100 km of it.

Why this page exists: the nightly r/Utah + r/arizona answers keep hand-building
this table from the same feed, and nobody publishes it in one place for the
Southwest. It renews itself every 30 minutes, which is the site's moat.

Also emits /data (the open-data catalog) and data/fires/growth-history.csv.
Lives here because the fire growth archive is the flagship dataset and is
already loaded in this script; /data only enumerates the conditions and climate
files, it does not own them.
"""

import os
import re
import csv
import glob
import json
import math
from datetime import datetime, timezone

BASE_URL = "https://alwayshave.fun"
OUT_DIR = "generated/fires"
DATA_OUT_DIR = "generated/data"
INCIDENTS = "data/fires/incidents.json"
ARCHIVE = "data/fires/archive.json"
GROWTH_CSV = "data/fires/growth-history.csv"
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
      <a href="/dog-friendly">Dog-Friendly</a> &nbsp;·&nbsp;
      <a href="/data">Open Data</a><br>
      Fire data: NIFC/WFIGS, read {stamp} &nbsp;·&nbsp; every reading here is
      <a href="/data">downloadable as CSV</a> &nbsp;·&nbsp; <a href="/">alwayshave.fun</a>
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
      <a href="/{(e.get("state") or "").lower()}">{state_name}</a> &nbsp;·&nbsp;
      <a href="/data">Open Data</a><br>
      Fire data: NIFC/WFIGS, read {stamp} &nbsp;·&nbsp; this fire's daily record is in the
      <a href="/data">open dataset</a> &nbsp;·&nbsp; <a href="/">alwayshave.fun</a>
    </footer>
  </div>
</body>
</html>'''


GROWTH_CSV_FIELDS = ["date", "incident_slug", "incident_name", "state", "acres",
                     "containment_pct", "cause", "discovered", "lat", "lng"]


def write_growth_csv(archive, path=GROWTH_CSV):
    """Flatten the archive to one row per incident per day.

    The JSON archive is the source of truth, but a CSV is what a journalist or
    researcher can actually open — and a `DataDownload` in a tabular format is
    what makes the dataset legible to Google Dataset Search.
    """
    rows = []
    for slug, e in sorted(archive.items()):
        if not e.get("name"):
            continue
        for h in e.get("history", []):
            rows.append({
                "date": h.get("date"),
                "incident_slug": slug,
                "incident_name": e.get("name"),
                "state": e.get("state"),
                "acres": h.get("acres"),
                "containment_pct": h.get("containment_pct"),
                "cause": e.get("cause") or "",
                "discovered": (e.get("discovered") or "")[:10],
                "lat": e.get("lat"),
                "lng": e.get("lng"),
            })
    rows.sort(key=lambda r: (r["date"] or "", r["incident_slug"]))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=GROWTH_CSV_FIELDS)
        w.writeheader()
        w.writerows(rows)
    return rows


CLIMATE_CSV = "data/climate/normals.csv"
CLIMATE_CSV_FIELDS = ["slug", "month", "avg_high_f", "avg_low_f", "wet_days", "source"]


def write_climate_csv(path=CLIMATE_CSV):
    """46 per-trail JSON files as one table — the shape anyone actually wants,
    and the `DataDownload` that makes the climate dataset legible to crawlers."""
    rows = []
    for fp in sorted(glob.glob("data/climate/*.json")):
        try:
            with open(fp) as f:
                c = json.load(f)
        except (OSError, ValueError):
            continue
        for m in c.get("months", []):
            rows.append({"slug": c.get("slug"), "month": m.get("month"),
                         "avg_high_f": m.get("avg_high_f"), "avg_low_f": m.get("avg_low_f"),
                         "wet_days": m.get("wet_days"), "source": c.get("source", "")})
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CLIMATE_CSV_FIELDS)
        w.writeheader()
        w.writerows(rows)
    return rows


def build_data_html(archive, rows, updated_at):
    """/data — the open-data catalog.

    Google's web index has crawled this domain's homepage once since June and
    knows no other URL: web-search discovery is gated on authority we do not
    have. Dataset Search is a separate index fed by schema.org/Dataset markup,
    where the competition is "who publishes this data" rather than "who has the
    most links" — and the daily wildfire growth record genuinely has no other
    publisher. Documenting and licensing it is also the precondition for anyone
    citing it, which is the backlink problem stated the honest way.
    """
    try:
        stamp = datetime.fromisoformat(updated_at).strftime("%Y-%m-%d %H:%M UTC")
    except (TypeError, ValueError):
        stamp = "unknown"
    page_url = f"{BASE_URL}/data"
    n_trails = len(glob.glob("data/conditions/*.json"))
    n_climate = len(glob.glob("data/climate/*.json"))
    incidents_with_curve = sum(1 for e in archive.values() if len(e.get("history", [])) > 1)
    dates = sorted({r["date"] for r in rows if r["date"]})
    span = f"{dates[0]}/{dates[-1]}" if dates else ""
    span_text = f"{dates[0]} to {dates[-1]}" if dates else "not yet"

    title = "Open Data — Southwest Wildfire, Trail Conditions & Climate Datasets | alwayshave.fun"
    desc = (f"Free, openly licensed datasets for Nevada, Utah, Arizona, Colorado and California: "
            f"a day-by-day wildfire size and containment record covering {len(archive)} incidents, "
            f"live trail conditions and air quality for {n_trails} trails, and 10-year monthly "
            f"climate normals. CC BY 4.0, JSON and CSV, updated every 30 minutes.")

    license_url = "https://creativecommons.org/licenses/by/4.0/"
    creator = {"@type": "Organization", "name": "alwayshave.fun", "url": BASE_URL}
    states_covered = [{"@type": "Place", "name": n} for n in STATES.values()]

    datasets = [
        {
            "@type": "Dataset",
            "@id": f"{page_url}#wildfire-growth",
            "name": "Southwest Wildfire Daily Growth Record (NV, UT, AZ, CO, CA)",
            "description": (
                "A day-by-day record of size (acres) and containment percentage for every "
                "wildfire of 1,000 acres or more in Nevada, Utah, Arizona, Colorado and "
                "California, built by reading the federal NIFC/WFIGS Incident Locations feed "
                "every 30 minutes and keeping the last reading of each UTC day. The upstream "
                "feed publishes only a current snapshot, so the historical curve it implies is "
                "not otherwise available; this dataset is that curve. Incidents are retained "
                "permanently after they leave the active feed. Perimeter remaps can move acreage "
                "downward and are recorded as read, not smoothed."),
            "url": f"{page_url}#wildfire-growth",
            "license": license_url,
            "creator": creator,
            "isAccessibleForFree": True,
            "dateModified": updated_at,
            "temporalCoverage": span,
            "spatialCoverage": states_covered,
            "keywords": ["wildfire", "fire containment", "acres burned", "NIFC", "WFIGS",
                         "Nevada", "Utah", "Arizona", "Colorado", "California",
                         "wildfire history", "fire growth"],
            "variableMeasured": [
                {"@type": "PropertyValue", "name": "acres",
                 "description": "Incident size in acres as reported by NIFC/WFIGS on that date",
                 "unitText": "acre"},
                {"@type": "PropertyValue", "name": "containment_pct",
                 "description": "Share of the fire perimeter under a control line, 0-100",
                 "unitText": "percent"},
                {"@type": "PropertyValue", "name": "cause",
                 "description": "Reported cause: natural, human, or undetermined"},
            ],
            "isBasedOn": "https://data-nifc.opendata.arcgis.com/",
            "distribution": [
                {"@type": "DataDownload", "encodingFormat": "text/csv",
                 "contentUrl": f"{BASE_URL}/{GROWTH_CSV}",
                 "name": "growth-history.csv — one row per incident per day"},
                {"@type": "DataDownload", "encodingFormat": "application/json",
                 "contentUrl": f"{BASE_URL}/{ARCHIVE}",
                 "name": "archive.json — full incident records with nested daily history"},
                {"@type": "DataDownload", "encodingFormat": "application/json",
                 "contentUrl": f"{BASE_URL}/{INCIDENTS}",
                 "name": "incidents.json — the current 30-minute read of the active feed"},
            ],
        },
        {
            "@type": "Dataset",
            "@id": f"{page_url}#trail-conditions",
            "name": "Live Trail Conditions and Air Quality, Southwest United States",
            "description": (
                f"Current weather, air quality index, wildfire proximity, river flow where "
                f"relevant, and a 1-100 hikeability score for {n_trails} hiking trails across "
                f"Nevada, Utah, Arizona, Colorado and California, refreshed every 30 minutes. "
                f"Each record carries the observation timestamp and names the source of each "
                f"reading, and reports missing values as missing rather than carrying a stale "
                f"number forward. Weather and AQI fallback come from Open-Meteo, primary AQI "
                f"from AirNow, fire proximity from NASA FIRMS and NIFC/WFIGS."),
            "url": f"{page_url}#trail-conditions",
            "license": license_url,
            "creator": creator,
            "isAccessibleForFree": True,
            "dateModified": updated_at,
            "spatialCoverage": states_covered,
            "keywords": ["air quality", "AQI", "hiking", "trail conditions", "PM2.5",
                         "weather", "wildfire smoke", "Southwest United States"],
            "variableMeasured": [
                {"@type": "PropertyValue", "name": "aqi",
                 "description": "US EPA Air Quality Index at or near the trailhead"},
                {"@type": "PropertyValue", "name": "score",
                 "description": "Composite 1-100 hikeability score (methodology at /scoring)"},
                {"@type": "PropertyValue", "name": "current",
                 "description": "Temperature, wind, precipitation and humidity at the trailhead"},
            ],
            "distribution": [
                {"@type": "DataDownload", "encodingFormat": "application/json",
                 "contentUrl": f"{BASE_URL}/data/trails-index.json",
                 "name": "trails-index.json — all trails with current score and conditions"},
            ],
        },
        {
            "@type": "Dataset",
            "@id": f"{page_url}#climate-normals",
            "name": "Trailhead Monthly Climate Normals, 2015-2024 (ERA5)",
            "description": (
                f"Ten-year monthly normals — average high, average low, and count of wet days — "
                f"computed at the trailhead coordinates of {n_climate} Southwest hiking trails "
                f"from the ERA5 reanalysis via Open-Meteo's historical archive. Intended for the "
                f"question a gridded national normal answers badly: what a specific trailhead is "
                f"typically like in a given month, including trails whose elevation puts them in "
                f"a different regime from the nearest town."),
            "url": f"{page_url}#climate-normals",
            "license": license_url,
            "creator": creator,
            "isAccessibleForFree": True,
            "temporalCoverage": "2015-01-01/2024-12-31",
            "spatialCoverage": states_covered,
            "keywords": ["climate normals", "ERA5", "monthly temperature", "precipitation",
                         "hiking season", "best time to hike"],
            "variableMeasured": [
                {"@type": "PropertyValue", "name": "avg_high_f",
                 "description": "Mean daily maximum temperature", "unitText": "degree Fahrenheit"},
                {"@type": "PropertyValue", "name": "avg_low_f",
                 "description": "Mean daily minimum temperature", "unitText": "degree Fahrenheit"},
                {"@type": "PropertyValue", "name": "wet_days",
                 "description": "Mean count of days per month with measurable precipitation",
                 "unitText": "day"},
            ],
            "isBasedOn": "https://open-meteo.com/en/docs/historical-weather-api",
            "distribution": [
                {"@type": "DataDownload", "encodingFormat": "text/csv",
                 "contentUrl": f"{BASE_URL}/{CLIMATE_CSV}",
                 "name": "normals.csv — one row per trail per month"},
            ],
        },
    ]

    # Datasets are nested inside the catalog, not referenced by @id. Reference-only
    # children ({"@id": ...} pointing at sibling @graph nodes) were silently dropped
    # by validator.schema.org — it reported the catalog with no `dataset` property
    # and zero Dataset nodes, i.e. exactly the markup this page exists for, invisible.
    schema = {"@context": "https://schema.org", "@graph": [
        {"@type": "DataCatalog", "@id": page_url, "name": "alwayshave.fun Open Data",
         "description": desc, "url": page_url, "license": license_url, "creator": creator,
         "dateModified": updated_at, "dataset": datasets},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL},
            {"@type": "ListItem", "position": 2, "name": "Open Data", "item": page_url}]},
    ]}

    def field_rows(pairs):
        return "".join(
            f'<div style="padding:9px 0;border-bottom:1px solid #21262d;font-size:.88rem">'
            f'<code style="color:#58a6ff">{esc(k)}</code> '
            f'<span style="color:#8b949e">— {esc(v)}</span></div>' for k, v in pairs)

    growth_fields = field_rows([
        ("date", "UTC date of the reading, YYYY-MM-DD"),
        ("incident_slug", "stable key for the incident; also its page at /fires/{slug}"),
        ("incident_name", "incident name as published by NIFC"),
        ("state", "NV, UT, AZ, CO or CA"),
        ("acres", "size in acres on that date"),
        ("containment_pct", "0–100; empty when the feed reported no value"),
        ("cause", "natural, human or undetermined, as last reported"),
        ("discovered", "discovery date, YYYY-MM-DD"),
        ("lat / lng", "incident point location, WGS84 decimal degrees"),
    ])

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
  <meta name="description" content="{esc(desc)}">
  <link rel="canonical" href="{page_url}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{esc(desc)}">
  <meta property="og:url" content="{page_url}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="alwayshave.fun">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{esc(desc)}">
  <script type="application/ld+json">{json.dumps(schema, separators=(",", ":"))}</script>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📊</text></svg>">
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
        <span class="nav-state">Open Data</span>
      </div>
    </div>
  </nav>

  <div class="wrap">
    <div class="hero">
      <div class="h1">📊 Open Data</div>
      <div class="stats">
        <div class="pill"><strong>{len(archive)}</strong> wildfire incidents</div>
        <div class="pill"><strong>{len(rows):,}</strong> daily fire readings</div>
        <div class="pill"><strong>{n_trails}</strong> trails</div>
      </div>
      <p class="intro">
        Everything this site measures is published here as plain JSON and CSV under
        <a href="{license_url}" rel="license noopener" style="color:#58a6ff">CC BY 4.0</a> —
        free to use, including commercially, with attribution. No key, no signup, no rate limit
        beyond ordinary politeness. Rebuilt every 30 minutes; last write <strong>{stamp}</strong>.
      </p>
    </div>

    <div class="section-title">1. Southwest wildfire daily growth record</div>
    <p class="intro">
      Size and containment for every wildfire of {PAGE_MIN_ACRES:,}+ acres in Nevada, Utah,
      Arizona, Colorado and California, <strong>one row per incident per day</strong> —
      {len(archive)} incidents, {len(rows):,} readings, {span_text}, with a multi-day curve on
      {incidents_with_curve} of them.
    </p>
    <p class="intro">
      The reason this exists: the federal NIFC/WFIGS feed publishes a <em>current snapshot</em>
      and overwrites it. Read it 48 times a day and keep the last reading of each UTC day and you
      have the growth curve the snapshot implies but never shows — how fast a fire ran, which day
      it blew up, when containment actually started moving. That record is what is published here.
      Incidents stay in the file permanently once they enter it, including after they drop off the
      active feed; when that happens the file says only that NIFC stopped listing the incident,
      because the feed does not say whether a fire was contained or declared out and we do not
      guess. Acreage sometimes falls when a perimeter is remapped — those revisions are kept as
      read rather than smoothed away.
    </p>
    <p class="intro">
      <a href="/{GROWTH_CSV}" style="color:#58a6ff">growth-history.csv</a> ({len(rows):,} rows) &nbsp;·&nbsp;
      <a href="/{ARCHIVE}" style="color:#58a6ff">archive.json</a> (nested daily history) &nbsp;·&nbsp;
      <a href="/{INCIDENTS}" style="color:#58a6ff">incidents.json</a> (current read) &nbsp;·&nbsp;
      <a href="/fires" style="color:#58a6ff">browse it as pages</a>
    </p>
    <div class="section-title" style="font-size:.85rem">CSV columns</div>
    {growth_fields}

    <div class="section-title">2. Live trail conditions and air quality</div>
    <p class="intro">
      Weather, AQI, wildfire proximity, river flow where it matters, and a 1–100 hikeability
      score for {n_trails} trails, refreshed every 30 minutes. Every record carries its
      observation timestamp and names the source of each reading; a value we could not fetch is
      reported as missing rather than backfilled with an old one, because these numbers get used
      to make safety decisions.
    </p>
    <p class="intro">
      <a href="/data/trails-index.json" style="color:#58a6ff">trails-index.json</a> (all trails)
      &nbsp;·&nbsp; <code style="color:#8b949e">/data/conditions/{{slug}}.json</code> per trail
      &nbsp;·&nbsp; <a href="/scoring" style="color:#58a6ff">how the score is computed</a>
    </p>

    <div class="section-title">3. Trailhead monthly climate normals, 2015–2024</div>
    <p class="intro">
      Average high, average low, and wet-day count by month for {n_climate} trailheads, computed
      from ERA5 reanalysis at the trail's own coordinates. The point is the coordinates: a
      national gridded normal will tell you about the nearest town, which is frequently several
      thousand feet below the trail and a different month-by-month regime entirely.
    </p>
    <p class="intro">
      <a href="/{CLIMATE_CSV}" style="color:#58a6ff">normals.csv</a> (one row per trail per
      month) &nbsp;·&nbsp; <code style="color:#8b949e">/data/climate/{{slug}}.json</code>
      &nbsp;·&nbsp; fields: <code style="color:#58a6ff">month</code>,
      <code style="color:#58a6ff">avg_high_f</code>, <code style="color:#58a6ff">avg_low_f</code>,
      <code style="color:#58a6ff">wet_days</code>
    </p>

    <div class="faq">
      <h3>How do I attribute this?</h3>
      <p>&ldquo;Wildfire growth data compiled by alwayshave.fun (CC BY 4.0), from the NIFC/WFIGS
      incident feed&rdquo; is plenty. A link to the page or dataset you used is appreciated and
      lets readers check the current numbers themselves.</p>
      <h3>Where does the underlying data come from, and can you license it to me?</h3>
      <p>Sources: the NIFC/WFIGS Incident Locations feed (US interagency, public domain),
      <a href="https://open-meteo.com" rel="noopener" style="color:#58a6ff">Open-Meteo</a> for
      weather and ERA5 history (CC BY 4.0), <a href="https://www.airnow.gov" rel="noopener"
      style="color:#58a6ff">AirNow</a> for air quality, and NASA FIRMS for satellite fire
      detections. The CC BY 4.0 license here covers <em>our compilation</em> — the daily record,
      the per-trail joins, the scoring — not the upstream feeds, which carry their own terms.
      Cite them too if you use those fields directly.</p>
      <h3>Is there an API?</h3>
      <p>These files are the API. They are static JSON and CSV on a CDN, regenerated every 30
      minutes; fetch them on any schedule you like. There is no versioned endpoint and no
      stability guarantee on field names yet — if you build something on this and want a heads-up
      before anything changes, say so and we will keep a changelog.</p>
      <h3>How accurate is it?</h3>
      <p>It is exactly as accurate as the sources, which is the honest answer. We do not model,
      interpolate, or estimate anything, and we do not correct the feeds. What we add is the time
      dimension — 48 reads a day, stamped — plus the joins between fires, trails, and air
      quality. Where a source disagrees with a ground monitor (smoke models routinely read high
      against ground PM2.5) the raw value is what appears, not a reconciled one.</p>
    </div>

    <footer>
      <a href="/">← All Trails</a> &nbsp;·&nbsp;
      <a href="/fires">Active Fires</a> &nbsp;·&nbsp;
      <a href="/scoring">How We Score</a> &nbsp;·&nbsp;
      <a href="/about">About</a> &nbsp;·&nbsp;
      <a href="/dog-friendly">Dog-Friendly</a><br>
      Data: NIFC/WFIGS, Open-Meteo, AirNow, NASA FIRMS &nbsp;·&nbsp; compilation CC BY 4.0
      &nbsp;·&nbsp; written {stamp} &nbsp;·&nbsp; <a href="/">alwayshave.fun</a>
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

    rows = write_growth_csv(archive)
    write_climate_csv()
    os.makedirs(DATA_OUT_DIR, exist_ok=True)
    with open(os.path.join(DATA_OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_data_html(archive, rows, data.get("updated_at")))
    print(f"  ✓ data/index.html + growth-history.csv ({len(rows)} rows)")


if __name__ == "__main__":
    main()
