#!/usr/bin/env python3
"""
test_status_list.py — the hydrated status list must never contradict the data.

trail.html's render() overwrites the server-rendered status list, so anything
hardcoded there is shown to every real (JS-enabled) visitor regardless of the
actual conditions. It used to hardcode "Fire Risk: Low" — this catches that.

Run: python3 scripts/test_status_list.py   (needs Google Chrome; repo root cwd)
"""
import http.server, json, os, shutil, socketserver, subprocess, sys, tempfile, threading

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SLUG = "__status-list-selfcheck"
FIXTURE = {
    "slug": SLUG, "name": "Selfcheck Trail", "state": "UT", "status": "Open",
    "score": 20, "score_label": "Stay home", "difficulty": "Moderate",
    "current": {"temp_f": 80, "conditions": "Clear", "wind_mph": 5, "humidity": 20},
    "aqi": {"value": 30, "category": "Good"},
    "fire": {"risk_level": "high", "nearest_fire_km": 8.0, "fire_count_50km": 4,
             "nearest_incident": {"name": "Selfcheck", "acres": 1234.0, "containment_pct": 15,
                                  "cause": "Lightning", "distance_km": 11.3, "direction": "WSW",
                                  "updated": "2026-07-26T23:04:00+00:00"}},
    "river": {"cfs": 8590, "stage": "flood", "gauge_id": "09405500"},
    "forecast": [], "gear_flags": [], "updated_at": "2026-07-26T04:00:00+00:00",
}
# Same trail, but the gauge has no trail-specific caution threshold (stage None):
# the reading must render as informational — no FLOOD label, no red/green judgment.
FIXTURE_INFO = dict(FIXTURE, river={"cfs": 9230, "stage": None, "gauge_id": "09402500"})


def hydrate(fixture, static_head=""):
    """Serve trail.html + fixture locally, return the full headless-Chrome DOM.

    static_head: extra HTML injected before </head> to mimic a build_static.py
    page (e.g. the #schema-ld block that tells render() the page is static).
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    fixture_path = f"data/conditions/{SLUG}.json"
    # trail.html is served for /{state}/{slug} by the worker; mimic that locally.
    tmp_dir = tempfile.mkdtemp(dir=root)
    os.mkdir(os.path.join(tmp_dir, SLUG))  # /{state}/{slug}/ → render() reads slug from the path
    html = open("trail.html").read()
    if static_head:
        html = html.replace("</head>", static_head + "\n</head>", 1)
    with open(os.path.join(tmp_dir, SLUG, "index.html"), "w") as f:
        f.write(html)
    with open(fixture_path, "w") as f:
        json.dump(fixture, f)

    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as srv:
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_address[1]}/{os.path.basename(tmp_dir)}/{SLUG}/"
        try:
            dom = subprocess.run(
                [CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                 "--virtual-time-budget=8000", "--dump-dom", url],
                capture_output=True, text=True, timeout=90).stdout
        finally:
            srv.shutdown()
            os.remove(fixture_path)
            shutil.rmtree(tmp_dir)

    return dom


def status_block(dom):
    start = dom.find('id="status-list"')
    assert start != -1, "status-list not found in hydrated DOM"
    return dom[start:dom.find("</ul>", start)]


def main():
    block = status_block(hydrate(FIXTURE))
    assert "Fire Risk: High" in block, f"fire risk not from data:\n{block}"
    assert "Fire Risk: Low" not in block, f"hardcoded 'Fire Risk: Low' is back:\n{block}"
    assert "dot-red" in block, f"high fire risk must not render a green/yellow dot:\n{block}"
    assert "8,590 cfs" in block and "FLOOD" in block, f"water level missing:\n{block}"
    want = "Nearest fire: Selfcheck Fire — 1,234 acres, 15% contained, 7 mi WSW, lightning (NIFC, Jul 26)"
    assert want in block, f"named incident line wrong or missing (want {want!r}):\n{block}"
    assert 'href="/fires"' in block, f"fire line must link to /fires:\n{block}"

    block = status_block(hydrate(FIXTURE_INFO))
    want = "Water level: 9,230 cfs (USGS 09402500)"
    assert want in block, f"informational water line wrong or missing (want {want!r}):\n{block}"
    assert "FLOOD" not in block and "9,230 cfs —" not in block, \
        f"stage-less reading must carry no judgment:\n{block}"
    li_start = block.rfind("<li", 0, block.find("Water level: 9,230"))
    li = block[li_start:block.find("</li>", li_start)]
    assert "dot-gray" in li, f"informational water line must use the gray dot:\n{li}"

    # Static-rendered page: render() must NOT rewrite crawler-facing tags.
    # build_static.py's title/desc are richer (⚠️ caution, dog flag, sunrise)
    # and its #schema-ld carries FAQPage; Googlebot indexes the hydrated DOM.
    head = '<script type="application/ld+json" id="schema-ld">{"@type":"FAQPage"}</script>'
    dom = hydrate(FIXTURE, static_head=head)
    assert "Selfcheck Trail Conditions | alwayshave.fun" not in dom, \
        "render() overwrote the static title (drops the score label)"
    n = dom.count('<script type="application/ld+json"')
    assert n == 1, f"static page must keep exactly one schema block, got {n}"
    assert '"trail-schema"' not in dom and "id=\"trail-schema\"" not in dom, \
        "render() appended its own schema on a static page"
    # Non-static page (no #schema-ld): render() must still fill meta + schema.
    dom = hydrate(FIXTURE)
    assert 'id="trail-schema"' in dom, "render() no longer writes schema on non-static pages"
    assert "Selfcheck Trail Conditions | alwayshave.fun" in dom, \
        "render() no longer writes the title on non-static pages"

    # Status list must still hydrate correctly on static pages too.
    block = status_block(hydrate(FIXTURE, static_head=head))
    assert "Fire Risk: High" in block, f"static page: status list not hydrated:\n{block}"

    print("PASS — hydrated status list reflects the data (fire High, named incident, "
          "river FLOOD when staged, informational when not); static pages keep their "
          "server-rendered title/meta/schema, non-static pages still get JS meta+schema")


if __name__ == "__main__":
    sys.exit(main())
