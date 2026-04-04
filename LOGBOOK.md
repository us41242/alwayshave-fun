# alwayshave.fun — Daily Logbook

Running record of every decision made, why it was made, what was learned, and what's coming next. Updated each session.

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
