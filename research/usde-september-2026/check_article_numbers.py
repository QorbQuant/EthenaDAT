#!/usr/bin/env python3
"""
Checks every computed figure in article_draft.md against the inputs.

Run:  python3 check_article_numbers.py
It recomputes each figure from ./inputs with its own code (closed-form Shapley, not the
permutation loop in usde_sept2026_review.py), formats it the way the article does, and
requires that exact phrase to appear in the article text. Rerun it after any edit to the draft.

Figures taken from SEC filings (cash, liabilities, warrant counts, token count, the company's
June 30 price) are entered below as constants with their source, and only their arithmetic is checked.
"""
import csv
import datetime as dt
import json
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).parent
INP = HERE / "inputs"
ART = (HERE / "article_draft.md").read_text(encoding="utf-8")
MINUS, X = "−", "×"

D = json.loads((INP / "ethenadat_data_759f283.json").read_text())["series"]
row = {d: i for i, d in enumerate(D["date"])}
cg = {"utc0000": {}, "utc2000": {}}
for r in csv.DictReader(open(INP / "ena_coingecko_via_defillama.csv")):
    cg[r["series"]][int(r["unix_ts"])] = float(r["price_usd"])
kraken = {r[0]: float(r[1]) for r in json.loads((INP / "kraken_enausd_4h.json").read_text())["rows"]}
coinbase = list(csv.DictReader(open(INP / "coinbase_ena_usd_hourly_spotchecks.csv")))


def ts(d, hour):
    y, m, dd = map(int, d.split("-"))
    return int(dt.datetime(y, m, dd, hour, tzinfo=dt.timezone.utc).timestamp())


def P(d): return D["usde_close"][row[d]]
def N(d): return D["shares_outstanding"][row[d]]
def H(d): return D["ena_holdings"][row[d]]
def E(d, basis):
    if basis == "dash":
        return D["ena_price"][row[d]]
    if basis == "close":
        return cg["utc2000"][ts(d, 20)]
    nxt = (dt.date.fromisoformat(d) + dt.timedelta(days=1)).isoformat()
    return cg["utc0000"][ts(nxt, 0)]          # "utcday"
def S(d): return H(d) / N(d)
def NAVPS(d, b): return E(d, b) * S(d)
def M(d, b): return P(d) / NAVPS(d, b)


def phi(a, b, basis):
    """Closed-form three-factor Shapley values for P = E*S*M between dates a and b."""
    e0, e1, s0, s1, m0, m1 = E(a, basis), E(b, basis), S(a), S(b), M(a, basis), M(b, basis)
    w = lambda x0, x1, y0, y1: x0 * y0 / 3 + (x1 * y0 + x0 * y1) / 6 + x1 * y1 / 3
    out = ((e1 - e0) * w(s0, s1, m0, m1), (s1 - s0) * w(e0, e1, m0, m1), (m1 - m0) * w(e0, e1, s0, s1))
    assert abs(sum(out) - (P(b) - P(a))) < 1e-9
    return out


def pct(x, n=1): return f"{x * 100:.{n}f}%"
def spct(x, n=1): return ("+" if x >= 0 else MINUS) + f"{abs(x) * 100:.{n}f}%"
def sn(x, n=3): return ("+" if x >= 0 else MINUS) + f"{abs(x):.{n}f}"
def sd(x, n=3): return ("+" if x >= 0 else MINUS) + f"${abs(x):.{n}f}"
def m3(x): return f"{x:.3f}{X}"
def m2(x): return f"{x:.2f}{X}"


A, B, LOW = "2026-08-31", "2026-09-30", "2026-09-16"
sess = [d for d in D["date"] if A <= d <= B]
sept = [d for d in D["date"] if d.startswith("2026-09")]
checks = []
def need(what, phrase): checks.append((what, phrase))

# ---- lede
dP = P(B) - P(A)
c, dsh = phi(A, B, "close"), phi(A, B, "dash")
need("lede close", f"closed September at ${P(B):.2f}, up {pct(P(B)/P(A)-1)} from ${P(A):.2f}")
need("lede ENA", f"rose {pct(E(B,'close')/E(A,'close')-1)} over the same span")
need("lede split", f"accounts for ${c[0]:.2f} of the ${dP:.2f} gain")
need("lede mNAV", f"moved from {m2(M(A,'close'))} to {m2(M(B,'close'))} and accounts for ${c[2]:.2f}")
need("lede shares", f"A {pct(N(B)/N(A)-1, 2)} larger share count subtracts ${abs(c[1]):.2f}")
c28 = phi("2026-08-28", B, "close"); d28 = P(B) - P("2026-08-28")
need("lede window", f"assigns {c28[0]/d28*100:.0f}% of its larger gain to ENA and {c28[2]/d28*100:.0f}% to mNAV")
need("lede dashboard", f"ENA accounts for ${dsh[0]:.2f} and mNAV for ${dsh[2]:.2f}")
need("Aug 31 rise", f"USDE rose {P(A)/P('2026-08-28')*100-100:.0f}% on August 31 itself")

# ---- observations table
need("obs USDE", f"| USDE close | ${P(A):.2f} | ${P(B):.2f} | {spct(P(B)/P(A)-1)} |")
need("obs ENA close", f"| ${E(A,'close'):.5f} | ${E(B,'close'):.5f} | {spct(E(B,'close')/E(A,'close')-1)} |")
need("obs ENA dash", f"| ${E(A,'dash'):.5f} | ${E(B,'dash'):.5f} | {spct(E(B,'dash')/E(A,'dash')-1)} |")
need("obs ENA held", f"| {H(A)/1e9:.3f} billion | {H(B)/1e9:.3f} billion | 0% |")
need("obs shares", f"| {N(A):,.0f} | {N(B):,.0f} | {spct(N(B)/N(A)-1, 2)} |")
need("obs ENA/share", f"| {S(A):.2f} | {S(B):.2f} | {spct(S(B)/S(A)-1, 2)} |")
need("obs NAV close", f"| ${NAVPS(A,'close'):.3f} | ${NAVPS(B,'close'):.3f} | {spct(NAVPS(B,'close')/NAVPS(A,'close')-1)} |")
need("obs NAV dash", f"| ${NAVPS(A,'dash'):.3f} | ${NAVPS(B,'dash'):.3f} | {spct(NAVPS(B,'dash')/NAVPS(A,'dash')-1)} |")
need("obs mNAV close", f"| {m3(M(A,'close'))} | {m3(M(B,'close'))} | +{round(M(B,'close'),3)-round(M(A,'close'),3):.3f}{X} |")
need("obs mNAV dash", f"| {m3(M(A,'dash'))} | {m3(M(B,'dash'))} | +{round(M(B,'dash'),3)-round(M(A,'dash'),3):.3f}{X} |")

# ---- attribution table
need("attr ENA", f"| ENA price | {sn(c[0])} | {pct(c[0]/dP)} | {sn(dsh[0])} | {pct(dsh[0]/dP)} |")
need("attr S", f"| ENA per share | {sn(c[1])} | {spct(c[1]/dP).replace('+','')} | {sn(dsh[1])} | {spct(dsh[1]/dP).replace('+','')} |")
need("attr M", f"| mNAV | {sn(c[2])} | {pct(c[2]/dP)} | {sn(dsh[2])} | {pct(dsh[2]/dP)} |")
need("attr total", f"| USDE change | {sn(dP)} | 100% | {sn(dP)} | 100% |")
need("heading 95%", f"ENA accounts for {c[0]/dP*100:.0f}% of the gain between month ends")

# ---- start date and window table
a28 = "2026-08-28"
need("Aug 31 session", f"from ${P(a28):.2f} to ${P(A):.2f}, while ENA fell {abs(E(A,'close')/E(a28,'close')-1)*100:.0f}%")
need("Aug 31 mNAV", f"lifted mNAV from {m2(M(a28,'close'))} to {m2(M(A,'close'))}")
for d, lab in ((a28, "Aug 28"), (A, "Aug 31, the month end"), ("2026-09-01", "Sep 1")):
    w = phi(d, B, "close"); g = P(B) - P(d)
    need(f"window {lab}", f"| {lab} | {pct(w[0]/g)} | {spct(w[1]/g).replace('+','')} | {pct(w[2]/g)} |")
u = phi(A, B, "utcday")
need("utc day", f"gives ENA {pct(u[0]/dP)} and mNAV {pct(u[2]/dP)}")

# ---- timestamp section
need("Sep 30 gap", f"ENA stood at ${E(B,'dash'):.4f} at the earlier time and ${E(B,'close'):.4f} at the stock close, a gap of {pct(E(B,'close')/E(B,'dash')-1)}")
need("Sep 30 mNAV", f"puts mNAV for that day at {m2(M(B,'dash'))}. Priced at the close it is {m2(M(B,'close'))}")
gaps = {d: E(d, "close") / E(d, "dash") - 1 for d in sess}
wide = max(gaps, key=lambda d: abs(gaps[d]))
assert wide == "2026-09-25"
need("widest gap", "The widest gap of the month fell on September 25")
need("Sep 25", f"ENA rose {pct(gaps[wide])} between the two times and USDE gained {pct(P(wide)/P('2026-09-24')-1)} on the day")
alltime = [d for d in D["date"] if d <= B]
assert max(alltime, key=lambda d: M(d, "dash")) == wide and D["date"][0] == "2026-06-26"
need("Sep 25 dash", f"shows {m2(M(wide,'dash'))} for that date, its highest reading since the June 26 listing")
need("Sep 25 close", f"Priced at the close, mNAV was {m2(M(wide,'close'))}")
for ena, lab in ((0.260069, "first"), (0.268311, "second")):          # repo commits 0efe051 and 04cf641
    both = {f"{P(wide)/(ena*H(wide)/n):.2f}" for n in (24029375, 24110000)}
    assert len(both) == 1, both                                          # same to two decimals on either share count
    need(f"Sep 25 {lab} same-evening print", f"{both.pop()}{X}")
CO_PRICE, CO_NAVPS = 0.07204, 9.09                                       # Q2 release, 8-K Exhibit 99.1 filed Aug 14, 2026
need("June 30 dataset rows", f"shows ${E('2026-06-30','dash'):.4f} for June 30 and ${E('2026-07-01','dash'):.4f} for July 1")
need("June 30 NAV", f"reads ${NAVPS('2026-06-30','dash'):.2f} of token NAV per share")
assert abs(CO_PRICE * S("2026-06-30") - CO_NAVPS) < 0.01               # "to within a cent"
ch = lambda b: [abs(M(sess[i], b) / M(sess[i-1], b) - 1) for i in range(1, len(sess))]
need("noise", f"was {pct(st.median(ch('dash')))} of its level on the dashboard series and {pct(st.median(ch('close')))} at the close. "
              f"The means were {pct(st.mean(ch('dash')))} and {pct(st.mean(ch('close')))}")

# ---- legs
lowc = min(sept, key=P); assert lowc == "2026-09-15"
need("low close", f"low close of the month was ${P(lowc):.2f} on September 15")
assert min(sess, key=lambda d: M(d, "close")) == LOW
need("mNAV low", f"reached its low one session later at {m3(M(LOW,'close'))}")
l1, l2 = phi(A, LOW, "close"), phi(LOW, B, "close")
need("legs USDE", f"| USDE close | ${P(A):.2f} to ${P(LOW):.2f}, {spct(P(LOW)/P(A)-1)} | ${P(LOW):.2f} to ${P(B):.2f}, {spct(P(B)/P(LOW)-1)} |")
need("legs ENA", f"| ENA price | ${E(A,'close'):.5f} to ${E(LOW,'close'):.5f}, {spct(E(LOW,'close')/E(A,'close')-1)} | "
                 f"${E(LOW,'close'):.5f} to ${E(B,'close'):.5f}, {spct(E(B,'close')/E(LOW,'close')-1)} |")
need("legs mNAV", f"| mNAV | {m3(M(A,'close'))} to {m3(M(LOW,'close'))}, {spct(M(LOW,'close')/M(A,'close')-1)} | "
                  f"{m3(M(LOW,'close'))} to {m3(M(B,'close'))}, {spct(M(B,'close')/M(LOW,'close')-1)} |")
need("legs ENA $", f"| ENA price contribution | {sd(l1[0])} | {sd(l2[0])} |")
need("legs mNAV $", f"| mNAV contribution | {sd(l1[2])} | {sd(l2[2])} |")
need("legs S $", f"| ENA per share contribution | ${abs(l1[1]):.3f} | {sd(l2[1])} |")
need("fall share", f"mNAV accounts for {l1[2]/(P(LOW)-P(A))*100:.0f}% of the fall to September 16")
s18 = "2026-09-18"
need("two sessions", f"rose from {m3(M(LOW,'close'))} to {m3(M(s18,'close'))} in two sessions, September 17 and 18")
need("after Sep 18", f"moved only to {m3(M(B,'close'))} while the stock rose {P(B)/P(s18)*100-100:.0f}% and ENA rose {E(B,'close')/E(s18,'close')*100-100:.0f}%")
need("chain", f"mNAV fell {pct(1-M(LOW,'close')/M(A,'close'))} and then rose {pct(M(B,'close')/M(LOW,'close')-1)}, a net gain of {pct(M(B,'close')/M(A,'close')-1)}")
gap = lambda d: (E(d, "close") * H(d) - P(d) * N(d)) / 1e6
need("dollar gap", f"grew from ${gap(A):.0f} million to ${gap(B):.0f} million over the month, while mNAV rose by {round(M(B,'close'),3)-round(M(A,'close'),3):.3f}{X}")

# ---- share count, warrants, lock-ups (filing constants, arithmetic checked here)
TOK_10Q = 284954407.29 + 1405754435.84 + 1340695577.81                  # 10-Q Note 3
need("10-Q tokens", f"that sum to {TOK_10Q:,.0f} tokens, {pct(TOK_10Q/H(B)-1, 2)} more")
need("10-Q effect", f"would raise ENA per share and token NAV per share by {pct(TOK_10Q/H(B)-1, 2)}")
need("director shares", f"{N(B)-N(A):,.0f} restricted shares awarded to five directors")
assert N(B) - N(A) == 5 * 22000                                          # five Forms 4, 22,000 each
need("derived count", f"so the September 30 figure of {N(B):,.0f} is derived")
need("per million", f"lowers ENA per share by about {(1-N(B)/(N(B)+1e6))*100:.0f}%")
PUB, SP1150, SP1500 = 11500000, 3267679, 4356907                         # 424B3 cover, Sep 14, 2026
need("warrant shares", f"covers {PUB+SP1150+SP1500:,} shares under warrants, against {N(B):,.0f} Class A shares")
need("warrant strikes", f"{PUB+SP1150:,} carry an $11.50 exercise price and {SP1500:,} carry $15.00")
assert P(A) < 11.50                                                      # all out of the money at the Aug 31 close
f1150 = next(d for d in D["date"] if P(d) is not None and P(d) > 11.50)
f1500 = next(d for d in D["date"] if P(d) is not None and P(d) > 15.00)
assert (f1150, f1500) == ("2026-09-21", "2026-09-25")
need("first closes", "USDE first closed above $11.50 on September 21 and above $15.00 on September 25")
cash = (PUB + SP1150) * 11.50 + SP1500 * 15.00
need("full exercise", f"would add {(PUB+SP1150+SP1500)/N(B)*100:.0f}% to the share count and raise about ${cash/1e6:.0f} million")
ge10 = [d for d in D["date"] if d <= B and P(d) is not None and P(d) >= 10.00]
assert len(ge10) == 9 and ge10[0] == "2026-09-18"
need("qualifying closes", "Nine qualifying closes had accrued by September 30")
need("sponsor warrants", f"The {(SP1150+SP1500)/1e6:.1f} million sponsor warrants may be exercised without cash")
assert max(P(d) for d in sess) < 18.00                                   # no close at or above $18.00 in the window
need("no $18 close", "USDE had no close at or above $18.00 in the window")
ge10_all = [d for d in D["date"] if P(d) is not None and P(d) >= 10.00]
assert ge10_all[9] == "2026-10-01" and ge10_all[10] == "2026-10-02"      # the tenth and eleventh closes at or above $10.00
assert P("2026-10-01") > 10 and P("2026-10-02") > 10
need("after cutoff", "USDE closed above $10.00 again on October 1 and October 2, the tenth and eleventh such closes")
CASH, LIAB, WLIAB, DIGITAL = 18856144, 18292004, 4715000, 212918841      # 10-Q balance sheet at June 30, 2026
need("cash and liabilities", f"${CASH/1e6:.1f} million of cash and ${LIAB/1e6:.1f} million of total liabilities")
need("warrant liability", f"a ${WLIAB/1e6:.1f} million warrant liability")
w0, w1 = D["usdew_close"][row["2026-06-30"]], D["usdew_close"][row[B]]
assert abs(PUB * w0 - WLIAB) < 0.5                                       # liability = 11,500,000 x the June 30 close
need("USDEW closes", f"closed June at ${w0:.2f} and September at ${w1:.2f}")
need("warrants now", f"the same {PUB/1e6:.1f} million warrants come to about ${PUB*w1/1e6:.0f} million")
need("carrying value", f"${DIGITAL/1e6:.1f} million at June 30")

# ---- cross-checks quoted in the last section
chk = [d for d in D["date"] if "2026-08-28" <= d <= "2026-10-02"]
assert all(ts(d, 20) in kraken for d in chk) and len(chk) == 25           # every session from Aug 28 to Oct 2 has a Kraken candle
k = max(abs(kraken[ts(d, 20)] / E(d, "close") - 1) for d in chk)
cbx = max(abs(float(r["open"]) / cg["utc2000"][int(r["unix_ts"])] - 1) for r in coinbase)
need("Kraken", f"within {pct(k, 2)} of Kraken's price at the same time on every session from August 28 to October 2")
need("Coinbase", f"within {pct(cbx, 2)} of Coinbase on five dates checked")
assert len(coinbase) == 5

bad = [(w, p) for w, p in checks if p not in ART]
for w, p in checks:
    print(("ok   " if p in ART else "MISS ") + f"{w:28s} {p}")
print(f"\n{len(checks) - len(bad)} of {len(checks)} phrases found in article_draft.md")
sys.exit(1 if bad else 0)
