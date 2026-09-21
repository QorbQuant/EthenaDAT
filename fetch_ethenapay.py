"""Build docs/ethenapay.json for the EthenaPay tab from Dune.

EthenaPay is the USDe card programme on Avalanche C-Chain. The metric
definitions — and the on-chain reasoning behind them — live in the
QorbQuant/ethenaPay repo under dune/; this script runs that SQL and reshapes
the results into the column-oriented series the dashboard expects.

Two failure modes are worth recording, because both came from depending on
*saved* Dune queries:

  1. Reading a saved query's cached result and never executing it silently
     froze the tab — every refresh republished the same day.
  2. Re-executing the saved queries fixed that until 2026-09-17, when both ids
     began returning "Query not found or private" (deleted, or no longer
     API-visible). The workflow step is `continue-on-error`, and GitHub reports
     such a step as *success*, so four days of failures surfaced nowhere.

So there is no saved-query id here any more: the SQL itself is sent to Dune's
ad-hoc /sql/execute endpoint, sourced from the public ethenaPay repo, which is
the source of truth for these definitions.

Executions cost credits (~50 each, so ~100 for the pair), so the run is gated
on the age of the existing docs/ethenapay.json — the queries only re-run once
the published data is older than MAX_AGE_HOURS. The refresh workflow can keep
firing every 30 minutes without burning the budget.

Needs DUNE_API_KEY in the environment.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).parent
OUT = ROOT / "docs" / "ethenapay.json"
DUNE = "https://api.dune.com/api/v1"

SQL_BASE = os.environ.get(
    "ETHENAPAY_SQL_BASE",
    "https://raw.githubusercontent.com/QorbQuant/ethenaPay/main/dune",
)
SQL_FILES = {"daily": "05_daily_metrics.sql", "headline": "06_kpi_headline.sql"}
MAX_AGE_HOURS = float(os.environ.get("DUNE_MAX_AGE_HOURS", 20))
PERFORMANCE = os.environ.get("DUNE_PERFORMANCE", "medium")  # "small" is not on this plan

# Dune column -> the name the dashboard uses. "users" is deliberately renamed to
# "wallets": a wallet is deployed at signup and most are never funded, so the
# two are not the same thing and the tab shows the funnel instead.
SERIES_COLUMNS = {
    "new_users": "new_wallets",
    "cumulative_users": "cumulative_wallets",
    "active_wallets": "active_wallets",
    "spend_count": "spend_count",
    "spend_usde": "spend_usde",
    "deposits_usde": "deposits_usde",
    "withdrawals_usde": "withdrawals_usde",
    "reversals_usde": "reversals_usde",
    "depositing_wallets": "depositing_wallets",
    "tvl_usde": "tvl_usde",
    "cashback_avax": "cashback_avax",
}

# A silent schema change upstream would otherwise publish a tab full of dashes.
REQUIRED_HEADLINE = {"total_users", "funded_wallets", "lifetime_spend_usde", "tvl_usde"}
REQUIRED_DAILY = {"day", "new_users", "spend_usde"}


def published_age_hours() -> float:
    """Age of the data already on the site, in hours."""
    try:
        stamp = json.loads(OUT.read_text())["generated_at"]
        when = datetime.strptime(stamp[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    except Exception:
        return float("inf")
    return (datetime.now(timezone.utc) - when).total_seconds() / 3600


def fetch_sql(name: str) -> str:
    r = requests.get(f"{SQL_BASE}/{SQL_FILES[name]}", timeout=60)
    r.raise_for_status()
    return r.text


def run_sql(name: str, sql: str, api_key: str) -> list:
    headers = {"X-Dune-API-Key": api_key}
    r = requests.post(f"{DUNE}/sql/execute", headers=headers,
                      json={"sql": sql, "performance": PERFORMANCE}, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"{name}: execute failed {r.status_code}: {r.text[:300]}")
    execution_id = r.json()["execution_id"]

    state = None
    for _ in range(150):
        time.sleep(4)
        st = requests.get(f"{DUNE}/execution/{execution_id}/status", headers=headers, timeout=60)
        st.raise_for_status()
        state = st.json().get("state")
        if state == "QUERY_STATE_COMPLETED":
            break
        if state in ("QUERY_STATE_FAILED", "QUERY_STATE_CANCELLED", "QUERY_STATE_EXPIRED"):
            raise RuntimeError(f"{name}: execution {execution_id} ended {state}")
    else:
        raise RuntimeError(f"{name}: execution {execution_id} timed out (last state {state})")

    res = requests.get(f"{DUNE}/execution/{execution_id}/results",
                       headers=headers, params={"limit": 5000}, timeout=120)
    res.raise_for_status()
    rows = res.json().get("result", {}).get("rows")
    if not rows:
        raise RuntimeError(f"{name}: execution {execution_id} returned no rows")
    print(f"{name}: {len(rows)} rows")
    return rows


def check_columns(name: str, row: dict, required: set) -> None:
    missing = required - set(row)
    if missing:
        raise RuntimeError(f"{name}: result is missing expected columns {sorted(missing)}")


def num(v):
    return None if v is None else float(v)


def main() -> None:
    api_key = os.environ.get("DUNE_API_KEY")
    if not api_key:
        # Not fatal: the NAV tracker is the site's primary job and must keep
        # refreshing. Leaves any existing docs/ethenapay.json in place.
        print("DUNE_API_KEY not set — skipping EthenaPay refresh")
        return

    age = published_age_hours()
    if age < MAX_AGE_HOURS and not os.environ.get("ETHENAPAY_FORCE"):
        print(f"published data is {age:.1f}h old (< {MAX_AGE_HOURS}h) — skipping, no credits spent")
        return
    print(f"published data is {age:.1f}h old — running queries")

    daily = sorted(run_sql("daily", fetch_sql("daily"), api_key), key=lambda r: r["day"])
    headline = run_sql("headline", fetch_sql("headline"), api_key)[0]
    check_columns("daily", daily[0], REQUIRED_DAILY)
    check_columns("headline", headline, REQUIRED_HEADLINE)

    series = {"date": [str(r["day"])[:10] for r in daily]}
    for src, dest in SERIES_COLUMNS.items():
        series[dest] = [num(r.get(src)) for r in daily]

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "dune",
        "sql": {k: f"{SQL_BASE}/{v}" for k, v in SQL_FILES.items()},
        "headline": {
            "wallets_created": num(headline.get("total_users")),
            "wallets_created_30d": num(headline.get("new_users_30d")),
            "funded_wallets": num(headline.get("funded_wallets")),
            "spending_wallets": num(headline.get("lifetime_spenders")),
            "funding_rate": num(headline.get("funding_rate")),
            "activation_rate": num(headline.get("activation_rate")),
            "lifetime_spend_count": num(headline.get("lifetime_spend_count")),
            "lifetime_spend_usde": num(headline.get("lifetime_spend_usde")),
            "spend_usde_30d": num(headline.get("spend_usde_30d")),
            "mau_30d": num(headline.get("mau_30d")),
            "wau_7d": num(headline.get("wau_7d")),
            "avg_spend_usde": num(headline.get("avg_spend_usde")),
            "median_spend_usde": num(headline.get("median_spend_usde")),
            "tvl_usde": num(headline.get("tvl_usde")),
            "top10_balance_share": num(headline.get("top10_balance_share")),
            "cashback_avax_total": num(headline.get("cashback_avax_total")),
            "cashback_payments_total": num(headline.get("cashback_payments_total")),
            "max_logs_per_tx": num(headline.get("max_logs_per_tx")),
            "batched_spend_share": num(headline.get("batched_spend_share")),
        },
        "series": series,
    }

    # Lifetime deposits/withdrawals aren't in the headline query — they are a
    # sum over the daily series, so derive them here rather than adding a column.
    payload["headline"]["lifetime_deposits_usde"] = sum(v or 0 for v in series["deposits_usde"])
    payload["headline"]["lifetime_withdrawals_usde"] = sum(v or 0 for v in series["withdrawals_usde"])
    payload["headline"]["lifetime_reversals_usde"] = sum(v or 0 for v in series["reversals_usde"])
    spend = payload["headline"]["lifetime_spend_usde"] or 0
    payload["headline"]["refund_rate"] = (
        payload["headline"]["lifetime_reversals_usde"] / spend if spend else None
    )

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(payload, separators=(",", ":"), allow_nan=False))
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes, {len(daily)} rows, "
          f"through {series['date'][-1]})")


if __name__ == "__main__":
    main()
