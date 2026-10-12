# What EthenaPay's card cashback paid

Reward review / Cashback paid to October 9, 2026

By [Qorban Ferrell · @Degenerate\_DeFi](https://ethenadash.com/about/) · Published 12 October 2026 · Cashback read to the end of October 9 UTC · Sources read October 12, 2026 UTC

EthenaPay card payments that could be matched one to one with a cashback transfer earned a median 3.98%, close to the 4% that Ethena Pay's [Pricing page](https://pay.ethena.fi/pricing) gives the Standard tier's first band, and heavy spending earned much less. EthenaPay is this site's name for Ethena Pay, Ethena's payment app and card. A card payment is a payment of USDe, Ethena's synthetic dollar, from an EthenaPay wallet, a smart-wallet contract on the Avalanche blockchain, to the card programme, and cashback arrives in AVAX, Avalanche's native token.

The Standard schedule pays 4% on the first $2,500 of card spend in a calendar month, 1% on the next $1,500 and nothing above $4,000, so its cashback stops at $115 a month. Twenty-eight wallets that spent from $4,161.54 to $47,670.88 by card in September 2026 were paid between $109.39 and $119.92 for the month. In all, the 4,595.29 AVAX of cashback paid in September was worth $41,604.25 at the AVAX price that Chainlink's price feed showed when each transfer arrived, 2.62% of the month's $1,588,430.13 of card spend.

The wallets are the smart-wallet contracts that EthenaPay's two factory contracts deployed, as the site's [adoption review](https://ethenadash.com/research/ethenapay-adoption-2026-10-05/) counts them. Each card payment is a spend event, the AllowanceSpent record a wallet emits when it sends USDe to one of two settlement addresses, the contracts that pass card payments on to the card issuer, as the site's [spend-events guide](https://ethenadash.com/research/ethenapay-spend-events/) explains. The chain shows card payments, not receipts, so one card payment need not be one purchase at a merchant. Cashback comes from two cashback accounts, and Ethena Pay's terms convert it to AVAX at the time of credit. This review values each cashback transfer at the price that Chainlink's AVAX / USD price feed on Avalanche showed at that moment.

The 88 wallets that spent $4,000 or more in September made 69.3% of the month's card spend and were paid 2.28% of it, counting the cashback paid from September 3 to October 1. Wallets that spent less than $2,500 were paid 3.58%. The site's [cash-flow review](https://ethenadash.com/research/ethenapay-cash-flows-2026-10-05/) put September's cashback at 2.63% with the dashboard's daily AVAX prices and found that the chain could not separate caps, conditions and timing in that total. Wallet by wallet, 46 of the 78 wallets that spent $4,000 or more by September 28 were paid within 5% of a published schedule.

## The published schedule

| Tier | Cashback on a calendar month's card spend | Most a month can pay |
| --- | --- | ---: |
| Standard | 4% to $2,500, 1% to $4,000, nothing above | $115 |
| Pro | 4.5% to $8,000, 2% to $10,000, 1% to $12,000, 0.5% above | No limit |
| VIP | 5% to $20,000, 2% to $30,000, 1% to $40,000, 0.5% above | No limit |

Each rate applies only to the part of the month's spend inside its band, like a tax bracket, and spend resets at the start of each calendar month. In the [FAQ](https://pay.ethena.fi/faq)'s worked example, a Pro user who spends $9,000 in a month earns $380. Only settled purchases earn cashback, and settlement usually takes one to three business days. Settled cashback is calculated and paid in a batch once a day, ordinarily within several days of the purchase and no later than 30 days. Purchases under $1.00 earn nothing, nor do excluded categories such as crypto purchases, gift cards, gambling, peer-to-peer transfers, account funding, and fees or taxes. A refund reverses the cashback and takes the purchase out of the month's spend, and small amounts are carried forward until they reach the minimum transfer. The [Terms of Use](https://pay.ethena.fi/terms) add that no other monthly, annual or lifetime cap applies at present, and that any such cap would be published on the Pricing page before it took effect. A user's tier shows in the app, and the pages do not say how a user becomes Pro or VIP, or whether the month runs in UTC or by the date of purchase or settlement. The Pricing page took effect on September 1, 2026 and was last updated on September 30, and the Terms of Use were last updated on September 22.

## Two accounts paid 9,219.43 AVAX to 845 wallets

A batch is a run of cashback transfers from one account with no gap of more than three hours. From the first cashback transfer, at 17:35 UTC on May 20, 2026, to the last batch read, at 02:30 UTC on October 9, the two accounts made 9,036 cashback transfers worth 9,219.43 AVAX to 845 wallets. The earlier account paid 171.12 AVAX from May 20 to July 14 and the current one 9,048.32 AVAX from July 15. September's 4,595.29 AVAX was about half of the total, and the first nine days of October brought 2,716.30 more.

| Month paid | Batches | Transfers | AVAX | Wallets paid | Dollars at Chainlink |
| --- | ---: | ---: | ---: | ---: | ---: |
| May, from the 20th | 3 | 4 | 0.09 | | |
| June | 16 | 82 | 50.43 | | |
| July | 29 | 362 | 549.96 | | |
| August | 31 | 966 | 1,307.37 | | |
| September | 30 | 4,972 | 4,595.29 | 622 | 41,604.25 |
| October 1 to 9 | 9 | 2,650 | 2,716.30 | 671 | 29,731.35 |

Wallet counts and dollar values start in September, the first full month for which this review kept each transfer and its price. From August 15 the current account paid once a day, and 53 of its 56 batches began at 02:30 UTC, two at 03:00 and one, on September 8, at 05:30. Each of these batches paid a wallet at most once. From September 19, 19 of the 21 batches went out in two transactions, the second within a minute of the first or about half an hour later. The largest batch, on October 7, paid 391 wallets.

The two accounts also sent 19,696.33 AVAX in 18 transfers to one address that is not an EthenaPay wallet, which this review does not count as cashback. Sixteen of those transfers, 19,686.23 AVAX, passed on in the same transaction AVAX that the account had just received from elsewhere.

## Isolated card payments earned about 4%

Most wallets used the card often, so one cashback transfer usually covered several card payments. To test the rate on one, this review took isolated card payments. An isolated card payment is a card payment of $1 or more from August 21 to October 2 with no other card payment from the same wallet within three days either side, no reversal to the wallet from three days before to six days after, and no cashback to it in the two days before. A reversal is a USDe transfer from a settlement address back to a wallet, such as a refund.

There were 216 isolated card payments. For 181 of them, exactly one cashback transfer reached the wallet in the six days after the payment. At Chainlink's price when that transfer arrived, the median came to 3.98% of the card payment, half fell between 3.92% and 4.06%, and 148 of the 181 came within a quarter of a point of 4%. Nineteen came within a quarter of a point of 4.5%, the Pro tier's first-band rate, and 3 of VIP's 5%. The other 11 fell outside those three bands. Eight card payments were followed by no cashback within six days, as purchases in excluded categories would be, and 27 by more than one transfer, which this review left out. Widening the three-day windows to five days, either side of the payment for other card payments and before it for reversals, left 139 card payments matched to one transfer at a median of 3.98%, and widening them to seven days left 99 at 3.99%. The test picks out wallets that use the card rarely, so it shows the rate on a single payment, not on the month's spend.

In 142 of the 181 matches the cashback came with the second or third daily batch after the card payment, and the median wait was 2.00 days, in line with settlement in one to three business days. Of 16 card payments under $1 that passed the same test, 15 brought no cashback within six days, as the $1.00 minimum says.

The median was 0.02 of a point under 4%. If a purchase in another currency was paid with the card network's conversion fee of about 1% included in the card payment, 4% of the purchase would be about 3.96% of the USDe paid, since fees earn no cashback. Ethena Pay may also price AVAX from sources other than Chainlink. The chain shows neither the currency of a purchase nor the price Ethena Pay used.

## Standard cashback stopped at $115

Seventy-eight wallets made $4,000 or more of card payments from September 1 to 28, early enough for most of their September cashback to arrive by October 1. Ten more crossed $4,000 on September 29 or 30, which makes the 88 above. This review compared the cashback each of the 78 was paid from September 3 to October 1, which covers card payments from about September 1 to 28 at the usual wait of two or three batches, with what each tier's schedule pays on that spend.

Twenty-eight of them were paid within 5% of $115, the most the Standard schedule pays in a month, between $109.39 and $119.92, and this review calls them the capped wallets. They spent from $4,161.54 to $47,670.88 each in September, $303,085.31 together or 19.1% of all September card spend, and were paid $3,240.84, 1.07% of it. At 4% they would have earned $12,123.41.

Twelve others were paid within 5% of what the VIP schedule gives for their spend, and 6 within 5% of the Pro schedule. Half of each group spent less than $8,000 by September 28, where the Pro and VIP schedules pay 4.5% and 5%, so those matches tell the two tiers apart only weakly. The largest-spending wallet, with $126,019.43 of card payments in September, was paid $1,688.76, 1.34% of it, close to the VIP schedule's $1,730.10. The other 32 matched no schedule within 5%. Seven were paid less than Standard's $115, 13 between the Standard and Pro schedules, 5 between Pro and VIP, and 7 more than the VIP schedule, 5 of them more than 5% of their card payments to September 28, above any published rate. Six of the seven paid more than the VIP schedule had card payments from August 25 to 31, whose cashback could arrive in the window. A change of tier during the month, refunds, excluded purchases, promotions, other rewards in AVAX, August cashback paid in the window or September cashback paid after it, and one user's spend split across wallets could each move a wallet off its line, and the chain does not show which.

![Scatter chart of 580 EthenaPay wallets with $10 or more of card payments from September 1 to 28, 2026 and some cashback paid from September 3 to October 1, each placed by the two amounts in dollars, the cashback at Chainlink's AVAX price, on log scales. Lines show the Standard, Pro and VIP schedules. Light-spending wallets sit near the Standard line, 28 heavy-spending wallets sit on the flat Standard line at about $115, 12 sit near the VIP line and 6 near the Pro line.](/research-assets/ethenapay-cashback-2026-10-09/chart_cashback_schedules.svg)

*Cashback and card payments on Avalanche C-Chain, read to the end of October 9 UTC · Schedules from Ethena Pay's Pricing page*

The 28 capped wallets kept spending and earned again when the month turned. From September 25 to 30 they made $68,277.05 of card payments and were paid $510.46 in the batches of September 27 to October 1, 0.75%. From October 1 to 7 they spent $55,846.25 and were paid $1,686.88 in the batches of October 2 to 9, 3.02%. All 23 of them that used the card from October 1 to 7 received cashback in those batches.

## Why September came to 2.62%

The table divides the cashback paid from September 3 to October 1, at Chainlink's price at each transfer, by each group's card payments in September, before reversals. The window leaves out cashback for the last card payments of September, which arrived from October 2, and takes in some for the last days of August, so on balance its rates run a little low. It gives 2.63% overall, against 2.62% for the batches paid in September. The median wallet that spent between $100 and $2,500 was paid 3.87%.

| Card spend in September | Wallets | Share of card spend | Rate, paid September 3 to October 1 | Short of 4% |
| --- | ---: | ---: | ---: | ---: |
| Under $2,500 | 524 | 19.1% | 3.58% | $1,268.20 |
| $2,500 to $4,000 | 61 | 11.6% | 3.19% | $1,497.11 |
| $4,000 or more | 88 | 69.3% | 2.28% | $18,954.87 |
| All | 673 | 100% | 2.63% | $21,713.41 |

The last row adds $6.77 paid to wallets that made no card payment in September. A flat 4% on September's card spend would have paid $63,537.21. Cashback paid from September 3 to October 1, $41,823.80 at Chainlink's price, fell $21,713.41 short of that, and 87.3% of the shortfall sat with the wallets that spent $4,000 or more. The 28 capped wallets accounted for $8,882.57 of it and the largest-spending wallet alone for $3,352.02.

The published schedules bracket the result. Had every wallet been Standard, the schedules would have paid $28,652.37 on September's card spend, 1.80%. All Pro would have paid 3.32% and all VIP 4.39%. Under the Standard bands, 42.5% of the month's spend fell within each wallet's first $2,500, 10.3% between $2,500 and $4,000, and 47.2% above $4,000.

Counted by the day it was paid, September's cashback came to $41,604.25 at Chainlink's price at each transfer, 2.62% of the month's card spend. Valuing each batch at its first transfer gives $41,628.88. The dashboard values each day's cashback at the average AVAX price for that day in Dune, the data service its queries run on, and gave $41,835.80, 0.6% more. Moving the window one to four days later raises the rate from 2.66% to 3.12%, close to the dashboard's 2.67% to 3.14%, because the batches of early October were larger. AVAX rose from $7.26 at the September 1 batch to $11.34 at the September 30 batch, and since cashback converts at the time of credit, the dollar value at credit is the one that measures the rate.

## How this review counts

A browser read every contract EthenaPay's two wallet factories deployed, every USDe transfer to or from those wallets, every AllowanceSpent record to the two settlement addresses, every internal AVAX transfer, AVAX that a contract sends during a transaction, into or out of the two cashback accounts, and every price update of Chainlink's AVAX / USD feed from shortly before August 20, on Avalanche C-Chain through block 97,161,009, the last block of October 9 UTC, from the Routescan explorer API. This review counts as wallets the 14,555 contracts the factories created with the CREATE2 instruction by that block, and leaves out 3 other contracts they created with a plain CREATE. Each wallet's first USDe and its balance at block 96,815,525, the adoption review's cutoff at 15:53 UTC on October 5, matched to the wei the chain recount this site published with that review, and the daily flows and USDe held on all 144 days to October 5 matched the daily file published with the cash-flow review. One USDe transfer to a settlement address, 5 USDe on September 24, carried no spend event and is left out, as the cash-flow review found. The spend events to October 5, September's card payments and reversals, the cashback in September's batches and the cashback to October 5 matched the cash-flow review's figures. The current cashback account is `0x37dea6fe8bc3d8d8c47fa3dac98c39a88585a71d` and the earlier one `0xfdc9d265ba3cdac512c7fe7e30417cc29487ff7b`.

Cashback is an internal AVAX transfer from either account to a wallet. Chainlink's feed publishes the price in rounds, and the price of a transfer is that of the latest round updated at or before it. The feed's proxy is `0x0a77230d17318075983913bc2145db16c7366156`, and Chainlink's [documentation](https://docs.chain.link/data-feeds/price-feeds/addresses?network=avalanche) lists a 0.1% deviation threshold and a 120-second heartbeat for it, so a new round comes when the price moves 0.1% and otherwise about every two minutes. At the first transfer of every batch from August 20 the price in force was at most 116 seconds old. September is the calendar month in UTC, for card payments by their time and for the batches that paid cashback, since the pages read do not say how Ethena Pay draws the month, and a different boundary could move a wallet near $4,000 across the Standard ceiling. The wallet comparisons count card payments before reversals, and a wallet matches a schedule when its cashback comes within 5% of what the schedule pays on its spend. Ethena Pay's Pricing page, FAQ and Terms of Use, Chainlink's feed listing and the site's own files were read on October 12 UTC.

## What the chain cannot show

The chain shows which wallet was paid and when. It does not show a user's tier, the merchant, the currency or the category of a purchase, or when a purchase settled, and the waits in this review come from the transfers themselves. It cannot separate excluded purchases or promotions from the rest. The accounts may also pay other rewards in AVAX, such as the $30 referral bonus on the Pricing page, though the transfers showed no cluster at that amount, with 19 worth between $29.50 and $30.50 against 16 and 20 in the dollars on either side. The Pricing page read for this review was last updated on September 30, and this review did not see the version in force earlier in September. The bands apply to a user's spend, and one person may hold more than one wallet.

## Reproduce the numbers

The main script checks every input against its recorded hash, the published recount and the cash-flow review, and stops before writing its tables if any of its 79 checks fails. The chain read's script fetches the public data again. Download the [monthly totals](/research-assets/ethenapay-cashback-2026-10-09/months.csv), the [isolated card payments](/research-assets/ethenapay-cashback-2026-10-09/single_payments.csv), the [September wallets](/research-assets/ethenapay-cashback-2026-10-09/september_wallets.csv), the [spend groups](/research-assets/ethenapay-cashback-2026-10-09/spend_groups.csv), or the [calculation files and source inputs](/research-assets/ethenapay-cashback-2026-10-09/calculation-files.zip). No EthenaPay wallet's address appears in the files.

```text
cashback in dollars = AVAX x Chainlink price in force at the transfer
September rate      = 41,604.25 / 1,588,430.13 = 2.62%
Standard maximum    = 2,500 x 4% + 1,500 x 1% = $115
Pro on $9,000       = 8,000 x 4.5% + 1,000 x 2% = $380
isolated payment    = cashback in dollars / card payment
```

The [EthenaPay dashboard](https://ethenadash.com/ethenapay/) tracks wallets, balances, spending and rewards, the [cash-flow review](https://ethenadash.com/research/ethenapay-cash-flows-2026-10-05/) follows every USDe flow, and the [methodology page](https://ethenadash.com/methodology/) defines the site's figures.

Analysis of public blockchain data and published product terms. Not investment advice.
