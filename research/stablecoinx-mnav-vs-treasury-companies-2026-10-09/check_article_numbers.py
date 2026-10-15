#!/usr/bin/env python3
"""
Recomputes every computed figure in article_draft.md, metadata.json, layout.json and the chart's text from the files in
inputs/, with code written apart from dat_mnav_review.py, and confirms that each exact phrase appears. Counts that the
article quotes from filings are taken from the quoted passages in inputs/filings/sec_quotes_2026-10-12.csv, not from
inputs/facts.csv. It also checks the article's punctuation rules. Exits with an error if a phrase is missing or an
assertion fails, so rerun it after any edit. Python 3 standard library only. No network.
"""
import csv
import json
import re
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).parent
ARTICLE = (HERE / "article_draft.md").read_text()
META = json.loads((HERE / "metadata.json").read_text())
LAYOUT = json.loads((HERE / "layout.json").read_text())
SVG = (HERE / "out" / "chart_mnav_peers.svg").read_text()
FINDINGS = "\n".join(LAYOUT["keyFindings"])
TEXT = ARTICLE + "\n" + "\n".join(META[k] for k in ("title", "headline", "description", "imageAlt")) + "\n" + SVG + "\n" + FINDINGS
found, missing = 0, []


def need(phrase, where=TEXT):
    global found
    if phrase in where:
        found += 1
    else:
        missing.append(phrase)


def load(rel):
    with open(HERE / rel, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def rnd(x, places):
    """Round a non-negative Fraction half up to a number of decimal places and return a string with thousands separators."""
    q = Fraction(x) * 10 ** places
    assert q >= 0, "rnd takes non-negative numbers"
    n = int(q) + (1 if q - int(q) >= Fraction(1, 2) else 0)
    whole, frac = divmod(n, 10 ** places)
    return f"{whole:,}" + (f".{str(frac).rjust(places, '0')}" if places else "")


def F(s):
    return Fraction(s.replace(",", ""))


# ---------------------------------------------------------------- counts, from the quoted passages
QROWS = load("inputs/filings/sec_quotes_2026-10-12.csv")
Q = {r["fact"]: r["quote"] for r in QROWS}
assert all(r["found"] == "true" for r in QROWS)


def grab(fact, pattern, group=1):
    m = re.search(pattern, Q[fact])
    assert m, (fact, pattern)
    return F(m.group(group))


usde_tokens = grab("usde_ena", r"approximately ([\d,]+) million ENA") * 1_000_000
usde_class_a = grab("usde_class_a_aug28", r"offering ([\d,]+) shares of Class A Common Stock \(as of August 28, 2026\)")
assert usde_class_a == grab("usde_class_a_aug12", r"2026, ([\d,]+) shares of Class A")
usde_warrants = grab("usde_class_a_aug28", r"issuance of ([\d,]+) shares of Class A Common Stock upon exercise")
usde_rsus = grab("usde_class_a_aug28", r"Warrants and ([\d,]+) shares of Class A Common Stock upon vesting")
usde_class_b = grab("usde_class_b_count", r"and ([\d,]+) shares of Class B")
assert "not entitled to participate in dividends or receipt of any of the Company’s assets" in Q["usde_class_b_rights"]
f4 = load("inputs/carried/form4_director_awards_2026-10-02.csv")
awards = sum(F(x["shares"]) for x in f4)
usde_shares = usde_class_a + awards
mstr_btc = grab("mstr_btc_oct4", r"\(2\) ([\d,]+)$")
m = re.search(r"there were an aggregate of ([\d,]+) shares of our Class A Stock and ([\d,]+) shares of our Class B", Q["mstr_record_shares"])
mstr_a, mstr_b = F(m.group(1)), F(m.group(2))
mstr_oct = grab("mstr_sales_oct1_4", r"MSTR Stock ([\d,]+) ")
mstr_sep = grab("mstr_sales_sep21_27", r"MSTR Stock ([\d,]+) ")
assert Q["mstr_sales_sep28_30"].startswith("During Period September 28, 2026 to September 30, 2026")
assert "MSTR Stock - $ - $ - $ 18,844.4 Class A Common Stock" in Q["mstr_sales_sep28_30"]      # no class A sales September 28 to 30
mstr_shares = mstr_a + mstr_b + mstr_oct
mstr_stre = grab("mstr_stre", r"there were ([\d,]+) shares of STRE")
asst_btc = grab("asst_btc", r"held([\d,]+) ([\d,]+) ", 2)
m = re.search(r"\(2\)(\d{1,3}(?:,\d{3})+)(\d{1,3}(?:,\d{3})+)(\d{1,3}(?:,\d{3})+)$", Q["asst_shares"])
asst_shares = F(m.group(2))
m = re.search(r"SATA Stock(\d{1,3}(?:,\d{3})+)(\d{1,3}(?:,\d{3})+)(\d{1,3}(?:,\d{3})+)$", Q["asst_sata_shares"])
asst_sata = F(m.group(2))
asst_cash = grab("asst_cash", r"\$[\d,]+ \$([\d,]+) ") * 1000
asst_strc = grab("asst_strc", r"\$[\d,]+ \$([\d,]+) ") * 1000
sata_stated = grab("asst_balance_sep30", r"SATA stated amount \(in thousands\)\$([\d,]+)$") * 1000
assert "Debt and Preferred Debt principal balance (in thousands)$—" in Q["asst_balance_sep30"]
sata_sep30 = grab("asst_sata_sep30", r"and ([\d,]+) shares of SATA Stock outstanding")
fwd_sol = grab("fwdi_sol", r"\* ([\d,]+) \$")
fwd_px30 = grab("fwdi_sol", r"\$([\d.]+) \$")
fwd_shares = grab("fwdi_common", r"Common shares ([\d,]+) ")
fwd_close30 = grab("fwdi_common", r" \$([\d.]+) \$")
fwd_fd = grab("fwdi_fully_diluted", r"count ([\d,]+) ")
fwd_other = grab("fwdi_other", r"Various \$([\d,]+)$")
fwd_cash = grab("fwdi_cash", r"^Cash \$([\d,]+) ")
fwd_debt = grab("fwdi_debt", r"\(\$([\d,]+)\)$")
fwd_nav = grab("fwdi_nav", r"\$([\d,]+)$")
hy_gross = grab("hypd_gross_sep30", r"aggregate of ([\d.]+) million Gross HYPE") * 1_000_000
assert grab("hypd_sep30", r"owned ([\d.]+) million Gross HYPE") * 1_000_000 == hy_gross
hy_shares = grab("hypd_sep30", r"approximately ([\d,]+) outstanding HYPD common shares")
hy_cash = grab("hypd_sep30", r"held \$([\d.]+) million in cash") * 1_000_000
hy_sold = grab("hypd_gross_sep30", r"sold a total of ([\d,]+) HYPE")
hy_jun30 = grab("hypd_reconciliation", r"Gross HYPE Tokens\(2\) ([\d,]+)$")
parts = [grab("hypd_reconciliation", p) for p in (r"HYPE digital assets [\d,]+ ([\d,]+) ", r"HiHYPE at Carrying Value [\d,]+ ([\d,]+) ",
                                                     r"kHYPE at Carrying Value [\d,]+ ([\d,]+) ", r"kmHYPE at Carrying Value [\d,]+ ([\d,]+) ",
                                                     r"reconversion\(11\) [\d,]+ ([\d,]+) ")]
assert sum(parts) == hy_jun30
hy_pref = grab("hypd_preferred", r"^([\d,]+) and")
hy_liq = grab("hypd_preferred", r"liquidation preference of \$([\d,]+) ")
assert "convertible into three shares of common stock" in Q["hypd_conversion"]
hy_conv_shares = hy_shares + 3 * hy_pref
assert "can be traded, sold, or redeemed for HYPE" in Q["hypd_lst_def"]
bm_shares = grab("bmnr_shares_jul9", r"was ([\d,]+) shares")
bm_eth = grab("bmnr_eth_oct4", r"of ([\d,]+) ETH")
bm_eth_aug = grab("bmnr_eth_aug16", r"of ([\d,]+) ETH")
bm_cash = grab("bmnr_cash_oct4", r"of \$([\d,]+) million") * 1_000_000
bm_cash_aug = grab("bmnr_cash_aug16", r"of \$([\d,]+) million") * 1_000_000
bm_buyback = grab("bmnr_buyback", r"repurchased ([\d.]+) million") * 1_000_000
assert Q["bmnr_buyback_dates"].startswith("On July 14th, Bitmine began a stock buyback")
purr_hype = grab("purr_hype_sep8", r"approximately ([\d.]+) million HYPE") * 1_000_000
purr_sep8 = grab("purr_shares_sep8", r"Offering ([\d,]+) shares as of September 8")
purr_sep30 = grab("purr_shares_sep30", r"we had ([\d,]+) issued")
mpu_ena = grab("mpu_ena", r"held ([\d,]+) and")
mpu_val = grab("mpu_total", r"ENA ([\d,]+) ")
mpu_total = grab("mpu_total", r"ETH 1,600 - \$ ([\d,]+) \$")
mstr_reserve = grab("mstr_usd_reserve", r"were \$([\d.]+) billion") * 1_000_000_000
mstr_cash = grab("mstr_usd_reserve", r"and \$([\d.]+) million") * 1_000_000
bv = {r["id"]: F(r["value"]) for r in load("inputs/carried/stablecoinx_10q_facts_from_book_value_review.csv") if r["unit"] in ("usd", "tokens", "shares")}
usde_10q_tokens = bv["ena_tokens_contribution"] + bv["ena_tokens_pipe_initial"] + bv["ena_tokens_pipe_additional"]

# ---------------------------------------------------------------- prices
Y = {(r["ticker"], r["session_date"]): r for r in load("inputs/prices/yahoo_daily_2026-10-08_09.csv")}
close = {t: Fraction(rnd(F(Y[(t, "2026-10-09")]["close"]), 2)) for t in ("USDE", "MSTR", "ASST", "FWDI", "HYPD", "BMNR")}
SA = {r["ticker"]: r for r in load("inputs/prices/stockanalysis_closes_read_2026-10-12.csv")}
assert all(close[t] == F(SA[t]["close_2026_10_09"]) for t in close)
K = {(r["token"], r["start_utc"]): F(r["close"]) for r in load("inputs/prices/kraken_1h_2026-10-09_19utc_20utc.csv")}
px = {t: K[(t, "2026-10-09T19:00:00Z")] for t in ("BTC", "ETH", "SOL", "ENA", "HYPE")}
G = {r["token"]: F(r["price_usd"]) for r in load("inputs/prices/coingecko_via_defillama_2026-10-09_20utc.csv")}

# ---------------------------------------------------------------- the five companies
comp = {
    "HYPD": (hy_gross, hy_shares, close["HYPD"], px["HYPE"]),
    "USDE": (usde_tokens, usde_shares, close["USDE"], px["ENA"]),
    "FWDI": (fwd_sol, fwd_shares, close["FWDI"], px["SOL"]),
    "MSTR": (mstr_btc, mstr_shares, close["MSTR"], px["BTC"]),
    "ASST": (asst_btc, asst_shares, close["ASST"], px["BTC"]),
}
tok_of = {"HYPD": "HYPE", "USDE": "ENA", "FWDI": "SOL", "MSTR": "BTC", "ASST": "BTC"}
nps, mnav, implied, gap, mnav_g = {}, {}, {}, {}, {}
for t, (tokens, shares, c, p) in comp.items():
    nps[t] = tokens * p / shares
    mnav[t] = c / nps[t]
    implied[t] = c * shares / tokens
    gap[t] = tokens * p - c * shares
    mnav_g[t] = c / (tokens * G[tok_of[t]] / shares)
order = sorted(comp, key=lambda t: mnav[t])
assert order == ["HYPD", "USDE", "FWDI", "MSTR", "ASST"]
assert sorted(comp, key=lambda t: mnav_g[t]) == order
assert max(abs(G[k] / px[k] - 1) for k in ("BTC", "SOL", "ENA", "HYPE")) < Fraction(25, 10000)       # less than 0.25%
assert max(abs(mnav_g[t] - mnav[t]) for t in comp) <= Fraction(1, 1000)                               # no more than 0.001

need(f"was priced at {rnd(mnav['USDE'], 2)}× the value of the ENA, the governance token of Ethena, that the company reported for each share. That was the "
     "second lowest of five crypto treasury companies")
need(f"Hyperion DeFi, which holds HYPE, the token of the Hyperliquid network, was lower at {rnd(mnav['HYPD'], 2)}× on its common shares alone")
need(f"Forward Industries, which holds SOL, the token of the Solana network, was at {rnd(mnav['FWDI'], 2)}×.")
need(f"Strategy and Strive, which both hold bitcoin, or BTC, were at {rnd(mnav['MSTR'], 2)}× and {rnd(mnav['ASST'], 2)}×.")
need(f"USDE closed at ${rnd(close['USDE'], 2)}.")
need(f"was at ${rnd(px['ENA'], 4)}, which put the approximately {rnd(usde_tokens / 10**9, 3)} billion ENA that StablecoinX reported at "
     f"${rnd(usde_tokens * px['ENA'] / 10**6, 1)} million, or ${rnd(nps['USDE'], 2)} a share.")
need(f"The market value of its {rnd(usde_shares, 0)} Class A shares, the only class with a claim on dividends and assets, was "
     f"${rnd(close['USDE'] * usde_shares / 10**6, 1)} million at the close, ${rnd(gap['USDE'] / 10**6, 1)} million less than the ENA.")
need(f"at an ENA price of ${rnd(implied['USDE'], 4)}, {rnd((1 - implied['USDE'] / px['ENA']) * 100, 1)}% below ENA's price at the close.")
m_conv = close["HYPD"] / (hy_gross * px["HYPE"] / hy_conv_shares)
sata_per = sata_stated / sata_sep30
assert abs(sata_per - 100) < Fraction(1, 100)
sata_oct2 = asst_sata * 100
asst_net_ps = (asst_btc * px["BTC"] + asst_cash + asst_strc - sata_oct2) / asst_shares
need(f"Counting Hyperion DeFi's preferred stock as the common shares it converts into raises its figure to {rnd(m_conv, 2)}×, and subtracting "
     f"Strive's preferred stock and adding its cash and securities raises Strive's to {rnd(close['ASST'] / asst_net_ps, 2)}×.")

names = {"HYPD": "Hyperion DeFi", "USDE": "StablecoinX", "FWDI": "Forward Industries", "MSTR": "Strategy", "ASST": "Strive"}
for t in order:
    tokens, shares, c, p = comp[t]
    pp = 4 if t == "USDE" else 2
    need(f"| {names[t]} | {tok_of[t]} | ${rnd(c, 2)} | ${rnd(p, pp)} | ${rnd(nps[t], 2)} | {rnd(mnav[t], 2)}× |")
    direction = "lower" if implied[t] < p else "higher"
    need(f"| {names[t]} | {tok_of[t]} | ${rnd(p, pp)} | ${rnd(implied[t], pp)} | {rnd(abs(implied[t] / p - 1) * 100, 1)}% {direction} |")
need(f"| Hyperion DeFi | About {rnd(hy_gross / 10**6, 2)} million HYPE | September 30 | About {rnd(hy_shares, 0)} | September 30 |")
need(f"| StablecoinX | About {rnd(usde_tokens / 10**6, 0)} million ENA | June 25 | {rnd(usde_shares, 0)} | September 30 |")
need(f"| Forward Industries | {rnd(fwd_sol, 0)} SOL | September 30 | {rnd(fwd_shares, 0)} | September 30 |")
need(f"| Strategy | {rnd(mstr_btc, 0)} BTC | October 4 | {rnd(mstr_shares, 0)} | October 4 |")
need(f"| Strive | {rnd(asst_btc, 0)} BTC | October 2 | {rnd(asst_shares, 0)} | October 2 |")
need("had prices stamped 20:00 UTC, read through DefiLlama's public price service, that differed from Kraken's by less than 0.25% and moved no mNAV by more "
     "than 0.001. The counts are dated from June 25 to October 4")
assert min(("2026-06-25", "2026-09-30", "2026-10-04", "2026-10-02")) == "2026-06-25"
need(f"In dollars, Hyperion DeFi's HYPE was worth ${rnd(gap['HYPD'] / 10**6, 1)} million more than the market value of its common shares, StablecoinX's "
     f"ENA ${rnd(gap['USDE'] / 10**6, 1)} million more and Forward Industries' SOL ${rnd(gap['FWDI'] / 10**6, 1)} million more. Strategy's BTC was worth "
     f"${rnd(gap['MSTR'] / 10**9, 2)} billion more than the market value of its common shares. Strive's market value was ${rnd(-gap['ASST'] / 10**6, 1)} million "
     "more than its BTC.")

# ---------------------------------------------------------------- how the counts were chosen
review = load("inputs/filings/sec_window_review_2026-10-12.csv")
assert {r["ticker"] for r in review if r["verdict"] == "later count, used"} == {"PURR"}
wd = load("inputs/filings/sec_window_documents_2026-10-12.csv")
assert sum(1 for r in wd if r["ticker"] == "BMNR" and r["searched"] == "no (almost no text)") == 3
need("A search of the text of the filings of the seven companies other than Mega Matrix")
assert {r["ticker"] for r in wd} == {"USDE", "MSTR", "ASST", "FWDI", "HYPD", "BMNR", "PURR"}
need("apart from StablecoinX's rounded figures, though three of BitMine's exhibits were images with no text to search.")
need(f"gave {rnd(hy_gross / 10**6, 2)} million gross HYPE tokens at September 30, after it sold {rnd(hy_sold, 0)} HYPE and HYPE liquid staking tokens in the third quarter.")
need(f"gave approximately {rnd(hy_shares, 0)} common shares at September 30.")
need(f"for {rnd(hy_jun30, 0)} gross HYPE tokens.")
need(f"gave approximately {rnd(usde_tokens / 10**6, 0)} million ENA, the figure the site's")
assert "approximately 3.0 billion tokens" in Q["usde_results_0814"] and "3.03 billion" in Q["usde_ceo_0908"] and "3.03 billion" in Q["usde_424b3_0914"]
need("Apart from the 10-Q, its filings to October 9 rounded the holding to about 3.0 billion or 3.03 billion ENA.")
m10q = close["USDE"] / (usde_10q_tokens * px["ENA"] / usde_shares)
need(f"sum to {rnd(usde_10q_tokens, 0)} ENA, and on that count StablecoinX's mNAV is {rnd(m10q, 4)} instead of {rnd(mnav['USDE'], 4)}.")
assert len(f4) == 5 and all(F(x["shares"]) == 22000 for x in f4)
need(f"Its share count is the {rnd(usde_class_a, 0)} Class A shares its")
need(f"gave at August 28, the same number as on the 10-Q's cover, plus {rnd(awards, 0)} restricted Class A shares that five directors received on September 30")
need(f"The {rnd(usde_class_b, 0)} Class B shares carry votes and no right to dividends or to assets in a liquidation")
need(f"gave {rnd(fwd_sol, 0)} SOL and {rnd(fwd_shares, 0)} common shares at September 30.")
need(f"gave {rnd(mstr_btc, 0)} BTC at 4 pm New York time on October 4. Its share count starts from the {rnd(mstr_a, 0)} Class A shares and {rnd(mstr_b, 0)} "
     f"Class B shares outstanding on September 25")
need(f"It adds the {rnd(mstr_oct, 0)} Class A shares Strategy sold from October 1 to 4, and the 8-K reported no sales from September 28 to 30.")
m_hi = close["MSTR"] / (mstr_btc * px["BTC"] / (mstr_shares + mstr_sep))
need(f"Strategy also sold {rnd(mstr_sep, 0)} Class A shares from September 21 to 27")
need(f"Counting all of them puts Strategy's mNAV at {rnd(m_hi, 2)}×, so on these counts its figure is between {rnd(mnav['MSTR'], 2)}× and {rnd(m_hi, 2)}×.")
need(f"gave {rnd(asst_btc, 0)} BTC and {rnd(asst_shares, 0)} Class A and Class B shares on October 2")

# ---------------------------------------------------------------- beyond token NAV
need(f"Hyperion DeFi's 10-Q reported {rnd(hy_pref, 0)} shares of Series A preferred stock at June 30, each convertible into three common shares, with a "
     f"liquidation preference of ${rnd(hy_liq, 0)}.")
need(f"Counted as the {rnd(3 * hy_pref, 0)} common shares they convert into, they would raise its share count to {rnd(hy_conv_shares, 0)} and its mNAV to "
     f"{rnd(m_conv, 2)}×.")
wf = load("inputs/filings/sec_window_filings_2026-10-12.csv")
assert {r["form"] for r in wf if r["ticker"] == "HYPD"} <= {"8-K", "10-Q", "4", "SCHEDULE 13G/A"}
assert not any(set(r["items"].split(",")) & {"3.02", "3.03", "5.03"} for r in wf if r["ticker"] == "HYPD" and r["form"] == "8-K")
need("Any of them converted between June 30 and September 30 would already be in the September 30 count and would be counted twice. Its filings from June 30 "
     "to the close included no prospectus and no 8-K item for an unregistered sale of equity, a change to holders' rights or a charter amendment.")
need(f"It also held ${rnd(hy_cash / 10**6, 1)} million of cash, cash equivalents and stablecoins")
net_usde = (usde_tokens * px["ENA"] + bv["cash"] - bv["total_liabilities"]) / usde_shares
need(f"StablecoinX had ${rnd(bv['cash'] / 10**6, 1)} million of cash and ${rnd(bv['total_liabilities'] / 10**6, 1)} million of liabilities at June 30")
need(f"moves its mNAV from {rnd(mnav['USDE'], 4)} to {rnd(close['USDE'] / net_usde, 4)}.")
need(f"Its share count also leaves out the {rnd(usde_warrants, 0)} warrants and the {rnd(usde_rsus, 0)} shares due on restricted stock units")
need(f"its balance sheet for that day gave its {rnd(sata_sep30, 0)} SATA preferred shares a stated amount, the fixed dollar value assigned to each preferred "
     f"share, of ${rnd(sata_stated / 10**9, 2)} billion, ${rnd(sata_per, 0)} a share.")
need(f"Strive's {rnd(asst_sata, 0)} SATA preferred shares on October 2 came to ${rnd(sata_oct2 / 10**9, 2)} billion at that ${rnd(sata_per, 0)}.")
need(f"adding its ${rnd(asst_cash / 10**6, 1)} million of cash and its ${rnd(asst_strc / 10**6, 1)} million of Strategy's STRC preferred stock leaves "
     f"${rnd(asst_net_ps, 2)} a common share, and on that count Strive's mNAV is {rnd(close['ASST'] / asst_net_ps, 2)}×.")
assert fwd_sol * fwd_px30 - 1003663266 < 30 and fwd_nav == 1003663266 + fwd_other + fwd_cash - fwd_debt
own_common = fwd_close30 / (fwd_nav / fwd_shares)
own_fd = fwd_close30 / (fwd_nav / fwd_fd)
need(f"subtracted ${rnd(fwd_debt / 10**6, 1)} million of institutional debt, and at September 30 it put its mNAV at {rnd(own_common, 3)}× on common shares and "
     f"{rnd(own_fd, 3)}× on its fully diluted count of {rnd(fwd_fd, 0)} shares, at ${rnd(fwd_close30, 2)} a share and SOL at ${rnd(fwd_px30, 2)}.")
need(f"On the token-only count at the same prices it was {rnd(fwd_close30 / (fwd_sol * fwd_px30 / fwd_shares), 2)}×.")
own_oct9 = close["FWDI"] / ((fwd_sol * px["SOL"] + fwd_other + fwd_cash - fwd_debt) / fwd_shares)
need(f"its own measure on common shares came to {rnd(own_oct9, 2)}×.")
need(f"the token-only figure at the October 9 close came to {rnd(close['FWDI'] / (fwd_sol * px['SOL'] / fwd_fd), 2)}×.")
need(f"Strategy reported ${rnd(mstr_reserve / 10**9, 2)} billion in what it calls its USD Reserve and ${rnd(mstr_cash / 10**6, 1)} million in its USD Cash on October 4.")
need(f"its proxy statement listed {rnd(mstr_stre, 0)} shares of a fifth series, STRE, at September 15.")
D = {r["date"]: r for r in load("inputs/carried/dashboard_series_2c7c5a5_october.csv")}
d9 = D["2026-10-09"]
dash = F(d9["usde_close"]) / (F(d9["ena_price"]) * F(d9["ena_holdings"]) / F(d9["shares_outstanding"]))
assert F(d9["ena_holdings"]) == usde_tokens and F(d9["shares_outstanding"]) == usde_shares
passages = (HERE / "inputs" / "carried" / "site_review_passages_2c7c5a5.txt").read_text()
assert "pairs each close with ENA's price at midnight UTC, 8 pm in New York the evening before" in passages
assert "StablecoinX can sell its ENA only with the Ethena Foundation's consent, even though the lock-ups covered by the waiver ended on October 5, 2026." in passages
need(f"The dashboard's own figure for StablecoinX on October 9 was {rnd(dash, 2)}×. It pairs each close with ENA's price at midnight UTC, 8 pm in New York the "
     f"evening before, which was ${rnd(F(d9['ena_price']), 4)} for October 9")
need("StablecoinX could sell its ENA only with the Ethena Foundation's consent even after the lock-ups ended on October 5")

# ---------------------------------------------------------------- companies left out
need(f"| BitMine Immersion Technologies | ETH | {rnd(bm_eth, 0)} ETH on October 4. {rnd(bm_shares, 0)} shares on July 9 |")
need(f"| Hyperliquid Strategies | HYPE | About {rnd(purr_hype / 10**6, 1)} million HYPE and {rnd(purr_sep8, 0)} shares on September 8. {rnd(purr_sep30, 0)} shares on "
     f"September 30 | No HYPE count after its shares rose {rnd((purr_sep30 / purr_sep8 - 1) * 100, 1)}% |")
need(f"| Mega Matrix | ENA | {rnd(mpu_ena, 0)} ENA on June 30 | Its ENA was ${rnd(mpu_val, 0)} of its ${rnd(mpu_total, 0)} of digital assets |")
need(f"reported {rnd(bm_eth, 0)} ETH at 6:30 pm New York time on October 4 in its")
need(f"Its latest share count in a filing was {rnd(bm_shares, 0)} shares on July 9")
need(f"said it had bought back {rnd(bm_buyback / 10**6, 1)} million shares since July 1, and its chairman's")
need("dated the start of the buyback to July 14, after that count.")
need(f"its reported ETH rose by {rnd(bm_eth - bm_eth_aug, 0)} and its cash and marketable securities from ${rnd(bm_cash_aug / 10**6, 0)} million to "
     f"${rnd(bm_cash / 10**6, 0)} million.")
bm_low = bm_shares - bm_buyback
bm_m = close["BMNR"] / (bm_eth * px["ETH"] / bm_low)
bm_step = close["BMNR"] / (bm_eth * px["ETH"] / (bm_low + 10**7)) - bm_m
need(f"On the July 9 count less the {rnd(bm_buyback / 10**6, 1)} million shares, BitMine's mNAV would be {rnd(bm_m, 2)}×, and each 10 million shares issued "
     f"since would add {rnd(bm_step, 3)}.")
need(f"gave about {rnd(purr_hype / 10**6, 1)} million HYPE and {rnd(purr_sep8, 0)} shares on September 8")
need(f"gave {rnd(purr_sep30, 0)} shares on September 30.")
need(f"showed {rnd(mpu_ena, 0)} ENA at June 30, valued at ${rnd(mpu_val, 0)} of its ${rnd(mpu_total, 0)} of digital assets. StablecoinX's count is "
     f"{rnd(usde_tokens / mpu_ena, 0)} times as large.")

# ---------------------------------------------------------------- caveats, from the tracking review's published chart data
T = load("inputs/carried/usde_ena_tracking_chart_data_2c7c5a5.csv")
lo = min(T, key=lambda r: F(r["mnav_4pm"]))
hi = max(T, key=lambda r: F(r["mnav_4pm"]))
assert (T[0]["date"], T[-1]["date"], lo["date"], hi["date"]) == ("2026-06-26", "2026-10-08", "2026-07-24", "2026-09-25")
need(f"StablecoinX's mNAV at the close ranged from {rnd(F(lo['mnav_4pm']), 2)}× on July 24 to {rnd(F(hi['mnav_4pm']), 2)}× on September 25 between June 26 and October 8")

# ---------------------------------------------------------------- code block
need(f"Hyperion DeFi        = {rnd(close['HYPD'], 2)} / ({rnd(px['HYPE'], 2)} x {rnd(hy_gross, 0)} / {rnd(hy_shares, 0)})\n"
     f"                     = {rnd(close['HYPD'], 2)} / {rnd(nps['HYPD'], 2)} = {rnd(mnav['HYPD'], 2)}")
need(f"StablecoinX shares   = {rnd(usde_class_a, 0)} + 5 x 22,000 = {rnd(usde_shares, 0)}")
need(f"StablecoinX          = {rnd(close['USDE'], 2)} / ({rnd(px['ENA'], 4)} x {rnd(usde_tokens, 0)} / {rnd(usde_shares, 0)})\n"
     f"                     = {rnd(close['USDE'], 2)} / {rnd(nps['USDE'], 2)} = {rnd(mnav['USDE'], 2)}")
need(f"Forward Industries   = {rnd(close['FWDI'], 2)} / ({rnd(px['SOL'], 2)} x {rnd(fwd_sol, 0)} / {rnd(fwd_shares, 0)})\n"
     f"                     = {rnd(close['FWDI'], 2)} / {rnd(nps['FWDI'], 2)} = {rnd(mnav['FWDI'], 2)}")
need(f"Strategy shares      = {rnd(mstr_a, 0)} + {rnd(mstr_b, 0)} + {rnd(mstr_oct, 0)} = {rnd(mstr_shares, 0)}")
need(f"Strategy             = {rnd(close['MSTR'], 2)} / ({rnd(px['BTC'], 2)} x {rnd(mstr_btc, 0)} / {rnd(mstr_shares, 0)})\n"
     f"                     = {rnd(close['MSTR'], 2)} / {rnd(nps['MSTR'], 2)} = {rnd(mnav['MSTR'], 2)}")
need(f"Strive               = {rnd(close['ASST'], 2)} / ({rnd(px['BTC'], 2)} x {rnd(asst_btc, 0)} / {rnd(asst_shares, 0)})\n"
     f"                     = {rnd(close['ASST'], 2)} / {rnd(nps['ASST'], 2)} = {rnd(mnav['ASST'], 2)}")
run_log = (HERE / "out" / "run_log.txt").read_text()
n_checks = int(re.search(r"All (\d+) checks passed", run_log).group(1))
need(f"checks that all {len(Q)} quoted passages were recorded as found word for word in the filings, and stops before writing its tables if any of its "
     f"{n_checks} checks fails.")

# ---------------------------------------------------------------- metadata, chart and key findings
need(f"StablecoinX's stock, USDE, closed October 9, 2026 at {rnd(mnav['USDE'], 2)} times the value of its ENA per share, second lowest of five crypto treasury "
     "companies compared.", META["description"])
alt = (f"Hyperion DeFi, which holds HYPE, {rnd(mnav['HYPD'], 2)}. StablecoinX, which holds ENA, {rnd(mnav['USDE'], 2)}. Forward Industries, which holds SOL, "
       f"{rnd(mnav['FWDI'], 2)}. Strategy, which holds BTC, {rnd(mnav['MSTR'], 2)}. Strive, which holds BTC, {rnd(mnav['ASST'], 2)}. A dashed line marks 1, "
       "where the share price equals token NAV per share.")
need(alt, META["imageAlt"])
need(alt, ARTICLE)
for t in order:
    need(f">{rnd(mnav[t], 2)}×</text>", SVG)
    need(f"mNAV {rnd(mnav[t], 3)}", SVG)
need("StablecoinX was second lowest of five crypto treasury companies on token-only mNAV", SVG)
need(f"At the October 9, 2026 close, StablecoinX's stock, USDE, was priced at {rnd(mnav['USDE'], 2)} times the value of the ENA tokens it reported per share, "
     "second lowest of five crypto treasury companies on a token-only measure.", FINDINGS)
need(f"Hyperion DeFi was at {rnd(mnav['HYPD'], 2)} on its common shares alone, Forward Industries at {rnd(mnav['FWDI'], 2)}, Strategy at {rnd(mnav['MSTR'], 2)} "
     f"and Strive at {rnd(mnav['ASST'], 2)}. USDE's close would have equaled the value of StablecoinX's ENA per share at an ENA price of "
     f"${rnd(implied['USDE'], 4)}.", FINDINGS)
need("Token NAV, the value of a company's reported tokens, leaves out cash, debt, preferred stock and warrants and uses reported counts, not verified "
     "balances. BitMine Immersion Technologies and Hyperliquid Strategies were left out because their filed counts could not be matched.", FINDINGS)
assert len(LAYOUT["keyFindings"]) == 3
assert not any(ch in FINDINGS for ch in ("—", "–", ";", ":")), "key findings punctuation"

# ---------------------------------------------------------------- page rules
body = re.sub(r"```.*?```", "", ARTICLE, flags=re.S)
body = re.sub(r"\]\([^)]*\)", "]", body)
body = re.sub(r"`[^`]*`", "", body)
body = re.sub(r"\b\d{1,2}:\d{2}(:\d{2})?\b", "", body)
body = re.sub(r"^\|[\s\-:|]+\|$", "", body, flags=re.M)
problems = [ch for ch in ("—", "–", ";") if ch in body] + (["colon"] if ":" in body else [])
assert not problems, problems
for field in ("description", "imageAlt", "headline", "title"):
    assert not any(ch in META[field] for ch in ("—", "–", ";", ":")), field
assert ARTICLE.count("\n# ") + ARTICLE.startswith("# ") == 1, "one H1"
assert ARTICLE.startswith("# " + META["headline"] + "\n"), "the H1 is the metadata headline"
assert "This article" not in ARTICLE and "this article" not in ARTICLE
for link in ("https://ethenadash.com/about/", "https://ethenadash.com/stablecoinx/", "https://ethenadash.com/methodology/",
             "https://ethenadash.com/research/stablecoinx-mnav/"):
    assert link in ARTICLE, link
assert ARTICLE.rstrip().endswith("Analysis of public filings and market data. Not investment advice.")
assert not re.findall(r"0x[0-9a-fA-F]{40}", ARTICLE), "no addresses"
assert len(META["description"]) <= 160 and len(META["title"]) <= 60
assert "USDE's mNAV" not in ARTICLE and "review of how USDE tracks ENA" not in ARTICLE      # one name per thing
assert "token treasury compan" not in TEXT and "Token at 4 pm" not in ARTICLE                # one name per thing
assert "on-chain" not in ARTICLE.lower()
quotes = re.findall(r"\"[^\"]+\"", re.sub(r"```.*?```", "", ARTICLE, flags=re.S))
assert len(quotes) <= 1, quotes
anchors = {a for _, a in LAYOUT["navigation"]}
heads = {re.sub(r"[^\w\s-]", "", h.lower()).strip().replace(" ", "-") for h in re.findall(r"^## (.+)$", ARTICLE, flags=re.M)}
assert anchors == heads, (anchors ^ heads)
assert "layout.json" in LAYOUT["archiveFiles"] and all((HERE / f).exists() for f in LAYOUT["archiveFiles"])

if missing:
    print(f"{len(missing)} phrases missing:")
    for m in missing:
        print("  ", m)
    sys.exit(1)
print(f"All {found} phrases found, every assertion holds and the page rules pass.")
