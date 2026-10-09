#!/usr/bin/env python3
"""
Recomputes every computed figure in article_draft.md and metadata.json with code written separately from
usdeb_review.py, using exact fractions and plain Unix seconds, and confirms that each phrase appears in the text.
Run after any edit:  python3 check_article_numbers.py   It exits with an error if a phrase is missing.
"""
import csv
import json
import sys
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).parent
art = (HERE / "article_draft.md").read_text()
meta = (HERE / "metadata.json").read_text()
text = art + "\n" + meta
flows = json.loads((HERE / "inputs" / "usdeb_flows_e7fb070.json").read_text())
checks = {r["check"]: r for r in csv.DictReader(open(HERE / "inputs" / "chain_checks.csv"))}
holders = {r["rank"]: r for r in csv.DictReader(open(HERE / "inputs" / "bscscan_holders_top.csv"))}
pending = json.loads((HERE / "inputs" / "usdeb_flow_pending_e7fb070.json").read_text())
closes = {r["date"]: r["close"] for r in csv.DictReader(open(HERE / "inputs" / "usde_close.csv"))}
dataset = json.loads((HERE / "inputs" / "data_e7fb070.json").read_text())["series"]

E18 = 10 ** 18
OPEN = 1791374400          # 2026-10-07 12:00:00 UTC in Unix seconds
MIDNIGHT = 1791417600      # 2026-10-08 00:00:00 UTC
CUT = 1791498505           # 2026-10-08 22:28:25 UTC, the supply check block's time
DAY0 = 1791331200          # 2026-10-07 00:00:00 UTC


def hms(sec):
    s = sec % 86400
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def hm_round(sec):
    s = (sec + 30) % 86400
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}"


def fmt(x, nd):
    q = round(x, nd)
    whole = int(q)
    frac = abs(q - whole)
    s = f"{whole:,}"
    if nd:
        s += "." + str(round(frac * 10 ** nd)).zfill(nd)
    return s


assert hms(OPEN) == "12:00:00" and hms(CUT) == "22:28:25" and (OPEN - DAY0) == 12 * 3600 and (MIDNIGHT - DAY0) == 86400
ev = [(e["t"] // 1000, e["kind"], F(int(e["rawAmount"]), E18)) for e in flows["events"]]
mints = [a for t, k, a in ev if k == "mint"]
burns = [a for t, k, a in ev if k == "burn"]
supply = sum(mints) - sum(burns)
assert supply == F(int(checks["total_supply_raw"]["value"]), E18), "supply against the chain check"
running, levels = F(0), []
for t, k, a in ev:
    running += a if k == "mint" else -a
    levels.append((t, k, a, running))
pre = [x for x in levels if x[0] < OPEN]
peak = max(levels, key=lambda x: x[3])
burn = [x for x in levels if x[1] == "burn"][0]
director_awards = 5 * 22000            # five restricted-stock awards of 22,000 shares, Forms 4 of October 2, 2026
class_a = 24029375 + director_awards   # prospectus of September 14, 2026, as of August 28, 2026
assert class_a == int(dataset["shares_outstanding"][-1]), "Class A count against the dashboard dataset"
share = supply / class_a * 100
close = F(closes["2026-10-08"])
assert dataset["date"][-1] == "2026-10-08" and F(str(dataset["usde_close"][-1])) == close, "close against the dashboard dataset"
value = supply * close
ADMITTED = 1200000                     # admission notice of October 7, 2026, paragraph 4
per = []
for lo, hi in ((0, OPEN), (OPEN, MIDNIGHT), (MIDNIGHT, CUT + 1)):
    sel = [x for x in levels if lo <= x[0] < hi]
    per.append((sum(1 for x in sel if x[1] == "mint"), sum(x[2] for x in sel if x[1] == "mint"),
                sum(1 for x in sel if x[1] == "burn"), sum(x[2] for x in sel if x[1] == "burn"),
                [x for x in levels if x[0] < hi][-1][3]))
offsets = [x[0] % 300 for x in levels if x[1] == "mint"]
at_open = pre[-1][3]
flows_observed = flows["observedAt"][11:16]
pending_time = hms(int(pending["block"]["timestamp"], 16))[:5]
top1, top2, top3 = (F(holders[r]["quantity"]) / supply * 100 for r in ("1", "2", "3"))

phrases = [
    # lead
    f"{fmt(supply, 2)} USDEB were outstanding. At one share per token, that was {fmt(share, 2)}% of the {class_a:,} Class A shares",
    # holder rights section
    "it listed 87 bStocks",
    # supply section
    f"had no tokens outstanding until {hm_round(ev[0][0])} UTC on October 7",
    f"admitted up to {ADMITTED:,} USDEB to trading at the open",
    f"At the open, {fmt(at_open, 0)} USDEB existed, {fmt(at_open / ADMITTED * 100, 1)}% of that number",
    f"| {per[0][0]} | {fmt(per[0][1], 2)} | {per[0][2]} | {fmt(per[0][3], 2)} | {fmt(per[0][4], 2)} |",
    f"| {per[1][0]} | {fmt(per[1][1], 2)} | {per[1][2]} | {fmt(per[1][3], 2)} | {fmt(per[1][4], 2)} |",
    f"| {per[2][0]} | {fmt(per[2][1], 2)} | {per[2][2]} | {fmt(per[2][3], 2)} | {fmt(per[2][4], 2)} |",
    f"the October 8 Nasdaq close of ${close.numerator / close.denominator:.2f}, the {fmt(supply, 2)} USDEB outstanding at the cutoff "
    f"would correspond to about ${fmt(round(value / 1000) * 1000, 0)} of stock",
    f"Each of the {len(mints)} mints landed between {min(offsets)} and {max(offsets)} seconds after a five-minute mark",
    f"with {fmt(top1, 1)}% of supply",
    f"held another {fmt(top2, 1)}%",
    # checks section
    f"listed {len(mints)} mints and one burn through {flows_observed} UTC, and a later chain reading by its collector found the same supply at {pending_time} UTC",
    f"Each of those {len(ev)} events also matched the record of its transaction",
    f"showed the same {len(ev)} events and no others at {checks['bscscan_zero_address_transfers']['observed_at_utc'][11:16]} UTC",
    f"At block {int(checks['total_supply_raw']['block']):,}, at {hms(CUT)} UTC, totalSupply read {fmt(supply, 8)} USDEB, "
    f"equal to {fmt(sum(mints), 8)} minted less {fmt(sum(burns), 8)} burned",
    # chart alt text and metadata
    f"reached {fmt(pre[-1][3], 0)} before trading opened at 12:00 UTC",
    f"peaked at {fmt(peak[3], 0)} at {hm_round(peak[0])} UTC",
    f"fell to {fmt(burn[3], 0)} after a burn of {fmt(burn[2], 0)} at {hm_round(burn[0])} UTC, both on October 7",
    f"stood at {fmt(supply, 0)} at {hm_round(CUT)} UTC on October 8",
    f"which peaked at {fmt(peak[3], 0)} and stood at {fmt(supply, 0)} at {hm_round(CUT)} UTC on October 8",
    # method
    f"adds {director_awards:,} shares from five director restricted-stock awards, reported on Forms 4 on October 2, to the 24,029,375 shares",
    f"supply in USDEB ÷ {class_a:,}",
]
assert (burn[0] - DAY0) // 86400 == 0 and (peak[0] - DAY0) // 86400 == 0
assert len(burns) == 1 and peak[0] < burn[0] and pre[-1][3] == F(25771) and int(pending["values"]["rawSupply"], 16) == supply * E18
missing = [p for p in phrases if p not in text]
for p in phrases:
    print(("ok      " if p in text else "MISSING ") + p)
print(f"{len(phrases) - len(missing)} of {len(phrases)} phrases found.")
if missing:
    sys.exit(1)
