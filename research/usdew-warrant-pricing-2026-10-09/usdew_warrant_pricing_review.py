#!/usr/bin/env python3
"""How the market priced StablecoinX's public warrants, USDEW, against the warrant terms, from the warrants'
first session on June 29 to the October 9, 2026 close.

Reads the files in inputs/ and runs every check. If any check fails it stops before writing anything, so
out/ keeps the tables of the last clean run. Otherwise it rewrites the tables in out/. Python 3 standard
library only. It makes no network requests.

Terms, from the warrant agreement, Sections 3.2 and 6, and the resale prospectus of September 14, 2026, pages 93 to 98.
  Each public warrant buys one Class A share for $11.50 until 5 pm New York time on June 25, 2031, five
  years after StablecoinX completed its business combination with TLGY Acquisition Corp. on June 25, 2026.
  Under the warrant agreement StablecoinX assumed that day, it may call every public warrant for $0.01 once
  USDE's last reported sale price has been at least $18.00 on 20 trading days within 30, or for $0.10 once it
  has been at least $10.00 on 20 within 30. The 30-trading-day period ends on the third trading day before
  the notice, and the notice comes at least 30 days before the redemption date. The prospectus says three
  business days, and the 10-Q's Note 9 describes the test as 10 within 20.
  In a $10.00 call, holders may instead exercise without paying cash and receive the number of shares in the
  make-whole table. The table sets it by the months from the redemption date to expiry and by the
  volume-weighted average price over the ten trading days after the notice, with straight-line
  interpolation between rows and columns, and never more than 0.361 shares.

Measures, per session.
  exercise value    = USDE close - $11.50, or zero below $11.50
  time value        = USDEW close - exercise value
  share ratio       = USDEW close / USDE close
  table shares      = the make-whole table at the USDE close, for a redemption date 30 days after the
                      session, the earliest a notice that day allows. The close stands in for the ten-day
                      average after a notice. Defined for closes from $10.00, capped at $18.00.
  table value       = table shares x USDE close
  qualifying closes = USDE closes at or above $10.00 in the 30 sessions ending that day
"""
import csv
import hashlib
import json
import os
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, "inputs")
OUT = os.path.join(HERE, "out")
LOG, FAILED = [], []


def say(s=""):
    LOG.append(s)
    print(s)


def check(name, ok, detail=""):
    say(f"[{'ok' if ok else 'FAIL'}] {name}{' . ' + detail if detail else ''}")
    if not ok:
        FAILED.append(name)


def read_csv(name):
    with open(os.path.join(INP, name), newline="") as f:
        return list(csv.DictReader(f))


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def pct(x):
    return f"{x * 100:.1f}%"


# ---------------------------------------------------------------- inputs and their hashes
manifest = read_csv("manifest.csv")
bad = [r["file"] for r in manifest if sha256_file(os.path.join(INP, r["file"])) != r["sha256"]
       or os.path.getsize(os.path.join(INP, r["file"])) != int(r["bytes"])]
check("every input matches the SHA-256 and size in manifest.csv", not bad and len(manifest) == 5,
      f"{len(manifest)} files" + (f", mismatched {bad}" if bad else ""))

facts = {r["id"]: r for r in read_csv("filing_facts.csv")}
STRIKE = float(facts["exercise_price"]["value"])
CLOSING = date.fromisoformat(facts["closing_date"]["value"])
EXPIRY = CLOSING.replace(year=CLOSING.year + int(facts["term_years"]["value"]))
CALL10 = float(facts["call10_trigger"]["value"])
CALL18 = float(facts["call18_trigger"]["value"])
NEED = int(facts["trigger_closes"]["value"])
WINDOW = int(facts["trigger_window"]["value"])
NOTICE = int(facts["notice_days"]["value"])
CAP = float(facts["make_whole_cap"]["value"])
PUBLIC = int(facts["public_warrants"]["value"])
CLASS_A = int(facts["class_a_outstanding_aug28"]["value"])
check("the warrant terms read from filing_facts.csv agree with each other",
      (STRIKE, CALL10, CALL18, NEED, WINDOW, NOTICE, CAP) == (11.5, 10.0, 18.0, 20, 30, 30, 0.361)
      and EXPIRY == date.fromisoformat(facts["tranche_a_expiry"]["value"]) == date(2031, 6, 25),
      f"expiry {EXPIRY}, five years after the {CLOSING} closing, the date page 97 gives the Tranche A warrants")
check("the warrant agreement and the prospectus set the price test at 20 closes within 30 trading days, the 10-Q's Note 9 "
      "describes it as 10 within 20, and the June 25 amendment left the redemption section alone",
      (int(facts["agreement_test_closes"]["value"]), int(facts["agreement_test_window"]["value"])) == (NEED, WINDOW)
      and (int(facts["tenq_test_closes"]["value"]), int(facts["tenq_test_window"]["value"])) == (10, 20)
      and facts["amendment_redemption_unchanged"]["value"] == "true"
      and date.fromisoformat(facts["tenq_expiry"]["value"]) == EXPIRY)
PUBLIC_OUT = int(facts["public_warrants_outstanding"]["value"])
DATASET_CLASS_A = int(facts["dataset_class_a_oct8"]["value"])

# ---------------------------------------------------------------- prices
usde, usdew = {}, {}
for r in read_csv("usde_daily_stockanalysis_2026-10-09.csv"):
    usde[date.fromisoformat(r["date"])] = float(r["close"])
for r in read_csv("usdew_daily_stockanalysis_2026-10-09.csv"):
    usdew[date.fromisoformat(r["date"])] = float(r["close"])
FIRST_USDE, FIRST_W, LAST = date(2026, 6, 26), date(2026, 6, 29), date(2026, 10, 9)
all_sessions = sorted(d for d in usde if FIRST_USDE <= d <= LAST)
sessions = [d for d in all_sessions if d >= FIRST_W]
check("74 USDE sessions from its first on June 26 to October 9, none on a weekend",
      len(all_sessions) == 74 and all(d.weekday() < 5 for d in all_sessions)
      and all_sessions[0] == FIRST_USDE and all_sessions[-1] == LAST)
missing = [d for d in sessions if d not in usdew]
check("USDEW has a close on every USDE session from June 29 to October 9 but two, and on no other day",
      sorted(usdew) == [d for d in sessions if d not in missing] and missing == [date(2026, 7, 17), date(2026, 8, 18)],
      f"{len(usdew)} of {len(sessions)} sessions, none on {', '.join(map(str, missing))}")
check("the price history matches the closes the prospectus cover gives for September 8",
      usde[date(2026, 9, 8)] == float(facts["prospectus_close_usde_sep8"]["value"])
      and usdew[date(2026, 9, 8)] == float(facts["prospectus_close_usdew_sep8"]["value"]),
      f"USDE ${usde[date(2026, 9, 8)]:.2f}, USDEW ${usdew[date(2026, 9, 8)]:.2f}")

# ---------------------------------------------------------------- the make-whole table
COLS = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0]
TABLE = {}
for r in read_csv("warrant_make_whole_table.csv"):
    TABLE[int(r["months_to_expiration"])] = [float(r[f"fmv_{c:.2f}"]) if r[f"fmv_{c:.2f}"] else None for c in COLS]
MONTHS = sorted(TABLE, reverse=True)
check("the table has 21 rows from 60 months to 0 in steps of 3 and nine prices from $10.00 to $18.00",
      MONTHS == list(range(60, -1, -3)) and all(len(v) == 9 for v in TABLE.values()))
rows_rise = all(all(a <= b for a, b in zip([x for x in v if x is not None], [x for x in v if x is not None][1:]))
                for v in TABLE.values())
cols_fall = all(all((TABLE[m][i] is None or TABLE[m - 3][i] is None or TABLE[m - 3][i] <= TABLE[m][i])
                    for m in MONTHS[:-1]) for i in range(9))
check("shares rise with the price along every row and fall toward expiry down every column", rows_rise and cols_fall)
check("every value in the $18.00 column is the 0.361 cap, and no value exceeds it",
      all(v[-1] == CAP for v in TABLE.values()) and max(x for v in TABLE.values() for x in v if x is not None) == CAP)
check("at $18.00 the cap is worth what paying the exercise price is worth, within a cent",
      abs(CAP * CALL18 - (CALL18 - STRIKE)) < 0.01, f"0.361 x $18.00 = ${CAP * CALL18:.3f}, $18.00 - $11.50 = $6.50")


def months_before(d, n):
    y, m = divmod(d.year * 12 + d.month - 1 - n, 12)
    return date(y, m + 1, d.day)


ROW_DATE = {m: months_before(EXPIRY, m) for m in MONTHS}


def table_shares(redeem, fmv):
    """Shares per warrant in a $10.00 call, interpolated in straight lines between the table's prices and
    between its redemption dates, counted in days. None below $10.00."""
    if fmv < CALL10:
        return None, None
    f = min(fmv, CALL18)
    i = min(int(f - CALL10), 7)
    frac = f - COLS[i]
    hi = min(m for m in MONTHS if ROW_DATE[m] <= redeem)        # the last row dated on or before the redemption
    lo = hi - 3                                                 # the next row, three months nearer expiry
    w = (redeem - ROW_DATE[hi]).days / (ROW_DATE[lo] - ROW_DATE[hi]).days
    assert 0 <= w < 1

    def at(m):
        a, b = TABLE[m][i], TABLE[m][i + 1]
        return a + (b - a) * frac

    return at(hi) + (at(lo) - at(hi)) * w, hi - 3 * w


check("below $18.00 the table gives more than paying $11.50 would, at every quarter dollar from $10.00, for a notice on October 9",
      all(table_shares(date(2026, 11, 8), 10 + k / 4)[0] * (10 + k / 4) > (10 + k / 4) - STRIKE for k in range(32))
      and table_shares(date(2026, 11, 8), 18.0)[0] * 18.0 < 18.0 - STRIKE)
check("the interpolation returns the table's own values at its rows and prices",
      all(abs(table_shares(ROW_DATE[m], c)[0] - TABLE[m][k]) < 1e-12
          for m in MONTHS[:-1] for k, c in enumerate(COLS) if TABLE[m][k] is not None and TABLE[m - 3][k] is not None))

# ---------------------------------------------------------------- per session
rows = []
for d in sessions:
    S = usde[d]
    k = all_sessions.index(d)
    window = all_sessions[max(0, k - WINDOW + 1):k + 1]
    qual = sum(usde[x] >= CALL10 for x in window)
    row = {"date": d, "usde_close": S, "usdew_close": usdew.get(d), "exercise_value": max(S - STRIKE, 0.0),
           "closes_at_or_above_10_in_30": qual, "sessions_in_window": len(window)}
    redeem = d + timedelta(days=NOTICE)
    sh, mo = table_shares(redeem, S)
    row.update({"redemption_date_if_notice": redeem if sh is not None else None, "months_to_expiry": mo,
                "table_shares": sh, "call_value": None if sh is None else max(sh * S, S - STRIKE)})
    if row["usdew_close"] is not None:
        W = row["usdew_close"]
        row["time_value"] = W - row["exercise_value"]
        row["share_ratio"] = W / S
        row["usdew_vs_call_value"] = None if sh is None else W / row["call_value"] - 1
    rows.append(row)
priced = [r for r in rows if r["usdew_close"] is not None]
above = [r for r in priced if r["usde_close"] >= CALL10]
below = [r for r in priced if r["usde_close"] < CALL10]
first10 = above[0]["date"]
check("USDE first closed at or above $10.00 on September 18 and closed there at every session after it",
      first10 == date(2026, 9, 18) and all(usde[d] >= CALL10 for d in all_sessions if d >= first10)
      and all(usde[d] < CALL10 for d in all_sessions if d < first10), f"{len(above)} sessions")
check("USDE never closed at or above $18.00", max(usde[d] for d in all_sessions) < CALL18,
      f"highest close ${max(usde[d] for d in all_sessions):.2f}")
check("USDEW never closed below its exercise value", all(r["time_value"] >= 0 for r in priced))
last = rows[-1]
check("the 30 sessions to October 9 hold 16 closes at or above $10.00, short of the 20 the call needs",
      last["closes_at_or_above_10_in_30"] == 16 and last["sessions_in_window"] == WINDOW
      and max(r["closes_at_or_above_10_in_30"] for r in rows) == 16)
# the 10-Q's wording, 10 closes within 20 sessions
def count_in(d, n):
    k = all_sessions.index(d)
    return sum(usde[x] >= CALL10 for x in all_sessions[max(0, k - n + 1):k + 1])


tenq_first = next(d for d in all_sessions if count_in(d, 20) >= 10)
check("under the 10-Q's wording USDE would have reached 10 closes at or above $10.00 within 20 sessions on October 1",
      tenq_first == date(2026, 10, 1), f"{tenq_first}")

# a later redemption date, 60 or 90 days out
mid = [r for r in above if date(2026, 9, 21) <= r["date"] <= date(2026, 10, 7)]
sens = {}
for days in (30, 60, 90):
    sens[days] = {}
    for r in above:
        sh_d, _ = table_shares(r["date"] + timedelta(days=days), r["usde_close"])
        sens[days][r["date"]] = r["usdew_close"] / (sh_d * r["usde_close"]) - 1
check("from September 21 to October 7 USDEW closed below its call value with the redemption date 30, 60 or 90 days out",
      len(mid) == 13 and all(sens[k][r["date"]] < 0 for k in sens for r in mid),
      ", ".join(f"{k} days {min(-sens[k][r['date']] for r in mid) * 100:.2f}% to {max(-sens[k][r['date']] for r in mid) * 100:.2f}% below"
                for k in sens))

# half-cent closes implied by the source's daily change column
raw = {date.fromisoformat(r["date"]): r for r in read_csv("usdew_daily_stockanalysis_2026-10-09.csv")}
rd = sorted(raw)


def implied(d):
    i = rd.index(d)
    fwd = float(raw[rd[i - 1]]["close"]) * (1 + float(raw[d]["change_pct"]) / 100)
    back = float(raw[rd[i + 1]]["close"]) / (1 + float(raw[rd[i + 1]]["change_pct"]) / 100)
    return fwd, back


HALF = {date(2026, 9, 25): 6.015, date(2026, 9, 30): 5.165, date(2026, 10, 8): 3.885}
check("the source's daily changes, from both neighboring days, put USDEW's September 25, September 30 and October 8 closes at "
      "half cents", all(abs(x - v) < 0.001 for d, v in HALF.items() for x in implied(d)),
      ", ".join(f"{d} {implied(d)[0]:.4f} and {implied(d)[1]:.4f}" for d in HALF))
half_gap = {d: v / next(r["call_value"] for r in above if r["date"] == d) - 1 for d, v in HALF.items()}

filings = read_csv("edgar_filings_2026-10-09.csv")
check("EDGAR listed no filing after October 2 and no 8-K after September 17",
      max(r["filing_date"] for r in filings) == "2026-10-02"
      and max(r["filing_date"] for r in filings if r["form"] == "8-K") == "2026-09-17", f"{len(filings)} filings from June 25")

# ---------------------------------------------------------------- results
ratio_hi = max(above, key=lambda r: r["share_ratio"])
ratio_lo = min(above, key=lambda r: r["share_ratio"])
gap_hi = max(above, key=lambda r: r["usdew_vs_call_value"])
gap_lo = min(above, key=lambda r: r["usdew_vs_call_value"])
peak = max(priced, key=lambda r: r["usde_close"])
o8 = next(r for r in rows if r["date"] == date(2026, 10, 8))
cashless_shares = PUBLIC_OUT * last["table_shares"]
mid_gaps = sorted(-r["usdew_vs_call_value"] for r in mid)
say()
say("USDEW against USDE")
say(f"  {len(priced)} sessions with both closes, {priced[0]['date']} to {priced[-1]['date']}")
say(f"  before {first10}: share ratio {min(r['share_ratio'] for r in below):.4f} to {max(r['share_ratio'] for r in below):.4f}")
say(f"  from {first10}: share ratio {ratio_lo['share_ratio']:.4f} on {ratio_lo['date']} to {ratio_hi['share_ratio']:.4f} "
    f"on {ratio_hi['date']}; table shares {min(r['table_shares'] for r in above):.4f} to {max(r['table_shares'] for r in above):.4f}")
say(f"  USDEW against table value from {first10}: {gap_lo['usdew_vs_call_value'] * 100:+.1f}% on {gap_lo['date']} to "
    f"{gap_hi['usdew_vs_call_value'] * 100:+.1f}% on {gap_hi['date']}")
for r in (peak, o8, last):
    say(f"  {r['date']}: USDE ${r['usde_close']:.2f}, USDEW ${r['usdew_close']:.2f}, exercise value ${r['exercise_value']:.2f}, "
        f"time value ${r['time_value']:.2f}, ratio {r['share_ratio']:.4f}, table {r['table_shares']:.4f} shares at "
        f"{r['months_to_expiry']:.2f} months = ${r['call_value']:.4f}, USDEW {r['usdew_vs_call_value'] * 100:+.2f}%")
say(f"  closes at or above $10.00 in the 30 sessions to {LAST}: {last['closes_at_or_above_10_in_30']} of {NEED} needed")
say(f"  September 21 to October 7: USDEW {mid_gaps[0] * 100:.2f}% to {mid_gaps[-1] * 100:.2f}% below call value, median "
    f"{mid_gaps[len(mid_gaps) // 2] * 100:.2f}%")
for k in (60, 90):
    say(f"  redemption date {k} days out: October 8 {sens[k][date(2026, 10, 8)] * 100:+.2f}%, October 9 "
        f"{sens[k][LAST] * 100:+.2f}%")
say("  half-cent closes: " + ", ".join(f"{d} ${v} gap {half_gap[d] * 100:+.2f}%" for d, v in HALF.items()))
say(f"  a $10.00 call settled at the {LAST} close: {PUBLIC_OUT:,} x {last['table_shares']:.7f} = {cashless_shares:,.0f} shares, "
    f"{cashless_shares / CLASS_A * 100:.2f}% of {CLASS_A:,} and {cashless_shares / DATASET_CLASS_A * 100:.2f}% of "
    f"{DATASET_CLASS_A:,} Class A shares; paying $11.50 for each: {PUBLIC_OUT:,} shares and ${PUBLIC_OUT * STRIKE:,.0f}")

if FAILED:
    say(f"{len(FAILED)} check(s) failed: {', '.join(FAILED)}. Nothing was written to out/.")
    raise SystemExit(1)

os.makedirs(OUT, exist_ok=True)


def fmt(v, nd):
    return "" if v is None else (f"{v:.{nd}f}" if isinstance(v, float) else str(v))


with open(os.path.join(OUT, "usdew_by_session.csv"), "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["date", "usde_close", "usdew_close", "exercise_value", "time_value", "share_ratio",
                "closes_at_or_above_10_in_30", "redemption_date_if_notice", "months_to_expiry", "table_shares",
                "call_value", "usdew_vs_call_value_pct"])
    for r in rows:
        w.writerow([r["date"], f"{r['usde_close']:.2f}", fmt(r["usdew_close"], 2), f"{r['exercise_value']:.2f}",
                    fmt(r.get("time_value"), 2), fmt(r.get("share_ratio"), 6), r["closes_at_or_above_10_in_30"],
                    fmt(r["redemption_date_if_notice"], 0), fmt(r["months_to_expiry"], 4), fmt(r["table_shares"], 6),
                    fmt(r["call_value"], 6),
                    "" if r.get("usdew_vs_call_value") is None else f"{r['usdew_vs_call_value'] * 100:.2f}"])

# chart curves at the October 9 notice: exercise value, and table value from $10.00 to $18.00
curve = []
for k in range(0, 73):
    s = k * 0.25
    sh, _ = table_shares(last["redemption_date_if_notice"], s)
    curve.append([f"{s:.2f}", f"{max(s - STRIKE, 0):.4f}", "" if sh is None else f"{max(sh * s, s - STRIKE):.4f}"])
with open(os.path.join(OUT, "chart_curves.csv"), "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["usde_price", "exercise_value", "call_value_at_october_9"])
    w.writerows(curve)


def rec(r):
    return {k: (str(v) if isinstance(v, date) else v) for k, v in r.items()}


results = {
    "window": {"first_usdew_session": str(priced[0]["date"]), "last_session": str(LAST), "sessions_with_both": len(priced),
               "usdew_missing": [str(d) for d in missing]},
    "terms": {"exercise_price": STRIKE, "expiry": str(EXPIRY), "call10": CALL10, "call18": CALL18, "closes_needed": NEED,
              "window": WINDOW, "notice_days": NOTICE, "cap": CAP, "public_warrants": PUBLIC,
              "class_a_aug28": CLASS_A},
    "first_close_at_or_above_10": str(first10),
    "sessions_at_or_above_10": len(above),
    "highest_close": {"date": str(peak["date"]), "usde_close": peak["usde_close"]},
    "share_ratio_before": [min(r["share_ratio"] for r in below), max(r["share_ratio"] for r in below)],
    "share_ratio_from_first10": {"low": rec(ratio_lo), "high": rec(ratio_hi)},
    "table_shares_from_first10": [min(r["table_shares"] for r in above), max(r["table_shares"] for r in above)],
    "usdew_vs_call_value_from_first10": {"low": rec(gap_lo), "high": rec(gap_hi)},
    "peak": rec(peak), "october8": rec(o8), "october9": rec(last),
    "cashless_call_at_october9": {"public_warrants_outstanding": PUBLIC_OUT, "shares": cashless_shares,
                                  "of_class_a_aug28": cashless_shares / CLASS_A,
                                  "of_dataset_class_a_oct8": cashless_shares / DATASET_CLASS_A,
                                  "cash_exercise_shares": PUBLIC_OUT, "cash_exercise_proceeds": PUBLIC_OUT * STRIKE},
    "september21_to_october7": {"sessions": len(mid), "gap_low": -mid_gaps[0], "gap_high": -mid_gaps[-1],
                                "gap_median": -mid_gaps[len(mid_gaps) // 2]},
    "redemption_date_sensitivity": {str(k): {str(d): g for d, g in v.items()} for k, v in sens.items()},
    "tenq_tenth_close_within_20": str(tenq_first),
    "half_cent_closes": {str(d): {"implied_close": v, "gap": half_gap[d]} for d, v in HALF.items()},
}
with open(os.path.join(OUT, "results.json"), "w") as f:
    json.dump(results, f, indent=1)
    f.write("\n")
say("All checks passed. Tables written to out/.")
with open(os.path.join(OUT, "run_log.txt"), "w") as f:
    f.write("\n".join(LOG) + "\n")
