// ponytail: guards /players-cards-compared/#what-is — the "what is a players card" answer (Bing query, 2026-11-20).
// Re-derives "$100 through a slot earns 10 to 20 cents" from the page's own PROGRAMS table, then pins the copy.
// usage: node scripts/check_players_card_def.js <guides/players-cards-compared/index.html>
const fs = require('fs'), assert = require('assert');
const html = fs.readFileSync(process.argv[2], 'utf8');
const sec = html.split('id="what-is"')[1].split('<h2')[0];
const P = eval(html.match(/const PROGRAMS = (\[[\s\S]*?\]);/)[1]);
const cents = P.filter(p => p.slots).map(p => +(100 * p.slots * p.value * 100).toFixed(2));
assert.equal(cents.length, 4, 'four programs publish a slot rate');
assert.equal(Math.min(...cents), 10); assert.equal(Math.max(...cents), 20);
for (const t of ['four big programs that publish a rate', '$100 through a slot earns 10 to 20 cents', 'Boyd only once you reach Sapphire',
  'NRS 463.350', 'photo ID', 'all 27 Boyd destinations', 'win/loss', 'W-2G']) assert(sec.includes(t), 'copy missing ' + t);
assert(html.includes('<a href="#what-is">'), 'toc link');
console.log('ok');
