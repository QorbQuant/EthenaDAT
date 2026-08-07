"""Build the StablecoinX (Nasdaq: USDE) chart dataset.

Fetches USDE daily closes (Yahoo Finance) and ENA daily prices (CoinGecko),
joins them with the hand-maintained event tables in inputs/, and writes
output/ethena_dat.csv and output/ethena_dat.json with:

    date, usde_close, shares_outstanding, market_cap,
    ena_price, ena_holdings, ena_nav, nav_per_share, mnav
"""

from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

ROOT = Path(__file__).parent
LISTING_DATE = "2026-06-26"  # first Nasdaq trading day post TLGY merger
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/ethena/market_chart"


def fetch_usde() -> pd.Series:
    df = yf.download("USDE", start=LISTING_DATE, auto_adjust=False, progress=False)
    if df.empty:
        raise RuntimeError("yfinance returned no data for USDE")
    close = df["Close"]
    if isinstance(close, pd.DataFrame):  # yfinance>=0.2.4x multi-index columns
        close = close.iloc[:, 0]
    close.index = close.index.tz_localize(None).normalize()
    return close.rename("usde_close")


def fetch_ena(days: int) -> pd.Series:
    resp = requests.get(
        COINGECKO_URL,
        params={"vs_currency": "usd", "days": days, "interval": "daily"},
        timeout=30,
    )
    resp.raise_for_status()
    prices = resp.json()["prices"]  # [[ms_timestamp, price], ...]
    s = pd.Series(
        {pd.Timestamp(ts, unit="ms").normalize(): p for ts, p in prices},
        name="ena_price",
    )
    return s[~s.index.duplicated(keep="last")]


def load_events(name: str, column: str, index: pd.DatetimeIndex) -> pd.Series:
    """Forward-fill a date,value event table onto the trading-day index."""
    events = pd.read_csv(ROOT / "inputs" / name, parse_dates=["date"])
    s = events.set_index("date")[column].sort_index()
    return s.reindex(index.union(s.index)).ffill().reindex(index)


def main() -> None:
    usde = fetch_usde()
    days = (pd.Timestamp.today().normalize() - pd.Timestamp(LISTING_DATE)).days + 5
    ena = fetch_ena(days)

    df = pd.DataFrame(usde)
    df["shares_outstanding"] = load_events("shares_out.csv", "shares_outstanding", df.index)
    df["ena_price"] = ena.reindex(df.index)
    df["ena_holdings"] = load_events("ena_holdings.csv", "ena_holdings", df.index)

    df["market_cap"] = df["usde_close"] * df["shares_outstanding"]
    df["ena_nav"] = df["ena_price"] * df["ena_holdings"]
    df["nav_per_share"] = df["ena_nav"] / df["shares_outstanding"]
    df["mnav"] = df["market_cap"] / df["ena_nav"]

    df.index.name = "date"
    df = df.round(
        {"usde_close": 4, "market_cap": 0, "ena_price": 6, "ena_nav": 0,
         "nav_per_share": 4, "mnav": 4}
    )

    out = ROOT / "output"
    out.mkdir(exist_ok=True)
    df.to_csv(out / "ethena_dat.csv", date_format="%Y-%m-%d")
    df.reset_index().assign(date=lambda d: d["date"].dt.strftime("%Y-%m-%d")).to_json(
        out / "ethena_dat.json", orient="records", indent=2
    )

    print(df.tail().to_string())
    print(f"\n{len(df)} rows -> {out / 'ethena_dat.csv'}")


if __name__ == "__main__":
    main()
