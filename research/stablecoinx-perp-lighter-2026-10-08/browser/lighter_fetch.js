// Reads Lighter's public market data for the STABLECOINX perpetual (market 229)
// and builds the CSV inputs for stablecoinx_perp_review.py.
//
// Run it in a browser tab open on https://mainnet.zklighter.elliot.ai/ (any API
// page, for example /api/v1/orderBookDetails?market_id=229), in the developer
// console. Every request is a read-only GET to Lighter's public REST API, with no
// login. The script keeps the raw text of each response, records its SHA-256, and
// writes window.__lighter = { log, files, sha256, checks }.
//
// Cutoff. Hourly candles that start before 2026-10-09 00:00 UTC, and fundings
// settled at or before that time. The market's first hourly candle is
// 2026-08-26 18:00 UTC, so requests start at 2026-08-26 00:00 UTC.
await (async () => {
  const API = "/api/v1/";
  const MARKET = 229;
  const SYMBOL = "STABLECOINX";
  const FIRST = 1787702400; // 2026-08-26T00:00:00Z
  const CUT = 1791504000; // 2026-10-09T00:00:00Z
  const WIN = 15 * 86400; // 360 hourly rows a request, under the 500 and 750 caps
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const sha = async (s) =>
    [...new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s)))]
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  const log = [];
  const raw = {};
  async function get(path) {
    const at = new Date().toISOString();
    const r = await fetch(API + path, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    const text = await r.text();
    log.push({ path, status: r.status, at, chars: text.length, sha256: await sha(text) });
    raw[path] = text;
    await sleep(400);
    if (!r.ok) throw Error(path + " HTTP " + r.status);
    const j = JSON.parse(text);
    if (j.code !== 200) throw Error(path + " code " + j.code);
    return j;
  }
  const windows = [];
  for (let s = FIRST; s < CUT + 3600; s += WIN) windows.push([s, Math.min(s + WIN, CUT + 3600)]);
  const q = (s, e, n) =>
    `market_id=${MARKET}&resolution=1h&start_timestamp=${s}&end_timestamp=${e}&count_back=${n}`;

  // Merges rows from overlapping windows. A key seen twice must carry identical rows.
  const conflicts = [];
  const merge = (rows, key) => {
    const m = new Map();
    for (const r of rows) {
      const k = r[key];
      const s = JSON.stringify(r);
      if (m.has(k) && JSON.stringify(m.get(k)) !== s) conflicts.push(key + "=" + k);
      m.set(k, r);
    }
    return [...m.values()].sort((a, b) => a[key] - b[key]);
  };
  // Zero values are omitted by the API, so an absent field is written as 0 for
  // volumes and left empty for anything else.
  const cell = (v, zero) => (v === undefined || v === null ? (zero ? "0" : "") : String(v));
  const csv = (header, rows, fields, zeros = []) =>
    [header, ...rows.map((r) => fields.map((f) => cell(r[f], zeros.includes(f))).join(","))].join("\n") + "\n";

  let candles = [], mark = [], funding = [];
  for (const [s, e] of windows) {
    candles.push(...(await get("candles?" + q(s, e, 500))).c);
    mark.push(...(await get("markPriceCandles?" + q(s, e, 500))).c);
    funding.push(...(await get("fundings?" + q(s, e, 500))).fundings);
  }
  candles = merge(candles, "t").filter((r) => r.t >= FIRST * 1000 && r.t < CUT * 1000);
  mark = merge(mark, "t").filter((r) => r.t >= FIRST * 1000 && r.t < CUT * 1000);
  funding = merge(funding, "timestamp").filter((r) => r.timestamp > FIRST && r.timestamp <= CUT);

  const d1 = `market_id=${MARKET}&resolution=1d&start_timestamp=${FIRST}&end_timestamp=${CUT}&count_back=500`;
  const candlesDay = (await get("candles?" + d1)).c.filter((r) => r.t < CUT * 1000);
  const markDay = (await get("markPriceCandles?" + d1)).c.filter((r) => r.t < CUT * 1000);

  const metric = async (kind) =>
    (await get(`exchangeMetrics?period=all&kind=${kind}&filter=byMarket&value=${SYMBOL}`)).metrics;
  const oi = await metric("open_interest");
  const vol = await metric("volume");
  const byDay = new Map();
  for (const r of oi) byDay.set(r.timestamp, { timestamp: r.timestamp, open_interest: r.data });
  for (const r of vol) byDay.set(r.timestamp, { ...(byDay.get(r.timestamp) || { timestamp: r.timestamp }), volume: r.data });
  const metrics = [...byDay.values()]
    .filter((r) => r.timestamp >= FIRST - 86400 && r.timestamp < CUT)
    .sort((a, b) => a.timestamp - b.timestamp);

  const details = await get(`orderBookDetails?market_id=${MARKET}`);
  const oracle = await get(`priceOracleInfo?symbol=${SYMBOL}`);

  const files = {
    "lighter_candles_1h.csv": csv("t_ms,o,h,l,c,v,V", candles, ["t", "o", "h", "l", "c", "v", "V"], ["v", "V"]),
    "lighter_mark_1h.csv": csv("t_ms,o,h,l,c,sc", mark, ["t", "o", "h", "l", "c", "sc"], ["sc"]),
    "lighter_funding_1h.csv": csv("timestamp,value,rate,direction", funding, ["timestamp", "value", "rate", "direction"]),
    "lighter_candles_1d.csv": csv("t_ms,o,h,l,c,v,V", candlesDay, ["t", "o", "h", "l", "c", "v", "V"], ["v", "V"]),
    "lighter_mark_1d.csv": csv("t_ms,o,h,l,c,sc", markDay, ["t", "o", "h", "l", "c", "sc"], ["sc"]),
    "lighter_metrics_1d.csv": csv("timestamp,open_interest,volume", metrics, ["timestamp", "open_interest", "volume"], ["open_interest", "volume"]),
    "lighter_orderbookdetails.json": raw[`orderBookDetails?market_id=${MARKET}`] + "\n",
    "lighter_priceoracleinfo.json": raw[`priceOracleInfo?symbol=${SYMBOL}`] + "\n",
  };
  // The request log keeps each endpoint and its parameters in separate fields,
  // as k:v pairs joined by semicolons, so the full address can be rebuilt as
  // https://mainnet.zklighter.elliot.ai/api/v1/<endpoint> with those parameters.
  files["lighter_fetch_log.csv"] =
    "endpoint,params,status,fetched_at,chars,sha256\n" +
    log
      .map((r) => {
        const [endpoint, query = ""] = r.path.split("?");
        const params = [...new URLSearchParams(query)].map(([k, v]) => k + ":" + v).join(";");
        return [endpoint, params, r.status, r.at, r.chars, r.sha256].join(",");
      })
      .join("\n") + "\n";

  const sha256 = {};
  for (const [k, v] of Object.entries(files)) sha256[k] = await sha(v);

  // Checks the script can make on its own. The Python script repeats them.
  const hours = (rows) => rows.map((r) => r.t / 1000);
  const gaps = (ts, step) => ts.slice(1).filter((t, i) => t - ts[i] !== step).length;
  const m = details.order_book_details.find((v) => v.market_id === MARKET);
  const checks = {
    market_symbol: m && m.symbol,
    market_type: m && m.market_type,
    market_status: m && m.status,
    candles_1h: candles.length,
    candles_1h_first: candles.length && new Date(candles[0].t).toISOString(),
    candles_1h_last: candles.length && new Date(candles.at(-1).t).toISOString(),
    candles_1h_breaks: gaps(hours(candles), 3600),
    mark_1h: mark.length,
    mark_1h_first: mark.length && new Date(mark[0].t).toISOString(),
    mark_1h_breaks: gaps(hours(mark), 3600),
    funding_1h: funding.length,
    funding_first: funding.length && new Date(funding[0].timestamp * 1000).toISOString(),
    funding_last: funding.length && new Date(funding.at(-1).timestamp * 1000).toISOString(),
    funding_breaks: gaps(funding.map((r) => r.timestamp), 3600),
    funding_directions: [...new Set(funding.map((r) => r.direction))].join("|"),
    days: candlesDay.length,
    metric_days: metrics.length,
    duplicate_conflicts: conflicts.length,
    oracle_computed_at: new Date(oracle.computed_at_ms).toISOString(),
    requests: log.length,
    failed_requests: log.filter((r) => r.status !== 200).length,
  };
  window.__lighter = { log, files, sha256, checks, raw };
  return checks;
})();
