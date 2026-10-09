#!/usr/bin/env python3
"""How closely StablecoinX's Class A stock, USDE, followed ENA from its first session on June 26 to
October 8, 2026.

Reads the files in inputs/ and runs every check. If any check fails it stops before writing
anything, so out/ keeps the tables of the last clean run. Otherwise it rewrites the tables in
out/. Python 3 standard library only. It makes no network requests.

Prices.
  USDE daily open and close from S&P Global Market Intelligence through StockAnalysis.
  ENA at 4 pm New York time, 20:00 UTC, from Kraken's ENA/USD market: the close of the
  4-hour candle from 16:00 to 20:00 UTC, the last trade before 20:00.
  ENA from CoinGecko through DefiLlama's price API at 20:00 UTC, a second source, and at
  13:30 UTC, 9:30 am New York time, for the opening comparison.
  ENA as this site's dashboard records it, from the dataset at commit 152e758. Each date's
  price there is the price at 00:00 UTC that day, 8 pm New York time the evening before.

Every date in the window fell in daylight saving time, so New York time is UTC minus four hours. NYSE's
calendar for 2026 lists no early close in the window, so every session closed at 4 pm. The closing 8-K's
Item 2.01 gives June 26 as USDE's first trading day.
A daily move is the percentage change from one session's close to the next. ENA's move over
the same span runs from 20:00 UTC to 20:00 UTC. mNAV is USDE's close divided by the value of
the ENA per share, with the dashboard's 3,029,000,000 ENA and its Class A share count.
"""
import csv
import hashlib
import json
import math
import os
import statistics
import sys
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, "inputs")
OUT = os.path.join(HERE, "out")
FIRST, LAST = date(2026, 6, 26), date(2026, 10, 8)
PERIODS = [("2026-06-26 to 2026-07-31", date(2026, 6, 26), date(2026, 7, 31)),
           ("2026-07-31 to 2026-08-31", date(2026, 7, 31), date(2026, 8, 31)),
           ("2026-08-31 to 2026-10-08", date(2026, 8, 31), date(2026, 10, 8))]

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


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def stats(x, y):
    """Correlation, slope of y on x, share of y's variance explained, same-direction count."""
    mx, my = statistics.mean(x), statistics.mean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    r = sxy / math.sqrt(sxx * syy)
    return {"n": len(x), "correlation": r, "r_squared": r * r, "beta": sxy / sxx,
            "same_direction": sum(1 for a, b in zip(x, y) if a * b > 0),
            "either_unchanged": sum(1 for a, b in zip(x, y) if a == 0 or b == 0),
            "sd_x": statistics.stdev(x), "sd_y": statistics.stdev(y)}


def ranks(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    out = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        for k in range(i, j + 1):
            out[order[k]] = (i + j) / 2
        i = j + 1
    return out


def write_csv(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def r6(x):
    return round(x, 6)


say("USDE against ENA, StablecoinX Inc.'s Class A stock and its treasury token")
say(f"Sessions {FIRST} to {LAST}")
say()

# ---------------------------------------------------------------- inputs and their integrity
manifest = read_csv("manifest.csv")
bad = [m["file"] for m in manifest if sha256(os.path.join(INP, m["file"])) != m["sha256"]]
check("every input matches the SHA-256 in manifest.csv", not bad and len(manifest) == 7,
      f"{len(manifest)} files" + (f", mismatched {bad}" if bad else ""))
facts = {r["key"]: r["value"] for r in read_csv("filing_facts.csv")}
ENA_HELD = int(facts["ena_held_dashboard"])
check("the dashboard's ENA count read from filing_facts.csv", ENA_HELD == 3_029_000_000)
FIRST_TRADING_DAY = date.fromisoformat(facts["first_trading_day"])

kr_log = read_csv("kraken_fetch_log.csv")
ll_log = read_csv("defillama_fetch_log.csv")
check("Kraken and DefiLlama each answered with HTTP 200", all(r["status"] == "200" for r in kr_log + ll_log),
      f"Kraken {kr_log[0]['fetched_at']}, DefiLlama {ll_log[0]['fetched_at']} and {ll_log[1]['fetched_at']}")

spg = {date.fromisoformat(r["date"]): r for r in read_csv("usde_daily_spglobal_stockanalysis.csv")}
sessions = sorted(d for d in spg if FIRST <= d <= LAST)
check("73 USDE sessions from June 26 to October 8, none on a weekend",
      len(sessions) == 73 and all(d.weekday() < 5 for d in sessions))
check("the first session is the first trading day in the closing 8-K", sessions[0] == FIRST_TRADING_DAY == FIRST)
close = {d: float(spg[d]["close"]) for d in sessions}
opn = {d: float(spg[d]["open"]) for d in sessions}

# Kraken 4-hour candles: the one starting 16:00 UTC closes at 20:00 UTC, the one starting 20:00 UTC at 00:00
k16, k20 = {}, {}
kr_rows = read_csv("kraken_enausd_4h_20utc_00utc.csv")
other_hours = 0
for r in kr_rows:
    t = datetime.fromtimestamp(int(r["start_unix"]), timezone.utc)
    assert r["start_utc"] == t.strftime("%Y-%m-%dT%H:%M:%SZ")
    if (t.hour, t.minute) == (16, 0):
        k16[t.date()] = r
    elif (t.hour, t.minute) == (20, 0):
        k20[t.date()] = r
    else:
        other_hours += 1
days = [date(2026, 6, 25) + timedelta(days=i) for i in range((date(2026, 10, 8) - date(2026, 6, 25)).days + 1)]
check("Kraken has both 4-hour candles for every day from June 25 to October 8, and nothing else",
      other_hours == 0 and len(kr_rows) == 2 * len(days) and sorted(k16) == days and sorted(k20) == days,
      f"{len(kr_rows)} candles")
check("every Kraken candle has trades, and its close lies between its low and high",
      all(int(r["trades"]) > 0 and float(r["low"]) <= float(r["close"]) <= float(r["high"])
          for r in list(k16.values()) + list(k20.values())))
ena4 = {d: float(k16[d]["close"]) for d in k16}                                # 20:00 UTC on d
ena0 = {d + timedelta(days=1): float(k20[d]["close"]) for d in k20}            # 00:00 UTC on d

cg20, cg13 = {}, {}
for r in read_csv("ena_coingecko_via_defillama.csv"):
    d = date.fromisoformat(r["target_utc"][:10])
    (cg20 if r["series"] == "close_2000utc" else cg13)[d] = r
check("CoinGecko prices for 20:00 UTC on June 25 and every session, and for 13:30 UTC on every session",
      sorted(cg20) == [date(2026, 6, 25)] + sessions and sorted(cg13) == sessions)
offsets = [abs(int(r["offset_s"])) for r in list(cg20.values()) + list(cg13.values())]
check("each CoinGecko price lies within the 600-second search width of its target time", max(offsets) <= 600,
      f"largest offset {max(offsets)} s")
cg4 = {d: float(cg20[d]["price_usd"]) for d in cg20}
cgo = {d: float(cg13[d]["price_usd"]) for d in cg13}
gap = {d: abs(ena4[d] / cg4[d] - 1) for d in sessions}
check("Kraken's 4 pm price is within 1% of CoinGecko's on every session", max(gap.values()) < 0.01,
      f"largest {pct(max(gap.values()), 2)} on {max(gap, key=gap.get)}, median {pct(statistics.median(gap.values()), 3)}")

dash = {date.fromisoformat(r["date"]): r for r in read_csv("dashboard_series_152e758.csv")}
check("the dashboard series holds every session, with the same closes as S&P Global",
      all(d in dash and abs(float(dash[d]["usde_close"]) - close[d]) < 0.005 for d in sessions))
dgap = {d: abs(float(dash[d]["ena_price"]) / ena0[d] - 1) for d in sessions}
check("the dashboard's ENA price for each session is within 0.5% of Kraken's price at 00:00 UTC that day",
      max(dgap.values()) < 0.005, f"largest {pct(max(dgap.values()), 2)}, median {pct(statistics.median(dgap.values()), 3)}")
dgap4 = [abs(float(dash[d]["ena_price"]) / ena4[d] - 1) for d in sessions]
say(f"  for comparison, against Kraken's 4 pm price the dashboard's differs by a median {pct(statistics.median(dgap4), 2)}")
shares = {d: int(dash[d]["shares_outstanding"]) for d in sessions}
check("the dashboard counts 3,029,000,000 ENA on every session", all(int(dash[d]["ena_holdings"]) == ENA_HELD
                                                                    for d in sessions))
mn_dash = {d: close[d] / (float(dash[d]["ena_price"]) * ENA_HELD / shares[d]) for d in sessions}
check("mNAV recomputed from the dashboard's own inputs matches its mnav column to four decimals",
      all(abs(mn_dash[d] - float(dash[d]["mnav"])) < 0.0001 for d in sessions))
share_changes = [(d, shares[d]) for i, d in enumerate(sessions) if i == 0 or shares[d] != shares[sessions[i - 1]]]
say("  dashboard Class A shares: " + ", ".join(f"{d} {s:,}" for d, s in share_changes))

# ---------------------------------------------------------------- daily moves at 4 pm
pairs = list(zip(sessions, sessions[1:]))


def move(p, a, b):
    return p[b] / p[a] - 1


usde = [move(close, a, b) for a, b in pairs]
ena = [move(ena4, a, b) for a, b in pairs]
results = {"window": {"first_session": str(FIRST), "last_session": str(LAST), "sessions": len(sessions),
                      "daily_moves": len(pairs)}}
daily = stats(ena, usde)
results["daily_kraken"] = daily
results["daily_coingecko"] = stats([move(cg4, a, b) for a, b in pairs], usde)
results["daily_dashboard_midnight"] = stats([move({d: float(dash[d]["ena_price"]) for d in sessions}, a, b)
                                             for a, b in pairs], usde)
results["daily_spearman"] = stats(ranks(ena), ranks(usde))["correlation"]
top3 = sorted(range(len(usde)), key=lambda i: -abs(usde[i]))[:3]
keep = [i for i in range(len(usde)) if i not in top3]
results["daily_without_largest_three"] = {"dates": [str(pairs[i][1]) for i in top3],
                                          **stats([ena[i] for i in keep], [usde[i] for i in keep])}
lg = stats([math.log(1 + x) for x in ena], [math.log(1 + y) for y in usde])
results["daily_log_changes"] = lg
periods = []
for label, lo, hi in PERIODS:
    idx = [i for i, (a, b) in enumerate(pairs) if a >= lo and b <= hi]
    periods.append({"period": label, **stats([ena[i] for i in idx], [usde[i] for i in idx])})
results["by_period"] = periods
check("the three periods cover every daily move once", sum(p["n"] for p in periods) == len(pairs))

weekly_end = {}
for d in sessions:
    weekly_end[d.isocalendar()[:2]] = d
weeks = [weekly_end[k] for k in sorted(weekly_end)]
wpairs = list(zip(weeks, weeks[1:]))
results["weekly"] = {"weeks": len(wpairs), **stats([move(ena4, a, b) for a, b in wpairs],
                                                     [move(close, a, b) for a, b in wpairs])}

# mNAV at 4 pm
mn = {d: close[d] / (ena4[d] * ENA_HELD / shares[d]) for d in sessions}
mn_moves = [move(mn, a, b) for a, b in pairs]
low_d, high_d = min(mn, key=mn.get), max(mn, key=mn.get)
results["mnav_4pm"] = {"first": mn[FIRST], "last": mn[LAST], "low": mn[low_d], "low_date": str(low_d),
                       "high": mn[high_d], "high_date": str(high_d), "sd_daily_move": statistics.stdev(mn_moves),
                       "sessions_below_0_25": sum(1 for d in sessions if mn[d] < 0.25)}
results["cumulative"] = {"usde": close[LAST] / close[FIRST] - 1, "ena_4pm": ena4[LAST] / ena4[FIRST] - 1,
                         "usde_first": close[FIRST], "usde_last": close[LAST], "ena_first": ena4[FIRST],
                         "ena_last": ena4[LAST]}

# opening gaps and the session itself, both against CoinGecko at the same moments
gap_usde = [opn[b] / close[a] - 1 for a, b in pairs]
gap_ena = [cgo[b] / cg4[a] - 1 for a, b in pairs]
day_usde = [close[b] / opn[b] - 1 for a, b in pairs]
day_ena = [cg4[b] / cgo[b] - 1 for a, b in pairs]
results["overnight"] = stats(gap_ena, gap_usde)
results["trading_hours"] = stats(day_ena, day_usde)
biggest = max(range(len(gap_ena)), key=lambda i: abs(gap_ena[i]))
results["largest_overnight_ena"] = {"date": str(pairs[biggest][1]), "ena": gap_ena[biggest], "usde_gap": gap_usde[biggest]}

# robustness of the split at the open and of August, and sampling uncertainty
results["overnight_spearman"] = stats(ranks(gap_ena), ranks(gap_usde))["correlation"]
results["trading_hours_spearman"] = stats(ranks(day_ena), ranks(day_usde))["correlation"]
big1 = top3[0]
keep1 = [i for i in range(len(pairs)) if i != big1]
results["without_largest_day"] = {"date": str(pairs[big1][1]),
                                  "overnight": stats([gap_ena[i] for i in keep1], [gap_usde[i] for i in keep1]),
                                  "trading_hours": stats([day_ena[i] for i in keep1], [day_usde[i] for i in keep1]),
                                  "overnight_spearman": stats(ranks([gap_ena[i] for i in keep1]),
                                                              ranks([gap_usde[i] for i in keep1]))["correlation"],
                                  "trading_hours_spearman": stats(ranks([day_ena[i] for i in keep1]),
                                                                  ranks([day_usde[i] for i in keep1]))["correlation"]}
aug = [i for i, (a, b) in enumerate(pairs) if a >= PERIODS[1][1] and b <= PERIODS[1][2]]
aug_top2 = sorted(aug, key=lambda i: -abs(usde[i]))[:2]
aug_rest = [i for i in aug if i not in aug_top2]
results["august_without_two_largest"] = {"dates": [str(pairs[i][1]) for i in aug_top2],
                                         "same_direction_on_those_days": all(usde[i] * ena[i] > 0 for i in aug_top2),
                                         **stats([ena[i] for i in aug_rest], [usde[i] for i in aug_rest])}


def fisher_ci(r, n):
    z, se = math.atanh(r), 1 / math.sqrt(n - 3)
    return [math.tanh(z - 1.959964 * se), math.tanh(z + 1.959964 * se)]


results["ci95"] = {"daily_kraken": fisher_ci(daily["correlation"], daily["n"]),
                   "daily_dashboard_midnight": fisher_ci(results["daily_dashboard_midnight"]["correlation"], len(pairs))}
tests = []
for i in range(len(periods)):
    for j in range(i + 1, len(periods)):
        a_, b_ = periods[i], periods[j]
        zz = (math.atanh(b_["correlation"]) - math.atanh(a_["correlation"])) / math.sqrt(1 / (a_["n"] - 3) + 1 / (b_["n"] - 3))
        tests.append({"periods": [a_["period"], b_["period"]], "z": zz, "p_two_sided": math.erfc(abs(zz) / math.sqrt(2))})
results["period_tests"] = tests
wk_u = [move(close, a, b) for a, b in wpairs]
wk_e = [move(ena4, a, b) for a, b in wpairs]
wbig = max(range(len(wpairs)), key=lambda i: abs(wk_u[i]))
results["weekly_extra"] = {"spearman": stats(ranks(wk_e), ranks(wk_u))["correlation"],
                           "largest_week_end": str(wpairs[wbig][1]), "largest_week_usde": wk_u[wbig], "largest_week_ena": wk_e[wbig],
                           "without_largest_week": stats([wk_e[i] for i in range(len(wpairs)) if i != wbig],
                                                         [wk_u[i] for i in range(len(wpairs)) if i != wbig])}
dm = {d: float(dash[d]["mnav"]) for d in sessions}
dmax = max(sessions, key=dm.get)
dmin = min(sessions, key=dm.get)
results["dashboard_mnav"] = {"last": dm[LAST], "high": dm[dmax], "high_date": str(dmax), "low": dm[dmin], "low_date": str(dmin)}

check("ENA's 4 pm price came from the same Kraken candle on every session as the moves use",
      all(ena4[d] == float(k16[d]["close"]) for d in sessions))

say()
d = daily
say(f"Daily moves, 4 pm to 4 pm, {d['n']} pairs")
for key, label in (("daily_kraken", "Kraken 4 pm"), ("daily_coingecko", "CoinGecko 4 pm"),
                   ("daily_dashboard_midnight", "dashboard, midnight UTC"), ("daily_log_changes", "Kraken, log changes")):
    s = results[key]
    say(f"  {label}: correlation {s['correlation']:.3f}, R squared {s['r_squared']:.3f}, slope {s['beta']:.2f}, same "
        f"direction {s['same_direction']} of {s['n']}, either unchanged {s['either_unchanged']}, sd USDE {pct(s['sd_y'], 2)}, "
        f"sd ENA {pct(s['sd_x'], 2)}")
w3 = results["daily_without_largest_three"]
say(f"  rank correlation {results['daily_spearman']:.3f}; without the three largest USDE moves ({', '.join(w3['dates'])}) "
    f"{w3['correlation']:.3f}")
for p in periods:
    say(f"  {p['period']}: {p['n']} moves, correlation {p['correlation']:.3f}, slope {p['beta']:.2f}, same direction "
        f"{p['same_direction']}")
wk = results["weekly"]
say(f"  weekly, last session of each week, {wk['weeks']} moves: correlation {wk['correlation']:.3f}, slope {wk['beta']:.2f}, "
    f"same direction {wk['same_direction']}")
m = results["mnav_4pm"]
say(f"  mNAV at 4 pm: {m['first']:.3f} on {FIRST}, {m['last']:.3f} on {LAST}, low {m['low']:.3f} on {m['low_date']}, high "
    f"{m['high']:.3f} on {m['high_date']}, sd of daily moves {pct(m['sd_daily_move'], 2)}, below 0.25 on "
    f"{m['sessions_below_0_25']} sessions")
c = results["cumulative"]
say(f"  June 26 to October 8: USDE {pct(c['usde'])}, from ${c['usde_first']:.2f} to ${c['usde_last']:.2f}; ENA at 4 pm "
    f"{pct(c['ena_4pm'])}, from ${c['ena_first']:.4f} to ${c['ena_last']:.4f}")
o, s = results["overnight"], results["trading_hours"]
say(f"  overnight, 4 pm close to 9:30 am open: correlation {o['correlation']:.3f}, slope {o['beta']:.2f}, same direction "
    f"{o['same_direction']}")
say(f"  trading hours, 9:30 am open to 4 pm close: correlation {s['correlation']:.3f}, slope {s['beta']:.2f}, same direction "
    f"{s['same_direction']}")
lo_ = results["largest_overnight_ena"]
say(f"  largest overnight ENA move: {lo_['date']}, ENA {pct(lo_['ena'])}, USDE gap {pct(lo_['usde_gap'])}")
wl_ = results["without_largest_day"]
say(f"  rank correlation overnight {results['overnight_spearman']:.3f}, trading hours {results['trading_hours_spearman']:.3f}; "
    f"without {wl_['date']}, overnight {wl_['overnight']['correlation']:.3f}, trading hours "
    f"{wl_['trading_hours']['correlation']:.3f}, rank correlations {wl_['overnight_spearman']:.3f} and "
    f"{wl_['trading_hours_spearman']:.3f}")
au = results["august_without_two_largest"]
say(f"  August without {', '.join(au['dates'])}: correlation {au['correlation']:.3f}, those days in the same direction "
    f"{au['same_direction_on_those_days']}")
ci = results["ci95"]
say(f"  95% intervals, Fisher: Kraken {ci['daily_kraken'][0]:.2f} to {ci['daily_kraken'][1]:.2f}, dashboard midnight "
    f"{ci['daily_dashboard_midnight'][0]:.2f} to {ci['daily_dashboard_midnight'][1]:.2f}")
say("  period tests: " + "; ".join(f"{x['periods'][0]} vs {x['periods'][1]} p {x['p_two_sided']:.3f}" for x in tests))
we = results["weekly_extra"]
say(f"  weekly rank correlation {we['spearman']:.3f}; without the week to {we['largest_week_end']} "
    f"(USDE {pct(we['largest_week_usde'])}, ENA {pct(we['largest_week_ena'])}) {we['without_largest_week']['correlation']:.3f}")
dmn = results["dashboard_mnav"]
say(f"  dashboard mNAV, midnight ENA: {dmn['last']:.4f} on {LAST}, high {dmn['high']:.4f} on {dmn['high_date']}, low "
    f"{dmn['low']:.4f} on {dmn['low_date']}")

say()
if FAILED:
    say(f"{len(FAILED)} check(s) failed: {', '.join(FAILED)}. Nothing was written to out/.")
    sys.exit(1)

os.makedirs(OUT, exist_ok=True)
write_csv("daily_moves.csv",
          ["date", "prior_session", "usde_close", "ena_4pm_kraken", "ena_4pm_coingecko", "ena_midnight_dashboard",
           "usde_move", "ena_move_kraken", "ena_move_coingecko", "ena_move_dashboard", "mnav_4pm", "mnav_move",
           "usde_open", "ena_930am_coingecko", "usde_overnight", "ena_overnight", "usde_trading_hours", "ena_trading_hours"],
          [[FIRST, "", close[FIRST], ena4[FIRST], cg4[FIRST], float(dash[FIRST]["ena_price"]), "", "", "", "", r6(mn[FIRST]), "",
            opn[FIRST], cgo[FIRST], "", "", "", ""]] +
          [[b, a, close[b], ena4[b], cg4[b], float(dash[b]["ena_price"]), r6(move(close, a, b)), r6(move(ena4, a, b)),
            r6(move(cg4, a, b)), r6(float(dash[b]["ena_price"]) / float(dash[a]["ena_price"]) - 1), r6(mn[b]),
            r6(move(mn, a, b)), opn[b], cgo[b], r6(opn[b] / close[a] - 1), r6(cgo[b] / cg4[a] - 1),
            r6(close[b] / opn[b] - 1), r6(cg4[b] / cgo[b] - 1)] for a, b in pairs])
full_rows = [("daily, Kraken 4 pm", results["daily_kraken"]), ("daily, CoinGecko 4 pm", results["daily_coingecko"]),
             ("daily, dashboard midnight UTC", results["daily_dashboard_midnight"]),
             ("daily, without the three largest USDE moves", results["daily_without_largest_three"]),
             ("daily, log changes", results["daily_log_changes"])]
full_rows += [(f"daily, {p['period']}", p) for p in periods]
full_rows += [("daily, August without its two largest USDE moves", results["august_without_two_largest"]),
              ("weekly", results["weekly"]), ("weekly, without the largest week", results["weekly_extra"]["without_largest_week"]),
              ("overnight", results["overnight"]), ("trading hours", results["trading_hours"]),
              ("overnight, without the largest daily USDE move", results["without_largest_day"]["overnight"]),
              ("trading hours, without the largest daily USDE move", results["without_largest_day"]["trading_hours"])]
rank_rows = [("daily, ranks", results["daily_spearman"]), ("weekly, ranks", results["weekly_extra"]["spearman"]),
             ("overnight, ranks", results["overnight_spearman"]), ("trading hours, ranks", results["trading_hours_spearman"]),
             ("overnight, ranks, without the largest daily USDE move", results["without_largest_day"]["overnight_spearman"]),
             ("trading hours, ranks, without the largest daily USDE move",
              results["without_largest_day"]["trading_hours_spearman"])]
write_csv("summary.csv", ["measure", "moves", "correlation", "r_squared", "slope", "same_direction", "sd_usde", "sd_ena"],
          [[label, s["n"], round(s["correlation"], 4), round(s["r_squared"], 4), round(s["beta"], 4), s["same_direction"],
            round(s["sd_y"], 6), round(s["sd_x"], 6)] for label, s in full_rows]
          + [[label, results["weekly"]["n"] if "weekly" in label else (71 if "without" in label else 72), round(r, 4), "", "", "",
              "", ""] for label, r in rank_rows])
# ten decimals, so that the chart's hover text, rounded to two decimals of a percent, is not rounded twice
write_csv("chart_data.csv", ["date", "ena_move", "usde_move", "period", "mnav_4pm"],
          [[FIRST, "", "", "", round(mn[FIRST], 10)]]
          + [[b, round(move(ena4, a, b), 10), round(move(close, a, b), 10),
              next(p[0] for p in PERIODS if a >= p[1] and b <= p[2]), round(mn[b], 10)] for a, b in pairs])
with open(os.path.join(OUT, "results.json"), "w") as f:
    json.dump(results, f, indent=1, default=str)
    f.write("\n")
say("All checks passed. Tables written to out/.")
with open(os.path.join(OUT, "run_log.txt"), "w") as f:
    f.write("\n".join(LOG) + "\n")
