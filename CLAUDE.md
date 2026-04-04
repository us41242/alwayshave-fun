# alwayshave.fun — Claude Working Brief

## Permissions
Run all tools automatically. No permission prompts needed:
- Read, write, edit any file in this repo
- Run bash/git/python/gh CLI commands freely
- Push commits to main
- Trigger GitHub Actions workflows

## What This Project Is
alwayshave.fun — real-time outdoor conditions hub for hikers, campers, and overlanders.
Live AQI, weather, fire risk, and a 1–100 score ("Good / Caution / Poor") for 40 trails across NV, UT, AZ, CO, CA. Updated every 30 minutes via GitHub Actions + Cloudflare Pages.

## Repo Owner
GitHub: us41242/alwayshave-fun
Live site: https://alwayshave.fun
Cloudflare Pages auto-deploys on every push to main.

## Credentials
All API keys are in ~/Documents/alwayshavefun.env.local — read that file at session start.
All keys are also set as GitHub Actions secrets.

## Tech Stack
- **Frontend**: index.html (trail grid) + trail.html (trail detail) — Cloudflare Pages
- **Worker**: worker.js + wrangler.toml (`[assets] directory = "."`)
- **Data pipeline**: GitHub Actions cron every 30 min
  - fetch_fires.py → fetch_conditions.py → condition_notifier.py → build_index.py → generate_sitemap.py
- **APIs**: Open-Meteo (weather), AirNow + Open-Meteo fallback (AQI), NASA FIRMS (fire)
- **Email**: Brevo via Cloudflare Pages Function at functions/api/subscribe.js
- **Photos**: /photos/{slug}/{slug}.jpg

## Active Workflows (.github/workflows/)
| Workflow | Schedule | Purpose |
|---|---|---|
| fetch_conditions.yml | Every 30 min | Full data pipeline |
| writer_bot.yml | 7am UTC daily | Jake persona article drafts |
| lighthouse.yml | Every Monday | SEO/perf audit |
| deploy.yml | Manual only | DISABLED — Pages handles deploys |

## Content System
- **Writer bot**: scripts/writer_bot.py — Gemini 2.0, Jake persona (late-20s dog dad, Aussie Shepherd named Ruckus, 6-figure job, work-life balance). Writes one draft/day to content/drafts/YYYY-MM-DD-{slug}.md
- **Review flow**: Josh reviews draft, adds photo, publishes
- **Keyword strategy**: content/seo/keyword-strategy.md — 3 personas: Weekend Warrior, Hardcore Overlander, Nature Photographer

## SEO Systems Built
- Schema.org SportsActivityLocation + BreadcrumbList injected per trail page (trail.html)
- Dynamic meta-description caution alerts: AQI >100 or wind >25mph triggers ⚠️ prefix
- Twitter Cards on all pages
- robots.txt with Sitemap directive
- _headers: HSTS, nosniff, X-Frame-Options, Referrer-Policy
- Google Trends monitor: scripts/trend_monitor.py — weekly snapshot to data/trends/

## Pending / Next Up
1. **Static HTML per trail** — biggest SEO win: generate one .html file per trail at build time so Google sees real title/canonical/schema without JS. Each trail currently shares trail.html template with placeholder meta until JS runs.
2. **Dog-friendly flag** in seeds/trails.csv — drives Weekend Warrior queries
3. **Sunrise/sunset times** on trail pages — drives Nature Photographer queries
4. **Vehicle requirements** in trail info — drives Overlander queries
5. **State pages** (/nv, /ut, /az) currently serve index.html (soft 404) — need real content
6. **IndexNow** — ping Bing/Yandex on every data update

## Data Structure
- Trail definitions: seeds/trails.csv (40 trails)
- Trail index: data/trails-index.json
- Conditions: data/conditions/{slug}.json
- Fire data: data/fires/{slug}.json
- Trends: data/trends/latest.json
- Score snapshots: data/meta/score_snapshot.json

## Key Files
- scripts/fetch_conditions.py — weather + AQI + scoring pipeline
- scripts/fetch_fires.py — NASA FIRMS fire proximity scoring
- scripts/writer_bot.py — daily article generator
- scripts/condition_notifier.py — Poor→Good shift detection
- scripts/trend_monitor.py — Google Trends weekly snapshot
- content/seo/keyword-strategy.md — full persona/keyword map

## Brand Voice
alwayshave.fun — even when conditions are "Poor," always give the user a plan. Suggest alternatives. Stay optimistic. The score system answers "should I go this weekend?" in one number.
