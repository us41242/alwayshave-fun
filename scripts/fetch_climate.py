"""
fetch_climate.py — one-time fetch of 10-year monthly weather normals per trail
from the Open-Meteo Historical (ERA5) API. Output: data/climate/{slug}.json
with 12 rows of {month, avg_high_f, avg_low_f, wet_days} that build_static.py
renders as the "Typical Weather by Month" table on every trail page.

Normals don't change — run once (or when trails are added). Not part of the
30-min pipeline. Free tier: 10k calls/day; this uses 1 call per trail.

  python scripts/fetch_climate.py            # fetch trails missing a climate file
  python scripts/fetch_climate.py --force    # refetch everything
"""
import glob, json, os, sys, time, urllib.request
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COND_DIR = os.path.join(ROOT, "data", "conditions")
OUT_DIR = os.path.join(ROOT, "data", "climate")
API = ("https://archive-api.open-meteo.com/v1/archive"
       "?latitude={lat}&longitude={lng}"
       "&start_date=2015-01-01&end_date=2024-12-31"
       "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
       "&temperature_unit=fahrenheit&precipitation_unit=inch&timezone=UTC")
WET_DAY_IN = 0.04  # NOAA threshold for a "wet day" (>= 0.01 in is trace; 0.04 ≈ measurable rain)


def fetch(slug, lat, lng):
    with urllib.request.urlopen(API.format(lat=lat, lng=lng), timeout=60) as r:
        d = json.load(r)["daily"]
    highs, lows, wet, days = (defaultdict(float), defaultdict(float),
                              defaultdict(int), defaultdict(int))
    for date, hi, lo, pr in zip(d["time"], d["temperature_2m_max"],
                                d["temperature_2m_min"], d["precipitation_sum"]):
        if hi is None or lo is None:
            continue
        m = int(date[5:7])
        days[m] += 1
        highs[m] += hi
        lows[m] += lo
        if (pr or 0) >= WET_DAY_IN:
            wet[m] += 1
    years = 10
    return {
        "slug": slug,
        "source": "Open-Meteo ERA5 historical, 2015-2024",
        "months": [
            {"month": m,
             "avg_high_f": round(highs[m] / days[m]),
             "avg_low_f": round(lows[m] / days[m]),
             "wet_days": round(wet[m] / years)}
            for m in range(1, 13) if days[m]
        ],
    }


def main():
    force = "--force" in sys.argv
    os.makedirs(OUT_DIR, exist_ok=True)
    done = fail = 0
    for path in sorted(glob.glob(f"{COND_DIR}/*.json")):
        d = json.load(open(path))
        slug, lat, lng = d.get("slug"), d.get("lat"), d.get("lng")
        if not (slug and lat and lng):
            continue
        out = os.path.join(OUT_DIR, f"{slug}.json")
        if os.path.exists(out) and not force:
            continue
        try:
            data = fetch(slug, lat, lng)
            assert len(data["months"]) == 12, f"{slug}: {len(data['months'])} months"
            json.dump(data, open(out, "w"), indent=1)
            print(f"  ✓ {slug}")
            done += 1
        except Exception as e:
            print(f"  ✗ {slug}: {e}")
            fail += 1
        time.sleep(8)  # archive API rate-limits bursts hard (429 at ~1s spacing)
    print(f"\nDone — {done} fetched, {fail} failed → {OUT_DIR}/")


if __name__ == "__main__":
    main()
