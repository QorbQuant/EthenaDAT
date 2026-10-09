// Reads Kraken's public 4-hour OHLC candles for ENA/USD and keeps the two candles that end at
// 20:00 UTC (4 pm New York time in daylight time) and at 00:00 UTC, for every day from June 25 to
// October 8, 2026. Kraken returns its most recent 720 candles, which reach back about 120 days.
// Paste into the developer console on any page of https://api.kraken.com/ . One read-only GET
// request, no login. Results in window.__kr.
await (async () => {
  const URL = "https://api.kraken.com/0/public/OHLC?pair=ENAUSD&interval=240&since=1782345600";
  const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
  const sha = async (bytes) => hex(await crypto.subtle.digest("SHA-256", bytes));
  const r = await fetch(URL, { cache: "no-store" });
  const buf = await r.arrayBuffer();
  const body = JSON.parse(new TextDecoder().decode(buf));
  const key = Object.keys(body.result).find((k) => k !== "last");
  const all = body.result[key];
  const first = Date.UTC(2026, 5, 25) / 1000, last = Date.UTC(2026, 9, 8, 20) / 1000;
  const keep = all.filter(([t]) => t >= first && t <= last && [16, 20].includes(new Date(t * 1000).getUTCHours()));
  const csv = ["start_unix,start_utc,open,high,low,close,vwap,volume_ena,trades",
    ...keep.map((c) => [c[0], new Date(c[0] * 1000).toISOString().replace(".000Z", "Z"), ...c.slice(1)].join(","))].join("\n") + "\n";
  const log = ["url,status,fetched_at,bytes,sha256,candles_returned,first_candle_utc,last_candle_utc",
    [URL, r.status, new Date().toISOString(), buf.byteLength, await sha(buf), all.length,
     new Date(all[0][0] * 1000).toISOString(), new Date(all[all.length - 1][0] * 1000).toISOString()].join(",")].join("\n") + "\n";
  const files = { "kraken_enausd_4h_20utc_00utc.csv": csv, "kraken_fetch_log.csv": log };
  const digests = {};
  for (const [name, text] of Object.entries(files)) digests[name] = await sha(new TextEncoder().encode(text));
  window.__kr = { files, digests };
  return `status ${r.status}, pair ${key}, candles ${all.length}, kept ${keep.length}, ${Object.entries(digests).map(([k, v]) => k + " " + v.slice(0, 12)).join(" ")}`;
})();
