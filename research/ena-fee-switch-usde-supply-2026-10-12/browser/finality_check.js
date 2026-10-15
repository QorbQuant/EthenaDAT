// finality_check.js
//
// Run after usde_supply_read.js, once its last day-end block is older than Ethereum's finality delay of about
// 13 minutes. Reads the finalized block on two RPCs, then the hash of every day-end block again on the first
// archive RPC, and compares the SHA-256 of those hashes, joined in day order with newlines, with
// sha256_primary_day_end_block_hashes in run.json. If the digests are the same and every day-end block is at
// or below the finalized block, the supply figures in day_reads.csv come from final blocks.
//
// Paste into the developer console on https://eth.blockscout.com/api/v2/stats and run
//     window.__fcRun = FINALITY_CHECK.run(blocks, wantSha); await window.__fcRun;
// where blocks is the block column of day_reads.csv, in order, and wantSha the digest in run.json.
// The file finality_check.json and its SHA-256 digest are left in window.__fc.
//
// Every request is read-only, with no login and no key.
(function (root) {
  "use strict";

  const FINAL_RPCS = ["https://ethereum-rpc.publicnode.com", "https://eth.drpc.org"];
  const HASH_RPC = "https://eth.drpc.org"; // the first archive RPC of usde_supply_read.js
  const BATCH = 3;
  const host = (u) => u.split("/")[2];
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  let requests = 0;

  async function post(url, body) {
    for (let attempt = 0; attempt < 6; attempt++) {
      const ctl = new AbortController();
      const t = setTimeout(() => ctl.abort(), 25000);
      try {
        requests++;
        const r = await fetch(url, { method: "POST", cache: "no-store", signal: ctl.signal, headers: { "content-type": "application/json" }, body });
        const text = await r.text();
        if (r.status !== 200) { await sleep((r.status === 429 ? 5000 : 1500) * (attempt + 1)); continue; }
        const j = JSON.parse(text);
        const items = Array.isArray(j) ? j : [j];
        if (items.some((x) => x.error)) { await sleep(2000 * (attempt + 1)); continue; }
        return j;
      } catch (e) {
        await sleep(1500 * (attempt + 1));
      } finally {
        clearTimeout(t);
      }
    }
    throw new Error("no answer from " + host(url));
  }

  async function sha256hex(text) {
    const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
    return Array.from(new Uint8Array(h)).map((b) => b.toString(16).padStart(2, "0")).join("");
  }

  async function run(blocks, wantSha) {
    const started = new Date().toISOString();
    const finalized = [];
    for (const url of FINAL_RPCS) {
      const j = await post(url, JSON.stringify({ jsonrpc: "2.0", id: 1, method: "eth_getBlockByNumber", params: ["finalized", false] }));
      finalized.push({ rpc_host: host(url), block: parseInt(j.result.number, 16), block_time_unix: parseInt(j.result.timestamp, 16) });
    }
    const hashes = new Array(blocks.length);
    for (let i = 0; i < blocks.length; i += BATCH) {
      const part = blocks.slice(i, i + BATCH);
      const j = await post(HASH_RPC, JSON.stringify(part.map((b, k) => ({ jsonrpc: "2.0", id: k + 1, method: "eth_getBlockByNumber", params: ["0x" + b.toString(16), false] }))));
      const byId = {};
      for (const x of j) byId[x.id] = x.result;
      part.forEach((b, k) => {
        const res = byId[k + 1];
        if (!res || parseInt(res.number, 16) !== b) throw new Error("bad header " + b);
        hashes[i + k] = res.hash;
      });
    }
    const last = Math.max.apply(null, blocks);
    const sha = await sha256hex(hashes.join("\n"));
    const out = {
      started_utc: started,
      finished_utc: new Date().toISOString(),
      finalized,
      hash_rpc_host: host(HASH_RPC),
      day_end_blocks: blocks.length,
      last_day_end_block: last,
      every_day_end_block_at_or_below_finalized: finalized.every((f) => f.block >= last),
      sha256_day_end_block_hashes_now: sha,
      sha256_day_end_block_hashes_in_run: wantSha,
      same_digest: sha === wantSha,
      requests,
    };
    const text = JSON.stringify(out, null, 1) + "\n";
    root.__fc = { text, digest: await sha256hex(text) };
    return root.__fc;
  }

  root.FINALITY_CHECK = { run };
})(typeof window !== "undefined" ? window : globalThis);
