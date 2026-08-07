"""Self-check for build_fires.py — filtering and trail proximity. Run: python3 scripts/test_build_fires.py"""

import build_fires as bf

FIXTURE = {
    "updated_at": "2026-08-07T04:00:00+00:00",
    "incidents": [
        # keep: big, uncontained, in-state
        {"name": "Widemouth 2", "acres": 96702, "containment_pct": 10, "cause": "Natural",
         "lat": 38.7, "lng": -112.4, "state": "UT", "personnel": 540,
         "discovered": "2026-07-27T00:00:00+00:00", "updated": "2026-08-07T00:00:00+00:00"},
        # drop: fully contained
        {"name": "Babylon", "acres": 107189, "containment_pct": 100, "state": "UT",
         "lat": 37.2, "lng": -113.5, "discovered": None, "personnel": None, "cause": None},
        # drop: under 100 acres
        {"name": "Tiny", "acres": 12, "containment_pct": 0, "state": "AZ",
         "lat": 36.0, "lng": -112.0, "discovered": None, "personnel": None, "cause": None},
        # drop: outside our 5 states
        {"name": "Sacaton", "acres": 9861, "containment_pct": 0, "state": "NM",
         "lat": 33.0, "lng": -108.0, "discovered": None, "personnel": None, "cause": None},
    ],
}

kept = bf.active_incidents(FIXTURE)
assert [i["name"] for i in kept] == ["Widemouth 2"], kept

trails = [
    {"name": "Near Trail", "slug": "near-ut", "state": "ut", "lat": 38.75, "lng": -112.45},
    {"name": "Far Trail", "slug": "far-ca", "state": "ca", "lat": 37.0, "lng": -119.0},
]
near = bf.nearby_trails(kept[0], trails)
assert [t["slug"] for _, t in near] == ["near-ut"], near

html = bf.build_html(kept, trails, FIXTURE["updated_at"])
assert "Widemouth 2 Fire" in html and "96,702 acres" in html and "10% contained" in html
assert "/ut/near-ut" in html and "/ca/far-ca" not in html
assert "Babylon" not in html and "Sacaton" not in html
assert "2026-08-07 04:00 UTC" in html          # the read is always stamped
assert '<link rel="canonical" href="https://alwayshave.fun/fires">' in html

# Empty feed must say so, not render a bare page.
empty = bf.build_html([], trails, FIXTURE["updated_at"])
assert "No wildfire over 100 acres" in empty

print("test_build_fires: OK")
