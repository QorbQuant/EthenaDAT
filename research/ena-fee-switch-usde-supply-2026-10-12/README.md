# USDe's supply against the ENA fee switch milestones, read onchain, October 12, 2026

This folder holds the review behind `article_draft.md`. ENA holders approved a schedule, the ENA fee switch, that sends a share of Ethena's revenue to buying back ENA once USDe's circulating supply reaches $7.5 billion, rising at $10, $15, $20 and $25 billion. The review read USDe's total supply on Ethereum at the last block of every UTC day from January 1, 2024 to October 12, 2026, computed the daily supply and its 14, 30 and 90 day trailing averages against the milestones, and rebuilt the backtest that Blockworks Advisory posted with the proposal.

## Run it

```text
python3 fee_switch_supply.py
python3 make_chart_svg.py
python3 check_article_numbers.py
```

Python 3.8 or later and the standard library only. None of the scripts uses the network.

The first script reads the inputs and runs its 21 checks. If any check fails it writes `out/run_log_failed.txt` and stops before writing its tables. It builds the tables, `out/results.json` and `out/run_log.txt` in memory and writes them together at the end, so `out/` keeps the files of the last clean run. It confirms every input against its size and SHA-256 fingerprint in `inputs/manifest.csv`, the browser's files against the digests the browser computed, the three browser scripts against the digests recorded when the browser ran them, and `inputs/chain/finality_check.json` against the digest the browser computed for it. It checks that the days run without a gap, that each day's block is the last at or before 23:59:59 UTC, that the second archive RPC gave the same supply and block hash on every day, that every day-end block was at or below the finalized block after the read, and that two RPCs gave the same supply at the read block. It then compares the series with the published facts, the first day above $7.5 billion, Blockworks Advisory's counts for four supply measures, its two peaks and its supply figure for August 27, 2026, and writes the tables. Every average is an exact fraction of USDe's smallest unit. The second script draws `out/chart_usde_supply_milestones.svg` from `out/chart_data.csv` and `out/results.json`. The third recomputes every computed figure in the article, its metadata, its key findings and the chart's text with separately written code in decimal arithmetic, checks the quoted figures against the source files, exits with an error if a phrase no longer appears, and checks the article's punctuation, links, navigation, closing line and the addresses in the published files.

`out/chart_preview.png` is the SVG on a page of 840 by 506 pixels, rendered at twice that size, 1680 by 1012 pixels, for link previews. A headless browser rendered it, and no script here writes it.

## Read the sources again

| Script or page | Where it runs | What it reads |
| --- | --- | --- |
| `browser/usde_supply_read.js`, `USDE_SUPPLY.run()` | the developer console on `https://eth.blockscout.com/api/v2/stats` | USDe's total supply and decimals at one recent block on two RPCs, the last block of every UTC day from January 1, 2024, and USDe's total supply at each on two archive RPCs, with the second's block hashes |
| `browser/bundle_files.js` | the same page, after the read | Nothing. It packs the files and their digests into one gzip-compressed bundle in base64 for copying out of the browser |
| `browser/finality_check.js`, `FINALITY_CHECK.run(blocks, wantSha)` | the same page, at least 13 minutes after the last day end | The finalized block on two RPCs and the hash of every day-end block again |
| Ethena Foundation governance forum, topic 830 | `https://gov.ethenafoundation.com/raw/830` and `/raw/830/<post number>` | The proposal, Blockworks Advisory's backtest, OAK Research's table and the notice that the vote passed |
| Snapshot's GraphQL API | `https://hub.snapshot.org/graphql`, proposal `0xcb6b9ed95bf0c64b6101ff7d3a770af86e07701d8419b541cf91a6894022f2a3` | The vote's dates, result, votes and quorum, and in a second query its text and voting strategies |
| The milestone table in post 1 | the image linked in `inputs/sources.csv` | The five milestones, the take rates and the illustration at a 6.0% protocol APY |
| Ethena's documentation | `https://docs.ethena.fi/overview/ena.md` and, for the reserve fund review of the same day, `https://docs.ethena.fi/protocol-overview/governance/risk-committee.md` | ENA, the Risk Committee's role in the fee switch and its members |

Every request is read-only, with no login and no key, and the scripts never send a transaction. An RPC is a public server that answers queries about a chain, and an archive RPC also serves past states. The read ran from 00:03:42 to 00:17:21 UTC on October 13, 2026, three minutes after the last day end. It used `https://ethereum-rpc.publicnode.com` and `https://eth.drpc.org` for the read block and `https://eth.drpc.org` and `https://gateway.tenderly.co/public/mainnet` for the day ends. The first archive RPC's free plan took batches of at most three requests. The second limited its rate, and every request it refused was retried until it answered, as `inputs/chain/request_failures.csv` lists. A day end is the last block at or before 23:59:59 UTC, found from block headers and checked against the next block's time. Because the last day ended only minutes before the read, `browser/finality_check.js` ran from 00:31:36 to 00:33:08 UTC. Both RPCs then reported block 26,179,923 as finalized, above the last day-end block, 26,179,841, and the SHA-256 of the 1,016 day-end block hashes read again equaled the read's.

The read's files left the browser as one gzip-compressed JSON bundle of 36,364 base64 characters in 37 numbered lines, each shown with the first 12 hexadecimal characters of its SHA-256 and copied from the page's text. Every line was checked against its digest. Lines 5 and 8 were misread on the first copy and read again, and lines 5, 8 and 15 to 36 were copied as 100-character pieces, each checked against the first 8 hexadecimal characters of its own SHA-256. The joined bundle's SHA-256, `5c76921479da17f5ccb32cf815b6b0269edacbd1e15f416d3fbb2baa8c99d580`, and that of the JSON inside it, `9a6e4b141b4a62b4720f08878db0b47084a4ae030e747b49942bf250201acc1f`, matched the browser's, and every file matched the digest the browser computed for it, which `inputs/chain/browser_digests.json` keeps. The finality check's file was copied as text and matched its browser digest, `98fd7d3ca05ba344d5f279953108d0debe9e25e73f5f7f2dfd94e1088ed7802e`, which `fee_switch_supply.py` checks.

The forum, Snapshot, the image and the documentation were read in the same browser between 23:58 UTC on October 12 and 00:01 UTC on October 13, 2026, and Snapshot's text and voting strategies, with post 1 again for comparison, at 01:07 UTC. Post 1 was searched once more at about 01:20 UTC for any account of how supply is measured. The Risk Committee page was read at 22:11 UTC on October 12 for the reserve fund review. `inputs/sources.csv` lists every read. `inputs/web/ena_fee_switch_sources_2026-10-13.txt` holds the passages used and the SHA-256 of each page or response. The passages are summaries with the sources' figures, not quotations. `inputs/web/usde_chain_review_carried_2026-10-12.txt` carries the figures from the USDe chain review of the same day that show the total supply on Ethereum includes the USDe locked to back other chains.

## Files

| File | What it holds |
| --- | --- |
| `article_draft.md` | The article |
| `metadata.json` | Title, headline, description and preview image |
| `layout.json` | Cutoff line, contents, chart label, dashboard link, published files and key findings |
| `fee_switch_supply.py` | The main script |
| `make_chart_svg.py` | The chart |
| `check_article_numbers.py` | The article's figures and page rules |
| `browser/usde_supply_read.js` | The read |
| `browser/bundle_files.js` | The bundle for copying the files out of the browser |
| `browser/finality_check.js` | The check that every day-end block was final |
| `inputs/chain/day_reads.csv` | Each day's last block, its time and the next block's, USDe's total supply there on the first archive RPC, and whether the second gave the same supply and block hash |
| `inputs/chain/read_block.csv` | The read block on two RPCs, with its time, hash, USDe's total supply and decimals |
| `inputs/chain/run.json` | The run's times, the RPCs, counts and the SHA-256 of the first archive RPC's day-end block hashes |
| `inputs/chain/finality_check.json` | The finalized block on two RPCs after the read and the SHA-256 of the day-end block hashes read again |
| `inputs/chain/request_summary.csv` and `request_failures.csv` | Every request of the read counted by host, kind and status, and each one that did not return 200 |
| `inputs/chain/browser_digests.json` | The SHA-256 of each file of the read, computed in the browser |
| `inputs/web/ena_fee_switch_sources_2026-10-13.txt` | Summaries of the forum topic, the Snapshot proposal, the milestone table and Ethena's documentation, with their SHA-256 |
| `inputs/web/usde_chain_review_carried_2026-10-12.txt` | Figures carried from the USDe chain review of the same day, with the SHA-256 of its files |
| `inputs/sources.csv` | Every source, with its address, read time and use |
| `inputs/manifest.csv` | Size and SHA-256 of every input |
| `out/daily_supply.csv` | Each day's block, supply, 14, 30 and 90 day averages and the take rate on the daily and 14 day measures |
| `out/milestones.csv` | Each milestone with its take rate, the published illustrations, the rise needed from the last day and the days each measure spent at or above it |
| `out/supply_measures.csv` | The backtest's counts for four measures, onchain and as published |
| `out/chart_data.csv` | The chart's values |
| `out/results.json` | The figures the article uses |
| `out/run_log.txt` | The main script's last clean run |
| `out/chart_usde_supply_milestones.svg` and `out/chart_preview.png` | The chart and its preview image |
