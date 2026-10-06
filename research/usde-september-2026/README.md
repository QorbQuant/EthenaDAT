# StablecoinX September 2026 review

Published at https://ethenadash.com/research/usde-september-2026/ on October 5, 2026.

The article uses the dashboard snapshot at commit 759f283adff372f05678de909efe099db6791ce6, not the changing live feed. ENA is compared at 00:00 UTC on each stock-session date and 20:00 UTC (4 pm New York during September). The September 30 share count is derived, not a reported total. All inputs are public market data or filing-derived observations.

## Reproduce

From this directory, with Python 3 (standard library only):

    python3 usde_sept2026_review.py
    python3 check_article_numbers.py
    python3 make_chart_svg.py

The first script recreates the CSVs and arithmetic results in out/. The second checks 73 numerical phrases in the edited article against independently expressed formulas. Filing constants are arithmetic checks, not automated verification of the filings. The third draws the vector chart directly from the daily CSV.

## Publication review

The pinned JSON matches the repository snapshot byte for byte. Coinbase candle opens were rechecked on all five sampled dates; 38 supplied 20:00 UTC CoinGecko observations matched the live DefiLlama historical API. SEC references were reviewed, including the warrant agreement and amendment, the lock-up waiver, the prospectus, and all five director Forms 4. Editorial changes clarify absolute session changes, restrict the token-count adjustment to ENA and token NAV per share, qualify the redemption search to filings reviewed, and note that the Foundation can clear a sale before the five-business-day review period expires. This article does not change the dashboard price pipeline.

For the website build, install research/requirements.txt and run scripts/build_research.py from the repository root. The generated HTML and public download files are committed; the Worker needs no Markdown runtime.
