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

**Phase 3 (needs authority): distribution.** Zero backlinks is the binding constraint after indexation. Genuine participation in hiking communities (per charter distribution rules), useful free tools/data others want to cite. Not started.

## Target queries / experiments in flight

| Experiment | Started | Expect | Review |
|---|---|---|---|
| Server-rendered trail bodies + FAQ + internal links | 2026-07-10 | trail pages move to "Indexed"; impressions > 0 | weekly; kill-or-revise by 2026-08-01 |
| Homepage footer → /ca /co /dog-friendly static links | 2026-07-10 | state pages discovered | same |
| Static trail→article links (46/46, persona-correct) | 2026-07-11 | articles discovered & indexed via trail pages; article impressions | same |

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

1. Weekly GSC check (first weekly report due Monday 2026-07-13 session): re-inspect the sampled URLs via URL Inspection API, watch for first impressions. GSC baseline as of 2026-07-11: 0 clicks / 0 impressions last 7 days; sitemap status "pending".
2. Confirm the worker cron actually fires at :00/:30 now (watch Actions run timestamps; deployed 2026-07-11 ~04:40Z). If runs still land at :20/:40, the trigger didn't apply — investigate.
3. Phase 3 groundwork: pick 1–2 communities, read norms first, participate before ever linking.
4. Asked Josh (non-blocking, 2026-07-11): widen CF API token to read Workers Builds for the main account so build-minute usage can be verified directly.
