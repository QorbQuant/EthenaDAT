// Reads Kraken's public daily OHLC candles for ENA/USD from June 25, 2026, the day of StablecoinX's
// merger, and writes them as kraken_enausd_daily.csv. Each candle covers one UTC day, and its low is
// the lowest trade that day. The last candle is still open until 00:00 UTC the next day.
// Paste into the developer console on any page of https://api.kraken.com/ . One read-only GET
// request, no login. Results in window.__krd.
await (async () => {
  const URL = "https://api.kraken.com/0/public/OHLC?pair=ENAUSD&interval=1440&since=1782345600";
  const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
  const sha = async (bytes) => hex(await crypto.subtle.digest("SHA-256", bytes));
  const r = await fetch(URL, { cache: "no-store" });
  const buf = await r.arrayBuffer();
  const body = JSON.parse(new TextDecoder().decode(buf));
  const key = Object.keys(body.result).find((k) => k !== "last");
  const all = body.result[key].filter(([t]) => t >= 1782345600);
  const csv = ["date_utc,time_unix,open,high,low,close,vwap,volume,count",
    ...all.map((c) => [new Date(c[0] * 1000).toISOString().slice(0, 10), ...c].join(","))].join("\n") + "\n";
  window.__krd = { csv, fetched_at: new Date().toISOString(), status: r.status, bytes: buf.byteLength,
    response_sha256: await sha(buf), csv_sha256: await sha(new TextEncoder().encode(csv)) };
  return `status ${r.status}, pair ${key}, candles ${all.length}, csv ${window.__krd.csv_sha256.slice(0, 12)}`;
})();
