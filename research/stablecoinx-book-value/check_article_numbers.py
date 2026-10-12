#!/usr/bin/env python3
"""
Recomputes every computed figure in article_draft.md, metadata.json and the chart's text from the
files in inputs/, with code written apart from stablecoinx_book_value_review.py, and confirms that
each exact phrase appears. Exits with an error if a phrase is missing or an assertion fails, so
rerun it after any edit. Python 3 standard library only. No network.
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
SVG = (HERE / "out" / "chart_book_value.svg").read_text()
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
    return ("-" if x < 0 else "") + out


def comma(x, places=0):
    s = rnd(x, places)
    whole, _, frac = s.partition(".")
    whole = f"{int(whole):,}"
    return whole + ("." + frac if frac else "")


def md(d):
    return f"{d:%B} {d.day}"


fact = {r["id"]: r["value"] for r in rows("filing_facts.csv")}


def v(k):
    return F(fact[k])


# ---------------------------------------------------------------- headline figures
equity = v("total_stockholders_equity")
A = v("class_a_shares_june30")
B = v("class_b_shares_cover")
ena = v("digital_intangible_assets")
assert equity == v("total_assets") - v("total_liabilities")
bvps = equity / A
need(f"StablecoinX's book value, its total assets less total liabilities, was ${rnd(equity / 10**6, 1)} million at June 30, 2026, "
     f"or ${rnd(bvps, 2)} per Class A share, in the balance sheet of its second-quarter report on Form 10-Q.")
need(f"ENA, the Ethena governance token the company holds as its treasury, accounted for ${rnd(ena / 10**6, 1)} million of it.")
tokens = v("ena_tokens_contribution") + v("ena_tokens_pipe_initial") + v("ena_tokens_pipe_additional")
carry = ena / tokens
need(f"The 10-Q lists three lots of ENA received at the merger, {comma(tokens)} tokens in all.")

# Kraken daily lows
daily = rows("kraken_enausd_daily.csv")
lows = {r["date_utc"]: F(r["low"]) for r in daily}
to_j30 = {d: x for d, x in lows.items() if "2026-06-25" <= d <= "2026-06-30"}
low_j30 = min(to_j30.values())
assert [d for d, x in to_j30.items() if x == low_j30] == ["2026-06-30"]
assert rnd(carry, 4) == rnd(low_j30, 4) == "0.0702" and carry > low_j30
need(f"The company carries ENA at cost less impairment, ${rnd(carry, 5)} a token at June 30. That is close to ${rnd(low_j30, 4)}, "
     "ENA's lowest trade on Kraken, a crypto exchange, between the June 25 merger and June 30.")
need(f"ENA's lowest trade on Kraken from June 25 to June 30 was ${rnd(low_j30, 4)}, on June 30, ${rnd(carry - low_j30, 5)} below the "
     "carrying value per token, so the company's write-down price was not Kraken's lowest ENA/USD trade.")
assert all(len(r["low"].split(".")[1]) == 4 for r in daily)

# sessions, built from the Nasdaq calendar: Independence Day observed on Friday July 3 and Labor Day on September 7
holidays = {date(2026, 7, 3), date(2026, 9, 7)}
sessions = []
d = date(2026, 6, 30)
while d <= date(2026, 10, 8):
    if d.weekday() < 5 and d not in holidays:
        sessions.append(d.isoformat())
    d += timedelta(days=1)
assert len(sessions) == 71
assert all("2026-03-08" < s < "2026-11-01" for s in sessions)  # daylight saving time, so 4 pm is 20:00 UTC
usde = {r["date"]: F(r["close"]) for r in rows("usde_daily_spglobal_stockanalysis.csv")}
usdew = {r["date"]: F(r["close"]) for r in rows("usdew_daily_spglobal_stockanalysis.csv")}
assert all(s in usde for s in sessions)
close20 = {}
for r in rows("kraken_enausd_4h_20utc_00utc.csv"):
    if r["start_utc"][11:13] == "16":
        close20[r["start_utc"][:10]] = F(r["close"])
dash = {r["date"]: r for r in rows("dashboard_series_dda5a00.csv")}


def shares_on(day):
    # 24,029,375 until the five directors' restricted shares of September 30
    return A + (5 * v("director_award_shares") if day >= "2026-09-30" else 0)


assert all(F(dash[s]["shares_outstanding"]) == shares_on(s) for s in sessions)
per = {s: close20[s] * tokens / shares_on(s) for s in sessions}
o8, j30 = "2026-10-08", "2026-06-30"
mv_o8 = close20[o8] * tokens
need(f"At the October 8 close the reported tokens were worth ${rnd(mv_o8 / 10**6, 1)} million at Kraken's price, "
     f"{rnd(mv_o8 / ena, 1)} times their carrying value, which put token NAV per share at ${rnd(per[o8], 2)}.")
need(f"USDE closed that day at ${rnd(usde[o8], 2)}, which was {rnd(usde[o8] / bvps, 2)} times June 30 book value per share and "
     f"{rnd(usde[o8] / per[o8], 2)} times token NAV per share.")
need(f"USDE closed Oct 8 at {rnd(usde[o8] / bvps, 2)} times that figure.", META["description"])
need(f"StablecoinX's June 30, 2026 book value was ${rnd(bvps, 2)} per Class A share, with ENA carried at about "
     f"${rnd(carry, 4)} a token.", META["description"])

# ---------------------------------------------------------------- the balance-sheet table
cash = v("cash")
other_a = v("total_assets") - ena - cash
notes = v("sponsor_convertible_demand_notes")
other_l = v("total_liabilities") - notes - v("accrued_expenses") - v("warrant_liability")
table = [("ENA, at cost less impairment", ena), ("Cash", cash), ("Other assets", other_a), ("Total assets", v("total_assets")),
         ("Convertible notes owed to former sponsors", notes), ("Accrued expenses", v("accrued_expenses")),
         ("Warrant liability", v("warrant_liability")), ("Other liabilities", other_l),
         ("Total liabilities", v("total_liabilities")), ("Book value", equity)]
for label, x in table:
    need(f"| {label} | {rnd(x / 10**6, 1)} |")
# the rounded rows also add up
assert F(rnd(ena / 10**6, 1)) + F(rnd(cash / 10**6, 1)) + F(rnd(other_a / 10**6, 1)) == F(rnd(v("total_assets") / 10**6, 1))
assert sum(F(rnd(x / 10**6, 1)) for _, x in table[4:8]) == F(rnd(v("total_liabilities") / 10**6, 1))
assert F(rnd(v("total_assets") / 10**6, 1)) - F(rnd(v("total_liabilities") / 10**6, 1)) == F(rnd(equity / 10**6, 1))
net_other = equity - ena
need(f"Everything other than ENA, net of all liabilities, came to ${rnd(net_other / 10**6, 2)} million, or ${rnd(net_other / A, 2)} "
     "per Class A share.")
need(f"Cash of ${rnd(cash / 10**6, 1)} million slightly exceeded total liabilities of ${rnd(v('total_liabilities') / 10**6, 1)} million.")
assert cash > v("total_liabilities")
assert v("software_license_net") + v("capitalized_software") == v("intangible_assets_net")
assert other_a == v("intangible_assets_net") + v("digital_assets_restricted") + v("digital_assets_receivable_related_party") + \
    v("prepaid_insurance") + v("prepaid_and_other_current")
need(f"The other assets were ${comma(v('intangible_assets_net'))} of software, {fact['eth_restricted_tokens']} restricted ETH worth "
     f"${comma(v('eth_restricted_fair_value'))}, ${comma(v('prepaid_insurance') + v('prepaid_and_other_current'))} of prepaid expenses "
     f"and other current assets, and a receivable of ${comma(v('digital_assets_receivable_related_party'))} from Ethena.")
assert fact["dvn_fees_paid_in"] == "ENA tokens" and v("dvn_revenue_q2") == v("digital_assets_receivable_related_party")
need("That receivable equals the quarter's fees for the company's decentralized verifier node")
need("and Ethena pays those fees in ENA.")
need(f"The warrant liability was the value of the {comma(v('public_warrants_at_closing'))} public warrants")
need(f"The 10-Q leaves the {comma(B)} Class B shares out of its loss per share")
need(f"Divided across both classes, book value would come to ${rnd(equity / (A + B), 2)} a share.")

# ---------------------------------------------------------------- cost and impairment
cost = v("ena_value_contribution") + v("ena_value_pipe_initial") + v("ena_value_pipe_additional")
assert abs(cost - v("ena_gross_carrying")) < 1
prices = [v("ena_value_contribution") / v("ena_tokens_contribution"), v("ena_value_pipe_initial") / v("ena_tokens_pipe_initial"),
          v("ena_value_pipe_additional") / v("ena_tokens_pipe_additional")]
assert len({rnd(p, 6) for p in prices}) == 1
need(f"Cost was ${rnd(v('ena_gross_carrying') / 10**6, 1)} million, the June 25 value of the three lots of ENA received at the merger, "
     f"and each lot works out to ${rnd(prices[0], 5)} a token.")
assert v("ena_gross_carrying") - v("impairment_q2") == ena
need(f"The second quarter's impairment was ${rnd(v('impairment_q2') / 10**6, 1)} million, which left ${rnd(ena / 10**6, 1)} million, "
     f"or ${rnd(carry, 5)} a token.")
assert "related party" in fact["ena_outside_fair_value_scope"]
need("The 10-Q says ENA falls outside ASC 350-60")
need(f"The {fact['eth_restricted_tokens']} ETH fall within ASC 350-60, so the company carries them at fair value.")

# the results release
rel = tokens * v("release_ena_price")
assert rnd(rel / 10**6, 1) == "218.4" and rnd(rel / A, 2) == "9.09"
need(f"The results release of August 14 priced the same tokens at ${fact['release_ena_price']}, which it called ENA's closing price on June 30.")
kday = {r["date_utc"]: F(r["close"]) for r in daily}
assert abs(kday["2026-06-30"] - v("release_ena_price")) < F(1, 10000)
need(f"That price sits near Kraken's ${rnd(kday['2026-06-30'], 4)} at the end of the UTC day, hours after the 4 pm New York close of "
     f"${rnd(close20['2026-06-30'], 4)} used below.")
need(f"The release put the ENA at ${rnd(rel / 10**6, 1)} million, or about ${rnd(rel / A, 2)} per Class A share")
gap_price = rel - ena
gap_book = rel - equity
assert gap_book == gap_price - (equity - ena)
assert F(comma(gap_price).replace(",", "")) - (equity - ena) == F(comma(gap_book).replace(",", ""))
need(f"Rebuilt from the 10-Q's lots, the release's figure is ${comma(rel)}, and book value came to ${comma(gap_book)} less. Carrying "
     f"ENA at ${rnd(carry, 5)} a token instead of ${fact['release_ena_price']} took ${comma(gap_price)} off, and everything other than "
     f"ENA, net of all liabilities, added back ${comma(equity - ena)}.")

# ---------------------------------------------------------------- the sessions
need(f"At the June 30 close ENA was ${rnd(close20[j30], 4)} on Kraken, which put token NAV per share at ${rnd(per[j30], 2)}, "
     "the same as book value per share to the cent.")
assert rnd(per[j30], 2) == rnd(bvps, 2)
need(f"USDE closed at ${rnd(usde[j30], 2)}, or {rnd(usde[j30] / bvps, 2)} times book value per share.")
lowest = min(sessions, key=lambda s: usde[s])
need(f"Its lowest close came on {md(date.fromisoformat(lowest))}, at ${rnd(usde[lowest], 2)}, or {rnd(usde[lowest] / bvps, 2)} times "
     "book value per share.")
above = [s for s in sessions if usde[s] > bvps]
first = above[0]
assert above == [s for s in sessions if s >= first]
need(f"USDE first closed above ${rnd(bvps, 2)} on {md(date.fromisoformat(first))}, at ${rnd(usde[first], 2)}, and closed above it at "
     f"all {len(above)} sessions from then to October 8.")
need(f"## USDE closed above June 30 book value from {md(date.fromisoformat(first))} to October 8")
peak = max(sessions, key=lambda s: per[s])
top = max(sessions, key=lambda s: usde[s])
assert peak == top
need(f"Token NAV per share peaked at ${rnd(per[peak], 2)} on {md(date.fromisoformat(peak))}, the day of "
     f"USDE's highest close, ${rnd(usde[top], 2)}, or {rnd(usde[top] / bvps, 2)} times book value per share.")
ratios = [usde[s] / per[s] for s in sessions]
assert max(ratios) < 1
need(f"At every close from June 30 to October 8, USDE was below token NAV per share, at {rnd(min(ratios), 2)} to "
     f"{rnd(max(ratios), 2)} times.")
# the chart's own text
need(f"USDE closed above June 30 book value per share from {md(date.fromisoformat(first))}", SVG)
need(f"${rnd(per[o8], 2)} on Oct 8", SVG)
need(f"${rnd(usde[o8], 2)} on Oct 8", SVG)
need(f"Sep 18, ${rnd(usde[first], 2)}", SVG)
need(f"${rnd(bvps, 2)} at June 30", SVG)
need(f"a high of ${rnd(per[peak], 2)} on {md(date.fromisoformat(peak))}", SVG)
need(f"a high of ${rnd(per[peak], 2)} on {md(date.fromisoformat(peak))}", META["imageAlt"])
need(f"was ${rnd(per[o8], 2)} on October 8", META["imageAlt"])
need(f"USDE's close rose from ${rnd(usde[j30], 2)}, passed June 30 book value per share of ${rnd(bvps, 2)} on "
     f"{md(date.fromisoformat(first))} and was ${rnd(usde[o8], 2)} on October 8.", META["imageAlt"])
need(f"Token NAV per share, with ENA at its 4 pm price, rose from ${rnd(per[j30], 2)}", META["imageAlt"])
need("Token NAV per share", SVG)
alt_md = ARTICLE.split("![")[1].split("](")[0]
need(f"Token NAV per share at ENA's price at the 4 pm close, ${rnd(per[j30], 2)} on June 30, a high of ${rnd(per[peak], 2)} on "
     f"{md(date.fromisoformat(peak))} and ${rnd(per[o8], 2)} on October 8.", alt_md)
need(f"Token NAV per share on {comma(A)} Class A shares to September 29 and a derived {comma(shares_on('2026-09-30'))} from September 30")
need(f"USDE's close, ${rnd(usde[j30], 2)} on June 30, first above book value on {md(date.fromisoformat(first))} at "
     f"${rnd(usde[first], 2)}, and ${rnd(usde[o8], 2)} on October 8.", alt_md)
need(f"Book value per Class A share at June 30, ${rnd(bvps, 2)}, flat across the chart.", alt_md)

# ---------------------------------------------------------------- after June 30
pa, pb = v("sponsor_tranche_a_share") / 100, v("sponsor_tranche_b_share") / 100
ta, tb = notes * pa / v("sponsor_tranche_a_warrant_price"), notes * pb / v("sponsor_tranche_b_warrant_price")
assert int(ta) == v("tranche_a_warrants") and abs(tb - v("tranche_b_warrants")) < 2
need(f"Applied to the ${comma(notes)} on the balance sheet, those percentages give the {comma(v('tranche_a_warrants'))} Tranche A "
     f"warrants in the resale prospectus of September 14, its {comma(v('tranche_b_warrants'))} Tranche B warrants to within two, and "
     f"${comma(notes * v('sponsor_cash_share') / 100)} in cash.")
need(f"On August 21 it agreed to pay {fact['sponsor_cash_share']}% of their original principal in cash, {fact['sponsor_tranche_a_share']}% "
     f"in Tranche A warrants priced at ${fact['sponsor_tranche_a_warrant_price']} each and {fact['sponsor_tranche_b_share']}% in Tranche B "
     f"warrants priced at ${fact['sponsor_tranche_b_warrant_price']} each")
pw = v("public_warrants_at_closing")
assert round(pw * usdew["2026-06-30"], -3) == v("warrant_liability")
need(f"At USDEW's June 30 close of ${rnd(usdew['2026-06-30'], 2)}, the {comma(pw)} public warrants come to the "
     f"${comma(v('warrant_liability'))} on the balance sheet, to the nearest thousand dollars.")
rise = pw * usdew["2026-09-30"] - v("warrant_liability")
need(f"At USDEW's September 30 close of ${rnd(usdew['2026-09-30'], 2)}, the same method gives "
     f"${rnd(pw * usdew['2026-09-30'] / 10**6, 1)} million, ${rnd(rise / 10**6, 1)} million more than at June 30 and equal to "
     f"{rnd(rise / equity * 100, 0)}% of June 30 book value.")
need(f"Five directors each received {comma(v('director_award_shares'))} restricted Class A shares on September 30")
need(f"Added to the {comma(A)} shares on the 10-Q's cover, they give {comma(shares_on('2026-09-30'))}, a derived count that no filing states.")
assert v("class_a_shares_cover") == A
q3 = {d: x for d, x in lows.items() if "2026-07-01" <= d <= "2026-09-30"}
lq3 = min(q3.values())
dq3 = [d for d, x in q3.items() if x == lq3]
assert dq3 == ["2026-07-01"] and lq3 > carry
need(f"Kraken's lowest ENA trade from July 1 to September 30 was ${rnd(lq3, 4)}, on July 1, {rnd((lq3 / carry - 1) * 100, 1)}% above "
     f"the carrying value of ${rnd(carry, 5)}.")
need(f"whether ENA traded below ${rnd(carry, 5)} elsewhere in the quarter.")
fil = rows("edgar_filings_2026-10-09.csv")
assert max(r["filing_date"] for r in fil) == "2026-10-02"
need("The company's filing list, read at 21:02 UTC on October 9, showed nothing filed after the directors' Forms 4.")

# ---------------------------------------------------------------- method
assert all(abs(F(dash[s]["usde_close"]) - usde[s]) < F(1, 200) for s in sessions)
need(f"USDE's matched this site's dataset at all {len(sessions)} sessions from June 30 to October 8.")
need(f"Per-share figures divide by Class A shares, the reported {comma(A)} to September 29 and the derived "
     f"{comma(shares_on('2026-10-01'))} from September 30")
held = F(dash[o8]["ena_holdings"])
assert held == 3029000000
need(f"Token NAV here uses the {comma(tokens)} ENA in the 10-Q's three lots.")
need(f"used {comma(held)} ENA, the approximate figure in the merger press release and {rnd((1 - held / tokens) * 100, 2)}% fewer than "
     "the 10-Q's lots.")
dm = F(dash[o8]["mnav"])
dp = F(dash[o8]["ena_price"])
assert abs(usde[o8] / (held * dp / shares_on(o8)) - dm) < F(1, 1000)
need(f"It priced ENA at 00:00 UTC, which put USDE at {rnd(dm, 2)} times token NAV per share on October 8.")
need("In its dataset generated at 18:45 UTC on October 9")
need(f"add no shares for the {comma(pw)} public warrants or the {comma(v('tranche_a_warrants') + v('tranche_b_warrants'))} Tranche A "
     "and B warrants")

# ---------------------------------------------------------------- formula block
need(f"= {comma(equity)} ÷ {comma(A)} = ${rnd(bvps, 2)} at June 30")
need(f"= {comma(ena)} ÷ {comma(tokens, 2)} = ${rnd(carry, 5)} at June 30")
need(f"= {rnd(close20[o8], 4)} × {comma(tokens, 2)} ÷ {comma(shares_on(o8))} = ${rnd(per[o8], 2)} on October 8")
need(f"= {rnd(usde[o8], 2)} ÷ {rnd(bvps, 2)} = {rnd(usde[o8] / F(rnd(bvps, 2)), 2)} on October 8")

# ---------------------------------------------------------------- headings, title, cutoff and closing line
for h in ("# What is StablecoinX's book value per share?", "## ENA made up almost all of the June 30 balance sheet",
          "## The 10-Q carries ENA close to its lowest trade since the merger", "## What changed after June 30",
          "## How this review counts", "## What these figures leave out", "## Reproduce the numbers"):
    need(h, ARTICLE)
need("StablecoinX Book Value per Share: June 30, 2026 10-Q", META["title"])
need("Analysis of public market data. Not investment advice.", ARTICLE)
need("Balance sheet at June 30, 2026 · Prices to the October 8, 2026 close · Sources read October 6 to 9, 2026 UTC", ARTICLE)
if LAYOUT is not None:
    need("Balance sheet at June 30, 2026 · Prices to the October 8, 2026 close · Sources read October 6 to 9, 2026 UTC",
         LAYOUT["cutoff"])

print(f"{found} phrases found")
if missing:
    print("MISSING:")
    for m in missing:
        print("  " + m)
    sys.exit(1)
