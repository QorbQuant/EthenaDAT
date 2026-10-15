import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  loadSupplemental,
  supplementalView,
} from "../site-worker/supplemental.mjs";
import { DATASETS } from "../site-worker/dataset-meta.mjs";
import {
  dataset,
  datasetPage,
  datasetDownload,
} from "../site-worker/datasets.mjs";
import { classifyReferral, recordReferral } from "../site-worker/referrals.mjs";
import { PAGES, sitemap, graph } from "../site-worker/seo.mjs";
import { content } from "../site-worker/content.mjs";
const read = (p) => JSON.parse(readFileSync(new URL(p, import.meta.url)));
const sx = read("../docs/data.json"),
  pay = read("../docs/ethenapay.json"),
  flows = read("../output/usdeb-flows.json");
const feeds = {
  sx: { data: sx, fallback: false },
  pay: { data: pay, fallback: false },
};
const now = Date.parse("2026-10-12T01:30:00Z");
const lighter = {
  fetchedAt: new Date(now).toISOString(),
  markPrice: 12,
  openInterestUsd: 0,
  volume24hUsd: null,
  latestFunding: { t: now - 3600000, ratePct: 0 },
  prices: [{ t: now - 3600000, close: 12 }],
  funding: [
    { t: now - 3600000, ratePct: 0 },
    { t: now - 7200000, ratePct: -0.005 },
  ],
};
test("slow supplemental sources are bounded and do not discard a successful independent panel", async () => {
  const background = [];
  const result = await loadSupplemental(
    { waitUntil: (p) => background.push(p) },
    ["fast", "slow", "bad"],
    {
      fast: async () => Response.json({ value: 0 }),
      slow: () =>
        new Promise((resolve) =>
          setTimeout(() => resolve(Response.json({ value: 1 })), 60),
        ),
      bad: async () => {
        throw Error("offline");
      },
    },
    5,
  );
  assert.deepEqual(result, { fast: { value: 0 }, slow: null, bad: null });
  await Promise.all(background);
});
test("supplemental rendering retains zero, missing and delayed distinctions", () => {
  const view = supplementalView(
    {
      tokenized: {
        supply: 0,
        multiplier: "1000000000000000000",
        observedAt: new Date(now - 600000).toISOString(),
        blockNumber: 1,
      },
      lighter,
      flows,
    },
    sx,
    now,
  );
  assert.equal(view.ids["tokenized-supply"], "0");
  assert.match(view.ids["tokenized-status"], /Refresh delayed/);
  assert.equal(view.ids["lighter-oi"], "$0.00");
  assert.equal(view.ids["lighter-volume"], "N/A");
  assert.equal(view.ids["lighter-funding"], "0.0000%");
  assert.match(view.ids["lighter-payer"], /No funding payment/);
  assert.doesNotMatch(view.ids["lighter-payer"], /Unavailable/);
  assert.ok(view.flowRows.includes("<tr>"));
});
test("every dataset is canonical, linked in the sitemap, structured and downloadable", async () => {
  for (const path of Object.keys(DATASETS)) {
    assert.ok(PAGES[path]);
    assert.ok(sitemap().includes(path));
    const d = dataset(path, feeds, { flows, lighter }, now),
      html = await datasetPage(path, d).text();
    assert.equal(d.available, true);
    assert.equal((html.match(/<h1>/g) || []).length, 1);
    const schema = [
      ...html.matchAll(/application\/ld\+json">([\s\S]*?)<\/script>/g),
    ]
      .flatMap((m) => JSON.parse(m[1])["@graph"])
      .find((s) => s["@type"] === "Dataset");
    assert.equal(schema.url, d.canonical);
    assert.equal(schema.distribution.length, 2);
    assert.equal(schema.dateModified, d.sourceUpdatedAt);
    const json = await datasetDownload(d, "json").json();
    assert.equal(json.rows.length, d.rows.length);
    const csv = await datasetDownload(d, "csv").text();
    assert.equal(csv.trim().split("\r\n").length, d.rows.length + 1);
  }
});
test("missing feeds never fabricate zero or a download distribution", async () => {
  for (const path of Object.keys(DATASETS)) {
    const d = dataset(path, {}, {});
    assert.equal(d.available, false);
    assert.deepEqual(d.rows, []);
    const html = await datasetPage(path, d).text();
    assert.match(html, /temporarily unavailable/);
    assert.ok(!html.includes('"distribution"'));
    assert.equal(datasetDownload(d, "json").status, 503);
  }
});
test("partial days use the source cutoff, and delayed snapshots remain dated", () => {
  const d = dataset("/data/ethenapay-spending/", feeds, {}, now + 7 * 86400000);
  assert.equal(d.stale, true);
  assert.equal(d.rows.at(-1).partial, true);
  assert.equal(d.sourceUpdatedAt, pay.generated_at);
});
test("supply stays separate from issuance, and sparse funding observations retain missing prices", () => {
  const d = dataset("/data/usdeb-supply/", {}, { flows }, now);
  assert.equal(d.snapshot.rawSupplyUnits, flows.rawSupply);
  assert.equal(
    BigInt(d.snapshot.rawMintedUnits) - BigInt(d.snapshot.rawBurnedUnits),
    BigInt(d.snapshot.rawSupplyUnits),
  );
  const p = dataset("/data/stablecoinx-perpetuals/", {}, { lighter }, now);
  assert.equal(p.rows[0].trade_close_usd, null);
  assert.equal(p.rows[0].funding_rate_pct, -0.005);
  assert.equal(p.rows[1].funding_rate_pct, 0);
});
const req = (url = "https://ethenadash.com/research/", headers = {}) =>
  new Request(url, {
    headers: { accept: "text/html", "user-agent": "Mozilla/5.0", ...headers },
  });
test("AI referrals use exact domain boundaries and separate campaign attribution", () => {
  assert.deepEqual(
    classifyReferral(
      req(undefined, { referer: "https://www.perplexity.ai/search/private" }),
    ),
    { provider: "Perplexity", method: "referrer" },
  );
  assert.deepEqual(
    classifyReferral(
      req("https://ethenadash.com/research/?utm_source=chatgpt.com"),
    ),
    { provider: "ChatGPT", method: "campaign" },
  );
  assert.equal(
    classifyReferral(
      req(undefined, { referer: "https://chatgpt.com.evil.test/" }),
    ),
    null,
  );
  assert.equal(
    classifyReferral(
      req("https://ethenadash.com/?utm_source=chatgpt.com", {
        referer: "https://ethenadash.com/research/",
      }),
    ),
    null,
  );
  for (const headers of [
    { "user-agent": "ChatGPT-User" },
    { "user-agent": "PerplexityBot" },
    { purpose: "prefetch" },
    { "sec-fetch-dest": "image" },
    { accept: "application/json" },
  ])
    assert.equal(
      classifyReferral(
        req("https://ethenadash.com/?utm_source=chatgpt.com", headers),
      ),
      null,
    );
});
test("referral payload contains only provider, canonical path and attribution, and errors never affect pages", () => {
  const r = req(
    "https://ethenadash.com/?utm_source=chatgpt.com&private=secret",
  );
  let point;
  recordReferral(
    r,
    {
      AI_REFERRALS: {
        writeDataPoint: (p) => {
          point = p;
        },
      },
    },
    "/stablecoinx/",
  );
  assert.deepEqual(point, {
    indexes: ["ChatGPT"],
    blobs: ["ChatGPT", "/stablecoinx/", "campaign"],
    doubles: [1],
  });
  assert.doesNotThrow(() =>
    recordReferral(
      r,
      {
        AI_REFERRALS: {
          writeDataPoint: () => {
            throw Error("offline");
          },
        },
      },
      "/stablecoinx/",
    ),
  );
});
test("all research articles have concise findings and a related dataset", () => {
  const articles = Object.keys(PAGES).filter((p) => PAGES[p].article);
  assert.equal(articles.length, 25);
  for (const path of articles) {
    assert.ok(content[path].includes('class="key-findings"'), path);
    assert.ok(content[path].includes('class="dataset-related"'), path);
    assert.ok(!content[path].includes("\u2014"), path);
  }
});

test("new research citations match visible sources and point readers to relevant data", () => {
  const paths = Object.keys(PAGES).filter((path) => PAGES[path].datePublished === "2026-10-15");
  assert.equal(paths.length, 5);
  for (const path of paths) {
    const article = graph(path)["@graph"].find((item) => item["@type"] === "Article");
    assert.equal(article.datePublished, "2026-10-15");
    assert.ok(article.citation.length > 0);
    for (const source of article.citation) assert.ok(content[path].includes(source), source);
    if (!path.includes("mnav-vs-treasury")) {
      assert.ok(content[path].includes(`href="${path}#reproduce-the-numbers"`));
      assert.ok(content[path].includes('id="reproduce-the-numbers"'));
    }
  }
});
