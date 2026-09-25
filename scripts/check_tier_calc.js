// ponytail: runs the tier calculator's own script (repo file or live HTML) against a stub DOM
// and checks its numbers against hand-derived ones from the programs' published rates.
// usage: node scripts/check_tier_calc.js <file.html>
const fs = require('fs'), assert = require('assert');
const src = fs.readFileSync(process.argv[2], 'utf8');
const js = src.split('<script>').map(x => x.split('</script>')[0]).find(x => x.includes('TIER_PROGRAMS'));
assert(js, 'tier calculator script missing');
const els = {};
const el = () => ({ value: '', innerHTML: '', textContent: '', style: {}, opts: [],
  add(o) { this.opts.push(o); if (this.opts.length === 1) this.value = o.value; }, addEventListener() {} });
global.document = { getElementById: id => (els[id] ||= el()) };
global.Option = function (t, v) { this.text = t; this.value = String(v); };
const api = new Function(js + '; return {TIER_PROGRAMS, minEarn, price, tierRun, fillTiers};')();
const [cz, stn, ven, rw] = api.TIER_PROGRAMS;
const P = (p, tc, g, b) => api.price(p, tc, g, b);
// Caesars: must match the homepage table (check_tier_table.py)
assert.equal(P(cz, 15000, 'slots', false).coinIn, 75000); assert.equal(P(cz, 15000, 'slots', false).loss, 6000);
assert.equal(P(cz, 15000, 'slots', true).coinIn, 25000);  assert.equal(P(cz, 15000, 'slots', true).loss, 2000);
assert.equal(P(cz, 15000, 'vp', false).coinIn, 150000);   assert.equal(Math.round(P(cz, 15000, 'vp', false).loss), 690);
assert.equal(Math.round(P(cz, 15000, 'vp', true).loss), 230);
assert.equal(P(cz, 5000, 'slots', true).coinIn, 12500);   // guide: Platinum $12,500 in one day
assert.deepEqual(P(cz, 75000, 'slots', true).days, [5000, 5000, 5000, 5000, 5000]); // 5 x (5,000 + 10,000)
// brute-force the knapsack for every Caesars tier: min earn over up to 6 days of each level
for (const [, tc] of cz.tiers) {
  let best = tc;
  for (let a = 0; a <= 6; a++) for (let b = 0; b <= 6; b++) for (let c = 0; c <= 6; c++) for (let d = 0; d <= 6; d++) {
    const e = 500*a + 1000*b + 2500*c + 5000*d, got = 625*a + 2000*b + 7500*c + 15000*d;
    best = Math.min(best, e + Math.max(0, tc - got));
  }
  assert.equal(api.minEarn(tc, cz.bonus).earn, best, `knapsack wrong at ${tc}`);
}
// the other three: guide table's first two paid tiers
assert.equal(Math.round(P(stn, 1000, 'slots').coinIn), 333); assert.equal(Math.round(P(stn, 40000, 'slots').coinIn), 13333);
assert.equal(P(ven, 3000, 'slots').coinIn, 12000); assert.equal(P(ven, 20000, 'slots').coinIn, 80000);
assert.equal(P(rw, 3000, 'slots').coinIn, 1000);   assert.equal(P(rw, 75000, 'slots').coinIn, 25000);
assert.equal(Math.round(P(rw, 75000, 'vp').coinIn), 87500);
// table cells in the HTML match
for (const cell of ['Gold: <b>$333</b> · Platinum: <b>$13,333</b>', 'Sapphire: <b>$12,000</b> · Ruby: <b>$80,000</b>', 'Elite: <b>$1,000</b> · Prime: <b>$25,000</b>'])
  assert(src.includes(cell), 'table cell missing: ' + cell);
// UI renders without throwing, for every program/tier/game/mode
for (let i = 0; i < 4; i++) { els['tp-prog'].value = String(i); api.fillTiers();
  for (let t = 0; t < api.TIER_PROGRAMS[i].tiers.length; t++) for (const g of ['slots', 'vp']) for (const w of ['spread', 'bonus']) {
    Object.assign(els['tp-tier'], { value: String(t) }); els['tp-game'].value = g; els['tp-when'].value = w; els['tp-bet'].value = '5';
    api.tierRun(); assert(!/NaN|undefined/.test(els['tp-out'].innerHTML + els['tp-note'].textContent), `bad render ${i}/${t}/${g}/${w}`);
  } }
// a bonus day that cannot fit in 24 hours is called out: Diamond Elite, slots, $1.25 -> 5,000 TC day = $25,000 = 33 h
els['tp-prog'].value = '0'; api.fillTiers(); els['tp-tier'].value = '3'; els['tp-game'].value = 'slots'; els['tp-when'].value = 'bonus'; els['tp-bet'].value = '1.25';
api.tierRun(); assert(els['tp-note'].textContent.includes('is 33 hours of play'), 'infeasible-day warning missing');
els['tp-bet'].value = '25'; api.tierRun(); assert(!els['tp-note'].textContent.includes('hours of play'), 'warning shown when feasible');
console.log('Caesars Diamond Elite, bonus-timed slots:', P(cz, 75000, 'slots', true));
console.log('ALL TIER CALC CHECKS PASS');
