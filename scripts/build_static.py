"""
build_static.py — Generate pre-rendered HTML per trail for SEO.

For each trail, reads conditions JSON and injects real title, canonical,
meta description, OG tags, Twitter tags, and schema.org JSON-LD directly
into the HTML <head> — no JavaScript required for Google to read them.

The JS still runs on page load and updates live data for users.
Google sees complete, unique, correct metadata immediately.

Output: generated/{state}/{slug}.html
Worker checks these first; falls back to trail.html if missing.
"""

import os
import json
import glob
import re
import html as html_lib
from datetime import datetime, timezone

BASE_URL  = "https://alwayshave.fun"
DATA_DIR  = "data/conditions"
CLIMATE_DIR = "data/climate"
TMPL_PATH = "trail.html"
OUT_DIR   = "generated"
ARTICLES_DIR = "articles"

STATE_NAMES = {
    "NV": "Nevada", "UT": "Utah", "AZ": "Arizona",
    "CO": "Colorado", "CA": "California", "NM": "New Mexico"
}

# Authorial persona per state (see AUTONOMY.md "Personas")
PERSONAS = {"CA": "Olivia", "CO": "John"}  # default: Jake


def aqi_category(aqi):
    if aqi is None: return "Unknown"
    if aqi <= 50:   return "Good"
    if aqi <= 100:  return "Moderate"
    if aqi <= 150:  return "Unhealthy for Sensitive Groups"
    if aqi <= 200:  return "Unhealthy"
    if aqi <= 300:  return "Very Unhealthy"
    return "Hazardous"


def build_meta(d):
    """Build all SEO strings for a trail."""
    cur       = d.get("current") or {}
    aqi_data  = d.get("aqi") or {}
    fire      = d.get("fire") or {}
    state     = (d.get("state") or "").upper()
    state_lc  = state.lower()
    state_name = STATE_NAMES.get(state, state)
    slug      = d.get("slug", "")
    name      = d.get("name", "")
    park      = d.get("park_name", "")
    score     = d.get("score", 0)
    label     = d.get("score_label", "")
    aqi_val   = aqi_data.get("aqi")
    wind      = cur.get("wind_mph")
    temp      = cur.get("temp_f")
    rain      = cur.get("rain_pct")
    diff      = d.get("difficulty", "")
    miles     = d.get("length_mi", "")
    gain      = d.get("gain_ft", "")
    notes       = (d.get("notes") or "").strip()
    dog         = d.get("dog_friendly", "")
    lat         = d.get("lat", 0)
    lng         = d.get("lng", 0)
    updated     = (d.get("updated_at") or "")[:10]
    # Top-level sunrise/sunset (ISO datetime); fall back to first forecast entry.
    sunrise_iso = d.get("sunrise") or ((d.get("forecast") or [{}])[0].get("sunrise", ""))
    sunset_iso  = d.get("sunset")  or ((d.get("forecast") or [{}])[0].get("sunset",  ""))
    sunrise_hm  = sunrise_iso[11:16] if sunrise_iso and len(sunrise_iso) >= 16 else ""
    sunset_hm   = sunset_iso[11:16]  if sunset_iso  and len(sunset_iso)  >= 16 else ""

    page_url  = f"{BASE_URL}/{state_lc}/{slug}"
    photo_url = f"{BASE_URL}/photos/{slug}/{slug}.jpg"

    # Caution prefix
    alerts = []
    if aqi_val and aqi_val > 100:
        alerts.append(f"AQI {aqi_val} — {aqi_category(aqi_val).lower()}")
    if wind and wind > 25:
        alerts.append(f"winds {wind} mph")
    alert_str = f"⚠️ CAUTION: {', '.join(alerts)}. " if alerts else ""

    # Meta description (dog-friendly flag for Weekend Warrior queries)
    parts = [f"{name} conditions: {label} ({score}/100)."]
    if temp:    parts.append(f"{temp}°F")
    if wind:    parts.append(f"wind {wind} mph")
    if aqi_val: parts.append(f"AQI {aqi_val}")
    if dog == "Yes":
        parts.append("Dogs welcome.")
    elif dog == "No":
        parts.append("No dogs on trail.")
    if sunrise_hm and sunset_hm:
        parts.append(f"Sunrise {sunrise_hm}, sunset {sunset_hm}.")
    meta_desc = f"{alert_str}{' '.join(parts)} Live data updated every 30 min."

    # Page title ("South Kaibab Trail" must not become "... Trail Trail Conditions")
    if name.lower().endswith(" trail"):
        title = f"{name} Conditions — {label} | alwayshave.fun"
    else:
        title = f"{name} Trail Conditions — {label} | alwayshave.fun"

    # Schema
    description = f"{name} in {park}."
    if miles: description += f" {miles} miles"
    if gain:  description += f", {gain} ft gain"
    if diff:  description += f". Difficulty: {diff}."
    if notes: description += f" {notes}"

    additional = [
        {"@type": "PropertyValue", "name": "Difficulty",       "value": str(diff)},
        {"@type": "PropertyValue", "name": "Distance",         "value": f"{miles} miles"},
        {"@type": "PropertyValue", "name": "Elevation Gain",   "value": f"{gain} ft"},
        {"@type": "PropertyValue", "name": "Current Score",    "value": f"{score}/100 — {label}"},
        {"@type": "PropertyValue", "name": "Trail Type",       "value": str(d.get("trail_type", ""))},
    ]
    if aqi_val is not None:
        additional.append({"@type": "PropertyValue", "name": "Air Quality (AQI)", "value": str(aqi_val)})
    if temp is not None:
        additional.append({"@type": "PropertyValue", "name": "Current Temperature", "value": f"{temp}°F"})
    if fire.get("risk_level"):
        additional.append({"@type": "PropertyValue", "name": "Fire Risk", "value": fire["risk_level"].capitalize()})
    if dog in ("Yes", "No"):
        additional.append({"@type": "PropertyValue", "name": "Dog Friendly", "value": dog})
    if sunrise_hm:
        additional.append({"@type": "PropertyValue", "name": "Sunrise (local)", "value": sunrise_hm})
    if sunset_hm:
        additional.append({"@type": "PropertyValue", "name": "Sunset (local)",  "value": sunset_hm})

    # FAQPage — answers high-intent "is X trail safe/open/dog-friendly?" queries
    faq_pairs = []
    cond_bits = []
    if temp is not None: cond_bits.append(f"Temperature: {temp}°F")
    if wind is not None: cond_bits.append(f"wind: {wind} mph")
    if rain is not None: cond_bits.append(f"rain chance: {rain}%")
    faq_pairs.append({
        "q": f"What are the current conditions at {name}?",
        "a": f"As of the latest update, {name} is scoring {score}/100 ({label}). "
             + (", ".join(cond_bits) + ". " if cond_bits else "")
             + "Data is refreshed every 30 minutes."
    })
    faq_pairs.append({
        "q": f"Is {name} dog-friendly?",
        "a": (f"Yes, dogs are welcome on {name}. Leash required."
              if dog == "Yes" else
              f"No, dogs are not permitted on {name}.")
        if dog in ("Yes", "No") else
        f"Check the park's current pet policy before visiting {name}."
    })
    faq_pairs.append({
        "q": f"How difficult is {name}?",
        "a": f"{name} is rated {diff}. "
             f"The trail is {miles} miles with {gain} ft of elevation gain."
        if diff and miles else f"{name} difficulty: {diff or 'see trail details'}."
    })
    if aqi_val is not None:
        faq_pairs.append({
            "q": f"What is the air quality (AQI) at {name} today?",
            "a": f"Current AQI at {name} is {aqi_val} — {aqi_category(aqi_val)}. "
                 f"AQI under 50 is Good; 51-100 is Moderate; above 100 may require a mask."
        })
    faq_pairs.append({
        "q": f"When is the best time to visit {name}?",
        "a": f"The best months to hike {name} are {d.get('best_months', 'spring and fall')}."
        if d.get("best_months") else
        f"Spring and fall typically offer the best conditions at {name}."
    })

    faq_schema = {
        "@type": "FAQPage",
        "@id": f"{page_url}#faq",
        "mainEntity": [
            {
                "@type": "Question",
                "name": p["q"],
                "acceptedAnswer": {"@type": "Answer", "text": p["a"]}
            }
            for p in faq_pairs
        ]
    }

    # amenityFeature surfaces "dogs allowed" as a Schema.org-recognized facility flag —
    # better for AI overviews & rich results than a bare additionalProperty.
    amenity_features = []
    if dog in ("Yes", "No"):
        amenity_features.append({
            "@type": "LocationFeatureSpecification",
            "name": "Dogs allowed",
            "value": dog == "Yes",
        })

    sports_loc = {
        "@type": "SportsActivityLocation",
        "@id": page_url,
        "name": name,
        "description": description.strip(),
        "url": page_url,
        "image": photo_url,
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": float(lat),
            "longitude": float(lng)
        },
        "containedInPlace": {"@type": "Park", "name": park},
        "additionalProperty": additional,
        "dateModified": updated
    }
    if amenity_features:
        sports_loc["amenityFeature"] = amenity_features

    schema = {
        "@context": "https://schema.org",
        "@graph": [
            sports_loc,
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home",       "item": BASE_URL},
                    {"@type": "ListItem", "position": 2, "name": state_name,   "item": f"{BASE_URL}/{state_lc}"},
                    {"@type": "ListItem", "position": 3, "name": name,         "item": page_url}
                ]
            },
            faq_schema
        ]
    }

    return {
        "title":      title,
        "meta_desc":  meta_desc,
        "page_url":   page_url,
        "photo_url":  photo_url,
        "state_lc":   state_lc,
        "state_name": state_name,
        "schema":     json.dumps(schema, indent=2),
        "faq_pairs":  faq_pairs,
    }


def inject_head(html, m):
    # Use lambda replacements so re.sub does not interpret backslashes in JSON schema.
    subs = [
        (r'<title[^>]*>.*?</title>',
         f'<title id="page-title">{m["title"]}</title>'),
        (r'<meta name="description"[^>]*>',
         f'<meta name="description" id="page-desc" content="{m["meta_desc"]}">'),
        (r'<link rel="canonical"[^>]*>',
         f'<link rel="canonical" id="canonical" href="{m["page_url"]}">'),
        (r'<meta property="og:title"[^>]*>',
         f'<meta property="og:title" id="og-title" content="{m["title"]}">'),
        (r'<meta property="og:description"[^>]*>',
         f'<meta property="og:description" id="og-desc" content="{m["meta_desc"]}">'),
        (r'<meta property="og:url"[^>]*>',
         f'<meta property="og:url" id="og-url" content="{m["page_url"]}">'),
        (r'<meta property="og:image"[^>]*>',
         f'<meta property="og:image" id="og-image" content="{m["photo_url"]}">'),
        (r'<meta name="twitter:title"[^>]*>',
         f'<meta name="twitter:title" id="tw-title" content="{m["title"]}">'),
        (r'<meta name="twitter:description"[^>]*>',
         f'<meta name="twitter:description" id="tw-desc" content="{m["meta_desc"]}">'),
        (r'<meta name="twitter:image"[^>]*>',
         f'<meta name="twitter:image" id="tw-image" content="{m["photo_url"]}">'),
    ]

    for pattern, replacement in subs:
        repl = replacement  # capture for lambda closure
        html = re.sub(pattern, lambda _m, r=repl: r, html, flags=re.DOTALL | re.IGNORECASE)

    # Inject schema before </head> — trail.html has no existing ld+json block
    schema_tag = f'<script type="application/ld+json" id="schema-ld">{m["schema"]}</script>\n'
    html = html.replace('</head>', schema_tag + '</head>', 1)

    return html


def esc(v):
    return html_lib.escape(str(v), quote=True)


def replace_once(html, old, new, slug, anchor):
    """Exact-string replacement; warn loudly if the template anchor is missing
    so a template refactor can't silently regress the static render."""
    if old not in html:
        print(f"  ! anchor missing for {slug}: {anchor}")
        return html
    return html.replace(old, new, 1)


def inject_body(html, d, m, siblings):
    """Render the trail's real content into the HTML body at build time.

    Google previously received this page as an empty JS shell ('Loading trail
    conditions…') and refused to index it. Every value below is also
    re-rendered client-side by trail.html's render() — the JS overwrites these
    nodes with fresher data on load, so hydration stays consistent.
    """
    cur      = d.get("current") or {}
    aqi_data = d.get("aqi") or {}
    fire     = d.get("fire") or {}
    slug     = d.get("slug", "")
    name     = esc(d.get("name", ""))
    score    = d.get("score", 0)
    label    = esc(d.get("score_label", ""))
    state_lc = m["state_lc"]
    state_nm = esc(m["state_name"])
    updated  = (d.get("updated_at") or "")[:16].replace("T", " ")

    def rep(old, new, anchor):
        nonlocal html
        html = replace_once(html, old, new, slug, anchor)

    # ── Nav / breadcrumb / hero ──
    rep('<a href="/" id="nav-back" class="nav-back">← All Trails</a>',
        f'<a href="/{state_lc}" id="nav-back" class="nav-back">← {state_nm} Trails</a>', 'nav-back')
    rep('<a href="#" id="bc-state">State</a>',
        f'<a href="/{state_lc}" id="bc-state">{state_nm}</a>', 'bc-state')
    rep('<span id="bc-trail">Trail</span>',
        f'<span id="bc-trail">{name}</span>', 'bc-trail')
    rep('<h1 class="hero-trail-name" id="trail-name">—</h1>',
        f'<h1 class="hero-trail-name" id="trail-name">{name}</h1>', 'trail-name')
    rep('<span class="num" id="score-num">—</span>',
        f'<span class="num" id="score-num">{score}</span>', 'score-num')
    rep('<span class="score-pill-label" id="score-label">—</span>',
        f'<span class="score-pill-label" id="score-label">{label}</span>', 'score-label')
    rep('<span class="score-pill-updated" id="score-updated">—</span>',
        f'<span class="score-pill-updated" id="score-updated">Updated {updated} UTC</span>', 'score-updated')

    qs = []
    if cur.get("temp_f")   is not None: qs.append(f'🌡 {cur["temp_f"]}°F')
    if cur.get("wind_mph") is not None: qs.append(f'🌬 {cur["wind_mph"]} mph')
    if aqi_data.get("aqi") is not None: qs.append(f'💨 AQI {aqi_data["aqi"]}')
    rep('<div class="hero-quick-stats" id="hero-quick-stats"></div>',
        '<div class="hero-quick-stats" id="hero-quick-stats">'
        + ''.join(f'<div class="hero-stat">{s}</div>' for s in qs)
        + '</div>', 'hero-quick-stats')

    rep('<div class="score-bar-fill" id="score-bar" style="width:0%"></div>',
        f'<div class="score-bar-fill" id="score-bar" style="width:{score}%"></div>', 'score-bar')

    # ── Metric cards ──
    def metric(el_id, cls, value, anchor):
        rep(f'<div class="{cls}" id="{el_id}">—</div>',
            f'<div class="{cls}" id="{el_id}">{value}</div>', anchor)

    if cur.get("temp_f") is not None:
        metric('m-temp', 'metric-value', f'{cur["temp_f"]}°F', 'm-temp')
    if cur.get("feels_like_f") is not None:
        rep('<div class="metric-sub"  id="m-feels">—</div>',
            f'<div class="metric-sub"  id="m-feels">Feels like {cur["feels_like_f"]}°F</div>', 'm-feels')
    if aqi_data.get("aqi") is not None:
        metric('m-aqi', 'metric-value', aqi_data["aqi"], 'm-aqi')
        cat = esc(aqi_data.get("category") or aqi_category(aqi_data["aqi"]))
        if aqi_data.get("pollutant"):
            cat += f' · {esc(aqi_data["pollutant"])}'
        rep('<div class="metric-sub"  id="m-aqi-cat">—</div>',
            f'<div class="metric-sub"  id="m-aqi-cat">{cat}</div>', 'm-aqi-cat')
    if cur.get("wind_mph") is not None:
        metric('m-wind', 'metric-value', f'{cur["wind_mph"]} mph', 'm-wind')
    if cur.get("gusts_mph") is not None:
        rep('<div class="metric-sub"  id="m-gusts">—</div>',
            f'<div class="metric-sub"  id="m-gusts">Gusts {cur["gusts_mph"]} mph</div>', 'm-gusts')
    if cur.get("rain_pct") is not None:
        metric('m-rain', 'metric-value', f'{cur["rain_pct"]}%', 'm-rain')

    # ── Trail info ──
    stats = [
        ('t-difficulty', esc(d.get("difficulty") or "—")),
        ('t-length',     f'{d.get("length_mi")} mi' if d.get("length_mi") else '—'),
        ('t-gain',       f'{int(float(d["gain_ft"])):,} ft' if d.get("gain_ft") else '—'),
        ('t-type',       esc(d.get("trail_type") or "—")),
        ('t-months',     esc(d.get("best_months") or "—")),
        ('t-park',       esc(d.get("park_name") or "—")),
    ]
    for el_id, val in stats:
        rep(f'<span class="trail-stat-value" id="{el_id}">—</span>',
            f'<span class="trail-stat-value" id="{el_id}">{val}</span>', el_id)

    # ── Status list (honest fire risk from FIRMS data, not a hardcoded 'Low') ──
    status = (d.get("status") or "Unknown")
    dot = 'dot-green' if status.lower() == 'open' else 'dot-yellow' if status.lower() == 'seasonal' else 'dot-red'
    items = [f'<li class="status-item"><span class="dot {dot}"></span><span>Trail: {esc(status)}</span></li>']
    risk = (fire.get("risk_level") or "").lower()
    if risk:
        fdot = 'dot-green' if risk == 'low' else 'dot-yellow' if risk in ('moderate', 'medium') else 'dot-red'
        items.append(f'<li class="status-item"><span class="dot {fdot}"></span><span>Fire Risk: {esc(risk.capitalize())} (NASA FIRMS)</span></li>')
    river = d.get("river") or {}
    if river.get("cfs") is not None:
        rstage = (river.get("stage") or "").lower()
        rdot = 'dot-green' if rstage in ('low', 'normal') else 'dot-yellow' if rstage == 'high' else 'dot-red'
        rlabel = {'low': 'Low', 'normal': 'Normal', 'high': 'High — use caution', 'flood': 'FLOOD — do not enter'}.get(rstage, rstage.capitalize())
        items.append(f'<li class="status-item"><span class="dot {rdot}"></span>'
                     f'<span>Water level: {river["cfs"]:,} cfs — {esc(rlabel)} (USGS {esc(river.get("gauge_id") or "gauge")})</span></li>')
    items.append('<li class="status-item"><span class="dot dot-gray"></span><span>Campground: Check official alerts</span></li>')
    rep('<ul class="status-list" id="status-list"></ul>',
        f'<ul class="status-list" id="status-list">{"".join(items)}</ul>', 'status-list')

    # ── 5-day forecast (same markup render() produces) ──
    cards = []
    for day in (d.get("forecast") or []):
        try:
            dt = datetime.strptime(day["date"], "%Y-%m-%d")
        except (KeyError, ValueError):
            continue
        sr = (day.get("sunrise") or "")[11:16]
        ss = (day.get("sunset") or "")[11:16]
        sun = f'<div class="forecast-sun" title="Sunrise / Sunset">☀️ {sr}–{ss}</div>' if sr else ''
        cards.append(
            f'<div class="forecast-day">'
            f'<div class="forecast-label">{dt.strftime("%a")}<br>{dt.month}/{dt.day}</div>'
            f'<div class="forecast-chart"><div class="bar-bg"><div class="bar-fill" style="height:{max(day.get("rain_pct", 0), 3)}%"></div></div></div>'
            f'<div class="forecast-pct">{day.get("rain_pct", "—")}%</div>'
            f'<div class="forecast-high">{day.get("high_f", "—")}°</div>'
            f'<div class="forecast-low">{day.get("low_f", "—")}°</div>'
            f'<div class="forecast-uv">UV {day.get("uv", "—")}</div>'
            f'{sun}</div>'
        )
    if cards:
        rep('<div class="forecast-grid" id="forecast-grid"></div>',
            f'<div class="forecast-grid" id="forecast-grid">{"".join(cards)}</div>', 'forecast-grid')

    # ── Notes ──
    notes = (d.get("notes") or "").strip()
    if notes:
        rep('<p id="trail-notes" style="font-size:0.9rem;line-height:1.65">—</p>',
            f'<p id="trail-notes" style="font-size:0.9rem;line-height:1.65">{esc(notes)}</p>', 'trail-notes')

    # ── FAQ (visible copy of the FAQPage schema — schema without visible
    #     content violates Google's structured-data guidelines) ──
    faq_html = ''.join(
        f'<div class="faq-item" style="margin-bottom:0.9rem">'
        f'<h3 style="font-size:0.95rem;margin-bottom:0.25rem">{esc(p["q"])}</h3>'
        f'<p style="font-size:0.9rem;line-height:1.6;color:var(--text-muted)">{esc(p["a"])}</p></div>'
        for p in m["faq_pairs"]
    )
    faq_card = (f'<div class="card" id="faq-card">'
                f'<div class="card-title">Frequently Asked Questions</div>{faq_html}</div>\n\n    ')

    # ── Related trails (crawlable internal links, freshest scores first) ──
    related_card = ''
    if siblings:
        lis = ''.join(
            f'<li class="status-item" style="margin-bottom:0.4rem">'
            f'<a href="/{state_lc}/{s["slug"]}" style="color:var(--brand);font-weight:600">{esc(s["name"])}</a>'
            f'&nbsp;— {s["score"]}/100 {esc(s["score_label"])}</li>'
            for s in siblings
        )
        related_card = (f'<div class="card" id="related-card">'
                        f'<div class="card-title">More {state_nm} Trails</div>'
                        f'<ul class="status-list">{lis}</ul>'
                        f'<p style="margin-top:0.6rem;font-size:0.9rem">'
                        f'<a href="/{state_lc}" style="color:var(--brand);font-weight:600">All {state_nm} trail conditions →</a></p>'
                        f'</div>\n\n    ')

    # ── Typical weather by month (10-yr normals; targets "{trail} weather in
    #     {month}" / "best time to hike {trail}" queries) ──
    climate_card = ''
    cpath = os.path.join(CLIMATE_DIR, f"{slug}.json")
    if os.path.exists(cpath):
        with open(cpath) as cf:
            clim = json.load(cf)
        month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
                       'August', 'September', 'October', 'November', 'December']
        rows = ''.join(
            f'<tr><td style="padding:0.3rem 0.5rem">{month_names[r["month"] - 1]}</td>'
            f'<td style="padding:0.3rem 0.5rem;text-align:right">{r["avg_high_f"]}°F</td>'
            f'<td style="padding:0.3rem 0.5rem;text-align:right">{r["avg_low_f"]}°F</td>'
            f'<td style="padding:0.3rem 0.5rem;text-align:right">{r["wet_days"]}</td></tr>'
            for r in clim.get("months", [])
        )
        best = (f'<p style="font-size:0.9rem;line-height:1.6;margin-bottom:0.6rem">'
                f'Best months to hike {name}: <strong>{esc(d["best_months"])}</strong>.</p>'
                if d.get("best_months") else '')
        climate_card = (
            f'<div class="card" id="climate-card">'
            f'<div class="card-title">Typical Weather by Month at {name}</div>{best}'
            f'<table style="width:100%;border-collapse:collapse;font-size:0.9rem">'
            f'<thead><tr style="color:var(--text-muted);text-align:right">'
            f'<th style="padding:0.3rem 0.5rem;text-align:left">Month</th>'
            f'<th style="padding:0.3rem 0.5rem">Avg High</th>'
            f'<th style="padding:0.3rem 0.5rem">Avg Low</th>'
            f'<th style="padding:0.3rem 0.5rem">Wet Days</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>'
            f'<p style="margin-top:0.6rem;font-size:0.8rem;color:var(--text-muted)">'
            f'{esc(clim.get("source", ""))}. Historical averages — check the live '
            f'forecast above before you go.</p></div>\n\n    ')

    rep('<!-- ACTION LINKS -->', faq_card + climate_card + related_card + '<!-- ACTION LINKS -->', 'faq/related insert')

    # ── Persona article link (crawlable; JS skips insertion when #jakes-take exists) ──
    if os.path.exists(os.path.join(ARTICLES_DIR, f"{slug}.html")):
        persona = PERSONAS.get((d.get("state") or "").upper(), "Jake")
        rep('<div class="action-links" id="action-links"></div>',
            '<div class="action-links" id="action-links"></div>\n    '
            f'<a id="jakes-take" class="jakes-take-link" href="/articles/{slug}">'
            f'📝 {persona}&#8217;s Take on {name} — full conditions report →</a>',
            'article link')

    # ── Content visible without JS; render() re-applies these classes on load ──
    rep('<div id="loading" class="loading-state" role="status" aria-live="polite">',
        '<div id="loading" class="loading-state hidden" role="status" aria-live="polite">', 'loading hide')
    rep('<div class="hero-image hidden" id="hero-image">',
        '<div class="hero-image" id="hero-image">', 'hero unhide')
    rep('<main id="content" class="hidden">',
        '<main id="content">', 'content unhide')

    return html


def pick_siblings(d, conditions, limit=6):
    """Same-state trails, best current score first."""
    state = (d.get("state") or "").upper()
    sibs = [
        {"slug": s.get("slug"), "name": s.get("name"), "score": s.get("score", 0),
         "score_label": s.get("score_label", "")}
        for s in conditions.values()
        if (s.get("state") or "").upper() == state and s.get("slug") != d.get("slug")
    ]
    sibs.sort(key=lambda s: s["score"], reverse=True)
    return sibs[:limit]


def load_all_conditions():
    results = {}
    for path in glob.glob(f"{DATA_DIR}/*.json"):
        try:
            with open(path) as f:
                d = json.load(f)
            slug = d.get("slug")
            if slug:
                results[slug] = d
        except Exception:
            pass
    return results


def main():
    with open(TMPL_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    conditions = load_all_conditions()
    generated  = 0
    errors     = 0

    for slug, d in conditions.items():
        state = (d.get("state") or "").lower()
        if not state or not slug:
            continue
        try:
            m    = build_meta(d)
            html = inject_head(template, m)
            html = inject_body(html, d, m, pick_siblings(d, conditions))

            out_dir  = os.path.join(OUT_DIR, state)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f"{slug}.html")

            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html)

            generated += 1
            print(f"  ✓ {state}/{slug}.html")
        except Exception as e:
            print(f"  ✗ {slug}: {e}")
            errors += 1

    print(f"\nDone — {generated} pages generated, {errors} errors → {OUT_DIR}/")


if __name__ == "__main__":
    main()
