"""
request_indexing.py — nudge Google to (re)crawl alwayshave.fun URLs via the
Indexing API. This is the "crawl-nudge lever": instead of waiting weeks for
Google's ~monthly homepage recrawl, ping URL_UPDATED on demand.

Auth: the breakingeven service account, which must be an OWNER of the AHF GSC
property (Full user is NOT enough — the API verifies ownership), and the
Indexing API must be enabled in the 'breakingeven' GCP project. Both done
2026-07-15.

URLs are pulled live from the sitemap, so new trails are covered automatically.

  python request_indexing.py --check          # publish homepage only, prove auth
  python request_indexing.py                   # live-check each URL, submit the 200s
  python request_indexing.py --no-livecheck    # submit every sitemap URL, no pre-check
  python request_indexing.py --only ut,az      # limit to path prefixes (state pages/trails)

Daily Indexing API quota is 200 publishes; the sitemap is ~96 URLs.
Note: the Indexing API is officially scoped to JobPosting/BroadcastEvent pages,
so Google may ignore these page types. It is a free, no-downside shot at the
indexation bottleneck.
"""
import sys, time, argparse, urllib.request, xml.etree.ElementTree as ET
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

CRED = "/Users/joshuaedrake/Documents/breakingeven.online/.credentials/google-service-account.json"
SITEMAP = "https://alwayshave.fun/sitemap.xml"
HOME = "https://alwayshave.fun/"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def client():
    creds = service_account.Credentials.from_service_account_file(
        CRED, scopes=["https://www.googleapis.com/auth/indexing"])
    return build("indexing", "v3", credentials=creds, cache_discovery=False)


def sitemap_urls():
    req = urllib.request.Request(SITEMAP, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        root = ET.fromstring(r.read())
    # strip the sitemap namespace so <loc> lookups work regardless of prefix
    return [el.text.strip() for el in root.iter() if el.tag.endswith("loc") and el.text]


def live(url):
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def publish(idx, url):
    idx.urlNotifications().publish(body={"url": url, "type": "URL_UPDATED"}).execute()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="publish only the homepage, to prove auth")
    ap.add_argument("--no-livecheck", action="store_true", help="skip the HTTP 200 pre-check")
    ap.add_argument("--only", default="", help="comma-separated path prefixes to include, e.g. ut,az")
    a = ap.parse_args()

    idx = client()

    if a.check:
        try:
            publish(idx, HOME)
            print(f"auth OK — nudged {HOME}")
        except HttpError as e:
            print(f"auth FAIL [{getattr(e,'status_code','?')}]: {str(e)[:200]}")
            sys.exit(1)
        return

    urls = sitemap_urls()
    if a.only:
        prefixes = tuple(f"https://alwayshave.fun/{p.strip().strip('/')}" for p in a.only.split(","))
        urls = [u for u in urls if u == HOME or u.startswith(prefixes)]
    print(f"{len(urls)} URLs from sitemap")

    targets = urls
    if not a.no_livecheck:
        print("live-checking...")
        good, skipped = [], []
        for u in urls:
            s = live(u)
            (good if s == 200 else skipped).append(u if s == 200 else (u, s))
        targets = good
        for u, s in skipped:
            print(f"  SKIP {s}  {u}")
        if skipped:
            print(f"  ({len(skipped)} non-200 skipped)")

    print(f"\nsubmitting {len(targets)} URLs...")
    done = fail = 0
    for u in targets:
        try:
            publish(idx, u)
            done += 1
            print(f"  ok  {u}")
        except HttpError as e:
            fail += 1
            print(f"  x [{getattr(e,'status_code','?')}] {u} — {str(e)[:120]}")
            if "Quota" in str(e):
                print("  quota hit — stopping; resume tomorrow.")
                break
        time.sleep(0.4)
    print(f"\nsubmitted {done}, failed {fail}, of {len(targets)}")


if __name__ == "__main__":
    main()
