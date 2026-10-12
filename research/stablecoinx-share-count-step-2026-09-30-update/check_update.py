#!/usr/bin/env python3
"""Checks the figures behind update 21 and the proposed text. Python 3 standard library only. No network."""
import csv
import re
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).parent
f4 = list(csv.DictReader(open(HERE / "inputs" / "form4_director_awards_2026-10-02.csv", newline="")))
assert len(f4) == 5 and len({r["reporting_owner"] for r in f4}) == 5
assert all(r["is_director"] == "1" and r["issuer_cik"] == "0002080215" and r["security"] == "Class A Common Stock" and r["transaction_date"] == "2026-09-30"
           and r["transaction_code"] == "A" and r["acquired_disposed"] == "A" and Fraction(r["shares"]) == 22000 and Fraction(r["price_per_share"]) == 0
           and r["filed"] == "2026-10-02" for r in f4)
assert all("restricted stock that vests in four equal quarterly installments beginning on October 1, 2026" in r["footnote_F1"] for r in f4)
awarded = sum(int(Fraction(r["shares"])) for r in f4)
assert awarded == 110_000

steps = {r["date"]: int(r["shares_outstanding"]) for r in csv.DictReader(open(HERE / "inputs" / "shares_out_598dac4.csv", newline=""))}
assert steps == {"2026-06-26": 24_029_375, "2026-09-30": 24_139_375}
assert steps["2026-09-30"] - steps["2026-06-26"] == awarded

reads = (HERE / "inputs" / "sec_reads_2026-10-12.txt").read_text()
assert "As of August 28, 2026, prior to the issuance and resale of the securities offered by this prospectus, we had a total of 24,029,375 shares of our Class A Common Stock outstanding." in reads
assert "no filing after these five as of the read" in reads

before, after = steps["2026-06-26"], steps["2026-09-30"]
rise = Fraction(after - before, before) * 100
ena_per_share = (Fraction(before, after) - 1) * 100
print(f"awarded {awarded:,} shares, count {before:,} to {after:,}, +{float(rise):.4f}%, ENA per share {float(ena_per_share):.4f}%")
assert round(rise, 2) == Fraction(46, 100) and round(-ena_per_share, 2) == Fraction(46, 100)

text = (HERE / "proposed_text.md").read_text()
for phrase in ("On September 30, 2026 five directors each received 22,000 restricted Class A shares, which vest in four quarterly installments from October 1, "
               "and the count rose from 24,029,375 to 24,139,375.",
               "The company last stated its own count as 24,029,375 Class A shares as of August 28, 2026, so 24,139,375 is derived until a later company filing states a count.",
               "110,000 restricted shares awarded to five directors took the count to 24,139,375"):
    assert phrase in text, phrase
body = re.sub(r'"[^"]*"', "", text)
assert not any(ch in body for ch in ("—", "–", ";", ":")), "punctuation"
print("All checks pass.")
