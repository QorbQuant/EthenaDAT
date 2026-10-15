// Reads the SEC filings behind each company's token count and share count, hashes each document as
// served, and keeps the passages that state the figures. Also reads each company's EDGAR filing list
// and keeps the filings from September 1 to October 9, 2026. Paste into the developer console on any
// page of https://www.sec.gov/ . Read-only GET requests, no login. Results in window.__sec.
await (async () => {
  const A = "https://www.sec.gov/Archives/edgar/data/";
  const DOCS = [
    ["usde_closing_release", A + "2080215/000121390026072231/ea029602401ex99-1.htm", ["ENA", "3,029", "3.029"]],
    ["usde_10q_cover", A + "2080215/000121390026090250/ea0301482-10q_stable.htm", ["shares of Class A common stock", "outstanding as of", "Class A Common Stock, par value"]],
    ["mstr_8k_2026-10-05", A + "1050446/000119312526413164/mstr-20261005.htm", ["As of October 4, 2026", "Aggregate BTC Holdings", "MSTR Stock", "4:00 p.m. Eastern Time", "not yet settled"]],
    ["mstr_def14a_2026-10-05", A + "1050446/000119312526413159/d503578ddef14a.htm", ["On the record date, there were"]],
    ["mstr_8k_2026-09-28", A + "1050446/000119312526403417/mstr-20260914.htm", ["September 21, 2026 to September 27, 2026", "MSTR Stock"]],
    ["asst_8k_2026-10-05", A + "1920406/000162828026064753/asst-20261005.htm", ["Bitcoin held", "Effective Common Shares Outstanding", "Includes shares outstanding", "SATA stated amount", "Cash and cash equivalents"]],
    ["bmnr_10q_cover", A + "1829311/000162828026048157/bmnr-20260531.htm", ["The number of shares outstanding of the registrant"]],
    ["bmnr_release_2026-10-05", A + "1829311/000149315226045699/ex99-1.htm", ["As of October 4, 2026", "total cash & marketable securities of"]],
    ["bmnr_release_2026-07-20", A + "1829311/000149315226033855/ex99-1.htm", ["repurchased approximately", "As of July 19, 2026"]],
    ["bmnr_release_2026-08-17", A + "1829311/000149315226038652/ex99-1.htm", ["Since July 1, 2026, Bitmine has repurchased", "As of August 16, 2026"]],
    ["bmnr_chairman_2026-10-07", A + "1829311/000149315226046088/ex99-2.htm", ["began a stock buyback", "21 million shares", "trade above NAV"]],
    ["fwdi_release_2026-10-01", A + "38264/000168316826007543/forward_ex9901.htm", ["Total FV of SOL Treasury", "Common shares", "Fully diluted share count", "Total net asset value", "mNAV is the FWDI share price", "Includes SOL, fwdSOL"]],
    ["purr_10k_holdings", A + "2078856/000119312526370281/purr-20260630.htm", ["As of August 23, 2026, the Company holds approximately", "As of August 23, 2026, there were"]],
    ["purr_def14a_2026-10-02", A + "2078856/000119312526412569/d290166ddef14a.htm", ["As of the Record Date, we had"]],
    ["mpu_6k_2026-10-01_ex991", A + "1953021/000121390026105759/ea030681101ex99-1.htm", ["held 5,203,582", "ENA 374,900"]],
    ["hypd_release_2026-10-02", A + "1682639/000110465926113050/tm2626852d1_ex99-1.htm", ["As of September 30, 2026, the Company had approximately"]],
  ];
  const CIKS = { USDE: "0002080215", MSTR: "0001050446", ASST: "0001920406", BMNR: "0001829311", FWDI: "0000038264", PURR: "0002078856" };
  const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
  const sha = async (bytes) => hex(await crypto.subtle.digest("SHA-256", bytes));
  const text = (html) => new DOMParser().parseFromString(html, "text/html").body.innerText.replace(/\s+/g, " ");
  const out = [], log = [];
  for (const [key, url, needles] of DOCS) {
    const r = await fetch(url, { cache: "no-store" });
    const buf = await r.arrayBuffer();
    const t = text(new TextDecoder().decode(buf));
    log.push([key, url, r.status, new Date().toISOString(), buf.byteLength, await sha(buf), t.length]);
    out.push(`### ${key}\n${url}`);
    for (const n of needles) {
      let i = t.indexOf(n), found = 0;
      while (i >= 0 && found < 3) { out.push(`[${n}] ` + t.slice(Math.max(0, i - 300), i + 600)); found++; i = t.indexOf(n, i + 600); }
      if (!found) out.push(`[${n}] NOT FOUND`);
    }
    await new Promise((ok) => setTimeout(ok, 250));
  }
  const filings = [];
  for (const [tk, cik] of Object.entries(CIKS)) {
    const url = `https://data.sec.gov/submissions/CIK${cik}.json`;
    const r = await fetch(url, { cache: "no-store" });
    const buf = await r.arrayBuffer();
    const s = JSON.parse(new TextDecoder().decode(buf));
    const f = s.filings.recent;
    for (let i = 0; i < f.form.length; i++) {
      if (f.filingDate[i] > "2026-10-09" || f.filingDate[i] < "2026-09-01") continue;
      filings.push([tk, f.filingDate[i], f.acceptanceDateTime[i], f.form[i], f.accessionNumber[i], f.primaryDocument[i], '"' + f.items[i] + '"']);
    }
    log.push(["submissions_" + tk, url, r.status, new Date().toISOString(), buf.byteLength, await sha(buf), f.form.length]);
    await new Promise((ok) => setTimeout(ok, 250));
  }
  const files = {
    "sec_passages_2026-10-12.txt": out.join("\n\n") + "\n",
    "sec_filings_2026-09-01_to_10-09.csv": ["ticker,filing_date,accepted,form,accession,primary_document,items", ...filings.map((x) => x.join(","))].join("\n") + "\n",
    "sec_fetch_log.csv": ["key,url,status,fetched_at,bytes,sha256,text_chars_or_filings", ...log.map((x) => x.join(","))].join("\n") + "\n",
  };
  const digests = {};
  for (const [name, txt] of Object.entries(files)) digests[name] = await sha(new TextEncoder().encode(txt));
  window.__sec = { files, digests };
  return `docs ${DOCS.length}, statuses ${log.map((x) => x[2]).join("/")}, filings ${filings.length}, not found ${out.filter((x) => x.endsWith("NOT FOUND")).length}, ${Object.entries(digests).map(([k, v]) => k + " " + v.slice(0, 12)).join(" ")}`;
})();
