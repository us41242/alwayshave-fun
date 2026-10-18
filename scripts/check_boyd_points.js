// ponytail: pins the players-cards Boyd points/TC converter and the worked 47,000/41,000 example in its prose.
// usage: node scripts/check_boyd_points.js <guides/players-cards-compared/index.html>
const fs = require('fs'), assert = require('assert');
const html = fs.readFileSync(process.argv[2], 'utf8');
const src = html.split('const BOYD_TIERS')[1].split('function runBoyd')[0];
const boyd = new Function('return (() => { const BOYD_TIERS' + src + ' return boyd; })()')();
const r = boyd(47000, 41000);
assert.deepStrictEqual(r, {dollars: 47, slots: 47000, vp: 94000, tier: 'Emerald', toNext: 9000, next: 'Onyx', carry: 5000});
assert.equal(boyd(0, 18000).carry, 3000); assert.equal(boyd(0, 280000).carry, 40000); // Boyd's own examples
assert.equal(boyd(0, 749).tier, 'Ruby'); assert.equal(boyd(0, 750).tier, 'Sapphire'); assert.equal(boyd(0, 200000).next, undefined);
const sec = html.split('id="boyd-points"')[1].split('<h3>')[0];
for (const t of ['47,000 points is $47', '$47,000 through slots or $94,000 through video poker', '9,000 short of Onyx', 'starts next year at 5,000', '500 at Sapphire, 5,000 at Emerald, 10,000 at Onyx, 40,000 at Titanium']) assert(sec.includes(t), 'copy missing ' + t);
console.log('ok');
