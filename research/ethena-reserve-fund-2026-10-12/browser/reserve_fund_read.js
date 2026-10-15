// reserve_fund_read.js
//
// Reads Ethena's reserve fund, the Safe multisig that Ethena's key addresses page names as the Reserve
// Fund on Ethereum, at one block and at the end of every month since its first transfer, and its whole
// history of token transfers from two explorers.
//
// Paste into the developer console on https://eth.blockscout.com/api/v2/stats , a page that allows
// requests to the RPCs and explorers below, and run
//     window.__rfRun = RESERVE_FUND.run(); await window.__rfRun;
// The files and their SHA-256 digests are left in window.__rf.files and window.__rf.digests.
//
// Every request is read-only, with no login and no key. The script never sends a transaction. It keeps
// no transaction hashes and replaces the address of every counterparty that is not a contract with a
// label such as eoa-3, so the files it writes name no person's account.
(function (root) {
  "use strict";

  const RF = "0x2b5ab59163a6e93b4486f6055d33ca4a115dd4d5"; // Reserve Fund, Ethena's key addresses page
  const NAMED = {
    "0x2b5ab59163a6e93b4486f6055d33ca4a115dd4d5": "Reserve Fund (Ethena)",
    "0x71e4f98e8f20c88112489de3dded4489802a3a87": "sUSDe Payout Fund (Ethena)",
    "0x3b0aaf6e6fcd4a7ceef8c92c32dfea9e64dc1862": "Dev multisig (Ethena)",
    "0xd7fcade52afb60fbf0e1e5f72a683f43820f56a0": "USDe PSM Custodian (Ethena)",
    "0x0000000000000000000000000000000000000000": "zero address",
  };
  // Tokens with a market or a redemption value that the fund held at some time.
  const TOKENS = [
    ["USDC", "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"],
    ["USDT", "0xdac17f958d2ee523a2206206994597c13d831ec7"],
    ["DAI", "0x6b175474e89094c44da98b954eedeac495271d0f"],
    ["sDAI", "0x83f20f44975d03b1b09e64809b757c47f942beea"],
    ["USDS", "0xdc035d45d973e3ec169d2276ddab16f1e407384f"],
    ["sUSDS", "0xa3931d71877c0e7a3148cb7eb4463524fec27fbd"],
    ["USDe", "0x4c9edd5852cd905f086c759e8383e09bff1e68b3"],
    ["sUSDe", "0x9d39a5de30e57443bff2a8307a4256c8797a3497"],
    ["USDtb", "0xc139190f447e929f090edeb554d95abb8b18ac1c"],
    ["BUIDL", "0x7712c34205737192402172409a8f7ccef8aa2aec"],
    ["USTB", "0x43415eb6ff9db7e26a15b704e7a3edce97d31c4e"],
    ["CurveLP", "0xc2921134073151490193ac7369313c8e0b08e1e7"],
  ];
  const VAULTS = ["sDAI", "sUSDS", "sUSDe"]; // ERC-4626 vaults, valued with convertToAssets
  const CURVE = "0xc2921134073151490193ac7369313c8e0b08e1e7"; // Curve USDtb/USDC pool, also its LP token
  const NPM = "0xc36442b4a4522e871399cd717abdd847ab11fe88"; // Uniswap V3 NonfungiblePositionManager
  const UNI_FACTORY = "0x1f98431c8ad98523631ae4a59f267346ea31f984";
  const ETH_USD = "0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419"; // Chainlink ETH / USD
  const ARCHIVE = ["https://eth.drpc.org", "https://gateway.tenderly.co/public/mainnet"];
  const LATEST = ["https://ethereum-rpc.publicnode.com", "https://eth.drpc.org"];
  const BS = "https://eth.blockscout.com";
  const RS = "https://api.routescan.io/v2/network/mainnet/evm/1/etherscan/api";
  const SEL = {
    balanceOf: "0x70a08231", totalSupply: "0x18160ddd", decimals: "0x313ce567", convertToAssets: "0x07a2d13a",
    coins: "0xc6610657", balances: "0x4903b0d1", getVirtualPrice: "0xbb7b8b80", fee: "0xddca3f43",
    getThreshold: "0xe75235b8", getOwners: "0xa0e67e2b", nonce: "0xaffed0e0", VERSION: "0xffa1ad74",
    positions: "0x99fbab88", tokenOfOwnerByIndex: "0x2f745c59", ownerOf: "0x6352211e",
    slot0: "0x3850c7bd", feeGrowthGlobal0X128: "0xf3058399", feeGrowthGlobal1X128: "0x46141319",
    ticks: "0xf30dba93", getPool: "0x1698ee82", latestRoundData: "0xfeaf968c",
  };
  const TOPIC = {
    Transfer: "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
    Deposit: "0xdcbc1c05240f31ff3ad067ef1ee35ce4997762752e3a095284754544f4c709d7",
    Withdraw: "0xfbde797d201c681b91056529119e0b02407c7bb96a4a2c75c01fc9667232c8db",
    IncreaseLiquidity: "0x3067048beee31b25b2f1681f88dac838c8bba36af25bfb2b7cf7473a5847e35f",
    DecreaseLiquidity: "0x26f6a048ee9138f2c0ce266f322cb99228e8d619ae2bff30c67f8dcf9d2377b4",
    Collect: "0x40d0efd1a53d60ecbf40971b9daf7dc90178c3aadc7aab1765632738fa8b8f01",
    CurveAddLiquidity: "0x189c623b666b1b45b83d7178f39b8c087cb09774317ca2f53c2d3c3726f222a2",
  };

  const LOG = [];
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const nowIso = () => new Date().toISOString();
  const low = (s) => String(s).toLowerCase();

  async function fetchText(label, url, opts, timeoutMs) {
    for (let attempt = 0; attempt < 6; attempt++) {
      const ctl = new AbortController();
      const t = setTimeout(() => ctl.abort(), timeoutMs || 25000);
      const started = nowIso();
      try {
        const r = await fetch(url, Object.assign({ cache: "no-store", signal: ctl.signal }, opts || {}));
        const text = await r.text();
        LOG.push([started, label, url.split("?")[0], (opts && opts.method) || "GET", r.status, text.length]);
        if (r.status === 429 || r.status >= 500) { await sleep((r.status === 429 ? 5000 : 1500) * (attempt + 1)); continue; }
        return { status: r.status, text };
      } catch (e) {
        LOG.push([started, label, url.split("?")[0], (opts && opts.method) || "GET", "error " + e.name, 0]);
        await sleep(1500 * (attempt + 1));
      } finally {
        clearTimeout(t);
      }
    }
    return { status: 0, text: "", error: "gave up" };
  }

  async function getJson(label, url) {
    const r = await fetchText(label, url, {}, 30000);
    if (r.status !== 200) throw new Error(label + " http " + r.status);
    return JSON.parse(r.text);
  }

  async function rpc(label, url, method, params) {
    const body = JSON.stringify({ jsonrpc: "2.0", id: 1, method, params });
    for (let attempt = 0; attempt < 3; attempt++) {
      const r = await fetchText(label, url, { method: "POST", headers: { "content-type": "application/json" }, body }, 20000);
      if (r.status !== 200) { await sleep(1000); continue; }
      try {
        const j = JSON.parse(r.text);
        if (j.error) {
          const msg = JSON.stringify(j.error).slice(0, 160);
          if (/rate|limit|too many|timeout/i.test(msg)) { await sleep(2000 * (attempt + 1)); continue; }
          return { err: msg };
        }
        return { ok: j.result };
      } catch (e) {
        await sleep(1000);
      }
    }
    return { err: "no answer" };
  }

  // Runs tasks with at most n at a time.
  async function pool(tasks, n) {
    const out = new Array(tasks.length);
    let next = 0;
    async function worker() {
      while (next < tasks.length) {
        const i = next++;
        out[i] = await tasks[i]();
      }
    }
    const ws = [];
    for (let k = 0; k < Math.min(n, tasks.length); k++) ws.push(worker());
    await Promise.all(ws);
    return out;
  }

  async function sha256hex(text) {
    const buf = new TextEncoder().encode(text);
    const h = await crypto.subtle.digest("SHA-256", buf);
    return Array.from(new Uint8Array(h)).map((b) => b.toString(16).padStart(2, "0")).join("");
  }

  const pad32 = (hexNoPrefix) => hexNoPrefix.toLowerCase().padStart(64, "0");
  const addrArg = (a) => pad32(a.slice(2));
  const uintArg = (n) => pad32(BigInt(n).toString(16));
  function int24Arg(n) {
    const v = BigInt(n);
    return pad32((v < 0n ? (1n << 256n) + v : v).toString(16));
  }
  const word = (hex, i) => "0x" + hex.slice(2 + 64 * i, 2 + 64 * (i + 1));

  function csv(rows) {
    return rows.map((r) => r.map((v) => {
      const s = v === null || v === undefined ? "" : String(v);
      return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
    }).join(",")).join("\n") + "\n";
  }

  // Month ends from January 2024 to the month before the reads, as the last second of each month, UTC.
  function monthEnds(fromYear, fromMonth, untilIso) {
    const out = [];
    let y = fromYear, m = fromMonth;
    for (;;) {
      const next = Date.UTC(m === 12 ? y + 1 : y, m === 12 ? 0 : m, 1) / 1000;
      if (next * 1000 > Date.parse(untilIso)) break;
      out.push({ label: y + "-" + String(m).padStart(2, "0"), ts: next - 1 });
      if (m === 12) { y++; m = 1; } else m++;
    }
    return out;
  }

  // Counterparty labels. Contracts keep their address and explorer name, named Ethena addresses their
  // name, and every other address becomes eoa-N in order of first appearance.
  const LABEL = {};
  let eoaCount = 0;
  const isContract = {};
  const contractName = {};
  function label(addr) {
    const a = low(addr);
    if (NAMED[a]) return a + " " + NAMED[a];
    if (isContract[a] === true) return a + (contractName[a] ? " " + contractName[a] : " contract");
    if (!LABEL[a]) LABEL[a] = "eoa-" + (++eoaCount);
    return LABEL[a];
  }

  async function classifyAddresses(addrs) {
    const todo = addrs.filter((a) => isContract[a] === undefined);
    await pool(todo.map((a) => async () => {
      try {
        const j = await getJson("address " + a.slice(0, 8), BS + "/api/v2/addresses/" + a);
        isContract[a] = !!j.is_contract;
        if (j.name) contractName[a] = String(j.name).replace(/[,\n]/g, " ");
      } catch (e) {
        isContract[a] = null;
      }
    }), 4);
  }

  // ---- history ------------------------------------------------------------------------------------

  async function blockscoutTransfers(U) {
    let items = [], params = "", pages = 0;
    for (;;) {
      const j = await getJson("blockscout transfers", BS + "/api/v2/addresses/" + RF + "/token-transfers" + (params ? "?" + params : ""));
      items = items.concat(j.items || []);
      pages++;
      if (!j.next_page_params || pages > 40) break;
      params = new URLSearchParams(j.next_page_params).toString();
    }
    U.bsItems = items;
    U.bsPages = pages;
    for (const x of items) {
      for (const side of [x.from, x.to]) {
        const a = low(side.hash);
        if (side.is_contract !== undefined && side.is_contract !== null) isContract[a] = !!side.is_contract;
        if (side.name) contractName[a] = String(side.name).replace(/[,\n]/g, " ");
      }
    }
  }

  async function blockscoutFundTxs(U) {
    let items = [], params = "", pages = 0;
    for (;;) {
      const j = await getJson("blockscout transactions", BS + "/api/v2/addresses/" + RF + "/transactions" + (params ? "?" + params : ""));
      items = items.concat(j.items || []);
      pages++;
      if (!j.next_page_params || pages > 40) break;
      params = new URLSearchParams(j.next_page_params).toString();
    }
    // Transactions sent to the Safe, the ones its signers executed.
    U.fundTxs = new Set(items.filter((t) => t.to && low(t.to.hash) === RF).map((t) => low(t.hash)));
    U.fundTxCount = items.length;
    U.fundTxToSafe = U.fundTxs.size;
    U.fundTxFailed = items.filter((t) => t.to && low(t.to.hash) === RF && t.status !== "ok").length;
  }

  async function routescanTransfers(U) {
    U.rs = {};
    for (const action of ["tokentx", "tokennfttx", "token1155tx"]) {
      let all = [];
      for (let page = 1; page <= 5; page++) {
        const j = await getJson("routescan " + action, RS + "?module=account&action=" + action + "&address=" + RF + "&startblock=0&endblock=" + U.block + "&page=" + page + "&offset=1000&sort=asc");
        const res = Array.isArray(j.result) ? j.result : [];
        all = all.concat(res);
        if (res.length < 1000) break;
      }
      U.rs[action] = all;
    }
  }

  // The fund's first transaction was in January 2024, after block 19,000,000.
  const FROM_BLOCK = 19000000;

  // Logs of one contract in one block, from the archive RPC.
  async function blockLogs(label, address, block, topics) {
    const hex = "0x" + block.toString(16);
    const r = await rpc(label, ARCHIVE[0], "eth_getLogs", [{ address, fromBlock: hex, toBlock: hex, topics }]);
    if (!r.ok) throw new Error(label + " " + r.err);
    return r.ok.map((l) => ({ block: parseInt(l.blockNumber, 16), logIndex: parseInt(l.logIndex, 16), topics: l.topics, data: l.data }));
  }

  // The blocks in which the fund's balance of a token changed. The balance is read at 1,025 evenly
  // spaced blocks, about one a day, and every interval whose ends differ is halved until each change
  // is pinned to one block. Used for sDAI, whose deposits and withdrawals emit no Transfer events, so
  // the explorers' transfer lists miss them. A change undone within one interval would not be seen.
  async function balanceChangeBlocks(token, lo, hi) {
    const bal = async (b) => {
      const r = await rpc("bisect " + b, ARCHIVE[0], "eth_call", [{ to: token, data: SEL.balanceOf + addrArg(RF) }, "0x" + b.toString(16)]);
      if (!r.ok) throw new Error("bisect " + r.err);
      return BigInt(r.ok);
    };
    const points = [];
    for (let i = 0; i <= 1024; i++) points.push(Math.round(lo + (hi - lo) * i / 1024));
    const vals = await pool(points.map((b) => () => bal(b)), 8);
    const out = [];
    async function walk(a, va, b, vb) {
      if (va === vb) return;
      if (b - a === 1) { out.push(b); return; }
      const m = Math.floor((a + b) / 2);
      const vm = await bal(m);
      await walk(a, va, m, vm);
      await walk(m, vm, b, vb);
    }
    for (let i = 0; i < 1024; i++) await walk(points[i], vals[i], points[i + 1], vals[i + 1]);
    return out;
  }

  async function eventLogs(U) {
    const rf32 = "0x" + addrArg(RF);
    const sdai = TOKENS.find((t) => t[0] === "sDAI")[1];
    const susds = TOKENS.find((t) => t[0] === "sUSDS")[1];
    U.events = [];
    U.eventQueries = [];
    const timeOf = {};
    for (const x of U.bsItems) timeOf[x.block_number] = Date.parse(x.timestamp) / 1000;
    const names = {};
    names[TOPIC.Deposit] = "Deposit";
    names[TOPIC.Withdraw] = "Withdraw";
    names[TOPIC.IncreaseLiquidity] = "IncreaseLiquidity";
    names[TOPIC.DecreaseLiquidity] = "DecreaseLiquidity";
    names[TOPIC.Collect] = "Collect";
    names[TOPIC.CurveAddLiquidity] = "AddLiquidity";
    // Every log of a kind in the given blocks. A block that fails is counted in run.json.
    const collect = async (prefix, contract, blocks, topics, keep) => {
      let rows = 0, failed = 0;
      for (const b of blocks) {
        try {
          for (const l of await blockLogs(prefix + " " + b, contract, b, topics)) {
            if (keep && !keep(l)) continue;
            const kind = prefix + " " + names[l.topics[0]] + (prefix === "NPM" ? " " + BigInt(l.topics[1]).toString() : "");
            U.events.push({ kind, contract, block: l.block, time: timeOf[l.block] || "", logIndex: l.logIndex, topics: l.topics.slice(1), data: l.data });
            rows++;
          }
        } catch (e) {
          failed++;
        }
      }
      U.eventQueries.push([prefix + " in " + blocks.length + " blocks", failed ? "failed in " + failed + " blocks" : "ok", rows]);
    };
    const tokenBlocks = (addr) => [...new Set(U.bsItems.filter((x) => low(x.token.address_hash) === addr).map((x) => x.block_number))].sort((a, b) => a - b);
    // sDAI, in the blocks where the fund's sDAI balance changed.
    const sdaiBlocks = await balanceChangeBlocks(sdai, FROM_BLOCK, U.block);
    U.sdaiBlocks = sdaiBlocks;
    await collect("sDAI", sdai, sdaiBlocks, [[TOPIC.Deposit, TOPIC.Withdraw]],
      (l) => l.topics.slice(1).some((t) => low(t) === rf32));
    // sUSDS, in the blocks of the fund's sUSDS transfers.
    await collect("sUSDS", susds, tokenBlocks(susds), [[TOPIC.Deposit, TOPIC.Withdraw]],
      (l) => l.topics.slice(1).some((t) => low(t) === rf32));
    // Curve, in the blocks of the fund's LP token transfers.
    await collect("Curve", CURVE, tokenBlocks(CURVE), [TOPIC.CurveAddLiquidity, rf32]);
    // Uniswap positions, in the blocks where the fund moved tokens to or from the pool or received a
    // position.
    const uniBlocks = [];
    for (const x of U.bsItems) {
      const cp = low(x.to.hash) === RF ? low(x.from.hash) : low(x.to.hash);
      if (cp === low(U.uniPool) || low(x.token.address_hash) === NPM) uniBlocks.push(x.block_number);
    }
    await collect("NPM", NPM, [...new Set(uniBlocks)].sort((a, b) => a - b),
      [[TOPIC.IncreaseLiquidity, TOPIC.DecreaseLiquidity, TOPIC.Collect], U.positionIds.map((id) => "0x" + uintArg(id))]);
    // Block times for events in blocks with no transfer of the fund.
    for (const e of U.events) {
      if (e.time === "") {
        const h = await blockAt(ARCHIVE[0], "0x" + e.block.toString(16));
        e.time = h ? h.time : "";
      }
    }
  }

  // The last block at or before a time, from block headers on the archive RPC. Starts from an estimate
  // at 12 seconds a block and steps until the block is at or before the time and the next one after it.
  async function blockByTime(ts, ref) {
    const head = async (b) => {
      const r = await blockAt(ARCHIVE[0], "0x" + b.toString(16));
      if (!r) throw new Error("header " + b);
      return r.time;
    };
    let b = ref.number - Math.ceil((ref.time - ts) / 12);
    let t = await head(b);
    for (let i = 0; i < 40; i++) {
      if (t > ts) { b -= Math.max(1, Math.floor((t - ts) / 12)); t = await head(b); continue; }
      const tn = await head(b + 1);
      if (tn <= ts) { b += Math.max(1, Math.floor((ts - tn) / 12) + 1); t = await head(b); continue; }
      return b;
    }
    throw new Error("block by time " + ts);
  }

  // An event's topics and data with addresses replaced by labels. NPM topics are token IDs. The
  // recipient of a Collect, the first word of its data, is replaced the same way.
  function eventRow(e) {
    const npm = e.kind.indexOf("NPM ") === 0;
    const topics = e.topics.map((t) => (npm ? BigInt(t).toString() : label("0x" + t.slice(26))));
    while (topics.length < 3) topics.push("");
    let data = e.data, recipient = "";
    if (e.kind.indexOf("NPM Collect") === 0) {
      recipient = label("0x" + data.slice(26, 66));
      data = "0x" + "0".repeat(64) + data.slice(66);
    }
    return [e.kind, e.contract, e.block, e.time, e.logIndex, topics[0], topics[1], topics[2], recipient, data];
  }

  // ---- reads at a block ----------------------------------------------------------------------------

  // The calls made at every block. Each is [label, to, data]. Positions, pool and tick calls are added
  // after the first round, from what it returns.
  function baseCalls(U) {
    const calls = [];
    for (const [sym, addr] of TOKENS) calls.push(["balanceOf " + sym, addr, SEL.balanceOf + addrArg(RF)]);
    calls.push(["totalSupply USDe", TOKENS.find((t) => t[0] === "USDe")[1], SEL.totalSupply]);
    calls.push(["totalSupply USDtb", TOKENS.find((t) => t[0] === "USDtb")[1], SEL.totalSupply]);
    calls.push(["Curve balances 0", CURVE, SEL.balances + uintArg(0)]);
    calls.push(["Curve balances 1", CURVE, SEL.balances + uintArg(1)]);
    calls.push(["Curve totalSupply", CURVE, SEL.totalSupply]);
    calls.push(["Chainlink ETH/USD latestRoundData", ETH_USD, SEL.latestRoundData]);
    for (const id of U.positionIds) calls.push(["positions " + id, NPM, SEL.positions + uintArg(id)]);
    return calls;
  }

  async function readAt(url, blockHex, calls) {
    return pool(calls.map((c) => async () => {
      const r = await rpc(c[0], url, "eth_call", [{ to: c[1], data: c[2] }, blockHex]);
      return [c[0], c[1], c[2], r.ok !== undefined ? r.ok : "error " + r.err];
    }), 5);
  }

  // Second round at a block: vault conversions of the balances read, and the Uniswap pool and ticks of
  // any position with liquidity.
  function secondCalls(U, first) {
    const get = (lbl) => { const r = first.find((x) => x[0] === lbl); return r ? r[3] : null; };
    const calls = [];
    for (const v of VAULTS) {
      const bal = get("balanceOf " + v);
      if (bal && /^0x[0-9a-f]+$/i.test(bal) && BigInt(bal) > 0n) {
        calls.push(["convertToAssets " + v, TOKENS.find((t) => t[0] === v)[1], SEL.convertToAssets + pad32(BigInt(bal).toString(16))]);
      }
    }
    let anyLiquidity = false;
    for (const id of U.positionIds) {
      const p = get("positions " + id);
      if (!p || !/^0x[0-9a-f]+$/i.test(p) || p.length < 2 + 64 * 12) continue;
      const liq = BigInt(word(p, 7));
      if (liq === 0n) continue;
      anyLiquidity = true;
      const tl = Number(BigInt.asIntN(24, BigInt(word(p, 5))));
      const tu = Number(BigInt.asIntN(24, BigInt(word(p, 6))));
      calls.push(["ticks " + tl, U.uniPool, SEL.ticks + int24Arg(tl)]);
      calls.push(["ticks " + tu, U.uniPool, SEL.ticks + int24Arg(tu)]);
    }
    if (anyLiquidity) {
      calls.push(["Uniswap slot0", U.uniPool, SEL.slot0]);
      calls.push(["Uniswap feeGrowthGlobal0X128", U.uniPool, SEL.feeGrowthGlobal0X128]);
      calls.push(["Uniswap feeGrowthGlobal1X128", U.uniPool, SEL.feeGrowthGlobal1X128]);
    }
    // One call per label.
    const seen = {};
    return calls.filter((c) => (seen[c[0]] ? false : (seen[c[0]] = true)));
  }

  async function blockAt(url, blockHex) {
    const r = await rpc("block " + blockHex, url, "eth_getBlockByNumber", [blockHex, false]);
    if (!r.ok) return null;
    return { number: parseInt(r.ok.number, 16), time: parseInt(r.ok.timestamp, 16), hash: r.ok.hash };
  }

  async function fullRead(U, url, blockHex) {
    const first = await readAt(url, blockHex, baseCalls(U));
    const second = await readAt(url, blockHex, secondCalls(U, first));
    const eth = await rpc("eth balance", url, "eth_getBalance", [RF, blockHex]);
    const b = await blockAt(url, blockHex);
    const rows = first.concat(second);
    rows.push(["eth_getBalance", RF, "", eth.ok !== undefined ? eth.ok : "error " + eth.err]);
    return { block: b, rows };
  }

  // The canonical text whose SHA-256 compares two sources' answers at one block.
  function canon(rows) {
    return rows.map((r) => r[0] + "=" + r[3]).sort().join("\n");
  }

  // ---- main -----------------------------------------------------------------------------------------

  async function run() {
    const U = { started: nowIso(), files: {}, digests: {} };
    root.__rf = U;
    // The read block, a few blocks behind the head so that both RPCs serve it.
    const head = await rpc("head", LATEST[0], "eth_blockNumber", []);
    U.block = parseInt(head.ok, 16) - 3;
    const blockHex = "0x" + U.block.toString(16);

    // Uniswap V3 positions held by the fund and their pool.
    const nftBal = await rpc("npm balance", LATEST[0], "eth_call", [{ to: NPM, data: SEL.balanceOf + addrArg(RF) }, blockHex]);
    const nPos = Number(BigInt(nftBal.ok));
    U.positionIds = [];
    for (let i = 0; i < nPos; i++) {
      const r = await rpc("npm index " + i, LATEST[0], "eth_call", [{ to: NPM, data: SEL.tokenOfOwnerByIndex + addrArg(RF) + uintArg(i) }, blockHex]);
      U.positionIds.push(Number(BigInt(r.ok)));
    }
    U.positionIds.sort((a, b) => a - b);
    const p0 = await rpc("position 0", LATEST[0], "eth_call", [{ to: NPM, data: SEL.positions + uintArg(U.positionIds[0]) }, blockHex]);
    const t0 = "0x" + word(p0.ok, 2).slice(26), t1 = "0x" + word(p0.ok, 3).slice(26), fee = BigInt(word(p0.ok, 4));
    const gp = await rpc("getPool", LATEST[0], "eth_call", [{ to: UNI_FACTORY, data: SEL.getPool + addrArg(t0) + addrArg(t1) + pad32(fee.toString(16)) }, blockHex]);
    U.uniPool = "0x" + gp.ok.slice(26);
    U.uniPoolTokens = [t0, t1, Number(fee)];

    // Snapshot on two RPCs at the same block.
    U.snapshot = {};
    for (const url of LATEST) U.snapshot[url] = await fullRead(U, url, blockHex);
    // The Safe, the NFT owners and the pool's coins, once, at the read block.
    const safeRows = [];
    for (const [lbl, data] of [["getThreshold", SEL.getThreshold], ["nonce", SEL.nonce], ["VERSION", SEL.VERSION]]) {
      const r = await rpc(lbl, LATEST[0], "eth_call", [{ to: RF, data }, blockHex]);
      safeRows.push([lbl, RF, data, r.ok !== undefined ? r.ok : "error " + r.err]);
    }
    const owners = await rpc("getOwners", LATEST[0], "eth_call", [{ to: RF, data: SEL.getOwners }, blockHex]);
    // Only the number of owners is kept. Their addresses are people's accounts.
    safeRows.push(["getOwners count", RF, SEL.getOwners, owners.ok ? String(Number(BigInt(word(owners.ok, 1)))) : "error"]);
    for (const id of U.positionIds) {
      const r = await rpc("ownerOf " + id, LATEST[0], "eth_call", [{ to: NPM, data: SEL.ownerOf + uintArg(id) }, blockHex]);
      safeRows.push(["ownerOf " + id, NPM, SEL.ownerOf + uintArg(id), r.ok]);
    }
    for (const i of [0, 1]) {
      const r = await rpc("coins " + i, LATEST[0], "eth_call", [{ to: CURVE, data: SEL.coins + uintArg(i) }, blockHex]);
      safeRows.push(["Curve coins " + i, CURVE, SEL.coins + uintArg(i), r.ok]);
    }
    for (const [sym, addr] of TOKENS) {
      const r = await rpc("decimals " + sym, LATEST[0], "eth_call", [{ to: addr, data: SEL.decimals }, blockHex]);
      safeRows.push(["decimals " + sym, addr, SEL.decimals, r.ok]);
    }
    U.once = safeRows;

    // History.
    await blockscoutTransfers(U);
    await blockscoutFundTxs(U);
    await routescanTransfers(U);
    await eventLogs(U);

    // Month ends, on two archive RPCs.
    const firstTransfer = U.bsItems.map((x) => x.timestamp).sort()[0];
    const fy = Number(firstTransfer.slice(0, 4)), fm = Number(firstTransfer.slice(5, 7));
    U.months = monthEnds(fy, fm, new Date(U.snapshot[LATEST[0]].block.time * 1000).toISOString());
    const ref = U.snapshot[LATEST[0]].block;
    for (const m of U.months) m.block = await blockByTime(m.ts, ref);
    U.monthReads = {};
    for (const url of ARCHIVE) {
      U.monthReads[url] = {};
      for (const m of U.months) {
        U.monthReads[url][m.label] = await fullRead(U, url, "0x" + m.block.toString(16));
        if (url === ARCHIVE[0]) {
          const nb = await blockAt(url, "0x" + (m.block + 1).toString(16));
          m.nextTime = nb ? nb.time : "";
        }
      }
    }

    // Labels for every counterparty.
    const cps = new Set();
    for (const x of U.bsItems) { cps.add(low(x.from.hash)); cps.add(low(x.to.hash)); }
    for (const a of Object.keys(U.rs)) for (const x of U.rs[a]) { cps.add(low(x.from)); cps.add(low(x.to)); }
    for (const e of U.events) {
      if (e.kind.indexOf("NPM ") !== 0) for (const t of e.topics) cps.add(low("0x" + t.slice(26)));
      if (e.kind.indexOf("NPM Collect") === 0) cps.add(low("0x" + e.data.slice(26, 66)));
    }
    await classifyAddresses([...cps]);
    U.finished = nowIso();
    await writeFiles(U);
    return { block: U.block, months: U.months.length, transfers: U.bsItems.length, finished: U.finished };
  }

  async function writeFiles(U) {
    const f = U.files;
    const txIds = {};
    let txCount = 0;
    const txId = (h) => { const k = low(h); if (!txIds[k]) txIds[k] = "tx-" + (++txCount); return txIds[k]; };
    // A counterparty is written as its address if it is a contract or a named Ethena address, and as
    // its eoa-N label otherwise. counterparties.csv gives each one's explorer name.
    const who = (addr) => { const l = label(addr); return l.indexOf("eoa-") === 0 ? l : low(addr); };
    const seenCp = {};
    const tokens = {};
    // Blockscout, one row per token transfer, oldest first.
    const bsRows = U.bsItems.slice().sort((a, b) => a.block_number - b.block_number || a.log_index - b.log_index).map((x) => {
      const tok = low(x.token.address_hash);
      tokens[tok] = [tok, (x.token.symbol || "").replace(/[,\n]/g, " "), x.token.decimals || "", x.token.type];
      for (const s of [x.from.hash, x.to.hash]) seenCp[who(s)] = label(s);
      return [x.block_number, x.log_index, Date.parse(x.timestamp) / 1000, txId(x.transaction_hash), U.fundTxs.has(low(x.transaction_hash)) ? 1 : 0,
        tok, x.total && x.total.value !== undefined ? x.total.value : "", x.total && x.total.token_id !== undefined ? x.total.token_id : "",
        who(x.from.hash), who(x.to.hash)];
    });
    const head = ["block", "log_index", "time_unix", "tx", "tx_sent_to_fund", "token", "value_raw", "token_id", "from", "to"];
    f["transfers_blockscout.csv"] = csv([head].concat(bsRows));
    // Routescan, the same columns.
    const rsRows = [];
    for (const action of Object.keys(U.rs)) {
      for (const x of U.rs[action]) {
        const tok = low(x.contractAddress);
        if (!tokens[tok]) tokens[tok] = [tok, (x.tokenSymbol || "").replace(/[,\n]/g, " "), x.tokenDecimal || "", action];
        for (const s of [x.from, x.to]) seenCp[who(s)] = label(s);
        rsRows.push([Number(x.blockNumber), x.logIndex !== undefined && x.logIndex !== "" ? Number(x.logIndex) : "", Number(x.timeStamp), txId(x.hash),
          U.fundTxs.has(low(x.hash)) ? 1 : 0, tok, action === "tokentx" ? x.value : (x.tokenValue || ""), x.tokenID || "", who(x.from), who(x.to)]);
      }
    }
    rsRows.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    f["transfers_routescan.csv"] = csv([head].concat(rsRows));
    f["tokens.csv"] = csv([["token", "symbol", "decimals", "type"]].concat(Object.values(tokens).sort((a, b) => (a[0] < b[0] ? -1 : 1))));
    // Event logs.
    const evRows = U.events.slice().sort((a, b) => a.block - b.block || a.logIndex - b.logIndex).map(eventRow);
    f["events.csv"] = csv([["event", "contract", "block", "time_unix", "log_index", "topic1", "topic2", "topic3", "collect_recipient", "data"]].concat(evRows));
    for (const e of evRows) for (const v of [e[5], e[6], e[7], e[8]]) if (/^0x[0-9a-f]{40} |^eoa-/.test(v)) seenCp[v.split(" ")[0]] = v;
    f["counterparties.csv"] = csv([["counterparty", "label"]].concat(Object.keys(seenCp).sort().map((k) => [k, seenCp[k]])));
    // Reads.
    const readRows = [];
    const snapBlocks = {};
    for (const url of Object.keys(U.snapshot)) {
      const s = U.snapshot[url];
      snapBlocks[url] = s.block;
      for (const r of s.rows) readRows.push([url, r[0], r[3]]);
    }
    f["snapshot_reads.csv"] = csv([["rpc", "call", "result"]].concat(readRows));
    f["once_reads.csv"] = csv([["call", "to", "data", "result"]].concat(U.once));
    const primary = ARCHIVE[0], second = ARCHIVE[1];
    const mRows = [], mSum = [];
    for (const m of U.months) {
      const a = U.monthReads[primary][m.label], b = U.monthReads[second][m.label];
      for (const r of a.rows) mRows.push([m.label, r[0], r[3]]);
      const da = await sha256hex(canon(a.rows)), db = await sha256hex(canon(b.rows));
      mSum.push([m.label, m.ts, m.block, a.block.number, a.block.time, m.nextTime, a.block.hash, b.block.number, b.block.hash, da, db, da === db ? 1 : 0]);
    }
    f["month_reads.csv"] = csv([["month", "call", "result"]].concat(mRows));
    f["month_sources.csv"] = csv([["month", "month_end_unix", "block_by_time", "block_primary", "block_time_unix", "next_block_time_unix", "hash_primary", "block_second", "hash_second", "sha256_primary", "sha256_second", "same"]].concat(mSum));
    // Requests, counted by host, label kind and status, with every request that did not return 200.
    const counts = {};
    const failed = [];
    for (const r of LOG) {
      const host = r[2].split("/")[2] || r[2];
      const kind = String(r[1]).split(" ")[0];
      const k = host + "|" + kind + "|" + r[3] + "|" + r[4];
      counts[k] = counts[k] || [host, kind, r[3], r[4], 0, r[0], r[0]];
      counts[k][4]++;
      if (r[0] < counts[k][5]) counts[k][5] = r[0];
      if (r[0] > counts[k][6]) counts[k][6] = r[0];
      if (r[4] !== 200) failed.push(r);
    }
    f["request_summary.csv"] = csv([["host", "label", "method", "status", "requests", "first_utc", "last_utc"]].concat(Object.values(counts)));
    f["request_failures.csv"] = csv([["time_utc", "label", "url", "method", "status", "bytes"]].concat(failed));
    f["run.json"] = JSON.stringify({
      reserve_fund: RF, read_block: U.block, snapshot_blocks: snapBlocks, started_utc: U.started, finished_utc: U.finished,
      latest_rpcs: LATEST, archive_rpcs: ARCHIVE, uniswap_pool: U.uniPool, uniswap_pool_tokens: U.uniPoolTokens,
      position_ids: U.positionIds, blockscout_pages: U.bsPages, blockscout_transfers: U.bsItems.length,
      routescan: Object.fromEntries(Object.keys(U.rs).map((k) => [k, U.rs[k].length])),
      fund_transactions: U.fundTxCount, fund_transactions_sent_to_safe: U.fundTxToSafe, failed_safe_transactions: U.fundTxFailed,
      counterparties_not_contracts: eoaCount, transactions_labelled: txCount, months: U.months.length, requests: LOG.length,
      event_queries: U.eventQueries,
    }, null, 1) + "\n";
    for (const k of Object.keys(f)) U.digests[k] = await sha256hex(f[k]);
  }

  root.RESERVE_FUND = { run, _test: { csv, monthEnds, int24Arg, uintArg, addrArg, word, canon, writeFiles, eventRow, label, isContract, contractName, secondCalls, baseCalls } };
})(typeof window !== "undefined" ? window : globalThis);
