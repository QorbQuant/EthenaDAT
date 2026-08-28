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
    last = df.iloc[-1]
    return {
        "price": float(last.usde_close),
        "prev_close": float(df.iloc[-2].usde_close) if len(df) > 1 else None,
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
    out.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"wrote {out} ({out.stat().st_size:,} bytes, {len(df)} rows)")


if __name__ == "__main__":
    main()
