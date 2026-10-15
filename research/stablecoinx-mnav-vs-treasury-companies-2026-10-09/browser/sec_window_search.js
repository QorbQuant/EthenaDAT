// Searches the text of every document in every filing each company made from the date of the earliest count this
// review uses for it to the October 9, 2026 close, for a token count or share count dated later than the count used.
// Forms 3, 4, 5 and 144, holders' Schedules 13D and 13G and EFFECT notices are skipped. PDFs and documents with almost
// no text, usually images, are listed as not searched.
//
// Each document's text is cut into sentences at a period followed by a space. A sentence longer than 600 characters,
// usually a table, is cut into 500-character windows around each mention of the token, "outstanding" or "Preferred".
// A passage is a share passage if it has a number of 1,000,000 or more, or a number of millions, and the words "shares"
// and "outstanding". It is a token passage if it has the company's token and a number written with "million",
// "billion", "M", "B" or a thousands separator. For Hyperion DeFi it is also a preferred passage if it has "Preferred"
// and such a number. A passage is flagged for review when it gives a full date after the date of the count of its kind
// and no later than October 9, 2026, or when it gives no full date, comes from a filing made after that count's date,
// and is a share passage or a token passage that says the company holds or owns tokens.
//
// Paste into the developer console on any page of https://www.sec.gov/ . Read-only GET requests, no login.
// Progress in window.__wsProgress, results in window.__ws.
window.__wsRun = (async () => {
  // ticker, CIK, token words, token count date, share count date, preferred count date
  const COMPANIES = [
    ["USDE", "0002080215", "ENA", "2026-06-25", "2026-08-28", null],
    ["MSTR", "0001050446", "BTC|[Bb]itcoin", "2026-10-04", "2026-09-25", null],
    ["ASST", "0001920406", "BTC|[Bb]itcoin", "2026-10-02", "2026-10-02", null],
    ["FWDI", "0000038264", "SOL", "2026-09-30", "2026-09-30", null],
    ["HYPD", "0001682639", "HYPE", "2026-09-30", "2026-09-30", "2026-06-30"],
    ["BMNR", "0001829311", "ETH", "2026-10-04", "2026-07-09", null],
    ["PURR", "0002078856", "HYPE", "2026-08-23", "2026-09-30", null],
  ];
  const CLOSE = "2026-10-09";
  const SKIP = new Set(["3", "4", "5", "3/A", "4/A", "5/A", "144", "144/A", "SCHEDULE 13G", "SCHEDULE 13G/A",
    "SCHEDULE 13D", "SCHEDULE 13D/A", "SC 13G", "SC 13G/A", "SC 13D", "SC 13D/A", "EFFECT"]);
  const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
    "November", "December"];
  const BIG = /\b\d{1,3}(?:,\d{3}){2,}\b|\b\d+(?:\.\d+)?\s*million\b/;
  const AMOUNT = /\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b|\b\d+(?:\.\d+)?\s*(?:million|billion|M|B)\b/;
  const HOLD = /\b(?:holds?|held|holdings?|owns?|owned|treasury)\b/i;
  const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
  const sha = async (bytes) => hex(await crypto.subtle.digest("SHA-256", bytes));
  const esc = (s) => '"' + String(s).replace(/"/g, '""') + '"';
  const pause = (ms) => new Promise((ok) => setTimeout(ok, ms));
  const pad = (n) => String(n).padStart(2, "0");
  const datesIn = (p) => {
    const out = [];
    for (const m of p.matchAll(/\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b/g)) {
      out.push(`${m[3]}-${pad(MONTHS.indexOf(m[1]) + 1)}-${pad(m[2])}`);
    }
    for (const m of p.matchAll(/\b(\d{1,2})\/(\d{1,2})\/(\d{4})\b/g)) out.push(`${m[3]}-${pad(m[1])}-${pad(m[2])}`);
    return [...new Set(out)].sort();
  };
  window.__wsProgress = [];
  const docRows = [], flagRows = [];
  for (const [tk, cik, tokenWords, tokenDate, shareDate, prefDate] of COMPANIES) {
    const from = [tokenDate, shareDate, prefDate].filter(Boolean).sort()[0];
    const tokenRe = new RegExp(`\\b(?:${tokenWords})\\b`);
    const anchorRe = new RegExp(`\\b(?:${tokenWords})\\b|\\boutstanding\\b|\\bPreferred\\b`, "g");
    const s = await fetch(`https://data.sec.gov/submissions/CIK${cik}.json`, { cache: "no-store" }).then((r) => r.json());
    const f = s.filings.recent;
    for (let i = 0; i < f.form.length; i++) {
      const date = f.filingDate[i];
      if (date < from || date > CLOSE || SKIP.has(f.form[i])) continue;
      const acc = f.accessionNumber[i].replace(/-/g, "");
      const base = `https://www.sec.gov/Archives/edgar/data/${parseInt(cik, 10)}/${acc}/`;
      let items = [];
      try { items = (await fetch(base + "index.json", { cache: "no-store" }).then((r) => r.json())).directory.item.map((x) => x.name); } catch (e) { items = []; }
      await pause(200);
      const docs = items.filter((n) => /\.(htm|html|txt|pdf)$/i.test(n) && !/^R\d+\.htm$|index|FilingSummary|-index-headers|^\d{10}-\d{2}-\d{6}\.txt$/i.test(n));
      for (const n of docs) {
        window.__wsProgress.push(`${tk} ${date} ${n}`);
        if (/\.pdf$/i.test(n)) { docRows.push([tk, date, f.form[i], f.accessionNumber[i], n, "", "", "no (PDF)", 0, 0, 0, 0]); continue; }
        const r = await fetch(base + n, { cache: "no-store" });
        const buf = await r.arrayBuffer();
        const t = new DOMParser().parseFromString(new TextDecoder().decode(buf), "text/html").body.innerText.replace(/\s+/g, " ");
        const passages = new Set();
        for (const sentence of t.split(". ")) {
          if (sentence.length <= 600) { passages.add(sentence.trim()); continue; }
          for (const m of sentence.matchAll(anchorRe)) passages.add(sentence.slice(Math.max(0, m.index - 250), m.index + 250).trim());
        }
        const counts = { share: 0, token: 0, preferred: 0 };
        let flagged = 0;
        for (const p of passages) {
          const kinds = [];
          if (BIG.test(p) && /\bshares\b/i.test(p) && /\boutstanding\b/i.test(p)) kinds.push(["share count", shareDate]);
          if (tokenRe.test(p) && AMOUNT.test(p)) kinds.push(["token count", tokenDate]);
          if (prefDate && /\bPreferred\b/.test(p) && AMOUNT.test(p)) kinds.push(["preferred count", prefDate]);
          const ds = datesIn(p);
          for (const [kind, countDate] of kinds) {
            counts[kind.split(" ")[0]] += 1;
            const later = ds.filter((d) => d > countDate && d <= CLOSE);
            let why = "";
            if (later.length) why = "dated after the count";
            else if (!ds.length && date > countDate && (kind !== "token count" || HOLD.test(p))) why = "undated in a later filing";
            if (why) {
              flagged += 1;
              flagRows.push([tk, date, f.form[i], f.accessionNumber[i], n, kind, countDate, ds.join(" "), why, esc(p.slice(0, 500))]);
            }
          }
        }
        const searched = t.length > 200 ? "yes" : "no (almost no text)";
        docRows.push([tk, date, f.form[i], f.accessionNumber[i], n, buf.byteLength, await sha(buf), searched, counts.share, counts.token, counts.preferred, flagged]);
        await pause(200);
      }
    }
  }
  const files = {
    "sec_window_documents_2026-10-12.csv": ["ticker,filing_date,form,accession,document,bytes,sha256,searched,share_passages,token_passages,preferred_passages,flagged", ...docRows.map((x) => x.join(","))].join("\n") + "\n",
    "sec_window_flagged_2026-10-12.csv": ["ticker,filing_date,form,accession,document,kind,count_date,dates_in_passage,why_flagged,passage", ...flagRows.map((x) => x.join(","))].join("\n") + "\n",
  };
  const digests = {};
  for (const [name, txt] of Object.entries(files)) digests[name] = await sha(new TextEncoder().encode(txt));
  window.__ws = { files, digests, finished: new Date().toISOString() };
  return `documents ${docRows.length}, not searched ${docRows.filter((x) => x[7] !== "yes").length}, flagged ${flagRows.length}, ` +
    Object.entries(digests).map(([k, v]) => k + " " + v.slice(0, 12)).join(" ");
})();
await window.__wsRun;
