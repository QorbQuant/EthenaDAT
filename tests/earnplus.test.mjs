import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import EarnPlus from "../docs/assets/earnplus.js";
import { loadFeed } from "../site-worker/index.mjs";

const snapshot = JSON.parse(readFileSync(new URL("../docs/earnplus.json", import.meta.url)));
test("Earn+ history reconciles net balances and pending withdrawals at fixed UTC blocks", () => {
  assert.equal(EarnPlus.valid(snapshot), true);
  const s = snapshot.series;
  assert.equal(s.date[0], "2026-10-25");
  assert.equal(s.partial.at(-1), true);
  for (let i = 0; i < s.date.length - 1; i++) {
    assert.equal(s.partial[i], false);
    assert.match(s.observed_at[i], /T23:59:5\d/);
    assert.ok(s.block_number[i] < s.block_number[i + 1]);
    assert.ok(Math.abs(s.active_usde[i] + s.pending_usde[i] - s.nav_usde[i]) < 1e-6);
  }
});
test("Earn+ rejects malformed or unreconciled data rather than displaying zero", () => {
  for (const mutate of [
    d => { d.series.pending_usde[0] += 100; },
    d => { d.series.active_usde[0] = null; },
    d => { d.series.date.reverse(); },
    d => { d.series.partial[0] = true; },
    d => { d.chain_id = 1; },
    d => { d.headline.activeEarnBalanceUsde = ""; },
  ]) {
    const d = structuredClone(snapshot); mutate(d);
    assert.equal(EarnPlus.valid(d), false);
  }
  assert.equal(EarnPlus.view(null)["pay-earn-balance"], "N/A");
  assert.match(EarnPlus.view(null)["pay-earn-status"], /unavailable/);
});
test("Earn+ dates distinguish old external accounting, delayed collection and a valid zero", () => {
  const now = Date.parse(snapshot.generated_at);
  const view = EarnPlus.view(snapshot, now);
  assert.match(view["pay-earn-status"], /Observed.*Vault valuation updated/);
  assert.match(EarnPlus.view(snapshot, now + 48 * 3600000)["pay-earn-status"], /Refresh delayed.*Valuation delayed/);
  assert.match(EarnPlus.view(snapshot, now, true)["pay-earn-status"], /Refresh delayed/);
  const d = structuredClone(snapshot), i = d.series.date.length - 1;
  for (const k of ["active_usde", "pending_usde", "nav_usde"]) d.series[k][i] = 0;
  for (const k of ["activeEarnBalanceUsde", "pendingWithdrawalGrossUsde", "vaultReportedNavUsde"]) d.headline[k] = "0";
  d.headline.exposure = null;
  for (const k of ["exposure_usde", "strategy_supplied_usde", "exposure_multiple"]) if (d.series[k]) d.series[k][i] = null;
  assert.equal(EarnPlus.valid(d), true);
  assert.equal(EarnPlus.view(d, now)["pay-earn-balance"], "0.00 USDe");
});
test("Earn+ exposure is attributed to active balances and never summed into customer capital", () => {
  const {series:s, headline:h} = snapshot;
  assert.ok(s.exposure_usde.some(v => v > 1e8));
  for (let i = 0; i < s.date.length; i++) {
    if (s.exposure_usde[i] === null) continue;
    const multiple = s.nav_usde[i] ? s.strategy_supplied_usde[i] / s.nav_usde[i] : 0;
    assert.ok(Math.abs(s.exposure_usde[i] - s.active_usde[i] * multiple) < 1e-5);
    assert.ok(s.exposure_usde[i] <= s.strategy_supplied_usde[i] + 1e-5);
  }
  assert.equal(h.exposure.observedAt, snapshot.generated_at);
  assert.match(EarnPlus.view(snapshot)["pay-earn-multiple"], /×$/);
  const broken = structuredClone(snapshot);
  broken.series.exposure_usde[0] += 1000;
  assert.equal(EarnPlus.valid(broken), false);
});
test("missing exposure leaves vault accounting available and is not rendered as zero", () => {
  const d = structuredClone(snapshot), i = d.series.date.length - 1;
  d.headline.exposure = null;
  for (const k of ["exposure_usde", "strategy_supplied_usde", "exposure_multiple"]) d.series[k][i] = null;
  assert.equal(EarnPlus.valid(d), true);
  assert.equal(EarnPlus.view(d)["pay-earn-exposure"], "N/A");
  assert.notEqual(EarnPlus.view(d)["pay-earn-balance"], "N/A");
  assert.match(EarnPlus.view(d)["pay-earn-exposure-status"], /unavailable/);
});
test("Earn+ feed falls back independently after a failed upstream request", async () => {
  const env = { ASSETS: { fetch: async () => Response.json(snapshot) } };
  const result = await loadFeed("earnplus.json", "earn", env, "http://localhost", { waitUntil() {} },
    async () => { throw Error("offline"); }, null);
  assert.equal(result.fallback, true);
  assert.equal(result.data.generated_at, snapshot.generated_at);
  const unavailable = await loadFeed("earnplus.json", "earn", {ASSETS:{fetch: async () => Response.json({})}},
    "http://localhost", {waitUntil(){}}, async () => Response.json({}), null);
  assert.equal(unavailable.data, null);
});
