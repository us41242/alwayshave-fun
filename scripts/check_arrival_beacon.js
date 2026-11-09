// ponytail: the arrival beacon is a pure silent failure — if it is missing, drifts, or stops
// matching the URL, the site keeps working and simply stops counting arrivals, which is the one
// number every other decision now rests on. So: every page in sitemap.xml must carry the SAME
// beacon block (byte-identical, no drift across 14 inline copies), the slug it derives must match
// that page's real URL path, the ~<source> suffix must bucket the referrer the way traffic.py
// parses it, and the filters must still be the ones we intend.
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
assert.equal(urls.length, 15, 'sitemap page count changed: ' + urls.length);

// the beacon derives its slug the same way the page does, so run the page's own expression
const slug = p => '/e/v-' + (p.replace(/\//g, '') || 'home');

let first = null;
const run = (loc, nav, doc = { referrer: '' }) => new Function('location', 'navigator', 'document',
  `let sent; navigator.sendBeacon = u => sent = u;
  ${first.replace(/^<script>|<\/script>$/g, '')} return sent;`)(loc, nav, doc);
for (const u of urls) {
  const f = FILE[u] || 'guides' + u + 'index.html';
  const b = block(fs.readFileSync(path.join(root, f), 'utf8'));
  if (first === null) first = b;
  assert.equal(b, first, 'arrival beacon drifted in ' + f);
  // the slug must be this page's URL, derived by the page's own code, not a hand-written string
  const got = run({ protocol: 'https:', pathname: u, host: 'alwayshave.fun' },
    { sendBeacon: null, webdriver: false, userAgent: 'Mozilla/5.0 Safari' });
  assert.equal(got, slug(u) + '~direct', `${f} would report ${got}, not ${slug(u)}~direct`);
}
// the filters we rely on: file:// stays out (local checks), automation stays out (our own headless runs).
const https = { protocol: 'https:', pathname: '/casino-comps/', host: 'alwayshave.fun' };
const human = { sendBeacon: null, webdriver: false, userAgent: 'Mozilla/5.0 (iPhone) Safari/605' };
assert.equal(run(https, human), '/e/v-casino-comps~direct', 'a real https visit must beacon');

// The ~<source> bucket. Every future distribution-vs-conversion call is read off these buckets, and
// a referrer that silently collapsed to '' or leaked a path would be invisible on the dashboard.
const src = ref => {
  const got = run(https, human, { referrer: ref });
  assert.equal(got.split('~').length, 2, 'source must be exactly one ~ segment: ' + got);
  assert.equal(got.split('~')[0], '/e/v-casino-comps', 'page slug changed: ' + got);
  return got.split('~')[1];
};
assert.equal(src(''), 'direct', 'no referrer is direct');
assert.equal(src('https://alwayshave.fun/players-cards-compared/'), 'internal', 'our own pages are internal');
assert.equal(src('https://www.google.com/search?q=mgm+gold+tier+credits'), 'google.com', 'www stripped, query dropped');
assert.equal(src('https://chatgpt.com/'), 'chatgpt.com', 'the one channel with verified real traffic');
assert.equal(src('https://www.perplexity.ai/search/some-private-question'), 'perplexity.ai', 'a path must never reach the beacon');
assert.equal(src('https://old.reddit.com/r/vegas/comments/xyz/'), 'old.reddit.com', 'subdomain kept');
assert.equal(src('android-app://com.google.android.gm/'), 'com.google.android.gm', 'app referrers keep their package host');
assert.equal(src('https://例/'), 'other', 'a host with nothing left after sanitising must not become empty or junk');
assert.equal(run({ protocol: 'file:', pathname: '/tmp/x/index.html' }, human), undefined, 'file:// must not beacon');
assert.equal(run(https, { ...human, webdriver: true }), undefined, 'navigator.webdriver must not beacon');
assert.equal(run(https, { ...human, userAgent: 'HeadlessChrome/157.0.0.0' }), undefined, 'HeadlessChrome must not beacon');
console.log('ok: arrival beacon identical on all ' + urls.length
  + ' pages, slugs match their URLs, source buckets host-only, filters hold');
