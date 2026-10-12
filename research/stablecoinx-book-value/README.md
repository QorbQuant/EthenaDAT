# StablecoinX book value at June 30, 2026

These files reproduce every computed figure in the review of StablecoinX Inc.'s book value per share. The review takes the balance sheet at June 30, 2026 from the company's second-quarter 10-Q, divides it by the Class A shares, checks how the 10-Q carries the company's ENA against Kraken's lowest trades, and sets book value and the market value of the ENA against USDE's close at every session from June 30 to October 8, 2026. It also reconciles the warrant liability, the restructuring of the former sponsors' notes and the Class A count after June 30. The sources were read from October 6 to October 9, 2026 UTC.

No figure here is a forecast. Every number comes from a filing, a price or a share count recorded in the window, or from arithmetic on them that the article labels, such as the derived Class A count from September 30 and the public warrants priced at USDEW's September 30 close.

## Reproduce

From this directory, with Python 3 and the standard library only.

    python3 stablecoinx_book_value_review.py
    python3 make_chart_svg.py
    python3 check_article_numbers.py

The first script reads the inputs and runs its checks. If any check fails it stops before writing anything, so `out/` keeps the tables of the last clean run. Otherwise it rewrites the tables in `out/`. It confirms every input against `inputs/manifest.csv`, that each figure in `inputs/filing_facts.csv` appears once and cites a source, and that the balance sheet adds up line by line. It checks that the three lots of ENA in Note 3 sum to 3,031,404,420.94 tokens and to the gross carrying amount in Note 7, at one price per token, that gross less impairments equals the balance sheet's ENA, and that the carrying value per token is within $0.00005 of Kraken's lowest trade from June 25 to June 30 and above it. It checks that the results release's $218.4 million and $9.09 per share reproduce with the 10-Q's token count, that the warrant liability equals the public warrants at USDEW's June 30 close, that the Tranche A and B warrant counts follow from the restructured notes, that this site's dataset agrees with S&P Global's closes and steps its Class A count by the directors' 110,000 shares on September 30, and that the company's filing list holds nothing after October 2. The second script draws the chart from `out/per_share_by_session.csv` and `out/results.json` and stops if a point would fall outside the axis or a start label would touch a line. The third recomputes the article's computed figures, those in its metadata and the chart's text with separately written code and exits with an error if a phrase no longer appears. None of them uses the network.

To read Kraken's daily candles again, open any page of `https://api.kraken.com/` in a browser and paste `browser/kraken_ena_daily_fetch.js` into the developer console. It makes one read-only GET request and builds the file and its SHA-256 in the page. Kraken returns only its 720 most recent candles of any interval, which for daily candles reaches back about two years. The last candle is the current UTC day and stays open until midnight UTC, so a new read matches the saved file through October 8 and not in its October 9 row.

The other files were saved by hand. `inputs/filing_facts.csv` holds each figure and policy taken from the filings, with its document and location. The two price histories hold the rows of StockAnalysis's USDE and USDEW price tables, read in a browser. `inputs/dashboard_series_dda5a00.csv` holds, for each date from June 26, the USDE and USDEW closes, ENA price, Class A shares, ENA holdings, token NAV per share and mNAV in the `series` of `docs/data.json` in the site's repository at commit dda5a00. Its last row, October 9, is the dataset's price at the time of its update and is not used. `inputs/edgar_filings_2026-10-09.csv` holds the company's filings from June 25, 2026, from EDGAR's submissions list.

## Files

| File | What it is |
| --- | --- |
| `article_draft.md` | The article in the format the site's build reads. Headline, kicker, byline, then the body |
| `metadata.json` | Page metadata |
| `stablecoinx_book_value_review.py` | The main script |
| `check_article_numbers.py` | Recomputes each computed figure and confirms the exact phrase appears in `article_draft.md`, `metadata.json` or the chart |
| `make_chart_svg.py` | Draws `out/chart_book_value.svg` |
| `browser/kraken_ena_daily_fetch.js` | Reads Kraken's daily ENA/USD candles from June 25, 2026 |
| `inputs/filing_facts.csv` | Balance-sheet lines, notes and policies from the 10-Q, figures from the results release of August 14, the 8-K of August 24, the resale prospectus of September 14, the closing 8-K of July 2 and the directors' Forms 4 of October 2, each with its location |
| `inputs/kraken_enausd_daily.csv` | Kraken's daily ENA/USD candles, June 25 to October 9, the last still open when read |
| `inputs/kraken_enausd_4h_20utc_00utc.csv` | Kraken's 4-hour ENA/USD candles starting at 16:00 UTC, which close at 20:00, and at 20:00 UTC, June 25 to October 8 |
| `inputs/usde_daily_spglobal_stockanalysis.csv` | USDE daily prices and volume from StockAnalysis, sourced from S&P Global Market Intelligence |
| `inputs/usdew_daily_spglobal_stockanalysis.csv` | USDEW daily prices and volume from the same source, June 29 to October 9. It has no row for July 17 or August 18 |
| `inputs/dashboard_series_dda5a00.csv` | This site's daily series at commit dda5a00 |
| `inputs/edgar_filings_2026-10-09.csv` | The company's 31 filings from June 25 to October 2, 2026, as EDGAR listed them on October 9 |
| `inputs/manifest.csv` | Size and SHA-256 of every input above |
| `inputs/sources.csv` | Every document read, with its address, date, the time it was read and how |
| `out/run_log.txt` | The main script's output |
| `out/balance_sheet.csv` | The June 30 balance sheet in the article's ten lines, in dollars, in millions and per Class A share |
| `out/per_share_by_session.csv` | For each session, USDE's close, ENA's price at 20:00 UTC, Class A shares, the ENA's market value and its value per share, book value per share, price to book and mNAV |
| `out/results.json` | The main results |
| `out/chart_book_value.svg` | The chart as a static SVG |

## Names and terms

StablecoinX Inc. holds ENA, the governance token of the Ethena protocol, as its treasury. USDE is its Class A stock on Nasdaq and USDEW its public warrants. Book value is total stockholders' equity, total assets less total liabilities. Book value per share divides it by the 24,029,375 Class A shares at June 30. The 10-Q leaves Class B shares out of loss per share, because they carry votes and no right to dividends or to assets in a liquidation.

The carrying value of ENA is the 10-Q's net amount for its digital intangible assets, cost less accumulated impairment. Token NAV is the ENA's market value, the 3,031,404,420.94 tokens in the 10-Q's three lots times ENA's price, and token NAV per share divides it by the Class A shares of that date. From September 30 that count is a derived 24,139,375, the 10-Q cover's 24,029,375 plus the directors' 110,000 restricted shares, which no filing states. ENA's price at the close is the close of Kraken's 4-hour ENA/USD candle from 16:00 to 20:00 UTC, which was 4 pm New York time on every date here. The output files call USDE's close divided by book value per share at June 30 price to book, and the article calls it times book value. They call USDE's close divided by token NAV per share mNAV, as the dashboard does, and the article calls it times token NAV per share.

The former sponsors are the sponsors of TLGY Acquisition Corporation, the blank-check company in the June 25 merger, and the Tranche A and B warrants are the warrants the company agreed to issue them on August 21 for most of their notes.

## How the sources were read

The 10-Q was read in a browser from EDGAR from 20:47 to 20:50 UTC on October 9, 2026, again from 21:03 to 21:12 UTC for Notes 4, 5, 6, 8 and 14 and the loss per share policy, and at about 21:54 UTC for Note 7. The results release was read at 20:51 UTC and again at about 21:56 UTC, and the 8-K of August 24 at 20:57 UTC and again at about 21:19 UTC. The resale prospectus of September 14 and the prospectus supplement of September 17 were searched for token counts at about 21:22 to 21:26 UTC. Kraken's daily candles were read from its public API at 20:52:04 UTC, and the script in `browser/` reproduced them at 21:16:25 UTC through October 8. The USDEW price table was read at 20:55 UTC and EDGAR's submissions list at 21:02 UTC. The USDE price table, Kraken's 4-hour candles, the closing 8-K, the resale prospectus and the directors' Forms 4 were read for earlier reviews between October 6 and October 9, and the dataset was copied from the site's repository at commit dda5a00. None of the reads needed a login, and the browser downloaded nothing to disk.

## Limits

The ENA count is the sum of the three lots the company reported receiving at the June 25 merger, and nothing here verifies a wallet balance. No filing read gives a count dated after the merger. The 10-Q's interim statements are unaudited. The company does not name the price source it uses for impairment, and its carrying value per token sits $0.00004 above Kraken's lowest trade, so its price was not Kraken's lowest ENA/USD trade. Book value per share stays at June 30's figure in every row, although cash, liabilities and the warrant liability changed after June 30. Token NAV leaves out cash, other assets, liabilities, the warrants and any tax on a sale of ENA.
