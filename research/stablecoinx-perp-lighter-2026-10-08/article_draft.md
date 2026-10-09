# Does Lighter's StablecoinX perp track USDE?

Market review / Lighter's StablecoinX perp

By [Qorban Ferrell · @Degenerate\_DeFi](https://ethenadash.com/about/) · Published 9 October 2026 · Lighter data from 2 pm New York time on August 26, 2026 to 8 pm on October 8 · Market settings and open interest at 9:30 am on October 9 · USDE prices through the October 8 close · Sources read October 9, 2026 UTC

The mark price of Lighter's perpetual futures contract on USDE, the Class A stock of StablecoinX Inc. on Nasdaq, tracked USDE at the close because Lighter's rules hold it there, and the contract's trades strayed further. The mark, the fair value Lighter uses to decide liquidations, ended within 1% of USDE's closing price on 30 of the 31 trading days from August 26, 2026, the contract's first day, to October 8. While the USDE feed of Pyth, a network of price feeds, is live, from 9:30 am to 4 pm New York time on weekdays, Lighter's index, its reading of USDE's price, comes from that feed, and two of the three prices that set the mark follow it. The contract's last trade before 4 pm, the price traders paid, was within 1% of the close on 14 of the 31 days.

A perpetual futures contract, or perp, has no expiry date. Lighter, a crypto exchange, lists this one under the symbol STABLECOINX, and each contract tracks one share. Lighter says its markets in stocks and other real-world assets trade around the clock.

No trade took place in 461 of the 826 hours outside 9 am to 4 pm New York time on trading days, against 38 of the 212 hours inside them, yet the hours outside carried 59.9% of the perp's dollar volume. The mark's median move was largest while USDE traded before and after the session and smallest from 8 pm to 4 am, when USDE did not trade. At 4 am the mark sat nearer the next opening price than the prior close did on 17 of the 30 stretches between sessions, against about 12 for a guide with no bearing on the open, too short a record to measure that edge with any precision. By 9 am, after five hours of pre-market trading in USDE, it was nearer on 23 of 30.

The largest move while USDE was not trading came over the weekend of September 19 and 20. The perp's mark rose 29.6%, from $10.14 at 8 pm on Friday to $13.14 at 4 am on Monday, and USDE opened that Monday at $13.05, 28.1% above Friday's close. That weekend carried 89.0% of the perp's weekend trading in the six weeks.

Holders of long positions paid funding, an hourly payment between the two sides of the contract, to holders of short positions in 939 of the 1,039 hourly payments. A long position held at a constant dollar size from the first payment to October 8 paid a net 7.0% of that size. It paid 7.5% in the two weeks from September 14 alone, when USDE's closing price more than doubled. The perp's figures come from Lighter's public market data. USDE's opening and closing prices come from S&P Global Market Intelligence through [StockAnalysis](https://stockanalysis.com/stocks/usde/history/), checked against Yahoo Finance, which also supplied USDE's pre-market and after-hours prices.

## The perp's mark ended within 1% of USDE's close on 30 of 31 days

Lighter keeps two prices for the perp. The index is its reading of USDE's price. The mark is the perp's fair value, the middle of three prices under Lighter's [fair-price rules](https://docs.lighter.xyz/trading/fair-price-marking). One comes from Lighter's order book, one is the index plus a premium capped at 0.5%, and for real-world assets the third comes from the price feed while the feed is live, Lighter's [pricing documentation](https://docs.lighter.xyz/trading/real-world-assets-rwas/rwa-pricing-mechanism) says. The perp's feed is Pyth's USDE price, according to Lighter's [market specifications](https://docs.lighter.xyz/trading/real-world-assets-rwas/market-specifications), and [Pyth lists](https://hermes.pyth.network/v2/price_feeds?query=USDE&asset_type=equity) its hours as 9:30 am to 4 pm New York time on weekdays. While that feed is live, two of the three prices follow it, so the mark stays near USDE by design.

| At 4 pm New York time | Perp's mark | Perp's last trade |
| --- | ---: | ---: |
| Median gap to USDE's close | 0.42% | 1.40% |
| Largest gap | 1.60%, on August 26 | 6.40%, on September 17 |
| Days within 1% | 30 of 31 | 14 of 31 |
| Days within 2% | 31 of 31 | 19 of 31 |

The mark's largest gap came on the perp's first afternoon. The last trade strayed further. On 7 of the 31 days nobody traded the perp in the hour before the close, so its last trade came from earlier in the day, as it did for the largest gap, on September 17.

## Outside the session the perp's mark moved most during USDE's extended hours

USDE's extended hours, its pre-market and after-hours trading, ran from 4 am to the open and from the close to 8 pm New York time in Yahoo Finance's hourly data, which showed no trading from 8 pm to 4 am. Over the 30 stretches between a close and the next open, the perp's mark moved most in those extended hours.

| Window, New York time | Median move in the perp's mark | Stretches with a move over 2% |
| --- | ---: | ---: |
| 4 pm to 8 pm, USDE after-hours | 2.47% | 16 of 30 |
| 8 pm to 4 am, no USDE trading | 0.68% | 5 of 30 |
| 4 am to 9 am, USDE pre-market | 3.09% | 20 of 30 |

Over a weekend, or the Labor Day holiday, the middle window runs from 8 pm on Friday to 4 am on the next trading day. The 30 stretches were 24 weeknights, 5 weekends and the Labor Day weekend.

The medians hide larger swings inside the middle window. Over the weekend of September 19 and 20 the mark peaked at $14.33 on Sunday afternoon, 40.6% above Friday's close. On the evening of Sunday, September 27 it touched $22.57, 30.8% above Friday's close, as trades on the perp reached $25.00, and it stood at $17.80 at 4 am on Monday. On Sunday, October 4 it fell to $12.67, 10.5% below Friday's close. Lighter uses the mark to decide liquidations, so a position had to survive these swings as well as the moves between a window's ends.

When the feed goes stale, Lighter's pricing documentation says the index and the third of the mark's three prices come instead from Lighter's own order book, smoothed over about 30 minutes for the index and 2 minutes for that third price. Both are kept within a distance of the last feed price that the page ties to the market's leverage, and read with the perp's five-times maximum leverage its formula gives 20%. The page does not say when the feed counts as stale. Lighter's price-source data, read at 9:30 am on October 9 as Nasdaq opened, showed the index taken from Pyth and that distance set at 40%. In 266 of the 826 hours outside 9 am to 4 pm on trading days the mark did not move at all. Inside those hours it moved in all but one.

The perp's mark stayed near USDE's extended-hours prices without matching them. At 8 pm the mark sat a median 0.91% from USDE's last after-hours price and within 1% of it on 16 of 29 evenings. At 9 am it sat a median 1.38% from USDE's last pre-market price and within 1% of it on 12 of 30 mornings. Yahoo Finance's hourly data, the source of those prices, showed no trading after the closing print on October 7, so the evening comparison covers 29 stretches.

## By 9 am the perp's mark was nearer the open than the prior close on 23 of 30 mornings

The test for each of the 30 stretches was whether USDE's next opening price, at 9:30 am, landed nearer the perp's mark at 4 am or at 9 am than the prior close.

![Two scatter charts of the 30 stretches between a close and the next open, August 26 to October 8, 2026. With the perp's mark at 4 am New York time, USDE opened nearer the mark than the prior close 17 times. With the mark at 9 am, 23 times. The weekend of September 19 and 20 sits at the top right of both, where the mark sat about 29% above Friday's close and the open 28%.](/research-assets/stablecoinx-perp-lighter-2026-10-08/chart_off_hours.svg)

*Each dot is one stretch from a close to the next open. Each move runs from the prior close. Lighter hourly mark prices, and USDE prices from S&P Global Market Intelligence through StockAnalysis.*

| Guide to the next open | Open nearer it than the prior close | Average miss | Median miss |
| --- | ---: | ---: | ---: |
| Prior close | | 6.32% | 5.35% |
| Perp's mark at 4 am | 17 of 30 | 4.87% | 4.43% |
| Perp's mark at 9 am | 23 of 30 | 2.84% | 2.72% |
| USDE's last pre-market price before 9 am | 25 of 30 | 2.65% | 2.09% |

A miss is the distance from the guide to the next open, as a share of the prior close. A guide with no bearing on the open would still land nearer it than the prior close some of the time, though its own moves add to its miss. Pairing each opening move with the mark's 4 am move from each of the 30 stretches in turn, and averaging, gave about 12 nearer opens in 30. The mark's 17 beat that, and it pointed the same way as the opening move on 20 stretches, against about 15 for such a guide. Thirty stretches make a short record, though.

The mark's lower average miss at 4 am came mostly from the two largest opening moves, on September 18 and 21. Without them the average misses were 4.92% for the prior close and 4.65% for the mark at 4 am, the median misses were 4.98% and 4.43%, and the mark was nearer the open on 15 of 28 stretches. USDE's own last after-hours price, at 8 pm, made a stiffer test than the prior close. It was nearer the open than the prior close on 16 of 29 stretches. The mark at 4 am was nearer the open than that price on 14 of the 29 stretches and the 8 pm price on 15, though the mark had the smaller average and median misses, 4.91% and 4.45% against 5.74% and 4.97%.

By 9 am the perp's mark and USDE's last pre-market price gave similar average misses, 2.84% and 2.65%, though the pre-market price had the lower median miss, 2.09% against 2.72%. The mark was nearer the open than the pre-market price on 17 of 30 mornings.

## One weekend carried 89% of weekend trading

The weekends here run from 8 pm on Friday to 4 am on the next trading day, when USDE did not trade. The perp traded in 94 of their 360 hours. On the weekend of September 12 and 13 it traded once, 1.32 contracts worth $10.

| Weekend, 8 pm Friday to 4 am on the next trading day | Hours with a trade | Contracts traded | Dollar volume | Share of weekend volume |
| --- | ---: | ---: | ---: | ---: |
| August 29 and 30 | 10 of 56 | 3,292.23 | $22,238 | 0.7% |
| September 5 to 7, with Labor Day | 18 of 80 | 121.34 | $965 | under 0.1% |
| September 12 and 13 | 1 of 56 | 1.32 | $10 | under 0.1% |
| September 19 and 20 | 33 of 56 | 238,264.73 | $2,876,249 | 89.0% |
| September 26 and 27 | 17 of 56 | 8,181.68 | $148,540 | 4.6% |
| October 3 and 4 | 15 of 56 | 13,544.02 | $184,907 | 5.7% |

USDE closed at $10.19 on Friday, September 18. The perp's mark held at $10.24 from 9 pm that evening until 2 pm New York time on Saturday, while $2.12 million of contracts, 73.6% of that weekend's dollar volume, traded between 10 am and 2 pm at prices from $10.20 to $12.15. Between 2 pm and 3 pm the mark rose 24.3%, to $12.73. It touched $14.27 before 4 pm, stood at $13.71 at 4 pm and at $13.14 at 4 am on Monday. Trades reached $15.50 over the weekend. Longs paid the maximum funding rate of 0.5% an hour in four straight hourly payments, from noon to 3 pm on Saturday. On Monday USDE's pre-market trading opened at $11.87, and its opening price was $13.05.

Two prices recurred in the mark that weekend. The $10.24 it held from 9 pm on Friday to 2 pm on Saturday was 0.5% above Friday's close, the most Lighter's fair-price rules let the premium add to the index. In four separate hours on Saturday and Sunday its hourly high was exactly $14.27, 40.0% above Friday's close, the cap Lighter's price-source data showed on October 9. In the one hour it went higher, from 2 pm on Sunday, it reached $14.33, 0.4% above that level and inside the 0.5% the premium can add. Both prices fit an index that stayed at Friday's close until early Saturday afternoon, and Lighter's 40% cap around that close after it. This review could not see the index to confirm it.

## Longs paid 7.0% in funding over six weeks

Funding is the hourly payment between holders of long and short positions that pulls the perp's price toward the index. When the rate is positive, longs pay shorts. Lighter's [funding documentation](https://docs.lighter.xyz/trading/funding) sets a cap of 0.5% an hour and says Lighter computes each payment from the index. The perp's settings on October 9 gave a base rate of 0.0032% every eight hours, or 0.0004% an hour, the rate that applies while the perp trades close to the index.

From 2 pm New York time on August 26 to 8 pm on October 8, Lighter made 1,039 hourly payments. Longs paid in 939 of them and shorts in 98, and 2 were zero. The rate sat at the 0.0004% base in 800. The hourly rates added up to 7.01 percentage points, so a long position kept at a constant dollar size paid 7.0% of that size, about 1.1 percentage points a week. A long position of one contract paid $0.67, while USDE rose from $5.98 at the August 26 close to $12.79 at the October 8 close.

| Week starting Monday, UTC | Hourly payments | Net rate, percentage points | Payments by longs | Payments by shorts |
| --- | ---: | ---: | ---: | ---: |
| August 24 | 103 | 0.04 | 103 | 0 |
| August 31 | 168 | 1.25 | 168 | 0 |
| September 7 | 168 | 0.51 | 165 | 3 |
| September 14 | 168 | 3.81 | 149 | 18 |
| September 21 | 168 | 3.69 | 162 | 6 |
| September 28 | 168 | −0.22 | 132 | 36 |
| October 5 | 96 | −2.06 | 60 | 35 |

The two weeks from September 14 added 7.50 percentage points, more than the net for all six weeks, as USDE's closing price rose from $7.44 on September 14 to $17.25 on September 25. Five payments reached the 0.5% cap, one at 9 am on September 1 and four on Saturday, September 19. From September 28 the net flow reversed, and shorts paid longs.

## Open interest equaled 0.29% of the freely tradable shares

At 9:30 am New York time on October 9, open interest, the contracts still outstanding, stood at 56,128.89, worth $742,310 at the mark. That equals 0.29% of the roughly 19.06 million Class A shares that StablecoinX's [resale prospectus](https://www.sec.gov/Archives/edgar/data/2080215/000121390026099731/ea0305435-424b3_stable.htm) counted as freely tradable on August 28, and 0.23% of the 24,139,375 Class A shares this site's dashboard counted on October 8. From its first trade to October 8 the perp traded 1,308,611.91 contracts, worth $14.60 million, about $27,600 an hour from 9 am to 4 pm on trading days and $10,600 an hour outside those hours. USDE traded 167,555,071 shares in its 31 sessions, about 128 shares for every contract, counting all of August 26 for USDE and only the hours from 2 pm for the perp.

On October 9 Lighter charged no trading fees on the perp and required initial margin of 20% of a position's value, which allows leverage of up to five times. Its market specifications listed the perp's open interest cap as 10 million without naming the unit, and said the settings could change.

## What this review could not check

This review could not see which price source set Lighter's index in each hour. Lighter's price-source data reports only the current source, and this review kept one reading, from 9:30 am New York time on October 9.

It could not identify who traded the perp, and it did not look for news behind the moves of September 19.

Lighter's daily volume figures added up to $16.14 million, $1.54 million more than the trades in its hourly candles. They ran higher on 23 of the 44 days and by more than $1,000 on 12, most on September 19, by $1.04 million. This review used the candles and could not tell what the extra volume was.

Yahoo Finance's hourly data gave pre-market and after-hours prices without volume, so a bar's last price can come from early in its hour. Thirty stretches and six weekends make a short record, and Lighter can change the perp's margin, funding and price settings.

## Reproduce the numbers

The perp's figures come from Lighter's public market data, read in a browser on October 9, 2026 UTC, with a record of each request and the SHA-256 of each response. The main script checks the hourly series against Lighter's daily candles and the two daily price sources for USDE against each other. It also checks that the median price implied by the funding payments sits within 2% of the mark. Single payments stray further, because Lighter computes each from the index, which the downloaded data does not include. If any check fails, the script stops before writing its tables. Download the [comparison at the close](/research-assets/stablecoinx-perp-lighter-2026-10-08/close_comparison.csv), the [stretches between sessions](/research-assets/stablecoinx-perp-lighter-2026-10-08/off_hours.csv), the [weekly funding](/research-assets/stablecoinx-perp-lighter-2026-10-08/funding_by_week.csv), the [weekend trading](/research-assets/stablecoinx-perp-lighter-2026-10-08/weekend_activity.csv), or the [calculation files and source inputs](/research-assets/stablecoinx-perp-lighter-2026-10-08/calculation-files.zip).

```text
gap at the close     = perp mark at 4 pm ÷ USDE close − 1
move at the open     = USDE next open ÷ prior close − 1
open nearer the mark = |open − perp mark| < |open − prior close|
no-bearing guide     = nearer opens over all 900 pairings of an opening move
                       with a 4 am mark move ÷ 30 = 12.3
funding paid, long   = Σ hourly rate × (+1 when longs paid, −1 when shorts paid)
                     = 7.01 percentage points over 1,039 hourly payments
open interest share  = 56,128.89 contracts ÷ 19,063,653 freely tradable shares = 0.29%
```

The [StablecoinX dashboard](https://ethenadash.com/stablecoinx/) shows the perp's latest mark against USDE's last recorded close, with its open interest, latest hourly funding and 24-hour volume, and its [methodology page](https://ethenadash.com/methodology/) defines the dashboard's figures. The [USDEB explainer](https://ethenadash.com/research/usdeb-stablecoinx-bstock/) covers Binance's tokenized StablecoinX share.

Analysis of public market data. Not investment advice.

Related research: [Compare USDE stock with ENA at matched closing times.](/research/usde-ena-tracking-2026-10-08/)
