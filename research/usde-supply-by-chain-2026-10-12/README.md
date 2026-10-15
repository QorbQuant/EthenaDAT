# USDe on every chain, reconciled with the USDe locked on Ethereum, October 12, 2026

This folder holds the review behind `article_draft.md`. USDe is Ethena's synthetic dollar. Ethena issues it on Ethereum and moves it to other blockchains, here called chains, through LayerZero, a protocol that carries messages between blockchains. On Ethereum the contract `0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34`, here the adapter, locks the USDe that leaves, and a contract on the other chain mints the same amount. A peer is the contract on another chain that the adapter sends messages to and accepts messages from. The review read, at about 18:41 UTC on October 12, 2026, the USDe the adapter held and the USDe on every chain for which a peer has ever been set on the adapter, and reconciled the two.

## Run it

```text
python3 usde_chains_review.py
python3 make_chart_svg.py
python3 check_article_numbers.py
```

Python 3.8 or later and the standard library only. None of the scripts uses the network.

The first script reads the inputs and runs its 44 checks. If any check fails it writes `out/run_log_failed.txt` and stops before writing its tables, so `out/` keeps the tables of the last clean run. It confirms every input against its size and SHA-256 fingerprint in `inputs/manifest.csv`, the browser's files against the digests the browser computed, and the two browser scripts against the digests of the code the browser ran. It checks the adapter's token, that it locks USDe, its shared decimals and its peers at the read block against the 49 PeerSet records that two explorers returned, and every chain's supply against the raw responses. It compares second sources, recomputes which LayerZero transfers were under way at the reads, reconciles the chains' USDe with the adapter's balance and checks the remainders below a millionth of a USDe. It then writes the tables. The second script draws `out/chart_usde_by_chain.svg` from `out/chart_data.csv` and `out/results.json`. The third recomputes every computed figure in the article, its metadata, its key findings and the chart's text with separately written code, exits with an error if a phrase no longer appears, and checks the article's punctuation, links, navigation, closing line and the addresses in the published files.

`out/chart_preview.png` is the SVG on a page of 840 by 506 pixels, rendered at twice that size, 1680 by 1012 pixels, for link previews. A headless browser rendered it, and no script here writes it.

## Read the sources again

| Script or page | Where it runs | What it reads |
| --- | --- | --- |
| `browser/usde_chains_read.js`, `USDE_CHAINS.run()` | the developer console on `https://arbitrum.publicnode.com/` | LayerZero's metadata, the adapter's PeerSet records from Blockscout and Routescan, Ethereum and every chain at one time, the peers of each chain's contract and the arrivals and departures recorded by the adapter's peer on Ethereal |
| `browser/usde_chains_read.js`, `USDE_CHAINS.messages(window.__u)` | the same page, at least five minutes later | LayerZero Scan's records of USDe transfers from 24 hours before the reads to 30 minutes after |
| `browser/usde_chains_confirm.js` | the same page, after the reads | Second reads for the chains with one answering RPC, Routescan's token supply for them and the Arbitrum contract's peers |
| `browser/redact_raw_reads.js` | the same page, after the second reads | Nothing. It makes `raw_reads_redacted.jsonl` from `raw_reads.jsonl` in the browser, keeping only each block's number, hash and time and the count of its transactions, and records the file's SHA-256 |
| Stellar Expert's asset page | `https://api.stellar.expert/explorer/public/asset/USDE-GDJ5BNU5NN6NQ54D7OX6NQTUYNBZ42CAT33QGM5BIQ2QIYADAC5ICH47-1` | USDe's supply on Stellar, which the first page could not fetch |

Every request is read-only, with no login and no key. The read ran from 18:41:27 to 18:47:07 UTC on October 12, 2026, the reads of the chains themselves from 18:41:47 to 18:42:16 UTC, the LayerZero Scan step at 18:48:21 UTC, the second reads from 18:52:16 UTC and the Stellar read at 18:41:49 UTC. The redaction ran in the browser console at about 18:53:51 UTC, before the files left the browser, and the unredacted `raw_reads.jsonl` stayed in the browser. The browser recorded the SHA-256 of `raw_reads_redacted.jsonl` but not of the redaction script, and `browser_run.json` does not record that step. The time comes from the session's log of the console call, and the script's SHA-256, `7b5d86bd8c10a030a1c0870ec276cb99706503c04785cd399fdf2fd90748e823`, was computed afterwards from the text sent to the console. The redaction parsed and wrote again every JSON-RPC response that has a result, so those stored responses are not byte for byte what the servers sent, and integers too large for JavaScript numbers were rounded, such as the `rentEpoch` field of the Solana mint read. Supplies, balances, blocks and peers are strings or hexadecimal text and are unaffected. The files left the browser as one gzip-compressed JSON bundle in base64. Each of its 518 lines was checked against its SHA-256 in the browser, and every file was checked against the browser's SHA-256 after decoding. `inputs/chain/browser_run.json` records the run.

The DefiLlama extract, the key addresses page and the adapter's verified source were read in the same browser later the same day, as `inputs/sources.csv` lists. The DefiLlama extract keeps the current figure for each chain, the last daily figure and the SHA-256 of the full response.

An RPC is a public server that answers queries about a chain. RPCs on free plans refused batches, limited request rates and kept recent state only, so the read checks every RPC's chain ID first and retries on the next RPC that answers for the chain. `inputs/chain/request_log.csv` lists every request of the main read, from 18:41:27 to 18:47:03 UTC, with its time and status. `inputs/chain/lzscan_queries.csv` lists the LayerZero Scan queries, `inputs/chain/confirm_supply.csv` the second reads and `inputs/sources.csv` the web pages. A second read of the same chains gives the same supplies unless a transfer arrives or leaves between the reads, which LayerZero Scan records.

## Files

| File | What it holds |
| --- | --- |
| `article_draft.md` | The article |
| `metadata.json` | Title, headline, description and preview image |
| `layout.json` | Cutoff line, contents, chart label, dashboard link, published files and key findings |
| `usde_chains_review.py` | The main script |
| `make_chart_svg.py` | The chart |
| `check_article_numbers.py` | The article's figures and page rules |
| `browser/usde_chains_read.js` | The read of every chain, the peers and the LayerZero Scan step |
| `browser/usde_chains_confirm.js` | The second reads |
| `browser/redact_raw_reads.js` | The step that made `raw_reads_redacted.jsonl` in the browser |
| `inputs/chain/ethereum.json` | Ethereum's block and time, USDe's supply, the adapter's balance, token, shared decimals and conversion rate, the PSM custodian's balance, the RPCs checked for each chain and the SHA-256 of LayerZero's metadata and of the two explorers' responses |
| `inputs/chain/chains.csv` | One row for each of the 36 chains, with its connection dates, the contract read, the decimals, the block and time read, the supply, the custodian's balance, the contract's peer for Ethereum and the second source |
| `inputs/chain/lz_chains.csv` | LayerZero's metadata for the 36 chains, their IDs and USDe addresses |
| `inputs/chain/peer_history.csv` | The adapter's 49 PeerSet records |
| `inputs/chain/adapter_peers_at_read.csv` | The adapter's peer for all 186 endpoint IDs at the read block, on two RPCs for the 36 chains |
| `inputs/chain/peer_matrix.csv` | The peers each contract on an EVM chain or Tron named at the read, for Ethereum and the other 35 chains |
| `inputs/chain/arbitrum_peers.csv` | The Arbitrum contract's peers from a second RPC, at its latest block |
| `inputs/chain/ethereal_flows.csv` | The arrivals and departures recorded by the adapter's peer on Ethereal, by chain |
| `inputs/chain/lzscan_messages.csv` | The 153 USDe transfers LayerZero Scan listed, with their blocks, times, statuses and amounts, and no addresses |
| `inputs/chain/lzscan_queries.csv` and `lzscan_window.json` | The LayerZero Scan queries and their window |
| `inputs/chain/confirm_supply.csv` | The second reads |
| `inputs/chain/stellar_expert_usde_asset.json` | Stellar Expert's record of USDe on Stellar |
| `inputs/chain/raw_reads_public.jsonl` | Every kept request and response, with each block's list of transactions replaced by its count, its fee recipient removed and the Initia account's resources left out |
| `inputs/chain/request_log.csv` | Every request of the main read |
| `inputs/chain/browser_digests.json` and `browser_run.json` | The digests the browser computed and the run's times and scripts |
| `inputs/web/adapter_source_2026-10-12.txt` | The adapter's verified source, its contract name and how it moves USDe |
| `inputs/web/defillama_usde_extract_2026-10-12.json` | DefiLlama's USDe by chain |
| `inputs/web/ethena_key_addresses_2026-10-12.txt` | The passages used from Ethena's key addresses page |
| `inputs/sources.csv` | Every source, its address, read time and use |
| `inputs/manifest.csv` | Size and SHA-256 of every input, and whether it is in the public download |
| `out/chains_table.csv` | The 36 chains with their status, dates, USDe, share of the locked USDe and the custodian's USDe, or `not read` where its balance was not read |
| `out/reconciliation.csv` | The reconciliation, exact and rounded |
| `out/in_transit.csv` | The transfer under way at the reads |
| `out/dropped_chains.csv` | The 11 dropped chains and the peers their contracts named |
| `out/defillama_comparison.csv` | The chains against DefiLlama's figures |
| `out/peer_timeline.csv` | Every peer set, changed or removed |
| `out/chart_data.csv` | The chart's values |
| `out/results.json` | All results with the inputs' SHA-256 |
| `out/run_log.txt` | Every check of the last run |
| `out/chart_usde_by_chain.svg` | The chart |
| `out/chart_preview.png` | The chart as an image for link previews |

The review copy also holds `inputs/chain/raw_reads_redacted.jsonl`, the same responses with the Initia account's resources, which name an address that may belong to a person. The main script checks that the public file is that file without that one line when both are present.

## Names and terms

Amounts ending in `_raw` are in each token's smallest unit. USDe has 18 decimals on Ethereum and the EVM chains, 9 on Solana, 7 on Stellar and 6 on TON, Aptos, Initia and Tempo. The bridge moves amounts in whole millionths of a USDe, its 6 shared decimals. Amounts in `out/` are in USDe, rounded half up to the millionth, and shares are worked out from the exact amounts.

The adapter's peers come from its PeerSet records. A chain is connected if its last record names a contract and dropped if its last record sets the peer to zero. A chain's supply is the total supply recorded for its USDe, read at one block, or for TON and Stellar the figure that services indexing those chains gave. Ethereal's USDe is its native coin, the coin it uses to pay for transactions, and the adapter's peer on Ethereal held none at the read, so its supply here is the USDe that the peer received less the USDe it sent, from the chain's first block to the read. Stellar's supply is Stellar Expert's figure for the asset whose contract LayerZero's metadata gives for USDe on Stellar. The PSM custodian is `0xd7fcade52afb60fbf0e1e5f72a683f43820f56a0`, the address Ethena's key addresses page gives for USDe minted in advance for its peg stability modules, contracts that swap USDe one for one with other stablecoins. A transfer was under way at the reads if the read of its sending chain came after it left and the read of its receiving chain came before it arrived, compared by block on Ethereum, the EVM chains, Tron and Solana and by time elsewhere.

Analysis of public blockchain data. Not investment advice.
