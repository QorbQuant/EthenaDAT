# EthenaPay repeat spending by week of first spend, to October 4, 2026

These files reproduce every computed figure in the review of whether EthenaPay wallets kept spending after their first spend event. The review groups the 797 wallets with a spend event from June 4 to October 4, 2026 by the week of their first spend and counts how many spent in each later week. It also counts the wallets with no spend event in the last two weeks and what they held. The spend data come from the chain recount that this site published with its EthenaPay adoption review, and the review read its other sources from October 6 to October 9, 2026 UTC.

No figure here is a forecast. Every number describes spend events and balances recorded on Avalanche C-Chain by the end of October 5, 2026 UTC.

## Reproduce

From this directory, with Python 3 and the standard library only.

    python3 ethenapay_repeat_spending_review.py
    python3 make_chart_svg.py
    python3 check_article_numbers.py

The first script reads the inputs and runs its checks. If any check fails it stops before writing anything, so `out/` keeps the tables of the last clean run. Otherwise it rewrites the tables in `out/`. It confirms every input against `inputs/manifest.csv` and the three chain files against the recount's own manifest. It also confirms that the recount ends at block 96,839,679 with its last spend event on October 5, that the spend file holds all 29,556 spend events and 820 spending wallets in the recount's summary, and that each wallet's first spend day matches the activity file. Its weekly spending wallets and spend events must reproduce the adoption review's published table for the ten weeks from July 27 to October 4, and its monthly figures the monthly table in that review's calculation files, from June to October 4. The second script draws the chart from `out/weekly_shares.csv`. The third recomputes the article's computed figures, those in its metadata and the chart's text with separately written code and exits with an error if a phrase no longer appears. None of them uses the network.

The recount script `chain_recount.cjs` produced the chain files for the adoption review. It reads the Routescan explorer API and a public Avalanche RPC node. The files are byte-identical to those in that review's download at https://ethenadash.com/research-assets/ethenapay-adoption-2026-10-05/calculation-files.zip, which also holds the recount script and its test.

## Files

| File | What it is |
| --- | --- |
| `article_draft.md` | The article in the format the site's build reads. Headline, kicker, byline, then the body |
| `metadata.json` | Page metadata |
| `ethenapay_repeat_spending_review.py` | The main script |
| `check_article_numbers.py` | Recomputes each computed figure and confirms the exact phrase appears in `article_draft.md`, `metadata.json` or the chart |
| `make_chart_svg.py` | Draws `out/chart_repeat_spending.svg` |
| `inputs/chain/spend_wallet_days.csv` | Every qualifying spend event through October 5, grouped by UTC day, balance snapshot segment and wallet, with the USDe in cents |
| `inputs/chain/wallet_activity.csv` | For each wallet that ever received USDe, its first receipt, its first spend and its USDe balance at block 96,815,525, 15:53:28 UTC on October 5 |
| `inputs/chain/meta.json` | The recount's summary, with its row counts, end block and balance check |
| `inputs/chain_manifest.csv` | The three rows of the recount's own manifest that cover these files, with their SHA-256, the script's SHA-256 and the time of the run |
| `inputs/adoption_review_weeks_wallets.csv` | The adoption review's published weekly table, for the cross-check |
| `inputs/adoption_review_months_wallets.csv` | The adoption review's monthly table from its calculation files, for the cross-check |
| `inputs/manifest.csv` | Size and SHA-256 of every input above |
| `inputs/sources.csv` | Every document read, with its address, date, the time of the read and how |
| `out/run_log.txt` | The main script's output |
| `out/first_spend_cohorts.csv` | Each week of first spend, its wallets and how many spent in each of the eight following weeks, with the shares. Blank cells are weeks that end after the cutoff |
| `out/weekly_shares.csv` | The chart data. For the pre-beta wallets and the first four beta cohorts, the wallets observed and spending in each week after their first spend |
| `out/first_spend_months.csv` | Wallets that first spent in June, July and August 1 to 30, with how many spent in September, in the last week and on one day only |
| `out/weekly_check.csv` | Weekly spending wallets and spend events from the recount files beside the adoption review's published figures |
| `out/monthly_check.csv` | Monthly spending wallets, first spends, wallets that had spent in an earlier month and spend events, beside the adoption review's figures |
| `out/results.json` | The main results, including the wallets with no spend event in the last two weeks and their balances |
| `out/chart_repeat_spending.svg` | The chart as a static SVG |

## Names and terms

A wallet is a smart-contract account that one of EthenaPay's two factory contracts created on Avalanche C-Chain. It appears in these files as a position number in creation order, never as an address, and one wallet is not necessarily one person. The only addresses in these files are three contracts in `meta.json` that the factories created with a plain CREATE, which the recount counts as infrastructure and not as wallets. A spend event is one AllowanceSpent log that a wallet emits for USDe sent to either of the two settlement addresses, the current one and a retired one. The files count events as logs, never by transaction hash, and leave out each settlement address's onward transfer to the card issuer.

A week runs from Monday to Sunday in UTC. A wallet's cohort is the week of its first spend event, and the wallet counts in week k if it had at least one spend event in the k-th week after its cohort's week. The last full week ends on Sunday, October 4, the cutoff, so the counts leave out spend events on October 5 except where they say so. The beta week is August 31 to September 6, which holds the beta's opening on September 1. The pre-beta wallets are the 131 whose first spend came from June 4 to August 30, and the beta cohorts are those from the beta week on. The last two weeks are September 21 to October 4.

## How this review read its sources

The chain recount ran in a browser on October 6, 2026 from 06:55:10 to 06:58:53 UTC, for the adoption review. On October 9 its three files matched byte for byte the files in that review's download in the site's repository at commit 152e758, and at 19:18:28 UTC the live download's SHA-256 matched the repository's. A public Avalanche RPC node gave the times of blocks 96,815,525, 96,839,679 and 96,839,680 at 19:21:39 UTC on October 9, which place the recount's last block at the end of October 5 UTC. The review read EthenaPay's FAQ in the browser at about 19:04 UTC on October 9 and again at 19:15:54 and 20:22:38 UTC. The adoption review read Ethena's post on the beta's opening and EthenaPay's post of September 28 on X on October 6. The review read the site's own pages from its repository at commit 152e758 and live on October 9. The browser downloaded nothing to disk.

## Limits

The beta admitted users in stages, so a cohort's size reflects admissions as well as demand. Only the cohort of the beta week has four later weeks in the data. Two weeks without a spend event is a short window for a card whose Daily Boost, according to the FAQ, needed one qualifying card transaction a month and applied to balances up to a cap. The site's cash-flow review found that spend events point to the moment a card is used. Balances come from one snapshot. The chain shows when a wallet spends and what it holds, and nothing about why.
