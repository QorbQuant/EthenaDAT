# TLGY's SPAC redemptions and USDE against the merger's cash, December 2021 to October 9, 2026

These files reproduce every computed figure in the review of what happened to the public shareholders of TLGY Acquisition Corp., the special purpose acquisition company that merged with StablecoinX Inc. on June 25, 2026. The review counts the public shares redeemed at each of the six votes at which holders could take cash from the trust, from February 2023 to the merger, and the cash paid for them, rolls the trust's balance forward year by year, follows its value a share from the December 2021 initial public offering, or IPO, to the merger, and sets USDE's daily close from June 26 to October 9, 2026 against the cash a share paid at the merger. The filings were read from EDGAR on October 12, 2026 UTC, and the prices on the same morning.

No figure here is a forecast. The comparison with USDE uses closing prices and says nothing about what a holder should have done.

## Reproduce

From this directory, with Python 3 and the standard library only.

    python3 tlgy_redemption_review.py
    python3 make_chart_svg.py
    python3 check_article_numbers.py

The first script reads the inputs and runs its checks. If any check fails it stops before writing anything, so `out/` keeps the tables of the last clean run. Otherwise it rewrites the tables in `out/`. It confirms every input against `inputs/manifest.csv` and that the manifest lists every input. It checks that every filing in the five extract files was served with status 200, that every anchor was found, that documents read more than once were served identically each time, and that each of the 143 rows of `inputs/filing_facts.csv` quotes its window and shows its value. It checks that TLGY's list of filings holds six 8-Ks reporting a shareholder vote and ends with its June 26, 2026 deregistration, that 20,000,000 and 3,000,000 units make the 23,000,000 public shares, that $234,600,000 is $10.20 a unit, and that half a warrant and a quarter of a warrant a unit give 11,500,000 and 5,750,000 warrants. It checks that each vote leaves the public share count TLGY reported next, that the two 2023 votes add up to the 17,077,135 shares of the 10-K for 2023, that the fifth vote's and the merger's counts add up to the 393,538 in StablecoinX's share table, that the 96,349 public shares kept by the vote counts are also 489,887 less the share table's 393,538, and that the share table's lines add up to the 24,029,375 Class A shares in StablecoinX's 8-K on the closing. It checks the four votes before the July 21, 2025 merger agreement, the 11,499,988 warrants left after the merger, the cash a share against every price a share in the filings, the trust's yearly roll-forward from 2022 to 2025, that the 10-K for 2024 repeats the 2023 trust figures after the 2023 accounts were corrected for convertible notes, the $111 gap in 2025, the first quarter of 2026, the monthly deposits, that the trust's value a share rose at every step, and every USDE close against Yahoo Finance's. The second script draws the chart from `out/trust_a_share.csv`, `out/usde_against_merger_cash.csv` and `out/results.json`. The third recomputes the article's computed figures, those in its metadata and the chart's text in exact decimals with separately written code, reads the filing figures straight from the extracts with its own patterns, and exits with an error if a phrase no longer appears. None of them uses the network.

To read the filings again, open any EDGAR filing page in a browser and paste `browser/sec_extract.js` into the developer console. It rebuilds the five extract files and prints their sizes and SHA-256 hashes. The read times in their header lines will differ, and the window lines should match while EDGAR serves the same documents. `browser/edgar_and_yahoo_fetch.js` rebuilds the filing list on EDGAR's submissions page and the Yahoo Finance closes on Yahoo's chart page, and `browser/stockanalysis_history_fetch.js` the StockAnalysis histories on their history pages. Each builds its file and SHA-256 in the page and downloads nothing. Price sources can revise their latest rows, so a later read may differ in the last session's volume.

## Files

| File | What it is |
| --- | --- |
| `article_draft.md` | The article in the format the site's build reads. Headline, kicker, byline, then the body |
| `metadata.json` | Page metadata |
| `tlgy_redemption_review.py` | The main script |
| `check_article_numbers.py` | Recomputes each computed figure and confirms the exact phrase appears in `article_draft.md`, `metadata.json` or the chart |
| `make_chart_svg.py` | Draws `out/chart_tlgy_redemptions.svg` |
| `browser/sec_extract.js` | Rebuilds the five extract files from EDGAR |
| `browser/edgar_and_yahoo_fetch.js` | Rebuilds the filing list and the Yahoo Finance closes |
| `browser/stockanalysis_history_fetch.js` | Reads a StockAnalysis price history table into CSV |
| `inputs/sec_extracts_2026-10-12.txt` | Fixed windows of text from 21 filings by TLGY, StablecoinX and Nasdaq, each under its address, read time, size and SHA-256 as served |
| `inputs/sec_extracts_2_2026-10-12.txt` to `_5_` | Four later sets made the same way, for seven, two, six and seven filings, some of them read again |
| `inputs/filing_facts.csv` | 143 figures and terms from the filings, each with the extract it comes from, the exact quote and the part of the quote that shows the value |
| `inputs/edgar_filings_tlgy_2026-10-12.csv` | TLGY's 104 filings of the forms 8-K, 10-K, 10-K/A, 10-Q, DEF 14A, DEFM14A, 424B4, 25-NSE and 15-12G, as EDGAR listed them on October 12 |
| `inputs/usde_daily_stockanalysis_2026-10-12.csv` | USDE daily prices and volume from StockAnalysis, sourced from S&P Global Market Intelligence, April 9 to October 9. The 22 rows before June 26, with closes near $10 on small volume, appear to be TLGY's shares trading over the counter and are not used |
| `inputs/usde_daily_yahoo_2026-10-12.csv` | USDE's daily close and volume from Yahoo Finance, June 26 to October 9, used to check each close |
| `inputs/usdew_daily_stockanalysis_2026-10-12.csv` | USDEW daily prices from StockAnalysis, June 29 to October 9 |
| `inputs/manifest.csv` | Size and SHA-256 of every input above |
| `inputs/sources.csv` | Every document read, with its address, filing date, the times it was read and how |
| `out/run_log.txt` | The main script's output |
| `out/redemption_votes.csv` | For each vote, its date and the date used for growth rates, the vote's date or, for the merger, the June 25, 2026 closing, then the public shares before, redeemed and left, the cash paid and where it comes from, the cash a share and the prices a share in the filings |
| `out/trust_by_year.csv` | The trust's balance at the start of each year from 2022 to 2025, its income, the sponsors' deposits, the cash taken out and the balance at the end, computed and reported |
| `out/trust_a_share.csv` | The trust's value a public share at the IPO (kind `ipo`) and at nine report dates (`report`), and the cash a share paid for the redemptions at the six votes (`redemption`), dated as in `redemption_votes.csv`. On `redemption` rows `amount_usd` is the cash paid and `public_shares` the shares redeemed |
| `out/usde_against_merger_cash.csv` | USDE's close at each session from June 26 against the merger's cash a share, and USDEW's close |
| `out/results.json` | The main results |
| `out/chart_tlgy_redemptions.svg` | The chart as a static SVG |
| `out/chart_preview.png` | The chart as an image |

## Names and terms

TLGY Acquisition Corp. was a special purpose acquisition company, a listed shell company formed to merge with a private business. It sold 23,000,000 units in its December 2021 IPO, each holding one Class A share, half a warrant and a contingent right to more warrants, and it held the IPO money in a trust account, the trust. A public share is a Class A share sold in the IPO, the only kind the trust could redeem. To redeem is to hand a public share back for a pro rata part of the trust, which public shareholders could do at each vote to extend TLGY's deadline and at the vote on the merger. The founder shares, TLGY's Class B shares, belonged to its sponsors and other founder shareholders and were left out of the calculation of the price a share. TLGY's 8-K on the fourth vote reported that the sponsors and one other founder shareholder had converted theirs into Class A shares, which could not be redeemed either. The sponsors paid a deposit into the trust for each extension. They changed in June 2024, when two CPC Sponsor Opportunities funds bought founder shares and other securities from the former sponsor and others. StablecoinX Inc. is the company TLGY merged with on June 25, 2026, under an agreement of July 21, 2025. USDE is its Class A stock on Nasdaq and USDEW its public warrants. An 8-K is a current report, a 10-Q a quarterly report, a 10-K an annual report and a proxy a proxy statement, all filed with the SEC.

Cash a share is the cash paid for the redemptions at a vote divided by the public shares redeemed. The cash is the amount TLGY's 10-Qs and 10-Ks give as taken from the trust to pay redeeming holders. The second vote's cash is the 2023 total for both 2023 votes less the first vote's. The merger's cash is the approximate figure in StablecoinX's 8-K on the closing. Growth a year compounds the change in the cash a share between two votes over the days between them, using vote dates, and the June 25, 2026 closing date for the merger.

## How the sources were read

TLGY's list of filings was read from EDGAR's submissions service at 07:56:00 UTC on October 12, 2026 and again at 07:57:18 UTC with the same result, and the rows of the forms used were written out and matched by SHA-256. The filings themselves were first searched between 07:58 and 08:02 UTC. The five extract files were made from 08:03:53 to 08:04:30 UTC, at 08:13 UTC, at 08:21 UTC, at 08:29 UTC and at 09:07 UTC, each written out from the browser and matched by SHA-256. The last set followed the first independent review. Documents read in more than one set were served identically each time. StockAnalysis's USDE history was read at 08:07:09 UTC and matches the October 9 read used for earlier reviews but for the October 9 volume. Its USDEW history, read at 08:07:39 UTC, matches the October 9 read exactly. Yahoo Finance's chart data was read at 08:07:54 UTC. None of the reads needed a login, and the browser downloaded nothing to disk.

## Limits

The cash figures are before taxes and trading costs, and the merger's comes from an approximate figure. The review does not follow what redeeming holders did with their cash, any over-the-counter trading in TLGY's shares before the merger, or what a warrant was worth at each vote. It counts shares, not holders. TLGY's 8-K on the March 10, 2026 merger vote counted requests to redeem 388,406 public shares, 8,685 more than the closing redeemed, and the filings read here do not say whether those 8,685 were withdrawn or redeemed at the fifth vote instead. That the share table's 393,538 includes the fifth vote's 13,817 is this review's reading, from the table's starting count, taken before the fifth vote, and the exact match of 13,817, which no filing states in words. TLGY's 10-Q for the second quarter of 2025 gives $39,113,394 for the fourth vote's redemptions, and its 10-K for 2025 shows $39,113,505 taken from the trust that year. The 10-K for 2025 gives $11.92 a share at December 31, 2024, while $44,332,605 over 3,717,207 shares comes to $11.93.

## Runtime used for publication checks

The reproduction scripts were verified with Python 3.12. Python 3.11 cannot parse some f-string expressions in the article checker.
