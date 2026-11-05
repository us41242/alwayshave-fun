// ponytail: runs the video poker trainer's own engine (repo file or live HTML) in node and
// checks that every error hand lands in the right named leak. The leak report is the only
// part of the coach a player sees accumulate, so a misfiled leak teaches the wrong habit.
// Each case derives the best hold from the real exact-EV enumeration, not a pinned answer.
// usage: node scripts/check_vp_leaks.js <video-poker/index.html>
const fs = require('fs'), assert = require('assert');
if (!process.argv[2]) { console.error('usage: node check_vp_leaks.js <video-poker.html>'); process.exit(2); }
const src = fs.readFileSync(process.argv[2], 'utf8');
const js = src.split('<script>').map(x => x.split('</script>')[0]).find(x => x.includes('function leak('));
assert(js, 'video poker engine with leak() missing');
const engine = js.split('// ---- UI ----')[0];
assert(engine.includes('function leak('), 'leak() must live above the UI section so it stays testable');
const api = new Function(engine.replace(/console\.assert/g, '(()=>{})') +
  '; return {analyze, leak, LEAKS, H, GAMES, setGame: k => { game = GAMES[k]; }};')();
const {analyze, leak, LEAKS, H} = api;

// every leak id the UI can store must have copy to render
const ids = new Set(LEAKS.map(l => l[0]));
assert.equal(ids.size, LEAKS.length, 'duplicate leak id');
for (const l of LEAKS) assert(l[0] && l[1] && l[2], 'leak ' + l[0] + ' missing text or fix');

// classify(dealt, myHold) -> leak id, using the engine's own best hold
function classify(dealtStr, mineStr) {
  const dealt = H(dealtStr), mine = mineStr ? H(mineStr) : [];
  for (const c of mine) assert(dealt.includes(c), mineStr + ' not dealt in ' + dealtStr);
  const best = analyze(dealt), top = best[0].held;
  assert.notDeepEqual([...mine].sort(), [...top].sort(), 'test hand ' + mineStr + ' is the BEST hold, not an error');
  const id = leak(dealt, mine, top);
  assert(ids.has(id), 'leak() returned unknown id ' + id);
  return id;
}
const T = [];
const is = (want, dealt, mine, why) => { const got = classify(dealt, mine); T.push([want, got, why]);
  assert.equal(got, want, `${why}: dealt ${dealt}, held ${mine || 'nothing'} -> ${got}, expected ${want}`); };

// --- 9/6 Jacks or Better ---
api.setGame('job96');
is('kicker', 'Jh Jd Ah 4c 7s', 'Jh Jd Ah', 'high pair + ace kicker (best: the pair alone)');
is('kicker', '9h 9d 9s Ah 4c', '9h 9d 9s Ah', 'trips + kicker');
is('heldmade', 'Ah Kh Qh Jh 5h', 'Ah Kh Qh Jh 5h', 'kept the made flush over four to the royal');
is('brokemade', '2h 5h 8h Jh Kh', 'Jh Kh', 'broke a made flush for two to the royal');
is('royal', 'Ah Kh Qh 7s 3d', 'Ah Kh', 'two high cards when three to a royal was there');
is('toofew', 'Ah Kd Qc 7s 2h', 'Ah', 'one high card when KQ was the hold');
is('toomany', '3h 7d 9s Jc 4h', '3h 7d 9s Jc 4h', 'kept five junk cards');

// --- Full-Pay Deuces Wild: the deuce rule outranks everything ---
api.setGame('dw');
is('deuce', '2h Kd 7s 4c 9h', 'Kd', 'threw the deuce');
is('deuce', '2h 2d 9s 4c 7h', '2h 9s 4c 7h', 'threw one of two deuces');

// --- the classifier must not fire on a correct hold (guarded inside classify) ---
api.setGame('job96');
assert.throws(() => classify('Ah Kh Qh Jh Th', 'Ah Kh Qh Jh Th'), /is the BEST hold/, 'made royal is not an error');

console.log(`check_vp_leaks: ${T.length} hands classified, ${LEAKS.length} leaks defined — ok`);
