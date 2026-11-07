// ponytail: loads a page in real headless Chrome over raw CDP, stubs navigator.sendBeacon,
// drives the page, and asserts exactly the expected /e/ beacons — the arrival beacon first,
// then the interaction ones.
// The stub is installed BEFORE navigation (the arrival beacon fires at parse time, so a stub
// installed after load would miss it and let a real hit reach live analytics), the UA is
// overridden to a real browser (the arrival beacon deliberately skips HeadlessChrome), and
// /e/* is blocked at the network layer so even a broken stub cannot pollute the data.
// usage: node scripts/check_beacons.js <file-or-url> </e/event>   (fires 2 input + 1 change, expects one beacon)
//        node scripts/check_beacons.js <file-or-url> vp           (plays the VP trainer: deal/draw 5 hands,
//                                                                  jump to hand 25; expects vp-deal, vp-5, vp-25)
const { execFile } = require('child_process'), assert = require('assert');
const [,, target, event] = process.argv;
// the arrival beacon skips HeadlessChrome on purpose; pose as the phone the site is built for
const REAL_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1';
if (!target || !event) { console.error('usage: node check_beacons.js <file.html|url> </e/event>|vp'); process.exit(2); }
const url = /^https?:/.test(target) ? target : 'file://' + require('path').resolve(target);
const port = 9333;
const chrome = execFile('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  ['--headless=new', `--remote-debugging-port=${port}`, '--no-first-run', '--user-data-dir=/tmp/chk-beacons', 'about:blank']);
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  let targets;
  for (let i = 0; i < 20; i++) { // wait for chrome to listen
    try { targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); break; } catch { await sleep(250); }
  }
  const ws = new WebSocket(targets.find(t => t.type === 'page').webSocketDebuggerUrl);
  let id = 0; const pending = {};
  const send = (method, params = {}) => new Promise(res => { pending[++id] = res; ws.send(JSON.stringify({ id, method, params })); });
  ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id && pending[d.id]) pending[d.id](d.result); };
  await new Promise(r => ws.onopen = r);
  await send('Page.enable');
  await send('Network.enable');
  await send('Network.setBlockedURLs', { urls: ['*/e/*'] }); // belt: no beacon can ever leave this browser
  await send('Network.setUserAgentOverride', { userAgent: REAL_UA });
  await send('Page.addScriptToEvaluateOnNewDocument', { source:
    'window.__calls = []; navigator.sendBeacon = u => { window.__calls.push(u); return true; };' });
  await send('Page.navigate', { url });
  await sleep(1500); // page scripts run at end of body; plenty
  const vp = event === 'vp';
  const scenario = vp ? `
      const wait = async f => { for (let i = 0; i < 100 && !f(); i++) await new Promise(r => setTimeout(r, 100)); };
      const hand = async () => {
        document.getElementById('deal').click();
        await wait(() => !document.getElementById('draw').disabled);
        document.getElementById('draw').click();
      };
      for (let i = 0; i < 5; i++) await hand(); // fires vp-deal on hand 1, vp-5 on hand 5
      drawn = 24; await hand();                 // jump to hand 25 instead of playing 19 more
  ` : `
      const inp = document.querySelector('input'), sel = document.querySelector('select');
      inp.dispatchEvent(new Event('input', { bubbles: true }));
      inp.dispatchEvent(new Event('input', { bubbles: true }));
      if (sel) sel.dispatchEvent(new Event('change', { bubbles: true }));
  `;
  const { result } = await send('Runtime.evaluate', { awaitPromise: true, returnByValue: true, expression: `
    (async () => {
      const calls = window.__calls;
      ${scenario}
      await new Promise(r => setTimeout(r, 100));
      const leak = document.getElementById('leak');
      return { calls, leak: leak ? leak.textContent.trim() : null };
    })()` });
  chrome.kill();
  // the arrival beacon is https-only by design, so a file:// run must NOT produce one;
  // run this against the live URL to assert it end to end.
  // headless navigates straight to the URL, so there is no referrer: the source bucket is 'direct'.
  const arrival = url.startsWith('https:')
    ? ['/e/v-' + (new URL(url).pathname.replace(/\//g, '') || 'home') + '~direct'] : [];
  const expected = [...arrival, ...(vp ? ['/e/vp-deal', '/e/vp-5', '/e/vp-25'] : [event])];
  assert.deepStrictEqual(result.value.calls, expected, `expected ${JSON.stringify(expected)}, got ${JSON.stringify(result.value.calls)}`);
  // the leak report is a pure silent failure: if leakLine() throws or the node is missing,
  // the trainer still plays and just never teaches. Six holds of nothing must log a leak.
  if (vp) assert.match(result.value.leak || '', /Your biggest leak:.+coins\./,
    'played 6 imperfect hands and no leak was reported: ' + JSON.stringify(result.value.leak));
  console.log('ok: beacons', expected.join(' '), vp ? '| leak: ' + result.value.leak : '');
  process.exit(0);
})().catch(e => { chrome.kill(); console.error(e); process.exit(1); });
