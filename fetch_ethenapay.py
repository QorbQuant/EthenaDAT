"""Build docs/ethenapay.json for the EthenaPay tab from Dune.

EthenaPay is the USDe card programme on Avalanche C-Chain. The metric
definitions — and the on-chain reasoning behind them — live in the
QorbQuant/ethenaPay repo under dune/; this script only pulls the results of the
two saved queries and reshapes them into the column-oriented series the
dashboard already expects.

The refresh workflow runs every ~30 minutes, but these metrics have a daily
grain, so re-executing on every run would burn Dune credits for no new
information. Instead the cached result is reused until it is older than
MAX_AGE_HOURS (default 20), at which point both queries are re-executed once.
That works out to roughly one execution per query per day.

Reading the cache alone was the original design and it silently froze the tab:
nothing ever re-ran the queries, so every refresh republished the same day.

Needs DUNE_API_KEY in the environment.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).parent
DUNE = "https://api.dune.com/api/v1"

QUERY_DAILY = int(os.environ.get("DUNE_QUERY_DAILY", 8680891))
QUERY_HEADLINE = int(os.environ.get("DUNE_QUERY_HEADLINE", 8680892))
MAX_AGE_HOURS = float(os.environ.get("DUNE_MAX_AGE_HOURS", 20))

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


def dune_results(query_id: int, api_key: str) -> dict:
    r = requests.get(
        f"{DUNE}/query/{query_id}/results",
        headers={"X-Dune-API-Key": api_key},
        params={"limit": 1000},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def age_hours(body: dict) -> float:
    ended = body.get("execution_ended_at")
    if not ended:
        return float("inf")
    # Dune emits a variable number of fractional-second digits (e.g. ".62442"),
    # which older fromisoformat implementations reject; seconds are plenty here.
    ended = datetime.strptime(ended[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - ended).total_seconds() / 3600


def execute(query_id: int, api_key: str) -> None:
    headers = {"X-Dune-API-Key": api_key}
    r = requests.post(f"{DUNE}/query/{query_id}/execute", headers=headers,
                      json={"performance": "medium"}, timeout=60)
    r.raise_for_status()
    execution_id = r.json()["execution_id"]
    for _ in range(120):
        time.sleep(5)
        st = requests.get(f"{DUNE}/execution/{execution_id}/status", headers=headers, timeout=60)
        st.raise_for_status()
        state = st.json().get("state")
        if state == "QUERY_STATE_COMPLETED":
            return
        if state in ("QUERY_STATE_FAILED", "QUERY_STATE_CANCELLED", "QUERY_STATE_EXPIRED"):
            raise RuntimeError(f"query {query_id}: execution {execution_id} ended {state}")
    raise RuntimeError(f"query {query_id}: execution {execution_id} timed out")


def dune_rows(query_id: int, api_key: str) -> list:
    body = dune_results(query_id, api_key)
    age = age_hours(body)
    if age > MAX_AGE_HOURS:
        print(f"query {query_id}: cached result is {age:.1f}h old, re-executing")
        execute(query_id, api_key)
        body = dune_results(query_id, api_key)
    else:
        print(f"query {query_id}: using cached result ({age:.1f}h old)")
    rows = body.get("result", {}).get("rows")
    if rows is None:
        raise RuntimeError(f"query {query_id}: no rows (state={body.get('state')})")
    return rows


def num(v):
    return None if v is None else float(v)


def main() -> None:
    api_key = os.environ.get("DUNE_API_KEY")
    if not api_key:
        # Not fatal: the NAV tracker is the site's primary job and must keep
        # refreshing. Leaves any existing docs/ethenapay.json in place.
        print("DUNE_API_KEY not set — skipping EthenaPay refresh")
        return

    daily = sorted(dune_rows(QUERY_DAILY, api_key), key=lambda r: r["day"])
    headline = dune_rows(QUERY_HEADLINE, api_key)[0]

    series = {"date": [str(r["day"])[:10] for r in daily]}
    for src, dest in SERIES_COLUMNS.items():
        series[dest] = [num(r.get(src)) for r in daily]

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "dune",
        "queries": {"daily": QUERY_DAILY, "headline": QUERY_HEADLINE},
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

    out = ROOT / "docs" / "ethenapay.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(payload, separators=(",", ":"), allow_nan=False))
    print(f"wrote {out} ({out.stat().st_size:,} bytes, {len(daily)} rows)")


if __name__ == "__main__":
    main()
