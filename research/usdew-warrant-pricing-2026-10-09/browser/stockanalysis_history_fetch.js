// Run in the browser console on https://stockanalysis.com/stocks/usde/history/ or /stocks/usdew/history/.
// Pages through the table with the Next button, writes the rows as CSV with ISO dates, and prints the
// file's SHA-256 so the saved copy can be matched. Prices are S&P Global Market Intelligence's, as the
// page credits them. Reads only what the page shows.
const sleep = ms => new Promise(r => setTimeout(r, ms));
const M = {Jan: 1, Feb: 2, Mar: 3, Apr: 4, May: 5, Jun: 6, Jul: 7, Aug: 8, Sep: 9, Oct: 10, Nov: 11, Dec: 12};
const iso = s => {
  const m = s.match(/^([A-Z][a-z]{2}) (\d{1,2}), (\d{4})$/);
  return m ? `${m[3]}-${String(M[m[1]]).padStart(2, '0')}-${m[2].padStart(2, '0')}` : 'BAD:' + s;
};
const grab = () => [...document.querySelectorAll('table tbody tr')].map(r => [...r.querySelectorAll('td')].map(c => c.innerText.trim()));
let all = [];
for (let k = 0; k < 6; k++) {
  const rows = grab();
  all.push(...rows);
  const next = [...document.querySelectorAll('button')].find(b => b.innerText.trim() === 'Next');
  if (!next || next.disabled) break;
  const first = rows[0][0];
  next.click();
  let moved = false;
  for (let t = 0; t < 40; t++) {
    await sleep(150);
    const r2 = grab();
    if (r2.length && r2[0][0] !== first) { moved = true; break; }
  }
  if (!moved) break;
}
const seen = new Set();
const recs = [];
for (const r of all) {
  const d = iso(r[0]);
  if (seen.has(d)) continue;
  seen.add(d);
  recs.push([d, r[1], r[2], r[3], r[4], r[5], r[6].replace('%', '').replace(/^−/, '-'), r[7].replace(/,/g, '')]);
}
recs.sort((a, b) => (a[0] < b[0] ? -1 : 1));
const csv = 'date,open,high,low,close,adj_close,change_pct,volume\n' + recs.map(r => r.join(',')).join('\n') + '\n';
const buf = new TextEncoder().encode(csv);
const sha = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', buf))).map(x => x.toString(16).padStart(2, '0')).join('');
console.log(new Date().toISOString(), recs.length, 'rows', buf.length, 'bytes', sha);
console.log(csv);
