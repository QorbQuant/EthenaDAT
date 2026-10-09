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
test("share card keeps selected chart marker without header statistics", () => {
  const d = fixture(),
    xml = renderCard(d, d3);
  assert.ok(!xml.includes(">50.0%</text>"));
  assert.match(xml, /<circle cx="846"/);
  assert.ok(!xml.includes(">100.0%</text>"));
  assert.ok(xml.includes('width="3200" height="1800"'));
  assert.ok(xml.includes("Sources &amp; notes"));
  assert.doesNotMatch(xml, /NaN|Infinity|undefined/);
});
test("missing selected values remain missing while the plotted line has a gap", () => {
  const d = fixture();
  d.visual.series[0].data[1] = null;
  const xml = renderCard(d, d3);
  assert.ok(!xml.includes("<circle"));
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
  assert.ok(renderCard(d, d3).includes("Scenario, not a forecast"));
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
  assert.match(xml, /<circle cx="1016\.5"/);
  assert.ok(!xml.includes(">62.5%</text>"));
});

test("exports have one title and a single source footer without duplicate branding or timestamps", () => {
  const xml = renderCard(fixture(), d3);
  assert.ok(
    xml.includes("Source: ethenadash.com / Market data · As of Oct 5, 2026"),
  );
  assert.doesNotMatch(
    xml,
    /OBSERVATION|Charts &amp; methodology|22:33|>ethenadash<|>STABLECOINX</,
  );
  assert.ok(!xml.includes(">Price performance since listing</text>"));
  assert.ok(xml.includes('viewBox="0 0 1600 900"'));
});

test("optional annotation labels the selected value rather than its percent change", () => {
  const d = fixture();
  d.visual.annotate = true;
  d.visual.annotationFormat = v => v.toLocaleString("en-US");
  const xml = renderCard(d, d3);
  assert.match(xml, />150<\/text>/);
  assert.match(xml, /marker-end="url\(#arrow-0\)"/);
  assert.doesNotMatch(xml, />50\.0%<\/text>/);
  d.visual.series[0].data[1] = null;
  assert.ok(!renderCard(d, d3).includes('class="export-annotation"'));
});
test("annotation handles overlapping series and edge points without invalid geometry", () => {
  const d = fixture();
  d.visual.annotate = true;
  d.visual.series.push({ name: "Stock", data: [100, 150, 200] });
  for (const t of [1, 3]) {
    d.visual.selected = t;
    const xml = renderCard(d, d3);
    assert.equal((xml.match(/class="export-annotation"/g) || []).length, 2);
    assert.doesNotMatch(xml, /NaN|Infinity|undefined/);
  }
});
test("excluded current day uses the last included date in the image footer", () => {
  const d = fixture();
  d.visual.through = "2026-10-04";
  assert.match(renderCard(d, d3), /As of Oct 4, 2026/);
});
