import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url),
  d3 = require("../docs/assets/d3.min.js");
const source = await readFile(
  new URL("../docs/assets/export.js", import.meta.url),
  "utf8",
);
const { renderCard } = await import(
  "data:text/javascript;base64," + Buffer.from(source).toString("base64")
);
const fixture = () => ({
  title: "Price",
  updated: "2026-10-05T22:33:00Z",
  subtitle: "USD",
  note: "Sources & notes",
  url: "https://ethenadash.com/stablecoinx/",
  visual: {
    title: "StablecoinX vs ENA",
    category: "STABLECOINX",
    description: "Price performance since listing",
    caveat: "26 Jun 2026 = 100.",
    source: "Market data",
    rows: [
      { t: 1, d: "2026-06-26" },
      { t: 2, d: "2026-06-27" },
      { t: 3, d: "2026-06-28" },
    ],
    series: [{ name: "ENA", color: "#8aa9cf", data: [100, 150, 200] }],
    axisFormat: String,
    format: String,
    metricFormat: (v) => (v - 100).toFixed(1) + "%",
    selected: 2,
  },
});
test("share card preserves selected observation and fixed index basis", () => {
  const d = fixture(),
    xml = renderCard(d, d3);
  assert.ok(xml.includes(">50.0%</text>"));
  assert.ok(!xml.includes(">100.0%</text>"));
  assert.ok(xml.includes('width="1600" height="900"'));
  assert.ok(xml.includes("Sources &amp; notes"));
  assert.doesNotMatch(xml, /NaN|Infinity|undefined/);
});
test("missing selected values remain missing while the plotted line has a gap", () => {
  const d = fixture();
  d.visual.series[0].data[1] = null;
  const xml = renderCard(d, d3);
  assert.ok(xml.includes(">—</text>"));
  assert.doesNotMatch(xml, /NaN|Infinity/);
  assert.match(xml, /<path d="M[^\"]*M[^\"]*" fill="none"/);
});
test("single date, flat zero values and negative bar exports stay finite", () => {
  const d = fixture();
  d.visual.rows = [{ t: 1, d: "2026-06-26" }];
  d.visual.series = [
    { name: "Withdrawals", data: [-100], kind: "bar" },
    { name: "Deposits", data: [0], kind: "bar" },
  ];
  assert.doesNotMatch(renderCard(d, d3), /NaN|Infinity/);
  d.visual.series[0].data = [0];
  assert.doesNotMatch(renderCard(d, d3), /NaN|Infinity/);
});
test("scenario and attribution exports retain explicit assumptions and valid geometry", () => {
  const d = fixture();
  d.visual.type = "scenario";
  d.visual.scenario = {
    ena: 0.35,
    mnav: 0.7,
    per: 125.48,
    currentEna: 0.25,
    currentMnav: 0.48,
  };
  assert.ok(renderCard(d, d3).includes("$30.74"));
  assert.doesNotMatch(renderCard(d, d3), /NaN|Infinity/);
  d.visual.type = "waterfall";
  d.visual.start = 3.7;
  d.visual.end = 7.61;
  d.visual.contributions = [3.73, 0, 0.18];
  assert.ok(renderCard(d, d3).includes("ENA per share"));
  assert.doesNotMatch(renderCard(d, d3), /NaN|Infinity/);
});
test("titles and provenance are XML escaped", () => {
  const d = fixture();
  d.visual.title = '<unsafe & "quoted">';
  const xml = renderCard(d, d3);
  assert.ok(xml.includes("&lt;unsafe &amp; &quot;quoted&quot;&gt;"));
  assert.ok(!xml.includes("<unsafe"));
});

test("continuous scenario selections use exact values rather than snapping to a sampled point", () => {
  const d = fixture();
  d.visual.xFormat = (v) => "$" + v.toFixed(0);
  d.visual.contextFormat = (v) => "$" + v.toFixed(2);
  d.visual.selected = 2.25;
  d.visual.metricValues = [162.5];
  const xml = renderCard(d, d3);
  assert.ok(xml.includes(">62.5%</text>"));
  assert.ok(xml.includes(">$2.25</text>"));
});
