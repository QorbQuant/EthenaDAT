"""Refresh an independent Earn+ snapshot and UTC day-end history without Dune credits."""
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

from scripts.earnplus_rpc import collect

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs/earnplus.json"
CACHE = ROOT / "output/earnplus-history.json"
START = "2026-10-25"  # Includes the pre-launch ramp; public launch was October 28.


def retry(fn):
    for attempt in range(3):
        try:
            return fn()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(1 + attempt)


def day_end(day):
    stamp = int(datetime.fromisoformat(day + "T00:00:00+00:00").timestamp()) + 86399
    query = urlencode(dict(module="block", action="getblocknobytime", timestamp=stamp, closest="before"))
    def lookup():
        with urlopen("https://api.routescan.io/v2/network/mainnet/evm/43114/etherscan/api?" + query, timeout=30) as r:
            value = json.load(r)
        if value.get("status") != "1":
            raise RuntimeError("Historical block lookup failed")
        snapshot = collect(int(value["result"]))
        observed = datetime.fromisoformat(snapshot["observedAt"]).timestamp()
        if not stamp - 10 <= observed <= stamp:
            raise ValueError("Historical block is not at the requested UTC day-end")
        return snapshot
    return day, retry(lookup)


def build(history, current):
    today = current["observedAt"][:10]
    observations = [(day, row, False) for day, row in sorted(history.items()) if day < today]
    observations.append((today, current, True))
    keys = ["date", "active_usde", "pending_usde", "nav_usde", "block_number", "observed_at", "accounting_updated_at", "partial"]
    series = {key: [] for key in keys}
    for day, row, partial in observations:
        vals = [day, float(row["activeEarnBalanceUsde"]), float(row["pendingWithdrawalGrossUsde"]),
                float(row["vaultReportedNavUsde"]), row["blockNumber"], row["observedAt"], row["accountingUpdatedAt"], partial]
        for key, value in zip(keys, vals):
            series[key].append(value)
    return dict(generated_at=current["observedAt"], chain_id=43114, vault=current["vault"],
                units="USDe", valuation_basis=current["valuationBasis"],
                headline=current, series=series)


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, separators=(",", ":")) + "\n")
    temp.replace(path)


def main():
    history = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    current = retry(collect)
    today = current["observedAt"][:10]
    day = datetime.fromisoformat(START).date()
    missing = []
    while day.isoformat() < today:
        if day.isoformat() not in history:
            missing.append(day.isoformat())
        day += timedelta(days=1)
    # Small bounded concurrency for the one-time archive backfill.
    with ThreadPoolExecutor(max_workers=2) as pool:
        for day, snapshot in pool.map(day_end, missing):
            history[day] = snapshot
            atomic(CACHE, history)
            print("Verified day-end", day, "block", snapshot["blockNumber"], flush=True)
    atomic(OUT, build(history, current))
    print("Earn+ refreshed:", len(history), "completed UTC days; current", current["activeEarnBalanceUsde"], "USDe")


if __name__ == "__main__":
    main()
