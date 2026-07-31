"""Self-check for the safety-critical bits of scoring. Run: python3 scripts/test_scoring.py"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from fetch_conditions import river_stage, compute_score, score_label, gear_flags

# Stage is relative to the trail's own unsafe-flow number (Narrows: NPS closes at 150 cfs).
assert river_stage(39, 150) == "low"
assert river_stage(90, 150) == "normal"
assert river_stage(140, 150) == "high"
assert river_stage(150, 150) == "flood"
assert river_stage(8590, 150) == "flood"

# Perfect weather + clean air must NOT read "great day to go" when the river is up.
perfect = {"current": {"temperature_2m": 70, "wind_speed_10m": 5, "precipitation_probability": 0}}
clean = {"aqi": 20}
fire = {"score_pts": 20}
assert compute_score(perfect, clean, fire) == 100
assert score_label(compute_score(perfect, clean, fire, {"stage": "high"})) == "Use caution"
assert score_label(compute_score(perfect, clean, fire, {"stage": "flood"})) == "Stay home"
assert any("do not enter" in f for f in gear_flags(perfect, clean, fire, {"stage": "flood"}))

# No declared caution threshold → stage is None → the reading must not cap the
# score or emit flags (the Colorado's normal ~9,000 cfs is not a "flood").
assert compute_score(perfect, clean, fire, {"cfs": 9230, "stage": None}) == 100
assert gear_flags(perfect, clean, fire, {"cfs": 9230, "stage": None}) == []

print("ok")
