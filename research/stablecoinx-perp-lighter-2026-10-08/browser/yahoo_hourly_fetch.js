// Reads Yahoo Finance's hourly chart data for USDE including pre-market and
// after-hours trading, 2026-08-26 to 2026-10-08, to compare the perp's mark price
// with USDE's own trades outside the regular session.
// Run it in a browser tab open on https://query1.finance.yahoo.com/, in the
// developer console. One read-only GET, no login.
// Writes window.__yahooHourly = { url, fetched_at, status, chars, sha256, csv, csv_sha256 }.
// Each row is one bar. t is the bar's start in Unix seconds, new_york its start in
// New York time, then open, high, low, close and volume as Yahoo gives them.
// Bars with no trade come back with empty prices and are kept as empty fields.
await (async () => {
  const url =
    "/v8/finance/chart/USDE?period1=1787702400&period2=1791504000&interval=1h&includePrePost=true";
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
  const local = (t) =>
    new Intl.DateTimeFormat("sv-SE", {
      timeZone: tz,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(new Date(t * 1000));
  const rows = j.timestamp.map((t, i) =>
    [t, local(t), q.open[i], q.high[i], q.low[i], q.close[i], q.volume[i]]
      .map((v) => (v === null || v === undefined ? "" : String(v)))
      .join(","),
  );
  const csv = "t,new_york,open,high,low,close,volume\n" + rows.join("\n") + "\n";
  window.__yahooHourly = {
    url: "https://query1.finance.yahoo.com" + url,
    fetched_at,
    status: r.status,
    chars: text.length,
    sha256: await sha(text),
    csv,
    csv_sha256: await sha(csv),
    periods: JSON.stringify(j.meta.currentTradingPeriod),
  };
  return `status ${r.status}, ${rows.length} bars, first ${rows[0]}, last ${rows.at(-1)}, csv ${csv.length} chars`;
})();
