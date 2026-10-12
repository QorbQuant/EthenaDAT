/*
 avax_usde_read.cjs

 How much of the USDe on Avalanche C-Chain sits in EthenaPay wallets, at the end of each UTC day from the day the
 token was deployed on Avalanche, August 8, 2025, to October 11, 2026. It reads from the Routescan explorer API.

   1. Every contract the two EthenaPay wallet factories created with CREATE2                 (txlistinternal)
   2. Every USDe Transfer log from the token's deployment to the last block of October 11 UTC (getLogs)
   3. The receipt of every transaction the explorer lists a Transfer log for but gives no
      value or block hash, to show that the log is not in the transaction                   (eth_getTransactionReceipt)
   4. USDe's totalSupply() at the latest block, and the mints and burns after October 11,
      to tie the day-by-day count to the contract                                           (eth_call, getLogs)

 It writes daily.csv, holders.csv, flows.csv and meta.json. Wallets and other holders appear only as counts, ranks
 and the labels below. No wallet's address is written.

 Run it with Node 18 or later:   node avax_usde_read.cjs
 The same code runs unchanged in a browser console on a page of the explorer API, as
 AUR.run(fetch.bind(window), console.log), which returns the files as text. The files used were read with a fetch that
 skips the browser's cache, AUR.run(u => fetch(u, { cache: 'no-store' }), log). main() below calls the same run() and
 only adds the write to disk.

 Rules
   EthenaPay wallet   a contract one of the two factories created with CREATE2, the rule of the chain recount
                      published with the site's EthenaPay adoption review
   settlement         the two addresses card payments go to, the recount's current and retired settlement addresses
   reward accounts    the account the EthenaPay dashboard's daily query labels yield and the two it labels other
                      rewards
   settlement recipients  accounts outside the programme whose every USDe, to the end of October 11, came from a
                      settlement address
   mint, burn         a Transfer from the zero address, a Transfer to it
   supply             USDe minted less USDe burned
   flows              USDe moved between groups, the labeled contracts each counted as a group of their own, before
                      the UTC day of the first wallet, from it to the last day of the published recount, October 5,
                      and after it
   day                midnight to midnight UTC
   phantom record     a Transfer log the explorer lists with an empty value or an empty block hash. Each one is
                      checked against its transaction's receipt and left out when the receipt does not hold it
*/
globalThis.AUR = (() => {
  'use strict';
  const API = 'https://api.routescan.io/v2/network/mainnet/evm/43114/etherscan/api';
  const USDE = '0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34';
  const TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef';
  const ZERO = '0x0000000000000000000000000000000000000000';
  const FACTORIES = ['0x313be708df16979d9e5fe9db5ac4969b8add7207',     // v1 pilot factory
                     '0xac66ca9a79fb0d3c64cba44cd29610cd58602d6f'];    // v2 current factory
  const SETTLE = ['0x6070848bd19c37488d0516058f2933dd992733de',        // current settlement address
                  '0x3b3ffd99b87a2dee5ad244b75d5a8e266890fdb8'];       // retired settlement address
  const REWARDS = ['0xd0ec8cc7414f27ce85f8dece6b4a58225f273311',       // labeled yield in the dashboard's query
                   '0xab2b06efa6179e624f5e3b08b64978df114ff24f',       // labeled other rewards
                   '0xc9dd0d4351d3841a712f59cb4f1e88c3d500515b'];      // the pilot's other-reward account
  const DEPLOY_BLOCK = 66748921;     // the block of the transaction that created USDe on Avalanche, August 8, 2025
  const FACTORY_START = 85400000;    // before the first factory call on May 15, 2026, the recount's first block
  const END_BLOCK = 97318132;        // last block of October 11, 2026 UTC
  const DAY = 86400;
  const utc = (y, m, d, hh, mm, ss) => Date.UTC(y, m - 1, d, hh || 0, mm || 0, ss || 0) / 1000;
  const CUTOFF = utc(2026, 10, 12);  // the first second after the last day counted
  const RECOUNT_END = utc(2026, 10, 6);   // the first second after the last day of the published recount
  // Other holders the article names, with where each name comes from
  const LABELS = {
    '0x5e023c31e1d3dcd08a1b3e8c96f6ef8aa8fcacd1': 'rhino.fi bridge contract',   // rhino.fi's bridge configuration API gives it as the Avalanche contract
    '0x833e0ff43a8691f623cb8730ddb3e3180c7de08b': 'UniswapV3Pool contract',     // the contract name in the explorer's verified source
  };
  const FLOW_KEYS = {                // the same two contracts as groups in flows.csv
    '0x5e023c31e1d3dcd08a1b3e8c96f6ef8aa8fcacd1': 'rhino_fi_bridge_contract',
    '0x833e0ff43a8691f623cb8730ddb3e3180c7de08b': 'uniswap_v3_pool',
  };
  const FLOW_ORDER = ['minted', 'ethenapay_wallets', 'settlement', 'reward_accounts', 'settlement_recipients',
                      'rhino_fi_bridge_contract', 'uniswap_v3_pool', 'other_accounts', 'burned'];
  const TOP_OTHERS = 10;             // holders of each kind listed one by one in holders.csv, by balance at END_BLOCK
  const SEGMENT = 400000;            // blocks per request series when the log is read in parallel
  const CFG = { retryMs: 900, parallel: 4, tieWaitMs: 30000 };

  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const iso = t => new Date(t * 1000).toISOString().slice(0, 19) + 'Z';
  const dateOf = t => new Date(t * 1000).toISOString().slice(0, 10);
  const pad = a => '0x' + a.slice(2).toLowerCase().padStart(64, '0');
  const addrOf = topic => '0x' + String(topic).slice(26).toLowerCase();

  async function sha256hex(str) {
    const bytes = new TextEncoder().encode(str);
    const subtle = (globalThis.crypto && globalThis.crypto.subtle) || require('crypto').webcrypto.subtle;
    const d = await subtle.digest('SHA-256', bytes);
    return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, '0')).join('');
  }

  // ---------------------------------------------------------------- reading the chain
  function makeApi(fetchFn) {
    async function raw(params) {
      const u = API + '?' + Object.entries(params).map(([k, v]) => k + '=' + v).join('&');
      for (let i = 0; i < 6; i++) {
        try {
          const r = await fetchFn(u);
          if (r.ok) return await r.json();
        } catch (e) { /* retry */ }
        await sleep(CFG.retryMs * (i + 1));
      }
      throw new Error('request failed: ' + u.slice(API.length, API.length + 200));
    }
    async function list(params) {
      for (let i = 0; i < 6; i++) {
        const j = await raw(params);
        if (Array.isArray(j.result)) return j.result;
        if (j.message === 'No records found' || j.result === null) return [];
        await sleep(CFG.retryMs * (i + 1));
      }
      throw new Error('no list for ' + JSON.stringify(params).slice(0, 200));
    }
    return { raw, list };
  }

  // Pages through a block range. A full page is cut back to the blocks below its last block, which the next request
  // asks for again, so no block is split between two pages.
  async function walk(list, paramsFor, pageSize, blockOf, onRow, label, log, start, end) {
    let from = start, total = 0, span = end - start + 1;
    while (from <= end) {
      const to = Math.min(end, from + span - 1);
      let rows;
      try { rows = await list(paramsFor(from, to)); } catch (e) {
        if (span <= 5000) throw e;
        span = Math.ceil(span / 4);
        if (log) log(label + ': no answer for blocks ' + from + ' to ' + to + ', now asking for ' + span + ' blocks at a time');
        continue;
      }
      for (let i = 1; i < rows.length; i++) if (blockOf(rows[i]) < blockOf(rows[i - 1])) throw new Error(label + ': page is not in block order');
      for (const r of rows) if (blockOf(r) < from || blockOf(r) > to) throw new Error(label + ': row outside the requested blocks');
      let keep = rows, next = to + 1;
      if (rows.length >= pageSize) {
        const lastBlk = blockOf(rows[rows.length - 1]);
        if (blockOf(rows[0]) === lastBlk) throw new Error(label + ': one block fills a whole page at ' + lastBlk);
        keep = rows.filter(r => blockOf(r) < lastBlk);
        next = lastBlk;
      }
      for (const r of keep) onRow(r);
      total += keep.length;
      from = next;
    }
    if (log) log(label + ' ' + total + ' rows');
    return total;
  }

  function logRow(r) {
    const ed = !r.data || r.data === '0x', eb = !r.blockHash, empty = ed || eb;
    return {
      ed, eb, b: parseInt(r.blockNumber, 16), li: parseInt(r.logIndex, 16), ts: parseInt(r.timeStamp, 16),
      f: addrOf(r.topics[1]), t: addrOf(r.topics[2]), v: empty ? null : BigInt(r.data),
      h: String(r.transactionHash).toLowerCase(), topic0: String(r.topics[0]).toLowerCase(), addr: String(r.address).toLowerCase(),
    };
  }

  async function readLogs(list, extra, start, end, label, log) {
    const segs = [];
    for (let a = start; a <= end; a += SEGMENT) segs.push([a, Math.min(end, a + SEGMENT - 1)]);
    const out = new Array(segs.length);
    let next = 0, done = 0;
    const worker = async () => {
      while (next < segs.length) {
        const k = next++, [a, b] = segs[k], rows = [];
        await walk(list, (from, to) => Object.assign({ module: 'logs', action: 'getLogs', address: USDE, fromBlock: from, toBlock: to, topic0: TRANSFER }, extra, { page: 1, offset: 1000 }),
          1000, r => parseInt(r.blockNumber, 16), r => rows.push(logRow(r)), label + ' ' + a, null, a, b);
        out[k] = rows;
        done++;
        if (log && done % 10 === 0) log(label + ': ' + done + ' of ' + segs.length + ' block ranges read');
      }
    };
    await Promise.all(Array.from({ length: CFG.parallel }, worker));
    const rows = out.flat();
    for (const r of rows) if (r.topic0 !== TRANSFER || r.addr !== USDE) throw new Error(label + ': log does not match the filter');
    if (log) log(label + ' ' + rows.length + ' logs');
    return rows;
  }

  async function load(fetchFn, log) {
    const { raw, list } = makeApi(fetchFn);
    const S = { counts: {} };
    const blockTs = async b => {
      const j = await raw({ module: 'proxy', action: 'eth_getBlockByNumber', tag: '0x' + b.toString(16), boolean: 'false' });
      if (!j || !j.result || !j.result.timestamp) throw new Error('no timestamp for block ' + b);
      return parseInt(j.result.timestamp, 16);
    };
    const endTs = await blockTs(END_BLOCK), nextTs = await blockTs(END_BLOCK + 1);
    if (!(endTs < CUTOFF && nextTs >= CUTOFF)) throw new Error('block ' + END_BLOCK + ' is not the last block of October 11 UTC');
    S.counts.end_block_time = iso(endTs); S.counts.next_block_time = iso(nextTs);
    // the token's deployment
    const cr = await raw({ module: 'contract', action: 'getcontractcreation', contractaddresses: USDE });
    const ctx = await raw({ module: 'proxy', action: 'eth_getTransactionByHash', txhash: cr.result[0].txHash });
    if (parseInt(ctx.result.blockNumber, 16) !== DEPLOY_BLOCK) throw new Error('USDe was not created in block ' + DEPLOY_BLOCK);
    S.counts.deploy_block_time = iso(await blockTs(DEPLOY_BLOCK));
    // EthenaPay wallets
    S.wallets = new Map(); S.factoryOther = []; S.factoryOtherRows = 0;
    for (let g = 0; g < FACTORIES.length; g++) {
      const f = FACTORIES[g];
      S.counts['factory' + g + '_rows'] = await walk(list,
        (from, to) => ({ module: 'account', action: 'txlistinternal', address: f, startblock: from, endblock: to, page: 1, offset: 10000, sort: 'asc' }),
        10000, r => Number(r.blockNumber), r => {
          if (String(r.from).toLowerCase() !== f || !r.contractAddress || String(r.isError) !== '0') { S.factoryOtherRows++; return; }
          if (String(r.type).toLowerCase() === 'create2') S.wallets.set(r.contractAddress.toLowerCase(), Number(r.timeStamp));
          else S.factoryOther.push({ factory: f, type: String(r.type).toLowerCase(), address: r.contractAddress.toLowerCase(), block: Number(r.blockNumber) });
        }, 'factory ' + g, log, FACTORY_START, END_BLOCK);
    }
    // every USDe Transfer log to the end of October 11
    S.logs = await readLogs(list, {}, DEPLOY_BLOCK, END_BLOCK, 'transfer logs', log);
    // receipts of the records with no value or block hash
    S.phantoms = [];
    for (const r of S.logs.filter(x => x.v === null)) {
      const j = await raw({ module: 'proxy', action: 'eth_getTransactionReceipt', txhash: r.h });
      const rc = j && j.result;
      if (!rc || !Array.isArray(rc.logs)) throw new Error('no receipt for a record at block ' + r.b);
      const inReceipt = rc.logs.some(x => String(x.address).toLowerCase() === USDE && String(x.topics[0]).toLowerCase() === TRANSFER
        && parseInt(x.logIndex, 16) === r.li && addrOf(x.topics[1]) === r.f && addrOf(x.topics[2]) === r.t);
      S.phantoms.push({ b: r.b, li: r.li, ts: r.ts, f: r.f, t: r.t, receipt_block: parseInt(rc.blockNumber, 16), in_receipt: inReceipt,
                        receipt_usde_transfers: rc.logs.filter(x => String(x.address).toLowerCase() === USDE && String(x.topics[0]).toLowerCase() === TRANSFER).length });
    }
    if (log) log('checked ' + S.phantoms.length + ' records with no value against their receipts');
    // the contract's totalSupply now, and the mints and burns after October 11 up to that block. The explorer answers a
    // repeated request for the latest state from a cache, so these three requests carry the time as an extra parameter,
    // and the logs are read after a pause that lets the explorer's log index reach the block
    const now = () => ({ nc: Date.now() });
    for (let i = 0; i < 6; i++) {
      const b1 = parseInt((await raw(Object.assign({ module: 'proxy', action: 'eth_blockNumber' }, now()))).result, 16);
      const ts = BigInt((await raw(Object.assign({ module: 'proxy', action: 'eth_call', to: USDE, data: '0x18160ddd', tag: 'latest' }, now()))).result);
      const b2 = parseInt((await raw(Object.assign({ module: 'proxy', action: 'eth_blockNumber' }, now()))).result, 16);
      await sleep(CFG.tieWaitMs);
      const mints = await readLogs(list, { topic0_1_opr: 'and', topic1: pad(ZERO) }, END_BLOCK + 1, b2, 'mints after the cutoff', null);
      const burns = await readLogs(list, { topic0_2_opr: 'and', topic2: pad(ZERO) }, END_BLOCK + 1, b2, 'burns after the cutoff', null);
      const between = [...mints, ...burns].filter(x => x.v !== null && x.b > b1);
      if (between.length) { if (log) log('a mint or burn landed while totalSupply was read, reading again'); continue; }
      const real = rows => rows.filter(x => x.v !== null);
      S.tie = { block_before: b1, block_after: b2, total_supply_wei: ts.toString(),
                minted_after_wei: real(mints).reduce((s, x) => s + x.v, 0n).toString(), mints_after: real(mints).length,
                burned_after_wei: real(burns).reduce((s, x) => s + x.v, 0n).toString(), burns_after: real(burns).length,
                records_with_no_value_after: mints.length + burns.length - real(mints).length - real(burns).length };
      break;
    }
    if (!S.tie) throw new Error('could not read totalSupply between two blocks with no mint or burn');
    return S;
  }

  // ---------------------------------------------------------------- the calculation
  function analyze(S) {
    const settle = new Set(SETTLE), rewards = new Set(REWARDS), W = S.wallets;
    const recipients = new Set();
    const groupOf = a => (W.has(a) ? 'wallets' : settle.has(a) ? 'settlement' : rewards.has(a) ? 'rewards' : recipients.has(a) ? 'recipients' : 'other');
    const phantomKeys = new Set(S.phantoms.filter(p => !p.in_receipt).map(p => p.b + ':' + p.li + ':' + p.f + ':' + p.t));
    const kept = [], dropped = [];
    for (const r of S.logs) {
      if (r.v === null) {
        if (!phantomKeys.has(r.b + ':' + r.li + ':' + r.f + ':' + r.t)) throw new Error('a record with no value is in its receipt, block ' + r.b);
        dropped.push(r);
      } else kept.push(r);
    }
    kept.sort((x, y) => x.b - y.b || x.li - y.li);
    const seen = new Set();
    for (const r of kept) { const k = r.b + ':' + r.li; if (seen.has(k)) throw new Error('two logs share block ' + r.b + ' and index ' + r.li); seen.add(k); }
    // accounts outside the programme whose every USDe came from a settlement address, over the whole read
    const recv = new Map(), recvSettle = new Map();
    for (const r of kept) if (r.t !== ZERO) { recv.set(r.t, (recv.get(r.t) || 0n) + r.v); if (settle.has(r.f)) recvSettle.set(r.t, (recvSettle.get(r.t) || 0n) + r.v); }
    for (const [a, v] of recvSettle) if (!W.has(a) && !settle.has(a) && !rewards.has(a) && v > 0n && v === recv.get(a)) recipients.add(a);
    const firstDay = Math.floor(S.deployTs / DAY), lastDay = Math.floor((CUTOFF - 1) / DAY);
    const bal = new Map(), firstIn = new Map(), flows = new Map();
    const flow = a => { if (!flows.has(a)) flows.set(a, { received: 0n, minted_to: 0n, from_settlement: 0n, from_wallets: 0n, sent: 0n, burned: 0n, to_wallets: 0n }); return flows.get(a); };
    let fromOutside = 0n;
    const held = { wallets: 0n, settlement: 0n, rewards: 0n, recipients: 0n, other: 0n };
    let supply = 0n, holders = 0, walletsWith = 0, negatives = 0, i = 0;
    const createdTs = [...W.values()].sort((a, b) => a - b);
    let created = 0;
    // flows between groups, before the UTC day of the first wallet, from it to the recount's last day, and after it
    const flowKey = a => (W.has(a) ? 'ethenapay_wallets' : settle.has(a) ? 'settlement' : rewards.has(a) ? 'reward_accounts'
      : recipients.has(a) ? 'settlement_recipients' : FLOW_KEYS[a] || 'other_accounts');
    const walletDay = createdTs.length ? Math.floor(createdTs[0] / DAY) : lastDay + 1;
    const splitDay = Math.floor(RECOUNT_END / DAY);
    if (!(walletDay < splitDay && splitDay <= lastDay)) throw new Error('the flow periods are out of order');
    const periods = [[firstDay, walletDay - 1], [walletDay, splitDay - 1], [splitDay, lastDay]].map(([x, y]) => dateOf(x * DAY) + ' to ' + dateOf(y * DAY));
    const matrix = new Map();
    const days = [];
    const move = (a, d) => {
      const before = bal.get(a) || 0n, after = before + d;
      bal.set(a, after);
      held[groupOf(a)] += d;
      if (before <= 0n && after > 0n) { holders++; if (W.has(a)) walletsWith++; }
      if (before > 0n && after <= 0n) { holders--; if (W.has(a)) walletsWith--; }
      if (before >= 0n && after < 0n) negatives++;
      if (before < 0n && after >= 0n) negatives--;
    };
    for (let d = firstDay; d <= lastDay; d++) {
      const end = (d + 1) * DAY;
      const row = { date: dateOf(d * DAY), transfers: 0, minted: 0n, burned: 0n, minted_to_wallets: 0n, burned_from_wallets: 0n };
      while (i < kept.length && kept[i].ts < end) {
        const r = kept[i++];
        if (r.ts < d * DAY) throw new Error('log before its day');
        row.transfers++;
        if (r.f === ZERO) { row.minted += r.v; supply += r.v; if (W.has(r.t)) row.minted_to_wallets += r.v; } else move(r.f, -r.v);
        if (r.t === ZERO) { row.burned += r.v; supply -= r.v; if (W.has(r.f)) row.burned_from_wallets += r.v; } else move(r.t, r.v);
        if (r.t !== ZERO && !firstIn.has(r.t)) firstIn.set(r.t, r.ts);
        if (r.t !== ZERO) { const g = flow(r.t); g.received += r.v; if (r.f === ZERO) g.minted_to += r.v; if (settle.has(r.f)) g.from_settlement += r.v; if (W.has(r.f)) g.from_wallets += r.v; }
        if (r.f !== ZERO) { const g = flow(r.f); g.sent += r.v; if (r.t === ZERO) g.burned += r.v; if (W.has(r.t)) g.to_wallets += r.v; }
        if (W.has(r.t) && !W.has(r.f) && !settle.has(r.f) && !rewards.has(r.f)) fromOutside += r.v;
        const mk = (r.ts < walletDay * DAY ? 0 : r.ts < splitDay * DAY ? 1 : 2) + '|' + (r.f === ZERO ? 'minted' : flowKey(r.f)) + '|' + (r.t === ZERO ? 'burned' : flowKey(r.t));
        const m = matrix.get(mk) || { n: 0, v: 0n };
        m.n++; m.v += r.v; matrix.set(mk, m);
      }
      while (created < createdTs.length && createdTs[created] < end) created++;
      if (negatives !== 0) throw new Error('a balance is below zero at the end of ' + row.date);
      const parts = held.wallets + held.settlement + held.rewards + held.recipients + held.other;
      if (parts !== supply) throw new Error('the holdings do not add up to the supply at the end of ' + row.date);
      Object.assign(row, { supply, wallets_held: held.wallets, settlement_held: held.settlement, rewards_held: held.rewards,
                           recipients_held: held.recipients, other_held: held.other, holders, wallets_with_usde: walletsWith, wallets_created: created });
      days.push(row);
    }
    if (i !== kept.length) throw new Error('logs after the last day');
    // the flows, and each group's balance from them
    const flowRows = [];
    for (let p = 0; p < 3; p++) for (const fg of FLOW_ORDER) for (const tg of FLOW_ORDER) {
      const m = matrix.get(p + '|' + fg + '|' + tg);
      if (m) flowRows.push({ period: periods[p], from: fg, to: tg, n: m.n, v: m.v });
    }
    if (flowRows.reduce((s, r) => s + r.n, 0) !== kept.length) throw new Error('the flows do not count every log');
    const heldBy = {};
    for (const [a, v] of bal) if (v !== 0n) heldBy[flowKey(a)] = (heldBy[flowKey(a)] || 0n) + v;
    for (const g of FLOW_ORDER.slice(1, -1)) {
      const net = flowRows.reduce((s, r) => s + (r.to === g ? r.v : 0n) - (r.from === g ? r.v : 0n), 0n);
      if (net !== (heldBy[g] || 0n)) throw new Error('the flows into and out of ' + g + ' do not give its balance');
    }
    // holders at the end of the last day
    const groups = { wallets: [], settlement: [], rewards: [], recipients: [], other: [] };
    for (const [a, v] of bal) if (v > 0n) groups[groupOf(a)].push([a, v]);
    const byBalance = (x, y) => (y[1] > x[1] ? 1 : y[1] < x[1] ? -1 : (x[0] < y[0] ? -1 : 1));
    groups.other.sort(byBalance); groups.recipients.sort(byBalance);
    const sum = arr => arr.reduce((s, x) => s + x[1], 0n);
    const holderRows = [
      { group: 'ethenapay_wallets', rank: '', label: '', holders: groups.wallets.length, balance: sum(groups.wallets) },
      { group: 'settlement', rank: '', label: '', holders: groups.settlement.length, balance: sum(groups.settlement) },
      { group: 'reward_accounts', rank: '', label: '', holders: groups.rewards.length, balance: sum(groups.rewards) },
    ];
    const listed = (name, arr) => {
      arr.slice(0, TOP_OTHERS).forEach(([a, v], k) => holderRows.push(Object.assign({ group: name, rank: k + 1, label: LABELS[a] || '', holders: 1, balance: v,
        address: a, first_received: firstIn.has(a) ? dateOf(firstIn.get(a)) : '' }, { flows: flow(a) })));
      const rest = arr.slice(TOP_OTHERS);
      holderRows.push({ group: name + '_rest', rank: '', label: '', holders: rest.length, balance: sum(rest) });
    };
    listed('settlement_recipients', groups.recipients);
    listed('other', groups.other);
    return { days, holderRows, flowRows, periods, kept, dropped, supply, bal, fromOutside, recipients };
  }

  function csvDaily(days) {
    const head = 'date,transfers,minted_wei,burned_wei,supply_wei,minted_to_wallets_wei,burned_from_wallets_wei,wallets_held_wei,'
      + 'settlement_held_wei,reward_accounts_held_wei,settlement_recipients_held_wei,other_held_wei,holders,wallets_with_usde,wallets_created';
    return [head, ...days.map(r => [r.date, r.transfers, r.minted, r.burned, r.supply, r.minted_to_wallets, r.burned_from_wallets,
      r.wallets_held, r.settlement_held, r.rewards_held, r.recipients_held, r.other_held, r.holders, r.wallets_with_usde, r.wallets_created].join(','))].join('\n') + '\n';
  }

  function csvHolders(rows) {
    const head = 'group,rank,label,is_contract,first_received,holders,balance_wei,received_wei,minted_to_wei,received_from_settlement_wei,'
      + 'received_from_wallets_wei,sent_wei,burned_wei,sent_to_wallets_wei';
    const f = (r, k) => (r.flows ? r.flows[k] : '');
    return [head, ...rows.map(r => [r.group, r.rank, r.label, r.is_contract === undefined ? '' : r.is_contract ? 1 : 0,
      r.first_received || '', r.holders, r.balance, f(r, 'received'), f(r, 'minted_to'), f(r, 'from_settlement'), f(r, 'from_wallets'),
      f(r, 'sent'), f(r, 'burned'), f(r, 'to_wallets')].join(','))].join('\n') + '\n';
  }

  function csvFlows(rows) {
    return ['period,from_group,to_group,transfers,usde_wei', ...rows.map(r => [r.period, r.from, r.to, r.n, r.v].join(','))].join('\n') + '\n';
  }

  async function run(fetchFn, log) {
    const t0 = new Date().toISOString();
    const S = await load(fetchFn, log);
    S.deployTs = Date.parse(S.counts.deploy_block_time) / 1000;
    const R = analyze(S);
    for (const [a, l] of Object.entries(LABELS)) if (!R.holderRows.some(r => r.address === a)) throw new Error('a labeled holder is not among the largest other holders: ' + l);
    const { raw } = makeApi(fetchFn);
    for (const r of R.holderRows) if (r.address) {
      const j = await raw({ module: 'proxy', action: 'eth_getCode', address: r.address, tag: 'latest' });
      r.is_contract = !!(j && typeof j.result === 'string' && j.result.length > 2);
    }
    const last = R.days[R.days.length - 1];
    const minted = R.kept.filter(x => x.f === ZERO), burned = R.kept.filter(x => x.t === ZERO);
    const sumV = a => a.reduce((s, x) => s + x.v, 0n);
    const tieSupply = BigInt(S.tie.total_supply_wei) - BigInt(S.tie.minted_after_wei) + BigInt(S.tie.burned_after_wei);
    const files = { 'daily.csv': csvDaily(R.days), 'holders.csv': csvHolders(R.holderRows), 'flows.csv': csvFlows(R.flowRows) };
    const meta = {
      token: USDE, chain: 'Avalanche C-Chain', deploy_block: DEPLOY_BLOCK, deploy_block_time: S.counts.deploy_block_time,
      end_block: END_BLOCK, end_block_time: S.counts.end_block_time, next_block_time: S.counts.next_block_time,
      first_day: R.days[0].date, last_day: last.date, days: R.days.length,
      wallets: S.wallets.size, factory_rows: [S.counts.factory0_rows, S.counts.factory1_rows],
      factory_created_not_create2: S.factoryOther.sort((x, y) => x.block - y.block), factory_rows_not_creations: S.factoryOtherRows,
      transfer_records_listed: S.logs.length, transfer_logs_kept: R.kept.length,
      records_with_no_value: R.dropped.length,
      records_with_no_value_checked_against_receipts: S.phantoms.length,
      records_with_no_value_found_in_their_receipts: S.phantoms.filter(p => p.in_receipt).length,
      records_with_no_value_touching_ethenapay: R.dropped.filter(x => S.wallets.has(x.f) || S.wallets.has(x.t) || SETTLE.includes(x.f) || SETTLE.includes(x.t) || REWARDS.includes(x.f) || REWARDS.includes(x.t)).length,
      records_with_no_value_by_month: R.dropped.reduce((m, x) => { const k = dateOf(x.ts).slice(0, 7); m[k] = (m[k] || 0) + 1; return m; }, {}),
      records_with_no_value_empty_amount: R.dropped.filter(x => x.ed).length, records_with_no_value_empty_block_hash: R.dropped.filter(x => x.eb).length,
      mints: minted.length, burns: burned.length, minted_wei: sumV(minted).toString(), burned_wei: sumV(burned).toString(),
      supply_at_end_wei: last.supply.toString(),
      tie_to_contract: Object.assign({}, S.tie, { supply_at_end_from_contract_wei: tieSupply.toString(), equal: tieSupply === last.supply }),
      holders_at_end: last.holders,
      settlement_recipients: R.recipients.size,
      wallets_received_from_outside_wei: R.fromOutside.toString(),
      flow_periods: R.periods,
    };
    meta.run_started_utc = t0; meta.run_finished_utc = new Date().toISOString();
    files['meta.json'] = JSON.stringify(meta, null, 1) + '\n';
    const hashes = {};
    for (const [name, text] of Object.entries(files)) hashes[name] = { bytes: new TextEncoder().encode(text).length, sha256: await sha256hex(text) };
    return { files, hashes, R, S };
  }

  async function main() {
    const fs = require('fs'), path = require('path');
    const dir = path.join(__dirname, 'inputs', 'chain');
    fs.mkdirSync(dir, { recursive: true });
    const log = m => console.log(new Date().toISOString().slice(11, 19), m);
    const out = await run(globalThis.fetch, log);
    for (const [name, text] of Object.entries(out.files)) { fs.writeFileSync(path.join(dir, name), text); log('wrote ' + name + ' ' + out.hashes[name].bytes + ' bytes ' + out.hashes[name].sha256.slice(0, 12)); }
  }

  return { load, analyze, run, main, sha256hex, csvDaily, csvHolders, csvFlows, config: CFG, USDE, ZERO, FACTORIES, SETTLE, REWARDS,
           LABELS, FLOW_KEYS, FLOW_ORDER, DEPLOY_BLOCK, END_BLOCK, CUTOFF, RECOUNT_END, TOP_OTHERS };
})();
if (typeof module !== 'undefined' && typeof require === 'function' && require.main === module) {
  globalThis.AUR.main().catch(e => { console.error(e); process.exit(1); });
}
