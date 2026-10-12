// Runs the calculation in boost_recount.cjs on a small synthetic chain with known answers.
// Usage: node test_boost_recount.cjs boost_recount.cjs
const path = require('path');
require(path.resolve(process.argv[2]));
const EPB = globalThis.EPB;
const assert = require('assert');

const utc = (y, m, d, hh, mm, ss) => Date.UTC(y, m - 1, d, hh || 0, mm || 0, ss || 0) / 1000;
const E18 = 10n ** 18n;
const hex = (n, len) => n.toString(16).padStart(len, '0');
const addr = i => '0x' + hex(0xabc0000000 + i, 40);
const blkOf = ts => 90000000 + Math.floor((ts - utc(2026, 7, 1)) / 2);
const [S0] = EPB.SETTLE, BASE = EPB.BASE, TOP = EPB.TOPUP[0];
const FUNDER = addr(999999);
const wei = x => BigInt(Math.round(x * 1e6)) * 10n ** 12n;
const M = EPB.MODELS;

const wallets = new Map();
for (let i = 0; i < 6; i++) wallets.set(addr(i), { ts: utc(2026, 7, 1, 0, 0, i), blk: blkOf(utc(2026, 7, 1, 0, 0, i)), gen: 1 });
const xs = [];
const add = (f, t, v, ts) => xs.push({ f, t, fw: wallets.has(f), tw: wallets.has(t), v, ts, blk: blkOf(ts), tx: '0x' + hex(xs.length + 1, 64) });

// wallet 0: 1,000 USDe, standard, spends on September 10 and October 3
// wallet 1: 20,000 USDe, standard, capped at 5,000, spends on September 2, never in October
// wallet 2: 50,000 USDe, the 6% group, never spends
// wallet 3: 300 USDe, never paid a top-up, spent in August only
// wallet 4: 2,000 USDe deposited at 10:00 UTC on September 20, standard
// wallet 5: 150,000 USDe, the 6% group capped at 100,000
// Rates: base 4.0% to September 16 and 4.5% from September 17; top-ups 1.0% and 2.0% to September 15, 0.5% and 1.5% from September 16
const bal = [1000, 20000, 50000, 300, 0, 150000];
bal.forEach((b, i) => { if (b) add(FUNDER, addr(i), BigInt(b) * E18, utc(2026, 7, 2, 12)); });
add(addr(3), S0, 10n * E18, utc(2026, 8, 15, 12));
// wallet 2 and wallet 0 swap 10 USDe and back in July, which links them without moving their balances
add(addr(2), addr(0), 10n * E18, utc(2026, 7, 3, 12));
add(addr(0), addr(2), 10n * E18, utc(2026, 7, 4, 12));
const others = [
  [addr(0), S0, 5n * E18, utc(2026, 9, 10, 12)],
  [addr(1), S0, 7n * E18, utc(2026, 9, 2, 12)],
  [addr(0), S0, 5n * E18, utc(2026, 10, 3, 12)],
  [FUNDER, addr(4), 2000n * E18, utc(2026, 9, 20, 10)],
];
const dayStart = k => utc(2026, 9, 1) + k * 86400;
const events = others.map(e => ({ kind: 'x', e, ts: e[3] }));
for (let k = 0; k < 38; k++) {
  const next = dayStart(k) + 86400;
  events.push({ kind: 'top', k, ts: next + 2.5 * 3600 });
  if (!(k >= 12 && k <= 14)) events.push({ kind: 'base', k, ts: next + 4 * 3600 + 14 * 60 });
  if (k === 14) events.push({ kind: 'basecatch', k, ts: next + 4 * 3600 + 14 * 60 });
}
events.sort((a, b) => a.ts - b.ts);
// time-weighted balances worked out by hand, leaving out the small rewards, which the 1% tolerance absorbs
const twaOf = (i, k) => {
  if (i === 0) return k < 9 ? 1000 : k === 9 ? 1000 - 5 * 12 / 24 : k < 32 ? 995 : k === 32 ? 995 - 5 * 12 / 24 : 990;
  if (i === 1) return k < 1 ? 20000 : k === 1 ? 20000 - 7 * 12 / 24 : 19993;
  if (i === 3) return 290;
  if (i === 4) return k < 19 ? 0 : k === 19 ? 2000 * 14 / 24 : 2000;
  return bal[i];
};
const topRate = (i, k) => {
  const six = i === 2 || i === 5;
  if (i === 3) return 0;
  return six ? (k < 15 ? M.six_2_0 : M.six_1_5) : (k < 15 ? M.standard_1_0 : M.standard_0_5);
};
const cap = [5000, 5000, 1e6, 0, 5000, 100000];
const baseRate = k => (k < 16 ? M.base_4_0 : M.base_4_5);
for (const ev of events) {
  if (ev.kind === 'x') { add(...ev.e); continue; }
  if (ev.kind === 'top') for (let i = 0; i < 6; i++) { const t = Math.min(twaOf(i, ev.k), cap[i]) * topRate(i, ev.k); if (t > 0) add(TOP, addr(i), wei(t), ev.ts); }
  if (ev.kind === 'base') for (let i = 0; i < 6; i++) { const t = twaOf(i, ev.k) * baseRate(ev.k); if (t > 0) add(BASE, addr(i), wei(t), ev.ts); }
  if (ev.kind === 'basecatch') for (let i = 0; i < 6; i++) { let t = 0; for (const k of [12, 13, 14]) t += twaOf(i, k) * baseRate(k); if (t > 0) add(BASE, addr(i), wei(t), ev.ts); }
}
xs.sort((a, b) => a.blk - b.blk || a.ts - b.ts);
xs.forEach((x, i) => { x.q = i; });

(async () => {
  const R = await EPB.analyze({ wallets, infra: [], xfers: xs, counts: { transfers_scanned: xs.length, end_block_time: 'x', next_block_time: 'y' } });
  const csv = name => R.files[name].trim().split('\n').map(l => l.split(','));
  const per = csv('periods.csv'), head = per[0], rows = per.slice(1).map(r => Object.fromEntries(head.map((h, i) => [h, r[i]])));
  const base = rows.filter(r => r.payer === 'base'), top = rows.filter(r => r.payer === 'topup');
  assert.strictEqual(top.length, 38, 'one top-up period a day');
  assert.strictEqual(base.length, 36, 'base periods with one catch-up of three days');
  const catchUp = base.find(r => r.days === '3');
  assert.deepStrictEqual([catchUp.first_day, catchUp.last_day], ['2026-09-13', '2026-09-15']);
  for (const r of base) {
    assert.strictEqual(r.fit_utc, r.tested_wallets, 'every base payment fits on ' + r.first_day);
    const want = r.first_day >= '2026-09-17' ? 'base_4_5' : 'base_4_0';
    assert.strictEqual(r[want], r.tested_wallets, 'base model on ' + r.first_day);
  }
  for (const r of top) {
    const late = r.first_day >= '2026-09-16';
    assert.strictEqual(r.other, '0', 'no unexplained top-up on ' + r.first_day);
    assert.strictEqual(r.unpaid, '1', 'wallet 3 unpaid on ' + r.first_day);
    assert.strictEqual(r[late ? 'six_1_5_cap_100k' : 'six_2_0_cap_100k'], '1', 'wallet 5 capped at 100,000 on ' + r.first_day);
    assert.strictEqual(r[late ? 'six_1_5' : 'six_2_0'], '1', 'wallet 2 on ' + r.first_day);
  }
  const d20 = top.find(r => r.first_day === '2026-09-20');
  assert.strictEqual(d20.standard_0_5, '3', 'wallet 4 counts from its deposit day');
  const d10 = top.find(r => r.first_day === '2026-09-10');
  assert.strictEqual(d10.standard_1_0, '2', 'wallets 0 and 1 at 1.0% before September 16');
  // activity classes for tested wallets
  const act = csv('activity.csv').slice(1).filter(r => r[3] === 'ge100');
  const on = (d, c) => act.find(r => r[1] === d && r[4] === c);
  assert.strictEqual(on('2026-10-01', 'B')[5], '2', 'wallets 0 and 1 spent in September only');
  assert.strictEqual(on('2026-10-01', 'D')[5], '3', 'wallets 2, 4 and 5 never spent');
  assert.strictEqual(on('2026-10-01', 'C')[5], '1', 'wallet 3 spent in August');
  assert.strictEqual(on('2026-10-03', 'A')[5], '1', 'wallet 0 spent on October 3');
  assert.strictEqual(on('2026-09-05', 'A')[5], '1', 'wallet 1 spent on September 2');
  assert.strictEqual(on('2026-09-05', 'B')[5], '1', 'wallet 3 spent in August');
  assert.strictEqual(on('2026-09-05', 'D')[5], '3', 'wallets 0, 2 and 5 had not spent');
  assert.strictEqual(on('2026-10-01', 'D')[7], '3', 'all three paid at a model rate');
  // per-wallet day file
  const w = csv('wallet_day_2026-10-01.csv'); const wh = w[0];
  const row0 = Object.fromEntries(wh.map((h, i) => [h, w[1][i]]));
  assert.strictEqual(row0.wallet, '0');
  assert.ok(Math.abs(Number(row0.twa_micro) / 1e6 / 995 - 1) < 0.005, 'wallet 0 holds about 995 on October 1');
  assert.strictEqual(row0.card_spends_previous_month, '1');
  const row4 = Object.fromEntries(wh.map((h, i) => [h, w[5][i]]));
  assert.strictEqual(row4.wallet, '4');
  assert.ok(Number(row4.topup_wei) > 0);
  assert.strictEqual(R.meta.cross_checks.recount_wallet_rows, 6);
  // one row per wallet and month
  const mw = csv('month_wallets.csv'), mh = mw[0];
  const mrow = (m, i) => { const r = mw.find(x => x[0] === m && x[1] === String(i)); return r && Object.fromEntries(mh.map((h, j) => [h, r[j]])); };
  for (let i = 0; i < 6; i++) assert.ok(mrow('2026-09', i) && mrow('2026-10', i), 'wallet ' + i + ' has a row for each month');
  const s0 = mrow('2026-09', 0), s2 = mrow('2026-09', 2), s3 = mrow('2026-09', 3), s4 = mrow('2026-09', 4), o0 = mrow('2026-10', 0), o1 = mrow('2026-10', 1);
  assert.deepStrictEqual([s0.card_spends_before_month, s0.card_spends_in_month, s0.card_spends_after_month], ['0', '1', '1'], 'wallet 0 spends');
  assert.deepStrictEqual([s0.tested_days, s0.paid_days, s0.wallets_exchanged_with, s0.of_which_spent_in_month], ['30', '30', '1', '0'], 'wallet 0 month');
  assert.deepStrictEqual([s2.card_spends_in_month, s2.card_spends_after_month, s2.wallets_exchanged_with, s2.of_which_spent_in_month], ['0', '0', '1', '1'], 'wallet 2 is linked to wallet 0, which spent in September');
  assert.deepStrictEqual([s3.card_spends_before_month, s3.tested_days, s3.paid_days, s3.topup_wei], ['1', '30', '0', '0'], 'wallet 3 never paid');
  assert.deepStrictEqual([s4.tested_days, s4.paid_days], ['11', '11'], 'wallet 4 from September 20');
  assert.deepStrictEqual([o0.card_spends_before_month, o0.card_spends_in_month, o0.tested_days], ['1', '1', '8'], 'wallet 0 in October');
  assert.deepStrictEqual([o1.card_spends_before_month, o1.card_spends_in_month, o1.card_spends_after_month], ['1', '0', '0'], 'wallet 1 in October');
  let sepTop = 0n; for (const r of top) if (r.first_day < '2026-10-01') sepTop += BigInt(r.paid_wei);
  let rowsTop = 0n; for (const r of mw.slice(1)) if (r[0] === '2026-09') rowsTop += BigInt(r[mh.indexOf('topup_wei')]);
  assert.strictEqual(rowsTop, sepTop, 'September rows add up to the September top-up');
  console.log('all synthetic checks passed');
})().catch(e => { console.error(e); process.exit(1); });
