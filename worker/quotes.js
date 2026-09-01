// Live quote proxy for ethenadash.com — fetches Yahoo Finance server-side
// (no CORS in browsers) with a 60s edge cache. Falls back to Stooq daily data.

const SYMBOLS = ["USDE", "USDEW"];

async function yahooQuote(sym) {
  const r = await fetch(
    `https://query1.finance.yahoo.com/v8/finance/chart/${sym}?interval=1d&range=5d`,
    { headers: { "User-Agent": "Mozilla/5.0 (ethenadash quote proxy)" } }
  );
  if (!r.ok) throw new Error(`yahoo ${sym}: ${r.status}`);
  const j = await r.json();
  const result = j.chart?.result?.[0];
  const meta = result?.meta;
  if (!meta || meta.regularMarketPrice == null) throw new Error(`yahoo ${sym}: no meta`);
  // previous close = last fully closed session, i.e. second-to-last daily bar
  const closes = (result.indicators?.quote?.[0]?.close || []).filter(v => v != null);
  const prev = closes.length > 1 ? closes[closes.length - 2] : meta.chartPreviousClose ?? null;
  return {
    price: meta.regularMarketPrice,
    prev_close: prev,
    state: meta.marketState || null,
    t: meta.regularMarketTime ? new Date(meta.regularMarketTime * 1000).toISOString() : null,
    src: "yahoo",
  };
}

async function stooqQuote(sym) {
  const r = await fetch(`https://stooq.com/q/l/?s=${sym.toLowerCase()}.us&f=sd2t2ohlcv&h&e=csv`);
  if (!r.ok) throw new Error(`stooq ${sym}: ${r.status}`);
  const rows = (await r.text()).trim().split("\n");
  const c = rows[1]?.split(",");
  const price = parseFloat(c?.[6]);
  if (!isFinite(price)) throw new Error(`stooq ${sym}: no price`);
  return { price, prev_close: null, state: "STOOQ_DELAYED", t: `${c[1]}T${c[2]}Z`, src: "stooq" };
}

export default {
  async fetch(request, env, ctx) {
    const cache = caches.default;
    const cacheKey = new Request(new URL(request.url).origin + "/quotes");
    let res = await cache.match(cacheKey);
    if (!res) {
      const out = {};
      await Promise.all(SYMBOLS.map(async sym => {
        try {
          out[sym] = await yahooQuote(sym);
        } catch (e) {
          try { out[sym] = await stooqQuote(sym); }
          catch (e2) { out[sym] = { error: String(e2) }; }
        }
      }));
      out.fetched_at = new Date().toISOString();
      res = new Response(JSON.stringify(out), {
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
          "Cache-Control": "public, max-age=60",
        },
      });
      ctx.waitUntil(cache.put(cacheKey, res.clone()));
    }
    return res;
  },
};
