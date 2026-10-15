// ponytail: runs the Resorts World page's own script (repo file or live HTML) with no DOM, against the numbers in its copy.
// usage: node scripts/check_rw_page.js <guides/resorts-world-genting-rewards-tiers/index.html>
const fs = require('fs'), assert = require('assert');
if (!process.argv[2]) { console.error('usage: node check_rw_page.js <index.html>'); process.exit(2); }
const html = fs.readFileSync(process.argv[2], 'utf8');
const js = html.split('<script>').slice(1).map(x => x.split('</script>')[0]).find(x => x.includes('function rwx'));
assert(js, 'rw script missing');
const { rwx, tierYearEnd } = new Function(js + '; return { rwx, tierYearEnd };')();
const $ = n => '$' + Math.round(n).toLocaleString('en-US');
const cell = d => html.includes('<td>' + $(d) + '</td>') || html.includes('<td><b>' + $(d) + '</b></td>');
// every table cell = one kind of spend alone, and minimal
const T = { 3000: [600, 3000, 1000, 3500], 75000: [15000, 75000, 25000, 87500], 250000: [50000, 250000, 83334, 291667], 1000000: [200000, 1000000, 333334, 1166667] };
for (const [g, [sp, nt, sl, vp]] of Object.entries(T)) {
  assert.equal(rwx({ goal: +g, spend: sp }).need, 0, g + ' spend'); assert(rwx({ goal: +g, spend: sp - 1 }).need > 0, g + ' spend not minimal');
  assert.equal(rwx({ goal: +g, night: nt }).need, 0); assert(rwx({ goal: +g, night: nt - 1 }).need > 0);
  assert.equal(rwx({ goal: +g, game: 'slots' }).coin, sl); assert.equal(rwx({ goal: +g, game: 'vp' }).coin, vp);
  assert(Math.floor((sl - 1) * 3) < +g && Math.floor((vp - 1) * 3 / 3.5) < +g, g + ' coin not minimal');
  for (const d of [sp, nt, sl, vp]) assert(cell(d), 'cell missing ' + $(d));
}
// expected-loss table
const L = { 3000: [77, 16], 75000: [1935, 403], 250000: [6450, 1342], 1000000: [25800, 5367] };
for (const [g, [s, v]] of Object.entries(L)) {
  assert.equal(Math.round(rwx({ goal: +g, game: 'slots', edge: 7.74 }).loss), s, 'slots loss ' + g); assert(cell(s), 'copy ' + $(s));
  assert.equal(Math.round(rwx({ goal: +g, game: 'vp', edge: 0.46 }).loss), v, 'vp loss ' + g); assert(html.includes($(v)), 'copy ' + $(v));
}
assert.equal((1935 / 402.5).toFixed(1), '4.8');
// worked example: $3,000 dining = 15,000; rest 60,000
assert.equal(rwx({ goal: 75000, spend: 3000 }).fromSpend, 15000);
const v = rwx({ goal: 75000, spend: 3000, edge: 0.46 }); assert.equal(v.coin, 70000); assert.equal(Math.round(v.loss), 322);
const s = rwx({ goal: 75000, spend: 3000, game: 'slots', edge: 7.74 }); assert.equal(s.coin, 20000); assert.equal(Math.round(s.loss), 1548);
// edges
assert.equal(rwx({ goal: 75000, have: 80000 }).need, 0); assert.equal(rwx({ goal: 75000, spend: -5, night: 'x' }).need, 75000);
assert.equal(rwx({ goal: 3000, spend: 100, night: 50 }).fromSpend, 550);
assert.equal(tierYearEnd(new Date(2026, 9, 14)), 'January 4, 2027'); assert.equal(tierYearEnd(new Date(2027, 0, 4)), 'January 4, 2027');
assert.equal(tierYearEnd(new Date(2027, 0, 5)), 'January 4, 2028');
for (const t of ['$600 of meals', '$15,000 of dining, retail and spa', '7.74%', '0.46%', 'about $322', 'about $1,548', '5 per $1', '3 per $3.50', '5,000 points are worth $5', 'January 4, 2028', 'up to $600']) assert(html.includes(t), 'copy missing ' + t);
console.log('ok');
