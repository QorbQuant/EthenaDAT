# How much of Avalanche's USDe was in EthenaPay wallets?

Chain review / USDe on Avalanche to October 11, 2026

By [Qorban Ferrell · @Degenerate\_DeFi](https://ethenadash.com/about/) · Published 12 October 2026 · Chain read to the end of October 11, 2026 UTC · Sources read October 12, 2026 UTC

USDe is Ethena's synthetic dollar, and EthenaPay is this site's name for Ethena Pay, Ethena's payment app and card. At the end of October 11, 2026 UTC, 10,542,847.89 USDe existed on Avalanche C-Chain, the chain of the Avalanche network that runs Ethereum-style smart contracts. This review calls that total the supply and calls the chain Avalanche for short. EthenaPay wallets held 5,985,275.68 USDe, 56.8% of the supply. The wallets are smart-contract accounts, accounts run by code on the chain, and two factory contracts create them for the app. Of the 14,740 wallets created by the end of October 11, 1,216 held USDe.

Accounts tied to EthenaPay held 8,894,983.58 USDe, 84.4% of the supply. They are the wallets and three other groups. The settlement addresses are the two addresses, one in use and one retired, that received the USDe spent with the card. The settlement recipients are three accounts whose every USDe came from the settlement addresses. The reward accounts are the three accounts that the daily query behind the site's [EthenaPay dashboard](https://ethenadash.com/ethenapay/) lists as paying rewards into the wallets. The settlement recipients alone held 2,555,254.55 USDe, 24.2% of the supply.

On May 14, the day before the first wallets were created, 191,615.18 USDe existed on Avalanche. By October 11 the supply was 55 times as large and about twice its 2025 high. Most of the new USDe arrived at the rhino.fi bridge contract, the Avalanche contract of a bridge that moves tokens between blockchains. Deposits here are the USDe EthenaPay wallets received from accounts other than wallets, settlement addresses and reward accounts, or straight from another chain. From May 15 to October 11 the rhino.fi bridge contract paid 12,605,496.43 USDe into the wallets, 89.6% of their deposits.

## Who held the USDe at the end of October 11

The table splits the supply among those groups, the rhino.fi bridge contract, the Uniswap v3 pool and the other accounts. The Uniswap v3 pool is a contract that paired USDe with USDC, another dollar token, so that either could be traded for the other. The other accounts are all holders outside the named groups.

| Holder | Accounts | USDe | Share of supply |
| --- | ---: | ---: | ---: |
| EthenaPay wallets | 1,216 | 5,985,275.68 | 56.8% |
| Settlement recipients | 3 | 2,555,254.55 | 24.2% |
| Settlement addresses | 1 | 325,047.37 | 3.1% |
| Reward accounts | 3 | 29,405.98 | 0.3% |
| Uniswap v3 pool | 1 | 298,106.73 | 2.8% |
| rhino.fi bridge contract | 1 | 135,692.19 | 1.3% |
| Other accounts | 455 | 1,214,065.40 | 11.5% |
| All holders | 1,680 | 10,542,847.89 | 100.0% |

Each amount is rounded to the cent on its own, so the rows add up to the total only to within a cent. One of the two settlement addresses held USDe at the end of the day and the other held none. When read on October 12, the Uniswap v3 pool charged a fee of 0.05% on each trade. The 447 smallest of the 455 other accounts held 14,592.86 USDe between them. The supply is all the USDe that had arrived on Avalanche less all that had left. It matched the total kept by the token contract, USDe's contract on Avalanche, as [How the count was made](#how-the-count-was-made) shows.

## The supply rose to 55 times its May 14 level

| End of day | Supply | In EthenaPay wallets | Wallets' share | Share held by accounts tied to EthenaPay |
| --- | ---: | ---: | ---: | ---: |
| May 14 | 191,615.18 | 0.00 | 0.0% | 0.0% |
| May 31 | 194,042.79 | 3,870.16 | 2.0% | 2.0% |
| June 30 | 498,680.33 | 32,821.83 | 6.6% | 11.1% |
| July 31 | 750,535.83 | 128,980.95 | 17.2% | 31.5% |
| August 31 | 1,491,580.61 | 530,905.24 | 35.6% | 59.6% |
| September 30 | 7,397,742.08 | 3,712,925.71 | 50.2% | 76.5% |
| October 11 | 10,542,847.89 | 5,985,275.68 | 56.8% | 84.4% |

The wallets' USDe first passed half of the supply on September 2, at 64.3%. From then to October 11 the wallets' share moved between 48.1% on October 5 and 76.9% on September 8, and it was below half on 7 of those 40 days. The share moves whenever USDe enters or leaves the wallets and whenever USDe arrives on Avalanche or leaves it. On September 22 it fell 8.6 points in a day.

The chart splits the supply into three bands. EthenaPay wallets are the bottom band. The settlement and reward accounts, the middle band, are the settlement addresses, the settlement recipients and the reward accounts together. Holders outside EthenaPay, the top band, are all holders not tied to EthenaPay, the Uniswap v3 pool and the rhino.fi bridge contract among them. The chart's data comes from the Routescan explorer, a public website and API that indexes Avalanche.

![Stacked area chart of 150 days. The supply of USDe on Avalanche C-Chain rose from 0.187 million on May 15, 2026, the day the first EthenaPay wallets were created, to 10.543 million on October 11. Most of the rise came from September on. EthenaPay wallets, the bottom band, held more than half of the supply for the first time on September 2 and 5.985 million on October 11. The settlement and reward accounts, the middle band, held 2.910 million on October 11, and holders outside EthenaPay, the top band, 1.648 million. A dashed line marks the 2025 high of 5.237 million.](/research-assets/avalanche-usde-ethenapay-2026-10-11/chart_avax_usde_holders.svg)

*Transfers of USDe on Avalanche C-Chain, read from the Routescan explorer API on October 12, 2026 UTC · Wallets from EthenaPay's two factory contracts*

## Most of the new USDe arrived at the rhino.fi bridge contract

When read on October 12, the explorer named the token contract USDeOFT. The explorer also showed the contract's verified source, the code its developers published, checked by the explorer against the code on the chain. That source builds on the OFT, or omnichain fungible token, standard of LayerZero, a protocol that carries messages between blockchains. In it USDe is minted, or created, on Avalanche only when it arrives from another chain, and burned, or destroyed, only when it is sent to one. So every mint in the count is USDe arriving on Avalanche and every burn is USDe leaving it.

From May 15 to October 11, 16,505,582.27 USDe arrived on Avalanche and 6,154,349.56 USDe left, a net 10,351,232.71. Of the USDe that arrived, 13,485,247.44, or 81.7%, arrived at the rhino.fi bridge contract, `0x5e023c31e1d3dcd08a1b3e8c96f6ef8aa8fcacd1`. When read on October 12, rhino.fi's bridge configuration listed this contract as its contract on Avalanche. The explorer showed the contract as a proxy, a contract that runs another contract's code, here one named DVFDepositContract. From its first USDe on March 5, 2026, 99.7% of the USDe it received arrived from another chain straight into it, and none of its USDe left Avalanche. A bridge of this kind can also pay out on another chain from funds it holds there, which a count on Avalanche does not show.

The rhino.fi bridge contract paid 12,605,496.43 USDe into EthenaPay wallets in 4,690 transfers, 93.8% of all the USDe it sent from March 5 on. From May 15 to October 11 the wallets received 14,075,752.58 USDe in deposits, the name the site's [cash-flow review](https://ethenadash.com/research/ethenapay-cash-flows-2026-10-05/) also gives this flow, so the rhino.fi bridge contract supplied 89.6% of them. Other accounts sent 1,470,246.15 USDe, and 10 USDe arrived from another chain straight into a wallet. The chain does not show why the USDe went through rhino.fi. EthenaPay's FAQ and Terms of Use, searched on October 12, named neither rhino.fi nor any bridge.

## Most USDe paid to the settlement addresses went on to three accounts

A card payment here is a transfer of USDe from a wallet to a settlement address, the flow the cash-flow review calls card spend. From May 15 to October 11, 37,731 card payments moved 2,945,283.40 USDe from wallets to the settlement addresses, and other accounts sent them 75,010.00 USDe in 7 transfers. Of the 3,020,293.40 USDe they received, the settlement addresses paid 2,555,259.55 USDe, 84.6%, to the settlement recipients in 83 transfers. They sent 139,986.48 USDe back to wallets in 2,516 transfers, called returns here. None of their USDe left Avalanche and they sent none to any other account. They held 325,047.37 USDe at the end of October 11.

The largest settlement recipient received 2,468,211.09 USDe from August 8, 2026 on, 96.6% of what the three received, all of it from the settlement addresses. It had sent none by the end of October 11. A second settlement recipient passed 5 USDe on to one of the other accounts, so the settlement recipients held 5 USDe less than they received. Together the settlement addresses and the settlement recipients held 2,880,301.92 USDe, 27.3% of the supply. The chain does not show who controls these accounts or why the USDe stayed in them.

## Where the wallets' USDe went

From May 15 to October 11, 14,237,138.00 USDe went into wallets and 8,251,862.32 came out, which left the 5,985,275.68 they held at the end of October 11, not counting 119,834.44 USDe moved from one wallet to another. Besides the deposits, the wallets received 139,986.48 USDe in returns and 21,398.94 USDe from the reward accounts. Apart from card payments, 5,306,578.92 USDe went out of the wallets, the flow the cash-flow review calls withdrawals, all but 38.05 of it to other accounts. Of the rest, 36.05 USDe went to the rhino.fi bridge contract and 2 USDe left Avalanche straight from a wallet. Of the 6,154,349.56 USDe that left Avalanche from May 15, all but those 2 left from other accounts.

## Before EthenaPay

The token contract was created on August 8, 2025, in block 66,748,921. A block is one of the numbered batches in which the chain records transactions. Apart from amounts below a thousandth of a USDe on August 15 and 18, the first USDe arrived on August 19, 9,995 of it, and 2,497,499.41 USDe arrived on August 28. The supply reached its 2025 high, 5,237,412.27 USDe, on October 23, 2025. On October 29, 5,051,606.19 USDe left, and the year ended with 62,858.10 USDe on Avalanche. A second rise took the supply to 1,910,531.50 USDe on March 5, 2026, and 1,803,364.65 USDe left the next day. On May 14, 397 accounts held the 191,615.18 USDe on Avalanche.

## How the count was made

A browser read every USDe Transfer record on Avalanche from the token's deployment to block 97,318,132, the last block of October 11 UTC, from the Routescan explorer's API. A Transfer record is the entry the token contract writes for each movement of USDe. The browser also read every contract that EthenaPay's two factory contracts created with CREATE2, a way of creating a contract at an address fixed in advance. That is the wallet rule of the chain recount the site published with its [adoption review](https://ethenadash.com/research/ethenapay-adoption-2026-10-05/), here the published recount. The first factory contract was created on May 15, 2026 and the second on June 10, so no wallet existed before May 15.

The explorer listed 147,715 Transfer records. Of these, 63, all from August and September 2025, had an empty amount and an empty block hash. A block hash is the identifier of the block that holds a record. The receipts of these 63 records' transactions did not contain them, so the count left them out. A receipt is the chain's own record of what a transaction did. None of the 63 involved a wallet, a settlement address or a reward account. The other 147,652 records give every account's balance at the end of each UTC day.

The count ties to the token contract. Its totalSupply, the contract's own total, was 10,532,847.89 USDe at block 97,362,128 on October 12. Adding back the 10,000.00 USDe that left after October 11 and up to that block gives 10,542,847.89, the count's supply at the end of October 11.

The USDe in wallets also matched the published recount to the wei, the token's smallest unit, on all 144 days from May 15 to October 5, as did the number of wallets created and the number holding USDe. The published recount's totals over those days matched as well, deposits of 11,056,937.78 USDe and card payments of 2,470,248.65 USDe to October 5, its withdrawals, returns and transfers between wallets, and its two reward flows taken together. The published recount calls the returns reversals. Over the same days it counted 29,556 spend events, the records logged for card purchases, against 29,557 card payments in this count, and its spend events came to 5 USDe less, all of it on September 24.

The settlement addresses and the reward accounts are those named in the daily query. A settlement recipient is an account outside those groups and the wallets whose every USDe to the end of October 11 came from a settlement address. The rhino.fi bridge contract is the one that rhino.fi's bridge configuration listed for Avalanche, and the Uniswap v3 pool is the contract at `0x833e0ff43a8691f623cb8730ddb3e3180c7de08b`, which paired USDe with USDC at a fee of 0.05%. Every other holder counts as one of the other accounts. The site's guide [A transaction is not a card purchase](https://ethenadash.com/research/ethenapay-spend-events/) explains why one Avalanche transaction can hold card payments from several wallets, which is why the count works transfer by transfer.

## What the count leaves out

A wallet is not a person, and one person may hold several wallets. The chain does not show who controls the settlement recipients, the other accounts or the rhino.fi bridge contract, or whether EthenaPay's app routes deposits through rhino.fi. The settlement recipients count as tied to EthenaPay only because all their USDe came from the settlement addresses. The shares are for the end of each UTC day and move from day to day. The check against the published recount ends on October 5, so the wallets' figures for October 6 to 11 rest on this count alone. The supply on October 11 ties to totalSupply, but no outside source checks how the USDe outside the wallets splits among the other groups. The count covers Avalanche alone, so USDe on Ethereum and other chains is outside it.

## Reproduce the numbers

The main script checks every input against its recorded SHA-256 fingerprint and stops before writing its tables if any of its 74 checks fails. The chain read's script fetches the public data again. The downloads are the [holders at the end of October 11](/research-assets/avalanche-usde-ethenapay-2026-10-11/holders_at_end.csv), the [month ends](/research-assets/avalanche-usde-ethenapay-2026-10-11/month_ends.csv), the [wallets' flows](/research-assets/avalanche-usde-ethenapay-2026-10-11/wallet_flows.csv), the [settlement flows](/research-assets/avalanche-usde-ethenapay-2026-10-11/settlement_flows.csv), the [chart data](/research-assets/avalanche-usde-ethenapay-2026-10-11/chart_daily.csv) and the [calculation files and source inputs](/research-assets/avalanche-usde-ethenapay-2026-10-11/calculation-files.zip).

```text
supply on October 11 = USDe arrived to the end of the day - USDe left to the end of the day
                     = 38,432,121.456105 - 27,889,273.563368
                     = 10,542,847.892737
tie to the token     = totalSupply at block 97,362,128 - arrived after October 11
                       + left after October 11
                     = 10,532,847.892737 - 0 + 10,000
                     = 10,542,847.892737
wallets' share       = 5,985,275.68 / 10,542,847.89
                     = 56.8%
tied to EthenaPay    = 5,985,275.68 + 325,047.37 + 2,555,254.55 + 29,405.98
                     = 8,894,983.58, or 84.4%
rhino.fi share       = 12,605,496.43 / 14,075,752.58
                     = 89.6% of deposits
growth since May 14  = 10,542,847.89 / 191,615.18
                     = 55.0 times
```

The [EthenaPay dashboard](https://ethenadash.com/ethenapay/) tracks wallets, balances, spending and rewards, and the [methodology page](https://ethenadash.com/methodology/) defines the site's figures.

Analysis of public blockchain data. Not investment advice.
