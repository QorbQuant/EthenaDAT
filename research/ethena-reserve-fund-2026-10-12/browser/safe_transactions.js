// safe_transactions.js
//
// Run after reserve_fund_read.js, on the same page. Counts the transactions sent to the Reserve Fund's
// Safe by status, method and result, from Blockscout, and adds safe_transactions.csv and its SHA-256 to
// window.__rf.files and window.__rf.digests. It keeps no transaction hashes or senders.
(async function () {
  "use strict";
  const RF = "0x2b5ab59163a6e93b4486f6055d33ca4a115dd4d5";
  let items = [], params = "", pages = 0;
  for (;;) {
    const r = await fetch("https://eth.blockscout.com/api/v2/addresses/" + RF + "/transactions" + (params ? "?" + params : ""));
    const j = await r.json();
    items = items.concat(j.items || []);
    pages++;
    if (!j.next_page_params || pages > 40) break;
    params = new URLSearchParams(j.next_page_params).toString();
  }
  const counts = {};
  for (const t of items) {
    if (!t.to || t.to.hash.toLowerCase() !== RF) continue;
    if (Number(t.block_number) > window.__rf.block) continue;
    const k = [t.status || "", t.method || "", t.result || ""].join("|");
    counts[k] = (counts[k] || 0) + 1;
  }
  const lines = [["status", "method", "result", "transactions"]].concat(Object.keys(counts).sort().map((k) => k.split("|").concat([counts[k]])));
  const text = lines.map((r) => r.join(",")).join("\n") + "\n";
  window.__rf.files["safe_transactions.csv"] = text;
  window.__rf.digests["safe_transactions.csv"] = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text))))
    .map((b) => b.toString(16).padStart(2, "0")).join("");
  return text;
})();
