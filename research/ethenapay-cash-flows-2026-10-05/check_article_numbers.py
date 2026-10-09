#!/usr/bin/env python3
"""
Recomputes every computed figure in article_draft.md and metadata.json with code written separately from
ethenapay_cash_flows.py, using exact fractions, and confirms that each phrase appears in the text.
Run after any edit:  python3 check_article_numbers.py   It exits with an error if a phrase is missing.
"""
import csv
import datetime as dt
import json
import sys
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).parent
IN = HERE / "inputs"
art = (HERE / "article_draft.md").read_text()
meta_page = json.loads((HERE / "metadata.json").read_text())
text = art + "\n" + json.dumps(meta_page, ensure_ascii=False)
days = list(csv.DictReader(open(IN / "daily_chain_62503a1.csv")))
recount = json.loads((IN / "chain_meta_62503a1.json").read_text())
dash = json.loads((IN / "ethenapay_5faf41f.json").read_text())
ser, head = dash["series"], dash["headline"]
checks = {r["check"]: r for r in csv.DictReader(open(IN / "chain_checks.csv"))}
faq = {r["id"]: r["fact"] for r in csv.DictReader(open(IN / "faq_facts.csv"))}
WEI = 10 ** 18
KEYS = ("deposits", "withdrawals", "card_spend", "reversals", "yield", "other_rewards", "internal")


def fmt(x, n=2):
    """Round half away from zero to n decimals and add thousands separators."""
    x = F(x)
    q = (abs(x) * 10 ** n + F(1, 2)).__floor__()
    s = f"{q // 10 ** n:,}" + (f".{q % 10 ** n:0{n}d}" if n else "")
    return ("-" if x < 0 else "") + s


def usde(row, key):
    return F(int(row[key + "_wei"]), WEI)


def total(rows, key):
    return sum((usde(r, key) for r in rows), F(0))


def num(v):
    return F(repr(v)) if isinstance(v, float) else F(v)


by_day = {r["date"]: r for r in days}
dep, wd, card, rev, yld, oth, internal = (total(days, k) for k in KEYS)
held = F(int(days[-1]["held_wei"]), WEI)
rewards = yld + oth
events_usde = F(int(recount["spend_wei"]), WEI)
assert held == dep - wd - card + rev + rewards, "the lifetime flows add up to the balance"
pct = lambda a, b: F(a) / F(b) * 100

# the daily identity on every day, and the dashboard against the recount
prev = F(0)
for r in days:
    now = F(int(r["held_wei"]), WEI)
    assert now - prev == usde(r, "deposits") - usde(r, "withdrawals") - usde(r, "card_spend") + usde(r, "reversals") + usde(r, "yield") + usde(r, "other_rewards")
    prev = now
gap, compared = F(0), 0
for i, d in enumerate(ser["date"]):
    if d > "2026-10-05":
        continue
    r = by_day[d]
    for a, b in (("deposits_usde", "deposits"), ("withdrawals_usde", "withdrawals"), ("reversals_usde", "reversals"), ("yield_usde", "yield"),
                 ("other_rewards_usde", "other_rewards")):
        gap = max(gap, abs(num(ser[a][i]) - usde(r, b)))
    gap = max(gap, abs(num(ser["tvl_usde"][i]) - F(int(r["held_wei"]), WEI)), abs(num(ser["spend_usde"][i]) - F(int(r["spend_cents"]), 100)))
    assert int(ser["spend_count"][i]) == int(r["spend_events"])
    compared += 1
missing_days = sorted(set(by_day) - set(ser["date"]))
assert gap < F(1, 10 ** 8) and compared == 143 and missing_days == ["2026-05-30"]
assert all(int(by_day["2026-05-30"][k + "_wei"]) == 0 for k in KEYS[:6])

# periods
before = [r for r in days if r["date"] <= "2026-08-31"]
after = [r for r in days if r["date"] >= "2026-09-01"]
aug31 = F(int(by_day["2026-08-31"]["held_wei"]), WEI)


periods = ((before, F(0), aug31), (after, aug31, held), (days, F(0), held))


def period_line(label, value):
    return f"| {label} | " + " | ".join(fmt(value(rows, opening, closing)) for rows, opening, closing in periods) + " |"


period_lines = [period_line("Held at the start", lambda r, o, c: o), period_line("Deposits", lambda r, o, c: total(r, "deposits")),
                period_line("Withdrawals", lambda r, o, c: total(r, "withdrawals")), period_line("Card spend", lambda r, o, c: total(r, "card_spend")),
                period_line("Reversals", lambda r, o, c: total(r, "reversals")),
                period_line("USDe rewards", lambda r, o, c: total(r, "yield") + total(r, "other_rewards")),
                period_line("Held at the end", lambda r, o, c: c)]


row_sum_gap = (F(fmt(aug31).replace(",", "")) - sum(F(fmt(total(before, k)).replace(",", "")) * s for k, s in
                                                     (("deposits", 1), ("withdrawals", -1), ("card_spend", -1), ("reversals", 1)))
               - F(fmt(total(before, "yield") + total(before, "other_rewards")).replace(",", "")))

# September
sep = [r for r in days if r["date"][:7] == "2026-09"]
pay = [r for r in days if "2026-09-02" <= r["date"] <= "2026-10-01"]
avg_held = sum((F(int(r["held_wei"]), WEI) for r in sep), F(0)) / len(sep)
paid_lag = total(pay, "yield") + total(pay, "other_rewards")
paid_same = total(sep, "yield") + total(sep, "other_rewards")
year = lambda paid: paid / avg_held * F(365, 30) * 100
sep_spend = sum((F(int(r["spend_cents"]), 100) for r in sep), F(0))
sep_rev = total(sep, "reversals")
zero_yield = [r["date"][-2:] for r in sep if int(r["yield_wei"]) == 0]
pos = {d: i for i, d in enumerate(ser["date"])}


def series_sum(key, first, last):
    a, b = dt.date.fromisoformat(first), dt.date.fromisoformat(last)
    span = [(a + dt.timedelta(n)).isoformat() for n in range((b - a).days + 1)]
    assert all(d in pos or d in missing_days for d in span), "only the day without any activity is absent"
    return sum((num(ser[key][pos[d]]) for d in span if d in pos), F(0))


cb_sep_avax = series_sum("cashback_avax", "2026-09-01", "2026-09-30")
cb_sep_usd = series_sum("cashback_usd", "2026-09-01", "2026-09-30")
cb_late_usd = series_sum("cashback_usd", "2026-09-05", "2026-10-04")
cb_all_avax = series_sum("cashback_avax", "2026-05-15", "2026-10-05")
cb_all_usd = series_sum("cashback_usd", "2026-05-15", "2026-10-05")

sep_card = total(sep, "card_spend")
sep_events_usde = sum((F(int(r["spend_cents"]), 100) for r in sep), F(0))
assert sep_card - sep_events_usde == 5
same_rounding = all(fmt(pct(x, y)) == fmt(pct(x, z)) for x, y, z in ((rev, card, events_usde), (sep_rev, sep_card, sep_events_usde),
                                                                     (cb_sep_usd, sep_card, sep_events_usde)))
shifts = []
for k in range(1, 5):
    first = (dt.date(2026, 9, 1) + dt.timedelta(k)).isoformat()
    last = (dt.date(2026, 9, 30) + dt.timedelta(k)).isoformat()
    paid = series_sum("cashback_usd", first, last)
    same_rounding = same_rounding and fmt(pct(paid, sep_card)) == fmt(pct(paid, sep_events_usde))
    shifts.append(pct(paid, sep_card))
assert same_rounding and shifts == sorted(shifts)

# weekends against the Friday before and the Monday after, and the busiest day of each week from September 1
first_sat = dt.date(2026, 9, 5)
weekend_days, around_days = [], []
for n in range(5):
    sat = first_sat + dt.timedelta(weeks=n)
    weekend_days += [sat, sat + dt.timedelta(1)]
    around_days += [sat - dt.timedelta(1), sat + dt.timedelta(2)]
ev = lambda d: int(by_day[d.isoformat()]["spend_events"])
cs = lambda d: usde(by_day[d.isoformat()], "card_spend")
assert all(d.strftime("%A") in ("Saturday", "Sunday") for d in weekend_days) and all(d.strftime("%A") in ("Friday", "Monday") for d in around_days)
week_tops = {max((dt.date(2026, 9, 1) + dt.timedelta(7 * n + k) for k in range(7)), key=ev).strftime("%A") for n in range(5)}

# the pilot account, the only other-reward payer before July 15
before_jul15 = [r for r in days if r["date"] < "2026-07-15"]
pilot_days = [r["date"] for r in before_jul15 if int(r["other_rewards_wei"])]
assert pilot_days[0] == "2026-06-09" and pilot_days[-1] == "2026-07-13"

# weekdays since the beta opened
wk = {}
for r in after:
    w = dt.date.fromisoformat(r["date"]).strftime("%A")
    wk.setdefault(w, []).append((int(r["spend_events"]), F(int(r["spend_cents"]), 100)))
assert all(len(v) == 5 for v in wk.values()) and len(wk) == 7
avg_ev = {w: F(sum(e for e, _ in v), len(v)) for w, v in wk.items()}
wkend = [x for w in ("Saturday", "Sunday") for x in wk[w]]
wkday = [x for w in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday") for x in wk[w]]
busiest, quietest = max(avg_ev, key=avg_ev.get), min(avg_ev, key=avg_ev.get)

# bursts
w_sorted = sorted(days, key=lambda r: -int(r["withdrawals_wei"]))[:3]
d_sorted = sorted(days, key=lambda r: -int(r["deposits_wei"]))[:2]
assert sorted(r["date"] for r in w_sorted) == ["2026-09-15", "2026-09-16", "2026-09-22"]
assert sorted(r["date"] for r in d_sorted) == ["2026-09-02", "2026-09-04"]

# the dashboard's tiles and rates
win_dates = ser["date"][-31:-1]
w_held = [num(v) for v in ser["tvl_usde"][-31:-1]]
avg_w_held = sum(w_held, F(0)) / len(w_held)
tile_yield = sum((num(v) for v in ser["yield_usde"][-31:-1]), F(0)) / avg_w_held * F(365, 30) * 100
tile_both = (sum((num(v) for v in ser["yield_usde"][-31:-1]), F(0)) + sum((num(v) for v in ser["other_rewards_usde"][-31:-1]), F(0))) / avg_w_held * F(365, 30) * 100
tile_cb = sum((num(v) for v in ser["cashback_usd"][-31:-1]), F(0)) / sum((num(v) for v in ser["spend_usde"][-31:-1]), F(0)) * 100
assert abs(tile_yield - num(head["yield_apy_30d"]) * 100) < F(1, 10 ** 9) and abs(tile_cb - num(head["cashback_rate_30d"]) * 100) < F(1, 10 ** 9)
tiles = dep - wd - events_usde + rev + yld
assert held - tiles == oth - 5

# the worked day
oct5, oct4 = by_day["2026-10-05"], by_day["2026-10-04"]
i5 = pos["2026-10-05"]
assert dt.date(2026, 10, 5).strftime("%A") == "Monday"

# outside allowance destinations and the balance check
outside = [d for d in recount["other_destinations"]["destinations"] if not d["destination_is_programme_wallet"]]
outside_usde = sum((F(d["usde_from_programme_wallets"]) for d in outside), F(0))
bc = recount["balance_check"]

# the launch post's time, from its X post ID
post = 2094757140493910168
post_time = dt.datetime.fromtimestamp(((post >> 22) + 1288834974657) / 1000, dt.timezone.utc)
assert post_time.date() == dt.date(2026, 9, 1) and f"x.com/ethena/status/{post}" in art

# chain checks made for this review
yv, ov, cv, pv = (checks[k]["value"] for k in ("sep_yield_payer_out", "sep_other_reward_payer_out", "sep_cashback_safe_calls", "pilot_reward_payer_out"))
trunc6 = lambda x: f"{(x * 10 ** 6).__floor__() // 10 ** 6:,}.{(x * 10 ** 6).__floor__() % 10 ** 6:06d}"   # the explorer reads were truncated
assert f"{trunc6(total(sep, 'yield'))} USDe" in yv and f"{trunc6(total(sep, 'other_rewards'))} USDe" in ov and f"{trunc6(cb_sep_avax)} AVAX" in cv
assert "13,873 transfers out" in yv and "887 recipients" in yv and "10,402 transfers out" in ov and "777 recipients" in ov
assert "4,972 calls, 4,595.286078 AVAX, 622 recipients" in cv and "2026-06-09" in pv and "2026-07-13" in pv
assert f"{fmt(total(before_jul15, 'other_rewards'), 18)} USDe" in pv, "the pilot account's whole outflow equals other rewards before July 15"

# FAQ terms the article restates
for fact_id, needles in (("cashback_bands", ("4% on the first $2,500", "4.5% on the first $8,000", "5% on the first $20,000", "under $1.00")),
                         ("boost", ("Standard 5% up to $5,000", "Pro 6% up to $100,000", "VIP 6% up to $1,000,000", "only the base rate")),
                         ("boost_paid", ("within 24 hours", "at least one qualifying card transaction each calendar month")),
                         ("auth_settle", ("one to three business days", "Only settled transactions earn cashback")),
                         ("credit_terms", ("0% APR", "$40 and $29")), ("cashback_reversal", ("refunded or charged back",))):
    for n in needles:
        assert n in faq[fact_id], (fact_id, n)

phrases = [
    # lead
    f"received {fmt(dep)} USDe in deposits",
    f"Withdrawals took {fmt(pct(wd, dep), 0)}% of that amount and card spend {fmt(pct(card, dep), 0)}%.",
    f"USDe paid as rewards added back {fmt(pct(rev + rewards, dep), 1)}%, which left {fmt(held)} USDe, the equivalent of {fmt(pct(held, dep), 0)}% of deposits, "
    "in the wallets at the end of October 5",
    f"on each of the {len(days)} days the flows added up to the change in USDe held, to the smallest unit the token records",
    "A check at 15:53 UTC on October 5 found that the token contract's own balances matched the balances built from those transfers",
    f"matched a separate recount of the chain in flows, balances and spend events on all {compared} days of its series to October 5",
    f"USDe rewards paid from September 2 to October 1 came to {fmt(year(paid_lag), 1)}% a year on September's average balance, below the 5% and 6% tier totals",
    f"came to {fmt(pct(cb_sep_usd, sep_card))}% of the month's card spend, against first-band rates of 4% to 5%",
    # the flow table
    f"| {fmt(dep)} |", f"| {fmt(wd)} |", f"| {fmt(card)} |", f"| {fmt(rev)} |", f"| {fmt(yld)} |", f"| {fmt(oth)} |", f"| {fmt(internal)} |",
    f"Yield and other rewards together are the USDe rewards, {fmt(rewards)} USDe",
    f"{fmt(card)} USDe in {recount['wallet_to_settlement_transfers']:,} transfers",
    f"{fmt(events_usde)} USDe in {recount['spend_events']:,} events",
    f"The {fmt(card - events_usde, 0)} USDe gap is one transfer on September 24",
    "The reversal and cashback rates below divide by card spend, and spend events give the same rounded rates",
    f"Through October 5 those accounts paid {fmt(cb_all_avax)} AVAX to EthenaPay wallets",
    # card spend timing
    f"Saturdays and Sundays averaged {fmt(F(sum(map(ev, weekend_days)), 10), 1)} spend events, against {fmt(F(sum(map(ev, around_days)), 10), 1)} "
    f"on the Fridays before and the Mondays after them, and card spend was about the same, {fmt(sum(map(cs, weekend_days)) / 10, 0)} USDe a day "
    f"against {fmt(sum(map(cs, around_days)) / 10, 0)}",
    f"{week_tops.pop()} had the most spend events in each of the five weeks from September 1" if len(week_tops) == 1 else "one busiest weekday",
    "late payment and returned payment fees of up to $40 and $29",
    f"Reversals came to {fmt(rev)} USDe, {fmt(pct(rev, card))}% of card spend over the whole period and {fmt(pct(sep_rev, sep_card))}% in September",
    # where it went
    f"Withdrawals took {fmt(pct(wd, dep))}% of the USDe deposited and card spend {fmt(pct(card, dep))}%",
    f"Reversals added the equivalent of {fmt(pct(rev, dep))}% of deposits and USDe rewards {fmt(pct(rewards, dep))}%, which left {fmt(pct(held, dep))}% in the wallets",
    f"Deposits of {fmt(dep, 0)} USDe, less withdrawals of {fmt(wd, 0)} and card spend of {fmt(card, 0)}, plus reversals of {fmt(rev, 0)} "
    f"and USDe rewards of {fmt(rewards, 0)}, left {fmt(held, 0)} USDe held at the end of October 5",
    "| USDe, UTC days | May 15 to August 31 | September 1 to October 5 | May 15 to October 5 |",
    *period_lines,
    f"{fmt(pct(total(after, 'deposits'), dep))}% of all deposits came from that day on",
    f"the first period's parts sum to {fmt(row_sum_gap)} less than its end balance, and the two periods' deposits to "
    f"{fmt(F(fmt(dep).replace(',', '')) - F(fmt(total(before, 'deposits')).replace(',', '')) - F(fmt(total(after, 'deposits')).replace(',', '')))} less than the total",
    f"September 2 and 4 brought {fmt(pct(sum((usde(r, 'deposits') for r in d_sorted), F(0)), dep), 1)}% of all deposits",
    f"September 15, 16 and 22 accounted for {fmt(pct(sum((usde(r, 'withdrawals') for r in w_sorted), F(0)), wd), 1)}% of all withdrawals",
    # rewards
    f"One of those two paid {fmt(total(before_jul15, 'other_rewards'))} USDe into wallets from June {int(pilot_days[0][-2:])} to July {int(pilot_days[-1][-2:])} and nothing after",
    f"the yield account paid {fmt(yld)} USDe into EthenaPay wallets and the other two {fmt(oth)} USDe",
    "5% a year on up to $5,000 for Standard and 6% on up to $100,000 for Pro and up to $1,000,000 for VIP",
    f"They came to {fmt(paid_lag)} USDe, {fmt(year(paid_lag), 1)}% a year on the average end-of-day balance of {fmt(avg_held)} USDe",
    f"Payments made from September 1 to 30 give {fmt(year(paid_same), 1)}%",
    f"paid nothing on September {', '.join(str(int(d)) for d in zero_yield[:-1])} and {int(zero_yield[-1])} and "
    f"{fmt(usde(by_day['2026-09-17'], 'yield'))} USDe on September 17",
    "4% on the first $2,500 of monthly spend for Standard, 4.5% on the first $8,000 for Pro and 5% on the first $20,000 for VIP",
    f"Cashback paid in September came to {fmt(cb_sep_avax)} AVAX, which the dashboard valued at ${fmt(cb_sep_usd)}",
    f"That is {fmt(pct(cb_sep_usd, sep_card))}% of September's card spend of {fmt(sep_card)} USDe",
    f"Moving the cashback window one to four days later gives {fmt(shifts[0])}% to {fmt(shifts[-1])}%",
    f"Through October 5 cashback came to {fmt(cb_all_avax)} AVAX, worth ${fmt(cb_all_usd)}",
    # the worked day
    "October 5 was a Monday",
    f"That day {int(oct5['depositing_wallets'])} wallets deposited USDe, and {int(oct5['spending_wallets'])} wallets made {int(oct5['spend_events']):,} spend events",
    f"| Held at the end of October 4 | {fmt(F(int(oct4['held_wei']), WEI))} |",
    f"| Plus deposits | {fmt(usde(oct5, 'deposits'))} |", f"| Less withdrawals | {fmt(usde(oct5, 'withdrawals'))} |",
    f"| Less card spend | {fmt(usde(oct5, 'card_spend'))} |", f"| Plus reversals | {fmt(usde(oct5, 'reversals'))} |",
    f"| Plus yield | {fmt(usde(oct5, 'yield'))} |", f"| Plus other rewards | {fmt(usde(oct5, 'other_rewards'))} |",
    f"| Held at the end of October 5 | {fmt(F(int(oct5['held_wei']), WEI))} |",
    f"Wallets also sent {fmt(usde(oct5, 'internal'))} USDe to other EthenaPay wallets",
    f"Cashback that day came to {fmt(num(ser['cashback_avax'][i5]))} AVAX for {int(ser['cashback_wallets'][i5])} wallets, ${fmt(num(ser['cashback_usd'][i5]))}",
    f"At the end of the day {int(oct5['funded']):,} of the {int(oct5['wallets_created']):,} wallets created held USDe",
    # checks
    f"through block {recount['end_block']:,}, the last block of October 5",
    f"on all {compared} days of the dashboard's series to October 5, to within a hundred-millionth of a USDe",
    "The series has no row for May 30, a day with no flows",
    f"block {bc['block']:,}, the USDe contract's balance for each of the {bc['wallets_checked']:,} wallets then created equaled the balance built from transfers",
    f"Those balances summed to {fmt(F(int(bc['sum_wei']), WEI))} USDe",
    f"the yield account sent {fmt(total(sep, 'yield'))} USDe in 13,873 transfers to 887 recipients",
    f"the other reward accounts {fmt(total(sep, 'other_rewards'))} USDe in 10,402 transfers to 777 recipients",
    f"paid {fmt(cb_sep_avax)} AVAX in 4,972 payments to 622 wallets",
    # the dashboard
    f"came to {fmt(tiles)} USDe. That is {fmt(held - tiles)} short of the {fmt(held)} held, the other rewards of {fmt(oth)} less the 5 USDe",
    f"generated at {dash['generated_at'][11:16]} UTC on October 8, the tile showed {fmt(tile_yield, 1)}% for "
    f"{dt.date.fromisoformat(win_dates[0]).strftime('%B')} {int(win_dates[0][-2:])} to {dt.date.fromisoformat(win_dates[-1]).strftime('%B')} {int(win_dates[-1][-2:])}",
    f"Adding the other rewards for the same days gives {fmt(tile_both, 1)}%",
    f"The Realized cashback / 30d tile showed {fmt(tile_cb, 1)}%",
    # limits
    f"emitted {sum(d['events_from_programme_wallets'] for d in outside)} AllowanceSpent records for {fmt(outside_usde)} USDe sent to two addresses",
    f"card spend would be {fmt(pct(outside_usde, card))}% higher",
    # metadata
    f"Withdrawals took {fmt(pct(wd, dep), 0)}% and card spend {fmt(pct(card, dep), 0)}%, and reversals and rewards added {fmt(pct(rev + rewards, dep), 1)}%, "
    f"leaving {fmt(pct(held, dep), 0)}% in the wallets",
    f"from {fmt(dep, 0)} deposited to {fmt(held, 0)} held after withdrawals, card spend, reversals and USDe rewards",
]
assert art.splitlines()[0] == "# " + meta_page["headline"]
assert len(meta_page["title"]) <= 60 and len(meta_page["description"]) <= 160
missing = [p for p in phrases if p not in text]
for p in phrases:
    print(("ok      " if p in text else "MISSING ") + p)
print(f"{len(phrases) - len(missing)} of {len(phrases)} phrases found.")
if missing:
    sys.exit(1)
