/*
 cashback_recount.cjs

 Reads what EthenaPay's cashback accounts paid in AVAX to EthenaPay wallets, the card payments those wallets
 made in USDe, and the Chainlink AVAX / USD price, all on Avalanche C-Chain through block 97,161,009, the last
 block of October 9, 2026 UTC.

   1. Every contract the two wallet factories created                      (explorer API, txlistinternal)
   2. Every USDe Transfer that touches one of those wallets                (explorer API, tokentx)
   3. Every AllowanceSpent log to either settlement address                (explorer API, getLogs)
   4. Every internal AVAX transfer into or out of the two cashback accounts (explorer API, txlistinternal)
   5. Every AnswerUpdated log of the Chainlink AVAX / USD aggregator from shortly before 00:00 UTC on August 20, 2026
                                                                           (explorer API, getLogs)

 It writes the files in inputs/chain/, which ethenapay_cashback_review.py reads. Wallets appear in them as a
 position number in creation order, the numbering of the chain recount published with the EthenaPay
 adoption review. No wallet's address and no transaction hash is written.

 Run it with Node 18 or later:   node cashback_recount.cjs
 The same code runs unchanged in a browser console on a page that allows the requests, as
 ECB.run(u => fetch(u, { cache: 'no-store' }), console.log), which returns the files as text. That is how
 the files in this packet were produced. main() below calls the same run() and only adds the write to disk.

 Rules
   wallet          a contract a factory created with CREATE2
   card payment    a USDe transfer from a wallet to either settlement address. spends.csv marks each one that a
                   spend event matches, an AllowanceSpent log the same wallet emitted in the same transaction for
                   USDe to the same settlement address and the same amount, matched one to one
   reversal        a USDe transfer from either settlement address to a wallet
   cashback        an internal AVAX transfer, with value, from a cashback account to a wallet. Transfers from
                   those accounts to any other address are counted apart and are not cashback. For each of
                   those, the file gives the AVAX the same account received in the same transaction
   batch           cashback transfers from one account with no gap of more than three hours between them
   price           the answer of the Chainlink AVAX / USD round in force at a time, the latest round whose
                   updatedAt is at or before it, with 8 decimals. The files give it at each cashback transfer
                   and each batch's first transfer from August 20, and on the hour from August 20 to October 10

 The paging in walk() and the request retry in makeApi() are the chain recount's, unchanged.
*/
globalThis.ECB = (() => {
  'use strict';
  const API = 'https://api.routescan.io/v2/network/mainnet/evm/43114/etherscan/api';
  const USDE = '0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34';
  const FACTORIES = ['0x313be708df16979d9e5fe9db5ac4969b8add7207',     // v1 pilot factory
                     '0xac66ca9a79fb0d3c64cba44cd29610cd58602d6f'];    // v2 current factory
  const SETTLE = ['0x6070848bd19c37488d0516058f2933dd992733de',        // current settlement address
                  '0x3b3ffd99b87a2dee5ad244b75d5a8e266890fdb8'];       // retired settlement address
  const BASE = '0xd0ec8cc7414f27ce85f8dece6b4a58225f273311';           // USDe reward account labeled yield in the dashboard's query
  const TOPUP = ['0xab2b06efa6179e624f5e3b08b64978df114ff24f',          // USDe reward accounts labeled other rewards
                 '0xc9dd0d4351d3841a712f59cb4f1e88c3d500515b'];
  const CASHBACK = ['0x37dea6fe8bc3d8d8c47fa3dac98c39a88585a71d',      // cashback account from July 15, 2026
                    '0xfdc9d265ba3cdac512c7fe7e30417cc29487ff7b'];     // cashback account from May 20 to July 14, 2026
  const CL_PROXY = '0x0a77230d17318075983913bc2145db16c7366156';      // Chainlink AVAX / USD proxy on Avalanche C-Chain
  const CL_AGG = '0xcfbfe648ba88bf7d9776d970417a0b26c315feb4';        // the aggregator behind it, phase 2
  const T_ANSWER = '0x0559884fd3a460db3073b7fc896cc77986f16e378210ded43186175bf646fc5f';  // AnswerUpdated(int256,uint256,uint256)
  const T_SPENT = '0xa575fb45e6259a68f4974e75c94adc55a35f2c06eee07709e964a4407e7dcfeb';   // AllowanceSpent(address,address,uint256)
  const pad = a => '0x' + a.slice(2).padStart(64, '0');
  const START_BLOCK = 85400000;          // before the first factory call on May 15, 2026
  const END_BLOCK = 97161009;            // last block of October 9, 2026 UTC
  const PRICE_START_BLOCK = 93220397;    // first block at or after 00:00 UTC on August 20, 2026
  const ROUNDS_FROM_BLOCK = PRICE_START_BLOCK - 5000;   // Chainlink rounds are read from about 1.5 hours earlier, so one is in force at 00:00
  const RECOUNT_BLOCK = 96815525;        // the adoption review's balance snapshot, 15:53:28 UTC October 5
  const RECOUNT_LAST_DAY = 143;          // October 5, the recount's last UTC day
  const DAY = 86400;
  const utc = (y, m, d, hh, mm, ss) => Date.UTC(y, m - 1, d, hh || 0, mm || 0, ss || 0) / 1000;
  const DAY0 = Math.floor(utc(2026, 5, 15) / DAY);        // UTC day 0 is 2026-05-15
  const ROWS_FROM = utc(2026, 8, 15);                     // card payments, reversals and cashback are written from here
  const PRICE_FROM = utc(2026, 8, 20), PRICE_TO = utc(2026, 10, 10), HOUR = 3600;
  const GAP = 3 * 3600;
  const CENT = 10n ** 16n;

  const CFG = { retryMs: 900 };
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const iso = t => new Date(t * 1000).toISOString().slice(0, 19) + 'Z';
  const dateOf = t => new Date(t * 1000).toISOString().slice(0, 10);

  async function sha256hex(str) {
    const bytes = new TextEncoder().encode(str);
    const subtle = (globalThis.crypto && globalThis.crypto.subtle) || require('crypto').webcrypto.subtle;
    const d = await subtle.digest('SHA-256', bytes);
    return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, '0')).join('');
  }

  // ---------------------------------------------------------------- reading the chain
  function makeApi(fetchFn) {
    return async function api(params) {
      const u = API + '?' + Object.entries(params).map(([k, v]) => k + '=' + v).join('&');
      for (let i = 0; i < 6; i++) {
        try {
          const r = await fetchFn(u);
          if (r.ok) {
            const j = await r.json();
            if (Array.isArray(j.result)) return j.result;
            if (typeof j.result === 'string' && /^\d+$/.test(j.result)) return j.result;
          }
        } catch (e) { /* retry */ }
        await sleep(CFG.retryMs * (i + 1));
      }
      throw new Error('request failed: ' + u.slice(API.length, API.length + 200));
    };
  }

  async function walk(api, paramsFor, pageSize, blockOf, onRow, label, log, start) {
    let from = start === undefined ? START_BLOCK : start, total = 0, span = END_BLOCK - from + 1;
    while (from <= END_BLOCK) {
      const to = Math.min(END_BLOCK, from + span - 1);
      let rows;
      try { rows = await api(paramsFor(from, to)); } catch (e) {
        if (span <= 20000) throw e;
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
      if (log) log(label + ' ' + total + ' rows' + (next > END_BLOCK ? ', done' : ', next block ' + next));
      from = next;
    }
    return total;
  }

  async function load(fetchFn, log) {
    const api = makeApi(fetchFn);
    const S = { wallets: new Map(), infra: [], xfers: [], spent: [], cashback: [], other: [], incoming: [], rounds: [], counts: {} };
    const rpc = async params => {
      const u = API + '?' + Object.entries(params).map(([k, v]) => k + '=' + v).join('&');
      for (let i = 0; i < 6; i++) {
        try { const r = await fetchFn(u); if (r.ok) { const j = await r.json(); if (j && j.result !== undefined && j.result !== null) return j.result; } } catch (e) { /* retry */ }
        await sleep(CFG.retryMs * (i + 1));
      }
      throw new Error('rpc failed: ' + u.slice(API.length, API.length + 160));
    };
    const blockTs = async b => parseInt((await rpc({ module: 'proxy', action: 'eth_getBlockByNumber', tag: '0x' + b.toString(16), boolean: 'false' })).timestamp, 16);
    const endTs = await blockTs(END_BLOCK), nextTs = await blockTs(END_BLOCK + 1);
    if (!(endTs < utc(2026, 10, 10) && nextTs >= utc(2026, 10, 10))) throw new Error('block ' + END_BLOCK + ' is not the last block of October 9 UTC');
    const pTs = await blockTs(PRICE_START_BLOCK), pPrev = await blockTs(PRICE_START_BLOCK - 1);
    if (!(pTs >= PRICE_FROM && pPrev < PRICE_FROM)) throw new Error('block ' + PRICE_START_BLOCK + ' is not the first block of August 20 UTC');
    S.counts.end_block_time = iso(endTs); S.counts.next_block_time = iso(nextTs); S.counts.price_start_block_time = iso(pTs);
    for (let g = 0; g < FACTORIES.length; g++) {
      const f = FACTORIES[g];
      S.counts['factory' + g + '_rows'] = await walk(api,
        (from, to) => ({ module: 'account', action: 'txlistinternal', address: f, startblock: from, endblock: to, page: 1, offset: 10000, sort: 'asc' }),
        10000, r => Number(r.blockNumber), r => {
          if (String(r.from).toLowerCase() !== f || !r.contractAddress || String(r.isError) !== '0') return;
          const a = r.contractAddress.toLowerCase(), o = { ts: Number(r.timeStamp), blk: Number(r.blockNumber), gen: g };
          const typ = String(r.type).toLowerCase();
          if (typ === 'create2') S.wallets.set(a, o);
          else if (typ === 'create') S.infra.push({ gen: g, a, blk: o.blk, ts: o.ts });
        }, 'factory ' + g, log);
    }
    let scanned = 0, q = 0;
    await walk(api,
      (from, to) => ({ module: 'account', action: 'tokentx', contractaddress: USDE, startblock: from, endblock: to, page: 1, offset: 10000, sort: 'asc' }),
      10000, r => Number(r.blockNumber), r => {
        scanned++;
        const f = r.from.toLowerCase(), t = r.to.toLowerCase(), fw = S.wallets.has(f), tw = S.wallets.has(t);
        if (fw || tw) S.xfers.push({ f, t, fw, tw, v: BigInt(r.value), ts: Number(r.timeStamp), blk: Number(r.blockNumber), tx: r.hash.toLowerCase(), q: q++ });
      }, 'usde transfers', log);
    S.counts.transfers_scanned = scanned;
    // every AllowanceSpent log to a settlement address, whatever its token, the spend events the dashboard counts
    S.counts.spend_logs_by_token = {};
    let lq = 0;
    for (let s = 0; s < SETTLE.length; s++) {
      const byToken = {};
      await walk(api,
        (from, to) => ({ module: 'logs', action: 'getLogs', fromBlock: from, toBlock: to, topic0: T_SPENT, topic0_2_opr: 'and', topic2: pad(SETTLE[s]), page: 1, offset: 1000 }),
        1000, r => parseInt(r.blockNumber), r => {
          if (String(r.topics[0]).toLowerCase() !== T_SPENT || String(r.topics[2]).toLowerCase() !== pad(SETTLE[s])) throw new Error('log does not match the filter');
          const tok = '0x' + String(r.topics[1]).slice(26).toLowerCase();
          byToken[tok] = (byToken[tok] || 0) + 1;
          if (tok === USDE) S.spent.push({ w: String(r.address).toLowerCase(), to: SETTLE[s], v: BigInt(r.data), tx: String(r.transactionHash).toLowerCase(),
                                           ts: parseInt(r.timeStamp), blk: parseInt(r.blockNumber), q: lq++ });
        }, 'spend events ' + s, log);
      S.counts.spend_logs_by_token[s === 0 ? 'current_settlement' : 'retired_settlement'] = byToken;
    }
    let cq = 0;
    for (let c = 0; c < CASHBACK.length; c++) {
      const payer = CASHBACK[c];
      const k = { rows: 0, out_failed: 0, out_zero: 0, in_rows: 0, in_failed_or_zero: 0, neither: 0 };
      await walk(api,
        (from, to) => ({ module: 'account', action: 'txlistinternal', address: payer, startblock: from, endblock: to, page: 1, offset: 10000, sort: 'asc' }),
        10000, r => Number(r.blockNumber), r => {
          k.rows++;
          const fr = String(r.from).toLowerCase(), to = String(r.to).toLowerCase(), v = BigInt(r.value), ok = String(r.isError) === '0';
          if (fr !== payer) {
            if (to !== payer) { k.neither++; return; }            // a row that names the account another way, such as its creation
            if (!ok || v === 0n) { k.in_failed_or_zero++; return; }
            k.in_rows++;
            S.incoming.push({ c, from: fr, v, ts: Number(r.timeStamp), blk: Number(r.blockNumber), tx: r.hash.toLowerCase() });
            return;
          }
          if (!ok) { k.out_failed++; return; }
          if (v === 0n) { k.out_zero++; return; }
          const o = { c, to, v, ts: Number(r.timeStamp), blk: Number(r.blockNumber), tx: r.hash.toLowerCase(), q: cq++ };
          if (S.wallets.has(to)) S.cashback.push(o); else S.other.push(o);
        }, 'cashback ' + c, log);
      S.counts['cashback' + c] = k;
    }
    const word = h => BigInt(h);
    S.counts.cl_aggregator = '0x' + (await rpc({ module: 'proxy', action: 'eth_call', to: CL_PROXY, data: '0x245a7bfc', tag: 'latest' })).slice(26).toLowerCase();
    S.counts.cl_phase = Number(word(await rpc({ module: 'proxy', action: 'eth_call', to: CL_PROXY, data: '0x58303b10', tag: 'latest' })));
    S.counts.cl_decimals = Number(word(await rpc({ module: 'proxy', action: 'eth_call', to: CL_PROXY, data: '0x313ce567', tag: 'latest' })));
    if (S.counts.cl_aggregator !== CL_AGG) throw new Error('the proxy now points to another aggregator');
    await walk(api,
      (from, to) => ({ module: 'logs', action: 'getLogs', address: CL_AGG, fromBlock: from, toBlock: to, topic0: T_ANSWER, page: 1, offset: 1000 }),
      1000, r => parseInt(r.blockNumber), r => {
        if (String(r.topics[0]).toLowerCase() !== T_ANSWER || String(r.address).toLowerCase() !== CL_AGG) throw new Error('log does not match the filter');
        S.rounds.push({ round: BigInt(r.topics[2]), answer: BigInt.asIntN(256, BigInt(r.topics[1])), updated: Number(BigInt(r.data)), blk: parseInt(r.blockNumber), ts: parseInt(r.timeStamp) });
      }, 'chainlink rounds', log, ROUNDS_FROM_BLOCK);
    return S;
  }

  // ---------------------------------------------------------------- the files
  async function analyze(S) {
    const SETS = new Set(SETTLE), TOP = new Set(TOPUP);
    const files = {};
    const wl = [...S.wallets.entries()].map(([a, o]) => ({ a, ts: o.ts, blk: o.blk, gen: o.gen }))
      .sort((x, y) => x.blk - y.blk || (x.a < y.a ? -1 : x.a > y.a ? 1 : 0));
    const wid = new Map(); wl.forEach((w, i) => wid.set(w.a, i));
    const xs = S.xfers;
    for (let i = 1; i < xs.length; i++) if (xs[i].blk < xs[i - 1].blk || xs[i].ts < xs[i - 1].ts) throw new Error('transfers out of order at ' + i);

    // each transfer as one or two wallet events, for the cross-checks with the published recount
    const ev = new Map();
    const push = (a, e) => { let l = ev.get(a); if (!l) { l = []; ev.set(a, l); } l.push(e); };
    const flows = new Map();
    const flowOf = d => { let f = flows.get(d); if (!f) { f = { dep: 0n, wd: 0n, rev: 0n, yld: 0n, oth: 0n, card: 0n, intl: 0n }; flows.set(d, f); } return f; };
    const spendRows = [];
    let cardN = 0, cardWei = 0n, revN = 0, revWei = 0n;
    // spend events by transaction, wallet, settlement address and amount, each to be matched to one card payment
    const evKey = (tx, w, to, v) => tx + '|' + w + '|' + to + '|' + v;
    const open = new Map();
    for (const e of S.spent) { const k = evKey(e.tx, e.w, e.to, e.v); open.set(k, (open.get(k) || 0) + 1); }
    let matchedN = 0, matchedWei = 0n, bareN = 0, bareWei = 0n;
    for (const x of xs) {
      const f = flowOf(Math.floor(x.ts / DAY) - DAY0);
      if (x.fw && x.tw) {
        f.intl += x.v;
        push(x.f, { ts: x.ts, blk: x.blk, q: x.q, dv: -x.v, k: 'j' });
        push(x.t, { ts: x.ts, blk: x.blk, q: x.q, dv: x.v, k: 'i', inc: true });
      } else if (x.tw) {
        let k;
        if (SETS.has(x.f)) {
          f.rev += x.v; k = 'r'; revN++; revWei += x.v;
          if (x.ts >= ROWS_FROM) { if (x.v % CENT !== 0n) throw new Error('a reversal is not a whole number of cents'); spendRows.push([wid.get(x.t), x.ts, 'r', x.v / CENT, '']); }
        }
        else if (x.f === BASE) { f.yld += x.v; k = 'b'; }
        else if (TOP.has(x.f)) { f.oth += x.v; k = 't'; }
        else { f.dep += x.v; k = 'd'; }
        push(x.t, { ts: x.ts, blk: x.blk, q: x.q, dv: x.v, k, inc: true });
      } else {
        const k = SETS.has(x.t) ? 'c' : 'w';
        if (k === 'c') {
          f.card += x.v; cardN++; cardWei += x.v;
          const key = evKey(x.tx, x.f, x.t, x.v), n = open.get(key) || 0;
          if (n > 0) { open.set(key, n - 1); matchedN++; matchedWei += x.v; } else { bareN++; bareWei += x.v; }
          if (x.ts >= ROWS_FROM) { if (x.v % CENT !== 0n) throw new Error('a card payment is not a whole number of cents'); spendRows.push([wid.get(x.f), x.ts, 'c', x.v / CENT, n > 0 ? 1 : 0]); }
        } else f.wd += x.v;
        push(x.f, { ts: x.ts, blk: x.blk, q: x.q, dv: -x.v, k });
      }
    }
    for (const l of ev.values()) l.sort((a, b) => a.ts - b.ts || a.q - b.q);
    const recountEndTs = (DAY0 + RECOUNT_LAST_DAY + 1) * DAY;
    const recountRows = [];
    for (const [a, l] of ev) {
      if (!(l.length && l[0].ts < recountEndTs)) continue;
      let bal = 0n, fi = null;
      for (const e of l) {
        if (e.ts >= recountEndTs) break;
        if (fi === null && e.inc) fi = e;
        if (e.blk <= RECOUNT_BLOCK) bal += e.dv;
      }
      const kind = fi ? ({ d: 'd', i: 'i', r: 'r', b: 'y', t: 'o' })[fi.k] : '';
      recountRows.push([wid.get(a), fi ? fi.ts : '', kind, bal]);
    }
    recountRows.sort((x, y) => x[0] - y[0]);
    const recountCanon = recountRows.map(r => r.join(',')).join('\n') + '\n';
    const heldAt = new Array(RECOUNT_LAST_DAY + 1).fill(0n);
    for (const l of ev.values()) {
      let bal = 0n, p = 0;
      for (let d = 0; d <= RECOUNT_LAST_DAY; d++) {
        const end = (DAY0 + d + 1) * DAY;
        while (p < l.length && l[p].ts < end) bal += l[p++].dv;
        if (bal > 0n) heldAt[d] += bal;
      }
    }
    const flowLine = d => { const f = flows.get(d) || flowOf(d); return [dateOf((DAY0 + d) * DAY), f.dep, f.wd, f.rev, f.yld, f.oth, f.card, f.intl, heldAt[d]].join(','); };
    const flowsCanon = [...Array(RECOUNT_LAST_DAY + 1).keys()].map(flowLine).join('\n') + '\n';

    files['spends.csv'] = 'wallet,ts,kind,cents,spend_event\n' + spendRows.map(r => r.join(',')).join('\n') + '\n';
    const unmatchedEvents = [...open.values()].reduce((a, b) => a + b, 0);
    const evToOct5 = S.spent.filter(e => e.ts < recountEndTs);

    // the Chainlink rounds, in round order, and the price in force at any time
    const R = S.rounds.slice().sort((a, b) => (a.round < b.round ? -1 : a.round > b.round ? 1 : 0));
    for (let i = 1; i < R.length; i++) {
      if (R[i].round === R[i - 1].round) throw new Error('a round appears twice');
      if (R[i].updated < R[i - 1].updated) throw new Error('rounds out of time order');
    }
    if (!R.length || R[0].updated > PRICE_FROM) throw new Error('no Chainlink round in force at the start of the window');
    const priceAt = t => {
      let lo = 0, hi = R.length - 1, k = -1;
      while (lo <= hi) { const m = (lo + hi) >> 1; if (R[m].updated <= t) { k = m; lo = m + 1; } else hi = m - 1; }
      return k < 0 ? null : R[k];
    };
    const qRows = [];
    for (let t = PRICE_FROM; t <= PRICE_TO; t += HOUR) {
      const r = priceAt(t);
      if (!r) throw new Error('no Chainlink round in force at ' + iso(t));
      qRows.push([iso(t), r.round, r.answer, r.updated].join(','));
    }
    files['prices_hourly.csv'] = 'time,round,answer,updated\n' + qRows.join('\n') + '\n';

    // cashback transfers and their batches
    const cb = S.cashback.slice().sort((a, b) => a.c - b.c || a.blk - b.blk || a.q - b.q);
    const batches = [];
    let cur = null;
    for (const x of cb) {
      if (!cur || cur.c !== x.c || x.ts - cur.last > GAP) { cur = { c: x.c, id: batches.filter(b => b.c === x.c).length, first: x.ts, last: x.ts, n: 0, v: 0n, txs: new Set(), w: new Set() }; batches.push(cur); }
      cur.last = x.ts; cur.n++; cur.v += x.v; cur.txs.add(x.tx); cur.w.add(x.to); x.batch = cur.id;
    }
    files['cashback.csv'] = 'payer,batch,wallet,ts,avax_wei,cl_round,cl_answer\n' + cb.filter(x => x.ts >= ROWS_FROM).sort((a, b) => a.ts - b.ts || a.c - b.c || a.q - b.q)
      .map(x => { const p = x.ts >= PRICE_FROM ? priceAt(x.ts) : null; return [x.c, x.batch, wid.get(x.to), x.ts, x.v, p ? p.round : '', p ? p.answer : ''].join(','); }).join('\n') + '\n';
    files['batches.csv'] = 'payer,batch,first_ts,last_ts,transfers,transactions,recipients,avax_wei,cl_round,cl_answer,cl_updated\n' + batches.map(b => {
      const p = b.first >= PRICE_FROM ? priceAt(b.first) : null;
      return [b.c, b.id, b.first, b.last, b.n, b.txs.size, b.w.size, b.v, p ? p.round : '', p ? p.answer : '', p ? p.updated : ''].join(',');
    }).join('\n') + '\n';
    // what each account received in the transaction of each transfer to an address that is not a wallet
    const inByTx = new Map();
    for (const x of S.incoming) { const key = x.c + ':' + x.tx; inByTx.set(key, (inByTx.get(key) || 0n) + x.v); }
    const oth = S.other.slice().sort((a, b) => a.blk - b.blk || a.q - b.q);
    const othAddr = [...new Set(oth.map(x => x.to))];
    files['other_recipients.csv'] = 'payer,recipient,ts,avax_wei,same_tx_in_wei\n' + oth.map(x => [x.c, othAddr.indexOf(x.to) + 1, x.ts, x.v, inByTx.get(x.c + ':' + x.tx) || 0n].join(',')).join('\n') + '\n';

    const meta = {
      end_block: END_BLOCK, end_block_time: S.counts.end_block_time, next_block_time: S.counts.next_block_time,
      start_block: START_BLOCK, price_start_block: PRICE_START_BLOCK, price_start_block_time: S.counts.price_start_block_time,
      rows_from: iso(ROWS_FROM), prices_from: iso(PRICE_FROM), prices_to: iso(PRICE_TO), recount_block: RECOUNT_BLOCK,
      wallets: wl.length, wallets_v1: wl.filter(w => w.gen === 0).length, wallets_v2: wl.filter(w => w.gen === 1).length,
      other_factory_contracts: S.infra.length,
      usde_transfers_scanned: S.counts.transfers_scanned, usde_transfers_touching_wallets: xs.length,
      card_payments: cardN, card_payment_wei: cardWei.toString(), reversals: revN, reversal_wei: revWei.toString(),
      spend_logs_by_token: S.counts.spend_logs_by_token,
      spend_events: { usde_logs: S.spent.length, usde_wei: S.spent.reduce((a, e) => a + e.v, 0n).toString(),
        from_wallets: S.spent.filter(e => S.wallets.has(e.w)).length,
        matched_to_card_payments: matchedN, matched_wei: matchedWei.toString(), card_payments_without_event: bareN, card_payments_without_event_wei: bareWei.toString(),
        events_without_card_payment: unmatchedEvents,
        to_october_5: { logs: evToOct5.length, usde_wei: evToOct5.reduce((a, e) => a + e.v, 0n).toString() } },
      cashback_account_rows: CASHBACK.map((c, i) => S.counts['cashback' + i]),
      cashback_account_incoming: CASHBACK.map((c, i) => {
        const l = S.incoming.filter(x => x.c === i);
        return { transfers: l.length, avax_wei: l.reduce((s, x) => s + x.v, 0n).toString(), senders: new Set(l.map(x => x.from)).size };
      }),
      cashback_transfers: CASHBACK.map((c, i) => cb.filter(x => x.c === i).length),
      cashback_avax_wei: CASHBACK.map((c, i) => cb.filter(x => x.c === i).reduce((s, x) => s + x.v, 0n).toString()),
      cashback_wallets: new Set(cb.map(x => x.to)).size,
      cashback_first: iso(cb.reduce((m, x) => Math.min(m, x.ts), Infinity)), cashback_last: iso(cb.reduce((m, x) => Math.max(m, x.ts), 0)),
      other_recipient_transfers: oth.length, other_recipients: othAddr.length,
      other_recipient_avax_wei: oth.reduce((s, x) => s + x.v, 0n).toString(),
      other_recipient_passed_through: oth.filter(x => (inByTx.get(x.c + ':' + x.tx) || 0n) === x.v).length,
      chainlink: { proxy: CL_PROXY, aggregator: S.counts.cl_aggregator, phase: S.counts.cl_phase, decimals: S.counts.cl_decimals,
        rounds: R.length, first_round: R[0].round.toString(), first_updated: iso(R[0].updated), last_round: R[R.length - 1].round.toString(), last_updated: iso(R[R.length - 1].updated) },
      cross_checks: {
        recount_wallet_rows: recountRows.length,
        recount_wallet_rows_sha256: await sha256hex(recountCanon),
        recount_balance_sum_wei: recountRows.reduce((s, r) => s + r[3], 0n).toString(),
        utc_days_compared: RECOUNT_LAST_DAY + 1,
        utc_days_sha256: await sha256hex(flowsCanon),
      },
    };
    return { files, meta };
  }

  async function run(fetchFn, log) {
    const t0 = new Date().toISOString();
    const S = await load(fetchFn, log);
    const R = await analyze(S);
    R.meta.run_started_utc = t0; R.meta.run_finished_utc = new Date().toISOString();
    R.files['meta.json'] = JSON.stringify(R.meta, (k, v) => (typeof v === 'bigint' ? v.toString() : v), 1) + '\n';
    const hashes = {};
    for (const [name, text] of Object.entries(R.files)) hashes[name] = { bytes: new TextEncoder().encode(text).length, sha256: await sha256hex(text) };
    return { files: R.files, hashes, S };
  }

  async function main() {
    const fs = require('fs'), path = require('path');
    const dir = path.join(__dirname, 'inputs', 'chain');
    fs.mkdirSync(dir, { recursive: true });
    const log = m => console.log(new Date().toISOString().slice(11, 19), m);
    const out = await run(globalThis.fetch, log);
    for (const [name, text] of Object.entries(out.files)) { fs.writeFileSync(path.join(dir, name), text); log('wrote ' + name + ' ' + out.hashes[name].bytes + ' bytes ' + out.hashes[name].sha256.slice(0, 12)); }
  }

  return { load, analyze, run, main, sha256hex, config: CFG, FACTORIES, SETTLE, USDE, BASE, TOPUP, CASHBACK, CL_PROXY, CL_AGG, START_BLOCK, END_BLOCK, PRICE_START_BLOCK, ROUNDS_FROM_BLOCK, DAY0 };
})();
if (typeof module !== 'undefined' && typeof require === 'function' && require.main === module) {
  globalThis.ECB.main().catch(e => { console.error(e); process.exit(1); });
}
