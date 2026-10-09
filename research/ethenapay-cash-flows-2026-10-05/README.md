# EthenaPay cash flows, May 15 to October 5, 2026

Published on EthenaDash on 9 October 2026. These files reproduce the cash-flow review through October 5, 2026 UTC.

The article sorts every USDe transfer into or out of an EthenaPay wallet on Avalanche from May 15 to October 5, 2026 into deposits, withdrawals, card spend, reversals, yield and other rewards. It shows that those flows add up to the USDe held at the end of every day, works through October 5 line by line, and sets the rewards paid in September against the terms in the Ethena Pay FAQ. The daily flows come from the chain recount published with the EthenaPay adoption review, compared day by day with the dashboard's Dune-based dataset, and from checks made for this review on October 9, 2026 UTC.

No figure here is a forecast or a promised rate. The rates are realized averages over all the USDe held or spent in a period.

## Reproduce

From this directory, with Python 3 and the standard library only.

    python3 ethenapay_cash_flows.py
    python3 check_article_numbers.py
    python3 make_chart_svg.py

The first script reads the inputs, runs its checks, stops if one fails and rewrites the tables in `out/`. It confirms the pinned inputs against `inputs/manifest.csv`, that the change in USDe held equals the flows on each of the 144 days to the wei, that the dashboard's daily series matches the recount on all 143 days of the series to October 5, and that the September reward and cashback totals equal the checks made against the paying accounts. The second script recomputes every computed figure in the article and its metadata with separately written code and exits with an error if a phrase no longer appears, so rerun it after any edit to the text. The third draws the chart from `out/chart_bridge.csv`. None of them uses the network.

## Files in the download

| File | What it is |
| --- | --- |
| `article_draft.md` | The article in the format `scripts/build_research.py` reads. Headline, kicker, byline, then the body |
| `metadata.json` | Page metadata in the same shape as the published reviews. Publication and modification dates are recorded in UTC |
| `ethenapay_cash_flows.py` | The main script |
| `check_article_numbers.py` | Recomputes each computed figure and confirms the exact phrase appears in `article_draft.md` or `metadata.json` |
| `make_chart_svg.py` | Draws `out/chart_cash_flows.svg` in the site's palette |
| `inputs/daily_chain_62503a1.csv` | One row per UTC day from May 15 to October 5, 2026 of USDe flows, USDe held, spend events and wallet counts for EthenaPay wallets. The chain recount published with the adoption review, at commit 62503a1 of the dashboard's repository |
| `inputs/chain_meta_62503a1.json` | That recount's block range, counts, spend-event and settlement-transfer totals, payments to other destinations and its balanceOf check |
| `inputs/ethenapay_5faf41f.json` | The dashboard's EthenaPay dataset `docs/ethenapay.json` at commit 5faf41f, generated 15:30:06 UTC on October 8, 2026 |
| `inputs/dune_05_daily_metrics_eb01f5d.sql` | The dashboard's daily Dune query at commit eb01f5d of the ethenaPay repository, with the flow rules and the paying accounts |
| `inputs/dune_06_kpi_headline_eb01f5d.sql` | The dashboard's headline Dune query at the same commit |
| `inputs/manifest.csv` | Repository, path, commit, size and SHA-256 of the five files above |
| `inputs/chain_checks.csv` | The checks made for this review against the Routescan explorer, with method, time and result |
| `inputs/faq_facts.csv` | The Ethena Pay FAQ terms the article uses, paraphrased, with the section and the time each was read |
| `inputs/sources.csv` | Every document read, with its address, date, the time it was read and how |
| `out/run_log.txt` | The main script's output |
| `out/daily_flows.csv` | Each day's flows, internal transfers, USDe held and spend events in USDe to six decimals |
| `out/bridge_lifetime.csv` | The flows from May 15 to October 5 at full precision, with each as a share of deposits |
| `out/bridge_by_period.csv` | The flows before the beta, May 15 to August 31, and from September 1 to October 5 |
| `out/worked_day_2026-10-05.csv` | October 5 from the opening balance to the close |
| `out/september_rates.csv` | September's reward rate four ways, cashback against card spend with the payout window shifted zero to four days, and the reversal rate |
| `out/weekday_spend.csv` | Spend events and spend-event USDe by weekday from September 1 to October 5. Plain averages, which the article does not use because spend grew through the period |
| `out/chart_bridge.csv` | The chart data |
| `out/results.json` | The main results at full precision |
| `out/chart_cash_flows.svg` | The chart as a static SVG |

## Review material in this folder only

`evidence_table.md`, `calculation_appendix.md`, `review_notes.md` and `source_log.md` hold the claim-by-claim sources, the working, the decisions for review and the timed source reads. `layout.json` is the site build's page layout. `out/chart_preview.png` is the chart rendered on the site's background for the page preview. None of these goes into the download.

## Names and rules

EthenaPay is this site's name for Ethena Pay. USDe on Avalanche C-Chain, chain 43114, is `0x5d3a1Ff2b6BAb83b63cd9AD0787074081a52ef34`, with 18 decimals. The programme's contracts and accounts are these.

| Role | Address |
| --- | --- |
| Wallet factory, first | `0x313be708df16979d9e5fe9db5ac4969b8add7207` |
| Wallet factory, second | `0xac66ca9a79fb0d3c64cba44cd29610cd58602d6f` |
| Settlement address, current | `0x6070848bd19c37488d0516058f2933dd992733de` |
| Settlement address, retired | `0x3b3ffd99b87a2dee5ad244b75d5a8e266890fdb8` |
| Reward account labeled yield | `0xd0ec8cc7414f27ce85f8dece6b4a58225f273311` |
| Reward accounts labeled other rewards | `0xab2b06efa6179e624f5e3b08b64978df114ff24f` and `0xc9dd0d4351d3841a712f59cb4f1e88c3d500515b` |
| Cashback accounts, in AVAX | `0x37dea6fe8bc3d8d8c47fa3dac98c39a88585a71d` from July 15, 2026 and `0xfdc9d265ba3cdac512c7fe7e30417cc29487ff7b` from May 20 to July 14 |

The rules come from the dashboard's daily query and are applied in this order. A transfer between two EthenaPay wallets is internal. Into a wallet, USDe from a settlement address is a reversal, from the yield account yield, from either other-reward account other rewards, and from anything else a deposit. Out of a wallet, USDe to a settlement address is card spend and to anything else a withdrawal. USDe held is the running sum of deposits, reversals, yield and other rewards less withdrawals and card spend. A spend event is one AllowanceSpent log for USDe sent to a settlement address, counted once per log. Cashback is AVAX the cashback accounts send to wallets in successful plain calls, valued at the average AVAX price of the payout day.

## How the sources were read

The pinned inputs were copied from the two repositories at the commits named above. The Ethena Pay FAQ was read in a browser from 00:28 to 00:32 UTC on October 9, 2026, and the terms used are paraphrased in `inputs/faq_facts.csv`. The checks in `inputs/chain_checks.csv` used the Routescan explorer API for Avalanche, called from the API's own page in the same browser from 00:32 to 00:35 and 00:58 to 00:59 UTC, with a reread of one receipt at 01:09 UTC. The browser made read-only requests, downloaded nothing to disk and used no login. The dashboard page was read with a fetch tool at 01:02 UTC. Ethena's launch thread on X could not be read in the browser in this session. Its time comes from the post ID and its wording from the adoption review, which read it.

## Limits

The chain shows the USDe that moved and not the card account behind it, so authorized and settled amounts, fees, declined payments and the card's credit terms are outside these files. The chain records no reason for a reversal. No public source this review found says what each reward account pays for. The dollar value of cashback rests on Dune's average AVAX price for each payout day. Wallets are contracts and are not people. No EthenaPay wallet's address appears in these files. The addresses that do appear are the USDe and WAVAX token contracts, the programme's contracts and accounts, and four addresses that the recount or the query treats as not wallets.
