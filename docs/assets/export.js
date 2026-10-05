const escape = (v) =>
  String(v ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
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
function wrap(text, max = 105) {
  const lines = [];
  let line = "";
  for (const word of text.split(/\s+/)) {
    if ((line + " " + word).length > max) {
      lines.push(line);
      line = word;
    } else line += (line ? " " : "") + word;
  }
  if (line) lines.push(line);
  return lines;
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
  const clone = svg.cloneNode(true),
    originals = [svg, ...svg.querySelectorAll("*")],
    copies = [clone, ...clone.querySelectorAll("*")];
  // SVG styles normally inherit from the dashboard. Inline them for a portable image.
  originals.forEach((node, i) => {
    const s = getComputedStyle(node);
    for (const k of [
      "fill",
      "stroke",
      "stroke-width",
      "stroke-dasharray",
      "paint-order",
      "stroke-linejoin",
      "stroke-linecap",
      "font-family",
      "font-size",
      "font-weight",
      "opacity",
      "fill-opacity",
      "stroke-opacity",
      "text-anchor",
      "dominant-baseline",
    ])
      copies[i].style.setProperty(k, s.getPropertyValue(k));
  });
  clone.querySelectorAll("[data-chart-hit]").forEach((n) => n.remove());
  clone.setAttribute("x", "40");
  clone.setAttribute("y", "155");
  clone.setAttribute("width", "1520");
  clone.setAttribute("height", "580");
  clone.setAttribute("preserveAspectRatio", "xMidYMid meet");
  clone.removeAttribute("class");
  clone.style.overflow = "visible";
  clone.style.width = "1520px";
  clone.style.height = "580px";
  const lines = [
    ...wrap(d.subtitle || ""),
    ...wrap(d.note || ""),
    "Source updated: " +
      (d.updated || "unavailable") +
      " · Exported: " +
      new Date().toISOString(),
    "EthenaDash · ethenadash.com" +
      location.pathname +
      " · Methodology: ethenadash.com/methodology/",
  ];
  const h = 820 + lines.length * 25,
    xml =
      '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="' +
      h +
      '" viewBox="0 0 1600 ' +
      h +
      '"><rect width="1600" height="' +
      h +
      '" fill="#0d1116"/><g font-family="Arial,sans-serif"><text x="48" y="50" font-size="17" fill="#cf9b79">ETHENADASH / ' +
      escape(d.kind || "RECORDED DATA") +
      '</text><text x="48" y="100" font-size="32" fill="#eeeae3">' +
      escape(d.title) +
      '</text><text x="48" y="135" font-size="18" fill="#99a3b0">' +
      escape(d.period || "") +
      "</text>" +
      new XMLSerializer().serializeToString(clone) +
      lines
        .map(
          (line, i) =>
            '<text x="48" y="' +
            (785 + i * 25) +
            '" font-size="18" fill="#99a3b0">' +
            escape(line) +
            "</text>",
        )
        .join("") +
      "</g></svg>";
  const imageURL = URL.createObjectURL(
    new Blob([xml], { type: "image/svg+xml;charset=utf-8" }),
  );
  try {
    const image = new Image();
    await new Promise((resolve, reject) => {
      image.onload = resolve;
      image.onerror = () => reject(Error("Could not render the chart image."));
      image.src = imageURL;
    });
    const canvas = document.createElement("canvas");
    canvas.width = 1600;
    canvas.height = h;
    canvas.getContext("2d").drawImage(image, 0, 0);
    const blob = await new Promise((resolve) =>
      canvas.toBlob(resolve, "image/png"),
    );
    if (!blob) throw Error("Image download unavailable.");
    save(blob, name + ".png");
  } finally {
    URL.revokeObjectURL(imageURL);
  }
}
