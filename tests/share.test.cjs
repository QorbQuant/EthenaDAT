const test = require("node:test");
const assert = require("node:assert/strict");
const { read, windowRows, url, csv } = require("../docs/assets/share.js");

test("share links restore exact dates and validated scenario controls", () => {
  const state = {
    chart: "sx-main-chart",
    mode: "explore",
    range: "30",
    from: "2026-09-08",
    to: "2026-10-05",
    date: "2026-10-02",
    ena: 0.25,
    mnav: 0.48,
  };
  const link = new URL(url("/stablecoinx/", state));
  assert.equal(link.origin, "https://ethenadash.com");
  assert.equal(link.hash, "#sx-main-chart");
  for (const [k, v] of Object.entries(state))
    assert.equal(read(link.search)[k], v);
});
test("invalid controls and impossible calendar dates are rejected", () => {
  const s = read(
    "?chart=%3Cscript%3E&mode=bad&range=-1&ena=Infinity&mnav=4&payoff=-1&from=2026-02-30&to=garbage&factor=bad",
  );
  for (const key of [
    "chart",
    "mode",
    "range",
    "ena",
    "mnav",
    "payoff",
    "factor",
  ])
    assert.equal(s[key], undefined);
  assert.equal(s.from, null);
  assert.equal(s.to, null);
  assert.equal(read("?from=2024-02-29").from, "2024-02-29");
});
test("date windows are inclusive and keep old shared links stable as new rows arrive", () => {
  const rows = ["2026-09-08", "2026-09-09", "2026-09-10"].map((date) => ({
    date,
  }));
  assert.deepEqual(
    windowRows(rows, "2026-09-08", "2026-09-09"),
    rows.slice(0, 2),
  );
  assert.deepEqual(windowRows(rows, "2026-09-09", "2026-09-09"), [rows[1]]);
  assert.equal(windowRows(rows, "2027-01-01", "2027-02-01"), rows);
  assert.deepEqual(windowRows([{ d: "2026-09-09" }], null, "2026-09-09", "d"), [
    { d: "2026-09-09" },
  ]);
});
test("CSV preserves precision, missing values and negative numbers while escaping spreadsheet formulas", () => {
  const output = csv({
    columns: ["date", "amount", "missing", "memo"],
    rows: [
      ["2026-10-05", -12.3456789, null, "=1+1"],
      ["2026-10-04", 0, 0, 'a,"b"\nc'],
    ],
    updated: "2026-10-05T00:00:00Z",
    url: "https://ethenadash.com/ethenapay/",
    note: "Source, note",
  });
  assert.ok(
    output.startsWith(
      "\uFEFFdate,amount,missing,memo,source_updated_utc,exported_utc,view_url,notes\r\n",
    ),
  );
  assert.ok(output.includes("2026-10-05,-12.3456789,,'=1+1,"));
  assert.ok(output.includes('2026-10-04,0,0,"a,""b""\nc"'));
  assert.ok(output.endsWith('"Source, note"\r\n'));
});
test("EthenaPay share links preserve metric, aggregation and reward view", () => {
  const s = read(
    new URL(
      url("/ethenapay/", {
        chart: "pay-main-chart",
        view: "count",
        agg: "total",
        rewards: "daily",
        range: "90",
        payoff: 0,
      }),
    ).search,
  );
  assert.equal(s.view, "count");
  assert.equal(s.agg, "total");
  assert.equal(s.rewards, "daily");
  assert.equal(s.payoff, 0);
});
