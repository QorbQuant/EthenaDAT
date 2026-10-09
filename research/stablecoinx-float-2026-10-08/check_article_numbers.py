#!/usr/bin/env python3
"""
Recomputes every computed figure in article_draft.md and metadata.json from the files in inputs/, with code written
separately from stablecoinx_float_review.py, and confirms that each exact phrase appears. Exits with an error if one
does not, so rerun it after any edit to the text.

    python3 check_article_numbers.py
"""
import csv
import json
import statistics
import sys
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).parent
IN = HERE / "inputs"
article = (HERE / "article_draft.md").read_text()
meta = json.loads((HERE / "metadata.json").read_text())
meta_text = meta["title"] + "\n" + meta["description"] + "\n" + meta["imageAlt"]
missing = []
count = 0


def r(x, places):
    q = Decimal(1).scaleb(-places)
    return Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP)


def p(n, d, places=1):
    return f"{r(Decimal(n) / Decimal(d) * 100, places)}%"


def c(n):
    return f"{n:,}"


def need(phrase, where="article"):
    global count
    count += 1
    text = article if where == "article" else meta_text
    if phrase not in text:
        missing.append((where, phrase))


def load(name):
    with open(IN / name, newline="") as f:
        return list(csv.DictReader(f))


fact = {row["key"]: row["value"] for row in load("filing_facts.csv")}
holders0 = {h["holder"]: h for h in load("holders_2026-08-28.csv")}
num = lambda k: int(fact[k])

# share counts
A = num("class_a_outstanding_aug28")
FREE = num("freely_tradable_aug28")
PIPE, ETH_PIPE, ETH_CONTRIB = num("placement_shares_total"), num("ethena_placement_shares"), num("ethena_contribution_shares")
LEGACY, RETAINED = num("legacy_sc_assets_shares"), num("tlgy_insider_retained_shares")
table = {row["line"]: int(row["shares"]) for row in load("merger_share_table.csv")}
tlgy_holders = table["Class A common stock of TLGY"] + table["TLGY Class B common stock outstanding prior to the Merger"]
public = tlgy_holders - RETAINED
other_pipe = PIPE - ETH_PIPE
eth = ETH_CONTRIB + ETH_PIPE
restricted = eth + LEGACY + RETAINED
locked = LEGACY + RETAINED
assert other_pipe + public == FREE and restricted + FREE == A
directors = num("director_restricted_shares_each") * num("directors_with_awards")
dash = json.loads((IN / "data_1cc3b05.json").read_text())
assert int(dash["shares_outstanding"]) == A + directors
B = sum(int(h["class_b_shares"]) for h in load("holders_2026-08-28.csv"))
assert B == num("class_b_outstanding")

need(f"About {r(Decimal(FREE) / 1_000_000, 2)} million of StablecoinX's {r(Decimal(A) / 1_000_000, 2)} million Class A shares, or {p(FREE, A)}")
need(f"About {r(Decimal(FREE) / A * 100, 0)}% of StablecoinX's {r(Decimal(A) / 1_000_000, 2)} million Class A shares could trade freely on August 28, 2026", "meta")
need(f"The other {c(restricted)} Class A shares belonged to Ethena OpCo Ltd")
need(f"The prospectus registered all {c(restricted)} for resale. It says Ethena's {c(eth)} carry no contractual lock-up. Lock-up agreements hold the other {c(locked)} until December 25, 2026, according to the prospectus and the company's current report on the merger.")
need(f"The votes sit with {c(B)} Class B shares")
need(f"On August 28 they belonged to the holders of the {c(restricted)} registered merger shares, and Ethena held {p(int(holders0['Ethena OpCo Ltd']['class_b_shares']), B, 2)} of them")
need(f"With {c(directors)} shares that the company awarded its directors on September 30")
need(f"counted {c(A + directors)} Class A shares on October 8. Of those, {c(FREE + eth)}, or {p(FREE + eth, A + directors)}, were either freely tradable or Ethena's registered shares")
need(f"## The prospectus counted {r(Decimal(FREE) / 1_000_000, 2)} million freely tradable shares")
need(f"gives the freely tradable count as approximately {c(FREE)}")
rows_free = [
    ("Private placement investors other than Ethena", other_pipe), ("TLGY public holders who did not redeem", public),
    ("Ethena", eth), ("SC Assets' original shareholders", LEGACY), ("TLGY's insiders", RETAINED),
]
for label, n in rows_free:
    need(f"| {label} | {c(n)} | {p(n, A)} |")
need(f"| Total on August 28 | {c(A)} | 100% |")
need(f"sold {c(PIPE)} SC Assets Class A shares to investors who paid in cash and in ENA")
need(f"Ethena bought {c(ETH_PIPE)} of the placement shares, and the other {c(other_pipe)} made up all but {c(public)} of the freely tradable count")
need(f"Those {c(public)} are what TLGY's public shareholders kept. The share table gives {c(table['Class A common stock of TLGY'])} Class A shares and {c(table['TLGY Class B common stock outstanding prior to the Merger'])} Class B shares from TLGY, which this review adds up to {c(tlgy_holders)} shares")
need(f"TLGY's insiders received {c(RETAINED)} of them for their founder shares")
need(f"bought for ${Decimal(fact['private_warrant_price_usd']):.2f} each when TLGY first listed. That leaves {c(public)} for the public holders")
need(f"The table deducts {c(-table['Redemption of TLGY Class A common stock'])} redeemed shares, while the 8-K reports {c(num('public_shares_redeemed_8k'))} redeemed at about ${Decimal(fact['redemption_price_8k']):.2f} each")

# restricted holders
need(f"The {c(restricted)} shares outside the freely tradable count are the merger shares")
need(f"| Ethena | {c(eth)} | {c(ETH_CONTRIB)} | After 4:00 pm on September 14, 2026 |")
need(f"| SC Assets' original shareholders | {c(LEGACY)} | {c(LEGACY)} | After December 25, 2026 |")
need(f"| TLGY's insiders | {c(RETAINED)} | {c(RETAINED)} | After December 25, 2026 |")
need(f"| Total | {c(restricted)} | {c(B)} | |")
ena = Decimal(fact["ena_contributed"])
assert r(ena * Decimal(fact["contribution_price_per_ena"]), 0) == num("contribution_agreement_value_usd")
need(f"Ethena received {c(ETH_CONTRIB)} Class A shares and as many Class B shares for contributing {c(int(ena))} ENA, which the July 21, 2025 contribution agreement priced at ${num('contribution_agreement_value_usd') // 1_000_000} million, or ${fact['contribution_price_per_ena']} a token")
need(f"It also bought its {c(ETH_PIPE)} placement shares")
holders = {h["holder"]: h for h in load("holders_2026-08-28.csv")}
chen, cho = int(holders["Trust of the chairman of the board"]["class_a_shares"]), int(holders["Chief financial officer"]["class_a_shares"])
svj = int(holders["Schulz von Jacob Ltd (owned by the chief technology officer)"]["class_a_shares"])
assert chen == cho and chen + cho + svj == LEGACY
need(f"On August 28 a trust of Chen's and Cho each held {c(chen)} shares, and a company owned by the chief technology officer held {c(svj)}")
need(f"${c(num('svj_cash_contribution_usd'))} in cash")
need(f"handed in {c(num('tlgy_founder_shares_exchanged'))} founder shares and {c(num('tlgy_private_warrants_exchanged'))} private warrants at the merger for {c(RETAINED)} Class A shares")
need(f"Their agreement called for {fact['retained_share_pct_agreed']}% of the Class A shares after the merger, and {c(RETAINED)} is {r(Decimal(RETAINED) / A * 100, 2)}% of {c(A)}")
closing = date.fromisoformat(fact["closing_date"])
assert date(closing.year, closing.month + 6, closing.day) == date(2026, 12, 25)
lock_end = date(closing.year, closing.month + 6, closing.day)
assert lock_end.weekday() == 4 and lock_end.month == 12 and lock_end.day == 25
need("run until six months after the June 25 closing. That is December 25, 2026, a market holiday, so the first session after the lock-ups is December 28")

# volume
spg = {row["date"]: row for row in load("usde_daily_spglobal_stockanalysis.csv") if row["date"] >= fact["first_trading_day"]}
yah = {row["date"]: int(row["volume"]) for row in load("usde_daily_yahoo.csv")}
vol = {d: int(row["volume"]) for d, row in spg.items()}
assert sorted(vol) == sorted(yah) and len(vol) == 73
total, totaly = sum(vol.values()), sum(yah.values())
med0 = statistics.median(vol.values())
assert r(Decimal(locked) / Decimal(med0) * 100, 0) == 75
need(f"The {c(locked)} locked shares equal three quarters of the median session's volume, {c(med0)} shares")
need(f"USDE's volume over its first {len(vol)} sessions, from June 26 to October 8, came to {c(total)} shares, {r(Decimal(total) / FREE, 2)} times the freely tradable count")
need(f"## USDE's volume came to {r(Decimal(total) / FREE, 2)} times the freely tradable count")
need(f"added up to {c(total)} shares over the {len(vol)} sessions")
need(f"Yahoo Finance's daily volume added up to {c(totaly)}, or {p(totaly - total, total, 2)} more, and no session differed by more than {p(max(abs(yah[d] - vol[d]) / Decimal(vol[d]) for d in vol), 1, 1)}")
periods = [("June 26 to 30", "2026-06"), ("July", "2026-07"), ("August", "2026-08"), ("September", "2026-09"), ("October 1 to 8", "2026-10")]
for label, m in periods:
    v = [x for d, x in vol.items() if d.startswith(m)]
    avg = Decimal(sum(v)) / len(v)
    need(f"| {label} | {len(v)} | {c(sum(v))} | {c(int(r(avg, 0)))} | {p(avg, FREE)} |")
avg_all = Decimal(total) / len(vol)
need(f"| All 73 sessions | {len(vol)} | {c(total)} | {c(int(r(avg_all, 0)))} | {p(avg_all, FREE)} |")
for d, label in (("2026-07-02", "July 2 traded"), ("2026-08-21", "August 21 traded"), ("2026-08-27", "August 27 traded")):
    assert vol[d] > FREE
    times = r(Decimal(vol[d]) / FREE, 2)
    close = f"${Decimal(spg[d]['close']):.2f}"
    if d == "2026-07-02":
        need(f"{label} {c(vol[d])} shares, {times} times the count, and USDE closed at {close}")
    else:
        need(f"{label} {c(vol[d])}, or {times} times, and closed at {close}")
assert sum(1 for v in vol.values() if v > FREE) == 3
med = statistics.median(vol.values())
need(f"The median session traded {c(med)} shares, {p(med, FREE)} of the count")
eff_day, eff_time = fact["resale_registration_effective"].split("T")
assert eff_time == "16:00"
since = sorted(d for d in vol if d > eff_day)
assert since[0] == "2026-09-15"
need(f"From September 15, the first session after the resale registration took effect, to October 8, USDE traded {c(sum(vol[d] for d in since))} shares in {len(since)} sessions")
need("The registration took effect at 4:00 pm on September 14, as that day's session closed")

# 13F
f13 = load("13f_june30_2026.csv")
cls_a = sorted((x for x in f13 if x["cusip"].upper() == "85238K100"), key=lambda x: -int(x["shares"]))
held = sum(int(x["shares"]) for x in cls_a)
need(f"## Seven Form 13F reports listed {r(Decimal(held) / 1_000_000, 2)} million shares at June 30")
need(f"Together they reported {c(held)} shares, {p(held, FREE)} of the freely tradable count")
first3 = sum(v for d, v in vol.items() if d <= "2026-06-30")
need(f"Only {c(first3)} shares traded from June 26 to 30. Had the seven managers bought every one of them and every TLGY public share, at least {c(held - first3 - public)} of their shares would still have come from elsewhere")
need("for June 30, 2026, the third day USDE traded")
assert sorted(vol)[2] == "2026-06-30"
names = {"Ribbit Management Company, LLC": "Ribbit Management Company", "ParaFi Capital LP": "ParaFi Capital",
         "Kingsway Capital Partners Ltd": "Kingsway Capital Partners", "Pantera Capital Partners LP": "Pantera Capital Partners",
         "FRANKLIN RESOURCES INC": "Franklin Resources", "Galaxy Digital Inc.": "Galaxy Digital", "Clear Street Group Inc.": "Clear Street Group"}
for x in cls_a:
    filed = date.fromisoformat(x["filed"])
    need(f"| {names[x['filer']]} | {c(int(x['shares']))} | {filed.strftime('%B')} {filed.day} |")
need(f"| Total | {c(held)} | |")
wts = [x for x in f13 if x["cusip"].upper() == "85238K118" and "counted once" not in x["note"] and x["put_call"] == ""]
wt = sum(int(x["shares"]) for x in wts)
need(f"also listed {c(wt)} public warrants held by {len({x['filer_cik'] for x in wts})} managers, {p(wt, num('public_warrants'))} of the {c(num('public_warrants'))}")

# votes
eth_b = int(holders["Ethena OpCo Ltd"]["class_b_shares"])
od = num("officers_directors_class_b")
former_chair = num("tlgy_former_chairman_class_b")
rest = B - eth_b - od - former_chair
for label, n in (("Ethena", eth_b), ("Officers and directors", od), ("TLGY's former chairman", former_chair), ("Other former TLGY holders", rest)):
    need(f"| {label} | {c(n)} | {p(n, B, 2)} |")
need(f"| Total | {c(B)} | 100% |")
cpc = int(holders["CPC Sponsor Opportunities I, LP"]["class_b_shares"]) + int(holders["CPC Sponsor Opportunities I (Parallel), LP"]["class_b_shares"])
assert LEGACY + cpc == od
need(f"the {c(LEGACY)} of SC Assets' original shareholders and {c(cpc)} held by two former TLGY sponsor funds")

# awards, warrants and dates
need(f"The directors' {c(directors)} shares also sit outside the freely tradable count. On September 30 the company awarded {c(num('director_restricted_shares_each'))} restricted shares to each of five directors")
need(f"The directors' {c(directors)} shares are already in the October 8 count")
need(f"vest on December 25, 2026 for holders still in service and would then add up to {c(num('rsu_shares_offered'))} shares")
need(f"The stock units add {c(num('rsu_shares_offered'))} shares when they settle")
units = [x for x in load("selling_stockholders_2026-08-28.csv") if x["holder"] == "Chief financial officer"]
need(f"The chief financial officer held {c(int(units[0]['rsus']))} of the units on August 28")
need(f"The {c(num('public_warrants'))} public warrants trade as USDEW, each exercisable for one share at ${fact['public_warrant_strike']}")
need(f"the {c(num('tranche_a_sponsor_warrants') + num('tranche_b_sponsor_warrants'))} sponsor warrants are exercisable at ${fact['public_warrant_strike']} and ${fact['tranche_b_strike']}")
need(f"reserved {c(num('equity_plan_reserve'))} shares in all")
f10 = date.fromisoformat(fact["form10_information_filed"])
need(f"before {date(f10.year + 1, f10.month, f10.day).strftime('%B')} {f10.day}, {f10.year + 1}")
need(f"StablecoinX filed that information on July {f10.day}, {f10.year}")
need(f"The redemption counts differ by {c(-table['Redemption of TLGY Class A common stock'] - num('public_shares_redeemed_8k'))} shares")
par = [x for x in load("selling_stockholders_2026-08-28.csv") if "Parallel" in x["holder"]][0]
need(f"2,999,689 warrants where its totals imply {c(int(par['warrants']))}")

# formula block and chart text
need(f"= {c(PIPE)} − {c(ETH_PIPE)} + {c(public)} = {c(FREE)}")
need(f"= {c(table['Class A common stock of TLGY'])} + {c(table['TLGY Class B common stock outstanding prior to the Merger'])} − {c(RETAINED)} = {c(public)}")
need(f"= {c(total)} ÷ {c(FREE)} = {r(Decimal(total) / FREE, 2)}")
need(f"ends at {r(Decimal(total) / FREE, 2)} times")
need(f"divided by the {c(FREE)} shares the prospectus counted as freely tradable on August 28")
need(f"reaching {r(Decimal(total) / FREE, 2)} times the {c(FREE)} shares the resale prospectus counted as freely tradable", "meta")

print(f"checked {count} phrases")
if missing:
    for where, phrase in missing:
        print(f"MISSING in {where}: {phrase}")
    sys.exit(1)
print("all phrases found")
