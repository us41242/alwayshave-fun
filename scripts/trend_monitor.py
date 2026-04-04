"""
trend_monitor.py — Weekly Google Trends snapshot for alwayshave.fun

Tracks interest over time for key trail names + condition queries.
Writes to data/trends/YYYY-WW.json for historical comparison.

Uses pytrends (unofficial Google Trends client). Rate-limited by Google —
runs with backoff and is marked continue-on-error in the workflow.
"""

import json
import os
import time
import csv
import random
from datetime import datetime, timezone

try:
    from pytrends.request import TrendReq
except ImportError:
    print("pytrends not installed — skipping trend monitor")
    exit(0)

DATA_DIR = "data/trends"
os.makedirs(DATA_DIR, exist_ok=True)

# Core queries to track weekly
TRACKED_QUERIES = [
    # Brand + trail condition intent
    "trail conditions today",
    "hiking conditions this weekend",
    "trail air quality",
    "hiking aqi today",
    # Dog-friendly
    "dog friendly hikes",
    "hiking with dogs trail conditions",
    # Specific high-traffic trails we cover
    "Angels Landing conditions",
    "Bright Angel Trail conditions",
    "Zion Narrows conditions",
    "Red Rock Canyon conditions",
    "Half Dome conditions",
    # Overlander
    "4WD trail conditions",
    "off road trail conditions",
    # Fire/smoke
    "hiking wildfire smoke",
    "trail smoke conditions",
]

GEO_REGIONS = ["US-NV", "US-UT", "US-AZ", "US-CO", "US-CA"]


def safe_request(fn, retries=3, wait=10):
    for i in range(retries):
        try:
            return fn()
        except Exception as e:
            if i < retries - 1:
                sleep_time = wait * (i + 1) + random.uniform(0, 5)
                print(f"  Rate limited or error: {e}. Waiting {sleep_time:.0f}s...")
                time.sleep(sleep_time)
            else:
                print(f"  Failed after {retries} attempts: {e}")
                return None


def get_trending_now():
    """Get today's trending searches in US hiking/outdoor states."""
    pytrends = TrendReq(hl="en-US", tz=420, timeout=(10, 30))
    results = {}
    for pn in ["us_nv", "us_ut", "us_az", "us_co", "us_ca"]:
        data = safe_request(lambda: pytrends.trending_searches(pn=pn))
        if data is not None:
            results[pn] = data[0].head(10).tolist()
        time.sleep(random.uniform(3, 7))
    return results


def get_interest_over_time(keywords_batch):
    """Get interest over time for a batch of up to 5 keywords."""
    pytrends = TrendReq(hl="en-US", tz=420, timeout=(10, 60))
    safe_request(lambda: pytrends.build_payload(
        keywords_batch,
        timeframe="today 3-m",
        geo="US"
    ))
    data = safe_request(lambda: pytrends.interest_over_time())
    if data is None or data.empty:
        return {}
    data = data.drop(columns=["isPartial"], errors="ignore")
    # Return last 4 weeks average per keyword
    last4 = data.tail(4)
    return {kw: round(float(last4[kw].mean()), 1) for kw in keywords_batch if kw in last4.columns}


def load_trail_names():
    names = []
    try:
        with open("seeds/trails.csv", newline="", encoding="utf-8") as f:
            next(f)
            reader = csv.DictReader(f)
            for row in reader:
                names.append(row.get("name", "").strip())
    except Exception:
        pass
    return names


def main():
    now  = datetime.now(timezone.utc)
    week = now.strftime("%Y-W%W")
    out  = {
        "week":       week,
        "generated":  now.isoformat(),
        "trending":   {},
        "interest":   {},
        "top_trails": [],
    }

    print(f"Trend monitor — week {week}")

    # 1. Trending searches by state
    print("Fetching trending searches...")
    out["trending"] = get_trending_now()
    time.sleep(random.uniform(5, 10))

    # 2. Interest over time — run in batches of 5 (pytrends limit)
    print("Fetching interest over time...")
    interest = {}
    batches  = [TRACKED_QUERIES[i:i+5] for i in range(0, len(TRACKED_QUERIES), 5)]
    for batch in batches:
        result = get_interest_over_time(batch)
        interest.update(result)
        time.sleep(random.uniform(8, 15))  # be polite to Google

    out["interest"] = dict(sorted(interest.items(), key=lambda x: x[1], reverse=True))

    # 3. Top trails by search interest — helps prioritize which trails to write about
    trail_names = load_trail_names()
    trail_scores = []
    batches = [trail_names[i:i+5] for i in range(0, min(len(trail_names), 30), 5)]
    for batch in batches:
        result = get_interest_over_time(batch)
        for name, score in result.items():
            trail_scores.append({"name": name, "interest": score})
        time.sleep(random.uniform(8, 15))

    trail_scores.sort(key=lambda x: x["interest"], reverse=True)
    out["top_trails"] = trail_scores[:10]

    # Write output
    path = f"{DATA_DIR}/{week}.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Trend snapshot saved: {path}")

    # Also write latest.json for easy access
    with open(f"{DATA_DIR}/latest.json", "w") as f:
        json.dump(out, f, indent=2)

    # Summary
    print(f"\nTop trending queries this week:")
    for kw, score in list(out["interest"].items())[:5]:
        print(f"  {score:5.1f}  {kw}")

    if out["top_trails"]:
        print(f"\nTop trail search interest:")
        for t in out["top_trails"][:5]:
            print(f"  {t['interest']:5.1f}  {t['name']}")


if __name__ == "__main__":
    main()
