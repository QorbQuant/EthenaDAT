"""Build docs/data.json for the dashboard from the pipeline output.

Bundles the full daily series, the input tables (holdings, shares, tranches),
and a fresh USDE quote snapshot so the static page can render everything and
compute live ENA-side values client-side.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).parent


def usde_snapshot(df: pd.DataFrame) -> dict:
    try:
        info = yf.Ticker("USDE").info
        price = info.get("regularMarketPrice")
        if price:
            return {
                "price": price,
                "prev_close": info.get("previousClose"),
                "market_state": info.get("marketState"),
                "quote_time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
    except Exception:
        pass
    valid = df.dropna(subset=["usde_close"])
    last = valid.iloc[-1]
    return {
        "price": float(last.usde_close),
        "prev_close": float(valid.iloc[-2].usde_close) if len(valid) > 1 else None,
        "market_state": "FROM_DAILY_CLOSE",
        "quote_time": str(last.date.date()),
    }


def main() -> None:
    df = pd.read_csv(ROOT / "output" / "ethena_dat.csv", parse_dates=["date"])
    tranches = pd.read_csv(ROOT / "inputs" / "ena_tranches.csv")
    last = df.iloc[-1]

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "usde": usde_snapshot(df),
        "shares_outstanding": float(last.shares_outstanding),
        "ena_holdings": float(last.ena_holdings),
        "ena_unlocked_latest": float(last.ena_unlocked),
        # Public warrant terms per the Super 8-K (July 2, 2026) and the TLGY
        # Warrant Agreement (Exhibit 4.1, Dec 6, 2021 8-K)
        "warrants": {
            "count": 11499988,
            "strike": 11.50,
            "expiry": "2031-06-25",
            "exercisable_from": "2026-07-25",
            "redemption": "$0.01 call at $18.00 trigger; $0.10 call at $10.00 trigger (make-whole cashless, max 0.361 sh/warrant)",
        },
        "tranches": tranches.to_dict(orient="records"),
        "series": {
            "date": df["date"].dt.strftime("%Y-%m-%d").tolist(),
            **{
                c: [None if pd.isna(v) else float(v) for v in df[c]]
                for c in df.columns
                if c != "date"
            },
        },
    }

    out = ROOT / "docs" / "data.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(payload, separators=(",", ":"), allow_nan=False))
    print(f"wrote {out} ({out.stat().st_size:,} bytes, {len(df)} rows)")


if __name__ == "__main__":
    main()
