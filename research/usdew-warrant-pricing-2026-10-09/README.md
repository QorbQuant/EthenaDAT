# USDEW warrant pricing against the $10 call, June 29 to October 9, 2026

These files reproduce every computed figure in the review of how the market priced USDEW, StablecoinX Inc.'s public warrants. The review applies the make-whole table of the warrants' $10.00 call, from the warrant agreement that StablecoinX assumed on June 25, 2026, to USDE's close at every session from USDEW's first price in the source on June 29 to the October 9, 2026 close, and sets the resulting call value against USDEW's close. It also counts USDE's closes against the price test for a call, under the agreement's wording and the 10-Q's, and works out how many Class A shares a cashless call would create. The sources were read on October 9, 2026 UTC, and one section of the warrant agreement again just after midnight UTC on October 10.

No figure here is a forecast. The call value estimates what a holder would receive for one warrant in a $10.00 call at a session's close. No call had been made, and the agreement's price test for one had not been met by October 9.

## Reproduce

From this directory, with Python 3 and the standard library only.

    python3 usdew_warrant_pricing_review.py
    python3 make_chart_svg.py
    python3 check_article_numbers.py

The first script reads the inputs and runs its checks. If any check fails it stops before writing anything, so `out/` keeps the tables of the last clean run. Otherwise it rewrites the tables in `out/`. It confirms every input against `inputs/manifest.csv`, that the warrant terms in `inputs/filing_facts.csv` agree with each other, and that the agreement and the prospectus set the test at 20 closes within 30 trading days where the 10-Q's Note 9 says 10 within 20. It checks that USDE has 74 sessions from June 26 to October 9 and USDEW a close on all of them from June 29 but July 17 and August 18, and that both histories match the September 8 closes on the prospectus cover. It checks that the table has 21 rows and nine prices, rises with the price along each row and falls toward expiry down each column, holds the 0.361 cap in its $18.00 column, that below $18.00 it gives more than paying $11.50 would, and that the interpolation returns the table's own values at its rows and prices. It then checks the first close at or above $10.00, that no close reached $18.00, that USDEW never closed below its exercise value, the count of qualifying closes to October 9 and the date the 10-Q's wording would have been met, that USDEW closed below its call value from September 21 to October 7 with the redemption date 30, 60 or 90 days out, the three half-cent closes implied by the source's change column, and that the company's filing list holds nothing after October 2. The second script draws the chart from `out/usdew_by_session.csv`, `out/chart_curves.csv` and `out/results.json`, and stops if a dot from September 21 would sit on or above the call line. The third recomputes the article's computed figures, those in its metadata and the chart's text in exact fractions with separately written code, including its own trading calendar and interpolation, and exits with an error if a phrase no longer appears. None of them uses the network.

To read the price histories again, open StockAnalysis's history page for USDE or USDEW in a browser and paste `browser/stockanalysis_history_fetch.js` into the developer console. To parse the table again, open the prospectus on EDGAR and paste `browser/prospectus_table_fetch.js`. Each builds its file and SHA-256 in the page and downloads nothing. StockAnalysis can revise its latest rows, so a later read may differ in the last session's volume.

## Files

| File | What it is |
| --- | --- |
| `article_draft.md` | The article in the format the site's build reads. Headline, kicker, byline, then the body |
| `metadata.json` | Page metadata |
| `usdew_warrant_pricing_review.py` | The main script |
| `check_article_numbers.py` | Recomputes each computed figure and confirms the exact phrase appears in `article_draft.md`, `metadata.json` or the chart |
| `make_chart_svg.py` | Draws `out/chart_usdew_vs_usde.svg` |
| `browser/stockanalysis_history_fetch.js` | Reads a StockAnalysis price history table into CSV |
| `browser/prospectus_table_fetch.js` | Parses the make-whole table from the prospectus into CSV |
| `inputs/warrant_make_whole_table.csv` | The make-whole table, shares per warrant by months to expiry and by price from $10.00 to $18.00, as on page 95 of the prospectus and in Section 6.2 of the warrant agreement |
| `inputs/filing_facts.csv` | The warrant terms from the agreement, its June 25, 2026 amendment and the prospectus, the 10-Q's description of the test, the warrant counts, the Class A counts and the September 8 closes, each with its location |
| `inputs/usde_daily_stockanalysis_2026-10-09.csv` | USDE daily prices and volume from StockAnalysis, sourced from S&P Global Market Intelligence, April 9 to October 9. Rows before June 26, priced near $10 on small volume, appear to be TLGY Acquisition Corp.'s shares and are not used |
| `inputs/usdew_daily_stockanalysis_2026-10-09.csv` | USDEW daily prices, change and volume from the same source, June 29 to October 9. It has no row for July 17 or August 18 |
| `inputs/edgar_filings_2026-10-09.csv` | The 31 filings under StablecoinX's name from June 25 to October 2, 2026, as EDGAR listed them on October 9 |
| `inputs/manifest.csv` | Size and SHA-256 of every input above |
| `inputs/sources.csv` | Every document read, with its address, date, the time it was read and how |
| `out/run_log.txt` | The main script's output |
| `out/usdew_by_session.csv` | For each session from June 29, the two closes, exercise value, time value, USDEW's price in USDE shares, qualifying closes in the last 30 sessions, and from September 18 the redemption date, months to expiry, table shares, call value and USDEW against it |
| `out/chart_curves.csv` | The chart's two lines by USDE price, exercise value and the call value at October 9's months to expiry |
| `out/results.json` | The main results, with the redemption-date sensitivity and the half-cent closes |
| `out/chart_usdew_vs_usde.svg` | The chart as a static SVG |

## Names and terms

StablecoinX Inc. holds ENA, the governance token of the Ethena protocol, as its treasury. USDE is its Class A stock on Nasdaq and USDEW its public warrants, each of which buys one Class A share for $11.50 until 5 pm New York time on June 25, 2031. Exercise value is USDE's close less $11.50, or zero. Time value is USDEW's close less the exercise value.

A $10.00 call is the company's right, once USDE's last reported sale price has been at least $10.00 on 20 trading days within a 30-trading-day period ending on the third trading day before the notice, to buy back every public warrant for $0.10 on at least 30 days' notice. Holders may instead make a cashless exercise for the number of shares in the make-whole table. The 10-Q's Note 9 describes the test as 10 trading days within 20. The agreement governs, and the prospectus agrees with it. Table shares here are the table's value at a session's close for a redemption date 30 days after that session, and call value is table shares times the close. The agreement's table uses the volume-weighted average price over the ten trading days after a notice and the redemption date the company fixes, so the call value is an estimate. Between rows the interpolation runs by days between the dates 57 and 54 months before expiry, September 25 and December 25, 2026, as the agreement's straight-line rule on a 365- or 366-day year reads.

The closing 8-K of July 2 counted 11,499,988 public warrants outstanding, against the 11,500,000 issued. The share count of a cashless call uses the smaller number and does not round down fractional shares.

## How the sources were read

The resale prospectus was read in a browser from EDGAR at 23:00:17 UTC on October 9, 2026, and the make-whole table parsed from its text and matched by SHA-256. The script in `browser/` parsed the same table from the live page again at 23:14:44 UTC with the same hash. The warrant agreement was read at 23:45:37 UTC, and its Section 6.5 to the end at 00:14:26 UTC on October 10. Its June 25, 2026 amendment was read at 23:45:59 UTC. The closing 8-K was searched at 23:46:15 UTC, and the 10-Q at 23:06:33 UTC for the count of public warrants and at 23:46:34 to 23:46:54 UTC for Note 9. EDGAR's submissions list was read at 23:02:39 UTC and was byte for byte the list read at 21:02:31 UTC for an earlier review. StockAnalysis's USDE history was read at 23:03:14 UTC and its USDEW history at 20:55:36 UTC and again at 23:03:58 UTC, with the same file both times. None of the reads needed a login, and the browser downloaded nothing to disk.

## Limits

The call value stands the session's close in for the ten-day average after a notice and takes the earliest redemption date a notice that day allows. With a redemption date 90 days out the gaps on October 8 and 9 turn positive, by 0.3% and 0.2%. It leaves out what a warrant is worth if no call comes, trading costs and taxes. StockAnalysis rounds closes to the cent, and its change column implies half-cent USDEW closes on September 25, September 30 and October 8. The two closes are last trades and need not be simultaneous. StockAnalysis's October 9 rows were read about three hours after the close.
