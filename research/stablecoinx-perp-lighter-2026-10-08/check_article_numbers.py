#!/usr/bin/env python3
"""
Recomputes every computed figure in article_draft.md and metadata.json from the files in
inputs/, with code written apart from stablecoinx_perp_review.py, and confirms that each
exact phrase appears. Exits with an error if a phrase is missing, so rerun it after any edit.
Python 3 standard library only. No network.
"""
import csv
import json
import statistics
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).parent
INP = HERE / "inputs"
TEXT = (HERE / "article_draft.md").read_text() + "\n" + (HERE / "metadata.json").read_text()
Z = timezone.utc
H = timedelta(hours=1)
NYOFF = timedelta(hours=4)


def rows(name):
    return list(csv.DictReader(open(INP / name)))


def at_utc(y, m, d, h=0):
    return datetime(y, m, d, h, tzinfo=Z)


def p2(x):
    return f"{x * 100:.2f}%"


def p1(x):
    return f"{x * 100:.1f}%"


def md(d):
    return f"{d:%B} {d.day}"


# Lighter series, keyed by the hour each candle starts
mko = {datetime.fromtimestamp(int(r["t_ms"]) // 1000, Z): r for r in rows("lighter_mark_1h.csv")}
mk = {t: float(r["c"]) for t, r in mko.items()}
cd = {datetime.fromtimestamp(int(r["t_ms"]) // 1000, Z): r for r in rows("lighter_candles_1h.csv")}
fd = rows("lighter_funding_1h.csv")
snap = json.loads((INP / "lighter_orderbookdetails.json").read_text())["order_book_details"][0]
orc = json.loads((INP / "lighter_priceoracleinfo.json").read_text())["markets"][0]
facts = {r["key"]: int(r["value"]) for r in rows("filing_facts.csv")}


def mark_end(t):
    """Mark at moment t is the close of the hourly mark candle that started an hour earlier."""
    return mk[t - H]


def vol(t):
    return float(cd[t]["v"])


def usd(t):
    return float(cd[t]["V"])


# USDE prices, S&P Global through StockAnalysis
px = {date.fromisoformat(r["date"]): r for r in rows("usde_daily_spglobal_stockanalysis.csv")}
days = sorted(d for d in px if date(2026, 8, 26) <= d <= date(2026, 10, 8))
cl = {d: float(px[d]["close"]) for d in days}
op = {d: float(px[d]["open"]) for d in days}
yh = {r["new_york"]: r for r in rows("usde_hourly_yahoo.csv")}
in_session = {at_utc(d.year, d.month, d.day, h) for d in days for h in range(13, 20)}

found, missing = 0, []


def need(phrase):
    global found
    if phrase in TEXT:
        found += 1
    else:
        missing.append(phrase)


# ---- at the close
gm, gt, stale_days = [], [], []
for d in days:
    t = at_utc(d.year, d.month, d.day, 20)
    gm.append((abs(mark_end(t) / cl[d] - 1), d))
    u = t - H
    while vol(u) == 0:
        u -= H
    if u != t - H:
        stale_days.append(d)
    gt.append((abs(float(cd[u]["c"]) / cl[d] - 1), d))
need(f"ended within 1% of USDE's closing price on {sum(1 for g, _ in gm if g <= 0.01)} of the {len(days)} trading days")
need(f"was within 1% of the close on {sum(1 for g, _ in gt if g <= 0.01)} of the {len(days)} days")
need(f"| Median gap to USDE's close | {p2(statistics.median(g for g, _ in gm))} | "
     f"{p2(statistics.median(g for g, _ in gt))} |")
mx_m, mx_t = max(gm), max(gt)
need(f"| Largest gap | {p2(mx_m[0])}, on {md(mx_m[1])} | {p2(mx_t[0])}, on {md(mx_t[1])} |")
need(f"| Days within 1% | {sum(g <= 0.01 for g, _ in gm)} of 31 | {sum(g <= 0.01 for g, _ in gt)} of 31 |")
need(f"| Days within 2% | {sum(g <= 0.02 for g, _ in gm)} of 31 | {sum(g <= 0.02 for g, _ in gt)} of 31 |")
assert mx_t[1] in stale_days and mx_m[1] == days[0]
need(f"On {len(stale_days)} of the 31 days nobody traded the perp in the hour before the close, so its last trade came "
     f"from earlier in the day, as it did for the largest gap, on {md(mx_t[1])}")
need(f"ended within 1% of the close of USDE, StablecoinX's Nasdaq stock, on {sum(1 for g, _ in gm if g <= 0.01)} of 31 days "
     f"to October 8, 2026, and its last trade on {sum(1 for g, _ in gt if g <= 0.01)}")

# ---- settings at 9:30 am on October 9
cap = orc["index"]["price_cap_bps"] / 100
assert orc["index"]["median_sources"] == ["pythlazer"] and cap == 40
need(f"that distance set at {cap:.0f}%")
max_lev = 10000 // snap["default_initial_margin_fraction"]
assert max_lev == 5
need(f"read with the perp's five-times maximum leverage its formula gives {100 // max_lev}%")
need(f"initial margin of {snap['default_initial_margin_fraction'] // 100}% of a position's value, which allows leverage "
     f"of up to {['', 'one', 'two', 'three', 'four', 'five'][10000 // snap['default_initial_margin_fraction']]} times")
assert snap["taker_fee"] == "0.0000" and snap["maker_fee"] == "0.0000"
need("charged no trading fees")

# ---- hours inside and outside 9 am to 4 pm New York time on trading days
idle_in = sum(1 for t in cd if t in in_session and vol(t) == 0)
n_in = sum(1 for t in cd if t in in_session)
idle_out = sum(1 for t in cd if t not in in_session and vol(t) == 0)
n_out = sum(1 for t in cd if t not in in_session)
usd_out = sum(usd(t) for t in cd if t not in in_session)
usd_all = sum(usd(t) for t in cd)
need(f"No trade took place in {idle_out} of the {n_out} hours outside 9 am to 4 pm New York time on trading days, against "
     f"{idle_in} of the {n_in} hours inside them, yet the hours outside carried {p1(usd_out / usd_all)} of the perp's "
     f"dollar volume")
flat_out = [t for t in mko if t not in in_session and mko[t]["h"] == mko[t]["l"]]
flat_in = [t for t in mko if t in in_session and mko[t]["h"] == mko[t]["l"]]
assert len(flat_in) == 1 and sum(1 for t in mko if t not in in_session) == n_out
need(f"In {len(flat_out)} of the {n_out} hours outside 9 am to 4 pm on trading days the mark did not move at all. "
     f"Inside those hours it moved in all but one.")

# ---- stretches between sessions
st = []
for d, e in zip(days, days[1:]):
    c, o = cl[d], op[e]
    t8 = at_utc(d.year, d.month, d.day, 20) + 4 * H
    t4 = at_utc(e.year, e.month, e.day, 8)
    post = yh.get(f"{d} 19:00")
    window = [t for t in mko if t8 <= t < t4]
    trades = [t for t in cd if t8 <= t < t4]
    st.append(dict(d=d, e=e, c=c, o=o, m4p=mark_end(at_utc(d.year, d.month, d.day, 20)), m8p=mark_end(t8),
                   m4a=mark_end(t4), m9a=mark_end(at_utc(e.year, e.month, e.day, 13)),
                   pre=float(yh[f"{e} 08:00"]["close"]), post=float(post["close"]) if post and post["close"] else None,
                   gap=(e - d).days, window=window, trades=trades))
kinds = [s["gap"] for s in st]
need(f"{kinds.count(1)} weeknights, {kinds.count(3)} weekends and the Labor Day weekend")
assert kinds.count(4) == 1
for a, b, label in (("m4p", "m8p", "4 pm to 8 pm, USDE after-hours"), ("m8p", "m4a", "8 pm to 4 am, no USDE trading"),
                    ("m4a", "m9a", "4 am to 9 am, USDE pre-market")):
    mv = [abs(s[b] / s[a] - 1) for s in st]
    need(f"| {label} | {p2(statistics.median(mv))} | {sum(x > 0.02 for x in mv)} of 30 |")
# Yahoo shows no bars from 20:00 to 03:59 New York time
assert all(not ("20:00" <= k[11:] or k[11:] < "04:00") for k in yh)
eve = [abs(s["m8p"] / s["post"] - 1) for s in st if s["post"]]
mor = [abs(s["m9a"] / s["pre"] - 1) for s in st]
assert [str(s["d"]) for s in st if not s["post"]] == ["2026-10-07"]
need(f"sat a median {p2(statistics.median(eve))} from USDE's last after-hours price and within 1% of it on "
     f"{sum(x <= 0.01 for x in eve)} of {len(eve)} evenings")
need(f"sat a median {p2(statistics.median(mor))} from USDE's last pre-market price and within 1% of it on "
     f"{sum(x <= 0.01 for x in mor)} of {len(mor)} mornings")
oct7 = [k for k in yh if k.startswith("2026-10-07 ") and k[11:] >= "16:00"]
assert oct7 == ["2026-10-07 16:00"] and float(yh[oct7[0]]["high"]) == float(yh[oct7[0]]["low"]) == cl[date(2026, 10, 7)]
need(f"showed no trading after the closing print on October 7, so the evening comparison covers {len(eve)} stretches")


# swings of the mark between 8 pm and 4 am, against the prior close
def swing(s):
    hi = max(s["window"], key=lambda t: float(mko[t]["h"]))
    lo = min(s["window"], key=lambda t: float(mko[t]["l"]))
    return hi, float(mko[hi]["h"]), lo, float(mko[lo]["l"])


s19 = next(s for s in st if s["e"] == date(2026, 9, 21))
hi, hv, _, _ = swing(s19)
assert (hi - NYOFF).weekday() == 6 and 12 <= (hi - NYOFF).hour < 18
need(f"the mark peaked at ${hv:.2f} on Sunday afternoon, {p1(hv / s19['c'] - 1)} above Friday's close")
s27 = next(s for s in st if s["e"] == date(2026, 9, 28))
hi, hv, _, _ = swing(s27)
assert (hi - NYOFF).date() == date(2026, 9, 27) and (hi - NYOFF).hour == 20
need(f"On the evening of Sunday, September 27 it touched ${hv:.2f}, {p1(hv / s27['c'] - 1)} above Friday's close, as trades "
     f"on the perp reached ${float(cd[hi]['h']):.2f}, and it stood at ${s27['m4a']:.2f} at 4 am on Monday")
s04 = next(s for s in st if s["e"] == date(2026, 10, 5))
_, _, lo, lv = swing(s04)
assert (lo - NYOFF).date() == date(2026, 10, 4)
need(f"On Sunday, October 4 it fell to ${lv:.2f}, {p1(1 - lv / s04['c'])} below Friday's close")
ups = sorted(((swing(s)[1] / s["c"] - 1, s["e"]) for s in st), reverse=True)
assert ups[0][1] == date(2026, 9, 21) and ups[1][1] == date(2026, 9, 28)
downs = sorted((swing(s)[3] / s["c"] - 1, s["e"]) for s in st)
assert downs[0][1] == date(2026, 10, 5)


def miss(s, key):
    return abs(s["o"] - s[key]) / s["c"]


base = [miss(s, "c") for s in st]
need(f"| Prior close | | {p2(statistics.mean(base))} | {p2(statistics.median(base))} |")
for key, label in (("m4a", "Perp's mark at 4 am"), ("m9a", "Perp's mark at 9 am"),
                   ("pre", "USDE's last pre-market price before 9 am")):
    ms = [miss(s, key) for s in st]
    near = sum(miss(s, key) < miss(s, "c") for s in st)
    need(f"| {label} | {near} of 30 | {p2(statistics.mean(ms))} | {p2(statistics.median(ms))} |")
n4 = sum(miss(s, "m4a") < miss(s, "c") for s in st)
n9 = sum(miss(s, "m9a") < miss(s, "c") for s in st)
# a guide with no bearing on the open: every opening move against every 4 am mark move
moves = [(s["o"] - s["c"]) / s["c"] for s in st]
marks4 = [(s["m4a"] - s["c"]) / s["c"] for s in st]
pairs_near = sum(abs(x - y) < abs(x) for x in moves for y in marks4)
pairs_same = sum(x * y > 0 for x in moves for y in marks4)
same4 = sum(x * y > 0 for x, y in zip(moves, marks4))
need(f"on {n4} of the 30 stretches between sessions, against about {round(pairs_near / 30)} for a guide with no bearing "
     f"on the open")
need(f"it was nearer on {n9} of 30")
need(f"nearer the open than the prior close on {n9} of 30 mornings")
need(f"gave about {round(pairs_near / 30)} nearer opens in 30. The mark's {n4} beat that, and it pointed the same way as "
     f"the opening move on {same4} stretches, against about {round(pairs_same / 30)} for such a guide")
need(f"over all {len(moves) ** 2} pairings of an opening move")
need(f"with a 4 am mark move ÷ 30 = {pairs_near / 30:.1f}")
need(f"USDE opened nearer the mark than the prior close {n4} times. With the mark at 9 am, {n9} times.")
need(f"sat nearer the perp's mark than the prior close {n4} of 30 times at 4 am and {n9} of 30 times at 9 am")
need(f"where the mark sat about {round((s19['m4a'] / s19['c'] - 1) * 100)}% above Friday's close and the open "
     f"{round((s19['o'] / s19['c'] - 1) * 100)}%")
assert round((s19["m9a"] / s19["c"] - 1) * 100) == round((s19["m4a"] / s19["c"] - 1) * 100)
big2 = sorted(st, key=lambda s: abs(s["o"] / s["c"] - 1))[-2:]
assert sorted(s["e"] for s in big2) == [date(2026, 9, 18), date(2026, 9, 21)]
rest = [s for s in st if s not in big2]
need(f"Without them the average misses were {p2(statistics.mean(miss(s, 'c') for s in rest))} for the prior close and "
     f"{p2(statistics.mean(miss(s, 'm4a') for s in rest))} for the mark at 4 am, the median misses were "
     f"{p2(statistics.median(miss(s, 'c') for s in rest))} and {p2(statistics.median(miss(s, 'm4a') for s in rest))}, "
     f"and the mark was nearer the open on {sum(miss(s, 'm4a') < miss(s, 'c') for s in rest)} of {len(rest)} stretches")
# the gap in average misses came mostly from the two largest moves
gap_all = sum(miss(s, "c") - miss(s, "m4a") for s in st)
gap_rest = sum(miss(s, "c") - miss(s, "m4a") for s in rest)
assert gap_rest < 0.5 * gap_all
need("The mark's lower average miss at 4 am came mostly from the two largest opening moves, on September 18 and 21")
ah = [s for s in st if s["post"]]
mark_wins = sum(miss(s, 'm4a') < miss(s, 'post') for s in ah)
post_wins = sum(miss(s, 'post') < miss(s, 'm4a') for s in ah)
assert mark_wins + post_wins == len(ah)
need(f"It was nearer the open than the prior close on {sum(miss(s, 'post') < miss(s, 'c') for s in ah)} of {len(ah)} "
     f"stretches. The mark at 4 am was nearer the open than that price on {mark_wins} of the {len(ah)} stretches and the "
     f"8 pm price on {post_wins}, though the mark had the smaller average and median misses, "
     f"{p2(statistics.mean(miss(s, 'm4a') for s in ah))} and {p2(statistics.median(miss(s, 'm4a') for s in ah))} against "
     f"{p2(statistics.mean(miss(s, 'post') for s in ah))} and {p2(statistics.median(miss(s, 'post') for s in ah))}")
need(f"gave similar average misses, {p2(statistics.mean(miss(s, 'm9a') for s in st))} and "
     f"{p2(statistics.mean(miss(s, 'pre') for s in st))}, though the pre-market price had the lower median miss, "
     f"{p2(statistics.median(miss(s, 'pre') for s in st))} against {p2(statistics.median(miss(s, 'm9a') for s in st))}. "
     f"The mark was nearer the open than the pre-market price on {sum(miss(s, 'm9a') < miss(s, 'pre') for s in st)} of 30 "
     f"mornings")

# ---- weekends, 8 pm Friday to 4 am on the next trading day
wk = [s for s in st if s["gap"] > 1]
tot = sum(usd(t) for s in wk for t in s["trades"])
hours_w = sum(len(s["trades"]) for s in wk)
traded_w = sum(1 for s in wk for t in s["trades"] if vol(t) > 0)
need(f"The perp traded in {traded_w} of their {hours_w} hours")
for s in wk:
    u = sum(usd(t) for t in s["trades"])
    share = u / tot
    share_txt = "under 0.1%" if share < 0.001 else p1(share)
    sat_, last = s["d"] + timedelta(days=1), s["e"] - timedelta(days=1)
    if s["gap"] == 4:
        name = f"{md(sat_)} to {last.day}, with Labor Day"
    else:
        name = f"{md(sat_)} and {last.day}" if last.month == sat_.month else f"{md(sat_)} and {md(last)}"
    need(f"| {name} | {sum(1 for t in s['trades'] if vol(t) > 0)} of {len(s['trades'])} | "
         f"{sum(vol(t) for t in s['trades']):,.2f} | ${u:,.0f} | {share_txt} |")
q = next(s for s in wk if s["d"] == date(2026, 9, 11))
assert sum(1 for t in q["trades"] if vol(t) > 0) == 1
need(f"On the weekend of September 12 and 13 it traded once, {sum(vol(t) for t in q['trades']):.2f} contracts worth "
     f"${sum(usd(t) for t in q['trades']):.0f}")
w = s19
sep18 = sum(usd(t) for t in w["trades"]) / tot
assert sep18 == max(sum(usd(t) for t in s["trades"]) for s in wk) / tot
need(f"That weekend carried {p1(sep18)} of the perp's weekend trading")
need(f"One weekend carried {round(sep18 * 100)}% of weekend trading")

# ---- the weekend of September 19 and 20
need(f"The perp's mark rose {p1(w['m4a'] / w['m8p'] - 1)}, from ${w['m8p']:.2f} at 8 pm on Friday to ${w['m4a']:.2f} at 4 am "
     f"on Monday, and USDE opened that Monday at ${w['o']:.2f}, {p1(w['o'] / w['c'] - 1)} above Friday's close")
need(f"USDE closed at ${w['c']:.2f} on Friday, September 18")
held = {mk[t] for t in mk if at_utc(2026, 9, 19, 1) <= t < at_utc(2026, 9, 19, 18)}
assert len(held) == 1
hv = held.pop()
morning = [at_utc(2026, 9, 19, h) for h in range(14, 18)]
mu = sum(usd(t) for t in morning)
need(f"held at ${hv:.2f} from 9 pm that evening until 2 pm New York time on Saturday, while ${mu / 1e6:.2f} million of "
     f"contracts, {p1(mu / sum(usd(t) for t in w['trades']))} of that weekend's dollar volume, traded between 10 am and "
     f"2 pm at prices from ${min(float(cd[t]['l']) for t in morning):.2f} to ${max(float(cd[t]['h']) for t in morning):.2f}")
m2, m3, m4 = (mark_end(at_utc(2026, 9, 19, h)) for h in (18, 19, 20))
assert m2 == hv
top3 = float(mko[at_utc(2026, 9, 19, 19)]["h"])
need(f"Between 2 pm and 3 pm the mark rose {p1(m3 / m2 - 1)}, to ${m3:.2f}. It touched ${top3:.2f} before 4 pm, stood at "
     f"${m4:.2f} at 4 pm and at ${w['m4a']:.2f} at 4 am on Monday")
need(f"Trades reached ${max(float(cd[t]['h']) for t in w['trades'] if vol(t) > 0):.2f} over the weekend")
need(f"pre-market trading opened at ${float(yh['2026-09-21 04:00']['open']):.2f}, and its opening price was ${w['o']:.2f}")
need(f"The ${hv:.2f} it held from 9 pm on Friday to 2 pm on Saturday was {p1(hv / w['c'] - 1)} above Friday's close")
peak = [t for t in w["window"] if float(mko[t]["h"]) == 14.2674]
assert len(peak) == 4 and all((t - NYOFF).weekday() in (5, 6) for t in peak)
need(f"In {['', 'one', 'two', 'three', 'four'][len(peak)]} separate hours on Saturday and Sunday its hourly high was "
     f"exactly ${14.2674:.2f}, {p1(14.2674 / w['c'] - 1)} above Friday's close")
higher = [t for t in w["window"] if float(mko[t]["h"]) > 14.2674]
assert len(higher) == 1 and (higher[0] - NYOFF).weekday() == 6 and (higher[0] - NYOFF).hour == 14
hh = float(mko[higher[0]]["h"])
assert hh < 14.2674 * 1.005
need(f"In the one hour it went higher, from 2 pm on Sunday, it reached ${hh:.2f}, {p1(hh / 14.2674 - 1)} above that level")

# ---- funding
rate = [float(r["rate"]) * (1 if r["direction"] == "long" else -1) for r in fd]
paid = [float(r["value"]) * (1 if r["direction"] == "long" else -1) for r in fd]
need(f"in {sum(x > 0 for x in rate)} of the {len(rate):,} hourly payments")
need(f"Lighter made {len(rate):,} hourly payments. Longs paid in {sum(x > 0 for x in rate)} of them and shorts in "
     f"{sum(x < 0 for x in rate)}, and {sum(x == 0 for x in rate)} were zero. The rate sat at the 0.0004% base in "
     f"{rate.count(0.0004)}.")
assert float(snap["base_interest_rate"]) / 8 == 0.0004
need(f"base rate of {snap['base_interest_rate']}% every eight hours, or 0.0004% an hour")
need(f"added up to {sum(rate):.2f} percentage points")
need(f"paid {sum(rate):.1f}% of that size, about {sum(rate) / (len(rate) / 168):.1f} percentage points a week")
need(f"A long position of one contract paid ${sum(paid):.2f}")
need(f"USDE rose from ${cl[days[0]]:.2f} at the August 26 close to ${cl[days[-1]]:.2f} at the October 8 close")
need(f"= {sum(rate):.2f} percentage points over {len(rate):,} hourly payments")
weeks = {}
for r, x in zip(fd, rate):
    t = datetime.fromtimestamp(int(r["timestamp"]), Z) - H
    k = t.date() - timedelta(days=t.weekday())
    b = weeks.setdefault(k, [0, 0.0, 0, 0])
    b[0] += 1
    b[1] += x
    b[2] += x > 0
    b[3] += x < 0
for k, b in sorted(weeks.items()):
    net = f"{b[1]:.2f}".replace("-", "−")
    need(f"| {md(k)} | {b[0]} | {net} | {b[2]} | {b[3]} |")
two_weeks = weeks[date(2026, 9, 14)][1] + weeks[date(2026, 9, 21)][1]
assert two_weeks > 0.5 * sum(rate) and cl[date(2026, 9, 25)] > 2 * cl[date(2026, 9, 14)]
need(f"paid a net {sum(rate):.1f}% of that size. It paid {two_weeks:.1f}% in the two weeks from September 14 alone, when "
     "USDE's closing price more than doubled")
need(f"The two weeks from September 14 added {two_weeks:.2f} percentage points, more than the net for all six weeks")
assert two_weeks > sum(rate)
need(f"rose from ${cl[date(2026, 9, 14)]:.2f} on September 14 to ${cl[date(2026, 9, 25)]:.2f} on September 25")
assert all(b[1] < 0 for k, b in weeks.items() if k >= date(2026, 9, 28))
caps = [datetime.fromtimestamp(int(r["timestamp"]), Z) for r in fd if float(r["rate"]) >= 0.5]
assert len(caps) == 5 and caps[0] == at_utc(2026, 9, 1, 13) and all(c.date() == date(2026, 9, 19) for c in caps[1:])
assert [c.hour for c in caps[1:]] == [16, 17, 18, 19]
need("Five payments reached the 0.5% cap, one at 9 am on September 1 and four on Saturday, September 19")
need("in four straight hourly payments, from noon to 3 pm on Saturday")
# the payments match their rates at a typical price within 2% of the mark
implied = sorted((float(r["value"]) / (float(r["rate"]) / 100)) / mk[datetime.fromtimestamp(int(r["timestamp"]), Z) - H]
                 for r in fd if float(r["rate"]) > 0)
assert abs(implied[len(implied) // 2] - 1) < 0.02
need("the median price implied by the funding payments sits within 2% of the mark")

# ---- size
oi = float(snap["open_interest"])
ft, ca = facts["freely_tradable_aug28"], facts["dashboard_class_a_oct8"]
need(f"open interest, the contracts still outstanding, stood at {oi:,.2f}, worth ${oi * float(snap['mark_price']):,.0f} at "
     "the mark")
need(f"equals {oi / ft * 100:.2f}% of the roughly {ft / 1e6:.2f} million Class A shares")
need(f"and {oi / ca * 100:.2f}% of the {ca:,} Class A shares this site's dashboard counted on October 8")
need(f"{oi:,.2f} contracts ÷ {ft:,} freely tradable shares = {oi / ft * 100:.2f}%")
need(f"Open interest equaled {oi / ft * 100:.2f}% of the freely tradable shares")
ctr = sum(vol(t) for t in cd)
shares = sum(int(px[d]["volume"]) for d in days)
need(f"the perp traded {ctr:,.2f} contracts, worth ${usd_all / 1e6:.2f} million, about "
     f"${round((usd_all - usd_out) / n_in, -2):,.0f} an hour from 9 am to 4 pm on trading days and "
     f"${round(usd_out / n_out, -2):,.0f} an hour outside those hours")
need(f"USDE traded {shares:,} shares in its 31 sessions, about {round(shares / ctr)} shares for every contract")

# ---- Lighter's own volume figure against its candles
met = {datetime.fromtimestamp(int(r["timestamp"]), Z).date(): float(r["volume"]) for r in rows("lighter_metrics_1d.csv")}
daily = {}
for t in cd:
    daily[t.date()] = daily.get(t.date(), 0.0) + usd(t)
over = {d: met[d] - v for d, v in daily.items()}
assert min(over.values()) > -0.01
top = max(over, key=over.get)
mtot = sum(met[d] for d in daily)
need(f"Lighter's daily volume figures added up to ${mtot / 1e6:.2f} million, ${(mtot - usd_all) / 1e6:.2f} million more "
     f"than the trades in its hourly candles. They ran higher on {sum(v > 0.005 for v in over.values())} of the "
     f"{len(over)} days and by more than $1,000 on {sum(v > 1000 for v in over.values())}, most on {md(top)}, by "
     f"${over[top] / 1e6:.2f} million.")

print(f"{found} phrases found")
if missing:
    print("MISSING:")
    for m in missing:
        print("  " + m)
    sys.exit(1)
