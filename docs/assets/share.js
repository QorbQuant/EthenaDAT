/* Shared chart-link and CSV utilities; browser-only exports load on demand. */
(function (scope) {
  const esc = (v) =>
    String(v ?? "").replace(
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
  const date = (v) =>
    /^\d{4}-\d{2}-\d{2}$/.test(v || "") &&
    Number.isFinite(Date.parse(v + "T00:00:00Z")) &&
    new Date(v + "T00:00:00Z").toISOString().slice(0, 10) === v
      ? v
      : null;
  function read(search) {
    const p = new URLSearchParams(search),
      one = (k, allowed) => (allowed.includes(p.get(k)) ? p.get(k) : undefined),
      n = (k, min, max) =>
        p.has(k) &&
        Number.isFinite(+p.get(k)) &&
        +p.get(k) >= min &&
        +p.get(k) <= max
          ? +p.get(k)
          : undefined;
    return {
      chart: /^[a-z][a-z0-9-]{0,60}$/.test(p.get("chart") || "")
        ? p.get("chart")
        : undefined,
      mode: one("mode", ["history", "explore"]),
      range: one("range", ["30", "90", "all"]),
      from: date(p.get("from")),
      to: date(p.get("to")),
      date: date(p.get("date")),
      ena: n("ena", 0.01, 2),
      mnav: n("mnav", 0.01, 3),
      view: one("view", ["spend", "count", "active"]),
      agg: one("agg", ["daily", "total"]),
      rewards: one("rewards", ["daily", "total"]),
      payoff: n("payoff", 0, 40),
      factor: one("factor", ["ena", "holdings", "multiple", "price"]),
    };
  }
  function windowRows(rows, from, to, key = "date") {
    const result = rows.filter(
      (q) => (!from || q[key] >= from) && (!to || q[key] <= to),
    );
    return result.length ? result : rows;
  }
  function url(path, state) {
    const u = new URL(path, "https://ethenadash.com");
    for (const [k, v] of Object.entries(state))
      if (v !== undefined && v !== null && v !== "")
        u.searchParams.set(k, String(v));
    if (state.chart) u.hash = state.chart;
    return u.href;
  }
  function cell(value) {
    if (value == null) return "";
    let v = String(value);
    if (typeof value === "string" && /^[\s]*[=+\-@]/.test(v)) v = "'" + v;
    return /[",\r\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
  }
  function csv(d) {
    const extra = ["source_updated_utc", "exported_utc", "view_url", "notes"];
    const now = new Date().toISOString();
    return (
      "\uFEFF" +
      [
        d.columns.concat(extra),
        ...d.rows.map((r) => r.concat([d.updated, now, d.url, d.note])),
      ]
        .map((r) => r.map(cell).join(","))
        .join("\r\n") +
      "\r\n"
    );
  }
  function isTimeSeries(d) {
    const v = d?.visual;
    return !!(v?.rows?.length && v.series && !v.xFormat &&
      !["scenario", "waterfall"].includes(v.type));
  }
  function prepareExport(d, options = {}, now = new Date()) {
    if (!isTimeSeries(d)) return d;
    const v = d.visual;
    const today = new Intl.DateTimeFormat("en-CA", {
      timeZone: v.timeZone || "UTC",
    }).format(now);
    const indices = v.rows.map((_, i) => i).filter((i) =>
      options.includeToday !== false || v.rows[i].d < today);
    if (!indices.length) throw Error("No earlier observations in this range. Include the current day or choose a wider range.");
    const rows = indices.map(i => v.rows[i]);
    const selected = rows.reduce((best, row) =>
      Math.abs(row.t - (v.selected ?? rows.at(-1).t)) <
      Math.abs(best.t - (v.selected ?? rows.at(-1).t)) ? row : best, rows[0]);
    return {
      ...d,
      rows: indices.map(i => d.rows[i]),
      state: { ...d.state, from: rows[0].d, to: rows.at(-1).d, date: selected.d },
      period: rows[0].d + " to " + rows.at(-1).d,
      subtitle: d.subtitle?.replace(/Selected: \d{4}-\d{2}-\d{2}/, "Selected: " + selected.d),
      note: d.note + (options.includeToday === false ? ` Current day excluded (${v.timeZone || "UTC"}).` : ""),
      visual: { ...v, rows, selected: selected.t, metricValues: null,
        series: v.series.map(s => ({ ...s, data: indices.map(i => s.data[i]) })),
        annotate: options.annotate === true,
        through: options.includeToday === false ? rows.at(-1).d : null,
      },
    };
  }
  const api = { read, windowRows, url, csv, esc, isTimeSeries, prepareExport };
  if (typeof module !== "undefined") module.exports = api;
  else {
    scope.ChartShare = api;
    api.initial = read(location.search);
    const registry = new Map();
    let exportModule;
    api.register = (id, get) => {
      registry.set(id, get);
      const svg = document.getElementById(id);
      if (!svg || document.querySelector('[data-export-for="' + id + '"]'))
        return;
      const menu = document.createElement("details");
      menu.className = "chart-tools";
      menu.dataset.exportFor = id;
      menu.innerHTML =
        '<summary aria-label="Share or export ' +
        esc(
          id === "sx-main-chart"
            ? "valuation workspace"
            : svg.getAttribute("aria-label") || "chart",
        ) +
        '">Share / export <span aria-hidden="true">↗</span></summary><div class="chart-tools-panel"><button type="button" data-export="link">Copy chart link</button><fieldset class="chart-export-options"><legend>Download options</legend><label><input type="checkbox" data-option="today" checked> Include current day</label><label><input type="checkbox" data-option="annotate"> Label highlighted value (PNG)</label><p data-option-help></p></fieldset><button type="button" data-export="png">Download PNG</button><button type="button" data-export="csv">Download CSV</button><p>Links restore this view. Source data may be revised.</p><span role="status" aria-live="polite"></span></div>';
      const slot = document.querySelector('[data-export-slot="' + id + '"]');
      if (slot) slot.replaceWith(menu);
      else svg.insertAdjacentElement("afterend", menu);
      menu.addEventListener("toggle", () => {
        if (!menu.open) return;
        const d = registry.get(id)();
        menu.querySelector(".chart-export-options").hidden = !isTimeSeries(d);
        menu.querySelector("[data-option-help]").textContent =
          `Day boundary: ${d?.visual?.timeZone === "America/New_York" ? "New York" : "UTC"}. Current-day data may be partial. Hover or tap a chart point before exporting to highlight it.`;
      });
      menu.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
          menu.open = false;
          menu.querySelector("summary").focus();
        }
      });
      menu.addEventListener("click", async (e) => {
        const button = e.target.closest("[data-export]");
        if (!button) return;
        const status = menu.querySelector("[role=status]");
        button.disabled = true;
        try {
          let d = registry.get(id)();
          if (!d || !d.rows.length)
            throw Error("No data available for this chart.");
          if (button.dataset.export !== "link") d = prepareExport(d, {
            includeToday: menu.querySelector('[data-option="today"]').checked,
            annotate: menu.querySelector('[data-option="annotate"]').checked,
          });
          d.url = url(location.pathname, { chart: id, ...d.state });
          if (button.dataset.export === "link") {
            try {
              await navigator.clipboard.writeText(d.url);
              status.textContent = "Chart link copied.";
            } catch {
              status.textContent = "Copy this link:";
              const input = document.createElement("input");
              input.value = d.url;
              input.readOnly = true;
              input.setAttribute("aria-label", "Chart link");
              status.append(input);
              input.select();
            }
          } else {
            exportModule ??= import("/assets/export.js?v=20261009-annotations").catch((error) => {
              exportModule = null;
              throw error;
            });
            const mod = await exportModule;
            await mod.download(button.dataset.export, svg, d, csv(d));
            status.textContent = "Download ready.";
          }
        } catch (error) {
          status.textContent =
            error.message || "Export unavailable. Please retry.";
        } finally {
          button.disabled = false;
        }
      });
    };
    api.reveal = () => {
      const id = api.initial.chart,
        svg = id && document.getElementById(id);
      if (!svg || svg.closest("[hidden]")) return;
      for (let p = svg.parentElement; p; p = p.parentElement)
        if (p.tagName === "DETAILS") p.open = true;
      svg.scrollIntoView({ block: "center" });
    };
  }
})(typeof window === "undefined" ? globalThis : window);
