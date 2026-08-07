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
~3,029M ENA valued at $275M ($0.0909 30-day VWAP), stated as "$11.42 per
fully diluted share" → 24.11M fully diluted shares (275.3M ÷ 11.42).
The Super 8-K (July 2, 2026) reports 27,187,129 total shares at closing
(24,029,375 Class A + 3,157,754 unlisted Class B); the Class A-only count
is used here, matching the company's own NAV-per-share framing.

## Unlock schedule (`inputs/ena_tranches.csv`)

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

No API keys required (Yahoo Finance via `yfinance`, CoinGecko free tier).
