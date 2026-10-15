// usde_chains_read.js
//
// Reads, at one time, the USDe on every chain that Ethena's USDe OFT adapter on Ethereum has had as a
// peer, the USDe the adapter holds on Ethereum, and the adapter's history of peers. A peer is the
// contract on another chain that the adapter accepts LayerZero messages from and sends them to.
//
// Paste into the developer console on https://arbitrum.publicnode.com/ , a page that allows requests to
// other sites, and run
//     window.__uRun = USDE_CHAINS.run(); await window.__uRun;
// Then, at least five minutes later, on the same page,
//     window.__mRun = USDE_CHAINS.messages(window.__u); await window.__mRun;
// reads LayerZero Scan's records of the USDe messages around the reads. The files and their SHA-256
// digests are left in window.__u.files and window.__u.digests.
//
// Every request is read-only, with no login and no key. The script never sends a transaction.
(function (root) {
  "use strict";

  const ADAPTER = "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34"; // USDe OFT adapter on Ethereum
  const USDE = "0x4c9edd5852cd905f086c759e8383e09bff1e68b3"; // USDe on Ethereum
  const PSM = "0xd7fcade52afb60fbf0e1e5f72a683f43820f56a0"; // USDe PSM Custodian, Ethena's key addresses page
  const ETH_EID = 30101;
  const SEL = {
    totalSupply: "0x18160ddd", balanceOf: "0x70a08231", decimals: "0x313ce567", token: "0xfc0c546a",
    approvalRequired: "0x9f68b964", sharedDecimals: "0x857749b0", decimalConversionRate: "0x963efcaa",
    peers: "0xbb0b6a53",
  };
  const TOPIC = {
    PeerSet: "0x238399d427b947898edb290f5ff0f9109849b1c3ba196a42e35f00c50a54b98b",
    OFTSent: "0x85496b760a4b7f8d66384b9df21b381f5d1b1e79f229a47aaf4c232edc2fe59a",
    OFTReceived: "0xefed6d3500546b29533b128a29e3a94d70788727f0507505ac12eaf2e578fd9c",
  };
  const LZ_META = "https://metadata.layerzero-api.com/v1/metadata";
  const LZ_SCAN = "https://scan.layerzero-api.com/v1/messages/latest";
  const PEERSET_URLS = {
    blockscout: "https://eth.blockscout.com/api?module=logs&action=getLogs&fromBlock=0&toBlock=latest&address=" + ADAPTER + "&topic0=" + TOPIC.PeerSet,
    routescan: "https://api.routescan.io/v2/network/mainnet/evm/1/etherscan/api?module=logs&action=getLogs&fromBlock=0&toBlock=latest&address=" + ADAPTER + "&topic0=" + TOPIC.PeerSet,
  };
  const ETH_RPCS = ["https://ethereum-rpc.publicnode.com", "https://eth.drpc.org", "https://cloudflare-eth.com"];
  // RPCs added to LayerZero's list where its list had none that answered for the right chain.
  const EXTRA_RPCS = {
    zircuit: ["https://mainnet.zircuit.com"],
    swell: ["https://swell.drpc.org"],
  };
  const SOLANA_RPCS = ["https://solana-mainnet.gateway.tatum.io", "https://rpc.solanatracker.io/public"];
  const APTOS_APIS = ["https://api.mainnet.aptoslabs.com/v1", "https://fullnode.mainnet.aptoslabs.com/v1"];
  const INITIA_REST = "https://rest.initia.xyz";
  const STELLAR_EXPERT = "https://api.stellar.expert/explorer/public/asset/";
  const STELLAR_ASSET = "USDE-GDJ5BNU5NN6NQ54D7OX6NQTUYNBZ42CAT33QGM5BIQ2QIYADAC5ICH47-1";

  const LOG = [];
  const RAW = [];
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const nowIso = () => new Date().toISOString();
  const low = (s) => String(s).toLowerCase();

  async function fetchText(label, url, opts, timeoutMs) {
    const ctl = new AbortController();
    const t = setTimeout(() => ctl.abort(), timeoutMs || 20000);
    const started = nowIso();
    try {
      const r = await fetch(url, Object.assign({ cache: "no-store", signal: ctl.signal }, opts || {}));
      const text = await r.text();
      LOG.push([started, label, url.split("?")[0], (opts && opts.method) || "GET", r.status, text.length]);
      return { status: r.status, text };
    } catch (e) {
      LOG.push([started, label, url.split("?")[0], (opts && opts.method) || "GET", "error " + e.name, 0]);
      return { status: 0, text: "", error: e.name + " " + e.message };
    } finally {
      clearTimeout(t);
    }
  }

  async function rpc(label, url, method, params, keep) {
    const body = JSON.stringify({ jsonrpc: "2.0", id: 1, method, params });
    const r = await fetchText(label, url, { method: "POST", headers: { "content-type": "application/json" }, body }, 15000);
    if (keep) RAW.push({ label, url, request: JSON.parse(body), status: r.status, response: r.text });
    if (r.status !== 200) return { err: "http " + r.status + " " + (r.error || r.text.slice(0, 120)) };
    try {
      const j = JSON.parse(r.text);
      return j.error ? { err: JSON.stringify(j.error).slice(0, 200) } : { ok: j.result };
    } catch (e) {
      return { err: "bad json " + r.text.slice(0, 80) };
    }
  }

  async function rpcBatch(label, url, calls, keep) {
    const body = JSON.stringify(calls.map((c, i) => ({ jsonrpc: "2.0", id: i, method: c[0], params: c[1] })));
    const r = await fetchText(label, url, { method: "POST", headers: { "content-type": "application/json" }, body }, 25000);
    if (keep) RAW.push({ label, url, request: JSON.parse(body), status: r.status, response: r.text });
    if (r.status !== 200) throw new Error("batch http " + r.status);
    const j = JSON.parse(r.text);
    if (!Array.isArray(j)) throw new Error("batch not supported " + r.text.slice(0, 120));
    const out = new Array(calls.length);
    for (const x of j) out[x.id] = x.error ? { err: JSON.stringify(x.error).slice(0, 200) } : { ok: x.result };
    for (let i = 0; i < out.length; i++) if (!out[i]) out[i] = { err: "missing" };
    return out;
  }

  // Calls in one batch where the RPC allows it, one by one where it does not.
  async function multi(label, url, calls, keep) {
    try {
      return await rpcBatch(label, url, calls, keep);
    } catch (e) {
      const out = [];
      for (const c of calls) out.push(await rpc(label, url, c[0], c[1], keep));
      return out;
    }
  }

  async function sha256hex(text) {
    const buf = new TextEncoder().encode(text);
    const h = await crypto.subtle.digest("SHA-256", buf);
    return Array.from(new Uint8Array(h)).map((b) => b.toString(16).padStart(2, "0")).join("");
  }

  const pad32 = (hexNoPrefix) => hexNoPrefix.toLowerCase().padStart(64, "0");
  const addrArg = (a) => pad32(a.slice(2));
  const u32Arg = (n) => pad32(n.toString(16));
  const big = (hex) => (hex && hex !== "0x" ? BigInt(hex) : null);
  const isZero32 = (h) => /^0x0*$/.test(h);

  function units(raw, decimals) {
    if (raw === null || raw === undefined) return "";
    const neg = raw < 0n;
    let s = (neg ? -raw : raw).toString().padStart(decimals + 1, "0");
    const out = decimals ? s.slice(0, s.length - decimals) + "." + s.slice(s.length - decimals) : s;
    return (neg ? "-" : "") + out;
  }

  function b58(hex) {
    const A = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
    let n = BigInt("0x" + hex);
    let s = "";
    while (n > 0n) { s = A[Number(n % 58n)] + s; n /= 58n; }
    for (let i = 0; i < hex.length && hex.slice(i, i + 2) === "00"; i += 2) s = "1" + s;
    return s;
  }

  function csv(rows) {
    return rows.map((r) => r.map((v) => {
      const s = v === null || v === undefined ? "" : String(v);
      return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
    }).join(",")).join("\n") + "\n";
  }

  function parsePeerLogs(text) {
    const j = JSON.parse(text);
    if (!Array.isArray(j.result)) throw new Error("no result array");
    return j.result.map((l) => ({
      block: parseInt(l.blockNumber, 16),
      time: parseInt(l.timeStamp, 16),
      logIndex: parseInt(l.logIndex || "0x0", 16),
      eid: parseInt(l.data.slice(2, 66), 16),
      peer: "0x" + l.data.slice(66, 130).toLowerCase(),
    })).sort((a, b) => a.block - b.block || a.logIndex - b.logIndex);
  }

  // ---- chain readers -------------------------------------------------------------------------------

  async function pickEvmRpcs(c) {
    // Candidates in order, LayerZero's list after any added above, checked one by one until three
    // answer with the chain's ID.
    const cands = (EXTRA_RPCS[c.key] || []).concat(c.lzRpcs).filter((u, i, a) => /^https:\/\//.test(u) && !/[{}<>$]|api[_-]?key/i.test(u) && a.indexOf(u) === i);
    c.rpcChecks = [];
    c.goodRpcs = [];
    for (const u of cands) {
      if (c.goodRpcs.length >= 3) break;
      const r = await rpc("chainId " + c.key, u, "eth_chainId", []);
      const id = r.ok ? parseInt(r.ok, 16) : null;
      c.rpcChecks.push(u + " " + (id === null ? "no answer" : id));
      if (id === c.chainId) c.goodRpcs.push(u);
    }
  }

  async function trySnapEvm(c, u) {
    const bn = await rpc("block " + c.key, u, "eth_blockNumber", [], true);
    if (!bn.ok) { c.lastErr = "eth_blockNumber " + bn.err; return false; }
    // Tron's JSON-RPC answers calls only at the latest block, so its block is the one just before.
    const B = c.latestOnly ? "latest" : bn.ok;
    const calls = [
      ["eth_getBlockByNumber", [B, false]],
      ["eth_call", [{ to: c.oft, data: SEL.peers + u32Arg(ETH_EID) }, B]],
    ];
    if (c.native) calls.push(["eth_getBalance", [c.oft, B]]);
    else calls.push(["eth_call", [{ to: c.token, data: SEL.totalSupply }, B]], ["eth_call", [{ to: c.token, data: SEL.decimals }, B]], ["eth_call", [{ to: c.token, data: SEL.balanceOf + addrArg(PSM) }, B]]);
    const res = await multi("snapshot " + c.key, u, calls, true);
    const bad = res.findIndex((x) => !x.ok || x.ok === "0x");
    if (bad >= 0) { c.lastErr = calls[bad][0] + " " + (res[bad].err || "empty"); return false; }
    c.block = c.latestOnly ? parseInt(res[0].ok.number, 16) : parseInt(bn.ok, 16);
    c.time = new Date(parseInt(res[0].ok.timestamp, 16) * 1000).toISOString();
    c.peerToEthereum = res[1].ok;
    if (c.native) {
      c.proxyNativeBalance = big(res[2].ok).toString();
    } else {
      c.supplyRaw = big(res[2].ok);
      c.decimals = Number(big(res[3].ok));
      c.psmRaw = big(res[4].ok);
    }
    c.rpc1 = u;
    return true;
  }

  async function snapEvm(c) {
    if (!c.goodRpcs.length) { c.note = "no RPC answered for chain id " + c.chainId; return; }
    c.snapAttempts = 0;
    for (const u of c.goodRpcs) {
      for (let attempt = 0; attempt < 3; attempt++) {
        c.snapAttempts++;
        if (await trySnapEvm(c, u)) return;
        await sleep(1500 * (attempt + 1));
      }
    }
    c.note = "no complete read, last error " + c.lastErr;
  }

  async function confirmEvm(c) {
    if (c.block === undefined || c.native || c.latestOnly) return;
    const B = "0x" + c.block.toString(16);
    for (const u of c.goodRpcs.filter((x) => x !== c.rpc1)) {
      for (let attempt = 0; attempt < 3; attempt++) {
        const r = await rpc("confirm " + c.key, u, "eth_call", [{ to: c.token, data: SEL.totalSupply }, B], true);
        if (r.ok && r.ok !== "0x") { c.supply2Raw = big(r.ok); c.source2Block = c.block; c.rpc2 = u; return; }
        c.confirmErr = "second RPC " + (r.err || "empty");
        await sleep(2000);
      }
    }
  }

  async function peerMatrix(c, eids) {
    // The contract's peer for Ethereum and for every chain in the adapter's history, at the read block.
    if (!c.rpc1 || c.block === undefined) return;
    const B = c.latestOnly ? "latest" : "0x" + c.block.toString(16);
    c.peers = {};
    let res = null;
    try {
      res = await rpcBatch("peers " + c.key, c.rpc1, eids.map((e) => ["eth_call", [{ to: c.oft, data: SEL.peers + u32Arg(e) }, B]]));
    } catch (e) {
      res = null;
    }
    for (let k = 0; k < eids.length; k++) {
      if (res && res[k].ok) { c.peers[eids[k]] = res[k].ok; continue; }
      let v = "error";
      for (let attempt = 0; attempt < 3 && v === "error"; attempt++) {
        const r = await rpc("peers " + c.key, c.rpc1, "eth_call", [{ to: c.oft, data: SEL.peers + u32Arg(eids[k]) }, B]);
        if (r.ok) v = r.ok; else await sleep(700 * (attempt + 1));
      }
      c.peers[eids[k]] = v;
      await sleep(120);
    }
  }

  async function etherealNet(c) {
    // USDe on Ethereal is the chain's native coin. Its proxy contract holds none, so the USDe that came
    // through the bridge is the USDe the proxy received less the USDe it sent, from block 0 to the read.
    if (!c.rpc1 || c.block === undefined) return;
    const acc = { sentN: 0, sentLD: 0n, recvN: 0, recvLD: 0n, byEid: {}, calls: 0 };
    async function scan(topic, from, to, kind) {
      acc.calls++;
      const r = await rpc("ethereal logs", c.rpc1, "eth_getLogs", [{ address: c.oft, topics: [topic], fromBlock: "0x" + from.toString(16), toBlock: "0x" + to.toString(16) }]);
      if (r.err) {
        if (to > from && /limit|exceed|too many|range/i.test(r.err)) { const mid = Math.floor((from + to) / 2); await scan(topic, from, mid, kind); await scan(topic, mid + 1, to, kind); return; }
        throw new Error("ethereal getLogs " + from + "-" + to + " " + r.err);
      }
      for (const l of r.ok) {
        const eid = parseInt(l.data.slice(2, 66), 16);
        const a = BigInt("0x" + l.data.slice(66, 130));
        const e = (acc.byEid[eid] = acc.byEid[eid] || { sentN: 0, sentLD: 0n, recvN: 0, recvLD: 0n });
        if (kind === "sent") { acc.sentN++; acc.sentLD += a; e.sentN++; e.sentLD += a; }
        else { acc.recvN++; acc.recvLD += a; e.recvN++; e.recvLD += a; }
      }
    }
    await scan(TOPIC.OFTSent, 0, c.block, "sent");
    await scan(TOPIC.OFTReceived, 0, c.block, "recv");
    c.etherealFlows = acc;
    c.supplyRaw = acc.recvLD - acc.sentLD;
    c.decimals = 18;
  }

  async function snapSolana(c) {
    const reads = await Promise.all(SOLANA_RPCS.map((u) => rpc("solana supply", u, "getTokenSupply", [c.token, { commitment: "finalized" }], true)));
    const ok = reads.map((r, i) => ({ r, u: SOLANA_RPCS[i] })).filter((x) => x.r.ok);
    if (!ok.length) { c.note = "no Solana RPC answered"; return; }
    c.rpc1 = ok[0].u;
    c.block = ok[0].r.ok.context.slot;
    c.supplyRaw = BigInt(ok[0].r.ok.value.amount);
    c.decimals = ok[0].r.ok.value.decimals;
    if (ok[1]) { c.rpc2 = ok[1].u; c.supply2Raw = BigInt(ok[1].r.ok.value.amount); c.source2Block = ok[1].r.ok.context.slot; }
    const bt = await rpc("solana time", c.rpc1, "getBlockTime", [c.block], true);
    c.time = bt.ok ? new Date(bt.ok * 1000).toISOString() : "";
    const mi = await rpc("solana mint", c.rpc1, "getAccountInfo", [c.token, { encoding: "jsonParsed", commitment: "finalized" }], true);
    try { c.mintAuthority = mi.ok.value.data.parsed.info.mintAuthority; c.freezeAuthority = mi.ok.value.data.parsed.info.freezeAuthority; } catch (e) { c.mintAuthority = ""; }
  }

  async function snapAptos(c) {
    const info = await fetchText("aptos ledger", APTOS_APIS[0], {}, 15000);
    RAW.push({ label: "aptos ledger", url: APTOS_APIS[0], status: info.status, response: info.text });
    let v;
    try { const j = JSON.parse(info.text); v = j.ledger_version; c.block = Number(v); c.time = new Date(Number(j.ledger_timestamp) / 1000).toISOString(); } catch (e) { c.note = "aptos ledger info failed"; return; }
    const body = JSON.stringify({ function: "0x1::fungible_asset::supply", type_arguments: ["0x1::fungible_asset::Metadata"], arguments: [c.token] });
    const reads = await Promise.all(APTOS_APIS.map(async (u) => {
      const r = await fetchText("aptos supply", u + "/view?ledger_version=" + v, { method: "POST", headers: { "content-type": "application/json" }, body }, 15000);
      RAW.push({ label: "aptos supply", url: u + "/view?ledger_version=" + v, request: JSON.parse(body), status: r.status, response: r.text });
      try { return BigInt(JSON.parse(r.text)[0].vec[0]); } catch (e) { return null; }
    }));
    c.rpc1 = APTOS_APIS[0]; c.supplyRaw = reads[0];
    c.rpc2 = APTOS_APIS[1]; c.supply2Raw = reads[1]; c.source2Block = c.block;
    const d = await fetchText("aptos decimals", APTOS_APIS[0] + "/view?ledger_version=" + v, { method: "POST", headers: { "content-type": "application/json" }, body: body.replace("::supply", "::decimals") }, 15000);
    try { c.decimals = Number(JSON.parse(d.text)[0]); } catch (e) { c.decimals = null; }
  }

  async function snapTon(c) {
    const mc = await fetchText("ton masterchain", "https://toncenter.com/api/v3/masterchainInfo", {}, 15000);
    RAW.push({ label: "ton masterchain", url: "https://toncenter.com/api/v3/masterchainInfo", status: mc.status, response: mc.text });
    try { const j = JSON.parse(mc.text); c.block = j.last.seqno; c.time = new Date(j.last.gen_utime * 1000).toISOString(); } catch (e) { c.note = "masterchainInfo failed"; }
    const u1 = "https://toncenter.com/api/v3/jetton/masters?address=" + c.tokenFriendly + "&limit=1";
    const r1 = await fetchText("ton supply", u1, {}, 15000);
    RAW.push({ label: "ton supply", url: u1, status: r1.status, response: r1.text });
    try { const j = JSON.parse(r1.text).jetton_masters[0]; c.supplyRaw = BigInt(j.total_supply); c.decimals = Number(j.jetton_content.decimals); c.tonMaster = j.address; } catch (e) { c.note = "toncenter jetton read failed"; }
    c.rpc1 = "https://toncenter.com/api/v3";
    const u2 = "https://tonapi.io/v2/jettons/" + c.tokenFriendly;
    const r2 = await fetchText("ton supply 2", u2, {}, 15000);
    RAW.push({ label: "ton supply 2", url: u2, status: r2.status, response: r2.text });
    try { c.supply2Raw = BigInt(JSON.parse(r2.text).total_supply); c.rpc2 = "https://tonapi.io/v2"; } catch (e) { c.rpc2 = null; }
  }

  async function snapStellar(c) {
    const u = STELLAR_EXPERT + STELLAR_ASSET;
    const r = await fetchText("stellar supply", u, {}, 15000);
    RAW.push({ label: "stellar supply", url: u, status: r.status, response: r.text });
    try {
      const j = JSON.parse(r.text);
      c.supplyRaw = BigInt(j.supply); c.decimals = Number(j.decimals); c.stellarContract = j.contract; c.time = nowIso(); c.rpc1 = "https://api.stellar.expert";
    } catch (e) {
      c.note = "Stellar Expert not readable from this page, read separately";
    }
  }

  async function prepInitia(c) {
    const u = INITIA_REST + "/initia/move/v1/accounts/" + c.peer + "/resources";
    const r = await fetchText("initia resources", u, {}, 15000);
    RAW.push({ label: "initia resources", url: u, status: r.status, response: r.text });
    try {
      const res = JSON.parse(r.text).resources.find((x) => /::oft_fa::OftImpl$/.test(x.struct_tag));
      c.token = JSON.parse(res.move_resource).data.metadata.inner;
    } catch (e) {
      c.note = "Initia OftImpl not found";
    }
  }

  async function snapInitia(c) {
    if (!c.token) return;
    const lb = await fetchText("initia block", INITIA_REST + "/cosmos/base/tendermint/v1beta1/blocks/latest", {}, 15000);
    try { const h = JSON.parse(lb.text).block.header; c.block = Number(h.height); c.time = new Date(h.time).toISOString(); } catch (e) { c.note = "initia block failed"; return; }
    const u1 = INITIA_REST + "/cosmos/bank/v1beta1/supply/by_denom?denom=move/" + c.token.slice(2);
    const r1 = await fetchText("initia bank supply", u1, { headers: { "x-cosmos-block-height": String(c.block) } }, 15000);
    RAW.push({ label: "initia bank supply", url: u1, height: c.block, status: r1.status, response: r1.text });
    try { c.supplyRaw = BigInt(JSON.parse(r1.text).amount.amount); } catch (e) { c.note = "initia bank supply failed"; }
    c.rpc1 = INITIA_REST + " bank";
    const body = JSON.stringify({ address: "0x1", module_name: "fungible_asset", function_name: "supply", type_args: ["0x1::fungible_asset::Metadata"], args: [JSON.stringify(c.token)] });
    const r2 = await fetchText("initia view supply", INITIA_REST + "/initia/move/v1/view/json", { method: "POST", headers: { "content-type": "application/json", "x-cosmos-block-height": String(c.block) }, body }, 15000);
    RAW.push({ label: "initia view supply", url: INITIA_REST + "/initia/move/v1/view/json", request: JSON.parse(body), height: c.block, status: r2.status, response: r2.text });
    try { c.supply2Raw = BigInt(JSON.parse(JSON.parse(r2.text).data)); c.rpc2 = INITIA_REST + " move view"; c.source2Block = c.block; } catch (e) { c.rpc2 = null; }
    const r3 = await fetchText("initia decimals", INITIA_REST + "/initia/move/v1/view/json", { method: "POST", headers: { "content-type": "application/json" }, body: body.replace('"supply"', '"decimals"') }, 15000);
    try { c.decimals = Number(JSON.parse(JSON.parse(r3.text).data)); } catch (e) { c.decimals = null; }
  }

  // ---- run -----------------------------------------------------------------------------------------

  async function run() {
    const U = { started: nowIso(), files: {}, digests: {} };
    root.__u = U;

    // LayerZero's metadata: endpoint IDs, chain IDs, RPCs and token addresses.
    const metaR = await fetchText("lz metadata", LZ_META, {}, 60000);
    if (metaR.status !== 200) throw new Error("LayerZero metadata " + metaR.status);
    U.lzMetaSha256 = await sha256hex(metaR.text);
    U.lzMetaBytes = new TextEncoder().encode(metaR.text).length;
    const meta = JSON.parse(metaR.text);
    const eidKey = {};
    for (const [k, v] of Object.entries(meta)) for (const d of v.deployments || []) if (d.version === 2 && d.stage === "mainnet") eidKey[Number(d.eid)] = k;
    const allEids = Object.keys(eidKey).map(Number).sort((a, b) => a - b);

    // The adapter's peer history from two indexers.
    const ps = {};
    for (const [name, url] of Object.entries(PEERSET_URLS)) {
      const r = await fetchText("peerset " + name, url, {}, 60000);
      ps[name] = { status: r.status, text: r.text, sha256: await sha256hex(r.text) };
    }
    const logsA = parsePeerLogs(ps.blockscout.text);
    const logsB = parsePeerLogs(ps.routescan.text);
    const keyOf = (x) => [x.block, x.logIndex, x.eid, x.peer].join("|");
    const setB = new Set(logsB.map(keyOf));
    U.peerLogsAgree = logsA.length === logsB.length && logsA.every((x) => setB.has(keyOf(x)));
    const lastPeer = {};
    const firstSet = {};
    for (const x of logsA) { lastPeer[x.eid] = x; if (!isZero32(x.peer) && !firstSet[x.eid]) firstSet[x.eid] = x; }
    const unionEids = Object.keys(lastPeer).map(Number).sort((a, b) => a - b);

    // Chains to read, from LayerZero's metadata and the peer each one last had.
    const chains = unionEids.map((eid) => {
      const key = eidKey[eid];
      const v = meta[key] || {};
      const cd = v.chainDetails || {};
      const lastNonZero = [...logsA].reverse().find((x) => x.eid === eid && !isZero32(x.peer));
      const peer = lastNonZero.peer;
      const toks = Object.entries(v.tokens || {}).filter(([a, t]) => /^usde$/i.test(t.symbol || ""));
      const tokenEntry = toks.find(([a, t]) => t.type !== "ProxyOFT");
      const proxyEntry = toks.find(([a, t]) => t.type === "ProxyOFT");
      const c = {
        eid, key, chainType: cd.chainType || "", chainId: cd.nativeChainId || null, name: cd.name || key,
        lzRpcs: (v.rpcs || []).map((x) => x.url), peer, connected: !isZero32(lastPeer[eid].peer),
        firstPeerBlock: firstSet[eid] ? firstSet[eid].block : null, firstPeerTime: firstSet[eid] ? new Date(firstSet[eid].time * 1000).toISOString() : "",
        lastChangeBlock: lastPeer[eid].block, lastChangeTime: new Date(lastPeer[eid].time * 1000).toISOString(),
        lzToken: tokenEntry ? tokenEntry[0] : "", lzTokenType: tokenEntry ? tokenEntry[1].type : "", lzTokenDecimals: tokenEntry ? tokenEntry[1].decimals : "",
        lzProxy: proxyEntry ? proxyEntry[0] : "", unionEids,
      };
      if (c.chainType === "evm" || c.chainType === "tron") {
        c.method = "evm";
        c.latestOnly = c.chainType === "tron";
        c.oft = "0x" + peer.slice(26);
        c.native = c.lzTokenType === "NativeToken";
        c.token = c.native ? "" : (c.lzTokenType === "ERC20" ? c.lzToken : c.oft);
      } else if (c.chainType === "solana") {
        c.method = "solana"; c.token = c.lzToken; c.store = b58(peer.slice(2));
      } else if (c.chainType === "aptos") {
        c.method = "aptos"; c.token = c.lzToken;
      } else if (c.chainType === "ton") {
        c.method = "ton"; c.token = c.lzToken; c.tokenFriendly = "0:" + c.lzToken.slice(2);
      } else if (c.chainType === "stellar") {
        c.method = "stellar"; c.token = c.lzToken;
      } else if (c.chainType === "initia") {
        c.method = "initia";
      } else {
        c.method = "unknown";
      }
      return c;
    });
    U.chains = chains;

    // Ethereum RPCs and every chain's RPCs, checked for the right chain ID before the reads.
    const ethChecked = await Promise.all(ETH_RPCS.map(async (u) => { const r = await rpc("chainId ethereum", u, "eth_chainId", []); return r.ok === "0x1" ? u : null; }));
    const ethRpcs = ethChecked.filter(Boolean);
    U.ethRpcs = ethRpcs;
    await Promise.all(chains.filter((c) => c.method === "evm").map(pickEvmRpcs));
    await Promise.all(chains.filter((c) => c.method === "initia").map(prepInitia));

    // The reads, all started together.
    U.snapshotStarted = nowIso();
    const eth = { rpc1: ethRpcs[0], rpc2: ethRpcs[1] || null };
    const ethSnap = (async () => {
      const bn = await rpc("block ethereum", eth.rpc1, "eth_blockNumber", [], true);
      eth.block = parseInt(bn.ok, 16);
      const B = bn.ok;
      const calls = [
        ["eth_getBlockByNumber", [B, false]],
        ["eth_call", [{ to: USDE, data: SEL.totalSupply }, B]],
        ["eth_call", [{ to: USDE, data: SEL.balanceOf + addrArg(ADAPTER) }, B]],
        ["eth_call", [{ to: USDE, data: SEL.balanceOf + addrArg(PSM) }, B]],
        ["eth_call", [{ to: USDE, data: SEL.decimals }, B]],
        ["eth_call", [{ to: ADAPTER, data: SEL.token }, B]],
        ["eth_call", [{ to: ADAPTER, data: SEL.approvalRequired }, B]],
        ["eth_call", [{ to: ADAPTER, data: SEL.sharedDecimals }, B]],
        ["eth_call", [{ to: ADAPTER, data: SEL.decimalConversionRate }, B]],
      ];
      const res = await multi("snapshot ethereum", eth.rpc1, calls, true);
      eth.time = new Date(parseInt(res[0].ok.timestamp, 16) * 1000).toISOString();
      eth.usdeSupply = big(res[1].ok);
      eth.adapterBalance = big(res[2].ok);
      eth.psmBalance = big(res[3].ok);
      eth.usdeDecimals = Number(big(res[4].ok));
      eth.adapterToken = "0x" + res[5].ok.slice(26);
      eth.approvalRequired = Number(big(res[6].ok));
      eth.sharedDecimals = Number(big(res[7].ok));
      eth.decimalConversionRate = big(res[8].ok);
    })();
    await Promise.all([ethSnap].concat(chains.map((c) => {
      if (c.method === "evm") return snapEvm(c);
      if (c.method === "solana") return snapSolana(c);
      if (c.method === "aptos") return snapAptos(c);
      if (c.method === "ton") return snapTon(c);
      if (c.method === "stellar") return snapStellar(c);
      if (c.method === "initia") return snapInitia(c);
      return Promise.resolve();
    })));
    U.snapshotFinished = nowIso();
    U.eth = eth;

    // After the reads. The same figures from a second source, every peer of each EVM contract, the
    // adapter's peers at the read block and the bridge flows of Ethereal.
    const B = "0x" + eth.block.toString(16);
    eth.peers = {};
    for (let i = 0; i < allEids.length; i += 40) {
      const chunk = allEids.slice(i, i + 40);
      const res = await rpcBatch("peers ethereum", eth.rpc1, chunk.map((e) => ["eth_call", [{ to: ADAPTER, data: SEL.peers + u32Arg(e) }, B]]));
      chunk.forEach((e, k) => { eth.peers[e] = res[k].ok || "error"; });
    }
    if (eth.rpc2) {
      const res = await multi("confirm ethereum", eth.rpc2, [
        ["eth_call", [{ to: USDE, data: SEL.totalSupply }, B]],
        ["eth_call", [{ to: USDE, data: SEL.balanceOf + addrArg(ADAPTER) }, B]],
      ].concat(unionEids.map((e) => ["eth_call", [{ to: ADAPTER, data: SEL.peers + u32Arg(e) }, B]])), true);
      eth.usdeSupply2 = res[0].ok ? big(res[0].ok) : null;
      eth.adapterBalance2 = res[1].ok ? big(res[1].ok) : null;
      eth.peers2 = {};
      unionEids.forEach((e, k) => { eth.peers2[e] = res[2 + k].ok || "error"; });
    }
    await Promise.all(chains.filter((c) => c.method === "evm").map(confirmEvm));
    for (const c of chains.filter((x) => x.method === "evm" && x.native)) await etherealNet(c);
    await Promise.all(chains.filter((x) => x.method === "evm").map((c) => peerMatrix(c, [ETH_EID].concat(unionEids.filter((e) => e !== c.eid)))));

    // Files.
    const f = U.files;
    f["lz_chains.csv"] = csv([["eid", "chain_key", "chain_name", "chain_type", "native_chain_id", "usde_token", "usde_token_type", "usde_decimals", "usde_proxy", "rpcs_listed"]].concat(
      chains.map((c) => [c.eid, c.key, c.name, c.chainType, c.chainId, c.lzToken, c.lzTokenType, c.lzTokenDecimals, c.lzProxy, c.lzRpcs.length])));
    f["peer_history.csv"] = csv([["block", "time_utc", "log_index", "eid", "chain_key", "peer"]].concat(
      logsA.map((x) => [x.block, new Date(x.time * 1000).toISOString(), x.logIndex, x.eid, eidKey[x.eid] || "", x.peer])));
    f["adapter_peers_at_read.csv"] = csv([["eid", "chain_key", "peer_rpc1", "peer_rpc2"]].concat(
      allEids.map((e) => [e, eidKey[e], eth.peers[e], eth.peers2 && e in eth.peers2 ? eth.peers2[e] : ""])));
    f["chains.csv"] = csv([["eid", "chain_key", "chain_type", "native_chain_id", "connected_at_read", "first_peer_block", "first_peer_time_utc", "last_change_block", "last_change_time_utc", "method", "contract_read", "oft_or_store", "decimals", "read_at", "read_time_utc", "supply_raw", "supply_usde", "psm_custodian_raw", "chain_side_peer_for_ethereum", "source1", "source2", "source2_read_at", "source2_supply_raw", "note"]].concat(
      chains.map((c) => [c.eid, c.key, c.chainType, c.chainId, c.connected ? 1 : 0, c.firstPeerBlock, c.firstPeerTime, c.lastChangeBlock, c.lastChangeTime, c.native ? "evm native coin" : c.method,
        c.native ? "(native coin)" : (c.token || ""), c.oft || c.store || c.peer, c.decimals === null || c.decimals === undefined ? "" : c.decimals, c.block === undefined ? "" : c.block, c.time || "",
        c.supplyRaw === null || c.supplyRaw === undefined ? "" : c.supplyRaw.toString(), c.supplyRaw === null || c.supplyRaw === undefined || c.decimals === null || c.decimals === undefined ? "" : units(c.supplyRaw, c.decimals),
        c.psmRaw === null || c.psmRaw === undefined ? "" : c.psmRaw.toString(), c.peerToEthereum || "", c.rpc1 || "", c.rpc2 || "", c.source2Block === undefined ? "" : c.source2Block,
        c.supply2Raw === null || c.supply2Raw === undefined ? "" : c.supply2Raw.toString(), [c.note, c.confirmErr, c.snapAttempts > 1 ? "attempts " + c.snapAttempts : ""].filter(Boolean).join("; ")])));
    f["peer_matrix.csv"] = csv([["chain_key", "eid", "read_at", "eid_read", "peer"]].concat(
      [].concat(...chains.filter((c) => c.peers).map((c) => Object.entries(c.peers).map(([e, p]) => [c.key, c.eid, c.block, e, p])))));
    const eth1 = chains.find((c) => c.native);
    if (eth1 && eth1.etherealFlows) {
      const a = eth1.etherealFlows;
      f["ethereal_flows.csv"] = csv([["other_eid", "chain_key", "received_count", "received_raw", "sent_count", "sent_raw"]].concat(
        Object.entries(a.byEid).map(([e, v]) => [e, eidKey[e] || "", v.recvN, v.recvLD.toString(), v.sentN, v.sentLD.toString()])).concat([["all", "", a.recvN, a.recvLD.toString(), a.sentN, a.sentLD.toString()]]));
    }
    f["ethereum.json"] = JSON.stringify({
      rpc1: eth.rpc1, rpc2: eth.rpc2, block: eth.block, time_utc: eth.time, adapter: ADAPTER, usde: USDE, psm_custodian: PSM,
      usde_total_supply_raw: eth.usdeSupply.toString(), adapter_balance_raw: eth.adapterBalance.toString(), psm_custodian_balance_raw: eth.psmBalance.toString(),
      usde_decimals: eth.usdeDecimals, adapter_token: eth.adapterToken, adapter_approval_required: eth.approvalRequired, adapter_shared_decimals: eth.sharedDecimals,
      adapter_decimal_conversion_rate: eth.decimalConversionRate.toString(),
      rpc2_usde_total_supply_raw: eth.usdeSupply2 === null || eth.usdeSupply2 === undefined ? "" : eth.usdeSupply2.toString(),
      rpc2_adapter_balance_raw: eth.adapterBalance2 === null || eth.adapterBalance2 === undefined ? "" : eth.adapterBalance2.toString(),
      lz_metadata_sha256: U.lzMetaSha256, lz_metadata_bytes: U.lzMetaBytes,
      peer_logs: { blockscout: { status: ps.blockscout.status, count: logsA.length, sha256: ps.blockscout.sha256 }, routescan: { status: ps.routescan.status, count: logsB.length, sha256: ps.routescan.sha256 }, agree: U.peerLogsAgree },
      started_utc: U.started, snapshot_started_utc: U.snapshotStarted, snapshot_finished_utc: U.snapshotFinished, finished_utc: nowIso(),
      rpc_checks: Object.fromEntries(chains.filter((c) => c.rpcChecks).map((c) => [c.key, c.rpcChecks])),
      solana: chains.filter((c) => c.method === "solana").map((c) => ({ mint: c.token, mint_authority: c.mintAuthority, freeze_authority: c.freezeAuthority, oft_store: c.store })),
    }, null, 1) + "\n";
    f["peerset_blockscout.json"] = ps.blockscout.text;
    f["peerset_routescan.json"] = ps.routescan.text;
    f["raw_reads.jsonl"] = RAW.map((x) => JSON.stringify(x)).join("\n") + "\n";
    f["request_log.csv"] = csv([["time_utc", "label", "url", "method", "status", "bytes"]].concat(LOG));
    for (const [k, v] of Object.entries(f)) U.digests[k] = await sha256hex(v);
    U.finished = nowIso();
    return U;
  }

  // ---- LayerZero Scan ------------------------------------------------------------------------------

  async function messages(U, hoursBefore, minutesAfter) {
    hoursBefore = hoursBefore || 24;
    minutesAfter = minutesAfter || 30;
    const t0 = Date.parse(U.snapshotStarted);
    const start = new Date(t0 - hoursBefore * 3600e3).toISOString();
    const end = new Date(t0 + minutesAfter * 60e3).toISOString();
    // The USDe contract on each chain as LayerZero Scan names it.
    const ua = {};
    ua[ETH_EID] = ADAPTER;
    for (const c of U.chains) {
      if (c.method === "evm") ua[c.eid] = low(c.oft);
      else if (c.method === "solana") ua[c.eid] = c.store;
      else ua[c.eid] = low(c.lzProxy || c.peer);
    }
    const seen = new Map();
    const queries = [{ srcOrDstOAppId: "ethena" }].concat(Object.entries(ua).map(([e, a]) => ({ srcOrDstChainIdUaAddress: e + "-" + a })));
    U.scanQueries = [];
    for (const q0 of queries) {
      let next = null, pages = 0, n = 0;
      do {
        const q = Object.assign({ start, end, limit: "150" }, q0);
        if (next) q.nextToken = next;
        const url = LZ_SCAN + "?" + new URLSearchParams(q).toString();
        const r = await fetchText("lzscan", url, {}, 30000);
        if (r.status !== 200) { U.scanQueries.push([JSON.stringify(q0), "http " + r.status, pages, n]); break; }
        const j = JSON.parse(r.text);
        for (const m of j.data || []) { n++; seen.set(m.guid || m.pathway.id + "|" + m.pathway.nonce, m); }
        next = j.nextToken; pages++;
        await sleep(250);
      } while (next && pages < 200);
      U.scanQueries.push([JSON.stringify(q0), "ok", pages, n]);
    }
    const uaSet = new Set(Object.entries(ua).map(([e, a]) => e + "-" + low(a)));
    const readAt = {};
    readAt[ETH_EID] = { block: U.eth.block, time: U.eth.time };
    for (const c of U.chains) readAt[c.eid] = { block: c.block, time: c.time, method: c.method };
    const rows = [];
    for (const m of seen.values()) {
      const p = m.pathway;
      const sKey = p.srcEid + "-" + low(p.sender.address), dKey = p.dstEid + "-" + low(p.receiver.address);
      if (!uaSet.has(sKey) || !uaSet.has(dKey)) continue;
      const s = (m.source || {}).tx || {}, d = (m.destination || {}).tx || {};
      const payload = s.payload || "";
      const amountSD = payload.length >= 82 ? BigInt("0x" + payload.slice(66, 82)) : null;
      const inc = (eid, blk, ts) => {
        const r = readAt[eid];
        if (!r || blk === undefined || blk === null || blk === "") return 0;
        if (r.method && r.method !== "evm" && r.method !== "solana") return ts && r.time && ts * 1000 <= Date.parse(r.time) ? 1 : 0;
        return Number(blk) <= Number(r.block) ? 1 : 0;
      };
      const srcInc = inc(p.srcEid, s.blockNumber, s.blockTimestamp);
      const dstInc = d.blockNumber ? inc(p.dstEid, d.blockNumber, d.blockTimestamp) : 0;
      rows.push([p.srcEid, p.dstEid, p.nonce, s.blockNumber || "", s.blockTimestamp ? new Date(s.blockTimestamp * 1000).toISOString() : "", (m.source || {}).status || "",
        d.blockNumber || "", d.blockTimestamp ? new Date(d.blockTimestamp * 1000).toISOString() : "", (m.destination || {}).status || "", amountSD === null ? "" : amountSD.toString(), srcInc, dstInc]);
    }
    rows.sort((a, b) => String(a[4]).localeCompare(String(b[4])) || a[0] - b[0] || a[2] - b[2]);
    U.files["lzscan_messages.csv"] = csv([["src_eid", "dst_eid", "nonce", "src_block", "src_time_utc", "src_status", "dst_block", "dst_time_utc", "dst_status", "amount_sd", "src_in_read", "dst_in_read"]].concat(rows));
    U.files["lzscan_queries.csv"] = csv([["query", "result", "pages", "messages"]].concat(U.scanQueries));
    U.messagesWindow = { start, end, read_utc: nowIso(), all_messages: seen.size, usde_messages: rows.length };
    U.files["lzscan_window.json"] = JSON.stringify(U.messagesWindow, null, 1) + "\n";
    for (const k of ["lzscan_messages.csv", "lzscan_queries.csv", "lzscan_window.json"]) U.digests[k] = await sha256hex(U.files[k]);
    return U;
  }

  root.USDE_CHAINS = { run, messages, _test: { units, b58, csv, parsePeerLogs, pad32, u32Arg } };
})(typeof window !== "undefined" ? window : globalThis);
