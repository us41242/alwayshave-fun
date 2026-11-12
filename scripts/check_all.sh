# ponytail: run every content guard in one command — local (repo files) or live (curl the deployed
# pages and run the same guards on them). Twenty guards with twenty different argument shapes was a
# per-session copy-paste ritual; this is the ritual.
# usage: bash scripts/check_all.sh [local|live]

set -u
cd /Users/joshuaedrake/Documents/alwayshave-fun
B=${1:-local}   # local | live
if [ "$B" = live ]; then
  P() { curl -fsS "https://alwayshave.fun$1" > /tmp/live_$2.html && echo /tmp/live_$2.html; }
  PC=$(P /players-cards-compared/ pc); HOME=$(P / home); DIA=$(P /caesars-diamond/ dia)
  OLY=$(P /caesars-olympus/ oly); MGM=$(P /mgm-gold-platinum/ mgm); RW=$(P /resorts-world-genting-rewards-tiers/ rw)
  STN=$(P /station-boarding-pass-tiers/ stn); VEN=$(P /venetian-rewards-tiers/ ven); TEV=$(P /tournament-ev-calculator/ tev)
  VP=$(P /video-poker-trainer/ vp); BOYD=$(P /boyd-rewards-tiers/ boyd); CARD=$(P /tournament-card/ card)
else
  PC=guides/players-cards-compared/index.html; HOME=index.html; DIA=guides/caesars-diamond/index.html
  OLY=guides/caesars-olympus/index.html; MGM=guides/mgm-gold-platinum/index.html
  BOYD=guides/boyd-rewards-tiers/index.html
  RW=guides/resorts-world-genting-rewards-tiers/index.html; STN=guides/station-boarding-pass-tiers/index.html
  VEN=guides/venetian-rewards-tiers/index.html; TEV=tools/tournament-ev-calculator/index.html
  VP=games/video-poker/index.html; CARD=tools/tournament-card/index.html
fi
r=0
run() { printf '%-28s ' "$1"; shift; if "$@" >/tmp/g.out 2>&1; then tail -1 /tmp/g.out; else echo "FAIL"; cat /tmp/g.out; r=1; fi; }
run binions          node scripts/check_binions.js $PC
run boyd_points      node scripts/check_boyd_points.js $PC
run boyd_tiers       node scripts/check_boyd_tiers.js $BOYD
run tier_calc        node scripts/check_tier_calc.js $PC
run no_gambling      node scripts/check_no_gambling_table.js $PC
run diamond          node scripts/check_diamond_page.js $DIA
run olympus          node scripts/check_olympus_page.js $OLY
run mgm              node scripts/check_mgm_page.js $MGM
run rw               node scripts/check_rw_page.js $RW
run station          node scripts/check_station_page.js $STN
run station_food     node scripts/check_station_food_comps.js $STN
run venetian         node scripts/check_venetian_page.js $VEN
run tev              node scripts/check_tev_page.js $TEV
run tournament_card  node scripts/check_tournament_card.js $CARD
run home_quiz        node scripts/check_home_quiz.js $HOME
run tier_table       python3 scripts/check_tier_table.py $HOME
run vp_leaks         node scripts/check_vp_leaks.js $VP
run tier_routes      python3 scripts/check_tier_routes.py $HOME
run dated_claims     python3 scripts/check_dated_claims.py
run earn_rates       python3 scripts/check_earn_rates.py
run manifest         python3 scripts/check_manifest.py
run llms_txt         python3 scripts/check_llms_txt.py
run arrival_beacon   node scripts/check_arrival_beacon.js
run sitemap_lastmod  python3 scripts/sitemap_lastmod.py --check
echo "=== exit $r"
exit $r
