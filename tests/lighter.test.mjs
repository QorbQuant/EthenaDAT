import { test } from "node:test";
import assert from "node:assert/strict";
import { normalizeLighter, lighterResponse } from "../site-worker/lighter.mjs";

const now = Date.parse("2026-10-06T01:10:00Z"),
  hour = 3600000;
const market = {
  code: 200,
  order_book_details: [
    {
      symbol: "STABLECOINX",
      market_id: 229,
      market_type: "perp",
      status: "active",
      mark_price: "13.7604",
      index_price: "13.8295",
      last_trade_price: 14.0763,
      open_interest: 56666.2,
      daily_quote_token_volume: 388543.639502,
    },
  ],
};
const funding = {
  code: 200,
  fundings: [
    { timestamp: (now - 10 * 60000) / 1000, rate: "0.0004", direction: "long" },
    {
      timestamp: (now - hour - 10 * 60000) / 1000,
      rate: "0.0553",
      direction: "short",
    },
  ],
};
const candles = { code: 200, c: [{ t: now - 10 * 60000, c: 14.0763 }] };
const snapshot = (at = now) => normalizeLighter(market, funding, candles, at);
const ctx = { waitUntil: () => {} };

test("Lighter funding percentages and paying sides are not confused with fractional or eight-hour rates", () => {
  const d = snapshot();
  assert.equal(d.funding[0].ratePct, -0.0553);
  assert.equal(d.latestFunding.ratePct, 0.0004);
  assert.equal(d.latestFunding.t, now - 10 * 60000);
});
test("REST open interest is converted from contracts to notional once; missing fields never become zero", () => {
  assert.ok(Math.abs(snapshot().openInterestUsd - 779749.57848) < 1e-6);
  const m = structuredClone(market);
  m.order_book_details[0].open_interest = null;
  m.order_book_details[0].daily_quote_token_volume = "";
  const d = normalizeLighter(m, funding, candles, now);
  assert.equal(d.openInterestUsd, null);
  assert.equal(d.volume24hUsd, null);
});
test("wrong market and invalid mark prices cannot replace valid data", () => {
  for (const patch of [
    { symbol: "STABLE" },
    { market_id: 118 },
    { market_type: "spot" },
    { mark_price: null },
    { mark_price: 0 },
    { status: "inactive" },
  ]) {
    const m = structuredClone(market);
    Object.assign(m.order_book_details[0], patch);
    assert.throws(() => normalizeLighter(m, funding, candles, now));
  }
});
test("series preserve units, sort and deduplicate observations, and omit invalid or future values", () => {
  const f = structuredClone(funding);
  f.fundings.push(
    f.fundings[0],
    { timestamp: (now + hour) / 1000, rate: "1", direction: "long" },
    { timestamp: (now - 2 * hour) / 1000, rate: null, direction: "long" },
  );
  const c = structuredClone(candles);
  c.c.push({ t: now + hour, c: 15 }, { t: now - hour, c: null });
  const d = normalizeLighter(market, f, c, now);
  assert.equal(d.funding.length, 2);
  assert.equal(d.prices.length, 1);
  assert.equal(d.prices[0].t, now - 10 * 60000);
});
test("optional history failures do not remove the current market snapshot", async () => {
  const r = await lighterResponse(
    ctx,
    async (url) => {
      if (url.includes("orderBookDetails")) return Response.json(market);
      throw Error("History unavailable");
    },
    null,
    now,
  );
  assert.equal(r.status, 200);
  const d = await r.json();
  assert.equal(d.markPrice, 13.7604);
  assert.deepEqual(d.funding, []);
  assert.equal(d.latestFunding, null);
});
test("fresh cache avoids requests; upstream failure retains a labeled snapshot with its original timestamp", async () => {
  const previous = snapshot();
  const cache = { match: async () => Response.json(previous) };
  const unavailable = async () => {
    throw Error("Unavailable");
  };
  const fresh = await (
    await lighterResponse(ctx, unavailable, cache, now + 30000)
  ).json();
  assert.equal(fresh.stale, false);
  const stale = await (
    await lighterResponse(ctx, unavailable, cache, now + hour)
  ).json();
  assert.equal(stale.stale, true);
  assert.equal(stale.fetchedAt, previous.fetchedAt);
  const expired = await lighterResponse(
    ctx,
    unavailable,
    cache,
    now + 7 * hour,
  );
  assert.equal(expired.status, 503);
});
test("an upstream outage without cached data returns an isolated error, never fabricated prices", async () => {
  const r = await lighterResponse(
    ctx,
    async () => Response.json({ code: 500 }),
    null,
    now,
  );
  assert.equal(r.status, 503);
  assert.equal((await r.json()).markPrice, undefined);
});
test("malformed optional history and blank numeric strings are not presented as valid data", () => {
  const m = structuredClone(market);
  m.order_book_details[0].open_interest = " ";
  m.order_book_details[0].daily_quote_token_volume = false;
  const d = normalizeLighter(
    m,
    { code: 200, fundings: {} },
    { code: 200, c: [null, { t: now, c: true }] },
    now,
  );
  assert.equal(d.openInterestUsd, null);
  assert.equal(d.volume24hUsd, null);
  assert.deepEqual(d.funding, []);
  assert.deepEqual(d.prices, []);
});

test("partial history outages retain verified observations and explicitly label the delayed history", async () => {
  const previous = snapshot();
  const cache = {
    match: async () => Response.json(previous),
    put: async () => {},
  };
  const r = await lighterResponse(
    ctx,
    async (url) =>
      Response.json(url.includes("orderBookDetails") ? market : { code: 200 }),
    cache,
    now + hour,
  );
  const d = await r.json();
  assert.equal(d.stale, false);
  assert.deepEqual(d.funding, previous.funding);
  assert.deepEqual(d.prices, previous.prices);
  assert.equal(d.latestFunding.t, previous.latestFunding.t);
  assert.deepEqual(d.historyDelayed, { funding: true, prices: true });
});
