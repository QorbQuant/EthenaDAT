import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  validFlows,
  flowWindow,
} from "../docs/assets/tokenized-flow-model.mjs";
import { tokenizedFlowsResponse } from "../site-worker/tokenized-flows.mjs";
const real = JSON.parse(
  readFileSync(new URL("../output/usdeb-flows.json", import.meta.url)),
);
const now = Date.parse(real.generatedAt) + 1000;
test("published history reconciles exactly with its same-block supply", () => {
  assert.equal(validFlows(real, now), true);
  const w = flowWindow(real, "all");
  assert.ok(Math.abs(w.net - Number(real.rawSupply) / 1e18) < 1e-8);
});
test("duplicates, missing burns, wrong units and future snapshots fail validation", () => {
  for (const edit of [
    (d) => d.events.splice(0, 1),
    (d) => d.events.splice(1, 0, d.events[0]),
    (d) => (d.multiplier = "2"),
    (d) => (d.generatedAt = "2099-01-01"),
    (d) => (d.events[0].t = 0),
    (d) => (d.reconciled = false),
  ]) {
    const d = structuredClone(real);
    edit(d);
    assert.equal(validFlows(d, now), false);
  }
});
test("rolling windows exclude older events and retain quiet days and partial boundaries", () => {
  const d = structuredClone(real);
  d.coverageStart = "2026-09-01T00:00:00Z";
  d.observedAt = "2026-10-08T12:00:00Z";
  d.events = [
    {
      t: Date.parse("2026-10-07T11:59:59Z"),
      kind: "mint",
      rawAmount: "9000000000000000000",
    },
    {
      t: Date.parse("2026-10-07T12:00:01Z"),
      kind: "mint",
      rawAmount: "5000000000000000000",
    },
    {
      t: Date.parse("2026-10-08T12:00:00Z"),
      kind: "burn",
      rawAmount: "2000000000000000000",
    },
  ];
  const w = flowWindow(d, "24h");
  assert.equal(w.minted, 5);
  assert.equal(w.burned, 2);
  assert.equal(w.net, 3);
  assert.equal(w.rows.length, 2);
  assert.ok(w.rows.every((r) => r.partial));
  const seven = flowWindow(d, "7d");
  assert.equal(seven.minted, 14);
  assert.equal(seven.rows.length, 8);
  assert.ok(seven.rows.some((r) => !r.minted && !r.burned));
  d.events = [];
  assert.equal(flowWindow(d, "all").net, 0);
});
test("corporate-action adjustment does not change raw flow totals", () => {
  const d = structuredClone(real);
  d.multiplier = "2000000000000000000";
  d.adjustedSupply = (BigInt(d.rawSupply) * 2n).toString();
  assert.ok(validFlows(d, now));
  assert.deepEqual(flowWindow(d, "all"), flowWindow(real, "all"));
});
test("feed preserves labelled fallback on failure and expires old snapshots", async () => {
  const cache = {
    match: async () => Response.json({ data: real, savedAt: now - 600000 }),
  };
  const fail = async () => {
    throw Error("offline");
  };
  let r = await tokenizedFlowsResponse({}, fail, cache, now);
  assert.equal(r.status, 200);
  assert.equal((await r.json()).stale, true);
  r = await tokenizedFlowsResponse({}, fail, cache, now + 8 * 86400000);
  assert.equal(r.status, 503);
  assert.equal((await r.json()).events, undefined);
  r = await tokenizedFlowsResponse(
    { waitUntil: () => {} },
    async () => Response.json(real),
    null,
    now,
  );
  assert.equal((await r.json()).stale, false);
});
