/* A lazy, independent read-only market panel. Never changes the NAV model. */
(() => {
  const panel = document.getElementById("lighter-panel");
  if (!panel) return;
  const $ = (s) => panel.querySelector(s),
    d3 = window.d3;
  let data,
    visible = false,
    busy = false,
    failed = false,
    view = "price",
    hours = 24;
  const HOUR = 3600000,
    blue = "#8aa9cf",
    copper = "#cf9b79",
    muted = "#99a3b0";
  const money = (n) =>
    Number.isFinite(n)
      ? "$" +
        n.toLocaleString("en-US", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })
      : "—";
  const compact = (n) =>
    Number.isFinite(n)
      ? "$" +
        new Intl.NumberFormat("en-US", {
          notation: "compact",
          maximumFractionDigits: 1,
        }).format(n)
      : "—";
  const rate = (n) =>
    Number.isFinite(n)
      ? (n > 0 ? "+" : n < 0 ? "−" : "") + Math.abs(n).toFixed(4) + "%"
      : "—";
  const time = (t) =>
    new Date(t).toLocaleString("en-GB", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "UTC",
    }) + " UTC";
  let stock;
  try {
    const sx = JSON.parse(
      document.getElementById("dashboard-bootstrap")?.textContent || "null",
    )?.sx;
    if (sx?.series?.usde_close?.at(-1) > 0)
      stock = {
        price: sx.series.usde_close.at(-1),
        date: sx.series.date.at(-1),
      };
  } catch {}
  const payer = (r) =>
    r > 0
      ? "Longs pay shorts"
      : r < 0
      ? "Shorts pay longs"
      : "No funding payment";
  function status() {
    const stale =
      data &&
      (failed ||
        data.stale ||
        Date.now() - Date.parse(data.fetchedAt) > 120000);
    $("#lighter-status").textContent = data
      ? `${
          stale ? "Refresh delayed · showing last snapshot. " : ""
        }Source: Lighter · retrieved ${time(data.fetchedAt)}`
      : failed
      ? "Lighter is temporarily unavailable. Stock, warrant and options data remain available."
      : "Loading Lighter market data…";
    $("#lighter-status").classList.toggle("lighter-delayed", !!stale || failed);
  }
  function render() {
    status();
    if (!data) return;
    $("#lighter-mark").textContent = money(data.markPrice);
    $("#lighter-oi").textContent = compact(data.openInterestUsd);
    $("#lighter-volume").textContent = compact(data.volume24hUsd);
    if (stock) {
      const delta = (data.markPrice / stock.price - 1) * 100;
      $("#lighter-basis").textContent = `${delta >= 0 ? "+" : "−"}${Math.abs(
        delta,
      ).toFixed(2)}% vs recorded USDE ${money(stock.price)} · ${stock.date}`;
    }
    const f = data.latestFunding;
    $("#lighter-funding").textContent = f ? rate(f.ratePct) : "—";
    $("#lighter-payer").textContent = f
      ? `${payer(f.ratePct)} · ${time(f.t)}${
          data.historyDelayed?.funding || Date.now() - f.t > 2 * HOUR
            ? " · refresh delayed"
            : ""
        }`
      : "Funding history unavailable";
    draw();
  }
  function draw() {
    if (!d3 || !data) return;
    const funding = view === "funding",
      now = Date.parse(data.fetchedAt),
      start = now - hours * HOUR;
    const rows = (funding ? data.funding : data.prices).filter(
      (r) => r.t >= start && r.t <= now,
    );
    const svg = d3.select($("#lighter-chart")),
      width = Math.max(280, $("#lighter-chart").clientWidth),
      height = 260;
    svg.selectAll("*").remove();
    svg
      .attr("viewBox", `0 0 ${width} ${height}`)
      .attr("tabindex", "0")
      .attr(
        "aria-label",
        `${
          funding ? "Settled hourly funding" : "Hourly trade closing prices"
        } for StablecoinX on Lighter. Use left and right arrow keys to inspect observations.`,
      );
    $("#lighter-empty").hidden = rows.length > 0;
    $("#lighter-chart-note").textContent = funding
      ? "Hourly settled funding · copper: longs pay / blue: shorts pay · times in UTC."
      : "Hourly trade closes · times in UTC · latest candle may be partial.";
    if (data.historyDelayed?.[funding ? "funding" : "prices"])
      $("#lighter-chart-note").textContent += " History refresh delayed.";
    $("#lighter-readout").textContent = "";
    if (!rows.length) return;
    const left = funding ? 78 : 54,
      right = width - 12,
      bottom = height - 32;
    const x = d3.scaleUtc().domain([start, now]).range([left, right]);
    const value = (r) => (funding ? r.ratePct : r.close);
    let [low, high] = d3.extent(rows, value);
    if (funding) {
      low = Math.min(0, low);
      high = Math.max(0, high);
    }
    const pad = Math.max(
      (high - low) * 0.12,
      funding ? 0.0001 : Math.abs(high) * 0.002,
    );
    const y = d3
      .scaleLinear()
      .domain([low - pad, high + pad])
      .nice()
      .range([bottom, 16]);
    const axis = svg
      .append("g")
      .attr("transform", `translate(${left},0)`)
      .call(
        d3
          .axisLeft(y)
          .ticks(4)
          .tickSize(-(right - left))
          .tickFormat(
            funding
              ? (v) => `${v.toFixed(Math.abs(high - low) < 0.01 ? 4 : 2)}%`
              : (v) => "$" + v.toFixed(2),
          ),
      );
    axis.select(".domain").remove();
    axis.selectAll("line").attr("stroke", "#29313a");
    axis.selectAll("text").attr("dx", -8);
    const dates = svg
      .append("g")
      .attr("transform", `translate(0,${bottom})`)
      .call(
        d3
          .axisBottom(x)
          .ticks(width < 500 ? 3 : 6)
          .tickSize(0)
          .tickPadding(12)
          .tickFormat(d3.utcFormat(hours === 24 ? "%H:%M" : "%d %b")),
      );
    dates.select(".domain").remove();
    svg
      .selectAll("text")
      .attr("fill", muted)
      .attr("font-size", 11)
      .attr("font-family", "inherit");
    if (funding) {
      svg
        .append("line")
        .attr("x1", left)
        .attr("x2", right)
        .attr("y1", y(0))
        .attr("y2", y(0))
        .attr("stroke", muted)
        .attr("stroke-opacity", 0.5);
      const bar = Math.max(1, Math.min(12, ((right - left) / hours) * 0.65));
      svg
        .append("g")
        .selectAll("rect")
        .data(rows)
        .join("rect")
        .attr("x", (r) => x(r.t) - bar / 2)
        .attr("width", bar)
        .attr("y", (r) => Math.min(y(0), y(value(r))))
        .attr("height", (r) => Math.max(1, Math.abs(y(0) - y(value(r)))))
        .attr("fill", (r) => (value(r) < 0 ? blue : copper));
    } else {
      // Break at missing hourly observations instead of drawing across a gap.
      let segment = [];
      const line = d3
        .line()
        .x((r) => x(r.t))
        .y((r) => y(r.close));
      const flush = () => {
        if (segment.length)
          svg
            .append("path")
            .attr("d", line(segment))
            .attr("fill", "none")
            .attr("stroke", copper)
            .attr("stroke-width", 2);
      };
      for (const r of rows) {
        if (segment.length && r.t - segment.at(-1).t > 1.5 * HOUR) {
          flush();
          segment = [];
        }
        segment.push(r);
      }
      flush();
      svg
        .append("circle")
        .attr("cx", x(rows.at(-1).t))
        .attr("cy", y(rows.at(-1).close))
        .attr("r", 3)
        .attr("fill", copper);
    }
    const cursor = svg
      .append("line")
      .attr("y1", 16)
      .attr("y2", bottom)
      .attr("stroke", muted)
      .attr("stroke-dasharray", "3 4")
      .attr("opacity", 0);
    let selected = rows.length - 1;
    const inspect = (i) => {
      selected = Math.max(0, Math.min(rows.length - 1, i));
      const r = rows[selected];
      cursor.attr("x1", x(r.t)).attr("x2", x(r.t)).attr("opacity", 1);
      $("#lighter-readout").textContent = `${time(r.t)} · ${
        funding
          ? rate(r.ratePct) + " · " + payer(r.ratePct)
          : money(r.close) + " trade close"
      }`;
    };
    svg.on("pointermove", function (event) {
      const t = +x.invert(d3.pointer(event, this)[0]);
      inspect(d3.bisector((r) => r.t).center(rows, t));
    });
    svg.on("keydown", (event) => {
      if (["ArrowLeft", "ArrowRight"].includes(event.key)) {
        event.preventDefault();
        inspect(selected + (event.key === "ArrowRight" ? 1 : -1));
      }
    });
    inspect(selected);
  }
  async function refresh() {
    if (busy || !visible || document.hidden) return;
    busy = true;
    try {
      const r = await fetch("/api/lighter/stablecoinx", {
        signal: AbortSignal.timeout(8000),
        cache: "no-cache",
      });
      if (!r.ok) throw Error("Unavailable");
      const next = await r.json();
      if (
        next.symbol !== "STABLECOINX" ||
        !(next.markPrice > 0) ||
        !Number.isFinite(Date.parse(next.fetchedAt)) ||
        !Array.isArray(next.prices) ||
        !Array.isArray(next.funding)
      )
        throw Error("Invalid snapshot");
      if (data && Date.parse(next.fetchedAt) < Date.parse(data.fetchedAt))
        throw Error("Older snapshot");
      data = next;
      failed = false;
    } catch {
      failed = true;
    } finally {
      busy = false;
      render();
    }
  }
  panel
    .querySelectorAll("[data-lighter-view],[data-lighter-hours]")
    .forEach((button) =>
      button.addEventListener("click", () => {
        if (button.dataset.lighterView) view = button.dataset.lighterView;
        else hours = Number(button.dataset.lighterHours);
        panel
          .querySelectorAll("[data-lighter-view]")
          .forEach((b) =>
            b.setAttribute(
              "aria-pressed",
              String(b.dataset.lighterView === view),
            ),
          );
        panel
          .querySelectorAll("[data-lighter-hours]")
          .forEach((b) =>
            b.setAttribute(
              "aria-pressed",
              String(Number(b.dataset.lighterHours) === hours),
            ),
          );
        draw();
      }),
    );
  new IntersectionObserver(
    (entries) => {
      visible = entries[0].isIntersecting;
      if (visible) {
        render();
        refresh();
      }
    },
    { rootMargin: "200px" },
  ).observe(panel);
  new ResizeObserver(() => draw()).observe($("#lighter-chart"));
  setInterval(() => {
    status();
    refresh();
  }, 60000);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) refresh();
  });
})();
