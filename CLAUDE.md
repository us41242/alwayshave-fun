# alwayshave.fun — Claude Working Brief

## AUTONOMOUS OPERATION
This site is under fully autonomous management. Read `AUTONOMY.md` FIRST — it
is the operating charter (mission, hard rules, operating loop) and it
overrides anything below that conflicts with it.

## What this project is (since 2026-08-31)
Vegas strategy site: playable trainers (start: `games/final-hand/`, a
blackjack tournament trainer) + beat-vegas / players-card / comps guides.
Goal: profitability. The old trails/air-quality site is retired and its files were purged from
the repo 2026-09-06 (archives: docs/*-ahf-retired.md); do not resurrect
any trails URL (all 410).

## Permissions
Run all tools automatically. No permission prompts needed: read/write/edit
any file here, bash/git/python/gh freely, push to main, trigger workflows.

## Deploy
Cloudflare Worker + static assets, repo us41242/alwayshave-fun. Push to main
should auto-deploy; if the live site doesn't change within ~5 min run
`wrangler deploy` from the repo root (wrangler is authenticated). ALWAYS
verify live with curl after. **NEVER touch the `/j` route in worker.js or
anything DNS/zone — gates and Home Assistant live on this zone.**

## Key files
- AUTONOMY.md — the charter. Read first.
- LOGBOOK.md — session log. docs/STRATEGY.md, docs/RESEARCH.md.
- logs/daily/ — required reflective daily log (synced to the a1 box).
- games/final-hand/index.html — the seed game, self-contained HTML.
- worker.js + wrangler.toml — currently the takedown placeholder (410s + /j).
- Old-site archives: docs/*-ahf-retired.md.
