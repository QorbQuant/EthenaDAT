#!/usr/bin/env python3
"""
USDe's supply against the ENA fee switch milestones, read onchain.

Reads inputs/chain/day_reads.csv, USDe's total supply on Ethereum at the last block of every UTC day from
January 1, 2024, and inputs/chain/read_block.csv, the supply at one block after the last day, and compares them
with the milestones that ENA holders approved for ENA buybacks. Every figure is exact: supplies are integers of
USDe's smallest unit and averages are fractions. Python 3.8 or later, standard library only, no network.

If any check fails the script writes out/run_log_failed.txt and stops before writing its tables. The tables,
out/results.json and out/run_log.txt are built in memory and written together at the end, so a failure leaves
out/ as the last clean run wrote it.
"""
import csv
import hashlib
import io
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, "inputs")
CH = os.path.join(INP, "chain")
WEB = os.path.join(INP, "web")
OUT = os.path.join(HERE, "out")

USDE = "0x4c9edd5852cd905f086c759e8383e09bff1e68b3"
UNIT = 10 ** 18
B = 10 ** 9
# The milestones of the approved schedule: from each USDe supply, the share of net revenue for ENA buybacks.
RUNGS = [(F(75, 10) * B, 5), (F(10 * B), 10), (F(15 * B), 15), (F(20 * B), 20), (F(25 * B), 25)]
# Ethena Labs' illustrative table at a 6.0% protocol APY, and Blockworks Advisory's table at 6% and 4.60%.
ETHENA_TABLE = {7.5: ("450", "22.5"), 10: ("600", "60"), 15: ("900", "135"), 20: ("1,200", "240"), 25: (None, None)}
BLOCKWORKS_AT = {7.5: ("22.5", "17.3"), 10: ("60.0", "46.0"), 15: ("135.0", "103.5"), 20: ("240.0", "184.1")}
# Blockworks Advisory's backtest panel and its table of supply measures.
PANEL = ("2024-09-19", "2026-08-24")
FIRST_CROSS_PUBLISHED = "2025-07-27"
BLOCKWORKS = {1: (0, 117, 4), 14: (7, 118, 4), 30: (14, 120, 4), 90: (34, 141, 4)}
BLOCKWORKS_PEAK = {14: ("14.65", "2025-10"), 90: ("12.38", None)}
BLOCKWORKS_TODAY = ("2026-08-27", "4.07")
# SHA-256 of the browser scripts, checked in the browser against these files before they ran.
SCRIPTS = {
    "browser/usde_supply_read.js": "5a2517420ee2b7c11c6e2994ea8b44c9c8acd873daf9b727aa7b2107fff9deb1",
    "browser/bundle_files.js": "609165594153e05be3f4caf1c69f8400acf28f054819ea0d777b0d916196d8e3",
    "browser/finality_check.js": "7bb92722d53d632cd4ba7547c2353592a1f3a177b4035d555150e149ccc59b22",
}
# SHA-256 of finality_check.json as the browser computed it.
FINALITY_DIGEST = "98fd7d3ca05ba344d5f279953108d0debe9e25e73f5f7f2dfd94e1088ed7802e"

LOG, CHECKS = [], []


def log(msg):
    LOG.append(msg)
    print(msg)


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    log(("PASS " if ok else "FAIL ") + name + (" | " + detail if detail else ""))


def sha256_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def read_csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


PENDING = []  # the files of out/, written together only after every check has passed and every table is built


def write_csv(p, header, rows):
    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    PENDING.append((p, buf.getvalue()))


def write_pending():
    for p, text in PENDING:
        with open(p + ".tmp", "w", newline="", encoding="utf-8") as f:
            f.write(text)
    for p, _ in PENDING:
        os.replace(p + ".tmp", p)


def plain(x, places):
    """A fraction rounded half up to the given places, as text."""
    q = F(10) ** places
    n = x * q
    r = (n.numerator * 2 + n.denominator) // (2 * n.denominator) if n >= 0 else -((-n.numerator * 2 + n.denominator) // (2 * n.denominator))
    s = str(abs(r)).rjust(places + 1, "0")
    out = s[:-places] + "." + s[-places:] if places else s
    return ("-" if r < 0 else "") + out


def fmt(x, places=2):
    s = plain(x, places)
    neg = s.startswith("-")
    s = s.lstrip("-")
    whole, _, frac = s.partition(".")
    whole = "{:,}".format(int(whole))
    return ("-" if neg else "") + whole + ("." + frac if frac else "")


def pct(x, places=2):
    return plain(x * 100, places)


def iso(ts):
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def day_of(s):
    return date.fromisoformat(s)


def rung(x):
    take = 0
    for threshold, rate in RUNGS:
        if x >= threshold:
            take = rate
    return take


def main():
    os.makedirs(OUT, exist_ok=True)
    failed_log = os.path.join(OUT, "run_log_failed.txt")
    if os.path.exists(failed_log):
        os.remove(failed_log)
    log("USDe supply against the ENA fee switch milestones, run at " + datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))

    # ---- inputs -----------------------------------------------------------------------------------------
    man = read_csv(os.path.join(INP, "manifest.csv"))
    bad = [m["path"] for m in man if not os.path.exists(os.path.join(HERE, m["path"]))
           or os.path.getsize(os.path.join(HERE, m["path"])) != int(m["bytes"]) or sha256_file(os.path.join(HERE, m["path"])) != m["sha256"]]
    check("every input matches its size and SHA-256 in inputs/manifest.csv", not bad, "%d files%s" % (len(man), ", failed " + ", ".join(bad) if bad else ""))
    digests = json.load(open(os.path.join(CH, "browser_digests.json"), encoding="utf-8"))
    bad = [k for k, v in digests.items() if sha256_file(os.path.join(CH, k)) != v]
    check("the browser's files match the SHA-256 digests the browser computed", not bad and len(digests) == 5, "%d files" % len(digests))
    bad = [k for k, v in SCRIPTS.items() if sha256_file(os.path.join(HERE, k)) != v]
    check("the scripts in browser/ match the SHA-256 digests recorded when the browser ran them", not bad, ", ".join(bad))

    run = json.load(open(os.path.join(CH, "run.json"), encoding="utf-8"))
    rows = read_csv(os.path.join(CH, "day_reads.csv"))
    days = [r["day"] for r in rows]
    first, last = day_of(days[0]), day_of(days[-1])
    expect = [(first + timedelta(days=i)).isoformat() for i in range((last - first).days + 1)]
    check("the day ends run without a gap from January 1, 2024 to the day before the read",
          days == expect and days[0] == "2024-01-01" and run["days"] == len(days) and run["first_day"] == days[0] and run["last_day"] == days[-1],
          "%d days, %s to %s" % (len(days), days[0], days[-1]))
    ok = True
    prev = None
    for r in rows:
        ts, t, tn, b = int(r["day_end_unix"]), int(r["block_time_unix"]), int(r["next_block_time_unix"]), int(r["block"])
        ok = ok and t <= ts < tn and ts == int(datetime.fromisoformat(r["day"] + "T23:59:59+00:00").timestamp())
        ok = ok and (prev is None or b > prev)
        prev = b
    check("each day is read at the last block at or before 23:59:59 UTC, whose next block came after it", ok)
    check("the second archive RPC gave the same supply and the same block hash on every day",
          all(r["same_supply_second_rpc"] == "1" and r["same_hash_second_rpc"] == "1" for r in rows)
          and run["days_same_supply"] == run["days_same_hash"] == len(rows),
          "%d of %d days" % (run["days_same_supply"], len(rows)))
    fin_path = os.path.join(CH, "finality_check.json")
    fin = json.load(open(fin_path, encoding="utf-8"))
    last_block = max(int(r["block"]) for r in rows)
    check("after the read, every day-end block was at or below the finalized block on two RPCs and the day-end block hashes were unchanged",
          sha256_file(fin_path) == FINALITY_DIGEST and fin["same_digest"] is True
          and fin["sha256_day_end_block_hashes_now"] == fin["sha256_day_end_block_hashes_in_run"] == run["sha256_primary_day_end_block_hashes"]
          and fin["day_end_blocks"] == len(rows) and fin["last_day_end_block"] == last_block
          and len(fin["finalized"]) == 2 and all(f["block"] >= last_block for f in fin["finalized"]),
          "finalized block %s at %s, last day-end block %s" % ("{:,}".format(min(f["block"] for f in fin["finalized"])),
                                                               iso(min(f["block_time_unix"] for f in fin["finalized"])), "{:,}".format(last_block)))
    rb = read_csv(os.path.join(CH, "read_block.csv"))
    check("two RPCs served the same read block and gave the same supply there",
          len(rb) == 2 and rb[0]["block_hash"] == rb[1]["block_hash"] and rb[0]["usde_total_supply_raw"] == rb[1]["usde_total_supply_raw"]
          and rb[0]["usde_decimals"] == rb[1]["usde_decimals"] == "18" and int(rb[0]["block"]) == run["read_block"],
          "block %s at %s" % ("{:,}".format(int(rb[0]["block"])), iso(rb[0]["block_time_unix"])))
    check("the read block came after the last day end", int(rb[0]["block"]) > int(rows[-1]["block"]) and int(rb[0]["block_time_unix"]) > int(rows[-1]["day_end_unix"]))

    # ---- the daily series -----------------------------------------------------------------------------
    S = [F(int(r["usde_total_supply_raw"]), UNIT) for r in rows]
    check("every supply read is a positive whole number of USDe's smallest unit", all(int(r["usde_total_supply_raw"]) > 0 for r in rows))
    idx = {d: i for i, d in enumerate(days)}

    def avg(i, n):
        return None if i + 1 < n else sum(S[i - n + 1:i + 1], F(0)) / n

    A = {n: [avg(i, n) for i in range(len(S))] for n in (1, 14, 30, 90)}

    # ---- the published facts, checked against the chain -------------------------------------------------
    cross = next(d for i, d in enumerate(days) if S[i] >= RUNGS[0][0])
    check("daily supply first reached $7.5 billion on July 27, 2025, the date Blockworks Advisory gave", cross == FIRST_CROSS_PUBLISHED,
          "%s, %s USDe, the day before %s" % (cross, fmt(S[idx[cross]]), fmt(S[idx[cross] - 1])))
    p0, p1 = idx[PANEL[0]], idx[PANEL[1]]
    measures = []
    for n in (1, 14, 30, 90):
        rr = [rung(A[n][i]) for i in range(p0, p1 + 1)]
        active = [days[p0 + k] for k, v in enumerate(rr) if v > 0]
        changes = sum(1 for k in range(1, len(rr)) if rr[k] != rr[k - 1])
        to_first = (day_of(active[0]) - day_of(FIRST_CROSS_PUBLISHED)).days if active else None
        peak_i = max(range(p0, p1 + 1), key=lambda i: A[n][i])
        measures.append({"n": n, "days_to_first": to_first, "active": len(active), "changes": changes, "first": active[0], "last": active[-1],
                         "peak": A[n][peak_i], "peak_day": days[peak_i], "rungs": sorted(set(rr))})
    m = {x["n"]: x for x in measures}
    for x in measures:
        log("panel %s to %s, %s: first active %s, %d days after July 27, 2025, %d active days, %d rung changes, peak %s on %s, rungs %s" % (
            PANEL[0], PANEL[1], "daily" if x["n"] == 1 else "%d-day average" % x["n"], x["first"], x["days_to_first"], x["active"], x["changes"],
            fmt(x["peak"] / B, 3) + "B", x["peak_day"], x["rungs"]))
    same = [n for n in (1, 14, 30, 90) if (m[n]["days_to_first"], m[n]["active"], m[n]["changes"]) == BLOCKWORKS[n]]
    check("over Blockworks Advisory's panel the onchain supply reproduces its days to the first buyback, active days and rung changes for the daily, 14, 30 and 90 day measures",
          len(same) == 4, "%d of 4 measures equal" % len(same))
    check("the 14 day average peaked at $14.65 billion in October 2025 and the 90 day average at $12.38 billion, as Blockworks Advisory wrote",
          plain(m[14]["peak"] / B, 2) == "14.65" and m[14]["peak_day"].startswith("2025-10") and plain(m[90]["peak"] / B, 2) == "12.38",
          "%s on %s, %s on %s" % (fmt(m[14]["peak"] / B, 4), m[14]["peak_day"], fmt(m[90]["peak"] / B, 4), m[90]["peak_day"]))
    vote_day = BLOCKWORKS_TODAY[0]
    sv = S[idx[vote_day]]
    check("on August 27, 2026, the day Blockworks Advisory put USDe's supply at $4.07 billion, the onchain supply was within 1% of it",
          abs(sv / (F(407, 100) * B) - 1) < F(1, 100), "%s USDe at the day's end, %s USDe the day before" % (fmt(sv), fmt(S[idx[vote_day] - 1])))

    # ---- where the supply stands ------------------------------------------------------------------------
    now = F(int(rb[0]["usde_total_supply_raw"]), UNIT)
    li = len(S) - 1
    a14 = A[14][li]
    gaps = []
    for threshold, rate in RUNGS:
        gaps.append((threshold, rate, threshold - a14, threshold / a14 - 1, threshold - S[li], threshold / S[li] - 1))
    log("read block %s: %s USDe. Day end %s: %s USDe, 14 day average %s" % (rb[0]["block"], fmt(now), days[li], fmt(S[li]), fmt(a14)))
    active14_all = [days[i] for i in range(len(S)) if A[14][i] is not None and A[14][i] >= RUNGS[0][0]]
    runs = []
    for d in active14_all:
        if runs and (day_of(d) - day_of(runs[-1][1])).days == 1:
            runs[-1][1] = d
        else:
            runs.append([d, d])
    check("the 14 day average was at or above $7.5 billion in one unbroken stretch, and below it on every day since",
          len(runs) == 1 and day_of(runs[0][1]) < last, "%s to %s, %d days" % (runs[0][0], runs[0][1], len(active14_all)))
    check("at the last day end the 14 day average was below the first milestone, so the schedule took nothing", rung(a14) == 0 and rung(S[li]) == 0 and rung(now) == 0,
          "%s, %s short of $7.5 billion" % (fmt(a14), fmt(RUNGS[0][0] - a14)))
    # Daily supply above each milestone in the whole series.
    days_at = {rate: sum(1 for x in S if rung(x) >= rate) for _, rate in RUNGS}
    days14_at = {rate: sum(1 for x in A[14] if x is not None and rung(x) >= rate) for _, rate in RUNGS}
    top_i = max(range(len(S)), key=lambda i: S[i])
    log("highest day-end supply %s on %s. Days at or above each milestone, daily %s, 14 day average %s" % (fmt(S[top_i]), days[top_i], days_at, days14_at))

    # How long the supply took in 2025 to rise from today's level to $7.5 billion.
    ci = idx[cross]
    start_i = max(i for i in range(ci) if S[i] <= S[li])
    log("in 2025 the day-end supply last stood at or below %s on %s (%s) and reached $7.5 billion %d days later" % (
        fmt(S[li]), days[start_i], fmt(S[start_i]), ci - start_i))
    a14_start = max(i for i in range(ci) if A[14][i] is not None and A[14][i] <= a14)
    a14_cross = next(i for i in range(len(S)) if A[14][i] is not None and A[14][i] >= RUNGS[0][0])
    log("the 14 day average last stood at or below %s on %s and reached $7.5 billion on %s, %d days later" % (
        fmt(a14), days[a14_start], days[a14_cross], a14_cross - a14_start))
    check("in 2025 the 14 day average first reached $7.5 billion on August 3, seven days after daily supply, as the 14 day row of the table implies",
          days[a14_cross] == "2025-08-03" and a14_cross - ci == 7)
    # The largest rise over 30 and 90 days.
    best = {}
    for n in (30, 90):
        k = max(range(n, len(S)), key=lambda i: S[i] / S[i - n])
        best[n] = (days[k - n], days[k], S[k] / S[k - n] - 1, S[k] - S[k - n])
        log("largest %d day rise in day-end supply: %s to %s, %s%%, %s USDe" % (n, best[n][0], best[n][1], pct(best[n][2], 1), fmt(best[n][3])))
    # Since the vote opened.
    since_vote = S[li] / sv - 1
    # The fall from the peak, the low after it, and the rise since.
    low_i = min(range(top_i, len(S)), key=lambda i: S[i])
    log("after the peak the day-end supply fell to %s on %s, %s%% below the peak, and rose %s%% from there to %s" % (
        fmt(S[low_i]), days[low_i], pct(1 - S[low_i] / S[top_i], 2), pct(S[li] / S[low_i] - 1, 2), days[li]))
    recent_i = max(range(len(S) - 60, len(S)), key=lambda i: S[i])
    log("highest day-end supply in the last 60 days %s on %s" % (fmt(S[recent_i]), days[recent_i]))
    below_since = [days[i] for i in range(idx[runs[0][1]] + 1, len(S))]
    check("the 14 day average was below $7.5 billion on all %d days from the day after its last day above it to the last day" % len(below_since),
          all(A[14][idx[d]] < RUNGS[0][0] for d in below_since))
    ten = [days[i] for i in range(len(S)) if A[14][i] is not None and A[14][i] >= RUNGS[1][0]]
    log("14 day average at or above $10 billion on %d days, %s to %s" % (len(ten), ten[0], ten[-1]))
    check("the 14 day average was at or above $10 billion in one unbroken stretch",
          (day_of(ten[-1]) - day_of(ten[0])).days + 1 == len(ten))
    # From the day voting opened, no measure reached the first milestone.
    vo = idx[vote_day]
    tops = {n: max(A[n][i] for i in range(vo, len(S))) for n in (1, 14, 30, 90)}
    check("from August 27, 2026, when voting opened, to the last day, the day-end supply and its 14, 30 and 90 day averages stayed below $7.5 billion on every day",
          all(t < RUNGS[0][0] for t in tops.values()), ", ".join("%s %s" % ("daily" if n == 1 else "%d day" % n, fmt(t / B, 3) + "B") for n, t in tops.items()))
    # The 14 days in the last average.
    last14 = S[li - 13:li + 1]
    check("the last 14 day average is the sum of the 14 day-end supplies from %s to %s over 14" % (days[li - 13], days[li]),
          sum(last14, F(0)) / 14 == a14)
    log("day-end supply %s on %s against %s on %s, %s%%" % (fmt(S[li]), days[li], fmt(sv), vote_day, pct(since_vote, 1)))

    # Every check has run. If any failed, stop here, before any table in out/ is written.
    if not all(ok for _, ok, _ in CHECKS):
        with open(failed_log, "w", encoding="utf-8") as f:
            f.write("\n".join(LOG) + "\n")
        print("\n%d of %d checks failed; out/ not updated" % (sum(1 for c in CHECKS if not c[1]), len(CHECKS)))
        sys.exit(1)

    # ---- tables ----------------------------------------------------------------------------------------
    daily_rows = []
    for i, r in enumerate(rows):
        daily_rows.append([r["day"], r["block"], iso(r["block_time_unix"]), plain(S[i], 6)] +
                          [plain(A[n][i], 6) if A[n][i] is not None else "" for n in (14, 30, 90)] +
                          [rung(S[i]), rung(A[14][i]) if A[14][i] is not None else ""])
    write_csv(os.path.join(OUT, "daily_supply.csv"), ["day", "block", "block_time_utc", "usde_supply", "avg_14d", "avg_30d", "avg_90d",
                                                      "take_pct_daily", "take_pct_14d"], daily_rows)
    meas_rows = []
    for x in measures:
        pub = BLOCKWORKS[x["n"]]
        meas_rows.append(["daily" if x["n"] == 1 else "%d day average" % x["n"], x["first"], x["last"], x["days_to_first"], pub[0], x["active"], pub[1],
                          x["changes"], pub[2], plain(x["peak"] / B, 4), x["peak_day"], BLOCKWORKS_PEAK.get(x["n"], ("", ""))[0]])
    write_csv(os.path.join(OUT, "supply_measures.csv"), ["measure", "first_active_day", "last_active_day", "days_to_first", "days_to_first_published",
                                                          "active_days", "active_days_published", "rung_changes", "rung_changes_published",
                                                          "peak_billion", "peak_day", "peak_published_billion"], meas_rows)
    ms_rows = []
    for threshold, rate, g14, n14, gd, nd in gaps:
        key = float(threshold / B)
        et = ETHENA_TABLE[key]
        bw = BLOCKWORKS_AT.get(key, (None, None))
        ms_rows.append([plain(threshold / B, 1), rate, et[0] or "", et[1] or "", bw[0] or "", bw[1] or "", plain(g14, 2), pct(n14, 2), plain(gd, 2), pct(nd, 2),
                        days_at[rate], days14_at[rate]])
    write_csv(os.path.join(OUT, "milestones.csv"), ["usde_supply_billion", "take_pct", "ethena_revenue_6pct_musd", "ethena_buyback_6pct_musd",
                                                     "blockworks_buyback_6pct_musd", "blockworks_buyback_460_musd", "gap_from_14d_avg_usd",
                                                     "growth_needed_14d_pct", "gap_from_last_day_usd", "growth_needed_last_day_pct",
                                                     "days_daily_at_or_above", "days_14d_at_or_above"], ms_rows)
    chart_rows = [[r["day"], plain(S[i] / B, 4), plain(A[14][i] / B, 4) if A[14][i] is not None else ""] for i, r in enumerate(rows)]
    write_csv(os.path.join(OUT, "chart_data.csv"), ["day", "usde_supply_billion", "avg_14d_billion"], chart_rows)

    res = {
        "read_block": int(rb[0]["block"]), "read_block_time_utc": iso(rb[0]["block_time_unix"]), "supply_read_block": plain(now, 6),
        "last_day": days[li], "supply_last_day": plain(S[li], 6), "avg14_last_day": plain(a14, 6),
        "gap14_to_first": plain(RUNGS[0][0] - a14, 6), "growth14_needed_pct": pct(RUNGS[0][0] / a14 - 1, 4),
        "gap_day_to_first": plain(RUNGS[0][0] - S[li], 6), "growth_day_needed_pct": pct(RUNGS[0][0] / S[li] - 1, 4),
        "first_cross_daily": cross, "first_cross_14d": days[a14_cross], "active14_first": runs[0][0], "active14_last": runs[0][1],
        "active14_days": len(active14_all), "days_daily_at_or_above": days_at, "days14_at_or_above": days14_at,
        "top_day": days[top_i], "top_supply": plain(S[top_i], 6),
        "rise_2025_from_day": days[start_i], "rise_2025_from_supply": plain(S[start_i], 6), "rise_2025_days": ci - start_i,
        "rise14_2025_from_day": days[a14_start], "rise14_2025_days": a14_cross - a14_start,
        "best_30d": [best[30][0], best[30][1], pct(best[30][2], 4), plain(best[30][3], 6)],
        "best_90d": [best[90][0], best[90][1], pct(best[90][2], 4), plain(best[90][3], 6)],
        "vote_day_supply": plain(sv, 6), "since_vote_pct": pct(since_vote, 4),
        "blockworks_407_vs_aug26_pct": pct(F(407, 100) * B / S[idx[vote_day] - 1] - 1, 4), "blockworks_407_vs_aug27_pct": pct(F(407, 100) * B / sv - 1, 4),
        "low_day": days[low_i], "low_supply": plain(S[low_i], 6), "fall_to_low_pct": pct(1 - S[low_i] / S[top_i], 4),
        "rise_since_low_pct": pct(S[li] / S[low_i] - 1, 4), "recent60_top_day": days[recent_i], "recent60_top_supply": plain(S[recent_i], 6),
        "days_below_since": len(below_since), "below_since_first": below_since[0],
        "avg14_10b_days": len(ten), "avg14_10b_first": ten[0], "avg14_10b_last": ten[-1],
        "last14_first_day": days[li - 13], "last14_sum": plain(sum(last14, F(0)), 6),
        "peak14_short_of_15b": plain(RUNGS[2][0] - m[14]["peak"], 6),
        "measures": {str(x["n"]): {"first": x["first"], "last": x["last"], "days_to_first": x["days_to_first"], "active": x["active"],
                                   "changes": x["changes"], "peak": plain(x["peak"], 6), "peak_day": x["peak_day"]} for x in measures},
        "days": len(days), "checks": len(CHECKS),
    }
    PENDING.append((os.path.join(OUT, "results.json"), json.dumps(res, indent=1, sort_keys=True) + "\n"))
    log("\nall %d checks passed" % len(CHECKS))
    PENDING.append((os.path.join(OUT, "run_log.txt"), "\n".join(LOG) + "\n"))
    write_pending()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # any other failure leaves out/ as it was and says why
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, "run_log_failed.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(LOG) + "\nerror: %r\n" % (e,))
        raise
