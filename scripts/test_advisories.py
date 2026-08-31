"""Regression check: advisories render when active and vanish on expiry."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from build_static import load_advisories, advisory_card, build_meta

ADV = {
    "headline": "Flash flood closures below the rim (Aug 29)",
    "body": "Bridge closed.",
    "source_name": "NPS",
    "source_url": "https://www.nps.gov/grca/planyourvisit/key-messages.htm",
    "date": "2026-08-30",
    "expires": "2026-09-13",
}

with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
    json.dump({"live": ADV, "old": {**ADV, "expires": "2026-08-01"}}, f)
    path = f.name

active = load_advisories(path, today="2026-08-30")
assert "live" in active and "old" not in active, active
assert load_advisories(path, today="2026-09-14") == {}, "expiry gate failed"
os.unlink(path)

card = advisory_card(ADV)
assert "Flash flood closures" in card and "key-messages" in card and "advisory-card" in card

d = {"slug": "x", "name": "X Trail", "state": "AZ", "score": 80, "score_label": "Good"}
assert build_meta(d, advisory=ADV)["meta_desc"].startswith("⚠️ Flash flood closures")
assert not build_meta(d)["meta_desc"].startswith("⚠️")

# the real advisories file must always parse and carry expiry dates
real = json.load(open(os.path.join(os.path.dirname(__file__), "..", "data", "advisories.json")))
for slug, a in real.items():
    for k in ("headline", "body", "source_name", "source_url", "date", "expires"):
        assert a.get(k), f"{slug} missing {k}"

print("test_advisories: OK")
