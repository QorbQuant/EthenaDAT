"""Keep incomplete upstream market observations out of the published history."""

import math
import warnings

import pandas as pd


def positive(value):
    return isinstance(value, (int, float)) and math.isfinite(value) and value > 0


def reconcile_prices(current, previous, name):
    """Prefer fresh prices; recover gaps only from an observation on the same date.

    Never forward-fill a price into a new trading day. An incomplete new date
    waits until the provider supplies a usable observation.
    """
    fresh = pd.to_numeric(current, errors="coerce")
    old = pd.to_numeric(previous, errors="coerce")
    fresh = fresh.where(fresh.map(positive))
    old = old.where(old.map(positive))
    result = fresh.combine_first(old).dropna().sort_index().rename(name)
    gaps = fresh.index[fresh.isna()]
    if len(gaps):
        recovered = len(gaps.intersection(result.index))
        warnings.warn(
            f"{name}: {len(gaps)} incomplete observations; recovered {recovered} "
            "from previously recorded prices for the same dates; omitted "
            f"{len(gaps) - recovered} without a valid observation.",
            stacklevel=2,
        )
    if result.empty:
        raise ValueError(f"No valid {name} observations; keeping the published dataset")
    return result


def validate_history(df):
    """Fail before writing files if core inputs or calculated history are invalid."""
    dates = pd.DatetimeIndex(df["date"] if "date" in df else df.index)
    if df.empty or dates.hasnans or not dates.is_unique or not dates.is_monotonic_increasing:
        raise ValueError("History must contain unique, increasing dates")
    for name in (
        "usde_close", "ena_price", "shares_outstanding", "ena_holdings",
        "market_cap", "ena_nav", "nav_per_share", "mnav",
    ):
        if name not in df or not df[name].map(positive).all():
            raise ValueError(f"Invalid {name}; keeping the published dataset")
