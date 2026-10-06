# How many wallets use EthenaPay?

Adoption review / Through October 5, 2026

By [Qorban Ferrell · @Degenerate\_DeFi](https://ethenadash.com/about/) · Published 6 October 2026 · Chain data through 15:53 UTC on October 5, 2026 · Full weeks through October 4, 2026 · Full months through September 2026

In the seven full days to October 4, 2026, 617 distinct EthenaPay wallets had at least one card spend event. EthenaPay is this site's name for Ethena Pay, Ethena's payment app and card. USDe is Ethena's synthetic dollar and the token the card spends, and a spend event is one on-chain record of a wallet paying out USDe for the card. By 15:53 UTC on October 5, the cutoff of this review, 816 wallets had ever spent and 1,100 had ever received USDe, out of 14,047 created. The other 12,947, or 92.2% of those created, had never received USDe. A wallet is a contract on the Avalanche blockchain, and nothing on the chain ties one to a verified person.

Ethena's own posts described limited access through at least September 28. Ethena said the app's beta opened on September 1 with a first group of 400 users, and it offered a waitlist to people in regions it did not serve. On September 10 it said it would add waitlisted users every day, and on September 28 it was still pointing newcomers to a waitlist. On September 25 the product's own X account said 1,600 people had the app, at a moment when 12,667 wallets existed. On that figure created wallets outnumbered people with the app by about eight to one, so the count of created wallets says little about who could use the card.

Spending and balances sat in few wallets. Half of the USDe spent came from 39 wallets, and the ten largest balances held 43.3% of the USDe in EthenaPay wallets at the cutoff. The wallet, spend and balance figures here come from a recount of Avalanche chain data, checked against nine dated snapshots of the [EthenaPay dashboard](https://ethenadash.com/ethenapay/) dataset. A snapshot is a saved copy of the data the dashboard showed after one refresh.

## Spending wallets nearly tripled in four weeks

An AllowanceSpent log is a record a wallet contract writes to the chain that names a token, a destination and an amount. A spend event is one such log in which the token is USDe and the destination is one of the card programme's two settlement addresses, the current one and a retired one, which forward the funds to the card issuer. The guide [A transaction is not a card purchase](https://ethenadash.com/research/ethenapay-spend-events/) explains the rule. A spending wallet is a wallet with at least one spend event in the period.

![Stacked column chart of distinct EthenaPay wallets with a spend event in each seven-day period from August 3 to October 4, 2026. The count rises from 48 to 617. Each column is split into wallets that also spent in the previous seven days and wallets that did not.](/research-assets/ethenapay-adoption-2026-10-05/chart_weekly_spending_wallets.svg)

*Chain recount of USDe spend events to the two settlement addresses · Nine seven-day periods, August 3 to October 4, 2026*

| Seven days | Spending wallets | Also spent in the previous seven days | Did not | Spend events |
| --- | --- | --- | --- | --- |
| Aug 3 to Aug 9 | 48 | 34 | 14 | 664 |
| Aug 10 to Aug 16 | 60 | 41 | 19 | 881 |
| Aug 17 to Aug 23 | 75 | 52 | 23 | 885 |
| Aug 24 to Aug 30 | 92 | 64 | 28 | 1,290 |
| Aug 31 to Sep 6 | 212 | 78 | 134 | 2,148 |
| Sep 7 to Sep 13 | 281 | 184 | 97 | 2,987 |
| Sep 14 to Sep 20 | 416 | 232 | 184 | 4,421 |
| Sep 21 to Sep 27 | 495 | 340 | 155 | 5,805 |
| Sep 28 to Oct 4 | 617 | 425 | 192 | 7,172 |

In the seven days to October 4, 617 distinct wallets had a spend event. Four weeks earlier the figure was 212, and in the last full seven-day period before the beta it was 92. The week of August 31 to September 6 holds the day the beta opened and one day before it. Counted spend events began on June 4, three months before the beta, and this review did not establish who had access in that period.

Spending wallets rose by a factor of 2.91 over those four weeks. Spend events rose by a factor of 3.34, from 2,148 to 7,172. Two thirds of the latest period's events, 4,812 of 7,172, came from wallets with no spend event in the week of August 31 to September 6. Ethena said it would admit waitlisted users during these weeks, and the chain cannot separate new admissions from new demand.

In each of the last five seven-day periods, between 81.7% and 86.8% of the previous period's spending wallets spent again.

By calendar month spending wallets grew faster than spend events. September's 673 spending wallets were 5.8 times August's 116. Spend events were 4.4 times August's and spend in USDe 6.1 times.

| Month | Spending wallets | First spend in that month | Spent again from the previous month | Spend events |
| --- | --- | --- | --- | --- |
| June 2026 | 28 | 28 | no earlier month | 453 |
| July 2026 | 51 | 32 | 19 of 28 | 1,437 |
| August 2026 | 116 | 72 | 44 of 51 | 4,034 |
| September 2026 | 673 | 573 | 98 of 116 | 17,734 |

Two of September's wallets had last spent before August, so the two middle columns do not add up to the first in that row. In September 150 wallets spent on fifteen or more days and 360 on six or more, while 94 spent on a single day.

The dashboard's daily spending wallets for September add up to 6,030, about nine times the month's 673 distinct wallets, because that sum counts a wallet once for every day it spent. The four full days of October 1 to 4 had 553 distinct wallets, a figure the table omits because four days do not compare with a month.

## One wallet in thirteen had received USDe by the cutoff

One wallet had received USDe for every 12.8 created.

| Measure | Dashboard at the cutoff | Chain recount at the cutoff | Share of wallets created |
| --- | --- | --- | --- |
| Wallets created | 14,048 | 14,047 | 100% |
| Ever received USDe | not shown | 1,100 | 7.8% |
| Funded wallets, holding more than zero | 1,078 | 1,076 | 7.7% |
| Holding 1 USDe or more | not shown | 975 | 6.9% |
| Ever spent | 816 | 816 | 5.8% |
| Active wallets / 30d, including the partial run day | 778 | 778 | 5.5% |
| Active wallets / 7d, including the partial run day | 645 | 645 | 4.6% |

The run day is October 5, the day the queries that feed the dashboard ran. A created wallet is a deployed contract, and nothing ties it to a verified person, as the [methodology page](https://ethenadash.com/methodology/) states. Most created wallets had never held USDe.

The dashboard counts a wallet as funded when its balance is above zero. Of the 1,076 funded wallets, 101 held less than 1 USDe and 40 of those held less than a cent. The other 975 held at least 1 USDe.

Three in four wallets that received USDe had at least one spend event, 816 of 1,100. Of those 816, 548 spent within a day of their first USDe arriving and 750 within a week. One event is a low bar, and 88 of the 816 had a single event in their lifetime.

The two active-wallet rows use the dashboard's windows, which start at 00:00 UTC thirty and seven days before the run day and include the part of the run day before the cutoff. That is why the 7-day figure was 645 and the full-week figure was 617. The 28 extra wallets spent on October 5 before the cutoff and on none of the seven days before.

The dashboard showed one more wallet created and two more funded wallets than the recount. A contract the query counts as a wallet is the likely cause of the first, and rounding in the query's balance sum explains one of the other two.

## Wallet creation came in bursts while Ethena said access would open in stages

Two factory contracts deploy EthenaPay wallets. At the end of August 2,534 wallets existed. Of those, 1,873 date from May 15 to 31, before the first counted spend event on June 4, and the first factory deployed 814 of them on May 15 alone. June, July and August added 661.

Ethena opened the beta on September 1. Its [launch thread](https://x.com/ethena/status/2094757140493910168) said it would phase the roll-out, starting with a first group of 400 users and widening access each week in the regions it served as the product left beta during September. The chain shows 10 new wallets from 11:00 to 12:00 UTC that day, the hour before the thread, and 790 from 12:00 to 13:00. From 12:00 UTC to the end of the day it shows 4,054, about ten times the size of that first group. September 1 and 2 together produced 6,173 wallets, 43.9% of all wallets created by the cutoff.

Later posts from the product's account described a waitlist.

| Time (UTC) | Ethena statement | Wallets created by that time | Of which had received USDe | Of which had spent |
| --- | --- | --- | --- | --- |
| Sep 1, 11:59 | [Said the beta was opening to a first group of 400 users](https://x.com/ethena/status/2094757140493910168) | 2,569 | 259 | 133 |
| Sep 10, 07:49 | [Said it would add waitlisted users every day](https://x.com/EthenaPay/status/2097955643462394195), 100 of them the next day | 10,491 | 484 | 298 |
| Sep 25, 14:34 | [Said the app was "in the hands of 1,600 people and counting"](https://x.com/EthenaPay/status/2103493415174619587) | 12,667 | 861 | 618 |
| Sep 28, 17:32 | [Invited readers to download the app and join the waitlist](https://x.com/EthenaPay/status/2104625202730856677) | 13,010 | 901 | 661 |
| Oct 5, 15:53, the cutoff | no statement | 14,047 | 1,100 | 816 |

Ethena's 1,600 was about an eighth of the wallets that existed at that minute and nearly twice the number that had received USDe. The post did not define a person, and the chain cannot check the figure. The same post said 1.5 million dollars had moved through the app. Lifetime card spend on the chain was 1,539,454 USDe at the end of September 24, which is consistent with that figure.

The chain does not show which step in the app triggers a deployment. The counts fit an app that deploys a wallet when someone signs up, before Ethena grants access. They also fit scripted sign-ups and one person registering more than once, and the chain cannot separate these. Two outside trackers, opened on October 6, 2026 UTC, read the wallets as sign-ups. [Blockworks](https://app.blockworks.com/projects/ethena/analytics/ethena-pay) captioned its chart of accounts created as waitlist sign-ups, and [Paymentscan](https://paymentscan.xyz/cards/ethena-pay) titled its chart of registered accounts to include the waitlist. Neither page gave a basis for its label in the part this review could read, so the labels support that reading without confirming it.

| Creation period | Wallets created | Ever received USDe | Share that received | Ever spent | Share that spent |
| --- | --- | --- | --- | --- | --- |
| May 15 to 31 | 1,873 | 23 | 1.2% | 4 | 0.2% |
| June 1 to August 31 | 661 | 249 | 37.7% | 155 | 23.4% |
| September 1 and 2 | 6,173 | 576 | 9.3% | 463 | 7.5% |
| September 3 to 30 | 4,611 | 213 | 4.6% | 167 | 3.6% |
| October 1 to the cutoff | 729 | 39 | 5.3% | 27 | 3.7% |

The table shows status at the cutoff, which gave older groups more time. The May wallets all came from the first of the two factory contracts, which the dashboard's query labels a pilot. Without them, 1,077 of 12,174 wallets had received USDe, or 8.8%.

USDe kept arriving long after the burst. Of the 576 wallets from September 1 and 2 that had received USDe by the cutoff, 287 received it within 14 days of creation and 289 later. That fits access that opened in stages. It also fits holders who waited before depositing, and the chain cannot separate the two.

A comparison that holds time equal uses only the first 14 days after creation, for wallets created by September 20. On that basis 1.1% of the May wallets received USDe, 33.6% of those created from June to August, 4.6% of those from September 1 and 2 and 3.2% of those from September 3 to 20. By Ethena's account access differed between these groups, so the comparison holds time equal and nothing else.

## Half of the USDe spent came from 39 wallets

Lifetime spend at the cutoff was 2,454,347 USDe across 29,286 events and 816 wallets. Ten wallets accounted for 23.8% of the USDe with 6.9% of the events. Half of the USDe came from 39 wallets, 4.8% of those that had spent. The largest spender by USDe had six events.

Events were less concentrated than USDe. The ten wallets with the most events held 14.2% of them. The hundred with the most held 54.6%, against 70.8% of the USDe for the hundred largest spenders.

A few large events from one wallet can move spend in USDe, which is why this review leads with wallets and events.

At the cutoff 250 of the 816 wallets, 30.6%, had five or fewer events in their lifetime, and 346, or 42.4%, had more than twenty. Of those 250, 134 first spent in the 14 days before the cutoff, so low counts partly reflect short histories.

## The ten largest balances rose and fell while the rest grew at every week end

Top-10 share is the sum of the ten largest balances divided by USDe held.

| End of day | USDe held | Ten largest balances | All other wallets | Top-10 share | Funded wallets |
| --- | --- | --- | --- | --- | --- |
| Aug 30 | 524,696 | 407,306 | 117,390 | 77.6% | 230 |
| Sep 6 | 3,326,964 | 2,818,668 | 508,296 | 84.7% | 425 |
| Sep 13 | 4,278,518 | 3,187,318 | 1,091,200 | 74.5% | 517 |
| Sep 20 | 3,655,790 | 2,218,695 | 1,437,096 | 60.7% | 732 |
| Sep 27 | 3,601,525 | 1,684,180 | 1,917,345 | 46.8% | 872 |
| Oct 4 | 3,939,522 | 1,734,823 | 2,204,699 | 44.0% | 1,051 |

Each day is the last of a seven-day period in the spending table. Rounding can leave the two middle columns 1 USDe apart from the total.

The ten largest balances summed to 407,306 USDe at the end of August 30, the last day of the last full week before the beta. Their highest day-end sum was 3,187,671 on September 12, and they stood at 1,734,823 on October 4. All other wallets together held more at each week end than at the one before. They rose from 117,390 to 2,204,699 USDe while funded wallets rose from 230 to 1,051. September 22 was the first day that ended with the other wallets holding more than the ten largest. At the cutoff the ten largest held 1,719,813 USDe, 43.3% of the 3,968,570 in EthenaPay wallets.

Two wallets accounted for most of the rise in the ten largest balances and for the fall that followed. At the dashboard snapshot of September 11 each held about 1.0 million USDe, 1,999,309 between them. One fell from 1,000,313 USDe at the September 14 snapshot to 51,645 at the September 17 snapshot. The other held 993,463 on September 21 and was outside the twenty largest balances a day later. The dashboard series through October 4 showed its three largest days of withdrawals on September 15, 16 and 22, which matched that timing. This review did not trace where the USDe went. At the cutoff the two wallets held 43,958 USDe between them, and both had spend events.

| Balance in USDe at the cutoff | Wallets | USDe | Share of USDe held |
| --- | --- | --- | --- |
| Under 0.01 | 40 | 0.12 | 0.00% |
| 0.01 to under 1 | 61 | 21 | 0.00% |
| 1 to under 10 | 162 | 646 | 0.02% |
| 10 to under 100 | 274 | 10,180 | 0.26% |
| 100 to under 1,000 | 265 | 110,807 | 2.79% |
| 1,000 to under 10,000 | 219 | 776,724 | 19.57% |
| 10,000 to under 100,000 | 45 | 1,350,379 | 34.03% |
| 100,000 and over | 10 | 1,719,813 | 43.34% |

At the cutoff 55 wallets with 10,000 USDe or more held 77.4% of all USDe in EthenaPay wallets. The 802 funded wallets below 1,000 USDe held 3.1%. The rounded shares in the table sum to 100.01%.

None of the ten largest balances belonged to one of the ten largest spenders. Two of the ten had never spent and a third had three spend events. Two others ranked fourteenth and fifteenth of 816 wallets by USDe spent. Together the ten had spent 85,433 USDe, 3.5% of lifetime spend. Of the hundred largest balances, 39 were also among the hundred largest spenders, and 225 of the 274 wallets holding 1,000 USDe or more spent in the dashboard's 7-day window. Across all funded wallets, 264 had never spent. They held 597,682 USDe, 15.1% of the total, and two wallets held 490,699 of that.

Ethena's [FAQ](https://pay.ethena.fi/faq), read on October 6, 2026 UTC, said a balance earned a boosted rate up to a cap for each membership tier and that the boost required a qualifying card transaction every calendar month. Those terms gave holders a reason to keep a balance and a reason to spend at least once a month. The chain cannot show whether any holder acted on either.

## How this review checked the figures

The dashboard dataset comes from two queries on Dune, a blockchain data service. One produces the daily series and the other the headline figures, and the methodology page links both. This review used nine snapshots of that dataset, taken between September 11 and October 5, 2026. Two are from October 5.

The recount uses no Dune table. It takes its data from the Routescan block explorer and a public Avalanche node. It reads every wallet the two factory contracts deployed, every USDe spend event sent to either settlement address and every USDe transfer that touches one of those wallets. It counts log events and never transaction hashes, and it leaves out the settlement address's onward transfer to the issuer. The recount read the chain through the end of October 5. Every chain figure on this page stops at the cutoff block, 96,815,525, except the check of transfers against events in the next paragraph and the count of events sent to other destinations in the limits section.

At each of the nine snapshots the recount stopped at the block of the last spend event the dashboard had counted. It returned the same count of wallets that ever spent, the same 30-day and 7-day counts and the same lifetime spend to the cent, and the same USDe held to the cent at eight. On each of the 142 days in the dashboard's daily series from May 15 to October 4, spend events, daily spending wallets and spend in USDe were identical. The USDe contract's own balance for each of the 14,047 wallets at the cutoff block equaled the balance built from transfers. Through the end of October 5 the wallets sent 29,557 USDe transfers to the two settlement addresses, one more than the 29,556 spend events, and the transfers summed to exactly 5 USDe more than the events. The recount applies the dashboard's own rules, so agreement confirms the arithmetic and leaves the rules untested.

At the cutoff the dashboard counted one more wallet created and two more funded wallets than the recount. The likely cause of the first is a contract the first factory deployed on May 15 that was not a wallet and that the query's exclusion list did not name. The query sums balances in floating-point arithmetic, which rounds at each step, and replaying that sum adds one funded wallet at every snapshot. This review has not explained the second funded wallet or a gap of 15.22 USDe in USDe held at the October 5 snapshot generated at 15:41 UTC.

One outside tracker, [Paymentscan](https://paymentscan.xyz/cards/ethena-pay), showed 116 and 673 active addresses for August and September when read on October 6, 2026 UTC, the same as this recount. For August it showed 4,002 transactions, which equals the number of distinct transactions in this recount, against 4,034 spend events. For September it showed 17,387 transactions, eight fewer than the 17,395 distinct transactions in this recount, and this review has not explained that gap. For July it showed 48 active addresses and 62.94 thousand dollars of volume, against 51 wallets and 84,698.70 USDe here. The current settlement address received its first spend event on July 13, so a tracker that follows only that address misses everything before then. Three of the 51 wallets spent only before that day, which leaves 48, and July spend to the current address was 62,944.75 USDe. Those figures fit a tracker that counts transactions and follows only the current settlement address. Paymentscan stated neither rule, so both readings are this review's inference.

## Limits of this review

Wallets are not people. Nothing on the chain ties a wallet to one person, and one person may control several. In all, 208 wallets received their first USDe from another EthenaPay wallet, 111 of them from the same wallet. The chain does not show whether sender and receiver share an owner. The FAQ described a referral bonus, so some senders may have been funding another person's wallet.

Ethena was still pointing newcomers to a waitlist on September 28, and this review found no statement of how many people had access at the cutoff. A created wallet that never received USDe may belong to someone still on the waitlist.

A spend event is a log entry, and one transaction can hold several. The dashboard does not treat an event as a verified purchase, and no average or median purchase size appears here.

The spend rule counts two settlement addresses. Through the end of October 5, eight hours past the cutoff, another 113 AllowanceSpent events in USDe from EthenaPay wallets went to other destinations, 0.38% of the total. Eleven went to seven other EthenaPay wallets. Of the other 102, 56 went to one address between May 15 and June 10, a span that starts before the first counted spend event, and 46 went to a second address. The dashboard leaves all 113 out and so does this review, which has not identified those two addresses. Eight of the 32 wallets behind the 113 events had no counted spend event. If the first address was an earlier settlement address, the first spend would move to May 15 and seven more wallets would count as having spent.

Every figure here holds only for its stated date. The [dashboard](https://ethenadash.com/ethenapay/) shows current values.

## Reproduce the numbers

The observations come from nine snapshots of the [EthenaPay dashboard](/ethenapay/) dataset taken between September 11 and October 5, 2026, and from a recount of Avalanche chain data through block 96,839,679, the last block of October 5. The snapshots are in the calculation files below. The chain data is there as per-wallet and per-day tables that hold every chain figure on this page. The raw transfers and logs are not in the files. They are public chain data, and the README lists the contracts, the event and the block range the recount read. The balance figures for the eight earlier snapshots and for each day end come from that recount as results, so the files alone do not rebuild them. The chain tables identify each wallet by its position in creation order and contain no wallet address.

[Download the weekly figures](/research-assets/ethenapay-adoption-2026-10-05/weeks_wallets.csv), the [creation cohorts](/research-assets/ethenapay-adoption-2026-10-05/cohorts.csv), the [statement timeline](/research-assets/ethenapay-adoption-2026-10-05/timeline.csv), the [week-end balances](/research-assets/ethenapay-adoption-2026-10-05/balances_week_ends.csv), or the [calculation files and source inputs](/research-assets/ethenapay-adoption-2026-10-05/calculation-files.zip).

```text
spend event            = one AllowanceSpent log, token USDe, sent to one of the two settlement addresses
spending wallets       = distinct wallets with a spend event on at least one day in the period
share that spent again = wallets with a spend event in both periods ÷ wallets in the earlier period
top-10 share           = sum of the ten largest balances ÷ USDe held
```

This review never adds daily counts to make a weekly or monthly count. The [methodology page](https://ethenadash.com/methodology/) states the spend rule and the wallet measures. The two queries it links define the 30-day and 7-day windows, USDe held and the top-10 share.

Analysis of public blockchain data and published product terms. Not investment advice.
