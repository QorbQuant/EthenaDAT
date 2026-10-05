import Ethena from "../docs/assets/data.js";
import { esc } from "./seo.mjs";
export const num = (v) =>
  Number.isFinite(v)
    ? v.toLocaleString("en-US", { maximumFractionDigits: 0 })
    : "—";
export const usd = (v, n = 2) =>
  Number.isFinite(v)
    ? "$" +
      v.toLocaleString("en-US", {
        minimumFractionDigits: n,
        maximumFractionDigits: n,
      })
    : "—";
export const pct = (v) =>
  Number.isFinite(v) ? (v * 100).toFixed(1) + "%" : "—";
export const compact = (v) =>
  !Number.isFinite(v)
    ? "—"
    : Math.abs(v) >= 1e9
      ? "$" + (v / 1e9).toFixed(2) + "B"
      : Math.abs(v) >= 1e6
        ? "$" + (v / 1e6).toFixed(2) + "M"
        : Math.abs(v) >= 1000
          ? "$" + (v / 1000).toFixed(1) + "K"
          : usd(v);
export const stamp = (v) =>
  Number.isFinite(Date.parse(v))
    ? new Date(v)
        .toISOString()
        .replace("T", " ")
        .replace(/:\d\d\.\d{3}Z$/, " UTC")
    : "Unavailable";
export function values(D, P) {
  const ids = {},
    market = {};
  if (D) {
    const c = Ethena.current(D),
      s = D.series,
      w = s.usdew_close.at(-1),
      i = s.date.length - 1;
    Object.assign(ids, {
      "sx-ratio": c.mnav.toFixed(2) + "×",
      "sx-cents": Math.round(c.mnav * 100) + "¢",
      "sx-price": usd(c.price),
      "sx-price-change": D.usde.prev_close
        ? ((c.price / D.usde.prev_close - 1) * 100).toFixed(2) +
          "% vs prior close"
        : "Prior close unavailable",
      "sx-nav-value": compact(c.nav),
      "sx-cap-value": compact(c.cap),
      "sx-shares": (D.shares_outstanding / 1e6).toFixed(3) + "M",
      "sx-nav-share": usd(c.ena * c.per),
      "sx-warrant": usd(w),
      "sx-source-time":
        "USDE quote · " +
        stamp(D.usde.quote_time) +
        " | ENA daily · " +
        s.date[i],
      "history-source-time": "Recorded series · " + stamp(D.generated_at),
      "holdings-date":
        "Holdings last reported " +
        (D.ena_holdings_source?.date ?? "Unavailable"),
      "holdings-short-date":
        "Reported " + (D.ena_holdings_source?.date ?? "Unavailable"),
      "sx-history-date": s.date[i],
      "sx-history-mnav": s.mnav[i].toFixed(2) + "×",
      "sx-h-nav": compact(s.ena_price[i] * s.ena_holdings[i]),
      "sx-h-cap": compact(s.usde_close[i] * s.shares_outstanding[i]),
      "sx-h-price": usd(s.usde_close[i]),
      "sx-f-ena": usd(c.ena, 4),
      "sx-f-holdings": c.per.toFixed(2),
      "sx-f-mnav": c.mnav.toFixed(2) + "×",
      "sx-f-price": usd(c.price),
      "sx-f-price-label": "Observed share price",
      "sx-formula-context": "Current observation",
      "sx-plot-title": "Market cap & token NAV",
      "sx-chart-hint": "Blue · token NAV / Copper · market cap",
      "sx-chart-foot-right": s.date[0] + " — " + s.date[i],
      "unlocked-percent": pct(Ethena.unlocked(D) / D.ena_holdings),
      "unlocked-description":
        "Of reported ENA is contractually unlocked as of " +
        Ethena.nyDate(new Date()) +
        ".",
      "options-time": "Nasdaq options · " + stamp(D.options?.as_of),
    });
    Object.assign(market, {
      navPrice: usd(s.nav_per_share[i]) + " / " + usd(s.usde_close[i]),
      mnav: s.mnav[i].toFixed(2) + "×",
      holdings: (D.ena_holdings / 1e9).toFixed(3) + "B",
      shares: (D.shares_outstanding / 1e6).toFixed(3) + "M",
      nav: compact(c.nav),
      warrant: usd(w),
      strike: usd(D.warrants.strike),
      breakeven: usd(Number.isFinite(w) ? D.warrants.strike + w : null),
      warrantCount: (D.warrants.count / 1e6).toFixed(2) + "M",
    });
  }
  if (P) {
    const h = P.headline,
      s = P.series,
      i = s.date.length - 1;
    Object.assign(ids, {
      "pay-tvl": compact(h.tvl_usde),
      "pay-source-time": "Source updated · " + stamp(P.generated_at),
      "pay-funded-count":
        num(h.funded_wallets) +
        " · " +
        pct(h.wallets_created ? h.funded_wallets / h.wallets_created : null),
      "pay-spent-count":
        num(h.spending_wallets) +
        " · " +
        pct(h.wallets_created ? h.spending_wallets / h.wallets_created : null),
      "pay-hero-spend": compact(h.spend_usde_30d),
      "pay-refunds": compact(h.lifetime_reversals_usde),
      "pay-last-active": num(s.active_wallets[i]) + " latest day",
      "pay-concentration": pct(h.top10_balance_share),
      "pay-average-balance": usd(
        h.funded_wallets ? h.tvl_usde / h.funded_wallets : null,
        0,
      ),
      "pay-reward-total":
        Number.isFinite(h.cashback_usd_total) &&
        Number.isFinite(h.yield_usd_total)
          ? compact(h.cashback_usd_total + h.yield_usd_total)
          : "—",
      "pay-cashback-rate": pct(h.cashback_rate_30d),
      "pay-yield-apy": pct(h.yield_apy_30d),
      "pay-observation-date": s.date[i],
      "pay-observation-value": usd(s.spend_usde[i]),
      "pay-observation-count": num(s.spend_count[i]),
      "pay-observation-active": num(s.active_wallets[i]),
    });
  }
  return { ids, market };
}
export function chart(dates, values, label, money = false, secondary = []) {
  const finite = [...values, ...secondary].filter(Number.isFinite);
  if (!finite.length) return "";
  const lo = Math.min(0, ...finite),
    hi = Math.max(...finite, lo + 1),
    x = (i) => 60 + (i / Math.max(1, dates.length - 1)) * 700,
    y = (v) => 270 - ((v - lo) / (hi - lo)) * 230;
  const line = (points) => {
    let pen = false;
    return points
      .map((v, i) => {
        if (!Number.isFinite(v)) {
          pen = false;
          return "";
        }
        const op = pen ? "L" : "M";
        pen = true;
        return op + x(i).toFixed(1) + "," + y(v).toFixed(1);
      })
      .join(" ");
  };
  return `<title>${esc(label)}</title>${[0, 0.5, 1]
    .map((t) => {
      const v = lo + (hi - lo) * t;
      return `<line x1="60" x2="760" y1="${y(v)}" y2="${y(v)}" stroke="#29313a"/><text x="50" y="${y(v) + 4}" text-anchor="end" fill="#99a3b0" font-size="11">${esc(money ? compact(v) : v.toFixed(2) + "×")}</text>`;
    })
    .join(
      "",
    )}<path d="${line(values)}" fill="none" stroke="#8aa9cf" stroke-width="2.5"/>${secondary.length ? `<path d="${line(secondary)}" fill="none" stroke="#cf9b79" stroke-width="2.5"/>` : ""}<text x="60" y="302" fill="#99a3b0" font-size="11">${esc(dates[0])}</text><text x="760" y="302" text-anchor="end" fill="#99a3b0" font-size="11">${esc(dates.at(-1))}</text>`;
}
export function rows(d, type) {
  if (!d) return "";
  const s = d.series;
  return s.date
    .map((date, i) => ({ date, i }))
    .slice(-10)
    .reverse()
    .map(
      ({ date, i }) =>
        "<tr>" +
        (type === "sx"
          ? [
              date,
              usd(s.usde_close[i]),
              usd(s.ena_price[i], 4),
              usd(s.nav_per_share[i]),
              Number.isFinite(s.mnav[i]) ? s.mnav[i].toFixed(2) + "×" : "—",
            ]
          : [
              date,
              usd(s.spend_usde[i]),
              num(s.spend_count[i]),
              num(s.active_wallets[i]),
              usd(s.tvl_usde[i]),
            ]
        )
          .map((v) => "<td>" + esc(v) + "</td>")
          .join("") +
        "</tr>",
    )
    .join("");
}
