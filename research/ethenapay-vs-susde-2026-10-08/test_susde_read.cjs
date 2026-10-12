/*
 test_susde_read.cjs

 Runs susde_read.cjs against a synthetic chain served by a fake fetch, with known answers. No network.
   node test_susde_read.cjs susde_read.cjs

 The synthetic chain has a block every 12 seconds from 00:00 UTC August 29, 2026. It holds 2,600 Deposit logs, 1,900
 Withdraw logs and 3 RewardsReceived logs a day for 44 days, some of them sharing a block, so the explorer's
 1,000-row pages must be stitched together. Log index 0 is written "0x", as Etherscan-compatible APIs do. Each
 amount encodes its own position, so a lost, repeated or swapped log shows.
*/
const path = require('path');
const assert = require('assert');
require(path.resolve(process.argv[2] || './susde_read.cjs'));
const S = globalThis.SUS;
S.config.retryMs = 1;

const T0 = Date.UTC(2026, 7, 29) / 1000, B0 = 25850000, SPB = 12;
const tsOf = b => T0 + (b - B0) * SPB;
const blockAt = t => B0 + Math.floor((t - T0) / SPB);
const hex = n => '0x' + n.toString(16);
const w = v => BigInt(v).toString(16).padStart(64, '0');

const logs = [];
let seq = 0;
for (let day = 0; day < 44; day++) {
  for (let k = 0; k < 4503; k++) {
    const kind = k < 2600 ? 'd' : (k < 4500 ? 'w' : 'r');
    const b = B0 + day * 7200 + Math.floor(k * 7200 / 4503);
    seq++;
    const topic = kind === 'd' ? S.T_DEPOSIT : kind === 'w' ? S.T_WITHDRAW : S.T_REWARDS;
    const shares = 10n ** 18n * BigInt(seq);
    const assets = shares * 12n / 10n + BigInt(seq);          // a price near 1.2, nudged by the position
    const data = kind === 'r' ? '0x' + w(seq * 1000) : '0x' + w(assets) + w(shares);
    logs.push({ address: S.SUSDE, topics: [topic, '0x' + w(1), '0x' + w(2)].slice(0, kind === 'w' ? 4 : kind === 'd' ? 3 : 1),
                data, blockNumber: hex(b), timeStamp: hex(tsOf(b)), logIndex: (seq % 7 === 0 ? '0x' : hex(seq % 7)), seq, kind });
  }
}
const ok = j => ({ ok: true, json: async () => j });
const fakeFetch = async u => {
  const q = Object.fromEntries(new URL(u).searchParams.entries());
  if (q.module === 'block') return ok({ status: '1', result: String(blockAt(Number(q.timestamp))) });
  if (q.action === 'eth_getBlockByNumber') return ok({ jsonrpc: '2.0', result: { timestamp: hex(tsOf(parseInt(q.tag, 16))) } });
  if (q.action === 'eth_blockNumber') return ok({ jsonrpc: '2.0', result: hex(B0 + 44 * 7200) });
  if (q.action === 'eth_call') return ok({ jsonrpc: '2.0', result: '0x' + w(q.data.startsWith('0x35269315') ? 604800 : 1234567) });
  if (q.module === 'logs') {
    const from = Number(q.fromBlock), to = Number(q.toBlock);
    const rows = logs.filter(l => l.topics[0] === q.topic0 && parseInt(l.blockNumber, 16) >= from && parseInt(l.blockNumber, 16) <= to);
    return ok({ status: rows.length ? '1' : '0', result: rows.slice(0, Number(q.offset)).map(({ seq, kind, ...r }) => r) });
  }
  throw new Error('unexpected request ' + u);
};

(async () => {
  const out = await S.run(fakeFetch, () => {});
  const ev = out.files['events.csv'].trim().split('\n').slice(1).map(l => l.split(','));
  const rw = out.files['rewards.csv'].trim().split('\n').slice(1).map(l => l.split(','));
  const lo = blockAt(Date.UTC(2026, 7, 30) / 1000 - 1) + 1, hi = blockAt(Date.UTC(2026, 9, 11) / 1000 - 1);
  const want = logs.filter(l => parseInt(l.blockNumber, 16) >= lo && parseInt(l.blockNumber, 16) <= hi);
  const wantEv = want.filter(l => l.kind !== 'r'), wantRw = want.filter(l => l.kind === 'r');
  assert.strictEqual(ev.length, wantEv.length, 'every Deposit and Withdraw log in the range, once');
  assert.strictEqual(rw.length, wantRw.length, 'every RewardsReceived log in the range, once');
  const seen = new Set(ev.map(r => r[5]));
  assert.strictEqual(seen.size, ev.length, 'no log repeated');
  for (const l of wantEv) assert.ok(seen.has((10n ** 18n * BigInt(l.seq)).toString()), 'log ' + l.seq + ' present');
  for (const r of ev) { const s = BigInt(r[5]) / 10n ** 18n; assert.strictEqual(BigInt(r[4]), BigInt(r[5]) * 12n / 10n + s, 'assets and shares stay paired'); }
  for (let i = 1; i < ev.length; i++) assert.ok(Number(ev[i][0]) >= Number(ev[i - 1][0]), 'events in block order');
  assert.ok(ev.some(r => r[2] === '0'), 'log index "0x" read as 0');
  assert.ok(rw.every(r => BigInt(r[3]) % 1000n === 0n), 'reward amounts read from the data word');
  const mid = out.files['midnights.csv'].trim().split('\n').slice(1).map(l => l.split(','));
  assert.strictEqual(mid.length, 42, '42 midnights, August 31 to October 11');
  for (const m of mid) { assert.ok(Number(m[3]) <= Number(m[1]) && Number(m[4]) > Number(m[1]), 'block ends before midnight'); }
  assert.strictEqual(out.meta.now.cooldown_duration_s, '604800');
  assert.strictEqual(out.meta.start_block, lo);
  assert.strictEqual(out.meta.end_block, hi);
  const text = Object.values(out.files).join('');
  assert.ok(!/0x[0-9a-f]{40}/i.test(out.files['events.csv'] + out.files['rewards.csv'] + out.files['midnights.csv']), 'no address in the CSV files');
  console.log('all synthetic checks passed,', ev.length, 'events and', rw.length, 'reward logs');
})().catch(e => { console.error(e); process.exit(1); });
