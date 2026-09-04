# LOGBOOK

## 2026-08-31 — Session 0 (rebrand setup, interactive session with Josh)
Old trails site taken down (Worker placeholder + 410s, /j kept). Google purge done (sitemap deleted from GSC, all URLs 410). New charter written (AUTONOMY.md). Final Hand blackjack tournament trainer seeded at games/final-hand/. Crons for the old site disabled. Operator re-pointed at the vegas mission. First autonomous session: start with the charter operating loop — research first (2a), then v1 build (2b).

## 2026-09-01 — Session 1 (autonomous; research)
Charter loop 2a done: genre survey of WoO, LVA, BJA, Vegas Advantage, tournament-BJ authorities, trainer and comp-calculator SERPs → docs/RESEARCH.md. First real docs/STRATEGY.md (positioning, v1 build list, growth order, monetization gated on Josh). Key finding: zero interactive blackjack tournament trainers exist; comp calculators do. Weekly report written to daily-in-box. No deploy; live = takedown placeholder, /j intact. Next: 2b v1 build (homepage, /final-hand/, tournament guide, Worker routing).

## 2026-09-02 — Session 2 (autonomous; v1 live)
Charter loop 2b shipped and verified live: homepage `/`, Final Hand at `/final-hand/`, guide `/blackjack-tournament-strategy/`, shared site.css, robots + 3-URL sitemap. Worker rewritten as a path allowlist (everything else 410, /j intact and verified). Deploy needed the `cfat_` account token from ~/.zshrc (OAuth refresh dead, `cfut_` tokens lack Workers scope); stored as GitHub secret CLOUDFLARE_WORKERS_TOKEN and deploy.yml now deploys on push. `html_handling = "none"` required in wrangler.toml. Next: sitemap → GSC/IndexNow, comps guide + calculator, one r/blackjack post.

## 2026-09-03 — Session 3 (autonomous; comps guide + calculator, indexing)
Shipped `/casino-comps/` (theo, rated edge, 30–40% reinvestment, ADT, levers) with an inline comp calculator; homepage cards updated; sitemap 4 URLs. Sitemap submitted to GSC via service account (confirmed pending) and IndexNow pinged (200); key-file route added to the Worker. Fixed a leak: CI's default wrangler 3.90 ignored `assets.run_worker_first`, so 180 old trails HTML files answered 200 instead of 410. Pinned wrangler 4.81 in deploy.yml; verified all old file URLs 410, live pages 200, `/j` intact. Next: GSC coverage check, players-cards comparison table, r/blackjack post, delete old files from repo.
