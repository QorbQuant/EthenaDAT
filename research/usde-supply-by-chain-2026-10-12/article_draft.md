# How much USDe was on each chain, and did it add up?

Chain review / USDe on Ethereum and 35 other chains, October 12, 2026

By [Qorban Ferrell · @Degenerate\_DeFi](https://ethenadash.com/about/) · Published 15 October 2026 · Chains read at about 18:41 UTC on October 12, 2026 · Sources read October 12, 2026 UTC

USDe is Ethena's synthetic dollar. Ethena issues it on Ethereum and moves it to other blockchains, here called chains, through LayerZero, a protocol that carries messages between blockchains. On Ethereum a contract that this review calls the adapter locks the USDe that leaves. On the other chain the adapter's peer, the contract there that the adapter sends messages to and accepts messages from, mints the same amount. The adapter and its peers make up Ethena's USDe bridge. At 18:41 UTC on October 12, 2026, the adapter held 2,292,201,958.40 USDe. USDe's total supply on Ethereum, which counts the USDe in the adapter, was 4,746,167,897.22, so the adapter held 48.30% of it. USDe that the bridge mints on another chain is therefore not extra USDe. It stands for USDe locked on Ethereum.

The USDe on the 35 other chains that could be read came to 2,292,201,862.94, which was 95.45 USDe less than the adapter held. One transfer of 0.9995 USDe sent from Ethereum to Stellar had not been delivered, which left 94.45 USDe unexplained, 0.0000041% of the adapter's balance. The adapter's balance ended in a fraction smaller than the unit the bridge moves, a millionth of a USDe. So at least one transfer made outside the bridge had sent USDe straight to the adapter, and such a transfer widens the gap. Solana's supply also ended in a fraction smaller than a millionth, a sign that it had changed outside the bridge.

Five chains held USDe equal to 86.41% of the USDe locked on Ethereum. Plasma held 578,451,105.77 USDe, Solana 468,500,550.24, Base 392,201,135.67, Robinhood Chain 372,492,882.38 and TON 169,126,158.75. Monad, Mantle and BNB Chain held 78 million to 115 million each, and the other 27 chains read held 35,944,795.75 between them.

The adapter's PeerSet records, the entries it writes each time a peer is set or removed, show that a peer was set for 36 chains from March 2024 on and that 25 still had one at the reads. Ethena dropped six chains from the bridge on September 24, 2026 and Linea on September 30 by removing their peers. Those seven chains still held 14,245.50 USDe at the reads. On six of the seven, and on Swellchain and Doma, which Ethena dropped earlier, the chain's own USDe contract named no peer for Ethereum or for any of the other 35 chains, so it could not send USDe to any of them. Metis's contract still named the adapter as its peer, while the adapter no longer named Metis's contract.

## USDe on each connected chain

The table lists the 25 chains where the adapter had a peer at the reads, with the date a peer was first set for each. HyperEVM is the chain of the Hyperliquid network that runs Ethereum-style smart contracts.

| Chain | Peer first set | USDe | Share of locked USDe |
| --- | --- | ---: | ---: |
| Plasma | September 12, 2025 | 578,451,105.77 | 25.24% |
| Solana | August 2, 2024 | 468,500,550.24 | 20.44% |
| Base | June 19, 2024 | 392,201,135.67 | 17.11% |
| Robinhood Chain | June 8, 2026 | 372,492,882.38 | 16.25% |
| TON | April 4, 2025 | 169,126,158.75 | 7.38% |
| Monad | June 17, 2026 | 114,589,612.49 | 5.00% |
| Mantle | March 8, 2024 | 82,495,874.65 | 3.60% |
| BNB Chain | March 12, 2024 | 78,399,747.24 | 3.42% |
| Berachain | January 23, 2025 | 12,976,410.38 | 0.57% |
| Avalanche | August 13, 2025 | 10,884,149.27 | 0.47% |
| HyperEVM | April 30, 2025 | 7,529,626.81 | 0.33% |
| Arbitrum | March 11, 2024 | 1,933,931.18 | 0.08% |
| Ethereal | October 20, 2025 | 1,282,451.92 | 0.06% |
| Blast | April 25, 2024 | 712,090.12 | 0.03% |
| MegaETH | January 7, 2026 | 331,249.26 | 0.01% |
| Morph | December 19, 2024 | 78,421.58 | under 0.01% |
| Zircuit | August 29, 2024 | 66,721.33 | under 0.01% |
| Ink | October 31, 2025 | 64,935.23 | under 0.01% |
| Fraxtal | March 12, 2024 | 30,672.76 | under 0.01% |
| OP Mainnet | March 12, 2024 | 24,917.22 | under 0.01% |
| Aptos | February 5, 2025 | 95.29 | under 0.01% |
| X Layer | June 19, 2024 | 62.78 | under 0.01% |
| Tempo | April 29, 2026 | 22.26 | under 0.01% |
| Tron | September 11, 2026 | 3.70 | under 0.01% |
| Stellar | September 4, 2026 | 1.77 | under 0.01% |

Each figure except Ethereal's is the total supply recorded for the chain's USDe, read at the block or time given in the downloads. Ethereal is a chain whose native coin, the coin it uses to pay for transactions, is USDe, so its figure is the USDe that the adapter's peer on Ethereal received less the USDe that the peer sent. Avalanche's figure includes 500,992.49 USDe held by Ethena's PSM custodian, an address that holds USDe minted in advance for Ethena's peg stability modules, contracts that swap USDe one for one with other stablecoins. Ethena's key addresses page said that USDe held at the custodian was not in circulation. The custodian held no USDe on the other 27 chains that run Ethereum-style smart contracts where its balance was read, or on Tron, and it held 0.56 USDe on Ethereum.

![Horizontal bar chart of USDe on each chain at about 18:41 UTC on October 12, 2026, in millions. Plasma 578.5, Solana 468.5, Base 392.2, Robinhood Chain 372.5, TON 169.1, Monad 114.6, Mantle 82.5, BNB Chain 78.4, Berachain 13.0, Avalanche 10.9 and 25 other chains 12.1.](/research-assets/usde-supply-by-chain-2026-10-12/chart_usde_by_chain.svg)

*USDe on each chain read at about 18:41 UTC on October 12, 2026, Swellchain's at 06:39 UTC · Shares of the adapter's balance at Ethereum block 26,178,253*

## How the count adds up

| Line | USDe |
| --- | ---: |
| USDe's total supply on Ethereum, including the adapter's USDe | 4,746,167,897.22 |
| Locked in the adapter | 2,292,201,958.40 |
| On Ethereum outside the adapter | 2,453,965,938.83 |
| On the 35 other chains read | 2,292,201,862.94 |
| Adapter less the chains | 95.45 |
| Sent from Ethereum to Stellar and not delivered | 1.00 |
| Unexplained | 94.45 |

The reads of Ethereum and the other chains started together at 18:41:47 UTC and ended by 18:42:16 UTC. A transfer between chains takes effect on the sending chain first and on the receiving chain a few minutes later, so a transfer under way at the reads would show on one side and not the other. The adapter's peer on Ethereal also named peers of its own on seven other chains, and the contracts on Plasma and Tron named each other, so USDe could move between those chains without passing through Ethereum. LayerZero Scan, LayerZero's public record of messages, listed 153 USDe transfers on any route, sent from 18:41 UTC on October 11 to its read at 18:48 UTC on October 12. Comparing each transfer's blocks or times with the reads found one transfer that had left one chain and not reached the other, the 0.9995 USDe sent to Stellar at 16:29 UTC. LayerZero Scan showed that its delivery had failed a test run on Stellar and had not been carried out.

The adapter's own code takes in USDe only when it locks a transfer and pays out USDe only when it unlocks one, and both amounts are whole millionths of a USDe. Its balance still had 0.000000471165449406 USDe beyond a whole number of millionths, so at least one transfer of USDe made outside the bridge had gone straight to its address. USDe sent straight to the adapter stays locked with nothing minted against it, which keeps the adapter's balance above the chains' total. Every chain's supply was a whole number of millionths except Solana's, which had 0.000000552 beyond one. If the bridge also moves only whole millionths on Solana, Solana's supply had changed outside the bridge. Only the adapter's peer on Solana could create USDe there, so such a change would have been a removal, which also keeps the adapter's balance above the chains' total. So would a transfer left undelivered for longer than the 24 hours searched, and any USDe left on Plume's 2024 network, which could not be read because the only RPC listed for it, a public server that answers queries about a chain, did not answer. The review could not tell how much of the 94.45 USDe each accounted for.

## Chains Ethena dropped

Ethena dropped 11 chains by setting their peer on the adapter to zero. Six of the changes were made in a single Ethereum block, 26,045,746, on September 24, 2026.

| Chain | Dropped | USDe left | Peers its contract named |
| --- | --- | ---: | --- |
| Plume's 2024 network | March 5, 2025 | not read | not read |
| Doma | April 22, 2026 | 0.00 | none |
| Swellchain | July 7, 2026 | 14,785.22 | none |
| Initia | September 9, 2026 | 2.18 | not read |
| Kava | September 24, 2026 | 139.86 | none |
| Manta Pacific | September 24, 2026 | 1,749.24 | none |
| Metis | September 24, 2026 | 372.02 | Ethereum |
| Mode | September 24, 2026 | 974.77 | none |
| Scroll | September 24, 2026 | 1,953.77 | none |
| ZKsync Era | September 24, 2026 | 2,568.99 | none |
| Linea | September 30, 2026 | 6,486.86 | none |

The 10 dropped chains read held 29,032.90 USDe. Swellchain's figure came from a block of 06:39 UTC on October 12. The only Swellchain RPC that answered served that block as its latest, so the review had no later read of Swellchain. Ethena also changed one peer without dropping a chain. On May 7, 2026 it replaced Tempo's peer with a different contract.

## How other counts compare

DefiLlama, a site that tracks stablecoin supply by chain, gave the same figure to the millionth of a USDe for 25 chains when read at 19:14 UTC, once the PSM custodian's USDe was taken out of Avalanche's figure. DefiLlama's latest daily record counted 500,993.05 USDe as unreleased, separately from the USDe it counted as circulating. That figure equaled the custodian's balances on Avalanche and Ethereum together. DefiLlama's Solana, Base and Robinhood Chain figures differed by 117,071.09 to 657,413.37 USDe, and the review could not tell when DefiLlama had read those chains. It showed no USDe on Swellchain. It left out Ethereal, Aptos, Tron, Initia, Stellar and Doma, and it listed 21,072.21 USDe on Movement, a chain that did not appear in the adapter's records, so that token was not part of this count.

Ethena's key addresses page, last updated on September 17, 2026, listed 22 chains where Ethena's tokens were available. Eight of them, Kava, Linea, Manta Pacific, Metis, Mode, Scroll, Swellchain and ZKsync Era, had no peer on the adapter at the reads. The list left out 11 chains that did, Avalanche, Ethereal, HyperEVM, Ink, MegaETH, Monad, Plasma, Robinhood Chain, Stellar, Tempo and Tron. Tempo appeared in the page's table of addresses but not in its list.

## How the reads were made

The adapter is the contract at `0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34` on Ethereum, the same address as USDe's contract on most other chains. Its token is USDe at `0x4c9edd5852cd905f086c759e8383e09bff1e68b3`, and a read of its settings showed that it locks USDe rather than minting it. Routescan is an explorer, a website that indexes a chain's records. It showed the adapter's verified source code, which moves USDe only when the adapter locks or unlocks a transfer. The chains come from the adapter's 49 PeerSet records. Blockscout and Routescan, two explorers of Ethereum, returned the same 49 records. At the read block the adapter's peers for all 186 of LayerZero's endpoint IDs, its numbers for chains, matched the last record for each chain, and a second RPC gave the same peers for the 36 chains.

LayerZero's chain metadata gave each chain's ID and, for most chains, the address of its USDe and its RPCs. Where it gave no address, the review used the adapter's peer for that chain, and the read script in the calculation files lists the other RPCs and services the review used. Every RPC was checked for the right chain ID before the reads, which caught one RPC listed for Zircuit that served a different chain. For 28 chains that run Ethereum-style smart contracts and for Tron, the review read the USDe contract's total supply, its decimals, the PSM custodian's balance and the contract's peers for Ethereum and the other 35 chains at one block. On Ethereal the review read the same peers from the adapter's peer there. Arbitrum's peers for the other chains came from a second RPC about ten minutes later. Solana's supply came from two RPCs, and the Solana mint's authority to create USDe was the adapter's peer there. Aptos's and Initia's supplies each came from two sources reading the same state of the chain, TON's from toncenter and tonapi, two services that index TON, less than a second apart, and Stellar's from Stellar Expert, an explorer of Stellar. A second source gave the same supply for 27 chains. Later second reads matched for BNB Chain, Plasma, Robinhood Chain and Tempo and showed Avalanche's supply up 29,478.68 USDe ten minutes later. LayerZero Scan, read four minutes before that second read, listed no transfer that explains the rise.

The adapter's peer on Ethereal held none of Ethereal's USDe at the read. From the chain's first block to the read, it recorded 23,652 arrivals of 185,867,690.74 USDe and 29,129 departures of 184,585,238.83 USDe, which left 1,282,451.92 USDe on Ethereal. The peers named by the contracts on the dropped chains come from the same reads. The [Avalanche USDe review](https://ethenadash.com/research/avalanche-usde-ethenapay-2026-10-11/) follows the USDe on Avalanche holder by holder.

## Caveats

The figures describe one moment, and every transfer between chains changes them. A chain's figure is the USDe minted there, not who holds it or what it is used for. The PSM custodian's USDe on Avalanche counts in Avalanche's figure, though Ethena's key addresses page said it was not in circulation. TON's and Stellar's figures come from services that index those chains rather than from an RPC. Ethereal's figure counts only USDe that arrived through the bridge. The contracts on Solana, TON, Aptos, Initia and Stellar were not checked for peers, and the other contracts were checked only for peers on Ethereum and the other 35 chains. RPCs and explorers are run by third parties, which is why each figure was checked against a second source where one answered.

## Primary sources

[Ethena key addresses](https://docs.ethena.fi/technical-design/key-addresses).

## Reproduce the numbers

The main script checks every input against its recorded SHA-256 fingerprint and stops before writing its tables if any of its 43 checks fails. The browser scripts read the public sources again. The downloads are the [USDe on each chain](/research-assets/usde-supply-by-chain-2026-10-12/chains_table.csv), the [reconciliation](/research-assets/usde-supply-by-chain-2026-10-12/reconciliation.csv), the [dropped chains](/research-assets/usde-supply-by-chain-2026-10-12/dropped_chains.csv), the [peer history](/research-assets/usde-supply-by-chain-2026-10-12/peer_timeline.csv), the [comparison with DefiLlama](/research-assets/usde-supply-by-chain-2026-10-12/defillama_comparison.csv), the [chart data](/research-assets/usde-supply-by-chain-2026-10-12/chart_data.csv) and the [calculation files and source inputs](/research-assets/usde-supply-by-chain-2026-10-12/calculation-files.zip).

```text
locked share      = 2,292,201,958.40 / 4,746,167,897.22
                  = 48.30%
difference        = adapter balance - USDe on the 35 chains read
                  = 2,292,201,958.395178471165449406 - 2,292,201,862.942721552
                  = 95.452456919165449406
unexplained       = difference - undelivered transfer to Stellar
                  = 95.452456919165449406 - 0.9995
                  = 94.452956919165449406, or 0.0000041% of the adapter's balance
five largest      = (578,451,105.77 + 468,500,550.24 + 392,201,135.67
                     + 372,492,882.38 + 169,126,158.75) / 2,292,201,958.40
                  = 86.41%
Ethereal          = 185,867,690.742058 received - 184,585,238.826468 sent
                  = 1,282,451.915590
```

The [EthenaPay dashboard](https://ethenadash.com/ethenapay/) tracks EthenaPay's USDe on Avalanche, and the [methodology page](https://ethenadash.com/methodology/) defines the site's figures.

Related research includes [USDe supply and ENA buyback milestones](https://ethenadash.com/research/ena-fee-switch-usde-supply-2026-10-12/).

Analysis of public blockchain data. Not investment advice.
