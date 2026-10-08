# StablecoinX lock-up waiver review, October 2026

Calculation files for the EthenaDash review published on 8 October 2026. Read the article at https://ethenadash.com/research/stablecoinx-lock-up-waiver-2026-10-05/

The article explains what the waiver of StablecoinX's ENA lock-ups, effective October 5, 2026, released and what it left in place, and how it changed the unlocked figures on the StablecoinX dashboard. Contract terms come from the token purchase agreements, the Collaboration Agreement, the DVN services agreement and the waiver letter as filed with the SEC. Dashboard figures come from two dated snapshots of the dashboard's dataset. Filings were read through October 8, 2026, and the dashboard rows run through the October 7 close.

No figure in this folder is a net asset value reported by the company. Token NAV is reported ENA times an ENA price and leaves out cash, other assets and every liability.

## Reproduce

From this directory, with Python 3 and the standard library only.

    python3 stablecoinx_waiver_review.py
    python3 check_article_numbers.py
    python3 make_chart_svg.py

The first script reads the inputs, runs its cross-checks, stops if one fails and rewrites the tables in `out/`. It rebuilds the dashboard's unlocked columns on all 69 rows of the first snapshot and all 72 rows of the second from the tranche file and stops if a row differs. The second script recomputes every computed figure in the article and its metadata with separately written code and exits with an error if a phrase no longer appears, so rerun it after any edit to the text. The third draws the chart from `out/chart_locked_schedule.csv`. None of them uses the network.

## Files

| File | What it is |
| --- | --- |
| `article_draft.md` | The article in the format `scripts/build_research.py` reads. Headline, kicker, byline, then the body |
| `metadata.json` | Page metadata in the same shape as the published reviews. The two dates are placeholders |
| `layout.json` | Cutoff line, section navigation, chart and dashboard links, public assets and the list of files for the download |
| `stablecoinx_waiver_review.py` | The main script |
| `check_article_numbers.py` | Recomputes each computed figure and confirms the exact phrase appears in `article_draft.md` or `metadata.json` |
| `make_chart_svg.py` | Draws `out/chart_locked_schedule.svg` in the site's palette |
| `evidence_table.md` | Each claim with its primary source, date and verification status. Review material |
| `calculation_appendix.md` | Inputs, timestamps, formulas, checks and the chart's source data. Review material |
| `review_notes.md` | Decisions, open questions and facts to check before publication. Review material |
| `source_audit.csv` | The text searches run against the filings on October 8, 2026, with the match count of each. In a pattern a space stands for any run of white space and a tilde for any run of punctuation. Review material |
| `inputs/ethenadat_data_4c7c3a7.json` | `docs/data.json` of the dashboard repository at commit 4c7c3a7, generated 00:59:25 UTC on October 5, 2026. The last snapshot before the waiver took effect. Its last row is the October 2 session |
| `inputs/ethenadat_data_e57e314.json` | `docs/data.json` at commit e57e314, generated 01:01:13 UTC on October 8, 2026. Its last row is the October 7 session |
| `inputs/ena_tranches_e57e314.csv` | The dashboard's tranche file. Identical at both commits |
| `inputs/manifest.csv` | Repository, path, commit, size and SHA-256 of the three files above |
| `inputs/filing_facts.csv` | Every number taken from a filing, with the filing and the place in it |
| `inputs/filing_dates.csv` | Every date taken from a filing |
| `inputs/sec_sources.csv` | Address, size and SHA-256 of each of the nine filing documents, raw and canonical. See below |
| `inputs/other_sources.csv` | The Ethena Foundation post, the SEC's Form 10-Q instructions, Rule 0-3 and the EDGAR filing list |
| `inputs/usde_spglobal_via_stockanalysis.csv` | USDE daily prices from StockAnalysis, sourced from S&P Global, for October 1 to October 7, 2026 |
| `inputs/ena_coingecko_via_defillama.csv` | CoinGecko ENA prices at 00:00 UTC on October 2, 5, 6 and 7, 2026, as served by DefiLlama |
| `out/run_log.txt` | The main script's output |
| `out/holdings_by_source.csv` | The company's ENA by source at the merger, with the lock-up the filings describe and the dashboard's treatment |
| `out/tpa_schedule.csv` | Every step of the old schedule on the filing counts and the dashboard's dates, with the count still locked before and after the waiver |
| `out/chart_locked_schedule.csv` | The chart data, on the dashboard's tranche sizes |
| `out/dashboard_before_after.csv` | The dashboard rows of October 2, 5, 6 and 7 with every figure in the article's table, and the same figures on the old schedule |
| `out/unlocked_multiple_bridge.csv` | The move in the unlocked multiple from October 2 to October 5, split into the stock, ENA and the unlocked count |
| `out/pre_waiver_bounds.csv` | The October 2 unlocked count on the dashboard's model and with the contribution and July in-kind ENA counted as locked |
| `out/results.json` | The main results at full precision |
| `out/chart_locked_schedule.svg`, `out/chart_preview.png` | The chart as a static SVG, and the same chart rendered on the site's background |

## Names

TPA-1 and TPA-2 in the scripts are the token purchase agreements of July 21, 2025 and September 5, 2025, Annexes H-1 and H-2 to the proxy statement and prospectus of February 17, 2026. The article calls them the July and September purchases.

The dashboard model is the unlock schedule in the dashboard's `fetch_data.py`. It dates the purchases July 31 and September 30, 2025, unlocks 25% 12 months later and the rest in 36 equal monthly steps, and clamps each step to the end of a short month. The old schedule is the same model with the waiver ignored.

Unlocked token NAV per share is unlocked ENA times the row's ENA price, divided by Class A shares. Unlocked mNAV is the USDE close divided by it. Both are columns in the dashboard's dataset.

The private placement is the PIPE in the filings. The in-kind tokens are ENA that placement investors delivered instead of cash.

## How the sources were read

The workspace this review was written in cannot reach sec.gov from its shell. Each filing document was fetched in a browser tab on sec.gov between 15:24 and 15:46 UTC on October 8, 2026, and its size and SHA-256 were computed there. The browser made read-only requests, downloaded nothing and used no login. The figures and terms in `inputs/filing_facts.csv` and `evidence_table.md` were confirmed by searching each document's text for the exact figure or term together with the words around it, up to 16:13 UTC. `source_audit.csv` lists the searches. The browser stopped responding after that, and a few later checks went through a fetch tool that returns a page as text. The evidence table says which.

sec.gov adds a script tag before the closing body tag of every HTML document it serves, and the tag's path changes over time. The raw bytes and their hash therefore change from one day to the next even though the filing does not. `inputs/sec_sources.csv` records both. The canonical hash is the SHA-256 of the served bytes with that one tag removed, which is the tag that matches `<script type="text/javascript" src="/...">` with an empty body.

The EDGAR filing list was read from the SEC's submissions file at 15:25 UTC on October 8, 2026. It showed 67 filings, the newest five Forms 4 filed on October 2, 2026.

The Ethena Foundation post was read in a browser at 15:37 UTC on October 8. The StockAnalysis prices and the SEC's Form 10-Q instructions and Rule 0-3 were read through a fetch tool that returns a page as text. The CoinGecko values were read from DefiLlama's price service in a browser at 15:59 UTC on October 8.

## Limits

The contract readings are of the documents as filed and are not legal advice. Two terms in the signed waiver letter are in square brackets.

The schedule for the 284,954,407.29 ENA that Ethena contributed is not in any filing read here, and neither is the split by unlock month of the 173,869,934.53 ENA paid in kind under the July 2025 placement. The October 2 figures in `out/pre_waiver_bounds.csv` show the two ends of the range.

The filings give the purchase dates two ways. The pro forma notes say each purchase was completed by the end of its month, and the dashboard uses the last day. The prospectus's summary dates the July schedule from on or shortly after July 21, 2025 and the September schedule from September 5, 2025. The count still locked on October 4 is the same for any date in those windows, and the script checks every one. The September 5 reading moves one monthly step onto October 5 and is computed separately.

The ENA counts are reported or contractual. No wallet balance was checked, and the filings read here give no wallet addresses for the treasury.

The dashboard's rows price ENA at 00:00 UTC, about 20 hours before each stock close.
