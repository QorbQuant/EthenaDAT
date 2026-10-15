# Ethena's reserve fund, read onchain, October 12, 2026

This folder holds the review behind `article_draft.md`. Ethena's key addresses page names the multisig wallet `0x2b5ab59163a6e93b4486f6055d33ca4a115dd4d5` on Ethereum as the Reserve Fund, a pool of assets kept to bear losses that would otherwise fall on USDe's backing. It is a Safe, a smart contract wallet whose transactions need signatures from 4 of its 10 owners. The review read the fund at Ethereum block 26,178,998, 21:10:59 UTC on October 12, 2026, and at the last block of every month from January 2024 to September 2026, rebuilt its history from every token transfer two explorers listed, and compared it with what Ethena and its Risk Committee published.

## Run it

```text
python3 reserve_fund_review.py
python3 make_chart_svg.py
python3 check_article_numbers.py
```

Python 3.8 or later and the standard library only. None of the scripts uses the network. `univ3.py` holds the Uniswap V3 position math that the main script imports.

The first script reads the inputs and runs its 45 checks. If any check fails it writes `out/run_log_failed.txt` and stops before writing its tables, so `out/` keeps the tables of the last clean run. It confirms every input against its size and SHA-256 fingerprint in `inputs/manifest.csv`, the browser's files against the digests the browser computed, the three browser scripts against the digests recorded when the browser ran them, and the public copies against the browser's files when those are present. It checks that two RPCs gave the same answers at the read block, that two archive RPCs gave the same answers at each month end, the Safe's settings, the Uniswap positions' owner and pool, and the Curve pool's coins. It compares the two explorers' transfer lists, checks that every transaction moving a tracked token is classified exactly once and fits the counterparties, tokens and directions its category allows, reconciles the transfers and sDAI's events with the balances read at all 33 month ends and the read block, checks that each position's own tokens net to what the fund still held, matches every Uniswap and Curve deposit and withdrawal with the contracts' records, values the fund, checks that the sources of its value add up to it exactly, and compares 35 published figures with the onchain values, allowing for each one's rounding. It then writes the tables. The second script draws `out/chart_reserve_fund_by_month.svg` from `out/chart_data.csv` and `out/results.json`. The third recomputes every computed figure in the article, its metadata, its key findings and the chart's text with separately written code, valuing the Uniswap positions with decimal square-root prices instead of `univ3.py`, exits with an error if a phrase no longer appears, and checks the article's punctuation, links, navigation, closing line and the addresses in the published files.

`out/chart_preview.png` is the SVG on a page of 840 by 506 pixels, rendered at twice that size, 1680 by 1012 pixels, for link previews. A headless browser rendered it, and no script here writes it.

## Read the sources again

| Script or page | Where it runs | What it reads |
| --- | --- | --- |
| `browser/reserve_fund_read.js`, `RESERVE_FUND.run()` | the developer console on `https://eth.blockscout.com/api/v2/stats` | The fund at one block on two RPCs, the Safe's settings, Blockscout's and Routescan's lists of the fund's token transfers, Blockscout's list of its transactions, sDAI, sUSDS, Curve and Uniswap events, and the same reads at every month end on two archive RPCs |
| `browser/safe_transactions.js` | the same page, after the read | Counts of the transactions sent to the Safe by status and method |
| `browser/bundle_files.js` | the same page, last | Nothing. It packs the files and their digests into one gzip-compressed bundle in base64 for copying out of the browser |
| Ethena's documentation | `https://docs.ethena.fi/protocol-overview/reserve-fund.md` and `https://docs.ethena.fi/technical-design/key-addresses.md` | The fund's purpose and address, the revenue share, and which of the fund's counterparties the key addresses page names |
| Ethena Foundation governance forum | `https://gov.ethenafoundation.com/raw/<topic id>` | The Risk Committee's allocations, published sizes and decisions |
| `eth_getCode` requests to `https://ethereum-rpc.publicnode.com` at the latest block | the developer console on the same page | The code of the fund, the Dev multisig and the 34 counterparties kept by address other than the zero address and the fund. No script in `browser/` performs this read, and `inputs/chain/code_check_2026-10-12.txt` records it |

Every request is read-only, with no login and no key, and the scripts never send a transaction. The read ran from 21:11:46 to 21:19:02 UTC on October 12, 2026. An RPC is a public server that answers queries about a chain, and an archive RPC also serves past states. The read used `https://ethereum-rpc.publicnode.com` and `https://eth.drpc.org` for the read block and `https://eth.drpc.org` and `https://gateway.tenderly.co/public/mainnet` for the month ends. The second archive RPC limited its rate, and every request it refused was retried until it answered, as `inputs/chain/request_failures.csv` lists. A month end is the last block at or before 23:59:59 UTC on the month's last day, found from block headers and checked against the next block's time.

sDAI's contract does not record a transfer when it issues or redeems shares, so explorers' transfer lists miss those changes. The read script read the fund's sDAI balance at 1,025 evenly spaced blocks from block 19,000,000 to the read block, about one a day, halved every interval whose ends differed until each change was pinned to one block, and read sDAI's Deposit and Withdraw records in those blocks. A change undone within one interval would not be seen, and the balances at all 33 month ends match the result.

The script keeps no transaction hashes, which it replaces with labels such as `tx-12` in order of first appearance, and replaces the address of every counterparty that Blockscout marks as not a contract with a label such as `eoa-3`. Contracts keep their address and Blockscout's name for them. Of the Safe's owners only their number is kept. A later read of the code of every counterparty kept by address found one, the sender of 0.01 CANA, whose code is an EIP-7702 delegation, which makes it an account rather than a contract. The public copies of the transfer lists and counterparties, the files ending in `_public.csv`, label it `eoa-20` and sort its row among the other labels, and `inputs/chain/code_check_2026-10-12.txt` records the read. Token names that contain a web address are replaced in `inputs/chain/tokens_public.csv`. The browser's `tokens.csv`, `transfers_blockscout.csv`, `transfers_routescan.csv` and `counterparties.csv` are not published, and the main script checks the public copies against them when they are present. The analysis reads the public copies, which differ from the browser's files only in that label, its row's place and those names. The month-end answers kept are the first archive RPC's. Of the second, only the SHA-256 the browser computed is kept, which equals the first's for every month.

The files left the browser as one gzip-compressed JSON bundle of 40,612 base64 characters in 41 numbered lines, each shown with the first 12 hexadecimal characters of its SHA-256 and copied from the page's text. Every line was checked against its digest. Line 20 was misread on the first copy and read again, and one character of line 33 was corrected after comparing the SHA-256 of each 100-character piece with the browser's. The joined bundle's SHA-256, `1fbb4d243648cf59fcae399a8a29b5914024c9579d130eb2b58ed9f855ca4132`, and that of the JSON inside it, `6278f38361493b6851c9edd049c301d5e25e69a238850c4495480a7fda454120`, matched the browser's, and every file matched the digest the browser computed for it, which `inputs/chain/browser_digests.json` keeps.

The documentation, the forum and the contract code of the counterparties were read in the same browser between 21:12 and 22:45 UTC, as `inputs/sources.csv` lists. The text files in `inputs/web/` hold the passages used and the SHA-256 of each page's text. The forum passages are summaries with the posts' figures, not quotations. Ethena's transparency dashboard redirected to a page saying that access was restricted, and it was not read.

## Files

| File | What it holds |
| --- | --- |
| `article_draft.md` | The article |
| `metadata.json` | Title, headline, description and preview image |
| `layout.json` | Cutoff line, contents, chart label, dashboard link, published files and key findings |
| `reserve_fund_review.py` | The main script |
| `univ3.py` | Uniswap V3 position math in exact integers, as the contracts compute it |
| `make_chart_svg.py` | The chart |
| `check_article_numbers.py` | The article's figures and page rules |
| `browser/reserve_fund_read.js` | The read |
| `browser/safe_transactions.js` | The count of the Safe's transactions |
| `browser/bundle_files.js` | The bundle for copying the files out of the browser |
| `inputs/classification.csv` | The category and episode of each of the 106 transactions that moved a tracked token, written for this review and checked by the main script |
| `inputs/chain/run.json` | The read block on both RPCs, the run's times, the RPCs, the Uniswap pool and positions, and counts |
| `inputs/chain/snapshot_reads.csv` | The 23 reads at the read block on each RPC |
| `inputs/chain/once_reads.csv` | The Safe's threshold, owner count, nonce and version, the positions' owner, the Curve pool's coins and every token's decimals |
| `inputs/chain/month_reads.csv` | The reads at each month end on the first archive RPC |
| `inputs/chain/month_sources.csv` | Each month end's block, its time and the next block's, both archive RPCs' block hashes and the SHA-256 of each one's answers |
| `inputs/chain/transfers_blockscout_public.csv` | Blockscout's 182 token transfers of the fund, public copy |
| `inputs/chain/transfers_routescan_public.csv` | Routescan's 216 token transfers of the fund, public copy |
| `inputs/chain/events.csv` | sDAI, sUSDS, Curve and Uniswap events of the fund |
| `inputs/chain/counterparties_public.csv` | Every counterparty, by address or label, with Blockscout's name for contracts, public copy |
| `inputs/chain/code_check_2026-10-12.txt` | The read of the counterparties' contract code |
| `inputs/chain/tokens_public.csv` | Every token either explorer listed, with names that contain a web address replaced |
| `inputs/chain/safe_transactions.csv` | The transactions sent to the Safe, counted by status, method and result |
| `inputs/chain/request_summary.csv` and `request_failures.csv` | Every request of the read counted by host, kind and status, and each one that did not return 200 |
| `inputs/chain/browser_digests.json` | The SHA-256 of each file, computed in the browser |
| `inputs/web/ethena_reserve_fund_docs_2026-10-12.txt` | Summaries of Ethena's Reserve Fund, Key Addresses and Risk Committee pages and the check of the fund's counterparties against the Key Addresses page |
| `inputs/web/ethena_governance_forum_2026-10-12.txt` | Summaries of the forum posts used, with the SHA-256 of each topic |
| `inputs/web/usde_chain_review_carried_2026-10-12.txt` | Figures carried from the USDe chain review of the same day, with the SHA-256 of its files |
| `inputs/sources.csv` | Every source, with its address, read time and use |
| `inputs/manifest.csv` | Size and SHA-256 of every input |
| `out/holdings.csv` | The fund's holdings and values at the read block |
| `out/sources_of_value.csv` | The fund's value split into inflows and the result of each kind of position or exchange |
| `out/month_end.csv` | The value at each month end by group, USDe's supply and the fund's share of it |
| `out/flows.csv` | Every transfer of a tracked token with its category |
| `out/episodes.csv` | The transfers grouped by episode and category, with the tokens sent and received |
| `out/risk_committee_comparison.csv` | 35 figures for the fund or one of its holdings that Ethena Labs, LlamaRisk, the Risk Committee's reserve fund group and Ethena's governance updates published, with their precision and the gap beyond rounding, against the onchain values |
| `out/unlisted_tokens.csv` | The 42 tokens the review left out, with each explorer's count of their transfers |
| `out/chart_data.csv` | The chart's values |
| `out/results.json` | The figures the article uses |
| `out/run_log.txt` | The main script's last clean run |
| `out/chart_reserve_fund_by_month.svg` and `out/chart_preview.png` | The chart and its preview image |
