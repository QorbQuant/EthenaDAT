#!/usr/bin/env python3
"""
USDe's redemptions after the rsETH exploit of April 18, 2026, read onchain, with October 2025 for comparison.

Reads inputs/chain/day_reads.csv, USDe's total supply on Ethereum at the last block of every UTC day from
January 1, 2024 to October 12, 2026, carried from the USDe supply read of October 13, 2026, and the read of the two
windows around USDe's largest falls, inputs/chain/day_state.csv and day_flows.csv. Checks the reads against each
other and writes the tables the article uses. Every figure is exact: supplies and flows are integers of USDe's
smallest unit, 10^-18 USDe, and shares are fractions. Python 3.8 or later, standard library only, no network.

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
UNIT = 10 ** 18
M = 10 ** 6

# SHA-256 of the browser scripts, checked in the browser against these files before they ran.
SCRIPTS = {
    "browser/redemption_waves_read.js": "7d76ffdf76187ff970a845aa131b8734859821598e4bf0294cf712024fab800b",
    "browser/bundle_files.js": "257fef945e5bf502ed6d7f89c44af0c612df094c8a9b13cfcf330f70875ec00b",
}
# day_reads.csv as the browser wrote it in the USDe supply read of October 13, 2026 (its browser_digests.json).
DAY_READS_SHA = "00b21339a0f7f216583538655df2b4ea9df32f91b2dc20b6aad428b8b01c18a4"
# The two windows. State is read on every day of each, mints and burns on the days of each flow window.
STATE_WINDOWS = [("2025-09-30", "2025-11-30"), ("2026-01-31", "2026-05-31")]
FLOW_WINDOWS = [("2025-10-01", "2025-11-15"), ("2026-04-01", "2026-05-15")]
# The exploit, from the incident report on Aave's governance forum (sources file, A1).
EXPLOIT_BLOCK, EXPLOIT_UTC = 24908285, "2026-04-18 17:35"
# The two waves compared, nine UTC days each. Each is measured from the end of the day before its first day.
WAVES = [("april_2026", "2026-04-19", "2026-04-27"), ("october_2025", "2025-10-10", "2025-10-18")]
FIVE_DAYS = ("2026-04-19", "2026-04-23")
# The attestation window of Ethena's update, April 16 to April 30, 2026, measured on the days after April 16.
ATTEST_WINDOW = ("2026-04-17", "2026-04-30")
# Ethena's weekly attestations of USDe supply in March and April 2026, in billions (sources file, U3).
ATTESTED = [("2026-02-27", "6.07"), ("2026-03-06", "5.97"), ("2026-03-13", "5.92"), ("2026-03-20", "5.92"), ("2026-03-27", "5.92"),
            ("2026-04-02", "5.89"), ("2026-04-09", "5.84"), ("2026-04-16", "5.83"), ("2026-04-19", "5.64"), ("2026-04-23", "3.96"),
            ("2026-04-30", "3.90")]
# The update's sUSDe figures (sources file, U4): sUSDe supply of $1.71B at the end of April, a staking ratio of about
# 44.0%, down from 57.96% at the end of February.
T791_SUSDE_APRIL, T791_RATIO_APRIL, T791_RATIO_FEB = F(171, 100), F(440, 1000), F(5796, 10000)
# The 99th percentile benchmarks of net redemptions over one, three and seven days, as shares of supply, and the
# Tier 1 daily redemption capacity at the cooldown's activation (sources file, U7, U8 and D3).
BENCH = {1: F(41, 1000), 3: F(92, 1000), 7: F(120, 1000)}
TIER1_CAPACITY = 1880 * M * UNIT
COOLDOWN_CHANGE_DAY = "2026-03-16"
SEVEN_DAYS, ONE_DAY = 7 * 86400, 86400

LOG, CHECKS = [], []
PENDING = []


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
    """A fraction rounded half up, away from zero, to the given places, as text."""
    q = F(10) ** places
    n = abs(F(x)) * q
    r = (n.numerator * 2 + n.denominator) // (2 * n.denominator)
    s = str(r).rjust(places + 1, "0")
    out = s[:-places] + "." + s[-places:] if places else s
    return ("-" if x < 0 and r != 0 else "") + out


def fmt(x, places=2):
    s = plain(x, places)
    neg = s.startswith("-")
    s = s.lstrip("-")
    whole, _, frac = s.partition(".")
    return ("-" if neg else "") + "{:,}".format(int(whole)) + ("." + frac if frac else "")


def usde(raw, places=2):
    return fmt(F(raw, UNIT), places)


def usde6(raw):
    return plain(F(raw, UNIT), 6)


def pct(x, places=2):
    return plain(F(x) * 100, places)


def day_of(s):
    return date.fromisoformat(s)


def days_between(a, b):
    d, out = day_of(a), []
    while d <= day_of(b):
        out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def prev_day(s):
    return (day_of(s) - timedelta(days=1)).isoformat()


def utc(unix):
    return datetime.fromtimestamp(int(unix), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    os.makedirs(OUT, exist_ok=True)
    failed_log = os.path.join(OUT, "run_log_failed.txt")
    if os.path.exists(failed_log):
        os.remove(failed_log)
    log("USDe's redemptions after the rsETH exploit, run at " + datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    R = {}

    # ---- inputs -----------------------------------------------------------------------------------------
    man = read_csv(os.path.join(INP, "manifest.csv"))
    bad = [m["path"] for m in man if not os.path.exists(os.path.join(HERE, m["path"]))
           or os.path.getsize(os.path.join(HERE, m["path"])) != int(m["bytes"]) or sha256_file(os.path.join(HERE, m["path"])) != m["sha256"]]
    check("every input matches its size and SHA-256 in inputs/manifest.csv", not bad, "%d files%s" % (len(man), ", failed " + ", ".join(bad) if bad else ""))
    with open(os.path.join(CH, "browser_digests.json"), encoding="utf-8") as f:
        digests = json.load(f)
    bad = [k for k, v in digests.items() if sha256_file(os.path.join(CH, k)) != v]
    check("the browser's files match the SHA-256 digests the browser computed", not bad and len(digests) == 5, "%d files" % len(digests))
    bad = [k for k, v in SCRIPTS.items() if sha256_file(os.path.join(HERE, k)) != v]
    check("the scripts in browser/ match the SHA-256 digests recorded when the browser ran them", not bad, ", ".join(bad))
    check("day_reads.csv is the file the USDe supply read of October 13, 2026 wrote", sha256_file(os.path.join(CH, "day_reads.csv")) == DAY_READS_SHA)

    supply_rows = read_csv(os.path.join(CH, "day_reads.csv"))
    SUP = {r["day"]: int(r["usde_total_supply_raw"]) for r in supply_rows}
    BLK = {r["day"]: int(r["block"]) for r in supply_rows}
    BTIME = {r["day"]: int(r["block_time_unix"]) for r in supply_rows}
    ALL = [r["day"] for r in supply_rows]
    check("the supply read runs without a gap from January 1, 2024, each day at its last block, the same on two archive RPCs",
          ALL == days_between("2024-01-01", ALL[-1]) and all(int(r["block_time_unix"]) <= int(r["day_end_unix"]) < int(r["next_block_time_unix"])
                                                             and r["same_supply_second_rpc"] == "1" and r["same_hash_second_rpc"] == "1" for r in supply_rows),
          "%d days, %s to %s" % (len(ALL), ALL[0], ALL[-1]))
    with open(os.path.join(CH, "run.json"), encoding="utf-8") as f:
        run = json.load(f)
    st = read_csv(os.path.join(CH, "day_state.csv"))
    fl = read_csv(os.path.join(CH, "day_flows.csv"))

    # ---- the read of the windows, checked against the supply read -----------------------------------------
    want = [d for a, b in STATE_WINDOWS for d in days_between(a, b)]
    check("the state was read on every day of both windows, at the same day-end blocks as the supply read",
          [r["day"] for r in st] == want and all(int(r["block"]) == BLK[r["day"]] for r in st), "%d days" % len(st))
    check("USDe's total supply in the state read equals the supply read on every one of those days",
          all(int(r["usde_total_supply_raw"]) == SUP[r["day"]] for r in st))
    check("the second archive RPC gave the same six values on every day", all(r["same_on_second_source"] == "1" for r in st), "%d of %d days" % (
        sum(1 for r in st if r["same_on_second_source"] == "1"), len(st)))
    wantf = [d for a, b in FLOW_WINDOWS for d in days_between(a, b)]
    check("mints and burns were read for every day of both flow windows, from the block after the previous day end to the day end",
          [r["day"] for r in fl] == wantf and all(int(r["from_block"]) == BLK[prev_day(r["day"])] + 1 and int(r["to_block"]) == BLK[r["day"]] for r in fl),
          "%d days" % len(fl))
    recon = [r["day"] for r in fl if int(r["minted_raw"]) - int(r["burned_raw"]) != SUP[r["day"]] - SUP[prev_day(r["day"])]]
    check("on every day, USDe minted less USDe burned equals the change in total supply between the day ends, to the smallest unit",
          not recon, ", ".join(recon) or "%d days" % len(fl))
    check("the counts in run.json agree with the files",
          run["events"] == sum(int(r["mints"]) + int(r["burns"]) for r in fl) and run["log_days"] == len(fl) == run["days_flows_read"]
          and run["days"] == len(st) == run["days_state_same"], "%d events" % run["events"])
    check("sUSDe held at least as much USDe as its assets on every day, the difference being rewards not yet vested",
          all(int(r["usde_held_by_susde_raw"]) >= int(r["susde_total_assets_raw"]) for r in st))
    check("the cooldown silo was the same on both RPCs", run["cooldown_silo"] == run["silo_on_second_source"] != "error", run["cooldown_silo"])
    check("the USDe outside sUSDe and its silo was positive on every day",
          all(int(r["usde_total_supply_raw"]) - int(r["usde_held_by_susde_raw"]) - int(r["usde_in_cooldown_silo_raw"]) > 0 for r in st))
    check("on every day read for flows, the largest single burn was no larger than the day's burns, and a day with no burns burned nothing",
          all(0 <= int(r["largest_burn_raw"]) <= int(r["burned_raw"]) and (int(r["burns"]) > 0 or int(r["burned_raw"]) == 0) for r in fl))

    S = {r["day"]: r for r in st}
    FL = {r["day"]: r for r in fl}
    held = {d: int(S[d]["usde_held_by_susde_raw"]) for d in S}
    silo = {d: int(S[d]["usde_in_cooldown_silo_raw"]) for d in S}
    assets = {d: int(S[d]["susde_total_assets_raw"]) for d in S}
    shares = {d: int(S[d]["susde_total_supply_raw"]) for d in S}
    outside = {d: SUP[d] - held[d] - silo[d] for d in S}
    cool = {d: int(S[d]["cooldown_seconds"]) for d in S}

    # ---- the exploit and the cooldown ----------------------------------------------------------------------
    check("the exploit's block falls on April 18, 2026 UTC, after the end of April 17 and at or before the end of April 18",
          BLK["2026-04-17"] < EXPLOIT_BLOCK <= BLK["2026-04-18"], "day-end blocks %d and %d" % (BLK["2026-04-17"], BLK["2026-04-18"]))
    R["exploit"] = {"block": EXPLOIT_BLOCK, "utc": EXPLOIT_UTC, "day_end_block_april_18": BLK["2026-04-18"],
                    "day_end_time_april_18": utc(BTIME["2026-04-18"]), "blocks_after_exploit": BLK["2026-04-18"] - EXPLOIT_BLOCK}
    log("the last block of April 18, %d at %s, came %d blocks after the exploit's block" % (BLK["2026-04-18"], utc(BTIME["2026-04-18"]), BLK["2026-04-18"] - EXPLOIT_BLOCK))
    before = [d for d in S if d < COOLDOWN_CHANGE_DAY]
    after = [d for d in S if d >= COOLDOWN_CHANGE_DAY]
    check("sUSDe's cooldown was 7 days at every day end read before March 16, 2026 and 1 day at every day end read from March 16 to May 31, 2026",
          all(cool[d] == SEVEN_DAYS for d in before) and all(cool[d] == ONE_DAY for d in after),
          "%d and %d days, last 7 day reading %s" % (len(before), len(after), max(before)))
    R["cooldown"] = {"last_7_day": max(before), "first_1_day": min(after), "days_7": len(before), "days_1": len(after)}

    # ---- the waves -----------------------------------------------------------------------------------------
    R["waves"] = {}
    wave_rows = []
    for key, a, b in WAVES:
        d0, days = prev_day(a), days_between(a, b)
        w = {"first_day": a, "last_day": b, "start_day_end": d0, "days": len(days),
             "supply_start": SUP[d0], "supply_end": SUP[b], "change": SUP[b] - SUP[d0],
             "burned": sum(int(FL[d]["burned_raw"]) for d in days), "minted": sum(int(FL[d]["minted_raw"]) for d in days),
             "burns": sum(int(FL[d]["burns"]) for d in days), "mints": sum(int(FL[d]["mints"]) for d in days),
             "held_start": held[d0], "held_end": held[b], "silo_start": silo[d0], "silo_end": silo[b],
             "outside_start": outside[d0], "outside_end": outside[b], "cooldown_days": cool[b] // 86400}
        assert w["minted"] - w["burned"] == w["change"]
        w["change_pct"] = F(w["change"], w["supply_start"])
        w["held_change"] = w["held_end"] - w["held_start"]
        w["silo_change"] = w["silo_end"] - w["silo_start"]
        w["outside_change"] = w["outside_end"] - w["outside_start"]
        w["staked_change"] = w["held_change"] + w["silo_change"]
        assert w["staked_change"] + w["outside_change"] == w["change"]
        w["staked_share_of_fall"] = F(w["staked_change"], w["change"])
        w["outside_share_of_fall"] = F(w["outside_change"], w["change"])
        w["staked_change_pct"] = F(w["staked_change"], w["held_start"] + w["silo_start"])
        w["outside_change_pct"] = F(w["outside_change"], w["outside_start"])
        w["held_change_pct"] = F(w["held_change"], w["held_start"])
        w["staked_start_share"] = F(w["held_start"] + w["silo_start"], w["supply_start"])
        top = max(days, key=lambda d: int(FL[d]["burned_raw"]))
        w["top_burn_day"], w["top_burn_day_amount"] = top, int(FL[top]["burned_raw"])
        w["largest_single_burn"] = max(int(FL[d]["largest_burn_raw"]) for d in days)
        R["waves"][key] = w
        log("%s: %s to %s, supply %s to %s (%s, %s%%), burned %s in %d burns, minted %s in %d mints; held by sUSDe %s (%s%%), silo %s, "
            "outside %s (%s%%); sUSDe and silo %s%% of the fall, outside %s%%, against %s%% of supply at the start; cooldown %d days" % (
                key, a, b, usde(w["supply_start"]), usde(w["supply_end"]), usde(w["change"]), pct(w["change_pct"]), usde(w["burned"]), w["burns"],
                usde(w["minted"]), w["mints"], usde(w["held_change"]), pct(w["held_change_pct"]), usde(w["silo_change"]), usde(w["outside_change"]),
                pct(w["outside_change_pct"]), pct(w["staked_share_of_fall"]), pct(w["outside_share_of_fall"]), pct(w["staked_start_share"]), w["cooldown_days"]))
        wave_rows.append([key, a, b, d0, len(days), usde6(w["supply_start"]), usde6(w["supply_end"]), usde6(w["change"]), pct(w["change_pct"], 4),
                          usde6(w["burned"]), w["burns"], usde6(w["minted"]), w["mints"], usde6(w["held_start"]), usde6(w["held_end"]), usde6(w["held_change"]),
                          usde6(w["silo_start"]), usde6(w["silo_end"]), usde6(w["silo_change"]), usde6(w["outside_start"]), usde6(w["outside_end"]),
                          usde6(w["outside_change"]), pct(w["staked_share_of_fall"], 4), pct(w["outside_share_of_fall"], 4), pct(w["staked_start_share"], 4),
                          w["cooldown_days"]])
    A, O = R["waves"]["april_2026"], R["waves"]["october_2025"]
    check("the April 2026 wave ends at the lowest day-end supply from the 2025 peak to the last day read",
          min((d for d in ALL if d >= max(ALL, key=lambda x: SUP[x])), key=lambda x: SUP[x]) == A["last_day"], A["last_day"])
    check("the day of the exploit, April 18, 2026, burned no more than the largest day of the two weeks before it",
          int(FL["2026-04-18"]["burned_raw"]) <= max(int(FL[d]["burned_raw"]) for d in days_between("2026-04-04", "2026-04-17")),
          "%s burned on April 18" % usde(int(FL["2026-04-18"]["burned_raw"])))
    five = days_between(*FIVE_DAYS)
    R["five_days"] = {"burned": sum(int(FL[d]["burned_raw"]) for d in five), "minted": sum(int(FL[d]["minted_raw"]) for d in five),
                      "burns": sum(int(FL[d]["burns"]) for d in five), "change": SUP[FIVE_DAYS[1]] - SUP[prev_day(FIVE_DAYS[0])]}
    R["five_days"]["change_pct"] = F(R["five_days"]["change"], SUP[prev_day(FIVE_DAYS[0])])
    R["five_days"]["share_of_wave_burns"] = F(R["five_days"]["burned"], A["burned"])
    log("April 19 to 23: burned %s, minted %s, supply %s (%s%%), %s%% of the wave's burns" % (
        usde(R["five_days"]["burned"]), usde(R["five_days"]["minted"]), usde(R["five_days"]["change"]), pct(R["five_days"]["change_pct"]),
        pct(R["five_days"]["share_of_wave_burns"])))
    half = next(d for d in days_between(A["first_day"], A["last_day"]) if A["supply_start"] - SUP[d] >= -A["change"] / 2)
    R["half_by"] = half
    log("half of the wave's fall had come by the end of %s" % half)

    # ---- the days around the exploit, for the article's table ---------------------------------------------
    table = []
    for d in days_between("2026-04-17", "2026-04-30"):
        table.append([d, usde6(SUP[d]), usde6(SUP[d] - SUP[prev_day(d)]), pct(F(SUP[d] - SUP[prev_day(d)], SUP[prev_day(d)]), 4),
                      usde6(int(FL[d]["burned_raw"])), FL[d]["burns"], usde6(int(FL[d]["minted_raw"])), FL[d]["mints"],
                      usde6(held[d]), usde6(silo[d]), usde6(outside[d])])
    R["silo_peak_april"] = max(days_between("2026-04-01", "2026-05-31"), key=lambda d: silo[d])
    R["silo_peak_october"] = max(days_between("2025-10-01", "2025-11-30"), key=lambda d: silo[d])
    log("silo peaks: %s %s, %s %s" % (R["silo_peak_april"], usde(silo[R["silo_peak_april"]]), R["silo_peak_october"], usde(silo[R["silo_peak_october"]])))

    # ---- the largest falls since January 2024 -----------------------------------------------------------------
    falls = []
    for n in (1, 3, 7, 9, 30):
        ranked = sorted(((F(SUP[ALL[i]] - SUP[ALL[i - n]], SUP[ALL[i - n]]), ALL[i - n], ALL[i]) for i in range(n, len(ALL))))
        for k, (x, a, b) in enumerate(ranked[:8]):
            falls.append([n, k + 1, a, b, usde6(SUP[a]), usde6(SUP[b]), usde6(SUP[b] - SUP[a]), pct(x, 4)])
        R.setdefault("largest", {})[n] = [(a, b, x) for x, a, b in ranked[:8]]
        log("largest %d day falls: %s" % (n, ", ".join("%s to %s %s%%" % (a, b, pct(x)) for x, a, b in ranked[:5])))
    one = R["largest"][1]
    top5_april = [b for a, b, x in one[:5] if b.startswith("2026-04")]
    top7_april = [b for a, b, x in one[:7] if b.startswith("2026-04")]
    check("four of the five largest one-day falls since January 2, 2024 came on April 20 to 23, 2026, and five of the seven on April 19 to 23",
          sorted(top5_april) == days_between("2026-04-20", "2026-04-23") and sorted(top7_april) == days_between("2026-04-19", "2026-04-23")
          and one[0][1] == "2025-10-11", "largest %s on %s" % (pct(one[0][2]), one[0][1]))
    check("over three, seven and nine days the April 2026 falls were the largest since January 2024, and over 30 days October and November 2025",
          all(R["largest"][n][0][1].startswith("2026-04") for n in (3, 7, 9)) and R["largest"][30][0][0].startswith("2025-10"),
          "; ".join("%d days %s%% to %s" % (n, pct(R["largest"][n][0][2]), R["largest"][n][0][1]) for n in (3, 7, 9, 30)))
    check("the nine-day fall to April 27, 2026 is the April wave", (R["largest"][9][0][0], R["largest"][9][0][1]) == (A["start_day_end"], A["last_day"]))
    # sUSDe and its silo over the largest 30-day fall, which began with the October wave
    a30, b30 = R["largest"][30][0][0], R["largest"][30][0][1]
    s30 = (held[b30] + silo[b30]) - (held[a30] + silo[a30])
    R["october_30"] = {"from": a30, "to": b30, "change": SUP[b30] - SUP[a30], "staked_change": s30, "staked_share_of_fall": F(s30, SUP[b30] - SUP[a30])}
    check("the largest 30-day fall began at the start of the October wave, and sUSDe and its silo made up less than 15% of it",
          a30 == O["start_day_end"] and R["october_30"]["staked_share_of_fall"] < F(15, 100),
          "%s to %s, %s%%" % (a30, b30, pct(R["october_30"]["staked_share_of_fall"])))
    R["benchmarks"] = {}
    for n, bench in BENCH.items():
        # the largest fall over n days ending in the April wave
        cands = [(F(SUP[b] - SUP[ALL[ALL.index(b) - n]], SUP[ALL[ALL.index(b) - n]]), ALL[ALL.index(b) - n], b) for b in days_between(A["first_day"], A["last_day"])]
        x, a, b = min(cands)
        R["benchmarks"][n] = {"from": a, "to": b, "fall": -x, "bench": bench, "times": -x / bench}
        log("largest %d day fall in the April wave %s to %s, %s%%, %s times the benchmark of %s%%" % (n, a, b, pct(-x), plain(-x / bench, 2), pct(bench, 1)))
    check("in the April wave the falls over one, three and seven days were above the 99th percentile benchmarks the cooldown was set against",
          all(v["fall"] > v["bench"] for v in R["benchmarks"].values()))
    over = [d for d in days_between(A["first_day"], A["last_day"]) if F(SUP[prev_day(d)] - SUP[d], SUP[prev_day(d)]) > BENCH[1]]
    R["days_over_1d_bench"] = over
    log("days in the April wave whose fall was above 4.1%% of the previous day-end supply: %s" % ", ".join(over))
    three = R["benchmarks"][3]
    three_net = SUP[three["from"]] - SUP[three["to"]]
    R["tier1"] = {"capacity": TIER1_CAPACITY, "top_day_share": F(A["top_burn_day_amount"], TIER1_CAPACITY),
                  "three_day_net": three_net, "three_day_share": F(three_net, TIER1_CAPACITY)}
    log("Tier 1 capacity of $1.88 billion: the largest day's burns %s%%, the largest three-day net fall %s, %s%%" % (
        pct(R["tier1"]["top_day_share"]), usde(three_net), pct(R["tier1"]["three_day_share"])))

    # ---- Ethena's attestations against the chain ----------------------------------------------------------------
    with open(os.path.join(WEB, "redemption_sources_2026-10-13.txt"), encoding="utf-8") as f:
        web = f.read()
    MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    table_rows = [l for l in web.split("\n") if l.count("|") == 4 and l.split("|")[0].strip()[:1].isdigit()]
    got = [(datetime.strptime(" ".join(l.split("|")[0].split()[:3]), "%d %b %Y").date().isoformat(), l.split("|")[1].strip()) for l in table_rows]
    check("the attestation dates and supplies used here are those in the update's table, as the sources file copies it",
          got == [(d, "$%sB" % v) for d, v in ATTESTED], "%d rows" % len(got))
    assert MON  # the month names the table uses are those of strptime's %b
    att_rows, R["attest"] = [], []
    for d, v in ATTESTED:
        same = plain(F(SUP[d], UNIT * 10 ** 9), 2)
        prev = plain(F(SUP[prev_day(d)], UNIT * 10 ** 9), 2)
        att_rows.append([d, v, usde6(SUP[d]), same, usde6(SUP[prev_day(d)]), prev, "yes" if v in (same, prev) else "no"])
        R["attest"].append((d, v, same, prev))
    matched = sum(1 for d, v, s, p in R["attest"] if v in (s, p))
    check("every attestation but April 19 equals the day-end supply of its day or the day before, to the update's two decimals in billions",
          [d for d, v, s, p in R["attest"] if v not in (s, p)] == ["2026-04-19"], "%d of %d" % (matched, len(ATTESTED)))
    a19 = F(int(ATTESTED[8][1].replace(".", "")), 100) * 10 ** 9 * UNIT
    check("the April 19 attestation lies between the day-end supplies of April 18 and April 19", SUP["2026-04-19"] < a19 < SUP["2026-04-18"])
    aw = days_between(*ATTEST_WINDOW)
    R["attest_window"] = {"burned": sum(int(FL[d]["burned_raw"]) for d in aw), "minted": sum(int(FL[d]["minted_raw"]) for d in aw),
                          "change": SUP[ATTEST_WINDOW[1]] - SUP[prev_day(ATTEST_WINDOW[0])]}
    assert R["attest_window"]["minted"] - R["attest_window"]["burned"] == R["attest_window"]["change"]
    R["trough"] = {"fall_23_27": SUP["2026-04-27"] - SUP["2026-04-23"], "rise_27_30": SUP["2026-04-30"] - SUP["2026-04-27"],
                   "change_23_30": SUP["2026-04-30"] - SUP["2026-04-23"]}
    log("April 16 to 30 day ends: burned %s, minted %s, change %s. April 23 to 27 %s, April 27 to 30 %s, April 23 to 30 %s" % (
        usde(R["attest_window"]["burned"]), usde(R["attest_window"]["minted"]), usde(R["attest_window"]["change"]), usde(R["trough"]["fall_23_27"]),
        usde(R["trough"]["rise_27_30"]), usde(R["trough"]["change_23_30"])))

    # ---- sUSDe's staking ratio --------------------------------------------------------------------------------
    ratio_rows, R["ratio"] = [], {}
    for d in ("2026-02-26", "2026-02-27", "2026-02-28", "2026-04-18", "2026-04-27", "2026-04-30"):
        r = {"supply": SUP[d], "assets": assets[d], "shares": shares[d], "assets_ratio": F(assets[d], SUP[d]), "shares_ratio": F(shares[d], SUP[d]),
             "price": F(assets[d], shares[d])}
        R["ratio"][d] = r
        ratio_rows.append([d, usde6(SUP[d]), usde6(assets[d]), usde6(shares[d]), plain(r["price"], 6), pct(r["assets_ratio"], 4), pct(r["shares_ratio"], 4)])
        log("%s: sUSDe assets %s, shares %s, %s USDe a share, assets %s%% of supply, shares %s%%" % (
            d, usde(assets[d]), usde(shares[d]), plain(r["price"], 4), pct(r["assets_ratio"]), pct(r["shares_ratio"])))
    e30 = R["ratio"]["2026-04-30"]
    check("the update's $1.71 billion of sUSDe at the end of April matches sUSDe's token count, not its assets, at the end of April 30",
          plain(F(e30["shares"], UNIT * 10 ** 9), 2) == "1.71" and plain(F(e30["assets"], UNIT * 10 ** 9), 2) != "1.71",
          "%s tokens, %s USDe of assets" % (usde(e30["shares"]), usde(e30["assets"])))
    feb = [R["ratio"][d] for d in ("2026-02-26", "2026-02-27", "2026-02-28")]
    check("the update's 44.0% matches the token count over supply at the end of April 30 to one decimal, and its 57.96% for February the assets over "
          "supply at the end of February 26 to two decimals, the assets ratio staying between 57.96% and 58.07% to February 28 while the token count "
          "was below 48% of supply",
          plain(e30["shares_ratio"] * 100, 1) == "44.0" and plain(e30["assets_ratio"] * 100, 1) != "44.0"
          and pct(feb[0]["assets_ratio"]) == plain(T791_RATIO_FEB * 100, 2) and all(F(5796, 10000) <= r["assets_ratio"] <= F(5807, 10000) for r in feb)
          and all(r["shares_ratio"] < F(48, 100) for r in feb),
          "%s%%, %s%%, %s%% and %s%%" % (pct(e30["shares_ratio"]), pct(feb[0]["assets_ratio"]), pct(feb[1]["assets_ratio"]), pct(feb[2]["assets_ratio"])))

    # ---- after the wave --------------------------------------------------------------------------------------
    R["after"] = {"may_31": SUP["2026-05-31"], "last_day": ALL[-1], "last": SUP[ALL[-1]],
                  "rise_to_last": F(SUP[ALL[-1]] - SUP[A["last_day"]], SUP[A["last_day"]]),
                  "held_may_31": held["2026-05-31"], "outside_may_31": outside["2026-05-31"]}
    log("after the low: %s on May 31, %s on %s, %s%% above the low" % (usde(SUP["2026-05-31"]), usde(SUP[ALL[-1]]), ALL[-1], pct(R["after"]["rise_to_last"])))
    big = max(int(r["largest_burn_raw"]) for r in fl)
    at_big = [r["day"] for r in fl if int(r["largest_burn_raw"]) == big]
    R["largest_single_burn"] = {"amount": big, "days": len(at_big), "first": at_big[0], "last": at_big[-1]}
    log("largest single burn in either flow window %s USDe, on %d days" % (usde(big), len(at_big)))

    # ---- tables ----------------------------------------------------------------------------------------------
    daily = []
    for d in want:
        f_ = FL.get(d)
        daily.append([d, BLK[d], utc(BTIME[d]), usde6(SUP[d]), usde6(held[d]), usde6(silo[d]), usde6(outside[d]), usde6(assets[d]), usde6(shares[d]),
                      cool[d], usde6(int(f_["minted_raw"])) if f_ else "", f_["mints"] if f_ else "", usde6(int(f_["burned_raw"])) if f_ else "",
                      f_["burns"] if f_ else "", usde6(int(f_["largest_burn_raw"])) if f_ else ""])
    write_csv(os.path.join(OUT, "daily_state.csv"),
              ["day", "block", "block_time_utc", "usde_supply", "usde_held_by_susde", "usde_in_cooldown_silo", "usde_outside_susde", "susde_total_assets",
               "susde_shares", "cooldown_seconds", "usde_minted", "mints", "usde_burned", "burns", "largest_burn"], daily)
    write_csv(os.path.join(OUT, "april_days.csv"),
              ["day", "usde_supply", "supply_change", "supply_change_pct", "usde_burned", "burns", "usde_minted", "mints", "usde_held_by_susde",
               "usde_in_cooldown_silo", "usde_outside_susde"], table)
    write_csv(os.path.join(OUT, "waves.csv"),
              ["wave", "first_day", "last_day", "measured_from_day_end", "days", "supply_start", "supply_end", "supply_change", "supply_change_pct",
               "usde_burned", "burns", "usde_minted", "mints", "held_by_susde_start", "held_by_susde_end", "held_by_susde_change", "silo_start", "silo_end",
               "silo_change", "outside_start", "outside_end", "outside_change", "susde_and_silo_share_of_fall_pct", "outside_share_of_fall_pct",
               "susde_and_silo_share_of_supply_at_start_pct", "cooldown_days"], wave_rows)
    write_csv(os.path.join(OUT, "largest_falls.csv"),
              ["days", "rank", "from_day_end", "to_day_end", "supply_from", "supply_to", "change", "change_pct"], falls)
    write_csv(os.path.join(OUT, "attestations.csv"),
              ["attestation_date", "attested_billion", "day_end_supply", "day_end_billion", "previous_day_end_supply", "previous_day_end_billion",
               "matches_one_of_them"], att_rows)
    write_csv(os.path.join(OUT, "staking_ratio.csv"),
              ["day", "usde_supply", "susde_total_assets", "susde_shares", "usde_per_susde", "assets_over_supply_pct", "shares_over_supply_pct"], ratio_rows)
    chart = [[d, plain(F(held[d], UNIT * 10 ** 9), 4), plain(F(silo[d], UNIT * 10 ** 9), 4), plain(F(outside[d], UNIT * 10 ** 9), 4),
              plain(F(SUP[d], UNIT * 10 ** 9), 4)] for d in days_between("2026-01-31", "2026-05-31")]
    write_csv(os.path.join(OUT, "chart_data.csv"), ["day", "held_by_susde_billion", "cooldown_silo_billion", "outside_susde_billion", "usde_supply_billion"], chart)

    if not all(ok for _, ok, _ in CHECKS):
        with open(failed_log, "w", encoding="utf-8") as f:
            f.write("\n".join(LOG) + "\n")
        print("\n%d of %d checks failed; out/ not updated" % (sum(1 for c in CHECKS if not c[1]), len(CHECKS)))
        sys.exit(1)

    def js(x):
        if isinstance(x, F):
            return plain(x, 6)
        if isinstance(x, dict):
            return {str(k): js(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [js(v) for v in x]
        if isinstance(x, int) and not isinstance(x, bool) and abs(x) >= 10 ** 15:
            return usde6(x)
        return x
    R["checks"] = len(CHECKS)
    PENDING.append((os.path.join(OUT, "results.json"), json.dumps(js(R), indent=1, sort_keys=True) + "\n"))
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
