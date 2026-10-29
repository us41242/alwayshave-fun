"""
traffic.py — who actually uses alwayshave.fun, from Cloudflare zone analytics.

Plays: the games send one anonymous beacon to /e/<event> per page load when
someone really plays (fh-bet, fh-done, fh-share, vp-deal, vp-25, sizer, home-lh, home-ev). Crawlers do not
click Deal, so these are the human signal. Page views are raw 200 GETs split
by Cloudflare's browser guess; scrapers posing as Chrome land in "browser".

  CF_ANALYTICS_TOKEN=cfut_... python3 scripts/traffic.py [days]   # default 7

Token needs Zone Analytics Read (the cfut_ token in boothsight/.dev.vars has
it; the cfat_ deploy token does not). Read-only; free-plan data lasts ~8 days
per query window.
"""
import ipaddress, json, os, sys, urllib.request
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

# --- Verified AI crawlers -------------------------------------------------
# Most "ClaudeBot"/"GPTBot"/"PerplexityBot" hits are credential scanners
# spoofing the UA (they ask for /.env, never for a guide page), so the UA
# alone means nothing. Each operator publishes its crawler IP ranges; only
# requests from those ranges are counted as real. ponytail: published JSON
# only — no reverse-DNS fallback, so an operator without a list shows 0.
AI_RANGES = {
    "GPTBot": "https://openai.com/gptbot.json",
    "OAI-SearchBot": "https://openai.com/searchbot.json",
    "ChatGPT-User": "https://openai.com/chatgpt-user.json",
    "PerplexityBot": "https://www.perplexity.ai/perplexitybot.json",
}


def _nets(url):
    d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "curl/8"})))
    return [ipaddress.ip_network(p.get("ipv4Prefix") or p["ipv6Prefix"]) for p in d["prefixes"]]


print("Verified AI crawlers (UA matched AND IP in the operator's published range):")
for bot, src in AI_RANGES.items():
    try:
        nets = _nets(src)
    except Exception as e:
        print(f"  {bot:16} range list unavailable ({e})")
        continue
    real, fake = Counter(), 0
    for r in q(span + ',userAgent_like:"%%%s%%"' % bot, "clientIP clientRequestPath edgeResponseStatus"):
        ip = ipaddress.ip_address(r["dimensions"]["clientIP"])
        if any(ip in n for n in nets if ip.version == n.version):
            real[(r["dimensions"]["clientRequestPath"], r["dimensions"]["edgeResponseStatus"])] += r["count"]
        else:
            fake += r["count"]
    print(f"  {bot:16} {sum(real.values()):4} real, {fake:4} spoofed")
    for (p, st), n in real.most_common(6):
        print(f"      {n:4}  {st}  {p}")
