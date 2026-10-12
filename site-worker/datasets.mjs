import Ethena from "../docs/assets/data.js";
import { flowWindow } from "../docs/assets/tokenized-flow-model.mjs";
import { DATASETS } from "./dataset-meta.mjs";
import { ORIGIN, esc, documentPage } from "./seo.mjs";
import { usd, num, stamp } from "./render.mjs";
const clean = (n) => (Number.isFinite(n) ? n : null);
const day = (t) => new Date(t).toISOString().slice(0, 10);
const table = (columns, rows) =>
  `<div class="research-table" role="region" tabindex="0" aria-label="Dataset observations"><table><thead><tr>${columns.map((c) => `<th scope="col">${esc(c.label)}</th>`).join("")}</tr></thead><tbody>${rows.map((r) => `<tr>${columns.map((c) => `<td>${esc(r[c.key] == null ? "Unavailable" : typeof r[c.key] === "number" ? r[c.key].toLocaleString("en-US", { maximumFractionDigits: 6 }) : String(r[c.key]))}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
const cols = (fields) => fields.map(([key, label]) => ({ key, label }));
export function dataset(path, feeds = {}, markets = {}, now = Date.now()) {
  const def = DATASETS[path];
  if (!def) return null;
  let rows = [],
    columns = [],
    asOf = null,
    observedThrough = null,
    stale = false,
    snapshot = {},
    notes = [];
  if (def.key === "valuation" && feeds.sx?.data) {
    const d = feeds.sx.data,
      s = d.series;
    asOf = d.generated_at;
    observedThrough = s.date.at(-1);
    stale = feeds.sx.fallback || now - Date.parse(asOf) > 72 * 3600000;
    columns = cols([
      ["date", "Session date"],
      ["usde_close", "USDE close (USD)"],
      ["ena_price", "ENA daily price (USD)"],
      ["ena_holdings", "Reported ENA"],
      ["shares_outstanding", "Class A shares"],
      ["nav_per_share", "Token NAV / share (USD)"],
      ["mnav", "mNAV (multiple)"],
    ]);
    rows = s.date.map((date, i) =>
      Object.fromEntries(
        columns.map((c) => [
          c.key,
          c.key === "date" ? date : clean(s[c.key]?.[i]),
        ]),
      ),
    );
    snapshot = rows.at(-1) || {};
    notes.push(
      "The latest recorded session can precede the feed refresh. This dataset intentionally excludes browser-only intraday quotes.",
    );
  } else if (def.key === "spending" && feeds.pay?.data) {
    const d = Ethena.normalizePay(feeds.pay.data),
      s = d.series;
    asOf = d.generated_at;
    observedThrough = s.date.at(-1);
    stale = feeds.pay.fallback || now - Date.parse(asOf) > 36 * 3600000;
    columns = cols([
      ["date", "UTC day"],
      ["spend_usde", "Spend (USDe)"],
      ["spend_count", "Spend events"],
      ["active_wallets", "Spending wallets"],
      ["partial", "Potentially partial day"],
    ]);
    rows = s.date.map((date, i) => ({
      date,
      spend_usde: clean(s.spend_usde[i]),
      spend_count: clean(s.spend_count[i]),
      active_wallets: clean(s.active_wallets[i]),
      partial: date >= asOf.slice(0, 10),
    }));
    snapshot = rows.at(-1) || {};
  } else if (def.key === "supply" && markets.flows) {
    const f = markets.flows,
      w = flowWindow(f, "all");
    asOf = f.generatedAt;
    observedThrough = f.observedAt;
    stale = f.stale || now - Date.parse(f.observedAt) > 36 * 3600000;
    columns = cols([
      ["date", "UTC day"],
      ["minted", "Minted (raw USDEB)"],
      ["burned", "Burned (raw USDEB)"],
      ["net", "Net issuance (raw USDEB)"],
      ["partial", "Partial day"],
    ]);
    rows = w.rows.map((r) => ({
      date: day(r.t),
      minted: r.minted,
      burned: r.burned,
      net: r.net,
      partial: r.partial,
    }));
    snapshot = {
      blockNumber: f.blockNumber,
      rawSupplyUnits: f.rawSupply,
      rawMintedUnits: f.rawMinted,
      rawBurnedUnits: f.rawBurned,
      multiplier: f.multiplier,
      adjustedSupplyUnits: f.adjustedSupply,
      decimals: 18,
      reconciled: f.reconciled,
    };
    notes.push(
      `Reconciled supply at block ${num(f.blockNumber)}: ${(Number(f.adjustedSupply) / 1e18).toLocaleString("en-US", { maximumFractionDigits: 6 })} USDEB. Downloads retain exact 18-decimal integer totals in JSON; daily CSV amounts are decimal approximations.`,
      `${f.adjustments.length} multiplier scheduling event(s) recorded separately. The dashboard's current supply panel may show a later block than this reconciled history.`,
    );
  } else if (def.key === "perpetuals" && markets.lighter) {
    const l = markets.lighter;
    asOf = l.fetchedAt;
    observedThrough = l.fetchedAt;
    stale = l.stale || now - Date.parse(l.fetchedAt) > 120000;
    columns = cols([
      ["time", "Observation (UTC)"],
      ["trade_close_usd", "Hourly trade close (USD)"],
      ["funding_rate_pct", "Settled funding (%)"],
    ]);
    const records = new Map();
    for (const p of l.prices || [])
      records.set(p.t, {
        time: new Date(p.t).toISOString(),
        trade_close_usd: clean(p.close),
        funding_rate_pct: null,
      });
    for (const f of l.funding || []) {
      const r = records.get(f.t) || {
        time: new Date(f.t).toISOString(),
        trade_close_usd: null,
      };
      r.funding_rate_pct = clean(f.ratePct);
      records.set(f.t, r);
    }
    rows = [...records.entries()].sort((a, b) => a[0] - b[0]).map(([, r]) => r);
    snapshot = {
      marketId: 229,
      markPriceUsd: l.markPrice,
      openInterestUsd: clean(l.openInterestUsd),
      volume24hUsd: clean(l.volume24hUsd),
      latestFunding: l.latestFunding,
      historyDelayed: l.historyDelayed || {},
    };
    notes.push(
      `Market snapshot: mark ${usd(l.markPrice)}, open interest ${usd(l.openInterestUsd, 0)}, 24h traded notional ${usd(l.volume24hUsd, 0)}.`,
      `Latest settled funding: ${l.latestFunding ? l.latestFunding.ratePct.toFixed(4) + "% at " + stamp(new Date(l.latestFunding.t).toISOString()) : "unavailable"}.`,
    );
    if (l.historyDelayed?.funding || l.historyDelayed?.prices)
      notes.push(
        "One or more history feeds are delayed. Historical observation timestamps remain unchanged.",
      );
  }
  return {
    name: def.name,
    canonical: ORIGIN + path,
    definition: def.definition,
    limitations: def.limits,
    sourceUpdatedAt: asOf,
    observedThrough,
    stale: !!stale,
    available: !!asOf,
    columns,
    rows,
    snapshot,
    notes,
    sources: def.sources.map(([name, url]) => ({ name, url })),
  };
}
export function datasetIndex() {
  return documentPage(
    "/data/",
    `<div class="editorial-kicker">Data / Observations and definitions</div><h1>The data behind the charts.</h1><p class="editorial-lede">Dated observations you can inspect, download and cite. Each dataset explains its units, sources and limits.</p><div class="article-list">${Object.entries(
      DATASETS,
    )
      .map(
        ([path, d]) =>
          `<a href="${path}"><span>Dataset / ${esc(d.key)}</span><h2>${esc(d.name)}</h2><p>${esc(d.description)}</p><b>Explore the data →</b></a>`,
      )
      .join("")}</div>`,
  );
}
export function datasetPage(path, d) {
  const def = DATASETS[path];
  const schema = {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "@id": ORIGIN + path + "#dataset",
    url: ORIGIN + path,
    name: def.name,
    description: def.description,
    creator: { "@id": ORIGIN + "/about/#author" },
    isAccessibleForFree: true,
    citation: def.sources.map(([, url]) => url),
    measurementTechnique: def.definition,
    variableMeasured: d.columns.map((c) => ({
      "@type": "PropertyValue",
      name: c.label,
      propertyID: c.key,
    })),
    ...(d.available
      ? {
          dateModified: d.sourceUpdatedAt,
          temporalCoverage: d.rows.length
            ? d.rows[0].date || d.rows[0].time
            : d.observedThrough,
          distribution: ["csv", "json"].map((type) => ({
            "@type": "DataDownload",
            encodingFormat: type === "csv" ? "text/csv" : "application/json",
            contentUrl: ORIGIN + path + "download." + type,
          })),
        }
      : {}),
  };
  if (d.rows.length)
    schema.temporalCoverage =
      (d.rows[0].date || d.rows[0].time) +
      "/" +
      (d.rows.at(-1).date || d.rows.at(-1).time);
  const dates = d.available
    ? `<p class="research-cutoff">Observed through ${esc(d.observedThrough.length > 10 ? stamp(d.observedThrough) : d.observedThrough)} · Source refreshed ${esc(stamp(d.sourceUpdatedAt))}${d.stale ? " · Refresh delayed; showing the last available snapshot." : ""}</p>`
    : '<p role="status">Data is temporarily unavailable. Please try again shortly.</p>';
  const body = `<article><div class="editorial-kicker">Dataset / ${esc(def.key)}</div><h1>${esc(def.name)}</h1><p class="editorial-lede">${esc(def.definition)}</p>${dates}<p><a href="${def.dashboard}">Open the dashboard →</a> · <a href="/data/">All datasets</a></p>${d.available ? `<p class="dataset-downloads"><a download href="${path}download.csv">Download CSV ↓</a><a download href="${path}download.json">Download JSON ↓</a></p>` : ""}${d.notes.map((n) => `<p>${esc(n)}</p>`).join("")}<h2>Reading the data</h2><p>${esc(def.limits)}</p><p><a href="${def.guide}">Read the detailed methodology and analysis →</a></p>${d.rows.length ? `<h2>Recent observations</h2><p>Latest ${Math.min(30, d.rows.length)} of ${d.rows.length} observations, newest first. Downloads contain all observations available in this dataset. Empty cells in downloads mean unavailable.</p>${table(d.columns, [...d.rows].reverse().slice(0, 30))}` : ""}<h2>Sources and citation</h2><ul>${def.sources.map(([name, url]) => `<li><a href="${esc(url)}" rel="noopener noreferrer">${esc(name)}</a></li>`).join("")}</ul><p>Qorban Ferrell, EthenaDash. ${esc(def.name)}.${d.available ? ` Observation cutoff: ${esc(d.observedThrough)}.` : ""} <a href="${path}">${ORIGIN + path}</a>. This page updates; retain the downloaded snapshot when citing a particular observation.</p><p><a href="/about/">About the author and corrections →</a></p></article>`;
  return documentPage(path, body, 200, schema);
}
export function datasetDownload(d, format) {
  if (!d.available)
    return Response.json(
      { error: "Dataset is temporarily unavailable" },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  const cell = (v) =>
    v == null ? "" : '"' + String(v).replace(/"/g, '""') + '"';
  const body =
    format === "json"
      ? JSON.stringify(d, null, 2)
      : [
          d.columns.map((c) => cell(c.key)).join(","),
          ...d.rows.map((r) => d.columns.map((c) => cell(r[c.key])).join(",")),
        ].join("\r\n") + "\r\n";
  return new Response(body, {
    headers: {
      "Content-Type":
        format === "json"
          ? "application/json; charset=utf-8"
          : "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="${new URL(d.canonical).pathname.split("/")[2]}.${format}"`,
      "Cache-Control": d.stale ? "no-store" : "public, max-age=60",
      "X-Content-Type-Options": "nosniff",
    },
  });
}
