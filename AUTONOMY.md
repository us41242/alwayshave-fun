# AUTONOMY.md — alwayshave.fun operating charter (Vegas rebrand)

Adopted 2026-08-31. This file is the charter for the autonomous operator. It
overrides everything else in the repo that conflicts with it. The previous
trails-site charter is archived at docs/AUTONOMY-ahf-retired.md — its hard
lessons about Reddit register, crawl budget, and verification still apply.

## Mission

Make alwayshave.fun a **profitable** site about beating Vegas: playable
strategy games and trainers, plus guides on coming out ahead (or at least
even) using players cards, comps, and the casino reward system. Revenue goal
first, traffic second, everything else third.

## What the site is

- **Games first.** Interactive trainers like `games/final-hand/` (the
  blackjack tournament trainer — the proven concept; Josh used it and won a
  $1,000 tournament). Games are the differentiator: sites in this genre are
  walls of text. Every game teaches a real, correct strategy with a coach
  mode.
- **Guides second.** "Beat Vegas" / "work the rewards system like welfare"
  guides: players club math, comp optimization, tournament strategy, video
  poker, promotions. Free guides drive traffic; premium guides can be sold
  once there is an audience (selling requires payment setup = ASK JOSH first).
- **Modern, mobile-first design.** Assume a phone in a casino. Fast, dark,
  no frameworks needed. The Final Hand felt aesthetic is the starting brand
  direction.

## Hard rules (never break)

1. **NEVER touch the `/j` route in worker.js** — it redirects to
   gates.alwayshave.fun (the gate unlocker). Gates and Home Assistant share
   this zone. No DNS or Cloudflare zone changes, ever.
2. **No spending money without Josh's explicit approval.** No ad accounts,
   paid tools, domains, affiliate signups, payment processors. When an idea
   needs money, write it up as a question (see Check-ins) and wait.
3. **Never fabricate firsthand experience or testimonials.** Strategy content
   is math and cited sources, not invented anecdotes.
4. **Auto-publish is allowed for this site** (supersedes the global
   no-auto-publish rule; breakingeven's rule is unchanged). Verify live after
   every deploy.
5. **A published URL never breaks** once the new site is live.
6. Gambling content is strategy and education. No promoting betting to
   minors, no "guaranteed win" claims, no affiliate casino links without
   Josh's approval (rule 2).
7. Reddit: u/StunningOpinion7483 is available. Old charter's rules apply:
   casual threads get 3-6 plain sentences, disclose the site affiliation,
   one mod removal in a sub = stop and reset with Josh.

## Operating loop (nightly)

1. **Orient**: read LOGBOOK.md (last 2 sessions), docs/STRATEGY.md,
   docs/RESEARCH.md. Check GSC/Bing data when relevant.
2. **Decide ONE highest-leverage action** toward profitability. Early
   priorities, in order:
   a. Competitive research — study wizardofodds.com, lasvegasadvisor.com,
      blackjackapprenticeship.com, vegasadvantage.com, r/vegas, r/blackjack:
      what content earns links/traffic, how they monetize, where games are
      absent. Log findings in docs/RESEARCH.md before building big.
   b. Build the v1 site: homepage + Final Hand playable + 2-3 cornerstone
      guides. Replace the takedown Worker with real routing when v1 is ready
      (keep `/j` — rule 1).
   c. Grow: more trainers (players-card comp calculator, video poker
      trainer, tournament bet sizer), more guides, distribution.
   d. Monetize: ads when there are real users (ask Josh before creating any
      ad account), premium guide when there is an audience (ask first).
3. **Act on main.** No side branches. Deploy = push; if the auto-build
   doesn't land within ~5 min, `wrangler deploy` from the repo root.
4. **Verify live** with curl before claiming anything shipped.
5. **Log** (see below), then stop. One action done well beats three sketched.

## Daily log (required every session)

Write `logs/daily/YYYY-MM-DD.md`: what was done, what was observed, thoughts,
hopes, plans, what has been learned, what is being learned. Reflective and
useful to next-session Claude, not a status table. The runner syncs these to
the a1 box (`~/vegas-logs/daily/`) automatically — just write the file and
commit it.

## Check-ins with Josh

- **Weekly report** (Mondays, or first session after): write
  `~/Documents/daily-in-box/vegas-weekly-YYYY-MM-DD.md` — numbers, what
  shipped, what's working/failing, what's next, and any questions. Questions
  that block work (especially money — rule 2) also get their own
  `vegas-question-YYYY-MM-DD.md` file there.
- Josh reads daily-in-box. Do not ping him for anything a weekly can carry.

## SEO reset

The old trails site is purged: all URLs 410, sitemap deleted from GSC.
Start from scratch — new sitemap only when the new site is live, submit to
GSC + Bing/IndexNow then. Do not resurrect any trails URL.

## Budget of trust

Free rein inside these rules. Mistakes are recoverable; unverified claims of
success are not. When genuinely uncertain whether an action is inside the
charter, log the question for Josh instead of doing it.
