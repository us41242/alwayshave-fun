// ponytail: runs the Diamond page's own script (repo file or live HTML) with no DOM, against the numbers in its copy.
// usage: node scripts/check_diamond_page.js <guides/caesars-diamond/index.html>
const fs = require('fs'), assert = require('assert');
if (!process.argv[2]) { console.error('usage: node check_diamond_page.js <index.html>'); process.exit(2); }
const html = fs.readFileSync(process.argv[2], 'utf8');
const js = html.split('<script>').slice(1).map(x => x.split('</script>')[0]).find(x => x.includes('function tierx'));
assert(js, 'tier script missing');
const tierx = new Function(js + '; return tierx;')();
const r = (goal, game, bonus, have = 0, bet = 25) => tierx({ goal, have, game, bonus, bet });
const L = k => Math.round(k.loss);
// Diamond four ways
assert.equal(r(15000, 'slots', false).coinIn, 75000); assert.equal(L(r(15000, 'slots', false)), 6000);
assert.equal(r(15000, 'slots', true).coinIn, 25000); assert.equal(L(r(15000, 'slots', true)), 2000);
assert.equal(r(15000, 'vp', false).coinIn, 150000); assert.equal(L(r(15000, 'vp', false)), 690);
let k = r(15000, 'vp', true); assert.equal(k.coinIn, 50000); assert.equal(L(k), 230); assert.deepEqual(k.days, [5000]);
// prose: 2,000 hands, a bit over 3 h, ~$4,900 swing, 1/26
assert.equal(k.coinIn / 25, 2000); assert(k.hours > 3 && k.hours < 3.5); assert.equal(Math.round(k.sd / 100), 49); assert.equal(Math.round(6000 / k.loss), 26);
// every-tier table, row by row: slots spread, slots bonus, vp spread, vp bonus
const T = { 5000: [2000, 1000, 230, 115], 15000: [6000, 2000, 690, 230], 25000: [10000, 3600, 1150, 414], 75000: [30000, 10000, 3450, 1150] };
for (const [g, row] of Object.entries(T)) assert.deepEqual([r(+g, 'slots', false), r(+g, 'slots', true), r(+g, 'vp', false), r(+g, 'vp', true)].map(L), row, 'tier ' + g);
// bonus-day plans in the prose
assert.deepEqual(r(5000, 'vp', true).days, [2500]);
k = r(25000, 'vp', true); assert.equal(k.earn, 9000); assert.deepEqual(k.days.slice().sort((a, b) => a - b), [1000, 2500, 5000]);
k = r(75000, 'vp', true); assert.equal(k.earn, 25000); assert.deepEqual(k.days, Array(5).fill(5000));
// edges
assert.equal(r(15000, 'vp', true, 15000).loss, 0); assert.equal(r(15000, 'vp', true, 20000).need, 0);
assert.equal(r(15000, 'slots', true).sd, null); assert.equal(r(15000, 'vp', true, 0, 0).hours, 0);
for (const s of ['$75,000', '$6,000', '$25,000', '$2,000', '$150,000', '$690', '$50,000', '$230', '$4,900', '2,000 hands', '$115', '$414', '$1,150', '$3,450', '$30,000', '$10,000', '$3,600', '9,000 earned']) assert(html.includes(s), 'copy missing ' + s);
// forward Tier Credit calculator (#tc-calc): play -> credits, one bonus level per day on gaming only
const tjs = html.split('<script>').slice(1).map(x => x.split('</script>')[0]).find(x => x.includes('function tcx'));
assert(tjs, 'tier credit calculator script missing');
const tcx = new Function(tjs + '; return tcx;')();
let t = tcx({ slots: 5000 }); assert.deepEqual([t.base, t.bonus, t.total, t.tier, t.next.need, t.loss, t.freePlay], [1000, 1000, 2000, 'Gold', 3000, 400, 5]);
assert(html.includes('id="t-total">2,000<'), 'default output must match tcx default');
t = tcx({ slots: 25000 }); assert.equal(t.total, 15000); assert.equal(t.tier, 'Diamond');          // Diamond in a day, as the copy says
t = tcx({ slots: 25000, oneDay: false }); assert.equal(t.total, 5000); assert.equal(t.tier, 'Platinum');
t = tcx({ vp: 50000 }); assert.equal(t.total, 15000); assert.equal(Math.round(t.loss), 230);        // the $230 route
t = tcx({ slots: 12500 }); assert.equal(t.total, 7500);                                              // 2,500 -> +5,000
t = tcx({ slots: 2500 }); assert.equal(t.bonus, 125);
t = tcx({ spend: 5000 }); assert.equal(t.bonus, 0); assert.equal(t.total, 5000);                    // spend never triggers the bonus
t = tcx({ spend: 15000, oneDay: false }); assert.equal(t.tier, 'Diamond');                           // $15,000 no-gambling Diamond
t = tcx({ have: 149999, slots: 5 }); assert.equal(t.tier, 'Seven Stars (invitation only)'); assert.equal(t.next, null);
t = tcx({ have: 24999 }); assert.equal(t.tier, 'Diamond'); assert.equal(t.next.need, 1);
for (const s of ['0&ndash;4,999', '5,000&ndash;14,999', '15,000&ndash;24,999', '25,000&ndash;74,999', '75,000&ndash;149,999', '150,000+', '$1 per 200 Reward Credits', '0.1%']) assert(html.includes(s), 'tier table missing ' + s);
console.log('ok');
