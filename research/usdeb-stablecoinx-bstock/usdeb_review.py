#!/usr/bin/env python3
"""
USDEB supply review. Rebuilds every figure in the article from the inputs, checks them, and writes the tables in out/.

Run from this directory with Python 3 and the standard library only:  python3 usdeb_review.py

Inputs
  inputs/usdeb_flows_e7fb070.json       the dashboard's verified mint and burn history for USDEB, EthenaDAT commit e7fb070
  inputs/usdeb_flow_pending_e7fb070.json the dashboard collector's next chain checkpoint, same commit
  inputs/chain_checks.csv               independent checks made for this review against the chain, BscScan and Binance
  inputs/bscscan_holders_top.csv        BscScan's holder ranking, without addresses
  inputs/shares_out_e7fb070.csv         the dashboard's Class A share count, same commit
  inputs/data_e7fb070.json              the dashboard's dataset, same commit, for the close and Class A count the panel used
  inputs/usde_close.csv                 the USDE close used for the reference value, with its two sources
The script stops with an error if any check fails. It uses no network.
"""
import csv
import datetime as dt
import json
from decimal import Decimal as D, getcontext
from pathlib import Path

getcontext().prec = 50
HERE = Path(__file__).parent
IN, OUT = HERE / "inputs", HERE / "out"
OUT.mkdir(exist_ok=True)
WEI = D(10) ** 18
UTC = dt.timezone.utc
TOKEN = "0xdfd3ba51d4591f243481a6f26059d1a5ee95252f"
TRADING_OPEN = dt.datetime(2026, 10, 7, 12, 0, tzinfo=UTC)      # Binance announcement and admission notice of October 7, 2026 (16:00 UTC+4)
WITHDRAWALS_OPEN = dt.datetime(2026, 10, 7, 13, 0, tzinfo=UTC)  # Binance announcement
ADMITTED_AT_OPEN = 1_200_000                                      # admission notice, paragraph 4, USDEB admitted to trading at the admission time
log = []


def say(*parts):
    line = " ".join(str(p) for p in parts)
    log.append(line)
    print(line)


def check(cond, what):
    if not cond:
        raise SystemExit("CHECK FAILED: " + what)


def t_utc(ms):
    return dt.datetime.fromtimestamp(ms / 1000, UTC)


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def tok(raw):
    return D(raw) / WEI


# 1. The dashboard's verified flow file
f = json.loads((IN / "usdeb_flows_e7fb070.json").read_text())
check(f["symbol"] == "USDEB" and f["chainId"] == 56 and f["contract"] == TOKEN, "token identity in the flow file")
check(f["reconciled"] is True and f["multiplier"] == str(10 ** 18) and f["adjustments"] == [], "reconciled, multiplier 1.0, no adjustments")
ev = f["events"]
check(all(e["kind"] in ("mint", "burn") and int(e["rawAmount"]) > 0 for e in ev), "event kinds and amounts")
check([(e["block"], e["logIndex"]) for e in ev] == sorted((e["block"], e["logIndex"]) for e in ev), "events in chain order")
check(len({e["tx"] for e in ev}) == len(ev), "one event per transaction")
minted = sum(int(e["rawAmount"]) for e in ev if e["kind"] == "mint")
burned = sum(int(e["rawAmount"]) for e in ev if e["kind"] == "burn")
check(minted == int(f["rawMinted"]) and burned == int(f["rawBurned"]), "minted and burned totals")
check(minted - burned == int(f["rawSupply"]) == int(f["adjustedSupply"]), "mints less burns equal the recorded supply")
observed = dt.datetime.fromisoformat(f["observedAt"].replace("Z", "+00:00"))
coverage = dt.datetime.fromisoformat(f["coverageStart"].replace("Z", "+00:00"))
check(all(coverage <= t_utc(e["t"]) <= observed for e in ev), "every event inside the coverage window")
say("flow file", f["generatedAt"], "observed", f["observedAt"], "block", f["blockNumber"], "events", len(ev),
    "mints", sum(e["kind"] == "mint" for e in ev), "burns", sum(e["kind"] == "burn" for e in ev))
say(" minted", tok(minted), "burned", tok(burned), "supply", tok(minted - burned))

# 2. The dashboard collector's later checkpoint
p = json.loads((IN / "usdeb_flow_pending_e7fb070.json").read_text())
p_block, p_time = int(p["block"]["number"], 16), dt.datetime.fromtimestamp(int(p["block"]["timestamp"], 16), UTC)
check(int(p["values"]["rawSupply"], 16) == minted - burned and int(p["values"]["multiplier"], 16) == 10 ** 18,
      "the collector's later checkpoint shows the same supply")
say("collector checkpoint block", p_block, iso(p_time), "supply", tok(int(p["values"]["rawSupply"], 16)))

# 3. Independent checks made for this review
cc = list(csv.DictReader(open(IN / "chain_checks.csv")))
get = lambda name: [r for r in cc if r["check"] == name]
ts = get("total_supply_raw")[0]
CUTOFF_BLOCK = int(ts["block"])
CUTOFF = dt.datetime.fromisoformat(ts["observed_at_utc"].replace("Z", "+00:00"))
check(int(ts["value"]) == minted - burned, "totalSupply at the cutoff block equals the flow file's supply")
check(int(get("multiplier_raw")[0]["value"]) == 10 ** 18 and int(get("scaled_supply_raw")[0]["value"]) == minted - burned,
      "multiplier 1.0 and scaled supply at the cutoff block")
check(int(get("receipts_matched")[0]["value"]) == len(ev), "every event matched a chain receipt")
check(int(get("bscscan_zero_address_transfers")[0]["value"]) == len(ev), "BscScan lists the same number of mints and burns")
check(p_block < CUTOFF_BLOCK and p_time < CUTOFF and observed < CUTOFF, "cutoff after both dashboard observations")
creation = [r for r in get("block_time") if r["block"] == "124478553"][0]
check(creation["value"] == "2026-09-28T06:41:41Z" and f["coverageStart"] == "2026-09-28T06:41:41Z", "deployment time")
say("cutoff block", CUTOFF_BLOCK, iso(CUTOFF), "totalSupply", tok(int(ts["value"])), "receipts", get("receipts_matched")[0]["value"],
    "BscScan list", get("bscscan_zero_address_transfers")[0]["value"])

# 4. Running supply, milestones and periods
rows, s = [], 0
for e in ev:
    a = int(e["rawAmount"])
    s += a if e["kind"] == "mint" else -a
    rows.append({"t": t_utc(e["t"]), "block": e["block"], "log_index": e["logIndex"], "kind": e["kind"], "raw": a, "after": s, "tx": e["tx"]})
check(rows[-1]["after"] == minted - burned, "running supply ends at the recorded supply")
first = rows[0]
check(first["kind"] == "mint" and first["t"] < TRADING_OPEN, "first event is a mint before trading opened")
pre = [r for r in rows if r["t"] < TRADING_OPEN]
peak = max(rows, key=lambda r: r["after"])
burn = [r for r in rows if r["kind"] == "burn"]
check(len(burn) == 1, "exactly one burn")
burn = burn[0]
check(peak["t"] < burn["t"], "the peak came before the burn")
after_burn = burn["after"]
say("first mint", iso(first["t"]), tok(first["raw"]), "| mints before trading", len(pre), tok(pre[-1]["after"]),
    "| last before trading", iso(pre[-1]["t"]))
say("peak", tok(peak["after"]), "at", iso(peak["t"]), "| burn", tok(burn["raw"]), "at", iso(burn["t"]), "block", burn["block"],
    "| supply after burn", tok(after_burn))

periods = [
    ("Before trading opened, October 7 to 12:00 UTC", coverage, TRADING_OPEN),
    ("October 7 from 12:00 UTC", TRADING_OPEN, dt.datetime(2026, 10, 8, tzinfo=UTC)),
    (f"October 8 to {CUTOFF:%H:%M} UTC", dt.datetime(2026, 10, 8, tzinfo=UTC), CUTOFF + dt.timedelta(seconds=1)),
]
period_rows = []
for name, a0, a1 in periods:
    sel = [r for r in rows if a0 <= r["t"] < a1]
    m = [r for r in sel if r["kind"] == "mint"]
    b = [r for r in sel if r["kind"] == "burn"]
    end_supply = [r["after"] for r in rows if r["t"] < a1][-1]
    period_rows.append({"period": name, "mints": len(m), "minted": tok(sum(r["raw"] for r in m)), "burns": len(b),
                        "burned": tok(sum(r["raw"] for r in b)), "net": tok(sum(r["raw"] for r in m) - sum(r["raw"] for r in b)),
                        "supply_at_end": tok(end_supply)})
check(sum(r["mints"] for r in period_rows) + sum(r["burns"] for r in period_rows) == len(rows), "periods cover every event")
for r in period_rows:
    say(" period", r["period"], "| mints", r["mints"], r["minted"], "| burns", r["burns"], r["burned"], "| net", r["net"], "| end", r["supply_at_end"])

# minutes: how far past a five-minute mark each event landed
offsets = [(r["t"].minute % 5) * 60 + r["t"].second for r in rows]
mint_off = [o for o, r in zip(offsets, rows) if r["kind"] == "mint"]
say("seconds past a five-minute mark, mints: min", min(mint_off), "max", max(mint_off), "| burn", offsets[rows.index(burn)])
at_open = pre[-1]["after"]
open_share = tok(at_open) / ADMITTED_AT_OPEN * 100
say("supply at the open", tok(at_open), "of", f"{ADMITTED_AT_OPEN:,}", "admitted to trading =", f"{open_share:.4f}%")

# 5. Scale
shares = list(csv.DictReader(open(IN / "shares_out_e7fb070.csv")))
CLASS_A = int(D([r for r in shares if r["date"] <= CUTOFF.date().isoformat()][-1]["shares_outstanding"]))
check(CLASS_A == 24139375, "the dashboard's Class A count")
supply = tok(minted - burned)
share_pct = supply / CLASS_A * 100
close = [r for r in csv.DictReader(open(IN / "usde_close.csv")) if r["date"] == CUTOFF.date().isoformat()]
check(len(close) == 1, "a USDE close for the cutoff day")
close = close[0]
data = json.loads((IN / "data_e7fb070.json").read_text())
ser = data["series"]
i = ser["date"].index(CUTOFF.date().isoformat())
check(i == len(ser["date"]) - 1, "the cutoff day is the dataset's latest row, the one the panel uses")
check(D(str(ser["usde_close"][i])) == D(close["close"]), "the dashboard dataset records the same close")
check(int(ser["shares_outstanding"][i]) == CLASS_A, "the dashboard dataset uses the same Class A count")
check(data["usde"]["market_state"] == "POST" and data["generated_at"] < iso(CUTOFF).replace("Z", "+00:00"),
      "the dataset was generated after the Nasdaq close and before the cutoff")
value = supply * D(close["close"])
say("supply", supply, "Class A", f"{CLASS_A:,}", "share", f"{share_pct:.4f}%", "| value at", close["date"], "close", close["close"], "=", f"{value:,.2f}")

# 6. Where the tokens sat, from BscScan
h = list(csv.DictReader(open(IN / "bscscan_holders_top.csv")))
top = [r for r in h if r["rank"] in ("1", "2", "3", "4")]
check(sum(D(r["quantity"]) for r in top) <= supply, "the top holders hold no more than the supply")
check(all(abs(D(r["quantity"]) / supply * 100 - D(r["percentage"])) < D("0.001") for r in top),
      "BscScan's shares recompute on the same supply")
top2 = D(top[0]["percentage"]) + D(top[1]["percentage"])
say("BscScan holders 44 | rank 1", top[0]["bscscan_tag"], top[0]["percentage"], "% | rank 2", top[1]["percentage"], "% | top two", top2, "%")

# 7. Outputs
with open(OUT / "usdeb_supply_events.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["utc_time", "block", "log_index", "kind", "usdeb", "supply_after", "tx_hash"])
    for r in rows:
        w.writerow([iso(r["t"]), r["block"], r["log_index"], r["kind"], tok(r["raw"]), tok(r["after"]), r["tx"]])
with open(OUT / "usdeb_supply_by_period.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(period_rows[0].keys()))
    w.writeheader()
    w.writerows(period_rows)
with open(OUT / "chart_usdeb_supply.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["utc_time", "supply_after", "kind", "usdeb"])
    for r in rows:
        w.writerow([iso(r["t"]), tok(r["after"]), r["kind"], tok(r["raw"])])
    w.writerow([iso(CUTOFF), tok(rows[-1]["after"]), "cutoff", "0"])
results = {
    "cutoff_block": CUTOFF_BLOCK, "cutoff_utc": iso(CUTOFF), "supply": str(supply), "minted": str(tok(minted)), "burned": str(tok(burned)),
    "events": len(rows), "mints": sum(r["kind"] == "mint" for r in rows), "burns": 1,
    "first_mint_utc": iso(first["t"]), "first_mint": str(tok(first["raw"])), "minted_before_trading": str(tok(pre[-1]["after"])),
    "mints_before_trading": len(pre), "peak": str(tok(peak["after"])), "peak_utc": iso(peak["t"]),
    "burn": str(tok(burn["raw"])), "burn_utc": iso(burn["t"]), "burn_block": burn["block"], "supply_after_burn": str(tok(after_burn)),
    "class_a_shares": CLASS_A, "share_of_class_a_pct": str(share_pct), "usde_close_date": close["date"], "usde_close": close["close"],
    "value_at_close": str(value), "periods": [{k: str(v) for k, v in r.items()} for r in period_rows],
    "min_seconds_past_five_minute_mark_mints": min(mint_off), "max_seconds_past_five_minute_mark_mints": max(mint_off),
    "admitted_at_open": ADMITTED_AT_OPEN, "supply_at_open": str(tok(at_open)), "supply_at_open_pct_of_admitted": str(open_share),
    "deployment_utc": f["coverageStart"],
    "bscscan_holders": 44, "bscscan_rank1_pct": top[0]["percentage"], "bscscan_rank2_pct": top[1]["percentage"],
}
(OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
say("All checks passed.")
(OUT / "run_log.txt").write_text("\n".join(log) + "\n")
