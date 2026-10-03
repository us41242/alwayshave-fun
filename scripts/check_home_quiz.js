// ponytail: runs the homepage last-hand quiz's own script (repo file or live HTML) with no DOM
// and checks it against the homepage table's worked example.
// usage: node scripts/check_home_quiz.js <index.html>
const fs = require('fs'), assert = require('assert');
if (!process.argv[2]) { console.error('usage: node check_home_quiz.js <index.html>'); process.exit(2); }
const js = fs.readFileSync(process.argv[2], 'utf8').split('<script>').slice(1).map(x => x.split('</script>')[0]).find(x => x.includes('lh-quiz'));
assert(js, 'quiz script missing');
const { wins, deal } = new Function(js + '; return {wins, deal};')();
// homepage table: leader $2,600 bets $500, you $1,800 -> chase $1,325 wins 2, copy wins 1, minimum 0
assert.equal(wins(1800, 2600, 500, 1325), 2); assert.equal(wins(1800, 2600, 500, 500), 1); assert.equal(wins(1800, 2600, 500, 25), 0);
// leader bets big, can't be reached: the minimum (lose with the leader) wins 2, all in 1
assert.equal(wins(1800, 2600, 1500, 25), 2); assert.equal(wins(1800, 2600, 1500, 1800), 1);
const seen = {};
for (let n = 0; n < 20000; n++) {
  const h = deal();
  assert(h.Y < h.L && h.opts.every(o => o[1] >= 25 && o[1] <= h.Y && o[1] % 25 === 0), JSON.stringify(h));
  assert.equal(h.w.filter(x => x === h.best).length, 1);
  seen[h.opts[h.w.indexOf(h.best)][0]] = (seen[h.opts[h.w.indexOf(h.best)][0]] || 0) + 1;
}
console.log('ok; correct answer mix over 20,000 deals:', seen);
