# EthenaPay cashback, paid to October 9, 2026

These files reproduce every computed figure in the review of what EthenaPay's card cashback paid. The review reads every AVAX transfer that EthenaPay's two cashback accounts made to EthenaPay wallets on Avalanche C-Chain from the first on May 20, 2026 to the end of October 9, 2026 UTC, values each transfer from August 20 at the Chainlink AVAX / USD price in force when it arrived, and compares the cashback with each wallet's card payments, counted as spend events, and with the tier schedules on Ethena Pay's Pricing page, which the review read on October 12, 2026 UTC.

No figure here is a forecast. Every number describes transfers, card payments and prices recorded on Avalanche C-Chain by the end of October 9, 2026 UTC.

## Reproduce

From this directory, with Python 3 and the standard library only.

    python3 ethenapay_cashback_review.py
    python3 make_chart_svg.py
    python3 check_article_numbers.py

The first script reads the inputs and runs its checks. If any check fails it stops before writing anything, so `out/` keeps the tables of the last clean run. Otherwise it rewrites the tables in `out/`. It confirms every input against `inputs/manifest.csv`, the chain files against `inputs/chain_manifest.csv` and the SHA-256 of `cashback_recount.cjs`, and the chain read against the recount this site published with its EthenaPay adoption review. Every wallet's first USDe and its balance at block 96,815,525 must match that recount's `wallet_activity.csv`, and the daily flows and USDe held on all 144 days from May 15 to October 5 must match the daily file published with the cash-flow review, `daily_chain_62503a1.csv`, to the wei. The spend events to October 5, September's card payments and reversals, the cashback in September's batches and the cashback to October 5 must also match the cash-flow review's `results.json`. The second script draws the chart from `out/chart_points.csv` and `out/chart_lines.csv`. The third recomputes the article's computed figures, those in its metadata and the chart's text with separately written code and exits with an error if a phrase no longer appears. None of them uses the network.

`cashback_recount.cjs` produced the files in `inputs/chain/`. It reads the Routescan explorer API for Avalanche C-Chain. It ran in a browser, on a page of the explorer API, as `ECB.run(u => fetch(u, { cache: 'no-store' }), console.log)`, from 04:13:57 to 04:15:51 UTC on October 12, 2026, and returned the files as text. It runs the same way with Node 18 or later as `node cashback_recount.cjs`, which writes them to `inputs/chain/`. Its synthetic test runs with `node test_cashback_recount.cjs cashback_recount.cjs` and needs no network. A rerun gives the same data files, and a `meta.json` that differs only in its run times, unless the explorer's history of these blocks changes. Two earlier versions of the script ran on the same day. The first, from 03:17:49 to 03:18:01 UTC, priced each batch only at its first transfer and read neither what the two accounts received nor the spend events. The second, from 03:41:08 to 03:41:23 UTC, did not read the spend events. Both returned the same bytes for `prices_hourly.csv` and `batches.csv`, and the second the same `cashback.csv` and `other_recipients.csv`.

## Files

| File | What it is |
| --- | --- |
| `article_draft.md` | The article in the format the site's build reads. Headline, kicker, byline, then the body |
| `metadata.json` | Page metadata |
| `ethenapay_cashback_review.py` | The main script |
| `check_article_numbers.py` | Recomputes each computed figure and confirms the exact phrase appears in `article_draft.md`, `metadata.json` or the chart |
| `make_chart_svg.py` | Draws `out/chart_cashback_schedules.svg` |
| `cashback_recount.cjs` | The chain read that wrote `inputs/chain/`, in JavaScript for a browser or Node |
| `test_cashback_recount.cjs` | A synthetic chain of four wallets with known answers for the calculation in `cashback_recount.cjs`, including a transfer to a settlement address with no spend event and a spend event with no such transfer |
| `inputs/chain/spends.csv` | Every USDe transfer from a wallet to a settlement address, kind `c`, and back, kind `r`, from August 15, 2026, with the wallet's position, the block time, the amount in cents of USDe and, for kind `c`, `spend_event` 1 when an AllowanceSpent log matches it |
| `inputs/chain/cashback.csv` | Every cashback transfer from August 15, 2026, with the account, `0` for the current one and `1` for the earlier one, the batch, the wallet's position, the block time, the AVAX in wei, and from August 20 the Chainlink round in force and its answer with 8 decimals |
| `inputs/chain/batches.csv` | Every cashback batch of the two accounts from the first on May 20, 2026, with its first and last transfer, transfers, transactions, recipients and AVAX, and from August 20 the Chainlink round in force at its first transfer |
| `inputs/chain/other_recipients.csv` | Every transfer from the two accounts to an address that is not an EthenaPay wallet, numbered by recipient, with the AVAX the same account received in the same transaction |
| `inputs/chain/prices_hourly.csv` | The Chainlink AVAX / USD round in force on each hour from 00:00 UTC August 20 to 00:00 UTC October 10 |
| `inputs/chain/meta.json` | The read's block range and times, wallet counts, the USDe transfers to the settlement addresses, which it names `card_payments` here and in its `spend_events` fields, reversals, and spend events in all with how the spend events matched those transfers, every row the explorer returned for the two cashback accounts by kind, what each account received, the Chainlink feed and its rounds, and the two cross-checks |
| `inputs/chain_manifest.csv` | Size and SHA-256 of each chain file, the SHA-256 of the script that wrote it and the time of the run |
| `inputs/recount/wallet_activity.csv`, `inputs/recount/meta.json` | The chain recount's wallet file and summary, byte-identical to those in the adoption review's download |
| `inputs/recount/daily_chain_62503a1.csv` | The recount's daily flows to October 5, from the cash-flow review's download |
| `inputs/cashflow_results.json` | The cash-flow review's results, for its spend events to October 5, its September card spend, spend events, reversals and cashback, its cashback to October 5, its October 5 batch and the dashboard's rates for later windows |
| `inputs/terms_facts.csv` | The facts taken from Ethena Pay's Pricing page, FAQ and Terms of Use, in paraphrase, with the section and the time of each read |
| `inputs/sources.csv` | Every source, its address, the date it speaks for, when it was read and what it was used for |
| `inputs/manifest.csv` | Size and SHA-256 of every input |
| `out/results.json` | Every computed figure in the article |
| `out/run_log.txt` | Each check and its result |
| `out/months.csv` | Cashback by calendar month of payment, with wallets and dollars at Chainlink for September and October 1 to 9 |
| `out/september_windows.csv` | Cashback valued at Chainlink in the September window and in windows one to four days later, with the dashboard's rates for the same windows |
| `out/single_payments.csv` | The 216 isolated card payments, each with its time and amount, the number of cashback transfers in the six days after it and, for the 181 followed by exactly one, that transfer's time, AVAX, Chainlink price, value in dollars, the rate and the number of batches waited |
| `out/september_wallets.csv` | One row per wallet that made a card payment in September or was paid cashback from September 3 to October 1, with its card payments in the month and to September 28, its reversals, the cashback, what each tier's schedule pays on its spend to September 28, and the schedule it came within 5% of if it spent $4,000 or more by then |
| `out/spend_groups.csv` | The three groups by September card spend, with cashback, rates and the shortfall from 4% |
| `out/chart_points.csv`, `out/chart_lines.csv` | The chart's dots and schedule lines |
| `out/chart_cashback_schedules.svg` | The chart |

Wallets appear by position, their place in creation order, the numbering of the chain recount the adoption review published. No wallet's address and no transaction hash appears in the files. The two cashback accounts, the settlement addresses, the factories and the Chainlink feed are named in `cashback_recount.cjs`.

## Definitions

- **Wallet.** A contract that one of EthenaPay's two factory contracts created with CREATE2, 14,555 to the end of October 9. The factories also created 3 other contracts with a plain CREATE, which are not wallets.
- **Card payment.** A spend event, the AllowanceSpent log a wallet emits for USDe sent to either settlement address, as the dashboard counts it. Each is matched one to one to the USDe transfer in the same transaction from the same wallet to the same address for the same amount. One such transfer, 5 USDe on September 24, has no spend event and is left out. A card payment is not necessarily one purchase at a merchant. A **reversal** is a USDe transfer from either settlement address to a wallet.
- **Cashback.** An internal AVAX transfer, with value, from either cashback account to a wallet. An internal transfer is AVAX that a contract sends during a transaction. Transfers from the two accounts to any other address are counted apart and are not cashback.
- **Batch.** Cashback transfers from one account with no gap of more than three hours between them.
- **Price.** The answer of the latest Chainlink AVAX / USD round whose `updatedAt` is at or before the time, with 8 decimals. A transfer's value in dollars is its AVAX times that answer, divided by 10 to the 8th.
- **September.** The calendar month in UTC, for card payments and for the day a batch was paid. The wallet comparisons use card payments from September 1 to 28 and the cashback paid in the 29 batches from September 3 to October 1.
- **Isolated card payment.** A card payment of $1 or more from August 21 to October 2 with no other card payment from the same wallet within three days either side, no reversal to the wallet from three days before to six days after, and no cashback to it in the two days before. Its rate is the dollar value of the one cashback transfer that followed it within six days divided by the payment, when exactly one did. The two sensitivity runs widen the three-day windows to five or seven days, either side of the payment for other card payments and before it for reversals, and keep the six days after and the two days before.
- **Schedules.** The Pricing page's rates by tier on a calendar month's spend. Standard 4% to $2,500, 1% to $4,000 and nothing above. Pro 4.5% to $8,000, 2% to $10,000, 1% to $12,000 and 0.5% above. VIP 5% to $20,000, 2% to $30,000, 1% to $40,000 and 0.5% above. A wallet matches a schedule when its cashback comes within 5% of what the schedule pays on its spend.

## Limits

The chain shows which wallet was paid and when, not a user's tier, the merchant, the currency or the category of a purchase, or when a purchase settled. The waits between card payment and cashback come from the transfers. Card payments are counted before reversals. The window of September 3 to October 1 leaves out cashback paid from October 2 for the last card payments of September and takes in some cashback for the last days of August, so on balance the group rates are a little low. The pages read do not say whether the cashback month runs in UTC or by the date of purchase or settlement, so the calendar month in UTC is this review's assumption. The Pricing page read on October 12 was last updated on September 30, and earlier versions were not seen. The accounts may pay rewards other than cashback in AVAX, which the chain cannot separate.
