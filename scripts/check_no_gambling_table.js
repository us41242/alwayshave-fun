// ponytail: pins the players-cards "status without gambling" table: every price = ceil(threshold / published non-gaming rate).
// usage: node scripts/check_no_gambling_table.js <guides/players-cards-compared/index.html>
const fs = require('fs'), assert = require('assert');
if (!process.argv[2]) { console.error('usage: node check_no_gambling_table.js <index.html>'); process.exit(2); }
const html = fs.readFileSync(process.argv[2], 'utf8');
const sec = html.split('id="no-gambling"')[1].split('<h2 id="programs">')[0];
const $ = n => '$' + n.toLocaleString('en-US');
const price = (tc, rate) => Math.ceil(tc / rate);
const P = { // tier thresholds as published, rate per $1 of the cheapest non-gaming spend
  Station: [50, { Gold: 1000, Platinum: 40000, President: 100000, Chairman: 300000 }],
  'Resorts World': [5, { Elite: 3000, Prime: 75000, Monarch: 250000, Imperial: 1000000 }],
  Venetian: [2, { Sapphire: 3000, Ruby: 20000, Diamond: 50000 }],
  MGM: [4, { Pearl: 20000, Gold: 75000, Platinum: 200000 }],
  Caesars: [1, { Platinum: 5000, Diamond: 15000, 'Diamond Plus': 25000, 'Diamond Elite': 75000 }],
};
for (const [prog, [rate, tiers]] of Object.entries(P)) {
  const row = sec.split('<tr><td>' + prog + '</td>')[1].split('</tr>')[0];
  assert(row.includes('<b>' + rate + '</b>'), prog + ' rate');
  for (const [t, tc] of Object.entries(tiers)) assert(row.includes(t + ' <b>' + $(price(tc, rate)) + '</b>'), prog + ' ' + t + ' ' + $(price(tc, rate)));
}
// MGM accelerator: bonus on TC earned in one day (5k+1,250, 10k+5k, 20k+20k, 40k+60k); min spend at 4/$1
const bonus = e => e >= 40000 ? 60000 : e >= 20000 ? 20000 : e >= 10000 ? 5000 : e >= 5000 ? 1250 : 0;
const oneDay = goal => { for (let d = 1; ; d++) if (4 * d + bonus(4 * d) >= goal) return d; };
assert.equal(oneDay(20000), 3750); assert.equal(oneDay(75000), 10000);
assert.equal(2 * oneDay(100000), 20000); // Platinum: two 40,000 days = 200,000
for (const t of ['Pearl <b>$3,750</b>', 'Gold <b>$10,000</b> in one day', 'Platinum <b>$20,000</b> over two', '$600 of meals', 'one $800 hotel bill', '$10,000 of resort spend', '$15,000 of room and dining']) assert(sec.includes(t), 'copy missing ' + t);
console.log('ok');
