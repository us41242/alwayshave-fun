const STATES = ['nv', 'ut', 'az', 'ca', 'co', 'nm'];

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const parts = url.pathname.replace(/^\//, '').split('/').filter(p => p.length > 0);
    const first = (parts[0] || '').toLowerCase();

    // /{state}/{slug}  →  try pre-rendered static file first, fall back to trail.html
    if (parts.length === 2 && STATES.includes(first)) {
      const [state, slug] = parts;
      const staticUrl = new URL(`/generated/${state}/${slug}.html`, url.origin);
      const staticRes = await env.ASSETS.fetch(staticUrl);
      if (staticRes.status === 200) return staticRes;
      return env.ASSETS.fetch(new URL('/trail.html', url.origin));
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
