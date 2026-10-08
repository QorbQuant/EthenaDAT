#!/usr/bin/env python3
"""
Recomputes every computed figure in article_draft.md and metadata.json with code written separately from
stablecoinx_waiver_review.py, then confirms that the exact phrase appears in the text.

Run from this directory:  python3 check_article_numbers.py
Uses exact fractions, reads only inputs/, and exits with an error if any phrase is missing.
"""
import csv
import json
import sys
from datetime import date, timedelta
from fractions import Fraction as Fr
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "article_draft.md").read_text(encoding="utf-8")
META = json.loads((HERE / "metadata.json").read_text(encoding="utf-8"))
ALL = TEXT + "\n" + json.dumps(META, ensure_ascii=False)
facts = {r["fact"]: Fr(r["value"]) for r in csv.DictReader(open(HERE / "inputs" / "filing_facts.csv"))}
data = json.load(open(HERE / "inputs" / "ethenadat_data_e57e314.json"))
pre = json.load(open(HERE / "inputs" / "ethenadat_data_4c7c3a7.json"))
series = data["series"]

checked = []
missing = []


def need(phrase, where=ALL):
    checked.append(phrase)
    if phrase not in where:
        missing.append(phrase)


def commas(n, places=0):
    n = Fr(n)
    q = round(n * 10 ** places)
    whole, frac = divmod(abs(q), 10 ** places)
    s = f"{whole:,}"
    if places:
        s += "." + str(frac).zfill(places)
    return ("-" if q < 0 else "") + s


def fixed(v, places):
    q = round(Fr(v) * 10 ** places)
    s = str(abs(q)).zfill(places + 1)
    return ("-" if q < 0 else "") + (s[:-places] + "." + s[-places:] if places else s)


def pct(v, places=1):
    return fixed(Fr(v) * 100, places) + "%"


def money(v, places=2):
    return "$" + fixed(v, places)


def mult(v, places):
    return fixed(v, places) + "×"


# ---------- token counts from the filings ----------
p1 = facts["tpa1_vwap"] * (1 - facts["tpa1_discount"])
t1, t2 = facts["tpa1_tokens"], facts["tpa2_tokens"]
assert abs(facts["tpa1_amount"] / p1 - t1) < Fr(1, 100) and abs(facts["tpa2_amount"] / facts["tpa2_price"] - t2) < Fr(1, 100)
contrib = facts["contrib_tokens"]
assert abs(facts["contrib_usd"] / facts["contrib_price"] - contrib) < Fr(1, 100)
kj, ks = facts["inkind_july_tokens"], facts["inkind_sept_tokens"]
for v in (t1, t2, contrib, kj, ks):
    need(commas(v, 2))
need(commas(t1 + t2, 2))
need(commas(t1 + t2 + contrib + kj + ks, 2))
need(commas(contrib))
need(commas(kj))
need(commas(contrib + kj))
need(pct((contrib + kj) / 3029000000))
need(commas(facts["q2_pipe_july_tokens"] - t1 - kj, 2).lstrip("-"))     # the 10-Q's July count is lower by this
holdings = Fr(int(data["ena_holdings"]))
need(commas(holdings))
tr = {r["tranche"]: Fr(r["tokens"]) for r in csv.DictReader(open(HERE / "inputs" / "ena_tranches_e57e314.csv"))}
need(commas(holdings - tr["cash_pipe_initial"] - tr["cash_pipe_additional"]))


# ---------- the old schedule, counted month by month ----------
def months_between(start, d):
    """Whole months from start to d, counting a month as complete on the same day number or the month's last day."""
    m = (d.year - start.year) * 12 + (d.month - start.month)
    last = [31, 29 if d.year % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][d.month - 1]
    if d.day < min(start.day, last):
        m -= 1
    return m


def frac_unlocked(start, d):
    m = months_between(start, d)
    if m < 12:
        return Fr(0)
    return min(Fr(1), Fr(1, 4) + Fr(3, 4) * min(36, m - 12) / 36)


oct4 = date(2026, 10, 4)
f1 = {frac_unlocked(date(2025, 7, k), oct4) for k in range(21, 32)}
f2 = {frac_unlocked(date(2025, 9, k), oct4) for k in range(5, 31)}
assert f1 == {Fr(7, 24)} and f2 == {Fr(1, 4)}
locked = t1 * (1 - Fr(7, 24)) + t2 * Fr(3, 4)
need(commas(locked))
need(pct(locked / holdings))
need(pct(Fr(7, 24)))
need("25% of the September purchase")
need(commas(t1 * Fr(3, 4) / 36))
need(commas(t2 * Fr(3, 4) / 36))
need(fixed(locked / 10 ** 9, 2) + " billion")
need(fixed((t1 + t2) / 10 ** 9, 2) + " billion")
assert date(2025, 7, 31).replace(year=2029) == date(2029, 7, 31) and date(2025, 9, 30).replace(year=2029) == date(2029, 9, 30)
need("until July and September 2029")

# ---------- dashboard rows ----------
def row(ds, day):
    i = ds["series"]["date"].index(day)
    return {k: ds["series"][k][i] for k in ds["series"]}


r2, r5, r7 = row(data, "2026-10-02"), row(data, "2026-10-05"), row(data, "2026-10-07")
assert row(pre, "2026-10-02") == r2
for r in (r2, r5, r7):
    need(money(Fr(str(r["usde_close"]))))
    need("$" + str(r["ena_price"]))
shares = Fr(int(r2["shares_outstanding"]))
assert shares == Fr(int(r5["shares_outstanding"])) == Fr(int(r7["shares_outstanding"])) == 24139375


def nps(u, r):
    return Fr(u) * Fr(str(r["ena_price"])) / shares


u2 = Fr(int(r2["ena_unlocked"]))
assert round(holdings - tr["cash_pipe_initial"] * (1 - Fr(7, 24)) - tr["cash_pipe_additional"] * Fr(3, 4)) == u2
need(commas(u2))
need(pct(u2 / holdings))
need(money(nps(u2, r2)))
need(money(nps(holdings, r5)))
need(money(nps(holdings, r2)))
need(money(nps(holdings, r7)))
need(mult(Fr(str(r2["usde_close"])) / nps(u2, r2), 3))
need(mult(Fr(str(r5["usde_close"])) / nps(holdings, r5), 3))
need(mult(Fr(str(r7["usde_close"])) / nps(holdings, r7), 3))
need(mult(Fr(str(r2["usde_close"])) / nps(holdings, r2), 3))
cf5 = Fr(str(r5["usde_close"])) / nps(u2, r5)
cf7 = Fr(str(r7["usde_close"])) / nps(u2, r7)
need(mult(cf5, 2))
# the September schedule read from September 5, 2025: one monthly step of the September purchase falls due on October 5
u_sep5 = u2 + tr["cash_pipe_additional"] * Fr(3, 4) / 36
assert months_between(date(2025, 9, 5), date(2026, 10, 5)) == 13 and months_between(date(2025, 9, 5), date(2026, 10, 4)) == 12
need(mult(Fr(str(r5["usde_close"])) / nps(u_sep5, r5), 2))
need("by " + fixed(holdings / round(u_sep5), 2) + " rather than " + fixed(holdings / u2, 2))
need(commas(tr["cash_pipe_additional"] * Fr(3, 4) / 36))
need(str((date(2025, 9, 30) - date(2025, 9, 5)).days) + " days before")
need(fixed(abs(facts["q2_pipe_sept_tokens"] - t2 - ks), 2) + " ENA lower")
need(pct(Fr(str(r5["usde_close"])) / Fr(str(r2["usde_close"])) - 1))
need(pct(1 - Fr(str(r5["ena_price"])) / Fr(str(r2["ena_price"]))))
need("by " + fixed(holdings / u2, 2))
low = u2 - contrib - kj
need(commas(low))
need(pct(low / holdings))
need(mult(Fr(str(r2["usde_close"])) / nps(low, r2), 2))

# ---------- dates ----------
due = date(2026, 9, 30) + timedelta(days=int(facts["form10q_days_other"]))
assert due.strftime("%A") == "Saturday"
need("Saturday, " + due.strftime("%B") + " " + str(due.day))
nxt = due + timedelta(days=2)
need(nxt.strftime("%A") + ", " + nxt.strftime("%B") + " " + str(nxt.day))
need(str(int(facts["form10q_days_other"])) + " days")
need("July 21, 20" + str(25 + int(facts["ca_initial_term_years"])))
need("by five days")
assert (date(2026, 10, 5) - date(2026, 9, 30)).days == 5
need(str(int(facts["wl_clearance_days"])) + " days")
need("five business days")
need("zero to 36 months")
need("0 to 36 months")
need("48-month schedule")
dates = {r["event"]: r["date"] for r in csv.DictReader(open(HERE / "inputs" / "filing_dates.csv"))}
first, last = date.fromisoformat(dates["inkind_unlock_months_first"]), date.fromisoformat(dates["inkind_unlock_months_last"])
need(f"from {first:%B} {first.year} to {last:%B} {last.year}")

# ---------- metadata ----------
assert META["datePublished"] == META["dateModified"] == "2026-10-08"
assert len(META["description"]) <= 160 and META["headline"] in TEXT.splitlines()[0]
need("October 5, 2026", META["description"])

print(f"{len(checked) - len(missing)} of {len(checked)} phrases found.")
if missing:
    print("Missing:")
    for m in missing:
        print("  ", m)
    sys.exit(1)
