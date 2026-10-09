#!/usr/bin/env python3
"""Short selling in StablecoinX's Class A stock, USDE, from its first session on June 26 to
October 8, 2026.

Reads the files in inputs/ and runs every check. If any check fails it stops before writing
anything, so out/ keeps the tables of the last clean run. Otherwise it rewrites the tables in
out/. Python 3 standard library only. It makes no network requests.

Sources.
  FINRA consolidated short interest, the short positions member firms report under FINRA
  Rule 4560 as of each settlement date, twice a month.
  FINRA daily short sale volume files (consolidated NMS), the regular-hours trades reported to
  FINRA's trade reporting facilities, with the volume marked short and short exempt.
  USDE daily prices and volume from S&P Global Market Intelligence through StockAnalysis.
  The resale prospectus's share counts for August 28, 2026.
  FINRA's later checks for the September 30 settlement date, in finra_recheck_log.csv.

A short interest cycle runs from the session after one settlement date to the next settlement
date, both counted in New York trading days. Days to cover is the short interest divided by
the average daily volume in S&P Global's data over that cycle, the window FINRA uses for its
own average. A position counts in short interest once its trade has settled, one business day
after the trade, so the change from one settlement date to the next comes from trades made from
the earlier settlement date through the session before the later one. The comparison with daily
short volume uses that window.

The SEC's short sale price test, Rule 201, applies for the rest of the day once a stock falls
10% or more below the prior day's closing price during regular hours, and for the whole of the
next day. This review counts a trigger when S&P Global's daily low is at or below 90% of the
prior close.
"""
import csv
import hashlib
import json
import os
import statistics
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, "inputs")
OUT = os.path.join(HERE, "out")
FIRST, LAST = date(2026, 6, 26), date(2026, 10, 8)

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


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256(path):
    with open(path, "rb") as f:
        return sha256_bytes(f.read())


def pct(x, d=2):
    return f"{x * 100:.{d}f}%"


def r6(x):
    return None if x is None else round(x, 6)


def write_csv(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def d8(s):
    return date(int(s[:4]), int(s[4:6]), int(s[6:8]))


say("Short selling in USDE, StablecoinX Inc.'s Class A stock")
say(f"Sessions {FIRST} to {LAST}")
say()

# ---------------------------------------------------------------- inputs and their integrity
facts = {r["key"]: (int(r["value"]) if r["value"].isdigit() else r["value"]) for r in read_csv("filing_facts.csv")}
ETHENA = facts["ethena_registered_class_a_aug28"]
FREELY_TRADABLE = facts["freely_tradable_aug28"]
CLASS_A_AUG28 = facts["class_a_outstanding_aug28"]
CLASS_A_OCT8 = facts["dashboard_class_a_oct8"]
check("share counts read from filing_facts.csv",
      FREELY_TRADABLE == 19_063_653 and CLASS_A_AUG28 == 24_029_375 and CLASS_A_OCT8 == 24_139_375)

manifest = read_csv("manifest.csv")
bad = [m["file"] for m in manifest if sha256(os.path.join(INP, m["file"])) != m["sha256"]]
check("every input matches the SHA-256 in manifest.csv", not bad and len(manifest) == 10,
      f"{len(manifest)} files" + (f", mismatched {bad}" if bad else ""))

daily_log = read_csv("finra_daily_fetch_log.csv")
check("74 FINRA daily files read, each HTTP 200 with the expected header and a record count equal to its trailer",
      len(daily_log) == 74 and all(r["status"] == "200" and r["header_ok"] == "true" and r["records"] == r["trailer"]
                                   for r in daily_log),
      f"{daily_log[0]['fetched_at']} to {daily_log[-1]['fetched_at']}")

si_log = read_csv("finra_short_interest_fetch_log.csv")
raw_ok = []
for r in si_log:
    sym = json.loads(r["request_body"])["compareFilters"][0]["fieldValue"].lower()
    with open(os.path.join(INP, f"finra_short_interest_{sym}.json"), "rb") as f:
        raw = f.read()
    raw_ok.append(r["status"] == "200" and sha256_bytes(raw.rstrip(b"\n")) == r["sha256"])
check("each short interest file, without its final newline, matches the logged response hash",
      len(si_log) == 2 and all(raw_ok))

# ---------------------------------------------------------------- USDE daily prices
px = {}
for r in read_csv("usde_daily_spglobal_stockanalysis.csv"):
    d = date.fromisoformat(r["date"])
    px[d] = {k: float(r[k]) for k in ("open", "high", "low", "close")}
    px[d]["volume"] = int(r["volume"])
sessions = sorted(d for d in px if FIRST <= d <= LAST)
# The price test counts S&P Global's daily low as the regular-session low. Checked against Yahoo Finance's hourly
# bars, which start on August 26, because the price test can only be triggered during regular hours.
reg_low = {}
for r in read_csv("usde_hourly_yahoo.csv"):
    if r["low"] and "09:30" <= r["new_york"][11:] <= "15:30":
        d = date.fromisoformat(r["new_york"][:10])
        reg_low[d] = min(reg_low.get(d, 1e9), float(r["low"]))
low_checked = sorted(d for d in reg_low if d in px)
low_gap = {d: round(px[d]["low"] - reg_low[d], 4) for d in low_checked}
check("S&P Global's daily low is within a cent of the lowest regular-session price in Yahoo's hourly bars on every "
      "session from August 26", len(low_checked) == 31 and all(abs(g) <= 0.01 + 1e-9 for g in low_gap.values()),
      f"{len(low_checked)} sessions, equal to Yahoo's rounded to the cent on "
      f"{sum(abs(px[d]['low'] - round(reg_low[d], 2)) < 1e-9 for d in low_checked)}, a cent lower on "
      f"{sum(px[d]['low'] - round(reg_low[d], 2) < -0.005 for d in low_checked)}")
check("73 USDE sessions from June 26 to October 8, none on a weekend",
      len(sessions) == 73 and all(d.weekday() < 5 for d in sessions))
PRIOR = {d: (sessions[i - 1] if i else max(x for x in px if x < FIRST)) for i, d in enumerate(sessions)}
check("the session before June 26 is June 25, TLGY's last session, which S&P Global's USDE history carries",
      PRIOR[FIRST] == date(2026, 6, 25), f"close ${px[date(2026, 6, 25)]['close']}")

# ---------------------------------------------------------------- FINRA daily short sale volume
daily = {}
warrant_daily = {}
for r in read_csv("finra_daily_short_volume.csv"):
    row = {"short": float(r["short_volume"]), "exempt": float(r["short_exempt_volume"]),
           "total": float(r["total_volume"]), "market": r["market"]}
    (daily if r["symbol"] == "USDE" else warrant_daily)[d8(r["date"])] = row
check("one FINRA row for USDE on each session and none on other days", sorted(daily) == sessions,
      f"{len(daily)} rows")
check("in every row the exempt volume is within the short volume and the short volume within the total",
      all(0 <= v["exempt"] <= v["short"] <= v["total"] for v in list(daily.values()) + list(warrant_daily.values())))
over_total = [v for v in list(daily.values()) + list(warrant_daily.values()) if v["short"] + v["exempt"] > v["total"] + 1e-6]
check("the short volume includes the short exempt volume, as FINRA's file layout says, since the two together exceed "
      "the total in some rows", len(over_total) > 0, f"{len(over_total)} USDE and USDEW rows")

# ---------------------------------------------------------------- FINRA short interest
si = sorted(json.load(open(os.path.join(INP, "finra_short_interest_usde.json"))), key=lambda r: r["settlementDate"])
siw = sorted(json.load(open(os.path.join(INP, "finra_short_interest_usdew.json"))), key=lambda r: r["settlementDate"])
SCHEDULE = ["2026-06-30", "2026-07-15", "2026-07-31", "2026-08-14", "2026-08-31", "2026-09-15", "2026-09-30"]
got = [r["settlementDate"] for r in si]
check("one USDE short interest record for each settlement date FINRA had published from June 30, for StablecoinX's "
      "Class A stock",
      len(got) >= 6 and got == SCHEDULE[:len(got)] and [r["settlementDate"] for r in siw] == got
      and all(r["symbolCode"] == "USDE" and r["issueName"].startswith("StablecoinX Inc. Class A") for r in si),
      f"{len(got)} records, {got[0]} to {got[-1]}")
rechecks = read_csv("finra_recheck_log.csv")
LAST_CHECK = rechecks[-1]["checked_at_utc"]
check("FINRA's checks progress to the latest settlement date in the saved records",
      all(not r["latest_settlement_date"] or r["latest_settlement_date"] <= got[-1] for r in rechecks)
      and rechecks[-1]["latest_settlement_date"] == got[-1]
      and rechecks[-1]["status"] == "200" and int(rechecks[-1]["records"]) == len(got),
      f"last checked {LAST_CHECK}")
check("each record's previous position equals the record before it, and the change adds up",
      si[0]["previousShortPositionQuantity"] == 0
      and all(b["previousShortPositionQuantity"] == a["currentShortPositionQuantity"] for a, b in zip(si, si[1:]))
      and all(r["changePreviousNumber"] == r["currentShortPositionQuantity"] - r["previousShortPositionQuantity"]
              for r in si))
check("no record carries a revision or split flag", all(r["revisionFlag"] is None and r["stockSplitFlag"] is None
                                                        for r in si + siw))
check("every settlement date was a USDE session", all(date.fromisoformat(r["settlementDate"]) in px for r in si))

cycles = []
prev = PRIOR[FIRST]
for r in si:
    s = date.fromisoformat(r["settlementDate"])
    days = [d for d in sessions if prev < d <= s]
    adv = statistics.mean(px[d]["volume"] for d in days)
    q = r["currentShortPositionQuantity"]
    cycles.append({
        "settlement": s, "short_interest": q, "change": r["changePreviousNumber"], "previous": r["previousShortPositionQuantity"],
        "close": px[s]["close"], "value_usd": q * px[s]["close"],
        "of_freely_tradable": q / FREELY_TRADABLE, "of_class_a": q / CLASS_A_AUG28,
        "finra_adv": r["averageDailyVolumeQuantity"], "finra_days_to_cover": r["daysToCoverQuantity"],
        "sessions": len(days), "first": days[0], "spglobal_adv": adv, "days_to_cover": q / adv,
        "finra_adv_over_spglobal": r["averageDailyVolumeQuantity"] / adv,
    })
    prev = s
check("FINRA's average daily volume is within 4% of S&P Global's average over the same cycle, after the first",
      all(abs(c["finra_adv_over_spglobal"] - 1) < 0.04 for c in cycles[1:]),
      ", ".join(f"{c['finra_adv_over_spglobal']:.3f}" for c in cycles))
check("FINRA lists days to cover as 1 on every date", all(c["finra_days_to_cover"] == 1 for c in cycles))
say()
say("FINRA short interest, USDE")
for c in cycles:
    say(f"  {c['settlement']}: {c['short_interest']:,} shares ({c['change']:+,}), {pct(c['of_freely_tradable'])} of freely "
        f"tradable, {pct(c['of_class_a'])} of Class A; close ${c['close']}, ${c['value_usd']:,.0f}; cycle {c['first']} to "
        f"{c['settlement']}, {c['sessions']} sessions, average volume {c['spglobal_adv']:,.0f} (FINRA {c['finra_adv']:,}), "
        f"days to cover {c['days_to_cover']:.2f}")
last = cycles[-1]
peak_close = max(sessions, key=lambda d: px[d]["close"])
after = [d for d in sessions if d > last["settlement"]]
say(f"  window peak close ${px[peak_close]['close']} on {peak_close}; {LAST} close ${px[LAST]['close']}")
say("  USDEW warrants: " + "; ".join(f"{r['settlementDate']} {r['currentShortPositionQuantity']:,}" for r in siw))

# ---------------------------------------------------------------- daily short sale volume and the price test
rows = []
for d in sessions:
    p, f = px[d], daily[d]
    prior_close = px[PRIOR[d]]["close"]
    rows.append({"date": d, "close": p["close"], "prior_close": prior_close, "low": p["low"], "volume": p["volume"],
                 "trigger": p["low"] <= 0.9 * prior_close, "finra_total": f["total"], "short": f["short"],
                 "exempt": f["exempt"], "short_share": f["short"] / f["total"]})
for i, r in enumerate(rows):
    r["in_effect"] = r["trigger"] or (i > 0 and rows[i - 1]["trigger"])
tot_volume = sum(r["volume"] for r in rows)
tot_finra = sum(r["finra_total"] for r in rows)
tot_short = sum(r["short"] for r in rows)
tot_exempt = sum(r["exempt"] for r in rows)
in_effect = [r for r in rows if r["in_effect"]]
exempt_in_effect = sum(r["exempt"] for r in in_effect)
shares = [r["short_share"] for r in rows]
busiest = max(rows, key=lambda r: r["volume"])
flow = {
    "sessions": len(rows), "spglobal_volume": tot_volume, "finra_volume": tot_finra, "finra_short": tot_short,
    "finra_exempt": tot_exempt, "finra_share_of_spglobal": tot_finra / tot_volume, "short_share": tot_short / tot_finra,
    "median_daily_short_share": statistics.median(shares), "min_daily_short_share": min(shares),
    "max_daily_short_share": max(shares),
    "min_share_date": str(min(rows, key=lambda r: r["short_share"])["date"]),
    "max_share_date": str(max(rows, key=lambda r: r["short_share"])["date"]),
    "days_over_half": sum(1 for x in shares if x > 0.5),
    "turnover_of_freely_tradable": tot_volume / FREELY_TRADABLE,
    "busiest_date": str(busiest["date"]), "busiest_volume": busiest["volume"],
    "busiest_over_freely_tradable": busiest["volume"] / FREELY_TRADABLE,
    "busiest_move": busiest["close"] / busiest["prior_close"] - 1,
    "trigger_sessions": sum(r["trigger"] for r in rows), "in_effect_sessions": len(in_effect),
    "exempt_in_effect": exempt_in_effect, "exempt_in_effect_share": exempt_in_effect / tot_exempt,
    "exempt_share_of_short": tot_exempt / tot_short,
}
for c in cycles:
    cyc = [r for r in rows if c["first"] <= r["date"] <= c["settlement"]]
    c["finra_short_volume"] = sum(r["short"] for r in cyc)
    c["finra_volume"] = sum(r["finra_total"] for r in cyc)
    c["spglobal_volume"] = sum(r["volume"] for r in cyc)
# Trades settle one business day after they are made, so the change in short interest from one settlement date to the
# next comes from trades made from the earlier settlement date through the session before the later one. FINRA's
# settlement date before June 30 was June 15.
prev_settle = date(2026, 6, 15)
for c in cycles:
    win = [r for r in rows if prev_settle <= r["date"] < c["settlement"]]
    c["trade_window_first"], c["trade_window_last"], c["trade_window_sessions"] = win[0]["date"], win[-1]["date"], len(win)
    c["finra_short_volume_trade_window"] = sum(r["short"] for r in win)
    prev_settle = c["settlement"]
top_exempt = max(rows, key=lambda r: r["exempt"])
flow["top_exempt_date"], flow["top_exempt_volume"] = str(top_exempt["date"]), top_exempt["exempt"]
flow["top_exempt_share"] = top_exempt["exempt"] / tot_exempt
flow["exempt_in_effect_share_without_top"] = (exempt_in_effect - top_exempt["exempt"] * top_exempt["in_effect"]) / (
    tot_exempt - top_exempt["exempt"])
aug = next(c for c in cycles if c["settlement"] == date(2026, 8, 31))
flow["aug31_cycle_average_without_busiest"] = (aug["spglobal_volume"] - busiest["volume"]) / (aug["sessions"] - 1)
flow["aug31_days_to_cover_without_busiest"] = aug["short_interest"] / flow["aug31_cycle_average_without_busiest"]
low_close = min(rows, key=lambda r: r["close"])
flow["lowest_close_date"], flow["lowest_close"] = str(low_close["date"]), low_close["close"]
# The first session's trigger compares USDE's low with the $9.40 close of June 25 in S&P Global's USDE history,
# which appears to be TLGY Acquisition Corp.'s last close.
# If no prior close applied that day, June 26 drops out and every other session keeps its status.
trig_alt = [r["trigger"] and i > 0 for i, r in enumerate(rows)]
alt = [r for i, r in enumerate(rows) if trig_alt[i] or (i > 0 and trig_alt[i - 1])]
flow["without_first_trigger"] = {
    "trigger_sessions": sum(trig_alt), "in_effect_sessions": len(alt),
    "exempt_in_effect_share": sum(r["exempt"] for r in alt) / tot_exempt}
# How far the count moves if any session's low were a cent higher or lower, each session on its own or together
def in_effect_count(tr):
    return sum(1 for i in range(len(tr)) if tr[i] or (i > 0 and tr[i - 1]))


cent = [{round(r["low"] + dl, 2) <= 0.9 * r["prior_close"] for dl in (-0.01, 0.0, 0.01)} for r in rows]
movable = [i for i, s in enumerate(cent) if len(s) > 1]
counts = set()
for k in range(2 ** len(movable)):
    tr = [r["trigger"] for r in rows]
    for j, i in enumerate(movable):
        tr[i] = bool(k >> j & 1)
    counts.add(in_effect_count(tr))
flow["one_cent_low"] = {"sessions_that_can_flip": [str(rows[i]["date"]) for i in movable],
                        "in_effect_min": min(counts), "in_effect_max": max(counts)}
outside = [r for r in rows if not r["in_effect"]]
flow["sessions_outside_with_exempt"] = sum(1 for r in outside if r["exempt"] > 0)
flow["sessions_outside"] = len(outside)
check("the busiest session fell in the cycle to August 31", aug["first"] <= busiest["date"] <= aug["settlement"])
check("the price test was in effect on every session with a trigger and on the session after",
      all(rows[i + 1]["in_effect"] for i, r in enumerate(rows[:-1]) if r["trigger"]))
say()
say("FINRA daily short sale volume, regular-hours trades reported to FINRA's facilities")
say(f"  {flow['sessions']} sessions: {tot_finra:,.0f} shares, {pct(flow['finra_share_of_spglobal'], 1)} of S&P Global's "
    f"{tot_volume:,} shares; marked short {tot_short:,.0f}, {pct(flow['short_share'], 1)}; short exempt {tot_exempt:,.0f}")
say(f"  daily short share median {pct(flow['median_daily_short_share'], 1)}, from {pct(flow['min_daily_short_share'], 1)} "
    f"on {flow['min_share_date']} to {pct(flow['max_daily_short_share'], 1)} on {flow['max_share_date']}; over half on "
    f"{flow['days_over_half']} of {flow['sessions']}")
say(f"  S&P Global volume {tot_volume:,} shares, {flow['turnover_of_freely_tradable']:.1f} times the freely tradable "
    f"shares; busiest {flow['busiest_date']}, {flow['busiest_volume']:,} shares, "
    f"{flow['busiest_over_freely_tradable']:.1f} times, close {pct(flow['busiest_move'], 1)}")
for c in cycles:
    say(f"  cycle to {c['settlement']}: {c['finra_short_volume']:,.0f} shares marked short in FINRA's files; trades "
        f"{c['trade_window_first']} to {c['trade_window_last']}, {c['trade_window_sessions']} sessions, "
        f"{c['finra_short_volume_trade_window']:,.0f} marked short; short interest change {c['change']:+,}")
say(f"  cycle to August 31 without {flow['busiest_date']}: average {flow['aug31_cycle_average_without_busiest']:,.0f} a day")
say(f"  price test triggered on {flow['trigger_sessions']} sessions and in effect on {flow['in_effect_sessions']}; "
    f"short exempt volume on those sessions {exempt_in_effect:,.0f}, {pct(flow['exempt_in_effect_share'], 1)} of the total")
say(f"  most short exempt volume in one session: {flow['top_exempt_date']}, {flow['top_exempt_volume']:,.0f} shares, "
    f"{pct(flow['top_exempt_share'], 1)} of the total; without it the sessions with the test carried "
    f"{pct(flow['exempt_in_effect_share_without_top'], 1)}")
w = flow["without_first_trigger"]
say(f"  without a trigger on June 26: triggered on {w['trigger_sessions']}, in effect on {w['in_effect_sessions']}, "
    f"{pct(w['exempt_in_effect_share'], 1)} of short exempt volume")
say(f"  sessions without the price test that still had short exempt volume: {flow['sessions_outside_with_exempt']} of "
    f"{flow['sessions_outside']}")
say(f"  a one-cent move in any session's low: trigger can change on {', '.join(flow['one_cent_low']['sessions_that_can_flip'])}; "
    f"in effect on {flow['one_cent_low']['in_effect_min']} to {flow['one_cent_low']['in_effect_max']} sessions")
say(f"  lowest close ${flow['lowest_close']} on {flow['lowest_close_date']}; cycle to August 31 without the busiest "
    f"session, days to cover {flow['aug31_days_to_cover_without_busiest']:.2f}")

# ---------------------------------------------------------------- stop before writing if any check failed
say()
if FAILED:
    say(f"{len(FAILED)} check(s) failed: {', '.join(FAILED)}. Nothing was written to out/.")
    sys.exit(1)

os.makedirs(OUT, exist_ok=True)
write_csv("short_interest.csv",
          ["settlement_date", "short_interest_shares", "change_shares", "share_of_freely_tradable_aug28",
           "share_of_class_a_aug28", "usde_close", "value_at_close_usd", "cycle_first_session", "cycle_sessions",
           "spglobal_average_daily_volume", "finra_average_daily_volume", "days_to_cover", "finra_days_to_cover",
           "finra_short_volume_in_cycle"],
          [[c["settlement"], c["short_interest"], c["change"], r6(c["of_freely_tradable"]), r6(c["of_class_a"]), c["close"],
            round(c["value_usd"], 2), c["first"], c["sessions"], round(c["spglobal_adv"], 1), c["finra_adv"],
            round(c["days_to_cover"], 4), c["finra_days_to_cover"], round(c["finra_short_volume"], 2)] for c in cycles])
write_csv("daily_short_volume.csv",
          ["date", "usde_close", "prior_close", "low", "spglobal_volume", "price_test_triggered_by_daily_low",
           "price_test_in_effect_by_daily_low",
           "finra_total_volume", "finra_short_volume", "finra_short_exempt_volume", "short_share_of_finra_volume"],
          [[r["date"], r["close"], r["prior_close"], r["low"], r["volume"], int(r["trigger"]), int(r["in_effect"]),
            r["finra_total"], r["short"], r["exempt"], r6(r["short_share"])] for r in rows])
write_csv("chart_short_interest.csv",
          ["date", "usde_close", "short_interest_shares"],
          [[r["date"], r["close"], next((c["short_interest"] for c in cycles if c["settlement"] == r["date"]), "")]
           for r in rows])
results = {
    "window": {"first_session": str(FIRST), "last_session": str(LAST), "sessions": len(sessions)},
    "shares": {"freely_tradable_aug28": FREELY_TRADABLE, "class_a_aug28": CLASS_A_AUG28, "class_a_oct8": CLASS_A_OCT8},
    "short_interest": cycles,
    "warrants_short_interest": [{"settlement": r["settlementDate"], "short_interest": r["currentShortPositionQuantity"]}
                                for r in siw],
    "last_check_utc": LAST_CHECK,
    "last_settlement_alternatives": {"settlement": str(last["settlement"]), "short_interest": last["short_interest"],
                                     "ethena_registered": ETHENA,
                                     "of_freely_tradable_and_ethena": last["short_interest"] / (FREELY_TRADABLE + ETHENA),
                                     "of_class_a": last["short_interest"] / CLASS_A_AUG28,
                                     "of_freely_tradable_finra_adv_days": last["short_interest"] / last["finra_adv"]},
    "after_last_settlement": {"peak_close_date": str(peak_close), "peak_close": px[peak_close]["close"],
                              "last_close": px[LAST]["close"], "sessions_after": len(after)},
    "daily_flow": flow,
}
with open(os.path.join(OUT, "results.json"), "w") as f:
    json.dump(results, f, indent=1, default=str)
    f.write("\n")
say("All checks passed. Tables written to out/.")
with open(os.path.join(OUT, "run_log.txt"), "w") as f:
    f.write("\n".join(LOG) + "\n")
