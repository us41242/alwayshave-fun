# alwayshave.fun — Daily Logbook

Running record of every decision made, why it was made, what was learned, and what's coming next. Updated each session.

---

## 2026-08-03 — Session 25 (nightly, Monday — weekly report #4) — THE LIVE SITEMAP HAS BEEN FROZEN AT 2026-04-18 FOR 3.5 MONTHS

### Backfill: Session 24 (2026-08-01) shipped code but never logged
Commit `25ef5028e34` — the render() audit close-out (JS no longer overwrites the static title / meta description / schema on server-rendered trail pages; open question #5 closed) — was pushed with no LOGBOOK entry, and its `docs/STRATEGY.md` edits (kill-or-revise review held 08-01: KEEP everything, next review 09-01) were left **uncommitted in the working tree**. Both are committed tonight inside `d503f946930`. Third occurrence of the unlogged-session failure mode (Sessions 20, 22, now 24) — `git log` + `git status` against the last logged commit stays in the orient checklist.

### Oriented
- GSC (`sc-domain:alwayshave.fun`): **0 clicks / 0 impressions** 7d (through 07-30); 28d **0 clicks / 3 impressions**. Flat WoW. Weekly report due (last was 07-27).
- URL Inspection: homepage "Submitted and indexed," PASS, **last crawl still 2026-06-20 — 44 days**. `/nv/black-canyon-water-trail-nv` indexed (crawl 06-12), `/articles/petroglyph-canyon-gold-butte-nv` indexed (crawl 07-27, post-fix). `/ut/the-narrows-zion-ut` still "URL is unknown to Google." Sitemap status still **pending** since submission.
- Pipeline healthy, data commits every 30 min through 04:14Z.

### Found — the crawl-signal was broken at the source
**`/sitemap.xml`, the only file Google reads for freshness, was a hand-written static file dated 2026-04-18.** `scripts/generate_sitemap.py` has been generating a correct, fresh sitemap every 30 minutes for months — into `site/sitemap.xml`, which nothing serves. Consequences, all live until tonight:
- Every one of 96 `<lastmod>` values read `2026-04-18` — a site that rebuilds 48×/day was telling Google nothing had changed since April. Consistent with a 44-day-old homepage crawl and a permanently "pending" sitemap.
- **20 live URLs were absent from the served sitemap**: 5 CA trails (`bishop-pass-long-lake-ca`, `convict-lake-loop-ca`, `eagle-lake-desolation-ca`, `lone-pine-lake-ca`, `tokopah-falls-sequoia-ca`), `/ut/delicate-arch-ut`, 13 articles, and `/dog-friendly`.
- **`/site/*` was live and crawlable** (assets dir is the repo root): `/site/sitemap.xml` served a *second, competing* sitemap and `/site/index.html` an April clone of the homepage — duplicate content plus a conflicting crawl signal.
- The GH Actions commit step staged `site/`, not `sitemap.xml` — so even after repointing the generator, the fresh file would never have left the runner. Fixed in the same session; without it this would have re-frozen within 30 minutes.

Also found and fixed: the articles index advertised `rel=canonical` → `/articles`, but the assets layer (which runs **before** the Worker) 307s a bare `/articles` to `/articles/`. The canonical URL was a redirect, and worker.js's `/articles` branch was dead code that never executed. Canonical, og:url, schema `@id`/`url`, breadcrumbs, sitemap entry and every internal nav link now use `/articles/`; the dead branch is gone.

### Did
- `generate_sitemap.py` → writes the served `/sitemap.xml`; added `/about`, `/privacy`, `/scoring`; homepage loc now `https://alwayshave.fun/` (trailing slash, matching canonical). **116 URLs**, real per-trail `updated_at` lastmods.
- `.github/workflows/fetch_conditions.yml` → `git add … sitemap.xml …` (was `site/`).
- `worker.js` → `/site/*` 301s to its canonical equivalent (`/site/sitemap.xml` → `/sitemap.xml`, everything else → `/`); stale `site/` files deleted (hard rule 3 respected: the URLs redirect, they don't 404).
- `/articles/` canonicalization across `build_articles_index.py`, `publish_article.py`, `generate_sitemap.py`, all 57 article pages, and the root/static HTML.
- Commits: `d503f946930`, `920fba7a48c`, `925ef8301f4`.
- **Weekly report #4** → `~/Documents/daily-in-box/ahf-weekly-2026-08-03.md`.

### Verified (live, real-UA curl)
- `/sitemap.xml` serves 116 `<loc>`, valid XML, homepage lastmod `2026-08-03T04:17:44Z`.
- **All 116 sitemap URLs return 200** (full sweep, zero exceptions).
- `/site/sitemap.xml` → 301 → `/sitemap.xml`; `/site/index.html` → 301 → `/`.
- `/articles/` serves `rel=canonical https://alwayshave.fun/articles/`; zero remaining `href="/articles"` in the repo.
- Homepage 200.
- End-to-end: the post-fix pipeline run regenerated and committed `sitemap.xml` — see close-out below.

### Learned
- **A generator that runs clean every 30 minutes proves nothing about what is served.** `generate_sitemap.py` printed success 48×/day for months into a path no route touched. Verify the *served bytes*, not the build log — the same lesson shape as Session 19's hardcoded "Fire Risk: Low" (build was right, browser was wrong).
- **Cloudflare static assets are matched before the Worker.** Any worker.js branch whose path also resolves to an asset (or to an asset-layer redirect like `/foo` → `/foo/`) is dead code. That's why the `/articles` branch never ran.
- A build-output directory inside the assets root is publicly crawlable. `site/` was shipping a rival sitemap to Google.
- `git rebase` conflicts on a file the pipeline rewrites (`site/sitemap.xml`) resolve with `git rm` + `--continue`; use `-X theirs` on subsequent pulls, as the pipeline does.

### Expect
- This is the first change in weeks that targets the actual binding constraint (discovery/crawl) rather than page quality. If the frozen sitemap was suppressing recrawl, crawl activity should pick up in **1–3 weeks**: watch homepage `last crawl` moving off 2026-06-20, sitemap status leaving "pending", and sampled trail URLs leaving "URL unknown to Google". **Decision point ~2026-08-24:** if nothing moves, freshness signalling is not the constraint and authority is — Phase 3 becomes the entire strategy.

### Upcoming
- Homepage recrawl watch: 44 days since 2026-06-20 (now with an honest lastmod behind it).
- `scripts/indexnow.py` only submits homepage/state/trail URLs — **articles and `/dog-friendly` are never pinged to Bing/Yandex.** Small, obvious next fix.
- ~2026-08-04: Reddit site-mention eligibility (10 contributions live, all clean).
- Open question for Josh (3 weeks): widen the CF API token to read Workers Builds.

---

## 2026-07-31 — Session 23 (nightly) — PARTICIPATION ROUND 7 (OCTOBER MOAB TIMING)

### Oriented
- GSC (sc-domain property; the URL-prefix form now returns permission-denied — use `sc-domain:alwayshave.fun` going forward): **0 clicks / 0 impressions**, 7d and 28d both. Unchanged; authority is still the constraint.
- Weekly report #3 filed Monday 07-27 — no weekly section tonight.
- Reddit inbox: the two "new" items are still the Cedar City replies already answered in Session 19. Nothing new.
- Pipeline healthy: data commits landing every 30 min through 04:14Z.

### Did
- **Eighth-round contribution (`p10dvp9`)** in r/Utah `1vazezn` — October Moab lodging thread where OP asked "should I plan on coming at another time of year?" and 12 comments covered lodging but nobody answered the timing/conditions question. Answered with our own ERA5 10-yr normals near Delicate Arch (Oct 70/45 °F, ~5 wet days; July 98 for contrast), the mid-October UEA fall-break crowd week, the Arches timed-entry reservation reality (hedged to recreation.gov), and +1'd the Green River-as-cheaper-base consensus. No link, no site mention (eligible ~08-04).
- Passed on r/arizona's Greer campground thread (already fully answered) and nothing else fit. Docs-only push tonight.

### Verified
- All **10 comments** live via authed listing, none removed, none collapsed; `p10dvp9` score 1, `ozmi6b2` still +3, `oz7ywyd` +2.
- Live site: homepage 200 (real-UA curl), sitemap valid XML, 96 URLs.

### Learned
- `gsc_query.py` needs the domain property (`sc-domain:alwayshave.fun`) — the `https://` URL-prefix form is permission-denied under the service account.

### Expect
- Tally hits the "~a dozen contributions" bar within 1–2 more rounds; combined with the 08-04 two-week mark, a natural site mention becomes fair game in the next directly-relevant thread (or if asked, as `63insights`' "Thanks for the website" reply hints people already want the pointer).

### Upcoming
- ~2026-08-04: site-mention eligibility.
- Homepage recrawl watch: 41 days since 2026-06-20.
- Open question #5 (extend `test_status_list.py` to everything `render()` writes) remains the top site-side candidate.
- Check `p10dvp9` for replies.

---

## 2026-07-29 — Session 22 (nightly) — PARTICIPATION ROUND 6 (NOVEMBER ROAD-TRIP NORMALS); TRUE COMMENT TALLY IS 9

### Oriented
- GSC: **0 clicks / 0 impressions** (7d through 07-26). Homepage: "Submitted and indexed," PASS, last crawl **still 2026-06-20** (39 days). Weekly report #3 already filed Monday — no weekly section tonight.
- `git log` vs last logged commit: only pipeline data commits since Session 21 — no unlogged sessions this time.
- Reddit inbox: no new replies (the two "new" items are the Cedar City ones answered in Session 19). No smoke/fire threads in r/Utah or r/arizona tonight — the July smoke wave stays quiet.

### Did
- **Seventh contribution (`p0lv8lg`)** in r/Utah `1v9tijx` — November LA→Vegas→Havasupai→GC→Moab→Bryce→Zion road-trip planning thread. Five comments covered route logistics; nobody had touched *seasonal conditions*, which is our beat and exactly the shape of the account's first comment (`oz0h6w9`). Used our own ERA5 10-yr normals (data/climate/): Bryce 44/27 °F + early snow at 8–9k ft, Zion 55–57/low-30s + the ~5:15pm sunset constraint, Havasupai 65/42 + tribal-permit reality check, Moab 54/33; agreed with the one-car consensus; pointed at forecast.weather.gov, sourced the numbers as "10-year ERA5 monthly normals," treated as typical-not-forecast. No link, no site mention (day 8; mention eligible ~08-04).
- Passed on `1va7b36` (single mom, safe starter hikes near Riverton) — genuine thread but none of our 46 trails fit Riverton beginner terrain; never force one.
- No site code tonight; docs-only push.

### Found
- **True comment tally is 9, not 6.** Authed listing of u/StunningOpinion7483 shows two never-logged comments from ~07-23: `ozf6r6i` (in `1v3txnk`, the Zion flood thread) and `ozf6ya3` (in `1v3wyth`) — almost certainly the same unlogged 07-23 session that shipped the alerts_url audit (Session 18 backfill). Both live, +1, uncollapsed. STRATEGY tally corrected. The "~a dozen contributions" bar for a site mention is closer than we thought.

### Verified
- All **9 comments** live via authed API, none removed, none collapsed: `oz0h6w9` +1, `oz7ywyd` +2, `ozf6r6i` +1, `ozf6ya3` +1, `ozmhwpz` +1, `ozmi6b2` +3, `ozt1k8i` +1, `p0ekrx2` +1, `p0lv8lg` +1.
- Live site: homepage 200 (real-UA curl), sitemap valid XML, 96 `<loc>`.

### Learned
- The unlogged-session failure mode (Session 20's lesson) applies to Reddit too, not just git: the comment listing API (`/user/{name}/comments`) is the backstop tally, not the logbook. Re-pull it every orient, same as `git log`.

### Expect
- Account-history compounding; November trip-planning threads are a durable off-season surface when fire/smoke threads go quiet.

### Upcoming
- **~2026-08-04: site mention becomes fair game** (2 weeks + 9→~12 contributions) — only in a directly-relevant thread or if asked.
- Homepage recrawl watch: 39 days since 2026-06-20.
- Open question #5 (extend `test_status_list.py` to everything `render()` writes) is the top site-side candidate for the next code session.
- Check `p0lv8lg` / `p0ekrx2` for replies.

---

## 2026-07-28 — Session 21 (nightly) — GITHUB BACK; PARTICIPATION ROUND 5 (PARK CITY SMOKE)

### Oriented
- **GitHub connectivity restored** — Session 20's stranded LOGBOOK commit rebased and pushed first thing (`395f0362c2c`). Nothing else was queued.
- GSC: **0 clicks / 0 impressions** (7d through 07-25). Homepage: "Submitted and indexed," verdict PASS, last crawl **still 2026-06-20** (38 days).
- Reddit reachable again. Inbox: no NEW replies — the two unread items are the Cedar City replies already answered by `ozt1k8i` in Session 19.

### Did
- **Sixth contribution (`p0ekrx2`)** in r/Utah `1v92u3q` — "Going to Park City tomorrow. How's the smoke/wildfires?", OP traveling with young kids, only 3 thin comments ("you'll be fine" / a bare link). Pulled everything live first: AirNow PM2.5 AQI **38 Good** (Timpanogos Cave monitor, 9pm, sensitive-group framing for the kids); **zero VIIRS detections** in a ~1.4°×1.2° box, 24h, all three satellites; NIFC/WFIGS box query: every nearby named fire 95–100% contained (Buck Basin 145 ac/100% @ 42 km, Stookey 11,881 ac/95% @ 105 km near Tooele, Promontory + Adams both 100%); **no active NWS alerts** for the point. Pointed at fire.airnow.gov for a morning-of check. No link, no site mention — account is day 7 (guideline: ~2 weeks + ~a dozen contributions).
- No site code change tonight — no bug surfaced, and docs-only push.

### Verified
- All **6 comments** live via authed API (author correct, none removed, none collapsed): `oz0h6w9` +1, `oz7ywyd` +2, `ozmhwpz` +1, `ozmi6b2` +3, `ozt1k8i` +1, `p0ekrx2` +1.
- Live site: homepage 200 (real-UA curl), sitemap valid, 96 `<loc>`.
- Push confirmed on origin (`git ls-remote` matched local HEAD after push).

### Learned
- zsh eats `?` in unquoted URLs ("no matches found") — quote every curl URL with query strings.
- Env var names in alwayshavefun.env.local are `AIRNOW_KEY` / `NASA_FIRMS_KEY` (not `AIRNOW_API_KEY` / `FIRMS_MAP_KEY`) — grep the file for names before guessing.

### Expect
- Account-history compounding; a "traveling with kids, is it smoky" answer is the exact persona-audience match. Karma/replies are the metric.

### Upcoming
- Site mention becomes fair game ~2026-08-04 (2 weeks) if a directly-relevant thread appears and the tally is ~a dozen contributions (now 6).
- Homepage recrawl watch: 38 days since 2026-06-20.
- Check `p0ekrx2` for replies; keep scanning fire/smoke threads (season active).

---

## 2026-07-27 — Session 20 (nightly, Monday) — WEEKLY REPORT #3; WFIGS FEATURE VERIFIED LIVE; GITHUB UNREACHABLE

### Backfill: the WFIGS named-incident feature shipped 07-26 but was never logged
Commit `57fbd69018c` (Sun 07-26 21:28) — the Session 19 "next main action" got built and pushed by an unlogged session:
- `fetch_fires.py`: FIRMS `day_range=1` meant *current UTC day*, not last 24h — overnight runs scored fire risk on a near-empty dataset (0 hotspots vs 1,410 real). Now pulls 2 days from SNPP+NOAA20+NOAA21 and filters to a true trailing-24h window.
- Nearest **named** incident per trail from the free NIFC/WFIGS ArcGIS feed (name, acres, containment, cause, distance/bearing, record date). Status list now renders e.g. *"Nearest fire: Cliff Spring Fire — 170 acres, 10 mi ENE, undetermined (NIFC, Jul 27)"*, static + JS mirrored, `test_status_list.py` extended.

### Oriented
- GSC: **0 clicks / 0 impressions**, 7d (through 07-24) and 28d. Flat WoW, as every week. Homepage URL Inspection now reads **"Submitted and indexed," verdict PASS** — but **last crawl still 2026-06-20** (37 days, past the old ~monthly cadence). `/az/south-kaibab-gc-az` still "Crawled – not indexed" @ 2026-05-01.
- **GitHub unreachable tonight:** github.com:443 connections time out (DNS resolves — `140.82.112.4` — but the port hangs ~90s), while Google APIs and the live Cloudflare site respond fine. `git pull --rebase` failed on every retry. Reddit (www.reddit.com) also DNS-failed, so no fresh token/karma. Looks like a local network/routing issue, not a site or credential problem.

### Did
- **Wrote weekly report #3** → `~/Documents/daily-in-box/ahf-weekly-2026-07-27.md`. GSC flat 0/0; recapped the week's safety-and-differentiation work (Sessions 16–20: two gauge/score safety bugs, the hardcoded-"Fire Risk: Low" bug, the soft-404 close, the WFIGS named-fire feature); Reddit tally reported as last-confirmed (5 comments, 3 replies, all live — couldn't refresh tonight). Re-raised the 3-weeks-open Reddit-account question as the single highest-leverage ask.
- **No code pushed** — GitHub is down and there was no code change to make anyway; the highest-leverage completable action tonight was the mandated Monday weekly report plus verifying the unlogged feature actually deployed.

### Verified (live, real-UA curl — Cloudflare reachable)
- Homepage 200; sitemap valid, **96 `<loc>`**.
- WFIGS feature **live and correct**: `/az/south-kaibab-gc-az` static HTML carries `Nearest fire: Cliff Spring Fire — 170 acres, 10 mi ENE, undetermined (NIFC, Jul 27)`; the JS template mirror (`Nearest fire: ${nm} …`) is present; `Fire Risk: … (NASA FIRMS)` static line intact. Session 19's data-driven fire render is holding in production.

### Learned
- **A session can ship without logging.** The WFIGS work — Session 19's headline "next action" — was committed 07-26 with a real, verified commit message but left no LOGBOOK entry. The commit log is the backstop when the journal has a gap; check `git log` against the last logged commit every orient.
- Tonight's env failed selectively: Google + Cloudflare fine, GitHub + Reddit dead. When one host times out, test others before assuming the network is down — and DNS-resolves ≠ port-reachable (github resolved but :443 hung).

### Expect
- No traffic effect. Still 0/0 until Google recrawls the homepage; that single event will propagate the whole backlog of fixes at once.

### Upcoming
- **Push the local LOGBOOK commit** the moment GitHub connectivity returns (nothing else is queued to push).
- Reddit account remains the Phase-3 blocker; check `ozt1k8i`/`ozmi6b2` for replies once reddit.com resolves again.
- Homepage recrawl watch: 37 days and counting since 2026-06-20.

---

## 2026-07-25 — Session 19 (nightly) — HARDCODED "FIRE RISK: LOW" SHOWN TO EVERY VISITOR; SOFT-404 SPACE CLOSED

### Oriented
- GSC: 0 clicks / 0 impressions (7d through 07-22 and 28d). All 3 baselines byte-identical for the sixth session running: homepage last crawl **2026-06-20** (now 35 days — past its ~monthly cadence), `/az/south-kaibab-gc-az` "Crawled — not indexed" @ 2026-05-01, `/ut/the-narrows-zion-ut` "URL is unknown to Google."
- **Two new Reddit replies**, both on the Cedar City fire thread `1v5u5y8`, both to our comment `ozmi6b2` (now +3): *"Thanks for the website. That'll be useful"* (they meant fire.airnow.gov — we pointed at it, never at us) and *"Thank you I'm worried about my sister and appreciate it."* All 4 prior comments live, none removed or collapsed.

### Did
**1. Answered the worried replier with a 24-hour update (`ozt1k8i`, r/Utah).** Pulled everything fresh first:
- **NIFC/WFIGS incident feed** (free ArcGIS endpoint, no key) names two lightning-caused Iron County fires, not one: **Mound** (52.5 ac, 37.652/-113.273, ~11 mi WSW of Cedar City, record last touched 07-24 18:09 MDT — flagged as stale in the comment) and **Swett** (44.4 ac, 37.713/-113.213, ~9 mi WNW, updated 19:32 MDT tonight). Neither has a containment figure yet.
- **Last night's caveat played out exactly.** Session 18 said the satellites hadn't caught the start yet and that new starts show after the next overnight pass. Tonight VIIRS (SNPP + NOAA20 + NOAA21) has heat on the Mound footprint across every pass from 03:47Z through 21:40Z. Said so in the comment — being visibly right about a stated uncertainty is worth more than being right quietly.
- **AirNow Enoch:** PM2.5 AQI 33 / ozone 37 at 9pm, still Good but PM2.5 up from 23 at the same hour last night. Forecast Moderate Sun + Mon. **NWS:** zero active alerts for the point; wind SSE 5 mph tonight, **SW 3–9 Sunday — which puts Cedar City downwind of both fires**.
- Included one honest negative: a single MODIS Aqua pass at 16:03 MDT flagged a hotspot ~15 mi NNE (west of Parowan) that no VIIRS pass corroborates and that is on no incident list — stated as unconfirmed, might be a false positive. Also explicitly declined to speak for evacuations (Iron County SO, not a satellite). No link, no site mention — day 5, 5 comments.

**2. Fixed a live safety bug the Reddit work surfaced.** Reading `fetch_fires.py` to see whether the site could name incidents, I found `trail.html`'s `render()` hardcoded **`Fire Risk: Low (updated daily)` with a green dot**, unconditionally, and it *overwrites* the server-rendered status list. Google saw the honest FIRMS value; **every real JS visitor saw "Low" no matter what** — including on a trail with fire inside 20 km. Same class as the Narrows flood bug (Session 16) and squarely hard rule 4. The JS was also silently dropping the water-level row that `build_static.py` renders. Both now mirror the static build (`721623b17b5`).

**3. Closed an unbounded soft-404 space (`11b3723196b`).** `worker.js` fell back to the trail.html shell for **any** `/{state}/{anything}`, so `/ut/not-a-real-trail-xyz` returned **200** with a "Loading trail conditions…" page. Infinite 200s on a site whose binding constraint is crawl budget. The shell now serves only when `data/conditions/{slug}.json` exists; everything else returns the asset 404. Added `404.html` — **there was none** — linking the 5 state pages, dog-friendly, and articles, per the brand rule about always giving a plan.

### Verified
- `scripts/test_status_list.py` — new runnable check: renders the page in headless Chrome against a high-fire/flood fixture and asserts the hydrated DOM says High + FLOOD with red dots. **Confirmed non-vacuous** by running it against `git show HEAD:trail.html` — it fails there, passes on the fix.
- No pipeline race: the 04:30Z run picked up `721623b17b5` (checked `gh run list` headSha), completed success 04:47Z, regenerated all pages.
- Live, real-UA: **all 96 sitemap URLs return 200**; **zero** pages still carry `Fire Risk: Low (updated daily)`; every trail page carries the static `Fire Risk: … (NASA FIRMS)` line and the new data-driven JS; `/ut/not-a-real-trail-xyz` and `/nv/no-such-thing` → **404**; `/ut`, `/dog-friendly`, `/articles` → 200; sitemap valid XML, 96 URLs.
- Reddit `ozt1k8i` live via authed API: author correct, not removed, not collapsed.

### Learned
- **A JS hydration that overwrites a server-rendered node is a place bugs hide from every SEO check you run.** Curl and the URL Inspection API both showed the honest value; only a real browser showed the lie. Anything `render()` writes must be asserted against the data, not eyeballed — hence the headless-Chrome self-check, which is now the pattern for this file.
- Session 6 *documented* this exact hardcode ("the JS hardcodes Fire Risk: Low — static render uses real data") and moved on. A known-wrong value that only affects humans is still a bug; noting it in a logbook is not fixing it.
- **WFIGS/NIFC publishes current wildfire incidents free, no key** — name, acres, containment, cause, lat/lng, per state. `services3.arcgis.com/T4QMspbfLg3qTGWY/…/WFIGS_Incident_Locations_Current/FeatureServer/0/query`. Our fire card currently says "nearest fire 12 km" from anonymous VIIRS pixels; it could say "Mound Fire, 52 acres, 11 mi WSW." That is the single biggest content upgrade available to the site's differentiating asset.
- `fetch_fires.py` queries **VIIRS_SNPP only**. Tonight NOAA20 and NOAA21 each caught detections on passes SNPP missed. Single-satellite coverage understates fire proximity.
- `not_found_handling = "404-page"` means a failed `env.ASSETS.fetch` is *already* a correct 404 response — no need to construct one.

### Expect
- No traffic effect from either fix; both are trust/correctness. The soft-404 close is a small crawl-budget return whenever Google next crawls.
- Reddit: 5 comments, 3 replies received, all live. Site mention still off the table (guideline: ~2 weeks + ~a dozen contributions).

### Upcoming
- **Monday 2026-07-27: weekly report #3** — GSC WoW, Bing InIndex series, Reddit tally.
- **Build the WFIGS named-incident feature** — nearest active incident (name, acres, containment, distance) into `data/fires/{slug}.json` → `fetch_conditions.py` → the status list and fire card, both static and JS. Add NOAA20/NOAA21 to the FIRMS pull at the same time. This is the next session's main action.
- Check `ozt1k8i` for replies; the unconfirmed Parowan hotspot resolves on tonight's overnight pass — worth a follow-up only if it turns into a real start.
- Homepage recrawl watch: 35 days since 2026-06-20 and counting.

---

## 2026-07-24 — Session 18 (nightly) — FIRST REDDIT REPLY RECEIVED; PARTICIPATION ROUND 3

### Backfill: Session 17 (07-23) — committed but never logged
`6c5fbe9855a` — audited all 46 `alerts_url` values in seeds/trails.csv: 4 dead links repaired (Gold Butte + Paria BLM 404s, thehavasupaitribe.com DNS-dead, kanarraville.org TLS-broken), 11 redirects updated to final URLs (USFS `/rNN/` paths). Replacements title-checked, not just 200-checked. Verified live tonight: kanarra-creek page 200 and serving fresh data.

### Oriented
- GSC: 0 clicks / 0 impressions (7d and 28d through 07-21). All 3 baselines byte-identical again: homepage crawl 2026-06-20, South Kaibab "Crawled — not indexed" @ 2026-05-01, Narrows "URL unknown to Google". No nudge fired (lever closed Session 16).
- Reddit token minted fine via `scripts/reddit_token.py` (no browser). Both prior comments live: `oz0h6w9` +1, `oz7ywyd` +2.
- **First-ever reply received:** the Zion-flood OP (`oz7ywyd` thread) answered *"Thank you so much, this is very helpful! I had no idea where to look for this kind of info."* That's the account's voice validated by the exact audience the site targets.

### Did
- **Replied to the OP (`ozmhwpz`)** teaching the sources, not the site: USGS 09405500 on waterdata.usgs.gov + the 150 cfs NPS closure threshold, the rangers' daily flash-flood-potential rating on the Zion conditions page, forecast.weather.gov point forecasts. No link to us, no site mention — account is 3 days old; cadence rule holds.
- **Third contribution (`ozmi6b2`)** in r/Utah `1v5u5y8` (wildfire ignited west of Cedar City tonight, 29↑ news thread). Pulled live data first: both VIIRS satellites (SNPP + NOAA20, 24h, 1° box) show zero hotspots; Enoch AirNow monitor reads Good (PM2.5 AQI 23, O3 42) as of 9pm. Comment states both numbers with the satellite-lag caveat made explicit (new small starts appear after the next overnight pass) and points at fire.airnow.gov. Cedar City is Kanarra Creek's backyard — exactly our beat.
- **Closed the Session 16 follow-up on unverified external-ID columns:** grepped scripts/, worker.js, and both templates — `usfs_unit_id`, `recgov_facility_id`, `snotel_station_id` are consumed by NOTHING. Dormant seed data, no rendering path, no gauge-style exposure. Verify against source-of-truth only if/when a feature consumes them (note: the snotel values like `SntfMt-1` aren't even valid SNOTEL triplet format — treat as placeholders).

### Verified
- All 3 comments live via authed API (not removed, not collapsed).
- Live health (real-UA curl): homepage / kanarra-creek / narrows / sitemap all 200; sitemap 96 URLs; Narrows serving "38 cfs — Low (USGS 09405500)" with a consistent label — Session 16's safety fix holding in production.
- No site code pushed tonight (docs only).

### Learned
- The env file's keys are single-quoted — regexes that exclude quote chars silently miss them; strip quotes when parsing.
- `gsc_inspect.py` takes `--site-url sc-domain:...` + positional URL (not `--property/--url` like gsc_query.py).

### Expect
- The OP reply + fire-thread comment are account-history compounding; karma/replies are the metric. Site mention stays off the table until ~2 weeks + ~a dozen contributions.

### Upcoming
- Next session (Monday 07-27): weekly report #3 — GSC WoW, Bing InIndex series, Reddit tally.
- Check `ozmi6b2`/`ozmhwpz` for replies; scan for new genuine threads (fire season is producing them).
- Homepage recrawl watch: last crawl 06-20, cadence ~monthly → a recrawl is due any day; it's the first event that can propagate the 07-14 static grid.

---

## 2026-07-22 — Session 16 (nightly) — SAFETY DATA BUG FOUND & FIXED

### Oriented
- GSC: 0 clicks / 0 impressions (7d and 28d, through 07-19), sitemap still `pending`.
- Baselines after **5 nudge nights**: homepage last crawl **2026-06-20**, `/az/south-kaibab-gc-az` "Crawled — not indexed" @ **2026-05-01**, `/ut/the-narrows-zion-ut` **"URL is unknown to Google"** — byte-identical to the pre-nudge baseline.
- Reddit `token_v2` was **expired** (they last ~24h). Solved without a browser — see below.

### Decided
Two things earned tonight over anything else. (1) While pulling live data for a Reddit answer I noticed **The Narrows was serving "8,590 cfs — flood" and scoring 88 / "Great day to go" in the same breath.** That is a hard-rule-4 problem (safety-adjacent data) and it beats every SEO task on the list. (2) The Reddit thread that surfaced it — "Ok to visit zion national park tomorrow?" — is the exact question this site exists to answer, so contribute there.

### Did
- **Root cause: wrong river, and the river never mattered anyway.**
  - Both Narrows routes pointed at USGS **09380000 = Colorado River at Lees Ferry**, not the Virgin. 8,590 cfs was a *real* reading from the *wrong river*. Correct gauge **09405500** (North Fork Virgin near Springdale) reads **39 cfs**.
  - `compute_score()` never looked at `river` at all — a trail could be in genuine flood and still score 100.
  - Fixed (`8edf6710854`): gauge corrected on both routes; new `river_caution_cfs` column (Narrows = **150**, the NPS closure flow) because generic cfs bands are meaningless across rivers — 150 cfs is a flood on the North Fork Virgin and a trickle on the Colorado; stage now scales to the trail's own number when declared. **flood caps the score at 25 ("Stay home"), high at 55 ("Use caution")**; gear flags warn on high water; negative USGS sentinels (-999999) dropped. Water level now renders in the **static** status list too — it was JS-only, so no-JS crawlers and users never saw it.
  - `scripts/test_scoring.py` — runnable self-check: perfect weather + clean air must never label a flooded river "Great day to go".
- **Audited every other gauge — found a second one (`e473a0f1daa`).** Mount Whitney and Lone Pine Lake (CA Sierra) were wired to **09352900 = Vallecito Creek near Bayfield, COLORADO**, ~700 mi away, displaying its 45 cfs as local water. No active USGS discharge gauge exists on Lone Pine Creek (LADWP runs those), so the gauge is now blank and the card hides. Remaining 5 gauges verified genuinely local (Kanab Creek, Colorado nr Grand Canyon for Bright Angel, Oak Creek, Colorado blw Hoover Dam ×2).
- **Reddit token access solved permanently** — `scripts/reddit_token.py`. `token_v2` dies daily but `reddit_session` in the same session file is valid to 2027; loading `www.reddit.com` with it mints a fresh `token_v2` (stdlib only, no browser, no Camoufox). Verified: `/api/v1/me` → StunningOpinion7483.
- **Second Reddit contribution** — comment `oz7ywyd` in r/Utah `1v3txnk` ("Ok to visit zion national park tomorrow?", poster spooked by the flood-warning posts). Gave the actual USGS 09405500 reading (39 cfs vs the 150 cfs NPS closure), the NWS Springdale forecast (87°F, 10% PoP after 3pm), the fact that **no** flash-flood watch/warning is active, that the Junction/Marysvale flooding is the **Sevier** drainage not the Virgin, beginner-appropriate alternatives (Riverside Walk / Pa'rus / Lower Emerald), and deferred to the rangers' daily flash-flood-potential board over any gauge or forecast. **No link, no site mention** (account is 2 days old). Also corrected — gently, with a citation — a top comment asserting the Narrows were closed.
- **Nudge night 5:** 96 submitted, 0 failed.

### Verified
- `scripts/test_scoring.py` passes; local pipeline run on the 3 affected trails produced 39 cfs / `low` / gauge 09405500 (was 8,590 / `flood`).
- CI run with the new scripts, then live real-UA curl — see close-out below.
- Reddit comment `oz7ywyd` live via authed API: author correct, +1, not removed, not collapsed. Earlier comment `oz0h6w9` still live, +1, no replies yet.
- Indexing API: 96/96 accepted.

### Learned
- **The Reddit work found the bug the SEO work never would have.** Answering a real person's real question forced me to look at our own numbers the way a stranger would, and they were wrong. Genuine participation isn't only a distribution channel — it's QA.
- A gauge ID that returns 200 and plausible-looking numbers can still be the wrong river. Any external station ID in the seeds must be verified against its **site name and coordinates**, not just "does it return data."
- Reddit needs no browser automation: `reddit_session` → fresh bearer, forever, in ~30 lines of stdlib.

### Killed
- **Google Indexing API crawl-nudge — declared INERT after 5 nights, stopped.** 96/96 accepted every night, zero crawl-date movement on any baseline. It's documented for JobPosting/BroadcastEvent; on content pages it accepts and does nothing. STRATEGY question 0 closed. Authority (Phase 3) is the only remaining Google-side lever.

### Expect
- Score/label correctness: no traffic effect, and that's fine — this was a trust and safety fix. A page that says "Great day to go" during a flood is the one thing that ends the site.
- Reddit: `oz7ywyd` is the strongest-fit contribution yet; watch replies/karma next session.

### Upcoming
- Next session: check both comments for replies; find 1–2 new genuine threads (r/arizona had no fit tonight — politics/wildlife/photos only); **do not fire the nudge**.
- Consider surfacing the same audit discipline elsewhere: every seed column that points at an external ID (`usfs_unit_id`, `recgov_facility_id`, `snotel_station_id`) is unverified in exactly the way the gauges were.

---

## 2026-07-21 — Session 15 (nightly) — PHASE 3 STARTED

### Oriented
- GSC: still 0 clicks / 0 impressions (7- and 28-day, through 07-18), sitemap still `pending`. Note: GSC scripts now need `--property sc-domain:alwayshave.fun` (the URL-prefix form returns permission denied; only the domain property is verified).
- Baselines STILL unmoved after 3 nudge nights: homepage last crawl 2026-06-20, South Kaibab "Crawled — not indexed" @ 2026-05-01, Narrows "URL unknown to Google." Tonight was nudge night 4.
- **`reddit.env.local` EXISTS — Josh created the site Reddit account today (u/StunningOpinion7483, Google OAuth).** Phase 3 unblocked. Key facts from the file: no Reddit-native password; saved Camoufox session at `~/.camoufox-mcp/sessions/reddit.pw.json`; must post from the Mac (Reddit 403s the a1-box IP).

### Decided
Phase 3 participation is the action the last 3 sessions have been queuing behind, and the strategy's own analysis says authority is the only real lever. Tonight = re-fire nudge (cheap) + start genuine Reddit participation.

### Did
- **Indexing API night 4:** 96 submitted, 0 failed.
- **Found the no-browser path into Reddit:** the session file's `token_v2` cookie is a valid OAuth bearer for `oauth.reddit.com` (verified `/api/v1/me` → logged in as StunningOpinion7483; token expires ~24h after each browser session save). No Playwright/Camoufox needed for API-level read+comment.
- **Read r/arizona + r/Utah rules** via `/about/rules` — both ban self-promo; data-first comments are within rules.
- **Scanned both subs** (search + 25 newest each): the July smoke event has eased — zero active smoke/AQI threads. Best genuine fit: r/Utah thread `1v0yost` (Aug 22–Sep 5 Moab/Four Corners road trip with a 4-year-old; commenters saying "it'll be hot" with no numbers).
- **Posted first contribution** (comment `oz0h6w9`): ERA5 10-yr normals for the Delicate Arch area (Aug 95°F/70°F → Sep 87°F/60°F), trail stats (3.2 mi / 480 ft exposed slickrock at sunset), Arches timed-entry Apr–Oct, monsoon/flash-flood morning-front-load advice. **No link, no site mention** — account is 1 day old; history first.
- Updated STRATEGY.md: Distribution table (first entry), Phase 3 status → participation started, nudge tally night 4, cadence rule (1–2 genuine comments/session, never forced, no site mention until ~2 weeks of history).

### Verified
- Reddit comment live: authed API shows it in the thread, author correct, not removed/collapsed. Unauthenticated shadow-check impossible (reddit.com 403s curl even with browser UA) — true signal is replies/votes next sessions.
- Indexing API: 96/96 success responses.
- Live health (real-UA curl): homepage, South Kaibab, Narrows, sitemap all 200; sitemap 96 URLs. Docs-only push tonight; no rendering code changed.

### Expect
- Nudge verdict ~07-23: crawl dates unmoved through 4 nights → lever is almost certainly inert; 1–2 more firings then stop.
- Reddit: karma/replies on `oz0h6w9` = first external signal the voice works. Backlink/authority effects are months out; the near-term goal is account history so a site mention is ever legitimate.

### Upcoming
- Next session: check `oz0h6w9` for replies (respond if any), find 1–2 new genuine threads (check r/arizona again — nothing fit tonight), re-fire nudge (night 5, near-final), re-inspect baselines.
- Token note for next session: if `token_v2` is expired, the Camoufox session needs re-saving via browser login before API calls work.

---

## 2026-07-20 — Session 14 (nightly, Monday — weekly report #2)

### Backfill: Sessions 12–13 (07-18, 07-19) — crashed before logging
Session 12 (07-18) built the climate feature but stalled waiting on a pipeline run and never logged. Session 13 (07-19) committed and pushed it (`32d632f2f28` — "Typical Weather by Month" tables on all 46 trail pages: 10-yr ERA5 monthly normals via one-time `scripts/fetch_climate.py`, rendered by `build_static.py`; plus llms.txt 20→30-min cadence fix) but produced no log output and never verified. **Verified live tonight:** real-UA curl of `/az/south-kaibab-gc-az` contains the "Typical Weather" section; homepage/trail/sitemap all 200. Targets "{trail} weather in {month}" / "best time to hike {trail}" — the exact query shape Bing already surfaces us for. Added to the experiments table.

### Oriented
- GSC: still 0 clicks / 0 impressions (7- and 28-day), sitemap still `pending`.
- **Baselines unmoved after 2 prior nudge nights:** homepage last crawl 2026-06-20, `/az/south-kaibab-gc-az` "Crawled — not indexed" @ 2026-05-01, Narrows still "URL is unknown to Google." Nudges 07-18/07-19 never fired (sessions crashed), so tonight is nudge night 3 of the ~07-23 deadline window.
- Bing InIndex: 88→93 of 96 over the week (BWT GetCrawlStats). Still ~0 impressions.
- No `reddit.env.local` — Phase 3 still blocked on Josh's 5-minute signup (asked 07-17, re-asked in tonight's weekly).

### Did
- Re-fired Google Indexing API: **96 submitted, 0 failed** (night 3).
- **Closed STRATEGY open question 2:** `gh run list` shows fetch_conditions firing exactly at :00/:30, all success — the */30 trigger applied; build-minute headroom confirmed (~1,440 builds/mo vs 3,000-min ceiling).
- Wrote weekly report #2 → `~/Documents/daily-in-box/ahf-weekly-2026-07-20.md` (GSC WoW flat; Bing 88→93 as second series; Reddit re-ask).
- Backfilled Sessions 12–13 above; updated STRATEGY (climate experiment row, question 2 closed, nudge tally).

### Verified
- Live health (real-UA curl): homepage 200, `/az/south-kaibab-gc-az` 200 with climate table rendered, `/ut/the-narrows-zion-ut` 200, sitemap.xml 200. Docs-only push tonight; no rendering code changed.
- Indexing API 96/96 success responses; URL Inspection re-run on all 3 baselines.

### Expect
- 2 nudge nights left (07-21, 07-22-ish). No crawl-date movement by ~07-23 → declare the Indexing API inert for content pages, stop firing, and Phase 3 becomes the sole focus — which is blocked on the Reddit account.
- Climate tables: watch Bing query rows for month/best-time shapes (monthly check, not nightly).

### Upcoming
- Next session: re-inspect baselines, re-fire nudge (night 4), check `reddit.env.local`.
- ~07-23: nudge verdict day.

---

## 2026-07-17 — Session 11 (nightly)

### Oriented
- **Session 10's nudge: no movement yet (~24h in).** URL Inspection re-run on all 3 baselines: homepage `last_crawl_time` still 2026-06-20, `/az/south-kaibab-gc-az` still "Crawled — not indexed" @ 2026-05-01, `/ut/the-narrows-zion-ut` still "URL is unknown to Google." Too early to call the Indexing API dead — keep firing through ~07-23 (deadline set in STRATEGY §0).
- GSC 7-day (07-10→07-14): 0 clicks / 0 impressions / 0 rows. Sitemap still `pending`. Expected.
- Weekly report: written Session 8 (Mon 07-14); next due Mon 07-20 — none needed tonight.

### Decided
Re-fire the crawl nudge (planned, cheap), then before starting the queued Reddit work, audit the one never-checked free channel: **Bing**. Finding changed the picture (below), so tonight = Bing diagnosis + URL submission + unblocking Phase 3 via a Josh ask, rather than attempting automated Reddit signup (CAPTCHA + email verification is a deliberate human gate; automating past it risks an instant ban — hard rule 5).

### Did
- **Re-fired Google Indexing API at all 96 URLs** — 96 submitted, 0 failed (second consecutive night; quota ~97/200).
- **Discovered the site is already verified in Bing Webmaster Tools** (shared BWT API key in `~/.config/claude-seo/`, same account as breakingeven). Pulled the full baseline: **92/96 pages IN Bing's index**, crawling ~5–13 pages/day, sitemap known (96 URLs, fetched 07-15), zero crawl errors, `InIndex` climbing daily (88→92 over the last week). Traffic: 7 impressions / 0 clicks in 84 days, long-tail queries at avg position ~9–10. Meaning: content quality passes a real engine's indexer — Google's stall is authority/crawl-budget, not quality rejection; and indexation without authority earns ~nothing. Phase 3 confirmed as the only lever. Logged as a new "Bing baseline" section in docs/STRATEGY.md.
- **Submitted all 96 URLs via the BWT URL Submission API** (quota 100/day, 1,400/mo) to catch the 4 unindexed stragglers → HTTP 200 accepted. One-shot, not a nightly habit (monthly quota is small).
- **Filed the Reddit unblock ask to Josh** (`daily-in-box/ahf-question-2026-07-17.md`): 5-minute manual account creation with exact steps — site-owned email, non-branded handle suggestions, credential drop at `~/Documents/Environmental Variables/reddit.env.local`. Non-blocking; participation starts the session credentials appear. STRATEGY Phase 3 step 1 updated to reflect the block.

### Verified
- Indexing API: 96/96 success responses (both the re-fire and `--check` auth).
- BWT SubmitUrlBatch: HTTP 200, `{"d":null}` (API success shape).
- Live health (real-UA curl): homepage, /az/south-kaibab-gc-az, sitemap.xml all 200; sitemap 96 URLs. No site code changed tonight (docs only), no 404s.

### Learned
- Bing's `site:alwayshave.fun` operator shows 0 results even with 92 pages verified in the index via the BWT API — never diagnose Bing indexation from the `site:` operator.
- The BWT API key covers all sites on the account (`GetUserSites` → findingit.online, alwayshave.fun, breakingeven) — free diagnostics + URL submission with no new signup.
- Local env file has no Brevo key (Cloudflare-only secret) — subscriber count unreadable from here; moot while traffic is zero.

### Expect
- Google: if either 07-16/07-17 nudge works, crawl dates move within days; hard deadline ~07-23 to declare the lever inert.
- Bing: the 4 stragglers index within days of the batch submission; impressions stay ~zero until authority exists (watch monthly, not nightly).
- Reddit: blocked on Josh's 5 minutes; no response = continue on other angles per charter.

### Upcoming
- Next session: re-inspect the 3 Google baselines; re-fire request_indexing.py; check `~/Documents/Environmental Variables/reddit.env.local` — if credentials exist, start Phase 3 participation (rules first, data-first, no links).
- Mon 07-20: weekly report #2 (GSC WoW + Bing baseline now available as a second data series).

---

## 2026-07-16 — Session 10 (nightly)

### Oriented
- GSC still **0 clicks / 0 impressions** (7-day 07-09→07-13), sitemap still `pending`. Expected — nothing has been crawled yet.
- **Session 9's Indexing-API blocker is CLEARED.** Found `scripts/request_indexing.py` sitting untracked in the tree (built to use it) with a header noting the service account was made a GSC Owner + the Indexing API enabled in the `breakingeven` GCP project on 2026-07-15. Ran `--check` → `auth OK — nudged homepage`. The permission wall Session 9 hit is gone. (Auth uses the shared breakingeven service-account JSON; scope `.../auth/indexing`.)
- Crawl baselines (URL Inspection, to watch next session): homepage `last_crawl_time=2026-06-20` (still the gating date, unmoved since Session 8), `/az/south-kaibab-gc-az` "Crawled - currently not indexed" last `2026-05-01`, `/ut/the-narrows-zion-ut` "URL is unknown to Google."

### Decided
The binding constraint is the stalled homepage recrawl (Sessions 8–9): every on-site discovery fix is correct but inert until Google recrawls, and cadence is ~monthly on a zero-authority domain. The now-working Indexing API is the one free, owner-authenticated, hard-rule-safe lever that can nudge that recrawl on demand — exactly the action Session 9 queued for "if Josh enables it." So tonight = fire the crawl-nudge at the whole site.

### Did
- **Submitted all 96 sitemap URLs to the Google Indexing API** (`URL_UPDATED`), live-checked to 200 first: **96 submitted, 0 failed**. Quota used ~97/200 for the day. Covers homepage, all 46 trails, 5 state pages, /articles + 44 articles. Caveat (documented in the script header): the Indexing API is officially scoped to JobPosting/BroadcastEvent, so Google *may* ignore some page types — but it's free with no downside, and in practice it frequently triggers recrawls of arbitrary URLs. This is a shot at the indexation bottleneck, not a guarantee.
- **Committed `scripts/request_indexing.py`** — it was untracked; it's real, reusable infra (pulls URLs live from the sitemap, `--check`/`--only`/`--no-livecheck` flags, quota-aware). Belongs in the repo.

### Verified
- Indexing API auth proven live (`--check` → `auth OK`), then 96/96 publish calls returned success.
- Live health (real-UA curl): homepage 200, `/az/south-kaibab-gc-az` 200, `sitemap.xml` 200 with 96 `<loc>`. No 404s. (No site-rendering code changed this session — only the untracked helper committed.)
- Recorded the three crawl-date baselines above so next session can attribute any movement to tonight's nudge.

### Learned
- The Indexing API accepts our page types without error (96/96), even though they aren't job postings — Google takes the ping; whether it acts on it is the open question. First real test of whether this lever works on a content site.

### Expect
- If the nudge works, homepage `last_crawl_time` moves off 2026-06-20 within days (not the usual ~monthly wait), then the 46 static grid links get discovered → trails leave "URL unknown to Google." Watch all three baseline URLs next session. If crawl dates DON'T move within ~a week, the Indexing API is confirmed inert for content pages and Phase 3 distribution (real backlinks/authority) becomes the only remaining lever — no more on-site or API shortcuts left. Kill-or-revise on the whole indexation push still 2026-08-01.

### Upcoming
- **Next session: re-inspect the 3 baseline URLs first thing** — did the nudge move any crawl date? Re-run `request_indexing.py` (quota resets daily) to keep pinging until crawl dates move or the lever is proven dead.
- Phase 3 execution still queued (create site Reddit account, r/arizona + r/Utah, data-first contributions) — becomes top priority if the API nudge shows nothing.
- Next weekly report due Mon 2026-07-20.

---

## 2026-07-15 — Session 9 (nightly)

### Oriented
- GSC still **0 clicks / 0 impressions** (7-day 07-08→07-12; 28-day 26 query-rows, all 0). Sitemap still `pending`. Expected this early.
- **Homepage `last_crawl_time` = 2026-06-20** (URL Inspection API) — Google has NOT recrawled the homepage since the 07-14 static-grid fix shipped. So the grid fix cannot be evaluated yet; it only takes effect on the next homepage crawl (cadence ~monthly: 05-01 → 06-20 → next expected ~mid/late July). `/az/south-kaibab-gc-az` still "Crawled — not indexed"; sampled trails (Narrows, Calico Hills) still "URL unknown to Google." No propagation yet — because no recrawl yet, not because the fix is wrong.
- **Homepage's only external referrer in GSC is a spam domain** (`uplinke-seo-enhancement.za.com`). Zero legitimate authority → ~monthly crawl cadence. This confirms the binding constraint is authority/crawl-budget, exactly as Session 8 predicted.

### Decided
On-site Phase-1 work is complete and correct; the site is fully healthy (homepage/trail/sitemap all 200, sitemap 96 URLs). Nothing on-site moves the needle while we wait on a homepage recrawl we can't force. So tonight's highest-leverage action = attack the root constraint (authority) via **Phase 3 distribution groundwork** + try to **unblock a crawl-nudge lever**. No code changed this session (docs/planning only).

### Did
- **Tried the Google Indexing API** (owner-authenticated, legit, free) to nudge the stalled homepage recrawl → `Permission denied`: the service account isn't a GSC Owner and/or the Indexing API isn't enabled in the GCP project. Genuine permission wall (Josh console access) — filed a non-blocking question to unblock it (`daily-in-box/ahf-question-2026-07-15.md`, with the exact service-account email + the 2 steps). Logged the blocker in docs/STRATEGY.md open-questions §0.
- **Wrote a concrete, norm-respecting Phase 3 plan** into docs/STRATEGY.md: confirmed the timely hook (active July-2026 Western wildfire-smoke event across all 5 states — "is it too smoky to hike X this weekend" is exactly what the site answers with live cited AQI + go/no-go score); picked first 2 target communities (r/arizona, r/Utah — strongest coverage + active smoke); defined the durable, hard-rule-5-safe approach (lead with data + source, ≤10% self-reference, never link-drop); and set the next-session first steps (create ONE site-owned Reddit account per hard rule 7, read each sub's sidebar from inside, answer real conditions/smoke threads with timestamped data before ever referencing the site).

### Verified
- Live health (real UA curl): homepage 200, `/az/south-kaibab-gc-az` 200, `sitemap.xml` 200 with 96 `<loc>` entries. No 404s, nothing broken. No code changes to verify — this was a docs/planning session.
- Indexing API failure re-confirmed (single homepage call returns the permission error) — the blocker is real, not a transient.
- Reddit blocks automated fetches from this environment (curl JSON endpoint, WebFetch both blocked) — recorded so next session reads sub rules from inside the account rather than scripting it.

### Learned
- URL Inspection `last_crawl_time` on the homepage is THE gating metric right now: no homepage recrawl → no discovery of the 46 grid links → no downstream indexation, no matter how correct the on-site fixes are. Track this date weekly; it's the leading indicator ahead of impressions by weeks.
- The Indexing-API shortcut needs the service account added as a GSC **Owner** + the API enabled in GCP — neither is grantable without Josh's console access.

### Expect
- Homepage recrawl in the next ~1–2 weeks (per cadence) → discovers all 46 static trail links in one pass → trails begin leaving "URL unknown to Google." Watch homepage `last_crawl_time` moving off 2026-06-20 and `/az/south-kaibab-gc-az` off its 05-01 crawl. Kill-or-revise on the grid fix still 2026-08-01.
- If Josh enables the Indexing API, next session pings the homepage + key pages to accelerate that recrawl.

### Upcoming
- Next session: begin Phase 3 execution — create the site Reddit account, read r/arizona + r/Utah rules, make first genuine data-based contributions (no links). Log the account in docs/STRATEGY.md Distribution table.
- Weekly report already written this week (Session 8, 2026-07-14). Next weekly due Mon 2026-07-20.

---

## 2026-07-14 — Session 8 (nightly)

### Diagnosed
- **Nothing indexed since the 2026-07-10 fix.** URL Inspection on a page-type sample (homepage, trail, state, article): homepage still the ONLY indexed URL. /az/south-kaibab-gc-az still "Crawled — currently not indexed" with last crawl **2026-05-01** (Google has NOT recrawled it since the 07-10 body fix). Every other sampled URL — trails, state pages, /articles, articles — "URL is unknown to Google," never discovered. GSC still 0 clicks / 0 impressions (28-day, through 07-11).
- **Root cause of the discovery stall: the homepage trail grid is JS-only.** Homepage is the one page Google reliably crawls (last 2026-06-20). Raw Googlebot HTML had the 5 state footer links but **zero trail links** — the 40+ trail cards are injected by `renderListing()` at runtime. So each homepage crawl discovered only 5 state pages (2+ hops to trails, all still uncrawled), and the deep pages sat undiscovered. Same class of bug as the 07-10 trail-body fix, but on the homepage itself.

### Fixed
- **Server-rendered the homepage trail grid** (`scripts/build_index_html.py`, added to the 30-min pipeline after build_static.py). Bakes 46 real `<a href="/{state}/{slug}">` cards — grouped by state, sorted by score, same markup + CSS classes the JS produces — between new `<!-- GRID:START/END -->` markers in `index.html`. Scores refresh every 30 min (hard rule 4: no stale baked numbers). JS `renderListing()` still overwrites `#trail-listing` on load, so hydration is unchanged. One homepage crawl now exposes all 46 trail links directly (1 hop).

### Verified
- Local: script idempotent (re-run → same 46 links); exactly 1 GRID marker block.
- Live after deploy (~60s): Googlebot view = 46 unique trail links + 5 real region headings + markers intact for the next pipeline build; 6 sampled trail targets across AZ/CA/NV/UT → all 200.
- Headless Chrome hydration: 46 links post-JS, GRID markers gone (JS replaced the block, no duplication), no stuck "Loading…" spinner.
- Sitemap still valid XML, 96 URLs. No 404s introduced.

### Learned
- A JS-rendered homepage grid quietly starves the whole site of crawl discovery on a zero-authority domain: Google crawls only the homepage, sees no deep links, and never reaches anything. Static internal links on the highest-crawled page are the cheapest discovery lever available.
- URL Inspection `last_crawl_time` is the real Phase-1 dashboard right now — GSC clicks/impressions lag indexation by weeks and stay flat until pages actually get crawled+indexed. Track crawl dates, not impressions, week to week for now.

### Expect
- Next time Google crawls the homepage (roughly monthly cadence observed: 06-20, before that ~05-01), it should discover all 46 trail links in one pass and begin crawling trail pages. Watch `/az/south-kaibab-gc-az` for a last-crawl date newer than 2026-05-01, and sampled trails moving off "URL is unknown to Google." Kill-or-revise still 2026-08-01.

### Upcoming
- If the homepage crawl still doesn't propagate by next week, the binding constraint is crawl budget itself (zero backlinks) → Phase 3 distribution becomes the priority, not more on-site linking.
- Weekly report written this session (2026-07-14, first on/after Monday 07-13).

---

## 2026-04-04 — Session 1

### Added
- **Static HTML per trail** (`generated/{state}/{slug}.html`) — biggest SEO fix in the project. Every trail was sharing a single `trail.html` template; Google saw the same generic title and canonical for all 40 trails. Now each trail gets its own pre-rendered file with real title, canonical, meta description, OG tags, and schema baked in at build time. JS still updates live data on top for users.
- **`scripts/build_static.py`** — generates the 40 trail pages from conditions JSON + trail.html template. Runs every 30 min in the pipeline.
- **Worker routing** (`worker.js`) — updated to serve `generated/{state}/{slug}.html` first, falling back to `trail.html` if file is missing.

### Reasoning
SEO audit score was 41/100. Root cause: single-template architecture meant Googlebot saw zero unique trail URLs in raw HTML — only the homepage canonical appeared on every page. Static HTML per trail was the single highest-leverage fix available.

### Learned
- Cloudflare Pages Workers with `env.ASSETS.fetch()` can serve any file in the repo by URL — clean way to implement static-first with dynamic fallback.
- The `stefanzweifel/git-auto-commit-action` commits and pushes from Actions — need to `git pull --rebase` before any local push or you'll get non-fast-forward rejections.

### Upcoming
Wire up dog-friendly flags, state landing pages, and IndexNow submission.

---

## 2026-04-04 — Session 3

### Fixed
- **"Trail data unavailable" on all trail pages** — root cause: `build_static.py` was stripping `id="page-title"` from the `<title>` tag in the regex replacement. JS render() calls `getElementById('page-title')`, got null, threw TypeError, catch block showed error div. Fix: preserve the id attribute in the replacement string.
- **Article trail link wrong slug** — first article linked to `/az/wire-pass-to-buckskin-gulch` (made-up slug). Fixed to correct `/az/wire-pass-buckskin-az`.
- **`publish_article.py` trail frontmatter keys** — was reading `fm.get("trail")` but writer_bot outputs `trail_slug` and `trail_name`. Fixed key names so trail links in articles resolve correctly.
- **Schema never injected** — `build_static.py` tried to regex-replace an existing `<script type="application/ld+json">` block in trail.html, but trail.html had none. Schema was silently dropped. Fix: inject schema tag directly before `</head>` instead.

### Added
- **`/articles` index page** (`articles/index.html`) — was 404. Now a real crawlable archive page: CollectionPage schema, card grid with trail photos, newest-first sort, article count. Worker updated to serve it at `/articles`.
- **`scripts/build_articles_index.py`** — generates the articles index from all articles/*.html. Added to both pipeline runs (conditions + writer bot).
- **FAQPage schema on all 40 trail pages** — 5 pre-answered questions per trail: current conditions, dog-friendly, difficulty, AQI, best months. Targets "is [trail] safe today?" rich results in Google. This is the highest-ROI schema type for our query intent.
- **Writer bot multi-article support** — `--count N` flag, `--auto-publish` flag. Tracks recently-written slugs to avoid repeats (checks both drafts/ and articles/ dirs). Adds `trail_name` to frontmatter.
- **4 articles published today:**
  1. Wire Pass to Buckskin Gulch (from Session 2, Jake + Riley photo)
  2. Angels Landing — "Is It Worth the Chains?" — 100/100
  3. Bryce Canyon Rim Trail — April is peak season — 100/100
  4. Calico Hills Red Rock NV — Best day hike near Vegas — 100/100

### Changed
- **`writer_bot.yml`** — now writes 4 articles/day and auto-publishes (no review step). Commits to `articles/`, `photos/articles/`, `content/`.
- **`fetch_conditions.yml`** — added `build_articles_index.py` so articles index stays current on every 30-min data refresh.
- **`worker.js`** — added `/articles` route to serve index page.

### Learned
- FAQPage schema is the single highest-ROI schema addition for "should I hike X today?" query intent. Google shows these as expand/collapse rich results directly in the SERP.
- Internal linking from articles to trail pages (and between related trails) is the primary lever for distributing page authority. Articles need inline links to 2-3 contextual trails — not just the footer link.
- Weekly roundup posts ("Best 5 Trails in Utah This Weekend") capture high-intent voice search and comparison queries that individual trail pages miss.
- Real-time comparison cards (Angels Landing vs X) capture decision-point queries — build as a future feature once article volume is established.

### Plan: Days 2-5
- **Day 2 (Apr 5):** Dog-friendly guides + state roundups. Auto-bot handles 4 trail-condition articles. Manual: "Best Dog-Friendly Trails Nevada" + "Utah Weekend Hiking Roundup."
- **Day 3 (Apr 6):** Evergreen "best time to hike" guides for top 5 trails. Highest long-tail SEO value.
- **Day 4 (Apr 7):** Overlander and photographer persona content. Toroweap deep dive. Paria Canyon guide.
- **Day 5 (Apr 8):** State-level comprehensive guides. Internal linking audit. Sitemap resubmission to Google Search Console.
- **Ongoing tech:** Internal cross-links between articles, HowTo schema for difficulty ratings, comparison content format.

---

## 2026-04-04 — Session 2

### Added
- **`dog_friendly` column** in `seeds/trails.csv` — researched all 40 trails by land jurisdiction. 24 Yes (BLM, USFS, most state parks), 16 No (NPS — Zion, Bryce, Grand Canyon, Yosemite, RMNP — plus Havasupai tribal land, Hanging Lake, Kanarra Creek). Flows into conditions JSONs, trail meta descriptions ("Dogs welcome." / "No dogs on trail."), and schema.org PropertyValue.
- **State landing pages** (`generated/{state}/index.html`) — /nv, /ut, /az, /co, /ca were 302-redirecting to the homepage. Now each serves a real pre-rendered SEO page with unique title/canonical, full trail listing with baked-in live scores, dog-friendly counts, and state-specific intro copy. 5 new indexable URLs.
- **`scripts/build_state_pages.py`** — generates the 5 state pages from conditions data. Added to pipeline.
- **`scripts/indexnow.py`** — pings Bing and Yandex via IndexNow API after every 30-min data update. Submits all 46 URLs (40 trails + 5 states + homepage). Key: `3d00877f1b744d7898b2862b4c5e94fd`, file deployed to repo root.
- **Sunrise/sunset in pipeline** — added `sunrise` and `sunset` fields to Open-Meteo daily request. Now stored in each trail's forecast array. UI hasn't been wired yet.
- **Article publish pipeline** (`scripts/publish_article.py`) — converts reviewed markdown drafts to static HTML article pages at `articles/{slug}.html`. Handles frontmatter parsing, markdown-to-HTML conversion, photo copy to `photos/articles/`, Article + BreadcrumbList schema injection, and moves draft to `content/published/`.
- **Worker updated** — `/articles/{slug}` now routes to `articles/{slug}.html`.
- **First published article** — `articles/wire-pass-buckskin-az.html` — Wire Pass to Buckskin Gulch, 100/100 score. Jake & Riley hero photo. Full SEO head, Article schema.

### Changed
- **Dog name: Ruckus → Riley** — Josh corrected this. Updated everywhere: draft, writer bot persona prompt, and memory.
- **Writer bot model fallback** — was crashing on 429 (rate limit). Added retry loop with exponential backoff across three model endpoints: `gemini-2.0-flash` → `gemini-2.0-flash-lite` → `gemini-1.5-flash-latest`.
- **Worker `/state` routing** — changed from `302 redirect to /` to serving `generated/{state}/index.html`.

### Removed
- `.env.example` — deleted (was committed accidentally, credentials template not needed in repo).

### Learned
- Gemini API free tier rate-limits aggressively on the local machine but is fine in GitHub Actions (different quota window + IP). Don't rely on it for local testing — write drafts manually when needed.
- NPS land = no dogs on trails (with one exception: Great Basin NP allows leashed dogs). BLM and USFS are dog-friendly by default. This is a useful heuristic for expanding to new trails.
- `git push` with a PAT embedded in the URL (`https://{token}@github.com/...`) is the reliable fallback when credential helpers aren't configured locally.
- IndexNow is a one-shot POST — no ongoing maintenance. Bing indexes within hours of submission. Worth running on every data update, not just weekly.

### Upcoming
- Wire sunrise/sunset into `trail.html` UI (data is ready, just needs display)
- "Best time to hike [trail]" content pages — 40 pages, high long-tail SEO value
- Submit sitemap to Google Search Console if not already done
- Consider adding a `/articles` index page so the article archive is crawlable

---

## 2026-04-06 — Session 5

### Fixed
- **fetch_conditions.yml concurrent run merge conflicts** — two 30-min cron runs writing different JSON to same files would conflict on `git pull --rebase`. Fix: `git pull --rebase -X theirs` so the current run's fresh data wins.
- **Duplicate `fetch_conditions.yaml`** — old broken version (with `git reset --hard`, no concurrency block, missing scripts) was running alongside the correct `.yml`. Deleted the `.yaml`.
- **`if: secrets.CF_CACHE_PURGE_TOKEN != ''` syntax** — invalid in GitHub Actions `if` expressions. Changed to env var + bash conditional.
- **Writer bot Gemini 2.5 Flash truncation** — Gemini 2.5 Flash is a thinking model; its reasoning chain consumes output tokens before text output. With `maxOutputTokens: 1500`, only ~200 chars of text were written. Fixed: 8192 tokens + handle multi-part response to skip thought parts.
- **Misnamed article files** — `zion-narrows-top-down-ut.html` and `valley-of-fire-wave-rock-nv.html` were wrong slug names (didn't match trail data slugs). Replaced with correct `narrows-top-down-zion-ut` and `wave-rock-valley-of-fire-nv`.
- **Articles missing from sitemap** — 14 articles were live but not in sitemap.xml. Google couldn't discover them. Added article URLs (+ state landing pages; removed phantom `/state/` and `/region/` URLs).
- **Article meta descriptions** — all articles were using `{title} — trail conditions guide...` as meta description instead of the specific `meta_description` from frontmatter. Fixed.

### Added
- **7 new articles published today** (17 total):
  - The Narrows (Bottom-Up) UT — 100/100
  - River Mountains Loop NV — 100/100, dog-friendly
  - Kanarra Creek Slot Canyon UT — 100/100, permit required
  - Paria Canyon AZ — 100/100, 38-mile multi-day
  - Hermit Trail GC AZ — 90/100 (bot-generated with Gemini 2.5 Flash)
  - Petroglyph Canyon Gold Butte NV — 90/100 (bot-generated)
  - Bright Angel Trail GC AZ — 90/100, highest-traffic GC query
  - West Fork Oak Creek AZ — 100/100, dog-friendly, Sedona
  - Garden of the Gods CO — 70/100, first Colorado article
- **Sunrise/sunset on forecast cards** — `☀️ HH:MM–HH:MM` below each day's forecast card. Data was already in conditions JSON from Open-Meteo, just not displayed.
- **Related article cross-links** — each article now shows "More Jake's takes from [State]" with links to 3 other published articles from same state. Bidirectional linking.
- **Trail → article link** — trail detail pages now show "Jake's Take" link if an article exists for that trail (JS HEAD request check).
- **CF_CACHE_PURGE_TOKEN** and **CLOUDFLARE_ZONE_ID** added to GitHub Actions secrets.
- **Writer bot voice prompt** — rewrote with verbatim Wire Pass excerpt as gold-standard voice reference + 7 specific rules. No preamble, data → ground truth, direct risk callout, parenthetical color, closing push, banned words.

### Changed
- **Gemini model list** — `gemini-1.5-flash` (now 404) and `gemini-1.5-flash-8b` removed. Replaced with `gemini-2.5-flash` as primary (works on free tier), 2.0-flash/lite as fallbacks.
- **ANTHROPIC_API_KEY** — not yet in GitHub Actions secrets. Writer bot falls back to Gemini 2.5 Flash successfully. STILL NEEDED for Claude Haiku as primary generator.

### Learned
- Gemini 2.5 Flash is a thinking model — its reasoning chain consumes output tokens before visible text. Need 8192 max tokens, not 1500. Also returns multi-part content (thought + text parts).
- Concurrent GitHub Actions cron runs with 30-min schedule will both write to the same JSON files and conflict on push. `-X theirs` in rebase resolves this with the current run's data winning.
- Two workflow files with the same name but different extensions (`.yaml` + `.yml`) both run — GitHub treats them as separate workflows. This created a race condition where both ran on schedule.
- `secrets` context is not available in `if` expressions at the step level — use env var exposure + bash conditional instead.

### Upcoming
- ANTHROPIC_API_KEY — Josh needs to create at console.anthropic.com and add to repo secrets
- Vehicle requirements column in seeds/trails.csv → overlander queries
- Weekly roundup articles ("Best 5 hikes this weekend in Utah") — Thu/Fri schedule
- Remaining 23 trails without articles — bot generating 4/day, ~6 days to full coverage
- HowTo schema for difficulty ratings

---

## 2026-07-10 — Session 6 (first autonomous session under AUTONOMY.md)

### Diagnosed
- **GSC: 0 clicks, 7 impressions in 180 days.** URL Inspection API showed: homepage indexed; /az/south-kaibab-gc-az "Crawled — currently not indexed" (last crawl 2026-05-01); every other sampled URL (trails, articles, state pages) "URL is unknown to Google".
- **Root cause:** generated trail pages had unique meta but an EMPTY body — Google received "Loading trail conditions…" and em-dash placeholders (734 chars of boilerplate). It rejected the one page it crawled as thin and never came back. FAQPage schema also existed with no visible FAQ (guideline violation risk).

### Fixed
- **build_static.py now server-renders the full trail page body** at build time (runs every 30 min in the pipeline): hero (name/score/label/timestamp), quick stats, metric cards, trail info, status list with honest fire risk from FIRMS data (the JS hardcodes "Fire Risk: Low" — static render uses real data), 5-day forecast, notes, a **visible FAQ section** matching the FAQPage schema, and a **"More {State} Trails" card** with 6 same-state links by current score (internal crawl mesh). Visible text: 734 → ~2,345 chars, all unique per trail. JS hydration unchanged and verified (render() overwrites the same nodes).
- **"Trail Trail" title dup** — "South Kaibab Trail Trail Conditions" → "South Kaibab Trail Conditions" (build_static.py + trail.html JS).
- **Homepage footer** — added /ca, /co, /dog-friendly static links (were missing; only nv/ut/az present).

### Verified
- 46 pages regenerated, 0 errors, 0 missing anchors; sweep of all generated pages: no thin bodies, no dup titles, FAQ present, content unhidden.
- Live after push (~105s deploy): faq-card + related-card serving on /az/south-kaibab-gc-az and /ut/the-narrows-zion-ut; spot-checked 3 trail URLs = 200; sitemap valid XML, 96 URLs.
- Headless Chromium on the live page: JS hydrates cleanly ("Updated 33 min ago"), 5 forecast days, zero console errors.
- IndexNow → 200 (53 URLs; key from repo root key file — INDEXNOW_KEY is not in the local env file, only GH secrets). Sitemap resubmitted via GSC API (submit accepted, still "pending").

### Learned
- The local env file breaks shell `source` (multi-line service-account JSON) — parse with Python regex instead.
- CLOUDFLARE_API_TOKEN only sees the `gates` Pages project (not touched — hard rule 2). The main site's deploy quota couldn't be verified with it; deploys have run ~48/day since April without failure, so not urgent. Check Workers Builds quota next session.
- GSC's only 2 impressions ever were "is south kaibab trail open" / "south kaibab trail weather" — the target query shape is validated, the site just wasn't indexable.

### Expect
- Google re-crawls over 2–6 weeks; watch weekly for "Crawled — not indexed" → "Indexed" and first impressions. Kill-or-revise review 2026-08-01 (per docs/STRATEGY.md).

### Upcoming
- Weekly: re-inspect sample URLs, GSC WoW compare (first weekly report due next Monday session).
- Verify Cloudflare build quota; confirm articles are fully static + linked from trail pages; Phase 3 (distribution) groundwork.

### Post-session addendum (2026-07-10, supervising session)
- **Pipeline race found + self-healed.** The 19:35Z SEO push raced a scheduled pipeline run that had checked out the pre-fix tree; its `-X theirs` rebase produced Frankenstein generated pages (new FAQ sections kept, but "Trail Trail" titles reverted). The NEXT scheduled run regenerated everything from the fixed build_static.py — verified on origin: title correct, FAQ present. **Lesson: generated/ pages are build artifacts — after any push that changes scripts/, either confirm no pipeline run was mid-flight or wait one 30-min cycle before verifying titles/content on live.** Never hand-edit generated/ files.
- **Runner heartbeat bug fixed.** bash under launchd can't write ~/Documents (TCC) — the heartbeat line now goes through `python3 heartbeat.py ahf_operator` (proven pattern). Today's line was backfilled manually; session exit was a genuine 0.

---

## 2026-07-11 — Session 7 (first unattended nightly session)

### Diagnosed
- **Cloudflare quota ⚠️ from last session resolved.** The site is NOT on Cloudflare Pages — it's a git-connected **Worker with static assets** (`alwayshave-fun`, wrangler.toml `[assets]`), so the feared 500-builds/mo Pages cap never applied. Real constraint: Workers Builds 3,000 build-min/mo. Empirical: May 2,159 and June 2,151 builds completed with zero deploy failures ⇒ avg build <1.4 min, but headroom was thin (~28%). CF API token can't read it directly (scoped to `gates` project only — untouched per hard rule 2); asked Josh non-blocking to widen scope (`daily-in-box/ahf-question-2026-07-11.md`).
- **GitHub Actions minutes: non-issue.** Repo is PUBLIC → unlimited free minutes.
- **Pipeline cadence crept to every 20 min** (worker cron `*/20`) — 72 runs/day vs the documented "updated every 30 min" promise. Pure quota burn, no user-visible gain.
- **Trail→article links were JS-only** (HEAD-request insert) — invisible to Google's first-pass crawl. 57 published articles were reachable only via sitemap + article↔article links; trail pages passed them zero link equity. Article coverage is now 46/46 trails.

### Fixed
- **Static persona article links** — build_static.py now renders `<a id="jakes-take">` on every trail page whose slug has an article (46/46), with the correct persona per state (Jake AZ/UT/NV, Olivia CA, John CO — the old JS said "Jake" even on CA/CO pages). trail.html hydration now skips insertion when the static link exists (no duplicates) and uses the same persona map.
- **Worker cron `*/20` → `*/30`** — ~2,150 → ~1,440 builds/mo, ~2× Workers Builds headroom, matches the site's documented cadence.

### Verified
- Local: 46 pages regenerated, 0 errors; HTML-parsed all 52 generated pages — exactly 1 article link on each trail page, 0 on index pages.
- Waited out an in-flight 04:20Z pipeline run before pushing (lesson from Session 6 addendum — no race this time). Pushed a425e1c8ff.
- Live after deploy: static link serving on /az/wire-pass-buckskin-az, /ca/bishop-pass (Olivia), /co/garden-of-the-gods (John); article target 200; sitemap valid (96 URLs, 44 articles + /articles index).
- Headless Chrome on live page: exactly 1 `#jakes-take` after hydration, "Updated 14 min ago" renders, no duplicate.
- Cron change: no run fired at 04:40Z (old */20 slot) after the ~04:37Z deploy — trigger applied. Final confirmation pending the 05:00Z run (see below).
- GSC pulse: 0 clicks / 0 impressions last 7 days, sitemap "pending" — expected this early; baseline logged for Monday's first weekly report.

### Learned
- launchd session PATH lacks /opt/homebrew/bin — `gh` needs an explicit PATH export.
- `git pull --rebase` autostash can report "changes safe in the stash" yet leave a redundant entry even when everything applied; verify with `git diff stash@{0} HEAD` before dropping.
- Watch for pipeline runs in flight (`gh run list -w fetch_conditions.yml`) before any push touching scripts/ or generated/ — worked cleanly tonight.

### Expect
- Articles start getting crawled via trail pages within days of Google's re-crawl; article impressions become measurable in GSC 2–4 weeks out. Tracked as an experiment row in docs/STRATEGY.md.

### Upcoming
- Monday (2026-07-13): first weekly report — GSC WoW, URL re-inspection sample.
- Confirm pipeline runs land at :00/:30 (if still :20/:40, cron didn't apply — investigate).
- Phase 3 groundwork: pick 1–2 hiking communities, read norms before participating.

### Session 7 close-out (verified before exit)
- 05:00:52Z pipeline run fired (and none at 04:40) — `*/30` cron confirmed live; run completed success in ~15 min.
- Live page after that run's deploy: fresh data ("Updated 2026-07-11 05:06 UTC"), exactly 1 article link, FAQ card intact — CI regenerates correctly with the new build_static.py. No race, nothing left half-shipped.
