"""
indexnow.py — Ping Bing and Yandex with updated URLs via IndexNow protocol.

Runs after every conditions update. Submits all trail URLs + state pages
so Bing/Yandex index fresh conditions data without waiting for a crawl.

Key is read from env INDEXNOW_KEY (set as GitHub Actions secret).
The key file must exist at /{key}.txt on the domain — we write it to repo root.
"""

import os
import re
import sys
import requests
from datetime import datetime, timedelta, timezone

BASE_URL     = "https://alwayshave.fun"
SITEMAP      = "sitemap.xml"
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "")

INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"


def collect_urls(all_urls=False):
    """URLs from the generated sitemap that actually changed recently.

    The sitemap is the single source of truth (it was previously hand-built
    here and silently missed every article and /dog-friendly). Default is
    lastmod within 24h so we don't re-ping static pages every 30 minutes;
    `--all` forces a full submission for one-off backfills.
    """
    xml = open(SITEMAP, encoding="utf-8").read()
    # ponytail: compare DATES, not a 24h timestamp. sitemap_lastmod.py writes
    # date-only lastmods, so a page edited today looked "older than 24h" to any
    # session running after 00:30 UTC — i.e. every session, which is why this
    # silently submitted 0 URLs on 2026-10-29. The 30-minute conditions cron the
    # old cutoff protected died with the trails site.
    cutoff = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    urls = []
    for loc, lastmod in re.findall(r"<loc>(.*?)</loc>\s*<lastmod>(.*?)</lastmod>", xml, re.S):
        if all_urls:
            urls.append(loc)
            continue
        try:
            dt = datetime.fromisoformat(lastmod.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if dt.date() >= cutoff:
            urls.append(loc)
    return urls


def ensure_key_file():
    """Write the IndexNow key verification file to repo root."""
    if not INDEXNOW_KEY:
        return
    key_path = f"{INDEXNOW_KEY}.txt"
    if not os.path.exists(key_path):
        with open(key_path, "w") as f:
            f.write(INDEXNOW_KEY)
        print(f"  Created key file: {key_path}")


def submit_batch(urls, host):
    if not INDEXNOW_KEY:
        print("  INDEXNOW_KEY not set — skipping IndexNow submission")
        return

    payload = {
        "host":    host,
        "key":     INDEXNOW_KEY,
        "keyLocation": f"https://{host}/{INDEXNOW_KEY}.txt",
        "urlList": urls,
    }
    try:
        r = requests.post(
            INDEXNOW_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        print(f"  IndexNow → {r.status_code} ({len(urls)} URLs)")
    except Exception as e:
        print(f"  IndexNow error: {e}")


def selftest():
    """ponytail: the one failure this script had was silent — a date-only lastmod
    written today read as stale, so it submitted nothing and said so in a line
    nobody read. Asserts today's and yesterday's dates are collected and an old
    one is not.  python3 -I scripts/indexnow.py --selftest"""
    global SITEMAP
    import tempfile
    today = datetime.now(timezone.utc).date()
    rows = {"today": today, "yesterday": today - timedelta(days=1), "old": today - timedelta(days=9)}
    xml = "".join("<url><loc>https://x/%s</loc><lastmod>%s</lastmod></url>" % (k, d) for k, d in rows.items())
    with tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False) as f:
        f.write("<urlset>%s</urlset>" % xml)
        SITEMAP = f.name
    got = collect_urls()
    assert got == ["https://x/today", "https://x/yesterday"], got
    assert len(collect_urls(all_urls=True)) == 3
    print("ok: date-only lastmods from today and yesterday are collected, a 9-day-old one is not")


def main():
    if "--selftest" in sys.argv:
        return selftest()
    host = BASE_URL.replace("https://", "")
    ensure_key_file()
    urls = collect_urls(all_urls="--all" in sys.argv)
    print(f"IndexNow: submitting {len(urls)} URLs to Bing/Yandex")
    if not urls:
        return
    # IndexNow accepts up to 10,000 URLs per batch; we're well under that
    submit_batch(urls, host)


if __name__ == "__main__":
    main()
