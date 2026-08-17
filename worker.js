const STATES = ['nv', 'ut', 'az', 'ca', 'co', 'nm'];

// Articles served from /articles/{slug}.html
// Worker maps /articles/{slug} → /articles/{slug}.html

export default {
  // scheduled() handler removed 2026-08-14 — the pipeline cron moved to
  // GitHub Actions' native schedule after the Worker's GH_DISPATCH_TOKEN
  // expired and 401'd silently for 6 hours.

  async fetch(request, env) {
    const url = new URL(request.url);
    const parts = url.pathname.replace(/^\//, '').split('/').filter(p => p.length > 0);
    const first = (parts[0] || '').toLowerCase();

    // /api/geo — privacy-first visitor location beacon. Reads Cloudflare's edge
    // geo (request.cf) and logs it to Supabase. No IP stored. NOTE: this lives
    // here in the Worker (not functions/) because the site deploys as a Worker
    // with static assets — Pages Functions are NOT invoked in this model.
    if (first === 'api' && (parts[1] || '').toLowerCase() === 'geo') {
      return handleGeoBeacon(request, env);
    }

    // /j → short link to the Jones gate unlocker (302, repointable). ponytail: one gate = one line.
    if (url.pathname === '/j') {
      return Response.redirect('https://gates.alwayshave.fun/j', 302);
    }

    // Legacy /trail.html?slug=foo-bar-ut → 301 to /{state}/{slug}
    // (slug embeds the state suffix, so we map the suffix back to the state path)
    if (url.pathname === '/trail.html' || url.pathname === '/trail') {
      const slug = url.searchParams.get('slug');
      if (slug) {
        const m = slug.match(/-(nv|ut|az|co|ca|nm|gc-az)$/i);
        // Special: Grand Canyon trails end in "-gc-az" — state is az
        let state = '';
        if (m) {
          state = m[1].toLowerCase();
          if (state === 'gc-az') state = 'az';
        }
        if (state) {
          return Response.redirect(`${url.origin}/${state}/${slug}`, 301);
        }
      }
    }

    // /site/* — dead build-output copies (a rival sitemap.xml + an April homepage
    // clone). Never linked, but live and crawlable, so 301 rather than delete.
    if (first === 'site') {
      const dest = parts[1] === 'sitemap.xml' ? '/sitemap.xml' : '/';
      return Response.redirect(`${url.origin}${dest}`, 301);
    }

    // /dog-friendly  →  serve dog-friendly landing page
    if (parts.length === 1 && first === 'dog-friendly') {
      const dfUrl = new URL('/generated/dog-friendly/index.html', url.origin);
      const dfRes = await env.ASSETS.fetch(dfUrl);
      if (dfRes.status === 200) return dfRes;
    }

    // /states  →  serve states hub page
    if (parts.length === 1 && first === 'states') {
      return env.ASSETS.fetch(new URL('/states.html', url.origin));
    }

    // /fires  →  serve live active-wildfire page
    if (parts.length === 1 && first === 'fires') {
      const fRes = await env.ASSETS.fetch(new URL('/generated/fires/index.html', url.origin));
      if (fRes.status === 200) return fRes;
    }

    // /fires/{incident}  →  permanent per-incident page (kept after the fire
    // leaves the NIFC feed — hard rule 3, a published URL never breaks)
    if (parts.length === 2 && first === 'fires') {
      const iRes = await env.ASSETS.fetch(
        new URL(`/generated/fires/${parts[1]}/index.html`, url.origin));
      if (iRes.status === 200) return iRes;
    }

    // /data  →  open-data catalog. Real files under /data/... are served by the
    // asset layer before the Worker sees them, so only the bare path lands here.
    if (parts.length === 1 && first === 'data') {
      const dRes = await env.ASSETS.fetch(new URL('/generated/data/index.html', url.origin));
      if (dRes.status === 200) return dRes;
    }

    // /great-today  →  serve great trails page
    if (parts.length === 1 && first === 'great-today') {
      return env.ASSETS.fetch(new URL('/great-today.html', url.origin));
    }

    // /about, /privacy, /scoring  →  serve trust/E-E-A-T pages
    if (parts.length === 1 && ['about', 'privacy', 'scoring'].includes(first)) {
      return env.ASSETS.fetch(new URL(`/${first}.html`, url.origin));
    }

    // ponytail: no /articles branch here. Assets run before the Worker, so a
    // bare /articles is 307'd to /articles/ by the assets layer and never
    // reaches this code. The canonical form is /articles/ everywhere.

    // /articles/{slug}  →  serve published article HTML
    if (parts.length === 2 && parts[0] === 'articles') {
      const articleUrl = new URL(`/articles/${parts[1]}.html`, url.origin);
      const articleRes = await env.ASSETS.fetch(articleUrl);
      if (articleRes.status === 200) return articleRes;
    }

    // /{state}/{slug}  →  try pre-rendered static file first, fall back to trail.html
    if (parts.length === 2 && STATES.includes(first)) {
      const [state, slug] = parts;
      const staticUrl = new URL(`/generated/${state}/${slug}.html`, url.origin);
      const staticRes = await env.ASSETS.fetch(staticUrl);
      if (staticRes.status === 200) return staticRes;
      // No pre-rendered page. Only fall back to the JS shell for a slug that is
      // actually a trail — otherwise /{state}/{anything} is an unbounded space of
      // soft-404s, and crawl budget is the thing we have least of.
      const dataRes = await env.ASSETS.fetch(new URL(`/data/conditions/${slug}.json`, url.origin));
      if (dataRes.status === 200) return env.ASSETS.fetch(new URL('/trail.html', url.origin));
      return staticRes;  // already a 404 carrying /404.html (not_found_handling = "404-page")
    }

    // /{state}  →  serve pre-rendered state landing page, fall back to homepage
    if (parts.length === 1 && STATES.includes(first)) {
      const statePageUrl = new URL(`/generated/${first}/index.html`, url.origin);
      const stateRes = await env.ASSETS.fetch(statePageUrl);
      if (stateRes.status === 200) return stateRes;
      return env.ASSETS.fetch(new URL('/', url.origin));
    }

    // Everything else  →  serve static assets normally
    return env.ASSETS.fetch(request);
  }
};

// ── Visitor location beacon ────────────────────────────────────────────────
// Reads the visitor's coarse location from Cloudflare's edge (request.cf) —
// no IP is ever read or stored — and writes one row to the shared Supabase
// `site_visits` table using the SERVICE key. The browser beacon (geo-beacon.js)
// sends only { path }; everything about *where* comes from Cloudflare here.
//
// Env (set as Worker secrets/vars):
//   SUPABASE_URL          https://cuzyicjsyoddbeiosuxn.supabase.co
//   SUPABASE_SERVICE_KEY  sb_secret_...  (secret — server-side only)
async function handleGeoBeacon(request, env) {
  const origin = request.headers.get('Origin') || '';
  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: geoCors(origin) });
  }
  if (request.method !== 'POST') {
    return geoJson({ error: 'Method not allowed' }, 405, geoCors(origin));
  }

  const cf = request.cf || {};
  const lat = geoNum(cf.latitude);
  const lon = geoNum(cf.longitude);
  if (lat === null || lon === null) {
    return geoJson({ ok: true, skipped: 'no-geo' }, 200, geoCors(origin));
  }

  let path = '/';
  try {
    const body = await request.json();
    if (body && typeof body.path === 'string') path = body.path.slice(0, 300);
  } catch { /* empty/invalid body is fine */ }

  const supaUrl = env.SUPABASE_URL;
  const key = env.SUPABASE_SERVICE_KEY;
  if (!supaUrl || !key) {
    console.warn('geo: SUPABASE_URL / SUPABASE_SERVICE_KEY not set — skipping');
    return geoJson({ ok: true, skipped: 'unconfigured' }, 200, geoCors(origin));
  }

  const row = {
    site: 'ahf',
    lat,
    lon,
    city: geoStr(cf.city),
    region: geoStr(cf.region),
    postal: geoStr(cf.postalCode),
    country: geoStr(cf.country),
    path,
  };

  try {
    const res = await fetch(`${supaUrl}/rest/v1/site_visits`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        apikey: key,
        Authorization: `Bearer ${key}`,
        Prefer: 'return=minimal',
      },
      body: JSON.stringify(row),
    });
    if (!res.ok) {
      console.error('geo: supabase insert failed', res.status, await res.text().catch(() => ''));
      return geoJson({ error: 'log failed' }, 502, geoCors(origin));
    }
    return geoJson({ ok: true }, 200, geoCors(origin));
  } catch (err) {
    console.error('geo: fetch error', err);
    return geoJson({ error: 'network' }, 502, geoCors(origin));
  }
}

function geoCors(origin) {
  return {
    'Access-Control-Allow-Origin': origin || 'https://alwayshave.fun',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}
function geoJson(body, status, extraHeaders = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...extraHeaders },
  });
}
function geoNum(v) {
  const n = typeof v === 'string' ? parseFloat(v) : v;
  return Number.isFinite(n) ? n : null;
}
function geoStr(v) {
  return v && typeof v === 'string' ? v.slice(0, 120) : null;
}
