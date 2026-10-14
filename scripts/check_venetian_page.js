// ponytail: runs the Venetian page's own script (repo file or live HTML) with no DOM, against the numbers in its copy.
// usage: node scripts/check_venetian_page.js <guides/venetian-rewards-tiers/index.html>
const fs = require('fs'), assert = require('assert');
if (!process.argv[2]) { console.error('usage: node check_venetian_page.js <index.html>'); process.exit(2); }
const html = fs.readFileSync(process.argv[2], 'utf8');
const js = html.split('<script>').slice(1).map(x => x.split('</script>')[0]).find(x => x.includes('function vnx'));
assert(js, 'venetian script missing');
const { vnx, tierYearEnd } = new Function(js + '; return { vnx, tierYearEnd };')();
const $ = n => '$' + Math.round(n).toLocaleString('en-US');
// every table cell = one kind of spend alone
const T = { 3000: [1500, 1500, 12000, 30000], 20000: [10000, 10000, 80000, 200000], 50000: [25000, 25000, 200000, 500000] };
for (const [g, [sp, tb, sl, vp]] of Object.entries(T)) {
  assert.equal(vnx({ goal: +g, spend: sp }).need, 0, g + ' spend'); assert(vnx({ goal: +g, spend: sp - 1 }).need > 0, g + ' spend not minimal');
  assert.equal(vnx({ goal: +g, game: 'table' }).coin, tb); assert.equal(vnx({ goal: +g, game: 'slots' }).coin, sl); assert.equal(vnx({ goal: +g, game: 'vp' }).coin, vp);
  for (const d of [sp, sl, vp]) assert(html.includes('<td>' + $(d) + '</td>') || html.includes('<td><b>' + $(d) + '</b></td>'), 'cell missing ' + $(d));
}
// expected-loss table
const L = { 3000: [929, 138], 20000: [6192, 920], 50000: [15480, 2300] };
for (const [g, [s, v]] of Object.entries(L)) {
  assert.equal(Math.round(vnx({ goal: +g, game: 'slots', edge: 7.74 }).loss), s, 'slots loss ' + g); assert(html.includes($(s)), 'copy ' + $(s));
  assert.equal(Math.round(vnx({ goal: +g, game: 'vp', edge: 0.46 }).loss), v, 'vp loss ' + g); assert(html.includes($(v)), 'copy ' + $(v));
  assert.equal(vnx({ goal: +g, game: 'table', edge: 99 }).loss, T[g][1], 'table theo ' + g);
}
// worked example: $5,000 spend = 10,000; rest 10,000
assert.equal(vnx({ goal: 20000, spend: 5000 }).fromSpend, 10000);
const v = vnx({ goal: 20000, spend: 5000, edge: 0.46 }); assert.equal(v.coin, 100000); assert.equal(Math.round(v.loss), 460);
const s = vnx({ goal: 20000, spend: 5000, game: 'slots', edge: 7.74 }); assert.equal(s.coin, 40000); assert.equal(Math.round(s.loss), 3096);
assert.equal(Math.round(4 * 7.74), 31); assert.equal((10 * 0.46).toFixed(1), '4.6');
// edges
assert.equal(vnx({ goal: 20000, have: 25000 }).need, 0); assert.equal(vnx({ goal: 20000, spend: -5 }).need, 20000); assert.equal(vnx({ goal: 3000, game: 'table', have: 2999 }).coin, 1);
assert.equal(tierYearEnd(new Date(2026, 9, 13)), 'February 28, 2027'); assert.equal(tierYearEnd(new Date(2027, 1, 10)), 'February 28, 2027');
assert.equal(tierYearEnd(new Date(2027, 2, 1)), 'February 29, 2028');
for (const t of ['$80,000', '$200,000', '$10,000 of resort spend', '7.74%', '0.46%', 'about $460', 'about $3,096', '2 per $1', '$0.01', '90 days']) assert(html.includes(t), 'copy missing ' + t);
console.log('ok');
