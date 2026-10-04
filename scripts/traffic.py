"""
traffic.py — who actually uses alwayshave.fun, from Cloudflare zone analytics.

Plays: the games send one anonymous beacon to /e/<event> per page load when
someone really plays (fh-bet, fh-done, vp-deal, vp-25, sizer, home-lh, home-ev). Crawlers do not
click Deal, so these are the human signal. Page views are raw 200 GETs split
by Cloudflare's browser guess; scrapers posing as Chrome land in "browser".

  CF_ANALYTICS_TOKEN=cfut_... python3 scripts/traffic.py [days]   # default 7

Token needs Zone Analytics Read (the cfut_ token in boothsight/.dev.vars has
it; the cfat_ deploy token does not). Read-only; free-plan data lasts ~8 days
per query window.
"""
import json, os, sys, urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone

ZONE = "64ec4821dafd619fc5191a6723c3dd19"
BOTS = {"GoogleBot", "BingBot", "Curl", "Unknown"}


def q(where, dims):
    body = json.dumps({"query": "{viewer{zones(filter:{zoneTag:\"%s\"}){httpRequestsAdaptiveGroups("
                       "limit:5000,filter:{%s}){count dimensions{%s}}}}}" % (ZONE, where, dims)}).encode()
    req = urllib.request.Request("https://api.cloudflare.com/client/v4/graphql", body, {
        "Authorization": "Bearer " + os.environ["CF_ANALYTICS_TOKEN"], "Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req))
    if d.get("errors"):
        sys.exit(d["errors"])
    return d["data"]["viewer"]["zones"][0]["httpRequestsAdaptiveGroups"]


days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
end = datetime.now(timezone.utc).replace(microsecond=0)
span = 'datetime_geq:"%s",datetime_lt:"%s",clientRequestHTTPHost:"alwayshave.fun"' % (
    (end - timedelta(days=days)).isoformat().replace("+00:00", "Z"), end.isoformat().replace("+00:00", "Z"))

plays = Counter()
for r in q(span + ',clientRequestPath_like:"/e/%",edgeResponseStatus:204', "clientRequestPath date"):
    plays[r["dimensions"]["clientRequestPath"][3:]] += r["count"]
print(f"Plays, last {days} days:", dict(plays) or "none")

views = Counter()
for r in q(span + ',edgeResponseStatus:200,clientRequestHTTPMethodName:"GET",clientRequestPath_like:"%/"',
           "clientRequestPath userAgentBrowser"):
    d = r["dimensions"]
    views[(d["clientRequestPath"], "bot/tool" if d["userAgentBrowser"] in BOTS else "browser")] += r["count"]
print("Page GETs (path, browser|bot/tool):")
for (p, kind), n in sorted(views.items(), key=lambda x: -x[1]):
    print(f"  {n:5}  {kind:8}  {p}")
