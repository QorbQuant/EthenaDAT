#!/usr/bin/env python3
"""
Recomputes every computed figure in article_draft.md, metadata.json and the chart's text from
the files in inputs/, with code written apart from stablecoinx_short_interest_review.py, and
confirms that each exact phrase appears. Exits with an error if a phrase is missing or an
assertion fails, so rerun it after any edit. Python 3 standard library only. No network.
"""
import csv
import json
import statistics
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from itertools import product
from pathlib import Path

HERE = Path(__file__).parent
INP = HERE / "inputs"
ARTICLE = (HERE / "article_draft.md").read_text()
META = json.loads((HERE / "metadata.json").read_text())
SVG = (HERE / "out" / "chart_short_interest.svg").read_text()
TEXT = ARTICLE + "\n" + META["description"] + "\n" + META["imageAlt"] + "\n" + META["title"] + "\n" + SVG


def rows(name):
    with open(INP / name, newline="") as f:
        return list(csv.DictReader(f))


def md(d):
    return f"{d:%B} {d.day}"


found, missing = 0, []


def need(phrase, where=TEXT):
    global found
    if phrase in where:
        found += 1
    else:
        missing.append(phrase)


# ---------------------------------------------------------------- calendar
# NYSE and Nasdaq holidays between June and October 2026: Juneteenth on Friday June 19, Independence
# Day observed on Friday July 3, Labor Day on Monday September 7.
HOLIDAYS = {date(2026, 6, 19), date(2026, 7, 3), date(2026, 9, 7)}


def trading_days(a, b):
    out, d = [], a
    while d <= b:
        if d.weekday() < 5 and d not in HOLIDAYS:
            out.append(d)
        d += timedelta(days=1)
    return out


SESSIONS = trading_days(date(2026, 6, 26), date(2026, 10, 8))
assert len(SESSIONS) == 73

# ---------------------------------------------------------------- inputs
facts = {r["key"]: r["value"] for r in rows("filing_facts.csv")}
FT, CA = int(facts["freely_tradable_aug28"]), int(facts["class_a_outstanding_aug28"])
WARRANTS, ETHENA = int(facts["public_warrants"]), int(facts["ethena_registered_class_a_aug28"])
assert facts["resale_registration_effective"] == "2026-09-14T16:00"

spg = {date.fromisoformat(r["date"]): r for r in rows("usde_daily_spglobal_stockanalysis.csv")}
assert sorted(d for d in spg if d >= date(2026, 6, 26)) == SESSIONS
close = {d: float(spg[d]["close"]) for d in spg}
low = {d: float(spg[d]["low"]) for d in spg}
vol = {d: int(spg[d]["volume"]) for d in spg}
before = max(d for d in spg if d < SESSIONS[0])
assert before == date(2026, 6, 25) and vol[before] == 145
prior = dict(zip(SESSIONS, [before] + SESSIONS[:-1]))

fin, finw = {}, {}
for r in rows("finra_daily_short_volume.csv"):
    d = datetime.strptime(r["date"], "%Y%m%d").date()
    target = fin if r["symbol"] == "USDE" else finw
    assert d not in target
    target[d] = (float(r["short_volume"]), float(r["short_exempt_volume"]), float(r["total_volume"]))
assert sorted(fin) == SESSIONS
# short volume includes short exempt volume: in some rows the two together exceed the total
assert sum(s + e > t + 1e-6 for s, e, t in list(fin.values()) + list(finw.values())) > 0

si = {r["settlementDate"]: r for r in json.loads((INP / "finra_short_interest_usde.json").read_text())}
siw = {r["settlementDate"]: r for r in json.loads((INP / "finra_short_interest_usdew.json").read_text())}
SETTLE = [date.fromisoformat(k) for k in sorted(si)]
Q = {d: si[str(d)]["currentShortPositionQuantity"] for d in SETTLE}
LASTS = SETTLE[-1]
fetched = rows("finra_short_interest_fetch_log.csv")
assert all(r["fetched_at"].startswith("2026-10-09") for r in fetched)
rechecks = rows("finra_recheck_log.csv")
last_check = datetime.fromisoformat(rechecks[-1]["checked_at_utc"].replace("Z", "+00:00"))
assert all(not r["latest_settlement_date"] or r["latest_settlement_date"] <= str(LASTS) for r in rechecks)
assert rechecks[-1]["latest_settlement_date"] == str(LASTS)
CHECK = f"{last_check:%H:%M} UTC"

# FINRA's schedule, as read from its Short Interest Reporting Deadlines page: publication on the seventh
# business day after the settlement date.
SCHEDULE = {date(2026, 6, 30): date(2026, 7, 10), date(2026, 7, 15): date(2026, 7, 24), date(2026, 7, 31): date(2026, 8, 11),
            date(2026, 8, 14): date(2026, 8, 25), date(2026, 8, 31): date(2026, 9, 10), date(2026, 9, 15): date(2026, 9, 24),
            date(2026, 9, 30): date(2026, 10, 9)}


def seventh_business_day(s):
    d, n = s, 0
    while n < 7:
        d += timedelta(days=1)
        if d.weekday() < 5 and d not in HOLIDAYS:
            n += 1
    return d


assert all(seventh_business_day(s) == p for s, p in SCHEDULE.items())
assert SETTLE == sorted(SCHEDULE)[:len(SETTLE)]
assert SCHEDULE[LASTS] == date(2026, 10, 9)

# cycles, from the session after one settlement date to the next, and the trade windows, from the earlier
# settlement date through the session before the later one, since trades settle one business day later
cyc, win = {}, {}
start, prev_settle = SESSIONS[0], date(2026, 6, 15)
for s in SETTLE:
    cyc[s] = [d for d in SESSIONS if start <= d <= s]
    win[s] = [d for d in SESSIONS if prev_settle <= d < s]
    start, prev_settle = SESSIONS[SESSIONS.index(s) + 1], s
adv = {s: sum(vol[d] for d in cyc[s]) / len(cyc[s]) for s in SETTLE}
dtc = {s: Q[s] / adv[s] for s in SETTLE}

# ---------------------------------------------------------------- byline, title and lead
s15, a14, a31 = Q[date(2026, 9, 15)], Q[date(2026, 8, 14)], Q[date(2026, 8, 31)]
latest = Q[LASTS]
assert LASTS == date(2026, 9, 30)
need("Short interest through the September 30, 2026 settlement date")
need("Trading from June 26 through the October 8 close")
need("Sources read October 9, 2026 UTC")
need("# How much StablecoinX stock was sold short in September 2026?")
need("USDE Short Interest in September 2026: How Much Was Shorted", META["title"])
need(f"Short sellers held {latest:,} shares of USDE")
need(f"on {md(LASTS)}, 2026, the latest settlement date in FINRA's data when this review last checked it, at {CHECK} on "
     "October 9.")
need(f"That was {latest / FT * 100:.1f}% of the roughly {FT / 1e6:.2f} million Class A shares that the company's resale "
     "prospectus counted as freely tradable on August 28")
need(f"Short interest rose by {latest - s15:,} shares, or {(latest / s15 - 1) * 100:.1f}%, from September 15.")
need("A short sale counts once it has settled, one business day after the trade.")
assert len(cyc[LASTS]) == 11
need(f"In the 11 sessions to September 30 the stock traded an average of {adv[LASTS] / 1e6:.2f} million shares "
     f"a day, so short sellers held {dtc[LASTS]:.2f} days of volume, a ratio called days to cover.")
total_vol = sum(vol[d] for d in SESSIONS)
assert round(total_vol / FT) == 20
need(f"From its first session on June 26 to October 8, USDE traded {total_vol / 1e6:.1f} million shares, 20 times its freely "
     "tradable shares.")
fin_total = sum(v[2] for v in fin.values())
fin_short = sum(v[0] for v in fin.values())
fin_exempt = sum(v[1] for v in fin.values())
need(f"Of the {fin_total / 1e6:.1f} million USDE shares traded in regular hours and reported to FINRA's trade reporting "
     f"facilities, the systems that record trades made away from exchanges, {fin_short / fin_total * 100:.1f}% were marked "
     "short.")
need(f"so the {fin_short / fin_total * 100:.1f}% measures trading.")
peak = max(SESSIONS, key=lambda d: close[d])
assert peak < LASTS
need(f"USDE closed at ${close[date(2026, 9, 15)]:.2f} on September 15, reached a peak close of ${close[peak]:.2f} on "
     f"{md(peak)} and finished September at ${close[LASTS]:.2f}.")
need("FINRA's September 30 figures, published on October 9, show that aggregate short interest increased across that period.")
need("FINRA publishes the totals on the seventh business day after each settlement date.")
need(f"Its [short interest data](https://www.finra.org/finra-data/browse-catalog/equity-short-interest) for USDE starts at "
     f"{md(SETTLE[0])}, the first settlement date after the stock's first session.")

# ---------------------------------------------------------------- the short interest table
prevq = 0
for s in SETTLE:
    q = Q[s]
    chg = q - prevq
    sign = "+" if chg >= 0 else "−"
    need(f"| {md(s)} | {q:,} | {sign}{abs(chg):,} | {q / FT * 100:.2f}% | ${close[s]:.2f} | {dtc[s]:.2f} |")
    assert si[str(s)]["changePreviousNumber"] == chg and si[str(s)]["previousShortPositionQuantity"] == prevq
    prevq = q
need(f"This review divides by the prospectus's approximate count of {FT:,} freely tradable shares on August 28 at every date.")
need(f"also registered for sale the {ETHENA:,} Class A shares of Ethena OpCo Ltd")
need(f"Against those and the freely tradable shares, {FT + ETHENA:,} in all, the September 30 short interest came to "
     f"{latest / (FT + ETHENA) * 100:.2f}%.")
need(f"Against all {CA:,} Class A shares it came to {latest / CA * 100:.2f}%.")
need(f"At the ${close[LASTS]:.2f} close it was worth ${latest * close[LASTS] / 1e6:.2f} million.")

# chart text and image descriptions
words = {6: "six", 7: "seven"}
lowest = min(SESSIONS, key=lambda d: close[d])
alt = (f"USDE closed at ${close[SESSIONS[0]]:.2f} on {md(SESSIONS[0])}, fell to a low close of ${close[lowest]:.2f} on "
       f"{md(lowest)} and rose to ${close[peak]:.2f} on {md(peak)} before closing at ${close[SESSIONS[-1]]:.2f} on "
       f"{md(SESSIONS[-1])}. Short interest at the {words[len(SETTLE)]} settlement dates was "
       + ", ".join(f"{Q[s]:,}" for s in SETTLE[:-1]) + f" and {Q[LASTS]:,} shares.")
need(alt, ARTICLE)
need(alt, SVG)
need(f"USDE short interest reached {latest / 1e6:.2f} million shares on {md(LASTS)}", SVG)
need(f"when checked at {CHECK} on October 9.", SVG)
need(f"FINRA short interest at {words[len(SETTLE)]} settlement dates, from {Q[SETTLE[0]]:,} shares on {md(SETTLE[0])} to "
     f"{latest:,} on {md(LASTS)}.", META["imageAlt"])
need(f"Short sellers held {latest / 1e6:.2f} million USDE shares on {md(LASTS)}, 2026, {latest / FT * 100:.1f}% of the stock "
     "StablecoinX's prospectus counted as freely tradable in August.", META["description"])
assert len(META["description"]) <= 160 and len(META["title"]) <= 60
need(f"## Short interest reached {latest / 1e6:.2f} million shares on {md(LASTS)}")

rise = a31 - a14
assert rise > (s15 - a14) / 2
need(f"when short interest grew by {rise:,} shares and USDE's close rose from ${close[date(2026, 8, 14)]:.2f} to "
     f"${close[date(2026, 8, 31)]:.2f}.")
w15 = siw[str(LASTS)]["currentShortPositionQuantity"]
need(f"was {w15:,} warrants on {md(LASTS)}, {w15 / WARRANTS * 100:.2f}% of the {WARRANTS / 1e6:.1f} million public warrants.")

# ---------------------------------------------------------------- days to cover
assert all(si[str(s)]["daysToCoverQuantity"] == 1 for s in SETTLE)
need("FINRA listed days to cover as 1 for every date, the value its data shows for anything at or below one day.")
assert max(dtc.values()) < 0.5
need("USDE's short interest never reached half a day's trading.")
need("## Short sellers held less than half a day's volume")
ratio = {s: si[str(s)]["averageDailyVolumeQuantity"] / adv[s] for s in SETTLE}
assert all(abs(ratio[s] - 1) < 0.04 for s in SETTLE[1:]) and abs(ratio[SETTLE[0]] - 1) > 0.5
need("FINRA's own average daily volume came within 4% of S&P Global's in every cycle but the first.")
first_cycle = trading_days(date(2026, 6, 16), date(2026, 6, 30))
traded = [d for d in first_cycle if d >= SESSIONS[0]]
assert len(first_cycle) == 10 and len(traded) == 3
fadv = si["2026-06-30"]["averageDailyVolumeQuantity"]
assert abs(fadv * len(first_cycle) / sum(vol[d] for d in traded) - 1) < 0.04
need("FINRA averages over every trading day in a cycle, and USDE traded on three of the ten in its first.")
need(f"Trading was heavy for a stock with {FT / 1e6:.2f} million freely tradable shares.")
busiest = max(SESSIONS, key=lambda d: vol[d])
move = close[busiest] / close[prior[busiest]] - 1
need(f"On {md(busiest)} alone USDE traded {vol[busiest] / 1e6:.1f} million shares, {vol[busiest] / FT:.1f} times the freely "
     f"tradable shares, as its close rose {move * 100:.0f}% from ${close[prior[busiest]]:.2f} to ${close[busiest]:.2f}.")
ca31 = cyc[date(2026, 8, 31)]
assert busiest in ca31 and len(ca31) == 11
adv31x = (sum(vol[d] for d in ca31) - vol[busiest]) / (len(ca31) - 1)
need(f"lifted the average for the cycle to August 31 to {adv[date(2026, 8, 31)] / 1e6:.1f} million shares a day, which is why "
     f"days to cover on that date was {dtc[date(2026, 8, 31)]:.2f}.")
need(f"Without it the cycle averaged {adv31x / 1e6:.2f} million shares a day, and days to cover would have been "
     f"{a31 / adv31x:.2f}.")

# ---------------------------------------------------------------- daily short sale volume
need(f"For USDE the files covered {fin_total / 1e6:.1f} million shares over the 73 sessions, {fin_total / total_vol * 100:.1f}% "
     f"of the {total_vol / 1e6:.1f} million shares in S&P Global's daily volume.")
share = {d: fin[d][0] / fin[d][2] for d in SESSIONS}
lo, hi = min(share, key=share.get), max(share, key=share.get)
need(f"| Shares traded, regular hours, reported to FINRA | {fin_total:,.0f} |")
need(f"| Of which marked short | {fin_short:,.0f} |")
need(f"| Short volume marked short exempt | {fin_exempt:,.0f} |")
need(f"| Share marked short | {fin_short / fin_total * 100:.1f}% |")
need(f"| Median session | {statistics.median(share.values()) * 100:.1f}% |")
need(f"| Lowest session | {share[lo] * 100:.1f}%, on {md(lo)} |")
need(f"| Highest session | {share[hi] * 100:.1f}%, on {md(hi)} |")
need(f"| Sessions over half | {sum(v > 0.5 for v in share.values())} of 73 |")
w31, w15w = win[date(2026, 8, 31)], win[date(2026, 9, 15)]
assert (w31[0], w31[-1], len(w31)) == (date(2026, 8, 14), date(2026, 8, 28), 11)
assert (w15w[0], w15w[-1], len(w15w)) == (date(2026, 8, 31), date(2026, 9, 14), 10)
need(f"In the 11 sessions from August 14 to 28, whose trades settled by August 31, the files counted "
     f"{sum(fin[d][0] for d in w31) / 1e6:.1f} million shares marked short, while short interest rose by {rise / 1e6:.2f} million.")
need(f"In the ten sessions from August 31 to September 14 they counted {sum(fin[d][0] for d in w15w) / 1e6:.1f} million, while "
     f"short interest rose by {s15 - a31:,}.")

# ---------------------------------------------------------------- the price test
trig = {d: low[d] <= 0.9 * close[prior[d]] for d in SESSIONS}
on = {d: trig[d] or (i > 0 and trig[SESSIONS[i - 1]]) for i, d in enumerate(SESSIONS)}
n_trig, n_on = sum(trig.values()), sum(on.values())
trig2 = dict(trig)
trig2[SESSIONS[0]] = False
on2 = {d: trig2[d] or (i > 0 and trig2[SESSIONS[i - 1]]) for i, d in enumerate(SESSIONS)}
ex_on = sum(fin[d][1] for d in SESSIONS if on[d])
off = [d for d in SESSIONS if not on[d]]
top = max(SESSIONS, key=lambda d: fin[d][1])
assert on[top]
need(f"USDE fell 10% or more below its prior close on {n_trig} of its 73 sessions, implying the test would have applied on {n_on}, or "
     f"{sum(on2.values())} if no prior close applied on June 26.")
need(f"Those {n_on} sessions carried {ex_on / fin_exempt * 100:.1f}% of the {fin_exempt / 1e6:.2f} million shares that FINRA's "
     f"files counted as short exempt, and {md(top)} alone carried {fin[top][1] / fin_exempt * 100:.1f}%.")
need(f"the other {(1 - ex_on / fin_exempt) * 100:.1f}% came on {sum(fin[d][1] > 0 for d in off)} of the {len(off)} sessions "
     "without it.")
need(f"S&P Global's history for USDE includes a ${close[before]:.2f} close on June 25 on {vol[before]} shares, the day before "
     "USDE's first session")
assert min(n_on, sum(on2.values())) > 73 / 2
need("## Daily prices suggest the short sale price test covered more than half of USDE's sessions")

# S&P Global's daily low against Yahoo's hourly bars inside 9:30 am to 4 pm New York time (13:30 to 20:00 UTC)
reg = {}
for r in rows("usde_hourly_yahoo.csv"):
    t = datetime.fromtimestamp(int(r["t"]), timezone.utc)
    if r["low"] and (t.hour, t.minute) >= (13, 30) and t.hour < 20:
        reg.setdefault(t.date(), []).append(float(r["low"]))
assert len(reg) == 31 and min(reg) == date(2026, 8, 26)
gaps = [round(low[d] - round(min(v), 4), 4) for d, v in reg.items()]
assert max(abs(g) for g in gaps) <= 0.01 + 1e-9 and sum(g <= -0.01 + 1e-9 for g in gaps) == 4
need("For the 31 sessions from August 26 each was within a cent of the lowest regular-session price in Yahoo Finance's "
     "hourly data, and earlier sessions had no second source.")
opts = []
for d in SESSIONS:
    lo_, pc = Decimal(str(low[d])), Decimal(str(close[prior[d]]))
    opts.append(sorted({lo_ + k <= Decimal("0.9") * pc for k in (Decimal("-0.01"), Decimal("0"), Decimal("0.01"))}))
var = [i for i, o in enumerate(opts) if len(o) > 1]
assert [SESSIONS[i] for i in var] == [date(2026, 8, 10)]
cnts = set()
for combo in product(*[opts[i] for i in var]):
    tt = [trig[d] for d in SESSIONS]
    for i, v in zip(var, combo):
        tt[i] = v
    cnts.add(sum(1 for i in range(73) if tt[i] or (i > 0 and tt[i - 1])))
assert min(cnts) == n_on and max(cnts) - n_on == 1
need("Moving any session's low by a cent would add at most one session to the count.")

# ---------------------------------------------------------------- limits, revision flags and the formula block
assert all(si[k]["revisionFlag"] is None for k in si) and all(siw[k]["revisionFlag"] is None for k in siw)
need("The September 30 figures were published on October 9 and are the latest settlement snapshot included here.")
need(f"None of the {words[len(SETTLE)]} records read flagged one.")
need(f"so the {fin_total / total_vol * 100:.1f}% ratio is not a measure of all off-exchange trading in USDE.")
need(f"= {latest:,} ÷ {FT:,} = {latest / FT * 100:.2f}% on {md(LASTS)}")
need(f"= {latest:,} ÷ {adv[LASTS]:,.0f} = {dtc[LASTS]:.2f}")
need(f"= {fin_short:,.0f} ÷ {fin_total:,.0f} = {fin_short / fin_total * 100:.1f}%")

print(f"{found} phrases found")
if missing:
    print("MISSING:")
    for m in missing:
        print("  " + m)
    sys.exit(1)
