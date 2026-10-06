/*
 chain_recount.cjs

 Rebuilds the EthenaPay wallet, spend and balance figures from Avalanche C-Chain data,
 without the dashboard's Dune queries. It reads three things through block 96,839,679,
 the last block of October 5, 2026 UTC (timestamp 23:59:58).

   1. Every contract the two wallet factories created     (explorer API, txlistinternal)
   2. Every AllowanceSpent log in USDe to either settlement address   (explorer API, getLogs)
   3. Every USDe Transfer that touches one of those wallets           (explorer API, tokentx)

 It then writes the files in inputs/chain/, which ethenapay_adoption_review.py reads.
 Wallets appear in those files as a position number in creation order, never as an address.

 Run it with Node 18 or later:   node chain_recount.cjs
 The same code also runs unchanged in a browser console on any page that allows the requests.
 There the call is  EPR.run(fetch.bind(window), console.log)  which returns the six files as text.
 That is how the files in this packet were produced. main() below calls the same run() and
 only adds the write to disk.

 node chain_recount.cjs --review-addresses /some/private/path.json
 also writes the addresses of the twenty largest balances and the twenty largest spenders at the
 last snapshot, and the addresses that received spend-type events outside the spend rule. Keep
 that file out of this folder. The only addresses in inputs/chain/ are the three non-wallet
 contracts the factories created.

 Counting rules, taken from the dashboard's own SQL (dune/05_daily_metrics.sql, dune/06_kpi_headline.sql)
   wallet        a contract created by a factory with CREATE2
   spend event   one AllowanceSpent log, token USDe, destination one of the two settlement addresses.
                 Log events are counted. Transaction hashes are never counted.
   funded        USDe balance above zero, with no minimum
*/
globalThis.EPR = (() => {
  'use strict';
  const API = 'https://api.routescan.io/v2/network/mainnet/evm/43114/etherscan/api';
  const RPC = 'https://api.avax.network/ext/bc/C/rpc';
  const MULTICALL3 = '0xca11bde05977b3631167028862be2a173976ca11';
  const USDE = '0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34';
  const FACTORIES = ['0x313be708df16979d9e5fe9db5ac4969b8add7207',     // v1 pilot factory
                     '0xac66ca9a79fb0d3c64cba44cd29610cd58602d6f'];    // v2 current factory
  const SETTLE = ['0x6070848bd19c37488d0516058f2933dd992733de',        // current settlement address
                  '0x3b3ffd99b87a2dee5ad244b75d5a8e266890fdb8'];       // retired settlement address
  const YIELD = '0xd0ec8cc7414f27ce85f8dece6b4a58225f273311';          // reward payers named in the dashboard SQL
  const OTHER_REWARD = ['0xab2b06efa6179e624f5e3b08b64978df114ff24f', '0xc9dd0d4351d3841a712f59cb4f1e88c3d500515b'];
  const T_SPENT = '0xa575fb45e6259a68f4974e75c94adc55a35f2c06eee07709e964a4407e7dcfeb';   // AllowanceSpent(address,address,uint256)
  const START_BLOCK = 85400000;          // before the first factory call on May 15, 2026
  const END_BLOCK = 96839679;            // last block of October 5, 2026 UTC, timestamp 23:59:58
  const DAY = 86400;
  const utc = (y, m, d, hh, mm, ss) => Date.UTC(y, m - 1, d, hh || 0, mm || 0, ss || 0) / 1000;
  const DAY0 = Math.floor(utc(2026, 5, 15) / DAY);        // day 0 is 2026-05-15, the first day in the dashboard series

  // The nine committed versions of docs/ethenapay.json: short commit, generated time, lifetime spend events reported
  const SNAP = [
    ['90a04e1', utc(2026, 9, 11, 15, 41, 0), 9763],
    ['a58244e', utc(2026, 9, 14, 17, 55, 32), 11295],
    ['e279050', utc(2026, 9, 17, 18, 17, 52), 13033],
    ['364ba6b', utc(2026, 9, 21, 15, 35, 15), 15824],
    ['ed7f66f', utc(2026, 9, 22, 15, 5, 23), 16566],
    ['ccf36a7', utc(2026, 10, 3, 15, 6, 53), 26712],
    ['bd9fb3c', utc(2026, 10, 4, 16, 53, 29), 28078],
    ['56a0be9', utc(2026, 10, 5, 15, 41, 38), 29268],
    ['e9d94d8', utc(2026, 10, 5, 15, 57, 32), 29286],
  ];

  const CFG = { retryMs: 900 };          // pause before a failed request is tried again, times the attempt number
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const pad = a => '0x' + a.slice(2).toLowerCase().padStart(64, '0');
  const iso = t => new Date(t * 1000).toISOString().slice(0, 19) + 'Z';

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

  // Pages forward by block. A full page is cut back to its last complete block and the next
  // request restarts at that block, so no row is skipped and none is read twice.
  // The first request asks for every remaining block. If the explorer cannot answer that, the
  // range is cut to a quarter and asked again. A slow explorer costs more requests. It never changes the rows.
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
    const S = { endBlock: END_BLOCK, wallets: new Map(), infra: [], spends: [], xfers: [], counts: {} };
    const byTime = Number(await api({ module: 'block', action: 'getblocknobytime', timestamp: utc(2026, 10, 6) - 1, closest: 'before' }));
    if (byTime !== END_BLOCK) throw new Error('the explorer places the end of October 5 at block ' + byTime + ', not ' + END_BLOCK);

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

    for (let s = 0; s < SETTLE.length; s++) {
      S.counts['settle' + s + '_logs'] = await walk(api,
        (from, to) => ({ module: 'logs', action: 'getLogs', fromBlock: from, toBlock: to, topic0: T_SPENT, topic0_1_opr: 'and', topic1: pad(USDE), topic1_2_opr: 'and', topic2: pad(SETTLE[s]), topic0_2_opr: 'and', page: 1, offset: 1000 }),
        1000, r => parseInt(r.blockNumber), r => {
          if (String(r.topics[0]).toLowerCase() !== T_SPENT || String(r.topics[1]).toLowerCase() !== pad(USDE) || String(r.topics[2]).toLowerCase() !== pad(SETTLE[s])) throw new Error('log does not match the filter');
          S.spends.push({ w: r.address.toLowerCase(), ts: parseInt(r.timeStamp), blk: parseInt(r.blockNumber), li: parseInt(r.logIndex), amt: BigInt(r.data), tx: r.transactionHash.toLowerCase(), s });
        }, 'spend logs ' + s, log);
    }
    S.spends.sort((a, b) => a.blk - b.blk || a.li - b.li);

    let scanned = 0, q = 0;
    await walk(api,
      (from, to) => ({ module: 'account', action: 'tokentx', contractaddress: USDE, startblock: from, endblock: to, page: 1, offset: 10000, sort: 'asc' }),
      10000, r => Number(r.blockNumber), r => {
        scanned++;
        const f = r.from.toLowerCase(), t = r.to.toLowerCase(), fw = S.wallets.has(f), tw = S.wallets.has(t);
        if (fw || tw) S.xfers.push({ f, t, fw, tw, v: BigInt(r.value), ts: Number(r.timeStamp), blk: Number(r.blockNumber), tx: r.hash.toLowerCase(), q: q++ });
      }, 'usde transfers', log);
    S.counts.transfers_scanned = scanned;
    return S;
  }

  // AllowanceSpent logs in USDe whose destination is NOT a settlement address. Not counted as spend.
  // The summary names each destination by a label and says whether it is itself a programme wallet.
  // The addresses are returned apart from it, for private review.
  async function scanOtherDestinations(fetchFn, S, log) {
    const api = makeApi(fetchFn), SET = new Set(SETTLE), spenders = new Set(S.spends.map(e => e.w));
    const by = new Map(); let total = 0, toSettlement = 0;
    const rowsAll = [];
    // this scan starts at block 0 so that nothing before the first wallet is missed
    await walk(api,
      (from, to) => ({ module: 'logs', action: 'getLogs', fromBlock: from, toBlock: to, topic0: T_SPENT, topic0_1_opr: 'and', topic1: pad(USDE), page: 1, offset: 1000 }),
      1000, r => parseInt(r.blockNumber), r => rowsAll.push(r), 'all usde AllowanceSpent logs', log, 0);
    for (const l of rowsAll) {
      total++;
      const to = '0x' + l.topics[2].slice(26).toLowerCase();
      if (SET.has(to)) { toSettlement++; continue; }
      const w = l.address.toLowerCase(), isW = S.wallets.has(w), ts = parseInt(l.timeStamp), amt = BigInt(l.data);
      let o = by.get(to);
      if (!o) { o = { to, events: 0, events_from_programme_wallets: 0, wei_from_programme_wallets: 0n, wallets: new Set(), first_ts: null, last_ts: null }; by.set(to, o); }
      o.events++;
      if (isW) {
        o.events_from_programme_wallets++; o.wei_from_programme_wallets += amt; o.wallets.add(w);
        o.first_ts = o.first_ts === null ? ts : Math.min(o.first_ts, ts); o.last_ts = o.last_ts === null ? ts : Math.max(o.last_ts, ts);
      }
    }
    const found = [...by.values()].filter(o => o.events_from_programme_wallets > 0)
      .sort((a, b) => b.events_from_programme_wallets - a.events_from_programme_wallets || (a.to < b.to ? -1 : 1));
    const rows = found.map((o, i) => ({
      destination: 'destination ' + (i + 1), destination_is_programme_wallet: S.wallets.has(o.to),
      events_from_programme_wallets: o.events_from_programme_wallets,
      usde_from_programme_wallets: weiToDec(o.wei_from_programme_wallets), programme_wallets: o.wallets.size,
      of_which_never_spent_to_a_settlement_address: [...o.wallets].filter(w => !spenders.has(w)).length,
      first: iso(o.first_ts), last: iso(o.last_ts),
    }));
    const allW = new Set(); for (const o of found) for (const w of o.wallets) allW.add(w);
    const fromW = rows.reduce((s, r) => s + r.events_from_programme_wallets, 0);
    return {
      summary: {
        usde_allowance_spent_logs_block_0_to_end: total, to_a_settlement_address: toSettlement, to_any_other_destination: total - toSettlement,
        other_from_programme_wallets: fromW,
        // the rest were emitted by addresses that are not programme wallets, and are listed nowhere below
        other_from_addresses_that_are_not_programme_wallets: total - toSettlement - fromW,
        other_destinations_with_no_event_from_a_programme_wallet: by.size - found.length,
        programme_wallets_with_other_destination_events: allW.size,
        of_which_never_spent_to_a_settlement_address: [...allW].filter(w => !spenders.has(w)).length,
        destinations: rows,
      },
      addresses: found.map((o, i) => ({ destination: 'destination ' + (i + 1), address: o.to, is_programme_wallet: S.wallets.has(o.to) })),
    };
  }

  function weiToDec(v) {
    const neg = v < 0n; if (neg) v = -v;
    const s = v.toString().padStart(19, '0');
    const out = s.slice(0, -18) + '.' + s.slice(-18);
    return (neg ? '-' : '') + out.replace(/\.?0+$/, '');
  }

  // Reads balanceOf on the USDe contract for every wallet at one block, 500 wallets per call through Multicall3,
  // and compares each with the balance built from the transfer history.
  async function verifyBalances(fetchFn, wallets, expected, blockNumber, log) {
    const tag = '0x' + blockNumber.toString(16), CHUNK = 500;
    const word = v => BigInt(v).toString(16).padStart(64, '0');
    const res = { block: blockNumber, wallets_checked: 0, mismatches: [], wallets_with_balance: 0, sum_wei: 0n };
    for (let i = 0; i < wallets.length; i += CHUNK) {
      const part = wallets.slice(i, i + CHUNK), n = part.length;
      // aggregate3((address target, bool allowFailure, bytes callData)[]) with callData = balanceOf(wallet)
      let data = '0x82ad56cb' + word(32) + word(n);
      for (let k = 0; k < n; k++) data += word(n * 32 + k * 192);
      for (const a of part) data += word(USDE) + word(0) + word(96) + word(36) + '70a08231' + word(a) + '0'.repeat(56);
      const body = JSON.stringify({ jsonrpc: '2.0', id: i, method: 'eth_call', params: [{ to: MULTICALL3, data }, tag] });
      let hex = null;
      for (let t = 0; t < 7 && !hex; t++) {
        try {
          const r = await fetchFn(RPC, { method: 'POST', headers: { 'content-type': 'application/json' }, body });
          if (r.ok) { const j = await r.json(); if (j && typeof j.result === 'string' && j.result.length === 2 + 64 * (2 + 5 * n)) hex = j.result.slice(2); }
        } catch (e) { /* retry */ }
        if (!hex) await sleep(1500 * (t + 1));
      }
      if (!hex) throw new Error('rpc call failed at wallet ' + i);
      const at = w => BigInt('0x' + hex.slice(w * 64, w * 64 + 64));
      part.forEach((a, k) => {
        const start = 2 + Number(at(2 + k)) / 32, b = start + Number(at(start + 1)) / 32;
        if (at(start) !== 1n || at(b) !== 32n) throw new Error('balanceOf failed for ' + a);
        const on = at(b + 1), exp = expected.get(a) || 0n;
        res.wallets_checked++;
        if (on > 0n) { res.wallets_with_balance++; res.sum_wei += on; }
        if (on !== exp) res.mismatches.push({ wallet: a, on_chain_wei: on.toString(), from_transfers_wei: exp.toString() });
      });
      if (log) log('balanceOf at block ' + blockNumber + ': ' + res.wallets_checked + ' of ' + wallets.length);
    }
    res.sum_wei = res.sum_wei.toString();
    return res;
  }

  // ---------------------------------------------------------------- the calculation
  async function analyze(S) {
    const C16 = 10n ** 16n, E18 = 10n ** 18n;
    const SETS = new Set(SETTLE), OTH = new Set(OTHER_REWARD);
    const files = {};

    // Wallets in creation order. The position in this list is the wallet number used in every output file.
    const wl = [...S.wallets.entries()].map(([a, o]) => ({ a, ts: o.ts, blk: o.blk, gen: o.gen }))
      .sort((x, y) => x.blk - y.blk || (x.a < y.a ? -1 : x.a > y.a ? 1 : 0));
    const wid = new Map(); wl.forEach((w, i) => wid.set(w.a, i));
    const N = wl.length;
    for (let i = 1; i < N; i++) if (wl[i].ts < wl[i - 1].ts) throw new Error('wallet timestamps are not in block order');

    const sp = S.spends, xs = S.xfers;
    for (let i = 1; i < sp.length; i++) {
      if (sp[i].blk < sp[i - 1].blk || (sp[i].blk === sp[i - 1].blk && sp[i].li <= sp[i - 1].li)) throw new Error('spend events out of order or duplicated at ' + i);
    }
    for (const e of sp) {
      if (!wid.has(e.w)) throw new Error('spend event from an address that is not a programme wallet: ' + e.w);
      if (e.amt % C16 !== 0n) throw new Error('spend amount is not a whole number of cents');
    }
    for (let i = 1; i < xs.length; i++) if (xs[i].blk < xs[i - 1].blk || xs[i].ts < xs[i - 1].ts) throw new Error('transfers out of order at ' + i);

    const lowerBound = (n, pred) => { let lo = 0, hi = n; while (lo < hi) { const m = (lo + hi) >> 1; if (pred(m)) lo = m + 1; else hi = m; } return lo; };
    const createdAtBlock = b => lowerBound(N, m => wl[m].blk <= b);
    const createdAtTime = t => lowerBound(N, m => wl[m].ts <= t);
    const createdBefore = t => lowerBound(N, m => wl[m].ts < t);
    const xferPrefixByBlock = b => lowerBound(xs.length, m => xs[m].blk <= b);
    const xferPrefixByTime = t => lowerBound(xs.length, m => xs[m].ts <= t);

    // Where each dashboard snapshot sits on the chain: the block of the last spend event it had counted.
    const cuts = SNAP.map(([id, gen, C]) => {
      if (C > sp.length) throw new Error('snapshot ' + id + ' reports more events than the chain holds');
      const last = sp[C - 1], next = sp[C] || null;
      return { id, generated: iso(gen), generated_ts: gen, events_reported: C, cut_block: last.blk, cut_time: iso(last.ts), cut_ts: last.ts,
               seconds_before_generated: gen - last.ts, next_event_time: next ? iso(next.ts) : null,
               boundary_between_blocks: !next || next.blk !== last.blk,
               events_on_chain_at_generated_time: lowerBound(sp.length, m => sp[m].ts <= gen) };
    });

    function spendMetrics(C, gen) {
      const runDay = Math.floor(gen / DAY), s30 = (runDay - 30) * DAY, s7 = (runDay - 7) * DAY;
      let cents = 0n, cents30 = 0n; const all = new Set(), m30 = new Set(), m7 = new Set(), perTx = new Map();
      for (let i = 0; i < C; i++) {
        const e = sp[i], c = e.amt / C16; cents += c; all.add(e.w);
        if (e.ts >= s30) { m30.add(e.w); cents30 += c; }
        if (e.ts >= s7) m7.add(e.w);
        perTx.set(e.tx, (perTx.get(e.tx) || 0) + 1);
      }
      let maxTx = 0, batched = 0; const hist = {};
      for (const n of perTx.values()) { if (n > maxTx) maxTx = n; if (n > 1) batched += n; hist[n] = (hist[n] || 0) + 1; }
      return { spend_events: C, spend_cents: cents.toString(), wallets_ever_spent: all.size, wallets_spent_30d: m30.size, wallets_spent_7d: m7.size,
               spend_cents_30d: cents30.toString(), window_30d_starts: iso(s30), window_7d_starts: iso(s7),
               transactions: perTx.size, max_events_in_one_transaction: maxTx, events_in_multi_event_transactions: batched, transactions_by_event_count: hist };
    }

    // ---- balances: one pass over the transfers with a checkpoint at every day end and every snapshot
    const lastTs = Math.max(wl[N - 1].ts, sp.length ? sp[sp.length - 1].ts : 0, xs.length ? xs[xs.length - 1].ts : 0);
    const lastDay = Math.floor(lastTs / DAY) - DAY0;
    const cps = [];
    for (let d = 0; d <= lastDay; d++) cps.push({ kind: 'day', d, p: xferPrefixByTime((DAY0 + d + 1) * DAY - 1) });
    cuts.forEach((c, k) => {
      cps.push({ kind: 'cut', k, p: xferPrefixByBlock(c.cut_block), full: true });
      cps.push({ kind: 'gen', k, p: xferPrefixByTime(c.generated_ts), full: false });
    });
    cps.forEach((c, i) => { c.i = i; });
    cps.sort((a, b) => a.p - b.p || a.i - b.i);

    const bal = new Map(), balF = new Map(), firstIn = new Map(), flows = new Map();
    const flowOf = d => { let f = flows.get(d); if (!f) { f = { dep: 0n, wd: 0n, rev: 0n, yld: 0n, oth: 0n, card: 0n, intl: 0n, depW: new Set(), nCard: 0 }; flows.set(d, f); } return f; };
    function apply(x) {
      const f = flowOf(Math.floor(x.ts / DAY) - DAY0);
      let cls;
      if (x.fw && x.tw) { f.intl += x.v; cls = 'i'; }
      else if (x.tw) {
        if (SETS.has(x.f)) { f.rev += x.v; cls = 'r'; }
        else if (x.f === YIELD) { f.yld += x.v; cls = 'y'; }
        else if (OTH.has(x.f)) { f.oth += x.v; cls = 'o'; }
        else { f.dep += x.v; f.depW.add(x.t); cls = 'd'; }
      } else if (SETS.has(x.t)) { f.card += x.v; f.nCard++; }
      else f.wd += x.v;
      if (x.fw) { bal.set(x.f, (bal.get(x.f) || 0n) - x.v); balF.set(x.f, (balF.get(x.f) || 0) - Number(x.v) / 1e18); }
      if (x.tw) {
        bal.set(x.t, (bal.get(x.t) || 0n) + x.v); balF.set(x.t, (balF.get(x.t) || 0) + Number(x.v) / 1e18);
        if (!firstIn.has(x.t)) firstIn.set(x.t, [x.ts, cls, cls === 'i' ? x.f : null]);
      }
    }
    function stats(full) {
      const pos = []; let neg = 0, fpos = 0, fneg = 0, ftvl = 0;
      for (const [a, v] of bal) { if (v > 0n) pos.push([v, a]); else if (v < 0n) neg++; }
      for (const v of balF.values()) { if (v > 0) { fpos++; ftvl += v; } else if (v < 0) fneg++; }
      pos.sort((x, y) => (x[0] > y[0] ? -1 : x[0] < y[0] ? 1 : (x[1] < y[1] ? -1 : 1)));
      let tvl = 0n; for (const q of pos) tvl += q[0];
      const top = n => { let s = 0n; for (let i = 0; i < n && i < pos.length; i++) s += pos[i][0]; return s; };
      const ge = th => { let c = 0; while (c < pos.length && pos[c][0] >= th) c++; return c; };
      const o = { funded: pos.length, ge_1c: ge(C16), ge_1: ge(E18), ge_10: ge(10n * E18), ge_100: ge(100n * E18), ge_1k: ge(1000n * E18),
                  ge_10k: ge(10000n * E18), ge_100k: ge(100000n * E18), held_wei: tvl.toString(), top1_wei: top(1).toString(),
                  top10_wei: top(10).toString(), top50_wei: top(50).toString(), negative_balances: neg, wallets_ever_received: firstIn.size,
                  float_funded: fpos, float_negative: fneg, float_held: ftvl };
      if (full) o.top20 = pos.slice(0, 20).map(q => [wid.get(q[1]), q[0].toString()]);
      return o;
    }
    let p = 0, balAtLastCut = null, firstInAtLastCut = null;
    for (const cp of cps) {
      while (p < cp.p) apply(xs[p++]);
      cp.stats = stats(cp.full);
      if (cp.kind === 'cut' && cp.k === cuts.length - 1) { balAtLastCut = new Map(bal); firstInAtLastCut = new Map(firstIn); }
    }
    while (p < xs.length) apply(xs[p++]);
    const balEnd = new Map(bal);

    // every card spend must also appear as a USDe transfer from the wallet to the settlement address
    let cardN = 0, cardWei = 0n; for (const x of xs) if (x.fw && !x.tw && SETS.has(x.t)) { cardN++; cardWei += x.v; }
    let spendWei = 0n; for (const e of sp) spendWei += e.amt;

    // ---- snapshots file
    const snaps = cuts.map((c, k) => {
      const cut = cps.find(q => q.kind === 'cut' && q.k === k).stats, gen = cps.find(q => q.kind === 'gen' && q.k === k).stats;
      const runDay = Math.floor(c.generated_ts / DAY), s30 = (runDay - 30) * DAY;
      const createdCut = createdAtBlock(c.cut_block);
      return Object.assign({}, c,
        { wallets_created_at_cut_block: createdCut, wallets_created_at_generated_time: createdAtTime(c.generated_ts),
          wallets_created_since_30d_window_start: createdCut - createdBefore(s30) },
        spendMetrics(c.events_reported, c.generated_ts), { balances_at_cut_block: cut, balances_at_generated_time: gen });
    });
    files['snapshots_chain.json'] = JSON.stringify(snaps, null, 1) + '\n';

    // ---- wallets file: one row per wallet in creation order. factory 0 is the first (pilot) factory, 1 the second.
    files['wallets_created.csv'] = 'wallet,created_ts,factory\n' + wl.map((w, i) => i + ',' + w.ts + ',' + w.gen).join('\n') + '\n';

    // ---- spend events grouped by day, snapshot segment and wallet
    // segment = how many of the nine snapshots had already counted past this event's position. An event belongs to
    // snapshot number j (counting from 0) when its segment is j or lower. Segment 9 is after the last snapshot.
    const bounds = SNAP.map(s => s[2]);
    const wd = new Map();
    sp.forEach((e, i) => {
      let seg = 0; while (seg < bounds.length && i >= bounds[seg]) seg++;
      const d = Math.floor(e.ts / DAY) - DAY0, key = d + ',' + seg + ',' + wid.get(e.w);
      let o = wd.get(key); if (!o) { o = { d, seg, w: wid.get(e.w), n: 0, c: 0n }; wd.set(key, o); }
      o.n++; o.c += e.amt / C16;
    });
    const wdRows = [...wd.values()].sort((a, b) => a.d - b.d || a.seg - b.seg || a.w - b.w);
    files['spend_wallet_days.csv'] = 'day,segment,wallet,events,cents\n' + wdRows.map(o => o.d + ',' + o.seg + ',' + o.w + ',' + o.n + ',' + o.c).join('\n') + '\n';

    // ---- one row per wallet that ever received USDe or ever spent
    const firstSpend = new Map(); for (const e of sp) if (!firstSpend.has(e.w)) firstSpend.set(e.w, e.ts);
    const act = new Set([...firstIn.keys(), ...firstSpend.keys(), ...balEnd.keys()]);
    const actRows = [...act].map(a => ({ w: wid.get(a), a })).sort((x, y) => x.w - y.w);
    files['wallet_activity.csv'] = 'wallet,first_usde_in_ts,first_in_kind,first_spend_ts,balance_wei_at_last_snapshot\n' +
      actRows.map(r => { const fi = firstIn.get(r.a); return [r.w, fi ? fi[0] : '', fi ? fi[1] : '', firstSpend.get(r.a) || '', (balAtLastCut.get(r.a) || 0n).toString()].join(','); }).join('\n') + '\n';

    // ---- one row per UTC day
    const newBy = new Map(); for (const w of wl) { const d = Math.floor(w.ts / DAY) - DAY0, o = newBy.get(d) || [0, 0]; o[w.gen]++; newBy.set(d, o); }
    const spBy = new Map(); for (const e of sp) { const d = Math.floor(e.ts / DAY) - DAY0; let o = spBy.get(d); if (!o) { o = { n: 0, c: 0n, w: new Set(), tx: new Set() }; spBy.set(d, o); } o.n++; o.c += e.amt / C16; o.w.add(e.w); o.tx.add(e.tx); }
    const everSpent = new Set(); let cumNew = 0;
    const dayRows = [];
    for (let d = 0; d <= lastDay; d++) {
      const nb = newBy.get(d) || [0, 0], so = spBy.get(d), f = flows.get(d), st = cps.find(q => q.kind === 'day' && q.d === d).stats;
      if (so) for (const a of so.w) everSpent.add(a);
      cumNew += nb[0] + nb[1];
      dayRows.push([new Date((DAY0 + d) * DAY * 1000).toISOString().slice(0, 10), d, nb[0], nb[1], cumNew,
        so ? so.n : 0, so ? so.w.size : 0, so ? so.c.toString() : '0', so ? so.tx.size : 0, everSpent.size,
        f ? f.dep : 0n, f ? f.wd : 0n, f ? f.rev : 0n, f ? f.yld : 0n, f ? f.oth : 0n, f ? f.card : 0n, f ? f.intl : 0n, f ? f.depW.size : 0,
        st.funded, st.ge_1c, st.ge_1, st.ge_10, st.ge_100, st.ge_1k, st.ge_10k, st.ge_100k, st.held_wei, st.top1_wei, st.top10_wei, st.top50_wei,
        st.negative_balances, st.wallets_ever_received, st.float_funded].join(','));
    }
    files['daily_chain.csv'] = 'date,day,new_wallets_v1,new_wallets_v2,wallets_created,spend_events,spending_wallets,spend_cents,spend_transactions,wallets_ever_spent,' +
      'deposits_wei,withdrawals_wei,reversals_wei,yield_wei,other_rewards_wei,card_spend_wei,internal_wei,depositing_wallets,' +
      'funded,ge_1c,ge_1,ge_10,ge_100,ge_1k,ge_10k,ge_100k,held_wei,top1_wei,top10_wei,top50_wei,negative_balances,wallets_ever_received,float_funded\n' + dayRows.join('\n') + '\n';

    // ---- who sent each wallet its first USDe, as of the last snapshot
    const C = SNAP[SNAP.length - 1][2];
    const firstFrom = { d: 0, i: 0, r: 0, y: 0, o: 0 }, seeders = new Map();
    for (const fi of firstInAtLastCut.values()) {
      firstFrom[fi[1]]++;
      if (fi[1] === 'i') seeders.set(fi[2], (seeders.get(fi[2]) || 0) + 1);
    }
    const seedCounts = [...seeders.values()].sort((x, y) => y - x);

    // ---- fingerprints of the raw rows, so a second run can prove it read the same data
    const hWallets = await sha256hex(wl.map(w => w.a + ',' + w.blk + ',' + w.ts + ',' + w.gen).join('\n'));
    const hSpends = await sha256hex(sp.map(e => e.blk + ',' + e.li + ',' + e.tx + ',' + e.w + ',' + e.amt + ',' + e.s).join('\n'));
    const hXfers = await sha256hex(xs.map(x => x.blk + ',' + x.tx + ',' + x.f + ',' + x.t + ',' + x.v).sort().join('\n'));

    const meta = {
      end_block: S.endBlock, start_block: START_BLOCK, day_0: '2026-05-15',
      factory_created_contracts: N + S.infra.length, wallets: N, wallets_v1: wl.filter(w => w.gen === 0).length, wallets_v2: wl.filter(w => w.gen === 1).length,
      other_factory_contracts: S.infra.map(r => ({ address: r.a, factory: r.gen === 0 ? 'v1' : 'v2', block: r.blk, time: iso(r.ts) })),
      first_wallet_created: iso(wl[0].ts), last_wallet_created: iso(wl[N - 1].ts),
      spend_events: sp.length, spend_events_current_settlement: sp.filter(e => e.s === 0).length, spend_events_retired_settlement: sp.filter(e => e.s === 1).length,
      first_spend_event: iso(sp[0].ts), last_spend_event: iso(sp[sp.length - 1].ts), spend_wei: spendWei.toString(),
      // spend events in chain order for each settlement address, named by role and never by address here
      settlement_addresses: SETTLE.map((a, s) => {
        const ev = sp.filter(e => e.s === s);
        return { role: s === 0 ? 'current' : 'retired', spend_events: ev.length, spend_cents: ev.reduce((t, e) => t + e.amt / C16, 0n).toString(),
                 first_spend_event: ev.length ? iso(ev[0].ts) : null, last_spend_event: ev.length ? iso(ev[ev.length - 1].ts) : null };
      }),
      usde_transfers_scanned: S.counts.transfers_scanned, usde_transfers_touching_wallets: xs.length,
      wallet_to_settlement_transfers: cardN, wallet_to_settlement_wei: cardWei.toString(),
      spend_events_equal_wallet_to_settlement_transfers: cardN === sp.length && cardWei === spendWei,
      wallets_that_ever_received_usde: firstIn.size, wallets_that_ever_spent: firstSpend.size,
      first_usde_received_at_last_snapshot: {
        wallets: firstInAtLastCut.size, from_outside_the_programme: firstFrom.d, from_another_programme_wallet: firstFrom.i,
        from_a_reversal_or_reward: firstFrom.r + firstFrom.y + firstFrom.o,
        programme_wallets_that_sent_a_first_usde: seeders.size, first_funded_by_the_largest_such_sender: seedCounts[0] || 0,
        first_funded_by_each_of_the_five_largest: seedCounts.slice(0, 5),
      },
      raw_row_sha256: { wallets: hWallets, spend_events: hSpends, transfers_touching_wallets: hXfers },
    };

    // ---- addresses of the largest holders and spenders at the last snapshot. For private review only.
    const lastCut = cps.find(q => q.kind === 'cut' && q.k === cuts.length - 1).stats;
    const spentBy = new Map(); for (let i = 0; i < C; i++) { const e = sp[i], o = spentBy.get(e.w) || { n: 0, c: 0n }; o.n++; o.c += e.amt / C16; spentBy.set(e.w, o); }
    const review = {
      note: 'Addresses of the largest holders and spenders at the last snapshot. For private review. Not for publication.',
      largest_balances: lastCut.top20.map(([w, wei]) => ({ wallet: w, address: wl[w].a, usde: weiToDec(BigInt(wei)), created: iso(wl[w].ts), events: (spentBy.get(wl[w].a) || { n: 0 }).n })),
      largest_spenders: [...spentBy.entries()].sort((a, b) => (a[1].c > b[1].c ? -1 : a[1].c < b[1].c ? 1 : 0)).slice(0, 20)
        .map(([a, o]) => ({ wallet: wid.get(a), address: a, spend_cents: o.c.toString(), events: o.n, created: iso(S.wallets.get(a).ts) })),
    };

    return { files, meta, review, wl, wid, balAtLastCut, balEnd, cuts };
  }

  // ---------------------------------------------------------------- the whole run
  // Reads the chain, runs the calculation and returns the six files as text, with their sizes and SHA-256.
  // The review addresses are returned apart from the files and are never written into them.
  async function run(fetchFn, log) {
    const S = await load(fetchFn, log);
    const R = await analyze(S);
    const lastCut = R.cuts[R.cuts.length - 1];
    const od = await scanOtherDestinations(fetchFn, S, log);
    R.meta.other_destinations = od.summary;
    R.review.other_destinations = od.addresses;
    const atCut = R.wl.filter(w => w.blk <= lastCut.cut_block).map(w => w.a);
    const v = await verifyBalances(fetchFn, atCut, R.balAtLastCut, lastCut.cut_block, log);
    v.mismatch_count = v.mismatches.length; v.mismatches = v.mismatches.slice(0, 10).map(m => ({ wallet: R.wid.get(m.wallet), on_chain_wei: m.on_chain_wei, from_transfers_wei: m.from_transfers_wei }));
    R.meta.balance_check = v;
    R.files['meta.json'] = JSON.stringify(R.meta, null, 1) + '\n';
    const hashes = {};
    for (const [name, text] of Object.entries(R.files)) hashes[name] = { bytes: new TextEncoder().encode(text).length, sha256: await sha256hex(text) };
    return { files: R.files, hashes, review: R.review };
  }

  // ---------------------------------------------------------------- Node entry point
  async function main() {
    const fs = require('fs'), path = require('path');
    const dir = path.join(__dirname, 'inputs', 'chain');
    fs.mkdirSync(dir, { recursive: true });
    const log = m => console.log(new Date().toISOString().slice(11, 19), m);
    const out = await run(globalThis.fetch, log);
    for (const [name, text] of Object.entries(out.files)) { fs.writeFileSync(path.join(dir, name), text); log('wrote ' + name + ' ' + out.hashes[name].bytes + ' bytes ' + out.hashes[name].sha256.slice(0, 12)); }
    const k = process.argv.indexOf('--review-addresses');
    if (k > 0 && process.argv[k + 1]) fs.writeFileSync(path.resolve(process.argv[k + 1]), JSON.stringify(out.review, null, 1) + '\n');
  }

  return { load, analyze, scanOtherDestinations, verifyBalances, run, main, sha256hex, weiToDec, config: CFG, SNAP, SETTLE, FACTORIES, USDE, START_BLOCK, END_BLOCK, DAY0 };
})();
if (typeof module !== 'undefined' && typeof require === 'function' && require.main === module) {
  globalThis.EPR.main().catch(e => { console.error(e); process.exit(1); });
}
