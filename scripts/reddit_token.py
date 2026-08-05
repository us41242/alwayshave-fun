"""Print a fresh oauth.reddit.com bearer token for the site account.

The saved Camoufox session's `token_v2` cookie expires ~24h, but `reddit_session`
in the same file is good for a year — loading www.reddit.com with it mints a new
token_v2. So no browser / no re-login is needed; plain curl is enough.

Must run from the Mac: Reddit 403s the a1-box datacenter IP.

    TOK=$(python3 scripts/reddit_token.py)
    curl -H "Authorization: Bearer $TOK" -H "User-Agent: ahf-ops/1.0" \
         https://oauth.reddit.com/api/v1/me
"""
import http.cookiejar, json, os, sys, urllib.request

SESSION = os.path.expanduser("~/.camoufox-mcp/sessions/reddit.pw.json")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def main():
    cookies = json.load(open(SESSION))["cookies"]
    jar = http.cookiejar.CookieJar()
    for c in cookies:
        if "reddit.com" not in c["domain"]:
            continue
        jar.set_cookie(http.cookiejar.Cookie(
            0, c["name"], c["value"], None, False,
            c["domain"], c["domain"].startswith("."), c["domain"].startswith("."),
            c.get("path", "/"), True, bool(c.get("secure")),
            int(c.get("expires") or 0) or None, False, None, None, {}))

    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    opener.addheaders = [("User-Agent", UA), ("Accept", "text/html,*/*")]
    # The homepage alone stopped minting token_v2 (2026-08-04) — it now serves a
    # logged-out-cacheable shell. Warm the session on "/" (session_tracker +
    # csrf_token), then hit the authed-only /settings/, which does mint it.
    opener.open("https://www.reddit.com/", timeout=30).read()
    opener.open("https://www.reddit.com/settings/", timeout=30).read()

    for c in jar:
        if c.name == "token_v2":
            print(c.value)
            return 0
    print("no token_v2 returned — reddit_session is probably dead; "
          "Josh needs to re-login in the browser and re-save the session",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
