#!/usr/bin/env python3
"""
Recomputes every computed figure in article_draft.md with code written separately from
ethenapay_adoption_review.py and confirms that the exact phrase appears in the draft.
Exits with an error if any phrase is missing, so rerun it after any edit to the text.

Run from this folder:  python3 check_article_numbers.py

Figures quoted from outside sources (Ethena's posts, its FAQ, press reports, Paymentscan) are not
recomputed here. They are listed with their sources in evidence_table.md.
"""
import bisect
import csv
import datetime as dt
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent
TEXT = (HERE / "article_draft.md").read_text(encoding="utf-8")
LINES = TEXT.split("\n")
INP = HERE / "inputs"
CH = INP / "chain"
checks, missing = [], []


def need(phrase):
    checks.append(phrase)
    if phrase not in TEXT:
        missing.append(phrase)


def row_ends(prefix, tail):
    """A table row that starts with `prefix` must end with `tail`."""
    checks.append(prefix + " ... " + tail)
    hit = [l for l in LINES if l.startswith(prefix)]
    if len(hit) != 1 or not hit[0].endswith(tail):
        missing.append(prefix + " ... " + tail)


def pct(x, nd=1):
    return f"{x * 100:.{nd}f}%"


# ------------------------------------------------------------------ inputs
dune = {}
for m in csv.DictReader(open(INP / "manifest.csv")):
    if m["repo"] == "QorbQuant/EthenaDAT":
        dune[m["commit"][:7]] = json.load(open(INP / m["file"]))
order = sorted(dune, key=lambda k: dune[k]["generated_at"])
assert len(order) == 9
last = dune[order[-1]]
hl = last["headline"]
ser = last["series"]

EPOCH = dt.datetime(2026, 5, 15, tzinfo=dt.timezone.utc)
num = lambda iso: (dt.date.fromisoformat(iso) - dt.date(2026, 5, 15)).days
day_of = lambda t: (dt.datetime.fromtimestamp(t, dt.timezone.utc) - EPOCH).days
name = lambda d: (dt.date(2026, 5, 15) + dt.timedelta(days=d)).strftime("%b %-d")
iso_day = lambda d: (dt.date(2026, 5, 15) + dt.timedelta(days=d)).isoformat()
stamp = lambda iso: int(dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())
WEI = 10 ** 18
u = lambda wei: int(wei) / WEI

wallet_rows = list(csv.DictReader(open(CH / "wallets_created.csv")))
born = [int(r["created_ts"]) for r in wallet_rows]
maker = [r["factory"] for r in wallet_rows]
events = [dict(day=int(r["day"]), seg=int(r["segment"]), w=int(r["wallet"]), n=int(r["events"]), c=int(r["cents"])) for r in csv.DictReader(open(CH / "spend_wallet_days.csv"))]
active = {int(r["wallet"]): r for r in csv.DictReader(open(CH / "wallet_activity.csv"))}
chain_days = list(csv.DictReader(open(CH / "daily_chain.csv")))
cd = {r["date"]: r for r in chain_days}
csnap = json.load(open(CH / "snapshots_chain.json"))
meta = json.load(open(CH / "meta.json"))
cut = csnap[-1]
T, B = cut["cut_ts"], cut["cut_block"]
assert cut["cut_time"] == "2026-10-05T15:53:28Z" and meta["balance_check"]["block"] == B
need("Chain data through 15:53 UTC on October 5, 2026")

# ------------------------------------------------------------------ lead
n_created = sum(t <= T for t in born)
got = {w for w, r in active.items() if r["first_usde_in_ts"] and int(r["first_usde_in_ts"]) <= T}
assert all(born[w] <= T for w in got)                                             # every wallet counted as funded existed at the cutoff
bal = {w: int(r["balance_wei_at_last_snapshot"]) for w, r in active.items() if int(r["balance_wei_at_last_snapshot"]) > 0}
at_cut = [e for e in events if e["seg"] <= 8]
spent = {e["w"] for e in at_cut}
oct4 = num("2026-10-04")
week = lambda end: {e["w"] for e in events if end - 6 <= e["day"] <= end}
need(f"In the seven full days to October 4, 2026, {len(week(oct4))} distinct EthenaPay wallets had at least one card spend event.")
need(f"By 15:53 UTC on October 5, the cutoff of this review, {len(spent)} wallets had ever spent and {len(got):,} had ever received USDe, out of {n_created:,} created.")
need(f"The other {n_created - len(got):,}, or {pct((n_created - len(got)) / n_created)} of those created, had never received USDe.")
# a wallet counts as having received USDe from the later of its first inbound transfer and its deployment
first_in = sorted(max(int(r["first_usde_in_ts"]), born[w]) for w, r in active.items() if r["first_usde_in_ts"])
first_sp = sorted(int(r["first_spend_ts"]) for r in active.values() if r["first_spend_ts"])
at = lambda iso: (bisect.bisect_right(born, stamp(iso)), bisect.bisect_right(first_in, stamp(iso)), bisect.bisect_right(first_sp, stamp(iso)))
POSTS = [("Sep 1, 11:59", "2026-09-01T11:59:55Z"), ("Sep 10, 07:49", "2026-09-10T07:49:38Z"), ("Sep 25, 14:34", "2026-09-25T14:34:45Z"),
         ("Sep 28, 17:32", "2026-09-28T17:32:05Z"), ("Oct 5, 15:53, the cutoff", cut["cut_time"])]
sep25 = at("2026-09-25T14:34:45Z")
need(f"said 1,600 people had the app, at a moment when {sep25[0]:,} wallets existed")
assert 7.5 < sep25[0] / 1600 < 8.5                                                # "about eight to one" and "about an eighth"
need("created wallets outnumbered people with the app by about eight to one")
tot = defaultdict(lambda: [0, 0])
for e in at_cut:
    tot[e["w"]][0] += e["n"]
    tot[e["w"]][1] += e["c"]
EV, CENTS = sum(v[0] for v in tot.values()), sum(v[1] for v in tot.values())
assert EV == hl["lifetime_spend_count"] and abs(CENTS / 100 - hl["lifetime_spend_usde"]) < 0.006
rank_u = sorted(tot.values(), key=lambda v: -v[1])
rank_e = sorted(tot.values(), key=lambda v: -v[0])
run_, k = 0, 0
while run_ * 2 < CENTS:
    run_ += rank_u[k][1]
    k += 1
lastb = cut["balances_at_cut_block"]
need(f"Half of the USDe spent came from {k} wallets, and the ten largest balances held {pct(int(lastb['top10_wei']) / int(lastb['held_wei']))} of the USDe in EthenaPay wallets at the cutoff.")

# ------------------------------------------------------------------ seven-day periods
periods = [(oct4 - 7 * j - 6, oct4 - 7 * j) for j in range(8, -1, -1)]
prev = week(periods[0][0] - 1)
rows, back = [], []
for a, b in periods:
    ws = week(b)
    ev = sum(e["n"] for e in events if a <= e["day"] <= b)
    rows.append((a, b, ws, len(ws & prev), ev))
    need(f"| {name(a)} to {name(b)} | {len(ws)} | {len(ws & prev)} | {len(ws) - len(ws & prev)} | {ev:,} |")
    back.append(len(ws & prev) / len(prev))
    prev = ws
before, base, latest = rows[3], rows[4], rows[-1]
assert name(before[1]) == "Aug 30" and name(base[0]) == "Aug 31" and name(base[1]) == "Sep 6" and base[0] + 1 == num("2026-09-01")
need(f"In the seven days to October 4, {len(latest[2])} distinct wallets had a spend event. Four weeks earlier the figure was {len(base[2])}, and in the last full seven-day period before the beta it was {len(before[2])}.")
need("The week of August 31 to September 6 holds the day the beta opened and one day before it.")
assert meta["first_spend_event"].startswith("2026-06-04")
need("Counted spend events began on June 4, three months before the beta")
need(f"Spending wallets rose by a factor of {len(latest[2]) / len(base[2]):.2f} over those four weeks. Spend events rose by a factor of {latest[4] / base[4]:.2f}, from {base[4]:,} to {latest[4]:,}.")
assert 2.75 < len(latest[2]) / len(base[2]) < 3.0                                # the heading says nearly tripled
from_new = sum(e["n"] for e in events if latest[0] <= e["day"] <= latest[1] and e["w"] not in base[2])
assert 0.65 < from_new / latest[4] < 0.68                                         # "two thirds"
need(f"Two thirds of the latest period's events, {from_new:,} of {latest[4]:,}, came from wallets with no spend event in the week of August 31 to September 6.")
need(f"In each of the last five seven-day periods, between {min(back[-5:]) * 100:.1f}% and {max(back[-5:]) * 100:.1f}% of the previous period's spending wallets spent again.")
need(f"The count rises from {len(rows[0][2])} to {len(rows[-1][2])}.")
dser = dict(zip(ser["date"], ser["spend_count"]))
for a, b, _, _, ev in rows:                                                       # the dashboard's own series gives the same event totals
    assert ev == sum(dser.get(iso_day(d), 0) for d in range(a, b + 1))

# ------------------------------------------------------------------ months
seen, earlier = set(), None
mon = {}
for label, a, b in (("June 2026", "2026-06-01", "2026-06-30"), ("July 2026", "2026-07-01", "2026-07-31"), ("August 2026", "2026-08-01", "2026-08-31"), ("September 2026", "2026-09-01", "2026-09-30")):
    sel = [e for e in events if num(a) <= e["day"] <= num(b)]
    ws = {e["w"] for e in sel}
    ev = sum(e["n"] for e in sel)
    again = "no earlier month" if earlier is None else f"{len(ws & earlier)} of {len(earlier)}"
    need(f"| {label} | {len(ws)} | {len(ws - seen)} | {again} | {ev:,} |")
    mon[label] = dict(ws=ws, ev=ev, usde=sum(e["c"] for e in sel) / 100, days=Counter(w for w, d in {(e["w"], e["day"]) for e in sel}),
                      new=ws - seen, again=ws & earlier if earlier is not None else set(), tx=sum(int(r["spend_transactions"]) for r in chain_days if a <= r["date"] <= b))
    seen |= ws
    earlier = ws
ju, au, se = mon["July 2026"], mon["August 2026"], mon["September 2026"]
assert len(se["ws"]) / len(au["ws"]) > se["ev"] / au["ev"]
need("By calendar month spending wallets grew faster than spend events.")
need(f"September's {len(se['ws'])} spending wallets were {len(se['ws']) / len(au['ws']):.1f} times August's {len(au['ws'])}. Spend events were {se['ev'] / au['ev']:.1f} times August's and spend in USDe {se['usde'] / au['usde']:.1f} times.")
assert len(se["ws"]) - len(se["new"]) - len(se["again"]) == 2
need("Two of September's wallets had last spent before August")
dcount = se["days"]
need(f"In September {sum(v >= 15 for v in dcount.values())} wallets spent on fifteen or more days and {sum(v >= 6 for v in dcount.values())} on six or more, while {sum(v == 1 for v in dcount.values())} spent on a single day.")
daily_sum = sum(v for d, v in zip(ser["date"], ser["active_wallets"]) if d.startswith("2026-09"))
assert 8.5 < daily_sum / len(se["ws"]) < 9.5                                      # "about nine times"
need(f"The dashboard's daily spending wallets for September add up to {daily_sum:,.0f}, about nine times the month's {len(se['ws'])} distinct wallets")
octw = {e["w"] for e in events if num("2026-10-01") <= e["day"] <= oct4}
need(f"The four full days of October 1 to 4 had {len(octw)} distinct wallets")

# ------------------------------------------------------------------ participation table
run = num(last["generated_at"][:10])
in30 = {e["w"] for e in at_cut if e["day"] >= run - 30}
in7 = {e["w"] for e in at_cut if e["day"] >= run - 7}
one_plus = sum(v >= WEI for v in bal.values())
need(f"One wallet had received USDe for every {n_created / len(got):.1f} created.")
assert round(n_created / len(got)) == 13                                          # the heading says one wallet in thirteen
need(f"| Wallets created | {hl['wallets_created']:,.0f} | {n_created:,} | 100% |")
need(f"| Ever received USDe | not shown | {len(got):,} | {pct(len(got) / n_created)} |")
need(f"| Funded wallets, holding more than zero | {hl['funded_wallets']:,.0f} | {len(bal):,} | {pct(len(bal) / n_created)} |")
need(f"| Holding 1 USDe or more | not shown | {one_plus} | {pct(one_plus / n_created)} |")
need(f"| Ever spent | {hl['spending_wallets']:.0f} | {len(spent)} | {pct(len(spent) / n_created)} |")
need(f"| Active wallets / 30d, including the partial run day | {hl['mau_30d']:.0f} | {len(in30)} | {pct(len(in30) / n_created)} |")
need(f"| Active wallets / 7d, including the partial run day | {hl['wau_7d']:.0f} | {len(in7)} | {pct(len(in7) / n_created)} |")
under1 = sum(v < WEI for v in bal.values())
under_cent = sum(v < WEI // 100 for v in bal.values())
need(f"Of the {len(bal):,} funded wallets, {under1} held less than 1 USDe and {under_cent} of those held less than a cent. The other {one_plus} held at least 1 USDe.")
assert 0.73 < len(spent) / len(got) < 0.77 and spent <= got                       # "three in four"
need(f"Three in four wallets that received USDe had at least one spend event, {len(spent)} of {len(got):,}.")
lag = [(int(active[w]["first_spend_ts"]) - int(active[w]["first_usde_in_ts"])) / 86400 for w in spent]
single = sum(v[0] == 1 for v in tot.values())
need(f"Of those {len(spent)}, {sum(x < 1 for x in lag)} spent within a day of their first USDe arriving and {sum(x < 7 for x in lag)} within a week. One event is a low bar, and {single} of the {len(spent)} had a single event in their lifetime.")
full_week = week(oct4)
assert full_week <= in7 and all(any(e["w"] == w and e["day"] == run for e in at_cut) for w in in7 - full_week)
need(f"That is why the 7-day figure was {len(in7)} and the full-week figure was {len(full_week)}. The {len(in7 - full_week)} extra wallets spent on October 5 before the cutoff and on none of the seven days before.")
assert hl["wallets_created"] - n_created == 1 and hl["funded_wallets"] - len(bal) == 2
need("The dashboard showed one more wallet created and two more funded wallets than the recount.")

# ------------------------------------------------------------------ creation and access
bday = [day_of(t) for t in born]
per_day = Counter(bday)
end_aug = sum(d <= num("2026-08-31") for d in bday)
may = sum(d <= num("2026-05-31") for d in bday)
assert all(maker[i] == "0" for i, d in enumerate(bday) if d <= num("2026-05-31"))  # every May wallet came from the first factory
need(f"At the end of August {end_aug:,} wallets existed. Of those, {may:,} date from May 15 to 31, before the first counted spend event on June 4, and the first factory deployed {per_day[num('2026-05-15')]} of them on May 15 alone. June, July and August added {end_aug - may}.")
h11, noon, h13, midnight = (stamp(f"2026-09-01T{h}:00:00Z") for h in ("11", "12", "13", "23"))
midnight += 3600
before_post, after_post = sum(h11 <= t < noon for t in born), sum(noon <= t < h13 for t in born)
assert noon - 10 < stamp("2026-09-01T11:59:55Z") < noon                           # the thread was posted in the last seconds before 12:00
need(f"The chain shows {before_post} new wallets from 11:00 to 12:00 UTC that day, the hour before the thread, and {after_post} from 12:00 to 13:00.")
after_noon = sum(noon <= t < midnight for t in born)
assert 9.5 <= after_noon / 400 <= 10.5                                            # "about ten times"
need(f"From 12:00 UTC to the end of the day it shows {after_noon:,}, about ten times the size of that first group.")
sep12 = per_day[num("2026-09-01")] + per_day[num("2026-09-02")]
need(f"September 1 and 2 together produced {sep12:,} wallets, {pct(sep12 / n_created)} of all wallets created by the cutoff.")
for label, iso in POSTS:
    c, r, s = at(iso)
    row_ends(f"| {label} |", f"| {c:,} | {r:,} | {s} |")
assert at(cut["cut_time"]) == (n_created, len(got), len(spent))
assert 1.8 < 1600 / sep25[1] < 2.0                                                # "nearly twice"
need("Ethena's 1,600 was about an eighth of the wallets that existed at that minute and nearly twice the number that had received USDe.")
spend_to = lambda d: sum(int(r["spend_cents"]) for r in chain_days if r["date"] <= d) / 100
assert 1_500_000 <= spend_to("2026-09-24") < 1_600_000
need(f"Lifetime card spend on the chain was {spend_to('2026-09-24'):,.0f} USDe at the end of September 24")
coh = {}
for label, a, b in (("May 15 to 31", "2026-05-15", "2026-05-31"), ("June 1 to August 31", "2026-06-01", "2026-08-31"), ("September 1 and 2", "2026-09-01", "2026-09-02"),
                    ("September 3 to 30", "2026-09-03", "2026-09-30"), ("October 1 to the cutoff", "2026-10-01", "2026-10-05")):
    ids = [i for i, d in enumerate(bday) if num(a) <= d <= num(b) and born[i] <= T]
    r, s = sum(i in got for i in ids), sum(i in spent for i in ids)
    coh[label] = (len(ids), r, s)
    need(f"| {label} | {len(ids):,} | {r} | {pct(r / len(ids))} | {s} | {pct(s / len(ids))} |")
assert sum(v[0] for v in coh.values()) == n_created and sum(v[1] for v in coh.values()) == len(got) and sum(v[2] for v in coh.values()) == len(spent)
sql_file = INP / "06_kpi_headline_eb01f5d.sql"                                    # reference material; checked when it is present
sql = sql_file.read_text().lower() if sql_file.exists() else None
assert sql is None or "v1 pilot factory" in sql
rest_c, rest_r = n_created - coh["May 15 to 31"][0], len(got) - coh["May 15 to 31"][1]
need(f"Without them, {rest_r:,} of {rest_c:,} wallets had received USDe, or {pct(rest_r / rest_c)}.")


def within14(a, b):
    ids = [i for i, d in enumerate(bday) if num(a) <= d <= num(b)]
    assert all(born[i] + 14 * 86400 <= T for i in ids)                            # every wallet has had its 14 days
    hit = sum(1 for i in ids if i in active and active[i]["first_usde_in_ts"] and int(active[i]["first_usde_in_ts"]) - born[i] <= 14 * 86400)
    return hit, len(ids)


k12, n12 = within14("2026-09-01", "2026-09-02")
got12 = coh["September 1 and 2"][1]
need(f"Of the {got12} wallets from September 1 and 2 that had received USDe by the cutoff, {k12} received it within 14 days of creation and {got12 - k12} later.")
km, nm = within14("2026-05-15", "2026-05-31")
kj, nj = within14("2026-06-01", "2026-08-31")
k3, n3 = within14("2026-09-03", "2026-09-20")
need(f"On that basis {pct(km / nm)} of the May wallets received USDe, {pct(kj / nj)} of those created from June to August, {pct(k12 / n12)} of those from September 1 and 2 and {pct(k3 / n3)} of those from September 3 to 20.")

# ------------------------------------------------------------------ spend by wallet
assert rank_u[0][0] == 6
need(f"Lifetime spend at the cutoff was {CENTS / 100:,.0f} USDe across {EV:,} events and {len(tot)} wallets. Ten wallets accounted for {pct(sum(v[1] for v in rank_u[:10]) / CENTS)} of the USDe with {pct(sum(v[0] for v in rank_u[:10]) / EV)} of the events."
     f" Half of the USDe came from {k} wallets, {pct(k / len(tot))} of those that had spent. The largest spender by USDe had six events.")
need(f"The ten wallets with the most events held {pct(sum(v[0] for v in rank_e[:10]) / EV)} of them. The hundred with the most held {pct(sum(v[0] for v in rank_e[:100]) / EV)}, against {pct(sum(v[1] for v in rank_u[:100]) / CENTS)} of the USDe for the hundred largest spenders.")
few = [w for w, v in tot.items() if v[0] <= 5]
many = sum(v[0] > 20 for v in tot.values())
fresh = sum(1 for w in few if int(active[w]["first_spend_ts"]) >= T - 14 * 86400)
need(f"At the cutoff {len(few)} of the {len(tot)} wallets, {pct(len(few) / len(tot))}, had five or fewer events in their lifetime, and {many}, or {pct(many / len(tot))}, had more than twenty. Of those {len(few)}, {fresh} first spent in the 14 days before the cutoff")

# ------------------------------------------------------------------ balances at week ends
ends = [iso_day(b) for a, b in periods[-6:]]
wk = []
for d in ends:
    r = cd[d]
    h, t10 = int(r["held_wei"]), int(r["top10_wei"])
    wk.append((d, h, t10, int(r["funded"])))
    day = dt.date.fromisoformat(d)
    need(f"| {day:%b} {day.day} | {u(h):,.0f} | {u(t10):,.0f} | {u(h - t10):,.0f} | {pct(t10 / h)} | {int(r['funded']):,} |")
    i = ser["date"].index(d)
    assert abs(ser["tvl_usde"][i] - u(h)) < 0.01                                  # the dashboard's daily series holds the same USDe held
assert all(b[1] - b[2] > a[1] - a[2] for a, b in zip(wk, wk[1:]))               # all other wallets grew at every week end (the heading)
through_oct4 = [r for r in chain_days if r["date"] <= "2026-10-04"]
peak = max(through_oct4, key=lambda r: int(r["top10_wei"]))
assert peak["date"] == "2026-09-12" and wk[0][2] < int(peak["top10_wei"]) > wk[-1][2]      # rose and fell (the heading)
need(f"The ten largest balances summed to {u(wk[0][2]):,.0f} USDe at the end of August 30, the last day of the last full week before the beta. Their highest day-end sum was {u(peak['top10_wei']):,.0f} on September 12, and they stood at {u(wk[-1][2]):,.0f} on October 4.")
off_by = [round(u(h)) - round(u(t10)) - round(u(h - t10)) for _, h, t10, _ in wk]
assert all(abs(x) <= 1 for x in off_by) and any(off_by)                           # the rounded columns can miss the rounded total by 1
need("Rounding can leave the two middle columns 1 USDe apart from the total.")
assert [name(b) for a, b in periods[-6:]] == [f"{dt.date.fromisoformat(d):%b} {dt.date.fromisoformat(d).day}" for d in ends]
need("Each day is the last of a seven-day period in the spending table.")
need(f"They rose from {u(wk[0][1] - wk[0][2]):,.0f} to {u(wk[-1][1] - wk[-1][2]):,.0f} USDe while funded wallets rose from {wk[0][3]} to {wk[-1][3]:,}.")
cross = next(r["date"] for r in chain_days if r["date"] >= "2026-06-01" and int(r["held_wei"]) > 0 and int(r["held_wei"]) - int(r["top10_wei"]) > int(r["top10_wei"]))
assert cross == "2026-09-22"
need("September 22 was the first day that ended with the other wallets holding more than the ten largest.")
need(f"At the cutoff the ten largest held {u(lastb['top10_wei']):,.0f} USDe, {pct(int(lastb['top10_wei']) / int(lastb['held_wei']))} of the {u(lastb['held_wei']):,.0f} in EthenaPay wallets.")
assert abs(u(lastb["held_wei"]) - hl["tvl_usde"]) < 0.01 and abs(int(lastb["top10_wei"]) / int(lastb["held_wei"]) - hl["top10_balance_share"]) < 0.0002

# ------------------------------------------------------------------ the two wallets
first = csnap[0]["balances_at_cut_block"]
two = [(w, int(x)) for w, x in first["top20"][:10] if int(x) > 900_000 * WEI]
assert len(two) == 2 and all(0.99e6 < x / WEI < 1.01e6 for _, x in two) and csnap[0]["generated"].startswith("2026-09-11")
two_then, two_now = sum(x for _, x in two), sum(bal.get(w, 0) for w, _ in two)
rise = int(peak["top10_wei"]) - wk[0][2]
fall = int(peak["top10_wei"]) - wk[-1][2]
# one of the two did not exist on August 30 and the other held at most that day's largest balance, so their share of the rise is bounded
assert ends[0] == "2026-08-30" and sum(born[w] > stamp("2026-08-31T00:00:00Z") for w, _ in two) == 1
share_lo, share_hi = (two_then - int(cd[ends[0]]["top1_wei"])) / rise, two_then / rise
assert 0.66 < share_lo < share_hi < 0.73 and two_then - two_now > fall                              # most of the rise, and more than the whole fall
need("Two wallets accounted for most of the rise in the ten largest balances and for the fall that followed.")
need(f"At the dashboard snapshot of September 11 each held about 1.0 million USDe, {u(two_then):,.0f} between them.")


def seen_at(w, i):
    hit = [int(x) for w_, x in csnap[i]["balances_at_cut_block"]["top20"] if w_ == w]
    return hit[0] if hit else None


assert [c["generated"][:10] for c in csnap[:5]] == ["2026-09-11", "2026-09-14", "2026-09-17", "2026-09-21", "2026-09-22"]
early = next(w for w, _ in two if seen_at(w, 2) is not None and seen_at(w, 2) < 100_000 * WEI)     # the one that had fallen by September 17
late = next(w for w, _ in two if w != early)
assert seen_at(late, 4) is None
need(f"One fell from {u(seen_at(early, 1)):,.0f} USDe at the September 14 snapshot to {u(seen_at(early, 2)):,.0f} at the September 17 snapshot. The other held {u(seen_at(late, 3)):,.0f} on September 21 and was outside the twenty largest balances a day later.")
wd_days = sorted((d for d in ser["date"] if d <= "2026-10-04"), key=lambda d: -ser["withdrawals_usde"][ser["date"].index(d)])[:3]
assert sorted(wd_days) == ["2026-09-15", "2026-09-16", "2026-09-22"]
need("The dashboard series through October 4 showed its three largest days of withdrawals on September 15, 16 and 22")
assert all(w in tot for w, _ in two)
need(f"At the cutoff the two wallets held {u(two_now):,.0f} USDe between them, and both had spend events.")

# ------------------------------------------------------------------ balances at the cutoff
held = sum(bal.values())
assert held == int(lastb["held_wei"]) == int(meta["balance_check"]["sum_wei"])
fmt = lambda x: f"{x:,.2f}" if x < 1 else f"{x:,.0f}"
shares = []
for label, lo_, hi_ in (("Under 0.01", 0, 0.01), ("0.01 to under 1", 0.01, 1), ("1 to under 10", 1, 10), ("10 to under 100", 10, 100), ("100 to under 1,000", 100, 1000),
                        ("1,000 to under 10,000", 1000, 10000), ("10,000 to under 100,000", 10000, 100000), ("100,000 and over", 100000, 10 ** 12)):
    sel = [v for v in bal.values() if int(lo_ * 100) * WEI // 100 <= v < int(hi_ * 100) * WEI // 100]
    need(f"| {label} | {len(sel)} | {fmt(sum(sel) / WEI)} | {pct(sum(sel) / held, 2)} |")
    shares.append(round(sum(sel) / held * 100, 2))
assert f"{sum(shares):.2f}" == "100.01"
ranked = sorted(bal.values(), reverse=True)
n10k = sum(v >= 10000 * WEI for v in ranked)
n1k = sum(v >= 1000 * WEI for v in ranked)
need(f"At the cutoff {n10k} wallets with 10,000 USDe or more held {pct(sum(ranked[:n10k]) / held)} of all USDe in EthenaPay wallets. The {len(ranked) - n1k} funded wallets below 1,000 USDe held {pct(sum(ranked[n1k:]) / held)}. The rounded shares in the table sum to 100.01%.")
by_bal = sorted(bal, key=lambda w: -bal[w])
by_spend = sorted(tot, key=lambda w: -tot[w][1])
place = {w: i + 1 for i, w in enumerate(by_spend)}
ten = by_bal[:10]
assert not set(ten) & set(by_spend[:10])
need("None of the ten largest balances belonged to one of the ten largest spenders.")
never10 = [w for w in ten if w not in tot]
low = sorted((w for w in ten if w in tot), key=lambda w: tot[w][1])[0]
assert len(never10) == 2 and tot[low][0] == 3
need("Two of the ten had never spent and a third had three spend events.")
assert sorted(place[w] for w in ten if w in tot)[:2] == [14, 15]
need(f"Two others ranked fourteenth and fifteenth of {len(tot)} wallets by USDe spent.")
sp10 = sum(tot[w][1] for w in ten if w in tot)
need(f"Together the ten had spent {sp10 / 100:,.0f} USDe, {pct(sp10 / CENTS)} of lifetime spend.")
overlap = len(set(by_bal[:100]) & set(by_spend[:100]))
big = [w for w in bal if bal[w] >= 1000 * WEI]
need(f"Of the hundred largest balances, {overlap} were also among the hundred largest spenders, and {sum(w in in7 for w in big)} of the {len(big)} wallets holding 1,000 USDe or more spent in the dashboard's 7-day window.")
idle = sorted((w for w in bal if w not in spent), key=lambda w: -bal[w])
need(f"Across all funded wallets, {len(idle)} had never spent. They held {u(sum(bal[w] for w in idle)):,.0f} USDe, {pct(sum(bal[w] for w in idle) / held)} of the total, and two wallets held {u(bal[idle[0]] + bal[idle[1]]):,.0f} of that.")

# ------------------------------------------------------------------ how this review checked the figures
first_g = dt.datetime.fromisoformat(dune[order[0]]["generated_at"])
g = dt.datetime.fromisoformat(last["generated_at"])
need(f"nine snapshots of that dataset, taken between {first_g:%B} {first_g.day} and {g:%B} {g.day}, {g.year}. Two are from October 5.")
assert sum(dune[k_]["generated_at"].startswith("2026-10-05") for k_ in order) == 2
need(f"Every chain figure on this page stops at the cutoff block, {B:,}, except the check of transfers against events in the next paragraph and the count of events sent to other destinations in the limits section.")
cent, off, lags, moved = 0, [], [], 0
for i, k_ in enumerate(order):
    h_ = dune[k_]["headline"]
    c = csnap[i]
    gap = u(c["balances_at_cut_block"]["held_wei"]) - h_["tvl_usde"]
    if abs(gap) < 0.006:
        cent += 1
    else:
        off.append((dune[k_]["generated_at"], abs(gap)))
    lags.append(c["seconds_before_generated"])
    moved += c["balances_at_cut_block"]["held_wei"] != c["balances_at_generated_time"]["held_wei"]
    assert c["wallets_ever_spent"] == h_["spending_wallets"] and c["wallets_spent_30d"] == h_["mau_30d"] and c["wallets_spent_7d"] == h_["wau_7d"]
    assert abs(int(c["spend_cents"]) / 100 - h_["lifetime_spend_usde"]) < 0.006 and c["spend_events"] == h_["lifetime_spend_count"]
    assert h_["funded_wallets"] - c["balances_at_cut_block"]["funded"] in (1, 2)
    assert c["balances_at_cut_block"]["float_funded"] - c["balances_at_cut_block"]["funded"] == 1          # the time-order replay adds one at every snapshot
    assert h_["wallets_created"] - c["wallets_created_at_cut_block"] in (1, 2)
assert cent == 8 and len(off) == 1 and off[0][0].startswith("2026-10-05T15:41")
need("the same lifetime spend to the cent, and the same USDe held to the cent at eight")
need(f"a gap of {off[0][1]:.2f} USDe in USDe held at the October 5 snapshot generated at 15:41 UTC")
assert 2 <= min(lags) / 60 < 3 and 26 < max(lags) / 60 <= 27 and moved == 7       # used in the appendix and the evidence table
need("At the cutoff the dashboard counted one more wallet created and two more funded wallets than the recount.")
need("replaying that sum adds one funded wallet at every snapshot")                # asserted for all nine in the loop above
assert hl["funded_wallets"] - cut["balances_at_cut_block"]["float_funded"] == 1                      # so one funded wallet stays unexplained at the cutoff
assert meta["wallet_to_settlement_transfers"] - meta["spend_events"] == 1 and int(meta["wallet_to_settlement_wei"]) - int(meta["spend_wei"]) == 5 * WEI
need(f"Through the end of October 5 the wallets sent {meta['wallet_to_settlement_transfers']:,} USDe transfers to the two settlement addresses, one more than the {meta['spend_events']:,} spend events, and the transfers summed to exactly 5 USDe more than the events.")
odd_days = [r["date"] for r in chain_days if int(r["card_spend_wei"]) != int(r["spend_cents"]) * 10 ** 16]
assert odd_days == ["2026-09-24"]                                                 # on every other day the daily sums are equal
full = [d for d in ser["date"] if d <= "2026-10-04"]
for d in full:
    i = ser["date"].index(d)
    c = cd[d]
    assert ser["spend_count"][i] == int(c["spend_events"]) and ser["active_wallets"][i] == int(c["spending_wallets"]) and abs(ser["spend_usde"][i] - int(c["spend_cents"]) / 100) < 0.006
    assert ser["new_wallets"][i] - int(c["new_wallets_v1"]) - int(c["new_wallets_v2"]) == (1 if d == "2026-05-15" else 0)
assert full[0] == "2026-05-15" and "2026-05-30" not in ser["date"] and int(cd["2026-05-30"]["spend_events"]) == 0 and int(cd["2026-05-30"]["new_wallets_v1"]) == 0
need(f"On each of the {len(full)} days in the dashboard's daily series from May 15 to October 4, spend events, daily spending wallets and spend in USDe were identical.")
bc = meta["balance_check"]
assert bc["mismatch_count"] == 0
need(f"The USDe contract's own balance for each of the {bc['wallets_checked']:,} wallets at the cutoff block equaled the balance built from transfers.")
# Paymentscan's figures are typed in as read on October 6, 2026 UTC. The recount's side of each comparison is computed here.
PS = dict(aug_addr=116, sep_addr=673, aug_tx=4002, sep_tx=17387, jul_addr=48, jul_kusd="62.94")
assert len(au["ws"]) == PS["aug_addr"] and len(se["ws"]) == PS["sep_addr"] and au["tx"] == PS["aug_tx"]
need(f"showed {PS['aug_addr']} and {PS['sep_addr']} active addresses for August and September when read on October 6, 2026 UTC, the same as this recount")
need(f"For August it showed {PS['aug_tx']:,} transactions, which equals the number of distinct transactions in this recount, against {au['ev']:,} spend events.")
assert se["tx"] - PS["sep_tx"] == 8
need(f"For September it showed {PS['sep_tx']:,} transactions, eight fewer than the {se['tx']:,} distinct transactions in this recount, and this review has not explained that gap.")
need(f"For July it showed {PS['jul_addr']} active addresses and {PS['jul_kusd']} thousand dollars of volume, against {len(ju['ws'])} wallets and {ju['usde']:,.2f} USDe here.")
sa = {x["role"]: x for x in meta["settlement_addresses"]}
assert sa["retired"]["spend_events"] == meta["spend_events_retired_settlement"] and sa["retired"]["last_spend_event"] < sa["current"]["first_spend_event"]
assert sa["current"]["first_spend_event"].startswith("2026-07-13") and sa["retired"]["last_spend_event"].startswith("2026-07-13")
need("The current settlement address received its first spend event on July 13, so a tracker that follows only that address misses everything before then.")
d13 = num("2026-07-13")
jul_days = defaultdict(set)
for e in events:
    if num("2026-07-01") <= e["day"] <= num("2026-07-31"):
        jul_days[e["w"]].add(e["day"])
only_before = sum(max(v) < d13 for v in jul_days.values())
cents_before = sum(e["c"] for e in events if e["day"] < d13)                      # every event before July 13 went to the retired address
jul_current = (sum(e["c"] for e in events if num("2026-07-01") <= e["day"] <= num("2026-07-31")) - sum(e["c"] for e in events if num("2026-07-01") <= e["day"] < d13)
               - (int(sa["retired"]["spend_cents"]) - cents_before)) / 100
# the remaining wallets all reached the current address: each spent after July 13, or first spent on July 13 after the retired address had stopped
retired_last = stamp(sa["retired"]["last_spend_event"])
reached = [w for w, v in jul_days.items() if max(v) > d13 or (max(v) == d13 and int(active[w]["first_spend_ts"]) > retired_last)]
assert only_before == 3 and len(reached) == len(jul_days) - only_before == PS["jul_addr"] and f"{jul_current / 1000:.2f}" == PS["jul_kusd"]
need(f"Three of the {len(jul_days)} wallets spent only before that day, which leaves {len(reached)}, and July spend to the current address was {jul_current:,.2f} USDe.")
beacon = [o for o in meta["other_factory_contracts"] if o["factory"] == "v1"]
assert len(beacon) == 1 and beacon[0]["time"].startswith("2026-05-15") and beacon[0]["time"] < meta["first_wallet_created"]
assert sql is None or (beacon[0]["address"] not in sql and "cast(t.value as double)" in sql and "balance_usde > 0" in sql)
need("a contract the first factory deployed on May 15 that was not a wallet and that the query's exclusion list did not name")

# ------------------------------------------------------------------ limits and reproduction
fu = meta["first_usde_received_at_last_snapshot"]
assert fu["wallets"] == len(got) and fu["from_another_programme_wallet"] == sum(1 for w in got if active[w]["first_in_kind"] == "i")
need(f"{fu['from_another_programme_wallet']} wallets received their first USDe from another EthenaPay wallet, {fu['first_funded_by_the_largest_such_sender']} of them from the same wallet")
od = meta["other_destinations"]
other_share = od["other_from_programme_wallets"] / (od["to_a_settlement_address"] + od["other_from_programme_wallets"])
end_of_day = stamp("2026-10-06T00:00:00Z")
assert 7.5 < (end_of_day - T) / 3600 < 8.5                                        # "eight hours past the cutoff"
need(f"Through the end of October 5, eight hours past the cutoff, another {od['other_from_programme_wallets']} AllowanceSpent events in USDe from EthenaPay wallets went to other destinations, {pct(other_share, 2)} of the total.")
to_w = [x for x in od["destinations"] if x["destination_is_programme_wallet"]]
other = [x for x in od["destinations"] if not x["destination_is_programme_wallet"]]
assert sum(x["events_from_programme_wallets"] for x in to_w) == 11 and len(to_w) == 7 and len(other) == 2
need("Eleven went to seven other EthenaPay wallets.")
a1, a2 = other
assert a1["first"].startswith("2026-05-15") and a1["last"].startswith("2026-06-10") and a1["first"] < meta["first_spend_event"]
need(f"Of the other {a1['events_from_programme_wallets'] + a2['events_from_programme_wallets']}, {a1['events_from_programme_wallets']} went to one address between May 15 and June 10, a span that starts before the first counted spend event, and {a2['events_from_programme_wallets']} went to a second address.")
assert od["of_which_never_spent_to_a_settlement_address"] == 8 and a1["of_which_never_spent_to_a_settlement_address"] == 7
need(f"Eight of the {od['programme_wallets_with_other_destination_events']} wallets behind the {od['other_from_programme_wallets']} events had no counted spend event.")
need("the first spend would move to May 15 and seven more wallets would count as having spent")
need(f"through block {meta['end_block']:,}, the last block of October 5")
# no wallet address in any chain file or output table; meta.json may name the three non-wallet factory contracts only
allowed = {o["address"] for o in meta["other_factory_contracts"]}
for f in list(CH.iterdir()) + list((HERE / "out").glob("*.csv")) + [HERE / "out" / "results.json"]:
    if f.exists():
        found = set(re.findall(r"0x[0-9a-fA-F]{40}", f.read_text()))
        assert found <= (allowed if f.name == "meta.json" else set()), f"address found in {f.name}"

print(f"{len(checks) - len(missing)} of {len(checks)} phrases found in article_draft.md")
for p in missing:
    print("  MISSING:", p)
sys.exit(1 if missing else 0)
