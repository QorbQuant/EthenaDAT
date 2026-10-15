# StablecoinX's mNAV against four other crypto treasury companies at the October 9, 2026 close

This folder holds the review behind `article_draft.md`. It compares StablecoinX's mNAV, USDE's close divided by token NAV per share, with the same measure for Hyperion DeFi, Forward Industries, Strategy and Strive at 4 pm New York time on October 9, 2026, and explains why three other companies were left out. Token NAV per share is a company's token count from its SEC filings to October 9 times the token's last Kraken trade before 20:00 UTC, divided by its common shares from its filings.

## Run it

```text
python3 review_flagged_passages.py
python3 dat_mnav_review.py
python3 make_chart_svg.py
python3 check_article_numbers.py
```

Python 3.8 or later and the standard library only. None of the scripts uses the network.

The first script writes `inputs/filings/sec_window_review_2026-10-12.csv`, this review's reading of each passage that the search for later counts flagged, from rules that match the passages' words.

The second reads the inputs and runs its 159 checks. If any check fails it writes its log and stops before writing its tables, so `out/` keeps the tables of the last clean run. It confirms every input against its size and SHA-256 fingerprint in `inputs/manifest.csv`, and the files the browser scripts wrote against the digests the browser reported. It checks that all 69 quoted passages were recorded as found word for word in 24 SEC documents, that every count in `inputs/facts.csv` appears in its quoted passage, that the closes from Yahoo Finance match S&P Global Market Intelligence's on StockAnalysis to the cent, that Kraken's and CoinGecko's token prices are within 0.25% of each other, that Forward Industries' own net asset value and mNAV recompute from its table, that Hyperion DeFi's gross HYPE tokens are the sum of their parts, that every flagged passage has a reading and the only later count is the one used, and that the dashboard's own October 9 figure recomputes. It then writes the five companies, the alternative counts, the companies left out and the chart data.

The third draws `out/chart_mnav_peers.svg` from `out/companies.csv`. The fourth recomputes every computed figure in the article, its metadata, its key findings and the chart's text with separately written code that reads the counts from the quoted passages, exits with an error if a phrase no longer appears, and checks the article's punctuation, names, links, navigation and closing line.

`out/chart_preview.png` is the SVG on a page of 840 by 506 pixels, rendered at twice that size, 1680 by 1012 pixels, for link previews. A headless browser rendered it, and no script here writes it.

## Read the sources again

The scripts in `browser/` read the public sources again. Each runs in a browser's developer console on a page of the site it reads, makes read-only requests with no login, and leaves its files in a variable on the page with their SHA-256 digests.

| Script | Page to run it on | What it reads |
| --- | --- | --- |
| `browser/yahoo_closes_fetch.js` | `https://query1.finance.yahoo.com/` | Daily data for six stocks for October 8 and 9 |
| `browser/kraken_tokens_fetch.js` | `https://api.kraken.com/` | 1-hour candles for BTC, ETH, SOL, ENA and HYPE from 00:00 UTC on October 9 |
| `browser/defillama_tokens_fetch.js` | `https://coins.llama.fi/` | CoinGecko's prices at 20:00 UTC on October 9 |
| `browser/sec_filings_fetch.js` | `https://www.sec.gov/` | The first read of the filings and the EDGAR filing lists from September 1 to October 9 |
| `browser/sec_quotes_check.js` | `https://www.sec.gov/` | The 24 documents and the 69 quoted passages |
| `browser/sec_window_search.js` | `https://www.sec.gov/` | Every document that seven of the companies, all but Mega Matrix, filed from the dates of their counts to October 9, except insiders' and holders' forms, searched for later counts |
| `browser/sec_window_extra.js` | `https://www.sec.gov/` | The filings in the same windows with their 8-K items, and the text of the two PDFs among them |

The 15 documents read at 15:47 UTC and again at 17:19 UTC were the same byte for byte. A read at 16:08 UTC, since replaced, returned every document 363 bytes longer, so a document's SHA-256 can change between reads while its text does not. The quoted passages are what the review checks.

The search for later counts read 176 documents of the seven companies other than Mega Matrix, which is left out because its ENA was a small part of its digital assets. It cut each into sentences, kept those with a number next to the company's token or next to shares outstanding, and flagged any dated after the count used or undated in a filing made after it. It flagged 149 passages, and the only later count among them, Hyperliquid Strategies' 33.2 million HYPE on September 8, is the one the article uses. Six documents had no text to search as served. Two were PDFs, which `browser/sec_window_extra.js` read as text, and four had almost no text, three of BitMine's exhibits made of images and Hyperliquid Strategies' list of subsidiaries.

Kraken returns its most recent 720 candles, so its script reaches October 9 only until about early November 2026. Yahoo's and StockAnalysis's data can be revised.

## Files

| File | What it holds |
| --- | --- |
| `article_draft.md` | The article |
| `metadata.json` | Title, headline, description and preview image |
| `layout.json` | Cutoff line, contents, chart label, dashboard link, published files and key findings |
| `review_flagged_passages.py` | The readings of the flagged passages |
| `dat_mnav_review.py` | The main script |
| `make_chart_svg.py` | The chart |
| `check_article_numbers.py` | The article's figures and page rules |
| `inputs/facts.csv` | Every count and amount from the filings, with the quoted passage it comes from |
| `inputs/filings/sec_quotes_2026-10-12.csv` | The 69 quoted passages and whether each was found |
| `inputs/filings/sec_documents_2026-10-12.csv` | The 24 documents, their addresses, sizes and SHA-256 as served at 17:19 UTC |
| `inputs/filings/sec_fetch_log.csv` | The first read of the filings at 15:47 UTC and the EDGAR filing lists |
| `inputs/filings/sec_filings_2026-09-01_to_10-09.csv` | Filings of six companies from September 1 to October 9 |
| `inputs/filings/sec_window_documents_2026-10-12.csv` | Every document the search read, with its passage counts |
| `inputs/filings/sec_window_flagged_2026-10-12.csv` | The 149 flagged passages |
| `inputs/filings/sec_window_review_2026-10-12.csv` | The reading of each flagged passage |
| `inputs/filings/sec_window_filings_2026-10-12.csv` | Every filing in the windows, with 8-K items |
| `inputs/filings/sec_window_pdfs_2026-10-12.csv` | The two PDFs read as text |
| `inputs/prices/` | Yahoo's and StockAnalysis's closes, Kraken's candles and CoinGecko's prices, with fetch logs |
| `inputs/carried/form4_director_awards_2026-10-02.csv` | The five Forms 4 of September 30, carried from the share count update |
| `inputs/carried/stablecoinx_10q_facts_from_book_value_review.csv` | StablecoinX's 10-Q figures, carried from the book value review |
| `inputs/carried/dashboard_series_2c7c5a5_october.csv` | The dashboard's October rows at commit 2c7c5a5 |
| `inputs/carried/usde_ena_tracking_chart_data_2c7c5a5.csv` | The tracking review's chart data at commit 2c7c5a5 |
| `inputs/carried/site_review_passages_2c7c5a5.txt` | The passages of the tracking review and the lock-up waiver review the article relies on |
| `inputs/sources.csv` | Every source, its address, read time and use |
| `inputs/manifest.csv` | Size and SHA-256 of every input |
| `out/companies.csv` | The five companies' inputs and results |
| `out/variants.csv` | The alternative counts the article cites |
| `out/left_out.csv` | The three companies left out and why |
| `out/chart_data.csv` | The chart's values |
| `out/results.json` | All results with the inputs' SHA-256 |
| `out/run_log.txt` | Every check of the last run |
| `out/chart_mnav_peers.svg` | The chart |
| `out/chart_preview.png` | The chart as an image for link previews |

Analysis of public filings and market data. Not investment advice.
