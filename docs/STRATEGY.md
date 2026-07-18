# Strategy — living document

Maintained by the autonomous operator (see /AUTONOMY.md). Rewrite freely; LOGBOOK.md holds history, this holds the present.

## Situation assessment (2026-07-10, first autonomous session)

The site is functionally excellent and completely invisible. GSC shows **0 clicks, 7 impressions in 180 days**. Root causes found and confirmed via URL Inspection API:

1. **Homepage**: indexed ✓ (the only page that is).
2. **Trail pages**: served to Google as empty JS shells ("Loading trail conditions…", all values "—"). The one page Google crawled (/az/south-kaibab-gc-az, 2026-05-01) → "Crawled — currently not indexed" = quality rejection. Google then stopped crawling entirely.
3. **Most URLs**: "URL is unknown to Google" — never discovered despite the sitemap, because a zero-authority domain with one thin crawl gets ~no crawl budget.
4. FAQPage schema existed with no visible FAQ content (guideline violation risk).

## Current strategy

**Phase 1 (now): earn indexation.** Fixed 2026-07-10 — trail pages are now fully server-rendered at build time (score, metrics, forecast, notes, visible FAQ, related-trail links), refreshed every 30 min by the pipeline. Sitemap resubmitted, IndexNow pinged. Expect: Google re-crawls over 2–6 weeks; watch "Crawled — not indexed" → "Indexed" transitions weekly via URL Inspection API (quota ~2000/day, sample ~20 URLs weekly).

**Phase 2 (once pages index): win long-tail conditions queries.** The moat is freshness + honesty: live "is X open / X weather / X AQI / can I bring my dog to X" queries where AllTrails serves stale static content. GSC's two only-ever impressions were exactly this shape ("is south kaibab trail open", "south kaibab trail weather") — the demand is real.

**Phase 3 (needs authority): distribution.** Zero backlinks is the binding constraint after indexation. Genuine participation in hiking communities (per charter distribution rules), useful free tools/data others want to cite. Groundwork started 2026-07-15 (plan below).

### Bing baseline (discovered 2026-07-17)

The site is already verified in Bing Webmaster Tools (shared API key in `~/.config/claude-seo/`, same account as breakingeven/findingit). **Bing has 92/96 pages in its index**, crawls ~5–13 pages/day, sitemap known (96 URLs, last fetched 07-15), zero crawl errors. But traffic is ~zero: 7 impressions / 0 clicks in 84 days (long-tail queries like "april wether for havasu falls" at avg position ~9–10). Two conclusions: (1) the content is indexable and clean — Google's refusal is a crawl-budget/authority problem, not a quality rejection; (2) indexation alone earns nothing at zero authority — ranking is the constraint on both engines, which is exactly what Phase 3 attacks. All 96 URLs submitted via the BWT URL Submission API 2026-07-17 (quota 100/day, 1,400/mo — do not burn this nightly; it's for new/changed pages).

### Phase 3 plan — genuine community participation (2026-07-15)

Confirmed binding constraint: the homepage is Google's only reliably-crawled page and its last crawl is **2026-06-20** (cadence ~monthly, e.g. 05-01 → 06-20). The 07-14 static grid fix can't propagate until Google recrawls the homepage, and recrawl frequency on a zero-authority domain is itself gated by having ~no backlinks — the only external referrer GSC shows for the homepage is a spam domain (`uplinke-seo-enhancement.za.com`). So authority/distribution is now the real lever, not more on-site work.

**Timely hook (act while it lasts):** July 2026 is an active Western wildfire-smoke event — moderate AQI across all 5 of our states (CO/UT/AZ/NV/CA), some areas unhealthy-for-sensitive-groups (confirmed via news, 2026-07-15). "Is it too smoky to hike {trail} this weekend?" is exactly the question the site answers with live AirNow/Open-Meteo AQI + a go/no-go score + timestamped source. This is a genuine, time-sensitive reason to participate — not a link-drop pretext.

**Approach (durable, per hard rule 5 — genuine participation, never link drops):**
- Lead with the *answer and the data*, cited to the source (AirNow / Open-Meteo), in the community's own thread. Mention the site only when it genuinely adds value or someone asks "where do you check that." 90/10 rule (≤10% self-referential). One ban ends the channel — durable beats fast.
- Reddit blocks automated fetches (verified: curl, WebFetch, and JSON endpoint all blocked 2026-07-15), so each target sub's sidebar rules must be read from inside the account before posting there — that IS step 1, not an afterthought.

**Target communities (start with 2, expand only after building a genuine history):**
1. **r/arizona** — strongest state coverage (Grand Canyon: South Kaibab/Bright Angel/Hermit, Sedona, Paria). High volume, AZ smoke active now.
2. **r/Utah** — Zion/Bryce/Narrows coverage; high volume; UT smoke active now.
3. Later: r/Nevada, r/ColoradoHiking / r/hikingcolorado, r/CaliforniaHiking, r/hiking (~2M, strict self-promo — comment participation only), r/overlanding (overlander persona), niche r/AZhiking / r/utahhiking.

**Next-session first steps:**
1. ~~Create ONE site-owned Reddit account~~ **Blocked on Josh (2026-07-17):** Reddit signup = email verification + CAPTCHA, a human gate that must not be automated past (ban risk, hard rule 5). Asked Josh for the 5-minute manual creation (`daily-in-box/ahf-question-2026-07-17.md`, exact steps + credential drop location `~/Documents/Environmental Variables/reddit.env.local`). Once credentials appear: read sub rules from inside, participate data-first, log the account in the Distribution table below.
2. Read the sidebar rules of r/arizona + r/Utah from inside the account.
3. Find 2–3 current threads genuinely asking about conditions/smoke/"is X open"; answer with real timestamped data, no link. Build history before ever referencing the site.

**Candidate durable asset (future, not built — YAGNI until participation proves demand):** a shareable per-trail "smoke check" view someone would naturally cite. Note only; do not build speculatively.

## Target queries / experiments in flight

| Experiment | Started | Expect | Review |
|---|---|---|---|
| Server-rendered trail bodies + FAQ + internal links | 2026-07-10 | trail pages move to "Indexed"; impressions > 0 | weekly; kill-or-revise by 2026-08-01 |
| Homepage footer → /ca /co /dog-friendly static links | 2026-07-10 | state pages discovered | same |
| Static trail→article links (46/46, persona-correct) | 2026-07-11 | articles discovered & indexed via trail pages; article impressions | same |
| Server-rendered homepage trail grid (46 static links) | 2026-07-14 | next homepage crawl discovers all trails in 1 hop; sampled trails leave "URL unknown to Google" | weekly; kill-or-revise 2026-08-01 |

Target query shapes (all served by trail pages already): "is {trail} open", "{trail} weather", "{trail} conditions", "{trail} AQI/air quality", "are dogs allowed {trail}", "best time to hike {trail}".

## Distribution accounts

(none yet — log platform, handle, credential location for every account created)

## Free-services ledger

| Service | What for | Free-tier ceiling | Current usage |
|---|---|---|---|
| Cloudflare Workers Builds | hosting + deploys (git-connected Worker `alwayshave-fun` with static assets — NOT Pages, so the 500-builds/mo Pages cap never applied) | 3,000 build-min/mo | was ~2,150 builds/mo (May 2,159, June 2,151 — both completed with no deploy failure ⇒ avg build <1.4 min); cron cut */20→*/30 on 2026-07-11 → ~1,440/mo, ~2× headroom. Direct quota read blocked: CF API token is scoped to the `gates` project only (question filed to Josh 2026-07-11) |
| GitHub Actions | data pipeline cron | repo is PUBLIC → minutes unlimited/free | fetch_conditions every 30 min |
| Open-Meteo | weather + AQI fallback | non-commercial free | every 30 min |
| AirNow | AQI | free API key | every 30 min |
| NASA FIRMS | fire data | free | every 30 min |
| Gemini (writer bot) | drafts | free tier | 1/day |
| Brevo | subscriber email | 300 emails/day | idle |
| IndexNow (Bing/Yandex) | index pings | free, no known cap | 53 URLs per data update |

## Open questions / next session

0. **Indexing-API crawl-nudge: unblocked 2026-07-15 (Josh), fired 07-16 and 07-17** — all 96 URLs both nights via `scripts/request_indexing.py` (quota 200/day). As of 07-17 no crawl-date movement yet (homepage 06-20, South Kaibab 05-01, Narrows unknown). Keep re-firing nightly through ~07-23; if no crawl date moves by then, declare the lever inert for content pages and stop.

1. Weekly GSC check: re-inspect the sampled URLs via URL Inspection API, watch `last_crawl_time` on the homepage and on /az/south-kaibab-gc-az (still 2026-05-01 as of 07-14 — Google has not recrawled trails since the 07-10 fix). GSC still 0 clicks / 0 impressions through 07-11. **Discovery bottleneck found 07-14: homepage grid was JS-only → no static trail links → deep pages never discovered. Fixed (server-rendered grid). If the next homepage crawl still doesn't propagate to trails, crawl budget (zero backlinks) is the binding constraint → prioritize Phase 3.**
2. Confirm the worker cron actually fires at :00/:30 now (watch Actions run timestamps; deployed 2026-07-11 ~04:40Z). If runs still land at :20/:40, the trigger didn't apply — investigate.
3. Phase 3 groundwork: pick 1–2 communities, read norms first, participate before ever linking.
4. Asked Josh (non-blocking, 2026-07-11): widen CF API token to read Workers Builds for the main account so build-minute usage can be verified directly.
