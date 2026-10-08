#!/usr/bin/env python3
"""
StablecoinX lock-up waiver review. Dashboard rows through the October 7, 2026 close, filings through October 8, 2026.

Run from this directory with Python 3 and the standard library only:  python3 stablecoinx_waiver_review.py

Reads   inputs/ethenadat_data_4c7c3a7.json   dashboard dataset generated 2026-10-05 00:59:25 UTC, the last one before
                                             the waiver took effect. Its last row is the October 2 session
        inputs/ethenadat_data_e57e314.json   dashboard dataset generated 2026-10-08 01:01:13 UTC. Last row October 7
        inputs/ena_tranches_e57e314.csv      the dashboard's tranche file, identical at both commits
        inputs/filing_facts.csv              every number taken from a filing, with its source and place
        inputs/filing_dates.csv              every date taken from a filing
Writes  out/*.csv and out/results.json
Stops   with an AssertionError if any cross-check fails.

Names used below
  TPA-1, TPA-2   the token purchase agreements of July 21, 2025 and September 5, 2025 (Annexes H-1 and H-2)
  dashboard model    the dashboard's own unlock schedule: tranche purchase dates of July 31 and September 30, 2025,
                     a 25% unlock 12 months later, then 36 equal monthly steps, month ends clamped
"""
import calendar
import csv
import datetime as dt
import json
import math
from decimal import Decimal as D, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).parent
IN, OUT = HERE / "inputs", HERE / "out"
OUT.mkdir(exist_ok=True)

LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    LOG.append(s)
    print(s)


def q(x, places):
    return D(x).quantize(D(1).scaleb(-places), rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------------------------------------------
# 1. Inputs
# ---------------------------------------------------------------------------------------------------------------
F = {r["fact"]: D(r["value"]) for r in csv.DictReader(open(IN / "filing_facts.csv"))}
DATES = {r["event"]: dt.date.fromisoformat(r["date"]) for r in csv.DictReader(open(IN / "filing_dates.csv"))}
PRE = json.load(open(IN / "ethenadat_data_4c7c3a7.json"))
POST = json.load(open(IN / "ethenadat_data_e57e314.json"))
TR = list(csv.DictReader(open(IN / "ena_tranches_e57e314.csv")))

assert PRE["generated_at"] == "2026-10-05T00:59:25+00:00", PRE["generated_at"]
assert POST["generated_at"] == "2026-10-08T01:01:13+00:00", POST["generated_at"]
assert PRE["series"]["date"][-1] == "2026-10-02" and POST["series"]["date"][-1] == "2026-10-07"
assert PRE["tranches"] == POST["tranches"], "the tranche records differ between the two datasets"
assert [t["tranche"] for t in TR] == ["cash_pipe_initial", "cash_pipe_additional", "ena_paid_pipe_and_contribution"]
HOLD = D(int(POST["ena_holdings"]))
assert HOLD == D(3029000000) == D(int(PRE["ena_holdings"]))
WAIVER = DATES["waiver_effective"]
assert WAIVER == dt.date(2026, 10, 5) and POST["lockup_waiver"]["effective"] == "2026-10-05"
log("Inputs read. Dashboard holdings", f"{HOLD:,}", "ENA. Waiver effective", WAIVER)

# ---------------------------------------------------------------------------------------------------------------
# 2. Filing cross-checks
# ---------------------------------------------------------------------------------------------------------------
price1 = F["tpa1_vwap"] * (1 - F["tpa1_discount"])
assert price1 == F["contrib_price"] == D("0.21056")
assert abs(F["tpa1_amount"] / price1 - F["tpa1_tokens"]) < D("0.01")
assert abs(F["tpa2_amount"] / F["tpa2_price"] - F["tpa2_tokens"]) < D("0.01")
assert abs(F["contrib_usd"] / F["contrib_price"] - F["contrib_tokens"]) < D("0.01")
TPA = F["tpa1_tokens"] + F["tpa2_tokens"]
OTHER = F["contrib_tokens"] + F["inkind_july_tokens"] + F["inkind_sept_tokens"]
PROFORMA_TOTAL = TPA + OTHER
Q2_TOTAL = F["contrib_tokens"] + F["q2_pipe_july_tokens"] + F["q2_pipe_sept_tokens"]
diff_july = F["q2_pipe_july_tokens"] - (F["tpa1_tokens"] + F["inkind_july_tokens"])
diff_sept = F["q2_pipe_sept_tokens"] - (F["tpa2_tokens"] + F["inkind_sept_tokens"])
assert diff_july == D("-2536.45") and diff_sept == D("-0.40")
assert TPA == D("2146228863.59") and PROFORMA_TOTAL == D("3031406957.79") and Q2_TOTAL == D("3031404420.94")
assert F["pr_closing_ena_millions"] * 1000000 == HOLD
# the dashboard's tranche counts are the filing counts rounded, and its third tranche is what is left of 3,029,000,000
tok = {t["tranche"]: D(t["tokens"]) for t in TR}
assert tok["cash_pipe_initial"] == q(F["tpa1_tokens"], 0) == D(1231887038)
assert tok["cash_pipe_additional"] == q(F["tpa2_tokens"], 0) == D(914341826)
assert tok["ena_paid_pipe_and_contribution"] == HOLD - tok["cash_pipe_initial"] - tok["cash_pipe_additional"] == D(882771136)
CONTRIB_JULY = F["contrib_tokens"] + F["inkind_july_tokens"]
assert CONTRIB_JULY == D("458824341.82")
log("Token purchase prices and counts reconcile. TPA total", f"{TPA:,}", "| other ENA in the filings", f"{OTHER:,}",
    "| dashboard third tranche", f"{tok['ena_paid_pipe_and_contribution']:,}",
    "| filings' total", f"{PROFORMA_TOTAL:,}", "(pro forma),", f"{Q2_TOTAL:,}", "(10-Q)")

with open(OUT / "holdings_by_source.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["group", "ena_tokens", "source", "lock_up_before_october_5_per_filings", "dashboard_treatment_before_october_5"])
    w.writerow(["Bought under TPA-1 with July 2025 PIPE cash", F["tpa1_tokens"], "Prospectus of Feb 17, 2026, pro forma notes",
                "48-month schedule from Completion, by the end of July 2025", "48-month schedule from July 31, 2025"])
    w.writerow(["Bought under TPA-2 with September 2025 PIPE cash", F["tpa2_tokens"], "Prospectus of Feb 17, 2026, pro forma notes",
                "48-month schedule from Completion, by the end of September 2025", "48-month schedule from September 30, 2025"])
    w.writerow(["Contributed by Ethena", F["contrib_tokens"], "10-Q Note 3 and the prospectus's summary of the Contribution Agreement",
                "Locked at June 30, 2026, unlocking over up to 48 months on a schedule the filings do not give", "Counted as unlocked"])
    w.writerow(["Paid in kind under the July 2025 PIPE", F["inkind_july_tokens"], "Prospectus of Feb 17, 2026, pro forma notes",
                "Transfer restrictions of 0 to 36 months, split not given", "Counted as unlocked"])
    w.writerow(["Paid in kind under the September 2025 PIPE", F["inkind_sept_tokens"], "Prospectus of Feb 17, 2026, pro forma notes",
                "No restrictions on transfer", "Counted as unlocked"])
    w.writerow(["Total in the filings", PROFORMA_TOTAL, "Sum of the five rows", "", ""])
    w.writerow(["Dashboard holdings input", HOLD, "Press release of June 25, 2026, approximately 3,029 million", "", ""])

# ---------------------------------------------------------------------------------------------------------------
# 3. The dashboard model, written again from its description, and checked against every dataset row
# ---------------------------------------------------------------------------------------------------------------


def add_months(d, m):
    y, mo = divmod(d.month - 1 + m, 12)
    y, mo = d.year + y, mo + 1
    return dt.date(y, mo, min(d.day, calendar.monthrange(y, mo)[1]))


def steps_done(start, d):
    """Monthly steps that have fallen due on or before d after the 12-month cliff. -1 before the cliff."""
    if d < add_months(start, 12):
        return -1
    m = (d.year - start.year) * 12 + d.month - start.month - 12
    while add_months(start, 12 + m) > d:
        m -= 1
    while add_months(start, 12 + m + 1) <= d:
        m += 1
    return m


def unlocked_fraction(start, d):
    m = steps_done(start, d)
    if m < 0:
        return D(0)
    return min(D(1), D("0.25") + D("0.75") * min(36, m) / 36)


def dashboard_locked(d, honor_waiver=True):
    total = D(0)
    for t in TR:
        if t["locked"].strip().lower() != "true":
            continue
        if honor_waiver and t["waived_on"] and d >= dt.date.fromisoformat(t["waived_on"]):
            continue
        total += D(t["tokens"]) * (1 - unlocked_fraction(dt.date.fromisoformat(t["purchase_date"]), d))
    return total


def check_series(ds, name):
    s = ds["series"]
    n = 0
    for i, day in enumerate(s["date"]):
        d = dt.date.fromisoformat(day)
        unl = D(int(ds["ena_holdings"])) - dashboard_locked(d)
        assert abs(D(s["ena_unlocked"][i]) - q(unl, 0)) <= 1, (name, day, s["ena_unlocked"][i], unl)
        if s["usde_close"][i] is not None and s["ena_price"][i] is not None and s["nav_unlocked_per_share"][i] is not None:
            e, p, sh = D(str(s["ena_price"][i])), D(str(s["usde_close"][i])), D(str(s["shares_outstanding"][i]))
            nps = e * unl / sh
            assert abs(q(nps, 4) - D(str(s["nav_unlocked_per_share"][i]))) <= D("0.0001"), (name, day)
            assert abs(q(p / nps, 4) - D(str(s["mnav_unlocked"][i]))) <= D("0.0001"), (name, day)
        n += 1
    return n


n_pre, n_post = check_series(PRE, "4c7c3a7"), check_series(POST, "e57e314")
log("Dashboard model reproduces ena_unlocked, nav_unlocked_per_share and mnav_unlocked on", n_pre, "rows of 4c7c3a7 and",
    n_post, "rows of e57e314")

# the steps of the dashboard model, as dated events: (date, tranche, fraction of the tranche unlocked that day)
events = []
for t in TR:
    if t["locked"].strip().lower() != "true":
        continue
    start = dt.date.fromisoformat(t["purchase_date"])
    for m in range(0, 37):
        events.append((add_months(start, 12 + m), t["tranche"], D("0.25") if m == 0 else D("0.75") / 36))
events.sort()
assert len(events) == 74 and events[-1][0] == dt.date(2029, 9, 30) and events[0][0] == dt.date(2026, 7, 31)
FILING_SIZE = {"cash_pipe_initial": None, "cash_pipe_additional": None}   # filled in section 4

# ---------------------------------------------------------------------------------------------------------------
# 4. What the token purchase agreements still held locked when the waiver took effect
# ---------------------------------------------------------------------------------------------------------------
eve = WAIVER - dt.timedelta(days=1)          # October 4, 2026, the last day of the old schedule
lock_h1 = {F["tpa1_tokens"] * (1 - unlocked_fraction(dt.date(2025, 7, day), eve)) for day in range(21, 32)}
lock_h2 = {F["tpa2_tokens"] * (1 - unlocked_fraction(dt.date(2025, 9, day), eve)) for day in range(5, 31)}
assert len(lock_h1) == 1 and len(lock_h2) == 1, "the locked count depends on the completion day"
LOCK_H1, LOCK_H2 = lock_h1.pop(), lock_h2.pop()
LOCKED_TPA = LOCK_H1 + LOCK_H2
UNLOCKED_TPA = TPA - LOCKED_TPA
assert q(LOCKED_TPA, 0) == D(1558343021)
assert q(LOCKED_TPA / HOLD * 100, 1) == D("51.4")
# the dashboard model gives the same count on its rounded tranche sizes
dash_locked_eve = dashboard_locked(eve, honor_waiver=False)
assert q(dash_locked_eve, 0) == D(1558343021) == HOLD - D(1470656979)
log("Locked under the TPA schedules at the end of October 4, 2026:", f"{LOCKED_TPA:,.2f}", "ENA, for every completion day in",
    "July 21 to 31 and September 5 to 30, 2025.", f"{q(LOCKED_TPA / HOLD * 100, 1)}% of 3,029,000,000")
last_h1 = add_months(DATES["tpa1_completed_by"], 48)
last_h2 = add_months(DATES["tpa2_completed_by"], 48)
assert (last_h1, last_h2) == (dt.date(2029, 7, 31), dt.date(2029, 9, 30))
# the next step the old schedule had due after the waiver, on the dashboard model
nxt = [e for e in events if e[0] >= WAIVER][0]
assert nxt[0] == dt.date(2026, 10, 30) and nxt[1] == "cash_pipe_additional"
monthly_h1 = F["tpa1_tokens"] * D("0.75") / 36
monthly_h2 = F["tpa2_tokens"] * D("0.75") / 36

FILING_SIZE.update({"cash_pipe_initial": F["tpa1_tokens"], "cash_pipe_additional": F["tpa2_tokens"]})
# the schedule on the filing counts and the dashboard model's dates. Each row is one step of the old schedule
with open(OUT / "tpa_schedule.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "agreement", "unlocked_that_day", "still_locked_on_old_schedule", "still_locked_with_waiver"])
    run = TPA
    shown = False
    for d, tr, frac in events:
        if not shown and d >= WAIVER:
            w.writerow([WAIVER.isoformat(), "waiver takes effect", q(run, 2), q(run, 2), 0])
            assert q(run, 0) == q(LOCKED_TPA, 0)
            shown = True
        amt = FILING_SIZE[tr] * frac
        run -= amt
        w.writerow([d.isoformat(), "TPA-1" if tr == "cash_pipe_initial" else "TPA-2", q(amt, 2), q(run, 2), q(run, 2) if d < WAIVER else 0])
    assert abs(run) < D("0.000001")

# chart data, on the dashboard model's dates and tranche sizes: still-locked TPA ENA wherever the count changes
chart = []
for d in sorted({dt.date(2025, 7, 31), dt.date(2025, 9, 30), WAIVER, *[e[0] for e in events]}):
    if d < dt.date(2025, 9, 30):
        orig = D(tok["cash_pipe_initial"])          # TPA-2 tokens not yet bought
    else:
        orig = dashboard_locked(d, honor_waiver=False)
    chart.append((d, orig, orig if d < WAIVER else D(0)))
assert chart[0] == (dt.date(2025, 7, 31), D(1231887038), D(1231887038))
assert chart[1] == (dt.date(2025, 9, 30), D(2146228864), D(2146228864))
assert [c for c in chart if c[0] == WAIVER][0][1] == dash_locked_eve and chart[-1][1] == 0
with open(OUT / "chart_locked_schedule.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "locked_original_schedule", "locked_after_waiver"])
    for d, o, a in chart:
        w.writerow([d.isoformat(), q(o, 0), q(a, 0)])
log("Old schedule would have unlocked", f"{q(monthly_h1, 2):,}", "ENA a month under TPA-1 and", f"{q(monthly_h2, 2):,}",
    "under TPA-2, the last steps falling in July and September 2029. Next step after the waiver on the dashboard model:", nxt[0])

# ---------------------------------------------------------------------------------------------------------------
# 5. The dashboard's rows before and after the waiver
# ---------------------------------------------------------------------------------------------------------------


def row(ds, day):
    s = ds["series"]
    i = s["date"].index(day)
    return {k: s[k][i] for k in s}


r2_pre, r2_post = row(PRE, "2026-10-02"), row(POST, "2026-10-02")
assert r2_pre == r2_post, "the October 2 row was restated between the two datasets"
rows = [("2026-10-02", "4c7c3a7 and e57e314", r2_post)] + [(dday, "e57e314", row(POST, dday)) for dday in ("2026-10-05", "2026-10-06", "2026-10-07")]
BA = []
for day, src, r in rows:
    d = dt.date.fromisoformat(day)
    p, e, sh, u = D(str(r["usde_close"])), D(str(r["ena_price"])), D(str(r["shares_outstanding"])), D(str(r["ena_unlocked"]))
    cf_u = HOLD - dashboard_locked(d, honor_waiver=False)
    rec = {
        "date": day, "dataset": src, "usde_close": p, "ena_price": e, "shares": sh, "ena_holdings": HOLD, "ena_unlocked": u,
        "unlocked_share": u / HOLD, "token_nav_per_share": HOLD * e / sh, "mnav": p / (HOLD * e / sh),
        "nav_unlocked_per_share": u * e / sh, "mnav_unlocked": p / (u * e / sh),
        "old_schedule_ena_unlocked": cf_u, "old_schedule_nav_unlocked_per_share": cf_u * e / sh,
        "old_schedule_mnav_unlocked": p / (cf_u * e / sh),
    }
    # the dataset rounds ENA to six decimals but computes its NAV fields from the unrounded price, so allow 0.0002
    assert abs(q(rec["token_nav_per_share"], 4) - D(str(r["nav_per_share"]))) <= D("0.0002") and abs(q(rec["mnav"], 4) - D(str(r["mnav"]))) <= D("0.0001")
    BA.append(rec)
b2, b5 = BA[0], BA[1]
# second sources for every price in those rows: S&P Global closes via StockAnalysis, CoinGecko 00:00 UTC via DefiLlama
SA = {r["date"]: D(r["close"]) for r in csv.DictReader(open(IN / "usde_spglobal_via_stockanalysis.csv"))}
CG = {r["utc"][:10]: D(r["price_usd"]) for r in csv.DictReader(open(IN / "ena_coingecko_via_defillama.csv"))}
for rec in BA:
    assert SA[rec["date"]] == rec["usde_close"], ("USDE close", rec["date"])
    assert q(CG[rec["date"]], 6) == rec["ena_price"], ("ENA price", rec["date"])
log("USDE closes match S&P Global via StockAnalysis, and ENA prices match CoinGecko at 00:00 UTC, on", len(BA), "rows")
assert b2["ena_unlocked"] == D(1470656979) and b5["ena_unlocked"] == HOLD
assert q(b2["unlocked_share"] * 100, 1) == D("48.6")
assert (q(b2["nav_unlocked_per_share"], 2), q(b5["nav_unlocked_per_share"], 2)) == (D("14.82"), D("30.28"))
assert (q(b2["mnav_unlocked"], 3), q(b5["mnav_unlocked"], 3)) == (D("0.955"), D("0.494"))
assert (q(b2["token_nav_per_share"], 2), q(b5["token_nav_per_share"], 2)) == (D("30.52"), D("30.28"))
assert (q(b2["mnav"], 3), q(b5["mnav"], 3)) == (D("0.464"), D("0.494"))
assert q(b5["old_schedule_mnav_unlocked"], 2) == D("1.02") and q(b5["old_schedule_nav_unlocked_per_share"], 2) == D("14.70")
assert q(b5["old_schedule_ena_unlocked"], 0) == b2["ena_unlocked"]
with open(OUT / "dashboard_before_after.csv", "w", newline="") as f:
    w = csv.writer(f)
    keys = list(BA[0].keys())
    w.writerow(keys)
    for rec in BA:
        w.writerow([rec[k] if isinstance(rec[k], str) else (q(rec[k], 6) if abs(rec[k]) < 1000 else q(rec[k], 2)) for k in keys])
log("Oct 2 row: unlocked", f"{b2['ena_unlocked']:,}", f"({q(b2['unlocked_share'] * 100, 1)}%), unlocked token NAV per share",
    q(b2["nav_unlocked_per_share"], 4), ", unlocked mNAV", q(b2["mnav_unlocked"], 4), "| Oct 5 row:", f"{b5['ena_unlocked']:,}",
    q(b5["nav_unlocked_per_share"], 4), q(b5["mnav_unlocked"], 4), "| Oct 5 on the old schedule:",
    q(b5["old_schedule_nav_unlocked_per_share"], 4), q(b5["old_schedule_mnav_unlocked"], 4))

# the bridge from 0.955 to 0.494. mNAV(unlocked) = P / (E x U / S), and S is the same on both days
assert b2["shares"] == b5["shares"] == D(24139375)
f_price = b5["usde_close"] / b2["usde_close"]
f_ena = b2["ena_price"] / b5["ena_price"]
f_unl = b2["ena_unlocked"] / b5["ena_unlocked"]
assert abs(b2["mnav_unlocked"] * f_price * f_ena * f_unl - b5["mnav_unlocked"]) < D("1e-20")
mid = b2["mnav_unlocked"] * f_price * f_ena
assert abs(mid - b5["old_schedule_mnav_unlocked"]) < D("1e-8")   # rounded versus unrounded unlocked count
assert (q((f_price - 1) * 100, 1), q((b5["ena_price"] / b2["ena_price"] - 1) * 100, 1)) == (D("5.7"), D("-0.8"))
assert q(b5["ena_unlocked"] / b2["ena_unlocked"], 2) == D("2.06")
with open(OUT / "unlocked_multiple_bridge.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["step", "factor", "unlocked_mnav_after_step"])
    w.writerow(["October 2 row", "", q(b2["mnav_unlocked"], 6)])
    w.writerow(["USDE close from $14.15 to $14.96", q(f_price, 6), q(b2["mnav_unlocked"] * f_price, 6)])
    w.writerow(["ENA from $0.243211 to $0.241327", q(f_ena, 6), q(mid, 6)])
    w.writerow(["Unlocked ENA from 1,470,656,979 to 3,029,000,000", q(f_unl, 6), q(b5["mnav_unlocked"], 6)])
log("Bridge: x", q(f_price, 4), "for the stock, x", q(f_ena, 4), "for ENA, x", q(f_unl, 4), "for the unlocked count. Without the waiver",
    q(mid, 4))

# the merger prospectus's summary dates the September schedule from the agreement date, September 5, 2025. On that
# reading the first monthly step of the September purchase falls on October 5, 2026, the day the waiver took effect
sep5 = dt.date(2025, 9, 5)
assert steps_done(sep5, dt.date(2026, 10, 4)) == 0 and steps_done(sep5, WAIVER) == 1
step_sep = D(tok["cash_pipe_additional"]) * D("0.75") / 36
u_sep5 = HOLD - (dashboard_locked(WAIVER, honor_waiver=False) - step_sep)
nps_sep5 = u_sep5 * b5["ena_price"] / b5["shares"]
mnav_sep5 = b5["usde_close"] / nps_sep5
assert q(step_sep, 0) == D(19048788) and q(u_sep5, 0) == D(1489705767) and q(mnav_sep5, 2) == D("1.00")
assert q(HOLD / q(u_sep5, 0), 2) == D("2.03")   # the waiver's multiple of unlocked ENA on that reading
first_quarter_sep = F["tpa2_tokens"] * D("0.25")
assert q(first_quarter_sep, 0) == D(228585456) and (dt.date(2025, 9, 30) - sep5).days == 25
log("On a September 5 start the old schedule unlocks", f"{q(u_sep5, 0):,}", "ENA on October 5 and unlocked mNAV is", q(mnav_sep5, 4),
    "| the first quarter of the September purchase,", f"{q(first_quarter_sep, 0):,}", "ENA, would unlock 25 days before the dashboard's date")

# ---------------------------------------------------------------------------------------------------------------
# 6. How far the dashboard's pre-waiver figure could be too high
# ---------------------------------------------------------------------------------------------------------------
low = b2["ena_unlocked"] - CONTRIB_JULY
assert q(low, 0) == D(1011832637) and q(low / HOLD * 100, 1) == D("33.4")
assert q(CONTRIB_JULY / HOLD * 100, 1) == D("15.1")
low_nps = low * b2["ena_price"] / b2["shares"]
low_mnav = b2["usde_close"] / low_nps
log("If none of the contribution or July in-kind ENA had unlocked by October 2, the unlocked count was", f"{q(low, 0):,}",
    f"({q(low / HOLD * 100, 1)}%), unlocked token NAV per share", q(low_nps, 2), "and the multiple", q(low_mnav, 3))
with open(OUT / "pre_waiver_bounds.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["case_on_october_2", "ena_unlocked", "share_of_3029000000", "nav_unlocked_per_share", "usde_close_over_it"])
    w.writerow(["Dashboard model, contribution and in-kind ENA counted as unlocked", b2["ena_unlocked"], q(b2["unlocked_share"], 6),
                q(b2["nav_unlocked_per_share"], 4), q(b2["mnav_unlocked"], 4)])
    w.writerow(["Contribution and July in-kind ENA all still locked", q(low, 2), q(low / HOLD, 6), q(low_nps, 4), q(low_mnav, 4)])

# ---------------------------------------------------------------------------------------------------------------
# 7. Dates
# ---------------------------------------------------------------------------------------------------------------
q3_end = dt.date(2026, 9, 30)
due = q3_end + dt.timedelta(days=int(F["form10q_days_other"]))
assert due == dt.date(2026, 11, 14) and due.weekday() == 5
FEDERAL_2026 = {dt.date(2026, 11, 11), dt.date(2026, 11, 26), dt.date(2026, 10, 12)}
due_next = due
while due_next.weekday() >= 5 or due_next in FEDERAL_2026:
    due_next += dt.timedelta(days=1)
assert due_next == dt.date(2026, 11, 16)
term_end = add_months(DATES["collab_effective"], 12 * int(F["ca_initial_term_years"]))
assert term_end == DATES["collab_initial_term_end"] == dt.date(2030, 7, 21)
assert WAIVER.weekday() == 0 and (WAIVER - DATES["waiver_8k_filed"]).days == 18 and (DATES["waiver_effective"] - DATES["ethena_post"]).days == 39
log("10-Q for the quarter to September 30 due", due, "(a Saturday), so by", due_next, "| Collaboration Agreement initial term ends", term_end)

# a funding notice received on a Monday, with no holiday in the British Virgin Islands in the way
def add_bdays(d, n):
    while n:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


mon = dt.date(2026, 10, 12)
assert mon.weekday() == 0
clear = add_bdays(mon, int(F["wl_review_bdays"]))
assert clear.weekday() == 0 and (clear - mon).days == 7
settle_latest = add_bdays(clear, int(F["wl_settlement_bdays"]))
assert (settle_latest - mon).days == 14

# ---------------------------------------------------------------------------------------------------------------
# 8. Results
# ---------------------------------------------------------------------------------------------------------------
res = {
    "tpa_tokens": str(TPA), "tpa1_tokens": str(F["tpa1_tokens"]), "tpa2_tokens": str(F["tpa2_tokens"]),
    "locked_tpa_end_oct4": str(q(LOCKED_TPA, 2)), "locked_tpa_h1": str(q(LOCK_H1, 2)), "locked_tpa_h2": str(q(LOCK_H2, 2)),
    "unlocked_tpa_end_oct4": str(q(UNLOCKED_TPA, 2)), "locked_tpa_share_of_holdings": str(q(LOCKED_TPA / HOLD, 6)),
    "monthly_step_h1": str(q(monthly_h1, 2)), "monthly_step_h2": str(q(monthly_h2, 2)),
    "last_step_h1": last_h1.isoformat(), "last_step_h2": last_h2.isoformat(),
    "contribution_tokens": str(F["contrib_tokens"]), "inkind_july_tokens": str(F["inkind_july_tokens"]),
    "inkind_sept_tokens": str(F["inkind_sept_tokens"]), "contribution_plus_july_inkind": str(CONTRIB_JULY),
    "filings_total_pro_forma": str(PROFORMA_TOTAL), "filings_total_10q": str(Q2_TOTAL), "dashboard_holdings": str(HOLD),
    "dashboard_third_tranche": str(tok["ena_paid_pipe_and_contribution"]),
    "oct2": {k: str(v) for k, v in b2.items()}, "oct5": {k: str(v) for k, v in b5.items()},
    "oct6": {k: str(v) for k, v in BA[2].items()}, "oct7": {k: str(v) for k, v in BA[3].items()},
    "bridge": {"price": str(f_price), "ena": str(f_ena), "unlocked": str(f_unl), "without_waiver": str(mid)},
    "september_5_start": {"unlocked_oct5_old_schedule": str(q(u_sep5, 2)), "mnav_unlocked_oct5": str(q(mnav_sep5, 6)),
                          "first_quarter_tokens": str(q(first_quarter_sep, 2)), "days_earlier": 25,
                          "waiver_multiple_of_unlocked": str(q(HOLD / q(u_sep5, 0), 6))},
    "pre_waiver_low_unlocked": str(q(low, 2)), "pre_waiver_low_share": str(q(low / HOLD, 6)),
    "pre_waiver_low_nav_unlocked_per_share": str(q(low_nps, 6)), "pre_waiver_low_mnav_unlocked": str(q(low_mnav, 6)),
    "q3_10q_due": due_next.isoformat(), "collab_initial_term_end": term_end.isoformat(),
    "rows_checked": {"4c7c3a7": n_pre, "e57e314": n_post},
}
json.dump(res, open(OUT / "results.json", "w"), indent=1)
log("All checks passed.")
open(OUT / "run_log.txt", "w").write("\n".join(LOG) + "\n")
