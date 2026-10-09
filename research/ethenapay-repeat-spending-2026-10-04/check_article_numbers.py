#!/usr/bin/env python3
"""
Recomputes every computed figure in article_draft.md, metadata.json and the chart's text from
the files in inputs/, with code written apart from ethenapay_repeat_spending_review.py, and
confirms that each exact phrase appears. Exits with an error if a phrase is missing or an
assertion fails, so rerun it after any edit. Python 3 standard library only. No network.
"""
import csv
import json
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).parent
INP = HERE / "inputs"
ARTICLE = (HERE / "article_draft.md").read_text()
META = json.loads((HERE / "metadata.json").read_text())
# layout.json is part of the site build and not of the download, so its cutoff is checked only when present
LAYOUT = json.loads((HERE / "layout.json").read_text()) if (HERE / "layout.json").exists() else None
SVG = (HERE / "out" / "chart_repeat_spending.svg").read_text()
TEXT = ARTICLE + "\n" + META["description"] + "\n" + META["imageAlt"] + "\n" + META["title"] + "\n" + SVG

found, missing = 0, []


def need(phrase, where=TEXT):
    global found
    if phrase in where:
        found += 1
    else:
        missing.append(phrase)


def pc(n, d):
    return f"{100 * n / d:.0f}%"


# ---------------------------------------------------------------- inputs
meta = json.loads((INP / "chain" / "meta.json").read_text())
assert meta["day_0"] == "2026-05-15" and meta["end_block"] == 96839679
assert meta["balance_check"]["block"] == 96815525
src = list(csv.DictReader(open(INP / "sources.csv")))
assert any("15:53:28 UTC on October 5" in r["used_for"] for r in src)
assert min(r["read_at_utc"][:10] for r in src if r["read_at_utc"][:4] == "2026") == "2026-10-06"
D0 = date(2026, 5, 15)
CUT = date(2026, 10, 4)
assert CUT.weekday() == 6

spend = {}                 # wallet -> set of ordinal days through CUT
ev_day = {}                # ordinal day -> spend events, through CUT
ev_all = {}                # ordinal day -> spend events, through October 5
oct5 = set()               # wallets with a spend event on October 5, the day after the cutoff
total_events, all_w = 0, set()
for r in csv.DictReader(open(INP / "chain" / "spend_wallet_days.csv")):
    total_events += int(r["events"])
    all_w.add(r["wallet"])
    day = D0.toordinal() + int(r["day"])
    ev_all[day] = ev_all.get(day, 0) + int(r["events"])
    if day <= CUT.toordinal():
        spend.setdefault(r["wallet"], set()).add(day)
        ev_day[day] = ev_day.get(day, 0) + int(r["events"])
    elif day == CUT.toordinal() + 1:
        oct5.add(r["wallet"])
assert total_events == meta["spend_events"] == 29556 and len(all_w) == meta["wallets_that_ever_spent"] == 820
bal = {}
for r in csv.DictReader(open(INP / "chain" / "wallet_activity.csv")):
    bal[r["wallet"]] = int(r["balance_wei_at_last_snapshot"] or 0)

# weeks as ordinal of their Monday
def wk(o):
    return o - date.fromordinal(o).weekday()


LAST = wk(CUT.toordinal())
firstday = {w: min(s) for w, s in spend.items()}
fw = {w: wk(o) for w, o in firstday.items()}
wkset = {w: {wk(o) for o in s} for w, s in spend.items()}
BETA = date(2026, 8, 31).toordinal()


def later(w, k):
    return fw[w] + 7 * k in wkset[w]


def md(o):
    d = date.fromordinal(o)
    return f"{d:%B} {d.day}"


def short(o):
    d = date.fromordinal(o)
    return f"{d:%b} {d.day}"


# ---------------------------------------------------------------- byline, title and lead
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
need("· Full weeks through October 4, 2026 · Balances at 15:53 UTC on October 5 · Sources read October 6 to 9, 2026 UTC")
if LAYOUT:
    need(LAYOUT["cutoff"], ARTICLE)
need("# Do EthenaPay wallets keep spending?\n\nRepeat-spending review / Weeks to October 4, 2026\n")
assert META["headline"] == "Do EthenaPay wallets keep spending?" and len(META["title"]) <= 60 and len(META["description"]) <= 160
assert "Oct 4, 2026" in META["title"] and CUT == date(2026, 10, 4)
c0 = [w for w in fw if fw[w] == BETA]
k1 = sum(later(w, 1) for w in c0)
k4 = sum(later(w, 4) for w in c0)
assert date(2026, 9, 1).toordinal() - BETA == 1                 # the beta opened in the week of August 31
need(f"Of the {len(c0)} wallets whose first spend came in the week the beta opened, August 31 to September 6, 2026, {k1} spent "
     f"again the next week and {k4} in the week to October 4, four weeks on.")
need(f"Of {len(c0)} EthenaPay wallets that first spent in the week the beta opened, {k4} spent in the week to October 4, four "
     "weeks on. Weekly cohorts from a chain recount.", META["description"])
r1 = []
for c in (BETA + 7, BETA + 14, BETA + 21):
    ws = [w for w in fw if fw[w] == c]
    r1.append(round(100 * sum(later(w, 1) for w in ws) / len(ws)))
need(f"Of the wallets whose first spend came in each of the next three weeks, {min(r1)}% to {max(r1)}% spent again the "
     "following week.")
need("Ethena opened its beta on September 1, so August 31 to September 6 is the beta week here.")
pre = [w for w in fw if fw[w] < BETA]
beta = [w for w in fw if BETA <= fw[w] < LAST]
assert min(firstday[w] for w in pre) == date(2026, 6, 4).toordinal() and max(firstday[w] for w in pre) <= date(2026, 8, 30).toordinal()
assert min(firstday[w] for w in beta) >= BETA and max(firstday[w] for w in beta) <= date(2026, 9, 27).toordinal()


def curve(ws, kmax):
    out = []
    for k in range(1, kmax + 1):
        el = [w for w in ws if fw[w] + 7 * k <= LAST]
        out.append((k, len(el), sum(later(w, k) for w in el)))
    return out


bc = curve(beta, 4)
pcv = curve(pre, 5)
assert all(e == len(pre) for _, e, _ in pcv)
assert all(pcv[i][2] / pcv[i][1] < bc[i][2] / bc[i][1] for i in range(4))   # a lower rate in each of weeks 1 to 4
need(f"Wallets that first spent before the beta week, from June 4 to August 30, kept spending at a lower rate. Of these "
     f"{len(pre)} pre-beta wallets, {pcv[0][2] / pcv[0][1]:.0%} spent again the week after their first spend, against "
     f"{bc[0][2] / bc[0][1]:.0%} of the {len(beta)} wallets whose first spend came from August 31 to September 27.")
LAPSE = date(2026, 9, 21).toordinal()
early = [w for w in firstday if firstday[w] < LAPSE]
lapsed = [w for w in early if not any(LAPSE <= o <= CUT.toordinal() for o in spend[w])]
one_usde = sum(1 for w in lapsed if bal.get(w, 0) >= 10 ** 18)
assert round(len(lapsed) / len(early) * 5) == 1                  # about one in five
assert one_usde / len(lapsed) > 0.5                              # most of those
need(f"Of the {len(early)} wallets whose first spend came before September 21, {len(lapsed)}, about one in five, had no spend "
     f"event from September 21 to October 4, and {one_usde} of those held at least 1 USDe at 15:53 UTC on October 5.")

# ---------------------------------------------------------------- the beta cohort table and the chart
assert BETA + 28 == LAST
for c in [BETA, BETA + 7, BETA + 14, BETA + 21, BETA + 28]:
    ws = [w for w in fw if fw[w] == c]
    cells = []
    for k in range(1, 5):
        if c + 7 * k <= LAST:
            n = sum(later(w, k) for w in ws)
            cells.append(f"{n} ({pc(n, len(ws))})")
        else:
            cells.append("")
    row = f"| {short(c)} to {short(c + 6)} | {len(ws)} | " + " | ".join(cells) + " |"
    while "|  |" in row:
        row = row.replace("|  |", "| |")     # an empty cell is written "| |" in the article
    need(row)
after1 = []
for c in [BETA, BETA + 7, BETA + 14]:
    ws = [w for w in fw if fw[w] == c]
    for k in range(2, 5):
        if c + 7 * k <= LAST:
            after1.append(round(100 * sum(later(w, k) for w in ws) / len(ws)))
need(f"After the first week the share stayed between {min(after1)}% and {max(after1)}% in every beta cohort and week observed.")
bshares = [f"{n / e:.0%}" for _, e, n in bc]
pshares = [f"{n / e:.0%}" for _, e, n in pcv]
any4 = sum(1 for w in c0 if any(later(w, k) for k in range(1, 5)))
all4 = sum(1 for w in c0 if all(later(w, k) for k in range(1, 5)))
assert bc[0][1] > bc[1][1] > bc[2][1] > bc[3][1] == len(c0)        # each later week covers fewer cohorts
need(f"Taken together, the first four beta cohorts' shares were {bshares[0]}, {bshares[1]}, {bshares[2]} and {bshares[3]} in the "
     f"four weeks after their first spend. Each later week covers fewer cohorts, and only the cohort of the beta week, "
     f"{len(c0)} wallets, had reached a fourth week. Of those {len(c0)}, {any4} spent in at least one of the four weeks and {all4} "
     "in all four.")
need(f"Wallets of the first four beta cohorts, {len(beta)} in all, {bshares[0]} in week 1, {bshares[1]} in week 2, {bshares[2]} in "
     f"week 3 and {bshares[3]} in week 4, when {bc[3][1]} had been observed. Pre-beta wallets, {len(pre)} in all, {pshares[0]}, "
     f"{pshares[1]}, {pshares[2]}, {pshares[3]} and {pshares[4]} in weeks 1 to 5.", ARTICLE)
need(f"Wallets that first spent from August 31 to September 27, {bshares[0]} in week 1 and {bshares[3]} in week 4. Wallets that "
     f"first spent from June 4 to August 30, {pshares[0]} in week 1 and {pshares[4]} in week 5.", META["imageAlt"])
# chart text
assert round(bc[0][2] / bc[0][1] * 5) == 4
need("Four in five wallets of the first four beta cohorts spent again the next week", SVG)
need(f"{len(beta)} wallets, {bc[3][1]} observed in week 4", SVG)
need(f">{len(pre)} wallets</text>", SVG)
for k, e, n in bc + pcv:
    need(f"<title>Week {k}, {n} of {e} wallets, {n / e:.1%}</title>", SVG)
need("Two lines. Wallets that first spent from August 31 to September 27, " + str(len(beta)) + " in all, " +
     ", ".join(f"{n / e:.0%} in week {k} of {e} observed" for k, e, n in bc) + ". Wallets that first spent from June 4 to "
     f"August 30, {len(pre)} in all, " + ", ".join(f"{n / e:.0%} in week {k}" for k, e, n in pcv) + ".", SVG)

# ---------------------------------------------------------------- before the beta week, by month of first spend
tot = [0, 0, 0, 0]
lastshare = {}
for label, a, b in (("June", date(2026, 6, 1), date(2026, 6, 30)), ("July", date(2026, 7, 1), date(2026, 7, 31)),
                    ("August 1 to 30", date(2026, 8, 1), date(2026, 8, 30))):
    ws = [w for w in pre if a.toordinal() <= firstday[w] <= b.toordinal()]
    sep = sum(1 for w in ws if any(date(2026, 9, 1).toordinal() <= o <= date(2026, 9, 30).toordinal() for o in spend[w]))
    lw = sum(1 for w in ws if LAST in wkset[w])
    one = sum(1 for w in ws if len(spend[w]) == 1)
    need(f"| {label} | {len(ws)} | {sep} | {lw} | {one} |")
    for i, v in enumerate((len(ws), sep, lw, one)):
        tot[i] += v
    lastshare[label] = (lw, len(ws))
assert tot[0] == len(pre)
need(f"| June 4 to August 30 | {tot[0]} | {tot[1]} | {tot[2]} | {tot[3]} |")
assert max(lastshare, key=lambda x: lastshare[x][0] / lastshare[x][1]) == "July"
need(f"Of the three months, July's wallets kept spending most, with {lastshare['July'][0]} of {lastshare['July'][1]} spending in "
     "the week to October 4.")
need(f"Taken together, the pre-beta wallets' shares were {pshares[0]}, {pshares[1]}, {pshares[2]}, {pshares[3]} and {pshares[4]} "
     "in the five weeks after their first spend.")
c0s = [sum(later(w, k) for w in c0) / len(c0) for k in range(1, 5)]
assert all(pcv[k][2] / pcv[k][1] < c0s[k] for k in range(4))       # they trailed in each of the four weeks
need("Week for week, the cohort of the beta week alone had shares of " + ", ".join(f"{x:.0%}" for x in c0s[:3]) +
     f" and {c0s[3]:.0%}.")
need(f"With {len(pre)} wallets against {len(beta)}, the pre-beta shares carry more chance variation, but they trailed in each of "
     "the four weeks.")
need("Counted spend events began on June 4, three months before the beta")
assert meta["first_spend_event"].startswith("2026-06-04") and min(firstday.values()) == date(2026, 6, 4).toordinal()

# ---------------------------------------------------------------- no spend event in the last two weeks
pre_set = set(pre)
lp = sum(1 for w in lapsed if w in pre_set)
first3 = [w for w in early if w not in pre_set]
assert len(first3) == sum(1 for w in fw if BETA <= fw[w] <= BETA + 14)
need(f"Of the {len(early)} wallets whose first spend came before September 21, {len(lapsed)}, or "
     f"{len(lapsed) / len(early):.0%}, had no spend event from September 21 to October 4. They were {lp} of the {len(pre)} pre-beta "
     f"wallets, {lp / len(pre):.0%}, and {len(lapsed) - lp} of the {len(first3)} wallets of the first three beta cohorts, "
     f"{(len(lapsed) - lp) / len(first3):.0%}.")
oneday = sum(1 for w in lapsed if len(spend[w]) == 1)
back5 = sum(1 for w in lapsed if w in oct5)
need(f"Of the {len(lapsed)}, {oneday} had spent on only one day to October 4, and {WORDS[back5]} spent again on October 5, the "
     "day after the last full week.")
ten = sum(1 for w in lapsed if bal.get(w, 0) >= 10 * 10 ** 18)
hundred = sum(1 for w in lapsed if bal.get(w, 0) >= 100 * 10 ** 18)
still = [w for w in early if w not in lapsed]
still1 = sum(1 for w in still if bal.get(w, 0) >= 10 ** 18)
need(f"At the last balance snapshot, 15:53 UTC on October 5, {one_usde} of the {len(lapsed)} held at least 1 USDe, {ten} held 10 "
     f"USDe or more and {hundred} held 100 USDe or more. Of the {len(still)} that did spend in those two weeks, {still1} held at "
     "least 1 USDe.")
quiet = [w for w in pre if not any(date(2026, 9, 1).toordinal() <= o <= CUT.toordinal() for o in spend[w])]
quiet1 = sum(1 for w in quiet if bal.get(w, 0) >= 10 ** 18)
need(f"Over a longer window, {len(quiet)} of the {len(pre)} pre-beta wallets, or {len(quiet) / len(pre):.0%}, had no spend event "
     f"from September 1 to October 4, against {lp} in the two weeks to October 4, and {quiet1} of the {len(quiet)} held at least 1 "
     "USDe.")

# ---------------------------------------------------------------- method, limits and reproduction
roles = {x["role"]: x["spend_events"] for x in meta["settlement_addresses"]}
assert roles["current"] + roles["retired"] == total_events
need(f"Of its {total_events:,} spend events, {roles['current']:,} went to the current address and {roles['retired']:,} to the "
     "retired one.")
pub = list(csv.DictReader(open(INP / "adoption_review_weeks_wallets.csv")))
assert len(pub) == 10 and pub[0]["first_day"] == "2026-07-27" and pub[-1]["last_day"] == "2026-10-04"
for r in pub:
    m = date.fromisoformat(r["first_day"]).toordinal()
    assert sum(1 for w in wkset if m in wkset[w]) == int(r["spending_wallets"])
    assert sum(n for o, n in ev_day.items() if m <= o <= m + 6) == int(r["spend_events"])
need("reproduce that review's published table for all ten weeks from July 27 to October 4, and their monthly counts reproduce "
     "the monthly table in that review's calculation files, from June to October 4.")
pubm = {r["period"]: r for r in csv.DictReader(open(INP / "adoption_review_months_wallets.csv"))}
PER = [("June 2026", date(2026, 6, 1), date(2026, 6, 30)), ("July 2026", date(2026, 7, 1), date(2026, 7, 31)),
       ("August 2026", date(2026, 8, 1), date(2026, 8, 31)), ("September 2026", date(2026, 9, 1), date(2026, 9, 30)),
       ("October 1 to 4, 2026", date(2026, 10, 1), CUT)]
assert len(pubm) == len(PER)
for label, a, b in PER:
    A, B = a.toordinal(), b.toordinal()
    sw = [w for w in spend if any(A <= o <= B for o in spend[w])]
    mine = (len(sw), sum(1 for w in sw if A <= firstday[w] <= B), sum(1 for w in sw if firstday[w] < A),
            sum(n for o, n in ev_day.items() if A <= o <= B))
    r = pubm[label]
    assert mine == (int(r["spending_wallets"]), int(r["first_ever_spend_in_period"]), int(r["spent_in_an_earlier_period"]),
                    int(r["spend_events"])), label
aug_1_30 = sum(1 for w in pre if date(2026, 8, 1).toordinal() <= firstday[w] <= date(2026, 8, 30).toordinal())
aug_pub = int(pubm["August 2026"]["first_ever_spend_in_period"])
assert aug_pub - aug_1_30 == sum(1 for w in firstday if firstday[w] == BETA)
need(f"so its August row holds {aug_1_30} wallets against that review's {aug_pub} first spends in August.")
latest = [w for w in fw if fw[w] == LAST]
need(f"the latest cohort, {len(latest)} wallets, has none.")
d1 = meta["other_destinations"]["destinations"][0]
assert d1["destination"] == "destination 1" and not d1["destination_is_programme_wallet"]
assert d1["first"][:10] == "2026-05-15" and d1["last"][:10] == "2026-06-10"
need(f"The adoption review found {d1['events_from_programme_wallets']} AllowanceSpent events in USDe from {d1['programme_wallets']} "
     "wallets to one unidentified address from May 15 to June 10, a span that starts before the first counted spend event on "
     "June 4. If that address was an earlier settlement address, "
     f"{WORDS[d1['of_which_never_spent_to_a_settlement_address']]} more wallets would count as having spent before the beta week.")
# weekends from September 5 to October 4 against the Fridays before and the Mondays after them
wkend = [o for o in range(date(2026, 9, 5).toordinal(), CUT.toordinal() + 1) if date.fromordinal(o).weekday() >= 5]
around = sorted({o - 1 for o in wkend if date.fromordinal(o).weekday() == 5} | {o + 1 for o in wkend if date.fromordinal(o).weekday() == 6})
assert len(wkend) == 10 and len(around) == 10
assert sum(ev_all[o] for o in wkend) / 10 > sum(ev_all[o] for o in around) / 10   # 770.2 against 705.8
need("On the weekends from September 5 to October 4 they ran above the level of the Fridays and Mondays around them")
need(f"all {total_events:,} spend events and {len(all_w)} spending wallets in the recount's summary")
need(f"= {k4} ÷ {len(c0)} = {100 * k4 / len(c0):.1f}% for the week of August 31, four weeks on")

print(f"{found} phrases found")
if missing:
    print("MISSING:")
    for m in missing:
        print("  " + m)
    sys.exit(1)
