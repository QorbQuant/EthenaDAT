// Reads Yahoo Finance's daily chart data for six stocks for the sessions of October 8 and 9, 2026,
// and keeps each session's close. Paste into the developer console on any page of
// https://query1.finance.yahoo.com/ . Six read-only GET requests, no login. Results in window.__yh.
await (async () => {
  const TICKERS = ["USDE", "MSTR", "ASST", "BMNR", "FWDI", "HYPD"];
  const P1 = 1791417600, P2 = 1791676800; // 2026-10-08 00:00 UTC to 2026-10-11 00:00 UTC
  const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
  const sha = async (bytes) => hex(await crypto.subtle.digest("SHA-256", bytes));
  const rows = [], log = [];
  for (const t of TICKERS) {
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${t}?period1=${P1}&period2=${P2}&interval=1d`;
    const r = await fetch(url, { cache: "no-store" });
    const buf = await r.arrayBuffer();
    const res = JSON.parse(new TextDecoder().decode(buf)).chart.result[0];
    const q = res.indicators.quote[0];
    res.timestamp.forEach((ts, i) => {
      const day = new Date((ts + res.meta.gmtoffset) * 1000).toISOString().slice(0, 10);
      rows.push([t, day, ts, q.open[i], q.high[i], q.low[i], q.close[i], q.volume[i]]);
    });
    log.push([t, url, r.status, new Date().toISOString(), buf.byteLength, await sha(buf), res.meta.exchangeName, res.meta.currency, res.timestamp.length]);
    await new Promise((ok) => setTimeout(ok, 400));
  }
  const csv = ["ticker,session_date,session_start_unix,open,high,low,close,volume", ...rows.map((x) => x.join(","))].join("\n") + "\n";
  const logcsv = ["ticker,url,status,fetched_at,bytes,sha256,exchange,currency,sessions", ...log.map((x) => x.join(","))].join("\n") + "\n";
  const files = { "yahoo_daily_2026-10-08_09.csv": csv, "yahoo_fetch_log.csv": logcsv };
  const digests = {};
  for (const [name, text] of Object.entries(files)) digests[name] = await sha(new TextEncoder().encode(text));
  window.__yh = { files, digests };
  return `rows ${rows.length}, statuses ${log.map((x) => x[2]).join("/")}, ${Object.entries(digests).map(([k, v]) => k + " " + v.slice(0, 12)).join(" ")}`;
})();
