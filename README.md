# alwayshave.fun

Free Las Vegas strategy trainers and tier-cost math, live at **https://alwayshave.fun/**.
Playable in the browser, no ads, no accounts, no sign-ups. Every number comes
from a casino's own published earn rates or from standard gambling math, and
the tier-cost guides name their sources.

## Trainers (playable in the browser)

- [Final Hand — blackjack tournament trainer](https://alwayshave.fun/final-hand/): Six seats, 15 hands, most chips wins. A coach shows the bet that covers the leader, when betting to lose is correct, and how to defend a lead.
- [Video poker trainer](https://alwayshave.fun/video-poker-trainer/): 9/6 Jacks or Better, 8/5 Bonus Poker, 9/6 Double Double Bonus and Full-Pay Deuces Wild (100.76%). Scores all 32 ways to hold each hand by exact expected value and tracks what mistakes cost.

## Calculators

- [Blackjack tournament bet sizer](https://alwayshave.fun/tournament-bet-sizer/): The final-hand bet that covers the leader (gap + their bet + one chip), the double-cover number, and when to bet to lose.
- [Blackjack tournament EV calculator](https://alwayshave.fun/tournament-ev-calculator/): Expected value of one entry from entry fee, rebuys, entrants, guaranteed pool and payout places; overlay and break-even field size.
- [Blackjack tournament strategy card](https://alwayshave.fun/tournament-card/): The final-hand tournament math on one printable page, free, no signup: the chase bet, the double cover, when to bet to lose, the leader's threat ceiling.
- [Casino comps calculator](https://alwayshave.fun/casino-comps/): Theoretical loss (theo), average daily theo, and the 30–40% reinvestment rule that decides what a casino gives back.

## Strategy guide

- [Blackjack tournament strategy](https://alwayshave.fun/blackjack-tournament-strategy/): The final-hand formula, chip counting, betting to lose, and defending a lead, worked through with examples.

## What a tier actually costs (published earn rates, priced in expected loss)

Each page converts a program's published earn rate into the coin-in required,
then into expected loss at the game you would use to earn it — because coin-in
is not the cost.

Ranked cheapest-first, by expected loss on 9/6 Jacks or Better played
correctly, every tier at the five Vegas programs that publish a machine earn
rate: Station Gold $5, Resorts World Elite $16, Venetian Sapphire $138,
Station Platinum $184, Caesars Diamond $230 (on one daily-bonus day),
Resorts World Prime $403, Venetian Ruby $920, Caesars Olympus $4,600 (over 20
daily-bonus days). MGM publishes no machine earn rate and cannot be priced in
play. The same table in non-gaming spend, and the time and skill each route
costs: https://alwayshave.fun/#cheapest-status

- [Las Vegas players cards compared](https://alwayshave.fun/players-cards-compared/): Caesars Rewards, MGM Rewards, Boyd, Station Boarding Pass and Wynn Rewards side by side — earn rates, point values and tier thresholds, including what each tier costs with no gambling at all.
- [Caesars Diamond](https://alwayshave.fun/caesars-diamond/): 15,000 Tier Credits = $75,000 slot coin-in; expected loss $6,000 on slots down to about $230 on video poker timed to the daily Tier Credit multiplier.
- [Caesars Olympus](https://alwayshave.fun/caesars-olympus/): 300,000 Tier Credits by 2026-12-31 = $1.5M slot coin-in; expected loss $120,000 down to about $4,600.
- [MGM Gold and Platinum](https://alwayshave.fun/mgm-gold-platinum/): Gold is 75,000 Tier Credits = $18,750 of hotel, dining and show spend at 4 per $1 — $10,000 in a single day under MGM's 2026 Daily Tier Status Accelerator.
- [Station Casinos Boarding Pass](https://alwayshave.fun/station-boarding-pass-tiers/): Platinum is 40,000 status credits in six months = $13,334 slot coin-in, $40,000 video poker, or $800 of hotel stays at 50 credits per $1.
- [Venetian Rewards](https://alwayshave.fun/venetian-rewards-tiers/): Ruby is 20,000 Tier Points in a March–February tier year = $80,000 slot coin-in, $200,000 video poker, or $10,000 of direct-booked resort spend at 2 per $1.
- [Genting Rewards at Resorts World](https://alwayshave.fun/resorts-world-genting-rewards-tiers/): Prime is 75,000 Tier Credits in a Jan-5-to-Jan-4 year = $25,000 slot coin-in, $87,500 video poker, or $15,000 of dining, retail and spa at 5 per $1.
- [Boyd Rewards tiers](https://alwayshave.fun/boyd-rewards-tiers/): Ruby 0, Sapphire 750, Emerald 15,000, Onyx 50,000, Titanium 200,000 Tier Credits, plus an Onyx+ recognition band at 100,000-199,999. Boyd publishes no per-dollar Tier Credit rate for any game, so no Boyd tier can be priced in play; the only published price is $4.99 of Stardust Social Casino coin purchases per Tier Credit, which makes Titanium $998,000. Points: 1 per $1 reel/keno coin-in, 1 per $2 video poker, 1,000 = $1, and nothing at all below Sapphire.

## How it is built

Static HTML served by a Cloudflare Worker (`worker.js`, `wrangler.toml`). Each
game is a single self-contained `index.html` under `games/`; guides live under
`guides/`. No framework and no build step. `bash scripts/check_all.sh` re-derives
the published numbers from their source rates and fails if the copy drifts.
