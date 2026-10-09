#!/usr/bin/env python3
"""
Recomputes every computed figure in article_draft.md, metadata.json and the chart's text from
the files in inputs/, with code written apart from usde_ena_tracking_review.py, and confirms
that each exact phrase appears. Exits with an error if a phrase is missing or an assertion
fails, so rerun it after any edit. Python 3 standard library only. No network.
"""
import csv
import json
import math
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal, getcontext
from pathlib import Path

HERE = Path(__file__).parent
INP = HERE / "inputs"
ARTICLE = (HERE / "article_draft.md").read_text()
META = json.loads((HERE / "metadata.json").read_text())
# layout.json is part of the site build and not of the download, so its cutoff is checked only when present
LAYOUT = json.loads((HERE / "layout.json").read_text()) if (HERE / "layout.json").exists() else None
SVG = (HERE / "out" / "chart_usde_ena.svg").read_text()
TEXT = ARTICLE + "\n" + META["description"] + "\n" + META["imageAlt"] + "\n" + META["title"] + "\n" + SVG


def rows(name):
    with open(INP / name, newline="") as f:
        return list(csv.DictReader(f))


def md(d):
    return f"{d:%B} {d.day}"


def short(d):
    return f"{d:%b} {d.day}"


found, missing = 0, []


def need(phrase, where=TEXT):
    global found
    if phrase in where:
        found += 1
    else:
        missing.append(phrase)


def p1(x):
    return f"{x * 100:.1f}%"


def p0(x):
    return f"{x * 100:.0f}%"


def f2(x):
    return f"{x:.2f}".replace("-", "−")


# ---------------------------------------------------------------- calendar
# Nasdaq holidays in the window: Independence Day observed on Friday July 3, Labor Day on Monday
# September 7. US daylight saving time in 2026 ran from March 8 to November 1.
HOLIDAYS = {date(2026, 7, 3), date(2026, 9, 7)}
SESSIONS = []
d = date(2026, 6, 26)
while d <= date(2026, 10, 8):
    if d.weekday() < 5 and d not in HOLIDAYS:
        SESSIONS.append(d)
    d += timedelta(days=1)
assert len(SESSIONS) == 73
assert all(date(2026, 3, 8) < s < date(2026, 11, 1) for s in SESSIONS)
FIRST, LAST = SESSIONS[0], SESSIONS[-1]
PAIRS = [(SESSIONS[i - 1], SESSIONS[i]) for i in range(1, len(SESSIONS))]
N = len(PAIRS)
assert N == 72


def at(day, hh, mm=0):
    return datetime(day.year, day.month, day.day, hh, mm, tzinfo=timezone.utc)


# ---------------------------------------------------------------- inputs
spg = {date.fromisoformat(r["date"]): r for r in rows("usde_daily_spglobal_stockanalysis.csv")}
assert [x for x in sorted(spg) if x >= FIRST] == SESSIONS
CLOSE = {x: float(spg[x]["close"]) for x in SESSIONS}
OPEN = {x: float(spg[x]["open"]) for x in SESSIONS}

# Kraken: index every 4-hour candle by the moment it ends, start plus 240 minutes
kraken_end = {}
for r in rows("kraken_enausd_4h_20utc_00utc.csv"):
    start = datetime.fromtimestamp(int(r["start_unix"]), timezone.utc)
    kraken_end[start + timedelta(hours=4)] = float(r["close"])
K4 = {x: kraken_end[at(x, 20)] for x in SESSIONS}                 # the close, 20:00 UTC
K0 = {x: kraken_end[at(x, 0)] for x in SESSIONS}                  # midnight UTC at the start of the date
klog = rows("kraken_fetch_log.csv")
assert len(klog) == 1 and klog[0]["status"] == "200" and klog[0]["fetched_at"].startswith("2026-10-09")

cg = {}
for r in rows("ena_coingecko_via_defillama.csv"):
    target = datetime.fromtimestamp(int(r["target_unix"]), timezone.utc)
    cg[target] = (float(r["price_usd"]), int(r["price_unix"]) - int(r["target_unix"]))
CG4 = {x: cg[at(x, 20)][0] for x in SESSIONS}
CGO = {x: cg[at(x, 13, 30)][0] for x in SESSIONS}
assert max(abs(cg[at(x, 20)][1]) for x in SESSIONS) <= 120          # at most two minutes from 20:00 UTC
assert max(abs(cg[at(x, 13, 30)][1]) for x in SESSIONS) <= 120
llog = rows("defillama_fetch_log.csv")
assert len(llog) == 2 and all(r["status"] == "200" and r["fetched_at"].startswith("2026-10-09") for r in llog)

dash = {date.fromisoformat(r["date"]): r for r in rows("dashboard_series_152e758.csv")}
DENA = {x: float(dash[x]["ena_price"]) for x in SESSIONS}
SHARES = {x: int(dash[x]["shares_outstanding"]) for x in SESSIONS}
DMNAV = {x: float(dash[x]["mnav"]) for x in SESSIONS}
facts = {r["key"]: r for r in rows("filing_facts.csv")}
HELD = int(facts["ena_held_dashboard"]["value"])
TENQ = int(facts["ena_received_10q_sum"]["value"])
assert HELD == 3_029_000_000 and all(int(dash[x]["ena_holdings"]) == HELD for x in SESSIONS)
assert "about 3,029 million ENA" in facts["ena_held_dashboard"]["location"]
assert TENQ == round(284_954_407.29 + 1_405_754_435.84 + 1_340_695_577.81)
assert date.fromisoformat(facts["first_trading_day"]["value"]) == FIRST
assert all(abs(float(dash[x]["usde_close"]) - CLOSE[x]) < 0.005 for x in SESSIONS)

src = rows("sources.csv")
sp_row = [r for r in src if r["source"] == "stockanalysis"]
assert sp_row and sp_row[0]["read_at_utc"].startswith("2026-10-09")
read_days = {r["read_at_utc"][:10] for r in src}
assert min(read_days) == "2026-10-06" and max(read_days) == "2026-10-09"
assert any("CoinGecko" in r["used_for"] and "methodology" in r["address"] for r in src)
assert any(r["document"].startswith("docs/data.json at commit 152e758") and "2026-10-09" in r["as_of"] for r in src)


# ---------------------------------------------------------------- statistics, computational formulas
def summary(x, y):
    n = len(x)
    sx, sy = sum(x), sum(y)
    sxx, syy, sxy = sum(a * a for a in x), sum(b * b for b in y), sum(a * b for a, b in zip(x, y))
    cov = n * sxy - sx * sy
    vx, vy = n * sxx - sx * sx, n * syy - sy * sy
    return {"n": n, "r": cov / math.sqrt(vx * vy), "slope": cov / vx,
            "same": sum(1 for a, b in zip(x, y) if (a > 0 and b > 0) or (a < 0 and b < 0)),
            "opp": sum(1 for a, b in zip(x, y) if (a > 0 > b) or (a < 0 < b)),
            "zero": sum(1 for a, b in zip(x, y) if a == 0 or b == 0),
            "sdx": math.sqrt(vx / (n * (n - 1))), "sdy": math.sqrt(vy / (n * (n - 1)))}


def avg_ranks(v):
    pos = {}
    for i, val in enumerate(sorted(v)):
        pos.setdefault(val, []).append(i + 1)
    return [sum(pos[val]) / len(pos[val]) for val in v]


def rank_r(x, y):
    return summary(avg_ranks(x), avg_ranks(y))["r"]


def ret(series, a, b):
    return series[b] / series[a] - 1


U = {b: ret(CLOSE, a, b) for a, b in PAIRS}
E = {b: ret(K4, a, b) for a, b in PAIRS}
days = [b for _, b in PAIRS]
daily = summary([E[b] for b in days], [U[b] for b in days])
cgd = summary([ret(CG4, a, b) for a, b in PAIRS], [U[b] for b in days])
dsh = summary([ret(DENA, a, b) for a, b in PAIRS], [U[b] for b in days])
MNAV = {x: CLOSE[x] / (K4[x] * HELD / SHARES[x]) for x in SESSIONS}
lo = min(SESSIONS, key=MNAV.get)
hi = max(SESSIONS, key=MNAV.get)


def mx(v):
    return f"{v:.2f}×"


# ---------------------------------------------------------------- byline, title and lead
need("Prices from June 26 through the October 8, 2026 close · Sources read October 6 to 9, 2026 UTC")
if LAYOUT:
    need(LAYOUT["cutoff"], ARTICLE)
need("# How closely has StablecoinX's stock tracked ENA?")
assert META["headline"] == "How closely has StablecoinX's stock tracked ENA?"
assert len(META["title"]) <= 60 and len(META["description"]) <= 160
need("USDE vs ENA: How Closely StablecoinX Stock Has Tracked ENA", META["title"])
need(f"on {daily['same']} of the {N} trading days that followed its first session on {md(FIRST)}, 2026, through {md(LAST)}.")
need(f"a measure from −1 to 1 of how closely two series move in step, was {daily['r']:.2f}.")
need(f"Its square, {daily['r'] ** 2:.2f}, is the share of the variation in USDE's daily moves that a straight line on ENA's "
     "moves accounts for.")
need(f"a measure of their typical size, of {p1(daily['sdy'])}, against {p1(daily['sdx'])} for ENA.")
need(f"USDE moved {daily['slope']:.2f}% for each 1% move in ENA.")
top3 = sorted(days, key=lambda b: abs(U[b]), reverse=True)[:3]
rest = [b for b in days if b not in top3]
wo = summary([E[b] for b in rest], [U[b] for b in rest])
need(f"Without USDE's three largest moves, on {md(top3[0])}, {md(top3[1])} and {md(top3[2])}, the fitted slope was "
     f"{wo['slope']:.2f} and the correlation {wo['r']:.2f}.")
need(f"From {md(FIRST)} to {md(LAST)} USDE rose {p1(ret(CLOSE, FIRST, LAST))}, from ${CLOSE[FIRST]:.2f} to ${CLOSE[LAST]:.2f}, "
     f"while ENA's price at the close rose {p1(ret(K4, FIRST, LAST))}, from ${K4[FIRST]:.4f} to ${K4[LAST]:.4f}.")
need(f"went from {mx(MNAV[FIRST])} to {mx(MNAV[LAST])}, after a low of {mx(MNAV[lo])} on {md(lo)} and a high of "
     f"{mx(MNAV[hi])} on {md(hi)}.")
need("This site's [StablecoinX dashboard](https://ethenadash.com/stablecoinx/), in its dataset of October 9, pairs each close")
need(f"Measured with those prices, the correlation was {dsh['r']:.2f}, and USDE moved the same way as ENA on {dsh['same']} of "
     f"{N} days.")

# ---------------------------------------------------------------- daily moves table, chart and second source
need(f"## USDE moved the same way as ENA on {daily['same']} of {N} days")
need(f"| {N} daily moves, {md(FIRST)} close to {md(LAST)} close | Value |")
need(f"| USDE moved the same way as ENA | {daily['same']} |")
need(f"| USDE moved the opposite way | {daily['opp']} |")
need(f"| Either price unchanged | {daily['zero']} |")
assert daily["same"] + daily["opp"] + daily["zero"] == N
need(f"| Correlation | {daily['r']:.2f} |")
need(f"| Share of USDE's variation accounted for by ENA's moves | {daily['r'] ** 2 * 100:.0f}% |")
need(f"| Fitted slope, USDE's move for a 1% move in ENA | {daily['slope']:.2f}% |")
need(f"| Standard deviation of USDE's daily moves | {p1(daily['sdy'])} |")
need(f"| Standard deviation of ENA's daily moves | {p1(daily['sdx'])} |")
big = max(days, key=lambda b: U[b])
assert big == top3[0]
# whole percentages, since August 21's move is exactly 85.25% and would round either way at one decimal
assert abs(U[big] - 0.8525) < 1e-12
alt = (f"Left, a scatter of USDE's {N} daily moves against ENA's, from the {md(FIRST)} close to the {md(LAST)} close, with a "
       f"fitted line of slope {daily['slope']:.2f} and a dashed line of equal moves, and {md(big)} labeled at the top, when USDE "
       f"rose {p0(U[big])} and ENA {p0(E[big])}. Right, mNAV at the 4 pm close, from {mx(MNAV[FIRST])} on {md(FIRST)} to a low "
       f"of {mx(MNAV[lo])} on {md(lo)} and a high of {mx(MNAV[hi])} on {md(hi)}, ending at {mx(MNAV[LAST])} on {md(LAST)}.")
need(alt, ARTICLE)
need(f"Two panels. Left, USDE's {N} daily moves against ENA's, from the {md(FIRST)} close to the {md(LAST)} close, with a "
     f"fitted line of slope {daily['slope']:.2f}. Right, mNAV at the 4 pm close, from {mx(MNAV[FIRST])} on {md(FIRST)} to a low "
     f"of {mx(MNAV[lo])} on {md(lo)} and a high of {mx(MNAV[hi])} on {md(hi)}.", META["imageAlt"])
need(f"StablecoinX's stock, USDE, moved the same way as ENA on {daily['same']} of {N} days to {md(LAST)}, 2026, with a "
     f"{daily['r']:.2f} correlation of daily moves at the 4 pm close.", META["description"])
need("The left panel's two axes use different scales.")
gap = sorted(abs(K4[x] / CG4[x] - 1) for x in SESSIONS)
assert gap[-1] < 0.01
med = gap[len(gap) // 2]
need("each stamped within two minutes of 20:00 UTC and read through DefiLlama's public price API, served as a second source.")
need(f"Kraken's price at the close was within 1% of CoinGecko's on every session and {med * 100:.2f}% from it on the median "
     "session.")
# chart text
need(f"USDE moved the same way as ENA on {daily['same']} of {N} days", SVG)
need(f"Daily moves from one 4 pm New York close to the next, and mNAV at each close, {md(FIRST)} to {md(LAST)}, 2026.", SVG)
need(f"Left, {N} daily moves, ENA across and USDE up, correlation {daily['r']:.2f}, fitted slope {daily['slope']:.2f}. The two "
     f"axes use different scales. Right, mNAV at the 4 pm close, {mx(MNAV[FIRST])} on {md(FIRST)}, a low of {mx(MNAV[lo])} on "
     f"{md(lo)}, a high of {mx(MNAV[hi])} on {md(hi)} and {mx(MNAV[LAST])} on {md(LAST)}.", SVG)
need(f"fitted line, slope {daily['slope']:.2f}", SVG)
need(f"{mx(MNAV[lo])} on {short(lo)}", SVG)
need(f"{mx(MNAV[hi])} on {short(hi)}", SVG)
need(f">{short(big)}</text>", SVG)
assert "-" not in "".join(t.split(">")[1] for t in SVG.split("<text")[1:] if "%" in t.split(">")[1].split("<")[0])

# hover text on every point, recomputed with exact decimal arithmetic from the input strings
getcontext().prec = 50
DCLOSE = {x: Decimal(spg[x]["close"]) for x in SESSIONS}
DK4 = {}
for r in rows("kraken_enausd_4h_20utc_00utc.csv"):
    start = datetime.fromtimestamp(int(r["start_unix"]), timezone.utc)
    if (start + timedelta(hours=4)) in {at(x, 20) for x in SESSIONS}:
        DK4[(start + timedelta(hours=4)).date()] = Decimal(r["close"])


def hover(v):
    return f"{(v * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):+}%".replace("-", "−")


for a, b in PAIRS:
    ex = DK4[b] / DK4[a] - 1
    ey = DCLOSE[b] / DCLOSE[a] - 1
    need(f"<title>{short(b)}, ENA {hover(ex)}, USDE {hover(ey)}</title>", SVG)
for x in SESSIONS:
    dm_ = DCLOSE[x] / (DK4[x] * HELD / SHARES[x])
    need(f"<title>{short(x)}, mNAV {dm_.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)}×</title>", SVG)

# ---------------------------------------------------------------- periods
PERIODS = [(date(2026, 6, 26), date(2026, 7, 31)), (date(2026, 7, 31), date(2026, 8, 31)),
           (date(2026, 8, 31), date(2026, 10, 8))]
per = []
for a0, b0 in PERIODS:
    sel = [b for a, b in PAIRS if a0 <= a and b <= b0]
    s = summary([E[b] for b in sel], [U[b] for b in sel])
    per.append((sel, s))
    need(f"| {md(a0)} to {md(b0)} | {s['n']} | {s['same']} | {s['r']:.2f} | {s['slope']:.2f} |")
assert sum(s["n"] for _, s in per) == N
need(f"| {md(FIRST)} to {md(LAST)} | {N} | {daily['same']} | {daily['r']:.2f} | {daily['slope']:.2f} |")
aug_sel, aug = per[1]
need(f"In August USDE moved the same way as ENA on only {aug['same']} of {aug['n']} days, but the month's correlation was "
     f"{aug['r']:.2f}, because USDE's two largest moves of the month went the same way as ENA's.")
two = sorted(aug_sel, key=lambda b: abs(U[b]), reverse=True)[:2]
assert all(U[b] * E[b] > 0 for b in two) and set(two) == {date(2026, 8, 21), date(2026, 8, 27)}
aug_rest = [b for b in aug_sel if b not in two]
aug2 = summary([E[b] for b in aug_rest], [U[b] for b in aug_rest])
need(f"Without August 21 and August 27 the month's correlation was {aug2['r']:.2f}.")
assert per[2][1]["r"] == max(s["r"] for _, s in per)
need(f"From the August 31 close to October 8 USDE moved the same way as ENA on {per[2][1]['same']} of {per[2][1]['n']} days.")
ns = [s["n"] for _, s in per]
pvals = []
for i in range(3):
    for j in range(i + 1, 3):
        ri, rj, ni, nj = per[i][1]["r"], per[j][1]["r"], per[i][1]["n"], per[j][1]["n"]
        z = abs(0.5 * math.log((1 + ri) / (1 - ri)) - 0.5 * math.log((1 + rj) / (1 - rj))) / math.sqrt(1 / (ni - 3) + 1 / (nj - 3))
        pvals.append(math.erfc(z / math.sqrt(2)))
assert min(pvals) > 0.05
need(f"Each period holds only {min(ns)} to {max(ns)} moves, and by the usual test for comparing correlations none of the gaps "
     "between the periods is large enough to rule out chance at the 5% level.")
need("## The link was closest from September")

# ---------------------------------------------------------------- large days and other measures
t0, t1, t2 = top3
need(f"USDE's three largest moves came on {md(t0)}, when it rose {p0(U[t0])} and ENA {p0(E[t0])}, on {md(t1)}, when it rose "
     f"{p0(U[t1])} and ENA {p0(E[t1])}, and on {md(t2)}, when it rose {p0(U[t2])} and ENA {p0(E[t2])}.")
assert all(U[b] > 0 for b in top3)
need(f"so limits the weight of large days, was {rank_r([E[b] for b in days], [U[b] for b in days]):.2f}.")
need(f"| Daily, ENA from Kraken | {daily['r']:.2f} | {daily['slope']:.2f} | {daily['same']} of {N} |")
need(f"| Daily, ENA from CoinGecko | {cgd['r']:.2f} | {cgd['slope']:.2f} | {cgd['same']} of {N} |")
need(f"| Daily, without the three largest USDE moves | {wo['r']:.2f} | {wo['slope']:.2f} | {wo['same']} of {wo['n']} |")
need("## A few large days carried the fitted slope")

# ---------------------------------------------------------------- the dashboard's midnight prices
d0 = [abs(DENA[x] / K0[x] - 1) for x in SESSIONS]
assert max(d0) < 0.005
d4 = sorted(abs(DENA[x] / K4[x] - 1) for x in SESSIONS)
need("The dashboard records one ENA price for each date, from CoinGecko according to its methodology page.")
need(f"On every session that price was within 0.5% of Kraken's price at midnight UTC, 8 pm in New York the evening before the "
     f"close, and on the median session it was {d4[len(d4) // 2] * 100:.1f}% away from ENA's price at the close.")
overlaps = set()
for a, b in PAIRS:
    if (b - a).days == 1:
        u0, u1 = at(a, 20), at(b, 20)
        e0, e1 = at(a, 0), at(b, 0)
        overlaps.add((min(u1, e1) - max(u0, e0)).total_seconds() / 3600)
assert overlaps == {4.0}
need("The two share four hours.")
need(f"Measured with the dashboard's prices, USDE moved the same way as ENA on {dsh['same']} of {N} days, the correlation was "
     f"{dsh['r']:.2f} and the fitted slope {dsh['slope']:.2f}.")
need("## Midnight prices hide most of the link")

# ---------------------------------------------------------------- the split at the open, CoinGecko at 13:30 and 20:00 UTC
gx = {b: CGO[b] / CG4[a] - 1 for a, b in PAIRS}
gy = {b: OPEN[b] / CLOSE[a] - 1 for a, b in PAIRS}
sx_ = {b: CG4[b] / CGO[b] - 1 for a, b in PAIRS}
sy_ = {b: CLOSE[b] / OPEN[b] - 1 for a, b in PAIRS}
on = summary([gx[b] for b in days], [gy[b] for b in days])
ss = summary([sx_[b] for b in days], [sy_[b] for b in days])
on_rank = rank_r([gx[b] for b in days], [gy[b] for b in days])
ss_rank = rank_r([sx_[b] for b in days], [sy_[b] for b in days])
need("## Most of ENA's movement came outside USDE's trading hours")
need("with ENA from CoinGecko at 9:30 am and 4 pm, 13:30 and 20:00 UTC.")
need(f"| Correlation | {on['r']:.2f} | {ss['r']:.2f} |")
need(f"| Rank correlation | {on_rank:.2f} | {ss_rank:.2f} |")
need(f"| Fitted slope | {on['slope']:.2f} | {ss['slope']:.2f} |")
need(f"| USDE moved the same way as ENA | {on['same']} | {ss['same']} |")
need(f"| Standard deviation of USDE's moves | {p1(on['sdy'])} | {p1(ss['sdy'])} |")
need(f"| Standard deviation of ENA's moves | {p1(on['sdx'])} | {p1(ss['sdx'])} |")
assert 1.9 < on["sdx"] / ss["sdx"] < 2.1
need("ENA's overnight moves, from the close to the next open, had twice the standard deviation of its moves during trading "
     "hours.")
assert 0.9 < on["slope"] < 1.1
need("On the fitted line USDE's opening price moved almost one for one with ENA's overnight move.")
assert 0.85 < ss["sdy"] / on["sdy"] < 1.15
need(f"During trading hours USDE moved about as much as overnight, and ENA's moves accounted for {ss['r'] ** 2 * 100:.0f}% of the "
     "variation in USDE's.")
keep = [b for b in days if b != big]
on1 = summary([gx[b] for b in keep], [gy[b] for b in keep])
ss1 = summary([sx_[b] for b in keep], [sy_[b] for b in keep])
assert f"{on1['r']:.2f}" == f"{ss1['r']:.2f}" and on_rank > ss_rank and on["r"] > ss["r"]
on1_rank = rank_r([gx[b] for b in keep], [gy[b] for b in keep])
ss1_rank = rank_r([sx_[b] for b in keep], [sy_[b] for b in keep])
need(f"Without {md(big)} both were {on1['r']:.2f}, and the rank correlations were {on1_rank:.2f} overnight and {ss1_rank:.2f} "
     "during trading hours.")
a21 = date(2026, 8, 21)
p21 = SESSIONS[SESSIONS.index(a21) - 1]
assert CG4[a21] < CGO[a21]
need(f"On {md(a21)} USDE opened {p1(gy[a21])} above the prior close after ENA rose {p1(gx[a21])} overnight, then rose another "
     f"{p1(sy_[a21])} during trading hours while ENA fell {p1(-sx_[a21])}.")
gb = max(days, key=lambda b: abs(gx[b]))
ga = SESSIONS[SESSIONS.index(gb) - 1]
assert (ga, gb) == (date(2026, 9, 18), date(2026, 9, 21)) and ga.weekday() == 4 and gb.weekday() == 0
need(f"ENA's largest overnight move came over the weekend of {md(ga + timedelta(days=1))} and {(ga + timedelta(days=2)).day}, "
     f"a rise of {p1(gx[gb])} from Friday's close to Monday's open, and USDE opened {p1(gy[gb])} above its Friday close.")

# ---------------------------------------------------------------- mNAV
window = [x for x in SESSIONS if date(2026, 7, 1) <= x <= date(2026, 8, 13)]
below = [x for x in SESSIONS if MNAV[x] < 0.25]
assert below and min(below) == window[0] and max(below) == window[-1] and all(x in window for x in below)
need(f"At the close mNAV fell from {mx(MNAV[FIRST])} on {md(FIRST)} to {mx(MNAV[lo])} on {md(lo)} and stood below 0.25× on "
     f"{len(below)} of the {len(window)} sessions from {md(window[0])} to {md(window[-1])}.")
assert lo < hi
need(f"It then rose to {mx(MNAV[hi])} on {md(hi)} and was {mx(MNAV[LAST])} on {md(LAST)}.")
mm = [ret(MNAV, a, b) for a, b in PAIRS]
mean_mm = sum(mm) / N
sd_mm = math.sqrt(sum((v - mean_mm) ** 2 for v in mm) / (N - 1))
assert sd_mm > daily["sdx"]
need(f"Its daily moves had a standard deviation of {p1(sd_mm)}, larger than ENA's {p1(daily['sdx'])}")
dm_calc = {x: CLOSE[x] / (DENA[x] * HELD / SHARES[x]) for x in SESSIONS}
assert all(abs(dm_calc[x] - DMNAV[x]) < 0.0001 for x in SESSIONS)
dhi = max(SESSIONS, key=dm_calc.get)
need(f"The dashboard's own mNAV, with its midnight ENA prices, was {mx(dm_calc[LAST])} on {md(LAST)} and peaked at "
     f"{mx(dm_calc[dhi])} on {md(dhi)}.")
changes = [(x, SHARES[x]) for i, x in enumerate(SESSIONS) if i == 0 or SHARES[x] != SHARES[SESSIONS[i - 1]]]
assert len(changes) == 2
(c0, s0), (c1, s1) = changes
need(f"These figures use the dashboard's counts, {HELD:,} ENA on every date, the company's figure from its June 25 release, and "
     f"a Class A count that rises from {s0:,} to {s1:,} on {md(c1)}.")
lower = max(MNAV[x] - CLOSE[x] / (K4[x] * TENQ / SHARES[x]) for x in SESSIONS)
assert TENQ > HELD and lower < 0.001
need("the 10-Q's slightly larger ENA figure, which would lower each mNAV here by less than 0.001.")
need("## mNAV moved more than ENA")

# ---------------------------------------------------------------- limits, reproduction and the formula block
need(f"The window holds {N} daily moves")


def fisher(r, n):
    z, se = 0.5 * math.log((1 + r) / (1 - r)), 1 / math.sqrt(n - 3)
    return math.tanh(z - 1.959964 * se), math.tanh(z + 1.959964 * se)


c1_, c2_ = fisher(daily["r"], N), fisher(dsh["r"], N)
need(f"By the standard approximation for a correlation, {N} moves leave a 95% confidence interval, the range of underlying "
     f"correlations these moves are consistent with, of about {f2(c1_[0])} to {f2(c1_[1])} around the {daily['r']:.2f}, and of "
     f"about {f2(c2_[0])} to {f2(c2_[1])} around the {dsh['r']:.2f} from the dashboard's prices.")
need("the dashboard's series comes from its dataset at commit 152e758.")
need("that Kraken's price at the close is within 1% of CoinGecko's on every session")
need(f"= {CLOSE[LAST]:.2f} ÷ ({K4[LAST]:.4f} × {HELD:,} ÷ {SHARES[LAST]:,}) = {mx(MNAV[LAST])} on {md(LAST)}")

print(f"{found} phrases found")
if missing:
    print("MISSING:")
    for m in missing:
        print("  " + m)
    sys.exit(1)
