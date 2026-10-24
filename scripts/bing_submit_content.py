"""Push live page HTML straight into Bing (Content Submission API), bypassing crawl.
Usage: python3 -I scripts/bing_submit_content.py <slug>... ("home" = /). Quota ~100/day.
       python3 -I scripts/bing_submit_content.py --stale   # only pages edited (git) after Bing's LastCrawledDate
Added 2026-10-19 (session 43) for pages Bing never discovered via sitemap/IndexNow/SubmitUrl.
--stale added 2026-10-21 (session 44) after Station was discovered 2 days post-submit: resubmit on evidence, not habit."""
import base64,json,re,subprocess,sys,time,urllib.request,urllib.parse
from datetime import datetime,timezone
K=open("/Users/joshuaedrake/Documents/breakingeven.online/.credentials/bing-api-key.txt").read().strip()
API="https://ssl.bing.com/webmaster/api.svc/json/"; S="https://alwayshave.fun/"
R="/Users/joshuaedrake/Documents/alwayshave-fun"

CACHE=R+"/logs/bing-crawl-dates.json"  # {slug: {"crawled": date|"never", "checked": date}}; survives the GetUrlInfo throttle
def stale():
    routes=re.findall(r"'/([^']*?)/?':\s*'/([^']+\.html)'",open(R+"/worker.js").read())
    try: cache=json.load(open(CACHE))
    except FileNotFoundError: cache={}
    today=datetime.now(timezone.utc).strftime("%Y-%m-%d"); out=[]; throttled=None
    for slug,f in routes:
        key=slug or "home"
        edited=subprocess.run(["git","-C",R,"log","-1","--format=%cs","--",f],capture_output=True,text=True).stdout.strip()
        u=S+(slug+"/" if slug else "")
        if cache.get(key,{}).get("checked")==today: crawled=cache[key]["crawled"]
        elif throttled: crawled=None
        else:
            time.sleep(2)
            try:
                d=json.load(urllib.request.urlopen(API+"GetUrlInfo?"+urllib.parse.urlencode({"apikey":K,"siteUrl":S,"url":u})))["d"]
                ms=int(d["LastCrawledDate"][6:-2])
                crawled="never" if ms<0 else datetime.fromtimestamp(ms/1000,timezone.utc).strftime("%Y-%m-%d")
                cache[key]={"crawled":crawled,"checked":today}
            except urllib.error.HTTPError as e:  # ThrottleHost after ~13-25 GetUrlInfo calls (10-21, 10-22): keep what we have, never guess
                throttled=f"GetUrlInfo {e.code} {e.read()[:80]}"; crawled=None
        if crawled is None: print(f"?     {key:40} edited {edited} crawled (throttled, rerun later)"); continue
        st=crawled=="never" or edited>crawled
        print(f"{'STALE' if st else 'ok   '} {key:40} edited {edited} crawled {crawled}")
        if st and cache.get(key,{}).get("submitted")==today: print(f"      {key:40} already submitted today"); continue
        if st: out.append(key); cache.setdefault(key,{})["submitted"]=today
    json.dump(cache,open(CACHE,"w"),indent=1,sort_keys=True)
    if throttled: print(throttled,"— submitting the stale pages found so far; rerun in a few minutes for the rest")
    return out

def submit(p):
    u=S+(p+"/" if p!="home" else "")
    body=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 (compatible; bingbot/2.0)"})).read()
    msg=b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"+body
    data=json.dumps({"siteUrl":S,"url":u,"httpMessage":base64.b64encode(msg).decode(),"structuredData":"","dynamicServing":0}).encode()
    try:
        x=urllib.request.urlopen(urllib.request.Request(API+"SubmitContent?apikey="+K,data=data,headers={"Content-Type":"application/json; charset=utf-8"}))
        print(p,x.status,x.read()[:200])
    except urllib.error.HTTPError as e: print(p,e.code,e.read()[:400])

slugs=stale() if sys.argv[1:]==["--stale"] else sys.argv[1:]
for p in slugs: submit(p)
