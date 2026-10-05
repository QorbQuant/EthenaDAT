import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import worker, { loadFeed } from "../site-worker/index.mjs";
import {
  PAGES,
  ORIGIN,
  sitemap,
  safeJSON,
  documentPage,
} from "../site-worker/seo.mjs";
import { content } from "../site-worker/content.mjs";
import { rows, values } from "../site-worker/render.mjs";
const D = JSON.parse(
  readFileSync(new URL("../docs/data.json", import.meta.url)),
);
const ctx = { waitUntil: () => {} };
const assetEnv = { ASSETS: { fetch: async () => Response.json(D) } };
test("legacy URLs and alternate hosts redirect directly to one canonical destination", async () => {
  for (const [url, target] of [
    ["https://www.ethenadash.com", "/stablecoinx/"],
    ["https://new.ethenadash.com/ethenapay?x=1", "/ethenapay/?x=1"],
    ["https://ethenadash.com/index.html", "/stablecoinx/"],
    ["http://ethenadash.com/research/", "/research/"],
  ]) {
    const r = await worker.fetch(new Request(url), assetEnv, ctx);
    assert.equal(r.status, 301);
    assert.equal(r.headers.get("Location"), ORIGIN + target);
  }
});
test("unknown addresses return a real 404 and never the dashboard", async () => {
  const r = await worker.fetch(
    new Request(ORIGIN + "/missing-seo-page"),
    { ASSETS: { fetch: async () => new Response("", { status: 404 }) } },
    ctx,
  );
  assert.equal(r.status, 404);
  assert.match(await r.text(), /Page not found/);
});
test("invalid upstream data falls back to a validated deployed snapshot", async () => {
  const r = await loadFeed(
    "data.json",
    "sx",
    assetEnv,
    ORIGIN,
    ctx,
    async () => Response.json({}),
    null,
  );
  assert.equal(r.fallback, true);
  assert.equal(r.data.generated_at, D.generated_at);
});
test("failure of both sources does not fabricate observations", async () => {
  const r = await loadFeed(
    "data.json",
    "sx",
    { ASSETS: { fetch: async () => new Response("bad") } },
    ORIGIN,
    ctx,
    async () => {
      throw Error("offline");
    },
    null,
  );
  assert.equal(r.data, null);
});
test("cached validated data avoids an upstream request", async () => {
  const r = await loadFeed(
    "data.json",
    "sx",
    assetEnv,
    ORIGIN,
    ctx,
    async () => {
      throw Error("must not fetch");
    },
    { match: async () => Response.json(D) },
  );
  assert.equal(r.fallback, false);
  assert.equal(r.data.generated_at, D.generated_at);
});
test("all editorial pages have unique metadata, visible authorship and valid structured data", async () => {
  const titles = new Set();
  for (const [path, body] of Object.entries(content)) {
    const html = await documentPage(path, body).text();
    assert.equal((html.match(/<h1>/g) || []).length, 1);
    assert.ok(html.includes('href="' + ORIGIN + path + '"'));
    const schema = JSON.parse(
      html.match(/application\/ld\+json">([\s\S]*?)<\/script>/)[1],
    );
    assert.ok(schema["@graph"].some((x) => x.name === "Qorban Ferrell"));
    assert.ok(!titles.has(PAGES[path].title));
    titles.add(PAGES[path].title);
  }
});
test("embedded data cannot break out of its script element", () => {
  const value = { x: "</script><script>alert(1)</script>" };
  assert.ok(!safeJSON(value).includes("<"));
  assert.deepEqual(JSON.parse(safeJSON(value)), value);
});
test("sitemap contains each canonical page once without fragments", () => {
  const xml = sitemap();
  assert.equal((xml.match(/<loc>/g) || []).length, Object.keys(PAGES).length);
  assert.ok(!xml.includes("#"));
});
test("initial table and headline use the recorded data, including missing values", () => {
  const html = rows(D, "sx");
  assert.equal((html.match(/<tr>/g) || []).length, 10);
  assert.ok(html.includes(D.series.date.at(-1)));
  const changed = structuredClone(D);
  changed.usde.price = 20;
  assert.equal(values(changed, null).ids["sx-price"], "$20.00");
});
