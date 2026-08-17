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

# --- per-incident pages: permanent slugs, archive survival, honest inactive copy ---
assert bf.incident_slug(FIXTURE["incidents"][0]) == "widemouth-2-fire-ut-2026"
assert "/fires/widemouth-2-fire-ut-2026" in html          # the only crawl path in

arc = bf.update_archive(FIXTURE, {})
# 1,000-acre bar: Widemouth 2 (96,702) and Babylon (107,189) qualify; Tiny does not.
# Babylon is 100% contained — off /fires, but it still gets a permanent page.
assert set(arc) == {"widemouth-2-fire-ut-2026", "babylon-fire-ut-unknown"}, arc
assert arc["widemouth-2-fire-ut-2026"]["history"] == [
    {"date": "2026-08-07", "acres": 96702, "containment_pct": 10}]

# A second read the next day appends one point and does not duplicate the first.
day2 = {"updated_at": "2026-08-08T04:00:00+00:00",
        "incidents": [dict(FIXTURE["incidents"][0], acres=106450, containment_pct=24)]}
arc = bf.update_archive(day2, arc)
w = arc["widemouth-2-fire-ut-2026"]
assert [h["acres"] for h in w["history"]] == [96702, 106450], w["history"]
assert w["active"] is True
# Babylon fell out of this read — it must survive, flipped inactive, never deleted.
assert arc["babylon-fire-ut-unknown"]["active"] is False

page = bf.build_incident_html("widemouth-2-fire-ut-2026", w, trails)
assert "106,450 acres" in page and "24% contained" in page
assert '<link rel="canonical" href="https://alwayshave.fun/fires/widemouth-2-fire-ut-2026">' in page
assert "+9,748 ac" in page                     # growth curve is the unique asset
assert "/ut/near-ut" in page and "/ca/far-ca" not in page

gone = bf.build_incident_html("babylon-fire-ut-unknown", arc["babylon-fire-ut-unknown"], trails)
assert "No longer on the NIFC active list" in gone
assert "we do not guess" in gone               # hard rule 4: never claim it is out


# --- /data: the CSV flattening and the Dataset markup that feeds Dataset Search ---
import csv as _csv
import json as _json
import tempfile
import os as _os

with tempfile.TemporaryDirectory() as td:
    csv_path = _os.path.join(td, "growth-history.csv")
    rows = bf.write_growth_csv(arc, csv_path)
    # 2 days of Widemouth 2 + 1 of Babylon = 3 rows, one per incident per day, date-sorted.
    assert len(rows) == 3, rows
    with open(csv_path, newline="") as f:
        read_back = list(_csv.DictReader(f))
    assert [r["date"] for r in read_back] == ["2026-08-07", "2026-08-07", "2026-08-08"]
    assert read_back[-1]["acres"] == "106450"
    assert read_back[-1]["incident_slug"] == "widemouth-2-fire-ut-2026"
    assert list(read_back[0]) == bf.GROWTH_CSV_FIELDS

data_page = bf.build_data_html(arc, rows, day2["updated_at"])
assert '<link rel="canonical" href="https://alwayshave.fun/data">' in data_page
assert "growth-history.csv" in data_page and "creativecommons.org/licenses/by/4.0" in data_page
# The JSON-LD must parse and expose three Datasets — malformed markup is invisible
# to Dataset Search, and the whole point of the page is that markup.
ld = _json.loads(data_page.split('application/ld+json">')[1].split("</script>")[0])
kinds = [n["@type"] for n in ld["@graph"]]
assert kinds.count("Dataset") == 3, kinds
assert "DataCatalog" in kinds
for node in ld["@graph"]:
    if node["@type"] != "Dataset":
        continue
    # Dataset Search requires these; a Dataset without them is silently dropped.
    for key in ("name", "description", "license", "url", "creator"):
        assert node.get(key), (node["@id"], key)
    assert len(node["description"]) >= 50, node["@id"]

print("test_build_fires: OK")
