// ponytail: runs the MGM page's own script (repo file or live HTML) with no DOM, against the numbers in its copy.
// usage: node scripts/check_mgm_page.js <guides/mgm-gold-platinum/index.html>
const fs = require('fs'), assert = require('assert');
if (!process.argv[2]) { console.error('usage: node check_mgm_page.js <index.html>'); process.exit(2); }
const html = fs.readFileSync(process.argv[2], 'utf8');
const js = html.split('<script>').slice(1).map(x => x.split('</script>')[0]).find(x => x.includes('function mgmx'));
assert(js, 'mgm script missing');
const mgmx = new Function(js + '; return mgmx;')();
const r = (goal, bonus, have = 0, rate = 4, edge = 0) => mgmx({ goal, have, rate, bonus, edge });
// table: spread vs Accelerator days
const T = { 20000: [5000, 3750], 75000: [18750, 10000], 200000: [50000, 20000] };
for (const [g, row] of Object.entries(T)) assert.deepEqual([r(+g, false).spend, r(+g, true).spend], row, 'tier ' + g);
// plans in the table/prose
assert.deepEqual(r(20000, true).days, [10000]); assert.equal(r(20000, true).earn, 15000);
assert.deepEqual(r(75000, true).days, [40000]); assert.equal(r(75000, true).day, 10000);
assert.deepEqual(r(200000, true).days, [40000, 40000]);
assert.equal(2 * (20000 + 20000), 80000); assert(80000 >= 75000); // two 20,000 days also clear Gold for $10,000
assert.equal((40000 + 60000) / 10000, 10); assert.equal(10 / 4, 2.5);
// Gold then a second $10,000 day = Platinum
assert.equal(r(200000, true, 100000).spend, 10000);
// returns on the Platinum plan: $200 points + $100 + $200 celebration + $600 air
assert.equal(20000 * 0.01 + 100 + 200 + 600, 1100);
// gaming: your rate and edge
assert.equal(r(75000, true, 0, 1, 0.46).loss, 40000 * 0.0046);
// edges
assert.equal(r(75000, true, 80000).need, 0); assert.equal(r(75000, true, 75000).spend, 0); assert.equal(r(75000, true, 0, 0).spend, 0);
for (const s of ['$18,750', '$10,000', '$50,000', '$20,000', '$5,000', '$3,750', '$1,100', '$100 Tier Celebration Credit', '<b>$200</b>', 'up to $600', '0.46%', 'December 31, 2026']) assert(html.includes(s), 'copy missing ' + s);
console.log('ok');
