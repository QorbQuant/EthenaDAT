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

const { prepareExport } = require("../docs/assets/share.js");
const exportFixture = () => ({
  state: { date: "2026-10-09" }, note: "Daily wallets", columns: ["date", "wallets"],
  rows: [["2026-10-07", 390], ["2026-10-08", 412], ["2026-10-09", 352]],
  visual: {
    timeZone: "UTC", selected: Date.parse("2026-10-09T00:00:00Z"),
    rows: [7, 8, 9].map(day => ({ d: `2026-10-0${day}`, t: Date.parse(`2026-10-0${day}T00:00:00Z`) })),
    series: [{ name: "Wallets", data: [390, 412, 352] }],
  },
});
test("excluding today aligns PNG and CSV, clamps highlight and preserves original data", () => {
  const d = exportFixture(), before = JSON.stringify(d);
  const out = prepareExport(d, { includeToday: false, annotate: true }, new Date("2026-10-09T12:00:00Z"));
  assert.equal(JSON.stringify(d), before);
  assert.deepEqual(out.rows, d.rows.slice(0, 2));
  assert.deepEqual(out.visual.series[0].data, [390, 412]);
  assert.equal(out.visual.selected, d.visual.rows[1].t);
  assert.equal(out.state.to, "2026-10-08");
  assert.equal(out.state.date, "2026-10-08");
  assert.equal(out.visual.through, "2026-10-08");
  assert.equal(out.visual.annotate, true);
});
test("exclusion uses dataset timezone and never drops yesterday simply because it is the last row", () => {
  const now = new Date("2026-10-09T01:00:00Z"), d = exportFixture();
  assert.equal(prepareExport(d, { includeToday: false }, now).rows.length, 2);
  d.visual.timeZone = "America/New_York";
  assert.equal(prepareExport(d, { includeToday: false }, now).rows.length, 1);
  assert.equal(prepareExport(d, { includeToday: false }, new Date("2026-10-11T12:00:00Z")).rows.length, 3);
  assert.equal(prepareExport(d, {}, now).rows.length, 3);
});
test("empty exclusion reports an actionable error; hypothetical charts remain unchanged", () => {
  const d = exportFixture();
  assert.throws(() => prepareExport(d, { includeToday: false }, new Date("2026-10-07T12:00:00Z")), /No earlier observations/);
  d.visual.type = "scenario";
  assert.equal(prepareExport(d, { includeToday: false, annotate: true }), d);
});
