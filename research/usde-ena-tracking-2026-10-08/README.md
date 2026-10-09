# USDE against ENA, June 26 to October 8, 2026

These files reproduce every computed figure in the review of how closely USDE, the Class A stock of StablecoinX Inc. on Nasdaq, followed ENA, the Ethena token the company reports holding as its treasury. The review compares the 72 daily moves of USDE's close from June 26 to October 8, 2026 with ENA's moves over the same spans, priced at the stock's 4 pm New York close, by period and with other measures. It repeats the comparison with the ENA prices in this site's dashboard, splits each daily move at USDE's opening price, and follows mNAV at the close. The sources were read from October 6 to October 9, 2026 UTC.

No figure here is a forecast. Every number describes prices, holdings or share counts recorded in the window or reported by the company.

## Reproduce

From this directory, with Python 3 and the standard library only.

    python3 usde_ena_tracking_review.py
    python3 make_chart_svg.py
    python3 check_article_numbers.py

The first script reads the inputs and runs its checks. If any check fails it stops before writing anything, so `out/` keeps the tables of the last clean run. Otherwise it rewrites the tables in `out/`. It confirms every input against `inputs/manifest.csv`, that Kraken and DefiLlama answered with HTTP 200, that S&P Global's data holds the 73 sessions and that the first is the first trading day in the closing 8-K, that Kraken's file holds exactly the two 4-hour candles starting at 16:00 and 20:00 UTC for every day from June 25 to October 8, each with trades and a close between its low and high, that each CoinGecko price lies within the 600-second search width of its target time, and that Kraken's price at the close is within 1% of CoinGecko's on every session. It checks that the dashboard's series holds every session with S&P Global's closes, that its ENA price for each date is within 0.5% of Kraken's price at midnight UTC, that it counts 3,029,000,000 ENA on every date, and that mNAV recomputed from its inputs matches its own column. The second script draws the chart from `out/chart_data.csv` and `out/results.json` and stops if a point would fall outside the axes. The third recomputes the article's computed figures, those in its metadata and the chart's text with separately written code and exits with an error if a phrase no longer appears. None of them uses the network.

To read the prices again, open any page of `https://api.kraken.com/` in a browser and paste `browser/kraken_ena_fetch.js` into the developer console, then open any page of `https://coins.llama.fi/` and paste `browser/defillama_ena_fetch.js`. Each makes read-only GET requests and builds its input files and their SHA-256 in the page. Kraken returns only its 720 most recent candles of any interval, so a new read of 4-hour candles reaches back to 16:00 UTC on June 25 only until about October 23, 2026. A later read of DefiLlama's prices may differ if its price history changes.

The other two price files were saved by hand. `inputs/usde_daily_spglobal_stockanalysis.csv` holds the rows of StockAnalysis's USDE price history table, read in a browser. `inputs/dashboard_series_152e758.csv` holds, for each date from June 26, the date, USDE close, ENA price, Class A shares, ENA holdings and mNAV in the `series` of `docs/data.json` in the site's repository at commit 152e758. Its last row, October 9, is the dataset's price at the time of its update and is not used.

## Files

| File | What it is |
| --- | --- |
| `article_draft.md` | The article in the format the site's build reads. Headline, kicker, byline, then the body |
| `metadata.json` | Page metadata |
| `usde_ena_tracking_review.py` | The main script |
| `check_article_numbers.py` | Recomputes each computed figure and confirms the exact phrase appears in `article_draft.md`, `metadata.json` or the chart |
| `make_chart_svg.py` | Draws `out/chart_usde_ena.svg` |
| `browser/kraken_ena_fetch.js` | Reads Kraken's 4-hour ENA/USD candles and keeps those starting at 16:00 and 20:00 UTC |
| `browser/defillama_ena_fetch.js` | Reads CoinGecko's ENA prices through DefiLlama at 20:00 UTC and 13:30 UTC on each session |
| `inputs/kraken_enausd_4h_20utc_00utc.csv` | Kraken's 4-hour ENA/USD candles starting at 16:00 UTC, which close at 20:00, and at 20:00 UTC, which close at midnight, June 25 to October 8 |
| `inputs/kraken_fetch_log.csv` | The Kraken request, its time, status, size, the SHA-256 of the raw response and the candles returned |
| `inputs/ena_coingecko_via_defillama.csv` | CoinGecko's ENA price nearest 20:00 UTC on June 25 and on each session, and nearest 13:30 UTC on each session, with each price's own timestamp. The June 25 price is not used |
| `inputs/defillama_fetch_log.csv` | The two DefiLlama requests, their time, status, size, the SHA-256 of each raw response and the prices returned |
| `inputs/usde_daily_spglobal_stockanalysis.csv` | USDE daily prices and volume from StockAnalysis, sourced from S&P Global Market Intelligence. Its June 25 row appears to be TLGY Acquisition Corp.'s last session and is not used |
| `inputs/dashboard_series_152e758.csv` | The dashboard's USDE close, ENA price, Class A shares, ENA holdings and mNAV for each date, from its dataset at commit 152e758 |
| `inputs/filing_facts.csv` | The dashboard's ENA count, the 10-Q's ENA received at the merger and the first trading day, with their document and location |
| `inputs/manifest.csv` | Size and SHA-256 of every input above |
| `inputs/sources.csv` | Every document read, with its address, date, the time it was read and how |
| `out/run_log.txt` | The main script's output |
| `out/daily_moves.csv` | Each session's prices from every source, the daily moves, mNAV at the close, and the moves split at the open. The June 26 row holds prices only |
| `out/summary.csv` | Correlation, R squared, fitted slope, same-direction count and standard deviations for each measure, and the rank correlations |
| `out/chart_data.csv` | The chart data |
| `out/results.json` | The main results, with the confidence intervals, the tests between periods and the dashboard's own mNAV |
| `out/chart_usde_ena.svg` | The chart as a static SVG |

## Names and terms

USDE is the Class A stock of StablecoinX Inc. on Nasdaq. It first traded on June 26, 2026, according to the company's closing 8-K. ENA is the Ethena token the company reports holding as its treasury. The close is 4 pm New York time. Every date in the window fell in US daylight saving time, when 4 pm in New York is 20:00 UTC and 9:30 am is 13:30 UTC.

A daily move is the percentage change from one session's close to the next. ENA's daily move covers the same span, from 20:00 UTC to 20:00 UTC, so a move across a weekend or holiday spans the whole break. ENA's price at the close is the close of Kraken's 4-hour ENA/USD candle from 16:00 to 20:00 UTC. The dashboard's ENA price for a date is its price at midnight UTC at the start of that date, 8 pm in New York the evening before.

Correlation is Pearson's coefficient of the daily moves, R squared its square, and the fitted slope the least-squares slope of USDE's move on ENA's. Standard deviations use n − 1. The rank correlation is Spearman's, with tied values given their average rank. Same direction counts the moves where both rose or both fell, and a move where either price was unchanged counts in neither direction. The 95% confidence intervals and the tests between periods use Fisher's transformation of the correlation. Weekly moves run from the last session of one ISO week to the last of the next.

mNAV is USDE's close divided by the value of the ENA per share, which is ENA's price times the dashboard's 3,029,000,000 ENA divided by the dashboard's Class A shares. These figures use ENA at the close. The dashboard's own mNAV uses its midnight price.

The overnight move runs from one close to the next session's opening price, and the move during trading hours from the open to that day's close. For both, ENA comes from CoinGecko, at 20:00 UTC and at 13:30 UTC.

## How the sources were read

Kraken's candles were read in a browser from Kraken's public API at 17:28:52 UTC on October 9, 2026, and CoinGecko's prices from DefiLlama's public price API at 17:31:38 and 17:31:40 UTC. None of the requests needed a login. Each file was shown in the browser in parts and copied out, and the SHA-256 of every file matched the digest the browser computed. Kraken's and DefiLlama's documentation pages were read in the browser between 17:41 and 17:50 UTC. The dashboard's series was copied from its dataset at commit 152e758 at 17:35 UTC. EDGAR's list of the company's filings, NYSE's 2026 holiday calendar and the site's live research and methodology pages were read in the browser between about 18:28 and 18:30 UTC. The USDE daily prices from StockAnalysis, the closing 8-K and the resale prospectus were read for an earlier review between about 02:12 and 02:55 UTC on October 9, and the company's June 25 release and 10-Q for another at about 13:41 UTC on October 6. The browser downloaded nothing to disk.

## Limits

Correlation measures how closely the moves lined up and says nothing about what moved either price. The window holds 72 daily moves, and a few large days weigh heavily on the whole-window figures. ENA's price at the close comes from one exchange, checked against CoinGecko, and the prices at 13:30 UTC come from CoinGecko alone. The overnight figures use S&P Global's opening price and leave out USDE's extended-hours trading. mNAV holds the reported ENA constant across the window and leaves out cash, other assets, liabilities and the warrants.
