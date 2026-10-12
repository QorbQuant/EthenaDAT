import { tokenizedResponse } from "./tokenized.mjs";
import { tokenizedFlowsResponse } from "./tokenized-flows.mjs";
import { lighterResponse } from "./lighter.mjs";
import { flowWindow } from "../docs/assets/tokenized-flow-model.mjs";
import { num, usd, compact, stamp } from "./render.mjs";
import { esc } from "./seo.mjs";

// A slow market must not hold up the dashboard. Let timed-out work warm the cache.
export async function loadSupplemental(
  ctx,
  names = ["tokenized", "flows", "lighter"],
  providers = {
    tokenized: tokenizedResponse,
    flows: tokenizedFlowsResponse,
    lighter: lighterResponse,
  },
  deadline = 1800,
) {
  return Object.fromEntries(
    await Promise.all(
      names.map(async (name) => {
        const work = Promise.resolve()
          .then(() => providers[name](ctx))
          .then(async (r) => (r.ok ? await r.json() : null))
          .catch(() => null);
        ctx.waitUntil(work);
        let timer;
        const timeout = new Promise((resolve) => {
          timer = setTimeout(() => resolve(null), deadline);
        });
        const data = await Promise.race([work, timeout]);
        clearTimeout(timer);
        return [name, data];
      }),
    ),
  );
}
const decimal = (v, digits = 2) =>
  Number.isFinite(v)
    ? v.toLocaleString("en-US", { maximumFractionDigits: digits })
    : "N/A";
const signed = (v) =>
  Number.isFinite(v) ? (v > 0 ? "+" : "") + decimal(v) : "N/A";
export function supplementalView(markets = {}, sx, now = Date.now()) {
  const { tokenized: t, flows: f, lighter: l } = markets,
    s = sx?.series;
  const ids = {
    "tokenized-status":
      "USDEB chain data is temporarily unavailable. The panel will retry when visible.",
    "tokenized-flow-status":
      "Supply-flow history is temporarily unavailable. The panel will retry when visible.",
    "lighter-status":
      "Lighter is temporarily unavailable. The panel will retry when visible.",
    "lighter-payer": "Funding history unavailable",
  };
  let flowRows = "",
    priceChart = null;
  if (t) {
    ids["tokenized-status"] =
      `${t.stale || now - Date.parse(t.observedAt) > 300000 ? "Refresh delayed · " : ""}BNB Chain · ${stamp(t.observedAt)} · block ${num(t.blockNumber)}`;
    ids["tokenized-supply"] = decimal(t.supply);
    ids["tokenized-multiplier"] = decimal(Number(t.multiplier) / 1e18, 8) + "×";
    if (s?.usde_close?.at(-1) > 0 && s?.shares_outstanding?.at(-1) > 0) {
      ids["tokenized-value"] = usd(t.supply * s.usde_close.at(-1), 0);
      ids["tokenized-share"] =
        decimal((t.supply / s.shares_outstanding.at(-1)) * 100, 3) + "%";
      ids["tokenized-value-note"] =
        `Recorded USDE ${usd(s.usde_close.at(-1))} · ${s.date.at(-1)}`;
      ids["tokenized-share-note"] =
        `Of ${num(s.shares_outstanding.at(-1))} reported Class A shares · ${s.date.at(-1)}`;
    }
  }
  if (f) {
    const w = flowWindow(f, "7d");
    ids["tokenized-flow-status"] =
      `${f.stale || now - Date.parse(f.observedAt) > 36 * 3600000 ? "Refresh delayed · " : ""}Source: Dune / BNB Chain · through ${stamp(f.observedAt)} · reconciled to on-chain supply.`;
    ids["tokenized-minted"] = decimal(w.minted);
    ids["tokenized-burned"] = decimal(w.burned);
    ids["tokenized-net"] = signed(w.net);
    ids["tokenized-period"] = "7 days ending at the snapshot";
    ids["tokenized-flow-note"] =
      "Raw USDEB units · blue: minted / copper: burned · UTC days · boundary days may be partial.";
    ids["tokenized-adjustments"] = f.adjustments.length
      ? `${f.adjustments.length} multiplier scheduling event(s) recorded separately. These do not enter the mint/burn totals.`
      : "No multiplier changes after initialization are recorded in this snapshot.";
    flowRows = [...w.rows]
      .reverse()
      .map(
        (r) =>
          `<tr>${[new Date(r.t).toISOString().slice(0, 10) + (r.partial ? " (partial)" : ""), decimal(r.minted), decimal(r.burned), signed(r.net)].map((x) => `<td>${esc(x)}</td>`).join("")}</tr>`,
      )
      .join("");
  }
  if (l) {
    ids["lighter-status"] =
      `${l.stale || now - Date.parse(l.fetchedAt) > 120000 ? "Refresh delayed · " : ""}Source: Lighter · retrieved ${stamp(l.fetchedAt)}`;
    ids["lighter-mark"] = usd(l.markPrice);
    ids["lighter-oi"] = compact(l.openInterestUsd);
    ids["lighter-volume"] = compact(l.volume24hUsd);
    if (s?.usde_close?.at(-1) > 0)
      ids["lighter-basis"] =
        `${signed((l.markPrice / s.usde_close.at(-1) - 1) * 100)}% vs recorded USDE ${usd(s.usde_close.at(-1))} · ${s.date.at(-1)}`;
    const r = l.latestFunding;
    ids["lighter-funding"] = r
      ? (r.ratePct > 0 ? "+" : "") + r.ratePct.toFixed(4) + "%"
      : "N/A";
    if (r)
      ids["lighter-payer"] =
        `${r.ratePct > 0 ? "Longs pay shorts" : r.ratePct < 0 ? "Shorts pay longs" : "No funding payment"} · ${stamp(new Date(r.t).toISOString())}${l.historyDelayed?.funding || now - r.t > 7200000 ? " · refresh delayed" : ""}`;
    priceChart = (l.prices || []).filter(
      (r) =>
        r.t >= Date.parse(l.fetchedAt) - 86400000 &&
        r.t <= Date.parse(l.fetchedAt),
    );
  }
  return { ids, flowRows, priceChart };
}
