// Two console scripts. Each prints its file and the file's SHA-256 so a saved copy can be matched.
// Neither downloads anything.
//
// 1. Run on https://data.sec.gov/submissions/CIK0001879814.json to rebuild
//    inputs/edgar_filings_tlgy_2026-10-12.csv, TLGY Acquisition Corp.'s 8-K, 10-K, 10-K/A, 10-Q, DEF 14A,
//    DEFM14A, 424B4, 25-NSE and 15-12G filings as EDGAR lists them. TLGY filed to deregister on June 26, 2026,
//    so a later read is likely to match, but EDGAR can add or correct entries.
// 2. Run on https://query1.finance.yahoo.com/v8/finance/chart/USDE?range=6mo&interval=1d to rebuild
//    inputs/usde_daily_yahoo_2026-10-12.csv, USDE's daily close and volume as Yahoo Finance gives them, used
//    to check the StockAnalysis closes. The six-month range moves with the read date, so a later read starts
//    later and adds sessions, and Yahoo revises volumes.
const hex = async b => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', b)))
  .map(x => x.toString(16).padStart(2, '0')).join('');

if (location.host === 'data.sec.gov') {
  const resp = await fetch('https://data.sec.gov/submissions/CIK0001879814.json', {cache: 'no-store'});
  const buf = await resp.arrayBuffer();
  const r = JSON.parse(new TextDecoder().decode(buf)).filings.recent;
  const keep = new Set(['8-K', '10-K', '10-K/A', '10-Q', 'DEF 14A', 'DEFM14A', '424B4', '25-NSE', '15-12G']);
  const rows = ['filing_date,form,accession_number,primary_document,acceptance_utc,items'];
  for (let i = 0; i < r.accessionNumber.length; i++) {
    if (!keep.has(r.form[i])) continue;
    rows.push([r.filingDate[i], r.form[i], r.accessionNumber[i], r.primaryDocument[i], r.acceptanceDateTime[i],
      '"' + (r.items[i] || '') + '"'].join(','));
  }
  const csv = rows.join('\n') + '\n';
  console.log(new Date().toISOString(), 'filings', r.accessionNumber.length, 'kept', rows.length - 1,
    'json sha256', await hex(buf), 'csv sha256', await hex(new TextEncoder().encode(csv)));
  console.log(csv);
} else {
  const j = JSON.parse(document.body.innerText);
  const res = j.chart.result[0];
  const q = res.indicators.quote[0];
  const fmt = new Intl.DateTimeFormat('en-CA', {timeZone: res.meta.exchangeTimezoneName, year: 'numeric', month: '2-digit', day: '2-digit'});
  const csv = 'date,volume,close\n' + res.timestamp.map((t, i) => [fmt.format(new Date(t * 1000)), q.volume[i], q.close[i]].join(',')).join('\n') + '\n';
  console.log(new Date().toISOString(), res.meta.symbol, res.meta.exchangeName, res.timestamp.length, 'rows',
    await hex(new TextEncoder().encode(csv)));
  console.log(csv);
}
