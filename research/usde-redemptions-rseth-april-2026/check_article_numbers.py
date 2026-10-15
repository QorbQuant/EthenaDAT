#!/usr/bin/env python3
"""Recomputes every computed figure in article_draft.md, metadata.json, layout.json's key findings and the chart's
text from the inputs, with code written apart from redemption_waves.py, using decimal arithmetic instead of
fractions, and checks that each phrase appears where it should. Exits with an error if a phrase is missing or a
page rule fails. Python 3.8 or later, no network."""
import csv
import json
import re
import sys
from datetime import date, timedelta
from decimal import Decimal as D, getcontext, ROUND_HALF_UP
from pathlib import Path

getcontext().prec = 60
HERE = Path(__file__).parent
CH = HERE / "inputs" / "chain"
WEB = HERE / "inputs" / "web"
SLUG = "usde-redemptions-rseth-april-2026"
ARTICLE = (HERE / "article_draft.md").read_text(encoding="utf-8")
META = json.loads((HERE / "metadata.json").read_text(encoding="utf-8"))
LAYOUT = json.loads((HERE / "layout.json").read_text(encoding="utf-8"))
SVG = (HERE / "out" / "chart_usde_redemptions_april_2026.svg").read_text(encoding="utf-8")
WEBTXT = " ".join((WEB / "redemption_sources_2026-10-13.txt").read_text(encoding="utf-8").split())
FAILS, FOUND = [], []
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
E18 = D(10) ** 18
MIL = D(10) ** 6
BIL = D(10) ** 9


def need(phrase, where="article"):
    text = {"article": ARTICLE, "meta": json.dumps(META, ensure_ascii=False), "findings": " ".join(LAYOUT["keyFindings"]), "svg": SVG,
            "web": WEBTXT}[where]
    if phrase in text:
        FOUND.append((where, phrase))
    else:
        FAILS.append("missing in %s: %s" % (where, phrase))


def rule(ok, msg):
    if not ok:
        FAILS.append(msg)


def rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def r2(x, places=2):
    q = D(x).copy_abs().quantize(D(1).scaleb(-places), rounding=ROUND_HALF_UP)
    s = "{:,.{p}f}".format(q, p=places)
    return ("-" if D(x) < 0 and q != 0 else "") + s


def pc(x, places=2):
    return r2(D(x) * 100, places)


def long_day(s, year=True):
    d = date.fromisoformat(s)
    return "%s %d, %d" % (MONTHS[d.month - 1], d.day, d.year) if year else "%s %d" % (MONTHS[d.month - 1], d.day)


def days(a, b):
    d, out = date.fromisoformat(a), []
    while d <= date.fromisoformat(b):
        out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def prev(s):
    return (date.fromisoformat(s) - timedelta(days=1)).isoformat()


# ---- inputs, read on their own ----------------------------------------------------------------------------------
day = rows(CH / "day_reads.csv")
SUP = {r["day"]: D(int(r["usde_total_supply_raw"])) / E18 for r in day}
ALL = [r["day"] for r in day]
BLK = {r["day"]: int(r["block"]) for r in day}
st = {r["day"]: r for r in rows(CH / "day_state.csv")}
fl = {r["day"]: r for r in rows(CH / "day_flows.csv")}
run = json.loads((CH / "run.json").read_text(encoding="utf-8"))
HELD = {d: D(int(r["usde_held_by_susde_raw"])) / E18 for d, r in st.items()}
SILO = {d: D(int(r["usde_in_cooldown_silo_raw"])) / E18 for d, r in st.items()}
ASSETS = {d: D(int(r["susde_total_assets_raw"])) / E18 for d, r in st.items()}
SHARES = {d: D(int(r["susde_total_supply_raw"])) / E18 for d, r in st.items()}
OUT = {d: SUP[d] - HELD[d] - SILO[d] for d in st}
COOL = {d: int(r["cooldown_seconds"]) for d, r in st.items()}
BURN = {d: D(int(r["burned_raw"])) / E18 for d, r in fl.items()}
MINT = {d: D(int(r["minted_raw"])) / E18 for d, r in fl.items()}
NB = {d: int(r["burns"]) for d, r in fl.items()}
NM = {d: int(r["mints"]) for d, r in fl.items()}
BIG = {d: D(int(r["largest_burn_raw"])) / E18 for d, r in fl.items()}
for d in fl:
    rule(MINT[d] - BURN[d] == SUP[d] - SUP[prev(d)], "mints less burns equal the change in supply on " + d)
rule(all(st[d]["same_on_second_source"] == "1" for d in st), "second source")
rule(ALL == days("2024-01-01", "2026-10-12"), "the supply series runs from January 1, 2024 to October 12, 2026 without a gap")

# ---- page rules -------------------------------------------------------------------------------------------------
lines = ARTICLE.split("\n")
rule(sum(1 for l in lines if l.startswith("# ")) == 1 and lines[0] == "# " + META["headline"], "one H1, the metadata headline")
rule(len(META["title"]) <= 60 and 120 <= len(META["description"]) <= 160, "title and description lengths")
pub = date.fromisoformat(META["datePublished"])
rule("[Qorban Ferrell · @Degenerate\\_DeFi](https://ethenadash.com/about/) · Published %d %s %d" % (pub.day, MONTHS[pub.month - 1], pub.year) in ARTICLE,
     "byline with author link and the metadata's date")
rule(LAYOUT["cutoff"] in ARTICLE, "the cutoff in the byline")
rule(ARTICLE.rstrip().endswith("Analysis of public blockchain data. Not investment advice."), "closing line")
svg_text = " ".join(re.findall(r">([^<>]+)<", SVG))
readme = (HERE / "README.md").read_text(encoding="utf-8")
for bad_ in ["—", "–", ";", "This article", "on-chain", "FAQ"]:
    rule(bad_ not in ARTICLE, "forbidden text in article: %r" % bad_)
    rule(bad_ not in " ".join(LAYOUT["keyFindings"]) + META["description"] + META["imageAlt"] + LAYOUT["cutoff"] + LAYOUT["chartLabel"],
         "forbidden text in metadata or layout: %r" % bad_)
    rule(bad_ not in svg_text, "forbidden text in the chart's text: %r" % bad_)
for bad_ in ["—", "–"]:
    rule(bad_ not in readme, "dash in README")
in_code = False
for l in lines:
    if l.startswith("```"):
        in_code = not in_code
        continue
    if in_code or l.startswith("|") or l.startswith("!["):
        continue
    stripped = re.sub(r"\(https?://[^)]*\)|\(/research-assets/[^)]*\)|`[^`]*`|\b\d{1,2}:\d{2}(:\d{2})?\b", "", l)
    rule(":" not in stripped, "colon outside a clock time, link, code or table: " + l[:80])
for f in LAYOUT["keyFindings"] + [META["description"], META["imageAlt"], svg_text, LAYOUT["chartLabel"]]:
    rule(":" not in re.sub(r"\b\d{1,2}:\d{2}(:\d{2})?\b|https?://\S+", "", f), "colon in a finding, description, alt text or the chart's text")
heads = [l[3:] for l in lines if l.startswith("## ")]


def slug(h):
    return re.sub(r"[^a-z0-9]+", "-", h.lower().replace("'", "").replace("$", "").replace(".", "")).strip("-")


rule([slug(h) for h in heads] == [n[1] for n in LAYOUT["navigation"]], "navigation anchors match the headings")
for link in ["https://ethenadash.com/stablecoinx/", "https://ethenadash.com/methodology/", "https://ethenadash.com/research/ethenapay-vs-susde-2026-10-08/",
             "https://ethenadash.com/research/stablecoinx-mnav/"]:
    rule(link in ARTICLE, "link missing " + link)
rule(LAYOUT["dashboard"] == "/stablecoinx/", "dashboard link")
rule(len(LAYOUT["keyFindings"]) == 3, "three key findings")
rule(META["path"] == "/research/%s/" % SLUG and META["image"] == "/research-assets/%s/chart_preview.png" % SLUG, "paths use the slug")
rule("](/research-assets/%s/%s)" % (SLUG, LAYOUT["chartFile"]) in ARTICLE, "the chart in the article")
rule("![" + META["imageAlt"] + "](" in ARTICLE, "the article's alt text is the metadata's")
for f in LAYOUT["archiveFiles"]:
    rule((HERE / f).exists(), "archive file missing " + f)
for f in LAYOUT["assets"]:
    rule((HERE / "out" / f).exists(), "asset missing " + f)
for m in re.findall(r"\(/research-assets/" + SLUG + r"/([^)]+)\)", ARTICLE):
    rule(m in LAYOUT["assets"] or m == "calculation-files.zip", "linked download not in assets " + m)
# No account addresses and no transaction hashes in the published files. The only addresses are USDe's, sUSDe's,
# the cooldown silo's, the two mint and redeem contracts' and the OFT adapter's, and the only 64-digit hex string
# with 0x is the Transfer event's topic in the browser script.
allowed = {"0x4c9edd5852cd905f086c759e8383e09bff1e68b3", "0x9d39a5de30e57443bff2a8307a4256c8797a3497", "0x7fc7c91d556b400afa565013e3f32055a0713425",
           "0x2cc440b721d2cafd6d64908d6d8c4acc57f8afc3", "0xe3490297a08d6fc8da46edb7b6142e4f461b62d3",
           # Ethena's USDe OFT adapter, named in the carried chain review
           "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34"}
for f in LAYOUT["archiveFiles"]:
    p = HERE / f
    if p.suffix in (".png", ".zip") or not p.exists():
        continue
    text = p.read_text(encoding="utf-8")
    for a in sorted(set(x.lower() for x in re.findall(r"0x[0-9a-fA-F]{40}(?![0-9a-fA-F])", text))):
        if a not in allowed:
            FAILS.append("address not on the allowed list in %s: %s" % (f, a))
            break
    if f != "check_article_numbers.py":  # this file names the fields it looks for
        rule(not re.search(r"\b(?:transaction_hash|transactionHash|txHash)\b", text), "transaction hash field in " + f)
    found = set(re.findall(r"0x[0-9a-fA-F]{64}(?![0-9a-fA-F])", text))
    rule(found <= {"0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"} and (not found or f in ("browser/redemption_waves_read.js", "check_article_numbers.py")),
         "unexpected 64-digit hex in " + f)

# ---- the opening --------------------------------------------------------------------------------------------------
b = lambda x: r2(x / BIL)  # noqa: E731
W = days("2026-04-19", "2026-04-27")
b9, m9 = sum(BURN[d] for d in W), sum(MINT[d] for d in W)
s0, s1 = SUP["2026-04-18"], SUP["2026-04-27"]
need("About %s billion USDe was redeemed in the nine UTC days from April 19 to April 27, 2026, counting each burn of USDe as a redemption." % b(b9))
need("Over the nine days %s USDe was burned and %s USDe was minted." % (r2(b9), r2(m9)))
need("USDe's total supply on Ethereum fell by %s, or %s%%, from %s at the end of April 18 to %s at the end of April 27. April 18 was the day of the exploit of rsETH, a token issued by Kelp." % (
    r2(s0 - s1), pc((s0 - s1) / s0), r2(s0), r2(s1)))
peak = max(ALL, key=lambda d: SUP[d])
rule(min((d for d in ALL if d >= peak), key=lambda d: SUP[d]) == "2026-04-27" and peak == "2025-10-03" and ALL[-1] == "2026-10-12", "the low since the 2025 peak")
need("The supply at the end of April 27 was the lowest day-end supply, the total supply at the end of a UTC day, from the 2025 peak of %s on October 3, 2025 through October 12, 2026." % r2(SUP[peak]))
need("Ethena's documentation says that USDe redeemed through its mint and redeem contract is burned.")
need("the redeemed USDe is burned from the redeemer's balance", "web")
need("On 2026-04-18 at 17:35 UTC, at Ethereum block 24,908,285", "web")
need("released 116,500 rsETH from the rsETH adapter on Ethereum", "web")
need("LlamaRisk posted it at 2026-04-20 20:12:55 UTC, and it says Aave service providers wrote it together", "web")
need("The exploit came at 17:35 UTC on April 18, at Ethereum block 24,908,285, according to an incident report written by the service providers of Aave, a lending protocol, and posted on Aave's governance forum on April 20.")
need("A forged message on LayerZero, a cross-chain messaging protocol, released 116,500 rsETH from the rsETH adapter on Ethereum.")
need("A forged message from Unichain, with no matching burn there, released 116,500 rsETH", "web")
rule(BLK["2026-04-17"] < 24908285 <= BLK["2026-04-18"], "the exploit's block falls on April 18")
before = days("2026-04-04", "2026-04-17")
top_before = max(before, key=lambda d: BURN[d])
rule(top_before == "2026-04-07" and BURN["2026-04-18"] < BURN[top_before], "April 7 was the largest day of the two weeks before, above April 18")
need("Burns of USDe came to %s on April 18, less than the %s of April 7, the largest day of the two weeks before." % (r2(BURN["2026-04-18"]), r2(BURN["2026-04-07"])))
rule(max(W, key=lambda d: BURN[d]) == "2026-04-21", "April 21 is the largest day of burns in the wave")
rule(max(days("2026-04-01", "2026-05-15"), key=lambda d: BURN[d]) == "2026-04-21", "April 21 is the largest day of burns in the April window")
need("They came to %s on April 19 and peaked at %s on April 21." % (r2(BURN["2026-04-19"]), r2(BURN["2026-04-21"])))
# the cooldown and the split
st_days = sorted(st)
rule(all(COOL[d] == 604800 for d in st_days if d < "2026-03-16") and all(COOL[d] == 86400 for d in st_days if d >= "2026-03-16"), "the cooldown change")
need("When sUSDe is unstaked, its USDe is held in a separate contract, the cooldown silo, until a cooldown ends.")
need("Ethena cut the cooldown from seven days to one on March 16, 2026.")
need("The static 7 day sUSDe unstaking cooldown was replaced with a dynamic model", "web")
k0 = "2026-04-18"
stk0, stk1 = HELD[k0] + SILO[k0], HELD["2026-04-27"] + SILO["2026-04-27"]
need("sUSDe and its silo held %s%% of USDe's supply at the end of April 18 and made up %s%% of the nine days' fall, a little above their share." % (
    pc(stk0 / s0), pc((stk0 - stk1) / (s0 - s1))))
rule(D(0) < (stk0 - stk1) / (s0 - s1) - stk0 / s0 < D("0.05"), "a little above their share")
o0, o1 = SUP["2025-10-09"], SUP["2025-10-18"]
ostk0, ostk1 = HELD["2025-10-09"] + SILO["2025-10-09"], HELD["2025-10-18"] + SILO["2025-10-18"]
n8 = "2025-11-08"
o30 = ((HELD["2025-10-09"] + SILO["2025-10-09"]) - (HELD[n8] + SILO[n8])) / (o0 - SUP[n8])
need("In the nine days from October 10, 2025, when the cooldown was seven days, they held %s%% of supply at the start and made up %s%% of a %s%% fall, and %s%% of the 30-day fall to November 8, 2025." % (
    pc(ostk0 / o0), pc((ostk0 - ostk1) / (o0 - o1)), pc((o0 - o1) / o0), pc(o30)))
rule(COOL["2025-10-18"] == 604800 and COOL["2026-04-27"] == 86400, "the cooldowns of the two waves")


def falls(n):
    return sorted((((SUP[ALL[i]] - SUP[ALL[i - n]]) / SUP[ALL[i - n]]), ALL[i - n], ALL[i]) for i in range(n, len(ALL)))


def falls_usde(n):
    return sorted(((SUP[ALL[i]] - SUP[ALL[i - n]]), ALL[i - n], ALL[i]) for i in range(n, len(ALL)))


one = falls(1)
rule(sorted(b_ for x, a, b_ in one[:5] if b_.startswith("2026-04")) == days("2026-04-20", "2026-04-23") and one[0][2] == "2025-10-11", "four of the five")
rule(all(falls(n)[0][1:] in [("2026-04-20", "2026-04-23"), ("2026-04-18", "2026-04-25"), ("2026-04-18", "2026-04-27")] for n in (3, 7, 9)), "three, seven and nine")
need("As a share of supply, the April fall was the largest in USDe's day-end supply over three, seven or nine days since January 1, 2024, when the daily series begins, and four of the five largest one-day falls came on April 20 to 23, 2026.")
need("The largest one-day fall, %s%%, came on October 11, 2025." % pc(-one[0][0]))
# in USDe, October 2025 had the largest falls over one, three, seven and nine days
for n in (1, 3, 7, 9):
    x, a, z = falls_usde(n)[0]
    rule(a.startswith("2025-10") and z.startswith("2025-10"), "the largest %d-day fall in USDe is in October 2025" % n)
    apr = min((SUP[ALL[ALL.index(q)]] - SUP[ALL[ALL.index(q) - n]]) for q in W)
    rule(x < apr, "October's %d-day fall in USDe is larger than April's" % n)
O9 = days("2025-10-10", "2025-10-18")
need("Measured in USDe, October 2025 was larger, and %s USDe was burned in the nine days from October 10." % r2(sum(BURN[d] for d in O9)))

# ---- the nine days -------------------------------------------------------------------------------------------
for d in days("2026-04-18", "2026-04-30"):
    ch = SUP[d] - SUP[prev(d)]
    need("| %s | %s | %s %s | %s | %s | %d |" % (long_day(d, False), r2(SUP[d] / MIL), "down" if ch < 0 else "up", r2(abs(ch) / MIL), r2(BURN[d] / MIL),
                                               r2(MINT[d] / MIL), NB[d]))
F5 = days("2026-04-19", "2026-04-23")
b5 = sum(BURN[d] for d in F5)
need("In the five days from April 19 to April 23, %s USDe was burned, %s%% of the nine days' burns, and supply fell %s%%." % (
    r2(b5), pc(b5 / b9), pc((s0 - SUP["2026-04-23"]) / s0)))
half = next(d for d in W if s0 - SUP[d] >= (s0 - s1) / 2)
rule(half == "2026-04-21", "half by April 21")
need("Half of the nine days' fall had come by the end of April 21.")
need("The nine days had %s burns and %d mints." % ("{:,}".format(sum(NB[d] for d in W)), sum(NM[d] for d in W)))
rule(all(MINT[d] > BURN[d] for d in days("2026-04-28", "2026-04-30")), "mints above burns on April 28 to 30")
need("On each of April 28 to 30 mints exceeded burns, and supply rose %s over the three days." % r2(SUP["2026-04-30"] - SUP["2026-04-27"]))
mx = max(BIG.values())
rule(mx == 10 ** 7, "the largest single burn is 10 million")
need("No single burn in the windows read was larger than %s USDe, and %d of the %d days read had a burn of exactly that size." % (
    "{:,}".format(int(mx)), sum(1 for v in BIG.values() if v == mx), len(fl)))
need("Ethena's documentation says its contract caps the USDe that can be redeemed in each block without giving the cap, and the read did not establish whether the cap explains the burns of that size.")
need("The contract caps the USDe that can be minted or redeemed in each block. The page does not give the cap.", "web")
need("with no peg break and no draw on the Reserve Fund", "web")
need("rates on Aave likely spiked during the unwinding of leveraged positions in mid-April", "web")
need("The post says Kairos Research prepared it.", "web")
need("gave the topic's creation as 2026-05-28T14:12:11Z and one post", "web")
need("prepared by Kairos Research and posted on the Ethena Foundation's governance forum on May 28, 2026, said the mints and redemptions went through without a break in USDe's peg or a draw on its Reserve Fund, the pool")
need("or a draw on its Reserve Fund, the pool of assets Ethena holds as an additional margin of safety for USDe.")
need("The Reserve Fund is a pool of assets the protocol holds as an additional margin of safety for USDe.", "web")
need("their USDe is placed in the USDeSilo contract, 0x7fc7c91d556b400afa565013e3f32055a0713425", "web")
need("Reward payments into the contract come every 8 hours and vest linearly over 8 hours", "web")
need("The Staking USDe page calls USDe a synthetic dollar that does not earn rewards unless it is staked.", "web")
need("USDe is Ethena's synthetic dollar, and Ethena's documentation says")
CARRIED = " ".join((WEB / "usde_chain_review_carried_2026-10-12.txt").read_text(encoding="utf-8").split())
rule("USDe's total supply on Ethereum therefore counts the USDe locked to back USDe on other chains" in CARRIED, "carried file")
need("The USDe outside sUSDe is the rest, including the USDe locked on Ethereum to back USDe on other chains.")

# ---- which holdings fell ----------------------------------------------------------------------------------------
need("At the end of April 18, the day of the rsETH exploit, supply was %s billion, of which sUSDe held %s billion. At the end of April 27 it was %s billion, "
     "of which sUSDe held %s billion. The silo peaked at %s billion on April 20. On May 31 supply was %s billion, of which sUSDe held %s billion." % (
         b(s0), b(HELD[k0]), b(s1), b(HELD["2026-04-27"]), b(SILO["2026-04-20"]), b(SUP["2026-05-31"]), b(HELD["2026-05-31"])), "meta")
rule(max(days("2026-04-01", "2026-05-31"), key=lambda d: SILO[d]) == "2026-04-20", "the silo's April and May peak")
need("sUSDe's cooldown was cut from seven days to one on March 16, 2026.", "meta")


def wave(a, z):
    d0 = prev(a)
    ws = days(a, z)
    k0_, k1_ = HELD[d0] + SILO[d0], HELD[z] + SILO[z]
    return {"s0": SUP[d0], "s1": SUP[z], "fall": SUP[d0] - SUP[z], "b": sum(BURN[d] for d in ws), "m": sum(MINT[d] for d in ws),
            "h": HELD[d0] - HELD[z], "hp": (HELD[d0] - HELD[z]) / HELD[d0], "si": SILO[z] - SILO[d0], "o": OUT[d0] - OUT[z],
            "op": (OUT[d0] - OUT[z]) / OUT[d0], "share": (k0_ - k1_) / (SUP[d0] - SUP[z]), "start": k0_ / SUP[d0]}


A, O = wave("2026-04-19", "2026-04-27"), wave("2025-10-10", "2025-10-18")
need("| Supply at the start | %s | %s |" % (r2(A["s0"] / MIL), r2(O["s0"] / MIL)))
need("| Supply at the end | %s | %s |" % (r2(A["s1"] / MIL), r2(O["s1"] / MIL)))
need("| Fall in supply | %s, or %s%% | %s, or %s%% |" % (r2(A["fall"] / MIL), pc(A["fall"] / A["s0"]), r2(O["fall"] / MIL), pc(O["fall"] / O["s0"])))
need("| Burned | %s | %s |" % (r2(A["b"] / MIL), r2(O["b"] / MIL)))
need("| Minted | %s | %s |" % (r2(A["m"] / MIL), r2(O["m"] / MIL)))
need("| Fall in USDe held by sUSDe | %s, or %s%% | %s, or %s%% |" % (r2(A["h"] / MIL), pc(A["hp"]), r2(O["h"] / MIL), pc(O["hp"])))
need("| Rise in the cooldown silo | %s | %s |" % (r2(A["si"] / MIL), r2(O["si"] / MIL)))
need("| Fall in USDe outside sUSDe | %s, or %s%% | %s, or %s%% |" % (r2(A["o"] / MIL), pc(A["op"]), r2(O["o"] / MIL), pc(O["op"])))
need("| sUSDe and its silo, share of supply at the start | %s%% | %s%% |" % (pc(A["start"]), pc(O["start"])))
need("| sUSDe and its silo, share of the fall | %s%% | %s%% |" % (pc(A["share"]), pc(O["share"])))
need("| sUSDe's cooldown | 1 day | 7 days |")
rule(A["si"] > 0 and O["si"] > 0 and A["h"] > 0 and O["h"] > 0 and A["o"] > 0 and O["o"] > 0, "the signs of the table's rows")
need("In April the USDe held by sUSDe fell %s%%, from %s to %s, and the USDe outside sUSDe fell %s%%." % (pc(A["hp"]), r2(HELD[k0]), r2(HELD["2026-04-27"]), pc(A["op"])))
rule(A["hp"] > A["op"], "sUSDe fell by a larger share than the rest")
need("disproportionately on sUSDe positions", "web")
need("The USDe held by sUSDe fell by a larger share than the USDe outside it, which is consistent with that, although the split does not show whose USDe was burned.")
d19 = SUP["2026-04-19"] - SUP[k0]
need("On April 19 the USDe outside sUSDe accounted for %s%% of the day's fall, while the silo rose by %s. Over the next four days the USDe held by sUSDe fell by %s." % (
    pc((OUT["2026-04-19"] - OUT[k0]) / d19), r2(SILO["2026-04-19"] - SILO[k0]), r2(HELD["2026-04-19"] - HELD["2026-04-23"])))
rule(SILO["2025-10-18"] > 2 * SILO["2025-10-09"], "the October silo more than doubled")
need("In October 2025 the USDe held by sUSDe fell %s%% over the nine days, the silo more than doubled, and the USDe outside sUSDe fell %s%%." % (pc(O["hp"]), pc(O["op"])))
oc = days("2025-10-18", "2025-10-23")
rule(all(SILO[oc[i]] < SILO[oc[i + 1]] for i in range(len(oc) - 1)) and max(days("2025-10-01", "2025-11-30"), key=lambda d: SILO[d]) == "2025-10-23",
     "the silo rose on each day from October 19 to its peak on October 23")
need("The silo rose on each day from October 19 to October 23, to %s." % r2(SILO["2025-10-23"]))

# ---- the cooldown --------------------------------------------------------------------------------------------------
need("The proposal, posted on March 12, 2026, would replace the static 7 day sUSDe cooldown used since launch with cooldowns of 1, 3, 5 or 7 days", "web")
need("perpetual futures were 11% of the backing and liquid stablecoins 89%", "web")
need("gave the topic's creation as 2026-03-12T15:33:16Z", "web")
need("the third posted at 2026-03-16T09:44:16Z", "web")
need("Post 3 is LlamaRisk's analysis, as a member of the Risk Committee, in support of the proposal.", "web")
need("Blockworks derived the 99th percentile benchmarks from cumulative net USDe redemptions over rolling one, three and seven day windows", "web")
need("giving 4.1% of supply for one day, 9.2% for three days and 12.0% for seven days, so that only 1% of past periods saw more", "web")
need("sUSDe's cooldown was 604,800 seconds, or seven days, at every day end read up to March 15, 2026, and 86,400 seconds, or one day, at every day end from March 16 to May 31.")
need("LlamaRisk, a member of Ethena's Risk Committee, posted its analysis in support of the proposal at 09:44 UTC on March 16.")
need("They were 4.1% of supply over one day, 9.2% over three days and 12.0% over seven days.")
bench = {1: D("0.041"), 3: D("0.092"), 7: D("0.120")}
mx_fall = {}
for n in (1, 3, 7):
    c = [((SUP[ALL[ALL.index(z) - n]] - SUP[z]) / SUP[ALL[ALL.index(z) - n]], ALL[ALL.index(z) - n], z) for z in W]
    mx_fall[n] = max(c)
need("In April the falls in day-end supply reached %s%% over one day, %s%% over three days and %s%% over seven, %s, %s and %s times the benchmarks." % (
    pc(mx_fall[1][0]), pc(mx_fall[3][0]), pc(mx_fall[7][0]), r2(mx_fall[1][0] / bench[1]), r2(mx_fall[3][0] / bench[3]), r2(mx_fall[7][0] / bench[7])))
over = [z for z in W if (SUP[prev(z)] - SUP[z]) / SUP[prev(z)] > bench[1]]
rule(over == F5, "above 4.1% on April 19 to 23 only")
need("The one-day fall was above 4.1% on each of the five days from April 19 to April 23.")
need("the dynamic cooldown's Tier 1 daily redemption capacity was $1.88B at activation", "web")
need("together with other redemption channels it absorbed the redemptions after the rsETH incident", "web")
need("Tier 1 is USDC, USDT, PYUSD and the balances of the mint and redeem contracts, which settle in a day", "web")
cap = D(1880) * MIL
need("and said Tier 1 and other redemption channels absorbed the redemptions. The largest day of burns, April 21, came to %s%% of that capacity." % pc(BURN["2026-04-21"] / cap))

# ---- the largest falls --------------------------------------------------------------------------------------------
need("The table ranks the seven largest one-day falls in USDe's day-end supply from January 1, 2024 to October 12, 2026, by percentage")
for x, a, z in one[:7]:
    need("| %s | %s | %s%% |" % (long_day(z), r2((SUP[a] - SUP[z]) / MIL), pc(-x)))
rule(one[7][2] == "2025-03-01", "the eighth largest one-day fall is outside the table")
f3, f7, f9, f30 = falls(3)[0], falls(7)[0], falls(9)[0], falls(30)[0]
need("Over three days the largest fall in the series was %s%%, from the end of April 20 to the end of April 23, 2026." % pc(-f3[0]))
need("Over seven days it was %s%%, from the end of April 18 to the end of April 25, and over nine days %s%%, to the end of April 27." % (pc(-f7[0]), pc(-f9[0])))
rule(f3[1:] == ("2026-04-20", "2026-04-23") and f7[1:] == ("2026-04-18", "2026-04-25") and f9[1:] == ("2026-04-18", "2026-04-27"), "the multi-day dates")
rule(f30[1:] == ("2025-10-09", "2025-11-08"), "the 30 day dates")
need("Over 30 days the largest was %s%%, from the end of October 9 to the end of November 8, 2025, when supply fell from %s to %s." % (
    pc(-f30[0]), r2(SUP["2025-10-09"]), r2(SUP["2025-11-08"])))
need("Measured in USDe rather than as a share of supply, the October 2025 falls were larger.")
rule(not any(d.startswith("2026-07") for d in list(st) + list(fl)), "July 2026 is outside the windows read")

# ---- attestations -----------------------------------------------------------------------------------------------
att = [("2026-02-27", "6.07"), ("2026-03-06", "5.97"), ("2026-03-13", "5.92"), ("2026-03-20", "5.92"), ("2026-03-27", "5.92"), ("2026-04-02", "5.89"),
       ("2026-04-09", "5.84"), ("2026-04-16", "5.83"), ("2026-04-19", "5.64"), ("2026-04-23", "3.96"), ("2026-04-30", "3.90")]
MON3 = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
matches = 0
for d, v in att:
    dd = date.fromisoformat(d)
    need("%d %s 2026%s | $%sB |" % (dd.day, MON3[dd.month - 1], " (post-rsETH)" if d == "2026-04-19" else " (end-of-month)" if d == "2026-04-30" else "", v), "web")
    same, bef = b(SUP[d]), b(SUP[prev(d)])
    need("| %s | %s | %s | %s |" % (long_day(d, False), v, same, bef))
    matches += v in (same, bef)
rule(matches == 10, "ten of eleven")
need("Ten of the eleven attested supplies equal one of the two day ends to two decimals.")
rule(SUP["2026-04-19"] < D("5.64") * BIL < SUP["2026-04-18"], "April 19 between")
need("The attestation of April 19, 5.64 billion, lies between the day ends of April 18 and April 19, as a reading taken during April 19 would.")
AW = days("2026-04-17", "2026-04-30")
bw, mw = sum(BURN[d] for d in AW), sum(MINT[d] for d in AW)
need("From the end of April 16 to the end of April 30, %s USDe was burned and %s minted, a net fall of %s that matches the update's fall of about $1.93 billion." % (
    r2(bw), r2(mw), r2(bw - mw)))
rule(r2((bw - mw) / BIL) == "1.93", "1.93 billion")
need("then fell by about $1.93B between the attestations of April 16 and April 30", "web")
need("supply effectively stabilized in the last week, falling $62M between April 23 and April 30", "web")
need("The update said supply effectively stabilized in the last week of April, falling $62 million from April 23 to April 30.")
need("Day-end supply fell %s from April 23 to April 27 and then rose %s to April 30, a net fall of %s million." % (
    r2(SUP["2026-04-23"] - SUP["2026-04-27"]), r2(SUP["2026-04-30"] - SUP["2026-04-27"]), r2((SUP["2026-04-23"] - SUP["2026-04-30"]) / MIL)))
need("the update put sUSDe supply at $1.71B at the end of April, which it said implied a staking ratio of about 44.0% of USDe supply, down from 57.96% at the end of February", "web")
e30, f26, f28 = "2026-04-30", "2026-02-26", "2026-02-28"
need("At the end of April 30 sUSDe's token supply, the number of sUSDe in issue, was %s, and its total assets, the USDe held for those tokens, were %s, or %s USDe a token." % (
    r2(SHARES[e30]), r2(ASSETS[e30]), r2(ASSETS[e30] / SHARES[e30], 4)))
rule(r2(SHARES[e30] / BIL) == "1.71" and r2(ASSETS[e30] / BIL) != "1.71", "1.71 billion is the token supply")
need("The $1.71 billion matches the token supply, and 44.0%% matches the token supply over USDe's supply, %s%%." % pc(SHARES[e30] / SUP[e30]))
rule(r2(SHARES[e30] / SUP[e30] * 100, 1) == "44.0", "44.0% to one decimal")
need("By total assets sUSDe held %s%% of USDe's supply." % pc(ASSETS[e30] / SUP[e30]))
need("The February figure equals total assets over USDe's supply at the end of February 26, %s%%, and is %s point below the %s%% of February 28. By token supply the ratio was %s%% and %s%% on those days." % (
    pc(ASSETS[f26] / SUP[f26]), r2(ASSETS[f28] / SUP[f28] * 100 - D("57.96")), pc(ASSETS[f28] / SUP[f28]), pc(SHARES[f26] / SUP[f26]), pc(SHARES[f28] / SUP[f28])))
rule(pc(ASSETS[f26] / SUP[f26]) == "57.96" and all(abs(SHARES[d] / SUP[d] - D("0.5796")) > D("0.1") for d in (f26, f28)), "the February figure is the assets ratio")
need("If the update's two figures use different measures, as these matches suggest, the ratio fell %s points by total assets or %s points by token supply from the end of February 28 to the end of April 30, rather than the %s points between the update's figures." % (
    r2((ASSETS[f28] / SUP[f28] - ASSETS[e30] / SUP[e30]) * 100), r2((SHARES[f28] / SUP[f28] - SHARES[e30] / SUP[e30]) * 100), r2(D("57.96") - D("44.0"))))

# ---- method --------------------------------------------------------------------------------------------------------
t0, t1 = run["started_utc"][11:19], run["finished_utc"][11:19]
need("from %s to %s UTC on October 13, 2026." % (t0, t1))
rule(run["started_utc"].startswith("2026-10-13") and run["finished_utc"].startswith("2026-10-13"), "the read's date")
need("For each of the %d UTC days from September 30 to November 30, 2025 and from January 31 to May 31, 2026" % len(st))
rule(sorted(st) == days("2025-09-30", "2025-11-30") + days("2026-01-31", "2026-05-31"), "the state days")
need("The two RPCs gave the same six values on all %d days." % len(st))
need("%s in all over the %d days from October 1 to November 15, 2025 and April 1 to May 15, 2026." % ("{:,}".format(run["events"]), len(fl)))
rule(sorted(fl) == days("2025-10-01", "2025-11-15") + days("2026-04-01", "2026-05-15"), "the flow days")
rule(run["events"] == sum(NB.values()) + sum(NM.values()), "events")
rule(run["state_sources"] == ["https://eth.drpc.org", "https://eth-mainnet.public.blastapi.io"] and run["flow_source"] == "https://gateway.tenderly.co/public/mainnet",
     "the RPCs")
src = {r["id"]: r for r in rows(HERE / "inputs" / "sources.csv")}
sup_read = src["S3"]["read_utc"]
rule(sup_read == "2026-10-13T00:03:43Z to 00:17:21Z", "the supply read's times")
need("made from %s to %s UTC the same morning, and the supply matched it on every day." % (sup_read[11:16], sup_read[-9:-4]))
rule(LAYOUT["cutoff"].startswith("Reads of Ethereum at the end of each UTC day, made %s to %s UTC on October 13, 2026" % (sup_read[11:16], t1[:5])), "cutoff times")
need("The silo's address came from sUSDe's silo function on both RPCs at the latest block, and Ethena's documentation names the same contract.")
rule(("their USDe is placed in the USDeSilo contract, " + run["cooldown_silo"]) in WEBTXT, "the documentation names the silo the read used")
rule(all(int(r["block_time_unix"]) <= int(r["day_end_unix"]) < int(r["next_block_time_unix"]) for r in day), "day-end blocks")

# ---- reproduce ---------------------------------------------------------------------------------------------------------
log = (HERE / "out" / "run_log.txt").read_text(encoding="utf-8")
n_checks = sum(1 for l in log.split("\n") if l.startswith("PASS "))
rule(("all %d checks passed" % n_checks) in log and not any(l.startswith("FAIL ") for l in log.split("\n")), "run log")
need("stops before writing its tables if any of its %d checks fails" % n_checks)
need("burned, April 19 to 27  = %s" % r2(b9))
need("minted, April 19 to 27  = %s" % r2(m9))
need("minted - burned         = %s" % r2(m9 - b9))
need("                        = %s - %s\n                        = %s" % (r2(s1), r2(s0), r2(s1 - s0)))
need("fall                    = %s / %s\n                        = %s%%" % (r2(s0 - s1), r2(s0), pc((s0 - s1) / s0)))
need("sUSDe and its silo      = %s - %s\n                        = %s, or %s%% of the fall" % (r2(stk1), r2(stk0), r2(stk1 - stk0), pc(A["share"])))
need("outside sUSDe           = %s - %s\n                        = %s, or %s%% of the fall" % (r2(OUT["2026-04-27"]), r2(OUT[k0]), r2(OUT["2026-04-27"] - OUT[k0]),
                                                                                         pc((OUT["2026-04-27"] - OUT[k0]) / (s1 - s0))))

# ---- metadata, key findings and the chart -----------------------------------------------------------------------------
need("In the nine days after the rsETH exploit of April 18, 2026, %s billion USDe was burned and supply fell %s%%, its steepest nine-day fall since 2024." % (
    b(b9), pc((s0 - s1) / s0)), "meta")
rule(f9[1:] == ("2026-04-18", "2026-04-27"), "the largest nine-day fall")
need("USDe's total supply on Ethereum fell %s%% in the nine UTC days after the rsETH exploit of April 18, 2026, from %s to %s, as %s USDe was burned and %s minted." % (
    pc((s0 - s1) / s0), r2(s0), r2(s1), r2(b9), r2(m9)), "findings")
need("As a share of supply it was the largest fall over three, seven or nine days since January 1, 2024, while October 2025 was larger in USDe.", "findings")
need("With sUSDe's cooldown at one day since March 16, 2026, sUSDe and its cooldown silo made up %s%% of the April fall, a little above their %s%% share of supply." % (
    pc(A["share"]), pc(A["start"])), "findings")
need("In the nine days from October 10, 2025, under a seven-day cooldown, they held %s%% of supply and made up %s%% of the fall, and %s%% of the 30-day fall to November 8." % (
    pc(O["start"]), pc(O["share"]), pc(o30)), "findings")
need("so it does not show whose USDe was redeemed or that the cooldown caused the difference.", "findings")
need("USDe's supply fell %s%% in the nine days after the rsETH exploit" % pc((s0 - s1) / s0), "svg")
need("Silo %s on Apr 20" % (b(SILO["2026-04-20"]) + "B"), "svg")
need(">%sB<" % b(OUT["2026-05-31"]), "svg")
need(">%sB<" % b(HELD["2026-05-31"]), "svg")
need("At the end of April 18, 2026, the day of the rsETH exploit, supply was %s billion, of which sUSDe held %s billion." % (b(s0), b(HELD[k0])), "svg")
need("sUSDe's cooldown was cut from seven days to one on March 16, 2026.", "svg")
need("Cooldown cut to 1 day, Mar 16", "svg")
need("rsETH exploit, Apr 18", "svg")
cd = rows(HERE / "out" / "chart_data.csv")
rule([r["day"] for r in cd] == days("2026-01-31", "2026-05-31"), "chart days")
for r in cd:
    d = r["day"]
    for col, v in (("held_by_susde_billion", HELD[d]), ("cooldown_silo_billion", SILO[d]), ("outside_susde_billion", OUT[d]), ("usde_supply_billion", SUP[d])):
        rule(D(r[col]) == (v / BIL).quantize(D("0.0001"), rounding=ROUND_HALF_UP), "chart data %s %s" % (d, col))

if FAILS:
    print("\n".join(FAILS))
    print("\n%d failures, %d phrases found" % (len(FAILS), len(FOUND)))
    sys.exit(1)
print("all %d phrases found and every rule held" % len(FOUND))
