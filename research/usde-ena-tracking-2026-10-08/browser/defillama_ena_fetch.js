// Reads CoinGecko's ENA price through DefiLlama's public price API at 20:00 UTC (4 pm New York time,
// USDE's close) on June 25 and on every USDE session from June 26 to October 8, 2026, and at 13:30 UTC
// (9:30 am, USDE's open) on every session. DefiLlama returns the nearest price within the search width.
// Paste into the developer console on any page of https://coins.llama.fi/ . Two read-only GET requests,
// no login. Results in window.__ll.
await (async () => {
  const TS20 = [1782417600,1782504000,1782763200,1782849600,1782936000,1783022400,1783368000,1783454400,1783540800,1783627200,1783713600,1783972800,1784059200,1784145600,1784232000,1784318400,1784577600,1784664000,1784750400,1784836800,1784923200,1785182400,1785268800,1785355200,1785441600,1785528000,1785787200,1785873600,1785960000,1786046400,1786132800,1786392000,1786478400,1786564800,1786651200,1786737600,1786996800,1787083200,1787169600,1787256000,1787342400,1787601600,1787688000,1787774400,1787860800,1787947200,1788206400,1788292800,1788379200,1788465600,1788552000,1788897600,1788984000,1789070400,1789156800,1789416000,1789502400,1789588800,1789675200,1789761600,1790020800,1790107200,1790193600,1790280000,1790366400,1790625600,1790712000,1790798400,1790884800,1790971200,1791230400,1791316800,1791403200,1791489600];
  const TS1330 = [1782480600,1782739800,1782826200,1782912600,1782999000,1783344600,1783431000,1783517400,1783603800,1783690200,1783949400,1784035800,1784122200,1784208600,1784295000,1784554200,1784640600,1784727000,1784813400,1784899800,1785159000,1785245400,1785331800,1785418200,1785504600,1785763800,1785850200,1785936600,1786023000,1786109400,1786368600,1786455000,1786541400,1786627800,1786714200,1786973400,1787059800,1787146200,1787232600,1787319000,1787578200,1787664600,1787751000,1787837400,1787923800,1788183000,1788269400,1788355800,1788442200,1788528600,1788874200,1788960600,1789047000,1789133400,1789392600,1789479000,1789565400,1789651800,1789738200,1789997400,1790083800,1790170200,1790256600,1790343000,1790602200,1790688600,1790775000,1790861400,1790947800,1791207000,1791293400,1791379800,1791466200];
  const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
  const sha = async (bytes) => hex(await crypto.subtle.digest("SHA-256", bytes));
  const rows = [];
  const log = [];
  for (const [label, list] of [["close_2000utc", TS20], ["open_1330utc", TS1330]]) {
    const coins = encodeURIComponent(JSON.stringify({ "coingecko:ethena": list }));
    const url = `https://coins.llama.fi/batchHistorical?coins=${coins}&searchWidth=600`;
    const r = await fetch(url, { cache: "no-store" });
    const buf = await r.arrayBuffer();
    const prices = JSON.parse(new TextDecoder().decode(buf)).coins["coingecko:ethena"].prices;
    for (const target of list) {
      const p = prices.reduce((best, x) => (!best || Math.abs(x.timestamp - target) < Math.abs(best.timestamp - target) ? x : best), null);
      rows.push([label, target, new Date(target * 1000).toISOString().replace(".000Z", "Z"), p.timestamp, p.timestamp - target, p.price, p.confidence]);
    }
    log.push([label, r.status, new Date().toISOString(), buf.byteLength, await sha(buf), prices.length, list.length]);
    await new Promise((res) => setTimeout(res, 500));
  }
  const csv = ["series,target_unix,target_utc,price_unix,offset_s,price_usd,confidence", ...rows.map((x) => x.join(","))].join("\n") + "\n";
  const logcsv = ["series,status,fetched_at,bytes,sha256,prices_returned,timestamps_requested", ...log.map((x) => x.join(","))].join("\n") + "\n";
  const files = { "ena_coingecko_via_defillama.csv": csv, "defillama_fetch_log.csv": logcsv };
  const digests = {};
  for (const [name, text] of Object.entries(files)) digests[name] = await sha(new TextEncoder().encode(text));
  window.__ll = { files, digests };
  return `rows ${rows.length}, statuses ${log.map((x) => x[1]).join("/")}, returned ${log.map((x) => x[5]).join("/")}, max offset ${Math.max(...rows.map((x) => Math.abs(x[4])))} s`;
})();
