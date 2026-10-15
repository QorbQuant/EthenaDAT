// Reads Kraken's public 1-hour OHLC candles for BTC, ETH, SOL, ENA and HYPE against the US dollar
// from 00:00 UTC on October 9, 2026, and keeps the candles that start at 19:00 UTC and 20:00 UTC.
// The 19:00 candle's close is the last trade before 20:00 UTC, 4 pm New York time, the stock close.
// Paste into the developer console on any page of https://api.kraken.com/ . Five read-only GET
// requests, no login. Results in window.__kt.
await (async () => {
  const PAIRS = { BTC: "XBTUSD", ETH: "ETHUSD", SOL: "SOLUSD", ENA: "ENAUSD", HYPE: "HYPEUSD" };
  const SINCE = 1791504000; // 2026-10-09 00:00 UTC
  const KEEP = [1791572400, 1791576000]; // candles starting 19:00 and 20:00 UTC
  const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
  const sha = async (bytes) => hex(await crypto.subtle.digest("SHA-256", bytes));
  const rows = [], log = [];
  for (const [token, pair] of Object.entries(PAIRS)) {
    const url = `https://api.kraken.com/0/public/OHLC?pair=${pair}&interval=60&since=${SINCE}`;
    const r = await fetch(url, { cache: "no-store" });
    const buf = await r.arrayBuffer();
    const body = JSON.parse(new TextDecoder().decode(buf));
    if (body.error && body.error.length) { log.push([token, url, r.status, new Date().toISOString(), buf.byteLength, await sha(buf), "error " + body.error.join(" "), 0]); continue; }
    const key = Object.keys(body.result).find((k) => k !== "last");
    const all = body.result[key];
    for (const c of all.filter((c) => KEEP.includes(c[0])))
      rows.push([token, key, c[0], new Date(c[0] * 1000).toISOString().replace(".000Z", "Z"), ...c.slice(1)]);
    log.push([token, url, r.status, new Date().toISOString(), buf.byteLength, await sha(buf), key, all.length]);
    await new Promise((ok) => setTimeout(ok, 1100));
  }
  const csv = ["token,kraken_pair,start_unix,start_utc,open,high,low,close,vwap,volume,trades", ...rows.map((x) => x.join(","))].join("\n") + "\n";
  const logcsv = ["token,url,status,fetched_at,bytes,sha256,pair_key,candles_returned", ...log.map((x) => x.join(","))].join("\n") + "\n";
  const files = { "kraken_1h_2026-10-09_19utc_20utc.csv": csv, "kraken_fetch_log.csv": logcsv };
  const digests = {};
  for (const [name, text] of Object.entries(files)) digests[name] = await sha(new TextEncoder().encode(text));
  window.__kt = { files, digests };
  return `rows ${rows.length}, log ${log.map((x) => x[0] + ":" + x[2] + ":" + x[6]).join(" ")}, ${Object.entries(digests).map(([k, v]) => k + " " + v.slice(0, 12)).join(" ")}`;
})();
