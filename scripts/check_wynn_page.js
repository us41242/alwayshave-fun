// ponytail: guards /wynn-rewards-tiers/ by DERIVING its numbers from the page's own calculator
// constants (same pattern as check_boyd_tiers.js): the #fc price table, the lede's $2,500 /
// $193.50 / $23, the "8.4 times" ratio, the tier bands, and the 29-row benefit chart with
// Chairman's Club kept out of it (Wynn's chart has three columns; the terms add the fourth tier).
// usage: node scripts/check_wynn_page.js <guides/wynn-rewards-tiers/index.html>
const fs = require('fs'), assert = require('assert');
const html = fs.readFileSync(process.argv[2], 'utf8');

const src = html.split('const PER_PT')[1].split('if (typeof document')[0];
const { wynn, PER_PT, BONUS, EDGE, WYNN_TIERS } = new Function(
  'const console = { assert: (c, m) => { if (!c) throw new Error("page self-assert failed: " + m); } };' +
  'const PER_PT' + src + 'return { wynn, PER_PT, BONUS, EDGE, WYNN_TIERS };')();

const money = x => '$' + x.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const whole = x => '$' + x.toLocaleString('en-US', { minimumFractionDigits: x % 1 ? 2 : 0, maximumFractionDigits: 2 });
const r2 = x => Math.round(x * 100) / 100;
const sec = id => { const p = html.split('id="' + id + '"'); assert(p.length === 2, 'section missing: ' + id); return p[1].split('<h2')[0]; };
const text = s => s.replace(/<[^>]+>/g, ' ').replace(/&mdash;|&ndash;/g, '-').replace(/&rsquo;/g, "'").replace(/\s+/g, ' ');

// --- $5 of FREE CREDIT = 500 points; coin-in and expected loss per tier -------------------------
const cost = (game, tier) => 500 * PER_PT[game] / BONUS[tier];
const fc = text(sec('fc').split('</table>')[0]);
for (const tier of ['Red', 'Platinum', 'Black']) {
  const s = cost('slots', tier), v = cost('vp10', tier);
  const want = [whole(r2(s)), money(r2(s * EDGE.slots)), whole(r2(v)), money(r2(v * EDGE.vp10))].join(' ');
  assert(fc.includes(want), `#fc ${tier} row should read "${want}"`);
  assert.equal(wynn(Math.ceil(s * 100) / 100, 'slots', tier, 0).fc, 5, tier + ': the row coin-in must actually pay $5');
}
const lede = text(html.split('class="lede">')[1].split('</p>')[0]);
for (const s of [whole(cost('slots', 'Red')), money(cost('slots', 'Red') * EDGE.slots), whole(cost('vp10', 'Red') * EDGE.vp10)])
  assert(lede.includes(s), 'lede should quote ' + s);
const ratio = (cost('slots', 'Red') * EDGE.slots / (cost('vp10', 'Red') * EDGE.vp10)).toFixed(1);
assert(text(sec('free-credit')).includes(ratio + ' times'), 'ratio should be ' + ratio + ' times');
assert(text(sec('free-credit')).includes(whole(cost('vp20', 'Red') * EDGE.vp20)), 'vp20 Red price');
assert(cost('slots', 'Black') * EDGE.slots / (cost('vp10', 'Red') * EDGE.vp10) > 6, '"more than six times"');

// --- tier bands as rendered match the constants; Chairman's Club is listed but has no number ----
const bands = [...text(sec('tiers')).matchAll(/(Red|Platinum|Black)\s+([\d,]+)\s*(?:-\s*([\d,]+)|\+)/g)];
assert.equal(bands.length, 3, 'three numbered tiers, got ' + bands.length);
bands.forEach(([, name, lo, hi], i) => {
  assert.equal(name, WYNN_TIERS[i][0]); assert.equal(+lo.replace(/,/g, ''), WYNN_TIERS[i][1], name + ' floor');
  if (WYNN_TIERS[i + 1]) assert.equal(+hi.replace(/,/g, ''), WYNN_TIERS[i + 1][1] - 1, name + ' ceiling');
});
assert(/Chairman's Club\s+Invitation only/.test(text(sec('tiers'))), "Chairman's Club row");

// --- benefit chart: 29 benefit rows, 3 tier columns, monotone (no tier loses a benefit above it)
const rows = sec('wtab').split('</table>')[0].split('<tr>').slice(2).filter(r => !r.includes('colspan'));
assert.equal(rows.length, 29, 'benefit chart rows: ' + rows.length);
const CRUISE = /MSC/;  // the three cruise rows are tier-exclusive by design (one per tier)
for (const r of rows) {
  const c = [...r.matchAll(/<td([^>]*)>(.*?)<\/td>/g)].slice(1).map(m => !m[1].includes('na'));
  assert.equal(c.length, 3, 'row needs 3 tier cells: ' + r);
  if (!CRUISE.test(r)) assert(!(c[0] && !c[1]) && !(c[1] && !c[2]), 'higher tier lost a benefit: ' + text(r));
}

// --- the static default answer matches the calculator's default inputs --------------------------
const d = wynn(2500, 'slots', 'Red', 0);
assert(html.includes('<div class="big" id="w-fc">' + whole(d.fc) + '</div>'), 'static w-fc');
assert(html.includes('id="w-loss">' + money(d.loss) + ' at 7.74%'), 'static w-loss');
console.log('ok: wynn page — #fc ×3 tiers, lede, ratio ' + ratio + '×, 3 bands + Chairman, 29 benefit rows, static default');
