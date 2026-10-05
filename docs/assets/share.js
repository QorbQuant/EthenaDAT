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
  const api = { read, windowRows, url, csv, esc };
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
        '">Share / export <span aria-hidden="true">↗</span></summary><div class="chart-tools-panel"><button type="button" data-export="link">Copy chart link</button><button type="button" data-export="png">Download PNG</button><button type="button" data-export="csv">Download CSV</button><p>Links restore this view. Source data may be revised.</p><span role="status" aria-live="polite"></span></div>';
      const slot = document.querySelector('[data-export-slot="' + id + '"]');
      if (slot) slot.replaceWith(menu);
      else svg.insertAdjacentElement("afterend", menu);
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
          const d = registry.get(id)();
          if (!d || !d.rows.length)
            throw Error("No data available for this chart.");
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
            exportModule ??= import("/assets/export.js").catch((error) => {
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
