"""sitemap_lastmod.py — keep sitemap.xml's <lastmod> honest.

Hand-edited lastmods drifted (2026-10-26: 4 of 14 wrong, three of them
understating freshness by a month — a wasted recrawl signal on the one site
file Google still fetches). Dates come from git's last commit date for the
HTML file each route serves, so an edited page is always fresh in the sitemap.

  python3 -I scripts/sitemap_lastmod.py           # rewrite sitemap.xml
  python3 -I scripts/sitemap_lastmod.py --check    # exit 1 if any lastmod is wrong

ponytail: regenerates only the dates of existing <url> rows; adding a new page
is still a hand edit (ROUTES order != sitemap order, and new pages are rare).
"""
import re, subprocess, sys

R = "/Users/joshuaedrake/Documents/alwayshave-fun"
SM = R + "/sitemap.xml"


def git_date(f):
    d = subprocess.run(["git", "-C", R, "log", "-1", "--format=%cs", "--", f],
                       capture_output=True, text=True).stdout.strip()
    if not d:
        sys.exit("no git date for " + f)
    return d


def main(check):
    routes = dict(re.findall(r"'(/[^']*)':\s*'(/[^']+\.html)'", open(R + "/worker.js").read()))
    sm = open(SM).read()
    bad = []

    def fix(m):
        slug, cur = m.group(1), m.group(2)
        f = routes.get(slug)
        if not f:
            sys.exit("sitemap URL not in worker ROUTES: " + slug)
        want = git_date(f.lstrip("/"))
        if want != cur:
            bad.append("%s: sitemap %s -> git %s" % (slug, cur, want))
        return "<loc>https://alwayshave.fun%s</loc><lastmod>%s</lastmod>" % (slug, want)

    out = re.sub(r"<loc>https://alwayshave\.fun(/[^<]*)</loc><lastmod>([\d-]+)</lastmod>", fix, sm)
    missing = set(routes) - set(re.findall(r"<loc>https://alwayshave\.fun(/[^<]*)</loc>", sm))
    for slug in sorted(missing):
        bad.append("%s: in ROUTES but missing from sitemap" % slug)
    if check:
        print("\n".join(bad) or "sitemap lastmods ok")
        sys.exit(1 if bad else 0)
    open(SM, "w").write(out)
    print("\n".join(bad) or "no change")
    if missing:
        sys.exit("missing from sitemap: " + ", ".join(sorted(missing)))


main("--check" in sys.argv)
