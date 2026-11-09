// ponytail: guards /boyd-rewards-tiers/ by DERIVING every number on it from the page's own
// constants, never by pinning the rendered string. Same bug class the Station food-comps guard
// caught on 2026-11-07: right arithmetic, wrong quantity, pinned forever.
// The page's whole argument is "Boyd publishes no credit rate, so nobody can price a Boyd tier" —
// so the one price it does quote ($4.99/credit) and the rebate it does publish (0.10% / 0.05%)
// have to be re-derived here, or the page becomes the thing it warns about.
// usage: node scripts/check_boyd_tiers.js <guides/boyd-rewards-tiers/index.html>
const fs = require('fs'), assert = require('assert');
const html = fs.readFileSync(process.argv[2], 'utf8');

// --- the page's own calculator, run as the page runs it -----------------------------------------
const src = html.split('const BOYD_TIERS')[1].split('if (typeof document')[0];
const sandbox = new Function(
  'const console = { assert: (c, m) => { if (!c) throw new Error("page self-assert failed: " + m); } };' +
  'const BOYD_TIERS' + src +
  'return { boyd, BOYD_TIERS, PT_VALUE, REEL_PER_PT, VP_PER_PT, TC_PRICE };')();
const { boyd, BOYD_TIERS, PT_VALUE, REEL_PER_PT, VP_PER_PT, TC_PRICE } = sandbox;

const money = x => '$' + x.toLocaleString('en-US', { minimumFractionDigits: x % 1 ? 2 : 0, maximumFractionDigits: 2 });
const sec = id => { const p = html.split('id="' + id + '"'); assert(p.length === 2, 'section missing: ' + id); return p[1].split('<h2')[0]; };
const text = s => s.replace(/<[^>]+>/g, ' ').replace(/&mdash;|&ndash;/g, '-').replace(/&minus;/g, '-').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ');

// Boyd's own two worked carryover examples, and the floor that switches points on.
assert.deepStrictEqual(boyd(47000, 41000), { dollars: 47, reels: 47000, vp: 94000, tier: 'Emerald', toNext: 9000, next: 'Onyx', buy: 9000 * TC_PRICE, carry: 5000 });
assert.equal(boyd(0, 18000).carry, 3000, "Boyd's 18,000 example");
assert.equal(boyd(0, 280000).carry, 40000, "Boyd's 280,000 example");
assert.equal(boyd(0, 749).tier, 'Ruby'); assert.equal(boyd(0, 750).tier, 'Sapphire');
assert.equal(boyd(0, 200000).next, undefined, 'Titanium must be the top tier');

// --- the five tier bands, as rendered, must match the constants ---------------------------------
const bands = [...text(sec('tiers')).matchAll(/(Ruby|Sapphire|Emerald|Onyx|Titanium)\s+([\d,]+)\s*(?:-\s*([\d,]+)|\+)/g)];
assert.equal(bands.length, 5, 'tier table should render 5 bands, got ' + bands.length);
bands.forEach(([, name, lo, hi], i) => {
  const [cname, floor] = BOYD_TIERS[i], next = BOYD_TIERS[i + 1];
  assert.equal(name, cname, `band ${i} is ${name}, constant says ${cname}`);
  assert.equal(+lo.replace(/,/g, ''), floor, `${name} floor rendered ${lo}, constant ${floor}`);
  if (next) assert.equal(+hi.replace(/,/g, ''), next[1] - 1, `${name} ceiling rendered ${hi}, should be ${next[1] - 1}`);
  else assert.equal(hi, undefined, 'Titanium must render as open-ended');
});

// --- the only published price: every tier at TC_PRICE ------------------------------------------
const price = text(sec('price'));
for (const [name, floor] of BOYD_TIERS) {
  if (!floor) continue;  // Ruby is free
  assert(price.includes(money(floor * TC_PRICE)), `${name} at ${TC_PRICE}/credit should read ${money(floor * TC_PRICE)}`);
}
assert(price.includes(money(100000 * TC_PRICE)), 'the Onyx+ band must be priced too');
// 150 Boyd Points per $0.99 of coin purchases: the cost of a dollar of points, and the return
const BUY_USD = 0.99, BUY_PTS = 150;
assert(price.includes(money(BUY_USD / (BUY_PTS * PT_VALUE))), 'cost of $1 of points bought in-app');
assert(price.includes(Math.round(BUY_PTS * PT_VALUE * 100) + '&cent;'), 'value of 150 Boyd Points, in cents');
assert(price.includes(Math.round(BUY_PTS * PT_VALUE / BUY_USD * 100) + '%'), 'return on in-app point purchases');

// --- the rebate, derived from the published earn rates -----------------------------------------
const pts = text(sec('points'));
const rebate = perDollar => (PT_VALUE / perDollar * 100).toFixed(2) + '%';
assert.equal(rebate(REEL_PER_PT), '0.10%'); assert.equal(rebate(VP_PER_PT), '0.05%');
assert(pts.includes(rebate(REEL_PER_PT)), 'reel rebate ' + rebate(REEL_PER_PT));
assert(pts.includes(rebate(VP_PER_PT)), 'video poker rebate ' + rebate(VP_PER_PT));
assert(pts.includes('0.00%'), 'Ruby must be shown earning nothing');
assert(/Not published/i.test(pts), 'electronic table games must stay unpriced');

// --- expected loss per comp dollar, from the two published house figures ------------------------
const HOLD = 0.0836, VP_EDGE = 0.0046;       // GCB Downtown LV 12 mo to 8/31/2026; 9/6 JoB optimal
const holdStr = (HOLD * 100).toFixed(2) + '%';
// scope the arithmetic to the worked example, so a figure duplicated elsewhere in the prose
// can't keep a stale cell alive (it did, on the first negative test of this guard).
const ex = text((sec('points').match(/<div class="ex">([\s\S]*?)<\/div>/) || [])[1] || '');
assert(ex, 'the worked comp-dollar example is gone');
assert(ex.includes(holdStr), 'the example must state the hold it uses: ' + holdStr);
assert(ex.includes((VP_EDGE * 100).toFixed(2) + '%'), 'the example must state the video poker edge');
const lossPerCompDollar = (perDollar, edge) => (1 / PT_VALUE) * perDollar * edge;
const reelLoss = lossPerCompDollar(REEL_PER_PT, HOLD), vpLoss = lossPerCompDollar(VP_PER_PT, VP_EDGE);
assert(ex.includes(money(1 / PT_VALUE * REEL_PER_PT)), 'reel coin-in per comp dollar');
assert(ex.includes(money(1 / PT_VALUE * VP_PER_PT)), 'video poker coin-in per comp dollar');
assert(ex.includes(money(reelLoss)), `reel loss per comp dollar should read ${money(reelLoss)}, example says: ${ex}`);
assert(ex.includes(money(vpLoss)), `video poker loss per comp dollar should read ${money(vpLoss)}, example says: ${ex}`);
const WORDS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'];
const ratio = Math.round(reelLoss / vpLoss);
assert(ratio <= 10, 'ratio off the word list: ' + ratio);
assert(new RegExp('\\b' + WORDS[ratio] + ' times\\b', 'i').test(ex),
  `the ratio is ${(reelLoss / vpLoss).toFixed(2)}x, so the example must say "${WORDS[ratio]} times"`);
// the hold is a dated third-party figure, so it has to be attributed where we cite sources
assert(sec('sources').includes(holdStr), 'the Sources paragraph must carry the slot hold ' + holdStr);

// --- the benefit matrix: 15 published rows, 5 tier columns, and no dining comp ------------------
const rows = [...sec('benefits').matchAll(/<tr><td>(.*?)<\/td>(.*?)<\/tr>/gs)].map(([, name, rest]) =>
  [text(name).trim(), [...rest.matchAll(/<td[^>]*>(.*?)<\/td>/gs)].map(c => text(c[1]).trim())]);
assert.equal(rows.length, 15, 'Boyd publishes 15 all-casinos benefit rows, page has ' + rows.length);
rows.forEach(([name, cells]) => assert.equal(cells.length, 5, `${name}: ${cells.length} tier cells, need 5`));
const row = n => { const r = rows.find(([name]) => name.replace(/<[^>]*>/g, '').includes(n)); assert(r, 'benefit row missing: ' + n); return r[1]; };
assert.deepStrictEqual(row('Earn Boyd Points'), ['no', 'yes', 'yes', 'yes', 'yes'], 'points start at Sapphire, not Ruby');
assert.deepStrictEqual(row('Carryover Tier Credits'), ['no', 'yes', 'yes', 'yes', 'yes']);
assert.deepStrictEqual(row('Gift shop discount'), ['10%', '15%', '20%', '20%', '20%']);
assert.deepStrictEqual(row('VIP parking'), ['no', 'no', 'yes', 'yes', 'yes']);
assert.deepStrictEqual(row('Annual luxury gift'), ['no', 'no', 'no', 'yes', 'no'], 'Onyx-only, not a stack');
assert.deepStrictEqual(row('Earn Tier Credits'), ['yes', 'yes', 'yes', 'yes', 'yes']);
for (const [name] of rows) assert(!/\b(dining|food)\b/i.test(name), 'a dining comp appeared on the chart: ' + name);

// --- claims that are load-bearing because they are what the sources say ------------------------
const all = text(html);
for (const s of [
  'Onyx+',                               // the recognition band, not a tier
  '100,000 to 199,999',                  // its published range
  '15,000 - 49,000',                      // the carryover chart's band, which disagrees with the tier chart
  'six months of card inactivity',        // point expiry
  'based on tier level',                  // the rules clause behind the Ruby trap
  'based on game played, denomination, and time played',  // why no tier can be priced in play
]) assert(all.includes(s), 'source-backed claim missing or reworded: ' + s);
assert(/Sapphire is the only threshold on this chart that changes the economics/.test(all), 'the chart reading was dropped');

assert((html.match(/^console\.assert\(/gm) || []).length >= 5, 'the page dropped or commented out its own self-checks');

console.log(`ok  5 bands, 15 benefit rows, rebate ${rebate(REEL_PER_PT)}/${rebate(VP_PER_PT)}, ` +
  `${money(reelLoss)} vs ${money(vpLoss)} per comp dollar (${WORDS[ratio]}-to-one), Titanium ${money(200000 * TC_PRICE)}`);
