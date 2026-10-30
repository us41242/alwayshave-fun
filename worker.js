// alwayshave.fun Worker — v1 vegas site (2026-09-02).
// run_worker_first in wrangler.toml routes EVERY request here. Only the paths
// in ROUTES are served from static assets; everything else is 410 because
// the old trails site was purged (SEO reset, see AUTONOMY.md).
// /j is the short link into the gate unlocker on gates.alwayshave.fun.
// NEVER remove or change it — gates depend on it.

// ponytail: allowlist map instead of a router; grow it as pages ship.
const ROUTES = {
  '/': '/index.html',
  '/final-hand/': '/games/final-hand/index.html',
  '/blackjack-tournament-strategy/': '/guides/blackjack-tournament-strategy/index.html',
  '/casino-comps/': '/guides/casino-comps/index.html',
  '/players-cards-compared/': '/guides/players-cards-compared/index.html',
  '/tournament-bet-sizer/': '/tools/tournament-bet-sizer/index.html',
  '/video-poker-trainer/': '/games/video-poker/index.html',
  '/tournament-ev-calculator/': '/tools/tournament-ev-calculator/index.html',
  '/caesars-olympus/': '/guides/caesars-olympus/index.html',
  '/caesars-diamond/': '/guides/caesars-diamond/index.html',
  '/mgm-gold-platinum/': '/guides/mgm-gold-platinum/index.html',
  '/station-boarding-pass-tiers/': '/guides/station-boarding-pass-tiers/index.html',
  '/venetian-rewards-tiers/': '/guides/venetian-rewards-tiers/index.html',
  '/resorts-world-genting-rewards-tiers/': '/guides/resorts-world-genting-rewards-tiers/index.html',
  '/site.css': '/site.css',
  '/robots.txt': '/robots.txt',
  '/sitemap.xml': '/sitemap.xml',
  '/sitemap-pages.xml': '/sitemap.xml', // retired alias (2026-10-26): dropped from robots.txt + GSC, kept so the URL never 410s
  '/favicon.ico': '/favicon.ico',
  '/favicon.svg': '/favicon.svg',
  // Root assets real clients ask for unprompted. llms.txt is the AI-crawler
  // index; the apple-touch-icon family is handled by a pattern below, because
  // iOS asks for sizes, not just the two bare names.
  '/llms.txt': '/llms.txt',
  '/3d00877f1b744d7898b2862b4c5e94fd.txt': '/3d00877f1b744d7898b2862b4c5e94fd.txt', // IndexNow key
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const p = url.pathname;

    // /j → short link to the Jones gate unlocker (302, repointable). KEEP.
    if (p === '/j') {
      return Response.redirect('https://gates.alwayshave.fun/j', 302);
    }

    // /e/<event> — anonymous play counter beacon; the request itself is the count.
    if (p.startsWith('/e/')) return new Response(null, { status: 204 });

    // iOS asks for the Add-to-Home-Screen icon by size and gives up quietly:
    // apple-touch-icon-240x240[-precomposed].png, -180x180-, -152x152-, ...
    // Our one confirmed human asked for 240x240 and 240x240-precomposed on
    // 2026-10-29 and got 410 for both, two hours after the bare paths were
    // fixed. One pattern serves the single 180x180 PNG for every variant,
    // which is what the spec allows and what iOS downscales anyway.
    // ponytail: a pattern, not 10 more ROUTES lines.
    if (/^\/apple-touch-icon(-\d+x\d+)?(-precomposed)?\.png$/.test(p)) {
      url.pathname = '/apple-touch-icon.png';
      return env.ASSETS.fetch(new Request(url.toString(), request));
    }

    // Directory URLs are canonical with a trailing slash.
    if ((p + '/') in ROUTES) {
      url.pathname = p + '/';
      return Response.redirect(url.toString(), 301);
    }

    if (p in ROUTES) {
      url.pathname = ROUTES[p];
      return env.ASSETS.fetch(new Request(url.toString(), request));
    }

    // Every other URL is gone (old trails site) — 410 tells crawlers to drop it.
    url.pathname = '/404.html';
    const nf = await env.ASSETS.fetch(new Request(url.toString(), request));
    return new Response(nf.body, {
      status: 410,
      headers: { 'Content-Type': 'text/html; charset=utf-8' },
    });
  },
};
