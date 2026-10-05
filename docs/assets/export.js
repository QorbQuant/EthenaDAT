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
  H = 900;
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
    ? dateLabel(d) + " " + d.toISOString().slice(11, 16) + " UTC"
    : "Unavailable";
}
const safeFormat = (f, v) => (Number.isFinite(v) ? f(v) : "—");
function metric(x, label, value, color = C.text, suffix = "") {
  return (
    circle(x + 5, 211, color, 5) +
    text(x + 22, 219, label, 25, C.muted) +
    text(x, 283, value, 60, color, 'font-weight="600" letter-spacing="-2"') +
    (suffix ? text(x + 2, 314, suffix, 20, C.muted) : "")
  );
}
function context(label, value) {
  return (
    text(
      1536,
      218,
      label,
      18,
      C.muted,
      'text-anchor="end" letter-spacing="2"',
    ) + text(1536, 263, value, 29, C.text, 'text-anchor="end"')
  );
}
const bounds = { l: 156, r: 1536, t: 371, b: 738 };
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
        785,
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
      }" fill="none" stroke="${color}" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>`;
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
  // Metrics always refer to the selected observation, never a silently substituted last value.
  out += v.series
    .map((s, k) =>
      metric(
        64 + k * 490,
        s.name,
        safeFormat(v.metricFormat || v.format, selectedValues[k]),
        s.color || [C.blue, C.copper][k % 2],
        v.metricSuffix,
      ),
    )
    .join("");
  out += context(
    v.contextLabel || "OBSERVATION",
    v.xFormat ? (v.contextFormat || v.xFormat)(selectedX) : dateLabel(q.t),
  );
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
    out += text(x, 785, q.name, 23, C.muted, 'text-anchor="middle"');
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
  out += metric(
    64,
    "Share-price change",
    (v.end >= v.start ? "+" : "−") + v.format(Math.abs(v.end - v.start)),
    C.copper,
  );
  out += metric(
    554,
    "Price return",
    (v.end >= v.start ? "+" : "") +
      ((v.end / v.start - 1) * 100).toFixed(1) +
      "%",
    C.text,
  );
  return out + context("PERIOD END", dateLabel(v.rows.at(-1).t));
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
      785,
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
  out += metric(
    64,
    "Implied share price",
    "$" + (s.ena * s.per * s.mnav).toFixed(2),
    C.copper,
  );
  out +=
    text(554, 219, "SCENARIO INPUTS", 20, C.muted, 'letter-spacing="1"') +
    text(
      554,
      274,
      "ENA $" + s.ena.toFixed(4) + "  /  " + s.mnav.toFixed(3) + "× mNAV",
      34,
      C.text,
    );
  return (
    out +
    text(
      1536,
      332,
      "X: ENA price (USD)   ·   Y: mNAV",
      20,
      C.muted,
      'text-anchor="end"',
    )
  );
}
export function renderCard(d, d3) {
  const v = d.visual;
  if (!v || !d3) throw Error("Chart export unavailable. Reload and try again.");
  const title = v.title || d.title;
  const period =
    v.type === "scenario"
      ? ""
      : v.xFormat
        ? "Terminal stock price: $0–$40"
        : dateLabel(v.rows[0].t) + " — " + dateLabel(v.rows.at(-1).t);
  const description = v.description + (period ? "  ·  " + period : "");
  let body =
    text(
      64,
      57,
      "ethenadash",
      28,
      C.text,
      'font-weight="700" letter-spacing="-1"',
    ) +
    text(
      1536,
      57,
      v.category,
      19,
      C.copper,
      'text-anchor="end" letter-spacing="2"',
    );
  body += text(
    64,
    127,
    title,
    title.length > 43 ? 46 : 54,
    C.text,
    'font-weight="600" letter-spacing="-1.5"',
  );
  body += text(
    64,
    167,
    description,
    description.length > 110 ? 20 : 23,
    C.muted,
  );
  body += line(64, 338, 1536, 338, C.grid);
  body +=
    v.type === "scenario"
      ? scenario(v, d3)
      : v.type === "waterfall"
        ? waterfall(v, d3)
        : seriesPlot(v, d3);
  body += line(64, 818, 1536, 818, C.grid);
  body += text(64, 849, v.caveat, 19, C.muted);
  body += text(
    64,
    878,
    "Source: " + v.source + " · Updated " + sourceStamp(d.updated),
    18,
    C.muted,
  );
  body += text(
    1536,
    856,
    "ethenadash.com",
    26,
    C.text,
    'text-anchor="end" font-weight="600"',
  );
  body += text(
    1536,
    881,
    "Charts & methodology",
    17,
    C.muted,
    'text-anchor="end"',
  );
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><title>${esc(title)}</title><desc>${esc(d.subtitle + " " + d.note + " View: " + d.url)}</desc><rect width="${W}" height="${H}" fill="${C.bg}"/><g font-family="Arial,Helvetica,sans-serif">${body}</g></svg>`;
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
    canvas.width = W;
    canvas.height = H;
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
