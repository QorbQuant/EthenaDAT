/*
 susde_read.cjs

 Reads the share price of sUSDe, Ethena's staked USDe, from the sUSDe contract on Ethereum mainnet, for the UTC
 days from August 31 to October 10, 2026.

   1. The block at or before each UTC midnight from 00:00 August 31 to 00:00 October 11, 2026   (explorer API, getblocknobytime)
   2. Every Deposit and Withdraw log of the sUSDe contract from 00:00 August 30 to the end of October 10, 2026 UTC
                                                                                                 (explorer API, getLogs)
   3. Every RewardsReceived log of the sUSDe contract in the same blocks                        (explorer API, getLogs)
   4. At the time of the run, the contract's convertToAssets(1 sUSDe), totalAssets(), totalSupply() and
      cooldownDuration(), with the block they were read at                                      (explorer API, eth_call)

 sUSDe is an ERC-4626 vault. Each Deposit and Withdraw log carries the USDe (assets) and sUSDe (shares) that changed
 hands, so assets divided by shares is the share price at that moment, to within the contract's rounding of one unit
 of 10^-18. The files keep the amounts and the block time of each log, and nothing that names an address or a
 transaction.

 Run it with Node 18 or later:   node susde_read.cjs
 The same code runs unchanged in a browser console on a page that allows the requests, as
 SUS.run(u => fetch(u, { cache: 'no-store' }), console.log), which returns the files as text. main() below calls
 the same run() and only adds the write to disk, in inputs/chain/.

 The paging in walk() and the request retry in makeApi() are those of the site's chain recount, unchanged except for
 the block range.
*/
globalThis.SUS = (() => {
  'use strict';
  const API = 'https://api.routescan.io/v2/network/mainnet/evm/1/etherscan/api';
  const SUSDE = '0x9d39a5de30e57443bff2a8307a4256c8797a3497';   // sUSDe on Ethereum, from Ethena's key addresses page
  const T_DEPOSIT = '0xdcbc1c05240f31ff3ad067ef1ee35ce4997762752e3a095284754544f4c709d7';   // Deposit(address,address,uint256,uint256)
  const T_WITHDRAW = '0xfbde797d201c681b91056529119e0b02407c7bb96a4a2c75c01fc9667232c8db';  // Withdraw(address,address,address,uint256,uint256)
  const T_REWARDS = '0xbb28dd7cd6be6f61828ea9158a04c5182c716a946a6d2f31f4864edb87471aa6';   // RewardsReceived(uint256)
  const SEL = { convertToAssets: '0x07a2d13a', totalAssets: '0x01e1d114', totalSupply: '0x18160ddd', cooldownDuration: '0x35269315' };
  const ONE = 10n ** 18n;
  const utc = (y, m, d) => Date.UTC(y, m - 1, d) / 1000;
  const FIRST_MIDNIGHT = utc(2026, 8, 31), LAST_MIDNIGHT = utc(2026, 10, 11);
  const LOGS_FROM = utc(2026, 8, 30), LOGS_TO = utc(2026, 10, 11);   // logs from 00:00 August 30 to the last block before 00:00 October 11
  const DAY = 86400;
  const CFG = { retryMs: 900 };
  let START_BLOCK = 0, END_BLOCK = 0;
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const iso = t => new Date(t * 1000).toISOString().slice(0, 19) + 'Z';

  async function sha256hex(str) {
    const bytes = new TextEncoder().encode(str);
    const subtle = (globalThis.crypto && globalThis.crypto.subtle) || require('crypto').webcrypto.subtle;
    const d = await subtle.digest('SHA-256', bytes);
    return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, '0')).join('');
  }

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

  function makeRpc(fetchFn) {
    return async function rpc(params) {
      const u = API + '?' + Object.entries(params).map(([k, v]) => k + '=' + v).join('&');
      for (let i = 0; i < 6; i++) {
        try { const r = await fetchFn(u); if (r.ok) { const j = await r.json(); if (j && j.result !== undefined && j.result !== null && j.jsonrpc) return j.result; } } catch (e) { /* retry */ }
        await sleep(CFG.retryMs * (i + 1));
      }
      throw new Error('rpc failed: ' + u.slice(API.length, API.length + 160));
    };
  }

  async function walk(api, paramsFor, pageSize, blockOf, onRow, label, log) {
    let from = START_BLOCK, total = 0, span = END_BLOCK - from + 1;
    while (from <= END_BLOCK) {
      const to = Math.min(END_BLOCK, from + span - 1);
      let rows;
      try { rows = await api(paramsFor(from, to)); } catch (e) {
        if (span <= 2000) throw e;
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

  const word = (data, i) => BigInt('0x' + data.slice(2 + 64 * i, 2 + 64 * (i + 1)));
  const num = h => (typeof h === 'string' && h.startsWith('0x')) ? (h === '0x' ? 0 : parseInt(h, 16)) : Number(h);

  async function run(fetchFn, log) {
    const started = new Date().toISOString();
    const api = makeApi(fetchFn), rpc = makeRpc(fetchFn);
    const blockAt = async t => Number(await api({ module: 'block', action: 'getblocknobytime', timestamp: t, closest: 'before' }));
    START_BLOCK = await blockAt(LOGS_FROM - 1) + 1;          // first block at or after 00:00 August 30
    END_BLOCK = await blockAt(LOGS_TO - 1);                  // last block before 00:00 October 11
    const midnights = [];
    for (let t = FIRST_MIDNIGHT; t <= LAST_MIDNIGHT; t += DAY) {
      const b = await blockAt(t);
      const blk = await rpc({ module: 'proxy', action: 'eth_getBlockByNumber', tag: '0x' + b.toString(16), boolean: 'false' });
      const nxt = await rpc({ module: 'proxy', action: 'eth_getBlockByNumber', tag: '0x' + (b + 1).toString(16), boolean: 'false' });
      midnights.push({ date: iso(t).slice(0, 10), ts: t, block: b, block_ts: num(blk.timestamp), next_block_ts: num(nxt.timestamp) });
      if (!(num(blk.timestamp) <= t && num(nxt.timestamp) > t)) throw new Error('block ' + b + ' does not end before ' + iso(t));
    }
    if (log) log('blocks ' + START_BLOCK + ' to ' + END_BLOCK + ', ' + midnights.length + ' midnights');

    const events = [], rewards = [];
    const params = topic => (from, to) => ({ module: 'logs', action: 'getLogs', address: SUSDE, fromBlock: from, toBlock: to, topic0: topic, page: 1, offset: 1000 });
    const blockOf = r => num(r.blockNumber);
    for (const [topic, kind] of [[T_DEPOSIT, 'd'], [T_WITHDRAW, 'w']]) {
      await walk(api, params(topic), 1000, blockOf, r => {
        if (r.topics[0].toLowerCase() !== topic || r.address.toLowerCase() !== SUSDE) throw new Error('unexpected log');
        if (r.data.length !== 2 + 128) throw new Error('unexpected data length');
        events.push({ block: num(r.blockNumber), ts: num(r.timeStamp), li: num(r.logIndex), kind, assets: word(r.data, 0), shares: word(r.data, 1) });
      }, kind === 'd' ? 'Deposit' : 'Withdraw', log);
    }
    await walk(api, params(T_REWARDS), 1000, blockOf, r => {
      if (r.topics[0].toLowerCase() !== T_REWARDS || r.data.length !== 2 + 64) throw new Error('unexpected rewards log');
      rewards.push({ block: num(r.blockNumber), ts: num(r.timeStamp), li: num(r.logIndex), amount: word(r.data, 0) });
    }, 'RewardsReceived', log);
    events.sort((a, b) => a.block - b.block || a.li - b.li);
    rewards.sort((a, b) => a.block - b.block || a.li - b.li);

    // the contract now, at the latest block the explorer serves
    const head = num(await rpc({ module: 'proxy', action: 'eth_blockNumber' }));
    const call = async data => BigInt(await rpc({ module: 'proxy', action: 'eth_call', to: SUSDE, data, tag: 'latest' }));
    const now = {
      block_before_calls: head,
      convert_to_assets_1e18: (await call(SEL.convertToAssets + ONE.toString(16).padStart(64, '0'))).toString(),
      total_assets_wei: (await call(SEL.totalAssets)).toString(),
      total_supply_wei: (await call(SEL.totalSupply)).toString(),
      cooldown_duration_s: (await call(SEL.cooldownDuration)).toString(),
      read_utc: new Date().toISOString()
    };
    const headAfter = num(await rpc({ module: 'proxy', action: 'eth_blockNumber' }));
    now.block_after_calls = headAfter;

    const files = {};
    files['events.csv'] = 'block,ts,log_index,kind,assets_wei,shares_wei\n' +
      events.map(e => [e.block, e.ts, e.li, e.kind, e.assets, e.shares].join(',')).join('\n') + '\n';
    files['rewards.csv'] = 'block,ts,log_index,amount_wei\n' + rewards.map(r => [r.block, r.ts, r.li, r.amount].join(',')).join('\n') + '\n';
    files['midnights.csv'] = 'date,ts,block,block_ts,next_block_ts\n' + midnights.map(m => [m.date, m.ts, m.block, m.block_ts, m.next_block_ts].join(',')).join('\n') + '\n';
    const meta = {
      contract: SUSDE, start_block: START_BLOCK, end_block: END_BLOCK, logs_from: iso(LOGS_FROM), logs_to_before: iso(LOGS_TO),
      deposits: events.filter(e => e.kind === 'd').length, withdrawals: events.filter(e => e.kind === 'w').length, rewards: rewards.length,
      first_event: events.length ? iso(events[0].ts) : null, last_event: events.length ? iso(events[events.length - 1].ts) : null,
      now, run_started_utc: started, run_finished_utc: new Date().toISOString()
    };
    files['meta.json'] = JSON.stringify(meta, null, 1) + '\n';
    const hashes = {};
    for (const [k, v] of Object.entries(files)) hashes[k] = { bytes: new TextEncoder().encode(v).length, sha256: await sha256hex(v) };
    if (log) log('done, ' + events.length + ' events, ' + rewards.length + ' reward logs');
    return { files, hashes, meta };
  }

  async function main() {
    const fs = require('fs'), path = require('path');
    const dir = path.join(__dirname, 'inputs', 'chain');
    fs.mkdirSync(dir, { recursive: true });
    const log = m => console.log(new Date().toISOString().slice(11, 19), m);
    const out = await run(globalThis.fetch, log);
    for (const [name, text] of Object.entries(out.files)) { fs.writeFileSync(path.join(dir, name), text); log('wrote ' + name + ' ' + out.hashes[name].bytes + ' bytes ' + out.hashes[name].sha256.slice(0, 12)); }
  }

  return { run, main, sha256hex, config: CFG, SUSDE, T_DEPOSIT, T_WITHDRAW, T_REWARDS, SEL };
})();
if (typeof module !== 'undefined' && typeof require === 'function' && require.main === module) {
  globalThis.SUS.main().catch(e => { console.error(e); process.exit(1); });
}
