// Reads FINRA's consolidated short interest records for USDE and USDEW from FINRA's public
// Query API. Paste into the developer console on any page of https://api.finra.org/ .
// One POST request per symbol, no login. Results in window.__si.
await (async () => {
  const URL = "https://api.finra.org/data/group/otcMarket/name/consolidatedShortInterest";
  const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
  const sha = async (bytes) => hex(await crypto.subtle.digest("SHA-256", bytes));
  const files = {};
  const log = [];
  for (const symbol of ["USDE", "USDEW"]) {
    const body = JSON.stringify({ limit: 1000, compareFilters: [{ compareType: "equal", fieldName: "symbolCode", fieldValue: symbol }] });
    const r = await fetch(URL, { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body });
    const buf = await r.arrayBuffer();
    const text = new TextDecoder().decode(buf);
    files[`finra_short_interest_${symbol.toLowerCase()}.json`] = text.endsWith("\n") ? text : text + "\n";
    log.push([URL, "POST", `"${body.replace(/"/g, '""')}"`, r.status, new Date().toISOString(), buf.byteLength, await sha(buf)]);
    await new Promise((res) => setTimeout(res, 500));
  }
  files["finra_short_interest_fetch_log.csv"] = ["url,method,request_body,status,fetched_at,bytes,sha256",
    ...log.map((x) => x.join(","))].join("\n") + "\n";
  const digests = {};
  for (const [name, text] of Object.entries(files)) digests[name] = await sha(new TextEncoder().encode(text));
  window.__si = { files, digests };
  return Object.entries(files).map(([k, v]) => `${k} ${v.length}`).join("; ");
})();
