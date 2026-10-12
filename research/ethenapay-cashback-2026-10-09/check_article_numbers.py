#!/usr/bin/env python3
"""
Recomputes every computed figure in article_draft.md, metadata.json and the chart's text from the files in inputs/,
with code written apart from ethenapay_cashback_review.py, and confirms that each exact phrase appears. Exits with an
error if a phrase is missing or an assertion fails, so rerun it after any edit. Python 3 standard library only.
No network.
"""
import bisect
import csv
import json
import re
import statistics
import sys
import unicodedata
from collections import Counter
from calendar import timegm
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path

getcontext().prec = 50
HERE = Path(__file__).parent
INP = HERE / "inputs"
CH = INP / "chain"
ARTICLE = (HERE / "article_draft.md").read_text()
META = json.loads((HERE / "metadata.json").read_text())
LAYOUT = json.loads((HERE / "layout.json").read_text()) if (HERE / "layout.json").exists() else None   # the site's page layout, not in the download
SVG = (HERE / "out" / "chart_cashback_schedules.svg").read_text()
TEXT = ARTICLE + "\n" + META["description"] + "\n" + META["imageAlt"] + "\n" + META["title"] + "\n" + META["headline"] + "\n" + SVG
D = 86400

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


def t(y, m, d, hh=0, mm=0):
    return timegm((y, m, d, hh, mm, 0))


def r2(x):
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def c(x, places=2):
    """Thousands separators, rounded half up."""
    q = Decimal(1).scaleb(-places)
    return f"{Decimal(x).quantize(q, rounding=ROUND_HALF_UP):,}"


def pct(x, places=2):
    return f"{Decimal(x).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)}%"


WORDS = {28: "Twenty-eight", 78: "Seventy-eight", 12: "Twelve", 19: "Nineteen", 16: "Sixteen", 10: "Ten", 8: "Eight", 7: "Seven", 6: "Six"}
LOWER = {7: "seven"}

# ---------------------------------------------------------------- the inputs, read afresh
meta = json.loads((CH / "meta.json").read_text())
cf = json.loads((INP / "cashflow_results.json").read_text())
terms = {r["id"]: r for r in table(INP / "terms_facts.csv")}
pay_rows = table(CH / "spends.csv")
card = [(int(r["wallet"]), int(r["ts"]), int(r["cents"])) for r in pay_rows if r["kind"] == "c" and r["spend_event"] == "1"]
no_event = [r for r in pay_rows if r["kind"] == "c" and r["spend_event"] != "1"]
back = [(int(r["wallet"]), int(r["ts"]), int(r["cents"])) for r in pay_rows if r["kind"] == "r"]
cash = [(int(r["payer"]), int(r["batch"]), int(r["wallet"]), int(r["ts"]), int(r["avax_wei"]), int(r["cl_answer"]) if r["cl_answer"] else 0) for r in table(CH / "cashback.csv")]
bat = table(CH / "batches.csv")
oth = table(CH / "other_recipients.csv")


def dollars(wei, answer):
    return Decimal(wei) * Decimal(answer) / Decimal(10) ** 26


# ---------------------------------------------------------------- the schedule as published
assert "Standard pays 4% on the first $2,500 of spend in a calendar month, 1% from $2,500 to $4,000 and nothing above $4,000" in terms["bands"]["fact"]
assert "Pro pays 4.5% to $8,000, 2% to $10,000, 1% to $12,000 and 0.5% above" in terms["bands"]["fact"]
assert "VIP pays 5% to $20,000, 2% to $30,000, 1% to $40,000 and 0.5% above" in terms["bands"]["fact"]
BANDS = {"S": [(0, 2500, "4"), (2500, 4000, "1"), (4000, 10 ** 12, "0")],
         "P": [(0, 8000, "4.5"), (8000, 10000, "2"), (10000, 12000, "1"), (12000, 10 ** 12, "0.5")],
         "V": [(0, 20000, "5"), (20000, 30000, "2"), (30000, 40000, "1"), (40000, 10 ** 12, "0.5")]}


def pays(tier, spend):
    spend = Decimal(spend)
    return sum((max(Decimal(0), min(spend, hi) - lo) * Decimal(r) / 100 for lo, hi, r in BANDS[tier]), Decimal(0))


assert pays("S", 4000) == pays("S", 99999) == 115 and pays("P", 9000) == 380
need("| Standard | 4% to $2,500, 1% to $4,000, nothing above | $115 |")
need("| Pro | 4.5% to $8,000, 2% to $10,000, 1% to $12,000, 0.5% above | No limit |")
need("| VIP | 5% to $20,000, 2% to $30,000, 1% to $40,000, 0.5% above | No limit |")
need("The Standard schedule pays 4% on the first $2,500 of card spend in a calendar month, 1% on the next $1,500 and nothing above $4,000, so its cashback stops at $115 a month")
need("a Pro user who spends $9,000 in a month earns $380")
need("Standard maximum    = 2,500 x 4% + 1,500 x 1% = $115")
need("Pro on $9,000       = 8,000 x 4.5% + 1,000 x 2% = $380")
assert "$9,000 of Pro spend in a month earns 4.5% on $8,000 and 2% on $1,000, $380 in all" in terms["pro_example"]["fact"]
assert "Pricing page effective September 1, 2026 and last updated September 30, 2026. Terms of Use last updated September 22, 2026" in terms["document_dates"]["fact"]
need("The Pricing page took effect on September 1, 2026 and was last updated on September 30, and the Terms of Use were last updated on September 22")
assert "No separate monthly, annual or lifetime cap applies" in terms["no_other_cap"]["fact"]
assert "does not at present apply one and reserves the right to add such caps, publishing them on the Pricing page before they take effect" in terms["no_other_cap"]["fact"]
need("no other monthly, annual or lifetime cap applies at present, and that any such cap would be published on the Pricing page before it took effect")
assert "Transactions under $1.00 earn no cashback" == terms["minimum"]["fact"]
assert "around 1% for most currencies" in terms["fx_fee"]["fact"] and "Fees earn no cashback" in terms["fx_fee"]["fact"]
need("If a purchase in another currency was paid with the card network's conversion fee of about 1% included in the card payment, 4% of the purchase would be about "
     f"{Decimal(4) / Decimal('1.01'):.2f}% of the USDe paid, since fees earn no cashback")
assert "The referral bonus is $30 credited in AVAX" == terms["referral"]["fact"]
assert "do not say how a user becomes Pro or VIP" in terms["tier_shown_in_app"]["fact"]
need("the pages do not say how a user becomes Pro or VIP")

# ---------------------------------------------------------------- what the two accounts paid
n_all = sum(int(b["transfers"]) for b in bat)
wei_all = sum(int(b["avax_wei"]) for b in bat)
assert n_all == sum(meta["cashback_transfers"]) and wei_all == sum(int(x) for x in meta["cashback_avax_wei"])
need(f"the two accounts made {n_all:,} cashback transfers worth {c(Decimal(wei_all) / 10 ** 18)} AVAX to {meta['cashback_wallets']} wallets")
need(f"## Two accounts paid {c(Decimal(wei_all) / 10 ** 18)} AVAX to {meta['cashback_wallets']} wallets")
assert meta["cashback_first"] == "2026-05-20T17:35:14Z" and meta["cashback_last"] == "2026-10-09T02:30:04Z"
need("From the first cashback transfer, at 17:35 UTC on May 20, 2026, to the last batch read, at 02:30 UTC on October 9")
early = [b for b in bat if b["payer"] == "1"]
now = [b for b in bat if b["payer"] == "0"]
assert max(int(b["last_ts"]) for b in early) < t(2026, 7, 15) and min(int(b["first_ts"]) for b in now) >= t(2026, 7, 15)
need(f"The earlier account paid {c(Decimal(sum(int(b['avax_wei']) for b in early)) / 10 ** 18)} AVAX from May 20 to July 14 and the current one "
     f"{c(Decimal(sum(int(b['avax_wei']) for b in now)) / 10 ** 18)} AVAX from July 15")
months = {}
for b in bat:
    key = Decimal(int(b["first_ts"]))
    mo = __import__("time").strftime("%Y-%m", __import__("time").gmtime(int(b["first_ts"])))
    m = months.setdefault(mo, [0, 0, 0])
    m[0] += 1
    m[1] += int(b["transfers"])
    m[2] += int(b["avax_wei"])
for mo, label in (("2026-05", "May, from the 20th"), ("2026-06", "June"), ("2026-07", "July"), ("2026-08", "August")):
    m = months[mo]
    need(f"| {label} | {m[0]} | {m[1]:,} | {c(Decimal(m[2]) / 10 ** 18)} | | |")
for mo, label, lo, hi in (("2026-09", "September", t(2026, 9, 1), t(2026, 10, 1)), ("2026-10", "October 1 to 9", t(2026, 10, 1), t(2026, 10, 10))):
    m = months[mo]
    xs = [x for x in cash if lo <= x[3] < hi]
    assert len(xs) == m[1]
    need(f"| {label} | {m[0]} | {m[1]:,} | {c(Decimal(m[2]) / 10 ** 18)} | {len({x[2] for x in xs})} | {c(sum(dollars(x[4], x[5]) for x in xs))} |")
sep_wei = months["2026-09"][2]
need(f"September's {c(Decimal(sep_wei) / 10 ** 18)} AVAX was about half of the total, and the first nine days of October brought {c(Decimal(months['2026-10'][2]) / 10 ** 18)} more")
assert Decimal("0.45") < Decimal(sep_wei) / wei_all < Decimal("0.55")
# batch times
recent = [b for b in bat if int(b["first_ts"]) >= t(2026, 8, 15)]
assert all(b["payer"] == "0" for b in recent)
hhmm = [__import__("time").strftime("%H:%M", __import__("time").gmtime(int(b["first_ts"]))) for b in recent]
need(f"From August 15 the current account paid once a day, and {hhmm.count('02:30')} of its {len(recent)} batches began at 02:30 UTC, two at 03:00 and one, on September 8, at 05:30")
assert hhmm.count("03:00") == 2 and hhmm.count("05:30") == 1 and len({__import__("time").strftime("%m-%d", __import__("time").gmtime(int(b["first_ts"]))) for b in recent}) == len(recent) == 56
assert __import__("time").strftime("%m-%d", __import__("time").gmtime(int([b for b in recent if hhmm[recent.index(b)] == "05:30"][0]["first_ts"]))) == "09-08"
assert all(int(b["transfers"]) == int(b["recipients"]) for b in recent)
need("Each of these batches paid a wallet at most once")
from19 = [b for b in bat if int(b["first_ts"]) >= t(2026, 9, 19)]
two = [b for b in from19 if int(b["transactions"]) == 2]
assert all(int(b["transactions"]) == 1 for b in bat if t(2026, 9, 1) <= int(b["first_ts"]) < t(2026, 9, 19))
assert all(int(b["last_ts"]) - int(b["first_ts"]) < 60 or 1740 <= int(b["last_ts"]) - int(b["first_ts"]) <= 1860 for b in two)
need(f"From September 19, {len(two)} of the {len(from19)} batches went out in two transactions, the second within a minute of the first or about half an hour later")
big = max(bat, key=lambda b: int(b["transfers"]))
assert big["first_ts"].startswith("1791") and __import__("time").strftime("%m-%d", __import__("time").gmtime(int(big["first_ts"]))) == "10-07"
need(f"The largest batch, on October 7, paid {big['recipients']} wallets")
# transfers to an address that is not a wallet
through = [o for o in oth if o["avax_wei"] == o["same_tx_in_wei"]]
assert len({o["recipient"] for o in oth}) == 1
need(f"The two accounts also sent {c(Decimal(sum(int(o['avax_wei']) for o in oth)) / 10 ** 18)} AVAX in {len(oth)} transfers to one address that is not an EthenaPay wallet")
need(f"{WORDS[len(through)]} of those transfers, {c(Decimal(sum(int(o['avax_wei']) for o in through)) / 10 ** 18)} AVAX, passed on in the same transaction AVAX that the account had just received")
assert sum(int(k["avax_wei"]) for k in meta["cashback_account_incoming"]) == sum(int(o["avax_wei"]) for o in through)

# ---------------------------------------------------------------- isolated card payments, by a second implementation
by_w_card, by_w_back, by_w_cash = {}, {}, {}
for w, ts_, cents in card:
    by_w_card.setdefault(w, []).append((ts_, cents))
for w, ts_, cents in back:
    by_w_back.setdefault(w, []).append(ts_)
for x in cash:
    by_w_cash.setdefault(x[2], []).append(x)
for v in by_w_cash.values():
    v.sort(key=lambda x: x[3])
for v in by_w_back.values():
    v.sort()
batch_starts = sorted(int(b["first_ts"]) for b in bat if b["payer"] == "0")


def quiet(alone, wait, before, lo_cents, hi_cents):
    out = []
    for w, lst in by_w_card.items():
        times = sorted(x[0] for x in lst)
        for ts_, cents in lst:
            if not (t(2026, 8, 21) <= ts_ < t(2026, 10, 9) - wait * D) or not (lo_cents <= cents < hi_cents):
                continue
            i = bisect.bisect_left(times, ts_ - alone * D)
            j = bisect.bisect_right(times, ts_ + alone * D)
            if j - i > 1:
                continue
            rv = by_w_back.get(w, [])
            if bisect.bisect_right(rv, ts_ + wait * D) - bisect.bisect_left(rv, ts_ - alone * D) > 0:
                continue
            cs = by_w_cash.get(w, [])
            if any(ts_ - before * D < x[3] <= ts_ for x in cs):
                continue
            out.append((w, ts_, cents, [x for x in cs if ts_ < x[3] <= ts_ + wait * D]))
    return out


main = quiet(3, 6, 2, 100, 10 ** 12)
singles = [m for m in main if len(m[3]) == 1]
rates = sorted(dollars(m[3][0][4], m[3][0][5]) / (Decimal(m[2]) / 100) * 100 for m in singles)
q = statistics.quantiles([float(r) for r in rates], n=4)
near4 = sum(1 for r in rates if Decimal("3.75") <= r < Decimal("4.25"))
near45 = sum(1 for r in rates if Decimal("4.25") <= r < Decimal("4.75"))
near5 = sum(1 for r in rates if Decimal("4.75") <= r < Decimal("5.25"))
need(f"There were {len(main)} isolated card payments. For {len(singles)} of them, exactly one cashback transfer reached the wallet in the six days after the payment")
need(f"the median came to {pct(statistics.median(rates))} of the card payment, half fell between {pct(q[0])} and {pct(q[2])}, and {near4} of the {len(singles)} came within a quarter of a point of 4%")
need(f"{WORDS[near45]} came within a quarter of a point of 4.5%, the Pro tier's first-band rate, and {near5} of VIP's 5%. The other {len(rates) - near4 - near45 - near5} fell outside those three bands")
need(f"{WORDS[sum(1 for m in main if not m[3])]} card payments were followed by no cashback within six days, as purchases in excluded categories would be, and {sum(1 for m in main if len(m[3]) > 1)} by more than one transfer")
need(f"The median was {Decimal(4) - statistics.median(rates):.2f} of a point under 4%")
need(f"EthenaPay card payments that could be matched one to one with a cashback transfer earned a median {pct(statistics.median(rates))}")
need("## Isolated card payments earned about 4%")
need("An isolated card payment is a card payment of $1 or more from August 21 to October 2 with no other card payment from the same wallet within three days either side")
waits = [bisect.bisect_right(batch_starts, m[3][0][3] + 600) - bisect.bisect_right(batch_starts, m[1]) for m in singles]
need(f"In {waits.count(2) + waits.count(3)} of the {len(singles)} matches the cashback came with the second or third daily batch after the card payment, "
     f"and the median wait was {statistics.median((m[3][0][3] - m[1]) / D for m in singles):.2f} days")
s5 = [m for m in quiet(5, 6, 2, 100, 10 ** 12) if len(m[3]) == 1]
s7 = [m for m in quiet(7, 6, 2, 100, 10 ** 12) if len(m[3]) == 1]
med = lambda ms: pct(statistics.median(dollars(m[3][0][4], m[3][0][5]) / (Decimal(m[2]) / 100) * 100 for m in ms))
need(f"Widening the three-day windows to five days, either side of the payment for other card payments and before it for reversals, left {len(s5)} card payments "
     f"matched to one transfer at a median of {med(s5)}, and widening them to seven days left {len(s7)} at {med(s7)}")
small = quiet(3, 6, 2, 1, 100)
need(f"Of {len(small)} card payments under $1 that passed the same test, {sum(1 for m in small if not m[3])} brought no cashback within six days")

# ---------------------------------------------------------------- September wallet by wallet
S0, S1 = t(2026, 9, 1), t(2026, 10, 1)
month_spend, to28 = {}, {}
for w, ts_, cents in card:
    if S0 <= ts_ < S1:
        month_spend[w] = month_spend.get(w, 0) + cents
        if ts_ < t(2026, 9, 29):
            to28[w] = to28.get(w, 0) + cents
paid = {}
for x in cash:
    if t(2026, 9, 3) <= x[3] < t(2026, 10, 1, 12):
        paid[x[2]] = paid.get(x[2], Decimal(0)) + dollars(x[4], x[5])
assert len({x[3] for x in cash if t(2026, 9, 3) <= x[3] < t(2026, 10, 1, 12) and x[3] in {int(b["first_ts"]) for b in bat}}) == 29
heavy = [w for w, v in to28.items() if v >= 400000]
within = lambda a, b: b > 0 and abs(a / b - 1) <= Decimal("0.05")
capped = [w for w in heavy if within(paid.get(w, Decimal(0)), Decimal(115))]
vip = [w for w in heavy if w not in capped and within(paid.get(w, Decimal(0)), pays("V", Decimal(to28[w]) / 100))]
pro = [w for w in heavy if w not in capped and w not in vip and within(paid.get(w, Decimal(0)), pays("P", Decimal(to28[w]) / 100))]
assert not set(vip) & {w for w in heavy if within(paid.get(w, Decimal(0)), pays("P", Decimal(to28[w]) / 100))}
need(f"{WORDS[len(heavy)]} wallets made $4,000 or more of card payments from September 1 to 28")
cp = [paid[w] for w in capped]
cs = [Decimal(month_spend[w]) / 100 for w in capped]
need(f"{WORDS[len(capped)]} of them were paid within 5% of $115, the most the Standard schedule pays in a month, between ${c(min(cp))} and ${c(max(cp))}")
need(f"{WORDS[len(capped)]} wallets that spent from ${c(min(cs))} to ${c(max(cs))} by card in September 2026 were paid between ${c(min(cp))} and ${c(max(cp))} for the month")
sep_card = sum(v for v in month_spend.values())
need(f"They spent from ${c(min(cs))} to ${c(max(cs))} each in September, ${c(sum(cs))} together or {pct(sum(cs) / (Decimal(sep_card) / 100) * 100, 1)} of all September card spend, "
     f"and were paid ${c(sum(cp))}, {pct(sum(cp) / sum(cs) * 100)} of it. At 4% they would have earned ${c(sum(cs) * Decimal('0.04'))}")
need(f"{WORDS[len(vip)]} others were paid within 5% of what the VIP schedule gives for their spend, and {len(pro)} within 5% of the Pro schedule")
assert 2 * sum(1 for w in vip if to28[w] < 800000) == len(vip) and 2 * sum(1 for w in pro if to28[w] < 800000) == len(pro)
assert all(pays("P", Decimal(to28[w]) / 100) == Decimal(to28[w]) / 100 * Decimal("0.045") and pays("V", Decimal(to28[w]) / 100) == Decimal(to28[w]) / 100 * Decimal("0.05")
           for w in vip + pro if to28[w] < 800000)
need("Half of each group spent less than $8,000 by September 28, where the Pro and VIP schedules pay 4.5% and 5%, so those matches tell the two tiers apart only weakly")
need(f"The other {len(heavy) - len(capped) - len(vip) - len(pro)} matched no schedule within 5%")
need(f"Wallet by wallet, {len(capped) + len(vip) + len(pro)} of the {len(heavy)} wallets that spent $4,000 or more by September 28 were paid within 5% of a published schedule")
crossed = [w for w, v in month_spend.items() if v >= 400000 and to28.get(w, 0) < 400000]
need(f"{WORDS[len(crossed)]} more crossed $4,000 on September 29 or 30, which makes the {len(heavy) + len(crossed)} above")
unmatched = [w for w in heavy if w not in capped and w not in vip and w not in pro]


def gap(w):
    p, sv, pv, vv = paid.get(w, Decimal(0)), Decimal(115), pays("P", Decimal(to28[w]) / 100), pays("V", Decimal(to28[w]) / 100)
    assert sv < pv < vv and not any(within(p, x) for x in (sv, pv, vv))
    return "under" if p < sv else "standard-pro" if p < pv else "pro-vip" if p < vv else "over"


gaps = Counter(gap(w) for w in unmatched)
over = [w for w in unmatched if gap(w) == "over"]
late_august = {w for w, ts_, cents in card if t(2026, 8, 25) <= ts_ < S0}
need(f"{WORDS[gaps['under']]} were paid less than Standard's $115, {gaps['standard-pro']} between the Standard and Pro schedules, {gaps['pro-vip']} between Pro and VIP, "
     f"and {gaps['over']} more than the VIP schedule, {sum(1 for w in over if paid[w] > Decimal(to28[w]) / 100 * Decimal('0.05'))} of them more than 5% of their card payments "
     f"to September 28, above any published rate")
need(f"{WORDS[sum(1 for w in over if w in late_august)]} of the {LOWER[len(over)]} paid more than the VIP schedule had card payments from August 25 to 31")
top = max(heavy, key=lambda w: month_spend[w])
assert top in vip and to28[top] == month_spend[top]
need(f"The largest-spending wallet, with ${c(Decimal(month_spend[top]) / 100)} of card payments in September, was paid ${c(paid[top])}, "
     f"{pct(paid[top] / (Decimal(month_spend[top]) / 100) * 100)} of it, close to the VIP schedule's ${c(pays('V', Decimal(to28[top]) / 100))}")
# after the month turned
cset = set(capped)
late = sum(cents for w, ts_, cents in card if w in cset and t(2026, 9, 25) <= ts_ < S1)
late_paid = sum((dollars(x[4], x[5]) for x in cash if x[2] in cset and t(2026, 9, 27) <= x[3] < t(2026, 10, 1, 12)), Decimal(0))
octo = sum(cents for w, ts_, cents in card if w in cset and S1 <= ts_ < t(2026, 10, 8))
octo_paid = sum((dollars(x[4], x[5]) for x in cash if x[2] in cset and t(2026, 10, 2) <= x[3] < t(2026, 10, 10)), Decimal(0))
oct_users = {w for w, ts_, cents in card if w in cset and S1 <= ts_ < t(2026, 10, 8)}
assert oct_users == {x[2] for x in cash if x[2] in cset and t(2026, 10, 2) <= x[3] < t(2026, 10, 10)}
need(f"From September 25 to 30 they made ${c(Decimal(late) / 100)} of card payments and were paid ${c(late_paid)} in the batches of September 27 to October 1, "
     f"{pct(late_paid / (Decimal(late) / 100) * 100)}")
need(f"From October 1 to 7 they spent ${c(Decimal(octo) / 100)} and were paid ${c(octo_paid)} in the batches of October 2 to 9, {pct(octo_paid / (Decimal(octo) / 100) * 100)}")
need(f"All {len(oct_users)} of them that used the card from October 1 to 7 received cashback in those batches")
# spend groups
spend_d = Decimal(sep_card) / 100
rows_g = []
for label, lo, hi in (("Under $2,500", 0, 250000), ("$2,500 to $4,000", 250000, 400000), ("$4,000 or more", 400000, 10 ** 15)):
    ws = [w for w, v in month_spend.items() if lo <= v < hi]
    s = Decimal(sum(month_spend[w] for w in ws)) / 100
    p = sum((paid.get(w, Decimal(0)) for w in ws), Decimal(0))
    rows_g.append((label, len(ws), s, p))
    need(f"| {label} | {len(ws)} | {pct(s / spend_d * 100, 1)} | {pct(p / s * 100)} | ${c(s * Decimal('0.04') - p)} |")
all_paid = sum(paid.values(), Decimal(0))
no_spend_paid = sum((v for w, v in paid.items() if w not in month_spend), Decimal(0))
short = spend_d * Decimal("0.04") - all_paid
need(f"| All | {len(month_spend)} | 100% | {pct(all_paid / spend_d * 100)} | ${c(short)} |")
need(f"The last row adds ${c(no_spend_paid)} paid to wallets that made no card payment in September")
need(f"A flat 4% on September's card spend would have paid ${c(spend_d * Decimal('0.04'))}")
heavy_short = rows_g[2][2] * Decimal("0.04") - rows_g[2][3]
need(f"Cashback paid from September 3 to October 1, ${c(all_paid)} at Chainlink's price, fell ${c(short)} short of that, and {pct(heavy_short / short * 100, 1)} of the shortfall sat with the wallets that spent $4,000 or more")
need(f"The 28 capped wallets accounted for ${c(sum(cs) * Decimal('0.04') - sum(cp))} of it and the largest-spending wallet alone for "
     f"${c(Decimal(month_spend[top]) / 100 * Decimal('0.04') - paid[top])}")
need(f"The {rows_g[2][1]} wallets that spent $4,000 or more in September made {pct(rows_g[2][2] / spend_d * 100, 1)} of the month's card spend and were paid "
     f"{pct(rows_g[2][3] / rows_g[2][2] * 100)} of it, counting the cashback paid from September 3 to October 1")
need(f"Wallets that spent less than $2,500 were paid {pct(rows_g[0][3] / rows_g[0][2] * 100)}")
light = [paid.get(w, Decimal(0)) / (Decimal(v) / 100) * 100 for w, v in month_spend.items() if 10000 <= v < 250000]
need(f"The median wallet that spent between $100 and $2,500 was paid {pct(statistics.median(light))}")
assert len(heavy) + len(crossed) == rows_g[2][1]
need("| Card spend in September | Wallets | Share of card spend | Rate, paid September 3 to October 1 | Short of 4% |")
need(f"Had every wallet been Standard, the schedules would have paid ${c(sum(pays('S', Decimal(v) / 100) for v in month_spend.values()))} on September's card spend, "
     f"{pct(sum(pays('S', Decimal(v) / 100) for v in month_spend.values()) / spend_d * 100)}")
need(f"All Pro would have paid {pct(sum(pays('P', Decimal(v) / 100) for v in month_spend.values()) / spend_d * 100)} and all VIP "
     f"{pct(sum(pays('V', Decimal(v) / 100) for v in month_spend.values()) / spend_d * 100)}")
b1 = sum(min(Decimal(v) / 100, 2500) for v in month_spend.values())
b2 = sum(max(Decimal(0), min(Decimal(v) / 100, 4000) - 2500) for v in month_spend.values())
b3 = sum(max(Decimal(0), Decimal(v) / 100 - 4000) for v in month_spend.values())
assert b1 + b2 + b3 == spend_d
need(f"Under the Standard bands, {pct(b1 / spend_d * 100, 1)} of the month's spend fell within each wallet's first $2,500, {pct(b2 / spend_d * 100, 1)} between $2,500 and $4,000, "
     f"and {pct(b3 / spend_d * 100, 1)} above $4,000")

# ---------------------------------------------------------------- September by the day it was paid
assert spend_d == Decimal(cf["sep_card_spend_events_usde"])
assert Decimal(sum(int(r["cents"]) for r in pay_rows if r["kind"] == "c" and S0 <= int(r["ts"]) < S1)) / 100 == Decimal(cf["sep_card_spend"])
assert len(no_event) == 1 and no_event[0]["cents"] == "500" and __import__("time").strftime("%m-%d", __import__("time").gmtime(int(no_event[0]["ts"]))) == "09-24"
se = meta["spend_events"]
assert se["card_payments_without_event"] == 1 and se["events_without_card_payment"] == 0 and se["matched_to_card_payments"] == se["usde_logs"]
assert se["to_october_5"]["logs"] == cf["spend_events"] and Decimal(se["to_october_5"]["usde_wei"]) / 10 ** 18 == Decimal(cf["card_spend_events_usde"])
need("One USDe transfer to a settlement address, 5 USDe on September 24, carried no spend event and is left out, as the cash-flow review found")
need("The spend events to October 5, September's card payments and reversals, the cashback in September's batches and the cashback to October 5 matched the cash-flow review's figures")
sep_usd = sum(dollars(x[4], x[5]) for x in cash if S0 <= x[3] < S1)
firsts = {(b["payer"], b["batch"]): int(b["cl_answer"]) for b in bat if b["cl_answer"]}
sep_usd_b = sum(dollars(x[4], firsts[(str(x[0]), str(x[1]))]) for x in cash if S0 <= x[3] < S1)
need(f"In all, the {c(Decimal(sep_wei) / 10 ** 18)} AVAX of cashback paid in September was worth ${c(sep_usd)} at the AVAX price that Chainlink's price feed showed when each transfer arrived, "
     f"{pct(sep_usd / spend_d * 100)} of the month's ${c(spend_d)} of card spend")
need(f"Counted by the day it was paid, September's cashback came to ${c(sep_usd)} at Chainlink's price at each transfer, {pct(sep_usd / spend_d * 100)} of the month's card spend")
need(f"Valuing each batch at its first transfer gives ${c(sep_usd_b)}")
need(f"It gives {pct(all_paid / spend_d * 100)} overall, against {pct(sep_usd / spend_d * 100)} for the batches paid in September")
need(f"gave ${c(Decimal(cf['sep_cashback_usd']))}, {pct((Decimal(cf['sep_cashback_usd']) / sep_usd - 1) * 100, 1)} more")
need(f"put September's cashback at {pct(Decimal(cf['sep_cashback_rate_pct']))} with the dashboard's daily AVAX prices")
shift = [sum(dollars(x[4], x[5]) for x in cash if S0 + k * D <= x[3] < S1 + k * D) / spend_d * 100 for k in (1, 4)]
dash = [Decimal(cf["sep_cashback_rate_shifted_pct"][k]) for k in ("1", "4")]
need(f"Moving the window one to four days later raises the rate from {pct(shift[0])} to {pct(shift[1])}, close to the dashboard's {pct(dash[0])} to {pct(dash[1])}")
need(f"September rate      = {c(sep_usd)} / {c(spend_d)} = {pct(sep_usd / spend_d * 100)}")
sb = sorted((b for b in bat if S0 <= int(b["first_ts"]) < S1), key=lambda b: int(b["first_ts"]))
need(f"AVAX rose from ${c(Decimal(sb[0]['cl_answer']) / 10 ** 8)} at the September 1 batch to ${c(Decimal(sb[-1]['cl_answer']) / 10 ** 8)} at the September 30 batch")
assert sb[0]["first_ts"] == str(t(2026, 9, 1, 2, 30) + 4) and sb[-1]["first_ts"].startswith("17907")
ages = [int(b["first_ts"]) - int(b["cl_updated"]) for b in bat if b["cl_updated"]]
need(f"At the first transfer of every batch from August 20 the price in force was at most {max(ages)} seconds old")
assert min(int(b["first_ts"]) for b in bat if b["cl_updated"]) >= t(2026, 8, 20)
# the $30 check
vals = [dollars(x[4], x[5]) for x in cash if x[5]]
cnt = lambda a, b: sum(1 for v in vals if Decimal(a) <= v < Decimal(b))
need(f"with {cnt('29.5', '30.5')} worth between $29.50 and $30.50 against {cnt('28.5', '29.5')} and {cnt('30.5', '31.5')} in the dollars on either side")
# checks against the cash-flow review that the article reports
assert abs(Decimal(sep_wei) / 10 ** 18 - Decimal(cf["sep_cashback_avax"])) < Decimal("1e-12")
assert abs(Decimal(sum(int(b["avax_wei"]) for b in bat if int(b["first_ts"]) < t(2026, 10, 6))) / 10 ** 18 - Decimal(cf["cashback_avax_to_cutoff"])) < Decimal("1e-9")
assert Decimal(sum(cents for w, ts_, cents in back if S0 <= ts_ < S1)) / 100 == r2(Decimal(cf["sep_card_spend"]) * Decimal(cf["sep_reversal_rate_pct"]) / 100)

# ---------------------------------------------------------------- the chart, the page furniture and the review's own run
pts = table(HERE / "out" / "chart_points.csv")
assert len(pts) == sum(1 for w, v in to28.items() if v >= 1000 and paid.get(w, Decimal(0)) > 0)
need(f"Wallet ({len(pts)})", SVG)
alt = re.search(r"!\[(.+?)\]\(/research-assets/", ARTICLE).group(1)
assert alt == META["imageAlt"]
need(f"Scatter chart of {len(pts)} EthenaPay wallets with $10 or more of card payments from September 1 to 28, 2026 and some cashback paid from September 3 to October 1", alt)
need(f"Light-spending wallets sit near the Standard line, {len(capped)} heavy-spending wallets sit on the flat Standard line at about $115, {len(vip)} sit near the VIP line and {len(pro)} near the Pro line", alt)
need(f"{WORDS[len(capped)]} heavy-spending wallets were paid about $115, the Standard tier's ceiling", SVG)
need("Standard stops at $115 a month", SVG)
need("Light-spending wallets sit near the Standard line", SVG)
need(f"The chart has {len(pts)} dots", SVG)
c28 = [Decimal(to28[w]) / 100 for w in capped]
need(f"{WORDS[len(capped)]} wallets with ${c(min(c28))} to ${c(max(c28))} of card payments from September 1 to 28 sit on the flat Standard line, paid ${c(min(cp))} to ${c(max(cp))}", SVG)
need(f"Of the other wallets with $4,000 or more, {len(vip)} sit within 5% of the VIP line, among them the largest-spending wallet, ${c(Decimal(month_spend[top]) / 100)} in September "
     f"and ${c(paid[top])} of cashback, and {len(pro)} within 5% of the Pro line", SVG)
assert "spender" not in SVG and "spender" not in ARTICLE and "spender" not in json.dumps(META)
need(f"Isolated EthenaPay card payments earned a median {pct(statistics.median(rates))} in cashback, but the Standard tier stops at $115 a month", META["description"])
need(f"September came to {pct(sep_usd / spend_d * 100)} of card spend", META["description"])
assert len(META["description"]) <= 160 and len(META["title"]) <= 60
log = (HERE / "out" / "run_log.txt").read_text()
n_ok = sum(1 for line in log.splitlines() if line.startswith("ok"))
need(f"stops before writing its tables if any of its {n_ok} checks fails")
src = table(INP / "sources.csv")
assert all(r["read_at_utc"].startswith("2026-10-12") for r in src)
assert {"adoption_review", "spend_guide"} <= {r["source"] for r in src}
for r in src:
    if r["address"].startswith("https://ethenadash.com/"):
        assert r["address"] in ARTICLE or r["source"] in ("recount", "daily_chain"), r["source"]
need("Sources read October 12, 2026 UTC")
need("Ethena Pay's Pricing page, FAQ and Terms of Use, Chainlink's feed listing and the site's own files were read on October 12 UTC")
if LAYOUT:
    need(LAYOUT["cutoff"].split(" · ")[0])
    heads = [re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", unicodedata.normalize("NFKD", h).encode("ascii", "ignore").decode()).strip().lower())
             for h in re.findall(r"^## (.+)$", ARTICLE, re.M)]
    assert [anchor for _, anchor in LAYOUT["navigation"]] == heads, "the page navigation must follow the headings"
need("Cashback read to the end of October 9 UTC")
assert meta["end_block"] == 97161009 and meta["end_block_time"] == "2026-10-09T23:59:59Z"
need("on Avalanche C-Chain through block 97,161,009, the last block of October 9 UTC")
assert meta["wallets"] == meta["wallets_v1"] + meta["wallets_v2"]
need(f"This review counts as wallets the {meta['wallets']:,} contracts the factories created with the CREATE2 instruction by that block, and leaves out "
     f"{meta['other_factory_contracts']} other contracts they created with a plain CREATE")
need("The current cashback account is `0x37dea6fe8bc3d8d8c47fa3dac98c39a88585a71d` and the earlier one `0xfdc9d265ba3cdac512c7fe7e30417cc29487ff7b`")
need(f"The feed's proxy is `{meta['chainlink']['proxy']}`")
assert "deviation 0.1%, heartbeat 120s" in [r for r in src if r["source"] == "chainlink"][0]["how"]
need("lists a 0.1% deviation threshold and a 120-second heartbeat for it")

if missing:
    print(f"{len(missing)} phrases missing:")
    for m in missing:
        print("  ", m)
    sys.exit(1)
print(f"All {found} phrases found, every assertion holds")
