// Two additions to sec_window_search.js. First, it lists every filing each company made in its search window,
// including the forms that script skips, with the 8-K item numbers from EDGAR's submissions data. Second, it reads the
// text of the PDFs that script could not search. It inflates each compressed stream of the PDF in the browser, joins
// the text the page drawing commands show, and records the latest full date in the text, how often the token appears
// and every sentence that says the company holds a number of tokens.
//
// Paste into the developer console on any page of https://www.sec.gov/ . Read-only GET requests, no login.
// Results in window.__wx.
window.__wxRun = (async () => {
  // ticker, CIK, token, first day of the search window
  const COMPANIES = [
    ["USDE", "0002080215", "ENA", "2026-06-25"],
    ["MSTR", "0001050446", "BTC", "2026-09-25"],
    ["ASST", "0001920406", "BTC", "2026-10-02"],
    ["FWDI", "0000038264", "SOL", "2026-09-30"],
    ["HYPD", "0001682639", "HYPE", "2026-06-30"],
    ["BMNR", "0001829311", "ETH", "2026-07-09"],
    ["PURR", "0002078856", "HYPE", "2026-08-23"],
  ];
  const CLOSE = "2026-10-09";
  const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
    "November", "December"];
  const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
  const sha = async (bytes) => hex(await crypto.subtle.digest("SHA-256", bytes));
  const esc = (s) => '"' + String(s).replace(/"/g, '""') + '"';
  const pad = (n) => String(n).padStart(2, "0");
  const inflate = async (bytes) => {
    const ds = new DecompressionStream("deflate");
    const w = ds.writable.getWriter();
    w.write(bytes).catch(() => {});
    w.close().catch(() => {});
    const chunks = [];
    const rd = ds.readable.getReader();
    try { for (;;) { const { value, done } = await rd.read(); if (done) break; chunks.push(value); } } catch (e) { /* stop at the end of the data */ }
    const out = new Uint8Array(chunks.reduce((a, c) => a + c.length, 0));
    let o = 0;
    for (const c of chunks) { out.set(c, o); o += c.length; }
    return out;
  };
  const unesc = (x) => x.replace(/\\([nrtbf()\\]|[0-7]{1,3})/g, (a, b) => /^[0-7]+$/.test(b) ? String.fromCharCode(parseInt(b, 8)) : ({ n: "\n", r: "\r", t: "\t", b: "\b", f: "\f" }[b] || b));
  const drawnText = (t) => t.split(/\bBT\b/).slice(1).map((bt) => {
    const parts = [];
    for (const m of bt.split(/\bET\b/)[0].matchAll(/\[((?:\\.|[^\]])*)\]\s*TJ|\(((?:\\.|[^\\)])*)\)\s*Tj|(T\*|Td|TD|Tm)/g)) {
      if (m[1] !== undefined) {
        const arr = [];
        for (const k of m[1].matchAll(/\(((?:\\.|[^\\)])*)\)|(-?\d+\.?\d*)/g)) {
          if (k[1] !== undefined) arr.push(unesc(k[1])); else if (parseFloat(k[2]) < -200) arr.push(" ");
        }
        parts.push(arr.join(""));
      } else if (m[2] !== undefined) parts.push(unesc(m[2])); else parts.push(" ");
    }
    return parts.join("");
  }).join(" ");
  const filings = [["ticker", "filing_date", "report_date", "form", "items", "accession", "primary_document"].join(",")];
  const pdfs = [["ticker", "filing_date", "form", "accession", "document", "bytes", "sha256", "pages", "text_chars",
    "latest_full_date_to_close", "token_mentions", "holding_sentences"].join(",")];
  for (const [tk, cik, token, from] of COMPANIES) {
    const s = await fetch(`https://data.sec.gov/submissions/CIK${cik}.json`, { cache: "no-store" }).then((r) => r.json());
    const f = s.filings.recent;
    for (let i = 0; i < f.form.length; i++) {
      const date = f.filingDate[i];
      if (date < from || date > CLOSE) continue;
      filings.push([tk, date, f.reportDate[i], esc(f.form[i]), esc(f.items[i]), f.accessionNumber[i], esc(f.primaryDocument[i])].join(","));
      const base = `https://www.sec.gov/Archives/edgar/data/${parseInt(cik, 10)}/${f.accessionNumber[i].replace(/-/g, "")}/`;
      let names = [];
      try { names = (await fetch(base + "index.json", { cache: "no-store" }).then((r) => r.json())).directory.item.map((x) => x.name); } catch (e) { names = []; }
      for (const n of names.filter((x) => /\.pdf$/i.test(x))) {
        const buf = new Uint8Array(await fetch(base + n, { cache: "no-store" }).then((r) => r.arrayBuffer()));
        const raw = new TextDecoder("latin1").decode(buf);
        const texts = [];
        for (const m of raw.matchAll(/stream\r?\n/g)) {
          const start = m.index + m[0].length;
          const dict = raw.slice(raw.lastIndexOf("<<", m.index), m.index);
          if (!/FlateDecode/.test(dict)) continue;
          const len = dict.match(/\/Length (\d+)(?! \d+ R)/);
          const end = len ? start + parseInt(len[1], 10) : raw.indexOf("endstream", start);
          const out = await inflate(buf.slice(start, end));
          if (out.length) texts.push(new TextDecoder("latin1").decode(out));
        }
        const text = texts.filter((t) => /\bT[Jj]\b/.test(t)).map(drawnText).join(" ").replace(/\s+/g, " ");
        const dates = [];
        for (const m of text.matchAll(/\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b/g)) {
          const d = `${m[3]}-${pad(MONTHS.indexOf(m[1]) + 1)}-${pad(m[2])}`;
          if (d <= CLOSE) dates.push(d);
        }
        const holding = [...new Set(text.split(". ").filter((x) => new RegExp(`\\b${token}\\b`).test(x) && /\b(?:holds?|held|owns?|owned)\b/i.test(x) && /\d/.test(x)).map((x) => x.trim().slice(0, 300)))];
        pdfs.push([tk, date, esc(f.form[i]), f.accessionNumber[i], n, buf.length, await sha(buf), (raw.match(/\/Type\s*\/Page[^s]/g) || []).length,
          text.length, dates.sort().slice(-1)[0] || "", (text.match(new RegExp(`\\b${token}\\b`, "g")) || []).length, esc(holding.join(" | "))].join(","));
      }
      await new Promise((ok) => setTimeout(ok, 150));
    }
  }
  const files = {
    "sec_window_filings_2026-10-12.csv": filings.join("\n") + "\n",
    "sec_window_pdfs_2026-10-12.csv": pdfs.join("\n") + "\n",
  };
  const digests = {};
  for (const [name, txt] of Object.entries(files)) digests[name] = await sha(new TextEncoder().encode(txt));
  window.__wx = { files, digests, finished: new Date().toISOString() };
  return `filings ${filings.length - 1}, pdfs ${pdfs.length - 1}, ` + Object.entries(digests).map(([k, v]) => k + " " + v.slice(0, 12)).join(" ");
})();
await window.__wxRun;
