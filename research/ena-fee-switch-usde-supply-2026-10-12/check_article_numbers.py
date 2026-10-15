#!/usr/bin/env python3
"""Recomputes every computed figure in article_draft.md, metadata.json, layout.json's key findings and the chart's
text from the inputs, with code written apart from fee_switch_supply.py, using decimal arithmetic instead of
fractions, and checks that each phrase appears where it should. Exits with an error if a phrase is missing or a
page rule fails. Python 3.8 or later, no network."""
import csv
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal as D, getcontext, ROUND_HALF_UP
from pathlib import Path

getcontext().prec = 60
HERE = Path(__file__).parent
CH = HERE / "inputs" / "chain"
WEB = HERE / "inputs" / "web"
SLUG = "ena-fee-switch-usde-supply-2026-10-12"
ARTICLE = (HERE / "article_draft.md").read_text(encoding="utf-8")
META = json.loads((HERE / "metadata.json").read_text(encoding="utf-8"))
LAYOUT = json.loads((HERE / "layout.json").read_text(encoding="utf-8"))
SVG = (HERE / "out" / "chart_usde_supply_milestones.svg").read_text(encoding="utf-8")
FAILS, FOUND = [], []
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def need(phrase, where="article"):
    text = {"article": ARTICLE, "meta": json.dumps(META, ensure_ascii=False), "findings": " ".join(LAYOUT["keyFindings"]), "svg": SVG}[where]
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
    return r2(D(x) * 100, places) + "%"


def long_day(s):
    d = date.fromisoformat(s)
    return "%s %d, %d" % (MONTHS[d.month - 1], d.day, d.year)


def bn(x, places=2):
    return r2(D(x) / D(10) ** 9, places)


# ---- the series, recomputed ---------------------------------------------------------------------------------------
day = rows(CH / "day_reads.csv")
DAYS = [r["day"] for r in day]
S = [D(int(r["usde_total_supply_raw"])) / D(10) ** 18 for r in day]
POS = {d: i for i, d in enumerate(DAYS)}
rule(DAYS[0] == "2024-01-01" and len(DAYS) == (date.fromisoformat(DAYS[-1]) - date(2024, 1, 1)).days + 1, "the days run without a gap")
for r in day:
    rule(int(r["block_time_unix"]) <= int(r["day_end_unix"]) < int(r["next_block_time_unix"]), "day-end block " + r["day"])
    rule(r["same_supply_second_rpc"] == "1" and r["same_hash_second_rpc"] == "1", "second RPC " + r["day"])


def trailing(n):
    out, run = [], D(0)
    for i, v in enumerate(S):
        run += v
        if i >= n:
            run -= S[i - n]
        out.append(run / n if i + 1 >= n else None)
    return out


AV = {n: trailing(n) for n in (1, 14, 30, 90)}
FIRST = D("7.5") * D(10) ** 9
LEVELS = [(FIRST, 5), (D(10) ** 10, 10), (D(15) * D(10) ** 9, 15), (D(20) * D(10) ** 9, 20), (D(25) * D(10) ** 9, 25)]


def take(x):
    t = 0
    for lv, rate in LEVELS:
        if x is not None and x >= lv:
            t = rate
    return t


L = len(S) - 1
last_day = DAYS[L]
a14 = AV[14][L]

# ---- page rules -------------------------------------------------------------------------------------------------
lines = ARTICLE.split("\n")
rule(sum(1 for l in lines if l.startswith("# ")) == 1 and lines[0] == "# " + META["headline"], "one H1, the metadata headline")
rule(len(META["title"]) <= 60 and 120 <= len(META["description"]) <= 160, "title and description lengths")
rule("[Qorban Ferrell · @Degenerate\\_DeFi](https://ethenadash.com/about/) · Published %d %s %d" % (
    date.fromisoformat(META["datePublished"]).day, MONTHS[date.fromisoformat(META["datePublished"]).month - 1], date.fromisoformat(META["datePublished"]).year) in ARTICLE,
    "byline with author link and the metadata's date")
rule(ARTICLE.rstrip().endswith("Analysis of public blockchain data. Not investment advice."), "closing line")
svg_text = " ".join(re.findall(r">([^<>]+)<", SVG))
readme = (HERE / "README.md").read_text(encoding="utf-8")
for bad_ in ["—", "–", ";", "This article", "on-chain", "FAQ"]:
    rule(bad_ not in ARTICLE, "forbidden text in article: %r" % bad_)
    rule(bad_ not in " ".join(LAYOUT["keyFindings"]) + META["description"] + META["imageAlt"] + LAYOUT["cutoff"] + LAYOUT["chartLabel"], "forbidden text in metadata or layout: %r" % bad_)
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
for f in LAYOUT["keyFindings"] + [META["description"], META["imageAlt"], svg_text]:
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
for f in LAYOUT["archiveFiles"]:
    rule((HERE / f).exists(), "archive file missing " + f)
for f in LAYOUT["assets"]:
    rule((HERE / "out" / f).exists(), "asset missing " + f)
for m in re.findall(r"\(/research-assets/" + SLUG + r"/([^)]+)\)", ARTICLE):
    rule(m in LAYOUT["assets"] or m == "calculation-files.zip", "linked download not in assets " + m)
# No account addresses and no transaction hashes in the published files. The only addresses are USDe's, its OFT
# adapter's and the three contracts of the voting strategies, and the only 64-digit hex strings with 0x are the read block's hash and the Snapshot proposal's id.
allowed = {"0x4c9edd5852cd905f086c759e8383e09bff1e68b3", "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34",
           # ENA, sENA and the staking contract that Snapshot's voting strategies read, named in the sources file
           "0x57e114b691db790c35207b2e685d4a43181e6061", "0x8be3460a480c80728a8c4d7a5d5303c85ba7b3b9", "0x8707f238936c12c309bfc2b9959c35828acfc512"}
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
    if re.search(r"0x[0-9a-f]{64}(?![0-9a-f])", text):
        rule(f in ("inputs/chain/read_block.csv", "inputs/web/ena_fee_switch_sources_2026-10-13.txt", "README.md", "check_article_numbers.py"), "64-digit hex in " + f)
        found = set(re.findall(r"0x[0-9a-f]{64}(?![0-9a-f])", text))
        rule(found <= {"0xdf2c3a356d12c07c986374894c2e4a091a0e4320bdf8b017b992be549e040f6e",
                       "0xcb6b9ed95bf0c64b6101ff7d3a770af86e07701d8419b541cf91a6894022f2a3"}, "unexpected 64-digit hex in " + f)

# ---- phrases --------------------------------------------------------------------------------------------------------
WEBTXT = (WEB / "ena_fee_switch_sources_2026-10-13.txt").read_text(encoding="utf-8")
CARRIED = (WEB / "usde_chain_review_carried_2026-10-12.txt").read_text(encoding="utf-8")
B = D(10) ** 9
grow = lambda target, base: target / base - 1  # noqa: E731
need(r2(S[L]))
need("at the end of October 12, 2026 UTC")
need(r2(a14))
need("The average had to rise %s, or by %s, to reach $7.5 billion, and USDe's day-end supply, its total supply at the end of a UTC day, had to rise %s." % (
    pc(grow(FIRST, a14)), r2(FIRST - a14), pc(grow(FIRST, S[L]))))
# The last day the 14 day average was at or above the first milestone, and the days below it since.
above = [i for i in range(L + 1) if AV[14][i] is not None and AV[14][i] >= FIRST]
runs = []
for i in above:
    if runs and runs[-1][1] == i - 1:
        runs[-1][1] = i
    else:
        runs.append([i, i])
rule(len(runs) == 1, "one stretch of the 14 day average at or above $7.5 billion")
a_first, a_last = runs[0]
rule(all(AV[14][i] < FIRST for i in range(a_last + 1, L + 1)), "below since")
need("Below that milestone the take rate is zero, and the 14 day average was below it on all %d days from %s to %s." % (
    L - a_last, long_day(DAYS[a_last + 1]), long_day(last_day)))
rule(L - a_last == 318, "318 days below")
vo = POS["2026-08-27"]
rule(all(AV[n][i] < FIRST for n in (1, 14, 30, 90) for i in range(vo, L + 1)), "no measure at the first milestone since voting opened")
need("From August 27, 2026, when voting opened, to October 12, USDe's day-end supply and its 14, 30 and 90 day averages stayed below $7.5 billion on every day.")
need("the series reproduced all twelve counts in the backtest's table of supply measures")
need("reproduced all twelve counts in the table of supply measures", "findings")
p0, p1 = date(2024, 9, 19), date(2026, 8, 24)
need("Over the %d days of the backtest" % ((p1 - p0).days + 1))
need("In 2025 the 14 day average stood at or above $7.5 billion for %d days, from %s to %s, and it never reached $15 billion." % (
    a_last - a_first + 1, long_day(DAYS[a_first])[:-6], long_day(DAYS[a_last])[:-6]))
rule(DAYS[a_first].startswith("2025") and DAYS[a_last].startswith("2025"), "the stretch in 2025")
rule(max(v for v in AV[14] if v is not None) < 15 * B and max(S) < 15 * B, "never $15 billion")
# The vote, from the sources file.
for ph in ["Voting from 2026-08-27 13:59:52 UTC to 2026-09-02 13:59:52 UTC", "Scores 17,786,102.45 For, 0 Against and 0 Abstain, from 88 votes, against a",
           "quorum of 5,000,000", "confirmed on September 8, 2026 that the ENA snapshot vote had passed"]:
    rule(ph in WEBTXT.replace("\n", " "), "sources file: " + ph)
need("Voting ran from 13:59:52 UTC on August 27 to 13:59:52 UTC on September 2, 2026.")
need("The proposal passed with voting power of 17,786,102.45 for it, none against and none abstaining, from 88 votes, above a quorum of 5,000,000.")
need("A forum post confirmed the result on September 8.")
# Ethena's illustrative table, recomputed at 6.0%.
for bn_, rate in [(D("7.5"), 5), (D(10), 10), (D(15), 15), (D(20), 20)]:
    rev = bn_ * B * D("0.06") / D(10) ** 6
    buy = rev * rate / 100
    revs = "{:,}".format(int(rev)) if rev == int(rev) else str(rev)
    buys = ("{:,}".format(int(buy)) if buy == int(buy) else str(buy.normalize()))
    label = ("$%s billion" % (str(bn_.normalize()) if bn_ != int(bn_) else int(bn_)))
    need("| %s | %d%% | $%s million | $%s million |" % (label, rate, revs, buys))
need("| $25 billion and above | 25% | not given | not given |")
for ph in ["$450m, $600m, $900m and $1,200m", "5%, 10%, 15%, 20% and 25%", "$22.5m, $60m, $135m and $240m", "Gross protocol APY is 6.0% in every column",
           "below Ethena's realised gross protocol APY since inception", "4.60% realized protocol APY", "$7.5B and 5%, $22.5M and $17.3M", "95% of the net revenue",
           "a 14 day trailing average of USDe supply as the trigger, because one large mint can move a single day's supply", "in place of its own earlier 30 day ramp",
           "members for the current six-month term were Blockworks Advisory, LlamaRisk and Kairos Research", "nonvoting member",
           "The Risk Committee sets risk parameters across the protocol, including the activation conditions for mechanisms such as the fee switch",
           "Committee had signed off on the rates, the thresholds and the mechanics", "which was to launch the following week",
           "would be addressed in separate proposals", "suggested a mechanism for executing buybacks", "705 days of Ethena data, from 19 September 2024 to 24 August 2026",
           "Daily supply first crossed $7.5B on 27 July 2025", "The 14 day average peaked at $14.65B in October 2025", "the 90 day average at $12.38B",
           "at the USDe supply of the day, $4.07B, the schedule takes nothing", "Kairos Research supported turning on the fee switch",
           "OAK Research supported the architecture"]:
    rule(ph in WEBTXT.replace("\n", " "), "sources file: " + ph)
need("The proposal illustrated the schedule at a gross protocol APY of 6.0%, which it called lower than the gross protocol APY Ethena had realized since launch.")
need("| USDe supply | Take rate | Gross revenue a year at a 6.0% gross protocol APY | Buybacks a year at that APY |")
need("Its buybacks are the take rate times gross revenue, although the table called the take rate a share of net revenue.")
for ph in ["Annualized gross revenue is $450m", "The net revenue take rate for buybacks", "described the take as a share of gross protocol revenue",
           "annualized gross revenue $450M", "The proposal has four voting strategies", "Two count balances of ENA", "of sENA",
           "Two count ENA and sENA deposited in the contract", "read through its stakes function", "texts have 14 nonblank lines, and they differ only in formatting",
           "sENA is staked ENA, an ERC-4626 wrapper"]:
    rule(ph in WEBTXT.replace("\n", " "), "sources file: " + ph)
need("The proposal weighted each vote by the voter's ENA and sENA, a vault token for staked ENA, held directly or deposited in a separate contract.")
for ph in ["none of the words average, trailing, moving, window, day, measure or defin(e)", "Net revenue appears once, in the sentence on the 95%, and is not defined",
           "differ only in formatting and one list number"]:
    rule(ph in WEBTXT.replace("\n", " "), "sources file: " + ph)
need("would go to ENA buybacks, without defining net revenue.")
need("at the 4.60% gross protocol APY it called realized, put the buybacks at the first milestone at $17.3 million a year")
need("95% of the net revenue that Ethena's business lines pay to the Ethena Foundation would go to ENA buybacks")
# Where the supply stood: the gaps to every milestone.
for lv, rate in LEVELS:
    label = "$%s billion" % (str((lv / B).normalize()) if lv / B != int(lv / B) else int(lv / B))
    need("| %s | %d%% | %s, or %s | %s, or %s |" % (label, rate, r2(lv - a14), pc(grow(lv, a14)), r2(lv - S[L]), pc(grow(lv, S[L]))))
need("The average covers the 14 days from %s to %s." % (long_day(DAYS[L - 13])[:-6], long_day(last_day)))
r60 = max(range(L - 59, L + 1), key=lambda i: S[i])
need("after falling from %s on %s, the highest day end in the 60 days to October 12" % (r2(S[r60]), long_day(DAYS[r60])[:-6]))
rule(all(S[i] < S[r60] for i in range(r60 + 1, L + 1)), "the supply after the 60 day high stayed below it")
need("It was %s above the %s of August 27, 2026, the day voting opened" % (pc(grow(S[L], S[vo])), r2(S[vo])))
top = max(range(L + 1), key=lambda i: S[i])
low = min(range(top, L + 1), key=lambda i: S[i])
need("and %s above the %s of %s, its lowest day end since the 2025 peak" % (pc(grow(S[L], S[low])), r2(S[low]), long_day(DAYS[low])))
# The 2025 stretch.
cross = next(i for i in range(L + 1) if S[i] >= FIRST)
need("first reached $7.5 billion on %s, at %s, and the 14 day average followed on %s, seven days later" % (long_day(DAYS[cross]), r2(S[cross]), long_day(DAYS[a_first])[:-6]))
rule(a_first - cross == 7, "seven days later")
need("The average stayed at or above $7.5 billion for %d days, to %s" % (a_last - a_first + 1, long_day(DAYS[a_last])))
ten = [i for i in range(L + 1) if AV[14][i] is not None and AV[14][i] >= 10 * B]
rule(ten[-1] - ten[0] + 1 == len(ten), "one stretch at $10 billion")
need("at or above $10 billion for %d days, from %s to %s" % (len(ten), long_day(DAYS[ten[0]])[:-6], long_day(DAYS[ten[-1]])))
p14 = max(range(L + 1), key=lambda i: AV[14][i] if AV[14][i] is not None else D(0))
need("Day-end supply peaked at %s on %s, and the 14 day average at %s on %s, %s short of the $15 billion milestone" % (
    r2(S[top]), long_day(DAYS[top]), r2(AV[14][p14]), long_day(DAYS[p14])[:-6], r2(15 * B - AV[14][p14])))
need("After the peak, day-end supply fell %s, to its low of %s" % (pc(1 - S[low] / S[top]), long_day(DAYS[low])))
a14_start = max(i for i in range(cross) if AV[14][i] is not None and AV[14][i] <= a14)
d_start = max(i for i in range(cross) if S[i] <= S[L])
need("The 14 day average last stood at or below its October 12, 2026 level on %s, and reached $7.5 billion %d days later" % (long_day(DAYS[a14_start]), a_first - a14_start))
need("Day-end supply last stood at or below its October 12, 2026 level on %s, at %s, and reached $7.5 billion %d days later" % (
    long_day(DAYS[d_start]), r2(S[d_start]), cross - d_start))
# The backtest, recomputed over its panel.
P0, P1 = POS["2024-09-19"], POS["2026-08-24"]
names = {1: "Day-end supply", 14: "14 day average", 30: "30 day average", 90: "90 day average"}
published = {1: (0, 117, 4), 14: (7, 118, 4), 30: (14, 120, 4), 90: (34, 141, 4)}
for n in (1, 14, 30, 90):
    rates = [take(AV[n][i]) for i in range(P0, P1 + 1)]
    act = [P0 + k for k, t in enumerate(rates) if t > 0]
    changes = sum(1 for k in range(1, len(rates)) if rates[k] != rates[k - 1])
    to_first = (date.fromisoformat(DAYS[act[0]]) - date(2025, 7, 27)).days
    pk = max(range(P0, P1 + 1), key=lambda i: AV[n][i])
    rule((to_first, len(act), changes) == published[n], "backtest counts for %d" % n)
    rule(sorted(set(rates)) == [0, 5, 10], "rates reached for %d" % n)
    need("| %s | %s | %d (%d) | %d (%d) | %d (%d) | %s on %s |" % (names[n], long_day(DAYS[act[0]]), to_first, published[n][0], len(act), published[n][1],
                                                             changes, published[n][2], bn(AV[n][pk]), long_day(DAYS[pk])))
need("Blockworks Advisory gave the 14 day average's peak as $14.65 billion in October 2025 and the 90 day average's as $12.38 billion")
need("In its post of August 27, 2026 it put USDe's supply at $4.07 billion, %s above the onchain supply at the end of August 26 and %s above that at the end of August 27." % (
    pc(grow(D("4.07") * B, S[vo - 1])), pc(grow(D("4.07") * B, S[vo]))))
rule("2    | BlockworksAdvisory  | 2026-08-27 14:12:05" in WEBTXT, "Blockworks Advisory's post time")
# Which supply counts, carried figures.
for ph in ["approvalRequired() was true", "2,292,201,958.40", "4,746,167,897.22", "within 95.45 USDe", "35 other chains", "18:41:35 UTC"]:
    rule(ph in CARRIED.replace("\n", " "), "carried file: " + ph)
need("the adapter held 2,292,201,958.40 USDe, %s of the total supply on Ethereum, and the USDe on the 35 other chains read came to about %s USDe less" % (
    pc(D("2292201958.40") / D("4746167897.22")), r2(D("2292201958.40") - D("2292201862.94"), 0)))
rule(D("2292201958.40") > D("2292201862.94"), "the other chains' sum is below the adapter's balance")
# Method.
fin = json.loads((CH / "finality_check.json").read_text(encoding="utf-8"))
rb = rows(CH / "read_block.csv")
rbt = datetime.fromtimestamp(int(rb[0]["block_time_unix"]), tz=timezone.utc)
need("For each of the %s UTC days from January 1, 2024 to October 12, 2026" % "{:,}".format(len(DAYS)))
need("The two gave the same supply and the same block hash on all %s days." % "{:,}".format(len(DAYS)))
fin_t = datetime.fromisoformat(fin["started_utc"].replace("Z", "+00:00"))
need("When a second script ran at %s UTC on October 13, 2026, two RPCs reported block %s as finalized" % (fin_t.strftime("%H:%M"), "{:,}".format(fin["finalized"][0]["block"])))
rule(fin["same_digest"] and all(f["block"] == fin["finalized"][0]["block"] and f["block"] >= int(day[-1]["block"]) for f in fin["finalized"]), "finality")
rule(all(r["usde_total_supply_raw"] == day[-1]["usde_total_supply_raw"] for r in rb), "read block supply equals the last day end")
need("At the read block, %s, two RPCs gave the supply as %s, the same as at the end of October 12." % ("{:,}".format(int(rb[0]["block"])), r2(D(int(rb[0]["usde_total_supply_raw"])) / D(10) ** 18)))
cut = "read at Ethereum block %s, %s UTC on %s" % ("{:,}".format(int(rb[0]["block"])), rbt.strftime("%H:%M:%S"), long_day(rbt.date().isoformat()))
need(cut)
rule(cut in LAYOUT["cutoff"], "cutoff")
rule(date.fromisoformat(META["datePublished"]) >= rbt.date(), "the published date is not before the UTC date of the read")
log_ = (HERE / "out" / "run_log.txt").read_text(encoding="utf-8")
nchecks = int(re.search(r"all (\d+) checks passed", log_).group(1))
need("if any of its %d checks fails" % nchecks)
# The formula block.
s14 = sum(S[L - 13:L + 1], D(0))
rule(s14 / 14 == a14, "sum over 14")
need("= %s / 14" % r2(s14))
need("= %s\ngap" % r2(a14))
need("               = %s\nrise needed" % r2(FIRST - a14))
need("               = %s\nday-end rise" % pc(grow(FIRST, a14)))
need("= 7,500,000,000 / %s - 1\n               = %s" % (r2(S[L]), pc(grow(FIRST, S[L]))))
need("take rate      = 0%%, because %s is below 7,500,000,000" % r2(a14))
rule(take(a14) == 0, "nothing taken")
# Chart, caption, metadata and key findings.
need("had to rise %s%% to reach the first ENA buyback milestone" % r2(grow(FIRST, a14) * 100, 0), "svg")
need("included the USDe locked there", "svg")
need("%sB on Oct 3, 2025" % bn(S[top]), "svg")
need("%sB on Oct 12, 2026" % bn(S[L]), "svg")
need("closed on September 2, 2026", "svg")
for where in ("article", "meta"):
    need("Day-end supply peaked at %s billion on %s." % (bn(S[top]), long_day(DAYS[top])), where)
    need("The 14 day average was at or above 7.5 billion from %s to %s." % (long_day(DAYS[a_first])[:-6], long_day(DAYS[a_last])), where)
    need("On October 12, 2026 day-end supply was %s billion and the 14 day average %s billion." % (bn(S[L]), bn(a14)), where)
need("USDe's 14 day average supply was $%s billion on October 12, 2026. It needed to rise %s to reach $7.5 billion" % (bn(a14), pc(grow(FIRST, a14))), "meta")
need("USDe's total supply on Ethereum was %s at the end of October 12, 2026 UTC, and its 14 day trailing average was %s. The average had to rise %s" % (
    r2(S[L]), r2(a14), pc(grow(FIRST, a14))), "findings")
need("The 14 day average stood at or above $7.5 billion for %d days, from %s to %s, peaked at $%s billion and never reached $15 billion." % (
    a_last - a_first + 1, long_day(DAYS[a_first])[:-6], long_day(DAYS[a_last]), bn(AV[14][p14])), "findings")

if FAILS:
    print("\n".join(FAILS))
    sys.exit(1)
print("%d phrases found, page rules pass" % len(FOUND))
