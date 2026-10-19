// ponytail: re-derives the players-cards Binion's/Four Queens All Access numbers from the posted rules and pins them in the prose.
// usage: node scripts/check_binions.js <guides/players-cards-compared/index.html>
const fs = require('fs'), assert = require('assert');
const sec = fs.readFileSync(process.argv[2], 'utf8').split('id="binions"')[1].split('<h2')[0];
const pct = (x, d = 2) => +(x * 100).toFixed(d);
const SLOT = 5, VP = 8, PTS = 40, CASH = 1, COMP = 2, FSP = 50, BONUS = 500, BOTH = 25; // rules + 2026 flyer
assert.equal(pct(CASH / (PTS * SLOT)), 0.5); assert.equal(pct(COMP / (PTS * SLOT)), 1);
assert.equal(pct(CASH / (PTS * VP)), 0.31); assert.equal(pct(COMP / (PTS * VP)), 0.63);
const month = BONUS / PTS * (CASH + COMP) + FSP; // one property
assert.equal(month, 87.5); assert.equal(BONUS * SLOT, 2500); assert.equal(BONUS * VP, 4000);
assert.equal(pct(month / 2500), 3.5); assert.equal(pct(month / 4000, 1), 2.2);
assert.equal(2 * month + BOTH, 200); assert.equal(pct(200 / 5000), 4);
for (const t of ['0.5% cash plus 1% comps', '0.31% cash plus 0.63% comps', '$2,500 through slots or $4,000 through video poker',
  '$12.50 cash, $25 in comps and $50 of free play', '$87.50, or 3.5% of $2,500', '1.5% base rebate', '$200 on $5,000 (4%)', '$4,000 (2.2%)',
  'has no published tiers', '13 months', 'October 31, 2026']) assert(sec.includes(t), 'copy missing ' + t);
console.log('ok');
