// ponytail: runs the EV calculator page's own script (repo file or live HTML) with no DOM, against the page's worked examples.
// usage: node scripts/check_tev_page.js <tools/tournament-ev-calculator/index.html>
const fs = require('fs'), assert = require('assert');
if (!process.argv[2]) { console.error('usage: node check_tev_page.js <index.html>'); process.exit(2); }
const js = fs.readFileSync(process.argv[2], 'utf8').split('<script>').slice(1).map(x => x.split('</script>')[0]).find(x => x.includes('function tevx'));
assert(js, 'EV script missing');
const tevx = new Function(js + '; return tevx;')();
const d = { E: 200, N: 40, R: 0, r: 0, G: 10000, pct: 0, M: 5, X: 0, s: 1 }, t = o => tevx({ ...d, ...o });
let k = t({}); assert.equal(k.share, 250); assert.equal(k.ev, 50); assert.equal(k.be, 50); assert.equal(k.pct, 1.25); assert.equal(k.cash, 0.125); assert.equal(k.prize, 2000);
k = t({ N: 60 }); assert.equal(Math.round(k.ev), -33); assert.equal(k.need.toFixed(2), '1.20');
k = t({ R: 100, r: 1 }); assert.equal(k.cost, 300); assert.equal(k.ev, -50);                      // rebuys under a guarantee
k = t({ E: 100, G: 0, pct: 100, R: 100, r: 1, N: 500 }); assert.equal(k.ev, 0); assert.equal(k.be, Infinity);  // 100% payback: even at any size
k = t({ E: 100, G: 0, pct: 80 }); assert.equal(k.need, 1.25); assert.equal(k.be, 0);             // casino keeps 20%
k = t({ E: 100, G: 5000, pct: 80, N: 100 }); assert.equal(k.P, 8000); assert.equal(k.be, 50);     // whichever is bigger
k = t({ N: 3 }); assert.equal(k.cash, 1);                                                         // more places than players
k = t({ s: 1.5, N: 60 }); assert(k.mine > 0 && k.ev < 0);
assert.equal(t({ E: 0 }).be, Infinity); assert.equal(t({ G: 0 }).need, Infinity);                  // freeroll, empty pool
console.log('ok');
