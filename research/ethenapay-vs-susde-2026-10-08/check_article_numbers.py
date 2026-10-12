#!/usr/bin/env python3
"""
Recomputes every computed figure in article_draft.md, metadata.json and the chart's text from the files in inputs/,
with code written apart from susde_vs_ethenapay_review.py, and confirms that each exact phrase appears. Exits with an
error if a phrase is missing or an assertion fails, so rerun it after any edit. Python 3 standard library only.
No network.
"""
import bisect
import csv
import json
import re
import sys
import time
import unicodedata
from calendar import timegm
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path

getcontext().prec = 60
HERE = Path(__file__).parent
INP = HERE / "inputs"
CH = INP / "chain"
ARTICLE = (HERE / "article_draft.md").read_text()
META = json.loads((HERE / "metadata.json").read_text())
LAYOUT = json.loads((HERE / "layout.json").read_text()) if (HERE / "layout.json").exists() else None   # the site's page layout, not in the download
SVG = (HERE / "out" / "chart_susde_vs_ethenapay.svg").read_text()
TEXT = ARTICLE + "\n" + META["description"] + "\n" + META["imageAlt"] + "\n" + META["title"] + "\n" + META["headline"] + "\n" + SVG
D = 86400
found, missing = 0, []


def need(phrase, where=TEXT):
    global found
    if phrase in where:
        found += 1
    else:
        missing.append(phrase)


def rows(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def t(y, m, d, hh=0, mm=0):
    return timegm((y, m, d, hh, mm, 0))


def q(x, places=2):
    return Decimal(x).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def pct(x, places=2):
    return f"{q(x, places)}%"


def c(x, places=2):
    return f"{q(x, places):,}"


meta = json.loads((CH / "meta.json").read_text())
db = json.loads((INP / "dailyboost_results.json").read_text())
cf = json.loads((INP / "cashflow_results.json").read_text())
facts = {r["id"]: r["fact"] for r in rows(INP / "terms_facts.csv")}

# ---------------------------------------------------------------- sUSDe's price, by a second implementation
ev = [(int(r["ts"]), int(r["block"]), int(r["log_index"]), int(r["assets_wei"]), int(r["shares_wei"])) for r in rows(CH / "events.csv")]
kept = sorted((e for e in ev if e[4] >= 10 ** 15), key=lambda e: (e[0], e[1], e[2]))
assert len(kept) == 2325 and len(ev) - len(kept) == 8
need(f"The review used the {len(kept):,} records of 0.001 sUSDe or more")
price = [(e[0], Decimal(e[3]) / Decimal(e[4])) for e in kept]


def at(when):
    before = [p for p in price if p[0] <= when]
    after = [p for p in price if p[0] > when]
    a, b = before[-1], after[0]
    assert b[0] - a[0] < 4 * 3600
    return a[1] + (b[1] - a[1]) * (when - a[0]) / (b[0] - a[0])


mid = {r["date"]: int(r["ts"]) for r in rows(CH / "midnights.csv")}
P = {d: at(s) for d, s in mid.items() if d <= "2026-10-10"}
need("which were never more than four hours apart")


def grow(d0, d1):
    days = (mid[d1] - mid[d0]) // D
    g = P[d1] / P[d0]
    return (g - 1) * 365 / days * 100, (g ** (Decimal(365) / days) - 1) * 100


sep_b, sep_a = grow("2026-09-01", "2026-10-01")
oct_b, oct_a = grow("2026-10-01", "2026-10-09")
need(f"In September 2026 sUSDe paid {pct(sep_a)} a year after compounding")
need(f"| September | 4.70% | {pct(sep_b)} |")
need(f"| October 1 to 8 | 5.39% | {pct(oct_b)} |")
need(f"4.70% a year before compounding, a simple yearly rate, against {pct(sep_b)} for sUSDe")
need(f"In the first eight days of October EthenaPay's balances earned 5.39% before compounding and sUSDe {pct(oct_b)}")
need(f"| sUSDe | {pct(grow('2026-09-01', '2026-09-16')[1])} | {pct(grow('2026-09-17', '2026-10-01')[1])} | {pct(oct_a)} |")
need(f"September, sUSDe        = ({P['2026-10-01']:.12f} / {P['2026-09-01']:.12f}) ^ (365 / 30) - 1 = {pct(sep_a)}")
days = sorted(P)
daily = {d0: grow(d0, d1)[1] for d0, d1 in zip(days, days[1:])}
span = [d for d in daily if "2026-09-01" <= d <= "2026-10-08"]
assert len(span) == 38
lo, hi = min(span, key=lambda d: daily[d]), max(span, key=lambda d: daily[d])
assert (lo, hi) == ("2026-09-05", "2026-10-01")
assert all(daily[a] != daily[b] for a, b in zip(days, days[1:]) if b in daily)
need(f"sUSDe's rate changed every day, between {pct(daily[lo])} a year on September 5 and {pct(daily[hi])} on October 1")
need(f"sUSDe's rate a year after compounding ranged between {pct(daily[lo])} on September 5 and {pct(daily[hi])} on October 1")
need(f"Its lowest day from September 17 on was {pct(min(daily[d] for d in span if d >= '2026-09-17'))}")

# ---------------------------------------------------------------- EthenaPay's rates, recomputed from the daily shares
share = lambda r: (1 + Decimal(r) / 100) ** (Decimal(1) / 365) - 1
yearly = lambda dd: ((1 + dd) ** 365 - 1) * 100
assert db["rate_changes"]["base_first_4_5"] == "2026-09-17" and db["rate_changes"]["topup_first_0_5"] == "2026-09-16"
assert "Standard 5% a year on balance up to $5,000, Pro 6% up to $100,000, VIP 6% up to $1,000,000" in facts["caps"]
assert "does not set" in facts["total_rate"] and "discretionary promotional incentive that can be reduced to zero" in facts["discretionary"]
std_now, six_now = yearly(share("4.5") + share("0.5")), yearly(share("4.5") + share("1.5"))
std_then, six_then = yearly(share("4.0") + share("1.0")), yearly(share("4.0") + share("2.0"))
std_16, six_16 = yearly(share("4.0") + share("0.5")), yearly(share("4.0") + share("1.5"))
need(f"From September 17 EthenaPay's rates came to {pct(std_now)} a year after compounding on the first $5,000 of a Standard balance and {pct(six_now)} on Pro and VIP balances up to their caps of $100,000 and $1,000,000")
need(f"| EthenaPay Pro and VIP, within the cap | {pct(six_then)} | {pct(six_now)} | {pct(six_now)} |")
need(f"| EthenaPay Standard, first $5,000 | {pct(std_then)} | {pct(std_now)} | {pct(std_now)} |")
need("| EthenaPay, balance above the cap | 4.00% | 4.50% | 4.50% |")
need(f"for September 16 alone the rates were {pct(std_16)} on the first $5,000 of a Standard balance and {pct(six_16)} for Pro and VIP, against {pct(grow('2026-09-16', '2026-09-17')[1])} for sUSDe")
b1728 = db["base_sep_17_28"]
need(f"From September 17 to 28, of {int(b1728['tested']):,} wallet-days with 100 USDe or more, a wallet-day being one wallet on one day, the base payment came within 1% "
     f"of the 4.5% rate on {int(b1728['fit_4_5']):,} and was not made on {int(b1728['unpaid'])}")
bm = db["september_base_vs_model"]
assert abs(Decimal(bm["paid"]) / Decimal(bm["model"]) - 1) < Decimal("0.003") and Decimal(bm["paid"]) == Decimal(db["september"]["base_paid"])
off = db["periods_off_model"]   # the median wallet's rate on days off the model, base at 4.0% to September 16, the Boost at 1.0% to September 15
assert {k for k, d, v in off if Decimal(v) == 0} == {"base", "topup"}
assert any(k == "base" and d <= "2026-09-16" and 1.9 < float(v) / 4.0 < 2.1 for k, d, v in off) and any(k == "topup" and 2.9 < float(v) / 1.0 < 3.1 for k, d, v in off)
need("Over the month the base payments still came within 0.3% of their rates")
assert q(db["september"]["both_simple_pct"]) == Decimal("4.70") and q(db["october_avg_simple_pct"]["both"]) == Decimal("5.39")
assert abs(Decimal(db["september"]["base_paid"]) + Decimal(db["september"]["topup_paid"]) - Decimal(cf["sep_rewards_paid"])) < Decimal("0.01")
need(f"The {c(cf['sep_rewards_paid'])} USDe behind its 4.70% for September is the total the site's [cash-flow review]")
need(f"which that review put at {pct(cf['sep_reward_rate_pct'], 1)} a year of the average end-of-day balance")
# both rates divide the same rewards by a balance and multiply by 365 over the days, so only the balance differs
assert abs(Decimal(cf["sep_rewards_paid"]) / Decimal(cf["sep_avg_balance"]) * 365 / 30 * 100 - Decimal(cf["sep_reward_rate_pct"])) < Decimal("1e-9")
assert abs((Decimal(db["september"]["base_paid"]) + Decimal(db["september"]["topup_paid"])) / Decimal(db["september"]["twa_usde_days"]) * 365 * 100 - Decimal(db["september"]["both_simple_pct"])) < Decimal("0.0001")
need("The two rates differ only in the balance they divide by")
need(f"and found that {pct(db['day_detail']['2026-10-08']['above_cap_share_pct'], 1)} of the USDe in EthenaPay wallets that day sat above a cap")
caps = {"Standard": (5000, "0.5"), "Pro": (100000, "1.5"), "VIP": (1000000, "1.5")}


def wallet(tier, bal):
    cap, boost = caps[tier]
    return yearly(share("4.5") + share(boost) * min(Decimal(bal), cap) / Decimal(bal))


for tier, bal, label in (("Standard", 5000, "Standard, up to $5,000"), ("Standard", 10000, "Standard, $10,000"), ("Standard", 25000, "Standard, $25,000"),
                         ("Pro", 100000, "Pro, up to $100,000"), ("Pro", 250000, "Pro, $250,000"), ("Pro", 1000000, "Pro, $1,000,000"),
                         ("VIP", 1000000, "VIP, up to $1,000,000"), ("VIP", 5000000, "VIP, $5,000,000")):
    need(f"| {label} | {pct(wallet(tier, bal))} |")
# like for like, sUSDe from 00:00 September 17 to 00:00 October 9, the days EthenaPay's rates held, from unrounded growth
same_b, same_a = grow("2026-09-17", "2026-10-09")
need(f"At EthenaPay's rates from September 17 and sUSDe's {pct(same_a)} over the same days, to October 8")
need(f"against sUSDe's {pct(same_a)} over the same days, September 17 to October 8")


def meet(d0, d1):
    s_share = (P[d1] / P[d0]) ** (Decimal(1) / ((mid[d1] - mid[d0]) // D)) - 1
    even = {tier: cap * share(boost) / (s_share - share("4.5")) for tier, (cap, boost) in caps.items()}
    assert all(abs(wallet(k, v) - yearly(s_share)) < Decimal("1e-9") for k, v in even.items())
    return q(even["Standard"] / 100, 0) * 100, q(even["Pro"] / 1000, 0) * 1000, q(even["VIP"] / Decimal(10) ** 5, 0) / 10


std_e, pro_e, vip_e = meet("2026-09-17", "2026-10-09")
need(f"a Standard balance would have earned less than sUSDe above about ${std_e:,.0f}, a Pro balance above about ${pro_e:,.0f} and a VIP balance above about ${vip_e} million")
need(f"The balance at which EthenaPay's rate fell to sUSDe's was about ${std_e:,.0f} for Standard, about ${pro_e:,.0f} for Pro and about ${vip_e} million for VIP")
o_std, o_pro, o_vip = meet("2026-10-01", "2026-10-09")
need(f"at sUSDe's {pct(oct_a)} for October 1 to 8 they were about ${o_std:,.0f}, ${o_pro:,.0f} and ${o_vip} million")

# ---------------------------------------------------------------- day by day, against EthenaPay's rates that day
def epay(day):
    base = "4.0" if day <= "2026-09-16" else "4.5"
    b_std = "1.0" if day <= "2026-09-15" else "0.5"
    b_six = "2.0" if day <= "2026-09-15" else "1.5"
    return Decimal(base), yearly(share(base) + share(b_std)), yearly(share(base) + share(b_six))


above_base = sum(1 for d in span if daily[d] > epay(d)[0])
below_six = sum(1 for d in span if daily[d] < epay(d)[2])
above_std = [d for d in span if daily[d] > epay(d)[1]]
assert above_base == below_six == 38
need(f"sUSDe paid more than EthenaPay's base rate on all {above_base} days and less than the Pro and VIP rate on all of them")
rw = [(int(r["ts"]), int(r["amount_wei"])) for r in rows(CH / "rewards.csv")]
changes = [rw[0]] + [b for a, b in zip(rw, rw[1:]) if abs(b[1] - a[1]) > 10 ** 18]
weeks = [(s, a) for s, a in changes]
big = sorted(weeks[1:] + weeks[:1], key=lambda w: w[1])[-2:]
assert all(w[0] > t(2026, 9, 1) for w in big)
dip = [d for d in span if epay(d)[1] not in (std_then, std_now)]   # the one day the Standard rate fell below its usual level
assert dip == ["2026-09-16"]
usual = [d for d in above_std if d not in dip and any(w[0] < mid[d] + D and mid[d] < w[0] + 7 * D for w in big)]
others = [d for d in above_std if d not in usual]
assert usual == ["2026-09-13", "2026-09-14", "2026-09-26", "2026-09-27", "2026-09-28", "2026-09-29", "2026-09-30", "2026-10-01"] and others == ["2026-09-16", "2026-10-08"]
assert epay("2026-09-16")[1] == std_16
lead8 = daily["2026-10-08"] - std_now
assert q(lead8, 3) == Decimal("0.001")
need(f"It paid more than the Standard rate on {len(above_std)} days. Eight of them, September 13 and 14 and September 26 to October 1, fell in the two weeks with the largest payments")
need(f"The other two were September 16, when the Standard rate dipped to {pct(std_16)}, and October 8, when sUSDe led by about {q(lead8, 3)} of a point")
need(f"sUSDe stayed above the base rate and below the Pro and VIP rate on every day and paid more than the Standard rate on {len(above_std)} days")
# rewards
sep_rw = [a for s, a in rw if t(2026, 9, 1) <= s < t(2026, 10, 1)]
need(f"The contract received {c(Decimal(sum(sep_rw)) / Decimal(10) ** 18)} USDe in {len(sep_rw)} payments in September")
amts = sorted({a for s, a in changes})
need(f"to between {c(Decimal(amts[0]) / Decimal(10) ** 18)} and {c(Decimal(amts[-1]) / Decimal(10) ** 18)} USDe a payment")
hm = sorted(time.strftime("%H:%M", time.gmtime(s)) for s, a in changes[1:])
assert hm[0] == "02:24" and hm[-1] <= "02:55" and all(time.gmtime(s).tm_wday == 4 for s, a in changes[1:])
need("changed the amount every Friday in the weeks read, between 02:24 and 02:55 UTC")

# ---------------------------------------------------------------- the USDe behind sUSDe, integrated segment by segment
# Between breakpoints (events, payments and the ends of their 8-hour vesting) the USDe behind sUSDe moves in a straight
# line, so the trapezoid rule over the segments gives each day's average exactly.
start = mid["2026-08-31"]
fl = sorted((int(r["ts"]), Decimal(int(r["assets_wei"])) * (1 if r["kind"] == "d" else -1) / Decimal(10) ** 18)
            for r in rows(CH / "events.csv") if int(r["ts"]) >= start)
fl_t = [s for s, f in fl]
fl_sum = [Decimal(0)]
for s, f in fl:
    fl_sum.append(fl_sum[-1] + f)
pays = [(s, Decimal(a) / Decimal(10) ** 18) for s, a in rw]


def vest_by(when):
    return sum(a * min(max(Decimal(when - s) / 28800, Decimal(0)), Decimal(1)) for s, a in pays)


def moved(when, inclusive):
    """USDe added since 00:00 August 31 by deposits less withdrawals up to when, and by vesting."""
    k = bisect.bisect_right(fl_t, when) if inclusive else bisect.bisect_left(fl_t, when)
    return fl_sum[k] + vest_by(when) - vest_by(start)


model = []
for d0, d1 in zip(days, days[1:]):
    a, b = mid[d0], mid[d1]
    cuts = sorted({a, b} | {s for s, f in fl if a < s < b} | {x for s, _ in pays for x in (s, s + 28800) if a < x < b})
    area = sum((moved(x, True) + moved(y, False)) / 2 * (y - x) for x, y in zip(cuts, cuts[1:]))
    v = vest_by(b) - vest_by(a)
    r_before = grow(d0, d1)[0]
    model.append([d0, area / D, v, r_before])
c0 = sum(v * 365 * 100 / r - rel for d, rel, v, r in model) / len(model)
gap = max(abs(v * 365 * 100 / (c0 + rel) - r) for d, rel, v, r in model)
assert len(model) == 40 and gap < Decimal("0.001")
need(f"the review fitted one figure, {c(c0 / 10 ** 6, 1)} million USDe at 00:00 UTC on August 31, the average of what each day's rate implies")
need(f"matched the rate measured from the price to within 0.001 of a percentage point on all {len(model)} days from August 31 to October 9")
top = max(model, key=lambda m: m[1])
assert top[0] == lo == "2026-09-05"
oct9 = next(m for m in model if m[0] == "2026-10-09")
need(f"that USDe averaged most on September 5, about {c((c0 + top[1]) / 10 ** 6, 0)} million, the day of sUSDe's lowest rate, and about "
     f"{c((c0 + oct9[1]) / 10 ** 6, 0)} million on October 9")
first_of = {time.strftime("%Y-%m-%d", time.gmtime(s)): (s, a) for s, a in changes[1:]}
order = sorted(first_of.values())


def whole_days(day):
    s, a = first_of[day]
    nxt = next(x for x in order if x[0] > s)[0]
    return a, [d for d in span if s <= mid[d] and mid[d] + D <= nxt]


amt_a, in_a = whole_days("2026-09-04")
amt_b, in_b = whole_days("2026-10-02")
assert amt_b < amt_a and in_a == ["2026-09-0" + str(k) for k in range(5, 10)] + ["2026-09-10"] and len(in_b) == 6
need(f"So the week from October 2 paid less a payment than the week from September 4, {c(Decimal(amt_b) / Decimal(10) ** 18)} USDe against "
     f"{c(Decimal(amt_a) / Decimal(10) ** 18)}, and still paid more on each day wholly inside its week, at least {pct(min(daily[d] for d in in_b))} a year "
     f"against at most {pct(max(daily[d] for d in in_a))}")
assert all(abs(b[0] - a[0] - 8 * 3600) < 120 for a, b in zip(rw, rw[1:]))
assert "every 8 hours and vest linearly over 8 hours" in facts["susde_reward_timing"]
need("Ethena paid rewards into the contract in USDe every 8 hours, and each payment vested over the following 8 hours")
# the contract now and the cross-checks the method reports
now = meta["now"]
assert now["cooldown_duration_s"] == "86400"
need("Unstaking had a cooldown, which the contract set at one day when this review read it on October 12")
cta = Decimal(now["convert_to_assets_1e18"]) / Decimal(10) ** 18
rise = (cta / P["2026-10-10"] - 1) * 100
read_at = timegm(time.strptime(now["read_utc"][:19], "%Y-%m-%dT%H:%M:%S"))
expected = grow("2026-10-09", "2026-10-10")[0] / 365 * Decimal(read_at - mid["2026-10-10"]) / D
assert P["2026-10-10"] < cta and abs(rise / expected - 1) < Decimal("0.1")
need(f"The contract's own price on October 12, {q(cta, 6)} USDe per sUSDe, was {pct(rise)} above the price at 00:00 UTC on October 10, in line with the rate of the days before")
assert meta["end_block"] == 26165481 and meta["logs_from"] == "2026-08-30T00:00:00Z"
need("from 00:00 UTC on August 30 to the end of October 10, through block 26,165,481 on Ethereum")
need("`0x9d39a5de30e57443bff2a8307a4256c8797a3497`")
assert "0x9d39a5de30e57443bff2a8307a4256c8797a3497" in facts["susde_address"] and meta["contract"] == "0x9d39a5de30e57443bff2a8307a4256c8797a3497"
assert "European Union or the European Economic Area" in facts["susde_eu"] and "does not earn rewards" in facts["usde_no_rewards"]

# the records around each midnight hold no payment, no end of a vesting window and no left-out record, so the line is exact
small_ts = [e[0] for e in ev if e[4] < 10 ** 15]
for d in P:
    w = mid[d]
    a_, b_ = max(p[0] for p in price if p[0] <= w), min(p[0] for p in price if p[0] > w)
    assert not any(a_ < x < b_ for s_, _ in rw for x in (s_, s_ + 28800)) and not any(a_ < x < b_ for x in small_ts)
need("No payment was made and no vesting window ended between those two records at any midnight, so the price ran in a straight line between them")
# a missing deposit or withdrawal of 500,000 USDe, at noon on three days, shifts the rebuilt USDe from then on
probe = []
for when in ((2026, 9, 5), (2026, 9, 20), (2026, 10, 5)):
    t_m = t(*when) + D // 2
    for sign in (1, -1):
        shifted = [(rel - sign * 500000 * (1 if t_m <= mid[d] else (0 if t_m >= mid[d] + D else Decimal(mid[d] + D - t_m) / D)), v, r) for d, rel, v, r in model]
        c1 = sum(v * 365 * 100 / r - rel for rel, v, r in shifted) / len(shifted)
        probe.append(max(abs(v * 365 * 100 / (c1 + rel) - r) for rel, v, r in shifted))
assert min(probe) > Decimal("0.001")
need(f"would have widened the largest gap to between {q(min(probe), 4)} and {q(max(probe), 4)} of a point")

# ---------------------------------------------------------------- the chart, the page furniture and the review's own run
pts = rows(HERE / "out" / "chart_points.csv")
assert len(pts) == 38
alt = re.search(r"!\[(.+?)\]\(/research-assets/", ARTICLE).group(1)
assert alt == META["imageAlt"]
need(f"Line chart of {len(pts)} days from September 1 to October 8, 2026", alt)
need(f"about {pct(six_now)} for Pro and VIP balances within their caps, about {pct(std_now)} for the first $5,000 of a Standard balance", alt)
need(f"Both tier lines dip on September 16, to {pct(six_16)} and {pct(std_16)}", alt)
need(f"Line chart of {len(pts)} days", SVG)
need(f"ranged between {pct(daily[lo])} on September 5 and {pct(daily[hi])} on October 1", SVG)
need(f"paid more than the Standard rate on {len(above_std)} days", SVG)
need("sUSDe paid more than EthenaPay's base rate and less than its Pro and VIP rate every day", SVG)
need(f"Pro and VIP {pct(six_now)}", SVG)
need(f"Standard {pct(std_now)}", SVG)
need(f"sUSDe paid {pct(sep_a)} a year in September 2026", META["description"])
assert len(META["description"]) <= 160 and len(META["title"]) <= 60
log = (HERE / "out" / "run_log.txt").read_text()
n_ok = sum(1 for line in log.splitlines() if line.startswith("ok"))
need(f"stops before writing its tables if any of its {n_ok} checks fails")
src = rows(INP / "sources.csv")
assert all(r["read_at_utc"].startswith("2026-10-12") for r in src)
need("Sources read October 12, 2026 UTC")
need("Ethena's documentation, Ethena Pay's Pricing page, FAQ and Terms of Use and the site's own files were read on October 12 UTC")
need("sUSDe read to the end of October 10 UTC")
assert all(x < "2026-10-10" for k in ("base", "topup") for x in db["payment_times"][k])
need("EthenaPay payments read to the end of October 9 UTC")
if LAYOUT:
    need(LAYOUT["cutoff"].split(" · ")[0])
    heads = [re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", unicodedata.normalize("NFKD", h).encode("ascii", "ignore").decode()).strip().lower())
             for h in re.findall(r"^## (.+)$", ARTICLE, re.M)]
    assert [anchor for _, anchor in LAYOUT["navigation"]] == heads, "the page navigation must follow the headings"
shipped = {"article": ARTICLE, "metadata": json.dumps(META, ensure_ascii=False), "chart text": "\n".join(re.findall(r">([^<>]+)<", SVG)), "README": (HERE / "README.md").read_text(),
           "run log": (HERE / "out" / "run_log.txt").read_text(), "terms": (INP / "terms_facts.csv").read_text(), "sources": (INP / "sources.csv").read_text()}
for name, text in shipped.items():
    for ch in ("\u2014", "\u2013", ";"):
        assert ch not in text, (name, ch)
for word in ("spender", " APY", "This article"):
    assert word not in ARTICLE, word

if missing:
    print(f"{len(missing)} phrases missing:")
    for m in missing:
        print("  ", m)
    sys.exit(1)
print(f"All {found} phrases found, every assertion holds")
