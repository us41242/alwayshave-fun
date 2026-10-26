// ponytail: loads a page in real headless Chrome over raw CDP, stubs navigator.sendBeacon,
// fires two input events + one change, and asserts exactly ONE beacon to the expected /e/ path.
// usage: node scripts/check_beacons.js <file-or-url> </e/event>
const { execFile } = require('child_process'), assert = require('assert');
const [,, target, event] = process.argv;
if (!target || !event) { console.error('usage: node check_beacons.js <file.html|url> </e/event>'); process.exit(2); }
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
  await send('Page.navigate', { url });
  await sleep(1500); // page scripts run at end of body; plenty
  const { result } = await send('Runtime.evaluate', { awaitPromise: true, returnByValue: true, expression: `
    (async () => {
      const calls = [];
      navigator.sendBeacon = u => { calls.push(u); return true; };
      const inp = document.querySelector('input'), sel = document.querySelector('select');
      inp.dispatchEvent(new Event('input', { bubbles: true }));
      inp.dispatchEvent(new Event('input', { bubbles: true }));
      if (sel) sel.dispatchEvent(new Event('change', { bubbles: true }));
      await new Promise(r => setTimeout(r, 100));
      return calls;
    })()` });
  chrome.kill();
  assert.deepStrictEqual(result.value, [event], `expected one beacon [${event}], got ${JSON.stringify(result.value)}`);
  console.log('ok: exactly one beacon', event);
  process.exit(0);
})().catch(e => { chrome.kill(); console.error(e); process.exit(1); });
