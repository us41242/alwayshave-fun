# ponytail: the installability check, because a PWA fails silently — Chrome
# just doesn't offer "Install" and iOS pins a plain bookmark. Nothing in the
# page tells you. Asserts the manifest is valid, that every icon it names
# exists at the size it claims, that the Worker serves all three files, and
# that every routed page links it. Run against the repo or against live:
#   python3 scripts/check_manifest.py            # repo files
#   python3 scripts/check_manifest.py --live     # fetched from alwayshave.fun
import json, re, struct, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIVE = "--live" in sys.argv
MIN_INSTALLABLE = 144          # Chrome's floor for an installable icon


def fetch(path):
    """path is a site path like '/manifest.webmanifest'; returns (bytes, content_type)."""
    if LIVE:
        # A real UA: the zone 403s urllib's default one.
        req = urllib.request.Request("https://alwayshave.fun" + path, headers={
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 "
                          "(KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"})
        with urllib.request.urlopen(req) as r:
            return r.read(), r.headers.get("Content-Type", "")
    return (ROOT / path.lstrip("/")).read_bytes(), ""


def png_size(b):
    assert b[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    return struct.unpack(">II", b[16:24])


def routed_pages():
    """The site paths ROUTES maps to an HTML page, straight from worker.js."""
    src = (ROOT / "worker.js").read_text()
    block = src.split("const ROUTES = {", 1)[1].split("};", 1)[0]
    pairs = re.findall(r"'([^']+)':\s*'([^']+)'", block)
    return [(url, target) for url, target in pairs if target.endswith(".html")]


fails = []
raw, ctype = fetch("/manifest.webmanifest")
m = json.loads(raw)

for key in ("name", "short_name", "start_url", "display", "theme_color", "icons"):
    if not m.get(key):
        fails.append("manifest missing %s" % key)
if m.get("display") not in ("standalone", "fullscreen", "minimal-ui"):
    fails.append("display=%r is not installable" % m.get("display"))
if LIVE and "manifest+json" not in ctype and "json" not in ctype:
    # nosniff is set site-wide in _headers, so a wrong type makes Chrome drop it.
    fails.append("manifest served as %r, not JSON" % ctype)

biggest, purposes = 0, set()
for icon in m["icons"]:
    want = tuple(int(n) for n in icon["sizes"].split("x"))
    try:
        got = png_size(fetch(icon["src"])[0])
    except Exception as e:
        fails.append("icon %s: %s" % (icon["src"], e)); continue
    if got != want:
        fails.append("icon %s is %dx%d, manifest says %s" % (icon["src"], *got, icon["sizes"]))
    biggest = max(biggest, min(got))
    purposes.update(icon.get("purpose", "any").split())

if biggest < MIN_INSTALLABLE:
    fails.append("largest icon %dpx < Chrome's %dpx installability floor" % (biggest, MIN_INSTALLABLE))
if "maskable" not in purposes:
    fails.append("no maskable icon: Android will crop the brand chip")

theme = m["theme_color"]
for url, target in routed_pages():
    head = fetch(url if LIVE else "/" + target)[0].decode("utf-8", "replace").split("</head>")[0]
    if 'rel="manifest" href="/manifest.webmanifest"' not in head:
        fails.append("%s does not link the manifest" % url)
    if 'name="theme-color" content="%s"' % theme not in head:
        fails.append("%s theme-color does not match the manifest (%s)" % (url, theme))

print("check_manifest: %s, %d icons, %d pages%s" % (
    m["short_name"], len(m["icons"]), len(routed_pages()), " (live)" if LIVE else ""))
for f in fails:
    print("  FAIL", f)
sys.exit(1 if fails else 0)
