// Reads FINRA's daily short sale volume files (consolidated NMS, CNMSshvol) for every USDE
// session from June 25 to October 8, 2026, keeps the USDE and USDEW rows, and records the
// SHA-256, size and record count of each whole file. Paste into the developer console on any
// page of https://cdn.finra.org/ . Read-only GET requests, no login. Results in window.__finra.
await (async () => {
  const SESSIONS = "20260625,20260626,20260629,20260630,20260701,20260702,20260706,20260707,20260708,20260709,20260710,20260713,20260714,20260715,20260716,20260717,20260720,20260721,20260722,20260723,20260724,20260727,20260728,20260729,20260730,20260731,20260803,20260804,20260805,20260806,20260807,20260810,20260811,20260812,20260813,20260814,20260817,20260818,20260819,20260820,20260821,20260824,20260825,20260826,20260827,20260828,20260831,20260901,20260902,20260903,20260904,20260908,20260909,20260910,20260911,20260914,20260915,20260916,20260917,20260918,20260921,20260922,20260923,20260924,20260925,20260928,20260929,20260930,20261001,20261002,20261005,20261006,20261007,20261008".split(",");
  const SYMBOLS = ["USDE", "USDEW", "TLGY", "TLGYU", "TLGYW"];
  const HEADER = "Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market";
  const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
  const sha = async (bytes) => hex(await crypto.subtle.digest("SHA-256", bytes));
  const rows = [];
  const log = [];
  for (const d of SESSIONS) {
    const url = `https://cdn.finra.org/equity/regsho/daily/CNMSshvol${d}.txt`;
    const r = await fetch(url, { cache: "no-store" });
    const buf = await r.arrayBuffer();
    const text = new TextDecoder().decode(buf);
    const lines = text.split("\n").map((l) => l.replace(/\r$/, ""));
    const body = lines.filter((l) => l && l !== HEADER && l.includes("|"));
    const trailer = lines.filter((l) => /^\d+$/.test(l)).pop() || "";
    for (const l of body) {
      const f = l.split("|");
      if (SYMBOLS.includes(f[1])) rows.push(f);
    }
    log.push({ url, status: r.status, fetched_at: new Date().toISOString(), bytes: buf.byteLength,
               sha256: await sha(buf), header_ok: lines[0] === HEADER, records: body.length, trailer });
    await new Promise((res) => setTimeout(res, 250));
  }
  const csv = (header, list) => [header.join(","), ...list.map((x) => x.join(","))].join("\n") + "\n";
  const files = {
    "finra_daily_short_volume.csv": csv(["date", "symbol", "short_volume", "short_exempt_volume", "total_volume", "market"],
      rows.map((f) => [f[0], f[1], f[2], f[3], f[4], `"${f[5]}"`])),
    "finra_daily_fetch_log.csv": csv(["url", "status", "fetched_at", "bytes", "sha256", "header_ok", "records", "trailer"],
      log.map((x) => [x.url, x.status, x.fetched_at, x.bytes, x.sha256, x.header_ok, x.records, x.trailer])),
  };
  const digests = {};
  for (const [name, text] of Object.entries(files)) digests[name] = await sha(new TextEncoder().encode(text));
  window.__finra = { files, digests, log, rows };
  return `sessions ${SESSIONS.length}, rows ${rows.length}, statuses ${[...new Set(log.map((x) => x.status))].join("/")}`;
})();
