#!/usr/bin/env python3
"""
Recomputes every computed figure in article_draft.md, metadata.json and the chart's text from the files in inputs/,
with code written apart from tlgy_redemption_review.py, and confirms that each exact phrase appears. It reads the
filing figures straight from the saved extracts with its own patterns and compares them with filing_facts.csv. Exits
with an error if a phrase is missing or an assertion fails, so rerun it after any edit. Python 3 standard library
only. No network.
"""
import csv
import html
import json
import re
import sys
import unicodedata
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path

getcontext().prec = 50
HERE = Path(__file__).parent
INP = HERE / "inputs"
ARTICLE = (HERE / "article_draft.md").read_text()
META = json.loads((HERE / "metadata.json").read_text())
LAYOUT = json.loads((HERE / "layout.json").read_text()) if (HERE / "layout.json").exists() else None   # the site's page layout, not in the download
SVG = (HERE / "out" / "chart_tlgy_redemptions.svg").read_text()
TEXT = ARTICLE + "\n" + META["description"] + "\n" + META["imageAlt"] + "\n" + META["title"] + "\n" + META["headline"] + "\n" + SVG
found, missing = 0, []


def need(phrase, where=TEXT):
    global found
    if phrase in where:
        found += 1
    else:
        missing.append(phrase)


def rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def r2(x, nd=2):
    return Decimal(x).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)


def usd(x, nd=2):
    return f"${r2(x, nd):,}"


def pc(x, nd=1):
    return f"{r2(Decimal(x) * 100, nd)}%"


def n(x):
    return f"{int(x):,}"


# ---------------------------------------------------------------- the extracts, read with their own patterns
WINDOWS = {}
for name in sorted(INP.glob("sec_extracts*_2026-10-12.txt")):
    key = None
    for line in name.read_text(encoding="utf-8").split("\n"):
        if line.startswith("### "):
            key = line.split()[1]
        elif key and line.startswith("- @"):
            WINDOWS.setdefault(key, []).append(line.split(" ", 2)[2])
assert len(list(INP.glob("sec_extracts*_2026-10-12.txt"))) == 5


def grab(key, pattern, group=1):
    for w in WINDOWS[key]:
        m = re.search(pattern, w)
        if m:
            return m.group(group)
    raise AssertionError(f"no match for {pattern} in {key}")


def num(s):
    return Decimal(s.replace(",", "").replace("$", ""))


facts = {r["id"]: r["value"] for r in rows(INP / "filing_facts.csv")}


def same(fid, value):
    assert Decimal(facts[fid]) == value, (fid, facts[fid], value)
    return value


units = same("ipo_units", num(grab("ipo_8k", r"public offering \(the .IPO.\) of ([\d,]+) units")))
option = same("option_units", num(grab("ipo_8k2", r"purchased an additional ([\d,]+) Units")))
price = same("unit_price", num(grab("ipo_8k", r"sold at a price of \$([\d.]+) per Unit")))
trust0 = same("trust_initial", num(grab("ipo_8k2", r"approximately \$([\d,]+) of the proceeds")))
trust_unit = same("trust_per_unit", num(grab("ipo_424b4", r"\(\$([\d.]+) per unit in either case\)")))
right_total = same("right_aggregate", num(grab("ipo_424b4", r"or ([\d,]+) warrants if the over-allotment")))
public = units + option
assert public == 23_000_000 and trust0 / public == trust_unit == Decimal("10.20") and right_total == public / 4

v = {}
v["ext1"] = (num(grab("ext1_8k", r"([\d,]+) ordinary shares of the Company were rendered")),
             num(grab("q1_2023_10q", r"Cash withdrawn from Trust Account ([\d,]+)")))
both_2023 = num(grab("k10_2023", r"\$([\d,]+) was withdrawn from the Trust Account in order to pay"))
v["ext2"] = (num(grab("ext2_8k", r"([\d,]+) ordinary shares of the Company were rendered")), both_2023 - v["ext1"][1])
v["ext3"] = (num(grab("ext3_8k", r"([\d,]+) ordinary shares of the Company were tendered")),
             num(grab("k10_2024", r"2,205,658 shares were redeemed by public shareholders\. Accordingly, \$([\d,]+)")))
v["ext4"] = (num(grab("ext4_8k", r"holders of ([\d,]+) Class A ordinary shares properly exercised")),
             num(grab("q2_2025_10q", r"As a result, \$([\d,]+) was removed")))
v["ext5"] = (num(grab("ext5_8k", r"holding ([\d,]+) Class A Ordinary Shares")),
             num(grab("q1_2026_10q", r"As a result, \$([\d,]+) was removed")))
v["merger"] = (num(grab("closing_8k", r"a total of ([\d,]+) Public Shares were redeemed")),
               num(grab("closing_8k", r"aggregate redemption amount of approximately \$([\d,]+)")))
for k, fid in (("ext1", "ext1_shares"), ("ext2", "ext2_shares"), ("ext3", "ext3_shares"), ("ext4", "ext4_shares"),
               ("ext5", "ext5_shares"), ("merger", "merger_shares")):
    same(fid, v[k][0])
assert v["ext1"][0] + v["ext2"][0] == num(grab("k10_2023", r"an aggregate of ([\d,]+) shares were redeemed"))
order = ["ext1", "ext2", "ext3", "ext4", "ext5", "merger"]
label = {"ext1": ("First extension", "February 23, 2023"), "ext2": ("Second extension", "October 17, 2023"),
         "ext3": ("Third extension", "April 16, 2024"), "ext4": ("Fourth extension", "April 15, 2025"),
         "ext5": ("Fifth extension", "April 15, 2026"), "merger": ("Merger", "Voted March 10, paid June 25, 2026")}
assert grab("ext1_8k", r"On (February 23, 2023), shareholders") == label["ext1"][1]
assert grab("ext2_8k", r"On (October 17, 2023), shareholders") == label["ext2"][1]
assert grab("ext3_8k", r"On (April 16, 2024), shareholders") == label["ext3"][1]
assert grab("ext4_8k", r"On (April 15, 2025), TLGY") == label["ext4"][1]
assert grab("ext5_8k", r"On (April 15, 2026), TLGY") == label["ext5"][1]
assert grab("bc_vote_8k", r"On (March 10), 2026, TLGY") == "March 10" and "on June 25, 2026" in WINDOWS["closing_8k"][0]
left = public
reported_left = {"ext1": num(grab("q1_2023_10q", r"the ([\d,]+) and 23,000,000 Class A")),
                 "ext2": num(grab("k10_2024", r"the 3,717,207 and ([\d,]+), respectively")),
                 "ext3": num(grab("q2_2024_10q", r"the ([\d,]+) and 5,922,865 Class A")),
                 "ext4": num(grab("ext4_8k", r"approximately ([\d,]+) Class A ordinary shares are subject to future"))}
per = {}
for k in order:
    sh, cash = v[k]
    before, left = left, left - sh
    if k in reported_left:
        assert left == reported_left[k], k
    per[k] = cash / sh
    cash_txt = ("about " if k == "merger" else "") + usd(cash, 0)
    need(f"| {label[k][0]} | {label[k][1]} | {n(sh)} | {pc(sh / before)} | {cash_txt} | {usd(per[k])} | {n(left)} |")
kept = left
red = sum(v[k][0] for k in order)
cash_all = sum(v[k][1] for k in order)
avg = cash_all / red
assert kept == 96_349 and red + kept == public
need(f"| All six | | {n(red)} | {pc(red / public)} of {n(public)} | about {usd(cash_all, 0)} | {usd(avg)} | {n(kept)} |")
need(f"Holders handed back for cash {pc(red / public)} of the shares that TLGY Acquisition Corp. sold to the public, most of "
     "them more than a year before its merger with StablecoinX Inc.")
bca = grab("bc_vote_8k", r"the business combination agreement, dated (July 21, 2025)")
assert bca == "July 21, 2025"
early = ["ext1", "ext2", "ext3", "ext4"]
before_deal = sum(v[k][0] for k in early)
assert all(D_vote < (2025, 7, 21) for D_vote in ((2023, 2, 23), (2023, 10, 17), (2024, 4, 16), (2025, 4, 15)))
assert before_deal > red / 2
need(f"At four votes from February 2023 to April 2025, all before TLGY agreed on {bca} to merge with StablecoinX, holders "
     f"redeemed {n(before_deal)} public shares, {pc(before_deal / public)} of those sold")
need(f"They redeemed {n(v['ext5'][0])} more at a fifth vote in April 2026 and {n(v['merger'][0])} in connection with the merger, "
     "paid at the June 25, 2026 closing")
need(f"It sold {n(public)} units at {usd(price)} each in its initial public offering, or IPO, in December 2021 and put "
     f"{usd(trust_unit)} a unit into a trust account")
unit_text = WINDOWS["ipo_8k"][1]
assert all(t in unit_text for t in ("(i) one Class A ordinary share", "(ii) one-half of one detachable redeemable warrant",
                                    "(iii) a contingent right to receive at least one-fourth of one redeemable warrant"))
need("Each unit held one Class A share, here a public share, half a warrant to buy a share and a contingent right to more warrants")
need(f"In all, {n(red)} public shares brought about ${r2(cash_all / 1_000_000, 1)} million, an average of {usd(avg)} a share")
assert all(per[a] < per[b] for a, b in zip(order, order[1:]))
need(f"The cash a share, the cash paid divided by the shares redeemed, rose with each redemption, from {usd(per['ext1'])} at the "
     f"February 2023 vote to about {usd(per['merger'])} at the merger")
need(f"The {n(kept)} public shares that were never redeemed, {pc(kept / public, 2)} of those sold")
table = (num(grab("sx_q2_10q", r"outstanding prior to the Merger ([\d,]+)")),
         num(grab("sx_q2_10q", r"Sponsor forfeiture \(([\d,]+)\)")),
         num(grab("sx_q2_10q", r"Redemption of TLGY Class A common stock \(([\d,]+)\)")),
         num(grab("sx_q2_10q", r"Class A common stock of TLGY ([\d,]+)")))
assert table[0] - table[1] - table[2] == table[3] and table[2] == v["ext5"][0] + v["merger"][0]
assert table[0] == num(grab("ext4_8k", r"approximately ([\d,]+) Class A ordinary shares outstanding"))
assert table[0] == num(grab("bc_vote_8k", r"there were ([\d,]+) Class A ordinary shares"))
need(f"StablecoinX's own count of its shares right after the merger deducts {n(table[2])} redeemed TLGY shares, "
     f"{n(table[2] - v['merger'][0])} more than the {n(v['merger'][0])} it reported redeemed at the closing")
need(f"The difference matches the {n(v['ext5'][0])} redeemed at the fifth vote, the likely explanation for a gap that the site's "
     "[float review]")
total = num(grab("sx_q2_10q", r"immediately after the Merger ([\d,]+)"))
parts = [table[3]] + [num(grab("sx_q2_10q", pat)) for pat in (r"PIPE shares ([\d,]+)", r"Ethena contribution shares ([\d,]+)",
                                                               r"TLGY Class B common stock, outstanding prior to the Merger ([\d,]+)",
                                                               r"Legacy Stablecoin X Assets Shares ([\d,]+)")]
assert sum(parts) == total == num(grab("closing_8k", r"consisting of ([\d,]+) shares of StablecoinX Class A"))
assert "immediately following the consummation of the Merger" in " ".join(WINDOWS["sx_q2_10q"])
assert table[0] == num(grab("def14a_2026", r"consisting of ([\d,]+) Class A ordinary shares"))   # the fifth vote's record date
need(f"Since the share table starts from a count taken before the fifth vote, its {n(table[2])} appears to take in both 2026 "
     "redemptions, though no filing read says so in words")
need(f"Its lines add up to the {n(total)} Class A shares that the 8-K on the closing gives")
need(f"By the vote counts and by the share table, {n(kept)} public shares were left")
# the founder shares and the float review's 644,590
class_b = num(grab("sx_q2_10q", r"TLGY Class B common stock, outstanding prior to the Merger ([\d,]+)"))
assert table[3] + class_b - 644_590 == kept   # the float review's own reconciliation, 635,939 + 105,000 - 644,590
assert "Class B ordinary shares of the Company (the \u201cFounder Shares\u201d)" in WINDOWS["k8_2024_06_21"][0]
assert any("converted all of their Class B ordinary shares into Class A ordinary shares" in w and
           "of which approximately 489,887 Class A ordinary shares are subject to future redemptions" in w for w in WINDOWS["ext4_8k"])
assert any("excluded from the pro rata calculation used to determine the per-share Redemption Price" in w for w in WINDOWS["defm14a"])
assert any("sale of the Private Placement Warrants" in w for w in WINDOWS["ipo_8k"])
assert "(Parallel), LP (the \u201cSponsors\u201d)" in " ".join(WINDOWS["ext4_8k"])   # the sponsors are the two CPC funds
assert any("the Sponsors and TLGY Sponsors LLC converted" in w for w in WINDOWS["ext4_8k"])   # and one other founder shareholder
assert any("the private placement with the Sponsor" in w for w in WINDOWS["ipo_8k2"])
need("The founder shares, TLGY's Class B shares, belonged to the sponsors and other founder shareholders and were left out of "
     "the calculation of the price a share")
need("TLGY's 8-K on the fourth vote reported that the sponsors and one other founder shareholder had converted theirs into "
     "Class A shares, which could not be redeemed either")
need("The site's float review counts 644,590 StablecoinX Class A shares, and as many Class B shares, that the founder "
     "shareholders received for their founder shares and for warrants that TLGY sold privately to its sponsor at the IPO")
need("TLGY's and StablecoinX's filings with the U.S. Securities and Exchange Commission, or SEC, their current reports on Form 8-K")
# terms defined at first use
assert ARTICLE.find("IPO") == ARTICLE.find("or IPO,") + 3
assert ARTICLE.find("SEC") == ARTICLE.find("or SEC,") + 3
assert ARTICLE.find("8-K") == ARTICLE.find("Form 8-K") + 5

# the filings' own prices a share, against the cash paid
assert abs(per["ext1"] - num(grab("ext1_8k", r"approximately \$([\d.]+) per share"))) < Decimal("0.005")
assert abs(per["ext2"] - num(grab("ext2_8k", r"approximately \$([\d.]+) per share"))) < Decimal("0.005")
est3 = num(grab("ext3_8k", r"approximately \$([\d.]+) per share"))
assert abs(per["ext3"] - est3) > Decimal("0.04")
assert abs(per["ext4"] - num(grab("ext4_8k", r"approximately \$([\d.]+) per share"))) < Decimal("0.005")
note5 = num(grab("q1_2026_10q", r"or approximately \$([\d.]+) per share\. As a result"))
mdna5 = num(grab("q1_2026_10q", r"per-share price of approximately \$([\d.]+) per share"))
proxy5 = num(grab("def14a_2026", r"will be approximately \$([\d.]+) at the time"))
assert abs(per["ext5"] - mdna5) < Decimal("0.005") < abs(per["ext5"] - note5) and proxy5 == note5
assert abs(per["merger"] - num(grab("closing_8k", r"approximately \$([\d.]+) per share"))) < Decimal("0.005")
need(f"less the first vote's {usd(v['ext1'][1], 0)}")
need(f"the {usd(both_2023, 0)} that TLGY's 10-Ks give for both 2023 votes")
assert num(grab("k10_2024", r"in connection with redemptions 25,092,549 ([\d,]+)")) == both_2023
need(f"The merger's share of those outstanding is of the {n(reported_left['ext4'] - v['ext5'][0])} public shares left after the fifth vote")
need(f"estimated about {usd(est3)} a share, while the trust paid out {usd(v['ext3'][1], 0)}, or {usd(per['ext3'])} a share")
need(f"gives about {usd(note5)} a share in one place and about {usd(mdna5)} in another, and the proxy for that vote expected about {usd(proxy5)}")
need(f"The {usd(v['ext5'][1], 0)} paid comes to {usd(per['ext5'])}")
need(f"Holders of {pc(v['ext1'][0] / public)} of the public shares redeemed at the first vote, and of "
     f"{pc(v['ext4'][0] / reported_left['ext3'])} of those left at the fourth")
need(f"{n(reported_left['ext4'])} public shares remained, {pc(reported_left['ext4'] / public)} of those sold")
assert grab("k8_2024_12_05", r"On (December 2, 2024), TLGY") == "December 2, 2024"
assert grab("k8_2024_12_05", r"opening of business on (December 9, 2024)") == "December 9, 2024"
assert "2025-05-08 By" in WINDOWS["f25_2025_05_08"][2] and "IM 5101-2" in WINDOWS["k8_2024_12_05"][0]
assert "36 months of the effective date of its registration statement" in WINDOWS["k8_2024_12_05"][0]
assert "and was therefore subject to delisting" in " ".join(WINDOWS["k8_2024_12_05"])
assert "will not request a hearing" in WINDOWS["k8_2024_12_05"][1] and "intends to trade on the over the counter" in WINDOWS["k8_2024_12_05"][1]
need("On December 2, 2024 Nasdaq's staff told TLGY that, because it had not completed a merger within 36 months of its IPO "
     "registration statement taking effect, it was not in compliance with Nasdaq IM 5101-2 and was subject to delisting")
need("TLGY said it would not request a hearing and intended to trade over the counter, and that trading on Nasdaq would be "
     "suspended from December 9, 2024")
need("On May 8, 2025 Nasdaq filed to remove its shares, warrants and units from listing")

# ---------------------------------------------------------------- the trust year by year
inc = {"2022": num(grab("k10_2022", r"Investments held in Trust Account ([\d,]+)")),
       "2023": num(grab("k10_2023", r"investments held in Trust Account ([\d,]+) 2,901,000")),
       "2024": num(grab("k10_2024", r"investments held in Trust Account ([\d,]+) 5,072,178")),
       "2025": num(grab("k10_2025", r"investments held in Trust Account ([\d,]+) 2,598,427"))}
dep = {"2022": Decimal(0), "2023": num(grab("k10_2023", r"Cash deposited into Trust Account \(([\d,]+)\)")),
       "2024": num(grab("k10_2024", r"Cash deposited into Trust Account \(([\d,]+)\)")),
       "2025": num(grab("k10_2025", r"Cash deposited into Trust Account \(([\d,]+)\)"))}
out = {"2022": Decimal(0), "2023": num(grab("k10_2024", r"in connection with redemptions 25,092,549 ([\d,]+)")),
       "2024": num(grab("k10_2024", r"in connection with redemptions ([\d,]+)")),
       "2025": num(grab("k10_2025", r"Cash withdrawn from Trust Account ([\d,]+)"))}
ends = {"2022": num(grab("q1_2023_10q", r"in the amount of \$[\d,]+ and \$([\d,]+) at redemption value")),
        "2023": num(grab("k10_2023", r"\$([\d,]+) remains in the Company")),
        "2024": num(grab("k10_2024", r"\$([\d,]+) remains in the Company")),
        "2025": num(grab("k10_2025", r"held in the trust account of \$([\d,]+)"))}
assert num(grab("k10_2022", r"Cash deposited into Trust Account . \(([\d,]+)\)")) == trust0
start = trust0
for y in ("2022", "2023", "2024", "2025"):
    end = start + inc[y] + dep[y] - out[y]
    assert end == ends[y], (y, end, ends[y])
    dep_txt = usd(dep[y], 0)
    need(f"| {y} | {usd(start, 0)} | {usd(inc[y], 0)} | {dep_txt} | {usd(out[y], 0)} | {usd(end, 0)} |")
    start = end
assert out["2023"] == both_2023 and out["2024"] == v["ext3"][1]
need(f"From 2022 to 2025 the trust earned {usd(sum(inc.values()), 0)} and the sponsors deposited {usd(sum(dep.values()), 0)}")
assert num(grab("k10_2024", r"investments held in Trust Account 2,598,427 ([\d,]+)")) == inc["2023"]
assert num(grab("k10_2024", r"Cash deposited into Trust Account \(872,089\) \(([\d,]+)\)")) == dep["2023"]
assert num(grab("k10_2024", r"in the amount of \$44,332,605 and \$([\d,]+)")) == ends["2023"]
assert "related to the recording of convertible promissory notes" in WINDOWS["k8_2024_08_19"][0]
need("The 2023 figures are the same in the 10-K for 2024, which followed TLGY's August 2024 correction of its 2023 accounts for convertible notes")
need(f"shows {usd(out['2025'], 0)} taken out that year, ${out['2025'] - v['ext4'][1]} more than the {usd(v['ext4'][1], 0)}")
assert out["2025"] - v["ext4"][1] == num(facts["trust_2025_12_31"]) - ends["2025"] == 111
for a, b in (("$0.04", "$200,000"), ("$0.033", "$110,000"), ("$0.02", "$60,000")):
    assert any(a in w and b in w for k in ("ext2_8k", "ext3_8k", "ext4_8k") for w in WINDOWS[k])
need("Until October 2023 it was the lesser of $0.04 a share and $200,000")
need("The second vote, in October 2023, cut it to the lesser of $0.033 and $110,000, and the third, in April 2024, to $0.02 "
     "and $60,000")
q1_25 = num(grab("q1_2026_10q", r"Cash deposited into Trust Account \(73,483\) \(([\d,]+)\)"))
q1_26 = num(grab("q1_2026_10q", r"Cash deposited into Trust Account \(([\d,]+)\)"))
sh_2024 = reported_left["ext3"]
assert q1_25 == 3 * 60000
need(f"In the first quarter of 2025 the sponsors deposited {usd(q1_25, 0)}, $60,000 a month, or about "
     f"{usd(Decimal(60000) / sh_2024, 3)} a share a month on {n(sh_2024)} public shares")
monthly = num(grab("k8_2026_03_16", r"depositing \$([\d,.]+)"))
assert monthly == Decimal("0.05") * reported_left["ext4"]
assert "$0.05 per outstanding share and (y) $25,000" in WINDOWS["ext4_8k"][-1]
assert abs(dep["2025"] - q1_25 - 9 * monthly) < 1 and abs(q1_26 - 3 * monthly) < 1
need(f"The fourth vote, in April 2025, changed the deposit to the lesser of $0.05 a share and $25,000, which on "
     f"{n(reported_left['ext4'])} public shares came to {usd(monthly)}, the deposit the sponsors made in March 2026")
need(f"The deposits for April to December 2025, {usd(dep['2025'] - q1_25, 0)}, and for the first quarter of 2026, {usd(q1_26, 0)}, "
     "come to nine and three months at that amount, to within a dollar")
sp_shares = num(grab("k8_2024_06_21", r"purchased ([\d,]+) Class B ordinary shares"))
assert grab("k8_2024_06_21", r"at a closing on (June 19, 2024)") == "June 19, 2024"
assert grab("k8_2024_06_21", r"aggregate purchase price of \$([\d.]+)") == "1.00"
assert "CPC Sponsor Opportunities I (Parallel), LP" in WINDOWS["k8_2024_06_21"][0] and "Former Sponsor" in WINDOWS["k8_2024_06_21"][0]
need(f"TLGY's sponsors had changed in June 2024, when two CPC Sponsor Opportunities funds bought {n(sp_shares)} founder shares and "
     "other securities from the former sponsor and others for $1.00 in all")
year_dep = 12 * monthly / reported_left["ext4"]
rise = per["ext5"] - per["ext4"]
assert year_dep / rise > Decimal("0.5")
need(f"Over a year that amount added {usd(year_dep)} a share, more than half of the {usd(rise)} by which the cash a share rose")
assert "(y) $10,000" in " ".join(WINDOWS["q1_2026_10q"])
need("The fifth vote cut the cap to $10,000")


# own day count, by the civil-from-days algorithm
def day(y, m, d):
    y -= m <= 2
    era = y // 400
    yoe = y - era * 400
    doy = (153 * (m + (-3 if m > 2 else 9)) + 2) // 5 + d - 1
    return era * 146097 + yoe * 365 + yoe // 4 - yoe // 100 + doy


assert day(2026, 6, 25) - day(2025, 4, 15) == 436 > 365   # "most of them more than a year before its merger"
D = {"ipo": day(2021, 12, 3), "ext1": day(2023, 2, 23), "ext2": day(2023, 10, 17), "ext3": day(2024, 4, 16),
     "ext4": day(2025, 4, 15), "ext5": day(2026, 4, 15), "merger": day(2026, 6, 25)}
val = {"ipo": trust_unit, **per}
steps = [("ipo", "ext1", "| IPO, December 3, 2021 | First extension vote, February 23, 2023 |"),
         ("ext1", "ext2", "| First extension vote | Second, October 17, 2023 |"),
         ("ext2", "ext3", "| Second | Third, April 16, 2024 |"),
         ("ext3", "ext4", "| Third | Fourth, April 15, 2025 |"),
         ("ext4", "ext5", "| Fourth | Fifth, April 15, 2026 |"),
         ("ext5", "merger", "| Fifth | Merger closing, June 25, 2026 |"),
         ("ipo", "merger", "| IPO | Merger closing |")]
for a, b, head in steps:
    days = D[b] - D[a]
    g = (val[b] / val[a]) ** (Decimal(365) / days) - 1
    need(f"{head} {days:,} | {usd(val[a])} to {usd(val[b])} | {pc(g, 2)} |")
whole = val["merger"] / val["ipo"] - 1
g_whole = (val["merger"] / val["ipo"]) ** (Decimal(365) / (D["merger"] - D["ipo"])) - 1
g_unit = (val["merger"] / price) ** (Decimal(365) / (D["merger"] - D["ipo"])) - 1
need(f"From the IPO to the merger the trust's cash a share rose {pc(whole)}, or {pc(g_whole, 2)} a year")
need(f"the cash at the first vote was {pc(per['ext1'] / price - 1)} more and the cash at the merger "
     f"{pc(per['merger'] / price - 1)} more, or {pc(g_unit, 2)} a year")
need(f"## Cash a share in the trust grew {pc(whole)} before the merger")
# the trust's value a share in filings rises between the votes
pts = [(D["ipo"], trust_unit), (day(2022, 12, 31), num(facts["trust_2022_12_31"]) / public), (D["ext1"], per["ext1"]),
       (day(2023, 3, 31), num(facts["trust_2023_03_31"]) / reported_left["ext1"]), (D["ext2"], per["ext2"]),
       (day(2023, 12, 31), ends["2023"] / reported_left["ext2"]), (D["ext3"], per["ext3"]),
       (day(2024, 6, 30), num(facts["trust_2024_06_30"]) / sh_2024), (day(2024, 12, 31), ends["2024"] / sh_2024),
       (D["ext4"], per["ext4"])] + [(day(*d), num(facts[f]) / reported_left["ext4"]) for d, f in
                                    (((2025, 6, 30), "trust_2025_06_30"), ((2025, 9, 30), "trust_2025_09_30"),
                                     ((2025, 12, 31), "trust_2025_12_31"), ((2026, 3, 31), "trust_2026_03_31"))] + \
      [(D["ext5"], per["ext5"]), (D["merger"], per["merger"])]
assert all(b[0] > a[0] and b[1] > a[1] for a, b in zip(pts, pts[1:]))
chart_pts = rows(HERE / "out" / "trust_a_share.csv")
assert [r2(Decimal(r["value_a_share"]), 2) for r in chart_pts] == [r2(p[1], 2) for p in pts]

# ---------------------------------------------------------------- the share table and the merger vote's requests
need(f"start from {n(table[0])} TLGY Class A shares, deduct {n(table[1])} that the sponsors forfeited and {n(table[2])} "
     f"redeemed, and leave {n(table[3])}")
need(f"counts {n(v['merger'][0])} public shares redeemed at the closing, {n(table[2] - v['merger'][0])} fewer than the share table")
need(f"The share table starts from the count TLGY reported after its fourth vote, when {n(reported_left['ext4'])} of its "
     f"{n(table[0])} Class A shares were public shares, and that was still the count at the record dates of both 2026 votes")
need(f"redeemed {n(v['ext5'][0])} public shares and the closing {n(v['merger'][0])}, together the share table's {n(table[2])}")
asked = num(grab("bc_vote_8k", r"holding ([\d,]+) Class A Ordinary Shares"))
assert asked == num(grab("q1_2026_10q", r"holders of ([\d,]+) Class A ordinary shares exercised"))
need(f"holders of {n(asked)} public shares had asked to redeem them")
need(f"The closing redeemed {n(v['merger'][0])}, {n(asked - v['merger'][0])} fewer")
need(f"what happened to the {n(asked - v['merger'][0])}")
need(f"The counts paid, {n(v['ext5'][0])} and {n(v['merger'][0])}, do not depend on it")

# ---------------------------------------------------------------- USDE and USDEW
sa = rows(INP / "usde_daily_stockanalysis_2026-10-12.csv")
yh = {r["date"]: Decimal(r["close"]) for r in rows(INP / "usde_daily_yahoo_2026-10-12.csv")}
listed = [r for r in sa if r["date"] >= "2026-06-26"]
pre = [r for r in sa if r["date"] < "2026-06-26"]
assert len(listed) == 74 and [r["date"] for r in listed] == sorted(yh)
assert all(r2(yh[r["date"]]) == Decimal(r["close"]) for r in listed)
cash_m = per["merger"]
closes = [(r["date"], Decimal(r["close"])) for r in listed]
at = [d for d, c in closes if c >= cash_m]
assert len(at) == 11 and at[0] == "2026-09-22" and at[-1] == "2026-10-07"
assert [d for d, c in closes if "2026-09-22" <= d <= "2026-10-07" and c < cash_m] == ["2026-09-23"]
lo = min(closes, key=lambda x: x[1])
hi = max(closes, key=lambda x: x[1])
first, last = closes[0], closes[-1]
assert lo[0] == "2026-07-24" and hi[0] == "2026-09-25" and first[0] == "2026-06-26" and last[0] == "2026-10-09"
need(f"USDE closed at {usd(first[1])} in its first session on June 26, 2026, {pc(1 - first[1] / cash_m)} below the cash a share paid at the merger")
need(f"It closed at or above that {usd(cash_m)} in {len(at)} of its {len(closes)} sessions to October 9, all between September 22 and October 7")
need(f"closed at {usd(last[1])} on October 9, {pc(1 - last[1] / cash_m)} below it")
sep22 = dict(closes)["2026-09-22"]


def sign(x):
    return ("+" if x >= 0 else "−") + pc(abs(x))


need(f"| June 26, first session | {usd(first[1])} | {sign(first[1] / cash_m - 1)} |")
need(f"| July 24, lowest close | {usd(lo[1])} | {sign(lo[1] / cash_m - 1)} |")
need(f"| September 22, first close at or above $13.35 | {usd(sep22)} | {sign(sep22 / cash_m - 1)} |")
need(f"| September 25, highest close | {usd(hi[1])} | {sign(hi[1] / cash_m - 1)} |")
need(f"| October 9 | {usd(last[1])} | {sign(last[1] / cash_m - 1)} |")
need(f"in {len(at)} of its {len(closes)} sessions to October 9, in every session from September 22 to October 7 except September 23")
need(f"The {n(kept)} shares were worth about ${r2(kept * last[1] / 1_000_000)} million at the October 9 close, against about "
     f"${r2(kept * cash_m / 1_000_000)} million in cash at the merger's price")
weeks = Decimal(D["merger"] - D["ext5"]) / 7
assert 10 <= weeks < 10.5
need(f"Holders who redeemed at the fifth vote, on April 15, about ten weeks before the merger closed, received {usd(per['ext5'])} a share")
sw = {r["date"]: Decimal(r["close"]) for r in rows(INP / "usdew_daily_stockanalysis_2026-10-12.csv")}
w_first = min(sw)
need(f"USDEW's first close in StockAnalysis's history was {usd(sw[w_first])} on June 29, 2026, and it closed at "
     f"{usd(sw['2026-10-09'])} on October 9, {usd(sw['2026-10-09'] / 2)} for the half warrant in each unit")
assert w_first == "2026-06-29"
warrants = num(grab("defm14a", r"([\d,]+) StablecoinX Warrants issued for the TLGY Warrants"))
assert warrants == public / 2 and "$11.50" in WINDOWS["defm14a"][-1]
w_after = num(grab("closing_8k", r"StablecoinX also had ([\d,]+) Public Warrants outstanding"))
need(f"StablecoinX counted {n(w_after)} public warrants outstanding after the merger, of the {n(warrants)} that came with the units")
need(f"StablecoinX's 8-K on the closing counts {n(w_after)} public warrants outstanding, {n(warrants - w_after)} fewer than the "
     f"{n(warrants)} that came with the units, although {pc(red / public)} of the public shares had been redeemed")
assert "There will be no redemption rights or liquidating distributions with respect to our warrants" in " ".join(WINDOWS["def14a_2026"])
need("the proxy for the fifth vote says the warrants had no redemption rights")
assert any("each issued and outstanding whole warrant representing the right to purchase one TLGY Class A Ordinary Share" in w
           and "became a warrant to acquire one share of StablecoinX Class A Common Stock" in w for w in WINDOWS["closing_8k"])
need("Each unit held half a warrant, and each whole warrant, now a StablecoinX warrant, gives the right to buy one share at $11.50")
need("The unit's third part was the contingent right to more warrants. The prospectus provided for")
assert any("net of taxes payable and up to $100,000 of interest to pay dissolution expenses" in w for w in WINDOWS["ext1_8k"])
need("Its 8-K on the first vote said the price a share was worked out from the amount in the trust, including the interest "
     "earned net of taxes and of up to $100,000 set aside to pay dissolution expenses")
votes_for = num(grab("ext4_8k", r"For Against Abstain ([\d,]+) 66,750 0"))
votes_against = num(grab("ext4_8k", r"For Against Abstain 2,030,299 ([\d,]+) 0"))
need(f"by {n(votes_for)} votes to {n(votes_against)}")
need(f"The prospectus provided for {n(right_total)} warrants, a quarter of a warrant for each unit")
need(f"Spread over the {n(kept)} shares kept, the {n(right_total)} warrants would have come to about {r2(right_total / kept, 1)} a share")
need("TLGY's Class A shareholders approved cancelling the right")

# ---------------------------------------------------------------- method, limits and the downloads
need(f"leave the counts TLGY reported next, {n(reported_left['ext1'])}, {n(reported_left['ext2'])}, {n(reported_left['ext3'])} "
     f"and {n(reported_left['ext4'])}, and that the two 2023 votes add up to the {n(v['ext1'][0] + v['ext2'][0])} shares in TLGY's 10-K for 2023")
assert reported_left["ext4"] - table[2] == kept
need(f"It checks that the {n(kept)} shares left by the vote counts match {n(reported_left['ext4'])} less the share table's {n(table[2])}")
need(f"match Yahoo Finance's in all {len(listed)} sessions from June 26 to October 9")
need("except the float review's 644,590, and every market price and trading volume from the sources named below")
need("A close is one price at the end of a session")
need(f"StockAnalysis lists {len(pre)} earlier rows under the same ticker, from April 9 to June 25, with closes between "
     f"{usd(min(Decimal(r['close']) for r in pre))} and {usd(max(Decimal(r['close']) for r in pre))} on "
     f"{n(min(int(r['volume']) for r in pre))} to {n(max(int(r['volume']) for r in pre))} shares a day")
assert pre[0]["date"] == "2026-04-09" and pre[-1]["date"] == "2026-06-25"
ps_2024 = ends["2024"] / sh_2024
assert r2(ps_2024) == Decimal("11.93") and Decimal(facts["trust_ps_2024_12_31"]) == Decimal("11.92")
need(f"as $11.92 a share, while its {usd(ends['2024'], 0)} over {n(sh_2024)} shares comes to {usd(ps_2024)}")
need(f"appears as {usd(num(facts['trust_2025_06_30']), 0)} in that quarter's 10-Q and as "
     f"{usd(num(grab('defm14a', r'June 30, 2025 which was .([\d,]+)')), 0)} of cash in the merger proxy")
need(f"cash a share at the merger = {n(v['merger'][1])} ÷ {n(v['merger'][0])}\n                           = {usd(cash_m, 4)}")
need(f"second vote's cash         = {n(both_2023)} − {n(v['ext1'][1])}\n                           = {usd(v['ext2'][1], 0)}")
need(f"public shares kept         = {n(public)} − {n(red)}\n                           = {n(kept)}")
need(f"trust at the end of 2023   = {n(ends['2022'])} + {n(inc['2023'])} + {n(dep['2023'])} − {n(out['2023'])}\n"
     f"                           = {usd(ends['2023'], 0)}")
need(f"trust growth a year        = ({r2(cash_m, 4)} ÷ {r2(trust_unit)}) ^ (365 ÷ {D['merger'] - D['ipo']:,}) − 1\n"
     f"                           = {pc(g_whole, 2)}")
need(f"USDE against the cash      = {r2(last[1])} ÷ {r2(cash_m, 4)} − 1\n                           = −{pc(1 - last[1] / cash_m)} on October 9")

# ---------------------------------------------------------------- the chart, metadata and the page furniture
alt = re.search(r"!\[(.+?)\]\(/research-assets/", ARTICLE).group(1)
paid = ", ".join(usd(per[k]) for k in order[:-1]) + " and " + usd(per["merger"])
need(f"filled dots for the cash a share paid for redemptions at the six votes, {paid}", alt)
need(f"rising at every report date and extension vote to {usd(cash_m)} paid at the merger closing on June 25, 2026", alt)
need(f"rising at every report date and extension vote to {usd(cash_m)} paid at the merger closing on June 25, 2026", SVG)
need("Filled dots mark the cash a share paid for redemptions at the six votes", SVG)
need("Redemption cash a share", SVG)
need("hollow dots for the trust's value a share at the IPO and at nine report dates", alt)
need("Hollow dots mark the trust's value a share at the IPO and at nine report dates", SVG)
assert len(pts) - 6 == 10 and sum(1 for r in chart_pts if r["kind"] == "report") == 9
assert [r["kind"] for r in chart_pts].count("redemption") == 6 and {r["kind"] for r in chart_pts} == {"ipo", "report", "redemption"}
votes_head = (HERE / "out" / "redemption_votes.csv").read_text().split("\n")[0].split(",")
assert "date_used" in votes_head and "paid_at" not in votes_head
assert "Merger closing, Jun 25, 2026" in SVG and "Merger vote" not in SVG
need(f"USDE's close at {len(closes)} sessions from June 26 to October 9, 2026", alt)
need(f"It closed at {usd(first[1])} on its first day, fell to {usd(lo[1])} on July 24, rose to {usd(hi[1])} on September 25 "
     f"and closed at {usd(last[1])} on October 9, at or above the dashed line in {len(at)} sessions from September 22 to October 7", alt)
need(f"Redemptions paid {usd(per['ext1'])} to {usd(cash_m)} a share. USDE closed below {usd(cash_m)} in "
     f"{len(closes) - len(at)} of {len(closes)} sessions", SVG)
need(f"{n(len(closes))} sessions from June 26, 2026 to October 9, 2026", SVG)
need(f"in {len(at)} sessions, all from September 22 to October 7", SVG)
need(f"Holders redeemed {n(red)} of TLGY's {n(public)} public shares for about ${r2(cash_all / 1_000_000, 1)} million at six votes", META["description"])
need(f"The other {n(kept)} became USDE shares at the merger.", META["description"])
need("with the cash a share paid for redemptions at the six votes marked", META["imageAlt"])
need(f"from $3.70 on the first day down to {usd(lo[1])} on July 24, up to {usd(hi[1])} on September 25 and {usd(last[1])} on October 9", META["imageAlt"])
assert len(META["description"]) <= 160 and len(META["title"]) <= 60
src = rows(INP / "sources.csv")
assert all("2026-10-12" in r["read_at_utc"] for r in src if r["key"] != "float_review")
need("Filings read October 12, 2026 UTC")
need("Prices through the October 9, 2026 close")
assert max(r["date"] for r in sa) == "2026-10-09"
if LAYOUT:
    assert LAYOUT["cutoff"] == "Filings read October 12, 2026 UTC · Prices through the October 9, 2026 close"
    assert LAYOUT["dashboardLabel"] == "Open the StablecoinX dashboard →"
    assert "paid for redemptions at each vote" in LAYOUT["chartLabel"]
    heads = [re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", unicodedata.normalize("NFKD", h).encode("ascii", "ignore").decode()).strip().lower())
             for h in re.findall(r"^## (.+)$", ARTICLE, re.M)]
    assert [anchor for _, anchor in LAYOUT["navigation"]] == heads, "the page navigation must follow the headings"
    for name in LAYOUT["archiveFiles"]:
        assert (HERE / name).is_file(), name

# ---------------------------------------------------------------- house style in everything written for the page
prose = re.sub(r"```.*?```", "", ARTICLE, flags=re.S)
prose = re.sub(r"\]\([^)]*\)", "]", prose)
prose = re.sub(r"https?://\S+", "", prose)
shipped = {"article": prose, "metadata": json.dumps(META, ensure_ascii=False),
           "chart text": html.unescape("\n".join(re.findall(r">([^<>]+)<", SVG))), "README": (HERE / "README.md").read_text(),
           "run log": (HERE / "out" / "run_log.txt").read_text(),
           "facts": "\n".join(r["value"] for r in rows(INP / "filing_facts.csv")), "sources": (INP / "sources.csv").read_text()}
for name, text in shipped.items():
    for ch in ("—", "–", ";"):
        assert ch not in text, (name, ch)
for line in prose.split("\n"):
    if line.startswith("|"):
        continue
    assert ":" not in line, line
assert ":" not in shipped["run log"], "no colons in the run log"
for word in ("This article", "this article", " holders of record", "investors"):
    assert word not in ARTICLE, word

if missing:
    print(f"{len(missing)} phrases missing:")
    for m in missing:
        print("  ", m)
    sys.exit(1)
print(f"All {found} phrases found, every assertion holds")
