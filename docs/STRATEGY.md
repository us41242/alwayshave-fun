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

Target query shapes (all served by trail pages already): "is {trail} open", "{trail} weather", "{trail} conditions", "{trail} AQI/air quality", "are dogs allowed {trail}", "best time to hike {trail}".

## Distribution accounts

(none yet — log platform, handle, credential location for every account created)

## Free-services ledger

| Service | What for | Free-tier ceiling | Current usage |
|---|---|---|---|
| Cloudflare Pages | hosting + deploys | 500 builds/mo ⚠️ | ~48 data commits/day = ~1,440 deploys/mo — NEEDS VERIFICATION next session; if over, batch commits or skip CI deploys on data-only pushes |
| GitHub Actions | data pipeline cron | 2,000 min/mo (private repo) | fetch_conditions every 30 min |
| Open-Meteo | weather + AQI fallback | non-commercial free | every 30 min |
| AirNow | AQI | free API key | every 30 min |
| NASA FIRMS | fire data | free | every 30 min |
| Gemini (writer bot) | drafts | free tier | 1/day |
| Brevo | subscriber email | 300 emails/day | idle |
| IndexNow (Bing/Yandex) | index pings | free, no known cap | 53 URLs per data update |

## Open questions / next session

1. **Verify Cloudflare Pages build quota** (see ⚠️ above) — if the repo is git-connected and every data commit triggers a build, 48/day may exceed the free 500/mo. Check the Pages dashboard via API token in the env file.
2. Weekly GSC check: re-inspect the sampled URLs, watch for first impressions.
3. Articles (/articles/*.html): confirm they're fully static (they should be) and internally linked from trail pages.
4. Phase 3 groundwork: pick 1–2 communities, read norms first, participate before ever linking.
