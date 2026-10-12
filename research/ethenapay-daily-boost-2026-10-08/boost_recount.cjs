/*
 boost_recount.cjs

 Sets the USDe rewards paid to EthenaPay wallets against each wallet's time-weighted balance on each
 accrual day from September 1 to October 8, 2026, and against its card spend in the calendar month.
 It reads three things from Avalanche C-Chain through block 97,161,009, the last block of October 9, 2026 UTC.

   1. Every contract the two wallet factories created               (explorer API, txlistinternal)
   2. Every USDe Transfer that touches one of those wallets         (explorer API, tokentx)
   3. Every AllowanceSpent log to either settlement address, any token (explorer API, getLogs)

 It writes the files in inputs/chain/, which ethenapay_boost_review.py reads. Wallets appear in them as a
 position number in creation order, the numbering of the chain recount published with the EthenaPay
 adoption review. No wallet's address is written.

 Run it with Node 18 or later:   node boost_recount.cjs
 The same code runs unchanged in a browser console on a page that allows the requests, as
 EPB.run(fetch.bind(window), console.log), which returns the files as text. That is how the files in
 this packet were produced. main() below calls the same run() and only adds the write to disk.

 Rules, from the dashboard's daily query and the chain recount
   wallet         a contract a factory created with CREATE2
   card spend     a USDe transfer from a wallet to either settlement address
   base account   the account the dashboard's query labels yield
   top-up account either account the query labels other rewards
   accrual day    midnight to midnight UTC, which the payments fit best. The files also give each
                  wallet's balance over days that start at midnight in Central Europe, 23:00 and
                  22:00 UTC, which fit fewer payments
   calendar month the same, so October began at 00:00 UTC on October 1
   tested wallet  one whose balance averaged at least 100 USDe over the days a payment covers, enough
                  for a 0.5% top-up to reach 0.001 USDe a day, the smallest payment the chain shows
   exchanged with another wallet that sent the wallet USDe or received USDe from it, at any time to the
                  end of the read. The chain shows wallets, not people, and a person can hold two wallets

 The paging in walk() and the request retry in makeApi() are the chain recount's, unchanged.
*/
globalThis.EPB = (() => {
  'use strict';
  const API = 'https://api.routescan.io/v2/network/mainnet/evm/43114/etherscan/api';
  const USDE = '0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34';
  const FACTORIES = ['0x313be708df16979d9e5fe9db5ac4969b8add7207',     // v1 pilot factory
                     '0xac66ca9a79fb0d3c64cba44cd29610cd58602d6f'];    // v2 current factory
  const SETTLE = ['0x6070848bd19c37488d0516058f2933dd992733de',        // current settlement address
                  '0x3b3ffd99b87a2dee5ad244b75d5a8e266890fdb8'];       // retired settlement address
  const BASE = '0xd0ec8cc7414f27ce85f8dece6b4a58225f273311';           // labeled yield in the dashboard's query
  const TOPUP = ['0xab2b06efa6179e624f5e3b08b64978df114ff24f',          // labeled other rewards
                 '0xc9dd0d4351d3841a712f59cb4f1e88c3d500515b'];         // the pilot's other-reward account
  const T_SPENT = '0xa575fb45e6259a68f4974e75c94adc55a35f2c06eee07709e964a4407e7dcfeb';   // AllowanceSpent(address,address,uint256)
  const START_BLOCK = 85400000;          // before the first factory call on May 15, 2026
  const END_BLOCK = 97161009;            // last block of October 9, 2026 UTC
  const RECOUNT_BLOCK = 96815525;        // the adoption review's balance snapshot, 15:53:28 UTC October 5
  const RECOUNT_LAST_DAY = 143;          // October 5, the recount's last UTC day
  const DAY = 86400;
  const utc = (y, m, d, hh, mm, ss) => Date.UTC(y, m - 1, d, hh || 0, mm || 0, ss || 0) / 1000;
  const DAY0 = Math.floor(utc(2026, 5, 15) / DAY);        // UTC day 0 is 2026-05-15
  const SHIFTS = { utc: 0, cet: 3600, cest: 7200 };      // seconds an accrual day starts before UTC midnight
  const MAIN = 'utc';
  const FIRST_DATE = utc(2026, 9, 1);                     // calendar date of accrual day 0
  const N_DAYS = 38;                                      // September 1 to October 8
  const MONTH_STARTS = [utc(2026, 8, 1), utc(2026, 9, 1), utc(2026, 10, 1), utc(2026, 11, 1)];
  const SNAPSHOT_DAYS = [30, 37];                         // October 1 and October 8
  const E18 = 10n ** 18n;
  const TESTED_MIN = 100n * E18;                          // average balance at which a 0.5% top-up clears 0.001 USDe a day
  const CAPS = { standard: 5000n * E18, pro: 100000n * E18, vip: 1000000n * E18 };
  const TOL = 0.01;                                       // a payment fits a model within 1% of it
  const TOL_LOOSE = 0.05;                                 // a looser count, for wallets whose balance moved during the day
  const GAP = 3 * 3600;                                   // transfers from one account more than 3 hours apart start a new batch

  const CFG = { retryMs: 900 };
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const iso = t => new Date(t * 1000).toISOString().slice(0, 19) + 'Z';
  const pad = a => '0x' + a.slice(2).toLowerCase().padStart(64, '0');
  const dateOf = t => new Date(t * 1000).toISOString().slice(0, 10);

  // daily factor of an annual rate compounded daily
  const daily = r => Math.pow(1 + r, 1 / 365) - 1;
  // name, annual rate, cap on the time-weighted balance; tried in this order and the first that fits names the payment
  const BASE_MODELS = [['base_4_5', 0.045, null], ['base_4_0', 0.04, null]];
  const TOPUP_MODELS = [['standard_0_5', 0.005, 'standard'], ['standard_1_0', 0.01, 'standard'], ['six_1_5', 0.015, 'vip'],
                        ['six_2_0', 0.02, 'vip'], ['six_1_5_cap_100k', 0.015, 'pro'], ['six_2_0_cap_100k', 0.02, 'pro']];
  const MODELS = Object.fromEntries([...BASE_MODELS, ...TOPUP_MODELS].map(([n, r]) => [n, daily(r)]));

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
    const S = { wallets: new Map(), infra: [], xfers: [], counts: {} };
    // END_BLOCK must be the last block before 00:00 UTC on October 10
    const blockTs = async b => {
      for (let i = 0; i < 6; i++) {
        try {
          const r = await fetchFn(API + '?module=proxy&action=eth_getBlockByNumber&tag=0x' + b.toString(16) + '&boolean=false');
          if (r.ok) { const j = await r.json(); if (j && j.result && j.result.timestamp) return parseInt(j.result.timestamp, 16); }
        } catch (e) { /* retry */ }
        await sleep(CFG.retryMs * (i + 1));
      }
      throw new Error('no timestamp for block ' + b);
    };
    const endTs = await blockTs(END_BLOCK), nextTs = await blockTs(END_BLOCK + 1);
    if (!(endTs < utc(2026, 10, 10) && nextTs >= utc(2026, 10, 10))) throw new Error('block ' + END_BLOCK + ' is not the last block of October 9 UTC');
    S.counts.end_block_time = iso(endTs); S.counts.next_block_time = iso(nextTs);
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
    // every AllowanceSpent log to a settlement address, whatever its token, to show which token card debits use
    S.cardTokens = {};
    for (let s = 0; s < SETTLE.length; s++) {
      const byToken = {};
      await walk(api,
        (from, to) => ({ module: 'logs', action: 'getLogs', fromBlock: from, toBlock: to, topic0: T_SPENT, topic0_2_opr: 'and', topic2: pad(SETTLE[s]), page: 1, offset: 1000 }),
        1000, r => parseInt(r.blockNumber), r => {
          if (String(r.topics[0]).toLowerCase() !== T_SPENT || String(r.topics[2]).toLowerCase() !== pad(SETTLE[s])) throw new Error('log does not match the filter');
          const tok = '0x' + String(r.topics[1]).slice(26).toLowerCase();
          byToken[tok] = (byToken[tok] || 0) + 1;
        }, 'settlement logs ' + s, log);
      S.cardTokens[s === 0 ? 'current_settlement' : 'retired_settlement'] = byToken;
    }
    return S;
  }

  // ---------------------------------------------------------------- the calculation
  async function analyze(S) {
    const SETS = new Set(SETTLE), TOP = new Set(TOPUP);
    const files = {};

    // positions in creation order, the chain recount's numbering
    const wl = [...S.wallets.entries()].map(([a, o]) => ({ a, ts: o.ts, blk: o.blk, gen: o.gen }))
      .sort((x, y) => x.blk - y.blk || (x.a < y.a ? -1 : x.a > y.a ? 1 : 0));
    const wid = new Map(); wl.forEach((w, i) => wid.set(w.a, i));
    const xs = S.xfers;
    for (let i = 1; i < xs.length; i++) if (xs[i].blk < xs[i - 1].blk || xs[i].ts < xs[i - 1].ts) throw new Error('transfers out of order at ' + i);
    // USDe sent from a wallet back to a reward account would show a reward clawed back
    const REWARD = new Set([BASE, ...TOPUP]);
    let backN = 0, backWei = 0n;
    for (const x of xs) if (x.fw && REWARD.has(x.t)) { backN++; backWei += x.v; }

    // each transfer as one or two wallet events: kind d deposit, w withdrawal, c card spend, r reversal,
    // b base payment, t top-up payment, i internal in, j internal out
    const ev = new Map();
    const push = (a, e) => { let l = ev.get(a); if (!l) { l = []; ev.set(a, l); } l.push(e); };
    const flows = new Map();   // UTC day -> sums, for the cross-check with the recount
    const flowOf = d => { let f = flows.get(d); if (!f) { f = { dep: 0n, wd: 0n, rev: 0n, yld: 0n, oth: 0n, card: 0n, intl: 0n }; flows.set(d, f); } return f; };
    const payments = { base: [], topup: [] };
    for (const x of xs) {
      const f = flowOf(Math.floor(x.ts / DAY) - DAY0);
      if (x.fw && x.tw) {
        f.intl += x.v;
        push(x.f, { ts: x.ts, blk: x.blk, q: x.q, dv: -x.v, k: 'j' });
        push(x.t, { ts: x.ts, blk: x.blk, q: x.q, dv: x.v, k: 'i', inc: true });
      } else if (x.tw) {
        let k;
        if (SETS.has(x.f)) { f.rev += x.v; k = 'r'; }
        else if (x.f === BASE) { f.yld += x.v; k = 'b'; payments.base.push({ ts: x.ts, w: x.t, v: x.v, tx: x.tx }); }
        else if (TOP.has(x.f)) { f.oth += x.v; k = 't'; payments.topup.push({ ts: x.ts, w: x.t, v: x.v, tx: x.tx, from: x.f }); }
        else { f.dep += x.v; k = 'd'; }
        push(x.t, { ts: x.ts, blk: x.blk, q: x.q, dv: x.v, k, inc: true });
      } else {
        const k = SETS.has(x.t) ? 'c' : 'w';
        if (k === 'c') f.card += x.v; else f.wd += x.v;
        push(x.f, { ts: x.ts, blk: x.blk, q: x.q, dv: -x.v, k });
      }
    }
    for (const l of ev.values()) l.sort((a, b) => a.ts - b.ts || a.q - b.q);

    // ---- cross-check 1: the recount's wallet rows, first USDe in and balance at its snapshot block
    const recountEndTs = (DAY0 + RECOUNT_LAST_DAY + 1) * DAY;   // first second after October 5 UTC
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

    // ---- cross-check 2: daily flows and USDe held at each UTC day end, May 15 to October 5
    const lastDay = Math.floor(utc(2026, 10, 9) / DAY) - DAY0;
    const heldAt = new Array(lastDay + 1).fill(0n);
    for (const l of ev.values()) {
      let bal = 0n, p = 0;
      for (let d = 0; d <= lastDay; d++) {
        const end = (DAY0 + d + 1) * DAY;
        while (p < l.length && l[p].ts < end) bal += l[p++].dv;
        if (bal > 0n) heldAt[d] += bal;
      }
    }
    const flowLine = d => { const f = flows.get(d) || flowOf(d); return [dateOf((DAY0 + d) * DAY), f.dep, f.wd, f.rev, f.yld, f.oth, f.card, f.intl, heldAt[d]].join(','); };
    const flowsCanon = [...Array(RECOUNT_LAST_DAY + 1).keys()].map(flowLine).join('\n') + '\n';
    files['utc_days_after_recount.csv'] = 'date,deposits_wei,withdrawals_wei,reversals_wei,base_wei,topup_wei,card_spend_wei,internal_wei,held_wei\n' +
      [...Array(lastDay - RECOUNT_LAST_DAY).keys()].map(i => flowLine(RECOUNT_LAST_DAY + 1 + i)).join('\n') + '\n';

    // ---- accrual days: time-weighted balance, end balance and other flows for each wallet and day
    const startOf = (k, shift) => FIRST_DATE + k * DAY - SHIFTS[shift];
    const twa = {}, eod = new Map(), moved = new Map();
    for (const shift of Object.keys(SHIFTS)) {
      const m = new Map();
      for (const [a, l] of ev) {
        const arr = new Array(N_DAYS).fill(0n);
        let bal = 0n, p = 0;
        const s0 = startOf(0, shift);
        while (p < l.length && l[p].ts < s0) bal += l[p++].dv;
        let any = false;
        for (let k = 0; k < N_DAYS; k++) {
          const s = startOf(k, shift), e = s + DAY;
          let acc = 0n, t = s;
          while (p < l.length && l[p].ts < e) { acc += bal * BigInt(l[p].ts - t); t = l[p].ts; bal += l[p++].dv; }
          acc += bal * BigInt(e - t);
          arr[k] = acc / BigInt(DAY);
          if (arr[k] !== 0n) any = true;
          if (shift === MAIN) {
            let eo = eod.get(a); if (!eo) { eo = new Array(N_DAYS).fill(0n); eod.set(a, eo); }
            eo[k] = bal;
          }
        }
        if (any) m.set(a, arr);
      }
      twa[shift] = m;
    }
    for (const [a, l] of ev) {
      const fl = new Array(N_DAYS).fill(false);
      for (const e of l) {
        if (e.k === 'b' || e.k === 't') continue;
        const k = Math.floor((e.ts - startOf(0, MAIN)) / DAY);
        if (k >= 0 && k < N_DAYS) fl[k] = true;
      }
      moved.set(a, fl);
    }

    // ---- card spend by calendar month, on the accrual days' boundaries
    const monthOf = t => { let i = -1; for (let j = 0; j < MONTH_STARTS.length; j++) if (t >= MONTH_STARTS[j] - SHIFTS[MAIN]) i = j; return i; };
    const cardTs = new Map();
    for (const [a, l] of ev) { const c = l.filter(e => e.k === 'c').map(e => e.ts); if (c.length) cardTs.set(a, c); }
    function activity(a, k) {
      const end = startOf(k, MAIN) + DAY, mk = monthOf(startOf(k, MAIN));
      const ms = MONTH_STARTS[mk] - SHIFTS[MAIN], ps = MONTH_STARTS[mk - 1] - SHIFTS[MAIN];
      let month = 0, prev = 0, earlier = 0;
      for (const t of cardTs.get(a) || []) {
        if (t >= end) break;
        if (t >= ms) month++; else if (t >= ps) prev++; else earlier++;
      }
      const cls = month ? 'A' : prev ? 'B' : earlier ? 'C' : 'D';
      return { month, prev, earlier, cls };
    }

    // ---- payment batches and the accrual days each one covers
    const batches = [], periods = [];
    for (const payer of ['base', 'topup']) {
      const ps = payments[payer];
      let cur = null;
      const bl = [];
      for (const p of ps) {
        if (!cur || p.ts - cur.last > GAP) { cur = { payer, first: p.ts, last: p.ts, rows: [] }; bl.push(cur); }
        cur.last = p.ts; cur.rows.push(p);
      }
      let covered = -1, period = null;
      for (const b of bl) {
        let lastEnded = -1;
        for (let k = 0; k < N_DAYS + 2; k++) if (startOf(k, MAIN) + DAY <= b.first) lastEnded = k;
        b.from = null; b.to = null;
        if (lastEnded < 0) continue;                       // pays for days before September 1
        if (lastEnded > covered && covered + 1 < N_DAYS) {
          period = { payer, id: periods.filter(x => x.payer === payer).length, from: covered + 1, to: Math.min(lastEnded, N_DAYS - 1), batches: [] };
          periods.push(period); covered = period.to;
        } else if (!period || lastEnded > N_DAYS - 1) continue;   // a later day than the window, or nothing to join
        period.batches.push(b); b.from = period.from; b.to = period.to;
      }
      for (const b of bl) batches.push(b);
    }

    // ---- each period, wallet by wallet
    const fits = (paid, expect, tol) => expect > 0 && Math.abs(paid / expect - 1) <= tol;
    const sumMin = (arr, from, to, cap) => { let s = 0n; for (let k = from; k <= to; k++) s += cap && arr[k] > cap ? cap : arr[k]; return s; };
    const toNum = v => Number(v) / 1e18;
    // the first model the payment fits, or unpaid, or other
    const classify = (payer, pv, arr, from, to, tol = TOL) => {
      if (pv === 0n) return 'unpaid';
      const p = toNum(pv);
      for (const [name, , cap] of (payer === 'base' ? BASE_MODELS : TOPUP_MODELS))
        if (fits(p, MODELS[name] * toNum(sumMin(arr, from, to, cap ? CAPS[cap] : null)), tol)) return name;
      return 'other';
    };
    const MODEL_NAMES = [...BASE_MODELS, ...TOPUP_MODELS].map(m => m[0]);
    const periodRows = [], activityRows = [];
    for (const P of periods) {
      const paid = new Map(), rec = new Set(), txs = new Set();
      let paidWei = 0n, transfers = 0;
      for (const b of P.batches) for (const p of b.rows) { paid.set(p.w, (paid.get(p.w) || 0n) + p.v); paidWei += p.v; transfers++; rec.add(p.w); txs.add(p.tx); }
      const days = P.to - P.from + 1;
      const fitCount = { utc: 0, cet: 0, cest: 0, loose: 0 };
      const groups = Object.fromEntries([...MODEL_NAMES, 'unpaid', 'other', 'other_without_flows'].map(n => [n, 0]));
      let funded = 0, twaSum = 0n, paidFunded = 0, paidUnfunded = 0, tested = 0, testedStill = 0;
      const rates = [];
      const act = {};
      const addAct = (scope, cls, isPaid, tw, pv, atModel) => {
        const key = scope + cls; let o = act[key];
        if (!o) { o = { scope, cls, wallets: 0, paid_wallets: 0, model_wallets: 0, twa: 0n, twa_paid: 0n, paid_wei: 0n }; act[key] = o; }
        o.wallets++; o.twa += tw; o.paid_wei += pv; if (isPaid) { o.paid_wallets++; o.twa_paid += tw; } if (atModel) o.model_wallets++;
      };
      const addrs = new Set([...twa[MAIN].keys(), ...paid.keys()]);
      for (const a of addrs) {
        const arr = twa[MAIN].get(a) || new Array(N_DAYS).fill(0n);
        let tw = 0n; for (let k = P.from; k <= P.to; k++) tw += arr[k];
        const pv = paid.get(a) || 0n;
        if (tw === 0n && pv === 0n) continue;
        if (tw > 0n) { funded++; twaSum += tw; if (pv > 0n) paidFunded++; } else paidUnfunded++;
        const isTested = tw >= TESTED_MIN * BigInt(days);
        const cl = isTested ? classify(P.payer, pv, arr, P.from, P.to) : null;
        if (P.payer === 'topup' && tw > 0n) {
          const ac = activity(a, P.from);
          addAct('all', ac.cls, pv > 0n, tw, pv, false);
          if (isTested) addAct('ge100', ac.cls, pv > 0n, tw, pv, cl !== 'unpaid' && cl !== 'other');
        }
        if (!isTested) continue;
        tested++;
        const still = !moved.get(a).slice(P.from, P.to + 1).some(Boolean);
        if (still) testedStill++;
        rates.push(toNum(pv) / toNum(tw));
        for (const shift of Object.keys(SHIFTS)) {
          const c = classify(P.payer, pv, twa[shift].get(a) || new Array(N_DAYS).fill(0n), P.from, P.to);
          if (c !== 'unpaid' && c !== 'other') fitCount[shift]++;
        }
        groups[cl]++;
        if (cl === 'other' && still) groups.other_without_flows++;
        const cLoose = classify(P.payer, pv, arr, P.from, P.to, TOL_LOOSE);
        if (cLoose !== 'unpaid' && cLoose !== 'other') fitCount.loose++;
      }
      rates.sort((x, y) => x - y);
      const med = rates.length ? rates[Math.floor(rates.length / 2)] : 0;
      const own = new Set((P.payer === 'base' ? BASE_MODELS : TOPUP_MODELS).map(m => m[0]));
      periodRows.push([P.payer, P.id, dateOf(FIRST_DATE + P.from * DAY), dateOf(FIRST_DATE + P.to * DAY), days, P.batches.length,
        iso(P.batches[0].first), iso(P.batches[P.batches.length - 1].last), transfers, txs.size, rec.size, paidWei,
        funded, twaSum, paidFunded, paidUnfunded, tested, testedStill, fitCount.utc, fitCount.cet, fitCount.cest, fitCount.loose,
        ...MODEL_NAMES.map(n => own.has(n) ? groups[n] : ''), groups.unpaid, groups.other, groups.other_without_flows, (med * 365 * 100).toFixed(5)].join(','));
      if (P.payer === 'topup') for (const o of Object.values(act).sort((x, y) => (x.scope + x.cls < y.scope + y.cls ? -1 : 1)))
        activityRows.push([P.id, dateOf(FIRST_DATE + P.from * DAY), dateOf(FIRST_DATE + P.to * DAY), o.scope, o.cls, o.wallets, o.paid_wallets, o.model_wallets, o.twa, o.twa_paid, o.paid_wei].join(','));
      P.paid = paid;
    }
    files['periods.csv'] = 'payer,period,first_day,last_day,days,batches,first_payment_utc,last_payment_utc,transfers,transactions,recipients,paid_wei,' +
      'funded_wallets,twa_wei_days,paid_wallets,paid_wallets_without_balance,tested_wallets,tested_wallets_without_other_flows,' +
      'fit_utc,fit_cet,fit_cest,fit_utc_within_5pct,' + MODEL_NAMES.join(',') + ',unpaid,other,other_without_flows,median_rate_simple_pct\n' + periodRows.join('\n') + '\n';
    files['activity.csv'] = 'period,first_day,last_day,scope,class,wallets,paid_wallets,model_wallets,twa_wei_days,paid_twa_wei_days,topup_wei\n' + activityRows.join('\n') + '\n';
    files['batches.csv'] = 'payer,first_utc,last_utc,transfers,transactions,recipients,paid_wei,first_day,last_day\n' +
      batches.map(b => [b.payer, iso(b.first), iso(b.last), b.rows.length, new Set(b.rows.map(r => r.tx)).size, new Set(b.rows.map(r => r.w)).size,
        b.rows.reduce((s, r) => s + r.v, 0n), b.from === null ? '' : dateOf(FIRST_DATE + b.from * DAY), b.to === null ? '' : dateOf(FIRST_DATE + b.to * DAY)].join(',')).join('\n') + '\n';

    // ---- one row per wallet on two accrual days
    for (const k of SNAPSHOT_DAYS) {
      const pb = periods.find(P => P.payer === 'base' && P.from <= k && k <= P.to);
      const pt = periods.find(P => P.payer === 'topup' && P.from <= k && k <= P.to);
      if (!pb || !pt || pb.from !== pb.to || pt.from !== pt.to) throw new Error('accrual day ' + k + ' is not paid in a period of its own');
      const rows = [];
      const addrs = new Set([...twa[MAIN].keys(), ...pb.paid.keys(), ...pt.paid.keys()]);
      for (const a of addrs) {
        const tw = (twa[MAIN].get(a) || [])[k] || 0n, bp = pb.paid.get(a) || 0n, tp = pt.paid.get(a) || 0n;
        if (tw === 0n && bp === 0n && tp === 0n) continue;
        const ac = activity(a, k);
        const micro = v => v / 10n ** 12n;
        rows.push([wid.get(a), micro(tw), micro((twa.cet.get(a) || [])[k] || 0n), micro((twa.cest.get(a) || [])[k] || 0n), bp, tp,
          moved.get(a)[k] ? 1 : 0, ac.month, ac.prev, ac.earlier]);
      }
      rows.sort((x, y) => x[0] - y[0]);
      files['wallet_day_' + dateOf(FIRST_DATE + k * DAY) + '.csv'] = 'wallet,twa_micro,twa_cet_micro,twa_cest_micro,base_wei,topup_wei,other_flows,card_spends_month,card_spends_previous_month,card_spends_earlier\n' +
        rows.map(r => r.join(',')).join('\n') + '\n';
    }

    // ---- one row per wallet and calendar month: the top-up paid for the month's accrual days, and card spends
    //      before the month, in the whole month and after it, to the end of the read
    const partners = new Map();
    for (const x of xs) if (x.fw && x.tw && x.f !== x.t)
      for (const [a, b] of [[x.f, x.t], [x.t, x.f]]) { let s = partners.get(a); if (!s) { s = new Set(); partners.set(a, s); } s.add(b); }
    const MONTHS = [{ name: '2026-09', from: 0, to: 29, mk: 1 }, { name: '2026-10', from: 30, to: N_DAYS - 1, mk: 2 }];
    const monthRows = [];
    for (const M of MONTHS) {
      const ms = MONTH_STARTS[M.mk] - SHIFTS[MAIN], me = MONTH_STARTS[M.mk + 1] - SHIFTS[MAIN];
      const spendsIn = (a, s, e) => (cardTs.get(a) || []).filter(t => t >= s && t < e).length;
      const acc = new Map();
      for (const P of periods) {
        if (P.to < M.from || P.from > M.to) continue;
        if (P.from < M.from || P.to > M.to) throw new Error('a ' + P.payer + ' payment covers days in two months');
        const days = P.to - P.from + 1;
        for (const a of new Set([...twa[MAIN].keys(), ...P.paid.keys()])) {
          const arr = twa[MAIN].get(a);
          let tw = 0n; if (arr) for (let k = P.from; k <= P.to; k++) tw += arr[k];
          const pv = P.paid.get(a) || 0n;
          if (tw === 0n && pv === 0n) continue;
          let o = acc.get(a);
          if (!o) { o = { tw: 0n, tested: 0, paidDays: 0, top: 0n, topTested: 0n, base: 0n }; acc.set(a, o); }
          if (P.payer === 'base') { o.base += pv; continue; }
          o.tw += tw; o.top += pv;
          if (tw >= TESTED_MIN * BigInt(days)) { o.tested += days; o.topTested += pv; }
          if (pv > 0n) o.paidDays += days;
        }
      }
      const rows = [];
      for (const [a, o] of acc) {
        if (!(o.tested > 0 || o.top > 0n)) continue;
        const ps = [...(partners.get(a) || [])];
        rows.push([M.name, wid.get(a), o.tw, o.tested, o.paidDays, o.top, o.topTested, o.base,
          spendsIn(a, -Infinity, ms), spendsIn(a, ms, me), spendsIn(a, me, Infinity), ps.length, ps.filter(p => spendsIn(p, ms, me) > 0).length]);
      }
      rows.sort((x, y) => x[1] - y[1]);
      for (const r of rows) monthRows.push(r.join(','));
    }
    files['month_wallets.csv'] = 'month,wallet,twa_wei_days,tested_days,paid_days,topup_wei,topup_tested_wei,base_wei,' +
      'card_spends_before_month,card_spends_in_month,card_spends_after_month,wallets_exchanged_with,of_which_spent_in_month\n' + monthRows.join('\n') + '\n';

    const meta = {
      end_block: END_BLOCK, end_block_time: S.counts.end_block_time, next_block_time: S.counts.next_block_time, start_block: START_BLOCK, recount_block: RECOUNT_BLOCK,
      accrual_days: { first: dateOf(FIRST_DATE), last: dateOf(FIRST_DATE + (N_DAYS - 1) * DAY), day_starts_utc: '00:00', count: N_DAYS },
      wallets: wl.length, wallets_v1: wl.filter(w => w.gen === 0).length, wallets_v2: wl.filter(w => w.gen === 1).length,
      other_factory_contracts: S.infra.length, last_wallet_created: iso(wl[wl.length - 1].ts),
      usde_transfers_scanned: S.counts.transfers_scanned, usde_transfers_touching_wallets: xs.length,
      wallets_with_any_transfer: ev.size,
      transfers_from_wallets_to_reward_accounts: backN, usde_wei_from_wallets_to_reward_accounts: backWei.toString(),
      card_debit_logs_by_token: S.cardTokens || null,
      base_payments: payments.base.length, topup_payments: payments.topup.length,
      topup_payments_by_account: TOPUP.map(t => payments.topup.filter(p => p.from === t).length),
      models_daily: MODELS, models_order: { base: BASE_MODELS.map(m => m[0]), topup: TOPUP_MODELS.map(m => m[0]) },
      tolerance: TOL, tolerance_loose: TOL_LOOSE, tested_minimum_usde_per_day: 100, batch_gap_hours: GAP / 3600,
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
    R.files['meta.json'] = JSON.stringify(R.meta, null, 1) + '\n';
    const hashes = {};
    for (const [name, text] of Object.entries(R.files)) hashes[name] = { bytes: new TextEncoder().encode(text).length, sha256: await sha256hex(text) };
    return { files: R.files, hashes };
  }

  async function main() {
    const fs = require('fs'), path = require('path');
    const dir = path.join(__dirname, 'inputs', 'chain');
    fs.mkdirSync(dir, { recursive: true });
    const log = m => console.log(new Date().toISOString().slice(11, 19), m);
    const out = await run(globalThis.fetch, log);
    for (const [name, text] of Object.entries(out.files)) { fs.writeFileSync(path.join(dir, name), text); log('wrote ' + name + ' ' + out.hashes[name].bytes + ' bytes ' + out.hashes[name].sha256.slice(0, 12)); }
  }

  return { load, analyze, run, main, sha256hex, config: CFG, MODELS, BASE_MODELS, TOPUP_MODELS, FACTORIES, SETTLE, USDE, BASE, TOPUP, START_BLOCK, END_BLOCK, DAY0 };
})();
if (typeof module !== 'undefined' && typeof require === 'function' && require.main === module) {
  globalThis.EPB.main().catch(e => { console.error(e); process.exit(1); });
}
