// Reads CoinGecko's prices for BTC, ETH, SOL, ENA and HYPE through DefiLlama's public price API at
// 20:00 UTC on October 9, 2026, 4 pm New York time. DefiLlama returns the nearest price within the
// search width of 600 seconds. Paste into the developer console on any page of https://coins.llama.fi/ .
// One read-only GET request, no login. Results in window.__dl.
await (async () => {
  const TS = 1791576000; // 2026-10-09 20:00 UTC
  const COINS = { BTC: "coingecko:bitcoin", ETH: "coingecko:ethereum", SOL: "coingecko:solana", ENA: "coingecko:ethena", HYPE: "coingecko:hyperliquid" };
  const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
  const sha = async (bytes) => hex(await crypto.subtle.digest("SHA-256", bytes));
  const url = `https://coins.llama.fi/prices/historical/${TS}/${Object.values(COINS).join(",")}?searchWidth=600`;
  const r = await fetch(url, { cache: "no-store" });
  const buf = await r.arrayBuffer();
  const coins = JSON.parse(new TextDecoder().decode(buf)).coins;
  const rows = Object.entries(COINS).map(([token, id]) => {
    const c = coins[id] || {};
    return [token, id, TS, new Date(TS * 1000).toISOString().replace(".000Z", "Z"), c.timestamp, c.timestamp - TS, c.price, c.confidence];
  });
  const csv = ["token,coin_id,target_unix,target_utc,price_unix,offset_s,price_usd,confidence", ...rows.map((x) => x.join(","))].join("\n") + "\n";
  const logcsv = ["url,status,fetched_at,bytes,sha256,coins_returned\n" + ['"' + url + '"', r.status, new Date().toISOString(), buf.byteLength, await sha(buf), Object.keys(coins).length].join(",")].join("\n") + "\n";
  const files = { "coingecko_via_defillama_2026-10-09_20utc.csv": csv, "defillama_fetch_log.csv": logcsv };
  const digests = {};
  for (const [name, text] of Object.entries(files)) digests[name] = await sha(new TextEncoder().encode(text));
  window.__dl = { files, digests };
  return `status ${r.status}, coins ${Object.keys(coins).length}, ${rows.map((x) => x[0] + " " + x[6] + " (" + x[5] + "s)").join(", ")}`;
})();
