#!/usr/bin/env python3
"""EthenaPay Daily Boost review: what the two reward accounts paid EthenaPay wallets, September 1 to October 8, 2026.

Reads the files boost_recount.cjs wrote in inputs/chain/, checks them against the chain recount this site published
with its EthenaPay adoption review, and works out the rates the two reward accounts paid, which balances they paid on,
and whether wallets without a card spend in the calendar month were paid. If any check fails the script stops before
writing anything, so out/ keeps the tables of the last clean run. Python 3 standard library only. No network.
"""
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 60
HERE = Path(__file__).parent
INP = HERE / "inputs"
CH = INP / "chain"
OUT = HERE / "out"
E18 = 10 ** 18
E12 = 10 ** 12

log_lines = []
failures = []


def log(msg=""):
    log_lines.append(msg)
    print(msg)


def check(name, ok, detail=""):
    log(("ok    " if ok else "FAIL  ") + name + (f"  ({detail})" if detail else ""))
    if not ok:
        failures.append(name)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def daily_factor(rate):
    """Daily factor of an annual rate compounded daily, (1 + rate) ** (1/365) - 1."""
    r = Decimal(rate)
    return ((1 + r).ln() / 365).exp() - 1


def simple(factor):
    """The daily factor as a simple annual rate in percent."""
    return factor * 365 * 100


# ---------------------------------------------------------------- inputs and their fingerprints
log("EthenaPay Daily Boost review")
log("Inputs")
manifest = rows(INP / "manifest.csv")
for m in manifest:
    p = INP / m["file"]
    check(f"input {m['file']} matches its SHA-256", p.exists() and sha(p) == m["sha256"] and p.stat().st_size == int(m["bytes"]))
listed = {m["file"] for m in manifest}
on_disk = {str(p.relative_to(INP)) for p in INP.rglob("*") if p.is_file() and p.name != "manifest.csv"}
check("the manifest lists every input file", listed == on_disk, f"{len(listed)} files")

chain_manifest = rows(INP / "chain_manifest.csv")
script_sha = sha(HERE / "boost_recount.cjs")
for m in chain_manifest:
    check(f"chain file {m['file']} is the one the run wrote", sha(CH / m["file"]) == m["sha256"])
    check(f"chain file {m['file']} came from this boost_recount.cjs", m["script_sha256"] == script_sha)

meta = json.loads((CH / "meta.json").read_text())
periods = rows(CH / "periods.csv")
activity = rows(CH / "activity.csv")
batches = rows(CH / "batches.csv")
after = rows(CH / "utc_days_after_recount.csv")
day_files = {d: rows(CH / f"wallet_day_{d}.csv") for d in ("2026-10-01", "2026-10-08")}
recount_meta = json.loads((INP / "recount" / "meta.json").read_text())
recount_wallets = rows(INP / "recount" / "wallet_activity.csv")
recount_days = rows(INP / "recount" / "daily_chain_62503a1.csv")
cashflow = json.loads((INP / "cashflow_results.json").read_text())
terms = {r["id"]: r for r in rows(INP / "terms_facts.csv")}

# ---------------------------------------------------------------- the new read against the published recount
log()
log("Cross-checks with the published recount")
canon = "".join(f"{r['wallet']},{r['first_usde_in_ts']},{r['first_in_kind']},{r['balance_wei_at_last_snapshot']}\n" for r in recount_wallets)
cc = meta["cross_checks"]
check("every wallet's first USDe and its balance at block 96,815,525 match the published recount",
      hashlib.sha256(canon.encode()).hexdigest() == cc["recount_wallet_rows_sha256"] and len(recount_wallets) == cc["recount_wallet_rows"] == 1106,
      f"{len(recount_wallets)} wallets")
recount_sum = sum(int(r["balance_wei_at_last_snapshot"]) for r in recount_wallets)
check("the balances sum to the recount's balanceOf total",
      recount_sum == int(cc["recount_balance_sum_wei"]) == int(recount_meta["balance_check"]["sum_wei"]),
      f"{Decimal(recount_sum) / E18:.6f} USDe")
day_canon = "".join(",".join([r["date"], r["deposits_wei"], r["withdrawals_wei"], r["reversals_wei"], r["yield_wei"], r["other_rewards_wei"],
                              r["card_spend_wei"], r["internal_wei"], r["held_wei"]]) + "\n" for r in recount_days)
check("daily flows and USDe held on all 144 days to October 5 match the published recount to the wei",
      hashlib.sha256(day_canon.encode()).hexdigest() == cc["utc_days_sha256"] and len(recount_days) == cc["utc_days_compared"] == 144)
check("the wallet count to October 5 matches the recount", recount_meta["wallets"] == 14103 and meta["wallets"] >= 14103,
      f"{meta['wallets']} wallets to October 9")

log()
log("The chain read")
check("block 97,161,009 is the last block of October 9 UTC",
      meta["end_block"] == 97161009 and meta["end_block_time"] == "2026-10-09T23:59:59Z" and meta["next_block_time"] == "2026-10-10T00:00:01Z")
usde = "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34"
cards = meta["card_debit_logs_by_token"]
check("every card debit log to either settlement address is in USDe",
      set(cards["current_settlement"]) == {usde} and set(cards["retired_settlement"]) == {usde},
      f"{cards['current_settlement'][usde]} and {cards['retired_settlement'][usde]} logs")
check("no wallet sent USDe back to either reward account", meta["transfers_from_wallets_to_reward_accounts"] == 0 and meta["usde_wei_from_wallets_to_reward_accounts"] == "0")
check("the pilot's top-up account made its 150 payments before the window", meta["topup_payments_by_account"][1] == 150)

# ---------------------------------------------------------------- payment models
MODEL_RATES = {"base_4_5": "0.045", "base_4_0": "0.04", "standard_0_5": "0.005", "standard_1_0": "0.01", "six_1_5": "0.015",
               "six_2_0": "0.02", "six_1_5_cap_100k": "0.015", "six_2_0_cap_100k": "0.02"}
CAPS = {"standard_0_5": 5000, "standard_1_0": 5000, "six_1_5": 1000000, "six_2_0": 1000000, "six_1_5_cap_100k": 100000, "six_2_0_cap_100k": 100000}
FACT = {k: daily_factor(v) for k, v in MODEL_RATES.items()}
check("the script's daily factors match (1 + rate) ** (1/365) - 1 to ten significant digits",
      all(abs(Decimal(repr(meta["models_daily"][k])) / FACT[k] - 1) < Decimal("1e-10") for k in FACT))
SIMPLE = {k: simple(v) for k, v in FACT.items()}
log("  simple annual rates: " + ", ".join(f"{k} {SIMPLE[k]:.5f}%" for k in ("base_4_5", "base_4_0", "standard_0_5", "standard_1_0", "six_1_5", "six_2_0")))

# ---------------------------------------------------------------- periods, batches and days
log()
log("Payments")
bad = []
for p in periods:
    bs = [b for b in batches if b["payer"] == p["payer"] and b["first_day"] == p["first_day"] and b["last_day"] == p["last_day"]]
    ok = (sum(int(b["paid_wei"]) for b in bs) == int(p["paid_wei"]) and sum(int(b["transfers"]) for b in bs) == int(p["transfers"])
          and len(bs) == int(p["batches"]))
    if not ok:
        bad.append(f"{p['payer']} {p['first_day']}")
check("every payment period equals the sum of its batches", not bad, f"{len(periods)} periods" + (", mismatched " + "; ".join(bad) if bad else ""))
for r in after:
    day = r["date"]
    for payer, col in (("base", "base_wei"), ("topup", "topup_wei")):
        tot = sum(int(b["paid_wei"]) for b in batches if b["payer"] == payer and b["first_utc"][:10] == day)
        check(f"{payer} payments on {day} UTC equal the day's batches", tot == int(r[col]))

P = {(p["payer"], p["first_day"]): p for p in periods}
OCT = [f"2026-10-0{d}" for d in range(1, 9)]
for d in OCT:
    for payer in ("base", "topup"):
        check(f"{payer} pays October {int(d[-2:])} in a period of its own", P[(payer, d)]["last_day"] == d and P[(payer, d)]["days"] == "1")


def n(p, k):
    return int(p[k]) if p[k] != "" else 0


# ---------------------------------------------------------------- wallet-level files for October 1 and October 8
log()
log("Wallet files")


def classify(payer, paid, twa, tol=Decimal("0.01")):
    if paid == 0:
        return "unpaid"
    names = ("base_4_5", "base_4_0") if payer == "base" else ("standard_0_5", "standard_1_0", "six_1_5", "six_2_0", "six_1_5_cap_100k", "six_2_0_cap_100k")
    for name in names:
        bal = twa if payer == "base" else min(twa, Decimal(CAPS[name]))
        expect = FACT[name] * bal
        if expect > 0 and abs(paid / expect - 1) <= tol:
            return name
    return "other"


def cls_of(r):
    return "A" if int(r["card_spends_month"]) else "B" if int(r["card_spends_previous_month"]) else "C" if int(r["card_spends_earlier"]) else "D"


snap = {}
for d, wr in day_files.items():
    pb, pt = P[("base", d)], P[("topup", d)]
    check(f"{d} wallet file sums to the base payments of the day", sum(int(r["base_wei"]) for r in wr) == int(pb["paid_wei"]))
    check(f"{d} wallet file sums to the top-up payments of the day", sum(int(r["topup_wei"]) for r in wr) == int(pt["paid_wei"]))
    # every row is a wallet with a balance that day: neither account paid a wallet without one (paid_wallets_without_balance is 0)
    funded = wr
    check(f"{d} wallet file holds every funded wallet", len(wr) == int(pt["funded_wallets"]) == int(pb["funded_wallets"])
          and pt["paid_wallets_without_balance"] == pb["paid_wallets_without_balance"] == "0", f"{len(wr)} wallets")
    twa_sum = sum(int(r["twa_micro"]) for r in wr)
    check(f"{d} time-weighted balances add up to the period's total", abs(twa_sum * E12 - int(pt["twa_wei_days"])) < len(wr) * E12)
    tested = [r for r in wr if int(r["twa_micro"]) >= 100 * 10 ** 6]
    check(f"{d} tested wallets match the period", len(tested) == int(pt["tested_wallets"]) == int(pb["tested_wallets"]), f"{len(tested)} wallets")
    # model fits recomputed from the wallet file, against the script's counts
    for payer, p in (("base", pb), ("topup", pt)):
        col = "base_wei" if payer == "base" else "topup_wei"
        for shift, tcol in (("utc", "twa_micro"), ("cet", "twa_cet_micro"), ("cest", "twa_cest_micro")):
            fit = 0
            for r in tested:
                c = classify(payer, Decimal(int(r[col])) / E18, Decimal(int(r[tcol])) / 10 ** 6)
                fit += c not in ("unpaid", "other")
            check(f"{d} {payer} fits on {shift} days recomputed from the wallet file", fit == int(p["fit_" + shift]), f"{fit}")
    # activity classes recomputed
    for scope in ("all", "ge100"):
        for c in "ABCD":
            sel = [r for r in (funded if scope == "all" else tested) if cls_of(r) == c]
            a = [x for x in activity if x["first_day"] == d and x["scope"] == scope and x["class"] == c]
            want = (int(a[0]["wallets"]), int(a[0]["paid_wallets"])) if a else (0, 0)
            got = (len(sel), sum(int(r["topup_wei"]) > 0 for r in sel))
            check(f"{d} class {c} ({scope}) recomputed from the wallet file", got == want, f"{got[1]} of {got[0]} paid")
    snap[d] = wr

# ---------------------------------------------------------------- results
log()
log("Results")
R = {}
R["models_simple_pct"] = {k: f"{SIMPLE[k]:.6f}" for k in ("base_4_5", "base_4_0", "standard_0_5", "standard_1_0", "six_1_5", "six_2_0")}
R["total_simple_pct"] = {"standard": f"{SIMPLE['base_4_5'] + SIMPLE['standard_0_5']:.6f}", "six": f"{SIMPLE['base_4_5'] + SIMPLE['six_1_5']:.6f}"}


def compounded(daily):
    """A daily factor compounded over 365 days, as a percentage."""
    return (((1 + daily).ln() * 365).exp() - 1) * 100


R["total_compounded_pct"] = {"standard": f"{compounded(FACT['base_4_5'] + FACT['standard_0_5']):.4f}",
                             "six": f"{compounded(FACT['base_4_5'] + FACT['six_1_5']):.4f}"}
R["standard_cap_daily_usde"] = f"{FACT['standard_0_5'] * 5000:.9f}"
R["simple_if_not_compounded_pct"] = {"base_4_5": "4.5", "standard_0_5": "0.5"}

# October 1 to 8, both accounts
octs = {payer: [P[(payer, d)] for d in OCT] for payer in ("base", "topup")}
tot = {}
for payer in ("base", "topup"):
    t = {k: sum(n(p, k) for p in octs[payer]) for k in ("tested_wallets", "fit_utc", "fit_cet", "fit_cest", "fit_utc_within_5pct", "unpaid", "other",
                                                          "other_without_flows", "base_4_5", "base_4_0", "standard_0_5", "six_1_5", "six_1_5_cap_100k",
                                                          "standard_1_0", "six_2_0", "six_2_0_cap_100k", "funded_wallets", "paid_wallets")}
    t["paid_usde"] = str(Decimal(sum(int(p["paid_wei"]) for p in octs[payer])) / E18)
    t["twa_usde_days"] = str(Decimal(sum(int(p["twa_wei_days"]) for p in octs[payer])) / E18)
    tot[payer] = t
R["october_1_to_8"] = tot
b, t = tot["base"], tot["topup"]
check("the base account paid 4.5% on every tested wallet-day it fitted in October", b["base_4_5"] == b["fit_utc"] and b["base_4_0"] == 0)
t_new = t["standard_0_5"] + t["six_1_5"] + t["six_1_5_cap_100k"]
t_old = t["standard_1_0"] + t["six_2_0"] + t["six_2_0_cap_100k"]
R["october_topup_models"] = {"current_rates": t_new, "september_1_to_15_rates": t_old}
check("in October the top-up fits the 0.5% and 1.5% models, and the rates of September 1 to 15 at most once",
      t_new + t_old == t["fit_utc"] and t_old <= 1, f"{t_new} and {t_old} of {t['fit_utc']} fits")
log(f"  October 1 to 8 base: {b['fit_utc']} of {b['tested_wallets']} tested wallet-days within 1% of 4.5%, {b['fit_utc_within_5pct']} within 5%,"
    f" {b['unpaid']} unpaid. CET {b['fit_cet']}, CEST {b['fit_cest']}")
log(f"  October 1 to 8 top-up: {t['fit_utc']} of {t['tested_wallets']} within 1% ({t['standard_0_5']} at 0.5% capped at $5,000,"
    f" {t['six_1_5']} at 1.5%, {t['six_1_5_cap_100k']} at 1.5% capped at $100,000), {t['fit_utc_within_5pct']} within 5%, {t['unpaid']} unpaid."
    f" CET {t['fit_cet']}, CEST {t['fit_cest']}")
paid_all = Decimal(b["paid_usde"]) + Decimal(t["paid_usde"])
twa_all = Decimal(b["twa_usde_days"])
check("both accounts' October periods cover the same balances", Decimal(b["twa_usde_days"]) == Decimal(t["twa_usde_days"]))
R["october_avg_simple_pct"] = {"base": f"{Decimal(b['paid_usde']) / twa_all * 36500:.4f}", "topup": f"{Decimal(t['paid_usde']) / twa_all * 36500:.4f}",
                               "both": f"{paid_all / twa_all * 36500:.4f}"}
R["october_avg_compounded_pct"] = f"{compounded(paid_all / twa_all):.4f}"
R["october_paid_usde"] = {"base": b["paid_usde"], "topup": t["paid_usde"], "both": f"{paid_all:.6f}", "twa_usde_days": f"{twa_all:.6f}",
                          "average_balance_usde": f"{twa_all / len(OCT):.2f}"}
log(f"  October 1 to 8 paid {paid_all:.2f} USDe on {twa_all:.0f} USDe-days, {R['october_avg_simple_pct']['both']}% a year simple"
    f" (base {R['october_avg_simple_pct']['base']}%, top-up {R['october_avg_simple_pct']['topup']}%), {R['october_avg_compounded_pct']}% compounded")
oct_medians = {payer: {P[(payer, d)]["median_rate_simple_pct"] for d in OCT} for payer in ("base", "topup")}
check("every October median payment is the daily share of a compounded rate, 4.40195% and 0.49876% a year, not 4.5% and 0.5% divided by 365",
      oct_medians["base"] == {f"{SIMPLE['base_4_5']:.5f}"} and oct_medians["topup"] == {f"{SIMPLE['standard_0_5']:.5f}"})

# September, by accrual day
sep_days = [f"2026-09-{d:02d}" for d in range(1, 31)]


def periods_in(payer, days):
    return [p for p in periods if p["payer"] == payer and p["first_day"] in days]


sep = {payer: periods_in(payer, sep_days) for payer in ("base", "topup")}
for payer in ("base", "topup"):
    check(f"the {payer} periods cover every September day once",
          sum(int(p["days"]) for p in sep[payer]) == 30 and sep[payer][-1]["last_day"] == "2026-09-30")
sep_paid = {payer: Decimal(sum(int(p["paid_wei"]) for p in sep[payer])) / E18 for payer in ("base", "topup")}
sep_twa = Decimal(sum(int(p["twa_wei_days"]) for p in sep["base"])) / E18
check("both accounts' September periods cover the same balances", sep_twa == Decimal(sum(int(p["twa_wei_days"]) for p in sep["topup"])) / E18)
R["september"] = {"base_paid": f"{sep_paid['base']:.6f}", "topup_paid": f"{sep_paid['topup']:.6f}", "twa_usde_days": f"{sep_twa:.6f}",
                  "base_simple_pct": f"{sep_paid['base'] / sep_twa * 36500:.4f}", "topup_simple_pct": f"{sep_paid['topup'] / sep_twa * 36500:.4f}",
                  "both_simple_pct": f"{(sep_paid['base'] + sep_paid['topup']) / sep_twa * 36500:.4f}",
                  "cashflow_review_rate_pct": cashflow["sep_reward_rate_pct"][:6]}
log(f"  September accrual days paid {sep_paid['base'] + sep_paid['topup']:.2f} USDe on {sep_twa:.0f} USDe-days,"
    f" {R['september']['both_simple_pct']}% a year simple. The cash-flow review's payment-date rate was {R['september']['cashflow_review_rate_pct']}%")
check("the September accrual days' payments equal the cash-flow review's September rewards, 13,064.13 USDe",
      f"{sep_paid['base'] + sep_paid['topup']:.2f}" == "13064.13")


# the base account over September against 4.0% a year to September 16 and 4.5% from September 17
def base_model(p):
    return Decimal(int(p["twa_wei_days"])) / E18 * FACT["base_4_0" if p["last_day"] <= "2026-09-16" else "base_4_5"]


ratios = {p["first_day"]: Decimal(int(p["paid_wei"])) / E18 / base_model(p) for p in sep["base"]}
model_sep = sum(base_model(p) for p in sep["base"])
R["september_base_vs_model"] = {"paid": f"{sep_paid['base']:.6f}", "model": f"{model_sep:.6f}", "ratio": f"{sep_paid['base'] / model_sep:.4f}",
                                "lowest_day": min(ratios, key=ratios.get), "lowest_ratio": f"{min(ratios.values()):.3f}",
                                "highest_day": max(ratios, key=ratios.get), "highest_ratio": f"{max(ratios.values()):.3f}"}
check("over September the base account paid within 0.5% of 4.0% a year to September 16 and 4.5% from September 17",
      abs(sep_paid["base"] / model_sep - 1) < Decimal("0.005"), f"{sep_paid['base']:.2f} against {model_sep:.2f} USDe")

# rate changes in September, from the median payment of each period, which sits within 0.1% of one model
def median_is(p, name):
    return abs(Decimal(p["median_rate_simple_pct"]) / SIMPLE[name] - 1) < Decimal("0.001")


def periods_at(payer, name):
    return [p for p in periods if p["payer"] == payer and median_is(p, name)]


R["rate_changes"] = {"topup_last_1_0": periods_at("topup", "standard_1_0")[-1]["last_day"], "topup_first_0_5": periods_at("topup", "standard_0_5")[0]["first_day"],
                     "base_last_4_0": periods_at("base", "base_4_0")[-1]["last_day"], "base_first_4_5": periods_at("base", "base_4_5")[0]["first_day"]}
check("the median top-up fell from 1.0% to 0.5% a year between the accrual days of September 15 and 16",
      R["rate_changes"]["topup_last_1_0"] == "2026-09-15" and R["rate_changes"]["topup_first_0_5"] == "2026-09-16"
      and all(p["first_day"] <= "2026-09-15" for p in periods_at("topup", "standard_1_0")) and all(p["first_day"] >= "2026-09-16" for p in periods_at("topup", "standard_0_5")))
check("the median base payment rose from 4.0% to 4.5% a year between the accrual days of September 16 and 17",
      R["rate_changes"]["base_last_4_0"] == "2026-09-16" and R["rate_changes"]["base_first_4_5"] == "2026-09-17"
      and all(p["first_day"] <= "2026-09-16" for p in periods_at("base", "base_4_0")) and all(p["first_day"] >= "2026-09-17" for p in periods_at("base", "base_4_5")))
# which top-up rates matched before and after the change, leaving out the days the medians show as missed or caught up
normal_before = [p for p in periods if p["payer"] == "topup" and p["last_day"] <= "2026-09-15" and median_is(p, "standard_1_0")]
after_change = [p for p in periods if p["payer"] == "topup" and p["first_day"] >= "2026-09-16"]
R["topup_rates_matched"] = {
    "before": {"days": [p["first_day"] for p in normal_before], "standard_1_0": sum(n(p, "standard_1_0") for p in normal_before),
               "six_2_0": sum(n(p, "six_2_0") for p in normal_before), "six_2_0_cap_100k": sum(n(p, "six_2_0_cap_100k") for p in normal_before),
               "standard_0_5": sum(n(p, "standard_0_5") for p in normal_before), "six_1_5": sum(n(p, "six_1_5") + n(p, "six_1_5_cap_100k") for p in normal_before)},
    "after": {"days": len(after_change), "standard_0_5": sum(n(p, "standard_0_5") for p in after_change),
              "six_1_5": sum(n(p, "six_1_5") + n(p, "six_1_5_cap_100k") for p in after_change),
              "old_rates": sum(n(p, "standard_1_0") + n(p, "six_2_0") + n(p, "six_2_0_cap_100k") for p in after_change)}}
tb, ta = R["topup_rates_matched"]["before"], R["topup_rates_matched"]["after"]
check("on the regular days to September 15 the top-up matched only 1.0% to $5,000 and 2.0%, and from September 16 only 0.5% and 1.5% but twice",
      len(normal_before) == 10 and tb["standard_0_5"] == tb["six_1_5"] == 0 and tb["six_2_0"] > 0 and ta["old_rates"] == 2 and ta["six_1_5"] > 0,
      f"{tb['standard_1_0']} and {tb['six_2_0']} wallet-days before, {ta['standard_0_5']} and {ta['six_1_5']} after")
# every period whose median matches no model is a catch-up or a missed day
odd = [(p["payer"], p["first_day"], p["median_rate_simple_pct"]) for p in periods
       if not any(median_is(p, nm) for nm in (("base_4_5", "base_4_0") if p["payer"] == "base" else ("standard_0_5", "standard_1_0")))]
R["periods_off_model"] = odd
log("  periods whose median payment matches no model: " + "; ".join(f"{a} {b} {c}%" for a, b, c in odd))
check("the periods whose median matches no model are the ones the article names", [(a, b) for a, b, _ in odd] == [
    ("base", "2026-09-09"), ("base", "2026-09-10"), ("base", "2026-09-12"), ("base", "2026-09-25"), ("base", "2026-09-28"), ("base", "2026-09-29"),
    ("topup", "2026-09-04"), ("topup", "2026-09-07"), ("topup", "2026-09-08")], f"{len(odd)} periods")
base_sep_mid = [p for p in periods if p["payer"] == "base" and "2026-09-17" <= p["first_day"] <= "2026-09-28"]
R["base_sep_17_28"] = {"periods": len(base_sep_mid), "tested": sum(n(p, "tested_wallets") for p in base_sep_mid),
                       "fit": sum(n(p, "fit_utc") for p in base_sep_mid), "fit_4_5": sum(n(p, "base_4_5") for p in base_sep_mid),
                       "other": sum(n(p, "other") for p in base_sep_mid),
                       "unpaid": sum(n(p, "unpaid") for p in base_sep_mid),
                       "median_low": min(Decimal(p["median_rate_simple_pct"]) for p in base_sep_mid),
                       "median_high": max(Decimal(p["median_rate_simple_pct"]) for p in base_sep_mid)}
R["base_sep_17_28"] = {k: str(v) for k, v in R["base_sep_17_28"].items()}
check("from September 17 to 28 the median base payment was 4.40% to 4.46% a year", Decimal(R["base_sep_17_28"]["median_low"]) >= Decimal("4.40")
      and Decimal(R["base_sep_17_28"]["median_high"]) < Decimal("4.46"))
p1316 = P[("base", "2026-09-13")]
R["base_sep_13_16"] = {"last_day": p1316["last_day"], "paid_utc": p1316["first_payment_utc"], "batches": p1316["batches"], "tested": p1316["tested_wallets"],
                       "fit_4_0": p1316["base_4_0"], "fit_4_5": p1316["base_4_5"], "other": p1316["other"], "unpaid": p1316["unpaid"],
                       "median": p1316["median_rate_simple_pct"], "paid_usde": f"{Decimal(int(p1316['paid_wei'])) / E18:.6f}"}
check("the base account paid September 13 to 16 in one payment on September 17, its median at 4.0%",
      p1316["last_day"] == "2026-09-16" and p1316["batches"] == "1" and p1316["first_payment_utc"][:10] == "2026-09-17" and median_is(p1316, "base_4_0"))
p29 = P[("base", "2026-09-29")]
R["base_sep_29"] = {"median": p29["median_rate_simple_pct"], "other": p29["other"], "tested": p29["tested_wallets"]}
irregular = {"topup_sep_4_6": P[("topup", "2026-09-04")], "base_sep_9": P[("base", "2026-09-09")], "base_sep_12": P[("base", "2026-09-12")],
             "base_sep_13_16": P[("base", "2026-09-13")]}
R["irregular"] = {k: {"days": f"{v['first_day']} to {v['last_day']}", "tested": v["tested_wallets"], "unpaid": v["unpaid"], "paid_wallets": v["paid_wallets"],
                      "batches": v["batches"], "first_payment": v["first_payment_utc"]} for k, v in irregular.items()}

# the monthly card condition
def act(d, scope, c, col="wallets"):
    a = [x for x in activity if x["first_day"] == d and x["scope"] == scope and x["class"] == c]
    return int(a[0][col]) if a else 0


acto = {}
for d in OCT:
    e = {c: {"wallets": act(d, "ge100", c), "paid": act(d, "ge100", c, "paid_wallets"), "model": act(d, "ge100", c, "model_wallets"),
             "twa": str(Decimal(act(d, "ge100", c, "twa_wei_days")) / E18), "topup": str(Decimal(act(d, "ge100", c, "topup_wei")) / E18)} for c in "ABCD"}
    acto[d] = e
R["activity_october"] = acto
o1, o8 = acto["2026-10-01"], acto["2026-10-08"]
no_oct = lambda e: sum(e[c]["wallets"] for c in "BCD")
no_oct_paid = lambda e: sum(e[c]["paid"] for c in "BCD")
R["oct1"] = {"tested": sum(o1[c]["wallets"] for c in "ABCD"), "paid": sum(o1[c]["paid"] for c in "ABCD"), "with_october_spend": o1["A"]["wallets"],
             "without_october_spend": no_oct(o1), "without_october_spend_paid": no_oct_paid(o1), "never": o1["D"]["wallets"], "never_paid": o1["D"]["paid"]}
R["oct8"] = {"tested": sum(o8[c]["wallets"] for c in "ABCD"), "paid": sum(o8[c]["paid"] for c in "ABCD"), "with_october_spend": o8["A"]["wallets"],
             "without_october_spend": no_oct(o8), "without_october_spend_paid": no_oct_paid(o8), "never": o8["D"]["wallets"], "never_paid": o8["D"]["paid"],
             "never_twa": o8["D"]["twa"], "never_model": o8["D"]["model"]}
check("October 1: every tested wallet with an October card spend was paid", o1["A"]["paid"] == o1["A"]["wallets"])
check("October 8: every tested wallet that never used the card was paid", o8["D"]["paid"] == o8["D"]["wallets"])
wd = {k: sum(acto[d][c][k] for d in OCT for c in "BCD") for k in ("wallets", "paid")}
wd_never = {k: sum(acto[d]["D"][k] for d in OCT) for k in ("wallets", "paid")}
top_never = sum(Decimal(acto[d]["D"]["topup"]) for d in OCT)
top_no_oct = sum(Decimal(acto[d][c]["topup"]) for d in OCT for c in "BCD")
top_all_tested = sum(Decimal(acto[d][c]["topup"]) for d in OCT for c in "ABCD")
R["october_wallet_days"] = {"without_october_spend": wd["wallets"], "without_october_spend_paid": wd["paid"], "never": wd_never["wallets"],
                            "never_paid": wd_never["paid"], "topup_never_usde": f"{top_never:.6f}", "topup_without_october_spend_usde": f"{top_no_oct:.6f}",
                            "topup_tested_usde": f"{top_all_tested:.6f}", "topup_all_usde": t["paid_usde"]}
log(f"  October 1 to 8: {wd['paid']} of {wd['wallets']} tested wallet-days without an October card spend were paid the top-up,"
    f" {wd_never['paid']} of {wd_never['wallets']} for wallets that never used the card. They received {top_no_oct:.2f} and {top_never:.2f} USDe"
    f" of {Decimal(t['paid_usde']):.2f}")
sep_never = [(d, act(d, "ge100", "D"), act(d, "ge100", "D", "paid_wallets")) for d in sep_days if act(d, "ge100", "D")]
R["september_never"] = {"days": len(sep_never), "wallet_days": sum(x[1] for x in sep_never), "paid": sum(x[2] for x in sep_never)}
sep_from9 = [x for x in sep_never if x[0] >= "2026-09-09"]
R["september_never_from_9"] = {"days": len(sep_from9), "wallet_days": sum(x[1] for x in sep_from9), "paid": sum(x[2] for x in sep_from9)}
log(f"  September 9 to 30: {R['september_never_from_9']['paid']} of {R['september_never_from_9']['wallet_days']} tested wallet-days of never-used wallets paid")

# ---------------------------------------------------------------- whole calendar months, wallet by wallet
log()
log("Calendar months, wallet by wallet")
mw = rows(CH / "month_wallets.csv")
MONTH_DAYS = {"2026-09": sep_days, "2026-10": OCT}
# card payments in these rows against the first spend event in the published recount, which runs to the end of October 5
first_spend = {r["wallet"]: r["first_spend_ts"] for r in recount_wallets}
OCT1 = 1790812800   # 2026-10-01 00:00:00 UTC
OCT6 = OCT1 + 5 * 86400
assert datetime.fromtimestamp(OCT1, timezone.utc).isoformat() == "2026-10-01T00:00:00+00:00"
bad = []
for r in mw:
    fs = first_spend.get(r["wallet"], "")
    before, inm, after = (int(r[k]) for k in ("card_spends_before_month", "card_spends_in_month", "card_spends_after_month"))
    if r["month"] == "2026-09":
        if (before + inm > 0) != (fs != "" and int(fs) < OCT1):
            bad.append(r["wallet"])
    elif before + inm + after == 0 and fs != "":
        bad.append(r["wallet"])
check("every wallet's card payments to September 30, and every wallet with none to October 9, agree with its first spend event in the published recount",
      not bad, f"{len(mw)} wallet-months" + (", differ " + ", ".join(bad) if bad else ""))
GROUPS = ("spent in the month", "spent only after the month", "spent only before the month", "never used the card")
R["months"] = {}
month_rows = []
for month, days in MONTH_DAYS.items():
    sel = [r for r in mw if r["month"] == month]
    tp = [p for p in periods if p["payer"] == "topup" and p["first_day"] in days]
    month_topup = sum(int(p["paid_wei"]) for p in tp)
    check(f"{month} wallet rows add up to the top-up paid for the month's accrual days", sum(int(r["topup_wei"]) for r in sel) == month_topup,
          f"{Decimal(month_topup) / E18:.6f} USDe")
    check(f"{month} wallet rows hold every tested wallet-day", sum(int(r["tested_days"]) for r in sel) == sum(int(p["tested_wallets"]) * int(p["days"]) for p in tp))
    check(f"{month} wallet rows are one per wallet", len({r["wallet"] for r in sel}) == len(sel), f"{len(sel)} wallets")
    if month == "2026-10":
        check("no card spend falls after October in a read that ends on October 9", all(r["card_spends_after_month"] == "0" for r in sel))
    tested = [r for r in sel if int(r["tested_days"]) > 0]
    out = {}
    for r in tested:
        b, i, a = (int(r[k]) for k in ("card_spends_before_month", "card_spends_in_month", "card_spends_after_month"))
        g = GROUPS[0] if i else GROUPS[1] if a else GROUPS[2] if b else GROUPS[3]
        o = out.setdefault(g, {"wallets": 0, "paid": 0, "tested_days": 0, "topup_wei": 0, "twa_wei_days": 0, "exchanged": 0, "exchanged_with_spender": 0,
                               "never_linked_wallets": 0, "never_linked_paid": 0, "never_linked_topup_wei": 0})
        o["wallets"] += 1
        o["paid"] += int(r["topup_wei"]) > 0
        o["tested_days"] += int(r["tested_days"])
        o["topup_wei"] += int(r["topup_wei"])
        o["twa_wei_days"] += int(r["twa_wei_days"])
        o["exchanged"] += int(r["wallets_exchanged_with"]) > 0
        o["exchanged_with_spender"] += int(r["of_which_spent_in_month"]) > 0
        if int(r["wallets_exchanged_with"]) == 0:
            o["never_linked_wallets"] += 1
            o["never_linked_paid"] += int(r["topup_wei"]) > 0
            o["never_linked_topup_wei"] += int(r["topup_wei"])
    summ = {"wallets_tested": len(tested), "topup_usde": f"{Decimal(month_topup) / E18:.6f}",
            "topup_to_tested_usde": f"{Decimal(sum(int(r['topup_wei']) for r in tested)) / E18:.6f}"}
    for g in GROUPS:
        if g not in out:
            continue
        o = out[g]
        summ[g] = {"wallets": o["wallets"], "paid": o["paid"], "tested_wallet_days": o["tested_days"], "topup_usde": f"{Decimal(o['topup_wei']) / E18:.6f}",
                   "share_of_month_topup_pct": f"{Decimal(o['topup_wei']) / Decimal(month_topup) * 100:.2f}",
                   "average_balance_usde": f"{Decimal(o['twa_wei_days']) / E18 / len(days):.2f}",
                   "exchanged_usde_with_another_wallet": o["exchanged"], "exchanged_with_a_wallet_that_spent_in_the_month": o["exchanged_with_spender"],
                   "no_exchange_wallets": o["never_linked_wallets"], "no_exchange_paid": o["never_linked_paid"],
                   "no_exchange_topup_usde": f"{Decimal(o['never_linked_topup_wei']) / E18:.6f}"}
        month_rows.append([month, g, o["wallets"], o["paid"], o["tested_days"], f"{Decimal(o['topup_wei']) / E18:.6f}", summ[g]["share_of_month_topup_pct"],
                           summ[g]["average_balance_usde"], o["exchanged"], o["exchanged_with_spender"], o["never_linked_wallets"], o["never_linked_paid"],
                           f"{Decimal(o['never_linked_topup_wei']) / E18:.6f}"])
        log(f"  {month} {g}: {o['paid']} of {o['wallets']} paid, {Decimal(o['topup_wei']) / E18:.2f} USDe ({summ[g]['share_of_month_topup_pct']}%),"
            f" {o['exchanged']} exchanged USDe with another wallet, {o['exchanged_with_spender']} with one that spent in the month")
    none_wallets = [r for r in tested if r["card_spends_in_month"] == "0" and r["card_spends_after_month"] == "0"]
    summ["no_spend_from_month_start_to_october_9"] = {"wallets": len(none_wallets), "paid": sum(int(r["topup_wei"]) > 0 for r in none_wallets),
                                                      "topup_usde": f"{Decimal(sum(int(r['topup_wei']) for r in none_wallets)) / E18:.6f}",
                                                      "share_pct": f"{Decimal(sum(int(r['topup_wei']) for r in none_wallets)) / Decimal(month_topup) * 100:.2f}"}
    R["months"][month] = summ
sm = R["months"]["2026-09"]
nsp = sm["no_spend_from_month_start_to_october_9"]
log(f"  September: {nsp['paid']} of {nsp['wallets']} tested wallets with no card spend from September 1 to October 9 were paid {Decimal(nsp['topup_usde']):.2f} USDe,"
    f" {nsp['share_pct']}% of the September top-up")
check("September: every tested wallet that never used the card through October 9 received the top-up",
      sm["never used the card"]["paid"] == sm["never used the card"]["wallets"], f"{sm['never used the card']['wallets']} wallets")


# ---------------------------------------------------------------- one day in detail
def day_detail(d):
    wr = snap[d]
    out = {}
    twa = {r["wallet"]: Decimal(int(r["twa_micro"])) / 10 ** 6 for r in wr}
    tot_twa = sum(twa.values())
    base = sum(Decimal(int(r["base_wei"])) for r in wr) / E18
    top = sum(Decimal(int(r["topup_wei"])) for r in wr) / E18
    out["wallets"] = len(wr)
    out["funded"] = len(wr)  # every row held a balance that day, some under 0.000001 USDe
    out["twa_usde"] = f"{tot_twa:.6f}"
    out["base_paid"] = f"{base:.6f}"
    out["topup_paid"] = f"{top:.6f}"
    out["base_simple_pct"] = f"{base / tot_twa * 36500:.4f}"
    out["topup_simple_pct"] = f"{top / tot_twa * 36500:.4f}"
    out["both_simple_pct"] = f"{(base + top) / tot_twa * 36500:.4f}"
    both_daily = (base + top) / tot_twa
    out["both_compounded_pct"] = f"{(((1 + both_daily).ln() * 365).exp() - 1) * 100:.4f}"
    groups = {}
    boosted = Decimal(0)
    above = Decimal(0)
    per = []
    for r in wr:
        tw = twa[r["wallet"]]
        tp = Decimal(int(r["topup_wei"])) / E18
        bp = Decimal(int(r["base_wei"])) / E18
        if tw < 100:
            g = "small"
        else:
            g = classify("topup", tp, tw)
            if g == "other":
                loose = classify("topup", tp, tw, Decimal("0.05"))
                g = "other" if loose in ("other", "unpaid") else loose + "_within_5pct"
        key = g.replace("_within_5pct", "") if g.endswith("_within_5pct") else g
        cap = CAPS.get(key)
        b_in = min(tw, Decimal(cap)) if cap else Decimal(0)
        a_cap = tw - b_in if cap else Decimal(0)
        boosted += b_in
        above += a_cap
        o = groups.setdefault(g, {"wallets": 0, "twa": Decimal(0), "topup": Decimal(0), "base": Decimal(0), "boosted": Decimal(0), "above_cap": Decimal(0)})
        o["wallets"] += 1; o["twa"] += tw; o["topup"] += tp; o["base"] += bp; o["boosted"] += b_in; o["above_cap"] += a_cap
        per.append({"wallet": r["wallet"], "twa": tw, "topup": tp, "base": bp, "group": g, "cls": cls_of(r), "flows": r["other_flows"],
                    "above": a_cap})
    out["groups"] = {g: {k: (f"{v:.6f}" if isinstance(v, Decimal) else v) for k, v in o.items()} for g, o in sorted(groups.items())}
    out["boosted_usde"] = f"{boosted:.6f}"
    out["above_cap_usde"] = f"{above:.6f}"
    out["boosted_share_pct"] = f"{boosted / tot_twa * 100:.4f}"
    out["above_cap_share_pct"] = f"{above / tot_twa * 100:.4f}"
    tested = [x for x in per if x["twa"] >= 100]
    out["tested"] = len(tested)
    out["tested_twa"] = f"{sum(x['twa'] for x in tested):.6f}"
    six = [x for x in tested if x["group"].startswith("six")]
    out["six_wallets"] = len(six)
    out["six_twa"] = f"{sum(x['twa'] for x in six):.6f}"
    out["six_share_pct"] = f"{sum(x['twa'] for x in six) / tot_twa * 100:.4f}"
    out["six_over_100k_uncapped"] = sum(1 for x in six if x["twa"] > 100000 and x["group"].startswith("six_1_5") and "cap" not in x["group"])
    std = [x for x in tested if x["group"].startswith("standard")]
    out["standard_wallets"] = len(std)
    out["standard_over_5k"] = sum(1 for x in std if x["twa"] > 5000)
    never = [x for x in tested if x["cls"] == "D"]
    out["never_tested"] = len(never)
    out["never_paid"] = sum(1 for x in never if x["topup"] > 0)
    out["never_twa"] = f"{sum(x['twa'] for x in never):.6f}"
    out["never_topup"] = f"{sum(x['topup'] for x in never):.6f}"
    out["never_six"] = sum(1 for x in never if x["group"].startswith("six"))
    paid_small = [x for x in per if 0 < x["twa"] < 100 and x["topup"] > 0]
    out["small_paid"] = len(paid_small)
    min_top = min(Decimal(int(r["topup_wei"])) for r in wr if int(r["topup_wei"]) > 0) / E18
    out["min_topup_usde"] = f"{min_top:.9f}"
    capped = [x for x in std if x["twa"] > 5000]
    if capped:
        caps_paid = sorted(x["topup"] for x in capped)
        out["standard_capped_topup_range"] = [f"{caps_paid[0]:.6f}", f"{caps_paid[-1]:.6f}"]
    return out, per


det = {}
per_oct8 = None
for d in ("2026-10-01", "2026-10-08"):
    det[d], per = day_detail(d)
    if d == "2026-10-08":
        per_oct8 = per
R["day_detail"] = det
o8d = det["2026-10-08"]
check("the minimum top-up payment on October 1 and October 8 is 0.001 USDe or more",
      all(Decimal(det[d]["min_topup_usde"]) >= Decimal("0.001") for d in det))
check("every standard wallet above $5,000 received 5,000 x the 0.5% daily factor on October 1 and October 8, 0.068323 USDe",
      all(det[d]["standard_capped_topup_range"] == [f"{FACT['standard_0_5'] * 5000:.6f}"] * 2 for d in det), R["standard_cap_daily_usde"])
R["october_topup_unmatched"] = {"tested": t["tested_wallets"], "matched_current": t_new, "matched_old_rate": t_old, "unpaid": t["unpaid"],
                                "other": t["other"], "other_without_flows": t["other_without_flows"], "other_with_flows": t["other"] - t["other_without_flows"]}
check("October top-up wallet-days add up: matched, unpaid and other", t_new + t_old + t["unpaid"] + t["other"] == t["tested_wallets"])
# the wallets that never sent USDe to a settlement address through October 9, as they stood on October 8
never_oct = {r["wallet"] for r in mw if r["month"] == "2026-10" and r["card_spends_before_month"] == r["card_spends_in_month"] == r["card_spends_after_month"] == "0"}
n8t = [x for x in per_oct8 if x["wallet"] in never_oct and x["twa"] >= 100]
tot8 = Decimal(o8d["twa_usde"])
R["never_through_oct9_on_oct8"] = {"tested": len(n8t), "paid": sum(1 for x in n8t if x["topup"] > 0), "twa_usde": f"{sum(x['twa'] for x in n8t):.6f}",
                                   "share_of_all_usde_pct": f"{sum(x['twa'] for x in n8t) / tot8 * 100:.4f}", "six_group": sum(1 for x in n8t if x["group"].startswith("six")),
                                   "topup_usde": f"{sum(x['topup'] for x in n8t):.6f}", "largest_twa_usde": f"{max(x['twa'] for x in n8t):.2f}"}
check("October 8: every wallet with 100 USDe or more that never used the card through October 9 was paid the top-up",
      R["never_through_oct9_on_oct8"]["paid"] == R["never_through_oct9_on_oct8"]["tested"], f"{len(n8t)} wallets")
unpaid8 = [x for x in per_oct8 if x["twa"] >= 100 and x["topup"] == 0]
R["oct8_unpaid_tested"] = [{"wallet": x["wallet"], "twa": f"{x['twa']:.2f}", "base": f"{x['base']:.6f}"} for x in unpaid8]
check("the one tested wallet unpaid on October 8 received no base payment either", len(unpaid8) == 1 and unpaid8[0]["base"] == 0)
log(f"  October 8: {o8d['twa_usde'][:-7]} USDe time-weighted in {o8d['funded']} wallets. Paid {o8d['both_simple_pct']}% a year simple"
    f" ({o8d['both_compounded_pct']}% compounded). Boosted {o8d['boosted_share_pct']}%, above a cap {o8d['above_cap_share_pct']}%."
    f" 6% group {o8d['six_wallets']} wallets with {o8d['six_share_pct']}%")
log(f"  October 8: {o8d['never_paid']} of {o8d['never_tested']} tested wallets that never used the card were paid, holding {o8d['never_twa'][:-7]} USDe")

# day boundaries, on the wallet-days where either Central European balance is more than 2% away from the UTC balance
def fits_any(payer, paid, twa):
    """Whether a payment matches one of the October rates, 4.5% for the base and 0.5% to $5,000, 1.5%, or 1.5% to $100,000 for the top-up, within 1%."""
    if paid == 0:
        return False
    for name in (("base_4_5",) if payer == "base" else ("standard_0_5", "six_1_5", "six_1_5_cap_100k")):
        bal = twa if payer == "base" else min(twa, Decimal(CAPS[name]))
        if bal > 0 and abs(paid / (FACT[name] * bal) - 1) <= Decimal("0.01"):
            return True
    return False


R["day_boundaries"] = {}
for d, wr in snap.items():
    for payer, col in (("topup", "topup_wei"), ("base", "base_wei")):
        cnt = {"wallet_days": 0, "only_utc": 0, "only_central_europe": 0, "both": 0, "neither": 0}
        for r in wr:
            u, c1, c2 = (Decimal(int(r[k])) / 10 ** 6 for k in ("twa_micro", "twa_cet_micro", "twa_cest_micro"))
            if u < 100 or max(abs(c1 / u - 1), abs(c2 / u - 1)) <= Decimal("0.02"):
                continue
            paid = Decimal(int(r[col])) / E18
            fu, fc = fits_any(payer, paid, u), fits_any(payer, paid, c1) or fits_any(payer, paid, c2)
            cnt["wallet_days"] += 1
            cnt["only_utc" if fu and not fc else "only_central_europe" if fc and not fu else "both" if fu else "neither"] += 1
        R["day_boundaries"][f"{d} {payer}"] = cnt
db = R["day_boundaries"]
log("  where the day boundary matters: " + "; ".join(f"{k} {v['only_utc']} only UTC, {v['only_central_europe']} only Central Europe of {v['wallet_days']}" for k, v in db.items()))
check("where the day boundary matters, payments matched the UTC day and never only a Central European day",
      all(v["only_central_europe"] == 0 and v["only_utc"] > 50 for v in db.values()))

# the wallets that never used the card and were paid for September, as they stood on October 8
never_sep_paid = {r["wallet"] for r in mw if r["month"] == "2026-09" and int(r["tested_days"]) > 0 and int(r["topup_wei"]) > 0
                  and r["card_spends_before_month"] == r["card_spends_in_month"] == r["card_spends_after_month"] == "0"}
held8 = [x for x in per_oct8 if x["wallet"] in never_sep_paid and x["twa"] >= 100]
R["never_paid_september_on_oct8"] = {"wallets": len(held8), "at_a_tier_rate_within_1pct": sum(1 for x in held8 if x["group"] in CAPS)}
check("every wallet that never used the card, was paid for September and held 100 USDe or more on October 8 was paid a tier rate that day",
      R["never_paid_september_on_oct8"]["wallets"] == R["never_paid_september_on_oct8"]["at_a_tier_rate_within_1pct"] == 32, f"{len(held8)} wallets")

# small balances in October: the Boost paid against 0.5% of the balance over the eight days
small_oct = [r for r in mw if r["month"] == "2026-10" and r["tested_days"] == "0" and int(r["topup_wei"]) > 0]
ratios = sorted(Decimal(int(r["topup_wei"])) / (Decimal(int(r["twa_wei_days"])) * FACT["standard_0_5"]) for r in small_oct)
R["small_balances_october"] = {"wallets_paid": len(small_oct), "paid_on_one_day": sum(1 for r in small_oct if r["paid_days"] == "1"),
                               "median_paid_over_accrual": f"{ratios[len(ratios) // 2]:.3f}", "lower_quartile": f"{ratios[len(ratios) // 4]:.3f}",
                               "upper_quartile": f"{ratios[3 * len(ratios) // 4]:.3f}", "balance_for_0_001_a_day": f"{Decimal('0.001') / FACT['standard_0_5']:.2f}"}
band = {d: [r for r in wr if Decimal("73.2") * 10 ** 6 <= int(r["twa_micro"]) < 100 * 10 ** 6] for d, wr in snap.items()}
R["small_balances_october"]["73_to_100_usde_paid"] = {d: f"{sum(1 for r in b if int(r['topup_wei']) > 0)} of {len(b)}" for d, b in band.items()}
still1 = [r for r in snap["2026-10-01"] if r["other_flows"] == "0" and 0 < int(r["topup_wei"]) and int(r["twa_micro"]) < 10 * 10 ** 6]
lowest = min(still1, key=lambda r: int(r["twa_micro"]))
R["small_balances_october"]["example"] = {"wallet": lowest["wallet"], "twa_usde": f"{Decimal(int(lowest['twa_micro'])) / 10 ** 6:.6f}",
                                          "topup_usde": f"{Decimal(int(lowest['topup_wei'])) / E18:.9f}",
                                          "days_of_accrual": f"{Decimal(int(lowest['topup_wei'])) / E18 / (Decimal(int(lowest['twa_micro'])) / 10 ** 6 * FACT['standard_0_5']):.2f}"}
check("wallets that never averaged 100 USDe in a period were paid about their 0.5% accrual over October 1 to 8, in lumps",
      Decimal("0.9") < ratios[len(ratios) // 2] < Decimal("1.1") and all(b and all(int(r["topup_wei"]) > 0 for r in b) for b in band.values()),
      f"{len(small_oct)} wallets, median {ratios[len(ratios) // 2]:.3f}")
std_big = [x for x in per_oct8 if x["group"].startswith("standard") and x["twa"] > 100000]
R["standard_over_100k_oct8"] = len(std_big)

# wallets first funded from another wallet, among the never-used wallets on October 8
first_kind = {r["wallet"]: r["first_in_kind"] for r in recount_wallets}
never8 = [x for x in per_oct8 if x["twa"] >= 100 and x["cls"] == "D"]
R["never_oct8_first_funded_by_wallet"] = sum(1 for x in never8 if first_kind.get(x["wallet"]) == "i")
R["never_oct8_created_after_recount"] = sum(1 for x in never8 if x["wallet"] not in first_kind)
log(f"  of those, {R['never_oct8_first_funded_by_wallet']} were first funded from another EthenaPay wallet and"
    f" {R['never_oct8_created_after_recount']} received their first USDe after October 5")

# payment times in October
R["payment_times"] = {payer: [P[(payer, d)]["first_payment_utc"] for d in OCT] for payer in ("base", "topup")}

# ---------------------------------------------------------------- stop if anything failed
log()
if failures:
    log(f"{len(failures)} checks failed. Nothing written.")
    (HERE / "run_log_failed.txt").write_text("\n".join(log_lines) + "\n")
    sys.exit(1)

OUT.mkdir(exist_ok=True)
with open(OUT / "october_days.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["accrual_day", "base_paid_utc", "topup_paid_utc", "tested_wallets", "base_fit", "base_fit_cet", "base_fit_cest", "base_unpaid",
                "topup_fit", "topup_fit_cet", "topup_fit_cest", "topup_within_5pct", "topup_at_0_5", "topup_at_1_5", "topup_at_1_5_cap_100k",
                "topup_unpaid", "topup_other", "card_payment_in_october_by_end_of_day", "card_payment_in_october_paid", "no_card_payment_in_october_by_end_of_day",
                "no_card_payment_in_october_paid", "never_used_card_by_end_of_day", "never_used_card_paid", "base_paid_usde", "topup_paid_usde", "twa_usde_days"])
    for d in OCT:
        pb, pt, e = P[("base", d)], P[("topup", d)], acto[d]
        w.writerow([d, pb["first_payment_utc"], pt["first_payment_utc"], pt["tested_wallets"], pb["fit_utc"], pb["fit_cet"], pb["fit_cest"], pb["unpaid"],
                    pt["fit_utc"], pt["fit_cet"], pt["fit_cest"], pt["fit_utc_within_5pct"], pt["standard_0_5"], pt["six_1_5"], pt["six_1_5_cap_100k"],
                    pt["unpaid"], pt["other"], e["A"]["wallets"], e["A"]["paid"], no_oct(e), no_oct_paid(e), e["D"]["wallets"], e["D"]["paid"],
                    f"{Decimal(int(pb['paid_wei'])) / E18:.6f}", f"{Decimal(int(pt['paid_wei'])) / E18:.6f}", f"{Decimal(int(pt['twa_wei_days'])) / E18:.6f}"])
with open(OUT / "september_days.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["payer", "first_day", "last_day", "days", "first_payment_utc", "tested_wallets", "fit_within_1pct", "model_4_5_or_0_5_1_5", "model_4_0_or_1_0_2_0",
                "unpaid", "other", "median_rate_simple_pct", "never_used_card_by_end_of_first_day", "never_used_card_by_end_of_first_day_paid"])
    for p in periods:
        if p["first_day"] > "2026-09-30":
            continue
        new = n(p, "base_4_5") if p["payer"] == "base" else n(p, "standard_0_5") + n(p, "six_1_5") + n(p, "six_1_5_cap_100k")
        old = n(p, "base_4_0") if p["payer"] == "base" else n(p, "standard_1_0") + n(p, "six_2_0") + n(p, "six_2_0_cap_100k")
        nv = (act(p["first_day"], "ge100", "D"), act(p["first_day"], "ge100", "D", "paid_wallets")) if p["payer"] == "topup" else ("", "")
        w.writerow([p["payer"], p["first_day"], p["last_day"], p["days"], p["first_payment_utc"], p["tested_wallets"], p["fit_utc"], new, old,
                    p["unpaid"], p["other"], p["median_rate_simple_pct"], nv[0], nv[1]])
with open(OUT / "month_groups.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["month", "card_spend", "tested_wallets", "paid_wallets", "tested_wallet_days", "topup_usde", "share_of_month_topup_pct", "average_balance_usde",
                "exchanged_usde_with_another_wallet", "exchanged_with_a_wallet_that_spent_in_the_month", "no_exchange_wallets", "no_exchange_paid",
                "no_exchange_topup_usde"])
    w.writerows(month_rows)
with open(OUT / "wallets_2026-10-08.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["wallet", "twa_usde", "base_usde", "topup_usde", "topup_rate_simple_pct", "group", "card_spend_by_october_8", "never_used_card_through_october_9",
                "balance_moved", "above_cap_usde"])
    names = {"A": "spent in October", "B": "spent in September only", "C": "spent before September only", "D": "never"}
    for x in per_oct8:
        if x["twa"] < 100:
            continue
        rate = x["topup"] / x["twa"] * 36500
        w.writerow([x["wallet"], f"{x['twa']:.6f}", f"{x['base']:.9f}", f"{x['topup']:.9f}", f"{rate:.5f}", x["group"], names[x["cls"]],
                    "yes" if x["wallet"] in never_oct else "no", x["flows"], f"{x['above']:.6f}"])
# chart data: the top-up rate against the balance, October 8, for tested wallets paid a top-up
with open(OUT / "chart_points.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["wallet", "twa_usde", "topup_rate_simple_pct", "series"])
    for x in per_oct8:
        if x["twa"] < 100 or x["topup"] == 0:
            continue
        w.writerow([x["wallet"], f"{x['twa']:.2f}", f"{x['topup'] / x['twa'] * 36500:.5f}",
                    "never used the card" if x["wallet"] in never_oct else "used the card"])
with open(OUT / "chart_lines.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["twa_usde", "standard_0_5_cap_5k_pct", "six_1_5_pct", "six_1_5_cap_100k_pct"])
    for k in range(81):  # 20 steps a decade from $100 to $1,000,000
        x = Decimal(round(100 * 10 ** (k / 20)))
        w.writerow([f"{x:.0f}", f"{SIMPLE['standard_0_5'] * min(1, Decimal(5000) / x):.5f}", f"{SIMPLE['six_1_5']:.5f}",
                    f"{SIMPLE['six_1_5'] * min(1, Decimal(100000) / x):.5f}"])
R["checks_passed"] = len([l for l in log_lines if l.startswith("ok")])
(OUT / "results.json").write_text(json.dumps(R, indent=1, default=str) + "\n")
log(f"All {R['checks_passed']} checks passed. Tables written to out/.")
(OUT / "run_log.txt").write_text("\n".join(log_lines) + "\n")
