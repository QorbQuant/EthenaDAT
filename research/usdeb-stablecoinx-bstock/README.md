# USDEB explained, October 2026

Calculation files for the EthenaDash article published on 8 October 2026. Read the article at https://ethenadash.com/research/usdeb-stablecoinx-bstock/

The article explains what USDEB is, how it differs from StablecoinX's Nasdaq stock USDE, its warrants USDEW and Ethena's synthetic dollar USDe, and how much USDEB existed on BNB Smart Chain through 22:28 UTC on October 8, 2026. The structure, rights and trading rules come from Binance's listing announcement and Admission to Trading Notice of October 7, 2026, its bStocks guide and its bStocks (Conversion) Product Terms. The supply figures come from the token contract, through the dashboard's verified flow file and three independent checks.

No figure here is a USDEB market price. The reference value multiplies supply by the October 8 USDE close and stands for the underlying shares only.

## Reproduce

From this directory, with Python 3 and the standard library only.

    python3 usdeb_review.py
    python3 check_article_numbers.py
    python3 make_chart_svg.py

The first script reads the inputs, runs its checks, stops if one fails and rewrites the tables in `out/`. It confirms that mints less burns equal the recorded supply, that the dashboard collector's later checkpoint and the chain's totalSupply at block 126,523,880 show the same supply, that every event matched a chain receipt and BscScan's list, and that the dashboard's dataset records the same close and Class A count. The second script recomputes every computed figure in the article and its metadata with separately written code and exits with an error if a phrase no longer appears, so rerun it after any edit to the text. The third draws the chart from `out/chart_usdeb_supply.csv`. None of them uses the network.

## Files in the download

| File | What it is |
| --- | --- |
| `article_draft.md` | The article in the format `scripts/build_research.py` reads. Headline, kicker, byline, then the body |
| `metadata.json` | Page metadata in the same shape as the published reviews. The dates record publication and modification |
| `usdeb_review.py` | The main script |
| `check_article_numbers.py` | Recomputes each computed figure and confirms the exact phrase appears in `article_draft.md` or `metadata.json` |
| `make_chart_svg.py` | Draws `out/chart_usdeb_supply.svg` in the site's palette |
| `inputs/usdeb_flows_e7fb070.json` | `output/usdeb-flows.json` of the dashboard repository at commit e7fb070, generated 22:27:24 UTC on October 8, 2026. Every USDEB mint and burn from deployment to block 126,498,018, observed 19:14:26 UTC |
| `inputs/usdeb_flow_pending_e7fb070.json` | The dashboard collector's next chain checkpoint at the same commit, block 126,523,450, 22:25:12 UTC |
| `inputs/shares_out_e7fb070.csv` | The dashboard's Class A share count at the same commit |
| `inputs/data_e7fb070.json` | The dashboard's dataset `docs/data.json` at the same commit, generated 22:25:17 UTC, for the close and the Class A count the panel used |
| `inputs/manifest.csv` | Repository, path, commit, size and SHA-256 of the four files above |
| `inputs/chain_checks.csv` | The independent checks made for this review, with method, time, block and result |
| `inputs/bscscan_holders_top.csv` | BscScan's four largest holders by tag, label, quantity and share, without addresses |
| `inputs/usde_close.csv` | The October 8, 2026 USDE close used for the reference value, with its two sources |
| `inputs/sources.csv` | Every document read, with its address, date, the time it was read and how |
| `out/run_log.txt` | The main script's output |
| `out/usdeb_supply_events.csv` | Every mint and burn with its time, block, log index, amount, running supply and transaction hash |
| `out/usdeb_supply_by_period.csv` | Mints, burns and supply before trading opened, on October 7 after it and on October 8 to the cutoff |
| `out/chart_usdeb_supply.csv` | The chart data, the running supply after each event and at the cutoff |
| `out/results.json` | The main results at full precision |
| `out/chart_usdeb_supply.svg` | The chart as a static SVG |

## Review material in this folder only

`evidence_table.md`, `calculation_appendix.md`, `review_notes.md` and `source_log.md` hold the claim-by-claim sources, the working, the decisions for review and the timed source reads. `layout.json` is the site build's page layout. `out/chart_preview.png` is the chart rendered on the site's background for the page preview. None of these goes into the download.

## Names

USDEB is the Binance bStock linked to StablecoinX Class A stock, contract `0xDfD3Ba51D4591f243481a6f26059d1a5Ee95252F` on BNB Smart Chain, chain 56. USDE is the Class A stock on Nasdaq and USDEW the public warrant. USDe is Ethena's synthetic dollar, at `0x5d3a1Ff2b6BAb83b63cd9AD0787074081a52ef34` on BNB Smart Chain.

A mint is a Transfer event from the zero address and a burn a Transfer event to it, counted once per log. Supply is mints less burns in raw units, times the multiplier divided by 10^18, divided by 10^18. The multiplier, which Binance uses for dividends and splits, was 1.0 throughout, so raw and adjusted supply are equal.

## How the sources were read

These checks were made in a browser rather than from the review workspace's shell. Binance's announcement, admission notice, guide, proof-of-collateral page, prospectus list and Conversion Terms, BscScan's token pages, Ethena's documentation and the SEC filings were read in a browser tab between 22:20 and 23:58 UTC on October 8, 2026. The browser made read-only requests, downloaded nothing to disk and used no login. The Conversion Terms and the admission notice are PDFs whose text was extracted page by page in the browser for exact searches. The Conversion Terms file is 215,034 bytes and the notice 130,097 bytes, and each file's SHA-256 equals its file name on Binance's server.

The chain checks used a public BNB Smart Chain node, `bsc-dataseed.bnbchain.org`, called from the same browser. Each of the 41 events in the flow file was matched to its transaction receipt, and totalSupply, the multiplier and the scaled supply were read at block 126,523,880. Public nodes would not return event logs over the block range, so completeness rests on the totalSupply reconciliation and on BscScan's independent list of transfers from and to the zero address.

## Limits

Binance's proof-of-collateral page did not list USDEB when read, so the custodied share count is unverified. Binance's list of approved bStocks prospectuses had no USDEB entry, so the USDEB prospectus was not read. BscScan's wallet tags are its own. Addresses are not recorded in this folder except the two token contracts and transaction hashes.

The Class A count of 24,139,375 is the dashboard's. It adds 110,000 shares from five director restricted-stock awards, reported on Forms 4 on October 2, 2026, to the 24,029,375 the September 14, 2026 prospectus reported as of August 28, 2026. It is not a fully diluted count.
