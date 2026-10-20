"""Push live page HTML straight into Bing (Content Submission API), bypassing crawl.
Usage: python3 -I scripts/bing_submit_content.py <slug>... ("home" = /). Quota ~100/day.
Added 2026-10-19 (session 43) for pages Bing never discovered via sitemap/IndexNow/SubmitUrl."""
import base64,json,sys,urllib.request
K=open("/Users/joshuaedrake/Documents/breakingeven.online/.credentials/bing-api-key.txt").read().strip()
for p in sys.argv[1:]:
    u="https://alwayshave.fun/"+(p+"/" if p!="home" else "")
    r=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 (compatible; bingbot/2.0)"}))
    body=r.read()
    msg=b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n"+body
    data=json.dumps({"siteUrl":"https://alwayshave.fun/","url":u,"httpMessage":base64.b64encode(msg).decode(),"structuredData":"","dynamicServing":0}).encode()
    try:
        x=urllib.request.urlopen(urllib.request.Request("https://ssl.bing.com/webmaster/api.svc/json/SubmitContent?apikey="+K,data=data,headers={"Content-Type":"application/json; charset=utf-8"}))
        print(p,x.status,x.read()[:200])
    except urllib.error.HTTPError as e: print(p,e.code,e.read()[:400])
