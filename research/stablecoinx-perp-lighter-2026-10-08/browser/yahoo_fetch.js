// Reads Yahoo Finance's chart data for USDE, daily sessions from 2026-08-26 to
// 2026-10-08, as a second source for the official opens and closes.
// Run it in a browser tab open on https://query1.finance.yahoo.com/ (for example
// the address below), in the developer console. One read-only GET, no login.
// Writes window.__yahoo = { url, fetched_at, chars, sha256, csv, csv_sha256 }.
await (async () => {
  const url =
    "/v8/finance/chart/USDE?period1=1787702400&period2=1791504000&interval=1d&includePrePost=false";
  const fetched_at = new Date().toISOString();
  const r = await fetch(url, { cache: "no-store" });
  const text = await r.text();
  const sha = async (s) =>
    [...new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s)))]
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  const j = JSON.parse(text).chart.result[0];
  const tz = j.meta.exchangeTimezoneName;
  const q = j.indicators.quote[0];
  const day = (t) =>
    new Intl.DateTimeFormat("en-CA", { timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit" }).format(
      new Date(t * 1000),
    );
  const rows = j.timestamp.map((t, i) =>
    [day(t), q.open[i], q.high[i], q.low[i], q.close[i], q.volume[i]].map((v) => (v === null ? "" : String(v))).join(","),
  );
  const csv = "date,open,high,low,close,volume\n" + rows.join("\n") + "\n";
  window.__yahoo = {
    url: "https://query1.finance.yahoo.com" + url,
    fetched_at,
    status: r.status,
    chars: text.length,
    sha256: await sha(text),
    exchange: j.meta.exchangeName + " " + j.meta.fullExchangeName,
    timezone: tz,
    csv,
    csv_sha256: await sha(csv),
  };
  return { status: r.status, rows: rows.length, first: rows[0], last: rows.at(-1), exchange: window.__yahoo.exchange, csv_sha256: window.__yahoo.csv_sha256 };
})();
