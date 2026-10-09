# Short selling in StablecoinX's Class A stock, June 26 to October 8, 2026

These files reproduce every computed figure in the review of short selling in USDE, the Class A stock of StablecoinX Inc. on Nasdaq. The review reads FINRA's short interest records for the seven settlement dates from June 30 to September 30, 2026, sets each against the freely tradable shares in the resale prospectus and against USDE's trading over the same reporting cycle, and compares them with FINRA's daily short sale volume for the 73 sessions from June 26 to October 8. It also estimates the sessions on which the SEC's short sale price test would have applied, using daily prices. The sources were read on October 9, 2026 UTC.

No figure here is a forecast. Every number describes positions, trades and prices recorded in the window.

## Reproduce

From this directory, with Python 3 and the standard library only.

    python3 stablecoinx_short_interest_review.py
    python3 make_chart_svg.py
    python3 check_article_numbers.py

The first script reads the inputs and runs its checks. If any check fails it stops before writing anything, so `out/` keeps the tables of the last clean run. Otherwise it rewrites the tables in `out/`. It confirms every input against `inputs/manifest.csv` and each FINRA short interest file against the hash of the response logged when it was read. From the fetch log it checks that all 74 daily files were read with HTTP 200, FINRA's header and a record count equal to the file's trailer. It checks that FINRA's daily files hold one USDE row for each of the 73 sessions, that the short volume includes the short exempt volume, that each short interest record's previous position equals the record before it, that no record carries a revision or split flag, that the final check matches the latest saved settlement date, and that FINRA's average daily volume is within 4% of S&P Global's in every cycle but the first. It also checks S&P Global's daily lows against Yahoo Finance's hourly bars from August 26 and that the price test logic marks the session after each trigger. The second script draws the chart from `out/chart_short_interest.csv` and `out/results.json`. The third recomputes the article's computed figures, those in its metadata and the chart's text with separately written code and exits with an error if a phrase no longer appears. None of them uses the network.

The whole daily files are not in this download. Their SHA-256, size and record count are in `inputs/finra_daily_fetch_log.csv`, so a fresh read can be checked against them.

To read FINRA's data again, open any page of `https://api.finra.org/` in a browser and paste `browser/finra_short_interest_fetch.js` into the developer console, then open any page of `https://cdn.finra.org/` and paste `browser/finra_daily_fetch.js`. Each builds its input files and their SHA-256 in the page. FINRA's daily files page says it may in rare cases update a file on a later day and marks such a file Updated. A new short interest settlement date adds records, and a record's revision flag marks a revision of the settlement date before it.

## Files

| File | What it is |
| --- | --- |
| `article_draft.md` | The article in the format the site's build reads. Headline, kicker, byline, then the body |
| `metadata.json` | Page metadata |
| `stablecoinx_short_interest_review.py` | The main script |
| `check_article_numbers.py` | Recomputes each computed figure and confirms the exact phrase appears in `article_draft.md`, `metadata.json` or the chart |
| `make_chart_svg.py` | Draws `out/chart_short_interest.svg` |
| `browser/finra_short_interest_fetch.js` | Reads FINRA's short interest records for USDE and USDEW from its public Query API |
| `browser/finra_daily_fetch.js` | Reads FINRA's daily short sale volume files for every session and keeps the USDE and USDEW rows |
| `inputs/finra_short_interest_usde.json` | FINRA's consolidated short interest records for USDE, as returned, with a final newline added |
| `inputs/finra_short_interest_usdew.json` | The same for the public warrants, USDEW |
| `inputs/finra_short_interest_metadata.json` | FINRA's field definitions for the short interest dataset, as returned |
| `inputs/finra_short_interest_fetch_log.csv` | Each short interest request, its body, time, status, size and the SHA-256 of the raw response |
| `inputs/finra_recheck_log.csv` | Later requests for the September 30 settlement date and the USDE records, with time, status, record count and size |
| `inputs/finra_daily_short_volume.csv` | The USDE and USDEW rows of FINRA's daily files, June 26 to October 8. Short, short exempt and total volume, and the reporting facilities |
| `inputs/finra_daily_fetch_log.csv` | Each daily file read, June 25 to October 8, with its time, status, size, SHA-256, header check, record count and trailer |
| `inputs/usde_daily_spglobal_stockanalysis.csv` | USDE daily prices and volume from StockAnalysis, sourced from S&P Global Market Intelligence. Its June 25 row appears to be TLGY Acquisition Corp.'s last session |
| `inputs/usde_hourly_yahoo.csv` | USDE hourly bars from Yahoo Finance from August 26, with pre-market and after-hours prices, in New York time |
| `inputs/filing_facts.csv` | The share and warrant counts and the resale registration's effective time, with their document and location |
| `inputs/manifest.csv` | Size and SHA-256 of every input above |
| `inputs/sources.csv` | Every document read, with its address, date, the time it was read and how |
| `out/run_log.txt` | The main script's output |
| `out/short_interest.csv` | Each settlement date's short interest, change, share of the freely tradable and Class A shares, close, value, cycle, average daily volume from both sources, days to cover and the short volume in FINRA's daily files over the cycle |
| `out/daily_short_volume.csv` | Each session's close, prior close, low, volume, the price test status estimated from the daily low, and FINRA's daily short sale volume |
| `out/chart_short_interest.csv` | The chart data |
| `out/results.json` | The main results |
| `out/chart_short_interest.svg` | The chart as a static SVG |

## Names and terms

USDE is the Class A stock of StablecoinX Inc. on Nasdaq, and USDEW its public warrants. USDE first traded on June 26, 2026. S&P Global's history for USDE includes a $9.40 close on June 25 on 145 shares, which appears to be the last close of TLGY Acquisition Corp., the listed blank-check company in StablecoinX's merger that day.

Short interest is the number of shares sold short and not yet bought back, as member firms report it to FINRA under Rule 4560 for each settlement date, in the middle and at the end of each month. A short sale counts once it has settled, one business day after the trade. A reporting cycle runs from the session after one settlement date to the next settlement date, the window FINRA uses for its average daily volume. Days to cover is short interest divided by the average daily volume over that cycle. FINRA shows its own figure as 1 whenever the result is at or below one day. The comparison of daily short volume with the change in short interest uses the trades that settled between the two dates, from the earlier settlement date through the session before the later one.

FINRA's daily short sale volume counts the regular-hours trades reported to its trade reporting facilities and published on the consolidated tape, with the part marked short. Its short volume includes the short exempt volume. The freely tradable shares are the prospectus's approximate count of 19,063,653 Class A shares that holders other than affiliates could sell without registration on August 28, 2026.

The SEC's short sale price test, Rule 201, applies once a stock falls 10% or more below the prior day's regular-hours close, for the rest of that day and all of the next, and the listing market decides when it is triggered. These files estimate a trigger when S&P Global's daily low is at or below 90% of the prior close. The columns `price_test_triggered_by_daily_low` and `price_test_in_effect_by_daily_low` hold that estimate, and the June 26 row uses the $9.40 close of June 25 as its prior close.

## How the sources were read

FINRA's daily files were read in a browser on FINRA's file server from 15:50:03 to 15:51:16 UTC on October 9, 2026, and the short interest records on FINRA's Query API at 15:54:29 and 15:54:32 UTC. None of the requests needed a login. Each file was shown in the browser in parts and copied out, and the SHA-256 of every file matched the digest the browser computed. The September 30 settlement date was checked again at about 15:59, at 16:16 and at 17:03 UTC and had no records. FINRA's pages, its 2019 notice on short sale volume and the SEC's pages on Rule 201 and on settlement were read in the browser between 16:50 and 17:05 UTC. FINRA's file layout PDF could only be read through a tool that returns a summary. The USDE daily prices from StockAnalysis, the prospectus and the dashboard's share count were read for an earlier review at about 02:30 UTC on October 9, and Yahoo Finance's hourly bars at 13:48:39 UTC. The original browser session downloaded nothing to disk. During publication review, direct HTTPS POST requests to the public FINRA Query API at 20:37:09 and 20:37:10 UTC on October 9 returned seven USDE and USDEW records, including September 30. Those raw responses replace the earlier six-record inputs, and their hashes, sizes and timestamps are recorded in the updated fetch log and manifest. The recheck log retains the earlier empty checks and appends the successful reads.

## Limits

FINRA's September 30 figures were published on October 9 and included in this review; they do not establish the short position at the October 8 close. Short interest does not say who held the positions, why, or what borrowing the shares cost. FINRA's daily files cover only regular-hours trades reported to its facilities and published on the tape, so they omit exchange trades, extended-hours trades and some trades that offset a short sale. The freely tradable count dates from August 28 and is approximate. The price test count rests on S&P Global's daily lows, checked against Yahoo Finance's regular-session prices only from August 26, and it uses TLGY's apparent last close as the prior close on USDE's first day.
