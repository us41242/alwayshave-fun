// ponytail: runs the Olympus page's own script (repo file or live HTML) with no DOM, against the numbers in its copy.
// usage: node scripts/check_olympus_page.js <guides/caesars-olympus/index.html>
const fs = require('fs'), assert = require('assert');
if (!process.argv[2]) { console.error('usage: node check_olympus_page.js <index.html>'); process.exit(2); }
const html = fs.readFileSync(process.argv[2], 'utf8');
const js = html.split('<script>').slice(1).map(x => x.split('</script>')[0]).find(x => x.includes('function olx'));
assert(js, 'Olympus script missing');
const olx = new Function(js + '; return olx;')();
const r = (game, bonus, have = 0, bet = 25) => olx({ have, game, bonus, bet });
// the four-route table
let k = r('slots', false); assert.equal(k.coinIn, 1500000); assert.equal(Math.round(k.loss), 120000);
k = r('slots', true); assert.equal(k.coinIn, 500000); assert.equal(Math.round(k.loss), 40000); assert.deepEqual(k.days, Array(20).fill(5000));
k = r('vp', false); assert.equal(k.coinIn, 3000000); assert.equal(Math.round(k.loss), 13800);
k = r('vp', true); assert.equal(k.coinIn, 1000000); assert.equal(Math.round(k.loss), 4600);
// prose: ~67 hours, a bit over 3 h per bonus day, ~$22,000 swing, 1/26 of the price
assert.equal(Math.round(k.hours), 67); assert(k.dayHours > 3 && k.dayHours < 3.5); assert.equal(Math.round(k.sd / 1000), 22);
assert.equal(Math.round(120000 / k.loss), 26);
// edges: already there, partial year, slots have no published variance
assert.equal(r('vp', true, 300000).loss, 0); assert.equal(r('vp', true, 450000).need, 0);
k = r('vp', true, 290000); assert.equal(k.need, 10000); assert(k.earn <= 5000 && k.earn >= 3334);
assert.equal(r('slots', true).sd, null); assert.equal(r('vp', true, 0, 0).hours, 0);
for (const s of ['$1,500,000', '$120,000', '$500,000', '$40,000', '$3,000,000', '$13,800', '$1,000,000', '$4,600', '$22,000', '$700 to $1,400']) assert(html.includes(s), 'copy missing ' + s);
console.log('ok');
