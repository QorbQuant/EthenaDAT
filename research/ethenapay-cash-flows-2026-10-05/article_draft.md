# Where did the USDe deposited into EthenaPay go?

Cash-flow review / EthenaPay on Avalanche

By [Qorban Ferrell · @Degenerate\_DeFi](https://ethenadash.com/about/) · Published 9 October 2026 · Chain data through the end of October 5, 2026 UTC · Sources read October 9, 2026 UTC

From May 15 to October 5, 2026, EthenaPay wallets received 11,056,937.78 USDe in deposits. Withdrawals took 43% of that amount and card spend 22%. USDe sent back from the card's settlement addresses and USDe paid as rewards added back 1.1%, which left 3,980,154.11 USDe, the equivalent of 36% of deposits, in the wallets at the end of October 5.

EthenaPay is this site's name for Ethena Pay, Ethena's payment app and card. USDe is Ethena's synthetic dollar and the token the card spends. Each EthenaPay wallet is a contract on the Avalanche blockchain, created by one of two factory contracts. Every USDe transfer into or out of a wallet is public on that chain. Apart from transfers between two wallets, every such transfer falls in exactly one of six flows, and on each of the 144 days the flows added up to the change in USDe held, to the smallest unit the token records. A check at 15:53 UTC on October 5 found that the token contract's own balances matched the balances built from those transfers, and the [EthenaPay dashboard](https://ethenadash.com/ethenapay/) matched a separate recount of the chain in flows, balances and spend events on all 143 days of its series to October 5.

USDe rewards paid from September 2 to October 1 came to 4.6% a year on September's average balance, below the 5% and 6% tier totals in the [Ethena Pay FAQ](https://pay.ethena.fi/faq) when this review read it on October 9. Cashback paid in September, in AVAX, came to 2.63% of the month's card spend, against first-band rates of 4% to 5%. The FAQ's caps and conditions pull a realized rate below the headline rate, payment timing moves it either way, and the chain cannot separate these effects. These aggregate rates do not establish what any eligible wallet should have received.

## Six kinds of transfer change the USDe in EthenaPay wallets

The dashboard's daily query runs on Dune, a blockchain data service. It sorts every USDe transfer that touches an EthenaPay wallet by the address on the other side, and this review uses its rules. A settlement address is the card programme's contract that receives the USDe a wallet pays and forwards it to the card issuer, and the programme has used two. A transfer between two EthenaPay wallets is internal and changes no total.

| Flow | What moves | USDe, May 15 to October 5 |
| --- | --- | ---: |
| Deposit | USDe into a wallet from any address other than a wallet, a settlement address or a reward account | 11,056,937.78 |
| Withdrawal | USDe out of a wallet to any address other than a wallet or a settlement address | 4,728,153.68 |
| Card spend | USDe from a wallet to a settlement address | 2,470,248.65 |
| Reversal | USDe from a settlement address back to a wallet | 104,428.76 |
| Yield | USDe from the reward account the dashboard labels yield | 14,938.58 |
| Other rewards | USDe from the two reward accounts the dashboard labels other rewards | 2,251.33 |
| Internal transfer | USDe from one wallet to another, left out of the totals | 107,350.05 |

Yield and other rewards together are the USDe rewards, 17,189.90 USDe. Card spend here counts every USDe transfer from a wallet to a settlement address, 2,470,248.65 USDe in 29,557 transfers. The dashboard counts spend events instead. A spend event is an AllowanceSpent record that a wallet contract emits for USDe sent to a settlement address, and spend events came to 2,470,243.65 USDe in 29,556 events. The 5 USDe gap is one transfer on September 24 that reached a settlement address with no spend event. The [spend-events guide](https://ethenadash.com/research/ethenapay-spend-events/) explains how spend events are counted. The reversal and cashback rates below divide by card spend, and spend events give the same rounded rates.

Cashback arrives in AVAX, Avalanche's native token, from two other accounts, so it changes no USDe total. Through October 5 those accounts paid 7,835.03 AVAX to EthenaPay wallets.

```text
USDe held at the end of a day = USDe held at the end of the day before
                              + deposits + reversals + yield + other rewards
                              − withdrawals − card spend
```

## Card spend left wallets on weekends too

The FAQ said authorization came when the card was used and settlement followed, usually within one to three business days. From September 1 to October 5, spend events happened every day. On the five weekends from September 5 to October 4, Saturdays and Sundays averaged 770.2 spend events, against 705.8 on the Fridays before and the Mondays after them, and card spend was about the same, 66,137 USDe a day against 67,335. Saturday had the most spend events in each of the five weeks from September 1. If USDe left wallets only at settlement on business days, weekends would have been quiet, so the timing points to the moment of use.

The FAQ also described what it called the Spend Card as 0% APR on purchases, with late payment and returned payment fees of up to $40 and $29. Those terms point to a separate card account. The wallet transfers do not expose that account's balance, fees or settlement records.

A reversal is USDe a settlement address sends back to a wallet. The dashboard's tile called the total Refunded on October 9, and the chain records the amount without the reason. Reversals came to 104,428.76 USDe, 4.23% of card spend over the whole period and 4.62% in September.

## Withdrawals took more USDe than the card

Withdrawals took 42.76% of the USDe deposited and card spend 22.34%. Reversals added the equivalent of 0.94% of deposits and USDe rewards 0.16%, which left 36.00% in the wallets at the end of October 5.

![Waterfall chart of USDe in EthenaPay wallets from May 15 to October 5, 2026. Deposits of 11,056,938 USDe, less withdrawals of 4,728,154 and card spend of 2,470,249, plus reversals of 104,429 and USDe rewards of 17,190, left 3,980,154 USDe held at the end of October 5.](/research-assets/ethenapay-cash-flows-2026-10-05/chart_cash_flows.svg)

*USDe into and out of EthenaPay wallets from May 15 to October 5, 2026. The steps add up to the balance at the end of October 5.*

| USDe, UTC days | May 15 to August 31 | September 1 to October 5 | May 15 to October 5 |
| --- | ---: | ---: | ---: |
| Held at the start | 0.00 | 530,905.24 | 0.00 |
| Deposits | 1,326,173.24 | 9,730,764.53 | 11,056,937.78 |
| Withdrawals | 450,003.70 | 4,278,149.98 | 4,728,153.68 |
| Card spend | 361,677.85 | 2,108,570.80 | 2,470,248.65 |
| Reversals | 14,641.76 | 89,787.00 | 104,428.76 |
| USDe rewards | 1,771.78 | 15,418.12 | 17,189.90 |
| Held at the end | 530,905.24 | 3,980,154.11 | 3,980,154.11 |

The [adoption review](https://ethenadash.com/research/ethenapay-adoption-2026-10-05/) dated the opening of the app's beta to September 1 from Ethena's [launch thread](https://x.com/ethena/status/2094757140493910168), and 88.01% of all deposits came from that day on. The table rounds each figure on its own, so the first period's parts sum to 0.01 less than its end balance, and the two periods' deposits to 0.01 less than the total.

Both directions came in bursts. September 2 and 4 brought 21.6% of all deposits. September 15, 16 and 22 accounted for 57.8% of all withdrawals. The adoption review found two wallets that each held about 1.0 million USDe on September 11. One balance fell between the dashboard's September 14 and 17 snapshots, and the other dropped out of the twenty largest balances between September 21 and 22. Neither review traced where the USDe went.

## USDe rewards came to 4.6% a year on September balances

The dashboard's query counts USDe from three reward accounts, each a Safe, a multi-signature contract account. It labels one yield and the other two other rewards, and its notes call the purpose of the other rewards unconfirmed. One of those two paid 8.65 USDe into wallets from June 9 to July 13 and nothing after. From May 15 to October 5 the yield account paid 14,938.58 USDe into EthenaPay wallets and the other two 2,251.33 USDe.

In the FAQ, balances earned what it called the USDe base rate, which Ethena Pay did not set, and a Daily Boost topped that up to a tier total of 5% a year on up to $5,000 for Standard and 6% on up to $100,000 for Pro and up to $1,000,000 for VIP. Balance above the cap earned the base rate only. The Boost accrued daily on time-weighted average balances, came in USDe, ordinarily within 24 hours of the end of the day, and needed at least one qualifying card transaction each calendar month. No source this review found said which account paid which part.

For September this review counted payments made from September 2 to October 1, a day after each accrual day. They came to 13,064.13 USDe, 4.6% a year on the average end-of-day balance of 3,444,038.32 USDe. Payments made from September 1 to 30 give 4.4%. The yield account paid nothing on September 14, 15 and 16 and 1,819.65 USDe on September 17, so payments did not follow the days evenly. The rate averages every USDe held, including balance above the caps and wallets that may not have met the card condition, so no single wallet's rate follows from it.

For cashback, the FAQ listed 4% on the first $2,500 of monthly spend for Standard, 4.5% on the first $8,000 for Pro and 5% on the first $20,000 for VIP, with lower rates above those amounts and nothing on transactions under $1.00 or in excluded categories. Only settled transactions earned cashback. It came once a day in AVAX at the rate when credited, and a refund or chargeback reversed it.

Cashback paid in September came to 4,595.29 AVAX, which the dashboard valued at $41,835.80 using each payout day's average AVAX price. That is 2.63% of September's card spend of 1,588,435.13 USDe. Cashback followed settlement, so some late-September spend earned cashback in October. Moving the cashback window one to four days later gives 2.67% to 3.14%. Through October 5 cashback came to 7,835.03 AVAX, worth $69,351.44 at the same prices.

## October 5 from the opening balance to the close

October 5 was a Monday. That day 168 wallets deposited USDe, and 382 wallets made 1,250 spend events.

| Line | USDe |
| --- | ---: |
| Held at the end of October 4 | 3,939,522.21 |
| Plus deposits | 166,503.91 |
| Less withdrawals | 41,739.07 |
| Less card spend | 87,087.69 |
| Plus reversals | 2,371.36 |
| Plus yield | 476.34 |
| Plus other rewards | 107.05 |
| Held at the end of October 5 | 3,980,154.11 |

Wallets also sent 9,666.80 USDe to other EthenaPay wallets, which changed no total. Cashback that day came to 407.49 AVAX for 335 wallets, $4,470.20 at the day's average price. At the end of the day 1,082 of the 14,103 wallets created held USDe.

## A recount of the chain matched the dashboard on all 143 days

The adoption review rebuilt these flows from the chain without Dune, using the Routescan block explorer and a public Avalanche node, through block 96,839,679, the last block of October 5. This review compared that recount, day by day, with the dashboard's dataset of October 8. They matched in every flow, in USDe held and in spend events on all 143 days of the dashboard's series to October 5, to within a hundred-millionth of a USDe. The series has no row for May 30, a day with no flows.

The flows add up to USDe held by construction, because both counts build the balance from the same transfers. The independent test is the token contract's own record. At 15:53 UTC on October 5, block 96,815,525, the USDe contract's balance for each of the 14,047 wallets then created equaled the balance built from transfers. Those balances summed to 3,968,569.94 USDe, the figure in the adoption review, and transfers after 15:53 UTC took the total to 3,980,154.11 by the end of the day.

Checks made for this review on October 9 tested the rules from the paying side. In September the yield account sent 11,178.04 USDe in 13,873 transfers to 887 recipients, and the other reward accounts 1,407.99 USDe in 10,402 transfers to 777 recipients. Both totals equaled what the recount counted into EthenaPay wallets, so every USDe payment from the reward accounts that month reached a wallet. The current cashback account paid 4,595.29 AVAX in 4,972 payments to 622 wallets, the dashboard's figure. The 5 USDe transfer of September 24 came from a wallet the second factory contract created and carried no spend event. These checks leave the deposit and withdrawal rules untested.

## The dashboard's tiles left out the other rewards

When this review read it on October 9, the dashboard showed Deposited, Withdrawn, Card spend and Refunded as all-time tiles, beside USDe in card wallets and a Balance yield total. Its card spend counted spend events, 5 USDe less than card spend here, and no tile showed the other rewards, which the dataset carried. Summed through October 5 in the dashboard's dataset, Deposited less Withdrawn and Card spend, plus Refunded and Balance yield, came to 3,977,907.78 USDe. That is 2,246.33 short of the 3,980,154.11 held, the other rewards of 2,251.33 less the 5 USDe.

The Realized yield APY / 30d tile counted the yield account alone over the last 30 complete days. When the dataset was generated at 15:30 UTC on October 8, the tile showed 4.2% for September 8 to October 7. Adding the other rewards for the same days gives 4.8%. The Realized cashback / 30d tile showed 2.9% for the same days. Both tiles change with every refresh, and the dashboard shows the current figures.

Two changes to the query on October 5, 2026 took rewards out of deposits and added an earlier cashback account that paid from May 20 to July 14, so dashboard figures read before that change differ from these.

## What this review could not check

The card account's records. Authorized and settled amounts, currency conversion, fees and declined payments are outside these figures, and a card spend shows only the USDe that left a wallet.

The reason for each reversal, which the chain does not record.

What each reward account pays for, and the time-weighted balances the FAQ's Boost used. This review used end-of-day balances.

Where deposits came from and where withdrawals went. A deposit can come from an exchange, another chain or a person's own wallet outside EthenaPay, and a withdrawal can go to any of them. Wallets also emitted 102 AllowanceSpent records for 2,006.03 USDe sent to two addresses that are neither wallets nor settlement addresses, and this review did not identify them. The rules count those payments as withdrawals. If they were card payments, card spend would be 0.08% higher.

Who holds the wallets. A wallet is a contract, and nothing on the chain ties one to a verified person.

The dollar value of cashback at the moment of credit. The dashboard's values rest on one source, Dune's average AVAX price for each payout day.

## Reproduce the numbers

The daily flows come from the chain recount published with the adoption review, in dashboard data version 62503a1. The comparison uses the dashboard's dataset at commit 5faf41f, generated at 15:30 UTC on October 8, and the daily and headline queries at commit eb01f5d. The checks made for this review and the FAQ terms it used are in the calculation files. The main script rebuilds every computed figure from those files, stops if any check fails, and writes the tables. [Download the daily flows](/research-assets/ethenapay-cash-flows-2026-10-05/daily_flows.csv), the [flows by period](/research-assets/ethenapay-cash-flows-2026-10-05/bridge_by_period.csv), the [worked day](/research-assets/ethenapay-cash-flows-2026-10-05/worked_day_2026-10-05.csv), the [September rates](/research-assets/ethenapay-cash-flows-2026-10-05/september_rates.csv), or the [calculation files and source inputs](/research-assets/ethenapay-cash-flows-2026-10-05/calculation-files.zip).

```text
reversal rate       = reversals ÷ card spend
reward rate, a year = USDe rewards paid September 2 to October 1
                      ÷ average end-of-day USDe held, September 1 to 30
                      × 365 ÷ 30
cashback rate       = cashback in dollars at each payout day's average AVAX price
                      ÷ card spend, September 1 to 30
```

The [methodology page](https://ethenadash.com/methodology/) states the dashboard's flow and reward definitions. No EthenaPay wallet's address appears in the files.

Analysis of public blockchain data and published product terms. Not investment advice.
