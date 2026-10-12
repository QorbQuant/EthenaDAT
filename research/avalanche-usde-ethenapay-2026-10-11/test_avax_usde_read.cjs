// Runs the calculation in avax_usde_read.cjs on a small synthetic chain with known answers. No network.
// Usage: node test_avax_usde_read.cjs avax_usde_read.cjs
const path = require('path');
require(path.resolve(process.argv[2]));
const AUR = globalThis.AUR;
const assert = require('assert');

const utc = (y, m, d, hh, mm, ss) => Date.UTC(y, m - 1, d, hh || 0, mm || 0, ss || 0) / 1000;
const E18 = 10n ** 18n;
const hex = (n, len) => n.toString(16).padStart(len, '0');
const addr = i => '0x' + hex(0xabc0000000 + i, 40);
const Z = AUR.ZERO, S0 = AUR.SETTLE[0], RW = AUR.REWARDS[0];
const deployTs = utc(2025, 8, 8, 9, 46, 4);
let li = 0;
const logs = [];
const add = (f, t, usde, ts, empty) => logs.push({ b: 1000 + Math.floor((ts - deployTs) / 2), li: li++, ts, f, t, v: empty ? null : BigInt(usde) * E18,
  h: '0x' + hex(logs.length + 1, 64), topic0: '', addr: '' });

// The chain runs from August 8, 2025 to October 11, 2026. Wallets A and B are EthenaPay wallets created in May and
// September 2026, C is another holder, D a second other holder.
const A = addr(1), B = addr(2), C = addr(3), D = addr(4), E = addr(5);
const wallets = new Map([[A, utc(2026, 5, 15, 15)], [B, utc(2026, 9, 2, 8)], [addr(9), utc(2026, 10, 11, 23, 59, 59)]]);
add(Z, C, 3000, utc(2025, 8, 15, 11));          // 3,000 minted to C
add(C, Z, 2000, utc(2025, 12, 1, 9));           // C burns 2,000
add(Z, A, 500, utc(2026, 5, 20, 10));           // 500 minted straight into wallet A
add(C, A, 250, utc(2026, 6, 1, 10));            // C pays wallet A 250
add(A, S0, 100, utc(2026, 6, 2, 10));           // A spends 100 on the card
add(RW, Z, 0, utc(2026, 6, 3, 10));             // a zero burn changes nothing
add(Z, RW, 10, utc(2026, 6, 3, 9));             // out of order in time: sorted by block and index below
add(RW, A, 5, utc(2026, 6, 4, 10));             // the reward account pays A 5
add(Z, B, 7000, utc(2026, 9, 3, 12));           // 7,000 minted to wallet B
add(B, D, 1000, utc(2026, 9, 20, 12));          // B withdraws 1,000 to D
add(S0, Z, 100, utc(2026, 9, 21, 12));          // settlement bridges 100 out
add(C, A, 999, utc(2026, 9, 22, 12), true);     // a phantom record, not in its receipt
add(A, S0, 50, utc(2026, 9, 25, 12));           // A spends 50 more
add(S0, E, 50, utc(2026, 9, 26, 12));           // the settlement address passes 50 to E, whose only USDe comes from it
add(S0, A, 0, utc(2026, 9, 27, 12));            // a zero reversal back to A changes nothing
add(B, Z, 500, utc(2026, 10, 11, 23, 59, 59));  // wallet B burns 500 in the last second
// the out-of-order mint sits in an earlier block than the zero burn, as on the chain
logs.find(x => x.t === RW && x.f === Z).b = logs.find(x => x.f === RW && x.t === Z).b - 1;

const phantoms = logs.filter(x => x.v === null).map(x => ({ b: x.b, li: x.li, ts: x.ts, f: x.f, t: x.t, in_receipt: false }));
const S = { wallets, logs, phantoms, deployTs };
const R = AUR.analyze(S);
const day = d => R.days.find(r => r.date === d);
const usd = x => Number(x / 10n ** 12n) / 1e6;

assert.strictEqual(R.days[0].date, '2025-08-08');
assert.strictEqual(R.days[R.days.length - 1].date, '2026-10-11');
assert.strictEqual(R.days.length, 430);
assert.strictEqual(R.dropped.length, 1);
assert.strictEqual(usd(day('2025-08-15').supply), 3000);
assert.strictEqual(usd(day('2025-08-15').minted), 3000);
assert.strictEqual(usd(day('2025-12-01').supply), 1000);
assert.strictEqual(usd(day('2025-12-01').burned), 2000);
assert.strictEqual(day('2025-12-01').holders, 1);
assert.strictEqual(usd(day('2026-05-20').minted_to_wallets), 500);
assert.strictEqual(usd(day('2026-05-20').wallets_held), 500);
assert.strictEqual(day('2026-05-20').wallets_with_usde, 1);
assert.strictEqual(day('2026-05-20').wallets_created, 1);
assert.strictEqual(usd(day('2026-06-01').wallets_held), 750);
assert.strictEqual(usd(day('2026-06-01').other_held), 750);
assert.strictEqual(usd(day('2026-06-02').settlement_held), 100);
assert.strictEqual(usd(day('2026-06-03').rewards_held), 10);
assert.strictEqual(usd(day('2026-06-03').supply), 1510);
assert.strictEqual(day('2026-06-03').transfers, 2);
assert.strictEqual(usd(day('2026-06-04').wallets_held), 655);
assert.strictEqual(usd(day('2026-06-04').rewards_held), 5);
assert.strictEqual(day('2026-09-02').wallets_created, 2);
assert.strictEqual(usd(day('2026-09-03').wallets_held), 7655);
assert.strictEqual(day('2026-09-03').wallets_with_usde, 2);
assert.strictEqual(usd(day('2026-09-20').other_held), 1750);
assert.strictEqual(usd(day('2026-09-21').settlement_held), 0);
assert.strictEqual(usd(day('2026-09-21').supply), 8410);
assert.strictEqual(usd(day('2026-09-22').wallets_held), 6655);     // the phantom record is left out
assert.strictEqual(day('2026-09-22').transfers, 0);
const last = R.days[R.days.length - 1];
assert.strictEqual(usd(last.burned_from_wallets), 500);
assert.strictEqual(usd(last.supply), 7910);
assert.strictEqual(usd(last.wallets_held), 6105);
assert.strictEqual(usd(last.recipients_held), 50);
assert.strictEqual(usd(day('2026-09-25').settlement_held), 50);
assert.strictEqual(usd(day('2026-09-26').recipients_held), 50);
assert.strictEqual(R.recipients.size, 1);
assert.strictEqual(last.wallets_created, 3);
assert.strictEqual(last.holders, 6);               // A, B, C, D, E and the reward account
for (const r of R.days) assert.strictEqual(r.wallets_held + r.settlement_held + r.rewards_held + r.recipients_held + r.other_held, r.supply);
const H = Object.fromEntries(R.holderRows.filter(r => r.group !== 'other').map(r => [r.group, r]));
assert.strictEqual(usd(H.ethenapay_wallets.balance), 6105);
const rec = R.holderRows.filter(r => r.group === 'settlement_recipients');
assert.deepStrictEqual(rec.map(r => [r.rank, usd(r.balance), usd(r.flows.from_settlement)]), [[1, 50, 50]]);
assert.strictEqual(R.holderRows.find(r => r.group === 'settlement_recipients_rest').holders, 0);
assert.strictEqual(H.ethenapay_wallets.holders, 2);
assert.strictEqual(usd(H.reward_accounts.balance), 5);
assert.strictEqual(H.settlement.holders, 0);
const others = R.holderRows.filter(r => r.group === 'other');
assert.deepStrictEqual(others.map(r => [r.rank, usd(r.balance)]), [[1, 1000], [2, 750]]);
assert.strictEqual(others[0].first_received, '2026-09-20');
assert.strictEqual(usd(others[0].flows.from_wallets), 1000);
assert.strictEqual(usd(others[1].flows.sent), 2250);
assert.strictEqual(usd(others[1].flows.burned), 2000);
assert.strictEqual(usd(others[1].flows.to_wallets), 250);
assert.strictEqual(usd(others[1].flows.minted_to), 3000);
assert.strictEqual(usd(R.fromOutside), 500 + 250 + 7000);   // mints into wallets and C's payment, not the reward
assert.ok(AUR.csvHolders(R.holderRows).split('\n')[6].endsWith(',1,1000000000000000000000,1000000000000000000000,0,0,1000000000000000000000,0,0,0'));
assert.strictEqual(R.holderRows.find(r => r.group === 'other_rest').holders, 0);
// the flows between groups, before the day of the first wallet, from it to October 5, and after it
const P0 = '2025-08-08 to 2026-05-14', P1 = '2026-05-15 to 2026-10-05', P2 = '2026-10-06 to 2026-10-11';
assert.deepStrictEqual(R.periods, [P0, P1, P2]);
assert.deepStrictEqual(R.flowRows.map(r => [r.period, r.from, r.to, r.n, usd(r.v)]), [
  [P0, 'minted', 'other_accounts', 1, 3000],
  [P0, 'other_accounts', 'burned', 1, 2000],
  [P1, 'minted', 'ethenapay_wallets', 2, 7500],
  [P1, 'minted', 'reward_accounts', 1, 10],
  [P1, 'ethenapay_wallets', 'settlement', 2, 150],
  [P1, 'ethenapay_wallets', 'other_accounts', 1, 1000],
  [P1, 'settlement', 'ethenapay_wallets', 1, 0],
  [P1, 'settlement', 'settlement_recipients', 1, 50],
  [P1, 'settlement', 'burned', 1, 100],
  [P1, 'reward_accounts', 'ethenapay_wallets', 1, 5],
  [P1, 'reward_accounts', 'burned', 1, 0],
  [P1, 'other_accounts', 'ethenapay_wallets', 1, 250],
  [P2, 'ethenapay_wallets', 'burned', 1, 500],
]);
assert.strictEqual(AUR.csvFlows(R.flowRows).split('\n')[0], 'period,from_group,to_group,transfers,usde_wei');
assert.strictEqual(AUR.csvFlows(R.flowRows).split('\n')[3], P1 + ',minted,ethenapay_wallets,2,7500000000000000000000');
// a labeled contract is a group of its own in the flows and stays outside the programme
const RH = Object.keys(AUR.FLOW_KEYS)[0];
const logs2 = [];
const add2 = (f, t, usde, ts) => logs2.push({ b: 1000 + Math.floor((ts - deployTs) / 2), li: logs2.length, ts, f, t, v: BigInt(usde) * E18,
  h: '0x' + hex(logs2.length + 1, 64), topic0: '', addr: '' });
add2(Z, RH, 900, utc(2026, 6, 1, 10));
add2(RH, A, 600, utc(2026, 6, 2, 10));
const R2 = AUR.analyze({ wallets, logs: logs2, phantoms: [], deployTs });
assert.deepStrictEqual(R2.flowRows.map(r => [r.period, r.from, r.to, usd(r.v)]), [[P1, 'minted', 'rhino_fi_bridge_contract', 900], [P1, 'rhino_fi_bridge_contract', 'ethenapay_wallets', 600]]);
assert.strictEqual(usd(R2.fromOutside), 600);
assert.strictEqual(R2.holderRows.find(r => r.group === 'other' && r.rank === 1).label, AUR.LABELS[RH]);

// a record with no value that its receipt does hold must stop the run
assert.throws(() => AUR.analyze({ wallets, logs, phantoms: [], deployTs }), /in its receipt/);
// a balance below zero must stop the run
const badTs = utc(2026, 10, 1, 12);
const bad = logs.filter(x => x.v !== null).concat([{ b: 1000 + Math.floor((badTs - deployTs) / 2), li: 9999, ts: badTs, f: D, t: C, v: 5000n * E18, h: '0x1', topic0: '', addr: '' }]);
assert.throws(() => AUR.analyze({ wallets, logs: bad, phantoms: [], deployTs }), /below zero/);
// two logs with the same block and index must stop the run
const dup = logs.filter(x => x.v !== null).concat([Object.assign({}, logs[0], { h: '0x2' })]);
assert.throws(() => AUR.analyze({ wallets, logs: dup, phantoms: [], deployTs }), /share block/);
// the CSV writers
assert.ok(AUR.csvDaily(R.days).startsWith('date,transfers,minted_wei,burned_wei,supply_wei,'));
assert.strictEqual(AUR.csvDaily(R.days).trim().split('\n').length, 431);
assert.ok(AUR.csvDaily(R.days).split('\n')[0].includes(',reward_accounts_held_wei,settlement_recipients_held_wei,other_held_wei,'));
assert.ok(!/0xabc/.test(AUR.csvHolders(R.holderRows)), 'holders.csv must not hold an address');
console.log('all synthetic checks passed, ' + R.days.length + ' days');
