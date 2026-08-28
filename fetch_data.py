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


def unlocked_fraction(purchase_date: pd.Timestamp, d: pd.Timestamp) -> float:
    """Locked ENA schedule per the Token Purchase Agreements (424B3):
    48-month lock-up — 25% unlocks on the 12-month anniversary of purchase,
    the remaining 75% in 36 equal monthly installments."""
    cliff = purchase_date + pd.DateOffset(months=12)
    if d < cliff:
        return 0.0
    months = (d.year - cliff.year) * 12 + (d.month - cliff.month)
    # compare against the clamped installment date so month-end tranches
    # (e.g. purchased Jul 31) vest on Sep 30, not Oct 1
    if d < purchase_date + pd.DateOffset(months=12 + months):
        months -= 1
    return min(1.0, 0.25 + 0.75 * min(36, months) / 36)


def locked_remaining(index: pd.DatetimeIndex) -> pd.Series:
    """Total still-locked tokens across the locked tranches, per date."""
    tranches = pd.read_csv(ROOT / "inputs" / "ena_tranches.csv", parse_dates=["purchase_date"])
    tranches = tranches[tranches["locked"]]
    return pd.Series(
        [
            sum(
                tr.tokens * (1 - unlocked_fraction(tr.purchase_date, d))
                for tr in tranches.itertuples()
            )
            for d in index
        ],
        index=index,
        name="ena_locked",
    )


def main() -> None:
    usde = fetch_usde()
    # CoinGecko's keyless tier caps history at 365 days; older dates are
    # backfilled from the previously committed output below.
    days = min((pd.Timestamp.today().normalize() - pd.Timestamp(LISTING_DATE)).days + 5, 360)
    ena = fetch_ena(days)
    prev_path = ROOT / "output" / "ethena_dat.csv"
    if prev_path.exists():
        prev = pd.read_csv(prev_path, parse_dates=["date"]).set_index("date")["ena_price"]
        ena = ena.combine_first(prev)

    df = pd.DataFrame(usde)
    df["shares_outstanding"] = load_events("shares_out.csv", "shares_outstanding", df.index)
    df["ena_price"] = ena.reindex(df.index)
    df["ena_holdings"] = load_events("ena_holdings.csv", "ena_holdings", df.index)

    df["market_cap"] = df["usde_close"] * df["shares_outstanding"]
    df["ena_nav"] = df["ena_price"] * df["ena_holdings"]
    df["nav_per_share"] = df["ena_nav"] / df["shares_outstanding"]
    df["mnav"] = df["market_cap"] / df["ena_nav"]

    # Realizable view: only tokens past their contractual unlock schedule.
    df["ena_unlocked"] = df["ena_holdings"] - locked_remaining(df.index)
    df["nav_unlocked"] = df["ena_price"] * df["ena_unlocked"]
    df["nav_unlocked_per_share"] = df["nav_unlocked"] / df["shares_outstanding"]
    df["mnav_unlocked"] = df["market_cap"] / df["nav_unlocked"]

    df.index.name = "date"
    df = df.round(
        {"usde_close": 4, "market_cap": 0, "ena_price": 6, "ena_nav": 0,
         "nav_per_share": 4, "mnav": 4, "ena_unlocked": 0, "nav_unlocked": 0,
         "nav_unlocked_per_share": 4, "mnav_unlocked": 4}
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
