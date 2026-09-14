# alwayshave.fun

Playable Vegas strategy trainers and guides, live at **https://alwayshave.fun/**.

- [Final Hand](https://alwayshave.fun/final-hand/) — blackjack tournament trainer with coach mode
- [Video poker trainer](https://alwayshave.fun/video-poker-trainer/) — 9/6 Jacks or Better, 8/5 Bonus Poker, 9/6 Double Double Bonus, Full-Pay Deuces Wild; exact EV of all 32 holds, play-money credits, no ads, no account
- [Tournament bet sizer](https://alwayshave.fun/tournament-bet-sizer/)
- Guides: [blackjack tournament strategy](https://alwayshave.fun/blackjack-tournament-strategy/), [casino comps](https://alwayshave.fun/casino-comps/), [players cards compared](https://alwayshave.fun/players-cards-compared/)

Static HTML served by a Cloudflare Worker (`worker.js`, `wrangler.toml`). Each game is a single self-contained `index.html` under `games/`.
