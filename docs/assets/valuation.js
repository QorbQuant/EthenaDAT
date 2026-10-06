window.mountValuation = function (initial) {
  const root = document.getElementById("sx-studio");
  const $ = (s) => root.querySelector(s),
    $$ = (s) => [...root.querySelectorAll(s)];
  let D = initial,
    S = D.series;
  const makeRows = () =>
    S.date.map((date, i) => ({
      date,
      t: Date.parse(date + "T00:00:00Z"),
      ena: S.ena_price[i],
      per: S.ena_holdings[i] / S.shares_outstanding[i],
      price: S.usde_close[i],
      nav: S.ena_price[i] * S.ena_holdings[i],
      cap: S.usde_close[i] * S.shares_outstanding[i],
      mnav:
        S.usde_close[i] /
        ((S.ena_price[i] * S.ena_holdings[i]) / S.shares_outstanding[i]),
    }));
  let rows = makeRows(),
    base = Ethena.current(D);
  const money = (v, n = 2) =>
      !Number.isFinite(v)
        ? "N/A"
        : "$" +
          v.toLocaleString("en-US", {
            minimumFractionDigits: n,
            maximumFractionDigits: n,
          }),
    mill = (v) => "$" + (v / 1e6).toFixed(1) + "M",
    sign = (v) => (v < 0 ? "−" : "+") + Math.abs(v).toFixed(2),
    dateLabel = (d) =>
      new Date(d + "T00:00:00Z").toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        timeZone: "UTC",
      }),
    ns = "http://www.w3.org/2000/svg";
  let state = {
      mode: "history",
      ena: base.ena,
      mnav: base.mnav,
      range: "all",
      attribRange: "30",
      factor: null,
      expanded: false,
    },
    selected = rows.length - 1,
    geometry = null,
    dragging = false;
  root.sxState = state;
  function el(tag, attrs = {}, text) {
    const n = document.createElementNS(ns, tag);
    Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, v));
    if (text !== undefined) n.textContent = text;
    return n;
  }
  function add(svg, tag, a, t) {
    const n = el(tag, a, t);
    svg.appendChild(n);
    return n;
  }
  const shared = ChartShare.initial;
  let fixedWindow = !!(shared.from || shared.to);
  function saved() {
    return {
      ...shared,
      attribRange: shared.chart === "sx-waterfall" ? shared.range : undefined,
      expanded: shared.chart === "sx-waterfall",
    };
  }
  function applySaved(v) {
    if (["history", "explore"].includes(v.mode)) state.mode = v.mode;
    if (Number.isFinite(v.ena) && v.ena >= 0.01 && v.ena <= 2)
      state.ena = v.ena;
    if (Number.isFinite(v.mnav) && v.mnav >= 0.01 && v.mnav <= 3)
      state.mnav = v.mnav;
    if (["30", "90", "all"].includes(v.range)) state.range = v.range;
    if (["30", "90", "all"].includes(v.attribRange))
      state.attribRange = v.attribRange;
    if (["ena", "holdings", "multiple", "price", null].includes(v.factor))
      state.factor = v.factor;
    if (typeof v.expanded === "boolean") state.expanded = v.expanded;
  }
  applySaved(saved());
  if (shared.date && rows.some((r) => r.date === shared.date))
    selected = rows.findIndex((r) => r.date === shared.date);
  function persist() {}
  function filter(range) {
    if (fixedWindow) return ChartShare.windowRows(rows, shared.from, shared.to);
    if (range === "all") return rows;
    const from = base.t - Number(range) * 864e5;
    return rows.filter((r) => r.t >= from);
  }
  if (!filter(state.range).includes(rows[selected]))
    selected = rows.indexOf(filter(state.range).at(-1));
  function path(points) {
    return points
      .map((p, i) => (i ? "L" : "M") + p[0].toFixed(2) + "," + p[1].toFixed(2))
      .join(" ");
  }
  function setup(svg, h) {
    const w = Math.max(230, svg.getBoundingClientRect().width);
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.replaceChildren();
    return w;
  }
  function mapChart() {
    const svg = $("#sx-main-chart"),
      h = svg.getBoundingClientRect().height || 310,
      w = setup(svg, h),
      l = 44,
      r = w - 19,
      t = 25,
      b = h - 44;
    const xmin = Math.min(0.05, state.ena * 0.8),
      xmax = Math.max(0.6, state.ena * 1.08),
      ymin = Math.min(0.1, state.mnav * 0.8),
      ymax = Math.max(1.2, state.mnav * 1.08),
      x = (v) => l + ((v - xmin) / (xmax - xmin)) * (r - l),
      y = (v) => b - ((v - ymin) / (ymax - ymin)) * (b - t);
    geometry = { l, r, t, b, xmin, xmax, ymin, ymax, w, h };
    add(
      svg,
      "title",
      {},
      "Scenario map: implied share price from ENA price and mNAV",
    );
    const yt = [
      0.25,
      0.5,
      0.75,
      1,
      ...(ymax > 1.5 ? [1.5, 2, 2.5, 3].filter((v) => v <= ymax) : []),
    ];
    yt.forEach((v) => {
      add(svg, "line", {
        x1: l,
        y1: y(v),
        x2: r,
        y2: y(v),
        class: "sx-grid",
        opacity: v === 1 ? 0.8 : 0.48,
      });
      add(
        svg,
        "text",
        { x: l - 10, y: y(v) + 3, "text-anchor": "end" },
        v.toFixed(2) + "×",
      );
    });
    const xt = w < 430 ? [0.1, 0.3, 0.5] : [0.1, 0.2, 0.3, 0.4, 0.5, 0.6];
    if (xmax > 0.8)
      xt.splice(
        0,
        xt.length,
        ...[0.1, 0.5, 1, 1.5, 2].filter((v) => v <= xmax),
      );
    xt.forEach((v) => {
      add(svg, "line", {
        x1: x(v),
        y1: t,
        x2: x(v),
        y2: b,
        class: "sx-grid",
        opacity: 0.35,
      });
      add(
        svg,
        "text",
        { x: x(v), y: b + 21, "text-anchor": "middle" },
        money(v, 2),
      );
    });
    add(svg, "text", { x: l, y: 12, "font-size": 9 }, "mNAV");
    add(
      svg,
      "text",
      { x: r, y: h - 3, "text-anchor": "end" },
      "ENA price · USD",
    );
    const prices = [5, 10, 15, 20, 30, 40, 60, 90];
    prices.forEach((p, i) => {
      const pts = [];
      for (let j = 0; j <= 200; j++) {
        const xv = xmin + ((xmax - xmin) * j) / 200,
          yv = p / (base.per * xv);
        if (yv >= ymin && yv <= ymax) pts.push([x(xv), y(yv)]);
      }
      if (pts.length < 2) return;
      add(svg, "path", { d: path(pts), class: "sx-contour" });
      let point =
        pts[
          Math.min(
            pts.length - 1,
            Math.floor(pts.length * (w < 430 ? 0.78 : 0.88)),
          )
        ];
      if (w >= 430 || i % 2 === 0)
        add(
          svg,
          "text",
          {
            x: point[0],
            y: point[1] - 6,
            "text-anchor": "middle",
            class: "sx-line-label",
          },
          "$" + p,
        );
    });
    const px = x(state.ena),
      py = y(state.mnav),
      cx = x(base.ena),
      cy = y(base.mnav);
    add(svg, "line", {
      x1: l,
      y1: py,
      x2: px,
      y2: py,
      stroke: "#eeeae3",
      "stroke-opacity": 0.33,
      "stroke-dasharray": "3 5",
    });
    add(svg, "line", {
      x1: px,
      y1: py,
      x2: px,
      y2: b,
      stroke: "#eeeae3",
      "stroke-opacity": 0.33,
      "stroke-dasharray": "3 5",
    });
    add(svg, "circle", { cx, cy, r: 4, fill: "#8aa9cf" });
    if (Math.hypot(cx - px, cy - py) > 35)
      add(svg, "text", { x: cx + 9, y: cy - 9, fill: "#8aa9cf" }, "Current");
    add(svg, "circle", {
      cx: px,
      cy: py,
      r: 13,
      fill: "none",
      stroke: "#eeeae3",
      "stroke-opacity": 0.32,
    });
    add(svg, "circle", {
      cx: px,
      cy: py,
      r: 5,
      fill: "#eeeae3",
      stroke: "#0d1116",
      "stroke-width": 2,
    });
    const value = money(state.ena * base.per * state.mnav),
      labelWidth = 74,
      lx = Math.min(r - labelWidth, Math.max(l, px + 15)),
      ly = Math.max(t + 8, py - 15);
    add(svg, "rect", {
      x: lx - 4,
      y: ly - 13,
      width: labelWidth,
      height: 23,
      rx: 3,
      fill: "#eeeae3",
    });
    add(
      svg,
      "text",
      {
        x: lx + labelWidth / 2 - 4,
        y: ly + 2,
        "text-anchor": "middle",
        style: "fill:#11161b;font-size:12px;font-weight:500",
      },
      value,
    );
  }
  function historyChart() {
    const svg = $("#sx-main-chart"),
      h = svg.getBoundingClientRect().height || 310,
      w = setup(svg, h),
      data = filter(state.range),
      l = 49,
      r = w - 14,
      t = 24,
      b = h - 38,
      max = Math.ceil(Math.max(...data.map((q) => q.nav)) / 2e8) * 2e8,
      x = (v) =>
        l +
        ((v - data[0].t) / Math.max(1, data.at(-1).t - data[0].t)) * (r - l),
      y = (v) => b - (v / max) * (b - t);
    geometry = { l, r, t, b, w, h, data, x, y };
    for (let i = 0; i <= 4; i++) {
      const v = (max * i) / 4;
      add(svg, "line", {
        x1: l,
        y1: y(v),
        x2: r,
        y2: y(v),
        class: "sx-grid",
        opacity: 0.6,
      });
      add(
        svg,
        "text",
        { x: l - 9, y: y(v) + 3, "text-anchor": "end" },
        "$" + Math.round(v / 1e6) + "M",
      );
    }
    const ticks = [
      0,
      Math.floor((data.length - 1) / 3),
      Math.floor(((data.length - 1) * 2) / 3),
      data.length - 1,
    ];
    ticks.forEach((i, j) => {
      const q = data[i];
      add(
        svg,
        "text",
        {
          x: x(q.t),
          y: b + 24,
          "text-anchor": j === 0 ? "start" : j === 3 ? "end" : "middle",
        },
        new Date(q.t).toLocaleDateString("en-GB", {
          month: "short",
          day: "numeric",
          timeZone: "UTC",
        }),
      );
    });
    add(svg, "path", {
      d: path(data.map((q) => [x(q.t), y(q.nav)])) + ` L${r},${b} L${l},${b} Z`,
      fill: "#8aa9cf",
      "fill-opacity": 0.045,
    });
    [
      ["nav", "#8aa9cf"],
      ["cap", "#cf9b79"],
    ].forEach(([key, c]) =>
      add(svg, "path", {
        d: path(data.map((q) => [x(q.t), y(q[key])])),
        fill: "none",
        stroke: c,
        "stroke-width": 1.8,
      }),
    );
    const q = rows[selected];
    if (q.t >= data[0].t) {
      add(svg, "line", {
        x1: x(q.t),
        y1: t,
        x2: x(q.t),
        y2: b,
        stroke: "#8b96a5",
        "stroke-width": 1,
        "stroke-dasharray": "3 4",
      });
      [
        ["nav", "#8aa9cf"],
        ["cap", "#cf9b79"],
      ].forEach(([key, c]) =>
        add(svg, "circle", {
          cx: x(q.t),
          cy: y(q[key]),
          r: 3.5,
          fill: c,
          stroke: "#0d1116",
          "stroke-width": 2,
        }),
      );
    }
  }
  function updateHistory() {
    const q = rows[selected];
    $("#sx-history-date").textContent = dateLabel(q.date);
    $("#sx-history-mnav").textContent = q.mnav.toFixed(2) + "×";
    $("#sx-h-nav").textContent = mill(q.nav);
    $("#sx-h-cap").textContent = mill(q.cap);
    $("#sx-h-price").textContent = money(q.price);
    $("#sx-history-date-input").value = selected;
  }
  function scenarioControls() {
    const implied = state.ena * base.per * state.mnav,
      delta = (implied / base.price - 1) * 100;
    $("#sx-result").textContent = money(implied);
    $("#sx-relative").textContent =
      Math.abs(delta) < 0.005
        ? "At current valuation"
        : sign(delta) + "% vs " + money(base.price) + " current";
    $("#sx-relative").style.color =
      Math.abs(delta) < 0.005
        ? "var(--sx-muted)"
        : delta > 0
          ? "var(--sx-green)"
          : "var(--sx-red)";
    $("#sx-ena-input").value = Number(state.ena.toFixed(4));
    $("#sx-mnav-input").value = Number(state.mnav.toFixed(4));
    $("#sx-ena-range").max = Math.max(0.6, state.ena);
    $("#sx-ena-range").min = Math.min(0.05, state.ena);
    $("#sx-mnav-range").max = Math.max(1.2, state.mnav);
    $("#sx-mnav-range").min = Math.min(0.1, state.mnav);
    $("#sx-ena-range").value = state.ena;
    $("#sx-mnav-range").value = state.mnav;
    const ends = $$(".sx-range-ends");
    ends[0].children[0].textContent = money(Number($("#sx-ena-range").min));
    ends[0].children[1].textContent = money(Number($("#sx-ena-range").max));
    ends[1].children[0].textContent =
      Number($("#sx-mnav-range").min).toFixed(2) + "×";
    ends[1].children[1].textContent =
      Number($("#sx-mnav-range").max).toFixed(2) + "×";
  }
  function formula() {
    const q =
      state.mode === "history"
        ? rows[selected]
        : {
            ena: state.ena,
            per: base.per,
            mnav: state.mnav,
            price: state.ena * base.per * state.mnav,
          };
    $("#sx-f-ena").textContent = money(q.ena, 4);
    $("#sx-f-holdings").textContent = q.per.toFixed(2);
    $("#sx-f-mnav").textContent = q.mnav.toFixed(3) + "×";
    $("#sx-f-price").textContent = money(q.price);
    $("#sx-f-price-label").textContent =
      state.mode === "explore" ? "Implied share price" : "Observed share price";
    $("#sx-formula-context").textContent =
      state.mode === "explore"
        ? "Scenario assumptions"
        : "Observation · " + dateLabel(rows[selected].date);
    $$("[data-factor]").forEach((b) =>
      b.setAttribute("aria-pressed", b.dataset.factor === state.factor),
    );
  }
  const factorMeta = {
    ena: [
      "ENA price",
      "Underlying token price from the repository’s CoinGecko series.",
      "ena",
      (v) => money(v, 4),
    ],
    holdings: [
      "ENA per share",
      "Reported ENA holdings divided by the dataset’s Class A share count.",
      "per",
      (v) => v.toFixed(2),
    ],
    multiple: [
      "mNAV",
      "The market’s valuation of the reported token assets. Recomputed from price and token NAV per share.",
      "mnav",
      (v) => v.toFixed(3) + "×",
    ],
    price: [
      "Share price",
      "USDE observations from the repository’s Yahoo Finance series.",
      "price",
      (v) => money(v),
    ],
  };
  function detail() {
    const box = $("#sx-factor-detail");
    box.hidden = !state.factor;
    if (!state.factor) return;
    const [title, desc, key, fmt] = factorMeta[state.factor];
    $("#sx-detail-title").textContent = title;
    $("#sx-detail-description").textContent = desc;
    const svg = $("#sx-detail-chart"),
      w = setup(svg, 110),
      l = 45,
      r = w - 5,
      t = 16,
      b = 85,
      data = filter(state.range),
      values = data.map((q) => q[key]),
      low = Math.min(...values),
      high = Math.max(...values),
      pad = Math.max((high - low) * 0.12, high * 0.003),
      min = low - pad,
      max = high + pad,
      x = (q) =>
        l +
        ((q.t - data[0].t) / Math.max(1, data.at(-1).t - data[0].t)) * (r - l),
      y = (v) => b - ((v - min) / (max - min)) * (b - t);
    [low, high].forEach((v) => {
      add(svg, "line", { x1: l, y1: y(v), x2: r, y2: y(v), stroke: "#29313a" });
      add(
        svg,
        "text",
        {
          x: l - 7,
          y: y(v) + 3,
          "text-anchor": "end",
          style: "fill:#99a3b0;font-size:11px",
        },
        fmt(v),
      );
    });
    add(svg, "path", {
      d: path(data.map((q) => [x(q), y(q[key])])),
      fill: "none",
      stroke: "#8aa9cf",
      "stroke-width": 1.6,
    });
    const q = rows[selected];
    if (q.t >= data[0].t) {
      add(svg, "line", {
        x1: x(q),
        y1: t,
        x2: x(q),
        y2: b,
        stroke: "#99a3b0",
        "stroke-dasharray": "3 4",
      });
      add(svg, "circle", { cx: x(q), cy: y(q[key]), r: 3, fill: "#eeeae3" });
    }
    add(
      svg,
      "text",
      { x: l, y: 105, style: "fill:#99a3b0;font-size:11px" },
      dateLabel(data[0].date),
    );
    add(
      svg,
      "text",
      {
        x: r,
        y: 105,
        "text-anchor": "end",
        style: "fill:#99a3b0;font-size:11px",
      },
      dateLabel(base.date),
    );
    $("#sx-detail-readout").textContent =
      dateLabel(q.date) + " · " + fmt(q[key]);
  }
  function shapley(a, b) {
    const orders = [
        [0, 1, 2],
        [0, 2, 1],
        [1, 0, 2],
        [1, 2, 0],
        [2, 0, 1],
        [2, 1, 0],
      ],
      c = [0, 0, 0],
      prod = (v) => v.reduce((p, x) => p * x, 1);
    for (const order of orders) {
      const v = [...a];
      for (const i of order) {
        const old = prod(v);
        v[i] = b[i];
        c[i] += (prod(v) - old) / 6;
      }
    }
    return c;
  }
  function attribution() {
    const data = filter(state.attribRange),
      end = data.at(-1),
      start = data[0],
      c = shapley(
        [start.ena, start.per, start.mnav],
        [end.ena, end.per, end.mnav],
      ),
      pct = (end.price / start.price - 1) * 100;
    $("#sx-total-move").textContent = sign(pct) + "%";
    $("#sx-moved-summary").textContent =
      (state.attribRange === "all"
        ? "Since listing"
        : state.attribRange === "30"
          ? "Past month"
          : "Past 3 months") +
      " · " +
      (c[0] > c[2] ? "ENA price leads" : "Multiple leads");
    $("#sx-attrib-dates").textContent =
      dateLabel(start.date) +
      " to " +
      dateLabel(end.date) +
      " · dollars per share";
    $("#sx-attrib").hidden = !state.expanded;
    $("#sx-moved-toggle").setAttribute("aria-expanded", state.expanded);
    $("#sx-moved-arrow").textContent = state.expanded ? "−" : "+";
    $$("[data-attrib-range]").forEach((b) =>
      b.setAttribute(
        "aria-pressed",
        b.dataset.attribRange === state.attribRange,
      ),
    );
    if (!state.expanded) return;
    let last = start.price;
    const bars = [
      { name: "Start", from: 0, to: start.price, color: "#8a96a5" },
    ];
    ["ENA price", "ENA / share", "mNAV"].forEach((name, i) => {
      bars.push({
        name,
        from: last,
        to: last + c[i],
        color: c[i] < 0 ? "#cf9b79" : "#8aa9cf",
        value: c[i],
      });
      last += c[i];
    });
    bars.push({ name: "End", from: 0, to: end.price, color: "#eeeae3" });
    const svg = $("#sx-waterfall"),
      w = setup(svg, 190),
      left = 12,
      right = w - 12,
      top = 28,
      bottom = 154,
      max = Math.max(...bars.flatMap((q) => [q.from, q.to])) * 1.12,
      min = Math.min(0, ...bars.flatMap((q) => [q.from, q.to])),
      y = (v) => bottom - ((v - min) / (max - min)) * (bottom - top),
      slot = (right - left) / 5,
      bw = Math.min(75, slot * 0.48);
    bars.forEach((q, i) => {
      let x = left + i * slot + (slot - bw) / 2,
        yy = Math.min(y(q.from), y(q.to)),
        hh = Math.max(2, Math.abs(y(q.from) - y(q.to)));
      add(svg, "rect", {
        x,
        y: yy,
        width: bw,
        height: hh,
        fill: q.color,
        rx: 1,
      });
      add(
        svg,
        "text",
        {
          x: x + bw / 2,
          y: Math.max(13, yy - 8),
          "text-anchor": "middle",
          style: "fill:#eeeae3;font-size:11px",
        },
        q.value === undefined
          ? money(q.to)
          : (q.value < 0 ? "−" : "+") + money(Math.abs(q.value)),
      );
      add(
        svg,
        "text",
        {
          x: x + bw / 2,
          y: 177,
          "text-anchor": "middle",
          style: "fill:#99a3b0;font-size:11px",
        },
        q.name,
      );
      if (i < 4)
        add(svg, "line", {
          x1: x + bw,
          y1: y(q.to),
          x2: left + (i + 1) * slot + (slot - bw) / 2,
          y2: y(q.to),
          stroke: "#45515e",
          "stroke-dasharray": "3 4",
        });
    });
    $("#sx-attrib-rows").replaceChildren();
    const labels = [
      "ENA price contribution",
      "ENA per share contribution",
      "mNAV contribution",
      "Total change",
    ];
    [...c, end.price - start.price].forEach((v, i) => {
      const tr = document.createElement("tr"),
        label = document.createElement("td"),
        val = document.createElement("td");
      label.textContent = labels[i];
      val.textContent = (v < 0 ? "−" : "+") + money(Math.abs(v));
      tr.append(label, val);
      $("#sx-attrib-rows").appendChild(tr);
    });
  }
  function render() {
    const explore = state.mode === "explore";
    $$("[data-mode]").forEach((b) =>
      b.setAttribute("aria-pressed", b.dataset.mode === state.mode),
    );
    $("#sx-scenario-controls").hidden = !explore;
    $("#sx-history-controls").hidden = explore;
    $("#sx-map-legend").hidden = !explore;
    $("#sx-history-ranges").hidden = explore;
    $("#sx-plot-title").textContent = explore
      ? "Implied share-price contours"
      : "Market cap & token NAV";
    $("#sx-chart-hint").textContent = explore
      ? "Drag anywhere to explore"
      : "Blue · token NAV     /     Copper · market cap";
    $("#sx-chart-foot-right").textContent = explore
      ? "Fixed ENA per share"
      : "Observed trading days";
    $("#sx-main-chart").setAttribute(
      "aria-label",
      explore
        ? "Valuation map. ENA price horizontally; mNAV vertically. Drag or use the scenario controls."
        : "Historical market cap and token NAV. Use the observation-date slider to inspect data.",
    );
    $$("[data-range]").forEach((b) =>
      b.setAttribute("aria-pressed", b.dataset.range === state.range),
    );
    const data = filter(state.range);
    if (!data.includes(rows[selected])) selected = rows.indexOf(data.at(-1));
    $("#sx-history-date-input").min = rows.indexOf(data[0]);
    $("#sx-history-date-input").max = rows.indexOf(data.at(-1));
    scenarioControls();
    updateHistory();
    formula();
    if (explore) mapChart();
    else historyChart();
    detail();
    attribution();
  }
  function announce() {
    const value = state.ena * base.per * state.mnav;
    $("#sx-scenario-announcement").textContent =
      "Scenario implied share price " + money(value);
  }
  function setScenario(key, value) {
    const max = key === "ena" ? 2 : 3;
    if (!Number.isFinite(value) || value < 0.01 || value > max) {
      $("#sx-error").textContent = "Enter a value from 0.01 to " + max + ".";
      return;
    }
    $("#sx-error").textContent = "";
    state[key] = value;
    scenarioControls();
    formula();
    mapChart();
  }
  $$("[data-mode]").forEach(
    (b) =>
      (b.onclick = () => {
        state.mode = b.dataset.mode;
        render();
        persist();
      }),
  );
  [
    ["ena", "sx-ena"],
    ["mnav", "sx-mnav"],
  ].forEach(([key, id]) => {
    const range = $("#" + id + "-range"),
      input = $("#" + id + "-input");
    range.oninput = () => setScenario(key, Number(range.value));
    range.onchange = () => {
      announce();
      persist();
    };
    input.oninput = () => {
      setScenario(key, input.valueAsNumber);
    };
    input.onchange = () => {
      announce();
      persist();
    };
  });
  $("#sx-reset").onclick = () => {
    state.ena = base.ena;
    state.mnav = base.mnav;
    $("#sx-error").textContent = "";
    render();
    announce();
    persist();
  };
  $$("[data-range]").forEach(
    (b) =>
      (b.onclick = () => {
        fixedWindow = false;
        state.range = b.dataset.range;
        state.attribRange = state.range;
        selected = rows.length - 1;
        render();
        persist();
      }),
  );
  $("#sx-history-date-input").oninput = (e) => {
    selected = Number(e.target.value);
    updateHistory();
    formula();
    historyChart();
    detail();
  };
  $$("[data-factor]").forEach(
    (b) =>
      (b.onclick = () => {
        state.factor =
          state.factor === b.dataset.factor ? null : b.dataset.factor;
        formula();
        detail();
        persist();
      }),
  );
  $("#sx-moved-toggle").onclick = () => {
    state.expanded = !state.expanded;
    attribution();
    persist();
  };
  $$("[data-attrib-range]").forEach(
    (b) =>
      (b.onclick = () => {
        fixedWindow = false;
        state.attribRange = b.dataset.attribRange;
        render();
        persist();
      }),
  );
  const main = $("#sx-main-chart");
  function pointer(e) {
    const rect = main.getBoundingClientRect(),
      g = geometry;
    if (!g) return;
    const px = Math.min(
        g.r,
        Math.max(g.l, ((e.clientX - rect.left) * g.w) / rect.width),
      ),
      py = Math.min(
        g.b,
        Math.max(g.t, ((e.clientY - rect.top) * g.h) / rect.height),
      );
    if (state.mode === "explore") {
      if (!dragging) return;
      state.ena = g.xmin + ((px - g.l) / (g.r - g.l)) * (g.xmax - g.xmin);
      state.mnav = g.ymin + ((g.b - py) / (g.b - g.t)) * (g.ymax - g.ymin);
      scenarioControls();
      formula();
      mapChart();
    } else {
      const time =
        g.data[0].t +
        ((px - g.l) / (g.r - g.l)) * (g.data.at(-1).t - g.data[0].t);
      let nearest = g.data.reduce((a, b) =>
        Math.abs(a.t - time) < Math.abs(b.t - time) ? a : b,
      );
      selected = rows.indexOf(nearest);
      updateHistory();
      formula();
      historyChart();
      detail();
    }
  }
  main.onpointerdown = (e) => {
    if (e.button !== 0) return;
    dragging = true;
    main.setPointerCapture(e.pointerId);
    pointer(e);
  };
  main.onpointermove = pointer;
  main.onpointerup = (e) => {
    dragging = false;
    if (main.hasPointerCapture(e.pointerId))
      main.releasePointerCapture(e.pointerId);
    announce();
    persist();
  };
  main.onpointercancel = () => {
    dragging = false;
  };
  function headline() {
    const ratio = $("#sx-ratio"),
      text = base.mnav.toFixed(2);
    if (ratio.textContent !== text + "×")
      ratio.innerHTML = text + "<span>×</span>";
    $("#sx-cents").textContent = Math.round(base.mnav * 100) + "¢";
    $("#sx-price").textContent = money(base.price);
    $("#sx-price-change").textContent = D.usde.prev_close
      ? sign((base.price / D.usde.prev_close - 1) * 100) + "% vs prior close"
      : "Prior close unavailable";
    $("#sx-price-change").classList.toggle(
      "positive",
      base.price >= D.usde.prev_close,
    );
    $(
      "#sx-nav-value",
    ).parentElement.nextElementSibling.firstElementChild.style.width =
      (base.nav / Math.max(base.nav, base.cap)) * 100 + "%";
    $("#sx-nav-value").textContent = mill(base.nav);
    $("#sx-cap-value").textContent = mill(base.cap);
    $("#sx-cap-bar").style.width =
      (base.cap / Math.max(base.cap, base.nav)) * 100 + "%";
    $("#sx-shares").textContent = (D.shares_outstanding / 1e6).toFixed(3) + "M";
    $("#sx-nav-share").textContent = money(base.ena * base.per);
    $("#sx-warrant").textContent = money(
      D.liveW?.price ?? S.usdew_close.at(-1),
    );
  }
  for (const id of ["sx-main-chart", "sx-detail-chart"])
    ChartShare.register(id, () => {
      const data = filter(state.range),
        scenario = id === "sx-main-chart" && state.mode === "explore";
      const q = rows[selected],
        factor = id === "sx-detail-chart" ? state.factor : null;
      const key = factor ? factorMeta[factor][2] : null;
      return {
        title: scenario
          ? "StablecoinX valuation scenario"
          : factor
            ? factorMeta[factor][0]
            : "StablecoinX market cap & token NAV",
        visual: {
          title: scenario
            ? "What could StablecoinX be worth?"
            : factor
              ? "StablecoinX: " + factorMeta[factor][0]
              : "StablecoinX: market cap vs NAV",
          category: scenario ? "SCENARIO / NOT A FORECAST" : "STABLECOINX",
          type: scenario ? "scenario" : "series",
          description: scenario
            ? "Implied share price · holdings and share count held fixed"
            : factor
              ? factorMeta[factor][0] + " history"
              : "Market value against reported ENA token holdings",
          source: "Public filings / market data",
          caveat:
            "Reported token NAV excludes other assets & liabilities. Class A share basis.",
          rows: data.map((r) => ({ d: r.date, t: r.t })),
          series: factor
            ? [
                {
                  name: factorMeta[factor][0],
                  color: "#8aa9cf",
                  data: data.map((r) => r[key]),
                },
              ]
            : [
                {
                  name: "Token NAV",
                  color: "#8aa9cf",
                  data: data.map((r) => r.nav),
                },
                {
                  name: "Market cap",
                  color: "#cf9b79",
                  data: data.map((r) => r.cap),
                },
              ],
          format: factor ? factorMeta[factor][3] : mill,
          axisFormat: factor
            ? factorMeta[factor][3]
            : (v) => "$" + (v / 1e6).toFixed(0) + "M",
          zero: !factor,
          selected: q.t,
          scenario: scenario
            ? {
                ena: state.ena,
                mnav: state.mnav,
                per: base.per,
                currentEna: base.ena,
                currentMnav: base.mnav,
              }
            : null,
        },
        kind: scenario ? "SCENARIO" : "RECORDED DATA",
        updated: D.generated_at,
        period: scenario
          ? "Illustrative inputs, not a forecast"
          : data[0].date + " to " + data.at(-1).date,
        subtitle: scenario
          ? `ENA $${state.ena.toFixed(4)} × ${base.per.toFixed(4)} ENA/share × ${state.mnav.toFixed(4)} mNAV = $${(state.ena * base.per * state.mnav).toFixed(2)} per share`
          : (factor
              ? factorMeta[factor][0] +
                " · " +
                {
                  ena: "USD per ENA",
                  holdings: "ENA per Class A share",
                  multiple: "multiple of token NAV",
                  price: "USD per share",
                }[factor]
              : "Blue: token NAV / Copper: market cap · USD") +
            " · Selected: " +
            q.date,
        note:
          "Reported ENA token NAV excludes other assets and liabilities; Class A share-count basis. " +
          (D.liveDate
            ? "Current session may include intraday quotes."
            : "Recorded source observations."),
        columns: scenario
          ? [
              "ena_price_usd",
              "ena_per_share",
              "mnav",
              "implied_share_price_usd",
            ]
          : factor
            ? [
                "date",
                {
                  ena: "ena_price_usd",
                  holdings: "ena_per_share",
                  multiple: "mnav",
                  price: "share_price_usd",
                }[factor],
              ]
            : [
                "date",
                "token_nav_usd",
                "market_cap_usd",
                "share_price_usd",
                "ena_price_usd",
                "ena_per_share",
                "mnav",
              ],
        rows: scenario
          ? [
              [
                state.ena,
                base.per,
                state.mnav,
                state.ena * base.per * state.mnav,
              ],
            ]
          : data.map((r) =>
              factor
                ? [r.date, r[key]]
                : [r.date, r.nav, r.cap, r.price, r.ena, r.per, r.mnav],
            ),
        state: {
          mode: state.mode,
          range: state.range,
          from: data[0].date,
          to: data.at(-1).date,
          date: q.date,
          ena: scenario ? state.ena : null,
          mnav: scenario ? state.mnav : null,
          factor,
        },
      };
    });
  ChartShare.register("sx-waterfall", () => {
    const data = filter(state.attribRange),
      start = data[0],
      end = data.at(-1);
    const c = shapley(
      [start.ena, start.per, start.mnav],
      [end.ena, end.per, end.mnav],
    );
    return {
      title: "StablecoinX share-price attribution",
      visual: {
        type: "waterfall",
        title: "What moved StablecoinX?",
        category: "STABLECOINX",
        description: "Share-price change, decomposed · USD per share",
        source: "Public filings / market data",
        caveat:
          "Shapley attribution is an accounting identity, not evidence of causation.",
        start: start.price,
        end: end.price,
        contributions: c,
        format: money,
        rows: [
          { d: start.date, t: start.t },
          { d: end.date, t: end.t },
        ],
      },
      updated: D.generated_at,
      period: start.date + " to " + end.date,
      subtitle:
        "USD per share · contributions allocated across ENA price, ENA per share, and mNAV",
      note: "Shapley decomposition of the recorded share-price change. Attribution is an accounting identity, not evidence of causation.",
      columns: ["component", "value_usd_per_share"],
      rows: [
        ["Starting share price", start.price],
        ["ENA price contribution", c[0]],
        ["ENA per share contribution", c[1]],
        ["mNAV contribution", c[2]],
        ["Ending share price", end.price],
      ],
      state: {
        mode: "history",
        range: state.attribRange,
        from: start.date,
        to: end.date,
      },
    };
  });
  headline();
  render();
  let resizeFrame;
  const sizes = new WeakMap();
  const observer = new ResizeObserver((entries) => {
    const changed = entries.some((e) => {
      const prev = sizes.get(e.target);
      sizes.set(e.target, e.contentRect.width);
      return prev !== undefined && prev !== e.contentRect.width;
    });
    if (!changed) return;
    cancelAnimationFrame(resizeFrame);
    resizeFrame = requestAnimationFrame(() => {
      if (state.mode === "explore") mapChart();
      else historyChart();
      detail();
      attribution();
    });
  });
  observer.observe(main);
  observer.observe($("#sx-detail-chart"));
  observer.observe($("#sx-waterfall"));
  return {
    update(next) {
      const follows =
        Math.abs(state.ena - base.ena) < 1e-8 &&
        Math.abs(state.mnav - base.mnav) < 1e-8;
      const atEnd = selected === rows.length - 1,
        day = rows[selected]?.date;
      D = next;
      S = D.series;
      rows = makeRows();
      base = Ethena.current(D);
      selected = atEnd
        ? rows.length - 1
        : Math.max(
            0,
            rows.findIndex((r) => r.date === day),
          );
      if (follows) {
        state.ena = base.ena;
        state.mnav = base.mnav;
      }
      headline();
      render();
    },
    redraw: render,
  };
};
