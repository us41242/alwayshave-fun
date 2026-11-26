// ponytail: Final Hand's first screen, as a cold phone visitor gets it. Renders the page in headless
// Chrome (repo file or curled live HTML) and checks hand 1 says what the game is above the Bet button,
// the coach doesn't call a six-way tie "the leader", and the narrow layout puts the coach right
// after the table. Ceiling: checks hand 1 only; later hands aren't played here.
// usage: node scripts/check_final_hand.js [index.html]
const { execFileSync } = require('child_process'), assert = require('assert'), path = require('path'), fs = require('fs');
const f = path.resolve(process.argv[2] || path.join(__dirname, '../games/final-hand/index.html'));
const dom = execFileSync('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  ['--headless=new', '--disable-gpu', '--virtual-time-budget=3000', '--dump-dom', 'file://' + f],
  { encoding: 'utf8', timeout: 60000, stdio: ['ignore', 'pipe', 'ignore'], maxBuffer: 1 << 26 });
const el = id => { const m = dom.match(new RegExp('id="' + id + '"[^>]*>([\\s\\S]*?)</div>')); assert(m, id + ' missing'); return m[1]; };
const msg = el('msg'), coach = el('coachBody');
assert(/6 players, 15 hands, most chips wins/.test(msg) && /Place your bet/.test(msg), 'hand-1 opener missing from #msg: ' + msg);
assert(/id="betAmt"/.test(dom), 'bet controls not rendered');
assert(/tied for the lead/.test(coach), 'hand 1 (all stacks equal) should read "tied for the lead": ' + coach);
assert(!/the leader\./.test(coach) && !/#\d of 6/.test(coach), 'coach gives a rank in a six-way tie: ' + coach);
const css = fs.readFileSync(f, 'utf8').split('<style>')[1].split('</style>')[0].replace(/\/\*[\s\S]*?\*\//g, '');
const m = css.match(/@media\(max-width:820px\)\{([\s\S]*?\})\s*\}/); assert(m, 'narrow-layout block missing');
const ord = sel => { const x = m[1].match(new RegExp(sel.replace(/[.#]/g, '\\$&') + '\\{order:(\\d)')); assert(x, sel + ' order missing'); return +x[1]; };
assert(/\.board>div\{display:contents\}/.test(m[1]), 'column wrappers not flattened');
assert(ord('.board .table') < ord('.board #coachPanel') && ord('.board #coachPanel') < ord('.board .panel'), 'coach is not straight after the table on phones');
console.log('ok; hand-1 opener, tie wording, coach follows table on narrow screens');
