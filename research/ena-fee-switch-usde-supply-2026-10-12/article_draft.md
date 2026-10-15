# How far is USDe's supply from the first ENA buyback milestone?

Onchain review / USDe's supply against the ENA fee switch milestones, January 1, 2024 to October 12, 2026

By [Qorban Ferrell · @Degenerate\_DeFi](https://ethenadash.com/about/) · Published 15 October 2026 · Supply at the end of each UTC day to October 12, 2026, read at Ethereum block 26,179,856, 00:02:59 UTC on October 13, 2026 · Sources read October 12 and 13, 2026 UTC

USDe's total supply on Ethereum was 4,767,154,941.71 at the end of October 12, 2026 UTC. USDe is Ethena's synthetic dollar, and ENA is Ethena's governance token. The ENA fee switch is a schedule that sends a share of Ethena's revenue, the take rate, to buying back ENA once USDe's circulating supply reaches $7.5 billion, and raises that share at higher milestones. The 14 day trailing average of USDe's supply, the mean of the supply at the end of each of the last 14 days, was 4,865,356,639.35 on October 12. The average had to rise 54.15%, or by 2,634,643,360.65, to reach $7.5 billion, and USDe's day-end supply, its total supply at the end of a UTC day, had to rise 57.33%. Below that milestone the take rate is zero, and the 14 day average was below it on all 318 days from November 29, 2025 to October 12, 2026.

Ethena Labs Research proposed the schedule with Ethena's Risk Committee. The Committee sets risk parameters across the protocol, including the conditions that turn on the fee switch. ENA holders approved the schedule in a vote that closed on September 2, 2026. Neither the proposal nor the vote said how circulating supply is measured or averaged. The 14 day average is the measure recommended by Blockworks Advisory, which Ethena's documentation listed as a member of the Committee in October 2026. From August 27, 2026, when voting opened, to October 12, USDe's day-end supply and its 14, 30 and 90 day averages stayed below $7.5 billion on every day.

The review read USDe's total supply at the last block of every UTC day from January 1, 2024 on two archive RPCs, public servers that answer queries about past states of a chain. Over the 705 days of the backtest that Blockworks Advisory posted on the proposal's forum topic, the series reproduced all twelve counts in the backtest's table of supply measures. In 2025 the 14 day average stood at or above $7.5 billion for 118 days, from August 3 to November 28, and it never reached $15 billion.

## The milestones ENA holders approved

Ethena Labs Research posted the proposal on the Ethena Foundation's governance forum on August 27, 2026 and put it to a vote on Snapshot, a voting site. The proposal weighted each vote by the voter's ENA and sENA, a vault token for staked ENA, held directly or deposited in a separate contract. Voting ran from 13:59:52 UTC on August 27 to 13:59:52 UTC on September 2, 2026. The proposal passed with voting power of 17,786,102.45 for it, none against and none abstaining, from 88 votes, above a quorum of 5,000,000. A forum post confirmed the result on September 8.

Gross revenue is what Ethena earns before paying rewards to holders of staked USDe, payouts to partners and its other uses of revenue, and gross protocol APY is a year of gross revenue as a share of USDe's supply. The proposal illustrated the schedule at a gross protocol APY of 6.0%, which it called lower than the gross protocol APY Ethena had realized since launch.

| USDe supply | Take rate | Gross revenue a year at a 6.0% gross protocol APY | Buybacks a year at that APY |
| --- | ---: | ---: | ---: |
| $7.5 billion | 5% | $450 million | $22.5 million |
| $10 billion | 10% | $600 million | $60 million |
| $15 billion | 15% | $900 million | $135 million |
| $20 billion | 20% | $1,200 million | $240 million |
| $25 billion and above | 25% | not given | not given |

The revenue and buyback columns are Ethena Labs Research's illustration from the proposal. Its buybacks are the take rate times gross revenue, although the table called the take rate a share of net revenue. Blockworks Advisory's version, at the 4.60% gross protocol APY it called realized, put the buybacks at the first milestone at $17.3 million a year. The milestones count USDe's supply only.

The proposal also said that once the first milestone is reached, 95% of the net revenue that Ethena's business lines pay to the Ethena Foundation would go to ENA buybacks, without defining net revenue. It named three lines, USDe savings, whitelabel stablecoins and Ethena \[X\], which was due to launch the following week. The Risk Committee had approved the take rates, the milestones and the mechanics. Kairos Research, another member of the Committee, backed the proposal. So did OAK Research, which posted its own analysis and which the Committee's page did not list as a member.

Blockworks Advisory recommended measuring supply as a 14 day average, because one large mint can move a single day's supply, and OAK Research supported the recommendation. OAK Research wrote that how the buybacks are carried out would be settled in separate proposals. The forum topic's last post, on October 12, 2026, suggested a way to execute them.

## Where USDe's supply stood on October 12, 2026

The table compares the supply at the end of October 12, 2026 and its 14 day average with each milestone. The average covers the 14 days from September 29 to October 12, 2026.

| Milestone | Take rate | Rise needed in the 14 day average | Rise needed in the day-end supply |
| --- | ---: | ---: | ---: |
| $7.5 billion | 5% | 2,634,643,360.65, or 54.15% | 2,732,845,058.29, or 57.33% |
| $10 billion | 10% | 5,134,643,360.65, or 105.53% | 5,232,845,058.29, or 109.77% |
| $15 billion | 15% | 10,134,643,360.65, or 208.30% | 10,232,845,058.29, or 214.65% |
| $20 billion | 20% | 15,134,643,360.65, or 311.07% | 15,232,845,058.29, or 319.54% |
| $25 billion | 25% | 20,134,643,360.65, or 413.84% | 20,232,845,058.29, or 424.42% |

Day-end supply ended October 12 below its 14 day average after falling from 4,979,459,075.99 on October 6, the highest day end in the 60 days to October 12. It was 17.92% above the 4,042,825,373.53 of August 27, 2026, the day voting opened, and 27.01% above the 3,753,508,213.58 of April 27, 2026, its lowest day end since the 2025 peak.

![Line chart of USDe's total supply on Ethereum at the end of each day and its 14 day trailing average from January 1, 2024 to October 12, 2026, in billions, with dashed lines at the fee switch milestones of 7.5, 10 and 15 billion. Day-end supply peaked at 14.82 billion on October 3, 2025. The 14 day average was at or above 7.5 billion from August 3 to November 28, 2025. On October 12, 2026 day-end supply was 4.77 billion and the 14 day average 4.87 billion.](/research-assets/ena-fee-switch-usde-supply-2026-10-12/chart_usde_supply_milestones.svg)

*USDe's total supply on Ethereum at the last block of each UTC day, January 1, 2024 to October 12, 2026 · USDe at $1 · Milestones of the vote that closed on September 2, 2026*

## The 2025 stretch above $7.5 billion

USDe's day-end supply first reached $7.5 billion on July 27, 2025, at 7,500,232,731.98, and the 14 day average followed on August 3, seven days later. The average stayed at or above $7.5 billion for 118 days, to November 28, 2025, and at or above $10 billion for 81 days, from August 15 to November 3, 2025. Day-end supply peaked at 14,819,842,076.32 on October 3, 2025, and the 14 day average at 14,648,426,209.50 on October 9, 351,573,790.50 short of the $15 billion milestone. After the peak, day-end supply fell 74.67%, to its low of April 27, 2026.

The 2025 climb shows what a rise of the size now needed took last time. The 14 day average last stood at or below its October 12, 2026 level on May 21, 2025, and reached $7.5 billion 74 days later. Day-end supply last stood at or below its October 12, 2026 level on May 13, 2025, at 4,754,867,947.30, and reached $7.5 billion 75 days later. The past climb does not say when, or whether, the next one comes.

## The backtest, rebuilt onchain

Blockworks Advisory backtested the schedule over the 705 days from September 19, 2024 to August 24, 2026. For four measures of supply, it counted the days from July 27, 2025 to the first buyback, the days the schedule would have taken revenue and the number of times its take rate would have changed. The day-end supply read for this review gives the same twelve counts. Blockworks Advisory's counts are in parentheses.

| Supply measure | First day at or above $7.5 billion | Days to the first buyback | Days taking revenue | Take rate changes | Peak, in billions |
| --- | --- | ---: | ---: | ---: | --- |
| Day-end supply | July 27, 2025 | 0 (0) | 117 (117) | 4 (4) | 14.82 on October 3, 2025 |
| 14 day average | August 3, 2025 | 7 (7) | 118 (118) | 4 (4) | 14.65 on October 9, 2025 |
| 30 day average | August 10, 2025 | 14 (14) | 120 (120) | 4 (4) | 14.24 on October 10, 2025 |
| 90 day average | August 30, 2025 | 34 (34) | 141 (141) | 4 (4) | 12.38 on November 1, 2025 |

Each measure rose to the 10% take rate and fell back to zero, four changes in all. Blockworks Advisory gave the 14 day average's peak as $14.65 billion in October 2025 and the 90 day average's as $12.38 billion, the same as the onchain series. In its post of August 27, 2026 it put USDe's supply at $4.07 billion, 0.57% above the onchain supply at the end of August 26 and 0.67% above that at the end of August 27.

## Which supply counts

The vote did not define USDe's circulating supply. The total supply recorded by USDe's contract on Ethereum reproduced the backtest's counts exactly, so it is the measure used here. USDe on other chains is not added to it. Ethena's OFT adapter is the contract on Ethereum through which USDe moves to other chains, and a chain review of the same day found that it locked USDe on Ethereum when USDe left rather than burning it. At 18:41 UTC on October 12, 2026 the adapter held 2,292,201,958.40 USDe, 48.30% of the total supply on Ethereum, and the USDe on the 35 other chains read came to about 95 USDe less. The total supply on Ethereum therefore already counted the USDe on those chains.

## How the reads were made

The reads ran in a browser through RPCs. For each of the 1,016 UTC days from January 1, 2024 to October 12, 2026, a script found the last block at or before 23:59:59 UTC, the block whose timestamp is at or before that second and whose next block's is after it. It read USDe's total supply at that block on two archive RPCs. The two gave the same supply and the same block hash on all 1,016 days. When a second script ran at 00:31 UTC on October 13, 2026, two RPCs reported block 26,179,923 as finalized, the point up to which Ethereum's validators had settled the chain for good. The hashes of all 1,016 day-end blocks, read again, were unchanged, so every day-end block read was final. At the read block, 26,179,856, two RPCs gave the supply as 4,767,154,941.71, the same as at the end of October 12.

The averages are exact. The 14 day average on a day is the sum of the day-end supply of that day and the 13 before it, divided by 14, and the 30 and 90 day averages work the same way. A day's take rate is the rate of the highest milestone at or below that day's measure. USDe counts as one dollar.

## Caveats

Neither the proposal nor the vote said how circulating supply is measured, over what window it is averaged or when a change of take rate takes effect, so Ethena could put the milestones into effect with a measure other than the ones here. The 14 day average was recommended by Blockworks Advisory and supported by OAK Research, and the vote did not set it. The proposal's table called the take rates a share of net revenue, but its illustration, like Blockworks Advisory's and OAK Research's tables, applied them to gross revenue. The proposal did not say how the take rates combine with the 95% of the business lines' net revenue paid to the Foundation. Revenue was not read, so the review gives no dollar figure for buybacks beyond the sources' illustrations. Day-end reads miss moves within a day.

## Primary sources

[ENA fee switch proposal and committee analysis](https://gov.ethenafoundation.com/t/ena-fee-switch-activation/830).

## Reproduce the numbers

The main script checks every input against its recorded SHA-256 fingerprint and stops before writing its tables if any of its 21 checks fails. The browser scripts read the chain again. The downloads are the [day-end supply and averages](/research-assets/ena-fee-switch-usde-supply-2026-10-12/daily_supply.csv), the [milestones](/research-assets/ena-fee-switch-usde-supply-2026-10-12/milestones.csv), the [backtest comparison](/research-assets/ena-fee-switch-usde-supply-2026-10-12/supply_measures.csv), the [chart data](/research-assets/ena-fee-switch-usde-supply-2026-10-12/chart_data.csv) and the [calculation files and source inputs](/research-assets/ena-fee-switch-usde-supply-2026-10-12/calculation-files.zip).

```text
14 day average = day-end supply, September 29 to October 12, 2026, summed / 14
               = 68,114,992,950.85 / 14
               = 4,865,356,639.35
gap            = 7,500,000,000 - 4,865,356,639.35
               = 2,634,643,360.65
rise needed    = 7,500,000,000 / 4,865,356,639.35 - 1
               = 54.15%
day-end rise   = 7,500,000,000 / 4,767,154,941.71 - 1
               = 57.33%
take rate      = 0%, because 4,865,356,639.35 is below 7,500,000,000
```

The [StablecoinX dashboard](https://ethenadash.com/stablecoinx/) tracks the ENA that StablecoinX, a listed company, reports holding against its share price, the [mNAV guide](https://ethenadash.com/research/stablecoinx-mnav/) explains how the ratio of its market value to its ENA is calculated, the [sUSDe comparison](https://ethenadash.com/research/ethenapay-vs-susde-2026-10-08/) measures what staked USDe paid in September 2026, and the [methodology page](https://ethenadash.com/methodology/) defines the site's figures.

Related research includes [USDe supply by chain](https://ethenadash.com/research/usde-supply-by-chain-2026-10-12/), [Ethena reserve fund review](https://ethenadash.com/research/ethena-reserve-fund-2026-10-12/).

Analysis of public blockchain data. Not investment advice.
