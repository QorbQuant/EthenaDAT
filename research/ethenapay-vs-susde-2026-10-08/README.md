# EthenaPay's reward and sUSDe, September 1 to October 8, 2026

These files reproduce every computed figure in the review that compares the rates EthenaPay's payments were set at on USDe with what sUSDe, Ethena's staked USDe, paid in the same days. The review reads every Deposit, Withdraw and RewardsReceived record of the staking contract on Ethereum from 00:00 UTC on August 30 to the end of October 10, 2026, takes sUSDe's share price at each UTC midnight, and works out its rate for each day and for September, October 1 to 8 and September 17 to October 8. EthenaPay's rates come from the site's Daily Boost review, which compared each EthenaPay reward payment with its wallet's average balance over the day the payment was for, and its tiers and caps from Ethena Pay's Pricing page, FAQ and Terms of Use, read on October 12, 2026 UTC.

No figure here is a forecast. Every number describes payments and prices recorded on Ethereum and Avalanche C-Chain by the end of October 10, 2026 UTC, except the contract's price and cooldown, read on October 12.

## Reproduce

From this directory, with Python 3 and the standard library only.

    python3 susde_vs_ethenapay_review.py
    python3 make_chart_svg.py
    python3 check_article_numbers.py

The first script reads the inputs and runs its checks. If any check fails it writes its log to `run_log_failed.txt` and stops before writing its tables, so `out/` keeps the tables of the last clean run. Otherwise it rewrites the tables in `out/`. It confirms every input against `inputs/manifest.csv`, and the chain files against `inputs/chain_manifest.csv` and the SHA-256 of `susde_read.cjs`. The second script draws the chart from `out/chart_points.csv` and `out/results.json`. The third recomputes the article's computed figures, those in its metadata and the chart's text with separately written code and exits with an error if a phrase no longer appears. None of them uses the network. `out/chart_preview.png`, the page's preview image, is the chart rendered in a browser at twice its size with a 20-pixel margin, so render it again after any change to the chart.

`susde_read.cjs` produced the files in `inputs/chain/`. It reads the Routescan explorer API for Ethereum mainnet. It ran in a browser, on a page of the explorer API, from 05:58:37 to 06:00:56 UTC on October 12, 2026, as `SUS.run(u => new Promise(r => setTimeout(r, 250)).then(() => fetch(u, { cache: 'no-store' })), console.log)` after `SUS.config.retryMs = 2000`, and returned the files as text. A first run without the pause stopped when one request failed six times in a row. The script runs the same way with Node 18 or later as `node susde_read.cjs`, which writes the files to `inputs/chain/`. Its synthetic test runs with `node test_susde_read.cjs susde_read.cjs` and needs no network. A rerun gives the same `events.csv`, `rewards.csv` and `midnights.csv`, and a `meta.json` that differs in its run times and in the contract's state at the time of the run.

The script is kept byte for byte as it ran, so its SHA-256 matches `inputs/chain_manifest.csv`, and three of its comments need a correction here. Its `walk()` follows the paging of the site's chain recount but gives up on a block range at 2,000 blocks rather than 20,000 and takes no start block. The files keep one address, the staking contract's, in `meta.json`. And the contract's state carries the latest block the explorer reported before and after the calls, which ran at the explorer's latest block, since it had refused a call at a past block, and were not pinned to one.

## Files

| File | What it is |
| --- | --- |
| `article_draft.md` | The article in the format the site's build reads. Headline, kicker, byline, then the body |
| `metadata.json` | Page metadata |
| `susde_vs_ethenapay_review.py` | The main script |
| `check_article_numbers.py` | Recomputes each computed figure and confirms the exact phrase appears in `article_draft.md`, `metadata.json` or the chart |
| `make_chart_svg.py` | Draws `out/chart_susde_vs_ethenapay.svg` |
| `susde_read.cjs` | The chain read that wrote `inputs/chain/`, in JavaScript for a browser or Node |
| `test_susde_read.cjs` | A synthetic chain with known answers for the paging and parsing in `susde_read.cjs` |
| `inputs/chain/events.csv` | Every Deposit, kind `d`, and Withdraw, kind `w`, record of the staking contract in the blocks read, with its block, block time, position in the block, and the USDe and sUSDe that changed hands in units of 10^-18 |
| `inputs/chain/rewards.csv` | Every RewardsReceived record in the same blocks, with the USDe paid into the contract in units of 10^-18 |
| `inputs/chain/midnights.csv` | The last block before each UTC midnight from August 31 to October 11, 2026, with its time and the next block's |
| `inputs/chain/meta.json` | The block range, counts, and the contract's convertToAssets of one sUSDe, totalAssets, totalSupply and cooldownDuration at the time of the run |
| `inputs/chain_manifest.csv` | Size and SHA-256 of each chain file, the SHA-256 of the script that wrote it and the time of the run |
| `inputs/dailyboost_results.json` | The Daily Boost review's results, for the rates EthenaPay's payments were set at, the days they changed, the days payments were missed or paid at a multiple, and the rates paid across all balances |
| `inputs/cashflow_results.json` | The cash-flow review's results, for the rewards paid for September and their rate on the average end-of-day balance |
| `inputs/terms_facts.csv` | The 18 facts taken from Ethena's documentation and from Ethena Pay's Pricing page, FAQ and Terms of Use, in paraphrase, with the section and the time of each read |
| `inputs/sources.csv` | Every source, its address, the date it speaks for, when it was read and what it was used for |
| `inputs/manifest.csv` | Size and SHA-256 of every input |
| `out/results.json` | Every computed figure in the article |
| `out/run_log.txt` | Each check and its result |
| `out/susde_daily.csv` | sUSDe's price at 00:00 UTC each day from August 31 to October 9, the next day's, the day's rate before and after compounding, the rewards paid into the contract that day and those that vested in it, the day's average USDe behind sUSDe, and the rate those vested rewards give on it |
| `out/periods.csv` | sUSDe's growth and rates for September, October 1 to 8, the parts of September either side of EthenaPay's rate change, September 17 to October 8 and August 31 to October 9 |
| `out/balances.csv` | EthenaPay's rate after compounding on example balances by tier, at its rates from September 17, beside sUSDe's for September 17 to October 8 |
| `out/reward_weeks.csv` | Each weekly reward amount, the time of its first payment and the week's total at 21 payments |
| `out/chart_points.csv` | The chart's daily rates |
| `out/chart_susde_vs_ethenapay.svg` | The chart |
| `out/chart_preview.png` | The chart rendered for the page's preview image |

No address of a staker or of an EthenaPay wallet, and no transaction hash, appears in the files. The staking contract's address appears in the article, `susde_read.cjs`, `inputs/chain/meta.json`, `inputs/terms_facts.csv` and `check_article_numbers.py`. `susde_read.cjs` also holds the three event topics, which are hashes of event signatures, not of transactions. `events.csv` gives each record's block and position in the block, from which an explorer would show its transaction.

## Definitions

- **sUSDe price.** The USDe divided by the sUSDe in a Deposit or Withdraw record of the staking contract, which follows ERC-4626. Records of less than 0.001 sUSDe are left out, 8 of 2,333, since one unit of the contract's rounding is a larger share of them.
- **Price at midnight.** The price on a straight line between the last record at or before 00:00 UTC and the first after it. Ethena's documentation said rewards were paid every 8 hours and vested evenly over the next 8 hours, and no payment, no end of a vesting window and no left-out record falls between the two records around any midnight, so the price runs in a straight line between them.
- **Rate after compounding.** The growth in the price over a period, compounded to a full year, (end / start) ^ (365 / days) - 1. **Rate before compounding.** (end / start - 1) x 365 / days.
- **USDe behind sUSDe.** The USDe that all sUSDe can be redeemed for, which rises with deposits and vested rewards and falls with withdrawals. The review starts it from one figure at 00:00 UTC on August 31, adds every deposit and vested reward and takes away every withdrawal, and averages the result over each UTC day. Each reward payment vests evenly over the 8 hours after it. The starting figure is what each day's rate implies, averaged over the 40 days from August 31 to October 9. For one day that is the day's vested rewards x 365 / the day's rate before compounding, less the day's average of what deposits, withdrawals and vested rewards had added since 00:00 UTC on August 31. Leaving out a deposit or withdrawal of 500,000 USDe at noon on September 5, September 20 or October 5 would widen the largest gap between the two rates past 0.001 of a point, which the main script checks.
- **Rate from the payments.** A day's vested rewards x 365 / the day's average USDe behind sUSDe, before compounding.
- **A day.** From 00:00 UTC to the next 00:00 UTC. **September.** From 00:00 UTC September 1 to 00:00 UTC October 1. **October 1 to 8.** From 00:00 UTC October 1 to 00:00 UTC October 9. **September 17 to October 8.** From 00:00 UTC September 17 to 00:00 UTC October 9, the days EthenaPay's rates held after the change.
- **EthenaPay's rates.** The rates its payments were set at. Each day's payment was the balance times the daily share of the rate, (1 + rate) ^ (1 / 365) - 1, as the Daily Boost review found, though in September payments were missed on some days and came to two or three times the usual amount on others. The base rate was 4.0% a year until September 16 and 4.5% from September 17. The Daily Boost was 1.0% on the first $5,000 of a Standard balance and 2.0% on Pro and VIP balances within their caps until September 15, and 0.5% and 1.5% from September 16. A balance B in a tier with cap C earns (1 + share(base) + share(Boost) x min(B, C) / B) ^ 365 - 1 a year after compounding.
- **Across all balances.** The Daily Boost review's figure, what the two reward accounts paid for the days divided by the USDe in EthenaPay wallets weighted by time, before compounding.
- **Break-even balance.** The balance at which EthenaPay's rate from September 17 equals sUSDe's rate after compounding over the same days, September 17 to October 8, cap x share(Boost) / (share(sUSDe) - share(base)), from unrounded rates.

## Limits

The rates are those of these days. sUSDe's changes with Ethena's weekly payments and with how much is staked, and Ethena Pay can change or end the Boost. The price at a midnight sits between records up to 3.4 hours apart. The starting figure for the USDe behind sUSDe is fitted to the rates, not read, since the explorer refused a call to the contract at a past block. The contract's totalAssets, totalSupply and price read on October 12 disagree with one another by 0.087%, so the explorer did not answer all three calls from one state, and only the price and the cooldown from that read are used in the article. The cooldown is the contract's setting on October 12, and earlier settings were not read. The comparison leaves out the time and fees of moving USDe between Avalanche and Ethereum, the wait of the cooldown and the Boost's monthly activity condition. The chain shows wallets, and one person may hold more than one.
