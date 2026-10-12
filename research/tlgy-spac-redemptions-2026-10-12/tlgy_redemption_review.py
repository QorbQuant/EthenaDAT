#!/usr/bin/env python3
"""What happened to the public shareholders of TLGY Acquisition Corp., the SPAC that merged with StablecoinX Inc.
on June 25, 2026. Counts the shares redeemed at each of the six votes that let holders take cash from the trust,
from February 2023 to the merger, and the cash paid for them, the trust's value a share between them, and USDE's close
against the cash a share paid at the merger, from USDE's first session on June 26 to the October 9, 2026 close.

Reads the files in inputs/ and runs every check. If any check fails it stops before writing anything, so out/
keeps the tables of the last clean run. Otherwise it rewrites the tables in out/. Python 3 standard library only.
It makes no network requests.

Sources. TLGY's and StablecoinX's SEC filings, cut into fixed windows of text in inputs/sec_extracts_2026-10-12.txt
and four later sets, sec_extracts_2 to 5, made the same way. Each row of inputs/filing_facts.csv names its
window and quotes it, and the script checks that the quote is there and shows the row's value. Daily prices from
StockAnalysis, which credits S&P Global Market Intelligence, with USDE's closes checked against Yahoo Finance's.

Measures.
  public share        a Class A share sold in the IPO, the only kind the trust could redeem
  cash a share        cash paid for the redemptions at a vote / public shares redeemed at it
  second vote's cash  the 2023 total withdrawn to pay redeeming holders, less the first vote's
  trust a share       the trust's value in a filing / public shares then outstanding
  growth a year       (later / earlier) ** (365 / days) - 1
  kept                public shares never redeemed, 23,000,000 less every vote's redemptions
  USDE against cash   USDE close / the merger's cash a share - 1
"""
import csv
import hashlib
import json
import os
import re
from datetime import date
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, "inputs")
OUT = os.path.join(HERE, "out")
LOG, FAILED = [], []


def say(s=""):
    LOG.append(s)
    print(s)


def check(name, ok, detail=""):
    say(f"[{'ok' if ok else 'FAIL'}] {name}{' . ' + detail if detail else ''}")
    if not ok:
        FAILED.append(name)


def read_csv(name):
    with open(os.path.join(INP, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def money(x, nd=2):
    return f"${float(x):,.{nd}f}"


def pct(x, nd=1):
    return f"{float(x) * 100:.{nd}f}%"


def nice(d):
    return d.strftime("%B ") + str(d.day) + d.strftime(", %Y")


# ---------------------------------------------------------------- inputs and their hashes
manifest = read_csv("manifest.csv")
bad = [r["file"] for r in manifest if sha256_file(os.path.join(INP, r["file"])) != r["sha256"]
       or os.path.getsize(os.path.join(INP, r["file"])) != int(r["bytes"])]
listed = {r["file"] for r in manifest}
present = {n for n in os.listdir(INP) if n != "manifest.csv"}
check("every input matches the SHA-256 and size in manifest.csv, and the manifest lists every input",
      not bad and listed == present, f"{len(manifest)} files" + (f", mismatched {bad}" if bad else "")
      + (f", unlisted {sorted(present - listed)}" if present - listed else ""))


# ---------------------------------------------------------------- the filing extracts
def blocks(name):
    out, key = {}, None
    with open(os.path.join(INP, name), encoding="utf-8") as f:
        for line in f.read().split("\n"):
            if line.startswith("### "):
                key = line.split()[1]
                out[key] = {"url": line.split()[2], "head": "", "lines": []}
            elif key and line.startswith("# status"):
                out[key]["head"] = line
            elif key and line.startswith("- "):
                out[key]["lines"].append(line)
    return out


EX = {"1": blocks("sec_extracts_2026-10-12.txt"), "2": blocks("sec_extracts_2_2026-10-12.txt"),
      "3": blocks("sec_extracts_3_2026-10-12.txt"), "4": blocks("sec_extracts_4_2026-10-12.txt"),
      "5": blocks("sec_extracts_5_2026-10-12.txt")}
heads = [b["head"] for f in EX.values() for b in f.values()]
check("every filing in the extracts was served with status 200 and every anchor was found",
      all(h.startswith("# status 200 ") for h in heads)
      and not any(l.startswith("- MISSING") for f in EX.values() for b in f.values() for l in b["lines"]),
      f"{len(EX['1'])}, {len(EX['2'])}, {len(EX['3'])}, {len(EX['4'])} and {len(EX['5'])} documents")
served = {}
for f in EX.values():
    for k, b in f.items():
        served.setdefault(k, set()).add(b["head"].split("raw_sha256 ")[1].split()[0])
again = sorted(k for k in served if sum(k in f for f in EX.values()) > 1)
check("documents read in more than one extract were served identically each time",
      all(len(served[k]) == 1 for k in again), ", ".join(again))

MONTHS = {m: i + 1 for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July",
                                         "August", "September", "October", "November", "December"])}
WORDS = {"one-half": Fraction(1, 2), "one-fourth": Fraction(1, 4), "one share": Fraction(1)}


def shown(s, unit):
    if unit == "date":
        m = re.fullmatch(r"([A-Z][a-z]+) (\d{1,2}), (\d{4})", s)
        return date(int(m[3]), MONTHS[m[1]], int(m[2])) if m else date.fromisoformat(s)
    if s in WORDS:
        return WORDS[s]
    return Fraction(s.replace("$", "").replace(",", "").strip())


F, fact_rows, fact_bad = {}, read_csv("filing_facts.csv"), []
for r in fact_rows:
    blk = EX[r["file"]].get(r["source_key"])
    ok = blk is not None and any(r["quote"] in l for l in blk["lines"]) and r["shows"] in r["quote"]
    if r["unit"] == "text":
        val = r["value"]
    elif r["unit"] == "date":
        val = date.fromisoformat(r["value"])
        ok = ok and shown(r["shows"], "date") == val
    else:
        val = Fraction(r["value"])
        ok = ok and shown(r["shows"], r["unit"]) == val
    if not ok:
        fact_bad.append(r["id"])
    F[r["id"]] = val
check("every row of filing_facts.csv quotes its filing window and the quote shows the row's value",
      not fact_bad and len(F) == len(fact_rows), f"{len(fact_rows)} rows" + (f", failed {fact_bad}" if fact_bad else ""))

filings = read_csv("edgar_filings_tlgy_2026-10-12.csv")
votes = sorted(r["filing_date"] for r in filings if r["form"] == "8-K" and "5.07" in r["items"])
check("TLGY's filing list has six 8-Ks reporting a shareholder vote, one for each vote counted here",
      votes == ["2023-02-27", "2023-10-19", "2024-04-16", "2025-04-21", "2026-03-11", "2026-04-20"], ", ".join(votes))
deregistered = [r for r in filings if r["form"] == "15-12G"]
check("TLGY's last filing in the list is its June 26, 2026 deregistration",
      len(deregistered) == 1 and max(r["filing_date"] for r in filings) == "2026-06-26" == deregistered[0]["filing_date"])

# ---------------------------------------------------------------- the IPO and the trust
IPO_SHARES = F["ipo_units"] + F["option_units"]
check("the IPO's 20,000,000 units and 3,000,000 over-allotment units make the 23,000,000 public shares in the "
      "first 10-Q of 2023", IPO_SHARES == 23_000_000 == F["shares_2022_12_31"])
TRUST_A_SHARE = F["trust_initial"] / IPO_SHARES
check("$234,600,000 in trust over 23,000,000 shares is the $10.20 a unit the prospectus set",
      TRUST_A_SHARE == F["trust_per_unit"] == Fraction("10.20"))
check("half a warrant a unit gives the 11,500,000 public warrants the merger proxy counts",
      IPO_SHARES * F["unit_warrant_fraction"] == F["public_warrants"])
check("a quarter of a warrant a unit gives the right's 5,750,000 warrants",
      IPO_SHARES * F["right_min_fraction"] == F["right_aggregate"])

# ---------------------------------------------------------------- the six votes
ROUNDS = [
    {"key": "ext1", "name": "First extension", "date": F["ext1_date"], "shares": F["ext1_shares"],
     "cash": F["ext1_cash"], "basis": "first 10-Q of 2023, cash withdrawn from the trust",
     "stated": {"8-K": F["ext1_price_8k"]}},
    {"key": "ext2", "name": "Second extension", "date": F["ext2_date"], "shares": F["ext2_shares"],
     "cash": F["y2023_cash"] - F["ext1_cash"], "basis": "2023 10-K total for both 2023 votes, less the first",
     "stated": {"8-K": F["ext2_price_8k"]}},
    {"key": "ext3", "name": "Third extension", "date": F["ext3_date"], "shares": F["ext3_shares"],
     "cash": F["ext3_cash"], "basis": "2024 10-K, cash withdrawn to pay redeeming holders",
     "stated": {"8-K": F["ext3_price_8k"]}},
    {"key": "ext4", "name": "Fourth extension", "date": F["ext4_date"], "shares": F["ext4_shares"],
     "cash": F["ext4_cash"], "basis": "second 10-Q of 2025, cash removed from the trust",
     "stated": {"8-K": F["ext4_price_8k"]}},
    {"key": "ext5", "name": "Fifth extension", "date": F["ext5_date"], "shares": F["ext5_shares"],
     "cash": F["ext5_cash"], "basis": "first 10-Q of 2026, cash removed from the trust",
     "stated": {"10-Q note": F["ext5_price_note"], "10-Q discussion": F["ext5_price_mdna"], "proxy": F["ext5_estimate"]}},
    {"key": "merger", "name": "Merger", "date": F["closing_date"], "vote": F["bc_date"], "shares": F["merger_shares"],
     "cash": F["merger_cash"], "basis": "closing 8-K, about $5,068,095", "approx": True,
     "stated": {"8-K": F["merger_price_8k"]}},
]
left = IPO_SHARES
for r in ROUNDS:
    r["before"] = left
    left -= r["shares"]
    r["after"] = left
    r["a_share"] = r["cash"] / r["shares"]
    r["of_before"] = r["shares"] / r["before"]
    r["of_ipo"] = r["shares"] / IPO_SHARES
KEPT = left
R = {r["key"]: r for r in ROUNDS}

check("the two 2023 votes add up to the 17,077,135 shares the 2023 10-K counts",
      R["ext1"]["shares"] + R["ext2"]["shares"] == F["y2023_shares"])
check("public shares left after each vote match the filings, 7,318,182, 5,922,865, 3,717,207 and 489,887",
      R["ext1"]["after"] == F["shares_2023_03_31"] and R["ext2"]["after"] == F["shares_2023_12_31"]
      and R["ext3"]["after"] == F["shares_2024_06_30"] == F["shares_2024_12_31"]
      and R["ext4"]["after"] == F["public_after_ext4"] == F["ext5_record_public"])
check("the fifth vote's 13,817 and the closing's 379,721 add up to the 393,538 redeemed shares in StablecoinX's share table",
      R["ext5"]["shares"] + R["merger"]["shares"] == F["table_redemption"],
      f"{int(R['ext5']['shares']):,} + {int(R['merger']['shares']):,}")
check("the share table starts from the 5,834,587 Class A shares outstanding after April 2025, before the fifth vote",
      F["table_start"] == F["class_a_after_ext4"] == F["bc_record_class_a"]
      and F["table_start"] - F["table_forfeiture"] - F["table_redemption"] == F["table_tlgy_class_a"])
check("public shares kept come to 96,349 by the vote counts and by the share table, 489,887 less 393,538, the count in "
      "the site's float review", KEPT == 96_349 == F["public_after_ext4"] - F["table_redemption"],
      f"{int(KEPT):,} kept, {pct(KEPT / IPO_SHARES, 2)} of the IPO's shares")
TABLE_SUM = F["table_tlgy_class_a"] + F["table_pipe"] + F["table_ethena"] + F["table_class_b"] + F["table_legacy"]
check("the share table's lines add up to its 24,029,375 Class A shares, the count in StablecoinX's closing 8-K, a check on "
      "the table's arithmetic", TABLE_SUM == F["table_total"] == F["closing_class_a"])
REDEEMED = sum(r["shares"] for r in ROUNDS)
CASH = sum(r["cash"] for r in ROUNDS)
say(f"  {int(REDEEMED):,} redeemed for {money(CASH, 0)}, {money(CASH / REDEEMED)} a share on average")
BEFORE_DEAL = sum(r["shares"] for r in ROUNDS if r["date"] < F["bca_date"])
EXTENSIONS = sum(r["shares"] for r in ROUNDS if r["key"] != "merger")
check("four votes, every one before the July 21, 2025 merger agreement, redeemed 22,510,113 public shares, the last of "
      "them more than a year before the closing", BEFORE_DEAL == 22_510_113 and [r["key"] for r in ROUNDS if r["date"] < F["bca_date"]]
      == ["ext1", "ext2", "ext3", "ext4"] and (F["closing_date"] - R["ext4"]["date"]).days > 365,
      f"{pct(BEFORE_DEAL / IPO_SHARES, 2)} of the IPO's shares, {(F['closing_date'] - R['ext4']['date']).days} days before the closing. "
      f"All five extension votes {int(EXTENSIONS):,}, {pct(EXTENSIONS / IPO_SHARES, 2)}, the merger {pct(R['merger']['shares'] / IPO_SHARES, 2)}")
check("StablecoinX counted 11,499,988 public warrants after the merger, 12 fewer than the 11,500,000 in the units, though "
      "99.6% of the public shares had been redeemed", F["public_warrants"] - F["warrants_after_merger"] == 12)

gaps = {r["key"]: {k: r["a_share"] - v for k, v in r["stated"].items()} for r in ROUNDS}
for r in ROUNDS:
    say(f"  {r['name']:17s} {nice(r['date'])}, {int(r['shares']):>10,} shares, {money(r['cash'], 0):>13s}, "
        f"{float(r['a_share']):.4f} a share, " + ", ".join(f"{k} {float(v):.2f}" for k, v in r["stated"].items())
        + f". {pct(r['of_before'])} of the {int(r['before']):,} then outstanding, {int(r['after']):,} left")
off = sorted((k, n) for k, g in gaps.items() for n, v in g.items() if abs(v) > Fraction(1, 200))
check("the cash a share agrees with each filing's rounded price within half a cent, except the third vote's 8-K, "
      "and the fifth vote's 10-Q note and proxy estimate", off == [("ext3", "8-K"), ("ext5", "10-Q note"), ("ext5", "proxy")],
      f"third vote paid {float(R['ext3']['a_share']):.4f} against the 8-K's $11.33, fifth paid "
      f"{float(R['ext5']['a_share']):.4f} against $13.19 in the note and the proxy and $13.20 in the discussion")
check("the fourth vote's $39,113,394 is the 8-K's about $39.1 million, and its 489,887 shares at $12.12 the about "
      "$5.9 million left", round(R["ext4"]["cash"] / 1_000_000, 1) == F["ext4_cash_8k"]
      and round(R["ext4"]["after"] * R["ext4"]["a_share"] / 1_000_000, 1) == F["ext4_trust_after"])
check("the March 2026 extension deposit of $24,494.35 is $0.05 for each of the 489,887 public shares",
      F["deposit_march_2026"] == Fraction("0.05") * F["public_after_ext4"])
check("the proxy's about $6.5 million in trust on March 20, 2026 fits 489,887 shares at its $13.19 estimate",
      round(F["ext5_record_public"] * F["ext5_estimate"] / 1_000_000, 1) == F["ext5_trust_record"])
ELECTED_GAP = F["bc_elections"] - F["merger_shares"]
check("redemption requests at the March 10 merger vote, 388,406 shares, exceed the 379,721 redeemed at the closing",
      F["bc_elections"] == F["bc_unpaid_march_31"] and ELECTED_GAP == 8_685, f"by {int(ELECTED_GAP):,}")

# ---------------------------------------------------------------- the trust's money, year by year
YEARS = [
    {"year": "2022", "start": F["trust_funded_2021"], "income": F["income_2022"], "deposits": Fraction(0), "paid": Fraction(0),
     "end_reported": F["trust_2022_12_31"]},
    {"year": "2023", "income": F["income_2023"], "deposits": F["deposits_2023"], "paid": F["withdrawn_2023"],
     "end_reported": F["trust_2023_12_31"]},
    {"year": "2024", "income": F["income_2024"], "deposits": F["deposits_2024"], "paid": F["withdrawn_2024"],
     "end_reported": F["trust_2024_12_31"]},
    {"year": "2025", "income": F["income_2025"], "deposits": F["deposits_2025"], "paid": F["withdrawn_2025"],
     "end_reported": F["trust_cash_2025_12_31"]},
]
for i, y in enumerate(YEARS):
    if i:
        y["start"] = YEARS[i - 1]["end_reported"]
    y["end"] = y["start"] + y["income"] + y["deposits"] - y["paid"]
check("the trust's balance rolls forward exactly each year from 2022 to 2025, start plus income plus the sponsors' "
      "deposits less the cash taken out giving the next reported balance",
      F["trust_funded_2021"] == F["trust_initial"] and all(y["end"] == y["end_reported"] for y in YEARS),
      ", ".join(f"{y['year']} ends {money(y['end'], 0)}" for y in YEARS))
check("the 10-K for 2024, filed after the August 2024 restatement of the 2023 accounts for convertible notes, repeats "
      "the 2023 trust figures of the 10-K for 2023", F["income_2023_in_2024_10k"] == F["income_2023"]
      and F["deposits_2023_in_2024_10k"] == F["deposits_2023"] and F["trust_2023_12_31_in_2024_10k"] == F["trust_2023_12_31"]
      and F["withdrawn_2023"] == F["y2023_cash"], f"the restatement concerned {money(F['restatement_amount'], 0)} in the convertible note accounts")
check("the cash withdrawn in 2023 and 2024 is what the votes of those years paid",
      F["withdrawn_2023"] == F["y2023_cash"] and F["withdrawn_2024"] == R["ext3"]["cash"])
EXTRA_2025 = F["withdrawn_2025"] - R["ext4"]["cash"]
check("the 2025 cash flow shows $111 more withdrawn than the fourth vote's redemptions, the same $111 by which the "
      "redemption value at December 31, 2025 exceeds the trust's reported cash",
      EXTRA_2025 == 111 == F["trust_2025_12_31"] - F["trust_cash_2025_12_31"])
Q1_2026_END = F["trust_cash_2025_12_31"] + F["income_q1_2026"] + F["deposits_q1_2026"]
check("the first quarter of 2026 leaves the trust at about $6.5 million, within $112 of the March 31 redemption value",
      round(Q1_2026_END / 1_000_000, 1) == Fraction("6.5") and F["trust_2026_03_31"] - Q1_2026_END == 112,
      f"{money(Q1_2026_END, 0)} from the roll-forward")
check("the first-quarter deposits fit three months at the monthly caps, $60,000 in 2025 and $24,494.35 in 2026",
      F["deposits_q1_2025"] == 3 * 60_000 and round(3 * F["deposit_march_2026"]) == F["deposits_q1_2026"])
MONTHLY = F["deposit_march_2026"]
LATER_2025 = F["deposits_2025"] - F["deposits_q1_2025"]
check("deposits from April to December 2025 and in the first quarter of 2026 fit $24,494.35 a month to within a dollar",
      abs(LATER_2025 - 9 * MONTHLY) < 1 and abs(F["deposits_q1_2026"] - 3 * MONTHLY) < 1,
      f"{money(LATER_2025, 0)} against nine months at {money(MONTHLY)}, {money(F['deposits_q1_2026'], 0)} against three")
DEPOSIT_YEAR = 12 * MONTHLY / F["public_after_ext4"]
RISE_4_5 = R["ext5"]["a_share"] - R["ext4"]["a_share"]
DEPOSIT_2025_Q1_A_SHARE = 60_000 / F["shares_2024_12_31"]
say(f"  deposits from April 2025, {float(DEPOSIT_YEAR):.2f} a share a year, against a rise of {float(RISE_4_5):.4f} from the "
    f"fourth vote to the fifth, {pct(DEPOSIT_YEAR / RISE_4_5)}. Early 2025, {float(DEPOSIT_2025_Q1_A_SHARE):.4f} a share a month")
INCOME = sum(y["income"] for y in YEARS)
DEPOSITS = sum(y["deposits"] for y in YEARS)
say(f"  2022 to 2025, income {money(INCOME, 0)}, sponsors' deposits {money(DEPOSITS, 0)}, "
    f"redemptions {money(sum(y['paid'] for y in YEARS), 0)}")

# ---------------------------------------------------------------- the trust's value a share over time
TRUST = [
    (F["ipo_date"], "ipo", F["trust_initial"], IPO_SHARES, "ipo_8k2"),
    (date(2022, 12, 31), "report", F["trust_2022_12_31"], F["shares_2022_12_31"], "q1_2023_10q"),
    (date(2023, 3, 31), "report", F["trust_2023_03_31"], F["shares_2023_03_31"], "q1_2023_10q"),
    (date(2023, 12, 31), "report", F["trust_2023_12_31"], F["shares_2023_12_31"], "k10_2023"),
    (date(2024, 6, 30), "report", F["trust_2024_06_30"], F["shares_2024_06_30"], "q2_2024_10q"),
    (date(2024, 12, 31), "report", F["trust_2024_12_31"], F["shares_2024_12_31"], "k10_2024"),
    (date(2025, 6, 30), "report", F["trust_2025_06_30"], F["public_after_ext4"], "q2_2025_10q"),
    (date(2025, 9, 30), "report", F["trust_2025_09_30"], F["public_after_ext4"], "defm14a"),
    (date(2025, 12, 31), "report", F["trust_2025_12_31"], F["public_after_ext4"], "k10_2025"),
    (date(2026, 3, 31), "report", F["trust_2026_03_31"], F["public_after_ext4"], "q1_2026_10q"),
] + [(r["date"], "redemption", r["cash"], r["shares"], r["key"]) for r in ROUNDS]
TRUST.sort(key=lambda t: (t[0], t[1] != "report"))
series = [(d, k, n / s, n, s, src) for d, k, n, s, src in TRUST]
check("the trust's value a public share rose at every step, from $10.20 at the IPO to the merger's payout",
      all(b[2] > a[2] for a, b in zip(series, series[1:])),
      " < ".join(f"{float(v):.2f}" for _, _, v, _, _, _ in series))
stated_ps = {date(2024, 12, 31): F["trust_ps_2024_12_31"], date(2025, 9, 30): F["trust_ps_2025_09_30"],
             date(2025, 12, 31): F["trust_ps_2025_12_31"], date(2026, 3, 31): F["trust_ps_2026_03_31"]}
calc_ps = {sd: next(v for d, k, v, *_ in series if d == sd and k == "report") for sd in stated_ps}
check("the filings' own values a share, $11.92, $12.68, $12.95 and $13.19, round from the computed ones but December 31, "
      "2024's, which the 10-K gives a cent lower than $44,332,605 over 3,717,207 shares",
      [sd for sd, sv in stated_ps.items() if round(calc_ps[sd], 2) != sv] == [date(2024, 12, 31)]
      and all(abs(calc_ps[sd] - sv) < Fraction(1, 100) for sd, sv in stated_ps.items()),
      f"December 31, 2024 computes to {float(calc_ps[date(2024, 12, 31)]):.4f}")
check("the two June 30, 2025 trust figures differ, the 10-Q's $6,072,600 against the merger proxy's $6,051,707 in cash",
      F["trust_2025_06_30"] - F["trust_cash_2025_06_30"] == 20_893, "the series uses the 10-Q's")


def growth(v0, v1, d0, d1):
    return (float(v1) / float(v0)) ** (365 / (d1 - d0).days) - 1


pay = [(F["ipo_date"], TRUST_A_SHARE, "IPO")] + [(r["date"], r["a_share"], r["name"]) for r in ROUNDS]
STEPS = [{"from": a[2], "to": b[2], "start": str(a[0]), "end": str(b[0]), "days": (b[0] - a[0]).days,
          "start_value": float(a[1]), "end_value": float(b[1]), "a_year": growth(a[1], b[1], a[0], b[0])}
         for a, b in zip(pay, pay[1:])]
WHOLE = {"days": (F["closing_date"] - F["ipo_date"]).days,
         "trust_growth": float(R["merger"]["a_share"] / TRUST_A_SHARE - 1),
         "trust_a_year": growth(TRUST_A_SHARE, R["merger"]["a_share"], F["ipo_date"], F["closing_date"]),
         "unit_price_growth": float(R["merger"]["a_share"] / F["unit_price"] - 1),
         "unit_price_a_year": growth(F["unit_price"], R["merger"]["a_share"], F["ipo_date"], F["closing_date"])}
for s in STEPS:
    say(f"  {s['from']} to {s['to']}, {s['days']} days, {s['start_value']:.4f} to {s['end_value']:.4f}, "
        f"{pct(s['a_year'], 2)} a year")
say(f"  IPO to the merger, {WHOLE['days']} days, trust {pct(WHOLE['trust_growth'])} or {pct(WHOLE['trust_a_year'], 2)} "
    f"a year. Against the $10.00 unit price {pct(WHOLE['unit_price_growth'])} or {pct(WHOLE['unit_price_a_year'], 2)} a year")

# ---------------------------------------------------------------- USDE against the merger's cash
sa = [r for r in read_csv("usde_daily_stockanalysis_2026-10-12.csv")]
yh = {r["date"]: float(r["close"]) for r in read_csv("usde_daily_yahoo_2026-10-12.csv")}
sw = {r["date"]: r for r in read_csv("usdew_daily_stockanalysis_2026-10-12.csv")}
LISTED = [r for r in sa if date.fromisoformat(r["date"]) >= F["first_trade"]]
early = [r for r in sa if date.fromisoformat(r["date"]) < F["first_trade"]]
EARLY = {"rows": len(early), "first": early[0]["date"], "last": early[-1]["date"],
         "volume_low": min(int(r["volume"]) for r in early), "volume_high": max(int(r["volume"]) for r in early),
         "close_low": min(float(r["close"]) for r in early), "close_high": max(float(r["close"]) for r in early)}
check("USDE's history has 74 sessions from its first Nasdaq session on June 26 to October 9, 2026",
      len(LISTED) == 74 and LISTED[0]["date"] == str(F["first_trade"]) and LISTED[-1]["date"] == "2026-10-09",
      f"{EARLY['rows']} earlier rows from {EARLY['first']} to {EARLY['last']}, closes {EARLY['close_low']:.2f} to "
      f"{EARLY['close_high']:.2f} on {EARLY['volume_low']:,} to {EARLY['volume_high']:,} shares, are left out as "
      "TLGY's over-the-counter shares")
check("every USDE close matches Yahoo Finance's to the cent, on the same 74 dates",
      sorted(yh) == [r["date"] for r in LISTED] and all(abs(round(yh[r["date"]], 2) - float(r["close"])) < 1e-9
                                                        for r in LISTED))
M = R["merger"]["a_share"]
rows = []
for r in LISTED:
    c = Fraction(r["close"])
    rows.append({"date": r["date"], "close": c, "vs": c / M - 1, "at_or_above": c >= M})
above = [r for r in rows if r["at_or_above"]]
lo = min(rows, key=lambda r: r["close"])
hi = max(rows, key=lambda r: r["close"])
first, last = rows[0], rows[-1]
run_start = next(i for i, r in enumerate(rows) if r["at_or_above"])
check("USDE closed at or above the merger's cash a share on 11 sessions, every one from September 22 to October 7 but "
      "September 23", len(above) == 11 and above[0]["date"] == "2026-09-22" and above[-1]["date"] == "2026-10-07"
      and [r["date"] for r in rows[run_start:] if not r["at_or_above"]] == ["2026-09-23", "2026-10-08", "2026-10-09"])
w_first = min(sw)
check("USDEW's history starts June 29 and closed at $3.64 on October 9", w_first == "2026-06-29"
      and sw["2026-10-09"]["close"] == "3.64")
VAL = {"kept_shares": int(KEPT), "at_merger_cash": float(KEPT * M), "at_first_close": float(KEPT * first["close"]),
       "at_last_close": float(KEPT * last["close"]), "at_high_close": float(KEPT * hi["close"]),
       "at_low_close": float(KEPT * lo["close"])}
say(f"  merger cash a share {float(M):.4f}. First close {float(first['close']):.2f} ({pct(first['vs'])}), low "
    f"{float(lo['close']):.2f} on {lo['date']} ({pct(lo['vs'])}), high {float(hi['close']):.2f} on {hi['date']} "
    f"({pct(hi['vs'])}), last {float(last['close']):.2f} ({pct(last['vs'])})")
say(f"  96,349 shares at the merger's cash {money(VAL['at_merger_cash'], 0)}, at the October 9 close "
    f"{money(VAL['at_last_close'], 0)}")

# ---------------------------------------------------------------- the contingent right, cancelled in April 2025
RIGHT_SPLIT = F["right_aggregate"] / KEPT
check("spread over the 96,349 shares kept, the right's 5,750,000 warrants would have come to about 59.7 a share",
      round(float(RIGHT_SPLIT), 1) == 59.7, "the right was cancelled on April 15, 2025, so this is arithmetic only")

if FAILED:
    say(f"{len(FAILED)} check(s) failed. Nothing written.")
    raise SystemExit(1)

# ---------------------------------------------------------------- outputs
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "redemption_votes.csv"), "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["vote", "vote_date", "date_used", "public_shares_before", "shares_redeemed", "share_of_those_before",
                "cash_paid_usd", "cash_basis", "cash_a_share", "filing_price_a_share", "public_shares_after"])
    for r in ROUNDS:
        w.writerow([r["name"], str(r.get("vote", r["date"])), str(r["date"]), int(r["before"]), int(r["shares"]),
                    f"{float(r['of_before']):.6f}", int(r["cash"]), r["basis"], f"{float(r['a_share']):.4f}",
                    ", ".join(f"{k} {float(v):.2f}" for k, v in r["stated"].items()), int(r["after"])])
with open(os.path.join(OUT, "trust_by_year.csv"), "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["year", "trust_at_start_usd", "income_earned_usd", "sponsor_deposits_usd", "taken_out_usd",
                "trust_at_end_usd", "trust_at_end_reported_usd"])
    for y in YEARS:
        w.writerow([y["year"], int(y["start"]), int(y["income"]), int(y["deposits"]), int(y["paid"]), int(y["end"]),
                    int(y["end_reported"])])
with open(os.path.join(OUT, "trust_a_share.csv"), "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["date", "kind", "value_a_share", "amount_usd", "public_shares", "source"])
    for d, k, v, n, s, src in series:
        w.writerow([str(d), k, f"{float(v):.4f}", int(n), int(s), src])
with open(os.path.join(OUT, "usde_against_merger_cash.csv"), "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["date", "usde_close", "merger_cash_a_share", "close_against_cash", "at_or_above", "usdew_close"])
    for r in rows:
        w.writerow([r["date"], f"{float(r['close']):.2f}", f"{float(M):.4f}", f"{float(r['vs']):.4f}",
                    int(r["at_or_above"]), sw[r["date"]]["close"] if r["date"] in sw else ""])


def rnd(r):
    return {"name": r["name"], "date": str(r["date"]), "vote": str(r.get("vote", r["date"])), "before": int(r["before"]),
            "shares": int(r["shares"]), "of_before": float(r["of_before"]), "of_ipo": float(r["of_ipo"]),
            "cash": int(r["cash"]), "a_share": float(r["a_share"]), "after": int(r["after"]),
            "stated": {k: float(v) for k, v in r["stated"].items()},
            "against_unit_price": float(r["a_share"] / F["unit_price"] - 1)}


results = {
    "ipo": {"date": str(F["ipo_date"]), "public_shares": int(IPO_SHARES), "unit_price": float(F["unit_price"]),
            "trust": int(F["trust_initial"]), "trust_a_share": float(TRUST_A_SHARE),
            "public_warrants": int(F["public_warrants"]), "right_warrants": int(F["right_aggregate"])},
    "votes": {r["key"]: rnd(r) for r in ROUNDS},
    "redeemed": int(REDEEMED), "redeemed_share": float(REDEEMED / IPO_SHARES), "cash": int(CASH),
    "average_a_share": float(CASH / REDEEMED), "kept": int(KEPT), "kept_share": float(KEPT / IPO_SHARES),
    "merger_vote_requests": int(F["bc_elections"]), "requests_less_redeemed_at_closing": int(ELECTED_GAP),
    "share_table": {"start": int(F["table_start"]), "redemption": int(F["table_redemption"]),
                    "closing_8k": int(F["merger_shares"]), "gap": int(F["table_redemption"] - F["merger_shares"])},
    "trust_steps": STEPS, "ipo_to_merger": WHOLE,
    "trust_by_year": [{k: (int(v) if isinstance(v, Fraction) else v) for k, v in y.items()} for y in YEARS],
    "income_2022_2025": int(INCOME), "deposits_2022_2025": int(DEPOSITS), "withdrawn_2025_beyond_vote": int(EXTRA_2025),
    "deposits_from_april_2025": {"monthly": float(MONTHLY), "a_share_a_year": float(DEPOSIT_YEAR),
                                 "rise_fourth_to_fifth": float(RISE_4_5), "share_of_rise": float(DEPOSIT_YEAR / RISE_4_5)},
    "deposit_a_share_a_month_early_2025": float(DEPOSIT_2025_Q1_A_SHARE),
    "first_quarter_2026": {"income": int(F["income_q1_2026"]), "deposits": int(F["deposits_q1_2026"]),
                           "end_from_roll_forward": int(Q1_2026_END), "redemption_value": int(F["trust_2026_03_31"])},
    "usde": {"sessions": len(rows), "first": {"date": first["date"], "close": float(first["close"]), "vs": float(first["vs"])},
             "low": {"date": lo["date"], "close": float(lo["close"]), "vs": float(lo["vs"])},
             "high": {"date": hi["date"], "close": float(hi["close"]), "vs": float(hi["vs"])},
             "last": {"date": last["date"], "close": float(last["close"]), "vs": float(last["vs"])},
             "at_or_above": [r["date"] for r in above], "merger_cash_a_share": float(M)},
    "usdew": {"first": {"date": w_first, "close": float(sw[w_first]["close"])},
              "last": {"date": "2026-10-09", "close": float(sw["2026-10-09"]["close"])}},
    "kept_value": VAL,
    "left_before_fifth_vote_share": float(R["ext4"]["after"] / IPO_SHARES),
    "before_merger_agreement": {"date": str(F["bca_date"]), "shares": int(BEFORE_DEAL), "share": float(BEFORE_DEAL / IPO_SHARES),
                                "days_from_fourth_vote_to_closing": (F["closing_date"] - R["ext4"]["date"]).days},
    "extension_votes": {"shares": int(EXTENSIONS), "share": float(EXTENSIONS / IPO_SHARES)},
    "merger_share_of_ipo": float(R["merger"]["shares"] / IPO_SHARES),
    "warrants_after_merger": int(F["warrants_after_merger"]),
    "sponsor_change": {"date": str(F["sponsor_change_date"]), "founder_shares": int(F["sponsor_change_shares"]),
                       "price": float(F["sponsor_change_price"])},
    "share_table_total": int(TABLE_SUM),
    "rows_before_listing": EARLY,
    "right_if_kept": float(RIGHT_SPLIT),
}
with open(os.path.join(OUT, "results.json"), "w") as f:
    json.dump(results, f, indent=1)
    f.write("\n")
say("All checks passed. Tables written to out/.")
with open(os.path.join(OUT, "run_log.txt"), "w") as f:
    f.write("\n".join(LOG) + "\n")
