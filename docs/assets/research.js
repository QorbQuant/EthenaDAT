window.mountResearch = function (initialD, initialP) {
  const root = document.getElementById("sx-studio"),
    $ = (s) => root.querySelector(s),
    $$ = (s) => [...root.querySelectorAll(s)];
  let D = initialD,
    P = initialP,
    S = D.series,
    H = P.headline,
    T = P.series;
  const blue = "#8aa9cf",
    copper = "#cf9b79",
    ink = "#eeeae3",
    muted = "#99a3b0",
    rule = "#29313a",
    ns = "http://www.w3.org/2000/svg";
  const usd = (v, n = 2) =>
      v == null || !Number.isFinite(v)
        ? "N/A"
        : "$" +
          v.toLocaleString("en-US", {
            minimumFractionDigits: n,
            maximumFractionDigits: n,
          }),
    num = (v) =>
      v == null ? "N/A" : v.toLocaleString("en-US", { maximumFractionDigits: 0 }),
    compact = (v) => {
      if (v == null) return "N/A";
      let abs = Math.abs(v),
        sign = v < 0 ? "−" : "";
      return (
        sign +
        "$" +
        (abs >= 1e9
          ? (abs / 1e9).toFixed(2) + "B"
          : abs >= 1e6
            ? (abs / 1e6).toFixed(2) + "M"
            : abs >= 1e3
              ? (abs / 1e3).toFixed(1) + "K"
              : abs.toFixed(2))
      );
    },
    pct = (v) => (Number.isFinite(v) ? (v * 100).toFixed(1) + "%" : "N/A"),
    date = (d) =>
      new Date(d + "T00:00:00Z").toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        timeZone: "UTC",
      }),
    short = (d) =>
      new Date(d + "T00:00:00Z").toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        timeZone: "UTC",
      }),
    esc = (s) =>
      String(s ?? "N/A").replace(
        /[&<>"']/g,
        (c) =>
          ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;",
          })[c],
      );
  const sum = (a) => a.reduce((x, y) => x + (y || 0), 0),
    cum = (a) => {
      let n = 0;
      return a.map((v) => (v == null ? null : (n += v)));
    };
  const shared = ChartShare.initial;
  let saved = {
    fullPage: location.pathname === "/ethenapay/" ? "pay" : "sx",
    fullPerf: shared.range,
    fullPayRange: shared.range,
    fullPayView: shared.view,
    fullPayAgg: shared.agg,
    fullRewardView: shared.rewards,
  };
  let fixedWindow = !!(shared.from || shared.to);
  let F = {
    fullPage: ["sx", "pay"].includes(saved.fullPage) ? saved.fullPage : "sx",
    fullPerf: ["30", "90", "all"].includes(saved.fullPerf)
      ? saved.fullPerf
      : "all",
    fullPayRange: ["30", "90", "all"].includes(saved.fullPayRange)
      ? saved.fullPayRange
      : "all",
    fullPayView: ["spend", "count", "active"].includes(saved.fullPayView)
      ? saved.fullPayView
      : "spend",
    fullPayAgg: ["daily", "total"].includes(saved.fullPayAgg)
      ? saved.fullPayAgg
      : "daily",
    fullRewardView: ["daily", "total"].includes(saved.fullRewardView)
      ? saved.fullRewardView
      : "total",
  };
  root.fullState = F;
  let payIndex = T.date.length - 1,
    perfIndex = S.date.length - 1,
    showAllFilings = false,
    payoff = shared.payoff ?? 20;
  if (shared.date && T.date.includes(shared.date))
    payIndex = T.date.indexOf(shared.date);
  if (shared.date && S.date.includes(shared.date))
    perfIndex = S.date.indexOf(shared.date);
  const registry = new Map();
  function persist() {}
  const ts = (d) => Date.parse(d + "T00:00:00Z");
  let rS = S.date.map((d, i) => ({ i, d, t: ts(d) })),
    rP = T.date.map((d, i) => ({ i, d, t: ts(d) }));
  function sliced(rows, range) {
    if (fixedWindow)
      return ChartShare.windowRows(rows, shared.from, shared.to, "d");
    if (range === "all") return rows;
    return rows.filter((r) => r.t >= rows.at(-1).t - Number(range) * 864e5);
  }
  function add(svg, tag, attrs = {}, text) {
    const e = document.createElementNS(ns, tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    if (text !== undefined) e.textContent = text;
    svg.appendChild(e);
    return e;
  }
  function chart(id, cfg) {
    registry.set(id, cfg);
    ChartShare.register(id, () => {
      const c = registry.get(id),
        pay = c.group === "pay",
        scenario = c.group === "payoff";
      const view = pay ? F.fullPayView : undefined;
      const date = pay
        ? T.date[payIndex]
        : c.group === "perf"
          ? S.date[perfIndex]
          : undefined;
      const units = {
        "full-per-share": "USD per share",
        "full-mnav": "multiple of token NAV",
        "full-indexed": "index, first recorded session = 100",
        "full-ena-per-share": "ENA per Class A share",
        "full-warrants-chart": "USD",
        "full-payoff-chart": "gross value per USD invested at expiry",
        "pay-main-chart":
          view === "spend"
            ? "USDe"
            : view === "count"
              ? "spend events"
              : "distinct wallets per day",
        "pay-balance-chart": "USDe",
        "pay-flows-chart": "USDe; withdrawals plotted negative",
        "pay-created-chart": "wallets",
        "pay-active-chart": "distinct wallets per day",
        "pay-cashback-chart": "USD at payout-day AVAX price",
        "pay-yield-chart": "USDe",
      };
      const aggregation = pay
        ? id === "pay-cashback-chart" || id === "pay-yield-chart"
          ? F.fullRewardView
          : id === "pay-main-chart" && view !== "active"
            ? F.fullPayAgg
            : null
        : null;
      const note = scenario
        ? `Hypothetical expiry payoff; ignores early redemption, fees and taxes. USDE input $${Ethena.current(D).price}; USDEW input $${D.liveW?.price ?? S.usdew_close.at(-1)}; strike $${D.warrants.strike}.`
        : pay
          ? "Successful spend events are not transaction hashes. Wallets are not people. Latest day may be partial."
          : "Reported ENA token NAV excludes other assets and liabilities; Class A share-count basis. Quotes may be delayed.";
      return {
        title: c.title,
        visual: {
          title: {
            "full-indexed": "StablecoinX vs ENA",
            "full-per-share": "StablecoinX: price vs token NAV",
            "full-mnav": "StablecoinX valuation multiple",
            "full-ena-per-share": "ENA backing each share",
            "full-warrants-chart": "StablecoinX stock & warrants",
            "full-payoff-chart": "Stock vs warrants at expiry",
            "pay-main-chart":
              "EthenaPay: " +
              (view === "active"
                ? "daily spending wallets"
                : (aggregation === "total" ? "cumulative " : "daily ") +
                  (view === "spend" ? "card spend" : "spend events")),
            "pay-balance-chart": "USDe in EthenaPay wallets",
            "pay-flows-chart": "EthenaPay deposits & withdrawals",
            "pay-created-chart": "EthenaPay wallets created",
            "pay-active-chart": "EthenaPay spending wallets",
            "pay-cashback-chart":
              "EthenaPay: " +
              (aggregation === "total" ? "cumulative" : "daily") +
              " cashback",
            "pay-yield-chart":
              "EthenaPay: " +
              (aggregation === "total" ? "cumulative" : "daily") +
              " balance yield",
          }[id],
          category: pay
            ? "ETHENAPAY"
            : scenario
              ? "SCENARIO / NOT A FORECAST"
              : "STABLECOINX",
          unit: units[id],
          description:
            id === "full-indexed"
              ? "Price performance since listing"
              : id === "pay-created-chart"
                ? "Cumulative wallets deployed"
                : (aggregation
                    ? (aggregation === "total"
                        ? "Cumulative since inception"
                        : "Daily observations") + " · "
                    : "") + units[id],
          source: pay
            ? "On-chain data · Avalanche"
            : id === "full-indexed"
              ? "Yahoo Finance / CoinGecko"
              : "Public filings / market data",
          caveat: scenario
            ? `Inputs: USDE $${Ethena.current(D).price.toFixed(2)} / USDEW $${(D.liveW?.price ?? S.usdew_close.at(-1)).toFixed(2)} / strike $${D.warrants.strike.toFixed(2)}. Excludes early redemption, fees & taxes.`
            : pay
              ? aggregation === "total"
                ? "Cumulative basis includes earlier dates. Latest day may be partial."
                : "Latest day may be partial. Wallets are not people."
              : id === "full-indexed"
                ? "26 Jun 2026 = 100. Price changes exclude distributions."
                : "Token NAV excludes other assets & liabilities. Quotes may be delayed.",
          rows: c.rows,
          series: c.series,
          format: c.valueFmt || c.fmt,
          axisFormat: c.fmt,
          xFormat: c.xfmt,
          contextFormat: scenario ? (v) => usd(v, 2) : null,
          metricValues: scenario
            ? [
                payoff / Ethena.current(D).price,
                Math.max(0, payoff - D.warrants.strike) /
                  (D.liveW?.price ?? S.usdew_close.at(-1)),
              ]
            : null,
          metricFormat:
            id === "full-indexed"
              ? (v) => (v >= 100 ? "+" : "") + (v - 100).toFixed(1) + "%"
              : scenario
                ? (v) => v.toFixed(2) + "×"
                : null,
          metricSuffix: id === "full-indexed" ? "since listing" : null,
          zero: c.zero,
          selected: scenario
            ? payoff
            : date
              ? Date.parse(date + "T00:00:00Z")
              : c.rows.at(-1).t,
          contextLabel: scenario ? "STOCK AT EXPIRY" : "OBSERVATION",
        },
        kind: scenario ? "SCENARIO" : "RECORDED DATA",
        updated: (pay ? P : D).generated_at,
        period: scenario
          ? "Terminal stock-price scenarios (USD)"
          : c.rows[0].d + " to " + c.rows.at(-1).d,
        subtitle:
          c.series
            .map(
              (v, i) =>
                (v.color === copper ? "Copper" : "Blue") + ": " + v.name,
            )
            .join(" / ") +
          " · Units: " +
          units[id] +
          (aggregation
            ? " · " +
              (aggregation === "total" ? "Cumulative since inception" : "Daily")
            : "") +
          (date ? " · Selected: " + date : ""),
        note:
          note +
          (aggregation
            ? " Values are " +
              (aggregation === "total"
                ? "cumulative since inception, including observations before the selected window."
                : "daily observations.")
            : "") +
          (scenario ? " Selected terminal stock price: $" + payoff + "." : ""),
        columns: [
          scenario ? "terminal_stock_price_usd" : "date",
          ...c.series.map(
            (v) =>
              (aggregation === "total" ? "Cumulative " : "") +
              v.name +
              " [" +
              units[id] +
              "]",
          ),
        ],
        rows: c.rows.map((r, i) => [
          scenario ? r.t : r.d,
          ...c.series.map((v) => v.data[i]),
        ]),
        state: {
          range: pay ? F.fullPayRange : F.fullPerf,
          from: scenario ? null : c.rows[0].d,
          to: scenario ? null : c.rows.at(-1).d,
          date,
          view: pay ? F.fullPayView : null,
          agg: pay ? F.fullPayAgg : null,
          rewards: pay ? F.fullRewardView : null,
          payoff: scenario ? payoff : null,
        },
      };
    });
    draw(id);
  }
  const nearViewport = (svg) => {
    const r = svg.getBoundingClientRect();
    return (
      !svg.closest("[hidden]") &&
      r.width > 20 &&
      r.bottom >= -200 &&
      r.top < innerHeight + 200
    );
  };
  function draw(id) {
    const svg = $("#" + id),
      c = registry.get(id);
    if (!svg || !c || !nearViewport(svg)) return;
    const w = svg.getBoundingClientRect().width,
      h = svg.getBoundingClientRect().height;
    if (w < 20) return;
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.replaceChildren();
    if (!globalThis.d3) {
      add(
        svg,
        "text",
        { x: 15, y: 30 },
        "Chart library unavailable. Data tables remain below.",
      );
      return;
    }
    const m = { l: w < 400 ? 54 : 62, r: 12, t: 18, b: 38 },
      l = m.l,
      r = w - m.r,
      t = m.t,
      b = h - m.b,
      values = c.series.flatMap((s) =>
        s.data.filter((v) => Number.isFinite(v)),
      ),
      ex = d3.extent(values),
      pad = (ex[1] - ex[0]) * 0.07 || Math.abs(ex[1]) * 0.03 || 1;
    if (!values.length || !c.rows.length) {
      add(svg, "text", { x: 15, y: 30 }, "No observations available");
      return;
    }
    const y = d3
      .scaleLinear()
      .domain(
        c.zero === false
          ? [ex[0] - pad, ex[1] + pad]
          : [Math.min(0, ex[0]), Math.max(0, ex[1]) + pad],
      )
      .nice(4)
      .range([b, t]);
    const data = c.rows,
      x = d3
        .scaleLinear()
        .domain(d3.extent(data, (q) => q.t))
        .range([l, r]);
    add(svg, "title", {}, c.title);
    y.ticks(4).forEach((v) => {
      add(svg, "line", {
        x1: l,
        y1: y(v),
        x2: r,
        y2: y(v),
        stroke: rule,
        "stroke-width": 1,
        opacity: v === 0 ? 0.8 : 0.5,
      });
      add(
        svg,
        "text",
        { x: l - 8, y: y(v) + 4, "text-anchor": "end" },
        c.fmt(v),
      );
    });
    const count = w < 360 ? 3 : 4;
    for (let k = 0; k < count; k++) {
      const q = data[Math.round(((data.length - 1) * k) / (count - 1))];
      add(
        svg,
        "text",
        {
          x: x(q.t),
          y: h - 13,
          "text-anchor": k === 0 ? "start" : k === count - 1 ? "end" : "middle",
        },
        c.xfmt ? c.xfmt(q.t) : short(q.d),
      );
    }
    const clipId = "clip-" + id;
    const defs = add(svg, "defs"),
      clip = add(defs, "clipPath", { id: clipId });
    add(clip, "rect", { x: l, y: t, width: r - l, height: b - t });
    const g = add(svg, "g", { "clip-path": `url(#${clipId})` });
    c.series.forEach((s, si) => {
      const color = s.color || [blue, copper][si % 2],
        points = data.map((q, j) => ({ x: x(q.t), y: s.data[j] }));
      if (s.kind === "bar") {
        const bw = Math.max(1, Math.min(12, ((r - l) / data.length) * 0.68));
        points.forEach((p) => {
          if (!Number.isFinite(p.y)) return;
          add(g, "rect", {
            x: p.x - bw / 2,
            y: Math.min(y(p.y), y(0)),
            width: bw,
            height: Math.max(0.7, Math.abs(y(p.y) - y(0))),
            fill: color,
            opacity: 0.86,
          });
        });
      } else {
        if (s.fill) {
          const area = d3
            .area()
            .defined((p) => Number.isFinite(p.y))
            .x((p) => p.x)
            .y0(y(0))
            .y1((p) => y(p.y));
          add(g, "path", {
            d: area(points),
            fill: color,
            "fill-opacity": 0.06,
          });
        }
        const line = d3
          .line()
          .defined((p) => Number.isFinite(p.y))
          .x((p) => p.x)
          .y((p) => y(p.y));
        add(g, "path", {
          d: line(points),
          stroke: color,
          "stroke-width": 1.7,
          fill: "none",
        });
      }
    });
    let selected =
      c.group === "pay" ? payIndex : c.group === "perf" ? perfIndex : null;
    const obs = selected == null ? null : data.find((q) => q.i === selected);
    if (obs) {
      add(svg, "line", {
        x1: x(obs.t),
        y1: t,
        x2: x(obs.t),
        y2: b,
        stroke: "#637486",
        "stroke-width": 1,
        "stroke-dasharray": "3 4",
      });
      const j = data.indexOf(obs);
      c.series.forEach((s, k) => {
        if (Number.isFinite(s.data[j]))
          add(svg, "circle", {
            cx: x(obs.t),
            cy: y(s.data[j]),
            r: 3,
            fill: s.color || [blue, copper][k % 2],
            stroke: "#0d1116",
            "stroke-width": 1.5,
          });
      });
    }
    const readout = svg.parentElement.querySelector(".full-readout");
    if (readout) {
      const q = obs || data.at(-1),
        i = data.indexOf(q);
      readout.textContent =
        (c.xfmt ? c.xfmt(q.t) : date(q.d)) +
        "  ·  " +
        c.series
          .map((s) => s.name + " " + (c.valueFmt || c.fmt)(s.data[i]))
          .join("  /  ");
    }
    const hit = add(svg, "rect", {
      x: l,
      y: t,
      width: r - l,
      height: b - t,
      fill: "transparent",
      "data-chart-hit": "",
      "data-chart-hover-overlay": "cross-series",
    });
    hit.onpointermove = hit.onpointerdown = (e) => {
      const rect = svg.getBoundingClientRect(),
        px = ((e.clientX - rect.left) * w) / rect.width,
        time = x.invert(Math.max(l, Math.min(r, px))),
        q = data[d3.bisector((q) => q.t).center(data, time)];
      if (c.group === "pay") {
        payIndex = q.i;
        updatePayObservation();
      } else if (c.group === "perf") perfIndex = q.i;
      else return;
      for (const [key, config] of registry)
        if (config.group === c.group) draw(key);
    };
  }
  function sourceSeries(arr, rows) {
    return rows.map((q) => arr[q.i]);
  }
  function lineChart(
    id,
    title,
    rows,
    series,
    fmt,
    group,
    zero = true,
    xfmt = null,
    valueFmt = null,
  ) {
    chart(id, { title, rows, series, fmt, group, zero, xfmt, valueFmt });
  }
  function performance() {
    if (!S.date.length) return;
    const rr = sliced(rS, F.fullPerf);
    if (!rr.some((r) => r.i === perfIndex)) perfIndex = rr.at(-1).i;
    $$("[data-perf]").forEach((b) =>
      b.setAttribute("aria-pressed", b.dataset.perf === F.fullPerf),
    );
    const series = (name, data, color = blue, extra = {}) => ({
      name,
      data: sourceSeries(data, rr),
      color,
      ...extra,
    });
    lineChart(
      "full-per-share",
      "NAV per share and share price",
      rr,
      [
        series("NAV/share", S.nav_per_share),
        series("USDE", S.usde_close, copper),
      ],
      (v) => usd(v, 0),
      "perf",
      true,
      null,
      (v) => usd(v, 2),
    );
    lineChart(
      "full-mnav",
      "Historical mNAV",
      rr,
      [series("mNAV", S.mnav, copper)],
      (v) => v.toFixed(2) + "×",
      "perf",
    );
    lineChart(
      "full-indexed",
      "Indexed performance since listing",
      rr,
      [
        series(
          "ENA",
          S.ena_price.map((v) => (v / S.ena_price[0]) * 100),
        ),
        series(
          "USDE",
          S.usde_close.map((v) => (v / S.usde_close[0]) * 100),
          copper,
        ),
      ],
      (v) => num(v),
      "perf",
    );
    lineChart(
      "full-ena-per-share",
      "ENA per Class A share",
      rr,
      [
        series(
          "ENA/share",
          S.ena_holdings.map((v, i) => v / S.shares_outstanding[i]),
        ),
      ],
      (v) => v.toFixed(1),
      "perf",
      false,
    );
    lineChart(
      "full-warrants-chart",
      "USDE and USDEW prices",
      rS,
      [
        { name: "USDE", data: S.usde_close, color: blue },
        { name: "USDEW", data: S.usdew_close, color: copper },
      ],
      (v) => usd(v, 0),
      "warrant",
      true,
      null,
      (v) => usd(v, 2),
    );
    payoffChart();
  }
  function payoffChart() {
    if (!S.date.length) return;
    const wp = D.liveW?.price ?? S.usdew_close.at(-1);
    if (!(wp > 0)) {
      $("#full-payoff-result").textContent = "Warrant quote unavailable";
      return;
    }
    const rr = Array.from({ length: 81 }, (_, i) => ({ i, t: i * 0.5, d: "" })),
      stock = rr.map((q) => q.t / Ethena.current(D).price),
      warrant = rr.map(
        (q) =>
          Math.max(0, q.t - D.warrants.strike) /
          (D.liveW?.price ?? S.usdew_close.at(-1)),
      );
    lineChart(
      "full-payoff-chart",
      "Value at expiry of one dollar invested",
      rr,
      [
        { name: "Stock", data: stock, color: blue },
        { name: "Warrant", data: warrant, color: copper },
      ],
      (v) => v.toFixed(1) + "×",
      "payoff",
      true,
      (v) => "$" + v.toFixed(0),
    );
    const svg = $("#full-payoff-chart");
    if (!nearViewport(svg)) return;
    const w = svg.getBoundingClientRect().width,
      l = w < 400 ? 54 : 62,
      r = w - 12,
      x = l + (payoff / 40) * (r - l);
    add(svg, "line", {
      x1: x,
      y1: 18,
      x2: x,
      y2: svg.getBoundingClientRect().height - 38,
      stroke: ink,
      "stroke-dasharray": "3 5",
      opacity: 0.65,
    });
    $("#full-payoff-label").textContent = usd(payoff);
    $("#full-payoff-result").textContent =
      "Stock " +
      (payoff / Ethena.current(D).price).toFixed(2) +
      "× · Warrant " +
      (
        Math.max(0, payoff - D.warrants.strike) /
        (D.liveW?.price ?? S.usdew_close.at(-1))
      ).toFixed(2) +
      "×";
  }
  let totals = {
    spend: cum(T.spend_usde),
    count: cum(T.spend_count),
    cashback: cum(T.cashback_usd),
    yield: cum(T.yield_usde),
  };
  function updatePayObservation() {
    const i = payIndex;
    $("#pay-observation-date").textContent = date(T.date[i]);
    let value =
      F.fullPayView === "spend"
        ? F.fullPayAgg === "total"
          ? totals.spend[i]
          : T.spend_usde[i]
        : F.fullPayView === "count"
          ? F.fullPayAgg === "total"
            ? totals.count[i]
            : T.spend_count[i]
          : T.active_wallets[i];
    $("#pay-observation-value").textContent =
      F.fullPayView === "spend" ? compact(value) : num(value);
    $("#pay-observation-metric").textContent =
      F.fullPayView === "active"
        ? "Daily spending wallets"
        : (F.fullPayAgg === "total" ? "Cumulative " : "Daily ") +
          (F.fullPayView === "spend" ? "card spend" : "spend events");
    $("#pay-observation-count").textContent = num(T.spend_count[i]);
    $("#pay-observation-active").textContent = num(T.active_wallets[i]);
    $("#pay-date-input").value = i;
  }
  function payCharts() {
    if (F.fullPage !== "pay" || !T.date.length) return;
    const rr = sliced(rP, F.fullPayRange),
      sel = rr.some((q) => q.i === payIndex);
    if (!sel) payIndex = rr.at(-1).i;
    $("#pay-date-input").min = rr[0].i;
    $("#pay-date-input").max = rr.at(-1).i;
    $$("[data-pay-range]").forEach((b) =>
      b.setAttribute("aria-pressed", b.dataset.payRange === F.fullPayRange),
    );
    $$("[data-pay-view]").forEach((b) =>
      b.setAttribute("aria-pressed", b.dataset.payView === F.fullPayView),
    );
    $$("[data-pay-agg]").forEach((b) =>
      b.setAttribute("aria-pressed", b.dataset.payAgg === F.fullPayAgg),
    );
    $$("[data-reward-view]").forEach((b) =>
      b.setAttribute("aria-pressed", b.dataset.rewardView === F.fullRewardView),
    );
    $("#pay-aggregation").hidden = F.fullPayView === "active";
    const series = (name, arr, color = blue, extra = {}) => ({
      name,
      data: sourceSeries(arr, rr),
      color,
      ...extra,
    });
    let arr =
        F.fullPayView === "spend"
          ? F.fullPayAgg === "total"
            ? totals.spend
            : T.spend_usde
          : F.fullPayView === "count"
            ? F.fullPayAgg === "total"
              ? totals.count
              : T.spend_count
            : T.active_wallets,
      name =
        F.fullPayView === "spend"
          ? "Spend"
          : F.fullPayView === "count"
            ? "Spend events"
            : "Wallets",
      isTotal = F.fullPayAgg === "total" && F.fullPayView !== "active";
    lineChart(
      "pay-main-chart",
      "EthenaPay card activity",
      rr,
      [
        series(name, arr, copper, {
          kind: isTotal ? "line" : "bar",
          fill: isTotal,
        }),
      ],
      F.fullPayView === "spend" ? compact : num,
      "pay",
    );
    lineChart(
      "pay-balance-chart",
      "USDe balance in card wallets",
      rr,
      [series("USDe held", T.tvl_usde, blue, { fill: true })],
      compact,
      "pay",
    );
    lineChart(
      "pay-flows-chart",
      "Daily deposits and withdrawals",
      rr,
      [
        series("Deposits", T.deposits_usde, blue, { kind: "bar" }),
        series(
          "Withdrawals",
          T.withdrawals_usde.map((v) => -v),
          copper,
          { kind: "bar" },
        ),
      ],
      compact,
      "pay",
    );
    lineChart(
      "pay-created-chart",
      "Cumulative card wallets created",
      rr,
      [series("Created", T.cumulative_wallets, blue, { fill: true })],
      num,
      "pay",
    );
    lineChart(
      "pay-active-chart",
      "Daily wallets with a successful spend event",
      rr,
      [series("Spending wallets", T.active_wallets, copper, { kind: "bar" })],
      num,
      "pay",
    );
    lineChart(
      "pay-cashback-chart",
      "Cashback payments",
      rr,
      [
        series(
          "Cashback",
          F.fullRewardView === "total" ? totals.cashback : T.cashback_usd,
          blue,
          {
            kind: F.fullRewardView === "total" ? "line" : "bar",
            fill: F.fullRewardView === "total",
          },
        ),
      ],
      compact,
      "pay",
    );
    lineChart(
      "pay-yield-chart",
      "Balance yield payments",
      rr,
      [
        series(
          "Yield",
          F.fullRewardView === "total" ? totals.yield : T.yield_usde,
          copper,
          {
            kind: F.fullRewardView === "total" ? "line" : "bar",
            fill: F.fullRewardView === "total",
          },
        ),
      ],
      compact,
      "pay",
    );
    updatePayObservation();
  }
  function switchPage(page) {
    F.fullPage = page;
    if (page === "sx") performance();
    else payCharts();
  }
  $$("[data-jump]").forEach(
    (b) =>
      (b.onclick = () =>
        $("#" + b.dataset.jump).scrollIntoView({
          behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
            ? "auto"
            : "smooth",
          block: "start",
        })),
  );
  $$("[data-perf]").forEach(
    (b) =>
      (b.onclick = () => {
        fixedWindow = false;
        F.fullPerf = b.dataset.perf;
        perfIndex = S.date.length - 1;
        performance();
        persist();
      }),
  );
  $$("[data-pay-range]").forEach(
    (b) =>
      (b.onclick = () => {
        fixedWindow = false;
        F.fullPayRange = b.dataset.payRange;
        payCharts();
        persist();
      }),
  );
  $$("[data-pay-view]").forEach(
    (b) =>
      (b.onclick = () => {
        F.fullPayView = b.dataset.payView;
        payCharts();
        persist();
      }),
  );
  $$("[data-pay-agg]").forEach(
    (b) =>
      (b.onclick = () => {
        F.fullPayAgg = b.dataset.payAgg;
        payCharts();
        persist();
      }),
  );
  $$("[data-reward-view]").forEach(
    (b) =>
      (b.onclick = () => {
        F.fullRewardView = b.dataset.rewardView;
        payCharts();
        persist();
      }),
  );
  $("#pay-date-input").oninput = (e) => {
    payIndex = Number(e.target.value);
    updatePayObservation();
    for (const [id, c] of registry) if (c.group === "pay") draw(id);
  };
  $("#full-payoff-price").value = payoff;
  $("#full-payoff-price").oninput = (e) => {
    payoff = Number(e.target.value);
    payoffChart();
  };
  function options() {
    const exp =
      D.options?.expiries?.[Number($("#full-option-expiry").value) || 0];
    if (!exp) {
      $("#full-option-rows").innerHTML =
        "<tr><td colspan=7>Options data unavailable</td></tr>";
      return;
    }
    $("#full-option-rows").innerHTML = exp.strikes
      .map(
        (row) =>
          "<tr><td>" +
          usd(row.strike) +
          "</td>" +
          [
            row.call.bid,
            row.call.ask,
            row.call.oi,
            row.put.bid,
            row.put.ask,
            row.put.oi,
          ]
            .map(
              (v, i) =>
                '<td class="num">' +
                (i === 2 || i === 5 ? num(v) : usd(v)) +
                "</td>",
            )
            .join("") +
          "</tr>",
      )
      .join("");
  }
  function tables() {
    const chosen = $("#full-option-expiry").selectedOptions[0]?.textContent;
    $("#full-option-expiry").replaceChildren();
    (D.options?.expiries || []).forEach((e, i) => {
      const o = document.createElement("option");
      o.value = i;
      o.textContent = date(e.expiry);
      $("#full-option-expiry").appendChild(o);
    });
    const match = [...$("#full-option-expiry").options].find(
      (o) => o.textContent === chosen,
    );
    if (match) $("#full-option-expiry").value = match.value;
    $("#full-option-expiry").onchange = options;
    options();
    const filingLabels = {
      "8-K": "Current report",
      "424B3": "Prospectus",
      "10-Q": "Quarterly report",
      "S-8": "Equity plan registration",
      "S-1": "Registration statement",
      "S-1/A": "Amended registration statement",
    };
    function filings() {
      const all = D.recent_filings || [],
        rr = showAllFilings ? all : all.slice(0, 5);
      $("#full-filing-rows").innerHTML = rr
        .map(
          (f) =>
            "<tr><td>" +
            date(f.date) +
            "</td><td>" +
            esc(f.form) +
            '</td><td><a href="' +
            esc(f.url) +
            '" target="_blank" rel="noopener noreferrer">' +
            esc(filingLabels[f.form] || "SEC filing") +
            " ↗</a></td></tr>",
        )
        .join("");
      $("#full-more-filings").textContent = showAllFilings
        ? "Show recent filings"
        : "Show all " + all.length + " filings";
    }
    $("#full-more-filings").onclick = () => {
      showAllFilings = !showAllFilings;
      filings();
    };
    filings();
    $("#full-insiders").innerHTML = (D.insiders || [])
      .map((f) => {
        const tx = f.transactions?.length ? f.transactions : [{}];
        return tx
          .map(
            (t) =>
              '<tr><td><a href="' +
              esc(f.url) +
              '" target="_blank" rel="noopener noreferrer">' +
              date(f.date) +
              " ↗</a></td><td>" +
              esc(f.owner) +
              '<br><span class="sx-muted">' +
              esc(f.role) +
              "</span></td><td>" +
              esc(t.label || "Initial ownership filing") +
              "</td><td>" +
              num(t.shares) +
              "</td><td>" +
              usd(t.price) +
              "</td></tr>",
          )
          .join("");
      })
      .join("");
    $("#full-tranches").innerHTML = (D.tranches || [])
      .map(
        (t, i) =>
          "<tr><td>" +
          [
            "Initial cash PIPE",
            "Additional cash PIPE",
            "ENA-paid PIPE + contribution",
          ][i] +
          "</td><td>" +
          num(t.tokens) +
          "</td><td>" +
          (t.locked ? "48-month lock-up" : "Modeled unlocked; restrictions disclosed") +
          "</td><td>" +
          (t.waived_on
            ? Date.now() >= Date.parse(t.waived_on)
              ? "Waived " + date(t.waived_on)
              : "Waiver " + date(t.waived_on)
            : t.locked
              ? "Scheduled lock-up"
              : "Unlocked") +
          "</td></tr>",
      )
      .join("");
    $("#full-sponsor").innerHTML = (D.warrants.sponsor || [])
      .map(
        (t) =>
          "<tr><td>" +
          esc(t.tranche) +
          "</td><td>" +
          (t.count / 1e6).toFixed(2) +
          "M</td><td>" +
          usd(t.strike) +
          "</td><td>" +
          esc(t.expiry) +
          "</td></tr>",
      )
      .join("");
    $("#full-data-rows").innerHTML = rS
      .slice(-10)
      .reverse()
      .map(
        (q) =>
          "<tr><td>" +
          date(q.d) +
          "</td><td>" +
          usd(S.usde_close[q.i]) +
          "</td><td>" +
          usd(S.ena_price[q.i], 4) +
          "</td><td>" +
          usd(S.nav_per_share[q.i]) +
          "</td><td>" +
          S.mnav[q.i].toFixed(3) +
          "×</td></tr>",
      )
      .join("");
    $("#pay-data-rows").innerHTML = rP
      .slice(-10)
      .reverse()
      .map(
        (q) =>
          "<tr><td>" +
          date(q.d) +
          "</td><td>" +
          compact(T.spend_usde[q.i]) +
          "</td><td>" +
          num(T.spend_count[q.i]) +
          "</td><td>" +
          num(T.active_wallets[q.i]) +
          "</td><td>" +
          compact(T.tvl_usde[q.i]) +
          "</td></tr>",
      )
      .join("");
    const per = D.ena_holdings / D.shares_outstanding,
      completed = Ethena.completedCloses(D),
      callCount = completed.slice(-30).filter((v) => v >= 10).length;
    $("#full-index-latest").textContent =
      "ENA " +
      Math.round((S.ena_price.at(-1) / S.ena_price[0]) * 100) +
      " · USDE " +
      Math.round((S.usde_close.at(-1) / S.usde_close[0]) * 100);
    $("#full-ena-share").textContent = per.toFixed(2);
    $("#full-treasury-per").textContent = per.toFixed(2);
    $("#full-call-count").textContent = callCount + " / 20 qualifying closes";
    $("#full-call-progress").innerHTML = Array.from(
      { length: 20 },
      (_, i) => '<i class="' + (i < callCount ? "on" : "") + '"></i>',
    ).join("");
    const wp = D.liveW?.price ?? S.usdew_close.at(-1),
      prior = S.usdew_close.at(-2);
    $("#full-warrant-delta").textContent =
      Number.isFinite(wp) && prior > 0
        ? ((wp / prior - 1) * 100).toFixed(1) + "% vs prior observation"
        : "Prior quote unavailable";
  }
  function payHeadlines() {
    if (!T.date.length) return;
    $("#pay-hero-spend").textContent = compact(H.spend_usde_30d);
    $("#pay-concentration").textContent = pct(H.top10_balance_share);
    $("#pay-top-ten-bar").style.width = pct(H.top10_balance_share);
    $("#pay-other-bar").style.width = pct(1 - H.top10_balance_share);
    $("#pay-average-balance").textContent = usd(
      H.funded_wallets ? H.tvl_usde / H.funded_wallets : null,
      0,
    );
    $("#pay-refunds").textContent = compact(H.lifetime_reversals_usde);
    $("#pay-last-active").textContent =
      num(T.active_wallets.at(-1)) + " latest day";
    $("#pay-reward-total").textContent = compact(
      H.cashback_usd_total + H.yield_usd_total,
    );
    $("#pay-cashback-rate").textContent = pct(H.cashback_rate_30d);
    $("#pay-yield-apy").textContent = pct(H.yield_apy_30d);
  }
  tables();
  payHeadlines();
  switchPage(F.fullPage);
  let frame;
  const sizes = new WeakMap();
  const ro = new ResizeObserver((entries) => {
    const changed = entries.some((e) => {
      const previous = sizes.get(e.target);
      sizes.set(e.target, e.contentRect.width);
      return previous !== undefined && previous !== e.contentRect.width;
    });
    if (!changed) return;
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(() => {
      for (const [id] of registry) draw(id);
      if (F.fullPage === "sx") payoffChart();
    });
  });
  const visible = new IntersectionObserver(
    (entries) => {
      for (const e of entries)
        if (e.isIntersecting) {
          if (e.target.id === "full-payoff-chart") payoffChart();
          else draw(e.target.id);
        }
    },
    { rootMargin: "200px" },
  );
  $$(".full-chart").forEach((e) => {
    ro.observe(e);
    visible.observe(e);
  });
  $$("details:not(.chart-tools)").forEach((e) =>
    e.addEventListener("toggle", () => {
      if (e.open) for (const [id] of registry) draw(id);
    }),
  );
  return {
    switchPage,
    update(nextD, nextP) {
      const payDay = T.date[payIndex],
        atEnd = payIndex === T.date.length - 1;
      D = nextD;
      P = nextP;
      S = D.series;
      H = P.headline;
      T = P.series;
      rS = S.date.map((d, i) => ({ i, d, t: ts(d) }));
      rP = T.date.map((d, i) => ({ i, d, t: ts(d) }));
      payIndex = atEnd
        ? T.date.length - 1
        : Math.max(0, T.date.indexOf(payDay));
      perfIndex = Math.min(perfIndex, S.date.length - 1);
      totals = {
        spend: cum(T.spend_usde),
        count: cum(T.spend_count),
        cashback: cum(T.cashback_usd),
        yield: cum(T.yield_usde),
      };
      tables();
      payHeadlines();
      switchPage(F.fullPage);
    },
  };
};
