# What is USDEB, and how much StablecoinX stock does it represent?

Explainer / USDEB on BNB Smart Chain

By [Qorban Ferrell · @Degenerate\_DeFi](https://ethenadash.com/about/) · Published 8 October 2026 · Chain data through 22:28 UTC, October 8, 2026 · Sources read October 8, 2026

USDEB is a Binance bStock, a tokenized security on BNB Smart Chain that Binance says is backed one for one by StablecoinX shares held at a custodian. The shares are StablecoinX's Class A stock, which trades on Nasdaq as USDE. Ethena's synthetic dollar, USDe, is a different token from a different issuer.

Binance's bStocks (Conversion) Product Terms, the Conversion Terms here, describe each token as a beneficial interest in a share held by the token's issuer, Btech Holdings Ltd. A beneficial interest is an economic interest in the share without direct ownership of it. Binance's bStocks guide calls the issuer a Binance group affiliate. Binance does not offer USDEB to US persons or to anyone in the United States, and its documents say bStocks do not represent any affiliation with the company whose shares back them.

At 22:28 UTC on October 8, 2026, 41,856.57 USDEB were outstanding. At one share per token, that was 0.17% of the 24,139,375 Class A shares this site's [StablecoinX dashboard](https://ethenadash.com/stablecoinx/) counted at the cutoff. The contract creates tokens in mints and destroys them in burns, and every mint and burn from deployment to the cutoff added up to the supply recorded then, to the last unit. Binance's [proof-of-collateral page](https://www.binance.com/en/proof-of-collateral/bstocks), where it reports the backing of each bStock, had no USDEB entry when this review read it, so this review could not count the shares held for the tokens.

The dashboard's USDEB panel tracks that supply and changes no other figure. USDEB is created from shares that are already outstanding, so it adds no shares to StablecoinX and no ENA, the Ethena governance token the company holds. Token NAV, the reported ENA holdings valued at the ENA price, and mNAV, the share price divided by token NAV per share, stay as they were.

## USDE, USDEW, USDEB and USDe are different instruments

The names differ by a letter or a capital, and USDEB and USDe both exist on BNB Smart Chain.

| Name | What it is | Issued by | Where it trades or is held | What the holder has |
| --- | --- | --- | --- | --- |
| USDE | Class A common stock | StablecoinX Inc. | Nasdaq | Shares in a company whose treasury strategy is focused on ENA |
| USDEW | Public warrant | StablecoinX Inc. | Nasdaq | A right to buy Class A shares on the warrant's terms |
| USDEB | bStock, a tokenized security | Btech Holdings Ltd | Binance Spot and BNB Smart Chain | A beneficial interest in a Class A share held by the token's issuer |
| USDe | Synthetic dollar | Ethena | Ethereum and other chains, BNB Smart Chain among them | A dollar token backed by crypto assets and short futures positions |
| ENA | Governance token | Ethena | Ethereum and other chains | Governance rights in the Ethena protocol |

The [StablecoinX prospectus](https://www.sec.gov/Archives/edgar/data/2080215/000121390026099731/ea0305435-424b3_stable.htm) of September 14 lists the Class A stock under USDE and the warrants under USDEW. It describes the company's treasury strategy as focused on acquiring, holding and using ENA. Ethena's [documentation](https://docs.ethena.fi/) defines USDe as a synthetic dollar and ENA as the protocol's [governance token](https://docs.ethena.fi/overview/ena). Binance's [listing announcement](https://www.binance.com/en/square/post/374582526748706) of October 7 gives the USDEB contract.

On BNB Smart Chain, the USDEB contract is `0xDfD3Ba51D4591f243481a6f26059d1a5Ee95252F` and Ethena's USDe is `0x5d3a1Ff2b6BAb83b63cd9AD0787074081a52ef34`, the address Ethena's [key addresses page](https://docs.ethena.fi/technical-design/key-addresses) lists for BNB Smart Chain and several other networks. The USDEB contract stores its name as StablecoinX Inc., though StablecoinX did not issue it.

The dashboard also tracks a perpetual futures market on StablecoinX's stock, a derivative with no expiry date, which the Lighter exchange lists as STABLECOINX. A position in it carries no claim on a share or a token.

## A USDEB holder has a beneficial interest in a share the token issuer holds

Besides the listing announcement, three Binance documents set out what a holder has. They are the [bStocks guide](https://www.binance.com/en/academy/articles/what-are-bstocks-a-guide-to-tokenized-stocks-on-binance), version 1.0 of the [Conversion Terms](https://www.binance.com/en/about-legal/product-terms-minting-redemption), effective June 11, 2026, and the [admission notice](https://www.binance.com/en/about-legal/admission-trading-notices-20061007) that admitted USDEB to trading on October 7. The disclaimer on the announcement, the guide and the notice says "bStocks are not stocks or shares".

| Question | What Binance's documents say | Where |
| --- | --- | --- |
| Who issues it | Btech Holdings Ltd, a private company incorporated in the Abu Dhabi Global Market (ADGM), an international financial center with its own regulator. BTech Services Limited manages and tokenizes for it. The bStocks guide spells the issuer's name BTech Holdings Limited | Conversion Terms, definitions. bStocks guide |
| What backs it | One StablecoinX share per token, held by the issuer. The Conversion Terms name Alpaca as custodian without saying in whose name it holds the shares. Nest Clearing and Custody Limited is the central securities depository that records holdings of the tokens | bStocks guide. Conversion Terms 1(a) and definitions. Admission notice paragraph 9 |
| Does the holder own the share | Only indirectly. Each token is a beneficial interest in a share the issuer holds. The tokens do not represent any affiliation with StablecoinX | Conversion Terms 1(a) and 2(a). Admission notice disclaimer |
| Votes | None of the four Binance documents mentions voting | Text searches of all four |
| Dividends and splits | A multiplier raises balances by the net dividend, reinvested, and adjusts them for splits. It stood at 1.0 at the cutoff. The StablecoinX prospectus said the company had never paid a cash dividend and did not expect to | bStocks guide. The token contract. StablecoinX prospectus, dividend policy |
| Creating and redeeming | Eligible users convert shares they bought through Binance one for one. Nest Trading Limited, one of Binance's ADGM companies, takes the shares and delivers the tokens itself. Shares bought elsewhere cannot be converted. Nest Trading charges no fee for the conversion itself. Redemption delivers shares one for one to the user's account with Nest Trading, and the Conversion Terms describe no redemption for cash | Conversion Terms 3(b), 3(c), 6(b), 7(b), 7(c) and 10(a) |
| Timing | The Conversion Terms guarantee no timeframe for a conversion. Nest Trading may reject or cancel an order for any reason, and minting, burning and transfers may be suspended | Conversion Terms 11(a) to 11(c) |
| Who may hold it | Eligible users outside the United States. The Conversion Terms bar US persons and anyone physically in the United States, and the tokens are not registered under the US Securities Act of 1933. bStocks are offered under prospectuses approved in the ADGM | Listing announcement. Conversion Terms 4(b) and definitions. Admission notice disclaimer |
| Tokens outside Binance | The listing announcement set withdrawals to open at 13:00 UTC on October 7. The transfer restrictions are built into the token contract and still bind after a token leaves Binance. A token held in breach of them may be frozen, rescinded or cancelled, which may deny the holder all economic benefit. Tokens at non-compliant addresses may be frozen, and moving tokens back into the depository is subject to conditions | Listing announcement. Conversion Terms 8(a), 8(c) and 8(d). Admission notice disclaimer |
| Price | USDEB trades around the clock on Binance Spot against USDT, Tether's dollar stablecoin. Binance sets trading bands at approximately ±20% of the Nasdaq price of one share, using the live price during Nasdaq's regular hours and the last available price outside them | bStocks guide. Admission notice paragraphs 6 and 9 |
| If a party fails | None of the four documents says what holders receive if the issuer, Nest Trading or the custodian fails. The bStocks guide lists issuer and custody risk. Shares in transit during a conversion lose the custody protections of Nest Trading's omnibus account, an account that pools many clients' shares | bStocks guide, risks. Conversion Terms 6(d) |

The bStocks guide points to a proof-of-collateral page for checking the backing. When this review read that page at 22:26 UTC on October 8, it listed 87 bStocks and had no entry for USDEB or for the three other tokens Binance listed the same day. It still had none at 23:26 UTC.

## Supply peaked on October 7 and stood at 0.17% of Class A shares

The USDEB contract was deployed on September 28 and had no tokens outstanding until 08:15 UTC on October 7. Binance scheduled trading to open at 12:00 UTC and let users convert shares they already held through Binance before then. The admission notice admitted up to 1,200,000 USDEB to trading at the open and said the number afterwards would depend on demand and liquidity. At the open, 25,771 USDEB existed, 2.1% of that number.

![Stepped line chart of USDEB outstanding on BNB Smart Chain from 06:00 UTC on October 7 to 22:28 UTC on October 8, 2026. Supply was zero until 08:15 UTC and reached 25,771 before trading opened at 12:00 UTC. It peaked at 52,154 at 22:15 UTC and fell to 39,899 after a burn of 12,255 at 23:26 UTC, both on October 7, and stood at 41,857 at 22:28 UTC on October 8.](/research-assets/usdeb-stablecoinx-bstock/chart_usdeb_supply.svg)

*USDEB outstanding after every mint and burn, times in UTC. The total at the cutoff equaled the supply the contract reported at that block.*

| Period, UTC | Mints | USDEB minted | Burns | USDEB burned | Supply at the end |
| --- | ---: | ---: | ---: | ---: | ---: |
| October 7, before trading opened at 12:00 | 4 | 25,771.00 | 0 | 0.00 | 25,771.00 |
| October 7, from 12:00 | 27 | 26,383.43 | 1 | 12,255.35 | 39,899.07 |
| October 8, to 22:28 | 9 | 1,957.50 | 0 | 0.00 | 41,856.57 |

Each figure is rounded on its own, so a total can differ by 0.01 from the sum of the rounded figures.

At one share per token and the October 8 Nasdaq close of $12.79, the 41,856.57 USDEB outstanding at the cutoff would correspond to about $535,000 of stock. The dashboard recorded the same close. The figure uses no USDEB market price.

Every mint went to the same address, and the burn came from a different one. The Binance documents reviewed here identify neither address, and this review does not attribute them. Each of the 40 mints landed between 11 and 47 seconds after a five-minute mark on the clock, which suggests minting runs on a schedule. One mint may then cover several conversions, so a mint count may not match the number of orders.

At 22:40 UTC on October 8, with supply unchanged since the cutoff, BscScan, a block explorer for BNB Smart Chain, tagged the largest holding address, with 82.3% of supply, as a Binance exchange wallet. One untagged address held another 16.9%. The tags are BscScan's, and an address is not a person.

## Three sources agreed on every mint and burn

The dashboard reads USDEB's Transfer logs, the records the contract writes for every token movement, through Dune, a service that indexes blockchain data. It keeps a mint and burn history only when mints less burns equal totalSupply, the supply the contract itself reports, at the same block. Its file generated at 22:27 UTC on October 8 listed 40 mints and one burn through 19:14 UTC, and a later chain reading by its collector found the same supply at 22:25 UTC.

Each of those 41 events also matched the record of its transaction from a public BNB Smart Chain node, a server that keeps a copy of the chain, on block, amount and direction. BscScan's list of transfers from and to the zero address, the address that stands for creation and destruction, showed the same 41 events and no others at 22:31 UTC. At block 126,523,880, at 22:28:25 UTC, totalSupply read 41,856.57010848 USDEB, equal to 54,111.92395023 minted less 12,255.35384175 burned.

## The dashboard tracks supply and changes no other figure

The panel reads USDEB supply at one block and adjusts it for the multiplier. Its value at recorded price multiplies that supply by the latest Nasdaq close of USDE in the dashboard's data. Its share of Class A equity divides supply by the dashboard's Class A count, which leaves out warrants and is not the free float, the shares available for public trading.

Its flow chart shows mints and burns in token units before the multiplier. The panel notes that these measure supply and that neither one confirms cash coming in or a customer redemption. Days at either end of a period can be partial, and the history refreshes no more than once every six hours.

The panel shows no USDEB price, holder count or net buying. The dashboard's notes say Binance market data was region-restricted in the dashboard's own testing. None of the panel's numbers feeds token NAV, mNAV or the share count, which the [methodology page](https://ethenadash.com/methodology/) defines. The panel shows the current supply, and the figures in this article stop at the cutoff. A [further burn](https://bscscan.com/tx/0xc82b2fa143e413e59f301949841338528fe22952fa90e3d2c739fa46b5a575f3) occurred later on October 8, after this snapshot. Use the [live supply panel](/stablecoinx/#tokenized-panel) for the latest reading.

## What this review could not check

Binance's proof-of-collateral page had no USDEB entry at 22:26 or at 23:26 UTC on October 8, so this review could not compare the shares held for the tokens with on-chain supply. Binance's [list of approved bStocks prospectuses](https://www.binance.com/en/about-legal-disclosures/bstocks-digital-securities-documentation-prospectuses) had no USDEB entry either, and its newest approval was dated September 22, so this review could not read the ADGM prospectus for USDEB. No document reviewed says whether holders can vote or what they receive if a party in the chain fails. When last checked, at 23:26 UTC on October 8, StablecoinX's newest SEC filings were five Forms 4, reports of insiders' holdings, filed on October 2, before Binance listed USDEB.

## Reproduce the numbers

The supply history is the dashboard's verified file at commit e7fb070, the saved version of the dashboard's code and data from 22:27 UTC on October 8, with this review's independent checks recorded beside it. The main script rebuilds every figure from those files, stops if any check fails, and writes the tables. [Download the mint and burn list](/research-assets/usdeb-stablecoinx-bstock/usdeb_supply_events.csv), the [supply by period](/research-assets/usdeb-stablecoinx-bstock/usdeb_supply_by_period.csv), or the [calculation files and source inputs](/research-assets/usdeb-stablecoinx-bstock/calculation-files.zip).

```text
raw supply        = raw units minted − raw units burned
supply in USDEB   = raw supply × (multiplier ÷ 10^18) ÷ 10^18
share of Class A  = supply in USDEB ÷ 24,139,375
reference value   = supply in USDEB × USDE Nasdaq close on October 8
```

The Class A count adds 110,000 shares from five director restricted-stock awards, reported on Forms 4 on October 2, to the 24,029,375 shares the StablecoinX prospectus reported as of August 28, 2026. The [USDEW warrant guide](https://ethenadash.com/research/usdew-warrants/) explains the warrants, and the [lock-up waiver review](https://ethenadash.com/research/stablecoinx-lock-up-waiver-2026-10-05/) covers what the company may do with its ENA.

Analysis of public documents and on-chain data. Not investment advice.
