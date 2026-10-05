/* Production feeds and page lifecycle. Source failures retain the last good
   observation; independently loaded pages remain usable during an outage. */
(() => {
  const $ = (s) => document.querySelector(s),
    $$ = (s) => [...document.querySelectorAll(s)];
  const RAW =
    "https://raw.githubusercontent.com/QorbQuant/EthenaDAT/main/docs/";
  const QUOTES =
    "https://ethenadash-quotes.creditforagents-keeper.workers.dev/";
  const marketKeys = [
    "date",
    "ena_price",
    "ena_holdings",
    "shares_outstanding",
    "usde_close",
    "usdew_close",
    "nav_per_share",
    "mnav",
  ];
  const payKeys = [
    "date",
    "spend_usde",
    "spend_count",
    "active_wallets",
    "tvl_usde",
    "deposits_usde",
    "withdrawals_usde",
    "cumulative_wallets",
    "cashback_usd",
    "yield_usde",
  ];
  const emptyD = {
    series: Object.fromEntries(marketKeys.map((k) => [k, []])),
    usde: { price: null },
    warrants: { strike: 11.5, sponsor: [] },
    options: { expiries: [] },
  };
  const emptyP = {
    headline: {},
    series: Object.fromEntries(payKeys.map((k) => [k, []])),
  };
  let source = null,
    D = null,
    P = null,
    valuation = null,
    research = null,
    quotes = null,
    ena = null,
    loading = true,
    refreshing = false,
    quoting = false;
  if (location.hash === "#pay" && location.pathname !== "/ethenapay/") {
    location.replace("/ethenapay/");
    return;
  }
  let page = location.pathname === "/ethenapay/" ? "pay" : "sx",
    feeds = { sx: {}, pay: {} };
  const usd = (v, n = 2) =>
    Number.isFinite(v)
      ? "$" +
        v.toLocaleString("en-US", {
          minimumFractionDigits: n,
          maximumFractionDigits: n,
        })
      : "—";
  const num = (v) =>
    Number.isFinite(v)
      ? v.toLocaleString("en-US", { maximumFractionDigits: 0 })
      : "—";
  const compact = (v) =>
    !Number.isFinite(v)
      ? "—"
      : Math.abs(v) >= 1e9
        ? "$" + (v / 1e9).toFixed(2) + "B"
        : Math.abs(v) >= 1e6
          ? "$" + (v / 1e6).toFixed(2) + "M"
          : Math.abs(v) >= 1000
            ? "$" + (v / 1000).toFixed(1) + "K"
            : usd(v);
  const pct = (v) => (Number.isFinite(v) ? (v * 100).toFixed(1) + "%" : "—");
  const stamp = (v) =>
    Number.isFinite(Date.parse(v))
      ? new Date(v).toLocaleString("en-GB", {
          timeZone: "UTC",
          day: "2-digit",
          month: "short",
          year: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        }) + " UTC"
      : "Unavailable";
  const day = (v) =>
    v
      ? new Date(v + "T00:00:00Z").toLocaleDateString("en-GB", {
          day: "numeric",
          month: "short",
          year: "numeric",
          timeZone: "UTC",
        })
      : "Unavailable";
  async function json(url) {
    const r = await fetch(url, {
      signal: AbortSignal.timeout(12000),
      cache: "no-store",
    });
    if (!r.ok) throw Error("HTTP " + r.status);
    return r.json();
  }
  async function feed(file, type) {
    const urls = ["localhost", "127.0.0.1"].includes(location.hostname)
      ? ["/" + file, RAW + file]
      : [RAW + file, "/" + file];
    for (let i = 0; i < urls.length; i++) {
      try {
        const d = await json(urls[i] + "?t=" + Date.now());
        if (!Ethena.valid(d, type)) throw Error("Invalid data");
        return { data: d, fallback: i > 0 };
      } catch {}
    }
    throw Error("Feed unavailable");
  }
  function status() {
    for (const key of ["sx", "pay"]) {
      const data = key === "sx" ? D : P,
        el = $("#" + key + "-status");
      let message = "";
      if (!data)
        message = loading
          ? "Loading " + (key === "sx" ? "market" : "card") + " data…"
          : "Data unavailable. Please reload to retry.";
      else {
        const age = (Date.now() - Date.parse(data.generated_at)) / 36e5;
        if (feeds[key].failed)
          message = "Refresh unavailable · showing the last successful data. ";
        else if (feeds[key].fallback)
          message =
            "Repository feed unavailable · showing the deployed backup. ";
        if (age > (key === "pay" ? 36 : 48))
          message += "Source data is " + Math.floor(age) + " hours old. ";
        if (message) message += "Updated " + stamp(data.generated_at) + ".";
      }
      el.textContent = message;
      el.classList.toggle("warning", !!data);
      el.hidden = key !== page || !message;
    }
  }
  function route(next) {
    page = next;
    $("#full-sx").hidden = page !== "sx" || !D;
    $("#full-pay").hidden = page !== "pay" || !P;
    status();
    research?.switchPage(page);
    if (page === "sx" && valuation) valuation.redraw();
  }
  function headlines() {
    if (D) {
      const c = Ethena.current(D),
        w = D.liveW?.price ?? D.series.usdew_close.at(-1),
        m = {
          navPrice:
            usd(D.series.nav_per_share.at(-1)) +
            " / " +
            usd(D.series.usde_close.at(-1)),
          mnav: D.series.mnav.at(-1).toFixed(2) + "×",
          holdings: (D.ena_holdings / 1e9).toFixed(3) + "B",
          shares: (D.shares_outstanding / 1e6).toFixed(3) + "M",
          nav: compact(c.nav),
          warrant: usd(w),
          strike: usd(D.warrants.strike),
          breakeven: usd(Number.isFinite(w) ? D.warrants.strike + w : null),
          warrantCount: (D.warrants.count / 1e6).toFixed(2) + "M",
        };
      $$("[data-market]").forEach((e) => (e.textContent = m[e.dataset.market]));
      $("#holdings-date").textContent =
        "Holdings last reported " + day(D.ena_holdings_source?.date);
      $("#holdings-short-date").textContent =
        "Reported " + day(D.ena_holdings_source?.date);
      $("#sx-source-time").textContent =
        "USDE quote · " +
        stamp(D.usde.quote_time) +
        " · " +
        (D.usde.source || D.usde.market_state || "source") +
        " | ENA · " +
        (D.liveEna
          ? "CoinGecko, " + stamp(new Date(D.liveEna.at).toISOString())
          : "daily " + day(D.series.date.at(-1)));
      $("#history-source-time").textContent =
        "Recorded series · " +
        stamp(D.generated_at) +
        (D.liveDate
          ? " · current session includes fresh intraday quotes"
          : " · current quotes shown above");
      $("#options-time").textContent =
        "Nasdaq options · " + stamp(D.options?.as_of);
      const u = Ethena.unlocked(D) / D.ena_holdings;
      $("#unlocked-percent").textContent = pct(u);
      $("#unlocked-description").textContent =
        "Of reported ENA is contractually unlocked as of " +
        day(Ethena.nyDate(new Date())) +
        ".";
      $("#unlocked-bar").style.width = pct(u);
    }
    if (P) {
      const h = P.headline;
      $$("[data-pay]").forEach(
        (e) =>
          (e.textContent = { num, usd, compact, pct }[
            e.dataset.format || "num"
          ](h[e.dataset.pay])),
      );
      const tvl = compact(h.tvl_usde),
        match = tvl.match(/^(.*?)([KMB])$/);
      $("#pay-tvl").replaceChildren(
        document.createTextNode(match ? match[1] : tvl),
      );
      if (match) {
        const span = document.createElement("span");
        span.textContent = match[2];
        $("#pay-tvl").appendChild(span);
      }
      $("#pay-source-time").textContent =
        "Source updated · " + stamp(P.generated_at);
      const fund = h.wallets_created
          ? h.funded_wallets / h.wallets_created
          : null,
        spend = h.wallets_created
          ? h.spending_wallets / h.wallets_created
          : null;
      $("#pay-funded-count").textContent =
        num(h.funded_wallets) + " · " + pct(fund);
      $("#pay-spent-count").textContent =
        num(h.spending_wallets) + " · " + pct(spend);
      $("#pay-funded-bar").style.width = pct(fund ?? 0);
      $("#pay-spent-bar").style.width = pct(spend ?? 0);
      $("#pay-rewards").hidden =
        !Number.isFinite(h.cashback_usd_total) ||
        !Number.isFinite(h.yield_usd_total);
    }
  }
  function render() {
    if (source) D = Ethena.applyQuotes(source, quotes, ena);
    if (D) {
      if (!valuation) valuation = mountValuation(D);
      else valuation.update(D);
    }
    if (!research && (D || P))
      research = mountResearch(D || emptyD, P || emptyP);
    else research?.update(D || emptyD, P || emptyP);
    headlines();
    route(page);
  }
  async function refresh() {
    if (refreshing) return;
    refreshing = true;
    const results = await Promise.allSettled([
      feed("data.json", "sx"),
      feed("ethenapay.json", "pay"),
    ]);
    for (let i = 0; i < 2; i++) {
      const result = results[i],
        key = i ? "pay" : "sx";
      if (result.status === "fulfilled") {
        const previous = i ? P : source;
        if (
          previous &&
          Date.parse(result.value.data.generated_at) <
            Date.parse(previous.generated_at)
        ) {
          feeds[key].failed = true;
          continue;
        }
        feeds[key] = { fallback: result.value.fallback };
        if (i) P = Ethena.normalizePay(result.value.data);
        else source = result.value.data;
      } else feeds[key].failed = true;
    }
    loading = false;
    refreshing = false;
    render();
  }
  async function refreshQuotes() {
    if (quoting || !source) return;
    quoting = true;
    const results = await Promise.allSettled([
      json(QUOTES),
      json(
        "https://api.coingecko.com/api/v3/simple/price?ids=ethena&vs_currencies=usd",
      ),
    ]);
    if (results[0].status === "fulfilled") quotes = results[0].value;
    if (
      results[1].status === "fulfilled" &&
      Number.isFinite(results[1].value.ethena?.usd)
    )
      ena = { price: results[1].value.ethena.usd, at: Date.now() };
    quoting = false;
    render();
  }
  try {
    const initial = JSON.parse(
      $("#dashboard-bootstrap")?.textContent || "null",
    );
    if (initial) {
      source = Ethena.valid(initial.sx, "sx") ? initial.sx : null;
      P = Ethena.valid(initial.pay, "pay")
        ? Ethena.normalizePay(initial.pay)
        : null;
      feeds = initial.feeds;
      loading = false;
      render();
    }
  } catch (error) {
    console.error("Snapshot initialization failed", error);
  }
  route(page);
  refresh().then(refreshQuotes);
  setInterval(() => {
    if (!document.hidden) refreshQuotes();
  }, 60000);
  setInterval(() => {
    if (!document.hidden) refresh();
  }, 300000);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
      refresh();
      refreshQuotes();
    }
  });
})();
