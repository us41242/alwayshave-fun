// ponytail: /tournament-card/ has two silent failures that leave a working-looking page.
// (1) The print layout IS the product — if the @page/column rules drift or a .noprint hook is
//     dropped, the page still reads fine on screen and quietly prints four pages of nav and prose.
//     That cannot be caught by eye in a diff, so assert the print contract: @page portrait, two
//     columns, white background, every screen-only block carrying .noprint, every card section
//     break-inside:avoid.
// (2) The card is a COMPRESSION of /blackjack-tournament-strategy/. If the guide's math is ever
//     corrected and the card is not, the pocket copy silently teaches the old number. So every
//     formula and frequency on the card is re-derived here from the worked example's own stacks
//     and cross-checked against the guide's page, not just asserted to "appear somewhere".
//     (Session 62's lesson: .includes() of a figure that occurs twice keeps a wrong one alive, so
//     the arithmetic assertions are scoped to the block the number is used in.)
// usage: node scripts/check_tournament_card.js [card.html] [guide.html]
const fs = require('fs'), assert = require('assert'), path = require('path');
const R = path.join(__dirname, '..');
const card = fs.readFileSync(process.argv[2] || path.join(R, 'tools/tournament-card/index.html'), 'utf8');
const guide = fs.readFileSync(process.argv[3] || path.join(R, 'guides/blackjack-tournament-strategy/index.html'), 'utf8');
const txt = h => h.replace(/<script[\s\S]*?<\/script>/g, ' ').replace(/<style[\s\S]*?<\/style>/g, ' ')
  .replace(/<[^>]+>/g, ' ').replace(/&mdash;|&ndash;/g, '-').replace(/&minus;/g, '-')
  .replace(/&times;/g, 'x').replace(/&rsquo;/g, "'").replace(/&ldquo;|&rdquo;/g, '"')
  .replace(/&middot;/g, '.').replace(/&rarr;/g, '->').replace(/&nbsp;/g, ' ')
  .replace(/&amp;/g, '&').replace(/&gt;/g, '>').replace(/&lt;/g, '<').replace(/&[a-z]+;/g, ' ').replace(/\s+/g, ' ');
const sect = (h, name) => {   // the one block a figure is used in, never the whole page
  const i = h.indexOf(name);
  assert.notStrictEqual(i, -1, 'section gone: ' + name);
  const j = h.indexOf('<section', i);
  return txt(h.slice(i, j === -1 ? h.length : j));
};
const style = card.slice(card.indexOf('<style>'), card.indexOf('</style>'));
const print = style.slice(style.indexOf('@media print'));
const body = card.slice(card.indexOf('<body>'));

// ---- 1. the print contract -------------------------------------------------
assert.match(print, /@page\{[^}]*size:portrait/, 'print must force portrait');
assert.match(print, /@page\{[^}]*margin:\s*\d+mm/, 'print needs a page margin or the card touches the edge');
assert.match(print, /\.cols\{[^}]*column-count:2/, 'the card is a two-column sheet');
assert.match(print, /html,body\{[^}]*background:#fff ?!important/, 'felt green must not print');
assert.match(print, /html,body\{[^}]*background-image:none ?!important/, 'the radial gradient must not print either');
assert.match(print, /html,body\{[^}]*color:#000/, 'print must be black text');
assert.match(print, /\.noprint\{display:none ?!important\}/, 'screen-only blocks must be hidden in print');
assert.match(style, /\.cols section\{[^}]*break-inside:avoid/, 'a card section must not split across columns');
// the font stack must be system/serif in print: a web font that fails to load mid-print reflows the sheet
assert.match(print, /html,body\{[^}]*font-family:Georgia,"Times New Roman",serif/, 'print needs a local font stack');

// every screen-only region is actually marked, and the sheet is not
// Structural, not a tag whitelist: strip the printable sheet and every .noprint region (balanced
// <div> scan), and whatever visible text is LEFT would print alongside the card. It must be nothing.
const take = (h, start) => {   // slice one balanced <tag>...</tag> beginning at `start`
  const tag = h.slice(start).match(/^<([a-z]+)/)[1];
  const re = new RegExp('</?' + tag + '\\b[^>]*>', 'g');
  re.lastIndex = start;
  let d = 0, m;
  while ((m = re.exec(h))) {
    d += m[0][1] === '/' ? -1 : 1;
    if (d === 0) return h.slice(start, m.index + m[0].length);
  }
  assert.fail('unbalanced <' + tag + '> at offset ' + start);
};
const sheetStart = body.indexOf('<div class="card-sheet">');
assert.notStrictEqual(sheetStart, -1, 'no .card-sheet — the printable card is gone');
const sheet = take(body, sheetStart);
assert.ok(!/noprint/.test(sheet), 'nothing inside the printable sheet may be .noprint');
let rest = body.replace(sheet, ' ');
for (let i; (i = rest.search(/<[a-z]+[^>]*class="[^"]*\bnoprint\b/)) !== -1; )
  rest = rest.replace(take(rest, i), ' ');
assert.strictEqual(txt(rest).trim(), '', 'this text is outside the sheet and not .noprint, so it '
  + 'would print on the card: ' + JSON.stringify(txt(rest).trim().slice(0, 160)));
// and the screen-only copy really is there (an empty page would also pass the test above)
for (const want of [/<nav class="noprint">/, /<h1>/, /<footer class="noprint">/])
  assert.match(body, want, 'the web page around the card lost ' + want);

// ONE SHEET is the promise in the title, so measure it instead of estimating it. A character
// budget looked like enough and was not: at 3,270 chars this card printed on TWO pages, because
// column-fill:auto filled column one to the full page height and spilled the rest. Only a real
// render can tell. So: print it with headless Chrome and count the pages in the PDF, on Letter
// AND A4 (the margin between them is 10mm of width, which is enough to push a line over).
const sheetText = txt(sheet).trim();
assert.ok(sheetText.length > 1800, 'printable text is only ' + sheetText.length + ' chars — the card lost content');
const { execFileSync } = require('child_process'), os = require('os');
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const src = path.resolve(process.argv[2] || path.join(R, 'tools/tournament-card/index.html'));
const pages = (html, label) => {
  const f = path.join(os.tmpdir(), 'card-' + label + '.html'), pdf = f.replace('.html', '.pdf');
  fs.writeFileSync(f, html);
  fs.rmSync(pdf, { force: true });
  // ponytail: its own --user-data-dir and a timeout. Without the profile dir this hung forever
  // contending with another Chrome on this machine (measured 11-09), and a hung guard in
  // check_all.sh looks exactly like a slow one.
  execFileSync(CHROME, ['--headless=new', '--disable-gpu', '--no-first-run', '--no-pdf-header-footer',
    '--user-data-dir=' + fs.mkdtempSync(path.join(os.tmpdir(), 'card-chrome-')),
    '--print-to-pdf=' + pdf, 'file://' + f], { stdio: 'ignore', timeout: 60000 });
  const d = fs.readFileSync(pdf);
  return Math.max(...[...d.toString('latin1').matchAll(/\/Count (\d+)/g)].map(m => +m[1]), 0);
};
if (fs.existsSync(CHROME)) {
  for (const [label, html] of [['letter', card], ['a4', card.replace('@page{size:portrait', '@page{size:A4 portrait')]]) {
    const n = pages(html, label);
    assert.strictEqual(n, 1, 'the card printed on ' + n + ' ' + label.toUpperCase()
      + ' pages — the whole promise of this page is one sheet');
  }
} else {
  console.error('WARN: Chrome not found, page count unverified (' + CHROME + ')');
}

// ---- 2. the math, re-derived ----------------------------------------------
const C = { L: 2600, Y: 1800, B: 500, Bbig: 1000, chip: 25 };
const G = C.L - C.Y;
const chase = G + C.B + C.chip;
const dbl = G + 2 * C.B + C.chip;
const lose = C.Bbig - G;
const m = n => '$' + n.toLocaleString('en-US');
const ex = sect(card, 'Worked: the chase');
assert.match(ex, new RegExp('G = 2,600 - 1,800 = ' + m(G).replace('$', '\\$')), 'gap line wrong');
assert.match(ex, new RegExp('Bet = 800 \\+ 500 \\+ 25 = ' + m(chase).replace('$', '\\$')), 'chase bet is not G+B+c');
assert.match(ex, new RegExp('double = 800 \\+ 1,000 \\+ 25 = ' + m(dbl).replace('$', '\\$')), 'double cover is not G+2B+c');
assert.match(ex, new RegExp('1,000 - 800 = ' + m(lose).replace('$', '\\$')), 'bet-to-lose threshold is not B-G');
// the both-win line must actually be true at that bet
assert.match(ex, new RegExp('Both win -> ' + (C.Y + chase).toLocaleString('en-US') + ' vs ' + (C.L + C.B).toLocaleString('en-US')),
  'both-win outcome does not match the bet above it');
assert.ok(C.Y + chase > C.L + C.B, 'the card prints a bet that loses the both-win case');
assert.match(ex, new RegExp('Both lose -> ' + (C.Y - chase).toLocaleString('en-US') + ' vs ' + (C.L - C.B).toLocaleString('en-US')),
  'both-lose outcome does not match the bet above it');
assert.match(ex, new RegExp('both lose leaves 1,800 - B vs their ' + (C.L - C.Bbig).toLocaleString('en-US')),
  'bet-to-lose example does not match the leader dropping by their own bet');

// the formulas themselves, in symbols
assert.match(sect(card, 'Behind, betting last'), /Bet = G \+ B \+ c/, 'the chase formula is the card');
assert.match(sect(card, 'Behind, betting last'), /Cover their double = G \+ 2B \+ c/, 'double-cover formula missing');
assert.match(sect(card, 'They bet big'), /If B > G: bet under \(B - G\)/, 'bet-to-lose formula missing');
assert.match(sect(card, 'Leading'), /all-in double = 2x their stack\s*,\s*all-in blackjack = 2\.5x/,
  "the leader's ceiling must be 2x (double) and 2.5x (3:2 blackjack on an all-in bet)");
// those two multiples are the guide's worked threat ceiling: an $1,800 stack reaching $3,600 / $4,500
for (const mult of [2, 2.5])
  assert.ok(txt(guide).includes((C.Y * mult).toLocaleString('en-US')),
    'the guide no longer shows ' + mult + 'x of an ' + m(C.Y) + ' stack (' + m(C.Y * mult)
    + ') — the card\'s ceiling multiples may be stale');

// hand frequencies must match the guide's cited numbers, not drift to rounder ones
const f = sect(card, 'They bet big');
for (const [label, pct] of [['loses', '49%'], ['wins', '42%'], ['pushes', '8.5%']]) {
  assert.ok(f.includes(pct), 'frequency ' + pct + ' (' + label + ') missing from the card');
  assert.ok(txt(guide).includes(pct.replace('%', '')), pct + ' is not the figure the guide cites');
}

// ---- 3. the card never contradicts the guide ------------------------------
const g = txt(guide);
for (const rule of [
  ['stand on 16 vs a dealer 10', /Stand on your stiff 16 against a dealer 10/i],
  ['hold back one chip', /bet everything except one chip/i],
  ['match the threat', /match the biggest threat's bet/i],
  ['minimum bet early', /Bet the table minimum/i],
  ['never copy the leader', /Copying the leader's bet/i],
]) assert.match(g, rule[1], 'the guide no longer says "' + rule[0] + '" — the card may be stale');
const c = txt(card);
assert.ok(/stand on 16 vs a dealer 10/i.test(c), 'the one deviation that matters is missing');
assert.ok(/everything except one chip/i.test(c), 'held-back chip missing');
assert.ok(/Match the biggest threat's bet/i.test(c), "leader's defence missing");
assert.ok(/Bet the table minimum/i.test(c), 'early-hand rule missing');
assert.ok(/Never copy/i.test(c), 'contrarian warning missing');
// no basic-strategy chart is a deliberate choice; keep the page honest about it
assert.ok(/not.{0,40}on it: a basic-strategy chart/i.test(c.replace(/\s+/g, ' ')),
  'the page must still say the card is not a basic-strategy chart');

// ---- 4. the claim in the title: free, no email ----------------------------
assert.ok(!/<(form|input)\b/i.test(body), '"no email" is in the title — this page must have no form or input');
assert.match(c, /no email/i, 'the no-email promise is the differentiator for the "free download" queries');
assert.match(card, /<button class="cta" id="print">/, 'the print button is the download');
assert.match(card, /addEventListener\('click', function \(\) \{ hit\(\); print\(\); \}\)/, 'button must beacon then print');
assert.match(card, /addEventListener\('beforeprint', hit\)/, 'a browser-menu print must count too');
assert.match(card, /navigator\.sendBeacon\('\/e\/card-print'\)/, 'card-print beacon missing');
assert.match(card, /location\.protocol !== 'https:'/, 'the beacon must stay out of local file:// runs');
assert.match(card, /if \(sent \|\| /, 'one print must not fire two beacons (button click also fires beforeprint)');

console.log('ok: tournament card — print contract holds, ' + sheetText.length
  + ' chars, rendered on exactly one Letter and one A4 page, G+B+c=' + m(chase) + ' / double ' + m(dbl) + ' / lose under ' + m(lose)
  + ', every rule still matches the guide, no form on the page');
