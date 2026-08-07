"""
fetch_fires.py — NASA FIRMS fire hotspot data for trail proximity scoring.

Queries the FIRMS NRT (Near Real-Time) VIIRS I-Band 375m dataset for the
Southwest/Mountain West bounding box, then computes fire proximity for every
trail in seeds/trails.csv and writes per-trail JSON to data/fires/{slug}.json.

Risk → score contribution mapping (feeds into fetch_conditions.py):
  low      — no fires within 100km  → 20 pts
  moderate — 1+ fires 50–100km      → 12 pts
  elevated — 1+ fires within 50km   → 6 pts
  high     — 1+ fires within 20km   → 0 pts
"""

import os
import csv
import json
import math
import requests
from datetime import datetime, timezone, timedelta

NASA_FIRMS_KEY = os.environ.get("NASA_FIRMS_KEY", "")

# Bounding box covering NV, UT, AZ, CO, CA, NM (west, south, east, north)
BBOX = "-124,32,-102,42"

# FIRMS day_range counts UTC *calendar days* (1 = today only), so a run just
# after 00:00Z would see an almost-empty dataset. Pull 2 days and filter to a
# true trailing-24h window in fetch_firms_csv().
LOOK_BACK_DAYS = 2

# All three VIIRS satellites — SNPP alone demonstrably misses passes the
# NOAA birds catch (verified 2026-07-25/26).
DATASETS = ["VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"]

# NIFC/WFIGS current wildfire incidents (public ArcGIS, no key). Gives the
# nearest fire a name, size, and containment instead of an anonymous pixel.
WFIGS_URL = ("https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/"
             "WFIGS_Incident_Locations_Current/FeatureServer/0/query")

COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
           "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def load_trails(path="seeds/trails.csv"):
    trails = []
    with open(path, newline="", encoding="utf-8") as f:
        next(f)  # skip header comment row
        reader = csv.DictReader(f)
        for row in reader:
            trails.append(row)
    return trails


def fetch_firms_csv():
    """Download FIRMS hotspot CSVs (all VIIRS satellites), trailing 24h only."""
    if not NASA_FIRMS_KEY:
        print("  WARNING: NASA_FIRMS_KEY not set — skipping live fire fetch")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    hotspots = []
    for dataset in DATASETS:
        url = (
            f"https://firms.modaps.eosdis.nasa.gov/api/area/csv"
            f"/{NASA_FIRMS_KEY}/{dataset}/{BBOX}/{LOOK_BACK_DAYS}"
        )
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            text = r.text.strip()
            if not text or text.startswith("Error") or text.startswith("You"):
                print(f"  FIRMS {dataset} returned non-data response: {text[:120]}")
                continue
            lines = text.splitlines()
            if len(lines) < 2:
                continue
            count = 0
            for row in csv.DictReader(lines):
                try:
                    acq = datetime.strptime(
                        f"{row['acq_date']} {int(row['acq_time']):04d}",
                        "%Y-%m-%d %H%M").replace(tzinfo=timezone.utc)
                    if acq < cutoff:
                        continue
                    hotspots.append({
                        "lat": float(row.get("latitude", 0)),
                        "lng": float(row.get("longitude", 0)),
                        "frp": float(row.get("frp", 0)),      # fire radiative power (MW)
                        "confidence": row.get("confidence", ""),
                    })
                    count += 1
                except (ValueError, KeyError):
                    continue
            print(f"  FIRMS {dataset}: {count} hotspots in last 24h")
        except Exception as e:
            print(f"  FIRMS {dataset} fetch error: {e}")
    print(f"  FIRMS total: {len(hotspots)} hotspots")
    return hotspots


def fetch_wfigs_incidents():
    """Named active wildfire incidents from NIFC/WFIGS inside the bounding box."""
    west, south, east, north = BBOX.split(",")
    params = {
        "where": "IncidentTypeCategory IN ('WF','CX') AND FireOutDateTime IS NULL",
        "geometry": f"{west},{south},{east},{north}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326", "outSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "IncidentName,IncidentSize,DiscoveryAcres,PercentContained,"
                     "FireCause,FireCauseGeneral,ModifiedOnDateTime_dt,"
                     "POOState,TotalIncidentPersonnel,FireDiscoveryDateTime",
        "returnGeometry": "true",
        "f": "json",
    }
    try:
        r = requests.get(WFIGS_URL, params=params, timeout=30)
        r.raise_for_status()
        d = r.json()
        if "error" in d:
            print(f"  WFIGS error response: {d['error'].get('message')}")
            return []
        incidents = []
        for feat in d.get("features", []):
            a = feat.get("attributes") or {}
            g = feat.get("geometry") or {}
            if g.get("y") is None or not a.get("IncidentName"):
                continue
            mod = a.get("ModifiedOnDateTime_dt")
            name = str(a["IncidentName"]).strip()
            if name.isupper():  # some dispatch systems shout ("MATEO" → "Mateo")
                name = name.title()
            disc = a.get("FireDiscoveryDateTime")
            incidents.append({
                "name": name,
                "acres": a.get("IncidentSize") if a.get("IncidentSize") is not None else a.get("DiscoveryAcres"),
                "containment_pct": a.get("PercentContained"),
                "cause": a.get("FireCauseGeneral") or a.get("FireCause") or None,
                "lat": g["y"],
                "lng": g["x"],
                "updated": datetime.fromtimestamp(mod / 1000, timezone.utc).isoformat() if mod else None,
                # /fires page only — nearest_incident() ignores these
                "state": (a.get("POOState") or "").replace("US-", "") or None,
                "personnel": a.get("TotalIncidentPersonnel"),
                "discovered": datetime.fromtimestamp(disc / 1000, timezone.utc).isoformat() if disc else None,
            })
        print(f"  WFIGS: {len(incidents)} active incidents in region")
        return incidents
    except Exception as e:
        print(f"  WFIGS fetch error: {e}")
        return []


def nearest_incident(incidents, trail_lat, trail_lng, max_km=100):
    """Nearest named incident within max_km (matches the risk-band radius), or None."""
    best, best_d = None, max_km
    for inc in incidents:
        d = haversine_km(trail_lat, trail_lng, inc["lat"], inc["lng"])
        if d <= best_d:
            best, best_d = inc, d
    if not best:
        return None
    bearing = math.degrees(math.atan2(
        math.sin(math.radians(best["lng"] - trail_lng)) * math.cos(math.radians(best["lat"])),
        math.cos(math.radians(trail_lat)) * math.sin(math.radians(best["lat"]))
        - math.sin(math.radians(trail_lat)) * math.cos(math.radians(best["lat"]))
        * math.cos(math.radians(best["lng"] - trail_lng))))
    direction = COMPASS[round(bearing % 360 / 22.5) % 16]
    return {**{k: best[k] for k in ("name", "acres", "containment_pct", "cause", "updated")},
            "distance_km": round(best_d, 1), "direction": direction}


def haversine_km(lat1, lng1, lat2, lng2):
    """Great-circle distance in km."""
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def classify_risk(hotspots, trail_lat, trail_lng):
    """
    Return (risk_level, nearest_km, count_20km, count_50km, count_100km, score_pts).
    Filters to high-confidence detections only to reduce false positives.
    """
    high_conf = [h for h in hotspots if str(h.get("confidence", "")).lower() in ("high", "h", "nominal", "n", "100", "99", "98", "97", "96", "95")]
    # Fall back to all hotspots if no high-confidence ones
    pool = high_conf if high_conf else hotspots

    nearest_km = float("inf")
    count_20  = 0
    count_50  = 0
    count_100 = 0

    for h in pool:
        d = haversine_km(trail_lat, trail_lng, h["lat"], h["lng"])
        if d < nearest_km:
            nearest_km = d
        if d <= 20:
            count_20 += 1
        if d <= 50:
            count_50 += 1
        if d <= 100:
            count_100 += 1

    if nearest_km == float("inf"):
        nearest_km = None

    if count_20 > 0:
        risk = "high"
        pts  = 0
    elif count_50 > 0:
        risk = "elevated"
        pts  = 6
    elif count_100 > 0:
        risk = "moderate"
        pts  = 12
    else:
        risk = "low"
        pts  = 20

    return {
        "risk_level":        risk,
        "score_pts":         pts,
        "nearest_fire_km":   round(nearest_km, 1) if nearest_km is not None else None,
        "fire_count_20km":   count_20,
        "fire_count_50km":   count_50,
        "fire_count_100km":  count_100,
    }


def process_trail(trail, hotspots, incidents):
    slug = trail.get("slug", "").strip()
    lat  = trail.get("lat", "").strip()
    lng  = trail.get("lng", "").strip()

    if not slug or not lat or not lng:
        return

    trail_lat = float(lat)
    trail_lng = float(lng)

    risk_data = classify_risk(hotspots, trail_lat, trail_lng)

    output = {
        "slug":       slug,
        "name":       trail.get("name", ""),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        **risk_data,
        "nearest_incident": nearest_incident(incidents, trail_lat, trail_lng),
    }

    out_path = f"data/fires/{slug}.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    label = risk_data["risk_level"].upper()
    nearest = risk_data.get("nearest_fire_km")
    dist_str = f"{nearest}km" if nearest else "no fires nearby"
    print(f"    {slug}: {label} ({dist_str})")


def write_summary(trails, hotspots):
    """Write a region-level summary used by the frontend fire/smoke map."""
    regions = {}
    for trail in trails:
        region = trail.get("region", "Unknown")
        slug   = trail.get("slug", "").strip()
        lat    = trail.get("lat", "").strip()
        lng    = trail.get("lng", "").strip()
        if not lat or not lng:
            continue
        risk = classify_risk(hotspots, float(lat), float(lng))
        regions.setdefault(region, []).append(risk["score_pts"])

    summary = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_hotspots": len(hotspots),
        "regions": {}
    }
    for region, pts_list in regions.items():
        avg_pts = sum(pts_list) / len(pts_list)
        if avg_pts >= 18:   level = "low"
        elif avg_pts >= 10: level = "moderate"
        elif avg_pts >= 3:  level = "elevated"
        else:               level = "high"
        summary["regions"][region] = {
            "risk_level":       level,
            "avg_score_pts":    round(avg_pts, 1),
            "trails_monitored": len(pts_list),
        }

    with open("data/fires/summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Summary written → data/fires/summary.json")


def main():
    print(f"fetch_fires.py — {datetime.now(timezone.utc).isoformat()}")
    trails    = load_trails()
    hotspots  = fetch_firms_csv()
    incidents = fetch_wfigs_incidents()

    # Full incident list — feeds the /fires page (build_fires.py). Same query,
    # no extra API cost; it used to be thrown away after the per-trail match.
    with open("data/fires/incidents.json", "w") as f:
        json.dump({
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "source": "NIFC/WFIGS Incident Locations (current)",
            "count": len(incidents),
            "incidents": sorted(incidents, key=lambda i: i.get("acres") or 0, reverse=True),
        }, f, indent=2)

    print(f"  Processing {len(trails)} trails against {len(hotspots)} hotspots…")
    for trail in trails:
        process_trail(trail, hotspots, incidents)

    write_summary(trails, hotspots)
    print("Done.")


if __name__ == "__main__":
    main()
