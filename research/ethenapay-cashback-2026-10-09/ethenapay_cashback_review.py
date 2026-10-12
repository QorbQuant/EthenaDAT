#!/usr/bin/env python3
"""EthenaPay cashback review: what the two cashback accounts paid EthenaPay wallets in AVAX to October 9, 2026, and
how it compares with the cashback rates on the Ethena Pay Pricing page.

Reads the files cashback_recount.cjs wrote in inputs/chain/, checks them against the chain recount this site published
with its EthenaPay adoption review and against the daily file and cashback figures in its cash-flow review, and works out what
cashback paid by month, at the Chainlink AVAX / USD price in force at each transfer, for isolated card payments, and wallet by wallet
against the three tier schedules. If any check fails the script stops before writing anything, so out/ keeps the tables
of the last clean run. Python 3 standard library only. No network.
"""
import csv
import hashlib
import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path

getcontext().prec = 60
getcontext().rounding = ROUND_HALF_UP   # every figure written is rounded half up
HERE = Path(__file__).parent
INP = HERE / "inputs"
CH = INP / "chain"
OUT = HERE / "out"
E18 = 10 ** 18
E26 = Decimal(10) ** 26   # AVAX wei times an 8-decimal price gives dollars after dividing by 10 ** 26
DAY = 86400

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


def ts(y, m, d, hh=0, mm=0):
    return int(datetime(y, m, d, hh, mm, tzinfo=timezone.utc).timestamp())


def iso(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def month_of(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m")


def avax(wei):
    return Decimal(wei) / E18


def usd(wei, answer):
    return Decimal(wei) * answer / E26


def money(x):
    return f"{Decimal(x):,.2f}"


# ---------------------------------------------------------------- the published schedule
# Pricing page, Section 3.1, effective September 1, 2026 and last updated September 30, 2026: the cashback rate for
# each band of spend in a calendar month. Each rate applies only to the spend inside its band.
SCHEDULE = {
    "standard": [(2500, "0.04"), (4000, "0.01"), (None, "0")],
    "pro": [(8000, "0.045"), (10000, "0.02"), (12000, "0.01"), (None, "0.005")],
    "vip": [(20000, "0.05"), (30000, "0.02"), (40000, "0.01"), (None, "0.005")],
}


def schedule(tier, spend):
    """Cashback in dollars for a calendar month's spend in dollars under a tier's bands."""
    spend, out, lo = Decimal(spend), Decimal(0), Decimal(0)
    for hi, rate in SCHEDULE[tier]:
        top = spend if hi is None else min(spend, Decimal(hi))
        if top > lo:
            out += (top - lo) * Decimal(rate)
        if hi is None or spend <= hi:
            break
        lo = Decimal(hi)
    return out


STANDARD_MAX = schedule("standard", 4000)

# ---------------------------------------------------------------- inputs and their fingerprints
log("EthenaPay cashback review")
log("Inputs")
manifest = rows(INP / "manifest.csv")
for m in manifest:
    p = INP / m["file"]
    check(f"input {m['file']} matches its SHA-256", p.exists() and sha(p) == m["sha256"] and p.stat().st_size == int(m["bytes"]))
listed = {m["file"] for m in manifest}
on_disk = {str(p.relative_to(INP)) for p in INP.rglob("*") if p.is_file() and p.name != "manifest.csv"}
check("the manifest lists every input file", listed == on_disk, f"{len(listed)} files")

chain_manifest = rows(INP / "chain_manifest.csv")
script_sha = sha(HERE / "cashback_recount.cjs")
for m in chain_manifest:
    check(f"chain file {m['file']} is the one the run wrote", sha(CH / m["file"]) == m["sha256"])
    check(f"chain file {m['file']} came from this cashback_recount.cjs", m["script_sha256"] == script_sha)
check("the chain manifest lists every chain file", {m["file"] for m in chain_manifest} == {p.name for p in CH.iterdir() if p.is_file()})

meta = json.loads((CH / "meta.json").read_text())
recount_meta = json.loads((INP / "recount" / "meta.json").read_text())
recount_wallets = rows(INP / "recount" / "wallet_activity.csv")
recount_days = rows(INP / "recount" / "daily_chain_62503a1.csv")
cashflow = json.loads((INP / "cashflow_results.json").read_text())
terms = {r["id"]: r for r in rows(INP / "terms_facts.csv")}

spend_rows = rows(CH / "spends.csv")
# every USDe transfer from a wallet to a settlement address, for the cross-checks with the recount, which counts transfers
transfers_c = [(int(r["wallet"]), int(r["ts"]), int(r["cents"])) for r in spend_rows if r["kind"] == "c"]
# the card payments this review counts are spend events, the transfers an AllowanceSpent log matches, and reversals
spends = [(int(r["wallet"]), int(r["ts"]), r["kind"], int(r["cents"])) for r in spend_rows if r["kind"] == "r" or r["spend_event"] == "1"]
cb = []
for r in rows(CH / "cashback.csv"):
    x = {"payer": int(r["payer"]), "batch": int(r["batch"]), "wallet": int(r["wallet"]), "ts": int(r["ts"]), "wei": int(r["avax_wei"]),
         "round": int(r["cl_round"]) if r["cl_round"] else None, "answer": Decimal(r["cl_answer"]) if r["cl_answer"] else None}
    x["usd"] = usd(x["wei"], x["answer"]) if x["answer"] is not None else None
    cb.append(x)
batches = []
for r in rows(CH / "batches.csv"):
    batches.append({"payer": int(r["payer"]), "batch": int(r["batch"]), "first": int(r["first_ts"]), "last": int(r["last_ts"]),
                    "transfers": int(r["transfers"]), "transactions": int(r["transactions"]), "recipients": int(r["recipients"]),
                    "wei": int(r["avax_wei"]), "round": int(r["cl_round"]) if r["cl_round"] else None,
                    "answer": Decimal(r["cl_answer"]) if r["cl_answer"] else None, "updated": int(r["cl_updated"]) if r["cl_updated"] else None})
prices = [{"time": r["time"], "round": int(r["round"]), "answer": Decimal(r["answer"]), "updated": int(r["updated"])} for r in rows(CH / "prices_hourly.csv")]
others = [{"payer": int(r["payer"]), "recipient": int(r["recipient"]), "ts": int(r["ts"]), "wei": int(r["avax_wei"]), "in_wei": int(r["same_tx_in_wei"])}
          for r in rows(CH / "other_recipients.csv")]

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
      recount_sum == int(cc["recount_balance_sum_wei"]) == int(recount_meta["balance_check"]["sum_wei"]), f"{Decimal(recount_sum) / E18:.6f} USDe")
day_canon = "".join(",".join([r["date"], r["deposits_wei"], r["withdrawals_wei"], r["reversals_wei"], r["yield_wei"], r["other_rewards_wei"],
                              r["card_spend_wei"], r["internal_wei"], r["held_wei"]]) + "\n" for r in recount_days)
check("daily flows and USDe held on all 144 days to October 5 match the published recount to the wei",
      hashlib.sha256(day_canon.encode()).hexdigest() == cc["utc_days_sha256"] and len(recount_days) == cc["utc_days_compared"] == 144)
check("the wallet count to October 5 matches the recount", recount_meta["wallets"] == 14103 and meta["wallets"] >= 14103, f"{meta['wallets']} wallets to October 9")
card_wei_recount = sum(int(r["card_spend_wei"]) for r in recount_days)
card_wei_after = sum(c for w, t, c in transfers_c if t >= ts(2026, 10, 6)) * 10 ** 16
sep_days_wei = sum(int(r["card_spend_wei"]) for r in recount_days if "2026-09-01" <= r["date"] <= "2026-09-30")
check("September card spend in the recount's daily file equals the USDe transfers to settlement addresses in spends.csv to the wei",
      sep_days_wei == sum(c for w, t, c in transfers_c if ts(2026, 9, 1) <= t < ts(2026, 10, 1)) * 10 ** 16)
check("transfers to settlement addresses to October 5 in the recount, plus those after it here, equal the run's total to the wei",
      card_wei_recount + card_wei_after == int(meta["card_payment_wei"]), f"{Decimal(meta['card_payment_wei']) / E18:,.2f} USDe in {meta['card_payments']:,} transfers")

log()
log("The chain read")
check("block 97,161,009 is the last block of October 9 UTC",
      meta["end_block"] == 97161009 and meta["end_block_time"] == "2026-10-09T23:59:59Z" and meta["next_block_time"] == "2026-10-10T00:00:01Z")
check("block 93,220,397 is the first block of August 20 UTC", meta["price_start_block_time"] == "2026-08-20T00:00:00Z")
cl = meta["chainlink"]
check("the Chainlink AVAX / USD proxy points to the phase 2 aggregator, with 8 decimals",
      cl["proxy"] == "0x0a77230d17318075983913bc2145db16c7366156" and cl["aggregator"] == "0xcfbfe648ba88bf7d9776d970417a0b26c315feb4"
      and cl["phase"] == 2 and cl["decimals"] == 8)
check("a Chainlink round was in force at 00:00 UTC on August 20 and the last one read is from October 9",
      cl["first_updated"] < "2026-08-20T00:00:00Z" and cl["last_updated"].startswith("2026-10-09"), f"{cl['rounds']:,} rounds")
for i, k in enumerate(meta["cashback_account_rows"]):
    to_wallets = meta["cashback_transfers"][i]
    to_other = sum(1 for o in others if o["payer"] == i)
    check(f"every row the explorer returned for cashback account {i} is counted once",
          k["rows"] == to_wallets + to_other + k["in_rows"] + k["in_failed_or_zero"] + k["neither"] + k["out_failed"] + k["out_zero"]
          and k["out_failed"] == 0 and k["out_zero"] == 0, f"{k['rows']:,} rows")
check("the two accounts paid wallets 9,036 times", sum(meta["cashback_transfers"]) == 9036)
se = meta["spend_events"]
check("every AllowanceSpent log to a settlement address was for USDe and came from a wallet",
      all(set(v) == {"0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34"} for v in meta["spend_logs_by_token"].values())
      and sum(sum(v.values()) for v in meta["spend_logs_by_token"].values()) == se["usde_logs"] == se["from_wallets"], f"{se['usde_logs']:,} spend events")
check("each spend event matched one transfer to a settlement address, and one such transfer of 5 USDe had no spend event",
      se["matched_to_card_payments"] == se["usde_logs"] and se["events_without_card_payment"] == 0 and se["card_payments_without_event"] == 1
      and se["card_payments_without_event_wei"] == str(5 * E18) and se["matched_to_card_payments"] + 1 == meta["card_payments"])
bare = [r for r in spend_rows if r["kind"] == "c" and r["spend_event"] == "0"]
check("spends.csv marks that one transfer, on September 24", len(bare) == 1 and bare[0]["cents"] == "500"
      and datetime.fromtimestamp(int(bare[0]["ts"]), timezone.utc).strftime("%Y-%m-%d") == "2026-09-24")
check("all reversals and no transfers to a settlement address leave the spend-event column empty", all((r["spend_event"] == "") == (r["kind"] == "r") for r in spend_rows))

# batches against the totals, and cashback.csv against the batches it covers
for i in (0, 1):
    bs = [b for b in batches if b["payer"] == i]
    check(f"account {i}'s batches add up to its transfers and AVAX",
          sum(b["transfers"] for b in bs) == meta["cashback_transfers"][i] and sum(b["wei"] for b in bs) == int(meta["cashback_avax_wei"][i]),
          f"{len(bs)} batches, {avax(sum(b['wei'] for b in bs)):,.6f} AVAX")
check("the first and last cashback transfers match the run's dates",
      iso(min(b["first"] for b in batches)) == meta["cashback_first"] and iso(max(b["last"] for b in batches)) == meta["cashback_last"])
ROWS_FROM = ts(2026, 8, 15)
by_batch = defaultdict(lambda: [0, 0])
for x in cb:
    by_batch[(x["payer"], x["batch"])][0] += 1
    by_batch[(x["payer"], x["batch"])][1] += x["wei"]
covered = [b for b in batches if b["first"] >= ROWS_FROM]
check("cashback.csv holds every transfer of every batch from August 15 and nothing earlier",
      all(by_batch[(b["payer"], b["batch"])] == [b["transfers"], b["wei"]] for b in covered) and len(by_batch) == len(covered)
      and min(x["ts"] for x in cb) >= ROWS_FROM, f"{len(cb):,} transfers in {len(covered)} batches")
check("from August 15 each batch paid each wallet once", all(b["transfers"] == b["recipients"] for b in covered))
PRICE_FROM = ts(2026, 8, 20)
check("every transfer from August 20 carries a Chainlink price and none before it does",
      all((x["answer"] is not None) == (x["ts"] >= PRICE_FROM) for x in cb))
first_of = {(b["payer"], b["batch"]): b for b in batches}
check("each batch's first transfer carries the batch's round, and later transfers in a batch never an earlier one",
      all(x["round"] >= first_of[(x["payer"], x["batch"])]["round"] and (x["ts"] != first_of[(x["payer"], x["batch"])]["first"]
          or x["round"] == first_of[(x["payer"], x["batch"])]["round"]) for x in cb if x["answer"] is not None))
check("every price read is between $5 and $20 an AVAX", all(Decimal(5e8) < p["answer"] < Decimal(20e8) for p in prices)
      and all(Decimal(5e8) < x["answer"] < Decimal(20e8) for x in cb if x["answer"] is not None))
check("the hourly table runs from 00:00 UTC August 20 to 00:00 UTC October 10 with no gap",
      len(prices) == (ts(2026, 10, 10) - ts(2026, 8, 20)) // 3600 + 1 and prices[0]["time"] == "2026-08-20T00:00:00Z"
      and all(p["updated"] <= ts(2026, 8, 20) + 3600 * i for i, p in enumerate(prices)))

# against the cash-flow review
log()
log("Cross-checks with the cash-flow review")
S0, S1 = ts(2026, 9, 1), ts(2026, 10, 1)
sep_card = sum(c for w, t, k, c in spends if k == "c" and S0 <= t < S1)
sep_rev = sum(c for w, t, k, c in spends if k == "r" and S0 <= t < S1)
sep_transfers = sum(c for w, t, c in transfers_c if S0 <= t < S1)
check("September's USDe transfers to the settlement addresses equal the review's card spend", Decimal(sep_transfers) / 100 == Decimal(cashflow["sep_card_spend"]),
      f"{money(Decimal(sep_transfers) / 100)} USDe")
check("September's spend events equal the review's spend-event total", Decimal(sep_card) / 100 == Decimal(cashflow["sep_card_spend_events_usde"]),
      f"{money(Decimal(sep_card) / 100)} USDe")
check("spend events to the end of October 5 equal the review's count and total",
      se["to_october_5"]["logs"] == cashflow["spend_events"] and Decimal(se["to_october_5"]["usde_wei"]) / E18 == Decimal(cashflow["card_spend_events_usde"]),
      f"{se['to_october_5']['logs']:,} events")
rev_from_review = Decimal(cashflow["sep_card_spend"]) * Decimal(cashflow["sep_reversal_rate_pct"]) / 100
check("September reversals match the review's reversal rate", abs(Decimal(sep_rev) / 100 - rev_from_review) < Decimal("0.005"), f"{money(Decimal(sep_rev) / 100)} USDe")
sep_wei = sum(b["wei"] for b in batches if S0 <= b["first"] < S1)
check("cashback in September batches equals the review's September cashback",
      abs(avax(sep_wei) - Decimal(cashflow["sep_cashback_avax"])) < Decimal("1e-12"), f"{avax(sep_wei):,.6f} AVAX")
to_oct5 = sum(b["wei"] for b in batches if b["first"] < ts(2026, 10, 6))
check("cashback to the end of October 5 equals the review's total, which came from the dashboard's daily sums, to a billionth of an AVAX",
      abs(avax(to_oct5) - Decimal(cashflow["cashback_avax_to_cutoff"])) < Decimal("1e-9"), f"{avax(to_oct5):,.6f} AVAX")
oct5 = [b for b in batches if ts(2026, 10, 5) <= b["first"] < ts(2026, 10, 6)]
check("the October 5 batch matches the review's worked day",
      len(oct5) == 1 and oct5[0]["recipients"] == cashflow["worked_cashback_wallets"] == 335
      and abs(avax(oct5[0]["wei"]) - Decimal(str(cashflow["worked_cashback_avax"]))) < Decimal("1e-9"))

# the schedule as published
check("the schedule gives the FAQ's worked example, $380 for $9,000 of Pro spend", schedule("pro", 9000) == 380)
check("Standard cashback stops at $115 a month however much is spent", STANDARD_MAX == 115 and schedule("standard", 50000) == 115)
check("terms_facts.csv records the bands the script uses",
      all(s in terms["bands"]["fact"] for s in ("4% on the first $2,500", "1% from $2,500 to $4,000", "nothing above $4,000", "4.5% to $8,000",
                                                 "2% to $10,000", "1% to $12,000", "0.5% above", "5% to $20,000", "2% to $30,000", "1% to $40,000")))

R = {"read_through": "2026-10-09T23:59:59Z", "run_utc": [meta["run_started_utc"], meta["run_finished_utc"]]}

# ---------------------------------------------------------------- what the two accounts paid
log()
log("What the two accounts paid")
tot_wei = sum(int(v) for v in meta["cashback_avax_wei"])
R["lifetime"] = {"transfers": sum(meta["cashback_transfers"]), "avax": f"{avax(tot_wei):.6f}", "wallets": meta["cashback_wallets"],
                 "first": meta["cashback_first"], "last": meta["cashback_last"],
                 "by_account": [{"transfers": meta["cashback_transfers"][i], "avax": f"{avax(int(meta['cashback_avax_wei'][i])):.6f}",
                                 "batches": sum(1 for b in batches if b["payer"] == i),
                                 "first": iso(min(b["first"] for b in batches if b["payer"] == i)),
                                 "last": iso(max(b["last"] for b in batches if b["payer"] == i))} for i in (0, 1)]}
log(f"  {R['lifetime']['transfers']:,} transfers, {avax(tot_wei):,.6f} AVAX, {meta['cashback_wallets']} wallets, {meta['cashback_first']} to {meta['cashback_last']}")
months = []
for mo in ("2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10"):
    bs = [b for b in batches if month_of(b["first"]) == mo]
    xs = [x for x in cb if month_of(x["ts"]) == mo]
    full = mo in ("2026-09", "2026-10")
    priced = full
    m = {"month": mo, "batches": len(bs), "transfers": sum(b["transfers"] for b in bs), "avax": f"{avax(sum(b['wei'] for b in bs)):.6f}",
         "wallets": len({x["wallet"] for x in xs}) if full else "",
         "usd_at_chainlink": f"{sum(x['usd'] for x in xs):.2f}" if priced else ""}
    if full:
        check(f"{mo} transfers in cashback.csv equal the month's batches", len(xs) == m["transfers"])
    months.append(m)
    log(f"  {mo}: {m['batches']} batches, {m['transfers']:,} transfers, {Decimal(m['avax']):,.2f} AVAX" + (f", {m['wallets']} wallets, ${Decimal(m['usd_at_chainlink']):,.2f}" if full else ""))
R["months"] = months
check("the months add up to the total", sum(b["wei"] for b in batches if month_of(b["first"]) in {m["month"] for m in months}) == tot_wei
      and sum(m["transfers"] for m in months) == 9036 and sum(m["batches"] for m in months) == len(batches))

# batch times
S0_BATCH = ts(2026, 9, 1)
recent = [b for b in batches if b["first"] >= ROWS_FROM]
at_0230 = [b for b in recent if b["first"] % DAY // 60 == 150]
other_times = Counter(iso(b["first"])[11:16] for b in recent if b["first"] % DAY // 60 != 150)
sep_oct = [b for b in batches if b["first"] >= S0_BATCH]
two_tx = [b for b in sep_oct if b["transactions"] > 1]
R["batch_times"] = {"batches_from_august_15": len(recent), "first_transfer_at_0230": len(at_0230), "other_first_times": dict(sorted(other_times.items())),
                    "september_october_batches": len(sep_oct), "september_october_at_0230": sum(1 for b in sep_oct if b["first"] % DAY // 60 == 150),
                    "september_october_batches_in_two_transactions": len(two_tx),
                    "first_two_transaction_batch": iso(min(b["first"] for b in two_tx))[:10],
                    "largest_batch_transfers": max(b["transfers"] for b in batches),
                    "largest_batch_date": iso(max(batches, key=lambda b: b["transfers"])["first"])[:10],
                    "current_account_first_batch": iso(min(b["first"] for b in batches if b["payer"] == 0))}
gaps = [b["last"] - b["first"] for b in two_tx]
R["batch_times"]["two_transaction_gap_under_1_minute"] = sum(1 for g in gaps if g < 60)
R["batch_times"]["two_transaction_gap_29_to_31_minutes"] = sum(1 for g in gaps if 29 * 60 <= g <= 31 * 60)
R["batch_times"]["batches_from_september_19"] = sum(1 for b in batches if b["first"] >= ts(2026, 9, 19))
check("from September 19 every second transaction came within a minute or about half an hour after the first",
      R["batch_times"]["two_transaction_gap_under_1_minute"] + R["batch_times"]["two_transaction_gap_29_to_31_minutes"] == len(two_tx)
      and min(b["first"] for b in two_tx) >= ts(2026, 9, 19))
priced_batches = [b for b in batches if b["answer"] is not None]
R["price_age"] = {"max_seconds_at_batch_first_transfer": max(b["first"] - b["updated"] for b in priced_batches),
                  "max_seconds_on_the_hour": max(ts(2026, 8, 20) + 3600 * i - p["updated"] for i, p in enumerate(prices))}
sepb = sorted((b for b in batches if S0_BATCH <= b["first"] < ts(2026, 10, 1)), key=lambda b: b["first"])
R["september_batch_prices"] = {"first_batch": iso(sepb[0]["first"]), "first_price": f"{sepb[0]['answer'] / 10 ** 8:.4f}",
                               "last_batch": iso(sepb[-1]["first"]), "last_price": f"{sepb[-1]['answer'] / 10 ** 8:.4f}",
                               "low": f"{min(b['answer'] for b in sepb) / 10 ** 8:.4f}", "high": f"{max(b['answer'] for b in sepb) / 10 ** 8:.4f}"}
log(f"  from August 15: {len(recent)} batches, {len(at_0230)} starting at 02:30 UTC, others {dict(other_times)}")
log(f"  price in force at most {R['price_age']['max_seconds_at_batch_first_transfer']} s old at a batch, {R['price_age']['max_seconds_on_the_hour']} s on the hour")
days_with_batch = {iso(b["first"])[:10] for b in batches if b["first"] >= ts(2026, 8, 15)}
check("from August 15 to October 9 there was one batch a day", len(days_with_batch) == 56 and all(
    sum(1 for b in batches if iso(b["first"])[:10] == d) == 1 for d in days_with_batch))

# transfers to other addresses, and what the accounts received
inc = meta["cashback_account_incoming"]
R["other_addresses"] = {"transfers": len(others), "recipients": meta["other_recipients"], "avax": f"{avax(sum(o['wei'] for o in others)):.6f}",
                        "passed_through": sum(1 for o in others if o["in_wei"] == o["wei"]),
                        "passed_through_avax": f"{avax(sum(o['wei'] for o in others if o['in_wei'] == o['wei'])):.6f}",
                        "not_passed_through_avax": f"{avax(sum(o['wei'] for o in others if o['in_wei'] != o['wei'])):.6f}",
                        "received": [{"transfers": k["transfers"], "avax": f"{avax(int(k['avax_wei'])):.6f}", "senders": k["senders"]} for k in inc]}
check("the run's count of pass-through transfers agrees with other_recipients.csv", R["other_addresses"]["passed_through"] == meta["other_recipient_passed_through"])
check("every AVAX the two accounts received by internal transfer left again in the same transaction",
      sum(int(k["avax_wei"]) for k in inc) == sum(o["in_wei"] for o in others) == sum(o["wei"] for o in others if o["in_wei"] == o["wei"]))
log(f"  to other addresses: {len(others)} transfers, {avax(sum(o['wei'] for o in others)):,.2f} AVAX, {R['other_addresses']['passed_through']} passed straight through")

# ---------------------------------------------------------------- September at the moment of credit
log()
log("September")
sep_x = [x for x in cb if S0 <= x["ts"] < S1]
sep_usd = sum(x["usd"] for x in sep_x)
sep_usd_batch = sum(usd(x["wei"], first_of[(x["payer"], x["batch"])]["answer"]) for x in sep_x)
sep_spend = Decimal(sep_card) / 100
R["september"] = {"card_spend": f"{sep_spend:.2f}", "card_payments": sum(1 for w, t, k, c in spends if k == "c" and S0 <= t < S1),
                  "spending_wallets": len({w for w, t, k, c in spends if k == "c" and S0 <= t < S1}),
                  "reversals": f"{Decimal(sep_rev) / 100:.2f}",
                  "cashback_transfers": len(sep_x), "cashback_wallets": len({x["wallet"] for x in sep_x}), "cashback_avax": f"{avax(sep_wei):.6f}",
                  "cashback_usd_at_transfer": f"{sep_usd:.2f}", "rate_pct_at_transfer": f"{sep_usd / sep_spend * 100:.4f}",
                  "cashback_usd_at_batch_first_transfer": f"{sep_usd_batch:.2f}", "rate_pct_at_batch_first_transfer": f"{sep_usd_batch / sep_spend * 100:.4f}",
                  "dashboard_usd": f"{Decimal(cashflow['sep_cashback_usd']):.2f}", "dashboard_rate_pct": f"{Decimal(cashflow['sep_cashback_rate_pct']):.4f}",
                  "average_price_usd": f"{sep_usd / avax(sep_wei):.4f}",
                  "card_payments_under_1_dollar": sum(1 for w, t, k, c in spends if k == "c" and S0 <= t < S1 and c < 100),
                  "card_spend_under_1_dollar": f"{Decimal(sum(c for w, t, k, c in spends if k == 'c' and S0 <= t < S1 and c < 100)) / 100:.2f}"}
log(f"  {money(sep_spend)} USDe of card payments, {avax(sep_wei):,.6f} AVAX of cashback worth ${sep_usd:,.2f} at Chainlink ({R['september']['rate_pct_at_transfer']}%),"
    f" dashboard ${Decimal(cashflow['sep_cashback_usd']):,.2f}")
shifted = []
for k in range(5):
    lo, hi = S0 + k * DAY, S1 + k * DAY
    v = sum(x["usd"] for x in cb if lo <= x["ts"] < hi)
    shifted.append({"days_later": k, "first_day": iso(lo)[:10], "last_day": iso(hi - 1)[:10], "usd_at_chainlink": f"{v:.2f}",
                    "rate_pct": f"{v / sep_spend * 100:.4f}", "dashboard_rate_pct": f"{Decimal(cashflow['sep_cashback_rate_shifted_pct'][str(k)]):.4f}"})
R["september_windows"] = shifted
log("  windows: " + ", ".join(f"+{s['days_later']} {s['rate_pct']}%" for s in shifted))

# ---------------------------------------------------------------- isolated card payments
log()
log("Isolated card payments")
pays, revs, credits = defaultdict(list), defaultdict(list), defaultdict(list)
for w, t, k, c in spends:
    (pays if k == "c" else revs)[w].append((t, c))
for x in cb:
    credits[x["wallet"]].append(x)
cur_batch_times = sorted(b["first"] for b in batches if b["payer"] == 0)


def isolated(alone_days, after_days, before_days, min_cents=100, max_cents=None, lo=ts(2026, 8, 21), hi=None):
    """Card payments with no other card payment by the wallet within alone_days either side, no reversal to it from
    alone_days before to after_days after, and no cashback to it in the before_days before. Each comes back with the
    cashback transfers to the wallet in the after_days after it."""
    hi = hi or ts(2026, 10, 9) - after_days * DAY
    found = []
    for w, lst in pays.items():
        for i, (t, c) in enumerate(lst):
            if not (lo <= t < hi) or c < min_cents or (max_cents is not None and c >= max_cents):
                continue
            if any(abs(t2 - t) <= alone_days * DAY for j, (t2, c2) in enumerate(lst) if j != i):
                continue
            if any(t - alone_days * DAY <= t2 <= t + after_days * DAY for t2, c2 in revs[w]):
                continue
            near = [x for x in credits[w] if t - before_days * DAY < x["ts"] <= t + after_days * DAY]
            if any(x["ts"] <= t for x in near):
                continue
            found.append({"wallet": w, "ts": t, "cents": c, "credits": near})
    return found


def summarize(found):
    one = [f for f in found if len(f["credits"]) == 1]
    ratios = sorted(f["credits"][0]["usd"] / (Decimal(f["cents"]) / 100) * 100 for f in one)
    q = statistics.quantiles([float(r) for r in ratios], n=4)
    band = lambda a, b: sum(1 for r in ratios if Decimal(a) <= r < Decimal(b))
    return {"payments": len(found), "no_cashback": sum(1 for f in found if not f["credits"]), "one_cashback": len(one),
            "more_than_one": sum(1 for f in found if len(f["credits"]) > 1),
            "median_pct": f"{statistics.median(ratios):.3f}", "quartiles_pct": [f"{q[0]:.3f}", f"{q[2]:.3f}"],
            "near_4_pct": band("3.75", "4.25"), "near_4_5_pct": band("4.25", "4.75"), "near_5_pct": band("4.75", "5.25"),
            "elsewhere": len(ratios) - band("3.75", "5.25"),
            "within_0_25_point_of_4_pct_share": f"{Decimal(band('3.75', '4.25')) / len(ratios) * 100:.1f}"}


main = isolated(3, 6, 2)
R["single_payments"] = summarize(main)
one = [f for f in main if len(f["credits"]) == 1]
waits = Counter(sum(1 for b in cur_batch_times if f["ts"] < b <= f["credits"][0]["ts"] + 600) for f in one)
lags = sorted((f["credits"][0]["ts"] - f["ts"]) / DAY for f in one)
R["single_payments"]["batches_waited"] = dict(sorted(waits.items()))
R["single_payments"]["second_or_third_batch_share_pct"] = f"{Decimal(waits[2] + waits[3]) / len(one) * 100:.1f}"
R["single_payments"]["median_days_to_cashback"] = f"{statistics.median(lags):.2f}"
R["single_payments"]["card_payments_from"] = "2026-08-21"
R["single_payments"]["card_payments_before"] = iso(ts(2026, 10, 3))[:10]
sp = R["single_payments"]
log(f"  {sp['payments']} isolated card payments of $1 or more, {sp['one_cashback']} with one cashback transfer: median {sp['median_pct']}%,"
    f" quartiles {sp['quartiles_pct']}, {sp['near_4_pct']} within a quarter point of 4%")
log(f"  batches waited {sp['batches_waited']}, median {sp['median_days_to_cashback']} days")
check("the isolated-payment test found more than 150 single matches", sp["one_cashback"] > 150)
R["single_payments_sensitivity"] = {f"quiet_{a}_days": summarize(isolated(a, 6, 2)) for a in (5, 7)}
for k, v in R["single_payments_sensitivity"].items():
    log(f"  sensitivity {k}: {v['one_cashback']} matches, median {v['median_pct']}%")
# transfers worth about $30, the referral bonus on the Pricing page, against the dollars on either side
vals = [x["usd"] for x in cb if x["usd"] is not None]
R["thirty_dollar_check"] = {f"{a}_to_{b}": sum(1 for v in vals if Decimal(a) <= v < Decimal(b)) for a, b in (("28.5", "29.5"), ("29.5", "30.5"), ("30.5", "31.5"))}
log(f"  transfers by dollar value around $30: {R['thirty_dollar_check']}")
small = isolated(3, 6, 2, min_cents=1, max_cents=100)
R["small_payments"] = {"isolated_under_1_dollar": len(small), "with_no_cashback": sum(1 for f in small if not f["credits"])}
log(f"  isolated card payments under $1: {len(small)}, {R['small_payments']['with_no_cashback']} with no cashback in six days")

# ---------------------------------------------------------------- September wallet by wallet
log()
log("September wallet by wallet")
A0, A1 = ts(2026, 9, 3), ts(2026, 10, 1, 12)   # the batches of September 3 to October 1
HEAVY_BY = ts(2026, 9, 29)                     # card payments to the end of September 28
spend_month, spend_to28, rev_month = defaultdict(int), defaultdict(int), defaultdict(int)
for w, t, k, c in spends:
    if S0 <= t < S1:
        if k == "c":
            spend_month[w] += c
            if t < HEAVY_BY:
                spend_to28[w] += c
        else:
            rev_month[w] += c
paid = defaultdict(Decimal)
for x in cb:
    if A0 <= x["ts"] < A1:
        paid[x["wallet"]] += x["usd"]
check("the September 3 to October 1 window holds 29 batches", len({b["first"] for b in batches if A0 <= b["first"] < A1}) == 29)


def near(a, b, tol=Decimal("0.05")):
    return b > 0 and abs(a / b - 1) <= tol


wallet_rows = []
for w in sorted(set(spend_month) | set(paid)):
    s28 = Decimal(spend_to28[w]) / 100
    e = {t: schedule(t, s28) for t in SCHEDULE}
    a = paid[w]
    fit = ""
    if s28 >= 4000 and near(a, STANDARD_MAX):
        fit = "standard ceiling"
    elif s28 >= 4000 and near(a, e["pro"]):
        fit = "pro"
    elif s28 >= 4000 and near(a, e["vip"]):
        fit = "vip"
    wallet_rows.append({"wallet": w, "spend_month": Decimal(spend_month[w]) / 100, "spend_to_28": s28, "reversals_month": Decimal(rev_month[w]) / 100,
                        "paid": a, "standard": e["standard"], "pro": e["pro"], "vip": e["vip"], "fit": fit})
heavy = [r for r in wallet_rows if r["spend_to_28"] >= 4000]
capped = [r for r in heavy if r["fit"] == "standard ceiling"]
R["heavy"] = {"wallets_4000_by_sep_28": len(heavy),
              "standard_ceiling_within_5pct": len(capped),
              "standard_ceiling_month_spend": f"{sum(r['spend_month'] for r in capped):.2f}",
              "standard_ceiling_spend_share_pct": f"{sum(r['spend_month'] for r in capped) / sep_spend * 100:.2f}",
              "standard_ceiling_paid": f"{sum(r['paid'] for r in capped):.2f}",
              "standard_ceiling_rate_pct": f"{sum(r['paid'] for r in capped) / sum(r['spend_month'] for r in capped) * 100:.3f}",
              "standard_ceiling_min_paid": f"{min(r['paid'] for r in capped):.2f}", "standard_ceiling_max_paid": f"{max(r['paid'] for r in capped):.2f}",
              "standard_ceiling_largest_month_spend": f"{max(r['spend_month'] for r in capped):.2f}",
              "standard_ceiling_smallest_month_spend": f"{min(r['spend_month'] for r in capped):.2f}",
              "standard_ceiling_at_4_pct": f"{sum(r['spend_month'] for r in capped) * Decimal('0.04'):.2f}",
              "pro_within_5pct": sum(1 for r in heavy if r["fit"] == "pro"), "vip_within_5pct": sum(1 for r in heavy if r["fit"] == "vip"),
              "matching_no_schedule": sum(1 for r in heavy if not r["fit"]),
              "paid_over_140": sum(1 for r in heavy if r["paid"] > 140), "paid_under_100": sum(1 for r in heavy if r["paid"] < 100),
              "largest_month_spend": f"{max(r['spend_month'] for r in heavy):.2f}"}
unmatched = [r for r in heavy if not r["fit"]]
R["heavy_unmatched"] = {
    "under_standard": sum(1 for r in unmatched if r["paid"] < STANDARD_MAX * Decimal("0.95")),
    "between_standard_and_pro": sum(1 for r in unmatched if STANDARD_MAX * Decimal("1.05") < r["paid"] < r["pro"] * Decimal("0.95")),
    "between_pro_and_vip": sum(1 for r in unmatched if r["pro"] * Decimal("1.05") < r["paid"] < r["vip"] * Decimal("0.95")),
    "over_vip": sum(1 for r in unmatched if r["paid"] > r["vip"] * Decimal("1.05"))}
check("every unmatched wallet falls in one of the four gaps between the schedules", sum(R["heavy_unmatched"].values()) == len(unmatched))
late_aug = defaultdict(int)
for w, t, k, c in spends:
    if k == "c" and ts(2026, 8, 25) <= t < S0:
        late_aug[w] += c
over_vip = [r for r in unmatched if r["paid"] > r["vip"] * Decimal("1.05")]
R["heavy_unmatched"]["over_vip_rate_range_pct"] = [f"{min(r['paid'] / r['spend_to_28'] * 100 for r in over_vip):.1f}", f"{max(r['paid'] / r['spend_to_28'] * 100 for r in over_vip):.1f}"]
R["heavy_unmatched"]["over_vip_with_card_payments_august_25_to_31"] = sum(1 for r in over_vip if late_aug[r["wallet"]] > 0)
R["heavy_unmatched"]["over_vip_paid_over_5_pct"] = sum(1 for r in over_vip if r["paid"] > r["spend_to_28"] * Decimal("0.05"))
R["heavy_unmatched"]["crossed_4000_on_september_29_or_30"] = sum(1 for r in wallet_rows if r["spend_month"] >= 4000 and r["spend_to_28"] < 4000)
R["heavy_unmatched"]["matched_any_schedule"] = sum(1 for r in heavy if r["fit"])
log(f"  unmatched {R['heavy_unmatched']}")
big = max(heavy, key=lambda r: r["spend_month"])
R["heavy"]["largest_spending_wallet"] = {"month_spend": f"{big['spend_month']:.2f}", "paid": f"{big['paid']:.2f}", "vip": f"{big['vip']:.2f}",
                                 "rate_pct": f"{big['paid'] / big['spend_month'] * 100:.2f}", "fit": big["fit"]}
h = R["heavy"]
log(f"  {h['wallets_4000_by_sep_28']} wallets reached $4,000 by September 28; {h['standard_ceiling_within_5pct']} were paid within 5% of $115"
    f" (${h['standard_ceiling_min_paid']} to ${h['standard_ceiling_max_paid']}) on ${Decimal(h['standard_ceiling_month_spend']):,.2f} of September spend;"
    f" {h['pro_within_5pct']} matched Pro and {h['vip_within_5pct']} VIP within 5%, {h['matching_no_schedule']} none")
check("every wallet paid within 5% of $115 spent at least $4,000 by September 28", all(r["spend_to_28"] >= 4000 for r in capped))
check("no wallet that reached $4,000 is within 5% of two schedules", all(sum([near(r["paid"], STANDARD_MAX), near(r["paid"], r["pro"]), near(r["paid"], r["vip"])]) <= 1 for r in heavy))

# the same wallets after the month turned
late_spend = sum(c for w, t, k, c in spends if k == "c" and ts(2026, 9, 25) <= t < S1 and w in {r["wallet"] for r in capped})
late_paid = sum(x["usd"] for x in cb if ts(2026, 9, 27) <= x["ts"] < A1 and x["wallet"] in {r["wallet"] for r in capped})
oct_spend = sum(c for w, t, k, c in spends if k == "c" and S1 <= t < ts(2026, 10, 8) and w in {r["wallet"] for r in capped})
oct_paid = sum(x["usd"] for x in cb if ts(2026, 10, 2) <= x["ts"] < ts(2026, 10, 10) and x["wallet"] in {r["wallet"] for r in capped})
capped_ids = {r["wallet"] for r in capped}
R["reset"] = {"late_september_spend": f"{Decimal(late_spend) / 100:.2f}", "late_september_paid": f"{late_paid:.2f}",
              "late_september_wallets_spending": len({w for w, t, k, c in spends if k == "c" and ts(2026, 9, 25) <= t < S1 and w in capped_ids}),
              "october_1_7_spend": f"{Decimal(oct_spend) / 100:.2f}", "october_2_9_paid": f"{oct_paid:.2f}",
              "october_wallets_spending": len({w for w, t, k, c in spends if k == "c" and S1 <= t < ts(2026, 10, 8) and w in capped_ids}),
              "october_wallets_paid": len({x["wallet"] for x in cb if ts(2026, 10, 2) <= x["ts"] < ts(2026, 10, 10) and x["wallet"] in capped_ids}),
              "late_rate_pct": f"{late_paid / (Decimal(late_spend) / 100) * 100:.2f}", "october_rate_pct": f"{oct_paid / (Decimal(oct_spend) / 100) * 100:.2f}"}
oct_card_wallets = {w for w, t, k, c in spends if k == "c" and S1 <= t < ts(2026, 10, 8) and w in capped_ids}
oct_paid_ids = {x["wallet"] for x in cb if ts(2026, 10, 2) <= x["ts"] < ts(2026, 10, 10) and x["wallet"] in capped_ids}
check("the capped wallets paid in the batches of October 2 to 9 are the ones that used the card from October 1 to 7", oct_card_wallets == oct_paid_ids,
      f"{len(oct_card_wallets)} wallets")
log(f"  the capped wallets spent ${Decimal(late_spend) / 100:,.2f} from September 25 to 30 and were paid ${late_paid:,.2f} from September 27 to October 1;"
    f" ${Decimal(oct_spend) / 100:,.2f} from October 1 to 7 and ${oct_paid:,.2f} paid October 2 to 9")

# spend groups
groups, exact_short = [], []
for name, lo, hi in (("under $2,500", 0, 2500), ("$2,500 to $4,000", 2500, 4000), ("$4,000 or more", 4000, None)):
    rs = [r for r in wallet_rows if r["spend_month"] > 0 and r["spend_month"] >= lo and (hi is None or r["spend_month"] < hi)]
    s = sum(r["spend_month"] for r in rs)
    p = sum(r["paid"] for r in rs)
    exact_short.append(s * Decimal("0.04") - p)
    groups.append({"group": name, "wallets": len(rs), "card_spend": f"{s:.2f}", "share_pct": f"{s / sep_spend * 100:.1f}", "paid": f"{p:.2f}",
                   "rate_pct": f"{p / s * 100:.2f}", "unpaid_wallets": sum(1 for r in rs if r["paid"] == 0),
                   "unpaid_spend": f"{sum(r['spend_month'] for r in rs if r['paid'] == 0):.2f}",
                   "at_4_pct": f"{s * Decimal('0.04'):.2f}", "short_of_4_pct": f"{s * Decimal('0.04') - p:.2f}",
                   "reversal_pct": f"{sum(r['reversals_month'] for r in rs) / s * 100:.2f}"})
paid_no_spend = sum(r["paid"] for r in wallet_rows if r["spend_month"] == 0)
all_paid = sum(paid.values())
short_all = sep_spend * Decimal("0.04") - all_paid
R["groups"] = groups
R["groups_total"] = {"wallets": sum(g["wallets"] for g in groups), "card_spend": f"{sep_spend:.2f}", "paid_in_window": f"{all_paid:.2f}",
                     "paid_to_wallets_without_september_spend": f"{paid_no_spend:.2f}", "rate_pct": f"{all_paid / sep_spend * 100:.3f}",
                     "at_4_pct": f"{sep_spend * Decimal('0.04'):.2f}", "short_of_4_pct": f"{short_all:.2f}",
                     "heavy_share_of_shortfall_pct": f"{exact_short[2] / short_all * 100:.1f}",
                     "capped_shortfall": f"{sum(r['spend_month'] for r in capped) * Decimal('0.04') - sum(r['paid'] for r in capped):.2f}",
                     "capped_share_of_shortfall_pct": f"{(sum(r['spend_month'] for r in capped) * Decimal('0.04') - sum(r['paid'] for r in capped)) / short_all * 100:.1f}",
                     "largest_spending_wallet_shortfall": f"{big['spend_month'] * Decimal('0.04') - big['paid']:.2f}"}
check("the groups' shortfalls from 4% add up, with the cashback paid to wallets that spent nothing in September",
      sum(exact_short) - paid_no_spend == short_all)
check("the groups hold every wallet that spent in September and all its spend",
      sum(g["wallets"] for g in groups) == R["september"]["spending_wallets"] and sum(Decimal(g["card_spend"]) for g in groups) == sep_spend)
for g in groups:
    log(f"  {g['group']}: {g['wallets']} wallets, {g['share_pct']}% of spend, paid {g['rate_pct']}%")
# the same groups with the window run one batch later, to October 2, which also takes in some cashback for card payments of October 1
paid2 = defaultdict(Decimal)
for x in cb:
    if A0 <= x["ts"] < ts(2026, 10, 2, 12):
        paid2[x["wallet"]] += x["usd"]
R["groups_window_to_october_2"] = []
for name, lo, hi in (("under $2,500", 0, 2500), ("$2,500 to $4,000", 2500, 4000), ("$4,000 or more", 4000, None)):
    rs = [r for r in wallet_rows if r["spend_month"] > 0 and r["spend_month"] >= lo and (hi is None or r["spend_month"] < hi)]
    s2 = sum(r["spend_month"] for r in rs)
    R["groups_window_to_october_2"].append({"group": name, "rate_pct": f"{sum(paid2[r['wallet']] for r in rs) / s2 * 100:.2f}"})
log("  with the window to October 2: " + ", ".join(f"{g['group']} {g['rate_pct']}%" for g in R["groups_window_to_october_2"]))
light = sorted(r["paid"] / r["spend_month"] * 100 for r in wallet_rows if 100 <= r["spend_month"] < 2500)
R["light_wallets"] = {"wallets_100_to_2500": len(light), "median_pct": f"{statistics.median(light):.2f}"}

# what the schedules would have paid on September's spend
R["schedule_totals"] = {t: {"usd": f"{sum(schedule(t, Decimal(c) / 100) for c in spend_month.values()):.2f}",
                            "rate_pct": f"{sum(schedule(t, Decimal(c) / 100) for c in spend_month.values()) / sep_spend * 100:.2f}"} for t in SCHEDULE}
R["schedule_totals"]["flat_4_pct"] = {"usd": f"{sep_spend * Decimal('0.04'):.2f}", "rate_pct": "4.00"}
bands = {"first_2500": Decimal(0), "2500_to_4000": Decimal(0), "over_4000": Decimal(0)}
for c in spend_month.values():
    s = Decimal(c) / 100
    bands["first_2500"] += min(s, 2500)
    bands["2500_to_4000"] += max(0, min(s, 4000) - 2500)
    bands["over_4000"] += max(0, s - 4000)
R["spend_by_standard_band"] = {k: {"usd": f"{v:.2f}", "share_pct": f"{v / sep_spend * 100:.1f}"} for k, v in bands.items()}
check("the bands hold all of September's spend", sum(bands.values()) == sep_spend)
log("  schedules on September's spend: " + ", ".join(f"{t} {v['rate_pct']}%" for t, v in R["schedule_totals"].items()))

# ---------------------------------------------------------------- stop if anything failed
log()
if failures:
    log(f"{len(failures)} checks failed. Nothing written.")
    (HERE / "run_log_failed.txt").write_text("\n".join(log_lines) + "\n")
    sys.exit(1)

OUT.mkdir(exist_ok=True)
with open(OUT / "months.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["month", "batches", "transfers", "avax", "wallets", "usd_at_chainlink"])
    for m in months:
        w.writerow([m["month"], m["batches"], m["transfers"], m["avax"], m["wallets"], m["usd_at_chainlink"]])
with open(OUT / "september_windows.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["days_later", "first_day", "last_day", "usd_at_chainlink", "rate_pct", "dashboard_rate_pct"])
    for s in shifted:
        w.writerow([s["days_later"], s["first_day"], s["last_day"], s["usd_at_chainlink"], s["rate_pct"], s["dashboard_rate_pct"]])
with open(OUT / "single_payments.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["wallet", "card_payment_utc", "card_payment_usde", "cashback_transfers_within_6_days", "cashback_utc", "cashback_avax", "chainlink_usd_per_avax",
                "cashback_usd", "rate_pct", "batches_waited"])
    for f in sorted(main, key=lambda f: (f["ts"], f["wallet"])):
        if len(f["credits"]) == 1:
            x = f["credits"][0]
            w.writerow([f["wallet"], iso(f["ts"]), f"{Decimal(f['cents']) / 100:.2f}", 1, iso(x["ts"]), f"{avax(x['wei']):.18f}", f"{x['answer'] / 10 ** 8:.8f}",
                        f"{x['usd']:.6f}", f"{x['usd'] / (Decimal(f['cents']) / 100) * 100:.4f}",
                        sum(1 for b in cur_batch_times if f["ts"] < b <= x["ts"] + 600)])
        else:
            w.writerow([f["wallet"], iso(f["ts"]), f"{Decimal(f['cents']) / 100:.2f}", len(f["credits"]), "", "", "", "", "", ""])
with open(OUT / "september_wallets.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["wallet", "card_spend_september", "card_spend_september_1_to_28", "reversals_september", "cashback_usd_paid_september_3_to_october_1",
                "standard_schedule_usd", "pro_schedule_usd", "vip_schedule_usd", "within_5pct_of"])
    for r in wallet_rows:
        w.writerow([r["wallet"], f"{r['spend_month']:.2f}", f"{r['spend_to_28']:.2f}", f"{r['reversals_month']:.2f}", f"{r['paid']:.6f}",
                    f"{r['standard']:.2f}", f"{r['pro']:.2f}", f"{r['vip']:.2f}", r["fit"]])
with open(OUT / "spend_groups.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["september_card_spend", "wallets", "card_spend", "share_of_spend_pct", "cashback_usd_paid_september_3_to_october_1", "rate_pct",
                "four_pct_of_spend", "short_of_four_pct", "reversals_pct_of_spend", "wallets_paid_nothing", "their_card_spend"])
    for g in groups:
        w.writerow([g["group"], g["wallets"], g["card_spend"], g["share_pct"], g["paid"], g["rate_pct"], g["at_4_pct"], g["short_of_4_pct"],
                    g["reversal_pct"], g["unpaid_wallets"], g["unpaid_spend"]])
# chart data: September spend to the 28th against cashback paid September 3 to October 1, for wallets with both
with open(OUT / "chart_points.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["wallet", "card_spend_september_1_to_28", "cashback_usd_paid_september_3_to_october_1", "within_5pct_of"])
    for r in wallet_rows:
        if r["spend_to_28"] >= 10 and r["paid"] > 0:
            w.writerow([r["wallet"], f"{r['spend_to_28']:.2f}", f"{r['paid']:.2f}", r["fit"]])
with open(OUT / "chart_lines.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["card_spend", "standard_usd", "pro_usd", "vip_usd"])
    for k in range(81):  # 16 steps a decade from $10 to $1,000,000
        x = Decimal(round(10 * 10 ** (k / 16), 2))
        w.writerow([f"{x:.2f}", f"{schedule('standard', x):.2f}", f"{schedule('pro', x):.2f}", f"{schedule('vip', x):.2f}"])
R["checks_passed"] = len([l for l in log_lines if l.startswith("ok")])
(OUT / "results.json").write_text(json.dumps(R, indent=1, default=str) + "\n")
log(f"All {R['checks_passed']} checks passed. Tables written to out/.")
(OUT / "run_log.txt").write_text("\n".join(log_lines) + "\n")
