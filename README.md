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

## Updating the input tables

Holdings and share count only change on discrete events (ENA purchases,
issuance), so they live in hand-maintained event tables that get
forward-filled by date. When StablecoinX announces a change, append a row:

- `inputs/ena_holdings.csv` — `date,ena_holdings`
- `inputs/shares_out.csv` — `date,shares_outstanding`

Seed values come from the closing 8-K (June 25, 2026 press release):
~3,029M ENA valued at $275M ($0.0909 30-day VWAP), stated as "$11.42 per
fully diluted share" → 24.11M fully diluted shares (275.3M ÷ 11.42).

No API keys required (Yahoo Finance via `yfinance`, CoinGecko free tier).
