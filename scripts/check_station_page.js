// ponytail: runs the Station page's own script (repo file or live HTML) with no DOM, against the numbers in its copy.
// usage: node scripts/check_station_page.js <guides/station-boarding-pass-tiers/index.html>
const fs = require('fs'), assert = require('assert');
if (!process.argv[2]) { console.error('usage: node check_station_page.js <index.html>'); process.exit(2); }
const html = fs.readFileSync(process.argv[2], 'utf8');
const js = html.split('<script>').slice(1).map(x => x.split('</script>')[0]).find(x => x.includes('function stnx'));
assert(js, 'station script missing');
const { stnx, periodEnd } = new Function(js + '; return { stnx, periodEnd };')();
const $ = n => '$' + Math.round(n).toLocaleString('en-US');
// every table cell = one kind of spend alone, rounded up to the dollar
const T = { 1000: [20, 34, 50, 100, 334, 1000], 40000: [800, 1334, 2000, 4000, 13334, 40000], 100000: [2000, 3334, 5000, 10000, 33334, 100000], 300000: [6000, 10000, 15000, 30000, 100000, 300000] };
const KEYS = ['hotel', 'bev', 'steak', 'rest', 'slots', 'vp'];
for (const [g, row] of Object.entries(T)) row.forEach((d, i) => {
  const k = KEYS[i], r = ['slots', 'vp'].includes(k) ? stnx({ goal: +g, game: k }) : stnx({ goal: +g, spend: { [k]: d } });
  if (['slots', 'vp'].includes(k)) assert.equal(r.coin, d, g + ' ' + k); else { assert.equal(r.need, 0, g + ' ' + k); assert(stnx({ goal: +g, spend: { [k]: d - 1 } }).need > 0, g + ' ' + k + ' not minimal'); }
  assert(html.includes('<td>' + $(d) + '</td>') || html.includes('<td><b>' + $(d) + '</b></td>'), 'cell missing ' + $(d));
});
// expected-loss table
const L = { 1000: [22, 5], 40000: [867, 184], 100000: [2167, 460], 300000: [6500, 1380] };
for (const [g, [s, v]] of Object.entries(L)) {
  assert.equal(Math.round(stnx({ goal: +g, game: 'slots', edge: 6.5 }).loss), s, 'slots loss ' + g);
  assert.equal(Math.round(stnx({ goal: +g, game: 'vp', edge: 0.46 }).loss), v, 'vp loss ' + g);
}
// worked example: $500 hotel + $300 steak + $100 bar = 34,000; rest 6,000
const ex = { hotel: 500, steak: 300, bev: 100 };
assert.equal(stnx({ goal: 40000, spend: ex }).fromSpend, 34000);
assert.equal(Math.round(stnx({ goal: 40000, spend: ex, edge: 0.46 }).loss), 28);
const sx = stnx({ goal: 40000, spend: ex, game: 'slots', edge: 6.5 }); assert.equal(sx.coin, 2000); assert.equal(Math.round(sx.loss), 130);
assert.equal((6.5 / 3).toFixed(1), '2.2');
// edges
assert.equal(stnx({ goal: 40000, have: 50000 }).need, 0); assert.equal(stnx({ goal: 40000, spend: { hotel: -5 } }).need, 40000);
assert.equal(periodEnd(new Date(2026, 5, 30)), 'June 30, 2026'); assert.equal(periodEnd(new Date(2026, 6, 1)), 'December 31, 2026');
for (const s of ['$13,334', '$40,000', '$800 of hotel stays', '395 days', '179 days', '6.50%', '0.46%', 'March 31, 2020', 'about $28', 'about $130']) assert(html.includes(s), 'copy missing ' + s);
console.log('ok');
