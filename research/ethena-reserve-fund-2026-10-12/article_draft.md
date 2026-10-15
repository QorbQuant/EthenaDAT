# How big is Ethena's reserve fund, and where did its money come from?

Onchain review / Ethena's reserve fund, January 2024 to October 12, 2026

By [Qorban Ferrell · @Degenerate\_DeFi](https://ethenadash.com/about/) · Published 15 October 2026 · Read at Ethereum block 26,178,998, 21:10:59 UTC on October 12, 2026 · Sources read October 12, 2026 UTC

Ethena's reserve fund held assets worth $62,096,266.02 at Ethereum block 26,178,998, 21:10:59 UTC on October 12, 2026, with every stablecoin counted at $1. That was 1.31% of USDe's total supply of 4,749,058,127.00. USDe is Ethena's synthetic dollar, and the reserve fund is a pool of assets kept to bear losses that would otherwise fall on the assets backing USDe, such as losses in periods when the cost of Ethena's hedges exceeds what its backing earns. The review tracked 12 tokens, which include every one the fund used, and the fund's positions on Uniswap V3, an exchange where each liquidity provider chooses a price range. It left out 42 other tokens listed for the fund by two explorers, websites that index a chain's records.

Ethena's key addresses page named the multisig wallet at `0x2b5ab59163a6e93b4486f6055d33ca4a115dd4d5` on Ethereum as the Reserve Fund. It is a Safe, a smart contract wallet whose transactions need signatures from a set number of its owners, here 4 of its 10. The Risk Committee, a committee of outside risk firms that votes on proposals about Ethena's risk, with Ethena Labs Research as a nonvoting member, linked the fund's holdings to the same address in its updates.

Most of the fund was USDtb, a stablecoin that Ethena Labs created and that its 2024 proposal described as backed mainly by BlackRock's BUIDL fund. The fund held 42,019,153.46 USDtb and 99.9984% of a pool of USDtb and USDC on Curve, an exchange whose pools swap stablecoins. The pool share was worth $20,076,248.34. USDtb, held directly and through the pool, made up 85.85% of the fund.

sUSDe is staked USDe. The sUSDe Payout Fund, the multisig that the key addresses page described as sending USDe to sUSDe's rewards contract, sent the fund $35,665,296.40 in 20 transfers from February 2 to December 12, 2024. A second Safe, `0xa2af…cced92`, and two addresses that are not contracts, none of them named on the key addresses page, sent $23,240,242.66. The fund's savings vaults, tokenized funds and liquidity pools, with the interest on its USDtb, earned $3,255,661.18, and minting USDtb, swaps and conversions cost $65,690.51.

Nothing was paid out of the fund. Every tracked token that left it went into a swap, a conversion or a position that returned assets to it, and its value rose from every month end to the next. No asset arrived after November 3, 2025. In April 2026 LlamaRisk and Blockworks Advisory, two members of the Risk Committee, recommended sending the interest on the fund's USDtb to sUSDe holders, and Ethena's governance update of June 5, 2026 said that it was going to them.

## What the fund held

| Holding | Amount | Value at $1 a stablecoin | Share |
| --- | ---: | ---: | ---: |
| USDtb | 42,019,153.46 | $42,019,153.46 | 67.67% |
| Curve pool share, USDtb | 11,288,778.64 | $11,288,778.64 | 18.18% |
| Curve pool share, USDC | 8,787,469.70 | $8,787,469.70 | 14.15% |
| ETH | 0.3 | $756.19 | under 0.01% |
| USDS, BUIDL and USDC | 108.03 | $108.03 | under 0.01% |
| Total | | $62,096,266.02 | 100.00% |

USDS is the stablecoin of Sky, the protocol formerly called Maker. The Curve pool's depositors receive LP tokens, shares of the pool's two coins. 19,980,948 LP tokens reached the fund on December 15, 2024 for 9,990,474 USDC and 9,990,474 USDtb, and they were all the LP tokens the pool had issued. At the read block the pool had issued 19,981,269.35, so the fund owned all but 0.0016% of it. The fund's share was worth $95,300.34 more than the coins put in, a gain of 0.48% in 22 months. ETH is valued at $2,520.62, the ETH/USD price that Chainlink's price feed on Ethereum last updated at 20:33 UTC. The fund also owned four Uniswap V3 positions, and they were empty.

The fund's 53,307,932.10 USDtb, held directly and through the pool, were 11.33% of USDtb's total supply on Ethereum of 470,646,018.06.

## Where the $62.10 million came from

The table splits the fund's value into what was paid in and what its positions earned or cost. sDAI and sUSDS are Sky's savings vaults for its stablecoins DAI and USDS. USTB is a tokenized fund issued by Superstate, which the Risk Committee's 2024 notes described as holding the same assets as BUIDL. CoW Protocol is an exchange that settles batches of orders.

| Source | Dates | USD |
| --- | --- | ---: |
| sUSDe Payout Fund, 20 transfers | February 2 to December 12, 2024 | 35,665,296.40 |
| Safe `0xa2af…cced92`, 5 transfers | January 24 to February 27, 2024 | 10,000,321.66 |
| An address that is not a contract, 10,000,000 USDC | December 20, 2024 | 10,000,000.00 |
| An address that is not a contract, 3,239,921 USDT | April 16, 2024 | 3,239,921.00 |
| Paid in | | 58,905,539.05 |
| sDAI and sUSDS savings vaults | March 2024 to September 2025 | 1,649,259.20 |
| USDtb interest, 9 transfers | March 14 to November 3, 2025 | 959,648.17 |
| Uniswap V3 USDe/USDT positions | January 2024 to February 2025 | 416,681.69 |
| Superstate's USTB fund | February to August 2025 | 106,245.27 |
| Curve USDtb/USDC pool | December 2024 to the read block | 95,300.34 |
| BUIDL | October and November 2024 | 28,526.50 |
| Earned | | 3,255,661.18 |
| USDtb minted for BUIDL and USDC | December 2024 to September 2025 | -29,097.71 |
| Swaps through CoW Protocol and Curve's router | 2024 and 2025 | -30,840.36 |
| Conversions through Safe `0x4423…9d9d` | April 2024 | -5,752.43 |
| Costs | | -65,690.51 |
| ETH, and transfers under 1 USDC | | 756.30 |
| Total | | 62,096,266.02 |

Each line counts the stablecoins and BUIDL that arrived less those that left, at $1 each, so the line of a vault, fund or pool is its gain or loss, including the cost of entering and leaving it. The BUIDL line ends where BUIDL was exchanged for USDtb, and that exchange is on the minting line. The Curve line adds the value of the fund's pool share at the read block. The sUSDe Payout Fund paid in USDT, DAI, USDC and USDe. Ethena's Reserve Fund page put the share of revenue allocated to the fund at 0%. On August 27, 2026 Blockworks Advisory wrote that the fund had received no allocation since December 12, 2024 and $35.7 million before it, the same date and amount as the transfers.

On March 14, 2024, 15,060,722.34 DAI went into sDAI. Most of the shares moved to sUSDS in October 2024, and the rest of both were sold or redeemed in August and September 2025 for $16,709,981.54. The four Uniswap V3 positions held USDe and USDT in a pool where the two swap for a 0.01% fee, and they earned $416,890.23 in fees. USTB shares, 492,917.00 of them, were bought in February 2025 for an average 10.5841 USDC each and redeemed for 10.7997 USDC each on August 26, 2025.

BUIDL is BlackRock's tokenized fund, which LlamaRisk described in December 2024 as invested in cash, US Treasury bills and repurchase agreements and as paying its dividends in new tokens each month. On October 11, 2024, 18,693,674 USDC went to BUIDL's contract for 18,675,000 BUIDL, and on November 1, 2024 the fund received 47,200.50 new BUIDL with no payment. Swaps went through CoW Protocol and Curve's router. USDtb was minted for 0.1% less than the BUIDL and USDC exchanged for it in December 2024, and for $5.20 less than the 22,033,214 USDC exchanged for it in September 2025. In April 2024 USDT and USDe were exchanged through Safe `0x4423…9d9d`, which the key addresses page also did not name.

Risk Committee members wrote in April 2026 that interest on the fund's USDtb was transferred to the fund by hand rather than accruing in the token. The nine USDtb transfers came from two addresses that are not contracts. The last three, of 500 and 103,191.74 USDtb on September 11, 2025 and 169,048.07 USDtb on November 3, 2025, match the amounts their update described. The six earlier ones came from the address that also received the BUIDL and USDC exchanged for USDtb, and are counted as interest because they follow the same pattern.

## How the holdings changed

![Stacked bar chart of the reserve fund's value at the end of each month from January 2024 to September 2026, in millions of dollars. It rose from 1.0 in January 2024 to 46.9 in November 2024 and 60.3 in December 2024, and stayed between 60.5 and 62.1 from January 2025 to September 2026. USDtb and the Curve USDtb/USDC pool made up almost all of it from September 2025.](/research-assets/ethena-reserve-fund-2026-10-12/chart_reserve_fund_by_month.svg)

*Value at the end of each month, January 2024 to September 2026, read at the last block before midnight UTC · Stablecoins at $1*

| Dates | What moved |
| --- | --- |
| January 24, 2024 | 500,000 USDe, 299,321.66 USDT and 201,000 USDC arrived from Safe `0xa2af…cced92` |
| January 25 to April 2, 2024 | 4,931,916.95 USDe and 6,278,217.13 USDT went into four Uniswap V3 positions |
| March 14, 2024 | 15,060,722.34 DAI went into sDAI |
| October 10 and 11, 2024 | 18,800,000 USDT was swapped for USDC, and 18,693,674 USDC went to BUIDL's contract for 18,675,000 BUIDL |
| October 15 to 31, 2024 | 12,157,224 of the fund's 14,195,794.59 sDAI moved into sUSDS |
| December 13 to 24, 2024 | 6,408,774.07 USDe and USDT came out of the Uniswap positions, 18,722,199 BUIDL and 10,323,664 USDC were exchanged for USDtb, and 9,990,474 USDC and 9,990,474 USDtb went into the Curve pool |
| February 5 to 26, 2025 | The last Uniswap position was emptied and 492,917.00 USTB were bought |
| August 26 to September 4, 2025 | The USTB was redeemed, the sUSDS and sDAI were sold, and 22,033,214 USDC was exchanged for USDtb |
| November 3, 2025 | 169,048.07 USDtb arrived, the last incoming transfer |

The fund's value reached $60,271,735.13 at the end of December 2024 and grew 3% from then to the end of September 2026. From the end of September 2025 to the read block it rose $239,171.38. The last interest transfer added 169,048.07 USDtb and the pool share gained $70,610.74, while a lower ETH price cut the value of the fund's 0.3 ETH by $487.42.

## What the Risk Committee decided

On October 10, 2024 Ethena Labs announced that a Risk Committee vote had set allocation weights for the fund of 40% for BUIDL, 29% for USDS, 16.5% for USDM, Mountain Protocol's stablecoin, and 14.5% for USTB. BUIDL was bought the next day, worth 39.95% of the fund at the end of October 2024. No token named USDM appears in either explorer's list of the fund's transfers. When the proposal to add USDtb to the assets the fund could hold drew support in December 2024, LlamaRisk wrote that USDtb and BUIDL together were expected to stay at or below 50% of the fund. USDtb, held directly and through the pool, stayed below 50% at every month end from December 2024 to August 2025, at most 48.34% in July 2025.

In April 2025 Ethena Labs proposed moving $5 million of the fund into USDe's backing, and LlamaRisk and Blockworks Advisory supported it. LlamaRisk's June 2025 update said that the plan had been approved and then abandoned, and no such transfer left the fund. LlamaRisk's update of August 26, 2025 said that the Committee's reserve fund group had accepted a proposal to consolidate the fund into USDtb, on condition that the USDC and USDT backing USDtb stayed larger than the fund. From August 26 to September 4 the fund's USTB, sUSDS and sDAI were exchanged for USDtb, and the Curve pool share stayed. USDtb was 86.59% of the fund at the end of September 2025. That update's list of holdings left out sDAI, which the fund still held, worth $2,374,844.59 at the end of August 2025.

The review compared 35 published figures for the fund or one of its holdings, from April 2025 to July 2026, with the onchain value at the nearest month end or on the same date. They were all the figures for the fund or a holding in the forum passages kept for the review, apart from two splits of the Curve position into its coins and nine weekly attestations that appear below only as a range. Allowing for the rounding of each published figure, 32 came within 0.35% of the onchain value and 27 within 0.1%. A figure given as $62.0 million, for example, counts as matching any value from $61.95 million to $62.05 million. The other three were higher. The governance update for January and February 2026 gave $62.51 million and $62.54 million, and the update for May 2026 gave $62.5 million, $0.42 million to $0.49 million more than the fund held at the nearest month end. The March and April update listed weekly attestations, which it attributed to Chaos Labs' proof-of-reserves service. They put the fund at $62.00 million to $62.07 million from February 27 to April 30, 2026, in line with the onchain values. The review could not tell what the larger figures included.

On April 8, 2026 LlamaRisk and Blockworks Advisory recommended sending the USDtb interest to sUSDe holders for as long as the fund stayed above twice the higher of their two estimates of what it needed, a floor that was then about $14 million.

## The fund against USDe's supply

| Month end | Fund | USDe supply | Fund as a share |
| --- | ---: | ---: | ---: |
| February 2024 | $11,778,945.67 | 584,429,371.39 | 2.02% |
| December 2024 | $60,271,735.13 | 5,875,821,896.27 | 1.03% |
| September 2025 | $61,857,094.63 | 14,713,959,485.58 | 0.42% |
| March 2026 | $62,051,087.91 | 5,883,872,296.93 | 1.05% |
| September 2026 | $62,095,873.73 | 4,866,806,662.25 | 1.28% |
| October 12, 2026 read block | $62,096,266.02 | 4,749,058,127.00 | 1.31% |

The fund was largest as a share of USDe at the end of February 2024 and smallest at the end of September 2025. With the fund flat since then, the share moved with USDe's supply. USDe's supply here is its total supply on Ethereum, which counts the USDe that Ethena's bridge locks there to back USDe on other chains.

## How the reads were made

The reads ran in a browser, through RPCs, public servers that answer queries about a chain, and the two explorers, Blockscout and Routescan. Two RPCs gave the same answers to all 23 reads at block 26,178,998. The month-end figures come from the last block at or before 23:59:59 UTC on the last day of each month, read on two archive RPCs, which serve past states of the chain. Their answers matched for all 33 months. Blockscout listed 182 token transfers of the fund and Routescan 216. Routescan missed one transfer of 135,219 USDT from the sUSDe Payout Fund, listed three of the fund's USDtb conversions twice under different transaction hashes, and listed more untracked tokens. For all 12 tracked tokens, Blockscout's transfers, with sDAI's records of deposits and withdrawals added, matched the balances at every month end and at the read block.

sDAI's contract does not record a transfer when it issues or redeems shares, so the review found the blocks where the fund's sDAI balance changed and read the vault's records in them. The three withdrawals went through Sky's MigrationActions contract into sUSDS. Uniswap and Curve positions are valued from their contracts' state at each block. Every Uniswap deposit and withdrawal matched the position manager's records, and the one Curve deposit matched the pool's. The review grouped the 106 transactions that moved a tracked token by what each did, and the groups add up to the fund's value to the cent.

## Caveats

The figures count only the address that Ethena and the Risk Committee named as the fund. Assets held elsewhere for the same purpose, if there are any, are not in them. Ethena's transparency dashboard, which shows the fund's size, redirected to a page saying that access was restricted, so its figure was not read. Stablecoins and BUIDL are valued at $1, and their market prices can differ. USTB's value at each month end from February to July 2025 uses a price drawn on a straight line between its purchase and redemption prices. The 42 other tokens are not valued. In Blockscout's list, 17 of them were sent to the fund and never left it, including 200,000 SYND, and 5 are tokens named like USDC, from contracts other than USDC's, whose 13 transfers appear as sent from the fund in the same amounts as its real USDC transfers. Routescan listed the other 20. The review could not tell who controls Safe `0xa2af…cced92`, Safe `0x4423…9d9d`, the two addresses that sent $13,239,921.00 or the two that sent the USDtb interest. Figures are rounded separately, so some totals differ from the sum of their rounded lines by a cent.

## Primary sources

[Ethena reserve fund documentation](https://docs.ethena.fi/protocol-overview/reserve-fund) · [Ethena key addresses](https://docs.ethena.fi/technical-design/key-addresses) · [Reserve fund consolidation review](https://gov.ethenafoundation.com/t/685) · [Reserve fund interest review](https://gov.ethenafoundation.com/t/775).

## Reproduce the numbers

The main script checks every input against its recorded SHA-256 fingerprint and stops before writing its tables if any of its 45 checks fails. The browser scripts read the public sources again. The downloads are the [holdings](/research-assets/ethena-reserve-fund-2026-10-12/holdings.csv), the [sources of value](/research-assets/ethena-reserve-fund-2026-10-12/sources_of_value.csv), the [month-end values](/research-assets/ethena-reserve-fund-2026-10-12/month_end.csv), [every transfer](/research-assets/ethena-reserve-fund-2026-10-12/flows.csv), the [grouped transactions](/research-assets/ethena-reserve-fund-2026-10-12/episodes.csv), the [comparison with published figures](/research-assets/ethena-reserve-fund-2026-10-12/risk_committee_comparison.csv), the [chart data](/research-assets/ethena-reserve-fund-2026-10-12/chart_data.csv) and the [calculation files and source inputs](/research-assets/ethena-reserve-fund-2026-10-12/calculation-files.zip).

```text
value         = 42,019,153.458 USDtb
                + 19,980,948 / 19,981,269.345 x (8,787,611.027 USDC + 11,288,960.195 USDtb)
                + 0.3 ETH x 2,520.62 + 106.515 USDS + 1.5 BUIDL + 0.014 USDC
              = 42,019,153.458 + 20,076,248.345 + 864.215
              = 62,096,266.02
share of USDe = 62,096,266.02 / 4,749,058,127.00
              = 1.31%
USDtb share   = (42,019,153.458 + 11,288,778.643) / 62,096,266.02
              = 85.85%
paid in       = 35,665,296.396 + 10,000,321.656 + 10,000,000 + 3,239,921
              = 58,905,539.05
earned        = 1,649,259.202 + 959,648.170 + 416,681.689 + 106,245.270 + 95,300.345 + 28,526.500
              = 3,255,661.18
costs         = -29,097.712 - 30,840.361 - 5,752.433
              = -65,690.51
total         = 58,905,539.05 + 3,255,661.18 - 65,690.51 + 756.30
              = 62,096,266.02
```

The [EthenaPay dashboard](https://ethenadash.com/ethenapay/) tracks USDe spent through EthenaPay, this site's name for Ethena Pay, Ethena's payment app and card, the [sUSDe comparison](https://ethenadash.com/research/ethenapay-vs-susde-2026-10-08/) measures what staked USDe paid in September 2026, and the [methodology page](https://ethenadash.com/methodology/) defines the site's figures.

Related research includes [USDe redemptions after the rsETH exploit](https://ethenadash.com/research/usde-redemptions-rseth-april-2026/), [ENA fee switch milestones](https://ethenadash.com/research/ena-fee-switch-usde-supply-2026-10-12/).

Analysis of public blockchain data. Not investment advice.
