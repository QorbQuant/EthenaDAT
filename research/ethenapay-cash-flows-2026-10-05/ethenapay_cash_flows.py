#!/usr/bin/env python3
"""
EthenaPay cash-flow review. Rebuilds every figure in the article from the pinned inputs, checks them, and writes
the tables in out/.

Run from this directory with Python 3 and the standard library only:  python3 ethenapay_cash_flows.py

Inputs
  inputs/daily_chain_62503a1.csv        one row per UTC day of USDe flows and end-of-day balances for EthenaPay wallets,
                                        from the chain recount published with the adoption review (EthenaDAT 62503a1)
  inputs/chain_meta_62503a1.json        that recount's counts, the AllowanceSpent and settlement-transfer totals and
                                        its balanceOf check of every wallet
  inputs/ethenapay_5faf41f.json         the dashboard's EthenaPay dataset from its Dune query (EthenaDAT 5faf41f)
  inputs/chain_checks.csv               checks made for this review against Routescan on October 9, 2026 UTC
  inputs/manifest.csv                   repository, path, commit, size and SHA-256 of the pinned inputs
The script stops with an error if any check fails. It uses no network.
"""
import csv
import datetime as dt
import hashlib
import json
from collections import defaultdict
from decimal import Decimal as D, getcontext
from pathlib import Path

getcontext().prec = 50
HERE = Path(__file__).parent
IN, OUT = HERE / "inputs", HERE / "out"
OUT.mkdir(exist_ok=True)
E18 = 10 ** 18
LAUNCH = "2026-09-01"          # the day Ethena opened the app's beta, in its launch thread at 11:59 UTC
CUTOFF_DAY = "2026-10-05"      # last full UTC day in the chain recount, block 96,839,679
WORKED_DAY = "2026-10-05"
log = []


def say(*parts):
    line = " ".join(str(p) for p in parts)
    log.append(line)
    print(line)


def check(cond, what):
    if not cond:
        raise SystemExit("CHECK FAILED: " + what)


def usde(wei):
    return D(wei) / E18


# 1. Pinned inputs
for r in csv.DictReader(open(IN / "manifest.csv")):
    b = (IN / r["saved_as"]).read_bytes()
    check(len(b) == int(r["bytes"]) and hashlib.sha256(b).hexdigest() == r["sha256"], "manifest hash for " + r["saved_as"])
say("manifest: all pinned inputs match their recorded size and SHA-256")

FLOWS = ["deposits_wei", "withdrawals_wei", "card_spend_wei", "reversals_wei", "yield_wei", "other_rewards_wei"]
rows = list(csv.DictReader(open(IN / "daily_chain_62503a1.csv")))
check(rows[0]["date"] == "2026-05-15" and rows[-1]["date"] == CUTOFF_DAY, "chain rows run from May 15 to the cutoff day")
dates = [r["date"] for r in rows]
check(dates == sorted(dates) and len(dates) == len(set(dates)) == 144, "144 consecutive days")
meta = json.loads((IN / "chain_meta_62503a1.json").read_text())
check(meta["end_block"] == 96839679, "recount end block")

# 2. The bridge closes exactly on every day of the chain recount
prev_held = 0
for r in rows:
    net = (int(r["deposits_wei"]) - int(r["withdrawals_wei"]) - int(r["card_spend_wei"]) + int(r["reversals_wei"])
           + int(r["yield_wei"]) + int(r["other_rewards_wei"]))
    check(int(r["held_wei"]) - prev_held == net, "daily bridge on " + r["date"])
    check(int(r["negative_balances"]) == 0, "no negative balance on " + r["date"])
    prev_held = int(r["held_wei"])
say("chain recount: on all 144 days the change in USDe held equals deposits - withdrawals - card spend + reversals + rewards, to the wei")

# 3. Card spend by event against USDe sent to settlement
diff_days = [(r["date"], int(r["card_spend_wei"]) - int(r["spend_cents"]) * 10 ** 16) for r in rows
             if int(r["card_spend_wei"]) != int(r["spend_cents"]) * 10 ** 16]
check(diff_days == [("2026-09-24", 5 * E18)], "the only day where settlement transfers exceed AllowanceSpent is Sep 24, by 5 USDe")
check(meta["wallet_to_settlement_transfers"] - meta["spend_events"] == 1
      and int(meta["wallet_to_settlement_wei"]) - int(meta["spend_wei"]) == 5 * E18, "recount totals show one extra 5 USDe transfer")
check(meta["balance_check"]["mismatch_count"] == 0 and meta["balance_check"]["wallets_checked"] == 14047, "balanceOf check of every wallet")
cc = {r["check"]: r for r in csv.DictReader(open(IN / "chain_checks.csv"))}
check(cc["five_usde_transfer"]["value"].startswith("5 USDe, block 96036325, 2026-09-24"), "fresh check found the 5 USDe transfer")
say("card spend: AllowanceSpent", f"{usde(int(meta['spend_wei'])):,.2f}", "USDe in", meta["spend_events"], "events; USDe sent to settlement",
    f"{usde(int(meta['wallet_to_settlement_wei'])):,.2f}", "in", meta["wallet_to_settlement_transfers"], "transfers; the gap is one 5 USDe transfer on 2026-09-24")

# 4. The dashboard's Dune series against the recount, day by day
dash = json.loads((IN / "ethenapay_5faf41f.json").read_text())
s = dash["series"]
chain = {r["date"]: r for r in rows}
pairs = [("deposits_usde", "deposits_wei"), ("withdrawals_usde", "withdrawals_wei"), ("reversals_usde", "reversals_wei"),
         ("yield_usde", "yield_wei"), ("other_rewards_usde", "other_rewards_wei"), ("tvl_usde", "held_wei")]
TOL = D("0.000001")
compared, worst = 0, D(0)
for i, day in enumerate(s["date"]):
    if day > CUTOFF_DAY:
        continue
    r = chain[day]
    for dk, ck in pairs:
        gap = abs(D(str(s[dk][i])) - usde(int(r[ck])))
        worst = max(worst, gap)
        check(gap <= TOL, f"dashboard {dk} on {day}")
    gap = abs(D(str(s["spend_usde"][i])) - D(int(r["spend_cents"])) / 100)
    worst = max(worst, gap)
    check(gap <= TOL, f"dashboard spend_usde on {day}")
    check(int(s["spend_count"][i]) == int(r["spend_events"]), f"dashboard spend_count on {day}")
    compared += 1
absent = [d for d in dates if d not in set(s["date"])]
check(absent == ["2026-05-30"] and all(int(chain["2026-05-30"][k]) == 0 for k in FLOWS + ["spend_events"]), "the one absent day had no flows")
check(compared == 143, "143 days compared")
say("dashboard vs recount: 143 of 144 days compared in 7 categories and spend counts, largest gap", f"{worst:.2E}", "USDe;",
    "2026-05-30 is absent from the dashboard series and had no flows")

# 5. Lifetime and period bridges
def totals(sel):
    t = {k: sum(int(r[k]) for r in sel) for k in FLOWS + ["internal_wei"]}
    t["spend_events"] = sum(int(r["spend_events"]) for r in sel)
    t["spend_cents"] = sum(int(r["spend_cents"]) for r in sel)
    return t


life = totals(rows)
before_beta = totals([r for r in rows if r["date"] < LAUNCH])
since_beta = totals([r for r in rows if r["date"] >= LAUNCH])
held_end = int(chain[CUTOFF_DAY]["held_wei"])
held_aug_31_wei = int(chain["2026-08-31"]["held_wei"])
check(held_end == (life["deposits_wei"] - life["withdrawals_wei"] - life["card_spend_wei"] + life["reversals_wei"]
                   + life["yield_wei"] + life["other_rewards_wei"]), "lifetime bridge")
dep = life["deposits_wei"]
share = lambda x: D(x) / dep * 100
rewards = life["yield_wei"] + life["other_rewards_wei"]
reversal_rate = D(life["reversals_wei"]) / D(life["card_spend_wei"]) * 100                  # card spend by transfer, as in the article
reversal_rate_events = D(life["reversals_wei"]) / (D(life["spend_cents"]) * 10 ** 16) * 100   # the dashboard's denominator, spend events
say("lifetime to", CUTOFF_DAY, "| deposits", f"{usde(dep):,.2f}", "| withdrawals", f"{usde(life['withdrawals_wei']):,.2f}",
    f"({share(life['withdrawals_wei']):.2f}%)", "| card spend", f"{usde(life['card_spend_wei']):,.2f}", f"({share(life['card_spend_wei']):.2f}%)",
    "| reversals", f"{usde(life['reversals_wei']):,.2f}", "| yield", f"{usde(life['yield_wei']):,.2f}", "| other rewards",
    f"{usde(life['other_rewards_wei']):,.2f}", "| held", f"{usde(held_end):,.2f}", f"({share(held_end):.2f}%)")
say(" internal transfers between programme wallets", f"{usde(life['internal_wei']):,.2f}", "| reversals", f"{reversal_rate:.2f}% of card spend",
    "| share of deposits before the beta", f"{D(before_beta['deposits_wei']) / dep * 100:.2f}%", "| held at Aug 31", f"{usde(held_aug_31_wei):,.2f}")

# 6. September rates
sep = [r for r in rows if r["date"].startswith("2026-09")]
check(len(sep) == 30, "30 September days")
sep_t = totals(sep)
pay_days = [r for r in rows if "2026-09-02" <= r["date"] <= "2026-10-01"]       # paid within a day of the accrual day
check(len(pay_days) == 30, "30 payment days")
pay_t = totals(pay_days)
avg_bal = sum(D(int(r["held_wei"])) for r in sep) / 30 / E18                    # end-of-day balances, Sep 1 to Sep 30
reward_rate = usde(pay_t["yield_wei"] + pay_t["other_rewards_wei"]) / avg_bal * 365 / 30 * 100
sep_reversal = D(sep_t["reversals_wei"]) / D(sep_t["card_spend_wei"]) * 100
sep_reversal_events = D(sep_t["reversals_wei"]) / (D(sep_t["spend_cents"]) * 10 ** 16) * 100
trunc6 = lambda wei: str(usde(wei).quantize(D("0.000001"), rounding="ROUND_DOWN"))   # the fresh read truncated to six decimals
check(trunc6(sep_t["yield_wei"]) == "11178.042656" and trunc6(sep_t["other_rewards_wei"]) == "1407.990942",
      "September rewards equal the fresh read of the payer Safes")
check("11,178.042656" in cc["sep_yield_payer_out"]["value"] and "1,407.990942" in cc["sep_other_reward_payer_out"]["value"],
      "chain_checks record the same September rewards")
check(f"{reversal_rate:.2f}" == f"{reversal_rate_events:.2f}" and f"{sep_reversal:.2f}" == f"{sep_reversal_events:.2f}",
      "spend events give the same rounded reversal rates")
say("September | rewards paid Sep 2 to Oct 1", f"{usde(pay_t['yield_wei'] + pay_t['other_rewards_wei']):,.2f}", "| average end-of-day balance Sep 1 to 30",
    f"{avg_bal:,.2f}", "| annualized", f"{reward_rate:.3f}%", "| reversals", f"{sep_reversal:.2f}% of card spend")
annual = lambda wei: usde(wei) / avg_bal * 365 / 30 * 100
rate_variants = {                                                               # the same September balance, four ways of counting the payments
    "both payers, paid Sep 2 to Oct 1": annual(pay_t["yield_wei"] + pay_t["other_rewards_wei"]),
    "both payers, paid Sep 1 to Sep 30": annual(sep_t["yield_wei"] + sep_t["other_rewards_wei"]),
    "yield payer only, paid Sep 2 to Oct 1": annual(pay_t["yield_wei"]),
    "yield payer only, paid Sep 1 to Sep 30": annual(sep_t["yield_wei"]),
}
check(rate_variants["both payers, paid Sep 2 to Oct 1"] == reward_rate, "rate variants share one formula")
no_yield_days = [r["date"] for r in sep if int(r["yield_wei"]) == 0]
check(no_yield_days == ["2026-09-14", "2026-09-15", "2026-09-16"], "the yield payer paid nothing on September 14 to 16 only")
say(" variants |", " | ".join(f"{k} {v:.2f}%" for k, v in rate_variants.items()), "| no yield paid on", ", ".join(no_yield_days),
    "| paid Sep 17", f"{usde(int(chain['2026-09-17']['yield_wei'])):,.2f}")

pilot_paid = sum(int(r["other_rewards_wei"]) for r in rows if r["date"] < "2026-07-15")   # the other account first paid on July 15
check(f"{usde(pilot_paid)} USDe" in cc["pilot_reward_payer_out"]["value"],
      "other rewards before July 15 equal the pilot account's whole outflow, so all of it reached wallets")

# 7. Cashback in AVAX, from the dashboard, with September checked against the cashback Safe
idx = [i for i, d in enumerate(s["date"]) if d <= CUTOFF_DAY]
sep_i = [i for i, d in enumerate(s["date"]) if d.startswith("2026-09")]
cb_avax = sum(D(str(s["cashback_avax"][i])) for i in idx)
cb_usd = sum(D(str(s["cashback_usd"][i])) for i in idx)
sep_cb_avax = sum(D(str(s["cashback_avax"][i])) for i in sep_i)
sep_cb_usd = sum(D(str(s["cashback_usd"][i])) for i in sep_i)
sep_cb_calls = sum(int(s["cashback_wallets"][i]) for i in sep_i)
check(abs(sep_cb_avax - D("4595.286078")) < D("0.000001") and "4,972 calls" in cc["sep_cashback_safe_calls"]["value"] and sep_cb_calls == 4972,
      "September cashback equals the fresh read of the cashback Safe")
sep_spend = usde(sep_t["card_spend_wei"])                                       # card spend by transfer, Sep 1 to 30
sep_spend_events = D(sep_t["spend_cents"]) / 100
check(sep_spend - sep_spend_events == 5, "September card spend by transfer exceeds spend events by the 5 USDe of September 24")
cb_rate = sep_cb_usd / sep_spend * 100
cb_rate_events = sep_cb_usd / sep_spend_events * 100
check(f"{cb_rate:.2f}" == f"{cb_rate_events:.2f}", "spend events give the same rounded cashback rate")
say("cashback to", CUTOFF_DAY, f"{cb_avax:,.2f} AVAX", f"${cb_usd:,.2f}", "| September", f"{sep_cb_avax:,.6f} AVAX", f"${sep_cb_usd:,.2f}",
    "on", f"{sep_spend:,.2f}", "USDe of card spend =", f"{cb_rate:.2f}%")
pos = {d: i for i, d in enumerate(s["date"])}
cb_shift = {}                                   # cashback paid k days later than the spend window, over September's card spend
for k in range(5):
    days = [(dt.date(2026, 9, 1) + dt.timedelta(days=k + j)).isoformat() for j in range(30)]
    check(all(d in pos for d in days), "cashback window present in the dashboard series")
    paid = sum(D(str(s["cashback_usd"][pos[d]])) for d in days)
    cb_shift[k] = paid / sep_spend * 100
    check(f"{cb_shift[k]:.2f}" == f"{paid / sep_spend_events * 100:.2f}", "spend events give the same rounded cashback rate")
check(cb_shift[0] == cb_rate, "the unshifted window is September itself")
say(" cashback shifted later by 0 to 4 days |", " | ".join(f"{k} {v:.2f}%" for k, v in cb_shift.items()))

# 8. When the card takes the USDe, by weekday since the beta opened
since = [r for r in rows if r["date"] >= LAUNCH]
check(len(since) == 35, "35 days since the beta opened, five of each weekday")
wk = defaultdict(lambda: [0, 0, 0])
for r in since:
    w = dt.date.fromisoformat(r["date"]).weekday()
    wk[w][0] += 1
    wk[w][1] += int(r["spend_events"])
    wk[w][2] += int(r["spend_cents"])
check(all(wk[w][0] == 5 for w in range(7)), "five of each weekday")
names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekend_ev = D(wk[5][1] + wk[6][1]) / 10
weekday_ev = D(sum(wk[w][1] for w in range(5))) / 25
weekend_usd = D(wk[5][2] + wk[6][2]) / 10 / 100
weekday_usd = D(sum(wk[w][2] for w in range(5))) / 25 / 100
say("spend since the beta opened | weekend average", f"{weekend_ev:.1f}", "events and", f"{weekend_usd:,.0f}", "USDe a day | weekday average",
    f"{weekday_ev:.1f}", "events and", f"{weekday_usd:,.0f}", "USDe a day")
# Spend events grew about sixfold over these 35 days, so weekday averages mix growth with timing. Compare each weekend with
# the Friday before and the Monday after it, which brackets it in time, and find the busiest day of each week from Sep 1.
sats = [dt.date(2026, 9, 5) + dt.timedelta(weeks=n) for n in range(5)]
day = lambda d: chain[d.isoformat()]
we_days = [d + dt.timedelta(k) for d in sats for k in (0, 1)]
adj_days = [d + dt.timedelta(k) for d in sats for k in (-1, 2)]
check(all(d.weekday() in (5, 6) for d in we_days) and all(d.weekday() in (4, 0) for d in adj_days)
      and max(adj_days).isoformat() <= CUTOFF_DAY, "five weekends with their Fridays and Mondays")
we_avg_ev = D(sum(int(day(d)["spend_events"]) for d in we_days)) / 10
adj_avg_ev = D(sum(int(day(d)["spend_events"]) for d in adj_days)) / 10
we_avg_usde = sum(usde(int(day(d)["card_spend_wei"])) for d in we_days) / 10
adj_avg_usde = sum(usde(int(day(d)["card_spend_wei"])) for d in adj_days) / 10
busiest = []
for n in range(5):
    week = [dt.date(2026, 9, 1) + dt.timedelta(days=7 * n + k) for k in range(7)]
    busiest.append(max(week, key=lambda d: int(day(d)["spend_events"])).strftime("%A"))
check(busiest == ["Saturday"] * 5, "Saturday had the most spend events in each week from September 1")
growth = D(int(day(dt.date(2026, 10, 5))["spend_events"])) / int(day(dt.date(2026, 9, 1))["spend_events"])
say(" weekends against the Fridays and Mondays around them | events", f"{we_avg_ev:.1f}", "against", f"{adj_avg_ev:.1f}", "| card spend",
    f"{we_avg_usde:,.0f}", "against", f"{adj_avg_usde:,.0f}", "USDe a day | busiest day of each week from Sep 1", ", ".join(busiest),
    "| spend events Oct 5 over Sep 1", f"{growth:.1f}")

# 8b. How lumpy the flows were, and allowance payments the spend rule leaves in withdrawals
by_w = sorted(((int(r["withdrawals_wei"]), r["date"]) for r in rows), reverse=True)
top3_w = by_w[:3]
check([d for _, d in top3_w] == ["2026-09-16", "2026-09-22", "2026-09-15"], "the three largest withdrawal days")
top3_w_share = D(sum(w for w, _ in top3_w)) / life["withdrawals_wei"] * 100
by_d = sorted(((int(r["deposits_wei"]), r["date"]) for r in rows), reverse=True)
check([d for _, d in by_d[:2]] == ["2026-09-02", "2026-09-04"], "the two largest deposit days")
top2_d_share = D(sum(x for x, _ in by_d[:2])) / dep * 100
other_dest = [x for x in meta["other_destinations"]["destinations"] if not x["destination_is_programme_wallet"]]
check(len(other_dest) == 2 and sum(x["events_from_programme_wallets"] for x in other_dest) == 102, "two outside destinations, 102 events")
other_dest_usde = sum(D(x["usde_from_programme_wallets"]) for x in other_dest)
other_dest_pct_spend = other_dest_usde / usde(life["card_spend_wei"]) * 100
say("lumpiness | three largest withdrawal days", ", ".join(d for _, d in top3_w), f"{top3_w_share:.1f}% of withdrawals",
    "| two largest deposit days", f"{top2_d_share:.1f}% of deposits | allowance payments to two outside addresses", f"{other_dest_usde:,.2f}",
    f"USDe, {other_dest_pct_spend:.2f}% of card spend, counted as withdrawals")

# 8c. The dashboard's tiles and rates, recomputed from its own dataset
H = dash["headline"]
win = slice(-31, -1)                                                            # fetch_ethenapay.py at e9d94d8, the last 30 complete days
w_dates = s["date"][win]
check((w_dates[0], w_dates[-1], len(w_dates)) == ("2026-09-08", "2026-10-07", 30), "dashboard rate window")
w_spend = sum(v or 0 for v in s["spend_usde"][win])
w_cb = sum(v or 0 for v in s["cashback_usd"][win])
w_y = sum(v or 0 for v in s["yield_usde"][win])
w_o = sum(v or 0 for v in s["other_rewards_usde"][win])
w_h = [v for v in s["tvl_usde"][win] if v is not None]
avg_h = sum(w_h) / len(w_h)
check(abs(w_cb / w_spend - H["cashback_rate_30d"]) < 1e-12 and abs(w_y / avg_h * 365 / 30 - H["yield_apy_30d"]) < 1e-12
      and abs(H["lifetime_reversals_usde"] / H["lifetime_spend_usde"] - H["refund_rate"]) < 1e-12, "the dashboard's three rates recompute")
dash_yield_apy = D(str(H["yield_apy_30d"])) * 100
dash_both_apy = D(str((w_y + w_o) / avg_h * 365 / 30)) * 100
tiles_gap = held_end - (life["deposits_wei"] - life["withdrawals_wei"] - int(meta["spend_wei"]) + life["reversals_wei"] + life["yield_wei"])
check(tiles_gap == life["other_rewards_wei"] - 5 * E18, "tiles leave out other rewards, and card spend counts events")
say("dashboard | yield APY tile", f"{dash_yield_apy:.2f}%", "over", w_dates[0], "to", w_dates[-1], "| with the other payer", f"{dash_both_apy:.2f}%",
    "| cashback tile", f"{D(str(H['cashback_rate_30d'])) * 100:.2f}%", "| tiles to the balance gap", f"{usde(tiles_gap):,.2f}",
    "USDe = other rewards less 5")

# 9. One day worked through
wd = chain[WORKED_DAY]
opening = int(chain[(dt.date.fromisoformat(WORKED_DAY) - dt.timedelta(days=1)).isoformat()]["held_wei"])
closing = int(wd["held_wei"])
check(closing == opening + int(wd["deposits_wei"]) - int(wd["withdrawals_wei"]) - int(wd["card_spend_wei"]) + int(wd["reversals_wei"])
      + int(wd["yield_wei"]) + int(wd["other_rewards_wei"]), "worked day bridge")
check(int(wd["card_spend_wei"]) == int(wd["spend_cents"]) * 10 ** 16, "worked day has no transfer without an event")
wi = pos[WORKED_DAY]
wd_cb = (D(str(s["cashback_avax"][wi])), D(str(s["cashback_usd"][wi])), int(s["cashback_wallets"][wi]))
say("worked day", WORKED_DAY, "| opening", f"{usde(opening):,.2f}", "| closing", f"{usde(closing):,.2f}", "| spend events", wd["spend_events"],
    "from", wd["spending_wallets"], "wallets | depositing wallets", wd["depositing_wallets"], "| funded wallets", wd["funded"],
    "| cashback", f"{wd_cb[0]:,.4f} AVAX", f"${wd_cb[1]:,.2f}", "to", wd_cb[2], "wallets")

# 10. Outputs
def row_out(label, wei):
    return [label, f"{usde(wei):.18f}".rstrip("0").rstrip("."), f"{usde(wei):.2f}"]


with open(OUT / "bridge_lifetime.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["line", "usde_exact", "usde_2dp", "share_of_deposits_pct"])
    for label, k, sign in (("deposits", "deposits_wei", 1), ("withdrawals", "withdrawals_wei", -1), ("card spend", "card_spend_wei", -1),
                           ("reversals", "reversals_wei", 1), ("yield", "yield_wei", 1), ("other rewards", "other_rewards_wei", 1)):
        w.writerow(row_out(label, sign * life[k]) + [f"{share(life[k]):.4f}"])
    w.writerow(row_out("held at the end of 2026-10-05", held_end) + [f"{share(held_end):.4f}"])
    w.writerow(row_out("internal transfers, not counted", life["internal_wei"]) + [""])
with open(OUT / "bridge_by_period.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["period", "opening_held", "deposits", "withdrawals", "card_spend", "reversals", "yield", "other_rewards", "usde_rewards", "closing_held",
                "spend_events"])
    for name, t, o, c in (("2026-05-15 to 2026-08-31", before_beta, 0, held_aug_31_wei), ("2026-09-01 to 2026-10-05", since_beta, held_aug_31_wei, held_end),
                          ("2026-05-15 to 2026-10-05", life, 0, held_end)):
        check(c == o + t["deposits_wei"] - t["withdrawals_wei"] - t["card_spend_wei"] + t["reversals_wei"] + t["yield_wei"] + t["other_rewards_wei"],
              "period bridge " + name)
        w.writerow([name] + [f"{usde(x):.2f}" for x in (o, t["deposits_wei"], t["withdrawals_wei"], t["card_spend_wei"], t["reversals_wei"],
                                                          t["yield_wei"], t["other_rewards_wei"], t["yield_wei"] + t["other_rewards_wei"], c)]
                  + [t["spend_events"]])
with open(OUT / "worked_day_2026-10-05.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["line", "usde"])
    for label, v in (("held at the end of 2026-10-04", opening), ("+ deposits", int(wd["deposits_wei"])), ("- withdrawals", int(wd["withdrawals_wei"])),
                     ("- card spend", int(wd["card_spend_wei"])), ("+ reversals", int(wd["reversals_wei"])), ("+ yield", int(wd["yield_wei"])),
                     ("+ other rewards", int(wd["other_rewards_wei"])), ("= held at the end of 2026-10-05", closing),
                     ("internal transfers, not counted", int(wd["internal_wei"]))):
        w.writerow([label, f"{usde(v):.2f}"])
with open(OUT / "daily_flows.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["date", "deposits", "withdrawals", "card_spend", "reversals", "yield", "other_rewards", "internal", "held_end_of_day",
                "spend_events", "in_dashboard_series"])
    present = set(s["date"])
    for r in rows:
        w.writerow([r["date"]] + [f"{usde(int(r[k])):.6f}" for k in FLOWS + ["internal_wei", "held_wei"]] + [r["spend_events"], r["date"] in present])
with open(OUT / "weekday_spend.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["weekday", "days", "spend_events", "avg_events_per_day", "spend_event_usde", "avg_spend_event_usde_per_day"])
    for i in range(7):
        n, e, c = wk[i]
        w.writerow([names[i], n, e, f"{D(e) / n:.1f}", f"{D(c) / 100:.2f}", f"{D(c) / 100 / n:.2f}"])
with open(OUT / "september_rates.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["measure", "paid", "base", "rate_pct"])
    for k, v in rate_variants.items():
        paid = (pay_t if "Oct 1" in k else sep_t)
        paid_wei = paid["yield_wei"] + (0 if "only" in k else paid["other_rewards_wei"])
        w.writerow([f"USDe rewards a year, {k}", f"{usde(paid_wei):.2f} USDe", f"{avg_bal:.2f} USDe average end-of-day balance, Sep 1 to 30, x 365/30", f"{v:.3f}"])
    for k, v in cb_shift.items():
        a = (dt.date(2026, 9, 1) + dt.timedelta(days=k)).isoformat()
        b = (dt.date(2026, 9, 30) + dt.timedelta(days=k)).isoformat()
        paid_usd = v * sep_spend / 100
        w.writerow([f"AVAX cashback, paid {a} to {b}", f"${paid_usd:.2f} at the payout day's average AVAX price", f"{sep_spend:.2f} USDe card spend, Sep 1 to 30", f"{v:.3f}"])
    w.writerow(["Reversals, Sep 1 to 30", f"{usde(sep_t['reversals_wei']):.2f} USDe", f"{sep_spend:.2f} USDe card spend, Sep 1 to 30", f"{sep_reversal:.3f}"])
chart = [("Deposits", usde(dep)), ("Withdrawals", -usde(life["withdrawals_wei"])), ("Card spend", -usde(life["card_spend_wei"])),
         ("Reversals", usde(life["reversals_wei"])), ("USDe rewards", usde(rewards)), ("Held on October 5", usde(held_end))]
with open(OUT / "chart_bridge.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["bar", "usde", "kind"])
    for i, (label, v) in enumerate(chart):
        w.writerow([label, f"{v:.2f}", "total" if i in (0, len(chart) - 1) else ("in" if v > 0 else "out")])
results = {
    "cutoff_day": CUTOFF_DAY, "end_block": meta["end_block"], "days": 144, "days_compared_with_dashboard": compared,
    "deposits": str(usde(dep)), "withdrawals": str(usde(life["withdrawals_wei"])), "card_spend_transfers": str(usde(life["card_spend_wei"])),
    "card_spend_events_usde": str(D(life["spend_cents"]) / 100), "spend_events": life["spend_events"], "reversals": str(usde(life["reversals_wei"])),
    "yield": str(usde(life["yield_wei"])), "other_rewards": str(usde(life["other_rewards_wei"])), "rewards": str(usde(rewards)),
    "internal": str(usde(life["internal_wei"])), "held_end": str(usde(held_end)), "held_aug_31": str(usde(held_aug_31_wei)),
    "withdrawals_pct_of_deposits": str(share(life["withdrawals_wei"])), "card_spend_pct_of_deposits": str(share(life["card_spend_wei"])),
    "held_pct_of_deposits": str(share(held_end)), "reversal_rate_pct": str(reversal_rate), "since_beta_deposits": str(usde(since_beta["deposits_wei"])),
    "since_beta_share_of_deposits_pct": str(D(since_beta["deposits_wei"]) / dep * 100), "sep_reward_rate_pct": str(reward_rate),
    "sep_avg_balance": str(avg_bal), "sep_rewards_paid": str(usde(pay_t["yield_wei"] + pay_t["other_rewards_wei"])),
    "sep_reversal_rate_pct": str(sep_reversal), "cashback_avax_to_cutoff": str(cb_avax), "cashback_usd_to_cutoff": str(cb_usd),
    "sep_cashback_avax": str(sep_cb_avax), "sep_cashback_usd": str(sep_cb_usd), "sep_card_spend": str(sep_spend), "sep_cashback_rate_pct": str(cb_rate),
    "weekend_avg_events": str(weekend_ev), "weekday_avg_events": str(weekday_ev), "weekend_avg_usde": str(weekend_usd), "weekday_avg_usde": str(weekday_usd),
    "worked_day": WORKED_DAY, "worked_opening": str(usde(opening)), "worked_closing": str(usde(closing)),
    "worked_flows_usde": {k.replace("_wei", ""): str(usde(int(wd[k]))) for k in FLOWS + ["internal_wei"]}, "worked_spend_events": int(wd["spend_events"]),
    "worked_spending_wallets": int(wd["spending_wallets"]), "worked_depositing_wallets": int(wd["depositing_wallets"]), "worked_funded": int(wd["funded"]),
    "worked_cashback_avax": str(wd_cb[0]), "worked_cashback_usd": str(wd_cb[1]), "worked_cashback_wallets": wd_cb[2],
    "weekend_days_avg_events": str(we_avg_ev), "fri_mon_around_them_avg_events": str(adj_avg_ev), "weekend_days_avg_card_spend": str(we_avg_usde),
    "fri_mon_around_them_avg_card_spend": str(adj_avg_usde), "busiest_day_each_week_from_sep_1": busiest, "spend_events_oct5_over_sep1": str(growth),
    "reversal_rate_on_spend_events_pct": str(reversal_rate_events), "sep_reversal_rate_on_spend_events_pct": str(sep_reversal_events),
    "sep_card_spend_events_usde": str(sep_spend_events), "sep_cashback_rate_on_spend_events_pct": str(cb_rate_events),
    "wallets_created_to_cutoff": int(wd["wallets_created"]),
    "sep_rate_variants_pct": {k: str(v) for k, v in rate_variants.items()}, "sep_days_without_yield": no_yield_days,
    "sep_17_yield": str(usde(int(chain["2026-09-17"]["yield_wei"]))),
    "sep_cashback_rate_shifted_pct": {str(k): str(v) for k, v in cb_shift.items()},
    "top3_withdrawal_days": [d for _, d in top3_w], "top3_withdrawal_share_pct": str(top3_w_share),
    "top2_deposit_days": [d for _, d in by_d[:2]], "top2_deposit_share_pct": str(top2_d_share),
    "allowance_to_outside_addresses_usde": str(other_dest_usde), "allowance_to_outside_addresses_pct_of_card_spend": str(other_dest_pct_spend),
    "dashboard_rate_window": [w_dates[0], w_dates[-1]], "dashboard_yield_apy_pct": str(dash_yield_apy),
    "dashboard_yield_apy_with_other_payer_pct": str(dash_both_apy), "dashboard_cashback_rate_pct": str(D(str(H["cashback_rate_30d"])) * 100),
    "dashboard_tiles_gap_usde": str(usde(tiles_gap)),
    "dashboard_generated_at": dash["generated_at"], "largest_daily_gap_usde": str(worst),
}
(OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
say("All checks passed.")
(OUT / "run_log.txt").write_text("\n".join(log) + "\n")
