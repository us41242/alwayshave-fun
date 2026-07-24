# alwayshave.fun — Daily Logbook

Running record of every decision made, why it was made, what was learned, and what's coming next. Updated each session.

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
