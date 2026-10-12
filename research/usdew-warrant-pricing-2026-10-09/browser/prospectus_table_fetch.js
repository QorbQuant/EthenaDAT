// Run in the browser console on StablecoinX's resale prospectus of September 14, 2026,
// https://www.sec.gov/Archives/edgar/data/2080215/000121390026099731/ea0305435-424b3_stable.htm
// Parses the make-whole table of the $10.00 call, on page 95, into CSV and prints its SHA-256, which should
// equal the hash of inputs/warrant_make_whole_table.csv. A dash in the table becomes an empty cell.
const T = document.body.innerText;
const a = T.indexOf('Redemption Date (period to expiration of warrants)');
const b = T.indexOf('The exact Redemption Fair Market Value');
const seg = T.slice(a, b).split('\n').map(s => s.trim()).filter(Boolean);
const hdr = seg[1].split(/\s+/).map(x => x.replace('$', ''));
let csv = 'months_to_expiration,' + hdr.map(x => 'fmv_' + x).join(',') + '\n';
for (const l of seg.slice(2)) {
  const m = l.match(/^(\d+)\s+months\s+(.*)$/);
  if (!m) continue;
  const v = m[2].split(/\s+/).map(x => (/^[—–-]$/.test(x) ? '' : x));
  if (v.length !== 9) throw new Error('row ' + l);
  csv += m[1] + ',' + v.join(',') + '\n';
}
const sha = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(csv))))
  .map(x => x.toString(16).padStart(2, '0')).join('');
console.log(new Date().toISOString(), 'page text', T.length, 'characters, table', sha);
console.log(csv);
