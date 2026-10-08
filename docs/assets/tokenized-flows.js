import { validFlows, flowWindow } from "./tokenized-flow-model.mjs";
const panel = document.getElementById("tokenized-flows");
if (panel) {
  const $ = (id) => document.getElementById(id),
    d3 = window.d3;
  let data,
    range = "7d",
    visible = false,
    busy = false,
    failed = false,
    focusIndex = 0;
  const format = (n) => n.toLocaleString("en-US", { maximumFractionDigits: 2 });
  const signed = (n) => (n > 0 ? "+" : n < 0 ? "−" : "") + format(Math.abs(n));
  const stamp = (t) =>
    new Date(t).toLocaleString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "UTC",
    }) + " UTC";
  const day = (t) =>
    new Date(t).toLocaleDateString("en-GB", {
      day: "numeric",
      month: "short",
      timeZone: "UTC",
    });
  function render() {
    const delayed =
      data &&
      (failed ||
        data.stale ||
        Date.now() - Date.parse(data.observedAt) > 36 * 3600000);
    $("tokenized-flow-status").textContent = data
      ? `${
          delayed ? "Refresh delayed · " : ""
        }Source: Dune / BNB Chain · through ${stamp(
          Date.parse(data.observedAt),
        )} · reconciled to on-chain supply.`
      : failed
      ? "Supply-flow history is temporarily unavailable."
      : "Loading verified supply history…";
    $("tokenized-flow-status").classList.toggle(
      "lighter-delayed",
      !!delayed || failed,
    );
    if (!data) return;
    const w = flowWindow(data, range);
    $("tokenized-minted").textContent = format(w.minted);
    $("tokenized-burned").textContent = format(w.burned);
    $("tokenized-net").textContent = signed(w.net);
    $("tokenized-period").textContent =
      range === "all"
        ? "Since contract deployment"
        : range === "24h"
        ? "24 hours ending at the snapshot"
        : "7 days ending at the snapshot";
    $("tokenized-flow-note").textContent =
      "Raw USDEB units · blue: minted / copper: burned · UTC days · boundary days may be partial.";
    $("tokenized-adjustments").textContent = data.adjustments.length
      ? `${data.adjustments.length} multiplier scheduling event(s) recorded separately. These do not enter the mint/burn totals.`
      : "No multiplier changes after initialization are recorded in this snapshot.";
    const body = $("tokenized-flow-table");
    body.replaceChildren();
    for (const r of [...w.rows].reverse()) {
      const tr = document.createElement("tr");
      for (const text of [
        day(r.t) + (r.partial ? " (partial)" : ""),
        format(r.minted),
        format(r.burned),
        signed(r.net),
      ]) {
        const td = document.createElement("td");
        td.textContent = text;
        tr.append(td);
      }
      body.append(tr);
    }
    draw(w);
  }
  function draw(w) {
    if (!d3) return;
    const svg = d3.select($("tokenized-flow-chart")),
      width = Math.max(280, $("tokenized-flow-chart").clientWidth),
      height = 280;
    const left = 62,
      right = width - 12,
      bottom = height - 36;
    svg.selectAll("*").remove();
    svg.attr("viewBox", `0 0 ${width} ${height}`);
    const x = d3
      .scaleBand()
      .domain(w.rows.map((r) => r.t))
      .range([left, right])
      .padding(0.3);
    const maxMint = Math.max(...w.rows.map((r) => r.minted), 0),
      maxBurn = Math.max(...w.rows.map((r) => r.burned), 0);
    const pad = Math.max(maxMint, maxBurn, 1) * 0.12;
    const y = d3
      .scaleLinear()
      .domain([-maxBurn - pad, maxMint + pad])
      .nice()
      .range([bottom, 16]);
    const axis = svg
      .append("g")
      .attr("transform", `translate(${left},0)`)
      .call(
        d3
          .axisLeft(y)
          .ticks(5)
          .tickSize(-(right - left))
          .tickFormat(d3.format("~s")),
      );
    axis.select(".domain").remove();
    axis.selectAll("line").attr("stroke", "#29313a");
    axis.selectAll("text").attr("dx", -8);
    const tickCount = width < 500 ? 3 : 7,
      step = Math.max(1, Math.ceil(w.rows.length / tickCount));
    const ticks = w.rows.filter((_, i) => i % step === 0).map((r) => r.t);
    const dates = svg
      .append("g")
      .attr("transform", `translate(0,${bottom})`)
      .call(
        d3
          .axisBottom(x)
          .tickValues(ticks)
          .tickSize(0)
          .tickPadding(12)
          .tickFormat(day),
      );
    dates.select(".domain").remove();
    svg
      .selectAll("text")
      .attr("fill", "#99a3b0")
      .attr("font-size", 11)
      .attr("font-family", "inherit");
    svg
      .append("line")
      .attr("x1", left)
      .attr("x2", right)
      .attr("y1", y(0))
      .attr("y2", y(0))
      .attr("stroke", "#788390");
    const barWidth = Math.min(58, x.bandwidth());
    for (const r of w.rows) {
      const position = x(r.t) + (x.bandwidth() - barWidth) / 2;
      svg
        .append("rect")
        .attr("x", position)
        .attr("y", y(r.minted))
        .attr("width", barWidth)
        .attr("height", y(0) - y(r.minted))
        .attr("fill", "#8aa9cf");
      svg
        .append("rect")
        .attr("x", position)
        .attr("y", y(0))
        .attr("width", barWidth)
        .attr("height", y(-r.burned) - y(0))
        .attr("fill", "#cf9b79");
    }
    const highlight = svg
      .append("rect")
      .attr("y", 8)
      .attr("height", bottom - 8)
      .attr("fill", "#ffffff")
      .attr("opacity", 0.035)
      .attr("pointer-events", "none");
    function inspect(index) {
      focusIndex = Math.max(0, Math.min(w.rows.length - 1, index));
      const r = w.rows[focusIndex];
      highlight.attr("x", x(r.t) - 4).attr("width", x.bandwidth() + 8);
      $("tokenized-flow-readout").textContent = `${day(r.t)}${
        r.partial ? " (partial)" : ""
      } · Minted ${format(r.minted)} · Burned ${format(
        r.burned,
      )} · Net ${signed(r.net)} USDEB`;
    }
    w.rows.forEach((r, i) =>
      svg
        .append("rect")
        .attr("x", x(r.t) - 4)
        .attr("y", 8)
        .attr("width", x.bandwidth() + 8)
        .attr("height", bottom - 8)
        .attr("fill", "transparent")
        .on("pointerenter", () => inspect(i))
        .on("click", () => inspect(i)),
    );
    svg.on("keydown", (event) => {
      if (["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) {
        event.preventDefault();
        inspect(
          event.key === "Home"
            ? 0
            : event.key === "End"
            ? w.rows.length - 1
            : focusIndex + (event.key === "ArrowRight" ? 1 : -1),
        );
      }
    });
    inspect(w.rows.length - 1);
    $("tokenized-flow-empty").hidden = w.minted !== 0 || w.burned !== 0;
  }
  async function refresh() {
    if (busy || !visible || document.hidden) return;
    busy = true;
    try {
      const r = await fetch("/api/tokenized/stablecoinx/flows", {
        signal: AbortSignal.timeout(12000),
      });
      if (!r.ok) throw Error();
      const next = await r.json();
      if (!validFlows(next)) throw Error();
      data = next;
      failed = false;
    } catch {
      failed = true;
    } finally {
      busy = false;
      render();
    }
  }
  panel.querySelectorAll("[data-flow-range]").forEach((button) =>
    button.addEventListener("click", () => {
      range = button.dataset.flowRange;
      panel.querySelectorAll("[data-flow-range]").forEach((b) => {
        b.classList.toggle("active", b === button);
        b.setAttribute("aria-pressed", String(b === button));
      });
      render();
    }),
  );
  new IntersectionObserver(
    (entries) => {
      visible = entries[0].isIntersecting;
      if (visible) refresh();
    },
    { rootMargin: "240px" },
  ).observe(panel);
  new ResizeObserver(() => {
    if (data) draw(flowWindow(data, range));
  }).observe($("tokenized-flow-chart"));
  setInterval(refresh, 300000);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
      render();
      refresh();
    }
  });
}
