# USDe's redemptions after the rsETH exploit, read onchain, April 2026 with October 2025 for comparison

This folder holds the review behind `article_draft.md`. On April 18, 2026 an exploit released 116,500 rsETH from Kelp's rsETH adapter on Ethereum, and USDe's supply fell by more than a third over the next nine days. The review read USDe's total supply, the USDe held by sUSDe and its cooldown silo, sUSDe's assets, token supply and cooldown at the last block of every UTC day of two windows, September 30 to November 30, 2025 and January 31 to May 31, 2026, and every USDe mint and burn on each day from October 1 to November 15, 2025 and April 1 to May 15, 2026. It compares the nine days after the exploit with the nine days from October 10, 2025, ranks the falls in USDe's day-end supply since January 1, 2024, and checks Ethena's weekly attestations and its sUSDe staking ratio against the chain.

## Run it

```text
python3 redemption_waves.py
python3 make_chart_svg.py
python3 check_article_numbers.py
```

Python 3.8 or later and the standard library only. None of the scripts uses the network.

The first script reads the inputs and runs its 29 checks. If any check fails it writes `out/run_log_failed.txt` and stops before writing its tables. It builds the tables, `out/results.json` and `out/run_log.txt` in memory and writes them together at the end, so `out/` keeps the files of the last clean run. It confirms every input against its size and SHA-256 fingerprint in `inputs/manifest.csv`, the browser's files against the digests the browser computed, the two browser scripts against the digests recorded when the browser ran them, and `inputs/chain/day_reads.csv` against the digest its own read recorded. It checks that the state was read on every day of both windows at the day-end blocks of the supply series, that USDe's supply there equals the series, that the second archive RPC gave the same six values on every day, and that on every day USDe minted less USDe burned equals the change in total supply between the day ends, to the smallest unit. It then checks the exploit's block against the day ends, the cooldown at every day end, the attestation table against the sources file, the claims the article makes about rank and timing, and the matches between the update's sUSDe figures and the chain, and writes the tables. Every supply and flow is an integer of USDe's smallest unit, 10^-18 USDe, and every share an exact fraction. The second script draws `out/chart_usde_redemptions_april_2026.svg` from `out/chart_data.csv` and `out/results.json`. The third recomputes every computed figure in the article, its metadata, its key findings and the chart's text with separately written code in decimal arithmetic, checks the figures taken from sources against the sources file, exits with an error if a phrase no longer appears, and checks the article's punctuation, links, navigation, closing line and the addresses in the published files.

`out/chart_preview.png` is the SVG on a page of 840 by 506 pixels, rendered at twice that size, 1680 by 1012 pixels, for link previews. A headless browser rendered it, and no script here writes it.

## Read the sources again

| Script or page | Where it runs | What it reads |
| --- | --- | --- |
| `browser/redemption_waves_read.js`, `REDEMPTION_WAVES.run(dayBlocks, logDays)` | the developer console on a page with no content security policy, such as `https://example.com` | sUSDe's silo on two RPCs at the latest block, then at each day-end block six values on two archive RPCs, and each day's USDe transfers from and to the zero address on a third |
| `browser/bundle_files.js` | the same page, after the read | Nothing. It packs the files and their digests into one gzip-compressed bundle in base64 for copying out of the browser |
| Ethena Foundation governance forum, topics 791 and 759 | `https://gov.ethenafoundation.com/raw/791/1`, `/raw/759/1`, `/raw/759/3` and `/t/759.json` | Ethena's governance update for March and April 2026, the dynamic cooldown proposal and LlamaRisk's analysis of it |
| Aave governance forum, topic 24580 | `https://governance.aave.com/raw/24580/1` | The incident report on the rsETH exploit |
| Ethena's documentation | `https://docs.ethena.fi/technical-design/key-addresses.md`, `/technical-design/minting-usde/mint-and-redeem-key-functions.md`, `/technical-design/staking-usde.md`, `/technical-design/staking-usde/staking-key-functions.md` and `/protocol-overview/reserve-fund.md` | The contracts' addresses, that redeemed USDe is burned, how the cooldown, the silo and the vesting of rewards work, and what the Reserve Fund is |

`dayBlocks` is the list of `[day, block]` pairs from `inputs/chain/day_reads.csv` for the days of the two state windows, and `logDays` the days of the two flow windows. Every request is read-only, with no login and no key, and the scripts never send a transaction. An RPC is a public server that answers queries about a chain, and an archive RPC also serves past states. The read ran from 02:14:28 to 02:18:02 UTC on October 13, 2026. It used `https://eth.drpc.org` and `https://eth-mainnet.public.blastapi.io` for the state and `https://gateway.tenderly.co/public/mainnet` for the transfers, because the free plans of the first two did not serve transfer logs over a day of blocks. The first RPC's free plan took batches of at most three requests. The third limited its rate, and the nine requests it refused were retried until it answered, as `inputs/chain/request_failures.csv` lists. Two earlier versions of the read script, which tried other RPCs for the transfers, stopped without finishing, and nothing they read is used. The day-end blocks come from `inputs/chain/day_reads.csv`, carried unchanged from the USDe supply read made from 00:03 to 00:17 UTC on October 13, 2026 for the companion packet `ena-fee-switch-usde-supply-2026-10-12`. That read found each day's last block at or before 23:59:59 UTC, read USDe's supply there on two archive RPCs, and found every day-end block final after the read. Its script, `browser/usde_supply_read.js`, is in that packet. The silo's address was read at the latest block and taken to be the same contract on every day read, which Ethena's Staking USDe page supports by naming the same contract.

The read's files left the browser as one gzip-compressed JSON bundle of 23,756 base64 characters in 24 numbered lines, each with the first 12 hexadecimal characters of its SHA-256. A short helper typed into the same page, which is not part of the packet, showed each line as 100-character pieces with the first 8 hexadecimal characters of each piece's SHA-256. Every line was copied from the page's text piece by piece, each piece was checked against its digest, and the joined line against its 12. The joined bundle's SHA-256, `36111679dbd68047472dccc22cced0a872b95526a2deb1e3566013b67acab292`, and that of the JSON inside it, `b1a72a54a4cca693d300e8aef4fa94ae54ab062a9b1f4db57450dc51c2d168c8`, matched the browser's, and every file matched the digest the browser computed for it, which `inputs/chain/browser_digests.json` keeps.

The forum topics and the documentation were read in the same browser between 01:39 and 03:28 UTC on October 13, 2026. `inputs/sources.csv` lists every read. `inputs/web/redemption_sources_2026-10-13.txt` holds the passages used and the SHA-256 of each page or response. The passages are summaries with the sources' figures, not quotations, except the attestation table, whose figures are copied as published. `inputs/web/usde_chain_review_carried_2026-10-12.txt` carries, unchanged from the companion packet, the figures from the USDe chain review of October 12, 2026 that show USDe's total supply on Ethereum includes the USDe locked there to back USDe on other chains.

## Files

| File | What it holds |
| --- | --- |
| `article_draft.md` | The article |
| `metadata.json` | Title, headline, description and preview image |
| `layout.json` | Cutoff line, contents, chart label, dashboard link, published files and key findings |
| `redemption_waves.py` | The main script |
| `make_chart_svg.py` | The chart |
| `check_article_numbers.py` | The article's figures and page rules |
| `browser/redemption_waves_read.js` | The read |
| `browser/bundle_files.js` | The bundle for copying the files out of the browser |
| `inputs/chain/day_reads.csv` | USDe's total supply at the last block of each UTC day from January 1, 2024 to October 12, 2026, carried from the supply read |
| `inputs/chain/day_state.csv` | At each day end of the two windows, USDe's total supply, sUSDe's total assets and token supply, the USDe in the silo and held by sUSDe, sUSDe's cooldown in seconds, and whether the second RPC gave the same six values |
| `inputs/chain/day_flows.csv` | For each day of the two flow windows, the block range, the number of mints and burns, the USDe minted and burned and the largest single burn |
| `inputs/chain/run.json` | The run's times, the RPCs, the silo's address on both, counts and the SHA-256 of the list of transfers |
| `inputs/chain/request_summary.csv` and `request_failures.csv` | Every request of the read counted by host, kind and status, and each one that did not return 200 |
| `inputs/chain/browser_digests.json` | The SHA-256 of each file of the read, computed in the browser |
| `inputs/web/redemption_sources_2026-10-13.txt` | Summaries of the forum topics and Ethena's documentation, with their SHA-256, and the attestation table |
| `inputs/web/usde_chain_review_carried_2026-10-12.txt` | Figures carried from the USDe chain review of October 12, 2026, with the SHA-256 of its files, showing that USDe's total supply on Ethereum counts the USDe locked there to back other chains |
| `inputs/sources.csv` | Every source, with its address, read time and use |
| `inputs/manifest.csv` | Size and SHA-256 of every input |
| `out/daily_state.csv` | Each day end of the two windows, with the split of the supply, sUSDe's assets and token supply, the cooldown, and the day's mints and burns where read |
| `out/april_days.csv` | April 17 to April 30, 2026, day by day |
| `out/waves.csv` | The two nine-day waves compared |
| `out/largest_falls.csv` | The eight largest falls in day-end supply since January 1, 2024 over one, three, seven, nine and 30 days |
| `out/attestations.csv` | Each attestation against the day-end supply of its day and the day before |
| `out/staking_ratio.csv` | sUSDe's total assets and token supply against USDe's supply at six day ends |
| `out/chart_data.csv` | The chart's values |
| `out/results.json` | The figures the article uses |
| `out/run_log.txt` | The main script's last clean run |
| `out/chart_usde_redemptions_april_2026.svg` and `out/chart_preview.png` | The chart and its preview image |
