// Runs the file-writing part of cashback_recount.cjs on a small synthetic chain with known answers.
// Usage: node test_cashback_recount.cjs cashback_recount.cjs
const path = require('path');
require(path.resolve(process.argv[2]));
const ECB = globalThis.ECB;
const assert = require('assert');

const utc = (y, m, d, hh, mm, ss) => Date.UTC(y, m - 1, d, hh || 0, mm || 0, ss || 0) / 1000;
const E18 = 10n ** 18n, CENT = 10n ** 16n;
const hex = (n, len) => n.toString(16).padStart(len, '0');
const addr = i => '0x' + hex(0xabc0000000 + i, 40);
const blkOf = ts => 90000000 + Math.floor((ts - utc(2026, 7, 1)) / 2);
const [S0, S1] = ECB.SETTLE, [C0] = ECB.CASHBACK;
const FUNDER = addr(999999), OUTSIDE = addr(888888);

// four wallets, created in this order, so their positions are 0 to 3
const wallets = new Map();
for (let i = 0; i < 4; i++) wallets.set(addr(i), { ts: utc(2026, 7, 1, 0, 0, i), blk: blkOf(utc(2026, 7, 1, 0, 0, i)), gen: 1 });
const xs = [];
const add = (f, t, v, ts) => xs.push({ f, t, fw: wallets.has(f), tw: wallets.has(t), v, ts, blk: blkOf(ts), tx: '0x' + hex(xs.length + 1, 64) });
[500, 2000, 50, 0].forEach((b, i) => { if (b) add(FUNDER, addr(i), BigInt(b) * E18, utc(2026, 7, 2, 12)); });
add(addr(0), S0, 1234n * CENT, utc(2026, 8, 10, 9));          // before August 15, left out of spends.csv
add(addr(0), S0, 3616n * CENT, utc(2026, 9, 1, 17, 47));      // $36.16
add(addr(1), S1, 79509n * CENT, utc(2026, 9, 3, 11, 21));     // $795.09 to the retired settlement address
add(S0, addr(1), 2500n * CENT, utc(2026, 9, 4, 8));           // a $25.00 reversal
add(addr(2), S0, 91n * CENT, utc(2026, 9, 4, 5, 19));         // $0.91, under a dollar
add(addr(0), addr(2), 10n * E18, utc(2026, 9, 5, 12));        // between wallets, not a card payment
add(addr(1), FUNDER, 100n * E18, utc(2026, 9, 6, 12));        // a withdrawal
xs.sort((a, b) => a.blk - b.blk || a.ts - b.ts);
xs.forEach((x, i) => { x.q = i; });
// spend events for three of the four card payments, none for the $0.91 one, and one event with no card payment
const spent = xs.filter(x => x.fw && (x.t === S0 || x.t === S1) && x.v !== 91n * CENT).map((x, i) => ({ w: x.f, to: x.t, v: x.v, tx: x.tx, ts: x.ts, blk: x.blk, q: i }));
spent.push({ w: addr(3), to: S0, v: 5n * E18, tx: '0x' + hex(777, 64), ts: utc(2026, 9, 24), blk: blkOf(utc(2026, 9, 24)), q: 99 });

// cashback: a batch at 02:30 on September 3 to wallets 0 and 1, a batch at 02:30 on September 5 to wallet 1,
// a second transfer two hours later in the same batch, one transfer to an outside address, and one on August 1
const cb = [], other = [], incoming = [];
let q = 0;
const pay = (to, avax, ts) => { const o = { c: 0, to, v: BigInt(Math.round(avax * 1e6)) * 10n ** 12n, ts, blk: blkOf(ts), tx: '0x' + hex(1000 + q, 64), q: q++ }; (wallets.has(to) ? cb : other).push(o); return o; };
pay(addr(0), 0.05, utc(2026, 8, 1, 2, 30));
pay(addr(0), 0.193, utc(2026, 9, 3, 2, 30));
pay(addr(1), 4.25, utc(2026, 9, 3, 2, 30));
pay(addr(1), 0.5, utc(2026, 9, 5, 2, 30));
pay(addr(1), 0.25, utc(2026, 9, 5, 4, 30));
// 400 AVAX arrives from an outside address and leaves for another in the same transaction, and 7 AVAX leaves on its own
const through = pay(OUTSIDE, 400, utc(2026, 9, 6, 10));
incoming.push({ c: 0, from: FUNDER, v: 400n * E18, ts: through.ts, blk: through.blk, tx: through.tx });
pay(OUTSIDE, 7, utc(2026, 9, 7, 10));
incoming.push({ c: 0, from: FUNDER, v: 50n * E18, ts: utc(2026, 9, 8, 10), blk: blkOf(utc(2026, 9, 8, 10)), tx: '0x' + hex(5000, 64) });

// Chainlink rounds every 10 minutes from 23:50 on August 19, price rising by a cent each round from $7.00
const rounds = [];
for (let k = 0, t = utc(2026, 8, 19, 23, 50); t <= utc(2026, 10, 10, 0, 30); k++, t += 600)
  rounds.push({ round: 36893488147419103232n + BigInt(k), answer: 700000000n + BigInt(k) * 1000000n, updated: t, blk: blkOf(t), ts: t });

(async () => {
  const S = { wallets, infra: [], xfers: xs, spent, cashback: cb, other, incoming, rounds, counts: { transfers_scanned: xs.length, end_block_time: 'x', next_block_time: 'y', price_start_block_time: 'z', cl_aggregator: ECB.CL_AGG, cl_phase: 2, cl_decimals: 8, spend_logs_by_token: {} } };
  const R = await ECB.analyze(S);
  const csv = name => R.files[name].trim().split('\n').map(l => l.split(','));
  // card payments and reversals from August 15, in cents, by wallet position
  const sp = csv('spends.csv');
  assert.deepStrictEqual(sp[0], ['wallet', 'ts', 'kind', 'cents', 'spend_event']);
  assert.deepStrictEqual(sp.slice(1).map(r => [r[0], r[2], r[3], r[4]]), [['0', 'c', '3616', '1'], ['1', 'c', '79509', '1'], ['2', 'c', '91', '0'], ['1', 'r', '2500', '']]);
  // the spend events, matched one to one, with the payment that has none and the event that has no payment
  const se = R.meta.spend_events;
  assert.deepStrictEqual([se.usde_logs, se.matched_to_card_payments, se.card_payments_without_event, se.card_payments_without_event_wei, se.events_without_card_payment, se.from_wallets],
                         [4, 3, 1, String(91n * CENT), 1, 4]);
  assert.strictEqual(se.to_october_5.logs, 4, 'every synthetic event falls before the end of October 5');
  assert.strictEqual(sp[1][1], String(utc(2026, 9, 1, 17, 47)));
  assert.strictEqual(R.meta.card_payments, 4, 'every card payment counted, the August 10 one too');
  assert.strictEqual(R.meta.reversals, 1);
  // cashback rows from August 15, batches by account with a three-hour gap
  const c = csv('cashback.csv');
  assert.deepStrictEqual(c.slice(1).map(r => [r[1], r[2], r[4]]), [['1', '0', '193000000000000000'], ['1', '1', '4250000000000000000'], ['2', '1', '500000000000000000'], ['2', '1', '250000000000000000']]);
  const b = csv('batches.csv');
  assert.strictEqual(b.length - 1, 3, 'three batches, the August 1 one included');
  assert.deepStrictEqual(b[2].slice(0, 7), ['0', '1', String(utc(2026, 9, 3, 2, 30)), String(utc(2026, 9, 3, 2, 30)), '2', '2', '2']);
  assert.deepStrictEqual(b[3].slice(4, 7), ['2', '2', '1'], 'two transfers two hours apart are one batch');
  // the round in force at 02:30 on September 3, the one updated at 02:30, and none for the August 1 batch
  const k = (utc(2026, 9, 3, 2, 30) - utc(2026, 8, 19, 23, 50)) / 600;
  assert.strictEqual(b[2][9], String(700000000n + BigInt(k) * 1000000n));
  assert.strictEqual(b[2][10], String(utc(2026, 9, 3, 2, 30)));
  assert.strictEqual(b[1][8], '', 'no price before August 20');
  // the price in force each hour
  const p = csv('prices_hourly.csv');
  assert.deepStrictEqual(p[1], ['2026-08-20T00:00:00Z', '36893488147419103233', '701000000', String(utc(2026, 8, 20))]);
  assert.deepStrictEqual(p[2].slice(2), ['707000000', String(utc(2026, 8, 20, 1, 0))], 'at 01:00 the round of 01:00 is in force');
  assert.strictEqual(p.length - 1, (utc(2026, 10, 10) - utc(2026, 8, 20)) / 3600 + 1);
  // each cashback transfer carries the round in force at its own time, so the transfer at 04:30 has a later price than its batch
  const k2 = (utc(2026, 9, 5, 4, 30) - utc(2026, 8, 19, 23, 50)) / 600;
  assert.deepStrictEqual(c[4].slice(5), [String(36893488147419103232n + BigInt(k2)), String(700000000n + BigInt(k2) * 1000000n)]);
  assert.deepStrictEqual(c[3].slice(5), [b[3][8], b[3][9]], 'the first transfer of a batch has the batch price');
  // transfers to an address that is not a wallet are listed apart, without the address, with what the account received in the same transaction
  const o = csv('other_recipients.csv');
  assert.deepStrictEqual(o.slice(1), [['0', '1', String(utc(2026, 9, 6, 10)), '400000000000000000000', '400000000000000000000'],
                                       ['0', '1', String(utc(2026, 9, 7, 10)), '7000000000000000000', '0']]);
  assert.strictEqual(R.meta.other_recipient_passed_through, 1);
  assert.deepStrictEqual(R.meta.cashback_account_incoming[0], { transfers: 2, avax_wei: '450000000000000000000', senders: 1 });
  assert.deepStrictEqual(R.meta.cashback_account_incoming[1], { transfers: 0, avax_wei: '0', senders: 0 });
  assert.ok(!Object.values(R.files).some(t => t.includes(OUTSIDE.slice(2)) || t.includes(addr(0).slice(2))), 'no address written');
  assert.strictEqual(R.meta.cross_checks.recount_wallet_rows, 3, 'three wallets received USDe by October 5');
  // a card payment that is not a whole number of cents stops the run
  const bad = xs.slice(); bad.push({ f: addr(0), t: S0, fw: true, tw: false, v: 3616n * CENT + 1n, ts: utc(2026, 9, 20), blk: blkOf(utc(2026, 9, 20)), tx: '0x' + hex(999, 64), q: 999 });
  await assert.rejects(ECB.analyze({ ...S, xfers: bad }), /whole number of cents/);
  // a first round after 00:00 on August 20 stops the run
  await assert.rejects(ECB.analyze({ ...S, rounds: rounds.filter(r => r.updated > utc(2026, 8, 20)) }), /no Chainlink round in force/);
  console.log('all synthetic checks passed');
})().catch(e => { console.error(e); process.exit(1); });
