// Runs chain_recount.cjs against a synthetic chain served by an in-process mock of the explorer API and the RPC.
// Usage: node test_chain_recount.cjs chain_recount.cjs
const path = require('path');
require(path.resolve(process.argv[2]));
const EPR = globalThis.EPR;
const assert = require('assert');

let seed = 12345;
const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; };
const ri = (a, b) => a + Math.floor(rnd() * (b - a + 1));
const hex = (n, len) => n.toString(16).padStart(len, '0');
const addr = i => '0x' + hex(0xabc0000000 + i, 40);
const txh = i => '0x' + hex(0x7700000000 + i, 64);
const tsOf = b => 1778849194 + Math.floor((b - 85497626) * 1.0929);
const pad = a => '0x' + a.slice(2).toLowerCase().padStart(64, '0');
const T = '0xa575fb45e6259a68f4974e75c94adc55a35f2c06eee07709e964a4407e7dcfeb';
const [F0, F1] = EPR.FACTORIES, [S0, S1] = EPR.SETTLE, USDE = EPR.USDE;
const YIELD = '0xd0ec8cc7414f27ce85f8dece6b4a58225f273311', OTHER = '0xab2b06efa6179e624f5e3b08b64978df114ff24f';
const END = EPR.END_BLOCK;
EPR.config.retryMs = 1;      // the mock explorer refuses wide log requests on purpose, so do not wait long between attempts

// ---- synthetic chain
const internals = [];    // {blockNumber, timeStamp, from, contractAddress, type, isError}
const wallets = [];      // {a, blk}
internals.push({ blk: 85497626, from: F0, contractAddress: addr(900001), type: 'create' });
let b = 85500000;
for (let i = 0; i < 2000; i++) { b += ri(0, 900); wallets.push({ a: addr(i), blk: b, gen: 0 }); internals.push({ blk: b, from: F0, contractAddress: addr(i), type: 'create2' }); }
internals.push({ blk: 87652557, from: F1, contractAddress: addr(900002), type: 'create' });
internals.push({ blk: 87652557, from: F1, contractAddress: addr(900003), type: 'create' });
b = 87652600;
for (let i = 2000; i < 13000; i++) { b += ri(0, 1600); if (b > END - 5000) b = END - 5000 - ri(0, 100); wallets.push({ a: addr(i), blk: b, gen: 1 }); internals.push({ blk: b, from: F1, contractAddress: addr(i), type: 'create2' }); }
internals.push({ blk: 88000000, from: F1, contractAddress: addr(900004), type: 'create2', isError: '1' });   // failed create, must be ignored
wallets.sort((x, y) => x.blk - y.blk);
const isWallet = new Set(wallets.map(w => w.a));

const transfers = [];    // {blk, tx, from, to, value}
const logs = [];         // {blk, li, tx, address, to, amt}
let txn = 0;
const spenders = wallets.filter((w, i) => i % 13 === 0).slice(0, 900);
// deposits first
for (const w of spenders) transfers.push({ blk: w.blk + ri(1, 50), tx: txh(txn++), from: addr(800000 + ri(0, 50)), to: w.a, value: BigInt(ri(5000, 900000)) * 10n ** 18n });
// other funded wallets that never spend
for (let i = 0; i < 600; i++) { const w = wallets[ri(0, wallets.length - 1)]; transfers.push({ blk: Math.min(END, w.blk + ri(1, 5000)), tx: txh(txn++), from: addr(800000 + ri(0, 50)), to: w.a, value: BigInt(ri(1, 99999)) * 10n ** 14n }); }
// wallets whose first USDe comes from another programme wallet: one sender seeds 25 wallets, another seeds 3
{
  const fresh = wallets.filter((w, i) => i % 13 === 5);
  const seed = (from, targets) => { for (const w of targets) transfers.push({ blk: Math.min(END, Math.max(from.blk + 60, w.blk + ri(1, 40))), tx: txh(txn++), from: from.a, to: w.a, value: 10n * 10n ** 18n }); };
  seed(spenders[5], fresh.slice(40, 65));
  seed(spenders[9], fresh.slice(70, 73));
}
// spend events
const NEV = 30000;
const evBlocks = [];
for (let i = 0; i < NEV; i++) evBlocks.push(ri(87200000, END));
evBlocks.sort((x, y) => x - y);
const liUsed = new Map();
for (let i = 0; i < NEV; i++) {
  const blk = evBlocks[i];
  const cands = spenders.filter(w => w.blk + 60 < blk);
  const w = cands[ri(0, cands.length - 1)];
  const n = rnd() < 0.03 ? ri(2, 4) : 1;
  const tx = txh(txn++);
  for (let k = 0; k < n && i + k < NEV; k++) {
    const li = (liUsed.get(blk) || 0) + 1 + ri(0, 3); liUsed.set(blk, li);
    const cents = BigInt(ri(1, 20000));
    const to = blk < 90000000 ? S1 : S0;
    logs.push({ blk, li, tx, address: w.a, to, amt: cents * 10n ** 16n });
    transfers.push({ blk, tx, from: w.a, to, value: cents * 10n ** 16n });
    if (k > 0) { evBlocks[i + k] = blk; }
  }
  i += n - 1;
}
// logs to another destination and from a non-wallet, which must not be counted
logs.push({ blk: 86000000, li: 1, tx: txh(txn++), address: spenders[0].a, to: addr(700001), amt: 999n * 10n ** 16n });
logs.push({ blk: 80000000, li: 1, tx: txh(txn++), address: addr(700002), to: addr(700001), amt: 5n * 10n ** 16n });
logs.push({ blk: 86000500, li: 1, tx: txh(txn++), address: addr(700002), to: addr(700003), amt: 7n * 10n ** 16n });      // no programme wallet involved
logs.push({ blk: 86001000, li: 1, tx: txh(txn++), address: spenders[1].a, to: spenders[2].a, amt: 100n * 10n ** 16n });   // one programme wallet to another
// withdrawals, rewards, reversals, internal transfers
for (let i = 0; i < 3000; i++) {
  const w = spenders[ri(0, spenders.length - 1)], blk = ri(w.blk + 100, END);
  const kind = ri(0, 4);
  if (kind === 0) transfers.push({ blk, tx: txh(txn++), from: YIELD, to: w.a, value: BigInt(ri(1, 999999)) * 10n ** 9n });
  else if (kind === 1) transfers.push({ blk, tx: txh(txn++), from: OTHER, to: w.a, value: BigInt(ri(1, 99999)) * 10n ** 9n });
  else if (kind === 2) transfers.push({ blk, tx: txh(txn++), from: S0, to: w.a, value: BigInt(ri(1, 5000)) * 10n ** 16n });
  else if (kind === 3) { const w2 = spenders[ri(0, spenders.length - 1)]; transfers.push({ blk: Math.max(blk, w2.blk + 100), tx: txh(txn++), from: w.a, to: w2.a, value: BigInt(ri(1, 500)) * 10n ** 16n }); }
  else transfers.push({ blk, tx: txh(txn++), from: w.a, to: addr(810000 + ri(0, 99)), value: BigInt(ri(1, 2000)) * 10n ** 16n });
}
// unrelated transfers
for (let i = 0; i < 40000; i++) transfers.push({ blk: ri(85400000, END), tx: txh(txn++), from: addr(600000 + ri(0, 999)), to: addr(600000 + ri(0, 999)), value: BigInt(ri(1, 10 ** 9)) });
// a transfer before the start block and one after the end, both outside the scan
transfers.push({ blk: 85000000, tx: txh(txn++), from: addr(600001), to: addr(600002), value: 1n });
transfers.forEach((t, i) => { t.seq = i; });
transfers.sort((x, y) => x.blk - y.blk || x.seq - y.seq);
logs.sort((x, y) => x.blk - y.blk || x.li - y.li);
internals.forEach((r, i) => { r.seq = i; });
internals.sort((x, y) => x.blk - y.blk || x.seq - y.seq);

// make balances non-negative: simulate, and where a wallet would go negative add a deposit just before
{
  const bal = new Map(); const extra = [];
  for (const t of transfers) {
    if (isWallet.has(t.from)) {
      const cur = bal.get(t.from) || 0n;
      if (cur < t.value) { const top = t.value - cur + BigInt(ri(0, 3)) * 10n ** 18n; extra.push({ blk: t.blk, tx: txh(txn++), from: addr(800000), to: t.from, value: top, seq: t.seq - 0.5 }); bal.set(t.from, cur + top); }
      bal.set(t.from, bal.get(t.from) - t.value);
    }
    if (isWallet.has(t.to)) bal.set(t.to, (bal.get(t.to) || 0n) + t.value);
  }
  for (const e of extra) transfers.push(e);
  transfers.sort((x, y) => x.blk - y.blk || x.seq - y.seq);
}

// ---- mock explorer API and RPC
// Like the real explorer on a slow day, the mock refuses a log request that spans more than 4,000,000 blocks.
let calls = 0, refused = 0;
async function mockFetch(url, opts) {
  calls++;
  if (opts && opts.method === 'POST') {
    const rq = JSON.parse(opts.body);
    const data = rq.params[0].data.slice(2), blk = parseInt(rq.params[1]);
    if (data.slice(0, 8) !== '82ad56cb' || rq.params[0].to !== '0xca11bde05977b3631167028862be2a173976ca11') throw new Error('unexpected rpc call');
    const W = i => data.slice(8 + i * 64, 8 + i * 64 + 64);
    const n = parseInt(W(1), 16);
    const balAt = new Map();
    for (const t of transfers) { if (t.blk > blk) break; balAt.set(t.to, (balAt.get(t.to) || 0n) + t.value); balAt.set(t.from, (balAt.get(t.from) || 0n) - t.value); }
    const word = v => BigInt(v).toString(16).padStart(64, '0');
    let out = word(32) + word(n);
    for (let k = 0; k < n; k++) out += word(n * 32 + k * 128);
    for (let k = 0; k < n; k++) {
      const start = 2 + parseInt(W(2 + k), 16) / 32;                 // tuple start, in words
      const cd = start + parseInt(W(start + 2), 16) / 32;            // callData length word
      const a = '0x' + data.slice(8 + (cd + 1) * 64 + 8 + 24, 8 + (cd + 1) * 64 + 8 + 64);
      out += word(1) + word(64) + word(32) + word(balAt.get(a) || 0n);
    }
    return { ok: true, json: async () => ({ jsonrpc: '2.0', id: rq.id, result: '0x' + out }) };
  }
  const q = Object.fromEntries(new URL(url).searchParams.entries());
  let result;
  if (q.action === 'getblocknobytime') result = String(END);
  else if (q.action === 'txlistinternal') {
    result = internals.filter(r => (r.from === q.address) && r.blk >= +q.startblock && r.blk <= +q.endblock).slice(0, +q.offset)
      .map(r => ({ blockNumber: String(r.blk), timeStamp: String(tsOf(r.blk)), from: r.from, to: '', contractAddress: r.contractAddress, type: r.type, isError: r.isError || '0' }));
  } else if (q.action === 'getLogs') {
    if (+q.toBlock - +q.fromBlock + 1 > 4000000) { refused++; return { ok: true, json: async () => ({ status: '0', message: 'An error occurred', result: null }) }; }
    result = logs.filter(l => l.blk >= +q.fromBlock && l.blk <= +q.toBlock && (!q.topic2 || pad(l.to) === q.topic2)).slice(0, +q.offset)
      .map(l => ({ address: l.address, topics: [T, pad(USDE), pad(l.to)], data: '0x' + l.amt.toString(16).padStart(64, '0'), blockNumber: '0x' + l.blk.toString(16), timeStamp: '0x' + tsOf(l.blk).toString(16), logIndex: '0x' + l.li.toString(16), transactionHash: l.tx }));
  } else if (q.action === 'tokentx') {
    result = transfers.filter(t => t.blk >= +q.startblock && t.blk <= +q.endblock).slice(0, +q.offset)
      .map(t => ({ blockNumber: String(t.blk), timeStamp: String(tsOf(t.blk)), hash: t.tx, from: t.from, to: t.to, value: t.value.toString() }));
  } else throw new Error('unexpected action ' + q.action);
  return { ok: true, json: async () => ({ status: '1', message: 'OK', result }) };
}

(async () => {
  const S = await EPR.load(mockFetch, null);
  const inScan = t => t.blk >= EPR.START_BLOCK && t.blk <= END;
  assert.strictEqual(S.wallets.size, 13000);
  assert.strictEqual(S.infra.length, 3);
  const qualifying = logs.filter(l => l.to === S0 || l.to === S1);
  assert.strictEqual(S.spends.length, qualifying.length);
  assert.strictEqual(S.counts.transfers_scanned, transfers.filter(inScan).length);
  assert.strictEqual(S.xfers.length, transfers.filter(t => inScan(t) && (isWallet.has(t.from) || isWallet.has(t.to))).length);
  assert.ok(refused >= 12, 'the wide log requests must have been refused and retried in smaller ranges');
  console.log('load ok:', S.wallets.size, 'wallets,', S.spends.length, 'spend events,', S.xfers.length, 'of', S.counts.transfers_scanned, 'transfers,', calls, 'requests,', refused, 'refused');

  const R = await EPR.analyze(S);
  assert.strictEqual(R.meta.spend_events_equal_wallet_to_settlement_transfers, true);
  const snaps = JSON.parse(R.files['snapshots_chain.json']);
  assert.strictEqual(snaps.length, 9);

  // brute-force check of the last snapshot
  const last = snaps[8], C = last.events_reported, pre = qualifying.slice(0, C);
  assert.strictEqual(last.cut_block, pre[C - 1].blk);
  assert.strictEqual(last.wallets_ever_spent, new Set(pre.map(l => l.address)).size);
  assert.strictEqual(last.spend_cents, pre.reduce((s, l) => s + l.amt / 10n ** 16n, 0n).toString());
  const runDay = Math.floor(last.generated_ts / 86400), s30 = (runDay - 30) * 86400, s7 = (runDay - 7) * 86400;
  assert.strictEqual(last.wallets_spent_30d, new Set(pre.filter(l => tsOf(l.blk) >= s30).map(l => l.address)).size);
  assert.strictEqual(last.wallets_spent_7d, new Set(pre.filter(l => tsOf(l.blk) >= s7).map(l => l.address)).size);
  assert.strictEqual(last.wallets_created_at_cut_block, wallets.filter(w => w.blk <= last.cut_block).length);
  const bal = new Map();
  for (const t of transfers) { if (t.blk > last.cut_block) break; if (isWallet.has(t.to)) bal.set(t.to, (bal.get(t.to) || 0n) + t.value); if (isWallet.has(t.from)) bal.set(t.from, (bal.get(t.from) || 0n) - t.value); }
  const pos = [...bal.values()].filter(v => v > 0n).sort((x, y) => (x > y ? -1 : 1));
  assert.strictEqual(last.balances_at_cut_block.funded, pos.length);
  assert.strictEqual(last.balances_at_cut_block.held_wei, pos.reduce((s, v) => s + v, 0n).toString());
  assert.strictEqual(last.balances_at_cut_block.top10_wei, pos.slice(0, 10).reduce((s, v) => s + v, 0n).toString());
  assert.strictEqual(last.balances_at_cut_block.negative_balances, 0);
  const txc = new Map(); for (const l of pre) txc.set(l.tx, (txc.get(l.tx) || 0) + 1);
  assert.strictEqual(last.max_events_in_one_transaction, Math.max(...txc.values()));
  assert.strictEqual(last.transactions, txc.size);

  // files
  const wdLines = R.files['spend_wallet_days.csv'].trim().split('\n').slice(1).map(l => l.split(',').map(Number));
  assert.strictEqual(wdLines.reduce((s, r) => s + r[3], 0), qualifying.length);
  for (let j = 0; j < 9; j++) assert.strictEqual(wdLines.filter(r => r[1] <= j).reduce((s, r) => s + r[3], 0), EPR.SNAP[j][2]);
  assert.strictEqual(new Set(wdLines.filter(r => r[1] <= 8).map(r => r[2])).size, last.wallets_ever_spent);
  const days = R.files['daily_chain.csv'].trim().split('\n').slice(1).map(l => l.split(','));
  assert.strictEqual(days.reduce((s, r) => s + Number(r[5]), 0), qualifying.length);
  assert.strictEqual(Number(days[days.length - 1][4]), 13000);
  const wc = R.files['wallets_created.csv'].trim().split('\n');
  assert.strictEqual(wc[0], 'wallet,created_ts,factory');
  const wrows = wc.slice(1).map(l => l.split(',').map(Number));
  assert.strictEqual(wrows.length, 13000);
  wrows.forEach((r, i) => { assert.strictEqual(r[0], i); assert.strictEqual(r[1], tsOf(R.wl[i].blk)); assert.strictEqual(r[2], R.wl[i].gen); });
  assert.strictEqual(wrows[wrows.length - 1][1], tsOf(wallets[wallets.length - 1].blk));
  assert.strictEqual(wrows.filter(r => r[2] === 0).length, 2000);

  // who sent each wallet its first USDe, by brute force
  const firstFrom = new Map();
  for (const t of transfers) { if (t.blk > last.cut_block) break; if (t.blk < EPR.START_BLOCK) continue; if (isWallet.has(t.to) && !firstFrom.has(t.to)) firstFrom.set(t.to, t.from); }
  const seeded = [...firstFrom.values()].filter(f => isWallet.has(f));
  const perSender = new Map(); for (const f of seeded) perSender.set(f, (perSender.get(f) || 0) + 1);
  const fu = R.meta.first_usde_received_at_last_snapshot;
  assert.strictEqual(fu.wallets, firstFrom.size);
  assert.strictEqual(fu.wallets, last.balances_at_cut_block.wallets_ever_received);
  assert.strictEqual(fu.from_another_programme_wallet, seeded.length);
  assert.ok(seeded.length >= 20);
  assert.strictEqual(fu.from_outside_the_programme + fu.from_another_programme_wallet + fu.from_a_reversal_or_reward, fu.wallets);
  assert.strictEqual(fu.from_outside_the_programme, [...firstFrom.values()].filter(f => !isWallet.has(f) && f !== S0 && f !== S1 && f !== YIELD && f !== OTHER).length);
  assert.strictEqual(fu.programme_wallets_that_sent_a_first_usde, perSender.size);
  assert.strictEqual(fu.first_funded_by_the_largest_such_sender, Math.max(...perSender.values()));
  assert.ok(!('event_sizes_by_month_at_last_snapshot' in R.meta) && !('largest_events_at_last_snapshot' in R.meta));
  // spend events per settlement address, by brute force
  for (const [role, a] of [['current', S0], ['retired', S1]]) {
    const mine = qualifying.filter(l => l.to === a), got = R.meta.settlement_addresses.find(o => o.role === role);
    const isoOf = b => new Date(tsOf(b) * 1000).toISOString().slice(0, 19) + 'Z';
    assert.ok(mine.length > 100);
    assert.strictEqual(got.spend_events, mine.length);
    assert.strictEqual(got.spend_cents, mine.reduce((s, l) => s + l.amt / 10n ** 16n, 0n).toString());
    assert.strictEqual(got.first_spend_event, isoOf(mine[0].blk));
    assert.strictEqual(got.last_spend_event, isoOf(mine[mine.length - 1].blk));
  }
  assert.strictEqual(R.meta.settlement_addresses.length, 2);
  assert.strictEqual(R.meta.settlement_addresses.reduce((s, o) => s + o.spend_events, 0), R.meta.spend_events);
  assert.strictEqual(R.meta.settlement_addresses[1].spend_events, R.meta.spend_events_retired_settlement);
  assert.ok(R.meta.settlement_addresses[1].last_spend_event < R.meta.settlement_addresses[0].first_spend_event, 'in the synthetic chain the retired address stops before the current one starts');
  assert.ok(!/0x[0-9a-f]{40}/.test(JSON.stringify(R.meta.settlement_addresses)));
  assert.ok(!Object.values(R.files).some(text => /0x[0-9a-f]{40}/.test(text)), 'no address may appear in the output files');
  const actRows = R.files['wallet_activity.csv'].trim().split('\n').slice(1).map(l => l.split(','));
  assert.strictEqual(actRows.filter(r => BigInt(r[4]) > 0n).length, last.balances_at_cut_block.funded);

  const atCut = R.wl.filter(w => w.blk <= last.cut_block).map(w => w.a);
  const v = await EPR.verifyBalances(mockFetch, atCut.slice(0, 1777), R.balAtLastCut, last.cut_block, null);
  assert.strictEqual(v.wallets_checked, 1777);
  assert.ok(v.wallets_with_balance > 50);
  assert.strictEqual(v.mismatches.length, 0);
  const scan = await EPR.scanOtherDestinations(mockFetch, S, null), od = scan.summary;
  assert.strictEqual(od.to_a_settlement_address, qualifying.length);
  assert.strictEqual(od.to_any_other_destination, 4);
  assert.strictEqual(od.other_from_programme_wallets, 2);
  assert.strictEqual(od.destinations.length, 2);                       // the destination no programme wallet sent to is left out
  assert.strictEqual(od.other_from_addresses_that_are_not_programme_wallets, 2);
  assert.strictEqual(od.other_destinations_with_no_event_from_a_programme_wallet, 1);
  assert.strictEqual(od.other_from_programme_wallets + od.other_from_addresses_that_are_not_programme_wallets, od.to_any_other_destination);
  assert.strictEqual(od.programme_wallets_with_other_destination_events, 2);
  assert.ok(!/0x[0-9a-f]{40}/.test(JSON.stringify(od)), 'the summary must not hold an address');
  assert.deepStrictEqual(scan.addresses.map(a => a.is_programme_wallet).sort(), [false, true]);
  assert.deepStrictEqual(scan.addresses.map(a => a.destination), od.destinations.map(d => d.destination));
  assert.deepStrictEqual(scan.addresses.map(a => a.is_programme_wallet), od.destinations.map(d => d.destination_is_programme_wallet));
  console.log('analyze ok. last snapshot:', JSON.stringify({ created: last.wallets_created_at_cut_block, ever: last.wallets_ever_spent, d30: last.wallets_spent_30d, d7: last.wallets_spent_7d, funded: last.balances_at_cut_block.funded, float_funded: last.balances_at_cut_block.float_funded }));
  console.log('files:', Object.entries(R.files).map(([k, s]) => k + ' ' + s.length).join(', '));
  console.log('balance check', v.wallets_checked, 'wallets, mismatches', v.mismatches.length, '| other destinations', od.to_any_other_destination, '| first USDe', JSON.stringify(fu));

  // the whole run, as main() and the browser call it
  const out = await EPR.run(mockFetch, null);
  assert.deepStrictEqual(Object.keys(out.files).sort(), ['daily_chain.csv', 'meta.json', 'snapshots_chain.json', 'spend_wallet_days.csv', 'wallet_activity.csv', 'wallets_created.csv']);
  for (const name of Object.keys(R.files)) assert.strictEqual(out.files[name], R.files[name], name + ' must not depend on the run');
  for (const [name, text] of Object.entries(out.files)) {
    assert.strictEqual(out.hashes[name].bytes, Buffer.byteLength(text));
    assert.strictEqual(out.hashes[name].sha256, require('crypto').createHash('sha256').update(text).digest('hex'));
  }
  const meta = JSON.parse(out.files['meta.json']);
  assert.deepStrictEqual(meta.other_destinations, od);
  assert.strictEqual(meta.balance_check.wallets_checked, atCut.length);
  assert.strictEqual(meta.balance_check.mismatch_count, 0);
  assert.deepStrictEqual(meta.balance_check.mismatches, []);
  const inMeta = new Set(out.files['meta.json'].match(/0x[0-9a-f]{40}/g));
  assert.deepStrictEqual([...inMeta].sort(), meta.other_factory_contracts.map(o => o.address).sort(), 'meta.json may name the non-wallet factory contracts and no other address');
  assert.strictEqual(meta.other_factory_contracts.length, 3);
  assert.deepStrictEqual(out.review.other_destinations, scan.addresses);
  assert.strictEqual(out.review.largest_balances.length, 20);
  console.log('run ok. meta.json', out.hashes['meta.json'].bytes, 'bytes');
  console.log('ALL TESTS PASSED');
})().catch(e => { console.error('TEST FAILED', e); process.exit(1); });
