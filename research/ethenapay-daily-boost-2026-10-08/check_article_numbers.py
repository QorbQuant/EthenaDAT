#!/usr/bin/env python3
"""
Recomputes every computed figure in article_draft.md, metadata.json and the chart's text from the files in
inputs/, with code written apart from ethenapay_boost_review.py, and confirms that each exact phrase appears.
The wallet-level figures for October 1 and October 8 and for the two calendar months are rebuilt from the
wallet files. The daily counts for the other October days come from inputs/chain/periods.csv, which
boost_recount.cjs wrote. Exits with an error if a phrase is missing or an assertion fails, so rerun it after
any edit. Python 3 standard library only. No network.
"""
import csv
import json
import sys
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 50
HERE = Path(__file__).parent
INP = HERE / "inputs"
CH = INP / "chain"
ARTICLE = (HERE / "article_draft.md").read_text()
META = json.loads((HERE / "metadata.json").read_text())
LAYOUT = json.loads((HERE / "layout.json").read_text()) if (HERE / "layout.json").exists() else None
SVG = (HERE / "out" / "chart_boost_rates.svg").read_text()
TEXT = ARTICLE + "\n" + META["description"] + "\n" + META["imageAlt"] + "\n" + META["title"] + "\n" + META["headline"] + "\n" + SVG
WEI = Decimal(10) ** 18

found, missing = 0, []


def need(phrase, where=TEXT):
    global found
    if phrase in where:
        found += 1
    else:
        missing.append(phrase)


def table(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def usd(x, places=0):
    return f"{x:,.{places}f}"


def factor(rate):
    """The daily share of a yearly rate compounded daily."""
    return ((1 + Decimal(rate)).ln() / 365).exp() - 1


def yearly(daily):
    """A daily share compounded over a year, in percent."""
    return (((1 + daily).ln() * 365).exp() - 1) * 100


F = {name: factor(r) for name, r in (("b45", "0.045"), ("b40", "0.04"), ("s05", "0.005"), ("s10", "0.01"), ("x15", "0.015"), ("x20", "0.02"))}

# ---------------------------------------------------------------- the rates in the terms and their totals
need("0.5% a year on a wallet's first $5,000, or 1.5% a year on the whole balance for a smaller group, on top of a base payment of 4.5% a year on all of it")
need("This review calls the wallets paid 1.5% the 6% group, after their total")
need("matched the 5% and 6% tiers and the caps in Ethena Pay's terms")
need(f"The base and the Standard Boost came to {(F['b45'] + F['s05']) * 36500:.2f}% a year before compounding and {yearly(F['b45'] + F['s05']):.2f}% after it, against the Standard tier's 5%")
assert f"{(F['b45'] + F['s05']) * 36500:.2f}" == "4.90" and f"{yearly(F['b45'] + F['s05']):.2f}" == "5.02"
need(f"The base and the 1.5% Boost came to {(F['b45'] + F['x15']) * 36500:.2f}% and {yearly(F['b45'] + F['x15']):.2f}%, against 6% for the Pro and VIP tiers")
cap_day = F["s05"] * 5000
need(f"All 61 Standard wallets above 5,000 USDe received the same {cap_day:.8f} USDe of Boost for October 8, the daily share of 0.5% on 5,000 USDe")
need(f"The rate divided by 365 would have paid {Decimal(5000) * Decimal('0.005') / 365:.8f}")
need(f"Standard at cap    = 5,000 x ((1.005) ^ (1/365) - 1) = {cap_day:.8f} USDe")
need(f"rate / 365 instead = 5,000 x 0.005 / 365             = {Decimal(5000) * Decimal('0.005') / 365:.8f} USDe")
need("Above $5,000, a fixed 0.068 USDe a day")
need(f"which a 0.5% Boost reaches in one day at about {Decimal('0.001') / F['s05']:.0f} USDe")
need(f"so 1.5% shows as {F['x15'] * 36500:.2f}%")
terms = {r["id"]: r for r in table(INP / "terms_facts.csv")}
assert "Terms of Use last updated September 22, 2026" in terms["document_dates"]["fact"]
need("Ethena Pay's Terms of Use, last updated September 22")
assert "Standard 5% a year on balance up to $5,000, Pro 6% up to $100,000, VIP 6% up to $1,000,000" in terms["caps"]["fact"]
assert "do not say how a user becomes Pro or VIP" in terms["tier_shown_in_app"]["fact"]
need("The pages read for this review did not say how a user becomes Pro or VIP")
assert "within minimum and maximum thresholds" in terms["eligible_balances"]["fact"]
need("The terms said eligible balances had to fall within minimum and maximum thresholds and did not give them")
assert "carried forward" in terms["small_amounts"]["fact"] and "cashback" in terms["small_amounts"]["fact"]
need("That fits a carry-forward like the one the FAQ described for small cashback amounts")
assert "Pricing page effective September 1, 2026 and last updated September 30, 2026" in terms["document_dates"]["fact"]
need("The Terms of Use read for this review were last updated on September 22 and the pricing page on September 30")
assert "ordinarily within 24 hours" in terms["accrual"]["fact"] and "Central European Time" in terms["accrual"]["fact"]
need("The terms said the Boost was ordinarily paid within 24 hours of the end of each accrual day and gave that time in Central European Time")

# ---------------------------------------------------------------- the chain read and the cross-checks
meta = json.loads((CH / "meta.json").read_text())
assert meta["end_block"] == 97161009 and meta["end_block_time"] == "2026-10-09T23:59:59Z" and meta["next_block_time"] >= "2026-10-10T00:00:00Z"
need("through block 97,161,009, the last block of October 9 UTC")
rmeta = json.loads((INP / "recount" / "meta.json").read_text())
assert meta["recount_block"] == 96815525 and meta["cross_checks"]["utc_days_compared"] == 144 == len(table(INP / "recount" / "daily_chain_62503a1.csv"))
need("Each wallet's first USDe and its balance at 15:53 UTC on October 5, and the daily flows and USDe held on all 144 days to October 5")
assert meta["transfers_from_wallets_to_reward_accounts"] == 0
need("No USDe went back to the reward accounts. Through October 9 no wallet sent USDe to either of them")
need("`0xd0ec8cc7414f27ce85f8dece6b4a58225f273311`")
need("`0xab2b06efa6179e624f5e3b08b64978df114ff24f`")
assert rmeta["end_block"] == 96839679

# ---------------------------------------------------------------- the payment periods
per = table(CH / "periods.csv")
P = {(p["payer"], p["first_day"]): p for p in per}
OCT = [f"2026-10-0{d}" for d in range(1, 9)]
for d in OCT:
    for payer in ("base", "topup"):
        assert P[(payer, d)]["last_day"] == d


def osum(payer, col):
    return sum(int(P[(payer, d)][col] or 0) for d in OCT)


tested = osum("topup", "tested_wallets")
assert tested == osum("base", "tested_wallets") == 4351
need(f"{usd(osum('base', 'base_4_5'))} of {usd(tested)}")
assert osum("base", "base_4_5") == osum("base", "fit_utc") == 4214
need(f"| Boost, Standard | 0.5% | First $5,000 | {usd(osum('topup', 'standard_0_5'))} of {usd(tested)} |")
need(f"| Boost, 6% group | 1.5% | All of it | {usd(osum('topup', 'six_1_5'))} of {usd(tested)} |")
need(f"| Boost, 6% group | 1.5% | First $100,000 | {usd(osum('topup', 'six_1_5_cap_100k'))} of {usd(tested)} |")
new = osum("topup", "standard_0_5") + osum("topup", "six_1_5") + osum("topup", "six_1_5_cap_100k")
old = osum("topup", "standard_1_0") + osum("topup", "six_2_0") + osum("topup", "six_2_0_cap_100k")
assert old == osum("topup", "six_2_0") == 1
need(f"Together the three Boost rates matched {usd(new)} of the {usd(tested)} wallet-days")
assert osum("topup", "unpaid") == 8 and osum("base", "unpaid") == 8
need("Eight were unpaid, all for one wallet that received no base payment either, and one matched the 2.0% rate that the 6% group was paid before September 16")
other, still = osum("topup", "other"), osum("topup", "other_without_flows")
assert new + old + 8 + other == tested
need(f"Of the {other} that matched none, {other - still} had USDe move in or out of the wallet during the day")
# day boundaries
need(f"On UTC days, {usd(osum('topup', 'fit_utc'))} of the {usd(tested)} October wallet-days matched a Boost rate, counting the one at 2.0%")
assert osum("topup", "fit_utc") == new + old
need(f"On days that start at midnight Central European Time as the terms wrote it, 23:00 UTC, {usd(osum('topup', 'fit_cet'))} matched, and on days that start at "
     f"midnight under the summer time in force until October 25, 22:00 UTC, {usd(osum('topup', 'fit_cest'))} matched")
need(f"The base payments split the same way, at {usd(osum('base', 'fit_utc'))}, {usd(osum('base', 'fit_cet'))} and {usd(osum('base', 'fit_cest'))}")
assert osum("topup", "fit_utc") > osum("topup", "fit_cet") > osum("topup", "fit_cest")
# payment times
tt = [P[("topup", d)]["first_payment_utc"] for d in OCT]
bt = [P[("base", d)]["first_payment_utc"] for d in OCT]
assert all(t[11:16] == "02:30" for t in tt) and all(t[:10] == f"2026-10-{int(d[-2:]) + 1:02d}" for t, d in zip(tt, OCT))
need("The Boost account paid each day from October 1 to 8 at 02:30 UTC the next morning")
rest = [t for t, d in zip(bt, OCT) if d != "2026-10-07"]
assert all("04:14" <= t[11:16] < "04:18" and t[:10] == f"2026-10-{int(d[-2:]) + 1:02d}" for t, d in zip(bt, OCT) if d != "2026-10-07")
assert P[("base", "2026-10-07")]["first_payment_utc"][:16] == "2026-10-08T21:54"
need("The base account paid between 04:14 and 04:18 UTC, except for October 7, which it paid at 21:54 UTC on October 8")
# October money
paid = Decimal(sum(int(P[(pay, d)]["paid_wei"]) for pay in ("base", "topup") for d in OCT)) / WEI
twa = Decimal(osum("topup", "twa_wei_days")) / WEI
assert twa == Decimal(osum("base", "twa_wei_days")) / WEI
base_oct = Decimal(sum(int(P[("base", d)]["paid_wei"]) for d in OCT)) / WEI
need(f"From October 1 to 8 the two accounts paid {usd(paid, 2)} USDe on an average balance of {usd(twa / 8)} USDe, "
     f"{paid / twa * 36500:.2f}% a year before compounding and {yearly(paid / twa):.2f}% after it")
need(f"The base made up {base_oct / twa * 36500:.2f}% and the Boost {(paid - base_oct) / twa * 36500:.2f}%")
need(f"Across all balances the two accounts paid {paid / twa * 36500:.2f}% a year, or {yearly(paid / twa):.2f}% with daily compounding")
need(f"= {usd(paid, 2)} / {usd(twa)} USDe-days x 365 = {paid / twa * 36500:.2f}% a year")

# ---------------------------------------------------------------- September
SEP = [f"2026-09-{d:02d}" for d in range(1, 31)]
sb = [p for p in per if p["payer"] == "base" and p["first_day"] in SEP]
st = [p for p in per if p["payer"] == "topup" and p["first_day"] in SEP]
assert sum(int(p["days"]) for p in sb) == sum(int(p["days"]) for p in st) == 30
sep_base = Decimal(sum(int(p["paid_wei"]) for p in sb)) / WEI
sep_top = Decimal(sum(int(p["paid_wei"]) for p in st)) / WEI
sep_twa = Decimal(sum(int(p["twa_wei_days"]) for p in sb)) / WEI
cash = json.loads((INP / "cashflow_results.json").read_text())
assert f"{sep_base + sep_top:.2f}" == f"{Decimal(cash['sep_rewards_paid']):.2f}" == "13064.13"
need(f"Both accounts together paid {usd(sep_base + sep_top, 2)} USDe for September, the figure in the site's cash-flow review, which put it at "
     f"{Decimal(cash['sep_reward_rate_pct']):.1f}% a year of the average end-of-day balance")
need(f"On the time-weighted balance of each day it came to {(sep_base + sep_top) / sep_twa * 36500:.2f}% a year before compounding")
model = sum(Decimal(int(p["twa_wei_days"])) / WEI * (F["b40"] if p["last_day"] <= "2026-09-16" else F["b45"]) for p in sb)
assert abs(sep_base / model - 1) < Decimal("0.003")
need(f"Over the month it paid {usd(sep_base, 2)} USDe, within 0.3% of 4.0% and 4.5% a year on the time-weighted balances")


def med_is(p, f):
    return abs(Decimal(p["median_rate_simple_pct"]) / (f * 36500) - 1) < Decimal("0.001")


# rate changes
assert max(p["last_day"] for p in st if med_is(p, F["s10"])) == "2026-09-15" and min(p["first_day"] for p in st if med_is(p, F["s05"])) == "2026-09-16"
assert max(p["last_day"] for p in sb if med_is(p, F["b40"])) == "2026-09-16" and min(p["first_day"] for p in sb if med_is(p, F["b45"])) == "2026-09-17"
assert all(int(p["six_2_0"] or 0) > 0 for p in st if med_is(p, F["s10"]))
assert sum(int(p["six_1_5"] or 0) + int(p["standard_0_5"] or 0) for p in st if med_is(p, F["s10"])) == 0
need("The Boost account paid 1.0% a year on the first $5,000, and 2.0% to the 6% group, until September 15, then 0.5% and 1.5% from September 16")
need("The base account paid 4.0% a year until September 16 and 4.5% from September 17")
need("Before and after the change, base and Boost added up to 5% and 6%")
p1316 = P[("base", "2026-09-13")]
assert p1316["last_day"] == "2026-09-16" and p1316["batches"] == "1" and p1316["first_payment_utc"][:10] == "2026-09-17" and med_is(p1316, F["b40"])
assert int(p1316["other"]) > int(p1316["tested_wallets"]) / 2
need("The Boost fell a day before the base rose, and the base account paid September 13 to 16 in one payment on September 17, at a median of 4.0% a year, though most wallets matched no rate in it")
# missed and caught-up days
p46 = P[("topup", "2026-09-04")]
assert p46["last_day"] == "2026-09-06"
need(f"The Boost account left {p46['unpaid']} of the {p46['tested_wallets']} wallets with 100 USDe or more unpaid for September 4 to 6")
r7 = Decimal(P[("topup", "2026-09-07")]["median_rate_simple_pct"]) / (F["s10"] * 36500)
r8 = Decimal(P[("topup", "2026-09-08")]["median_rate_simple_pct"]) / (F["s10"] * 36500)
assert abs(r7 - 3) < Decimal("0.01") and abs(r8 - 2) < Decimal("0.01")
need("for the median wallet its payments for September 7 and 8 came to about three and two times the usual amount")
for d in ("2026-09-09", "2026-09-12"):
    assert int(P[("base", d)]["unpaid"]) > int(P[("base", d)]["tested_wallets"]) / 2
for d, f in (("2026-09-10", F["b40"]), ("2026-09-29", F["b45"])):
    assert abs(Decimal(P[("base", d)]["median_rate_simple_pct"]) / (f * 36500) - 2) < Decimal("0.01")
need("The base account left most such wallets unpaid for September 9 and 12 and paid about double for September 10 and 29")
mid = [p for p in sb if "2026-09-17" <= p["first_day"] <= "2026-09-28"]
assert len(mid) == 12 and all(abs(Decimal(p["median_rate_simple_pct"]) / (F["b45"] * 36500) - 1) < Decimal("0.012") for p in mid)
need(f"From September 17 to 28 its median payment came within 1.2% of the 4.5% rate each day, but only "
     f"{usd(sum(int(p['base_4_5']) for p in mid))} of {usd(sum(int(p['tested_wallets']) for p in mid))} wallet-days matched 4.5% within 1%, "
     f"and {sum(int(p['unpaid']) for p in mid)} went unpaid")
late = [p for p in per if p["payer"] == "base" and p["first_day"] >= "2026-09-30"]
assert len(late) == 9 and all(int(p["fit_utc"]) / int(p["tested_wallets"]) > 0.95 for p in late)
need("From September 30 it matched more than 95% of the wallets with 100 USDe or more every day")

# ---------------------------------------------------------------- the two wallet-level days
def day_rows(d):
    return table(CH / f"wallet_day_{d}.csv")


def group(tw, tp):
    """The Boost rate a payment matches, within 1% and then within 5%."""
    if tp == 0:
        return "unpaid", None
    for tol in (Decimal("0.01"), Decimal("0.05")):
        for name, f, cap in (("standard", F["s05"], 5000), ("six", F["x15"], None), ("six_cap", F["x15"], 100000)):
            base = min(tw, Decimal(cap)) if cap else tw
            if abs(tp / (f * base) - 1) <= tol:
                return name, tol
    return "other", None


w8 = day_rows("2026-10-08")
assert len(w8) == int(P[("topup", "2026-10-08")]["funded_wallets"]) == 1153
tw8 = {r["wallet"]: Decimal(int(r["twa_micro"])) / 10 ** 6 for r in w8}
total8 = sum(tw8.values())
need(f"On October 8, {usd(len(w8))} wallets held a time-weighted {usd(total8)} USDe")
g8 = {}
for r in w8:
    tw = tw8[r["wallet"]]
    if tw < 100:
        continue
    g8[r["wallet"]] = group(tw, Decimal(int(r["topup_wei"])) / WEI)
six = [w for w, (g, _) in g8.items() if g in ("six", "six_cap")]
std = [w for w, (g, _) in g8.items() if g == "standard"]
six1 = [w for w in six if g8[w][1] == Decimal("0.01")]
assert len(six) == 98 and len(six1) == 95
need(f"On October 8, {len(six)} wallets were paid at the 1.5% rate, {len(six1)} within 1% and {len(six) - len(six1)} within 5%")
big = [w for w in six if tw8[w] > 100000]
need(f"{['No', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight'][sum(1 for w in big if g8[w][0] == 'six')]} of them held more than 100,000 USDe and were paid 1.5% on all of it")
assert sum(1 for w in big if g8[w][0] == "six_cap") == 1 and sum(1 for w in six if g8[w][0] == "six_cap") == 1
need("and one was paid on its first 100,000 USDe, the Pro cap")
assert max(tw8.values()) < 1000000
need("No wallet held more than 1,000,000 USDe, so the VIP cap itself went untested")
std_big = [w for w in std if tw8[w] > 100000]
need(f"{['No', 'One', 'Two', 'Three', 'Four'][len(std_big)]} wallets on the Standard rate held more than 100,000 USDe each, so a balance alone did not show a tier")
need("In this section a wallet that missed every rate by more than 1% counts under the one it came within 5% of")
six_twa = sum(tw8[w] for w in six)
need(f"The {len(six)} wallets paid at 1.5% held {usd(six_twa)} USDe of it, {six_twa / total8 * 100:.1f}%")
std_twa = sum(tw8[w] for w in std)
over5 = [w for w in std if tw8[w] > 5000]
above_std = sum(tw8[w] - 5000 for w in over5)
need(f"The {len(std)} wallets paid at the Standard rate held {usd(std_twa)} USDe, and {len(over5)} of them held more than 5,000 USDe, "
     f"with {usd(above_std)} USDe above the cap between them")
above = above_std + sum(tw8[w] - 100000 for w in six if g8[w][0] == "six_cap")
boosted = sum(tw8[w] for w in six if g8[w][0] == "six") + sum(min(tw8[w], Decimal(5000)) for w in std) + sum(min(tw8[w], Decimal(100000)) for w in six if g8[w][0] == "six_cap")
need(f"In all, {boosted / total8 * 100:.1f}% of the USDe sat within the cap of the rate its wallet was paid, and {above / total8 * 100:.1f}% sat above a cap and earned only the base")
odd = [w for w, (g, _) in g8.items() if g in ("other", "unpaid")]
need(f"The rest was in wallets under 100 USDe and in {len(odd)} wallets whose Boost came within 5% of no rate or was not paid")
need("about a fifth sat above a cap")
w1 = day_rows("2026-10-01")
tw1 = {r["wallet"]: Decimal(int(r["twa_micro"])) / 10 ** 6 for r in w1}
a1 = sum(tw1[r["wallet"]] - 5000 for r in w1 if tw1[r["wallet"]] >= 5000 and group(tw1[r["wallet"]], Decimal(int(r["topup_wei"])) / WEI)[0] == "standard")
assert Decimal("0.19") < above / total8 < Decimal("0.23") and Decimal("0.19") < a1 / sum(tw1.values()) < Decimal("0.23")
for rows_, tw_ in ((w1, tw1), (w8, tw8)):
    paid_top = [Decimal(int(r["topup_wei"])) / WEI for r in rows_ if int(r["topup_wei"]) > 0]
    assert Decimal("0.001") <= min(paid_top) < Decimal("0.0015")
    capped = [Decimal(int(r["topup_wei"])) / WEI for r in rows_ if tw_[r["wallet"]] > 5000 and group(tw_[r["wallet"]], Decimal(int(r["topup_wei"])) / WEI)[0] == "standard"]
    assert {f"{c:.8f}" for c in capped} == {f"{cap_day:.8f}"} and max(abs(c - cap_day) for c in capped) < Decimal("1e-14")
assert len(capped) == len(over5) == 61
need("The smallest Boost payment for October 1 and for October 8 was 0.001 USDe")
need("the smallest Boost payment for October 1 or October 8")
unpaid = [r for r in w8 if tw8[r["wallet"]] >= 100 and int(r["topup_wei"]) == 0]
assert len(unpaid) == 1 and unpaid[0]["base_wei"] == "0" and int(unpaid[0]["card_spends_previous_month"]) > 0 and unpaid[0]["card_spends_month"] == "0"
assert f"{tw8[unpaid[0]['wallet']]:.0f}" == "1000"

# ---------------------------------------------------------------- calendar months
mw = table(CH / "month_wallets.csv")


def month(m):
    return [r for r in mw if r["month"] == m and int(r["tested_days"]) > 0]


def spends(r):
    return tuple(int(r[k]) for k in ("card_spends_before_month", "card_spends_in_month", "card_spends_after_month"))


sep = month("2026-09")
sep_all_top = Decimal(sum(int(r["topup_wei"]) for r in mw if r["month"] == "2026-09")) / WEI
assert sep_all_top == sep_top
need(f"Of the {len(sep)} wallets that held 100 USDe or more on at least one September day, {sum(1 for r in sep if spends(r)[1])} used the card in September")
rows_ = {"In September": [r for r in sep if spends(r)[1]],
         "Not in September, but October 1 to 9": [r for r in sep if not spends(r)[1] and spends(r)[2]],
         "Only before September": [r for r in sep if spends(r) [1:] == (0, 0) and spends(r)[0]],
         "Never": [r for r in sep if spends(r) == (0, 0, 0)]}
for label, rs in rows_.items():
    need(f"| {label} | {len(rs)} | {sum(1 for r in rs if int(r['topup_wei']) > 0)} | {usd(Decimal(sum(int(r['topup_wei']) for r in rs)) / WEI, 2)} |")
none = rows_["Only before September"] + rows_["Never"]
none_top = Decimal(sum(int(r["topup_wei"]) for r in none)) / WEI
assert all(int(r["topup_wei"]) > 0 for r in none)
need(f"The {len(none)} wallets with no card use from September 1 to October 9 received {usd(none_top, 2)} USDe, "
     f"{none_top / sep_top * 100:.1f}% of the {usd(sep_top, 2)} USDe the Boost account paid for September")
never_sep = rows_["Never"]
need(f"All {len(never_sep)} wallets that held 100 USDe or more on some September day and had never used the card by the end of October 9 received the Boost for September")
top1 = max(never_sep, key=lambda r: int(r["topup_wei"]))
need(f"One wallet that never used the card received {Decimal(int(top1['topup_wei'])) / WEI:.2f} USDe of it")
unp = [r for r in rows_["In September"] if int(r["topup_wei"]) == 0]
assert len(unp) == 1 and unp[0]["tested_days"] == "1"
need("The one unpaid wallet in the first row held 100 USDe or more on one day only")
lone = [r for r in never_sep if r["wallets_exchanged_with"] == "0"]
need(f"Of the {len(never_sep)} wallets that had never used the card by the end of October 9, {len(lone)} never exchanged USDe with another EthenaPay wallet, "
     f"and those {len(lone)} received {Decimal(sum(int(r['topup_wei']) for r in lone)) / WEI:.2f} USDe for September")
oct_ = month("2026-10")
never_oct = [r for r in oct_ if spends(r) == (0, 0, 0)]
assert all(int(r["topup_wei"]) > 0 for r in never_oct)
big_oct = max(never_oct, key=lambda r: int(r["topup_wei"]))
need(f"Of the {len(oct_)} wallets that held 100 USDe or more on at least one day from October 1 to 8, {len(never_oct)} had never used the card through October 9, "
     f"and all {len(never_oct)} received the Boost, {Decimal(sum(int(r['topup_wei']) for r in never_oct)) / WEI:.2f} USDe")
need(f"One of them, holding {usd(tw8[big_oct['wallet']])} USDe on October 8, received {Decimal(int(big_oct['topup_wei'])) / WEI:.2f} of it")
need(f"The {len(never_oct)} such wallets in October were paid for October 1 to 8 as well, with most of the month still to run")
need("This review's accrual days ended on October 8 and its card payments on October 9, so an October card payment could still come later in the month")
nset = {r["wallet"] for r in never_oct}
n8 = [w for w in nset if w in tw8 and tw8[w] >= 100]
assert all(int(next(r for r in w8 if r["wallet"] == w)["topup_wei"]) > 0 for w in n8)
need(f"On October 8 the {len(n8)} such wallets with 100 USDe or more held {usd(sum(tw8[w] for w in n8))} USDe, "
     f"{sum(tw8[w] for w in n8) / total8 * 100:.1f}% of the USDe in EthenaPay wallets, and "
     f"{['no', 'one', 'two', 'three', 'four', 'five'][sum(1 for w in n8 if w in six)]} of them were paid at the 1.5% rate")
unp_oct = [r for r in oct_ if int(r["topup_wei"]) == 0]
assert len(unp_oct) == 1 and unp_oct[0]["wallet"] == unpaid[0]["wallet"] and unp_oct[0]["base_wei"] == "0" and unp_oct[0]["tested_days"] == "8"
need("The only wallet with 100 USDe or more that went unpaid for October 1 to 8 held 1,000 USDe, had used the card in September and received no base payment either")

# nothing taken back, wallet by wallet: the never-used wallets paid for September, on October 8
sep_paid_never = {r["wallet"] for r in never_sep if int(r["topup_wei"]) > 0}
held = [w for w in sep_paid_never if w in tw8 and tw8[w] >= 100]
assert all(group(tw8[w], Decimal(int(next(r for r in w8 if r["wallet"] == w)["topup_wei"])) / WEI)[1] == Decimal("0.01") for w in held)
assert len(sep_paid_never) == len(never_sep) == 40
need(f"Of the {len(sep_paid_never)} wallets in the September table that never used the card, {len(held)} still held 100 USDe or more on October 8, "
     f"and each was paid within 1% of a tier rate that day")
# small balances in October
small = [r for r in mw if r["month"] == "2026-10" and r["tested_days"] == "0" and int(r["topup_wei"]) > 0]
rat = sorted(Decimal(int(r["topup_wei"])) / (Decimal(int(r["twa_wei_days"])) * F["s05"]) for r in small)
need(f"From October 1 to 8, {len(small)} wallets that never averaged 100 USDe over a day were paid a Boost, {sum(1 for r in small if r['paid_days'] == '1')} of them "
     f"on one day only, and the median one received {rat[len(rat) // 2]:.2f} times its 0.5% accrual for the eight days")
still = [r for r in w1 if r["other_flows"] == "0" and int(r["topup_wei"]) > 0 and tw1[r["wallet"]] < 10]
ex = min(still, key=lambda r: tw1[r["wallet"]])
ex_tp = Decimal(int(ex["topup_wei"])) / WEI
need(f"A wallet that held {tw1[ex['wallet']]:.2f} USDe through October 1 received {ex_tp:.6f} USDe for that day, about "
     f"{ex_tp / (tw1[ex['wallet']] * F['s05']):.0f} days of accrual at that balance")
for rows_, tw_ in ((w1, tw1), (w8, tw8)):
    assert all(int(r["topup_wei"]) > 0 for r in rows_ if Decimal("73.2") <= tw_[r["wallet"]] < 100)
need("Smaller balances were paid about 0.001 USDe at a time every few days")
# the day boundary where it matters, either Central European balance more than 2% away from the UTC balance


def fits_now(tp, tw):
    return tp > 0 and any(abs(tp / (f * (min(tw, Decimal(c)) if c else tw)) - 1) <= Decimal("0.01") for f, c in ((F["s05"], 5000), (F["x15"], None), (F["x15"], 100000)))


def fits_base(tp, tw):
    return tp > 0 and abs(tp / (F["b45"] * tw) - 1) <= Decimal("0.01")


res_b = []
for rows_ in (w1, w8):
    n_, u_t, c_t, u_b, c_b = 0, 0, 0, 0, 0
    for r in rows_:
        u, c1, c2 = (Decimal(int(r[k])) / 10 ** 6 for k in ("twa_micro", "twa_cet_micro", "twa_cest_micro"))
        if u < 100 or max(abs(c1 / u - 1), abs(c2 / u - 1)) <= Decimal("0.02"):
            continue
        n_ += 1
        tp, bp = Decimal(int(r["topup_wei"])) / WEI, Decimal(int(r["base_wei"])) / WEI
        ft, fct = fits_now(tp, u), fits_now(tp, c1) or fits_now(tp, c2)
        fb, fcb = fits_base(bp, u), fits_base(bp, c1) or fits_base(bp, c2)
        u_t += ft and not fct; c_t += fct and not ft; u_b += fb and not fcb; c_b += fcb and not fb
    res_b.append((n_, u_t, c_t, u_b, c_b))
assert res_b[0][2] == res_b[1][2] == res_b[0][4] == res_b[1][4] == 0
need(f"Among wallets with 100 USDe or more, {res_b[0][0]} wallet-days of October 1 and {res_b[1][0]} of October 8 had a balance on either Central European day "
     f"more than 2% away from the UTC day's. On those, the Boost matched only the UTC day {res_b[0][1]} and {res_b[1][1]} times and only a Central European day "
     f"never. The base did the same, {res_b[0][3]} and {res_b[1][3]} times against none")
# the adoption review's never-spent share, from the recount's own wallet file
rw = table(INP / "recount" / "wallet_activity.csv")
nev_bal = sum(int(r["balance_wei_at_last_snapshot"]) for r in rw if r["first_spend_ts"] == "" and int(r["balance_wei_at_last_snapshot"]) > 0)
all_bal = sum(int(r["balance_wei_at_last_snapshot"]) for r in rw)
# the adoption review counted 264 such wallets with 597,682 USDe, and the recount's wallet file gives 263 with 597,672.51, both 15.1%
need(f"had found a similar share, {Decimal(nev_bal) / Decimal(all_bal) * 100:.1f}% of the USDe in wallets that had never spent, counting every wallet at 15:53 UTC on October 5")
# spend events against card use, and the second unidentified address
fs = {r["wallet"]: r["first_spend_ts"] for r in rw}
OCT1 = 1790812800
assert all((spends(r)[0] + spends(r)[1] > 0) == (fs.get(r["wallet"], "") != "" and int(fs[r["wallet"]]) < OCT1) for r in mw if r["month"] == "2026-09")
assert all(fs.get(r["wallet"], "") == "" for r in mw if spends(r) == (0, 0, 0))
need("the wallets counted below split the same way at September 30, and none of those that never used the card had a spend event through October 5")
d2 = [d for d in rmeta["other_destinations"]["destinations"] if d["destination"] == "destination 2"][0]
assert d2["first"] > "2026-06-10" and d2["of_which_never_spent_to_a_settlement_address"] == 1 and not d2["destination_is_programme_wallet"]
d1 = [d for d in rmeta["other_destinations"]["destinations"] if d["destination"] == "destination 1"][0]
assert d1["last"] < "2026-06-11"
need("Through October 5, only one wallet that sent USDe to the address in use after June 10 had never paid a settlement address")

# ---------------------------------------------------------------- the chart and the counts behind it
pts = table(HERE / "out" / "chart_points.csv")
pts_never = [p for p in pts if p["series"] == "never used the card"]
assert len(pts) == sum(1 for r in w8 if tw8[r["wallet"]] >= 100 and int(r["topup_wei"]) > 0) == 584
assert {p["wallet"] for p in pts_never} == set(n8)
need(f"Used the card at some time ({len(pts) - len(pts_never)})", SVG)
need(f"Never used the card, through October 9 ({len(pts_never)})", SVG)
need(f"{len(pts) - len(pts_never)} had used the card at some time and {len(pts_never)} never had through October 9")
need(f"by {len(pts)} of the {len(pts) + len(unpaid)} EthenaPay wallets with 100 USDe or more, all but one unpaid wallet")
need(f"Scatter chart of the Boost {len(pts)} EthenaPay wallets with 100 USDe or more received for October 8, 2026", META["imageAlt"])
need(f"The {len(pts_never)} wallets that never used the card sit on the same lines", META["imageAlt"])
hi = sorted(Decimal(p["topup_rate_simple_pct"]) for p in pts if Decimal(p["topup_rate_simple_pct"]) > 2)
need(f"2 wallets at {hi[-1]:.2f}% and {hi[0]:.2f}%, above the chart", SVG)

# ---------------------------------------------------------------- the review's own run and the page furniture
log = (HERE / "out" / "run_log.txt").read_text()
n_ok = sum(1 for line in log.splitlines() if line.startswith("ok"))
need(f"stops before writing its tables if any of its {n_ok} checks fails")
src = table(INP / "sources.csv")
reads = sorted(r["read_at_utc"][:10] for r in src if r["read_at_utc"][:4] == "2026")
assert reads and all(x["read_at_utc"][:10] == "2026-10-10" for x in src)
need("Sources read October 10, 2026 UTC")
need("Ethena Pay's FAQ, Terms of Use and pricing page were read on October 10 UTC")
assert all(r["read_at_utc"].startswith("2026-10-10") for r in src if r["source"] in ("faq", "terms", "pricing"))
if LAYOUT:
    need(LAYOUT["cutoff"].split(" · ")[0])
need("Payments read to the end of October 9 UTC")

if missing:
    print(f"{len(missing)} phrases missing:")
    for m in missing:
        print("  ", m)
    sys.exit(1)
print(f"All {found} phrases found, every assertion holds")
