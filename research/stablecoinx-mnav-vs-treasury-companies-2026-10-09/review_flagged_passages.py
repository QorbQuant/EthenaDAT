"""Writes inputs/filings/sec_window_review_2026-10-12.csv, this review's reading of every passage that
browser/sec_window_search.js flagged in inputs/filings/sec_window_flagged_2026-10-12.csv. Each rule below matches
passages by their words. The first rule that matches a passage gives its reading, and every flagged passage must
match at least one rule. Run it before dat_mnav_review.py, which checks that every flagged passage has a reading."""
import csv, hashlib, io, re, sys
from pathlib import Path

PK = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
rows = list(csv.DictReader(open(PK / "inputs/filings/sec_window_flagged_2026-10-12.csv", encoding="utf-8", newline="")))

RULES = [
    # (ticker, kind or None, pattern, verdict, note)
    ("PURR", "token count", r"the Company holds approximately 33\.2 million HYPE Tokens", "later count, used",
     "33.2 million HYPE on September 8, the latest HYPE count. The article uses it with the 237,919,288 shares of the same date"),
    ("PURR", "token count", r"the Company staked approximately 25\.1 million HYPE Tokens", "same count as used",
     "how the 33.2 million HYPE of September 8 were staked, 25.1 million plus 8.1 million"),
    ("PURR", "token count", r"digital assets tracked by CoinMarketCap|HIP-4 markets|Assistance Fund|circulating supply of approximately 235\.2 million|440\.4 million HYPE", "not a holding or share count",
     "market, network or supply figure, not the company's holding"),
    ("PURR", "token count", r"held approximately \$580 million in HYPE Tokens", "earlier count", "holding at the December 2, 2025 closing, in dollars"),
    ("PURR", "token count", r"netted approximately \$99\.8 million in proceeds", "not a holding or share count", "proceeds of an earlier offering"),
    ("PURR", "token count", r"net unrealized gains on HYPE tokens|Deferred tax liability|USDC held on Hyperliquid|raised \$647M|Where HSI Ranks", "not a holding or share count",
     "income, tax, protocol or ranking figure"),
    ("PURR", "token count", r"Tokens held rose from 18\.8M to 29\.3M|current 29\.3M HYPE tokens|Initial 12\.5M HYPE token", "earlier count",
     "investor presentation of August 27 with the fiscal year's figures, before the September 8 count"),
    ("PURR", "share count", r"we had 278,271,288 issued and outstanding shares", "same count as used", "the September 30 record date count the article uses"),
    ("PURR", "share count", r"Exchange Cap|Advisor Shares", "not a holding or share count", "terms of a purchase agreement or of shares issued at the 2025 closing"),
    ("USDE", "token count", r"approximately 3,029 million ENA tokens|ENA holdings at closing|3 billion ENA tokens represent", "same count as used",
     "the closing release of June 25 that the article uses"),
    ("USDE", "token count", r"approximately 3\.03 billion ENA|approximately 3\.0 billion tokens|approximately 2\.75 billion tokens", "rounded restatement",
     "the same holding rounded to 3.0 billion or 3.03 billion ENA, or its rounded parts"),
    ("USDE", "token count", r"approximately 9\.3 billion ENA tokens are in circulation|20% holder of the total supply", "not a holding or share count", "ENA supply, not the holding"),
    ("USDE", "token count", r"ENA contributed 249,120,581|Gross carrying amount|Total assets of \$232\.6 million|valued at \$218\.4 million|approximately \$9\.09 per share", "not a holding or share count",
     "dollar amounts of the ENA at cost, carrying value or market value, not a token count"),
    ("USDE", "token count", r"Earnout Shares|Janus Henderson", "not a holding or share count", "earnout terms or another investor's holding"),
    ("USDE", "share count", r"up to 12,668,943 shares", "not a holding or share count", "shares offered for resale, a fully diluted percentage"),
    ("USDE", "share count", r"27,187,129 shares of our Common Stock issued and outstanding as of the Closing|immediately following the consummation of the Merger|outstanding prior to the Merger", "earlier count",
     "the June 25 closing count, 24,029,375 Class A shares, the same as on August 28"),
    ("USDE", "share count", r"we also have outstanding: \(i\) ?19,124,586 Warrants", "same count as used", "the warrants the article cites from the prospectus"),
    ("USDE", "share count", r"1 share issued and outstanding|700,000 shares issued and outstanding", "not a holding or share count", "balance sheets of predecessor entities before the merger"),
    ("MSTR", "token count", r"Aggregate BTC Holdings .* 847,666", "earlier count", "847,666 BTC on September 30, before the October 4 count"),
    ("MSTR", "share count", r"there were an aggregate of 402,337,658 shares", "same count as used", "the September 25 record date count the article uses"),
    ("MSTR", "share count", r"Perpetual Stretch Preferred Stock|Perpetual Strike Preferred Stock", "not a holding or share count", "authorized preferred shares and redemption terms"),
    ("ASST", "share count", r"Assumed Fully Diluted Shares", "same count as used", "the October 2 table the article uses"),
    ("ASST", "token count", r"9/30/2026Balance Sheet|Bitcoin held28,000|Total treasury value \(in thousands\)\$2,675,086", "earlier count",
     "the September 30 balance sheet with 28,000 BTC, before the October 2 count"),
    ("FWDI", None, r"8,501,298|76,288,215|\$870,382,702", "same count as used", "the September 30 table the article uses"),
    ("HYPD", "preferred count", r"Series A convertible preferred.*16,307,691", "earlier count",
     "the earnings per share note's 16,307,691 as-converted shares for 2025, when 5,435,897 preferred shares were outstanding"),
    ("HYPD", "preferred count", r"Subsequent to June 30|Preferred Stock Dividend", "not a holding or share count",
     "subsequent events to August 13, a dividend paid in 235,618 common shares, no new preferred stock"),
    ("BMNR", "token count", r"5,067,309 staked ETH|5\.1 million ETH is 84%", "not a holding or share count", "the staked part of the holding"),
    ("BMNR", "token count", r"6\.02 [Mm]illion|6,016,414|ETH Holdings Reach", "same count as used", "the October 4 holding the article uses, rounded"),
    ("BMNR", "token count", r"forward-looking statements|Alchemy of 5%|weekly ETH acquisitions|4\.9% of the ETH supply", "not a holding or share count",
     "goals, forward-looking statements or the holding's share of ETH supply"),
    ("BMNR", "share count", r"Weighted-average number of common shares|Weighted average common shares|Pier Two", "not a holding or share count",
     "weighted averages for periods ended May 31 or acquisition terms"),
]

out = io.StringIO()
w = csv.writer(out, lineterminator="\n")
w.writerow(["ticker", "filing_date", "document", "kind", "passage_sha256_12", "verdict", "note"])
unmatched = []
for r in rows:
    hits = [x for x in RULES if x[0] == r["ticker"] and (x[1] is None or x[1] == r["kind"]) and re.search(x[2], r["passage"])]
    if not hits:
        unmatched.append((r["ticker"], r["kind"], r["passage"][:160]))
        continue
    h = hits[0]
    w.writerow([r["ticker"], r["filing_date"], r["document"], r["kind"],
                hashlib.sha256(f"{r['ticker']}|{r['document']}|{r['kind']}|{r['passage']}".encode()).hexdigest()[:12], h[3], h[4]])
for u in unmatched:
    print("UNMATCHED", u)
if not unmatched:
    (PK / "inputs/filings/sec_window_review_2026-10-12.csv").write_text(out.getvalue(), encoding="utf-8")
    from collections import Counter
    print(len(rows), "flagged rows reviewed", Counter((r[0]) for r in csv.reader(io.StringIO(out.getvalue())) if r[0] != "ticker"))
    print(Counter(r[5] for r in csv.reader(io.StringIO(out.getvalue())) if r[0] != "ticker"))
