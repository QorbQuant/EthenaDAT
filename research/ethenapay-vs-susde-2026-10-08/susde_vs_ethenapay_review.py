#!/usr/bin/env python3
"""EthenaPay's USDe reward next to staked USDe. What sUSDe's share price paid from September 1 to October 8, 2026,
against the rates EthenaPay's payments were set at on USDe balances in the same days.

Reads the files susde_read.cjs wrote in inputs/chain/, the measured EthenaPay rates in the Daily Boost review's
results (inputs/dailyboost_results.json) and the cash-flow review's results, checks them, and works out sUSDe's
share price at each UTC midnight from August 31 to October 10, its yearly rate for each day and for September and
October 1 to 8, the rewards paid into the contract, the USDe behind all sUSDe that those payments were shared over,
and where EthenaPay's tier rates and caps put a balance above or below sUSDe. If any check fails the script writes
its log to run_log_failed.txt and stops before writing its tables, so out/ keeps the tables of the last clean run.
Python 3 standard library only. No network.
"""
import bisect
import csv
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path

getcontext().prec = 60
getcontext().rounding = ROUND_HALF_UP   # every figure written is rounded half up
HERE = Path(__file__).parent
INP = HERE / "inputs"
CH = INP / "chain"
OUT = HERE / "out"
DAY = 86400
E18 = Decimal(10) ** 18
MIN_SHARES = 10 ** 15        # events of less than 0.001 sUSDe are left out of the price, where one unit of rounding matters

log_lines = []
failures = []


def log(msg=""):
    log_lines.append(msg)
    print(msg)


def check(name, ok, detail=""):
    log(("ok    " if ok else "FAIL  ") + name + (f"  ({detail})" if detail else ""))
    if not ok:
        failures.append(name)


def table(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ts(y, m, d):
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp())


def iso(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def day_of(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d")


def root(x, n):
    """x ** (1 / n) for Decimal x > 0, by Newton's method, to the context's precision."""
    x = Decimal(x)
    g = Decimal(1) + (x - 1) / n
    for _ in range(200):
        nxt = g - (g ** n - x) / (n * g ** (n - 1))
        if abs(nxt - g) < Decimal(10) ** -50:
            return nxt
        g = nxt
    return g


def daily_share(rate_pct):
    """The daily rate that compounds to rate_pct a year over 365 days, the convention Ethena Pay's payments followed."""
    return root(1 + Decimal(rate_pct) / 100, 365) - 1


def after_compounding(daily):
    return ((1 + Decimal(daily)) ** 365 - 1) * 100


R = {}
log("EthenaPay's reward next to sUSDe")
log("Inputs")
for m in table(INP / "manifest.csv"):
    p = INP / m["file"]
    check(f"input {m['file']} matches its SHA-256", p.exists() and p.stat().st_size == int(m["bytes"]) and sha(p) == m["sha256"])
for m in table(INP / "chain_manifest.csv"):
    p = CH / m["file"]
    check(f"chain file {m['file']} matches its SHA-256", p.exists() and p.stat().st_size == int(m["bytes"]) and sha(p) == m["sha256"])
    check(f"chain file {m['file']} was written by this susde_read.cjs", m["script_sha256"] == sha(HERE / "susde_read.cjs"))
meta = json.loads((CH / "meta.json").read_text())
db = json.loads((INP / "dailyboost_results.json").read_text())
cf = json.loads((INP / "cashflow_results.json").read_text())
terms = {r["id"]: r for r in table(INP / "terms_facts.csv")}

# ---------------------------------------------------------------- the chain read
log()
log("The chain read")
events = [{"block": int(r["block"]), "ts": int(r["ts"]), "li": int(r["log_index"]), "kind": r["kind"],
           "assets": int(r["assets_wei"]), "shares": int(r["shares_wei"])} for r in table(CH / "events.csv")]
rewards = [{"block": int(r["block"]), "ts": int(r["ts"]), "li": int(r["log_index"]), "amount": int(r["amount_wei"])} for r in table(CH / "rewards.csv")]
mids = table(CH / "midnights.csv")
check("the events match the read's counts", sum(e["kind"] == "d" for e in events) == meta["deposits"] and sum(e["kind"] == "w" for e in events) == meta["withdrawals"]
      and len(rewards) == meta["rewards"], f"{meta['deposits']} deposits, {meta['withdrawals']} withdrawals, {meta['rewards']} reward logs")
check("events and rewards are in block order with no log twice",
      all((a["block"], a["li"]) < (b["block"], b["li"]) for a, b in zip(events, events[1:])) and all((a["block"], a["li"]) < (b["block"], b["li"]) for a, b in zip(rewards, rewards[1:])))
check("every log lies in the blocks read", all(meta["start_block"] <= e["block"] <= meta["end_block"] for e in events + rewards))
check("block times never run backwards", all(a["ts"] <= b["ts"] for a, b in zip(events, events[1:])))
check("each midnight's block is the last before it",
      all(int(m["block_ts"]) <= int(m["ts"]) < int(m["next_block_ts"]) for m in mids) and len(mids) == 42 and mids[0]["date"] == "2026-08-31")
check("the read covers 00:00 August 30 to the end of October 10 UTC",
      meta["logs_from"] == "2026-08-30T00:00:00Z" and meta["logs_to_before"] == "2026-10-11T00:00:00Z")

# ---------------------------------------------------------------- the share price
log()
log("The share price")
used = [e for e in events if e["shares"] >= MIN_SHARES]
R["events"] = {"deposits": meta["deposits"], "withdrawals": meta["withdrawals"], "used_for_price": len(used), "left_out_under_0_001_susde": len(events) - len(used)}
for e in used:
    e["price"] = Decimal(e["assets"]) / Decimal(e["shares"])
falls = [(a, b) for a, b in zip(used, used[1:]) if b["price"] < a["price"]]
worst = max((Decimal(1) - b["price"] / a["price"] for a, b in falls), default=Decimal(0))
check("the price never falls by more than one part in a billion from one event to the next", worst < Decimal("1e-9"),
      f"{len(falls)} falls, the largest {worst:.2e}, all from the contract's rounding")
check("every fall happens inside one block's second", all(a["ts"] == b["ts"] for a, b in falls))
times = [e["ts"] for e in used]


def price_at(t):
    """Linear between the last event at or before t and the first after it. Rewards vest linearly over 8-hour
    windows that follow one another, and a check below confirms that no window starts or ends between the two events
    around any midnight, so the price runs in a straight line between them."""
    i = bisect.bisect_right(times, t)
    if i == 0 or i == len(used):
        return None, None
    a, b = used[i - 1], used[i]
    return a["price"] + (b["price"] - a["price"]) * Decimal(t - a["ts"]) / Decimal(b["ts"] - a["ts"]), (t - a["ts"], b["ts"] - t)


P, gaps = {}, {}
for m in mids:
    p, g = price_at(int(m["ts"]))
    if p is not None:
        P[m["date"]] = p
        gaps[m["date"]] = g
days = sorted(P)
check("a price at every midnight from August 31 to October 10", days[0] == "2026-08-31" and days[-1] == "2026-10-10" and len(days) == 41,
      f"{len(days)} midnights, October 11 has no event after it")
widest = max(sum(g) for g in gaps.values())
check("the events either side of each midnight are less than four hours apart", widest < 4 * 3600, f"widest {widest / 3600:.2f} hours")
edges = sorted({r["ts"] for r in rewards} | {r["ts"] + 8 * 3600 for r in rewards} | {e["ts"] for e in events if e["shares"] < MIN_SHARES})
mid_ts = {m["date"]: int(m["ts"]) for m in mids}
inside = [d for d in days if any(mid_ts[d] - gaps[d][0] < x < mid_ts[d] + gaps[d][1] for x in edges)]
check("no reward payment, end of a vesting window or left-out record falls between the events either side of a midnight", not inside,
      f"{len(days)} midnights, {len(rewards) * 2} payment times and window ends, {len(events) - len(used)} left-out records")
R["price_at_midnight"] = {d: f"{P[d]:.12f}" for d in days}


def period(d0, d1):
    n = (datetime.fromisoformat(d1) - datetime.fromisoformat(d0)).days
    r = P[d1] / P[d0]
    return {"from": d0, "to": d1, "days": n, "growth_pct": f"{(r - 1) * 100:.6f}",
            "before_compounding_pct": f"{(r - 1) * 100 * 365 / n:.4f}", "after_compounding_pct": f"{(root(r, n) ** 365 - 1) * 100:.4f}"}


R["periods"] = {"september": period("2026-09-01", "2026-10-01"), "october_1_to_8": period("2026-10-01", "2026-10-09"),
                "september_1_to_15": period("2026-09-01", "2026-09-16"), "september_16": period("2026-09-16", "2026-09-17"), "september_17_to_30": period("2026-09-17", "2026-10-01"),
                "september_17_to_october_8": period("2026-09-17", "2026-10-09"), "august_31_to_october_9": period("2026-08-31", "2026-10-10")}
daily = []
for d0, d1 in zip(days, days[1:]):
    pr = period(d0, d1)
    daily.append({"day": d0, "after": Decimal(pr["after_compounding_pct"]), "before": Decimal(pr["before_compounding_pct"])})
sep_days = [x for x in daily if "2026-09-01" <= x["day"] <= "2026-09-30"]
oct_days = [x for x in daily if "2026-10-01" <= x["day"] <= "2026-10-08"]
lo, hi = min(sep_days + oct_days, key=lambda x: x["after"]), max(sep_days + oct_days, key=lambda x: x["after"])
R["daily_range"] = {"lowest_day": lo["day"], "lowest_after_pct": f"{lo['after']:.2f}", "highest_day": hi["day"], "highest_after_pct": f"{hi['after']:.2f}",
                    "september_days_below_4_5": sum(1 for x in sep_days if x["after"] < Decimal("4.5")),
                    "september_days_above_5": sum(1 for x in sep_days if x["after"] > 5)}
for k, v in R["periods"].items():
    log(f"  {k.replace('_', ' ')}, {v['from']} to {v['to']}, {v['before_compounding_pct']}% a year before compounding, {v['after_compounding_pct']}% after")
log(f"  days from September 1 to October 8 ran from {lo['after']:.2f}% on {lo['day']} to {hi['after']:.2f}% on {hi['day']}")

# ---------------------------------------------------------------- rewards paid into the contract
log()
log("Rewards")
by_day = defaultdict(int)
for r in rewards:
    by_day[day_of(r["ts"])] += r["amount"]
per_day = [sum(1 for r in rewards if day_of(r["ts"]) == d) for d in sorted(by_day)]
gaps8 = [b["ts"] - a["ts"] for a, b in zip(rewards, rewards[1:])]
check("three reward payments a day, about eight hours apart", all(n == 3 for n in per_day) and all(28700 <= g <= 29000 for g in gaps8),
      f"{len(rewards)} payments, gaps of {min(gaps8)} to {max(gaps8)} seconds")
weeks = []
for r in rewards:
    if not weeks or abs(r["amount"] - weeks[-1]["amount"]) > 10 ** 18:
        weeks.append({"first": r["ts"], "amount": r["amount"], "payments": 0, "total": 0})
    weeks[-1]["payments"] += 1
    weeks[-1]["total"] += r["amount"]
full = weeks[1:-1]
check("each full week's 21 payments are the same amount, with the amount changing every seven days within an hour",
      all(w["payments"] == 21 for w in full) and all(abs((b["first"] - a["first"]) - 7 * DAY) < 3600 for a, b in zip(weeks[1:], weeks[2:])),
      f"{len(weeks)} amounts, changes on " + ", ".join(day_of(w["first"]) for w in weeks[1:]))
sep_rewards = sum(v for d, v in by_day.items() if d.startswith("2026-09"))
R["rewards"] = {"payments": len(rewards), "september_usde": f"{Decimal(sep_rewards) / E18:.2f}", "september_payments": sum(1 for r in rewards if day_of(r["ts"]).startswith("2026-09")),
                "smallest_per_payment_usde": f"{Decimal(min(w['amount'] for w in weeks)) / E18:.2f}", "largest_per_payment_usde": f"{Decimal(max(w['amount'] for w in weeks)) / E18:.2f}",
                "weeks": [{"from": iso(w["first"]), "per_payment_usde": f"{Decimal(w['amount']) / E18:.2f}", "payments": w["payments"],
                           "week_usde": f"{Decimal(w['amount']) / E18 * 21:.2f}"} for w in weeks]}
log(f"  {len(rewards)} payments, {Decimal(sep_rewards) / E18:,.2f} USDe in September")
# A loose check of the last full day against the contract's totalAssets read on October 12. The rewards paid that day over
# the contract's USDe should come close to the day's rate.
now = meta["now"]
total_assets = Decimal(now["total_assets_wei"]) / E18
last = period("2026-10-09", "2026-10-10")
vest_rate = Decimal(by_day["2026-10-09"]) / E18 / total_assets * 365 * 100
check("October 9's rewards over the contract's USDe come within 2% of that day's measured rate",
      abs(vest_rate / Decimal(last["before_compounding_pct"]) - 1) < Decimal("0.02"),
      f"{vest_rate:.3f}% against {last['before_compounding_pct']}% before compounding")
cta = Decimal(now["convert_to_assets_1e18"]) / E18
check("the contract's price on October 12 is above the price at 00:00 October 10 and close to its trend",
      P["2026-10-10"] < cta < P["2026-10-10"] * (1 + Decimal("0.06") * 3 / 365), f"{cta:.12f}, the explorer's latest block {now['block_before_calls']}")
# The explorer had refused a call at a past block, so the calls ran at its latest block, not pinned to one. totalAssets / totalSupply should equal
# convertToAssets to within rounding if all three came from one state. They do not, so the article uses only the price
# and the cooldown from this read, and the totalAssets checks here are loose.
ta_ts = (Decimal(now["total_assets_wei"]) + 1) / (Decimal(now["total_supply_wei"]) + 1)
R["contract_now"] = {"read_utc": now["read_utc"], "explorer_latest_block": now["block_before_calls"], "usde_per_susde": f"{cta:.6f}",
                     "total_assets_usde": f"{total_assets:.0f}", "total_supply_susde": f"{Decimal(now['total_supply_wei']) / E18:.0f}",
                     "total_assets_over_total_supply": f"{ta_ts:.6f}", "gap_from_convert_to_assets_pct": f"{(1 - ta_ts / cta) * 100:.3f}",
                     "cooldown_seconds": int(now["cooldown_duration_s"]), "cooldown_days": f"{Decimal(now['cooldown_duration_s']) / DAY:.2f}"}

# ---------------------------------------------------------------- what moved the rate, the payments over the USDe behind sUSDe
# The USDe behind all sUSDe rises with deposits and vested payments and falls with withdrawals. Start it from one unknown
# figure, C, at 00:00 UTC on August 31, add every deposit and vested payment, take away every withdrawal, and each
# day's vested payments over the day's average should give the day's rate. C is the average over the days of what each
# day's rate implies, and the test is how closely the 40 rates then match.
log()
log("What moved the rate")
VEST = 8 * 3600
T0 = int(next(m["ts"] for m in mids if m["date"] == "2026-08-31"))
T_END = int(next(m["ts"] for m in mids if m["date"] == "2026-10-11"))
flows = [(e["ts"], e["assets"] if e["kind"] == "d" else -e["assets"]) for e in events]   # every event, the small ones included
assert not any(t in (int(m["ts"]) for m in mids) for t, _ in flows)   # no event falls on a midnight's second, so the boundaries are clean


def g(p, t):
    """Wei of payment p vested by time t, evenly over the 8 hours after it."""
    return Decimal(p["amount"]) * min(max(Decimal(t - p["ts"]) / VEST, Decimal(0)), Decimal(1))


def g_integral(p, x0, x1):
    """The integral of g(p, t) over t from x0 to x1, in wei-seconds."""
    s = Decimal(0)
    lo, hi = max(x0, p["ts"]), min(x1, p["ts"] + VEST)
    if hi > lo:
        s += Decimal(p["amount"]) * (Decimal(hi - p["ts"]) ** 2 - Decimal(lo - p["ts"]) ** 2) / (2 * VEST)
    lo = max(x0, p["ts"] + VEST)
    if x1 > lo:
        s += Decimal(p["amount"]) * (x1 - lo)
    return s


def since_start(t):
    """Wei added to the USDe behind sUSDe from T0 to t, by deposits less withdrawals and by vested payments."""
    return Decimal(sum(f for s, f in flows if T0 <= s < t)) + sum(g(p, t) - g(p, T0) for p in rewards)


stake = []
for d0, d1 in zip(days, days[1:]):
    t0, t1 = int(next(m["ts"] for m in mids if m["date"] == d0)), int(next(m["ts"] for m in mids if m["date"] == d1))
    area = Decimal(sum(f for s, f in flows if T0 <= s < t0)) * (t1 - t0) + sum(Decimal(f) * (t1 - s) for s, f in flows if t0 <= s < t1)
    area += sum(g_integral(p, t0, t1) - g(p, T0) * (t1 - t0) for p in rewards)
    vested = sum(g(p, t1) - g(p, t0) for p in rewards)
    stake.append({"day": d0, "rel_avg": area / (t1 - t0), "vested": vested, "rate": (P[d1] / P[d0] - 1) * 365 * 100})
C = sum(x["vested"] * 365 * 100 / x["rate"] - x["rel_avg"] for x in stake) / len(stake)
for x in stake:
    x["avg"] = C + x["rel_avg"]
    x["error"] = x["vested"] * 365 * 100 / x["avg"] - x["rate"]
max_err = max(abs(x["error"]) for x in stake)
check("the payments over the USDe behind sUSDe match every day's rate to within 0.001 of a point", len(stake) == 40 and max_err < Decimal("0.001"),
      f"{len(stake)} days, largest gap {max_err:.6f} of a point, starting from {C / E18 / 10 ** 6:,.1f} million USDe at 00:00 UTC August 31")
end_model = C + since_start(T_END)
check("the USDe behind sUSDe at the end of October 10 is within 1% of the contract's totalAssets read on October 12",
      abs(end_model / E18 / total_assets - 1) < Decimal("0.01"), f"{end_model / E18 / 10 ** 6:,.1f} million against {total_assets / 10 ** 6:,.1f} million")
# How the fit tests the read. A deposit or withdrawal of 500,000 USDe missing from the records would leave the rebuilt
# USDe that much short or over from that moment on. Refit with the shift and see how far the largest gap moves.
MISS = 500000 * E18
probe = []
for when in ("2026-09-05", "2026-09-20", "2026-10-05"):
    t_m = ts(*map(int, when.split("-"))) + DAY // 2
    for sign in (1, -1):
        rel = []
        for x in stake:
            t0 = ts(*map(int, x["day"].split("-")))
            frac = Decimal(1) if t_m <= t0 else (Decimal(0) if t_m >= t0 + DAY else Decimal(t0 + DAY - t_m) / DAY)
            rel.append(x["rel_avg"] - sign * MISS * frac)
        c_ = sum(x["vested"] * 365 * 100 / x["rate"] - r for x, r in zip(stake, rel)) / len(stake)
        probe.append(max(abs(x["vested"] * 365 * 100 / (c_ + r) - x["rate"]) for x, r in zip(stake, rel)))
check("leaving out a deposit or withdrawal of 500,000 USDe at noon on September 5, 20 or October 5 widens the largest gap past 0.001 of a point",
      min(probe) > Decimal("0.001"), f"{min(probe):.5f} to {max(probe):.5f} of a point")
peak = max(stake, key=lambda x: x["avg"])
lowest_rate_day = R["daily_range"]["lowest_day"]


def week_days(first_day):
    """The UTC days that lie wholly inside the week whose first payment falls on first_day, so no other amount vests in them."""
    i = next(k for k, w in enumerate(weeks) if day_of(w["first"]) == first_day)
    w0, w1 = weeks[i]["first"], weeks[i + 1]["first"]
    inside = [x for x in daily if w0 <= ts(*map(int, x["day"].split("-"))) and ts(*map(int, x["day"].split("-"))) + DAY <= w1]
    return weeks[i], inside


wk_a, days_a = week_days("2026-09-04")
wk_b, days_b = week_days("2026-10-02")
check("the week from October 2 paid less a payment than the week from September 4 and a higher rate on every day",
      wk_b["amount"] < wk_a["amount"] and max(x["after"] for x in days_a) < min(x["after"] for x in days_b),
      f"{Decimal(wk_b['amount']) / E18:,.2f} against {Decimal(wk_a['amount']) / E18:,.2f} USDe, {min(x['after'] for x in days_b):.2f}% and up against "
      f"{max(x['after'] for x in days_a):.2f}% and down, days {days_b[0]['day']} to {days_b[-1]['day']} and {days_a[0]['day']} to {days_a[-1]['day']}")
R["staking"] = {"start_usde_august_31": f"{C / E18:.0f}", "days": len(stake), "largest_gap_points": f"{max_err:.6f}",
                "missing_500000_usde_largest_gap_points": [f"{min(probe):.4f}", f"{max(probe):.4f}"],
                "highest_day": peak["day"], "highest_average_usde": f"{peak['avg'] / E18:.0f}", "lowest_rate_day": lowest_rate_day,
                "october_9_average_usde": f"{next(x['avg'] for x in stake if x['day'] == '2026-10-09') / E18:.0f}",
                "end_october_10_usde": f"{end_model / E18:.0f}", "contract_october_12_usde": f"{total_assets:.0f}",
                "week_from_september_4": {"per_payment_usde": f"{Decimal(wk_a['amount']) / E18:.2f}", "days": [days_a[0]["day"], days_a[-1]["day"]],
                                          "highest_after_pct": f"{max(x['after'] for x in days_a):.2f}"},
                "week_from_october_2": {"per_payment_usde": f"{Decimal(wk_b['amount']) / E18:.2f}", "days": [days_b[0]["day"], days_b[-1]["day"]],
                                        "lowest_after_pct": f"{min(x['after'] for x in days_b):.2f}"}}
log(f"  the USDe behind sUSDe averaged most on {peak['day']}, {peak['avg'] / E18 / 10 ** 6:,.1f} million, and sUSDe's lowest day was {lowest_rate_day}")

# ---------------------------------------------------------------- EthenaPay's rates, as the Daily Boost review measured them
log()
log("EthenaPay")
check("the Pricing page, FAQ and Terms set Standard at 5% to $5,000 and Pro and VIP at 6% to $100,000 and $1,000,000",
      "Standard 5% a year on balance up to $5,000, Pro 6% up to $100,000, VIP 6% up to $1,000,000" in terms["caps"]["fact"])
rc = db["rate_changes"]
check("the Daily Boost review dates the rate change", rc == {"topup_last_1_0": "2026-09-15", "topup_first_0_5": "2026-09-16",
                                                           "base_last_4_0": "2026-09-16", "base_first_4_5": "2026-09-17"})
sep = db["september"]
check("the Daily Boost review's September total is the cash-flow review's", abs(Decimal(sep["base_paid"]) + Decimal(sep["topup_paid"]) - Decimal(cf["sep_rewards_paid"])) < Decimal("0.01"),
      f"{Decimal(sep['base_paid']) + Decimal(sep['topup_paid']):.2f} USDe")
d = {k: daily_share(k) for k in ("4.0", "4.5", "0.5", "1.0", "1.5", "2.0")}
check("the daily shares reproduce the Daily Boost review's models",
      all(abs(d[k] * 365 * 100 - Decimal(db["models_simple_pct"][m])) < Decimal("0.000001")
          for k, m in (("4.5", "base_4_5"), ("4.0", "base_4_0"), ("0.5", "standard_0_5"), ("1.0", "standard_1_0"), ("1.5", "six_1_5"), ("2.0", "six_2_0"))))
tiers = {"standard": {"cap": 5000, "boost": "0.5", "boost_before": "1.0"}, "pro": {"cap": 100000, "boost": "1.5", "boost_before": "2.0"},
         "vip": {"cap": 1000000, "boost": "1.5", "boost_before": "2.0"}}


def ethenapay_after(balance, tier, base="4.5", boost=None):
    t = tiers[tier]
    b = Decimal(balance)
    dd = d[base] + d[boost or t["boost"]] * min(b, t["cap"]) / b
    return after_compounding(dd)


R["ethenapay"] = {
    "standard_within_cap_after_pct": f"{ethenapay_after(1000, 'standard'):.2f}",
    "six_within_cap_after_pct": f"{ethenapay_after(1000, 'pro'):.2f}",
    "standard_within_cap_before_change_after_pct": f"{ethenapay_after(1000, 'standard', '4.0', '1.0'):.2f}",
    "six_within_cap_before_change_after_pct": f"{ethenapay_after(1000, 'pro', '4.0', '2.0'):.2f}",
    "base_until_sep_16_pct": "4.0", "base_from_sep_17_pct": "4.5",
    "september_all_balances_before_pct": f"{Decimal(sep['both_simple_pct']):.2f}",
    "october_1_to_8_all_balances_before_pct": f"{Decimal(db['october_avg_simple_pct']['both']):.2f}",
    "october_1_to_8_all_balances_after_pct": f"{Decimal(db['october_avg_compounded_pct']):.2f}",
    "cashflow_review_september_pct": f"{Decimal(cf['sep_reward_rate_pct']):.1f}",
    "above_cap_share_october_8_pct": f"{Decimal(db['day_detail']['2026-10-08']['above_cap_share_pct']):.1f}"}
check("the standard and 6% totals match the Daily Boost review's compounded figures",
      R["ethenapay"]["standard_within_cap_after_pct"] == f"{Decimal(db['total_compounded_pct']['standard']):.2f}"
      and R["ethenapay"]["six_within_cap_after_pct"] == f"{Decimal(db['total_compounded_pct']['six']):.2f}")
E = R["ethenapay"]
log(f"  within the caps {E['standard_within_cap_after_pct']}% and {E['six_within_cap_after_pct']}% after compounding, base {E['base_until_sep_16_pct']}% then {E['base_from_sep_17_pct']}%")
log(f"  all balances, September {E['september_all_balances_before_pct']}% before compounding, October 1 to 8 {E['october_1_to_8_all_balances_before_pct']}% and {E['october_1_to_8_all_balances_after_pct']}%")

# ---------------------------------------------------------------- where a balance stands against sUSDe over the same days
# EthenaPay's rates held from September 17, so the like-for-like sUSDe rate is the one from 00:00 September 17 to 00:00
# October 9. Every balance comes from the unrounded growth. sUSDe's daily share is its growth over the period to the
# power 1 / days, less 1.


def susde_share(d0, d1):
    n = (datetime.fromisoformat(d1) - datetime.fromisoformat(d0)).days
    return root(P[d1] / P[d0], n) - 1


def break_even(share):
    return {tier: Decimal(t["cap"]) * d[t["boost"]] / (share - d["4.5"]) for tier, t in tiers.items()}


s_share = susde_share("2026-09-17", "2026-10-09")
s_after = after_compounding(s_share)
be = break_even(s_share)
for tier, t in tiers.items():
    check(f"{tier}, the balance where EthenaPay's rate meets sUSDe's lies above the cap", be[tier] > t["cap"] and abs(ethenapay_after(be[tier], tier) - s_after) < Decimal("1e-9"),
          f"{be[tier]:,.0f} USDe")
R["break_even"] = {"susde_period": "september_17_to_october_8", "susde_after_pct": f"{s_after:.4f}", **{k: f"{v:.0f}" for k, v in be.items()}}
R["break_even_sensitivity"] = {}
for name, (d0, d1) in {"september": ("2026-09-01", "2026-10-01"), "october_1_to_8": ("2026-10-01", "2026-10-09"),
                       "august_31_to_october_9": ("2026-08-31", "2026-10-10")}.items():
    sh = susde_share(d0, d1)
    R["break_even_sensitivity"][name] = {"susde_after_pct": f"{after_compounding(sh):.4f}", **{k: f"{v:.0f}" for k, v in break_even(sh).items()}}
examples = [("standard", 1000), ("standard", 5000), ("standard", 10000), ("standard", 25000), ("pro", 100000), ("pro", 250000), ("pro", 1000000), ("vip", 1000000), ("vip", 5000000)]
R["examples"] = [{"tier": t, "balance": b, "ethenapay_after_pct": f"{ethenapay_after(b, t):.2f}"} for t, b in examples]
log(f"  balances where EthenaPay's rates from September 17 meet sUSDe's {s_after:.4f}% for the same days, " + ", ".join(f"{k} {v:,.0f}" for k, v in be.items()))

# ---------------------------------------------------------------- sUSDe's daily rate against EthenaPay's, day by day
rows_vs = []
for x in sep_days + oct_days:
    base = "4.0" if x["day"] <= rc["base_last_4_0"] else "4.5"
    boost_std = "1.0" if x["day"] <= rc["topup_last_1_0"] else "0.5"
    boost_six = "2.0" if x["day"] <= rc["topup_last_1_0"] else "1.5"
    rows_vs.append({"day": x["day"], "susde": x["after"], "base": Decimal(base), "standard": ethenapay_after(1000, "standard", base, boost_std),
                    "six": ethenapay_after(1000, "pro", base, boost_six)})
big_weeks = sorted(weeks, key=lambda w: w["amount"])[-2:]
in_big = lambda day: any(w["first"] <= ts(*map(int, day.split("-"))) + DAY - 1 and ts(*map(int, day.split("-"))) < w["first"] + 7 * DAY for w in big_weeks)
R["days_compared"] = {"days": len(rows_vs), "susde_above_base": sum(1 for r in rows_vs if r["susde"] > r["base"]),
                      "susde_below_six": sum(1 for r in rows_vs if r["susde"] < r["six"]),
                      "susde_above_standard": sum(1 for r in rows_vs if r["susde"] > r["standard"]),
                      "susde_above_standard_days": [r["day"] for r in rows_vs if r["susde"] > r["standard"]],
                      "september_16_standard_pct": f"{ethenapay_after(1000, 'standard', '4.0', '0.5'):.2f}",
                      "september_16_six_pct": f"{ethenapay_after(1000, 'pro', '4.0', '1.5'):.2f}",
                      "lowest_from_september_17_pct": f"{min(r['susde'] for r in rows_vs if r['day'] >= '2026-09-17'):.2f}",
                      "above_standard_in_two_largest_weeks": sum(1 for r in rows_vs if r["susde"] > r["standard"] and in_big(r["day"])),
                      "two_largest_weeks_from": [iso(w["first"]) for w in sorted(big_weeks, key=lambda w: w["first"])]}
# The Standard rate dipped on September 16 alone. Count the days above it at its usual rate in the two largest weeks,
# and the margin on October 8, from unrounded rates.
usual = {r["day"] for r in rows_vs if r["day"] != "2026-09-16"}
dc = R["days_compared"]
dc["above_standard_at_usual_rate_in_two_largest_weeks"] = [r["day"] for r in rows_vs if r["susde"] > r["standard"] and in_big(r["day"]) and r["day"] in usual]
dc["above_standard_other_days"] = [x for x in dc["susde_above_standard_days"] if x not in dc["above_standard_at_usual_rate_in_two_largest_weeks"]]
dc["october_8_lead_points"] = f"{after_compounding(susde_share('2026-10-08', '2026-10-09')) - ethenapay_after(1000, 'standard'):.4f}"
check("the days above the Standard rate split into 8 in the two largest weeks and 2 others, September 16 and October 8",
      len(dc["above_standard_at_usual_rate_in_two_largest_weeks"]) == 8 and dc["above_standard_other_days"] == ["2026-09-16", "2026-10-08"])
check("sUSDe paid more than the base rate and less than the Pro and VIP rate on every day compared",
      R["days_compared"]["susde_above_base"] == len(rows_vs) == R["days_compared"]["susde_below_six"] == 38)
log(f"  sUSDe above the Standard rate on {R['days_compared']['susde_above_standard']} of {len(rows_vs)} days")

# ---------------------------------------------------------------- tables
if failures:
    log()
    log(f"{len(failures)} checks failed, nothing written")
    (HERE / "run_log_failed.txt").write_text("\n".join(log_lines) + "\n")
    sys.exit(1)
OUT.mkdir(exist_ok=True)
with open(OUT / "susde_daily.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["day", "price_at_00_00_utc", "next_price", "before_compounding_pct", "after_compounding_pct", "rewards_paid_usde",
                "rewards_vested_usde", "usde_behind_susde_day_average", "rate_from_rewards_before_compounding_pct"])
    for x, s, (d0, d1) in zip(daily, stake, zip(days, days[1:])):
        assert x["day"] == s["day"] == d0
        w.writerow([x["day"], f"{P[d0]:.12f}", f"{P[d1]:.12f}", f"{x['before']:.4f}", f"{x['after']:.4f}", f"{Decimal(by_day[x['day']]) / E18:.2f}",
                    f"{s['vested'] / E18:.2f}", f"{s['avg'] / E18:.0f}", f"{s['vested'] * 365 * 100 / s['avg']:.4f}"])
with open(OUT / "periods.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["period", "from_00_00_utc", "to_00_00_utc", "days", "growth_pct", "before_compounding_pct", "after_compounding_pct"])
    for k, v in R["periods"].items():
        w.writerow([k, v["from"], v["to"], v["days"], v["growth_pct"], v["before_compounding_pct"], v["after_compounding_pct"]])
with open(OUT / "balances.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["tier", "balance_usde", "ethenapay_after_compounding_pct", "susde_september_17_to_october_8_after_compounding_pct"])
    for x in R["examples"]:
        w.writerow([x["tier"], x["balance"], x["ethenapay_after_pct"], f"{s_after:.2f}"])   # sUSDe from September 17 to October 8
with open(OUT / "reward_weeks.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["first_payment_utc", "per_payment_usde", "payments_read", "week_at_21_payments_usde"])
    for x in R["rewards"]["weeks"]:
        w.writerow([x["from"], x["per_payment_usde"], x["payments"], x["week_usde"]])
with open(OUT / "chart_points.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["day", "susde_after_compounding_pct", "ethenapay_base_pct", "ethenapay_standard_pct", "ethenapay_six_pct"])
    for r in rows_vs:
        w.writerow([r["day"], f"{r['susde']:.4f}", f"{r['base']}", f"{r['standard']:.4f}", f"{r['six']:.4f}"])
R["checks_passed"] = sum(1 for l in log_lines if l.startswith("ok"))
R["read_through"] = meta["logs_to_before"]
(OUT / "results.json").write_text(json.dumps(R, indent=1) + "\n")
log()
log(f"All {R['checks_passed']} checks passed. Tables written to out/.")
(OUT / "run_log.txt").write_text("\n".join(log_lines) + "\n")
