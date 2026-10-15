// usde_chains_confirm.js
//
// Second reads for the chains where usde_chains_read.js found only one RPC that answered, Routescan's
// token supply for the same chains where its explorer API covers them, and the peers of the Arbitrum
// contract, which the first RPC refused. Run on the same page after usde_chains_read.js,
//     window.__cRun = USDE_CONFIRM.run(window.__u); await window.__cRun;
// Each RPC is first checked for the chain's ID. totalSupply is read at the block of the first read
// where the RPC still serves it, otherwise at its latest block, and the file says which. The files and
// their SHA-256 digests are added to window.__u.files and window.__u.digests.
(function (root) {
  "use strict";
  const ALT = {
    bsc: ["https://bsc-dataseed.bnbchain.org", "https://bsc-dataseed1.defibit.io", "https://bsc.publicnode.com"],
    avalanche: ["https://avalanche-c-chain-rpc.publicnode.com", "https://avax.meowrpc.com"],
    plasma: ["https://plasma.drpc.org", "https://plasma-rpc.publicnode.com"],
    robinhood: ["https://robinhood-chain-rpc.publicnode.com", "https://robinhood-rpc.publicnode.com", "https://robinhood.drpc.org"],
    megaeth: ["https://megaeth.drpc.org", "https://rpc.megaeth.com", "https://megaeth-rpc.publicnode.com"],
    tempo: ["https://tempo.drpc.org", "https://tempo-rpc.publicnode.com"],
    zircuit: ["https://zircuit1-mainnet.p2pify.com", "https://zircuit-rpc.publicnode.com"],
    swell: ["https://swell-mainnet.alt.technology", "https://swellchain-rpc.publicnode.com"],
  };
  const ARB_PEERS_RPC = "https://arbitrum-one-rpc.publicnode.com";
  const ROUTESCAN = (chainId) => "https://api.routescan.io/v2/network/mainnet/evm/" + chainId + "/etherscan/api";
  const SEL_TOTAL = "0x18160ddd", SEL_PEERS = "0xbb0b6a53";
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  async function rpc(url, method, params) {
    const ctl = new AbortController();
    const t = setTimeout(() => ctl.abort(), 12000);
    try {
      const r = await fetch(url, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ jsonrpc: "2.0", id: 1, method, params }), cache: "no-store", signal: ctl.signal });
      const text = await r.text();
      let j = null;
      try { j = JSON.parse(text); } catch (e) { return { err: "http " + r.status + " not json", text }; }
      return j.error ? { err: "http " + r.status + " " + JSON.stringify(j.error).slice(0, 160), text } : { ok: j.result, text };
    } catch (e) {
      return { err: e.name };
    } finally {
      clearTimeout(t);
    }
  }

  function csv(rows) {
    return rows.map((r) => r.map((v) => {
      const s = v === null || v === undefined ? "" : String(v);
      return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
    }).join(",")).join("\n") + "\n";
  }

  async function sha256hex(text) {
    const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
    return Array.from(new Uint8Array(h)).map((b) => b.toString(16).padStart(2, "0")).join("");
  }

  async function run(U) {
    const rows = [["chain_key", "rpc", "chain_id_answer", "block_requested", "read_at", "read_time_utc", "supply_raw", "note", "read_utc"]];
    for (const c of U.chains.filter((x) => ALT[x.key])) {
      for (const u of ALT[c.key]) {
        const id = await rpc(u, "eth_chainId", []);
        const cid = id.ok ? parseInt(id.ok, 16) : null;
        if (cid !== c.chainId) { rows.push([c.key, u, cid === null ? "no answer" : cid, c.block, "", "", "", id.err || "wrong chain", new Date().toISOString()]); continue; }
        const B = "0x" + c.block.toString(16);
        let r = await rpc(u, "eth_call", [{ to: c.token, data: SEL_TOTAL }, B]);
        if (r.ok && r.ok !== "0x") {
          rows.push([c.key, u, cid, c.block, c.block, c.time, BigInt(r.ok).toString(), "", new Date().toISOString()]);
          continue;
        }
        const firstErr = r.err || "empty";
        const bn = await rpc(u, "eth_getBlockByNumber", ["latest", false]);
        if (!bn.ok) { rows.push([c.key, u, cid, c.block, "", "", "", firstErr + "; latest block " + (bn.err || "empty"), new Date().toISOString()]); continue; }
        r = await rpc(u, "eth_call", [{ to: c.token, data: SEL_TOTAL }, bn.ok.number]);
        rows.push([c.key, u, cid, c.block, parseInt(bn.ok.number, 16), new Date(parseInt(bn.ok.timestamp, 16) * 1000).toISOString(), r.ok && r.ok !== "0x" ? BigInt(r.ok).toString() : "", "at the block of the first read: " + firstErr + (r.ok ? "" : "; at the latest block: " + (r.err || "empty")), new Date().toISOString()]);
        await sleep(200);
      }
    }
    // Routescan's explorer API, its token supply at its latest block and that block.
    for (const c of U.chains.filter((x) => ALT[x.key])) {
      const base = ROUTESCAN(c.chainId);
      const ts = await fetch(base + "?module=stats&action=tokensupply&contractaddress=" + c.token, { cache: "no-store" }).then((r) => r.text()).catch((e) => "error " + e.name);
      const bn = await fetch(base + "?module=proxy&action=eth_blockNumber", { cache: "no-store" }).then((r) => r.text()).catch((e) => "error " + e.name);
      let supply = "", blk = "", err = "";
      try { const j = JSON.parse(ts); if (j.status === "1") supply = BigInt(j.result).toString(); else err = "tokensupply " + String(j.result).slice(0, 100); } catch (e) { err = "tokensupply " + ts.slice(0, 100); }
      try { blk = parseInt(JSON.parse(bn).result, 16); if (!Number.isFinite(blk)) { blk = ""; } } catch (e) { blk = ""; }
      rows.push([c.key, base, "", c.block, blk, "", supply, err ? err : "Routescan token supply at its latest block", new Date().toISOString()]);
      await sleep(300);
    }
    U.files["confirm_supply.csv"] = csv(rows);

    const arb = U.chains.find((x) => x.key === "arbitrum");
    const eids = [30101].concat(arb.unionEids.filter((e) => e !== arb.eid));
    const B = "0x" + arb.block.toString(16);
    const prow = [["chain_key", "rpc", "read_at", "eid_read", "peer"]];
    const body = JSON.stringify(eids.map((e, i) => ({ jsonrpc: "2.0", id: i, method: "eth_call", params: [{ to: arb.oft, data: SEL_PEERS + e.toString(16).padStart(64, "0") }, B] })));
    const r = await fetch(ARB_PEERS_RPC, { method: "POST", headers: { "content-type": "application/json" }, body, cache: "no-store" });
    const j = JSON.parse(await r.text());
    const byId = {};
    for (const x of j) byId[x.id] = x.error ? null : x.result;
    // Where the RPC no longer serves the read block, the peer at its latest block, marked as such.
    const missing = eids.map((e, i) => i).filter((i) => byId[i] === null);
    let latestBlock = "";
    if (missing.length) {
      const bn = await rpc(ARB_PEERS_RPC, "eth_blockNumber", []);
      latestBlock = bn.ok ? parseInt(bn.ok, 16) : "";
      const body2 = JSON.stringify(missing.map((i) => ({ jsonrpc: "2.0", id: i, method: "eth_call", params: [{ to: arb.oft, data: SEL_PEERS + eids[i].toString(16).padStart(64, "0") }, bn.ok] })));
      const r2 = await fetch(ARB_PEERS_RPC, { method: "POST", headers: { "content-type": "application/json" }, body: body2, cache: "no-store" });
      for (const x of JSON.parse(await r2.text())) byId[x.id] = x.error ? "error " + JSON.stringify(x.error).slice(0, 80) : x.result;
    }
    eids.forEach((e, i) => prow.push(["arbitrum", ARB_PEERS_RPC, missing.includes(i) ? latestBlock : arb.block, e, byId[i]]));
    U.files["arbitrum_peers.csv"] = csv(prow);
    for (const k of ["confirm_supply.csv", "arbitrum_peers.csv"]) U.digests[k] = await sha256hex(U.files[k]);
    return U;
  }

  root.USDE_CONFIRM = { run };
})(typeof window !== "undefined" ? window : globalThis);
