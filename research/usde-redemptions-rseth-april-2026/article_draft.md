# How much USDe was redeemed after the rsETH exploit?

Onchain review / USDe's burns, mints and supply around the rsETH exploit, April 2026, with October 2025 for comparison

By [Qorban Ferrell · @Degenerate\_DeFi](https://ethenadash.com/about/) · Published 15 October 2026 · Reads of Ethereum at the end of each UTC day, made 00:03 to 02:18 UTC on October 13, 2026 · Supply series to October 12, 2026 · Sources read October 12 and 13, 2026 UTC

About 2.16 billion USDe was redeemed in the nine UTC days from April 19 to April 27, 2026, counting each burn of USDe as a redemption. USDe is Ethena's synthetic dollar, and Ethena's documentation says that USDe redeemed through its mint and redeem contract is burned. Over the nine days 2,156,741,247.42 USDe was burned and 80,520,661.96 USDe was minted. USDe's total supply on Ethereum fell by 2,076,220,585.46, or 35.61%, from 5,829,728,799.04 at the end of April 18 to 3,753,508,213.58 at the end of April 27. April 18 was the day of the exploit of rsETH, a token issued by Kelp. The supply at the end of April 27 was the lowest day-end supply, the total supply at the end of a UTC day, from the 2025 peak of 14,819,842,076.32 on October 3, 2025 through October 12, 2026.

The exploit came at 17:35 UTC on April 18, at Ethereum block 24,908,285, according to an incident report written by the service providers of Aave, a lending protocol, and posted on Aave's governance forum on April 20. A forged message on LayerZero, a cross-chain messaging protocol, released 116,500 rsETH from the rsETH adapter on Ethereum. Burns of USDe came to 12,500,491.90 on April 18, less than the 55,301,484.31 of April 7, the largest day of the two weeks before. They came to 308,269,139.64 on April 19 and peaked at 506,766,046.09 on April 21.

sUSDe is the vault in which USDe is staked. When sUSDe is unstaked, its USDe is held in a separate contract, the cooldown silo, until a cooldown ends. Ethena cut the cooldown from seven days to one on March 16, 2026. sUSDe and its silo held 60.99% of USDe's supply at the end of April 18 and made up 64.68% of the nine days' fall, a little above their share. In the nine days from October 10, 2025, when the cooldown was seven days, they held 40.98% of supply at the start and made up 3.01% of a 17.23% fall, and 14.83% of the 30-day fall to November 8, 2025.

As a share of supply, the April fall was the largest in USDe's day-end supply over three, seven or nine days since January 1, 2024, when the daily series begins, and four of the five largest one-day falls came on April 20 to 23, 2026. The largest one-day fall, 11.14%, came on October 11, 2025. Measured in USDe, October 2025 was larger, and 2,575,379,021.74 USDe was burned in the nine days from October 10.

## The nine days after the exploit

The table gives USDe's day-end supply and each day's burns and mints, in millions of USDe. The change is from the previous day end, and the last column counts separate burns. Each figure is rounded on its own, so a change can differ by 0.01 from the figures beside it.

| Day, 2026 | Day-end supply | Change | Burned | Minted | Burns |
| --- | ---: | ---: | ---: | ---: | ---: |
| April 18 | 5,829.73 | down 2.48 | 12.50 | 10.02 | 13 |
| April 19 | 5,545.29 | down 284.44 | 308.27 | 23.83 | 307 |
| April 20 | 5,228.67 | down 316.62 | 341.14 | 24.52 | 189 |
| April 21 | 4,734.04 | down 494.63 | 506.77 | 12.14 | 285 |
| April 22 | 4,284.81 | down 449.23 | 461.38 | 12.14 | 261 |
| April 23 | 3,962.98 | down 321.82 | 325.60 | 3.78 | 170 |
| April 24 | 3,856.22 | down 106.76 | 106.81 | 0.05 | 80 |
| April 25 | 3,825.30 | down 30.92 | 31.05 | 0.13 | 39 |
| April 26 | 3,762.92 | down 62.38 | 62.51 | 0.13 | 54 |
| April 27 | 3,753.51 | down 9.42 | 13.22 | 3.81 | 14 |
| April 28 | 3,793.31 | up 39.80 | 10.83 | 50.63 | 17 |
| April 29 | 3,811.12 | up 17.81 | 2.93 | 20.74 | 12 |
| April 30 | 3,898.96 | up 87.84 | 4.61 | 92.45 | 13 |

In the five days from April 19 to April 23, 1,943,147,105.56 USDe was burned, 90.10% of the nine days' burns, and supply fell 32.02%. Half of the nine days' fall had come by the end of April 21. The nine days had 1,399 burns and 149 mints. On each of April 28 to 30 mints exceeded burns, and supply rose 145,453,884.34 over the three days. No single burn in the windows read was larger than 10,000,000 USDe, and 26 of the 91 days read had a burn of exactly that size. Ethena's documentation says its contract caps the USDe that can be redeemed in each block without giving the cap, and the read did not establish whether the cap explains the burns of that size.

Ethena's governance update for March and April 2026, prepared by Kairos Research and posted on the Ethena Foundation's governance forum on May 28, 2026, said the mints and redemptions went through without a break in USDe's peg or a draw on its Reserve Fund, the pool of assets Ethena holds as an additional margin of safety for USDe. The update also said USDe's borrow and supply rates on Aave likely spiked as leveraged positions unwound in mid-April. The read did not check prices or rates.

## Which holdings fell

The split below divides USDe's whole supply on Ethereum into three parts. The USDe held by sUSDe is the staked USDe plus rewards not yet vested. The cooldown silo holds the USDe of unstaked sUSDe until the cooldown ends. The USDe outside sUSDe is the rest, including the USDe locked on Ethereum to back USDe on other chains.

![Stacked areas of USDe's total supply on Ethereum at the end of each day from January 31 to May 31, 2026, in billions, split into the USDe held by sUSDe, the USDe in sUSDe's cooldown silo and the USDe outside both. sUSDe's cooldown was cut from seven days to one on March 16, 2026. At the end of April 18, the day of the rsETH exploit, supply was 5.83 billion, of which sUSDe held 3.53 billion. At the end of April 27 it was 3.75 billion, of which sUSDe held 2.16 billion. The silo peaked at 0.43 billion on April 20. On May 31 supply was 4.51 billion, of which sUSDe held 1.79 billion.](/research-assets/usde-redemptions-rseth-april-2026/chart_usde_redemptions_april_2026.svg)

*USDe's total supply on Ethereum at the last block of each UTC day, January 31 to May 31, 2026, split by where it was held · USDe at $1*

The table compares the nine days from April 19, 2026 with the nine days from October 10, 2025, each measured from the end of the day before, in millions of USDe. Each figure is rounded on its own, so the parts can differ by 0.01 from the total.

| | April 19 to 27, 2026 | October 10 to 18, 2025 |
| --- | ---: | ---: |
| Supply at the start | 5,829.73 | 14,664.27 |
| Supply at the end | 3,753.51 | 12,138.01 |
| Fall in supply | 2,076.22, or 35.61% | 2,526.26, or 17.23% |
| Burned | 2,156.74 | 2,575.38 |
| Minted | 80.52 | 49.12 |
| Fall in USDe held by sUSDe | 1,363.31, or 38.64% | 252.48, or 4.32% |
| Rise in the cooldown silo | 20.39 | 176.44 |
| Fall in USDe outside sUSDe | 733.30, or 32.25% | 2,450.21, or 28.31% |
| sUSDe and its silo, share of supply at the start | 60.99% | 40.98% |
| sUSDe and its silo, share of the fall | 64.68% | 3.01% |
| sUSDe's cooldown | 1 day | 7 days |

In April the USDe held by sUSDe fell 38.64%, from 3,528,252,468.49 to 2,164,943,911.70, and the USDe outside sUSDe fell 32.25%. Ethena's update said the redemptions fell disproportionately on sUSDe positions. The USDe held by sUSDe fell by a larger share than the USDe outside it, which is consistent with that, although the split does not show whose USDe was burned. On April 19 the USDe outside sUSDe accounted for 97.10% of the day's fall, while the silo rose by 190,657,776.25. Over the next four days the USDe held by sUSDe fell by 1,037,507,797.28. In October 2025 the USDe held by sUSDe fell 4.32% over the nine days, the silo more than doubled, and the USDe outside sUSDe fell 28.31%. The silo rose on each day from October 19 to October 23, to 582,381,184.06.

## The one-day cooldown

A proposal posted on the Ethena Foundation's governance forum on March 12, 2026 would replace the seven-day cooldown used since sUSDe's launch with one of one, three, five or seven days, set by the make-up of USDe's backing. It said liquid stablecoins were 89% of the backing. sUSDe's cooldown was 604,800 seconds, or seven days, at every day end read up to March 15, 2026, and 86,400 seconds, or one day, at every day end from March 16 to May 31. LlamaRisk, a member of Ethena's Risk Committee, posted its analysis in support of the proposal at 09:44 UTC on March 16.

LlamaRisk's analysis described the benchmarks of the cooldown framework, which Blockworks derived, as the 99th percentile of past net redemptions over rolling windows, a level that only 1% of past periods exceeded. They were 4.1% of supply over one day, 9.2% over three days and 12.0% over seven days. In April the falls in day-end supply reached 9.49% over one day, 24.21% over three days and 34.38% over seven, 2.31, 2.63 and 2.87 times the benchmarks. The one-day fall was above 4.1% on each of the five days from April 19 to April 23.

Ethena's update put the daily redemption capacity of Tier 1, the stablecoins and contract balances that settle within a day, at $1.88 billion when the one-day cooldown took effect, and said Tier 1 and other redemption channels absorbed the redemptions. The largest day of burns, April 21, came to 26.96% of that capacity.

## The largest falls since 2024

The table ranks the seven largest one-day falls in USDe's day-end supply from January 1, 2024 to October 12, 2026, by percentage, with the falls in millions of USDe.

| Day | Fall | Fall, % |
| --- | ---: | ---: |
| October 11, 2025 | 1,592.56 | 11.14% |
| April 22, 2026 | 449.23 | 9.49% |
| April 21, 2026 | 494.63 | 9.46% |
| April 23, 2026 | 321.82 | 7.51% |
| April 20, 2026 | 316.62 | 5.71% |
| July 10, 2026 | 217.56 | 5.13% |
| April 19, 2026 | 284.44 | 4.88% |

Over three days the largest fall in the series was 24.21%, from the end of April 20 to the end of April 23, 2026. Over seven days it was 34.38%, from the end of April 18 to the end of April 25, and over nine days 35.61%, to the end of April 27. Over 30 days the largest was 41.88%, from the end of October 9 to the end of November 8, 2025, when supply fell from 14,664,266,147.03 to 8,522,429,984.80. Measured in USDe rather than as a share of supply, the October 2025 falls were larger. The fall of July 10, 2026 lies outside the windows read here.

## The attestations against the chain

Ethena's update listed weekly attestations of USDe's supply for March and April. The table compares each attested supply with the day-end supply on the attestation's date and on the day before, in billions. The update gives dates and no times of day.

| Attestation, 2026 | Attested | Day end, same day | Day end, day before |
| --- | ---: | ---: | ---: |
| February 27 | 6.07 | 6.07 | 6.07 |
| March 6 | 5.97 | 5.96 | 5.97 |
| March 13 | 5.92 | 5.92 | 5.92 |
| March 20 | 5.92 | 5.92 | 5.93 |
| March 27 | 5.92 | 5.91 | 5.92 |
| April 2 | 5.89 | 5.89 | 5.88 |
| April 9 | 5.84 | 5.84 | 5.83 |
| April 16 | 5.83 | 5.83 | 5.83 |
| April 19 | 5.64 | 5.55 | 5.83 |
| April 23 | 3.96 | 3.96 | 4.28 |
| April 30 | 3.90 | 3.90 | 3.81 |

Ten of the eleven attested supplies equal one of the two day ends to two decimals. The attestation of April 19, 5.64 billion, lies between the day ends of April 18 and April 19, as a reading taken during April 19 would. From the end of April 16 to the end of April 30, 2,198,952,489.02 USDe was burned and 265,099,799.19 minted, a net fall of 1,933,852,689.83 that matches the update's fall of about $1.93 billion. The update said supply effectively stabilized in the last week of April, falling $62 million from April 23 to April 30. Day-end supply fell 209,476,451.18 from April 23 to April 27 and then rose 145,453,884.34 to April 30, a net fall of 64.02 million.

The update also put sUSDe's supply at $1.71 billion at the end of April, a staking ratio of about 44.0% of USDe's supply, down from 57.96% at the end of February. At the end of April 30 sUSDe's token supply, the number of sUSDe in issue, was 1,713,913,857.57, and its total assets, the USDe held for those tokens, were 2,107,677,005.06, or 1.2297 USDe a token. The $1.71 billion matches the token supply, and 44.0% matches the token supply over USDe's supply, 43.96%. By total assets sUSDe held 54.06% of USDe's supply. The February figure equals total assets over USDe's supply at the end of February 26, 57.96%, and is 0.10 point below the 58.06% of February 28. By token supply the ratio was 47.44% and 47.51% on those days. If the update's two figures use different measures, as these matches suggest, the ratio fell 4.00 points by total assets or 3.55 points by token supply from the end of February 28 to the end of April 30, rather than the 13.96 points between the update's figures.

## How the reads were made

The reads ran in a browser through public RPCs, servers that answer queries about Ethereum, from 02:14:28 to 02:18:02 UTC on October 13, 2026. For each of the 183 UTC days from September 30 to November 30, 2025 and from January 31 to May 31, 2026, a script read six values at the day's last block on two archive RPCs, which serve past states of the chain. The values were USDe's total supply, sUSDe's total assets, its token supply and its cooldown, and the USDe balances of sUSDe and its silo. The two RPCs gave the same six values on all 183 days. The day-end blocks, the last block at or before 23:59:59 UTC, came from a read of USDe's supply at every day end from January 1, 2024, made from 00:03 to 00:17 UTC the same morning, and the supply matched it on every day.

Mints and burns came from a third archive RPC. For each day's blocks it returned USDe's transfers from and to the zero address, which is how USDe's contract records USDe created and destroyed, 6,463 in all over the 91 days from October 1 to November 15, 2025 and April 1 to May 15, 2026. On every one of those days, USDe minted less USDe burned equaled the change in supply that the first two RPCs gave, to the smallest unit of USDe. The silo's address came from sUSDe's silo function on both RPCs at the latest block, and Ethena's documentation names the same contract.

## Caveats

The read counted every burn and mint and did not check which contract triggered each one. Ethena's documentation says redeemed USDe is burned, and the burns here are taken as redemptions. Day-end reads miss moves within a day, so the hours of April 18 after the exploit fall in that day's figures. The split between sUSDe, its silo and the USDe outside sUSDe compares holdings at day ends and does not follow individual USDe, so it does not show whose USDe was redeemed. The cooldown is one difference between the two waves, and the read does not measure the others or show that the cooldown caused the difference in the split. The silo was taken to be the same contract on every day read. The mints and burns came from one RPC, and the check against supply from the other two would catch a missing or extra event unless another offset it exactly. Ethena's update tied the redemptions to the rsETH exploit, and the read shows their timing, not their causes. The benchmarks and the Tier 1 capacity are as Ethena's update and LlamaRisk's analysis gave them, and USDe's backing was not read. USDe counts as one dollar.

## Primary sources

[rsETH incident report](https://governance.aave.com/t/24580) · [Ethena March and April governance update](https://gov.ethenafoundation.com/t/791) · [Dynamic cooldown proposal](https://gov.ethenafoundation.com/t/759) · [Ethena mint and redeem functions](https://docs.ethena.fi/technical-design/minting-usde/mint-and-redeem-key-functions).

## Reproduce the numbers

The main script checks every input against its recorded SHA-256 fingerprint and stops before writing its tables if any of its 29 checks fails. The browser script reads the chain again. The downloads are the [day-end state and daily flows](/research-assets/usde-redemptions-rseth-april-2026/daily_state.csv), the [days around the exploit](/research-assets/usde-redemptions-rseth-april-2026/april_days.csv), the [two waves](/research-assets/usde-redemptions-rseth-april-2026/waves.csv), the [largest falls](/research-assets/usde-redemptions-rseth-april-2026/largest_falls.csv), the [attestations](/research-assets/usde-redemptions-rseth-april-2026/attestations.csv), the [staking ratios](/research-assets/usde-redemptions-rseth-april-2026/staking_ratio.csv), the [chart data](/research-assets/usde-redemptions-rseth-april-2026/chart_data.csv) and the [calculation files and source inputs](/research-assets/usde-redemptions-rseth-april-2026/calculation-files.zip).

```text
burned, April 19 to 27  = 2,156,741,247.42
minted, April 19 to 27  = 80,520,661.96
minted - burned         = -2,076,220,585.46
supply, April 27 - April 18
                        = 3,753,508,213.58 - 5,829,728,799.04
                        = -2,076,220,585.46
fall                    = 2,076,220,585.46 / 5,829,728,799.04
                        = 35.61%
sUSDe and its silo      = 2,212,821,440.01 - 3,555,738,627.17
                        = -1,342,917,187.16, or 64.68% of the fall
outside sUSDe           = 1,540,686,773.57 - 2,273,990,171.87
                        = -733,303,398.29, or 35.32% of the fall
Each figure is rounded to the cent from exact values, so a last digit can differ from a sum of rounded figures.
```

The [StablecoinX dashboard](https://ethenadash.com/stablecoinx/) tracks StablecoinX's reported token treasury against its share price, the [sUSDe comparison](https://ethenadash.com/research/ethenapay-vs-susde-2026-10-08/) measures what staked USDe paid in September 2026, the [mNAV guide](https://ethenadash.com/research/stablecoinx-mnav/) explains how the ratio of StablecoinX's market value to the value of the tokens it reports holding is calculated, and the [methodology page](https://ethenadash.com/methodology/) defines the site's figures.

Related research includes [Ethena reserve fund review](https://ethenadash.com/research/ethena-reserve-fund-2026-10-12/), [USDe supply and ENA buyback milestones](https://ethenadash.com/research/ena-fee-switch-usde-supply-2026-10-12/).

Analysis of public blockchain data. Not investment advice.
