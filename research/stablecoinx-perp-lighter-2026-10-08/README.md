# Lighter's STABLECOINX perp against USDE, August 26 to October 8, 2026

Draft for review. Nothing in this folder has been published to ethenadash.com or pushed to a repository.

The article answers whether Lighter's perpetual futures contract on USDE, the Class A stock of StablecoinX Inc., tracks USDE, and what its mark price showed while USDE was not trading. It compares the perp's hourly mark price and trades with USDE's daily opening and closing prices in the 31 sessions from August 26 to October 8, 2026, splits each of the 30 stretches between sessions into USDE's after-hours trading, the hours with no USDE trading and USDE's pre-market trading, and adds up the hourly funding payments. The sources were read on October 9, 2026 UTC.

No figure here is a forecast. Every number describes trading and payments that took place in the window.

## Reproduce

From this directory, with Python 3 and the standard library only.

    python3 stablecoinx_perp_review.py
    python3 check_article_numbers.py
    python3 make_chart_svg.py

The first script reads the inputs and runs its checks. If any check fails it stops before writing anything, so `out/` keeps the tables of the last clean run. Otherwise it rewrites the tables in `out/`. It confirms every input against `inputs/manifest.csv`, that Lighter's hourly series have one row for every hour, that Lighter's daily candles agree with the hourly ones, that Lighter's daily volume figure is never below the candles, that the two daily price sources for USDE give the same open and close for every session, and that Yahoo's hourly bars have the expected hours. For funding it checks that the median price implied by the payments, each payment's dollar value divided by its rate, sits within 2% of the mark. Lighter computes each payment from the index, which the inputs do not hold, so single payments can sit further away. Of the 1,037 non-zero payments, 14 imply a price more than 2% from the mark, and the run log reports the count. The second script recomputes the article's computed figures and those in its metadata with separately written code and exits with an error if a phrase no longer appears, so rerun it after any edit to the text. The third draws the chart from `out/chart_off_hours.csv`. None of them uses the network.

`out/chart_preview.png`, the page's social image, is the SVG rendered at twice its size with a 20-pixel margin, 1680 by 1012 pixels, on the site's background in a headless browser. No script in this folder makes it.

To read Lighter's data again, open any page of `https://mainnet.zklighter.elliot.ai/api/v1/` in a browser, paste `browser/lighter_fetch.js` into the developer console, and compare the SHA-256 of each file it builds with `inputs/manifest.csv`. Lighter serves history, so the same requests should return the same rows, though the two snapshot files describe the moment they are read. `browser/yahoo_fetch.js` and `browser/yahoo_hourly_fetch.js` do the same for Yahoo Finance's chart data. They compute a SHA-256 for each file but keep no request log. `browser/show_chunk.js` is the helper that showed each file in parts so it could be copied out of the browser and checked against its SHA-256.

## Files in the download

| File | What it is |
| --- | --- |
| `article_draft.md` | The article in the format `scripts/build_research.py` reads. Headline, kicker, byline, then the body |
| `metadata.json` | Page metadata in the same shape as the published reviews. The two dates are placeholders |
| `stablecoinx_perp_review.py` | The main script |
| `check_article_numbers.py` | Recomputes each computed figure and confirms the exact phrase appears in `article_draft.md` or `metadata.json` |
| `make_chart_svg.py` | Draws `out/chart_off_hours.svg` |
| `browser/lighter_fetch.js` | Reads Lighter's public market data and builds the Lighter inputs |
| `browser/yahoo_fetch.js` | Reads Yahoo Finance's daily chart data for USDE |
| `browser/yahoo_hourly_fetch.js` | Reads Yahoo Finance's hourly chart data for USDE, with pre-market and after-hours bars |
| `browser/show_chunk.js` | Shows a file in parts of whole lines, each with its SHA-256 |
| `inputs/lighter_candles_1h.csv` | Hourly trade candles for market 229 from 18:00 UTC on August 26 to 23:00 UTC on October 8, 2026. Open, high, low, close, contracts and dollar volume |
| `inputs/lighter_mark_1h.csv` | Hourly mark price candles from 17:00 UTC on August 26, with the number of samples in each hour |
| `inputs/lighter_funding_1h.csv` | Each hourly funding payment from 18:00 UTC on August 26 to 00:00 UTC on October 9. Dollar value per contract, rate in percent, and the side that paid |
| `inputs/lighter_candles_1d.csv`, `inputs/lighter_mark_1d.csv` | Lighter's daily candles, used to check the hourly ones |
| `inputs/lighter_metrics_1d.csv` | Lighter's daily open interest and volume figures for the market |
| `inputs/lighter_orderbookdetails.json` | Lighter's market snapshot at 13:30:27 UTC on October 9, as returned |
| `inputs/lighter_priceoracleinfo.json` | Lighter's price-source snapshot at 13:30:29 UTC on October 9, as returned |
| `inputs/lighter_fetch_log.csv` | Every Lighter request, its parameters, time and the SHA-256 of the raw response |
| `inputs/usde_daily_spglobal_stockanalysis.csv` | USDE daily prices and volume from StockAnalysis, sourced from S&P Global Market Intelligence |
| `inputs/usde_daily_yahoo.csv` | USDE daily prices from Yahoo Finance, the cross-check |
| `inputs/usde_hourly_yahoo.csv` | USDE hourly bars from Yahoo Finance with pre-market and after-hours prices, in New York time |
| `inputs/filing_facts.csv` | The freely tradable and Class A share counts, with their document and location |
| `inputs/manifest.csv` | Size and SHA-256 of every input above |
| `inputs/sources.csv` | Every document read, with its address, date, the time it was read and how |
| `out/run_log.txt` | The main script's output |
| `out/close_comparison.csv` | Each session's close against the perp's mark and last trade at 4 pm |
| `out/off_hours.csv` | Each stretch between sessions, the perp's mark at 4 pm, 8 pm, 4 am and 9 am New York time, USDE's extended-hours prices, the next open, and the mark's high and low from 8 pm to 4 am |
| `out/funding_by_week.csv` | Funding by week. Each payment counts in the week of the hour it closes, so the payment at 00:00 UTC on a Monday counts in the week before |
| `out/weekend_activity.csv` | Perp trading on each weekend, from 8 pm on Friday to 4 am on the next trading day, with the mark's high and low against Friday's close |
| `out/daily_activity.csv` | Perp trading by UTC day, Lighter's daily volume and open interest figures, and USDE's volume. Lighter's open interest figure is about twice the value of one side's open contracts, so it appears to count both sides |
| `out/chart_off_hours.csv` | The chart data |
| `out/results.json` | The main results |
| `out/chart_off_hours.svg` | The chart as a static SVG |

## Review material in this folder only

`evidence_table.md`, `calculation_appendix.md`, `review_notes.md` and `source_log.md` hold the claim-by-claim sources, the working, the decisions for review and the timed source reads. `layout.json` is the site build's page layout. `out/chart_preview.png` is the chart rendered for the page preview. None of these goes into the download.

## Names and times

Lighter is the crypto exchange that lists the contract, market 229, under the symbol STABLECOINX. The article calls it the perp, and each contract tracks one share. USDE is the Class A stock of StablecoinX Inc. on Nasdaq. The mark is Lighter's fair price for the perp, the price it uses to decide liquidations, and the index is Lighter's reading of USDE's price. USDE's open and close are its daily opening and closing prices in S&P Global Market Intelligence's data, for the regular session from 9:30 am to 4 pm New York time.

Lighter's data is in UTC. Every date in the window fell in daylight saving time, so New York time was UTC minus four hours. The mark at a given moment means the close of the hourly mark candle that ends at that moment. The article's 4 pm, 8 pm, 4 am and 9 am New York time are 20:00 UTC, 00:00 UTC the next day, 08:00 UTC and 13:00 UTC. The session hours are 9 am to 4 pm New York time on the 31 trading days. A weekend runs from 8 pm on Friday to 4 am on the next trading day, 56 hours, or 80 over Labor Day.

## How the sources were read

Lighter's market data was read in a browser on the Lighter API's own address, with read-only requests and no login, from 13:30:14 to 13:30:29 UTC on October 9, 2026. Each file was shown in the browser in parts and copied out, and the SHA-256 of every part and every whole file matched the digest the browser computed. Yahoo Finance's daily and hourly data were read the same way at 13:45:13 and 13:48:39 UTC. Lighter's documentation and Pyth's feed list were read in the browser between 13:50 and 14:00 UTC, and the four Lighter pages the article cites were reread between 14:47 and 15:06 UTC. The USDE daily prices from StockAnalysis, the prospectus and the dashboard's share count were read for the previous review at about 02:30 UTC on October 9. The browser downloaded nothing to disk.

## Limits

Lighter's price-source data reports only the current source, so this review cannot say which source set the index in each hour. Lighter's documentation does not say when the price feed counts as stale. Yahoo Finance's pre-market and after-hours bars carry prices but no volume, and its data had no after-hours trading on October 7 or 8. Lighter's daily volume figures add up to $1.54 million more than the trades in its hourly candles, and this review used the candles. The perp's history covers six weeks, and Lighter can change its margin, funding and price settings.
