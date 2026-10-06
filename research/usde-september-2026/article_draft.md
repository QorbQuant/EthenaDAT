# What moved StablecoinX (USDE) in September 2026?

Valuation review / September 2026

By [Qorban Ferrell · @Degenerate\_DeFi](https://ethenadash.com/about/) · Published 5 October 2026 · Prices through the September 30, 2026 close · Filings reviewed through October 5, 2026

StablecoinX stock (Nasdaq USDE) closed September at $16.08, up 81.3% from $8.87 at the end of August. ENA, the Ethena governance token the company holds as its treasury, rose 76.4% over the same span. With ENA priced at the stock's 4 pm New York close, the token's price accounts for $6.87 of the $7.21 gain. mNAV, the share price divided by token value per share, moved from 0.47× to 0.49× and accounts for $0.40. A 0.46% larger share count subtracts $0.06.

That split depends on where the window opens. USDE rose 31% on August 31 itself while ENA fell, and a window that opens one session earlier assigns 57% of its larger gain to ENA and 43% to mNAV. The dashboard snapshot reviewed here prices historical ENA 20 hours before each stock close. On that series ENA accounts for $6.24 and mNAV for $1.02.

## Start and end observations

Both stock-price endpoints are closing prices. August 31 was the last session of August and September 30 the last of September.

| Observation | Aug 31, 2026 | Sep 30, 2026 | Change |
| --- | --- | --- | --- |
| USDE close | $8.87 | $16.08 | +81.3% |
| ENA price at 4 pm New York, the stock close | $0.14916 | $0.26311 | +76.4% |
| ENA price at 8 pm New York the evening before, the dashboard series | $0.14811 | $0.24829 | +67.6% |
| ENA held, carried forward from the June 25 closing release | 3.029 billion | 3.029 billion | 0% |
| Class A shares in the dataset | 24,029,375 | 24,139,375 | +0.46% |
| ENA tokens per Class A share | 126.05 | 125.48 | −0.46% |
| Token NAV per share, at the close | $18.802 | $33.015 | +75.6% |
| Token NAV per share, dashboard series | $18.670 | $31.155 | +66.9% |
| mNAV, at the close | 0.472× | 0.487× | +0.015× |
| mNAV, dashboard series | 0.475× | 0.516× | +0.041× |

Token NAV is ENA held times the ENA price. It leaves out cash, other assets and every liability. mNAV is the share price divided by token NAV per share. The share count is Class A shares outstanding, with no warrants or stock units added. The company also reported 3,157,754 Class B shares as of August 12. They carry votes and no claim on dividends or assets, and the dataset leaves them out. The [mNAV guide](https://ethenadash.com/research/stablecoinx-mnav/) explains the limits of the measure.

## Priced at the stock close, ENA accounts for 95% of the gain between month ends

Share price equals ENA price times ENA per share times mNAV. The attribution switches each factor from its August 31 value to its September 30 value, one at a time, in all six possible orders, and averages what each factor adds. The What moved? view on the [StablecoinX NAV tracker](https://ethenadash.com/stablecoinx/) runs the same calculation on the dashboard series over a rolling window.

| Factor | At the close, $ per share | At the close, share of move | Dashboard series, $ per share | Dashboard series, share of move |
| --- | --- | --- | --- | --- |
| ENA price | +6.870 | 95.3% | +6.244 | 86.6% |
| ENA per share | −0.057 | −0.8% | −0.057 | −0.8% |
| mNAV | +0.397 | 5.5% | +1.023 | 14.2% |
| USDE change | +7.210 | 100% | +7.210 | 100% |

The split is arithmetic on two endpoints and says nothing about why anyone traded.

The start date changes the split more than the timestamp does. USDE rose 31% on August 31 itself, from $6.76 to $8.87, while ENA fell 7%. That one session lifted mNAV from 0.34× to 0.47× before the month-end window opens.

| Window opens at the close of | ENA price | ENA per share | mNAV |
| --- | --- | --- | --- |
| Aug 28 | 57.4% | −0.5% | 43.1% |
| Aug 31, the month end | 95.3% | −0.8% | 5.5% |
| Sep 1 | 78.5% | −0.7% | 22.2% |

Each row ends at the September 30 close with ENA priced at the stock close. Pricing ENA at the end of the UTC day, which is consistent with the closing price the company used for its June 30 valuation, gives ENA 96.0% and mNAV 4.8% for the month-end window.

## The dashboard series prices ENA 20 hours before the stock close

The October 5 dataset snapshot used in this review takes ENA from CoinGecko's daily series. Each daily price carries the start of its UTC day. During daylight time that is 8 pm in New York on the evening before. USDE closes at 4 pm New York time, 20 hours later, and ENA trades through all of those hours. The newest row is the exception. It holds the price at the time of the update until the next day's refresh replaces it.

On September 30 ENA stood at $0.2483 at the earlier time and $0.2631 at the stock close, a gap of 6.0%. The dashboard series puts mNAV for that day at 0.52×. Priced at the close it is 0.49×.

The widest gap of the month fell on September 25. ENA rose 16.6% between the two times and USDE gained 21.3% on the day. The dashboard series shows 0.61× for that date, its highest reading since the June 26 listing. Priced at the close, mNAV was 0.52×.

![USDE mNAV by session on two ENA timestamps, August 31 to September 30, 2026](/research-assets/usde-september-2026/chart_mnav_two_timestamps.svg)

*EthenaDash dataset at commit 759f283 and CoinGecko ENA at 8 pm UTC · 22 sessions, Aug 31 to Sep 30, 2026*

Two other records point the same way. Two updates on the evening of September 25 put mNAV at [0.53×](https://github.com/QorbQuant/EthenaDAT/commit/0efe051) and [0.51×](https://github.com/QorbQuant/EthenaDAT/commit/04cf641), and the [next day's update](https://github.com/QorbQuant/EthenaDAT/commit/8d8a19a) replaced the ENA price. StablecoinX [valued its treasury](https://www.sec.gov/Archives/edgar/data/2080215/000121390026089504/ea030188301ex99-1.htm) for June 30 at a closing ENA price of $0.07204. The dataset shows $0.0786 for June 30 and $0.0720 for July 1, so its June 30 row reads $9.91 of token NAV per share. The company reported $9.09, and the ENA price explains that gap to within a cent.

The earlier timestamp also adds noise. The median absolute session-to-session change in mNAV was 11.3% of its level on the dashboard series and 3.1% at the close. The means were 12.5% and 6.2%.

## mNAV fell to 0.34×, then rose to 0.49×

USDE's low close of the month was $6.12 on September 15. Priced at the close, mNAV reached its low one session later at 0.336×. The table splits the month at that September 16 close, with ENA priced at the stock close.

| Measure | Aug 31 to Sep 16 | Sep 16 to Sep 30 |
| --- | --- | --- |
| USDE close | $8.87 to $6.20, −30.1% | $6.20 to $16.08, +159.4% |
| ENA price | $0.14916 to $0.14638, −1.9% | $0.14638 to $0.26311, +79.8% |
| mNAV | 0.472× to 0.336×, −28.8% | 0.336× to 0.487×, +44.9% |
| ENA price contribution | −$0.142 | +$6.041 |
| mNAV contribution | −$2.528 | +$3.888 |
| ENA per share contribution | $0.000 | −$0.049 |

mNAV accounts for 95% of the fall to September 16. It then rose from 0.336× to 0.482× in two sessions, September 17 and 18. From September 18 to month end it moved only to 0.487× while the stock rose 58% and ENA rose 57%.

A split at the low builds in a fall and a rebound. The two legs also sum to a different split than the month table. A given percentage change in mNAV is worth more dollars when token NAV per share is higher, so dollar contributions depend on the path. Percentage changes chain cleanly. mNAV fell 28.8% and then rose 44.9%, a net gain of 3.2%.

In dollars the gap between token NAV and market capitalization grew from $239 million to $409 million over the month, while mNAV rose by 0.015×.

## What the company filed in the window

The table lists what the company filed from the August 31 close to the cutoff, along with the insider reports that cover September 30. This review does not test whether any filing moved the price.

| Date | Filing | What it disclosed |
| --- | --- | --- |
| Aug 31 to Sep 14 | [S-1 registration](https://www.sec.gov/Archives/edgar/data/2080215/000121390026099731/ea0305435-424b3_stable.htm), filed August 31, amended September 9 and effective September 14 | Covers 19,124,586 shares issuable under warrants and the resale of 12,668,943 shares. The two figures share 7,624,586 sponsor warrant shares |
| Sep 3 | [S-8](https://www.sec.gov/Archives/edgar/data/2080215/000121390026097183/ea0304267-s8_stablecoinx.htm), a registration for a stock plan | Registered 1,802,203 Class A shares for the 2026 Stock Incentive Plan |
| Sep 8 | [8-K](https://www.sec.gov/Archives/edgar/data/2080215/000121390026097877/ea0304764-8k_stablecoinx.htm), a current report | Christopher Jensen became chief executive and Edward Chen stayed on as chairman |
| Sep 17 | [8-K](https://www.sec.gov/Archives/edgar/data/2080215/000121390026100751/ea0305686-8k_stablecoinx.htm), a current report | Disclosed that Ethena OpCo and the Ethena Foundation had waived the lock-ups on the company's ENA from October 5 |
| Oct 2 | Forms 4 from [Chen](https://www.sec.gov/Archives/edgar/data/2080215/000122520826008116/xslF345X06/doc4.xml), [Griffiths](https://www.sec.gov/Archives/edgar/data/2080215/000122520826008117/xslF345X06/doc4.xml), [Piano](https://www.sec.gov/Archives/edgar/data/2080215/000122520826008118/xslF345X06/doc4.xml), [Shah](https://www.sec.gov/Archives/edgar/data/2080215/000122520826008119/xslF345X06/doc4.xml) and [Tarala](https://www.sec.gov/Archives/edgar/data/2080215/000122520826008120/xslF345X06/doc4.xml), insider transaction reports | Each director reported 22,000 restricted shares awarded on September 30 |

The list leaves out a Form 3 in which the new chief executive reported no holdings and a prospectus supplement filed alongside the September 17 report.

## ENA per share fell 0.46% on a derived share count

The dataset carried 3.029 billion ENA through the month, the figure in the [June 25 closing release](https://www.sec.gov/Archives/edgar/data/2080215/000121390026072231/ea029602401ex99-1.htm). The [second-quarter 10-Q](https://www.sec.gov/Archives/edgar/data/2080215/000121390026090250/ea0301482-10q_stable.htm) lists three amounts received at that closing that sum to 3,031,404,421 tokens, 0.08% more. Using that count would raise ENA per share and token NAV per share by 0.08%, lower every mNAV by approximately the same proportion and leave the attribution unchanged. The most recent dated holdings figure in the filings reviewed here is for June 30, and nothing on the dashboard verifies a current wallet balance.

The one disclosed change in the share count is 110,000 restricted shares awarded to five directors on September 30. They vest quarterly from October 1. The last count the company itself reported is 24,029,375 Class A shares as of August 28, so the September 30 figure of 24,139,375 is derived and no filing states it. The dataset carries the count forward from filings, so stock units that settle in shares and awards under the incentive plan appear only after a filing reports them. Each additional million shares lowers ENA per share by about 4%.

## Warrants are the larger open item in the share count

The September 14 prospectus covers 19,124,586 shares under warrants, against 24,139,375 Class A shares in the dataset. Of those warrants, 14,767,679 carry an $11.50 exercise price and 4,356,907 carry $15.00. All were out of the money at the August 31 close. USDE first closed above $11.50 on September 21 and above $15.00 on September 25.

A cash exercise adds a share and adds the exercise price to the company's cash, so it changes both the share count and the assets that token NAV leaves out. Full cash exercise would add 79% to the share count and raise about $235 million. Both figures are ceilings. The 7.6 million sponsor warrants may be exercised without cash, which adds fewer shares and no cash. The dataset adds no warrant shares until a filing reports an exercise.

The [warrant agreement](https://www.sec.gov/Archives/edgar/data/1879814/000119312521348660/d225674dex41.htm), which the company [assumed and amended](https://www.sec.gov/Archives/edgar/data/2080215/000121390026093069/ea030312501ex4-2.htm) on June 25, 2026, lets it redeem the public warrants at $0.10 each, on at least 30 days' notice, once USDE has closed at or above $10.00 on 20 trading days within a 30-trading-day period. Holders may exercise before the redemption date, including on a cashless basis for up to 0.361 of a share per warrant. Nine qualifying closes had accrued by September 30. A second route allows redemption at $0.01 once the same test is met at $18.00, and USDE had no close at or above $18.00 in the window. The sponsor warrants cannot be redeemed while their original holders or permitted transferees keep them. Note 9 to the second-quarter 10-Q describes both tests as 10 trading days within 20. The descriptions differ; this review uses the agreement’s 20-of-30 test, which the June 25 amendment does not change. The tracker's [call-trigger watch](https://ethenadash.com/stablecoinx/#full-derivatives) follows the agreement, and the [warrant guide](https://ethenadash.com/research/usdew-warrants/) covers payoff, exercise and redemption.

## What changed after the cutoff

Ethena OpCo and the Ethena Foundation waived every lock-up on the company's ENA with effect from October 5, 2026. The [waiver letter](https://www.sec.gov/Archives/edgar/data/2080215/000121390026100751/ea030568601ex10-1.htm) is dated September 14. It is permanent and covers the 48-month schedule in the token purchase agreements. It changes no token count, no share count and no September figure on this page.

Part of the treasury was still under lock-up through September. The second-quarter 10-Q describes tokens that were locked at June 30 and due to unlock over up to 48 months. Token NAV priced locked and unlocked tokens alike throughout the month.

The Foundation's consent right stays. Clause 4 of the letter keeps the requirement for its prior written consent, which it may not unreasonably withhold, to any sale, transfer, loan, hedge or pledge of ENA. Any approval required from the investment committee, the Class B holders or the board also stays. The letter pre-approves sales that fund what it calls value-accretive activities. It names strategic investments and acquisitions, share repurchases under a Rule 10b5-1 plan that the Foundation has approved, working capital under the board-approved budget and new product development. The letter provides a five-business-day review period after receipt of the funding notice, although the Foundation may clear the sale earlier. In that window the Foundation may buy the tokens itself or ask to discuss the sale. The filed copy of the letter leaves the Foundation's purchase price and a 5% price tolerance in square brackets. Neither side may announce such a sale unless the law or an exchange rule requires it.

From October 5 the tracker's unlocked figure equals its total. Unlocked there means free of a time lock. A sale still needs the steps above, and the reported token count can lag a sale until the next filing.

The count of qualifying closes also moved after the cutoff. USDE closed above $10.00 again on October 1 and October 2, the tenth and eleventh such closes. Ten is the number in the 10-Q's description and twenty is the number in the agreement. No redemption announcement appears in the filings reviewed through October 5.

## What token NAV leaves out

At June 30 the second-quarter 10-Q showed $18.9 million of cash and $18.3 million of total liabilities. That total included a $4.7 million warrant liability, which the company carries at fair value. The public warrants closed June at $0.41 and September at $5.17. At the September price the same 11.5 million warrants come to about $59 million. That figure is arithmetic on the quoted price, and it leaves out the sponsor warrants issued in August.

The company carries its ENA at cost less impairment, $212.9 million at June 30. The 10-Q gives the reason, that a related party created the token. It does not write the carrying value back up when the price rises, so book value in the filings does not track token NAV.

## Reproduce the numbers

The observations come from the dashboard dataset as committed to the [public repository](https://github.com/QorbQuant/EthenaDAT/blob/759f283adff372f05678de909efe099db6791ce6/docs/data.json) on October 5, 2026. The dataset's share count changed on October 3 from 24,110,000 to the filed 24,029,375, so earlier commits show slightly different mNAV values.

The ENA price at the stock close is CoinGecko's 8 pm UTC price as served by DefiLlama's price API. 8 pm UTC is 4 pm in New York during daylight time. That series sits within 0.63% of Kraken's price at the same time on every session from August 28 to October 2 and within 0.14% of Coinbase on five dates checked. USDE closes match the S&P Global closes published by StockAnalysis for every session. [Download the daily figures on both timestamps](/research-assets/usde-september-2026/daily_mnav_two_timestamps.csv), the [attribution table](/research-assets/usde-september-2026/attribution_bridge.csv), or the [calculation files and source inputs](/research-assets/usde-september-2026/calculation-files.zip).

```text
share price   = ENA price × ENA per share × mNAV
ENA per share = ENA held ÷ Class A shares
mNAV          = share price ÷ (ENA price × ENA per share)
```

Each contribution is the factor's Shapley value. The [methodology page](https://ethenadash.com/methodology/) defines the terms.

Analysis of public filings and market data. Not investment advice.
