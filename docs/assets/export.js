// Re-render exports from plotted data, independent of the dashboard's viewport.
const esc = (v) =>
  String(v ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const C = {
  bg: "#0d1116",
  text: "#eeeae3",
  muted: "#9da9b7",
  grid: "#29323e",
  blue: "#8aa9cf",
  copper: "#cf9b79",
};
const W = 1600,
  H = 900,
  SCALE = 2;
const text = (x, y, value, size = 24, color = C.text, extra = "") =>
  `<text x="${x}" y="${y}" font-size="${size}" fill="${color}" ${extra}>${esc(value)}</text>`;
const line = (x1, y1, x2, y2, color = C.grid, extra = "") =>
  `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" ${extra}/>`;
const circle = (x, y, color, r = 6) =>
  `<circle cx="${x}" cy="${y}" r="${r}" fill="${color}" stroke="${C.bg}" stroke-width="3"/>`;
function dateLabel(value, year = true) {
  const date = new Date(value);
  return Number.isFinite(date.getTime())
    ? date.toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        ...(year ? { year: "numeric" } : {}),
        timeZone: "UTC",
      })
    : "Unavailable";
}
function sourceStamp(value) {
  const d = new Date(value);
  return Number.isFinite(d.getTime())
    ? d.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        timeZone: "UTC",
      })
    : "Unavailable";
}
const safeFormat = (f, v) => (Number.isFinite(v) ? f(v) : "N/A");
const bounds = { l: 156, r: 1536, t: 185, b: 760 };
function axes(y, fmt) {
  const { l, r } = bounds;
  return y
    .ticks(4)
    .map(
      (v) =>
        line(l, y(v), r, y(v), C.grid, 'stroke-width="1.4"') +
        text(
          l - 24,
          y(v) + 8,
          safeFormat(fmt, v),
          25,
          C.muted,
          'text-anchor="end"',
        ),
    )
    .join("");
}
function nearest(rows, value) {
  return rows.reduce(
    (best, r, i) =>
      Math.abs(r.t - value) < Math.abs(rows[best].t - value) ? i : best,
    0,
  );
}
function seriesPlot(v, d3) {
  const { l, r, t, b } = bounds,
    values = v.series.flatMap((s) => s.data.filter(Number.isFinite));
  if (!values.length || !v.rows.length)
    throw Error("No observations available to export.");
  const [lo, hi] = d3.extent(values),
    pad = (hi - lo) * 0.05 || Math.abs(hi) * 0.05 || 1;
  const y = d3
    .scaleLinear()
    .domain(
      v.zero === false
        ? [lo - pad, hi + pad]
        : [Math.min(0, lo), Math.max(0, hi) + pad],
    )
    .nice(4)
    .range([b, t]);
  const x = d3
    .scaleLinear()
    .domain(d3.extent(v.rows, (q) => q.t))
    .range([l + 8, r - 8]);
  const selected = nearest(v.rows, v.selected ?? v.rows.at(-1).t),
    q = v.rows[selected],
    selectedX = v.xFormat ? (v.selected ?? q.t) : q.t,
    selectedValues = v.metricValues ?? v.series.map((s) => s.data[selected]);
  let out = axes(y, v.axisFormat);
  const tickIndices = [
    ...new Set(
      Array.from({ length: 4 }, (_, i) =>
        Math.round(((v.rows.length - 1) * i) / 3),
      ),
    ),
  ];
  out += tickIndices
    .map((i, k) =>
      text(
        x(v.rows[i].t),
        803,
        v.xFormat ? v.xFormat(v.rows[i].t) : dateLabel(v.rows[i].t, false),
        25,
        C.muted,
        `text-anchor="${tickIndices.length === 1 ? "middle" : k === 0 ? "start" : k === tickIndices.length - 1 ? "end" : "middle"}"`,
      ),
    )
    .join("");
  out += `<defs><clipPath id="plot-clip"><rect x="${l}" y="${t - 10}" width="${r - l}" height="${b - t + 20}"/></clipPath></defs><g clip-path="url(#plot-clip)">`;
  v.series.forEach((s, k) => {
    const color = s.color || [C.blue, C.copper][k % 2],
      points = v.rows.map((row, i) => ({ x: x(row.t), value: s.data[i] }));
    if (s.kind === "bar") {
      const bw = Math.max(2, Math.min(28, ((r - l) / v.rows.length) * 0.68));
      out += points
        .filter((p) => Number.isFinite(p.value))
        .map(
          (p) =>
            `<rect x="${p.x - bw / 2}" y="${Math.min(y(0), y(p.value))}" width="${bw}" height="${Math.max(1, Math.abs(y(p.value) - y(0)))}" fill="${color}" opacity=".85"/>`,
        )
        .join("");
    } else {
      if (s.fill)
        out += `<path d="${
          d3
            .area()
            .defined((p) => Number.isFinite(p.value))
            .x((p) => p.x)
            .y0(y(0))
            .y1((p) => y(p.value))(points) || ""
        }" fill="${color}" opacity=".07"/>`;
      out += `<path d="${
        d3
          .line()
          .defined((p) => Number.isFinite(p.value))
          .x((p) => p.x)
          .y((p) => y(p.value))(points) || ""
      }" fill="none" stroke="${color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`;
    }
  });
  out += line(
    x(selectedX),
    t,
    x(selectedX),
    b,
    "#667585",
    'stroke-dasharray="5 7" stroke-width="1.5"',
  );
  v.series.forEach((s, k) => {
    if (Number.isFinite(selectedValues[k]))
      out += circle(
        x(selectedX),
        y(selectedValues[k]),
        s.color || [C.blue, C.copper][k % 2],
        7,
      );
  });
  out += "</g>";
  if (v.annotate) {
    const labels = v.series.flatMap((s, k) => {
      const value = selectedValues[k];
      if (!Number.isFinite(value)) return [];
      const formatted = (v.annotationFormat || v.format || String)(value);
      return [{ k, color: s.color || [C.blue, C.copper][k % 2],
        label: (v.series.length > 1 ? s.name + " · " : "") + formatted,
        px: x(selectedX), py: y(value) }];
    }).sort((a, b) => a.py - b.py);
    labels.forEach((a, i) => {
      a.ly = Math.max(t + 28, Math.min(b - 28, a.py - 65));
      if (i) a.ly = Math.max(a.ly, labels[i - 1].ly + 68);
    });
    if (labels.length && labels.at(-1).ly > b - 28) {
      const shift = labels.at(-1).ly - (b - 28);
      labels.forEach(a => a.ly -= shift);
    }
    for (const a of labels) {
      const size = v.series.length > 1 ? 24 : 32;
      const width = Math.min(650, Math.max(90, a.label.length * size * 0.62 + 30));
      const left = a.px > (l + r) / 2;
      const bx = left ? Math.max(l + 8, a.px - width - 75) : Math.min(r - width - 8, a.px + 75);
      const ax = left ? bx + width : bx, ay = a.ly;
      const distance = Math.hypot(a.px - ax, a.py - ay) || 1;
      const ex = a.px - (a.px - ax) / distance * 13;
      const ey = a.py - (a.py - ay) / distance * 13;
      out += `<g class="export-annotation"><defs><marker id="arrow-${a.k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M 1 1 L 9 5 L 1 9" fill="none" stroke="${a.color}" stroke-width="1.5"/></marker></defs>`;
      out += line(ax, ay, ex, ey, a.color, `stroke-width="2" marker-end="url(#arrow-${a.k})"`);
      out += `<rect x="${bx}" y="${a.ly - 25}" width="${width}" height="50" rx="4" fill="${C.bg}" fill-opacity=".94"/>`;
      out += text(bx + width / 2, a.ly + size * 0.34, a.label, size, a.color, 'text-anchor="middle" font-weight="600"');
      out += "</g>";
    }
  }
  return out;
}
function waterfall(v, d3) {
  const { l, r, t, b } = bounds;
  let last = v.start;
  const bars = [
    { name: "Start", from: 0, to: last, color: C.muted, value: last },
  ];
  ["ENA price", "ENA per share", "mNAV"].forEach((name, i) => {
    bars.push({
      name,
      from: last,
      to: last + v.contributions[i],
      value: v.contributions[i],
      color: v.contributions[i] < 0 ? C.copper : C.blue,
    });
    last += v.contributions[i];
  });
  bars.push({ name: "End", from: 0, to: v.end, value: v.end, color: C.text });
  const values = bars.flatMap((q) => [q.from, q.to]),
    max = Math.max(...values),
    min = Math.min(0, ...values),
    pad = (max - min) * 0.15 || 1;
  const y = d3
      .scaleLinear()
      .domain([min, max + pad])
      .nice(4)
      .range([b, t]),
    slot = (r - l) / 5,
    bw = 94;
  let out = axes(y, v.format);
  bars.forEach((q, i) => {
    const x = l + slot * (i + 0.5);
    out += `<rect x="${x - bw / 2}" y="${Math.min(y(q.from), y(q.to))}" width="${bw}" height="${Math.max(2, Math.abs(y(q.to) - y(q.from)))}" fill="${q.color}" rx="2"/>`;
    out += text(
      x,
      Math.min(y(q.from), y(q.to)) - 15,
      (i > 0 && i < 4 ? (q.value >= 0 ? "+" : "−") : "") +
        v.format(Math.abs(q.value)),
      26,
      q.color,
      'text-anchor="middle"',
    );
    out += text(x, 803, q.name, 23, C.muted, 'text-anchor="middle"');
    if (i < 4)
      out += line(
        x + bw / 2,
        y(q.to),
        x + slot - bw / 2,
        y(q.to),
        C.grid,
        'stroke-dasharray="4 6"',
      );
  });
  return out;
}
function scenario(v, d3) {
  const s = v.scenario,
    { l, r, t, b } = bounds;
  const x = d3
    .scaleLinear()
    .domain([Math.min(0.05, s.ena * 0.8), Math.max(0.6, s.ena * 1.08)])
    .range([l, r]);
  const y = d3
    .scaleLinear()
    .domain([Math.min(0.1, s.mnav * 0.8), Math.max(1.2, s.mnav * 1.08)])
    .range([b, t]);
  let out = axes(y, (n) => n.toFixed(2) + "×");
  x.ticks(5).forEach((n) => {
    out += text(
      x(n),
      803,
      "$" + n.toFixed(2),
      25,
      C.muted,
      'text-anchor="middle"',
    );
  });
  for (const price of [5, 10, 15, 20, 30, 40, 60, 90, 150, 250, 500]) {
    const points = Array.from({ length: 201 }, (_, i) => {
      const e = x.domain()[0] + ((x.domain()[1] - x.domain()[0]) * i) / 200;
      return [x(e), price / (s.per * e)];
    }).filter((p) => p[1] >= y.domain()[0] && p[1] <= y.domain()[1]);
    if (points.length < 2) continue;
    out += `<path d="${d3
      .line()
      .x((p) => p[0])
      .y((p) => y(p[1]))(
      points,
    )}" fill="none" stroke="${C.blue}" stroke-opacity=".48" stroke-width="2"/>`;
    const p = points[Math.floor((points.length - 1) * 0.85)];
    out += text(
      p[0],
      y(p[1]) - 9,
      "$" + price,
      22,
      C.blue,
      `text-anchor="middle" stroke="${C.bg}" stroke-width="7" paint-order="stroke"`,
    );
  }
  out +=
    line(x(s.ena), t, x(s.ena), b, C.copper, 'stroke-dasharray="5 7"') +
    line(l, y(s.mnav), r, y(s.mnav), C.copper, 'stroke-dasharray="5 7"') +
    circle(x(s.ena), y(s.mnav), C.copper, 9);
  if (
    s.currentEna >= x.domain()[0] &&
    s.currentEna <= x.domain()[1] &&
    s.currentMnav >= y.domain()[0] &&
    s.currentMnav <= y.domain()[1]
  )
    out +=
      circle(x(s.currentEna), y(s.currentMnav), C.blue, 7) +
      text(x(s.currentEna) + 15, y(s.currentMnav) - 15, "Current", 20, C.blue);
  return out;
}
export function renderCard(d, d3) {
  const v = d.visual;
  if (!v || !d3) throw Error("Chart export unavailable. Reload and try again.");
  const title =
    v.type === "scenario"
      ? "StablecoinX valuation scenario"
      : v.title || d.title;
  let body = text(
    64,
    96,
    title,
    title.length > 43 ? 44 : 50,
    C.text,
    'font-weight="600" letter-spacing="-1"',
  );
  // A key identifies multiple plotted series without adding a second headline.
  if (v.type !== "scenario" && v.type !== "waterfall" && v.series.length > 1) {
    let x = 66;
    for (const [k, s] of v.series.entries()) {
      const color = s.color || [C.blue, C.copper][k % 2];
      body +=
        line(x, 140, x + 28, 140, color, 'stroke-width="3"') +
        text(x + 40, 148, s.name, 23, C.muted);
      x += 100 + s.name.length * 14;
    }
  }
  body +=
    v.type === "scenario"
      ? scenario(v, d3)
      : v.type === "waterfall"
        ? waterfall(v, d3)
        : seriesPlot(v, d3);
  let explanation =
    v.type === "scenario"
      ? "Scenario, not a forecast · X: ENA (USD), Y: mNAV"
      : v.xFormat
        ? "Hypothetical expiry value per $1 invested"
        : v.metricSuffix === "since listing"
          ? "Jun 26, 2026 = 100"
          : v.unit === "USDe"
            ? "USDe"
            : v.unit === "USD at payout-day AVAX price"
              ? "USD at payout-day prices"
              : "";
  const footer =
    "Source: ethenadash.com / " +
    v.source.replaceAll(" / ", ", ") +
    " · As of " +
    sourceStamp(v.through || d.updated) +
    (explanation ? " · " + explanation : "");
  body += text(64, 865, footer, footer.length > 145 ? 17 : 20, C.muted);
  // Intrinsic SVG and canvas dimensions both use 2x resolution: no bitmap upscaling.
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W * SCALE}" height="${H * SCALE}" viewBox="0 0 ${W} ${H}"><title>${esc(title)}</title><desc>${esc(d.subtitle + " " + d.note + " View: " + d.url)}</desc><rect width="${W}" height="${H}" fill="${C.bg}"/><g font-family="Arial,Helvetica,sans-serif">${body}</g></svg>`;
}

function save(blob, name) {
  const href = URL.createObjectURL(blob),
    a = document.createElement("a");
  a.href = href;
  a.download = name;
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(href), 10000);
}
export async function download(type, svg, d, csv) {
  const name =
    "ethenadash-" +
    svg.id +
    "-" +
    (d.state.to || new Date().toISOString().slice(0, 10));
  if (type === "csv") {
    save(new Blob([csv], { type: "text/csv;charset=utf-8" }), name + ".csv");
    return;
  }
  const xml = renderCard(d, globalThis.d3),
    url = URL.createObjectURL(
      new Blob([xml], { type: "image/svg+xml;charset=utf-8" }),
    );
  try {
    const img = new Image();
    await new Promise((resolve, reject) => {
      img.onload = resolve;
      img.onerror = () => reject(Error("Could not render the share image."));
      img.src = url;
    });
    const canvas = document.createElement("canvas");
    canvas.width = W * SCALE;
    canvas.height = H * SCALE;
    canvas.getContext("2d").drawImage(img, 0, 0);
    const blob = await new Promise((resolve) =>
      canvas.toBlob(resolve, "image/png"),
    );
    if (!blob) throw Error("Image download unavailable.");
    save(blob, name + ".png");
  } finally {
    URL.revokeObjectURL(url);
  }
}
