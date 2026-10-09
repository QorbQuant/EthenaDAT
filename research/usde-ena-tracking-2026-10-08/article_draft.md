# How closely has StablecoinX's stock tracked ENA?

Market review / USDE against ENA

By [Qorban Ferrell · @Degenerate\_DeFi](https://ethenadash.com/about/) · Published 9 October 2026 · Prices from June 26 through the October 8, 2026 close · Sources read October 6 to 9, 2026 UTC

USDE, the Class A stock of StablecoinX Inc. on Nasdaq, moved the same way as ENA, the Ethena token the company reports holding as its treasury, on 50 of the 72 trading days that followed its first session on June 26, 2026, through October 8. Each daily move runs from one close, at 4 pm New York time, to the next, with ENA priced at the same moments. The correlation of the moves, a measure from −1 to 1 of how closely two series move in step, was 0.64. Its square, 0.41, is the share of the variation in USDE's daily moves that a straight line on ENA's moves accounts for.

USDE moved further than ENA. Its daily moves had a standard deviation, a measure of their typical size, of 16.6%, against 7.8% for ENA. On a straight line fitted through the 72 days, USDE moved 1.37% for each 1% move in ENA. Three days carried much of that slope. Without USDE's three largest moves, on August 21, August 27 and July 2, the fitted slope was 0.91 and the correlation 0.50.

From June 26 to October 8 USDE rose 245.7%, from $3.70 to $12.79, while ENA's price at the close rose 156.7%, from $0.0796 to $0.2043. mNAV, USDE's price divided by the value of the ENA per share, went from 0.37× to 0.50×, after a low of 0.13× on July 24 and a high of 0.52× on September 25.

The figures depend on pricing ENA at the moment of each close. This site's [StablecoinX dashboard](https://ethenadash.com/stablecoinx/), in its dataset of October 9, pairs each close with ENA's price at midnight UTC, 8 pm in New York the evening before. Measured with those prices, the correlation was 0.18, and USDE moved the same way as ENA on 31 of 72 days.

## USDE moved the same way as ENA on 50 of 72 days

Each daily move is the percentage change from one session's close to the next. USDE's closes come from S&P Global Market Intelligence through StockAnalysis. ENA's price at the close is the closing price of the four hours to 20:00 UTC on the Kraken exchange's ENA/USD market, from Kraken's public market data API. Every session in the window fell in US daylight saving time, when 20:00 UTC is 4 pm in New York. A move across a weekend or a market holiday spans the whole break, and ENA traded through it.

| 72 daily moves, June 26 close to October 8 close | Value |
| --- | ---: |
| USDE moved the same way as ENA | 50 |
| USDE moved the opposite way | 20 |
| Either price unchanged | 2 |
| Correlation | 0.64 |
| Share of USDE's variation accounted for by ENA's moves | 41% |
| Fitted slope, USDE's move for a 1% move in ENA | 1.37% |
| Standard deviation of USDE's daily moves | 16.6% |
| Standard deviation of ENA's daily moves | 7.8% |

![Two panels. Left, a scatter of USDE's 72 daily moves against ENA's, from the June 26 close to the October 8 close, with a fitted line of slope 1.37 and a dashed line of equal moves, and August 21 labeled at the top, when USDE rose 85% and ENA 27%. Right, mNAV at the 4 pm close, from 0.37× on June 26 to a low of 0.13× on July 24 and a high of 0.52× on September 25, ending at 0.50× on October 8.](/research-assets/usde-ena-tracking-2026-10-08/chart_usde_ena.svg)

*ENA's price at the close from the Kraken exchange's ENA/USD market. USDE's closes from S&P Global Market Intelligence through StockAnalysis. mNAV uses the ENA and Class A share counts in this site's dashboard data. The left panel's two axes use different scales.*

CoinGecko's ENA prices, each stamped within two minutes of 20:00 UTC and read through DefiLlama's public price API, served as a second source. Kraken's price at the close was within 1% of CoinGecko's on every session and 0.09% from it on the median session.

## The link was closest from September

| Daily moves, close to close | Moves | Same direction | Correlation | Fitted slope |
| --- | ---: | ---: | ---: | ---: |
| June 26 to July 31 | 24 | 16 | 0.47 | 1.20 |
| July 31 to August 31 | 21 | 10 | 0.62 | 1.45 |
| August 31 to October 8 | 27 | 24 | 0.78 | 1.17 |
| June 26 to October 8 | 72 | 50 | 0.64 | 1.37 |

In August USDE moved the same way as ENA on only 10 of 21 days, but the month's correlation was 0.62, because USDE's two largest moves of the month went the same way as ENA's. Without August 21 and August 27 the month's correlation was 0.17. From the August 31 close to October 8 USDE moved the same way as ENA on 24 of 27 days. Each period holds only 21 to 27 moves, and by the usual test for comparing correlations none of the gaps between the periods is large enough to rule out chance at the 5% level.

## A few large days carried the fitted slope

USDE's three largest moves came on August 21, when it rose 85% and ENA 27%, on August 27, when it rose 35% and ENA 21%, and on July 2, when it rose 34% and ENA 7%. A rank correlation, which compares only the order of the moves and so limits the weight of large days, was 0.49.

| Measure | Correlation | Fitted slope | Same direction |
| --- | ---: | ---: | ---: |
| Daily, ENA from Kraken | 0.64 | 1.37 | 50 of 72 |
| Daily, ENA from CoinGecko | 0.64 | 1.38 | 50 of 72 |
| Daily, without the three largest USDE moves | 0.50 | 0.91 | 47 of 69 |

## Midnight prices hide most of the link

The dashboard records one ENA price for each date, from CoinGecko according to its methodology page. On every session that price was within 0.5% of Kraken's price at midnight UTC, 8 pm in New York the evening before the close, and on the median session it was 3.2% away from ENA's price at the close.

For sessions on consecutive days, USDE's move runs from 4 pm on the first day to 4 pm on the second, and the dashboard's ENA move from 8 pm the evening before the first day to 8 pm on the first day. The two share four hours. Measured with the dashboard's prices, USDE moved the same way as ENA on 31 of 72 days, the correlation was 0.18 and the fitted slope 0.32. The [September review](https://ethenadash.com/research/usde-september-2026/) showed how the same gap changes the split of a month's gain between ENA and mNAV.

## Most of ENA's movement came outside USDE's trading hours

ENA trades around the clock, while USDE's regular trading hours run from 9:30 am to 4 pm New York time. This review split each daily move at USDE's opening price, with ENA from CoinGecko at 9:30 am and 4 pm, 13:30 and 20:00 UTC.

| 72 daily moves, split at the open | Close to open | Open to close |
| --- | ---: | ---: |
| Correlation | 0.55 | 0.40 |
| Rank correlation | 0.63 | 0.45 |
| Fitted slope | 0.96 | 1.30 |
| USDE moved the same way as ENA | 44 | 44 |
| Standard deviation of USDE's moves | 12.6% | 11.7% |
| Standard deviation of ENA's moves | 7.2% | 3.6% |

ENA's overnight moves, from the close to the next open, had twice the standard deviation of its moves during trading hours. On the fitted line USDE's opening price moved almost one for one with ENA's overnight move. During trading hours USDE moved about as much as overnight, and ENA's moves accounted for 16% of the variation in USDE's. One day drives the gap between the two correlations. Without August 21 both were 0.51, and the rank correlations were 0.61 overnight and 0.50 during trading hours.

On August 21 USDE opened 26.0% above the prior close after ENA rose 31.3% overnight, then rose another 47.0% during trading hours while ENA fell 3.3%. ENA's largest overnight move came over the weekend of September 19 and 20, a rise of 33.0% from Friday's close to Monday's open, and USDE opened 28.1% above its Friday close.

## mNAV moved more than ENA

At the close mNAV fell from 0.37× on June 26 to 0.13× on July 24 and stood below 0.25× on 29 of the 31 sessions from July 1 to August 13. It then rose to 0.52× on September 25 and was 0.50× on October 8. Its daily moves had a standard deviation of 12.2%, larger than ENA's 7.8%, so on a typical day mNAV changed more than ENA's price did. The dashboard's own mNAV, with its midnight ENA prices, was 0.45× on October 8 and peaked at 0.61× on September 25.

These figures use the dashboard's counts, 3,029,000,000 ENA on every date, the company's figure from its June 25 release, and a Class A count that rises from 24,029,375 to 24,139,375 on September 30. The September review explains both counts and the 10-Q's slightly larger ENA figure, which would lower each mNAV here by less than 0.001. This review did not check the ENA count against a token balance. mNAV here counts only the reported ENA. It leaves out cash, other assets and liabilities, and its Class A count adds no warrant shares, as the [mNAV guide](https://ethenadash.com/research/stablecoinx-mnav/) explains.

## What these figures leave out

Correlation measures how closely the moves lined up. It does not show what moved either price, and both may have responded to the same news.

The window holds 72 daily moves, and a few large days weigh heavily on the figures for the whole window. By the standard approximation for a correlation, 72 moves leave a 95% confidence interval, the range of underlying correlations these moves are consistent with, of about 0.48 to 0.76 around the 0.64, and of about −0.05 to 0.40 around the 0.18 from the dashboard's prices. ENA's price at the close comes from one exchange, checked against CoinGecko, and CoinGecko's prices at the open have no second source here. The overnight figures use S&P Global's opening price and leave out USDE's trading before 9:30 am and after 4 pm.

## Reproduce the numbers

This review read Kraken's 4-hour ENA/USD candles from Kraken's public market data API and CoinGecko's ENA prices from DefiLlama's public price API in a browser on October 9, 2026 UTC, with the SHA-256 of each response. USDE's daily prices are S&P Global's, read from StockAnalysis on October 9, and the dashboard's series comes from its dataset at commit 152e758. The main script checks every input against its recorded hash, that Kraken has both 4-hour candles for every day, that Kraken's price at the close is within 1% of CoinGecko's on every session, and that mNAV recomputed from the dashboard's inputs matches its own figures. If any check fails, the script stops before writing its tables. Download the [daily moves](/research-assets/usde-ena-tracking-2026-10-08/daily_moves.csv), the [summary of measures](/research-assets/usde-ena-tracking-2026-10-08/summary.csv), or the [calculation files and source inputs](/research-assets/usde-ena-tracking-2026-10-08/calculation-files.zip).

```text
daily move    = price at a close ÷ price at the previous close − 1
correlation   = Σ(x − x̄)(y − ȳ) ÷ √(Σ(x − x̄)² × Σ(y − ȳ)²)
fitted slope  = Σ(x − x̄)(y − ȳ) ÷ Σ(x − x̄)²
                x is ENA's daily move, y is USDE's, x̄ and ȳ their averages
mNAV          = USDE close ÷ (ENA at the close × 3,029,000,000 ÷ Class A shares)
              = 12.79 ÷ (0.2043 × 3,029,000,000 ÷ 24,139,375) = 0.50× on October 8
```

The [StablecoinX dashboard](https://ethenadash.com/stablecoinx/) tracks USDE's share price against the ENA treasury the company reports, and its [methodology page](https://ethenadash.com/methodology/) defines its figures.

Analysis of public market data. Not investment advice.

Related research: [Who holds USDE and what can trade?](/research/stablecoinx-float-2026-10-08/)
