# EthenaDAT

Daily chart dataset for **StablecoinX Inc. (Nasdaq: USDE)** — the Ethena DAT
(digital asset treasury) company — covering share price, market cap, and the
underlying ENA NAV. Output is designed to be dropped straight into a charting
tool (CSV or JSON).

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python fetch_data.py
```

Writes `output/ethena_dat.csv` and `output/ethena_dat.json` with one row per
Nasdaq trading day since listing (2026-06-26):

| column | meaning |
|---|---|
| `usde_close` | USDE daily close (Yahoo Finance) |
| `shares_outstanding` | fully diluted shares (from `inputs/shares_out.csv`) |
| `market_cap` | `usde_close × shares_outstanding` |
| `ena_price` | ENA/USD daily price (CoinGecko) |
| `ena_holdings` | ENA tokens held (from `inputs/ena_holdings.csv`) |
| `ena_nav` | `ena_price × ena_holdings` |
| `nav_per_share` | `ena_nav ÷ shares_outstanding` |
| `mnav` | `market_cap ÷ ena_nav` (premium/discount multiple) |
| `ena_unlocked` | tokens past their contractual unlock date (see below) |
| `nav_unlocked` | `ena_price × ena_unlocked` — "realizable" NAV |
| `nav_unlocked_per_share` | `nav_unlocked ÷ shares_outstanding` |
| `mnav_unlocked` | `market_cap ÷ nav_unlocked` |

## Updating the input tables

Holdings and share count only change on discrete events (ENA purchases,
issuance), so they live in hand-maintained event tables that get
forward-filled by date. When StablecoinX announces a change, append a row:

- `inputs/ena_holdings.csv` — `date,ena_holdings`
- `inputs/shares_out.csv` — `date,shares_outstanding`

Seed values come from the closing 8-K (June 25, 2026 press release):
~3,029M ENA valued at $275M ($0.0909 30-day VWAP). The Super 8-K (July 2,
2026) reports 27,187,129 total shares at closing (24,029,375 Class A +
3,157,754 unlisted Class B); the Class A-only count is used here, matching
the company's own NAV-per-share framing, and the Q2 10-Q cover confirms
24,029,375 as of Aug 12, 2026. (The seed was previously 24.11M, backed out of
the press release's "$11.42 per fully diluted share"; corrected to the filed
count on 2026-10-03, which moves historical per-share figures by ~0.3%.)

| date | shares | source |
|---|---|---|
| 2026-06-26 | 24,029,375 | Super 8-K / 10-Q cover |
| 2026-09-30 | 24,139,375 | + 5 × 22,000 director restricted-stock awards (Form 4s, Oct 2) |

Public warrants have been in the money since mid-September, so cash
exercises will add shares that only show up in the next 10-Q — check its
cover page and append a row.

When `inputs/ena_holdings.csv` changes, also update `ENA_HOLDINGS_SOURCE` in
`build_dashboard_data.py` so the site states which filing the figure comes
from. Since the lock-up waiver the company may sell ENA without announcing
each sale (see below), so the disclosed figure can be stale.

## Unlock schedule and the Oct 5, 2026 waiver (`inputs/ena_tranches.csv`)

**Superseded on 2026-10-05.** Per the 8-K filed 2026-09-17, the Ethena
Foundation waived every lock-up on the treasury's ENA effective Oct 5, 2026,
including the 48-month schedule below. The `waived_on` column records this:
a tranche is fully unlocked from that date, so `ena_unlocked` follows the
contractual schedule before it and equals `ena_holdings` from it. History is
unchanged. The same letter lets the company sell ENA ("Funding Sales") after
five business days' notice, during which the Foundation may buy at the offered
price; neither side has to announce a sale unless the law requires it.

The original schedule, kept for the pre-waiver history:

Most of the treasury is "Locked ENA" bought from Ethena OpCo with PIPE cash,
subject to a 48-month contractual lock-up: 25% unlocks on the 12-month
anniversary of purchase, the remaining 75% in 36 equal monthly installments
(per the Token Purchase Agreements described in the 424B3 prospectus).

| tranche | tokens | purchased | locked |
|---|---|---|---|
| Initial cash PIPE | 1,231,887,038 | ~2025-07-31 | 48-mo schedule |
| Additional cash PIPE | 914,341,826 | ~2025-09-30 | 48-mo schedule |
| ENA-paid PIPE + Ethena contribution | 882,771,136 | — | assumed unlocked |

Purchase dates are approximated as month-end ("completed by the end of
July/September 2025" per the 424B3). The ENA-paid tranche (tokens delivered
by PIPE investors and Ethena's $60M contribution) has no disclosed lock-up
and is assumed liquid from listing. `ena_unlocked` is computed as
`ena_holdings` minus the still-locked balance of the locked tranches, so
future purchases appended to `ena_holdings.csv` count as unlocked unless a
new locked tranche row is added.

No API keys required (Yahoo Finance via `yfinance`, CoinGecko free tier,
SEC EDGAR, Nasdaq's public option-chain API).

`build_dashboard_data.py` also writes two sections from those sources, each
carried forward from the previous `docs/data.json` if its source fails:

- `insiders` — the 15 most recent Forms 3/4/5 from EDGAR, parsed into owner,
  role and transactions (code, shares, price). Filings are immutable, so ones
  already parsed are reused by accession number rather than re-fetched.
- `options` — the listed USDE option chain from Nasdaq, per expiry and strike
  (bid/ask/last/volume/open interest). Yahoo did not carry the chain when
  this was added (2026-10-03).

## EthenaPay tab

`ethenadash.com/#pay` tracks **EthenaPay**, the USDe card programme on Avalanche
C-Chain (chain 43114) — USDe held, deposits and withdrawals, card spend, wallet
growth and cashback.

`fetch_ethenapay.py` pulls two saved Dune queries and writes
`docs/ethenapay.json`, which the page fetches from the GitHub raw feed exactly
like `data.json`. It reads each query's *last cached execution*, so the refresh
costs no Dune credits; re-running the queries themselves happens in the
[QorbQuant/ethenaPay](https://github.com/QorbQuant/ethenaPay) repo, which owns
the SQL and documents how every metric is defined.

```bash
DUNE_API_KEY=... python fetch_ethenapay.py
```

In CI the key comes from the `DUNE_API_KEY` repository secret. The step is
`continue-on-error` and the script exits cleanly when the key is absent — the
NAV tracker is the site's primary job and must keep refreshing regardless.

Two things worth knowing before quoting these numbers:

- **There is no single "users" figure.** A wallet is deployed cheaply at signup
  and most are never funded, so wallet count overstates adoption by ~30×. The tab
  shows the funnel (deployed → funded → ever spent) rather than picking one.
- **USDe held is concentrated** — the top 10 wallets hold ~76% of it, so the
  headline tracks a handful of accounts, not broad retail growth.

## Hosting

The dashboard (`docs/`) is live at **https://ethenadash.com**, served by a
Cloudflare **Worker** (`site-worker/`), not Cloudflare Pages:

```bash
npx wrangler deploy --config site-worker/wrangler.toml   # ship site changes
```

It ran on Pages until 2026-09-11, when the Pages *custom-domain* routing path
began returning HTTP 530 / error 1016 on ~10–13% of requests for this account
— while `ethenadash.pages.dev` stayed 100% healthy and the DNS and
custom-domain config were both correct. The same failure hit another Pages
custom domain on the account, so it was not project-specific. An interleaved
head-to-head measured Pages 4/30 failed vs Worker 0/30; after cutover the apex
measured 99/100.

The `ethenadash` Pages project is intentionally left intact as a rollback
path: re-attach the custom domains there to revert. Live prices come from the
`ethenadash-quotes` Worker (`worker/`) and CoinGecko, and the daily series
from the repo's own `docs/data.json` via the GitHub raw feed, so the site
stays current without redeploying.

## Dashboard UI

The StablecoinX valuation workspace and EthenaPay dashboard are static HTML,
CSS, and JavaScript in `docs/`. The visual design uses a shared dark theme,
interactive valuation scenarios, date inspection, performance charts, and
progressive disclosure for research tables.

- `docs/assets/data.js`: feed validation, valuation calculations, quote overlays,
  contractual unlocking, and completed-session filtering.
- `docs/assets/app.js`: independent page loading, hash navigation, live quote
  refresh every minute, and source refresh every five minutes while visible.
- `docs/assets/valuation.js`: scenario map, historical inspection, and exact
  three-factor Shapley attribution using historical endpoint observations.
- `docs/assets/research.js`: performance, derivatives, filings, and card analytics.
- `docs/assets/dashboard.css`: shared desktop/mobile styles.
- D3 7.9.0 is bundled locally with its ISC license; no runtime CDN is required.

The production page prefers the GitHub raw feeds and falls back to deployed
JSON. Failed refreshes retain the last successful data, and an older fallback
cannot replace a newer observation already loaded. Source timestamps remain
visible; EthenaPay displays a stale notice after 36 hours. Prices can be delayed.
Current quote-based valuation is distinct from historical observations: only
fresh same-session intraday quotes are folded into the current historical row.
The redemption tracker excludes unfinished observations.

Run calculation regression checks with `node --test tests/data.test.cjs`.
Preview with `python3 -m http.server 8765 --directory docs`; check `/` and `/#pay`.
Deploy remains `npx wrangler deploy --config site-worker/wrangler.toml`.

## Website and search pages

The production site is a Cloudflare Worker with static assets. Use the Worker
preview (a plain static server does not render the new page routes):

```bash
npx wrangler dev --config site-worker/wrangler.toml --port 8777 --var LOCAL_DEV:true
node --test tests/data.test.cjs tests/seo.test.mjs
python3 scripts/check_seo.py http://127.0.0.1:8777
npx wrangler deploy --config site-worker/wrangler.toml
python3 scripts/check_seo.py https://ethenadash.com
```

`LOCAL_DEV` is only a local CLI override; never add it to production variables.
`site-worker/index.mjs` renders both dashboard snapshots with the same validated
JSON and calculations used by the browser. The upstream GitHub datasets are
cached for five minutes at the edge; failed requests fall back to the deployed
JSON and display a backup/staleness notice. Source refresh commits therefore
continue to update the live dashboard without a website deployment. JavaScript
adds live quotes and interactive charts after the initial HTML arrives.

`site-worker/seo.mjs` owns canonical routes, metadata, author identity, sitemap
and shared navigation. `site-worker/content.mjs` contains the three sourced
research guides, methodology and About page. New articles need a unique route,
useful original analysis, reviewed primary sources, and a link from Research.
Change publication/update dates only when the editorial content actually changes.
Search Console verification is a public HTML meta tag in `extraHead`.

The root and legacy `/index.html` permanently redirect to `/stablecoinx/`;
legacy `#pay` bookmarks are handled by the client. Alternate hostnames redirect
to `https://ethenadash.com`. Unknown paths remain 404 responses.
