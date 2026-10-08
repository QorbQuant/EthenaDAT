import { test } from "node:test";
import assert from "node:assert/strict";
import {
  normalizeTokenized,
  tokenizedResponse,
  TOKEN,
} from "../site-worker/tokenized.mjs";
const now = Date.parse("2026-10-08T15:00:00Z");
const word = (n) => "0x" + BigInt(n).toString(16).padStart(64, "0");
const block = {
  number: "0x789b93f",
  timestamp: "0x" + (now / 1000).toString(16),
};
const values = {
  symbol: word(32) + word(5).slice(2) + "5553444542".padEnd(64, "0"),
  decimals: word(18),
  supply: word(1000n * 10n ** 18n),
  multiplier: word(10n ** 18n),
  uiSupply: word(1000n * 10n ** 18n),
};
test("supply follows the corporate-action multiplier without changing raw units", () => {
  assert.equal(normalizeTokenized(block, values, now).supply, 1000);
  const scaled = normalizeTokenized(
    block,
    {
      ...values,
      multiplier: word(2n * 10n ** 18n),
      uiSupply: word(2000n * 10n ** 18n),
    },
    now,
  );
  assert.equal(scaled.supply, 2000);
  assert.equal(scaled.rawSupply, (1000n * 10n ** 18n).toString());
  assert.equal(
    normalizeTokenized(
      block,
      { ...values, supply: word(0), uiSupply: word(0) },
      now,
    ).supply,
    0,
  );
});
test("wrong identity, mismatched units, corrupt results and stale blocks are rejected", () => {
  for (const change of [
    { symbol: "0x" },
    { decimals: word(8) },
    { multiplier: word(0) },
    { uiSupply: word(1) },
    { supply: null },
    { supply: "0x" },
  ])
    assert.throws(() =>
      normalizeTokenized(block, { ...values, ...change }, now),
    );
  assert.throws(() => normalizeTokenized(block, values, now + 301000));
  assert.throws(() => normalizeTokenized(block, values, now - 31000));
});
test("reads are pinned to one verified BNB block and tolerate reordered RPC batches", async () => {
  let requests = 0;
  const response = await tokenizedResponse(
    { waitUntil: () => {} },
    async (url, options) => {
      const calls = JSON.parse(options.body);
      requests++;
      if (requests === 1)
        return Response.json([
          { id: 1, result: block },
          { id: 0, result: "0x38" },
        ]);
      assert.equal(calls.length, 5);
      for (const c of calls) {
        assert.equal(c.method, "eth_call");
        assert.equal(c.params[0].to, TOKEN);
        assert.equal(c.params[1], block.number);
      }
      return Response.json(
        Object.values(values)
          .map((result, id) => ({ id, result }))
          .reverse(),
      );
    },
    null,
    now,
  );
  assert.equal(response.status, 200);
  assert.equal((await response.json()).supply, 1000);
  assert.equal(requests, 2);
});
test("outages retain a labelled snapshot, expire after six hours and never invent zeros", async () => {
  const saved = normalizeTokenized(block, values, now);
  const cache = { match: async () => Response.json(saved) };
  const fail = async () => {
    throw Error("offline");
  };
  const cached = await tokenizedResponse({}, fail, cache, now + 1000);
  assert.equal((await cached.json()).stale, false);
  const stale = await tokenizedResponse({}, fail, cache, now + 3600000);
  assert.equal((await stale.json()).stale, true);
  const expired = await tokenizedResponse({}, fail, cache, now + 7 * 3600000);
  assert.equal(expired.status, 503);
  assert.equal((await expired.json()).supply, undefined);
});
test("wrong chain and incomplete RPC batches fail closed", async () => {
  for (const rows of [
    [
      { id: 0, result: "0x1" },
      { id: 1, result: block },
    ],
    [{ id: 0, result: "0x38" }],
    [
      { id: 0, result: "0x38" },
      { id: 0, result: block },
    ],
  ]) {
    const r = await tokenizedResponse(
      {},
      async () => Response.json(rows),
      null,
      now,
    );
    assert.equal(r.status, 503);
  }
});
