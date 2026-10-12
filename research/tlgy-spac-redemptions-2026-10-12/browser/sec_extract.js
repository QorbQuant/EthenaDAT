// Run in the browser console on any https://www.sec.gov/Archives/... page, so the fetches stay on the same site.
// Rebuilds inputs/sec_extracts_2026-10-12.txt and the four later sets, sec_extracts_2 to 5, from EDGAR and
// prints each file's size and SHA-256. Every document is fetched once, hashed as served, reduced to text (script,
// style and the inline XBRL header removed, zero-width characters deleted, whitespace collapsed) and cut into
// the fixed windows listed below, given as [anchor, characters before, characters after, occurrences].
// The read times in the header lines will differ from the saved files, so compare the window lines, which
// should match exactly while EDGAR serves the same documents. Downloads nothing. Keep to EDGAR's fair access
// rate, as the pause between fetches does.
const sleep = ms => new Promise(r => setTimeout(r, ms));
const hex = async b => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', b)))
  .map(x => x.toString(16).padStart(2, '0')).join('');

async function anch(key, path, anchors) {
  const url = 'https://www.sec.gov' + path;
  const t0 = new Date().toISOString();
  const resp = await fetch(url, {cache: 'no-store'});
  const buf = await resp.arrayBuffer();
  const h = await hex(buf);
  const doc = new DOMParser().parseFromString(new TextDecoder('utf-8').decode(buf), 'text/html');
  doc.querySelectorAll('ix\\:header, script, style').forEach(e => e.remove());
  const text = (doc.body ? doc.body.textContent : doc.documentElement.textContent)
    .replace(/[​‌‍﻿]/g, '').replace(/ /g, ' ').replace(/\s+/g, ' ').trim();
  const lines = [`### ${key} ${url}`,
    `# status ${resp.status} read ${t0} raw_bytes ${buf.byteLength} raw_sha256 ${h} text_chars ${text.length}`];
  for (const [a, pre, post, n] of anchors) {
    let c = 0, from = 0;
    while (c < (n || 1)) {
      const i = text.indexOf(a, from);
      if (i < 0) break;
      lines.push(`- @${i} ${text.slice(Math.max(0, i - pre), Math.min(text.length, i + a.length + post))}`);
      c++;
      from = i + a.length;
    }
    if (c === 0) lines.push(`- MISSING ${a}`);
  }
  return lines.join('\n') + '\n';
}

const B = '/Archives/edgar/data/1879814/';
const S = '/Archives/edgar/data/2080215/';
const FIRST = [
  ['ipo_8k', B + '000119312521353043/d260802d8k.htm', [['consummated its initial public offering', 60, 60], ['Each Unit consists of', 0, 420], ['The Units were sold at a price of $10.00 per Unit', 0, 60], ['A total of $204,000,000', 0, 330]]],
  ['ipo_8k2', B + '000119312521356482/d261970d8k.htm', [['the underwriters purchased an additional 3,000,000 Units', 110, 120], ['An aggregate of approximately $234,600,000', 0, 230]]],
  ['ipo_424b4', B + '000119312521346884/d166704d424b4.htm', [['Each unit has an offering price of $10.00', 0, 1350], ['($10.20 per unit in either case)', 230, 40]]],
  ['ext1_8k', B + '000110465923025551/tm237896d1_8k.htm', [['On February 23, 2023, shareholders', 0, 230], ['15,681,818 ordinary shares', 70, 40], ['approximately $10.40 per share', 60, 0]]],
  ['ext2_8k', B + '000110465923110132/tm2328709d1_8k.htm', [['On October 17, 2023, shareholders', 0, 820], ['1,395,317 ordinary shares', 70, 40], ['approximately $10.96 per share', 60, 0]]],
  ['ext3_8k', B + '000110465924047788/tm2411664d3_8k.htm', [['On April 16, 2024, shareholders', 0, 830], ['2,205,658 ordinary shares', 70, 40], ['approximately $11.33 per share', 60, 0]]],
  ['ext4_8k', B + '000110465925036860/tm2512558d1_8k.htm', [['On April 15, 2025', 0, 200], ['Proposal 1', 0, 700], ['Proposal 4', 0, 420], ['2,030,299', 70, 20], ['holders of 3,227,320 Class A ordinary shares', 0, 200], ['balance in the Company', 20, 80], ['approximately 5,834,587 Class A ordinary shares outstanding', 160, 110]]],
  ['ext5_8k', B + '000121390026045658/ea0286515-8k_tlgyacq.htm', [['On April 15, 2026, TLGY Acquisition Corporation', 0, 200], ['holding 13,817 Class A Ordinary Shares', 60, 160]]],
  ['bc_vote_8k', B + '000121390026025809/ea0280899-8k425_tlgyacq.htm', [['On March 10, 2026, TLGY Acquisition Corporation', 0, 230], ['On February 4, 2026, the record date', 0, 330], ['were represented in person or by proxy', 90, 60], ['Shareholder Proposal No. 1', 0, 120], ['For Against Abstain 5,759,409 2,000 0 Shareholder Proposal No. 2', 0, 70], ['holding 388,406 Class A Ordinary Shares', 70, 150]]],
  ['k8_2024_12_05', B + '000110465924125922/tm2430127d1_8k.htm', [['On December 2, 2024', 0, 420], ['will not request a hearing', 70, 80], ['Trading in the Company', 0, 190]]],
  ['f25_2025_05_08', B + '000135445725000389/xslF25X02/primary_doc.xml', [['Exchange:', 30, 40], ['Class A Ordinary Share, Warrants, Units', 0, 40], ['2025-05-08 By', 0, 40]]],
  ['def14a_2026', B + '000121390026040497/ea0285135-01.htm', [['Our Board has fixed the close of business on March 20, 2026', 0, 60], ['On the record date, there were a total of 5,939,587', 0, 170], ['will be approximately $13.19 at the time of the Extraordinary General Meeting', 180, 0], ['approximately $6.5 million that was in the Trust Account as of March 20, 2026', 120, 20]]],
  ['q1_2026_10q', B + '000121390026056223/ea0287797-10q_tlgyacq.htm', [['489,887 shares (at redemption value of $13.19 and $12.95', 70, 110], ['holders of 388,406 Class A ordinary shares', 170, 190], ['from the lesser of (x) $0.05 per outstanding share and (y) $25,000', 0, 80], ['13,817 Class A ordinary shares elected to redeem', 80, 210], ['13,817 Class A ordinary shares were rendered for redemption', 60, 100]]],
  ['k10_2025', B + '000121390026036938/ea0275867-10k_tlgyacq.htm', [['As of December 31, 2025, the amount in the trust account was $12.95 per public share', 0, 0], ['489,887 and 3,717,207 shares (at redemption value of $12.95 and $11.92)', 70, 100], ['we had cash and investments held in the trust account of $6,344,805', 25, 0]]],
  ['defm14a', B + '000121390026017535/ea0277387-01.htm', [['Trust Account Value $ 6,210,376.00', 30, 110], ['the value of the cash held in the Trust Account as of June 30, 2025 which was $6,051,707', 0, 130], ['this would have amounted to approximately $13.05 per Public Share', 40, 0], ['As of the close of business on the Record Date for the extraordinary general meeting', 0, 140]]],
  ['closing_8k', S + '000121390026074559/ea0296210-8k_stablecoinx.htm', [['on June 25, 2026 (the', 70, 60], ['a total of 379,721 Public Shares were redeemed', 30, 120], ['each issued and outstanding unit of TLGY', 30, 60], ['(that was not redeemed pursuant to the Redemption) was exchanged', 60, 140], ['became a warrant to acquire one share of StablecoinX Class A Common Stock', 160, 60], ['there were 27,187,129 shares', 0, 160], ['June 26, 2026', 220, 120, 3]]],
  ['sx_q2_10q', S + '000121390026090250/ea0301482-10q_stable.htm', [['TLGY Class A common stock, outstanding prior to the Merger 5,834,587', 0, 150]]],
  ['q1_2023_10q', B + '000110465923059752/tlgyu-20230331x10q.htm', [['Cash withdrawn from Trust Account 163,150,810', 0, 0], ['Redemptions of Class A ordinary shares (163,150,810)', 0, 0], ['the 7,318,182 and 23,000,000 Class A ordinary shares', 60, 120]]],
  ['k10_2023', B + '000110465924039031/tlgyu-20231231x10k.htm', [['an aggregate of 17,077,135 shares were redeemed', 25, 260]]],
  ['k10_2024', B + '000141057825000276/tlgyu-20241231x10k.htm', [['an aggregate of 2,205,658 shares were redeemed', 60, 250]]],
  ['q2_2025_10q', B + '000141057825001609/tlgyu-20250630x10q.htm', [['3,227,320 Class A ordinary shares elected to redeem', 80, 260], ['489,887 and 3,717,207 Class A ordinary shares subject to possible redemption in the amount of $6,072,600', 30, 40]]],
];
const SECOND = [
  ['ipo_8k', B + '000119312521353043/d260802d8k.htm', [['consummated its initial public offering', 100, 60]]],
  ['ipo_424b4', B + '000119312521346884/d166704d424b4.htm', [['begin separate trading', 250, 200]]],
  ['k8_2026_03_16', B + '000121390026027981/ea0280898-8k_tlgy.htm', [['On March 11, 2026, the Company notified', 0, 420], ['On March 13, 2026', 0, 200]]],
  ['q2_2024_10q', B + '000141057824001531/tlgyu-20240630x10q.htm', [['the 3,717,207 and 5,922,865 Class A ordinary shares', 60, 130]]],
  ['k10_2024', B + '000141057825000276/tlgyu-20241231x10k.htm', [['the 3,717,207 and 5,922,865, respectively', 60, 140]]],
  ['k10_2025', B + '000121390026036938/ea0275867-10k_tlgyacq.htm', [['invested in U.S. government securities', 90, 300]]],
  ['defm14a', B + '000121390026017535/ea0277387-01.htm', [['will be excluded from the pro rata calculation used to determine the per-share Redemption Price', 60, 0], ['11,500,000 StablecoinX Warrants issued for the TLGY Warrants', 30, 80]]],
];
const THIRD = [
  ['def14a_2026', B + '000121390026040497/ea0285135-01.htm', [['other than any shares previously properly tendered for redemption in connection with the Business Combination', 200, 250], ['There will be no redemption rights or liquidating distributions with respect to our warrants', 0, 120]]],
  ['ext4_8k', B + '000110465925036860/tm2512558d1_8k.htm', [['Proposal 1 - Extension Amendment Proposal The shareholders approved', 0, 900]]],
];
const FOURTH = [
  ['k10_2022', B + '000110465923023530/tlgyu-20221231x10k.htm', [['Income earned on Investments held in Trust Account 2,901,000', 0, 0], ['Cash deposited into Trust Account — (234,600,000)', 0, 0]]],
  ['k10_2023', B + '000110465924039031/tlgyu-20231231x10k.htm', [['Income earned on investments held in Trust Account 5,072,178 2,901,000', 0, 0], ['Cash deposited into Trust Account (1,820,000)', 0, 0]]],
  ['k10_2024', B + '000141057825000276/tlgyu-20241231x10k.htm', [['Income earned on investments held in Trust Account 2,598,427 5,072,178', 0, 0], ['Cash withdrawn from Trust Account in connection with redemptions 25,092,549 178,438,540', 0, 0], ['Cash deposited into Trust Account (872,089) (1,820,000)', 0, 0]]],
  ['k10_2025', B + '000121390026036938/ea0275867-10k_tlgyacq.htm', [['Income earned on cash and investments held in Trust Account 725,255 2,598,427', 0, 0], ['Cash withdrawn from Trust Account 39,113,505 25,092,549 Cash deposited into Trust Account (400,450) (872,089)', 0, 0]]],
  ['q1_2026_10q', B + '000121390026056223/ea0287797-10q_tlgyacq.htm', [['Income earned on cash and investments held in Trust Account 44,722 466,024', 0, 0], ['Cash deposited into Trust Account (73,483) (180,000)', 0, 0]]],
  ['def14a_2026', B + '000121390026040497/ea0285135-01.htm', [['cease all operations except for the purpose of winding up', 250, 330]]],
];
const FIFTH = [
  ['ext1_8k', B + '000110465923025551/tm237896d1_8k.htm', [['The ordinary shares will be redeemed at a per-share price, payable in cash', 0, 330]]],
  ['k8_2024_12_05', B + '000110465924125922/tm2430127d1_8k.htm', [['it was not in compliance with Nasdaq IM 5101-2', 0, 60]]],
  ['k8_2024_06_21', B + '000110465924073933/tm2417671d1_8k.htm', [['Item 5.01', 0, 900]]],
  ['k8_2024_08_19', B + '000110465924090895/tm2421982d1_8k.htm', [['Item 4.02', 0, 1100]]],
  ['bc_vote_8k', B + '000121390026025809/ea0280899-8k425_tlgyacq.htm', [['the business combination agreement, dated', 0, 100]]],
  ['closing_8k', S + '000121390026074559/ea0296210-8k_stablecoinx.htm', [['11,499,988', 150, 120]]],
  ['sx_q2_10q', S + '000121390026090250/ea0301482-10q_stable.htm', [['The number of shares of common stock outstanding immediately following the consummation of the Merger', 0, 520]]],
];

async function build(jobs, head) {
  const parts = [];
  for (const j of jobs) { parts.push(await anch(...j)); await sleep(350); }
  const body = head + '\n\n' + parts.join('\n');
  const enc = new TextEncoder().encode(body);
  console.log(enc.length, 'bytes', await hex(enc), (body.match(/MISSING/g) || []).length, 'missing anchors');
  return body;
}

const one = await build(FIRST, '# SEC filing extracts for the TLGY redemption review. Each block gives the address, the read time, the size and SHA-256 of the raw document as served, and fixed windows of its text after removing script, style and the inline XBRL header, deleting zero-width characters and collapsing whitespace. @n is the character offset of the anchor in that text.');
const two = await build(SECOND, '# Second set of SEC filing extracts for the TLGY redemption review, made the same way as sec_extracts_2026-10-12.txt.');
const three = await build(THIRD, '# Third set of SEC filing extracts for the TLGY redemption review, made the same way as sec_extracts_2026-10-12.txt.');
const four = await build(FOURTH, '# Fourth set of SEC filing extracts for the TLGY redemption review, made the same way as sec_extracts_2026-10-12.txt.');
const five = await build(FIFTH, '# Fifth set of SEC filing extracts for the TLGY redemption review, made the same way as sec_extracts_2026-10-12.txt.');
console.log(one);
console.log(two);
console.log(three);
console.log(four);
console.log(five);
