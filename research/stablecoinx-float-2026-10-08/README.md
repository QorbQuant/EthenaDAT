# StablecoinX float and ownership, as of October 8, 2026

Draft for review. Nothing in this folder has been published to ethenadash.com or pushed to a repository.

The article answers how many of StablecoinX's Class A shares could trade freely, who held the rest and when they can sell, and how much USDE traded against the freely tradable count. It rebuilds the freely tradable count in the company's resale prospectus of September 14, 2026 from the merger's share table, adds up the prospectus's selling stockholder and ownership tables, sets daily volume from June 26 to October 8, 2026 against the count, and lists the Form 13F reports that named Class A holders at June 30, 2026. The sources were read on October 9, 2026 UTC.

No figure here is a forecast. Share counts are as of the dates the filings give, and volume is a record of past trading.

## Reproduce

From this directory, with Python 3 and the standard library only.

    python3 stablecoinx_float_review.py
    python3 check_article_numbers.py
    python3 make_chart_svg.py

The first script reads the inputs, runs its checks, stops if one fails and rewrites the tables in `out/`. It confirms the pinned dashboard files against `inputs/manifest.csv`, that the merger's share table adds up to the 24,029,375 Class A shares, that the placement shares less Ethena's plus the TLGY shares kept by public holders equal the prospectus's 19,063,653 freely tradable shares, that the holders of the registered merger shares hold every Class B share, that the selling stockholder table adds up to its total, and that the two volume sources agree. The second script recomputes the article's computed figures and those in its metadata with separately written code and exits with an error if a phrase no longer appears, so rerun it after any edit to the text. The third draws the chart from `out/chart_turnover.csv`. None of them uses the network.

## Files in the download

| File | What it is |
| --- | --- |
| `article_draft.md` | The article in the format `scripts/build_research.py` reads. Headline, kicker, byline, then the body |
| `metadata.json` | Page metadata in the same shape as the published reviews. The two dates are placeholders |
| `stablecoinx_float_review.py` | The main script |
| `check_article_numbers.py` | Recomputes each computed figure and confirms the exact phrase appears in `article_draft.md` or `metadata.json` |
| `make_chart_svg.py` | Draws `out/chart_turnover.svg` in the site's palette |
| `inputs/filing_facts.csv` | Each filed count, date and percentage the scripts use, with its document and page |
| `inputs/merger_share_table.csv` | The share table on page F-16 of the resale prospectus, line by line |
| `inputs/holders_2026-08-28.csv` | Class A and Class B shares by holder group on August 28, 2026, with the directors' awards of September 30. Private individuals are grouped |
| `inputs/selling_stockholders_2026-08-28.csv` | The selling stockholder table on page 90, split into shares, stock units and warrants. Private individuals are grouped |
| `inputs/usde_daily_spglobal_stockanalysis.csv` | USDE daily prices and volume from StockAnalysis, sourced from S&P Global Market Intelligence, June 25 to October 8, 2026 |
| `inputs/usde_daily_yahoo.csv` | USDE daily volume and close from Yahoo Finance's chart data, June 26 to October 8, 2026 |
| `inputs/13f_june30_2026.csv` | Every Form 13F row for June 30, 2026 that names StablecoinX Class A shares or public warrants |
| `inputs/edgar_filings_2026-10-09.csv` | StablecoinX's EDGAR filing list from June 25 to October 8, 2026 |
| `inputs/data_1cc3b05.json` | The dashboard's dataset `docs/data.json` at commit 1cc3b05, generated 02:19:03 UTC on October 9, 2026 |
| `inputs/shares_out_1cc3b05.csv` | The dashboard's Class A share count history at the same commit |
| `inputs/manifest.csv` | Repository, path, commit, size and SHA-256 of the two dashboard files |
| `inputs/sources.csv` | Every document read, with its address, date, the time it was read and how |
| `out/run_log.txt` | The main script's output |
| `out/holders_reconciled.csv` | Class A shares by holder group with each group's status |
| `out/daily_volume.csv` | Each session's volume from both sources, the close and the running total as a multiple of the freely tradable count |
| `out/volume_by_month.csv` | Sessions, volume and average session by month |
| `out/votes_class_b.csv` | Class B shares and votes by holder |
| `out/form13f_class_a_june30.csv` | The seven managers that reported Class A shares for June 30, 2026 |
| `out/chart_turnover.csv` | The chart data |
| `out/results.json` | The main results |
| `out/chart_turnover.svg` | The chart as a static SVG |

## Review material in this folder only

`evidence_table.md`, `calculation_appendix.md`, `review_notes.md` and `source_log.md` hold the claim-by-claim sources, the working, the decisions for review and the timed source reads. `layout.json` is the site build's page layout. `out/chart_preview.png` is the chart rendered on the site's background for the page preview. None of these goes into the download.

## Names

StablecoinX Inc. trades on Nasdaq as USDE, and its public warrants as USDEW. Its Class A shares carry the economic rights and its Class B shares carry the votes. TLGY Acquisition Corp. is the blank-check company it merged with on June 25, 2026. StablecoinX Assets Inc., here SC Assets, is the private company the placement investors bought into before the merger. Ethena means Ethena OpCo Ltd. The TLGY Insiders are TLGY's sponsors, directors and officers. Freely tradable is the prospectus's term for shares that holders other than affiliates can sell without a registration.

## How the sources were read

The filings were read in a browser from 02:12 to 02:54 UTC on October 9, 2026, from the SEC's website. A script in the same browser rechecked the quoted phrases and their page numbers from 02:52 to 02:54 UTC. The charter, the bylaws, the notice of effectiveness, the form of lock-up agreement in the merger prospectus and Rule 144 were read from 03:21 to 03:23 UTC. The Form 13F rows come from each report's information table, read as XML at 02:36:59 UTC. StockAnalysis's history table was read at about 02:27 UTC and reread at 02:54:34 UTC with the same 73 sessions and the same total, and Yahoo Finance's chart data at 02:30:05 UTC. The browser made read-only requests, downloaded nothing to disk and used no login.

## Limits

The prospectus dates its share counts August 28, 2026. Sales by the selling stockholders, warrant exercises and vesting after that date can change which shares are freely tradable, and no filing read here reports any of them. Form 13F covers only managers above the SEC's threshold and only the last day of a quarter. Volume counts every trade, so it cannot show how many holders changed. The names of the placement investors are not in the filings read here. Private individuals named in the prospectus's tables are grouped in these files, and holders are labeled by their role, as in the article.
