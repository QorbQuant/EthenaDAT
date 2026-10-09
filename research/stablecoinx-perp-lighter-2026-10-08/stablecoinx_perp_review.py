#!/usr/bin/env python3
"""Lighter's STABLECOINX perpetual against USDE on Nasdaq, August 26 to October 8, 2026.

Reads the files in inputs/ and runs every check. If any check fails it stops before
writing anything, so out/ keeps the tables of the last clean run. Otherwise it rewrites
the tables in out/. Python 3 standard library only. It makes no network requests.

Times. Lighter's data is in UTC. Every date in this window fell in daylight saving
time, so New York time was UTC minus four hours. Nasdaq's regular session ran from
9:30 am to 4:00 pm New York time, 13:30 to 20:00 UTC. Lighter's hourly candles carry
the start of their hour, so the candle stamped 19:00 UTC closes at 20:00 UTC, the
moment of the Nasdaq close. "The mark at T" below means the close of the hourly mark
candle that ends at T.

The points used for each stretch between sessions, in New York time:
  4 pm  the close (20:00 UTC)
  8 pm  the end of USDE's after-hours trading in Yahoo Finance's hourly data (00:00 UTC
        the next calendar day)
  4 am  the start of USDE's pre-market trading in that data on the next trading day
        (08:00 UTC)
  9 am  half an hour before the open (13:00 UTC)
The weekend window runs from 8 pm on Friday to 4 am on the next trading day, the hours
with no USDE trading in Yahoo's data. The session hours are 9 am to 4 pm New York time
(13:00 to 20:00 UTC) on the 31 trading days.

USDE's open and close are the daily opening and closing prices in S&P Global Market
Intelligence's data through StockAnalysis, checked against Yahoo Finance.
"""
import csv
import hashlib
import json
import os
import random
import statistics
import sys
from datetime import date, datetime, timedelta, timezone
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, "inputs")
OUT = os.path.join(HERE, "out")
UTC = timezone.utc
HOUR = timedelta(hours=1)
FIRST_DAY = date(2026, 8, 26)
LAST_DAY = date(2026, 10, 8)
CUT = datetime(2026, 10, 9, tzinfo=UTC)
FIRST_TRADE_HOUR = datetime(2026, 8, 26, 18, tzinfo=UTC)
FIRST_MARK_HOUR = datetime(2026, 8, 26, 17, tzinfo=UTC)
NY = timedelta(hours=-4)  # New York daylight time, valid for every date here
SHUFFLES, SEED = 20_000, 20261009

LOG = []
FAILED = []


def say(msg=""):
    LOG.append(msg)
    print(msg)


def check(name, ok, detail=""):
    say(f"[{'ok' if ok else 'FAIL'}] {name}{' . ' + detail if detail else ''}")
    if not ok:
        FAILED.append(name)


def read_csv(name):
    with open(os.path.join(INP, name), newline="") as f:
        return list(csv.DictReader(f))


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def num(v):
    return float(v) if v not in ("", None) else None


def utc(ms=None, s=None):
    return datetime.fromtimestamp((ms / 1000) if ms is not None else s, UTC)


def pct(x, d=2):
    return f"{x * 100:.{d}f}%"


def r6(x):
    return None if x is None else round(x, 6)


def write_csv(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def coin(k, n):
    """Chance that n fair coin tosses land at least as far from n/2 as k, both sides counted."""
    d = abs(k - n / 2)
    return min(1.0, sum(comb(n, i) for i in range(n + 1) if abs(i - n / 2) >= d) / 2 ** n)


def corr(xs, ys):
    mx, my = statistics.mean(xs), statistics.mean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return sxy / (sxx * syy) ** 0.5, sxy / sxx


def ny(t):
    return f"{t + NY:%Y-%m-%d %H:%M}"


say("STABLECOINX perpetual on Lighter against USDE on Nasdaq")
say(f"Sessions {FIRST_DAY} to {LAST_DAY}. Lighter hourly data before {CUT:%Y-%m-%d %H:%M} UTC")
say()

# ---------------------------------------------------------------- inputs and their integrity
facts = {r["key"]: r for r in read_csv("filing_facts.csv")}
FREELY_TRADABLE = int(facts["freely_tradable_aug28"]["value"])
CLASS_A_OCT8 = int(facts["dashboard_class_a_oct8"]["value"])
check("share counts read from filing_facts.csv", FREELY_TRADABLE == 19_063_653 and CLASS_A_OCT8 == 24_139_375)

manifest = read_csv("manifest.csv")
bad = [m["file"] for m in manifest if sha256(os.path.join(INP, m["file"])) != m["sha256"]]
check("every input matches the SHA-256 in manifest.csv", not bad and len(manifest) >= 13,
      f"{len(manifest)} files" + (f", mismatched {bad}" if bad else ""))

fetch_log = read_csv("lighter_fetch_log.csv")
check("every Lighter request returned HTTP 200", all(r["status"] == "200" for r in fetch_log),
      f"{len(fetch_log)} requests, {fetch_log[0]['fetched_at']} to {fetch_log[-1]['fetched_at']}")

details = json.load(open(os.path.join(INP, "lighter_orderbookdetails.json")))
m229 = next(v for v in details["order_book_details"] if v["market_id"] == 229)
oracle = json.load(open(os.path.join(INP, "lighter_priceoracleinfo.json")))
o229 = next(v for v in oracle["markets"] if v["symbol"] == "STABLECOINX")
created = utc(ms=int(m229["created_at"]))
check("the market snapshot is STABLECOINX, a perpetual, active, created on August 26",
      m229["symbol"] == "STABLECOINX" and m229["market_type"] == "perp" and m229["status"] == "active"
      and created.date() == FIRST_DAY and created.hour == 17,
      f"created {created:%Y-%m-%d %H:%M:%S} UTC")
market = {
    "created_utc": created.isoformat(),
    "taker_fee_pct": float(m229["taker_fee"]), "maker_fee_pct": float(m229["maker_fee"]),
    "initial_margin_pct": m229["default_initial_margin_fraction"] / 100,
    "maintenance_margin_pct": m229["maintenance_margin_fraction"] / 100,
    "max_leverage": 10000 / m229["default_initial_margin_fraction"],
    "base_interest_rate_pct_per_8h": float(m229["base_interest_rate"]),
    "funding_premium_multiplier": m229["funding_premium_multiplier"] / 100,
    "funding_clamp_big_pct_per_8h": float(m229["funding_clamp_big"]),
    "trading_hours": m229["market_config"]["trading_hours"],
    "open_interest_contracts": float(m229["open_interest"]),
    "mark_price": float(m229["mark_price"]), "index_price": float(m229["index_price"]),
    "snapshot_utc": "2026-10-09T13:30:27Z",
}
check("snapshot terms, no trading fee, 20% initial margin, no trading-hours limit, RWA funding multiplier",
      market["taker_fee_pct"] == 0 and market["maker_fee_pct"] == 0 and market["initial_margin_pct"] == 20
      and market["trading_hours"] == "" and market["funding_premium_multiplier"] == 0.5,
      f"maintenance margin {market['maintenance_margin_pct']}%, base interest "
      f"{market['base_interest_rate_pct_per_8h']}% per 8 hours")
oracle_at = utc(ms=oracle["computed_at_ms"])
cap_pct = o229["index"]["price_cap_bps"] / 100
check("price-source snapshot shows the index from Pyth, not internal, with a cap of 40% around the reference price",
      o229["index"]["median_sources"] == ["pythlazer"] and o229["index"]["using_internal_price"] is False
      and cap_pct == 40, f"read {oracle_at:%Y-%m-%d %H:%M:%S} UTC, reference {o229['index']['price_cap_reference_price']}")
say(f"      the docs set the cap at the last oracle price times (1 +/- 1/L); at the snapshot's maximum leverage of "
    f"{market['max_leverage']:.0f} that would be {100 / market['max_leverage']:.0f}%, against {cap_pct:.0f}% in the snapshot")

# ---------------------------------------------------------------- Lighter hourly series
candles = {}
for r in read_csv("lighter_candles_1h.csv"):
    candles[utc(ms=int(r["t_ms"]))] = {k: num(r[k]) for k in ("o", "h", "l", "c", "v", "V")}
mark = {}
for r in read_csv("lighter_mark_1h.csv"):
    t = utc(ms=int(r["t_ms"]))
    mark[t] = {k: num(r[k]) for k in ("o", "h", "l", "c")}
funding = []
for r in read_csv("lighter_funding_1h.csv"):
    rate, value = num(r["rate"]) or 0.0, num(r["value"]) or 0.0
    sign = 1 if r["direction"] == "long" else -1
    funding.append({"t": utc(s=int(r["timestamp"])), "rate": rate, "value": value, "direction": r["direction"],
                    "signed": sign * rate, "signed_value": sign * value})

ct, mt, ft = sorted(candles), sorted(mark), [f["t"] for f in funding]
hours = int((CUT - FIRST_TRADE_HOUR) / HOUR)
idle = [t for t in ct if not candles[t]["v"]]
check("a trade candle for every hour from 18:00 UTC on August 26 to the cutoff",
      ct[0] == FIRST_TRADE_HOUR and len(ct) == hours and all(b - a == HOUR for a, b in zip(ct, ct[1:])),
      f"{len(ct)} hours, {len(idle)} with no trade")
check("a mark price candle for every hour from 17:00 UTC on August 26 to the cutoff",
      mt[0] == FIRST_MARK_HOUR and len(mt) == int((CUT - FIRST_MARK_HOUR) / HOUR)
      and all(b - a == HOUR for a, b in zip(mt, mt[1:])), f"{len(mt)} hours")
check("one funding an hour from 18:00 UTC on August 26 to 00:00 UTC on October 9, with a known side",
      ft[0] == FIRST_TRADE_HOUR and ft[-1] == CUT and all(b - a == HOUR for a, b in zip(ft, ft[1:]))
      and {f["direction"] for f in funding} <= {"long", "short"} and all(f["rate"] >= 0 for f in funding),
      f"{len(funding)} fundings")

# Daily candles summarize the hourly ones. An hour with no trade repeats the last price.
# Lighter's daily high and low sometimes include that repeated price and sometimes do not,
# so each is compared with both the traded hours and all the hours of the day.
day_c = {utc(ms=int(r["t_ms"])).date(): {k: num(r[k]) for k in ("o", "h", "l", "c", "v", "V")}
         for r in read_csv("lighter_candles_1d.csv")}
agg = {}
for t in ct:
    c = candles[t]
    a = agg.setdefault(t.date(), {"c": None, "h": None, "l": None, "ha": c["h"], "la": c["l"], "v": 0.0, "V": 0.0,
                                  "idle": 0, "hours": 0})
    a["c"] = c["c"]
    a["ha"] = max(a["ha"], c["h"])
    a["la"] = min(a["la"], c["l"])
    a["v"] += c["v"] or 0.0
    a["V"] += c["V"] or 0.0
    a["hours"] += 1
    if c["v"]:
        a["h"] = c["h"] if a["h"] is None else max(a["h"], c["h"])
        a["l"] = c["l"] if a["l"] is None else min(a["l"], c["l"])
    else:
        a["idle"] += 1
check("daily trade candles have the same days, closes and volumes as the hours they cover",
      sorted(day_c) == sorted(agg)
      and all(abs(day_c[d]["c"] - agg[d]["c"]) < 1e-9 and abs(day_c[d]["V"] - agg[d]["V"]) <= 0.01
              and abs(day_c[d]["v"] - agg[d]["v"]) <= 0.01 for d in agg), f"{len(agg)} days")


def near(x, *ys):
    return any(y is not None and abs(x - y) < 1e-9 for y in ys)


hl_ok = all(near(day_c[d]["h"], agg[d]["h"], agg[d]["ha"]) and near(day_c[d]["l"], agg[d]["l"], agg[d]["la"]) for d in agg)
carried = sum(1 for d in agg if not (near(day_c[d]["h"], agg[d]["h"]) and near(day_c[d]["l"], agg[d]["l"])))
check("each daily high and low equals that of the traded hours or of all the hours", hl_ok,
      f"{carried} days include a repeated price")
day_m = {utc(ms=int(r["t_ms"])).date(): num(r["c"]) for r in read_csv("lighter_mark_1d.csv")}
check("each daily mark close equals the last hourly mark close of that day",
      all(abs(day_m[d] - mark[max(t for t in mt if t.date() == d)]["c"]) < 1e-9 for d in day_m))

# Lighter's own daily volume figure against the candles. It is never lower and often higher.
metrics = {utc(s=int(r["timestamp"])).date(): {"oi": num(r["open_interest"]), "volume": num(r["volume"])}
           for r in read_csv("lighter_metrics_1d.csv")}
diff = {d: metrics[d]["volume"] - agg[d]["V"] for d in agg}
vol_metric = {
    "days": len(diff), "metric_total_usd": sum(metrics[d]["volume"] for d in agg), "candle_total_usd": sum(agg[d]["V"] for d in agg),
    "days_higher": sum(1 for v in diff.values() if v > 0.005), "days_lower": sum(1 for v in diff.values() if v < -0.005),
    "days_over_1000": sum(1 for v in diff.values() if v > 1000),
    "largest_day": str(max(diff, key=diff.get)), "largest_usd": max(diff.values()),
}
vol_metric["excess_usd"] = vol_metric["metric_total_usd"] - vol_metric["candle_total_usd"]
check("Lighter's daily volume figure covers every day and is never below the candles",
      set(agg) <= set(metrics) and vol_metric["days_lower"] == 0,
      f"higher on {vol_metric['days_higher']} of {vol_metric['days']} days, by over $1,000 on "
      f"{vol_metric['days_over_1000']}, total ${vol_metric['metric_total_usd']:,.0f} against ${vol_metric['candle_total_usd']:,.0f}")

# Lighter computes each funding payment from the index, which the inputs do not hold, so the check
# compares the median price implied by the payments with the mark and reports the spread.
ratios = [(f["value"] / (f["rate"] / 100)) / mark[f["t"] - HOUR]["c"] for f in funding if f["rate"] > 0]
fund_check = {"payments": len(ratios), "median_ratio": statistics.median(ratios),
              "over_2pct": sum(1 for x in ratios if abs(x - 1) > 0.02), "over_5pct": sum(1 for x in ratios if abs(x - 1) > 0.05),
              "min_ratio": min(ratios), "max_ratio": max(ratios)}
check("the median price implied by the funding payments is within 2% of the mark",
      abs(fund_check["median_ratio"] - 1) < 0.02,
      f"median {fund_check['median_ratio']:.4f}, with {fund_check['over_2pct']} of {fund_check['payments']} payments more than 2% "
      f"from the mark, {fund_check['over_5pct']} more than 5%, range {fund_check['min_ratio']:.3f} to {fund_check['max_ratio']:.3f}")

# ---------------------------------------------------------------- USDE
sa = {date.fromisoformat(r["date"]): r for r in read_csv("usde_daily_spglobal_stockanalysis.csv")}
yd = {date.fromisoformat(r["date"]): r for r in read_csv("usde_daily_yahoo.csv")}
sessions = sorted(d for d in sa if FIRST_DAY <= d <= LAST_DAY)
check("31 sessions from August 26 to October 8, the same days in both daily sources, none on a weekend",
      len(sessions) == 31 and sessions == sorted(yd) and all(d.weekday() < 5 for d in sessions))
check("the two daily sources give the same open and close, to the cent, for every session",
      all(abs(float(sa[d][k]) - round(float(yd[d][k]), 2)) < 0.005 for d in sessions for k in ("open", "close")))
usde = {d: {"open": float(sa[d]["open"]), "close": float(sa[d]["close"]), "volume": int(sa[d]["volume"])} for d in sessions}

yh = {}
bad_times = []
for r in read_csv("usde_hourly_yahoo.csv"):
    yh[r["new_york"]] = r
    if f"{utc(s=int(r['t'])) + NY:%Y-%m-%d %H:%M}" != r["new_york"]:
        bad_times.append(r["new_york"])
check("every Yahoo hourly bar's New York time matches its timestamp", not bad_times, f"{len(yh)} bars")
hours_seen = sorted({k[11:] for k in yh})
check("Yahoo's hourly bars run from 04:00 to 19:00 New York time, with none from 20:00 to 03:00",
      hours_seen[0] == "04:00" and hours_seen[-1] == "19:00", f"bar starts {hours_seen}")
pre = {d: yh.get(f"{d} 08:00") for d in sessions}
post = {d: yh.get(f"{d} 19:00") for d in sessions}
check("Yahoo's hourly data has a pre-market bar ending 9 am for every session",
      all(pre[d] and pre[d]["close"] for d in sessions))
missing_post = [str(d) for d in sessions if not (post[d] and post[d]["close"])]
check("Yahoo's hourly data has an after-hours bar ending 8 pm for every session but the last two",
      missing_post == ["2026-10-07", "2026-10-08"], f"missing {missing_post}")


def mark_at(t):
    return mark[t - HOUR]["c"]


def trade_at(t):
    """Last traded price before t, and the hour it traded."""
    u = t - HOUR
    while u >= FIRST_TRADE_HOUR:
        if candles[u]["v"]:
            return candles[u]["c"], u
        u -= HOUR
    return None, None


SESSION = {datetime(d.year, d.month, d.day, h, tzinfo=UTC) for d in sessions for h in range(13, 20)}

# ---------------------------------------------------------------- at the close
close_rows = []
for d in sessions:
    t4 = datetime(d.year, d.month, d.day, 20, tzinfo=UTC)
    m = mark_at(t4)
    tr, tr_hour = trade_at(t4)
    c = usde[d]["close"]
    close_rows.append({"date": d, "close": c, "mark": m, "trade": tr, "trade_hour": tr_hour,
                       "gap_mark": m / c - 1, "gap_trade": tr / c - 1})
abs_mark = [abs(r["gap_mark"]) for r in close_rows]
abs_trade = [abs(r["gap_trade"]) for r in close_rows]
stale = sum(1 for r in close_rows if r["trade_hour"] != datetime(r["date"].year, r["date"].month, r["date"].day, 19, tzinfo=UTC))
close_summary = {
    "sessions": len(close_rows),
    "mark_median": statistics.median(abs_mark), "mark_mean": statistics.mean(abs_mark), "mark_max": max(abs_mark),
    "mark_within_1pct": sum(1 for x in abs_mark if x <= 0.01), "mark_within_half_pct": sum(1 for x in abs_mark if x <= 0.005),
    "trade_median": statistics.median(abs_trade), "trade_mean": statistics.mean(abs_trade), "trade_max": max(abs_trade),
    "trade_within_1pct": sum(1 for x in abs_trade if x <= 0.01), "trade_within_2pct": sum(1 for x in abs_trade if x <= 0.02),
    "last_trade_earlier_than_3pm_hour": stale,
    "mark_max_date": str(max(close_rows, key=lambda r: abs(r["gap_mark"]))["date"]),
    "trade_max_date": str(max(close_rows, key=lambda r: abs(r["gap_trade"]))["date"]),
    "trade_max_hour_new_york": ny(max(close_rows, key=lambda r: abs(r["gap_trade"]))["trade_hour"]),
}
say()
say("At the 4 pm close")
say(f"  mark: median gap {pct(close_summary['mark_median'])}, largest {pct(close_summary['mark_max'])} on "
    f"{close_summary['mark_max_date']}, within 1% on {close_summary['mark_within_1pct']} of 31, within 0.5% on "
    f"{close_summary['mark_within_half_pct']}")
say(f"  last trade: median gap {pct(close_summary['trade_median'])}, largest {pct(close_summary['trade_max'])} on "
    f"{close_summary['trade_max_date']} (hour starting {close_summary['trade_max_hour_new_york']} New York), within 1% on "
    f"{close_summary['trade_within_1pct']}, within 2% on {close_summary['trade_within_2pct']}; sessions with no trade in "
    f"the 3 pm hour {stale}")

# ---------------------------------------------------------------- between sessions
gap_rows = []
for d, d2 in zip(sessions, sessions[1:]):
    t_close = datetime(d.year, d.month, d.day, 20, tzinfo=UTC)
    t_8pm = t_close + 4 * HOUR
    t_4am = datetime(d2.year, d2.month, d2.day, 8, tzinfo=UTC)
    t_9am = t_4am + 5 * HOUR
    days = (d2 - d).days
    kind = "weeknight" if days == 1 else ("weekend" if days == 3 else "holiday weekend")
    c, o = usde[d]["close"], usde[d2]["open"]
    m4pm, m8pm, m4am, m9am = mark_at(t_close), mark_at(t_8pm), mark_at(t_4am), mark_at(t_9am)
    dark = [t for t in ct if t_8pm <= t < t_4am]
    dark_m = [t for t in mt if t_8pm <= t < t_4am]
    hi_t = max(dark_m, key=lambda t: mark[t]["h"])
    lo_t = min(dark_m, key=lambda t: mark[t]["l"])
    y8 = float(post[d]["close"]) if post[d] and post[d]["close"] else None
    y9 = float(pre[d2]["close"])
    gap_rows.append({
        "from": d, "to": d2, "kind": kind, "close": c, "open": o,
        "m4pm": m4pm, "m8pm": m8pm, "m4am": m4am, "m9am": m9am, "y8pm": y8, "y9am": y9,
        "a": m8pm / m4pm - 1, "b": m4am / m8pm - 1, "c": m9am / m4am - 1,
        "actual": o / c - 1, "implied_4am": m4am / c - 1, "implied_9am": m9am / c - 1,
        "near_4am": abs(o - m4am) < abs(o - c), "near_9am": abs(o - m9am) < abs(o - c),
        "same_4am": (o - c) * (m4am - c) > 0, "same_9am": (o - c) * (m9am - c) > 0,
        "perp_beats_premarket": abs(o - m9am) < abs(o - y9), "near_premarket": abs(o - y9) < abs(o - c),
        "near_after_hours": (abs(o - y8) < abs(o - c)) if y8 else None,
        "perp_4am_beats_after_hours": (abs(o - m4am) < abs(o - y8)) if y8 else None,
        "miss_close": abs(o - c) / c, "miss_4am": abs(o - m4am) / c, "miss_9am": abs(o - m9am) / c,
        "miss_premarket": abs(o - y9) / c, "miss_after_hours": (abs(o - y8) / c) if y8 else None,
        "dark_usd": sum(candles[t]["V"] or 0 for t in dark), "dark_contracts": sum(candles[t]["v"] or 0 for t in dark),
        "dark_hours": len(dark), "dark_traded_hours": sum(1 for t in dark if candles[t]["v"]),
        "dark_trade_high": max((candles[t]["h"] for t in dark if candles[t]["v"]), default=None),
        "swing_high": mark[hi_t]["h"], "swing_high_hour": hi_t, "swing_low": mark[lo_t]["l"], "swing_low_hour": lo_t,
        "swing_up": mark[hi_t]["h"] / c - 1, "swing_down": mark[lo_t]["l"] / c - 1,
        "vs_after_hours": (m8pm / y8 - 1) if y8 else None, "vs_premarket": m9am / y9 - 1,
    })
check("30 stretches between sessions, 24 weeknights, 5 weekends and the Labor Day weekend",
      len(gap_rows) == 30 and sum(g["kind"] == "weeknight" for g in gap_rows) == 24
      and sum(g["kind"] == "weekend" for g in gap_rows) == 5 and sum(g["kind"] == "holiday weekend" for g in gap_rows) == 1)
check("no opening price equals the mark it is compared with, so no stretch is a tie",
      all(g["open"] != g[k] for g in gap_rows for k in ("m4am", "m9am", "y9am")))


def unrelated(rows, key):
    """Expected counts if each opening move were paired with the perp's move from a stretch chosen at random.
    Averages every pairing, so it needs no random numbers."""
    a = [g["actual"] for g in rows]
    p = [g[f"implied_{key}"] for g in rows]
    n = len(rows)
    return (sum(1 for x in a for y in p if abs(x - y) < abs(x)) / n,
            sum(1 for x in a for y in p if x * y > 0) / n)


def shuffle_tail(rows, key):
    """Share of shuffles of the perp's moves across stretches with at least as many nearer opens, and at least as many
    moves in the same direction, as observed. Run log only."""
    a = [g["actual"] for g in rows]
    p = [g[f"implied_{key}"] for g in rows]
    obs_near = sum(1 for x, y in zip(a, p) if abs(x - y) < abs(x))
    obs_same = sum(1 for x, y in zip(a, p) if x * y > 0)
    rng = random.Random(SEED)
    q = p[:]
    hits_near = hits_same = 0
    for _ in range(SHUFFLES):
        rng.shuffle(q)
        hits_near += sum(1 for x, y in zip(a, q) if abs(x - y) < abs(x)) >= obs_near
        hits_same += sum(1 for x, y in zip(a, q) if x * y > 0) >= obs_same
    return hits_near / SHUFFLES, hits_same / SHUFFLES


def summarize(rows):
    s = {"count": len(rows)}
    for k in ("4am", "9am"):
        s[f"near_{k}"] = sum(g[f"near_{k}"] for g in rows)
        s[f"same_direction_{k}"] = sum(g[f"same_{k}"] for g in rows)
        s[f"coin_{k}"] = coin(s[f"near_{k}"], len(rows))
        s[f"mean_miss_{k}"] = statistics.mean(g[f"miss_{k}"] for g in rows)
        s[f"median_miss_{k}"] = statistics.median(g[f"miss_{k}"] for g in rows)
        s[f"unrelated_near_{k}"], s[f"unrelated_same_{k}"] = unrelated(rows, k)
        if len(rows) > 2:
            s[f"corr_{k}"], s[f"slope_{k}"] = corr([g[f"implied_{k}"] for g in rows], [g["actual"] for g in rows])
    s["mean_miss_close"] = statistics.mean(g["miss_close"] for g in rows)
    s["median_miss_close"] = statistics.median(g["miss_close"] for g in rows)
    s["mean_miss_premarket"] = statistics.mean(g["miss_premarket"] for g in rows)
    s["median_miss_premarket"] = statistics.median(g["miss_premarket"] for g in rows)
    s["perp_9am_nearer_than_premarket"] = sum(g["perp_beats_premarket"] for g in rows)
    s["near_premarket"] = sum(g["near_premarket"] for g in rows)
    ah = [g for g in rows if g["y8pm"] is not None]
    s["after_hours_count"] = len(ah)
    s["near_after_hours"] = sum(g["near_after_hours"] for g in ah)
    s["perp_4am_nearer_than_after_hours"] = sum(g["perp_4am_beats_after_hours"] for g in ah)
    s["after_hours_nearer_than_perp_4am"] = sum(abs(g["open"] - g["y8pm"]) < abs(g["open"] - g["m4am"]) for g in ah)
    s["mean_miss_after_hours"] = statistics.mean(g["miss_after_hours"] for g in ah)
    s["median_miss_after_hours"] = statistics.median(g["miss_after_hours"] for g in ah)
    s["mean_miss_4am_where_after_hours"] = statistics.mean(g["miss_4am"] for g in ah)
    s["median_miss_4am_where_after_hours"] = statistics.median(g["miss_4am"] for g in ah)
    for k, label in (("a", "4pm_to_8pm"), ("b", "8pm_to_4am"), ("c", "4am_to_9am")):
        s[f"median_abs_move_{label}"] = statistics.median(abs(g[k]) for g in rows)
        s[f"moves_over_2pct_{label}"] = sum(1 for g in rows if abs(g[k]) > 0.02)
    return s


groups = {"all": gap_rows, "weeknights": [g for g in gap_rows if g["kind"] == "weeknight"],
          "weekends": [g for g in gap_rows if g["kind"] != "weeknight"]}
gap_summary = {k: summarize(v) for k, v in groups.items()}
s = gap_summary["all"]
s["shuffle_tail_near_4am"], s["shuffle_tail_same_4am"] = shuffle_tail(gap_rows, "4am")
ah = [abs(g["vs_after_hours"]) for g in gap_rows if g["vs_after_hours"] is not None]
pm = [abs(g["vs_premarket"]) for g in gap_rows]
ext = {"after_hours_n": len(ah), "after_hours_median": statistics.median(ah), "after_hours_max": max(ah),
       "after_hours_within_1pct": sum(1 for x in ah if x <= 0.01),
       "premarket_n": len(pm), "premarket_median": statistics.median(pm), "premarket_max": max(pm),
       "premarket_within_1pct": sum(1 for x in pm if x <= 0.01)}
largest_two = sorted(gap_rows, key=lambda g: abs(g["actual"]))[-2:]
two = [g for g in gap_rows if g not in largest_two]
check("the two largest opening moves came on September 18 and 21",
      sorted(str(g["to"]) for g in largest_two) == ["2026-09-18", "2026-09-21"] and len(two) == 28)
w2 = summarize(two)
w2["shuffle_tail_near_4am"], w2["shuffle_tail_same_4am"] = shuffle_tail(two, "4am")
s["without_two_largest"] = w2
big = max(gap_rows, key=lambda g: abs(g["b"]))
say()
say("Between sessions, 30 stretches from a close to the next open")
say(f"  open nearer the perp than the prior close: at 4 am {s['near_4am']} of 30, at 9 am {s['near_9am']} of 30; "
    f"same direction as the opening move: 4 am {s['same_direction_4am']}, 9 am {s['same_direction_9am']}")
say(f"  if the perp's moves were unrelated to the open: nearer {s['unrelated_near_4am']:.2f} at 4 am and "
    f"{s['unrelated_near_9am']:.2f} at 9 am; same direction {s['unrelated_same_4am']:.2f} and {s['unrelated_same_9am']:.2f}")
say(f"  {SHUFFLES:,} shuffles of the 4 am moves (seed {SEED}): at least {s['near_4am']} nearer in "
    f"{pct(s['shuffle_tail_near_4am'], 1)}, at least {s['same_direction_4am']} in the same direction in "
    f"{pct(s['shuffle_tail_same_4am'], 1)}; fair-coin chance of a count as far from 15 as {s['near_4am']}, "
    f"{s['coin_4am']:.3f}")
say(f"  mean miss: prior close {pct(s['mean_miss_close'])}, perp at 4 am {pct(s['mean_miss_4am'])}, perp at 9 am "
    f"{pct(s['mean_miss_9am'])}, USDE's own pre-market price at 9 am {pct(s['mean_miss_premarket'])}")
say(f"  median miss: prior close {pct(s['median_miss_close'])}, 4 am {pct(s['median_miss_4am'])}, 9 am "
    f"{pct(s['median_miss_9am'])}, pre-market {pct(s['median_miss_premarket'])}")
say(f"  without September 18 and 21: nearer at 4 am {w2['near_4am']} of {w2['count']} (unrelated "
    f"{w2['unrelated_near_4am']:.2f}, shuffles {pct(w2['shuffle_tail_near_4am'], 1)}), same direction "
    f"{w2['same_direction_4am']}; mean miss prior close {pct(w2['mean_miss_close'])}, 4 am {pct(w2['mean_miss_4am'])}; "
    f"median miss prior close {pct(w2['median_miss_close'])}, 4 am {pct(w2['median_miss_4am'])}; 9 am median "
    f"{pct(w2['median_miss_9am'])} against pre-market {pct(w2['median_miss_premarket'])}")
say(f"  perp at 9 am nearer the open than USDE's pre-market price on {s['perp_9am_nearer_than_premarket']} of 30; "
    f"USDE's pre-market price nearer the open than the prior close on {s['near_premarket']} of 30")
say(f"  USDE's last after-hours price at 8 pm nearer the open than the prior close on {s['near_after_hours']} of "
    f"{s['after_hours_count']}; perp at 4 am nearer than it on {s['perp_4am_nearer_than_after_hours']}; median miss "
    f"after-hours {pct(s['median_miss_after_hours'])}, perp at 4 am {pct(s['median_miss_4am_where_after_hours'])} "
    f"on the same stretches")
say(f"  correlation with the opening move, 4 am {s['corr_4am']:.2f} (slope {s['slope_4am']:.2f}), 9 am "
    f"{s['corr_9am']:.2f} (slope {s['slope_9am']:.2f})")
say(f"  median absolute mark move, 4 pm to 8 pm {pct(s['median_abs_move_4pm_to_8pm'])} "
    f"({s['moves_over_2pct_4pm_to_8pm']} over 2%), 8 pm to 4 am {pct(s['median_abs_move_8pm_to_4am'])} "
    f"({s['moves_over_2pct_8pm_to_4am']} over 2%), 4 am to 9 am {pct(s['median_abs_move_4am_to_9am'])} "
    f"({s['moves_over_2pct_4am_to_9am']} over 2%)")
say(f"  largest 8 pm to 4 am move: {big['from']} to {big['to']}, mark {big['m8pm']} to {big['m4am']}, "
    f"{pct(big['b'], 1)}; USDE close {big['close']}, next open {big['open']} ({pct(big['actual'], 1)}); "
    f"perp dollar volume in those hours ${big['dark_usd']:,.0f}")
say(f"  mark against USDE's own extended-hours price: 8 pm median gap {pct(ext['after_hours_median'])}, within 1% "
    f"on {ext['after_hours_within_1pct']} of {ext['after_hours_n']}; 9 am median gap {pct(ext['premarket_median'])}, "
    f"within 1% on {ext['premarket_within_1pct']} of {ext['premarket_n']}")
for k in ("weeknights", "weekends"):
    g = gap_summary[k]
    say(f"  {k}: {g['count']}, nearer at 4 am {g['near_4am']}, at 9 am {g['near_9am']}; mean miss close "
        f"{pct(g['mean_miss_close'])}, 4 am {pct(g['mean_miss_4am'])}, 9 am {pct(g['mean_miss_9am'])}")
say("  largest swings of the mark from 8 pm to 4 am, against the prior close:")
swings = sorted(gap_rows, key=lambda g: -max(g["swing_up"], -g["swing_down"]))
for g in swings[:5]:
    say(f"    {g['from']} to {g['to']}: high {g['swing_high']} ({pct(g['swing_up'], 1)}) in the hour from "
        f"{ny(g['swing_high_hour'])}, low {g['swing_low']} ({pct(g['swing_down'], 1)}) in the hour from "
        f"{ny(g['swing_low_hour'])}; trades up to {g['dark_trade_high']}; mark at 4 am {g['m4am']}")
swing_summary = {
    "largest_up": max(g["swing_up"] for g in gap_rows), "largest_down": min(g["swing_down"] for g in gap_rows),
    "stretches_over_10pct": sum(1 for g in gap_rows if max(g["swing_up"], -g["swing_down"]) > 0.10),
    "top": [{"from": str(g["from"]), "to": str(g["to"]), "close": g["close"], "high": g["swing_high"],
             "high_hour_new_york": ny(g["swing_high_hour"]), "high_vs_close": g["swing_up"], "low": g["swing_low"],
             "low_hour_new_york": ny(g["swing_low_hour"]), "low_vs_close": g["swing_down"],
             "trade_high": g["dark_trade_high"], "mark_4am": g["m4am"]} for g in swings[:5]],
}

# ---------------------------------------------------------------- weekends, 8 pm Friday to 4 am on the next trading day
weekend_rows = groups["weekends"]
weekend_total = sum(g["dark_usd"] for g in weekend_rows)
weekend_hours = sum(g["dark_hours"] for g in weekend_rows)
weekend_traded = sum(g["dark_traded_hours"] for g in weekend_rows)
check("six weekend windows, five of 56 hours and the Labor Day weekend of 80",
      len(weekend_rows) == 6 and sorted(g["dark_hours"] for g in weekend_rows) == [56] * 5 + [80])
big_w = max(weekend_rows, key=lambda g: g["dark_usd"])
check("the busiest weekend ran from Friday, September 18 to Monday, September 21", str(big_w["from"]) == "2026-09-18")
say()
for g in weekend_rows:
    say(f"  weekend {g['from']} to {g['to']}: {g['dark_traded_hours']} of {g['dark_hours']} hours with a trade, "
        f"{g['dark_contracts']:,.2f} contracts, ${g['dark_usd']:,.2f}, {pct(g['dark_usd'] / weekend_total, 1)}")

# The weekend of September 19 and 20, hour by hour
W0, W1 = datetime(2026, 9, 19, tzinfo=UTC), datetime(2026, 9, 21, 8, tzinfo=UTC)
sat = [t for t in ct if W0 <= t < W1]
held = [t for t in mt if datetime(2026, 9, 19, 1, tzinfo=UTC) <= t < datetime(2026, 9, 19, 18, tzinfo=UTC)]
morning = [datetime(2026, 9, 19, h, tzinfo=UTC) for h in range(14, 18)]
fri_close = usde[date(2026, 9, 18)]["close"]
CAP_PRICE = 14.2674
rally = {
    "usde_close_fri": fri_close,
    "mark_fri_8pm": mark_at(W0),
    "mark_held": sorted({mark[t]["c"] for t in held}),
    "mark_held_hours": len(held),
    "mark_held_low": min(mark[t]["l"] for t in held), "mark_held_high": max(mark[t]["h"] for t in held),
    "mark_sat_2pm_new_york": mark_at(datetime(2026, 9, 19, 18, tzinfo=UTC)),
    "mark_sat_3pm_new_york": mark_at(datetime(2026, 9, 19, 19, tzinfo=UTC)),
    "mark_sat_4pm_new_york": mark_at(datetime(2026, 9, 19, 20, tzinfo=UTC)),
    "mark_mon_4am": mark_at(W1),
    "jump_2pm_to_3pm": mark_at(datetime(2026, 9, 19, 19, tzinfo=UTC)) / mark_at(datetime(2026, 9, 19, 18, tzinfo=UTC)) - 1,
    "trades_10am_to_2pm_usd": sum(candles[t]["V"] or 0 for t in morning),
    "trades_10am_to_2pm_contracts": sum(candles[t]["v"] or 0 for t in morning),
    "trades_10am_to_2pm_low": min(candles[t]["l"] for t in morning),
    "trades_10am_to_2pm_high": max(candles[t]["h"] for t in morning),
    "trade_high": max(candles[t]["h"] for t in sat if candles[t]["v"]),
    "first_big_hour_utc": min(t for t in sat if (candles[t]["V"] or 0) > 10000).isoformat(),
    "weekend_contracts": big_w["dark_contracts"], "weekend_usd": big_w["dark_usd"],
    "held_premium_over_close": mark_at(datetime(2026, 9, 19, 18, tzinfo=UTC)) / fri_close - 1,
    "cap_price_hours": [ny(t) for t in mt if W0 <= t < W1 and abs(mark[t]["h"] - CAP_PRICE) < 1e-9],
    "cap_price_over_close": CAP_PRICE / fri_close - 1,
    "mark_high": max(mark[t]["h"] for t in mt if W0 <= t < W1),
    "mark_high_3pm_hour": mark[datetime(2026, 9, 19, 19, tzinfo=UTC)]["h"],
    "hours_above_cap_price": [ny(t) for t in mt if W0 <= t < W1 and mark[t]["h"] > CAP_PRICE + 1e-9],
    "usde_monday_premarket_first": float(yh["2026-09-21 04:00"]["open"]),
    "usde_open_monday": usde[date(2026, 9, 21)]["open"],
    "usde_close_sep14": usde[date(2026, 9, 14)]["close"], "usde_close_sep25": usde[date(2026, 9, 25)]["close"],
    "funding_at_cap_times": [f["t"].isoformat() for f in funding if f["rate"] >= 0.5],
}
rally["trades_10am_to_2pm_share_of_weekend"] = rally["trades_10am_to_2pm_usd"] / big_w["dark_usd"]
# The same weekend counted by UTC Saturday and Sunday, for comparison with the first draft
utc_weekend = {t: candles[t]["V"] or 0 for t in ct if t.weekday() >= 5}
utc_sep19 = sum(v for t, v in utc_weekend.items() if t.date() in (date(2026, 9, 19), date(2026, 9, 20)))
rally["utc_weekend_share"] = utc_sep19 / sum(utc_weekend.values())
rally["trades_10am_to_2pm_share_of_utc_weekend"] = rally["trades_10am_to_2pm_usd"] / utc_sep19
check("the mark closed every hour from 9 pm Friday to 2 pm Saturday New York time at $10.2419",
      rally["mark_held"] == [10.2419] and rally["mark_held_hours"] == 17, f"low {rally['mark_held_low']}")
check("the mark's hourly high hit $14.2674 exactly in four hours that weekend", len(rally["cap_price_hours"]) == 4,
      ", ".join(rally["cap_price_hours"]))
check("one hour went higher, within the 0.5% premium of $14.2674", len(rally["hours_above_cap_price"]) == 1
      and rally["mark_high"] < CAP_PRICE * 1.005,
      f"{rally['mark_high']} in the hour from {rally['hours_above_cap_price'][0]}, {pct(rally['mark_high'] / CAP_PRICE - 1)} "
      f"above")
say(f"  September 19 and 20: mark ${rally['mark_fri_8pm']} at 8 pm Friday, ${rally['mark_sat_2pm_new_york']} at 2 pm "
    f"Saturday ({pct(rally['held_premium_over_close'])} above the ${fri_close} close), ${rally['mark_sat_3pm_new_york']} at "
    f"3 pm ({pct(rally['jump_2pm_to_3pm'], 1)}), ${rally['mark_mon_4am']} at 4 am Monday")
say(f"  10 am to 2 pm Saturday: {rally['trades_10am_to_2pm_contracts']:,.2f} contracts, "
    f"${rally['trades_10am_to_2pm_usd']:,.0f}, {pct(rally['trades_10am_to_2pm_share_of_weekend'], 1)} of the weekend's "
    f"${big_w['dark_usd']:,.0f}, at ${rally['trades_10am_to_2pm_low']} to ${rally['trades_10am_to_2pm_high']}")
say(f"  counted by UTC Saturday and Sunday instead, that weekend carried {pct(rally['utc_weekend_share'], 1)} of weekend "
    f"dollar volume and the Saturday morning trades {pct(rally['trades_10am_to_2pm_share_of_utc_weekend'], 1)} of it")
say(f"  mark high {rally['mark_high']}; ${CAP_PRICE} is {pct(rally['cap_price_over_close'])} above the close, reached in "
    f"the hours from {', '.join(rally['cap_price_hours'])} New York time")

# ---------------------------------------------------------------- funding
rates = [f["signed"] for f in funding]
longs = [f for f in funding if f["signed"] > 0]
shorts = [f for f in funding if f["signed"] < 0]
base = statistics.mode(rates)
in_session = sum(f["signed"] for f in funding if f["t"] - HOUR in SESSION)
fund = {
    "hours": len(funding), "total_pct_points": sum(rates), "usd_per_contract": sum(f["signed_value"] for f in funding),
    "hours_longs_paid": len(longs), "hours_shorts_paid": len(shorts), "hours_none": len(funding) - len(longs) - len(shorts),
    "zero_payments_utc": [f["t"].isoformat() for f in funding if f["rate"] == 0],
    "base_rate_pct": base, "hours_at_base": rates.count(base), "base_annual_pct": base * 24 * 365,
    "mean_rate_pct": statistics.mean(rates), "annualized_pct": statistics.mean(rates) * 24 * 365,
    "max_longs_pct": max(f["signed"] for f in longs), "max_shorts_pct": min(f["signed"] for f in shorts),
    "hours_at_cap": len(rally["funding_at_cap_times"]),
    "paid_by_longs_pct_points": sum(f["signed"] for f in longs),
    "paid_by_shorts_pct_points": -sum(f["signed"] for f in shorts),
    "in_session_pct_points": in_session, "outside_session_pct_points": sum(rates) - in_session,
    "above_base_pct_points": sum(r - base for r in rates if r > base),
    "implied_price_check": fund_check,
}
check("funding at its base rate matches the market's 0.0032% per eight hours",
      abs(base - market["base_interest_rate_pct_per_8h"] / 8) < 1e-12, f"{base}% an hour")
say()
say("Funding, percent of position value an hour, positive when longs paid shorts")
say(f"  {fund['hours']} hours: longs paid in {fund['hours_longs_paid']}, shorts in {fund['hours_shorts_paid']}, "
    f"none in {fund['hours_none']} ({', '.join(fund['zero_payments_utc'])}); base {base}% in {fund['hours_at_base']} "
    f"hours ({fund['base_annual_pct']:.3f}% a year)")
say(f"  net {fund['total_pct_points']:+.4f} percentage points; ${fund['usd_per_contract']:.4f} per contract; mean "
    f"{fund['mean_rate_pct']:.5f}% an hour, {fund['annualized_pct']:.1f}% a year at that pace")
say(f"  largest hour for longs {fund['max_longs_pct']}% ({fund['hours_at_cap']} hours at the 0.5% cap), for shorts "
    f"{fund['max_shorts_pct']}%; in session hours {in_session:+.4f}, outside {fund['outside_session_pct_points']:+.4f}")
weeks = {}
for f in funding:
    wk = (f["t"] - HOUR).date()  # a payment counts in the week of the hour it closes
    wk -= timedelta(days=wk.weekday())
    w = weeks.setdefault(wk, {"hours": 0, "sum": 0.0, "longs": 0, "shorts": 0, "usd": 0.0})
    w["hours"] += 1
    w["sum"] += f["signed"]
    w["usd"] += f["signed_value"]
    w["longs"] += f["signed"] > 0
    w["shorts"] += f["signed"] < 0

fund["two_weeks_from_sep14_pct_points"] = weeks[date(2026, 9, 14)]["sum"] + weeks[date(2026, 9, 21)]["sum"]
check("the two weeks from September 14 added more than the whole period's net",
      fund["two_weeks_from_sep14_pct_points"] > fund["total_pct_points"],
      f"{fund['two_weeks_from_sep14_pct_points']:.4f} against {fund['total_pct_points']:.4f} percentage points")

# ---------------------------------------------------------------- activity and size
contracts = sum(candles[t]["v"] or 0 for t in ct)
quote = sum(candles[t]["V"] or 0 for t in ct)
inside = [t for t in ct if t in SESSION]
outside = [t for t in ct if t not in SESSION]
mark_in = [t for t in mt if t in SESSION]
mark_out = [t for t in mt if t not in SESSION]
usde_shares = sum(usde[d]["volume"] for d in sessions)
size = {
    "hours": len(ct), "idle_hours": len(idle),
    "session_hours": len(inside), "session_idle": sum(1 for t in inside if not candles[t]["v"]),
    "outside_hours": len(outside), "outside_idle": sum(1 for t in outside if not candles[t]["v"]),
    "session_usd": sum(candles[t]["V"] or 0 for t in inside), "outside_usd": sum(candles[t]["V"] or 0 for t in outside),
    "mark_session_hours": len(mark_in), "mark_session_flat": sum(1 for t in mark_in if mark[t]["h"] == mark[t]["l"]),
    "mark_outside_hours": len(mark_out), "mark_outside_flat": sum(1 for t in mark_out if mark[t]["h"] == mark[t]["l"]),
    "weekend_hours": weekend_hours, "weekend_traded_hours": weekend_traded, "weekend_usd": weekend_total,
    "weekend_sep18_share": big_w["dark_usd"] / weekend_total,
    "contracts": contracts, "quote_usd": quote, "usde_shares": usde_shares,
    "contracts_over_shares": contracts / usde_shares,
    "oi_contracts": market["open_interest_contracts"],
    "oi_usd_at_mark": market["open_interest_contracts"] * market["mark_price"],
    "oi_over_freely_tradable": market["open_interest_contracts"] / FREELY_TRADABLE,
    "oi_over_class_a": market["open_interest_contracts"] / CLASS_A_OCT8,
    "metric_oi_oct8": metrics[LAST_DAY]["oi"],
    "metric_oi_oct8_over_one_side_at_8pm_mark": metrics[LAST_DAY]["oi"] / (market["open_interest_contracts"] * mark_at(CUT)),
}
size["outside_share"] = size["outside_usd"] / quote
check("session and outside hours add up", size["session_hours"] + size["outside_hours"] == len(ct)
      and size["session_idle"] + size["outside_idle"] == len(idle)
      and abs(size["session_usd"] + size["outside_usd"] - quote) < 1e-6)
say()
say(f"Activity: {size['idle_hours']} of {size['hours']} hours without a trade, {size['session_idle']} of "
    f"{size['session_hours']} in the session hours and {size['outside_idle']} of {size['outside_hours']} outside them; "
    f"weekend windows {weekend_traded} of {weekend_hours} hours with a trade")
say(f"  ${quote:,.2f} traded, {contracts:,.2f} contracts; outside the session hours ${size['outside_usd']:,.0f}, "
    f"{pct(size['outside_share'], 1)}, ${size['outside_usd'] / size['outside_hours']:,.0f} an hour against "
    f"${size['session_usd'] / size['session_hours']:,.0f} inside")
say(f"  mark candles with no movement: {size['mark_outside_flat']} of {size['mark_outside_hours']} outside the session "
    f"hours, {size['mark_session_flat']} of {size['mark_session_hours']} inside")
say(f"  contracts per USDE share {size['contracts_over_shares']:.4f}; open interest {size['oi_contracts']:,.2f} contracts, "
    f"${size['oi_usd_at_mark']:,.0f} at the mark, {pct(size['oi_over_freely_tradable'])} of freely tradable shares, "
    f"{pct(size['oi_over_class_a'])} of Class A shares")
say(f"  Lighter's open interest figure for October 8, ${size['metric_oi_oct8']:,.2f}, is "
    f"{size['metric_oi_oct8_over_one_side_at_8pm_mark']:.2f} times the October 9 open contracts at the 8 pm mark")

# ---------------------------------------------------------------- stop before writing if any check failed
say()
if FAILED:
    say(f"{len(FAILED)} check(s) failed: {', '.join(FAILED)}. Nothing was written to out/.")
    sys.exit(1)

# ---------------------------------------------------------------- outputs
os.makedirs(OUT, exist_ok=True)
write_csv("close_comparison.csv",
          ["date", "usde_close", "perp_mark_4pm", "perp_last_trade_4pm", "last_trade_hour_starts_new_york",
           "mark_vs_close", "last_trade_vs_close"],
          [[r["date"], r["close"], r["mark"], r["trade"], ny(r["trade_hour"]), r6(r["gap_mark"]), r6(r["gap_trade"])]
           for r in close_rows])
write_csv("off_hours.csv",
          ["from_session", "to_session", "kind", "usde_close", "usde_next_open", "perp_mark_4pm", "perp_mark_8pm",
           "perp_mark_4am", "perp_mark_9am", "usde_after_hours_8pm", "usde_pre_market_9am", "mark_move_4pm_to_8pm",
           "mark_move_8pm_to_4am", "mark_move_4am_to_9am", "open_vs_close", "perp_4am_vs_close", "perp_9am_vs_close",
           "open_nearer_perp_4am", "open_nearer_perp_9am", "perp_4am_same_direction", "perp_9am_same_direction",
           "perp_9am_nearer_than_pre_market", "perp_4am_nearer_than_after_hours", "mark_high_8pm_to_4am",
           "mark_high_vs_close", "mark_low_8pm_to_4am", "mark_low_vs_close", "perp_usd_traded_8pm_to_4am",
           "hours_with_trades_8pm_to_4am", "hours_8pm_to_4am"],
          [[g["from"], g["to"], g["kind"], g["close"], g["open"], g["m4pm"], g["m8pm"], g["m4am"], g["m9am"],
            g["y8pm"] if g["y8pm"] is not None else "", g["y9am"], r6(g["a"]), r6(g["b"]), r6(g["c"]), r6(g["actual"]),
            r6(g["implied_4am"]), r6(g["implied_9am"]), int(g["near_4am"]), int(g["near_9am"]), int(g["same_4am"]),
            int(g["same_9am"]), int(g["perp_beats_premarket"]),
            "" if g["perp_4am_beats_after_hours"] is None else int(g["perp_4am_beats_after_hours"]),
            g["swing_high"], r6(g["swing_up"]), g["swing_low"], r6(g["swing_down"]), round(g["dark_usd"], 2),
            g["dark_traded_hours"], g["dark_hours"]]
           for g in gap_rows])
write_csv("funding_by_week.csv",
          ["week_starting_monday_utc", "hours", "net_pct_points", "usd_per_contract", "hours_longs_paid", "hours_shorts_paid"],
          [[k, w["hours"], round(w["sum"], 4), round(w["usd"], 6), w["longs"], w["shorts"]] for k, w in sorted(weeks.items())])
write_csv("daily_activity.csv",
          ["date_utc", "hours", "hours_without_trade", "perp_contracts", "perp_usd", "lighter_volume_metric_usd",
           "lighter_open_interest_metric_usd", "usde_shares_traded"],
          [[d, agg[d]["hours"], agg[d]["idle"], round(agg[d]["v"], 2), round(agg[d]["V"], 2), metrics[d]["volume"],
            metrics[d]["oi"], usde[d]["volume"] if d in usde else ""] for d in sorted(agg)])
write_csv("weekend_activity.csv",
          ["friday_session", "next_session", "hours_8pm_friday_to_4am", "hours_with_a_trade", "perp_contracts", "perp_usd",
           "share_of_weekend_usd", "usde_friday_close", "mark_high", "mark_high_vs_friday_close", "mark_low",
           "mark_low_vs_friday_close"],
          [[g["from"], g["to"], g["dark_hours"], g["dark_traded_hours"], round(g["dark_contracts"], 2), round(g["dark_usd"], 2),
            round(g["dark_usd"] / weekend_total, 4), g["close"], g["swing_high"], r6(g["swing_up"]), g["swing_low"],
            r6(g["swing_down"])] for g in weekend_rows])
write_csv("chart_off_hours.csv",
          ["from_session", "to_session", "kind", "open_vs_close_pct", "perp_4am_vs_close_pct", "perp_9am_vs_close_pct",
           "open_nearer_perp_4am", "open_nearer_perp_9am"],
          [[g["from"], g["to"], g["kind"], round(g["actual"] * 100, 2), round(g["implied_4am"] * 100, 2),
            round(g["implied_9am"] * 100, 2), int(g["near_4am"]), int(g["near_9am"])] for g in gap_rows])
results = {
    "window": {"first_trade_hour_utc": FIRST_TRADE_HOUR.isoformat(), "cutoff_utc": CUT.isoformat(),
               "sessions": len(sessions), "stretches": len(gap_rows)},
    "market": market,
    "oracle_snapshot": {"computed_at_utc": oracle_at.isoformat(), "index": o229["index"], "mark": o229["mark"]},
    "close": close_summary,
    "off_hours": gap_summary,
    "extended_hours": ext,
    "swings_8pm_to_4am": swing_summary,
    "september_19_weekend": rally,
    "funding": fund,
    "size": size,
    "volume_metric": vol_metric,
}
with open(os.path.join(OUT, "results.json"), "w") as f:
    json.dump(results, f, indent=1, default=str)
    f.write("\n")
say("All checks passed. Tables written to out/.")
with open(os.path.join(OUT, "run_log.txt"), "w") as f:
    f.write("\n".join(LOG) + "\n")
