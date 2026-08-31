// Takedown 2026-08-31: alwayshave.fun retired ahead of the vegas rebrand.
// run_worker_first in wrangler.toml routes EVERY request here — no static
// assets are served. The only thing kept alive is /j, the short link into the
// gate unlocker on gates.alwayshave.fun (do not remove; gates depend on it).
// To restore the old site: git revert this commit.

const PLACEHOLDER = `<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>alwayshave.fun</title>
<style>body{font-family:system-ui;background:#0f172a;color:#e2e8f0;display:grid;place-items:center;min-height:100vh;margin:0}p{font-size:1.2rem}</style>
</head>
<body><p>Something new is coming.</p></body>
</html>`;

export default {
  async fetch(request) {
    const url = new URL(request.url);

    // /j → short link to the Jones gate unlocker (302, repointable). KEEP.
    if (url.pathname === '/j') {
      return Response.redirect('https://gates.alwayshave.fun/j', 302);
    }

    if (url.pathname === '/') {
      return new Response(PLACEHOLDER, {
        headers: { 'Content-Type': 'text/html; charset=utf-8' },
      });
    }

    // Every old URL is intentionally gone — 410 tells crawlers to drop it.
    return new Response(PLACEHOLDER, {
      status: 410,
      headers: { 'Content-Type': 'text/html; charset=utf-8' },
    });
  },
};
