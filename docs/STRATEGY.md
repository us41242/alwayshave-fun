# STRATEGY

Seeded 2026-08-31; first real version 2026-09-01 after the genre survey in
docs/RESEARCH.md.

## Thesis (confirmed by research)
Playable, coached strategy trainers are absent from this genre. Every
competitor is text plus, at most, an uncoached practice table or a bare
calculator. Tournament blackjack in particular has zero interactive trainers
and its authorities' pages date to 2009-2018. Games earn links and repeat
visits; guides monetize the audience the games attract.

## Positioning
"Play it before you bet it." Mobile-first, dark felt aesthetic (Final Hand
brand direction). Math and cited sources (Wong, Smith, Wizard of Odds), never
invented anecdotes. Honest about comps: they lower the cost of play, they
don't make you a winner.

## v1 build (charter loop 2b) — complete 2026-09-04
1. ✅ Homepage: one screen, one CTA into Final Hand, guide links.
2. ✅ `games/final-hand/` live at `/final-hand/` with coach mode.
3. Cornerstone guides (each links into a game/calculator):
   - ✅ Blackjack tournament strategy: `/blackjack-tournament-strategy/`.
   - ✅ Casino comps and theoretical loss, with calculator: `/casino-comps/` (2026-09-03).
   - ✅ Players cards compared: `/players-cards-compared/` (2026-09-04). Base
     rebate table, trip calculator, tier price list, locals clubs.
4. ✅ Worker: path allowlist → assets. `/j` kept. Everything else 410.
5. ✅ Sitemap live at /sitemap.xml; submitted to GSC (API, 2026-09-03) and pinged via IndexNow.

## Growth (2c) candidates, in order
1. ✅ Tournament bet sizer: `/tournament-bet-sizer/` (2026-09-05). One
   screen, Wong's last-hand rules encoded, asserted against the guide.
2. ✅ Video poker trainer: `/video-poker-trainer/` (2026-09-07). Exact EV of all
   32 holds by full enumeration; coach, hint, session stats.
3. ✅ Bonus Poker (8/5) + Double Double Bonus (9/6) added to the VP trainer
   (2026-09-10), a pay-table selector on the generic exact-EV engine. Built to
   a direct r/VideoPoker request (priority bonus > ddb > deuces).
4. ✅ Full-Pay Deuces Wild (2026-09-11), the #3 request. Needed a real
   wild-card evaluator (`dwRank`), not a table swap — wilds add four-deuces,
   wild royal and five-of-a-kind categories. 25/15/9/5/3/2/2/1, 100.76%: the
   one commonly available positive-expectation VP game. Requester's list
   (bonus > ddb > deuces) is now complete.
5. ✅ Play-money credit balance on the VP trainer (2026-09-13): 1,000 start,
   5 a hand, persists, rebuy when broke. Built to a live r/VideoPoker request
   ("ad-free, pretend money, bankroll he can build up, iPad"); derived from
   the existing stats. Unsolicited from the earlier requester the same day:
   "one of the best vp trainers; great design, gui, ease of use" (real,
   attributed — the only kind rule 3 permits; not used on-site yet).
6. Candidates: pay-table identifier; the positive-expectation-game hook on the
   homepage/guides; more trainers only once something is indexed. **Links /
   indexing are the bottleneck** — product direction is not.

Indexing: sitemap submitted 09-03, still never downloaded by 09-09. On
09-09 found the sitemap had declared the wrong XML namespace since 09-02
(`sitemaps.org/schema/`, singular — the protocol is `schemas/`); fixed and
re-registered in GSC, Bing SubmitUrlBatch/SubmitFeed, IndexNow, Indexing API.
Bing crawls the host 11-17 pages/day but has never fetched a non-homepage
page; Bing reports **InLinks: 2** for the whole domain. Both engines take the
homepage and decline its internal links. Diagnosis: host-level crawl demotion
after the 2,900-URL 410 purge, plus no inbound links. Cloudflare and robots
ruled out. Repo purged of trails files 09-06.

## Distribution
**Status 2026-09-14: Reddit is halted.** u/StunningOpinion7483 was suspended
sitewide (permanent per the API) and r/VideoPoker was banned by Reddit for
being unmoderated, both between the 09-13 and 09-14 sessions. The post, the
feature-request thread and the praise are gone. Do not post, comment, or
create a replacement account (ban evasion); appeal/abandon is Josh's call
(`daily-in-box/vegas-question-2026-09-14.md`). Lesson for any future account:
the spam classifier counts same-domain links per week, not disclosures —
five in five days on a two-month-old account was too dense. Candidate
communities that would need a new, disclosed identity (each is a question for
Josh): Wizard of Vegas forum, vpFREE2 (groups.io), LVA forum, blackjackinfo,
Hacker News "Show HN". The notes below are kept for the record.

Reddit account u/StunningOpinion7483 (session cookie at
~/.camoufox-mcp/sessions/reddit.pw.json, token via scripts/reddit_token.py,
Mac only). Register: answer real questions, disclose. Whether a *post* is
welcome is sub-specific, not a genre rule:
- **r/blackjack — comments only.** Rule 3 bans sharing "any new apps/sim
  sites/similar AI vibed garbage". Answer questions, do not link the site.
  First comment 2026-09-05 on "Blackjack Tournament Tomorrow".
- **r/VideoPoker — posts welcome.** A trainer launch (smartholdvp.com,
  2026-08-04) scored 9 with 24 comments and became a feature-request
  thread. Ours posted 2026-09-09: https://redd.it/1wc8lvp.
- **r/gambling — self-promo allowed** at the stated 10:1 ratio.
Competitor noted from that thread: smartholdvp has spaced repetition,
custom/shareable pay tables, multi-play, leaderboards, Android + iOS. Our
edge is exact enumeration instead of a chart, and nothing to install or buy.

## Monetization (2d) — all require asking Josh first
Ads once there are real users; affiliate links only with approval; premium
guide / BJA-style funnel (free trainer → email → paid) once there is an
audience.

## Metrics that matter
Games played per visit, return visits, guide→game click-through. Traffic
second. Track once v1 is live (GSC + a privacy-light counter).
