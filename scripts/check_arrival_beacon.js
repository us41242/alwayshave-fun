// ponytail: the arrival beacon is a pure silent failure — if it is missing, drifts, or stops
// matching the URL, the site keeps working and simply stops counting arrivals, which is the one
// number every other decision now rests on. So: every page in sitemap.xml must carry the SAME
// beacon block (byte-identical, no drift across 14 inline copies), the slug it derives must match
// that page's real URL path, and the filters must still be the ones we intend.
// usage: node scripts/check_arrival_beacon.js
const fs = require('fs'), assert = require('assert'), path = require('path');

const MARK = '/* ponytail: arrival beacon.';
const block = html => {
  const i = html.indexOf('<script>' + MARK);
  assert.notStrictEqual(i, -1, 'no arrival beacon');
  return html.slice(i, html.indexOf('</script>', i) + 9);
};

// sitemap URL -> the file that serves it (worker maps /final-hand/ and /video-poker-trainer/ to games/)
const FILE = {
  '/': 'index.html',
  '/final-hand/': 'games/final-hand/index.html',
  '/video-poker-trainer/': 'games/video-poker/index.html',
  '/tournament-bet-sizer/': 'tools/tournament-bet-sizer/index.html',
  '/tournament-ev-calculator/': 'tools/tournament-ev-calculator/index.html',
};
const root = path.join(__dirname, '..');
const urls = fs.readFileSync(path.join(root, 'sitemap.xml'), 'utf8')
  .match(/<loc>([^<]*)<\/loc>/g).map(m => new URL(m.slice(5, -6)).pathname);
assert.equal(urls.length, 14, 'sitemap page count changed: ' + urls.length);

// the beacon derives its slug the same way the page does, so run the page's own expression
const slug = p => '/e/v-' + (p.replace(/\//g, '') || 'home');

let first = null;
const run = (loc, nav) => new Function('location', 'navigator', `let sent; navigator.sendBeacon = u => sent = u;
  ${first.replace(/^<script>|<\/script>$/g, '')} return sent;`)(loc, nav);
for (const u of urls) {
  const f = FILE[u] || 'guides' + u + 'index.html';
  const b = block(fs.readFileSync(path.join(root, f), 'utf8'));
  if (first === null) first = b;
  assert.equal(b, first, 'arrival beacon drifted in ' + f);
  // the slug must be this page's URL, derived by the page's own code, not a hand-written string
  const got = run({ protocol: 'https:', pathname: u }, { sendBeacon: null, webdriver: false, userAgent: 'Mozilla/5.0 Safari' });
  assert.equal(got, slug(u), `${f} would report ${got}, not ${slug(u)}`);
}
// the filters we rely on: file:// stays out (local checks), automation stays out (our own headless runs).
const https = { protocol: 'https:', pathname: '/casino-comps/' };
const human = { sendBeacon: null, webdriver: false, userAgent: 'Mozilla/5.0 (iPhone) Safari/605' };
assert.equal(run(https, human), '/e/v-casino-comps', 'a real https visit must beacon');
assert.equal(run({ protocol: 'file:', pathname: '/tmp/x/index.html' }, human), undefined, 'file:// must not beacon');
assert.equal(run(https, { ...human, webdriver: true }), undefined, 'navigator.webdriver must not beacon');
assert.equal(run(https, { ...human, userAgent: 'HeadlessChrome/157.0.0.0' }), undefined, 'HeadlessChrome must not beacon');
console.log('ok: arrival beacon identical on all ' + urls.length + ' pages, slugs match their URLs, filters hold');
