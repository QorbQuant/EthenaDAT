#!/usr/bin/env python3
"""
Recomputes every computed figure in article_draft.md, metadata.json and the chart's text from the
files in inputs/, with code written apart from usdew_warrant_pricing_review.py and in exact fractions,
and confirms that each exact phrase appears. Exits with an error if a phrase is missing or an assertion
fails, so rerun it after any edit. Python 3 standard library only. No network.
"""
import csv
import json
import sys
from datetime import date, timedelta
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).parent
INP = HERE / "inputs"
ARTICLE = (HERE / "article_draft.md").read_text()
META = json.loads((HERE / "metadata.json").read_text())
# layout.json is part of the site build and not of the download, so its cutoff is checked only when present
LAYOUT = json.loads((HERE / "layout.json").read_text()) if (HERE / "layout.json").exists() else None
SVG = (HERE / "out" / "chart_usdew_vs_usde.svg").read_text()
TEXT = ARTICLE + "\n" + META["description"] + "\n" + META["imageAlt"] + "\n" + META["title"] + "\n" + SVG

found, missing = 0, []


def need(phrase, where=TEXT):
    global found
    if phrase in where:
        found += 1
    else:
        missing.append(phrase)


def rows(name):
    with open(INP / name, newline="") as f:
        return list(csv.DictReader(f))


def rnd(x, places):
    """Half-up rounding of a Fraction to a fixed number of decimals, as a string."""
    q = F(10) ** places
    v = (abs(x) * q * 2 + 1) // 2
    s = str(v).rjust(places + 1, "0")
    out = (s[:-places] + "." + s[-places:]) if places else s
    return ("-" if x < 0 and v != 0 else "") + out


def comma(x, places=0):
    s = rnd(x, places)
    whole, _, frac = s.partition(".")
    return f"{int(whole):,}" + ("." + frac if frac else "")


def signed_pct(x):
    s = rnd(abs(x) * 100, 1)
    return ("+" if x > 0 else "−") + s + "%"


def md(d):
    return f"{d:%B} {d.day}"


fact = {r["id"]: r["value"] for r in rows("filing_facts.csv")}
STRIKE, CAP = F(fact["exercise_price"]), F(fact["make_whole_cap"])
EXPIRY = date(2031, 6, 25)
assert fact["closing_date"] == "2026-06-25" and fact["term_years"] == "5" and fact["tranche_a_expiry"] == str(EXPIRY)

# ---------------------------------------------------------------- prices and the trading calendar
hist = {date.fromisoformat(r["date"]): r for r in rows("usde_daily_stockanalysis_2026-10-09.csv")}
close = {d: F(r["close"]) for d, r in hist.items()}
high = {d: F(r["high"]) for d, r in hist.items()}
wclose = {date.fromisoformat(r["date"]): F(r["close"]) for r in rows("usdew_daily_stockanalysis_2026-10-09.csv")}
FIRST, LAST = date(2026, 6, 26), date(2026, 10, 9)
HOLIDAYS = {date(2026, 7, 3), date(2026, 9, 7)}
CAL = [FIRST + timedelta(days=i) for i in range((LAST - FIRST).days + 1)]
CAL = [d for d in CAL if d.weekday() < 5 and d not in HOLIDAYS]
assert [d for d in sorted(close) if FIRST <= d <= LAST] == CAL and len(CAL) == 74
BOTH = [d for d in CAL if d in wclose]
assert len(BOTH) == 71 and BOTH[0] == date(2026, 6, 29) and max(wclose) == LAST
assert [d for d in CAL if d >= BOTH[0] and d not in wclose] == [date(2026, 7, 17), date(2026, 8, 18)]
assert close[date(2026, 9, 8)] == F(fact["prospectus_close_usde_sep8"]) and wclose[date(2026, 9, 8)] == F(fact["prospectus_close_usdew_sep8"])

# ---------------------------------------------------------------- the make-whole table and its interpolation
TBL = {}
for r in rows("warrant_make_whole_table.csv"):
    TBL[int(r["months_to_expiration"])] = {p: (F(r[f"fmv_{p}.00"]) if r[f"fmv_{p}.00"] else None) for p in range(10, 19)}
assert sorted(TBL) == list(range(0, 61, 3)) and all(TBL[m][18] == CAP for m in TBL)


def row_date(n):
    y, mth = EXPIRY.year, EXPIRY.month
    for _ in range(n):
        mth -= 1
        if mth == 0:
            y, mth = y - 1, 12
    return date(y, mth, EXPIRY.day)


def along_price(n, s):
    s = min(s, F(18))
    p = min(int(s), 17)
    lo, hi = TBL[n][p], TBL[n][p + 1]
    return lo + (hi - lo) * (s - p)


def call_shares(redeem, s):
    """Rows bracket the redemption date: the row dated on or before it and the row three months later."""
    for n in range(3, 61, 3):
        later, earlier = row_date(n - 3), row_date(n)
        if earlier <= redeem < later:
            w = F((redeem - earlier).days, (later - earlier).days)
            return along_price(n, s) * (1 - w) + along_price(n - 3, s) * w, n - 3 * w
    raise ValueError(redeem)


assert row_date(57) == date(2026, 9, 25) and row_date(54) == date(2026, 12, 25)

# ---------------------------------------------------------------- per session from the first $10 close
first10 = next(d for d in CAL if close[d] >= 10)
assert first10 == date(2026, 9, 18) and all(close[d] >= 10 for d in CAL if d >= first10)
assert all(close[d] < 10 for d in CAL if d < first10)
ses = [d for d in BOTH if d >= first10]
assert len(ses) == 16
res = {}
for d in ses:
    sh, mo = call_shares(d + timedelta(days=30), close[d])
    val = max(sh * close[d], close[d] - STRIKE)
    res[d] = {"shares": sh, "months": mo, "value": val, "gap": wclose[d] / val - 1, "ratio": wclose[d] / close[d]}

# the table in the article, row by row, shares to four decimals
table_rows = [l for l in ARTICLE.splitlines() if l.startswith("| September ") or l.startswith("| October ")]
assert len(table_rows) == 16
for line, d in zip(table_rows, ses):
    cells = [c.strip() for c in line.strip("|").split("|")]
    want = [md(d), f"${rnd(close[d], 2)}", f"${rnd(wclose[d], 2)}", rnd(res[d]["shares"], 4),
            f"${rnd(res[d]['value'], 2)}", signed_pct(res[d]["gap"])]
    assert cells == want, (cells, want)
    found += 1

o9, o8, s25 = LAST, date(2026, 10, 8), date(2026, 9, 25)
mid = [d for d in ses if date(2026, 9, 21) <= d <= date(2026, 10, 7)]
assert len(mid) == 13 and all(res[d]["gap"] < 0 for d in ses[1:]) and res[ses[0]]["gap"] > 0
gaps = sorted(-res[d]["gap"] for d in mid)


def gap_at(d, days):
    sh, _ = call_shares(d + timedelta(days=days), close[d])
    return wclose[d] / (sh * close[d]) - 1


# within 0.5% on October 8 and 9 under a 30, 60 or 90-day redemption date, and at the half-cent closes
HALF = {s25: F("6.015"), date(2026, 9, 30): F("5.165"), o8: F("3.885")}
assert all(abs(gap_at(d, k)) < F(1, 200) for d in (o8, o9) for k in (30, 60, 90))
assert abs(HALF[o8] / res[o8]["value"] - 1) < F(1, 200)

# ---------------------------------------------------------------- lead
need(f"closed below its estimated value in a $10 call at each of the {len(mid)} sessions from {md(mid[0])} to {md(mid[-1])}, "
     f"2026, by {rnd(gaps[0] * 100, 1)}% to {rnd(gaps[-1] * 100, 1)}% with a median of {rnd(gaps[len(gaps) // 2] * 100, 1)}%.")
need(f"On October 8 and 9 it closed within 0.5% of that value, and on October 9 it closed at ${rnd(wclose[o9], 2)} against "
     f"${rnd(res[o9]['value'], 2)}.")
need("buy back every public warrant for $0.10 once USDE, its Class A stock on Nasdaq, has closed at or above $10 on 20 of 30 "
     "trading days.")
need(f"never more than {fact['make_whole_cap']} of a share.")
need("It applies the table to each day's USDE close in place of the ten-day average price after a notice, with a redemption "
     "date 30 days later.")
assert (first10 - FIRST).days == 84
need(f"USDE first closed above $10 on {md(first10)}, twelve weeks after its first session on June 26.")
window = CAL[-30:]
qual = sum(close[d] >= 10 for d in window)
need(f"USDE had closed at or above $10 on {qual} of the 30 sessions to that date, "
     f"{['', 'one', 'two', 'three', 'four', 'five'][20 - qual]} short of the 20 that the warrant agreement requires.")
assert (fact["agreement_test_closes"], fact["agreement_test_window"]) == ("20", "30")
assert (fact["tenq_test_closes"], fact["tenq_test_window"]) == ("10", "20")
tenth = next(d for d in CAL if sum(close[x] >= 10 for x in CAL[max(0, CAL.index(d) - 19):CAL.index(d) + 1]) >= 10)
need(f"describes the test as 10 closes within 20 trading days, which USDE would have met on {md(tenth)}")
need(f"with its tenth close above $10, on {md(tenth)}.")
filings = rows("edgar_filings_2026-10-09.csv")
assert max(r["filing_date"] for r in filings) == "2026-10-02"
need("No filing through October 9 announced a call.")
need("A second provision allows a call at $0.01 a warrant after 20 closes at or above $18 within 30 trading days.")
top = max(CAL, key=lambda d: close[d])
assert close[top] < 18
need(f"USDE's highest close since June 26 was ${rnd(close[top], 2)}, on {md(top)}.")
need(f"That day USDEW closed at ${rnd(wclose[s25], 2)}, ${rnd(wclose[s25] - (close[s25] - STRIKE), 2)} above its exercise value "
     f"of ${rnd(close[s25] - STRIKE, 2)}, the stock price less the $11.50 exercise price")
assert top == s25 and F(9, 2) < F((EXPIRY - s25).days, 365) < 5
need("with more than four and a half years left before the warrants expire on June 25, 2031.")

# ---------------------------------------------------------------- the chart and the period before September 18
before = [d for d in BOTH if d < first10]
need(f"{len(BOTH)} sessions from {md(BOTH[0])} to {md(LAST)}, 2026")
need(f"{len(before)} sessions before {md(first10)} sit with USDE between ${rnd(min(close[d] for d in before), 2)} and "
     f"${rnd(max(close[d] for d in before), 2)} and USDEW between ${rnd(min(wclose[d] for d in before), 2)} and "
     f"${rnd(max(wclose[d] for d in before), 2)}.")
need(f"{len(ses)} sessions from {md(first10)} sit with USDE between ${rnd(min(close[d] for d in ses), 2)} and "
     f"${rnd(max(close[d] for d in ses), 2)}, all but the first below the call line")
line10 = call_shares(o9 + timedelta(days=30), F(10))[0] * 10
line18 = call_shares(o9 + timedelta(days=30), F(18))[0] * 18
need(f"which rises from ${rnd(line10, 2)} at $10 to ${rnd(line18, 2)} at $18.")
need(f"On October 9 USDEW closed at ${rnd(wclose[o9], 2)} against a call value of ${rnd(res[o9]['value'], 2)}.")
need(f"USDEW closed below its estimated call value from {md(ses[1])} to {md(mid[-1])}", SVG)
need("and on October 8 and 9 within 0.5% of it.", SVG)
need(f"Oct 9, USDEW ${rnd(wclose[o9], 2)}", SVG)
need(f"against a call value of ${rnd(res[o9]['value'], 2)}", SVG)
need(f"Sep 25, USDE ${rnd(close[s25], 2)}, USDEW ${rnd(wclose[s25], 2)}", SVG)
lo = min(ses, key=lambda d: res[d]["gap"])
need(f"by as much as {rnd(-res[lo]['gap'] * 100, 1)}% on {md(lo)}", SVG)
need(f"From {md(ses[1])} to {md(mid[-1])} every USDEW close sat below that session's call value, and on October 8 and 9 "
     "within 0.5% of it.", META["imageAlt"])
need(f"rises from ${rnd(line10, 2)} at a $10 USDE price to ${rnd(line18, 2)} at $18", META["imageAlt"])
need(f"USDEW closed {rnd(gaps[0] * 100, 1)}% to {rnd(gaps[-1] * 100, 1)}% below an estimate of its $10 call value from "
     f"{md(mid[0])} to {md(mid[-1])}, 2026, and within 0.5% of it on October 8 and 9.", META["description"])
assert len(META["description"]) <= 160 and len(META["title"]) <= 60

# ---------------------------------------------------------------- the terms
need(f"Each of the roughly {rnd(F(fact['public_warrants']) / 1_000_000, 1)} million public warrants buys one Class A share for "
     "$11.50 until 5 pm New York time on June 25, 2031, five years after the business combination.")
assert fact["tenq_expiry"] == str(EXPIRY) and fact["amendment_redemption_unchanged"] == "true"
need("the amendment left the expiry and redemption sections unchanged.")
need("USDE's last reported sale price must be at least $10 on 20 trading days within the 30-trading-day period that ends on "
     "the third trading day before the notice.")
need("The notice must come at least 30 days before the redemption date the company fixes.")
need("USDE's volume-weighted average price over the ten trading days after the notice")
need("Warrants not exercised by the redemption date are bought back for $0.10 each.")
need(f"it gives {rnd(TBL[54][10], 3)} to {rnd(TBL[57][10], 3)} shares at $10 and {rnd(CAP, 3)} at $18.")
need(f"At $18 the two are about equal, {rnd(CAP, 3)} × $18 = ${rnd(CAP * 18, 3)} against ${rnd(F(18) - STRIKE, 2)}")
# below $18 the table beats paying $11.50 at every quarter dollar from $10, for an October 9 notice
assert all(call_shares(o9 + timedelta(days=30), F(40 + k, 4))[0] * F(40 + k, 4) > F(40 + k, 4) - STRIKE for k in range(32))
need("so while USDE is below $18 a $10 call would cap a warrant's value at its table shares.")
ta, tb = F(fact["tranche_a_count"]), F(fact["tranche_b_count"])
need(f"The prospectus says StablecoinX cannot call the {comma(ta + tb)} warrants it issued privately to TLGY's former sponsors on "
     f"August 21, 2026, {comma(ta)} at $11.50 and {comma(tb)} at $15.00")
need("so the filings leave open what a $10 call below that level would mean for them.")

# ---------------------------------------------------------------- the price test, EDGAR and the share count
assert len(ses) == qual == 16
need(f"USDE closed at ${rnd(close[first10], 2)} on {md(first10)} and at or above $10 at every session after it, {qual} sessions "
     "to October 9.")
hi = max(CAL, key=lambda d: high[d])
need(f"USDE traded as high as ${rnd(high[hi], 2)} on {md(hi)} but closed at ${rnd(close[hi], 2)}")
latest = max(r["filing_date"] for r in filings)
n_latest = sum(r["filing_date"] == latest for r in filings)
assert all(r["form"] == "4" for r in filings if r["filing_date"] == latest)
own = sorted({(r["filing_date"], r["form"]) for r in filings if r["form"] not in ("3", "4")})[-2:]
assert own == [("2026-09-17", "424B3"), ("2026-09-17", "8-K")]
need(f"EDGAR, the SEC's filing system, listed no filing under StablecoinX's name after "
     f"{['', 'one', 'two', 'three', 'four', 'five'][n_latest]} Form 4 ownership reports by its directors on October 2.")
need("The company's own latest filings were a current report on Form 8-K and a prospectus supplement on September 17.")
out_w = F(fact["public_warrants_outstanding"])
conv = out_w * res[o9]["shares"]
need(f"the make-whole table gave {rnd(res[o9]['shares'], 4)} of a share per warrant.")
need(f"counted {comma(out_w)} public warrants outstanding after the business combination.")
need(f"would add about {rnd(conv / 1_000_000, 2)} million Class A shares")
need(f"## A $10 call would add about {rnd(conv / 1_000_000, 1)} million shares")
ca, cd = F(fact["class_a_outstanding_aug28"]), F(fact["dataset_class_a_oct8"])
assert rnd(conv / ca * 100, 1) == rnd(conv / cd * 100, 1)
need(f"That is {rnd(conv / ca * 100, 1)}% of the {comma(ca)} Class A shares the prospectus counted on August 28, and also "
     f"{rnd(conv / cd * 100, 1)}% of the {comma(cd)} in the site's dataset")
need(f"Paying $11.50 for every warrant would instead add about {rnd(out_w / 1_000_000, 1)} million shares and "
     f"${rnd(out_w * STRIKE / 1_000_000, 0)} million")
need(f"At the ${rnd(close[o9], 2)} close, paying $11.50 was worth ${rnd(close[o9] - STRIKE, 2)} a warrant against "
     f"${rnd(res[o9]['value'], 2)} in table shares.")

# ---------------------------------------------------------------- method, sensitivity and limits
assert fact["usdew_first_trading_day"] == "2026-06-26"
need("The current report of July 2 dates the first trading of both to June 26.")
need(f"the two series shared {len(BOTH)} sessions from then to October 9.")
need("The source showed no USDEW row for July 17 or August 18.")
need(f"The prospectus cover gives September 8 closes of ${fact['prospectus_close_usde_sep8']} and ${fact['prospectus_close_usdew_sep8']}")
need(f"the 57-month row falls on {md(row_date(57))}, 2026 and the 54-month row on {md(row_date(54))}, 2026")
need(f"For an October 9 notice that gives {rnd(res[o9]['months'], 2)} months.")
g60 = [gap_at(o8, 60), gap_at(o9, 60)]
g90 = [gap_at(o8, 90), gap_at(o9, 90)]
assert rnd(g60[0] * 100, 1) in ("0.0", "-0.0")
need(f"With 60 days the gaps on October 8 and 9 were about 0% and {signed_pct(g60[1])}, and with 90 days "
     f"{signed_pct(g90[0])} and {signed_pct(g90[1])}.")
worst = min(-gap_at(d, k) for d in mid for k in (60, 90))
assert worst >= F(25, 1000)
need("From September 21 to October 7 USDEW stayed at least 2.5% below its call value under either.")


def implied(d, raw):
    ds = sorted(raw)
    i = ds.index(d)
    fwd = F(raw[ds[i - 1]]["close"]) * (1 + F(raw[d]["change_pct"]) / 100)
    back = F(raw[ds[i + 1]]["close"]) / (1 + F(raw[ds[i + 1]]["change_pct"]) / 100)
    return fwd, back


wraw = {date.fromisoformat(r["date"]): r for r in rows("usdew_daily_stockanalysis_2026-10-09.csv")}
for d, v in HALF.items():
    assert all(abs(x - v) < F(1, 1000) for x in implied(d, wraw))
widen = [HALF[d] / res[d]["value"] - wclose[d] / res[d]["value"] for d in HALF]
assert all(F(5, 10000) < -w < F(15, 10000) for w in widen)
need("its daily changes implied USDEW closes of $6.015 on September 25, $5.165 on September 30 and $3.885 on October 8, which "
     "would widen those gaps by about 0.1 percentage point.")
need(f"= {rnd(close[o9], 2)} − 11.50 = ${rnd(close[o9] - STRIKE, 2)} on October 9")
need(f"= {rnd(res[o9]['shares'], 4)} at ${rnd(close[o9], 2)} and {rnd(res[o9]['months'], 2)} months to expiry, October 9")
need(f"= {rnd(res[o9]['shares'], 4)} × {rnd(close[o9], 2)} = ${rnd(res[o9]['value'], 2)}")
need(f"= {rnd(wclose[o9], 2)} ÷ {rnd(res[o9]['value'], 3)} − 1 = {signed_pct(res[o9]['gap'])}")

# ---------------------------------------------------------------- headings, title, cutoff and closing line
for h in ("# How were StablecoinX's USDEW warrants priced through October 9, 2026?",
          "## USDEW closed below its call value from September 21 to October 7", "## How a $10 call would work",
          "## The price test had not been met by October 9", "## How the figures were built",
          "## What these figures leave out", "## Reproduce the numbers"):
    need(h, ARTICLE)
need("USDEW Warrant Pricing and the $10 Call: October 9, 2026", META["title"])
need("How were StablecoinX's USDEW warrants priced through October 9, 2026?", META["headline"])
need("Analysis of public market data. Not investment advice.", ARTICLE)
need("Prices through the October 9, 2026 close · Sources read October 9 to 10, 2026 UTC", ARTICLE)
if LAYOUT is not None:
    need("Prices through the October 9, 2026 close · Sources read October 9 to 10, 2026 UTC", LAYOUT["cutoff"])

print(f"{found} phrases found")
if missing:
    print("MISSING:")
    for m in missing:
        print("  " + m)
    sys.exit(1)
