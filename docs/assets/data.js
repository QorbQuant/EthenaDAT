/* Shared data calculations; no network or DOM dependencies. */
(function (scope) {
  const positive = (v) => Number.isFinite(v) && v > 0;
  const nyDate = (d) =>
    new Intl.DateTimeFormat("en-CA", { timeZone: "America/New_York" }).format(
      d,
    );
  function valid(d, type) {
    if (
      !d ||
      !Number.isFinite(Date.parse(d.generated_at)) ||
      !d.series?.date?.length
    )
      return false;
    const s = d.series,
      n = s.date.length;
    if (
      s.date.some(
        (v, i) =>
          !/^\d{4}-\d{2}-\d{2}$/.test(v) || (i > 0 && v <= s.date[i - 1]),
      )
    )
      return false;
    const fields =
      type === "pay"
        ? [
            "spend_usde",
            "spend_count",
            "active_wallets",
            "tvl_usde",
            "deposits_usde",
            "withdrawals_usde",
            "cumulative_wallets",
          ]
        : [
            "ena_price",
            "ena_holdings",
            "shares_outstanding",
            "usde_close",
            "usdew_close",
            "nav_per_share",
            "mnav",
          ];
    if (
      !fields.every(
        (k) =>
          Array.isArray(s[k]) &&
          s[k].length === n &&
          s[k].every((v) => v === null || Number.isFinite(v)),
      )
    )
      return false;
    if (type === "pay")
      return d.headline && Number.isFinite(d.headline.tvl_usde);
    return (
      positive(d.shares_outstanding) &&
      positive(d.ena_holdings) &&
      positive(d.usde?.price) &&
      ["ena_price", "ena_holdings", "shares_outstanding", "usde_close"].every(
        (k) => s[k].every(positive),
      )
    );
  }
  function normalizePay(p) {
    for (const k of ["cashback_usd", "yield_usde"])
      if (!p.series[k]) p.series[k] = p.series.date.map(() => null);
    return p;
  }
  function current(d) {
    const s = d.series,
      ena = d.liveEna?.price ?? s.ena_price.at(-1),
      price = d.usde.price,
      per = d.ena_holdings / d.shares_outstanding;
    return {
      t: Date.parse(s.date.at(-1) + "T00:00:00Z"),
      ena,
      price,
      per,
      mnav: price / (ena * per),
      nav: ena * d.ena_holdings,
      cap: price * d.shares_outstanding,
      date: s.date.at(-1),
    };
  }
  function valuationSummary(d) {
    const fallback = "Track StablecoinX’s ENA holdings, token NAV per share and mNAV.";
    const s = d?.series, i = (s?.date?.length ?? 0) - 1;
    const date = s?.date?.[i], mnav = s?.mnav?.[i];
    const holdings = s?.ena_holdings?.[i], nav = s?.nav_per_share?.[i];
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date ?? "") ||
        ![mnav, holdings, nav].every(positive)) return fallback;
    const at = new Date(date + "T00:00:00Z");
    if (!Number.isFinite(+at) || at.toISOString().slice(0, 10) !== date) return fallback;
    const label = new Intl.DateTimeFormat("en-GB", {
      day: "numeric", month: "short", year: "numeric", timeZone: "UTC",
    }).format(at);
    const ena = new Intl.NumberFormat("en-US", {
      notation: "compact", maximumFractionDigits: 3,
    }).format(holdings);
    return `Latest observation (${label}): USDE mNAV is ${mnav.toFixed(2)}×, based on ${ena} reported ENA and $${nav.toFixed(2)} token NAV per share. Token NAV excludes other assets and liabilities.`;
  }
  function unlocked(d, at = new Date()) {
    const add = (p, m) => {
      const end = new Date(
        Date.UTC(p.getUTCFullYear(), p.getUTCMonth() + m + 1, 0),
      );
      return new Date(
        Date.UTC(
          end.getUTCFullYear(),
          end.getUTCMonth(),
          Math.min(p.getUTCDate(), end.getUTCDate()),
        ),
      );
    };
    let result = d.ena_holdings;
    for (const t of d.tranches || []) {
      if (
        t.locked === false ||
        t.locked === "false" ||
        (t.waived_on && at >= new Date(t.waived_on + "T00:00:00Z"))
      )
        continue;
      const p = new Date(t.purchase_date + "T00:00:00Z"),
        cliff = add(p, 12);
      let fraction = 0;
      if (at >= cliff) {
        let m =
          (at.getUTCFullYear() - cliff.getUTCFullYear()) * 12 +
          at.getUTCMonth() -
          cliff.getUTCMonth();
        if (at < add(p, 12 + m)) m--;
        fraction = Math.min(1, 0.25 + (0.75 * Math.min(36, m)) / 36);
      }
      result -= t.tokens * (1 - fraction);
    }
    return Math.max(0, Math.min(d.ena_holdings, result));
  }
  function completedCloses(d, now = new Date()) {
    // A same-day quote is not evidence of an official close. Only source
    // observations known to be post-session count; live overlay never counts.
    const today = nyDate(now),
      q = d.sourceUsde || d.usde,
      qt = Date.parse(q.quote_time);
    const quoteDay = Number.isFinite(qt) ? nyDate(new Date(qt)) : null;
    const partial =
      d.liveDate ||
      (["REGULAR", "PRE", "PREPRE", "LIVE"].includes(q.market_state)
        ? quoteDay
        : null);
    return d.series.usde_close.filter(
      (v, i) =>
        Number.isFinite(v) &&
        d.series.date[i] !== partial &&
        (d.series.date[i] < today ||
          (["POST", "POSTPOST", "CLOSED"].includes(q.market_state) &&
            d.series.date[i] === quoteDay)),
    );
  }
  function applyQuotes(source, quotes, ena, now = new Date()) {
    const d = structuredClone(source),
      q = quotes?.USDE;
    d.sourceUsde = source.usde;
    // Never overwrite a newer pipeline observation with an older proxy quote.
    if (
      positive(q?.price) &&
      Number.isFinite(Date.parse(q.t)) &&
      Date.parse(q.t) >= Date.parse(d.usde.quote_time || d.generated_at)
    )
      d.usde = {
        price: q.price,
        prev_close: q.prev_close,
        market_state: q.state || "QUOTED",
        quote_time: q.t,
        source: q.src,
      };
    if (
      positive(quotes?.USDEW?.price) &&
      Date.parse(quotes.USDEW.t) >= Date.parse(source.generated_at)
    )
      d.liveW = quotes.USDEW;
    if (positive(ena?.price) && now - ena.at < 180000) d.liveEna = ena;
    const qtime = Date.parse(d.usde.quote_time),
      session = Number.isFinite(qtime) ? nyDate(new Date(qtime)) : null,
      s = d.series,
      last = s.date.at(-1);
    // Pair intraday prices only when both are fresh; do not relabel Friday's
    // close with weekend ENA, or overwrite history with an after-hours blend.
    const parts = new Intl.DateTimeFormat("en-US", {
        timeZone: "America/New_York",
        hour: "2-digit",
        hourCycle: "h23",
        minute: "2-digit",
      }).formatToParts(now),
      hour = Number(parts.find((p) => p.type === "hour").value),
      minute = Number(parts.find((p) => p.type === "minute").value);
    const duringSession =
      hour * 60 + minute >= 570 &&
      hour < 16 &&
      ![0, 6].includes(new Date(session + "T12:00:00Z").getUTCDay());
    if (
      !d.liveEna ||
      !q ||
      d.usde.quote_time !== q.t ||
      session !== nyDate(now) ||
      session < last ||
      now - qtime > 20 * 60000 ||
      !duringSession
    )
      return d;
    const i = session > last ? s.date.length : s.date.length - 1,
      c = current(d),
      u = unlocked(d, now);
    const row = {
      date: session,
      usde_close: c.price,
      usdew_close: d.liveW?.price ?? s.usdew_close.at(-1),
      shares_outstanding: d.shares_outstanding,
      ena_price: c.ena,
      ena_holdings: d.ena_holdings,
      market_cap: c.cap,
      ena_nav: c.nav,
      nav_per_share: c.ena * c.per,
      mnav: c.mnav,
      ena_unlocked: u,
      nav_unlocked: c.ena * u,
      nav_unlocked_per_share: (c.ena * u) / d.shares_outstanding,
      mnav_unlocked: c.cap / (c.ena * u),
    };
    for (const k of Object.keys(s)) s[k][i] = k in row ? row[k] : s[k].at(-1);
    d.liveDate = session;
    return d;
  }
  const api = {
    valid,
    normalizePay,
    current,
    valuationSummary,
    unlocked,
    completedCloses,
    applyQuotes,
    nyDate,
  };
  if (typeof module !== "undefined") module.exports = api;
  else scope.Ethena = api;
})(globalThis);
