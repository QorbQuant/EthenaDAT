const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const E = require("../docs/assets/data.js");
const read = (n) =>
  JSON.parse(
    fs.readFileSync(new URL("../docs/" + n + ".json", "file://" + __filename)),
  );
const fresh = () => {
  const d = read("data");
  // Keep the fixture on the test clock as the production feed gains new dates.
  const count = d.series.date.filter(date => date <= "2026-10-05").length;
  for (const key of Object.keys(d.series)) d.series[key] = d.series[key].slice(0, count);
  d.generated_at = "2026-10-05T15:59:51Z";
  d.usde = {
    price: 13.97,
    prev_close: 14.15,
    market_state: "REGULAR",
    quote_time: "2026-10-05T15:59:52Z",
  };
  return d;
};
test("validates required series and accepts null option/warrant observations", () => {
  const d = fresh();
  assert.ok(E.valid(d, "sx"));
  assert.ok(E.valid(read("ethenapay"), "pay"));
  d.series.usde_close.pop();
  assert.equal(E.valid(d, "sx"), false);
  assert.equal(E.valid({}, "sx"), false);
});
test("rejects a corrupt or incomplete feed before it replaces last good data", () => {
  for (const value of [null, 0, "14"]) {
    const d = fresh();
    d.series.usde_close[0] = value;
    assert.equal(E.valid(d, "sx"), false);
  }
  const p = read("ethenapay");
  p.series.date.reverse();
  assert.equal(E.valid(p, "pay"), false);
});
test("quote overlay does not mutate the committed data", () => {
  const d = fresh(),
    before = JSON.stringify(d),
    now = new Date("2026-10-05T17:00:00Z"),
    q = {
      USDE: {
        price: 15,
        prev_close: 14.15,
        t: "2026-10-05T16:59:00Z",
        src: "yahoo",
      },
    },
    v = E.applyQuotes(d, q, { price: 0.3, at: +now }, now);
  assert.equal(JSON.stringify(d), before);
  assert.equal(v.series.usde_close.at(-1), 15);
  assert.equal(v.series.ena_price.at(-1), 0.3);
  assert.equal(v.liveDate, "2026-10-05");
  assert.ok(Math.abs(E.current(v).mnav * 0.3 * E.current(v).per - 15) < 1e-10);
});
test("older proxy quotes cannot replace a newer pipeline price", () => {
  const d = fresh(),
    v = E.applyQuotes(
      d,
      { USDE: { price: 1, t: "2026-10-02T20:00:00Z" } },
      null,
      new Date("2026-10-05T17:00:00Z"),
    );
  assert.equal(v.usde.price, d.usde.price);
});
test("weekend ENA updates current NAV without rewriting Friday history", () => {
  const d = fresh(),
    now = new Date("2026-10-10T17:00:00Z"),
    v = E.applyQuotes(
      d,
      { USDE: { price: 15, t: "2026-10-09T20:00:00Z" } },
      { price: 0.4, at: +now },
      now,
    );
  assert.deepEqual(v.series, d.series);
  assert.equal(E.current(v).ena, 0.4);
  assert.equal(v.liveDate, undefined);
});
test("stale ENA never gets combined into a live series row", () => {
  const d = fresh(),
    now = new Date("2026-10-05T17:00:00Z"),
    v = E.applyQuotes(
      d,
      { USDE: { price: 15, t: "2026-10-05T16:59:00Z" } },
      { price: 0.4, at: +now - 3600000 },
      now,
    );
  assert.deepEqual(v.series, d.series);
  assert.equal(v.liveEna, undefined);
});
test("call trigger excludes intraday observations even after the bell", () => {
  const d = fresh(),
    now = new Date("2026-10-05T21:00:00Z");
  assert.equal(E.completedCloses(d, now).length, d.series.date.length - 1);
  d.usde.market_state = "POST";
  assert.equal(E.completedCloses(d, now).length, d.series.date.length);
  const v = E.applyQuotes(
    d,
    { USDE: { price: 15, t: "2026-10-05T20:00:00Z" } },
    null,
    now,
  );
  assert.equal(E.completedCloses(v, now).length, d.series.date.length);
});
test("lockup waiver is date-dependent and bounded by disclosed holdings", () => {
  const d = fresh();
  assert.equal(E.unlocked(d, new Date("2026-10-05T00:00:00Z")), d.ena_holdings);
  assert.ok(E.unlocked(d, new Date("2026-10-04T00:00:00Z")) < d.ena_holdings);
});
