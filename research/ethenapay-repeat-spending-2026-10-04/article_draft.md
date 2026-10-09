# Do EthenaPay wallets keep spending?

Repeat-spending review / Weeks to October 4, 2026

By [Qorban Ferrell · @Degenerate\_DeFi](https://ethenadash.com/about/) · Published 9 October 2026 · Full weeks through October 4, 2026 · Balances at 15:53 UTC on October 5 · Sources read October 6 to 9, 2026 UTC

Most EthenaPay wallets that started spending kept spending. Of the 126 wallets whose first spend came in the week the beta opened, August 31 to September 6, 2026, 104 spent again the next week and 89 in the week to October 4, four weeks on. Of the wallets whose first spend came in each of the next three weeks, 78% to 80% spent again the following week.

EthenaPay is this site's name for Ethena Pay, Ethena's payment app and card. Ethena opened its beta on September 1, so August 31 to September 6 is the beta week here. USDe is Ethena's synthetic dollar and the token the card spends. A wallet is a contract on the Avalanche blockchain, created by one of two factory contracts, and nothing on the chain ties one to a verified person. A spend event is one on-chain record of a wallet paying out USDe for the card, as the [guide to spend events](https://ethenadash.com/research/ethenapay-spend-events/) explains, and a wallet's first spend is its first spend event.

Wallets that first spent before the beta week, from June 4 to August 30, kept spending at a lower rate. Of these 131 pre-beta wallets, 72% spent again the week after their first spend, against 80% of the 519 wallets whose first spend came from August 31 to September 27.

Of the 522 wallets whose first spend came before September 21, 110, about one in five, had no spend event from September 21 to October 4, and 81 of those held at least 1 USDe at 15:53 UTC on October 5.

## Four in five spent again the week after their first spend

Each wallet belongs to a cohort, the week of its first spend, Monday to Sunday in UTC. It counts in a later week if it had at least one spend event that week. The beta cohorts are those from the beta week on. The last full week ends on Sunday, October 4, so the latest cohort has no later week yet.

| Week of first spend | Wallets | 1 week later | 2 weeks later | 3 weeks later | 4 weeks later |
| --- | ---: | ---: | ---: | ---: | ---: |
| Aug 31 to Sep 6 | 126 | 104 (83%) | 88 (70%) | 91 (72%) | 89 (71%) |
| Sep 7 to Sep 13 | 92 | 74 (80%) | 61 (66%) | 72 (78%) | |
| Sep 14 to Sep 20 | 173 | 136 (79%) | 124 (72%) | | |
| Sep 21 to Sep 27 | 128 | 100 (78%) | | | |
| Sep 28 to Oct 4 | 147 | | | | |

![Line chart of the share of EthenaPay wallets with a spend event in each week after the week of their first spend, to October 4, 2026. Wallets of the first four beta cohorts, 519 in all, 80% in week 1, 70% in week 2, 75% in week 3 and 71% in week 4, when 126 had been observed. Pre-beta wallets, 131 in all, 72%, 66%, 62%, 62% and 63% in weeks 1 to 5.](/research-assets/ethenapay-repeat-spending-2026-10-04/chart_repeat_spending.svg)

*Chain recount of USDe spend events to the two settlement addresses, published with the EthenaPay adoption review · Weeks Monday to Sunday UTC*

After the first week the share stayed between 66% and 78% in every beta cohort and week observed. Taken together, the first four beta cohorts' shares were 80%, 70%, 75% and 71% in the four weeks after their first spend. Each later week covers fewer cohorts, and only the cohort of the beta week, 126 wallets, had reached a fourth week. Of those 126, 116 spent in at least one of the four weeks and 66 in all four.

## Wallets from before the beta week kept spending at a lower rate

| First spend | Wallets | Spent in September | Spent in the week to October 4 | Spent on one day only |
| --- | ---: | ---: | ---: | ---: |
| June | 28 | 15 | 13 | 3 |
| July | 32 | 28 | 25 | 1 |
| August 1 to 30 | 71 | 56 | 47 | 6 |
| June 4 to August 30 | 131 | 99 | 85 | 10 |

Counted spend events began on June 4, three months before the beta, and this review did not establish who had access then. Taken together, the pre-beta wallets' shares were 72%, 66%, 62%, 62% and 63% in the five weeks after their first spend. Week for week, the cohort of the beta week alone had shares of 83%, 70%, 72% and 71%. With 131 wallets against 519, the pre-beta shares carry more chance variation, but they trailed in each of the four weeks. Of the three months, July's wallets kept spending most, with 25 of 32 spending in the week to October 4.

## Wallets with no spend event from September 21 to October 4

Of the 522 wallets whose first spend came before September 21, 110, or 21%, had no spend event from September 21 to October 4. They were 40 of the 131 pre-beta wallets, 31%, and 70 of the 391 wallets of the first three beta cohorts, 18%. Of the 110, 45 had spent on only one day to October 4, and three spent again on October 5, the day after the last full week.

At the last balance snapshot, 15:53 UTC on October 5, 81 of the 110 held at least 1 USDe, 53 held 10 USDe or more and 30 held 100 USDe or more. Of the 412 that did spend in those two weeks, 405 held at least 1 USDe.

Over a longer window, 29 of the 131 pre-beta wallets, or 22%, had no spend event from September 1 to October 4, against 40 in the two weeks to October 4, and 20 of the 29 held at least 1 USDe. The chain shows when a wallet spends and what it holds, and nothing about why.

## How this review counts

The counts come from the chain recount published with this site's [EthenaPay adoption review](https://ethenadash.com/research/ethenapay-adoption-2026-10-05/), which read every qualifying spend event through the last block of October 5 UTC from the Routescan explorer API, and balances from a public Avalanche RPC node, on October 6. It counted AllowanceSpent logs in USDe to the current and the retired settlement address, never transaction hashes, and left out each settlement address's onward transfer to the card issuer. Of its 29,556 spend events, 28,720 went to the current address and 836 to the retired one.

The three chain files this review uses are byte-identical to that review's calculation files. Their weekly spending wallets and spend events reproduce that review's published table for all ten weeks from July 27 to October 4, and their monthly counts reproduce the monthly table in that review's calculation files, from June to October 4. The month table above stops at August 30, since August 31 falls in the beta week, so its August row holds 71 wallets against that review's 72 first spends in August.

## What these figures leave out

The beta admitted users in stages. Ethena opened it on September 1 to a first group of 400 users and said access would widen each week, and on September 28 EthenaPay's X account was still pointing newcomers to a waitlist. A cohort's size therefore reflects admissions as well as demand.

Only the cohort of the beta week has four later weeks in the data, and the latest cohort, 147 wallets, has none. Two weeks is also a short window for a card whose balance reward has a monthly condition. EthenaPay's [FAQ](https://pay.ethena.fi/faq), read on October 9, said the Daily Boost, an extra rate paid on balances up to a cap, required at least one qualifying card transaction in each calendar month, so a wallet that spends once a month can go two weeks without a spend event.

The adoption review found 56 AllowanceSpent events in USDe from 12 wallets to one unidentified address from May 15 to June 10, a span that starts before the first counted spend event on June 4. If that address was an earlier settlement address, seven more wallets would count as having spent before the beta week.

The site's [cash-flow review](https://ethenadash.com/research/ethenapay-cash-flows-2026-10-05/) found that spend events point to the moment a card is used. On the weekends from September 5 to October 4 they ran above the level of the Fridays and Mondays around them, while the FAQ said payments usually settled one to three business days after authorization. Few events should therefore fall in a later week than the purchase. Balances come from one snapshot and do not show what a wallet's owner intends.

## Reproduce the numbers

The main script checks every input against its recorded hash, that the chain files match the recount's own manifest, that the spend file holds all 29,556 spend events and 820 spending wallets in the recount's summary, that each wallet's first spend day matches the recount's activity file, and that the weekly and monthly figures reproduce the adoption review's tables. If any check fails, the script stops before writing its tables. Download the [cohort table](/research-assets/ethenapay-repeat-spending-2026-10-04/first_spend_cohorts.csv), the [weekly shares behind the chart](/research-assets/ethenapay-repeat-spending-2026-10-04/weekly_shares.csv), or the [calculation files and source inputs](/research-assets/ethenapay-repeat-spending-2026-10-04/calculation-files.zip). No EthenaPay wallet's address appears in the files.

```text
cohort week     = the Monday-to-Sunday UTC week of a wallet's first spend event
share in week k = cohort wallets with a spend event in the k-th week after the cohort week ÷ cohort wallets
                = 89 ÷ 126 = 70.6% for the week of August 31, four weeks on
```

The [EthenaPay dashboard](https://ethenadash.com/ethenapay/) tracks wallets, balances and spending, and the [methodology page](https://ethenadash.com/methodology/) defines its figures.

Analysis of public blockchain data and published product terms. Not investment advice.

Related research: [Read the broader EthenaPay adoption study.](/research/ethenapay-adoption-2026-10-05/) [Follow deposits, withdrawals and card spending in the cash-flow review.](/research/ethenapay-cash-flows-2026-10-05/)
