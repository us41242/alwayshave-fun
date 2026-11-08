// ponytail: runs the Station page's own PTS table + stnComp() (repo file or live HTML) against the comp-rate
// table in its copy, and re-derives the Chairman worked example from stnx so the two can't drift apart.
// usage: node scripts/check_station_food_comps.js <guides/station-boarding-pass-tiers/index.html>
const fs = require('fs'), assert = require('assert');
if (!process.argv[2]) { console.error('usage: node check_station_food_comps.js <index.html>'); process.exit(2); }
const html = fs.readFileSync(process.argv[2], 'utf8');
const js = html.split('<script>').slice(1).map(x => x.split('</script>')[0]).find(x => x.includes('function stnx'));
assert(js, 'station script missing');
const { PTS, stnComp, stnx } = new Function(js + '; return { PTS, stnComp, stnx };')();

// Station's published Reward Point rates, points per $1 wagered. Pinned here on purpose: this is the
// only assertion that fails if someone edits the page's rate away from what Station publishes.
const PUBLISHED = { pari: 20, keno: 15, bingo: 5, slots: 1, sports: 1, vp: 0.5 };
assert.deepEqual(PTS, PUBLISHED, "point rates drifted from Station's published chart");

// every row of the comp-rate table is derived, not typed: $1 of comps = 1,000 points
const LABEL = { pari: 'Pari-mutuel race', keno: 'Live keno', bingo: 'Bingo', slots: 'Slots and video keno', sports: 'Race and sports', vp: 'Video poker and multi-game' };
for (const [k, pts] of Object.entries(PTS)) {
  const { wager, rate } = stnComp(pts);
  assert.equal(wager, 1000 / pts, k);
  assert.equal(rate, pts / 10, k);
  const cells = '<tr><td>' + LABEL[k] + ' (' + pts + ')</td><td>$' + Math.round(wager).toLocaleString('en-US') + '</td><td>' + rate.toFixed(2) + '%</td></tr>';
  assert(html.includes(cells), 'comp-rate row wrong or missing: ' + cells);
}
// video poker must be the worst comp rate and pari-mutuel the best, or the prose below the table lies
const rates = Object.entries(PTS).map(([k, p]) => [k, stnComp(p).rate]);
assert.equal(rates.reduce((a, b) => a[1] < b[1] ? a : b)[0], 'vp', 'vp is no longer the lowest comp rate');
assert.equal(rates.reduce((a, b) => a[1] > b[1] ? a : b)[0], 'pari', 'pari-mutuel is no longer the highest comp rate');

// Chairman worked example, chained to the tier engine rather than retyped
const chair = g => stnx({ goal: 300000, game: g, edge: g === 'slots' ? 6.5 : 0.46 });
const food = coin => Math.round(coin * PTS.slots / 1000), foodVp = coin => Math.round(coin * PTS.vp / 1000);
const s = chair('slots'), v = chair('vp');
assert.equal(s.coin, 100000); assert.equal(food(s.coin), 100); assert.equal(Math.round(s.loss), 6500);
assert.equal(v.coin, 300000); assert.equal(foodVp(v.coin), 150); assert.equal(Math.round(v.loss), 1380);
assert.equal(Math.round((s.loss / food(s.coin)) / (v.loss / foodVp(v.coin))), 7, 'the "seven times the price" claim no longer holds');
for (const str of ['$100,000 of coin-in', '<b>$100 of food</b>', '<b>$6,500</b>', '<b>$150 of food</b>', '<b>$1,380</b>', '$65 of expected loss per comp dollar', 'seven times the price',
  // the point of the whole section: status buys no food, and the unpublished part is named as unpublished
  'not one of them is a food or dining comp', '20% cash discount on catering', '$1 of comps per hour played',
  '<b>$0 of food</b>', "invited locals' multipliers", 'nobody outside the program can price them',
  '1000 Points = $1 for comps, cashback, or free slot play', 'id="food-comps"']) assert(html.includes(str), 'copy missing: ' + str);
// the two corrected claims: points redeem for comps, and the old "cash back or free slot play" only wording is gone
assert(!/points as cash back or free slot play/.test(html), 'stale redemption wording still present');
assert(html.includes('1,000 points = $1 for comps, cash back or free slot play'), 'redemption rule not corrected');
assert(html.includes('pari-mutuel race wagers at 10'), 'pari-mutuel missing from the status-credit recap');
console.log('ok');
