#!/usr/bin/env python3
"""How often EthenaPay wallets kept spending after their first spend event, by the week it came in,
from June 4 to October 4, 2026.

Reads the files in inputs/ and runs every check. If any check fails it stops before writing
anything, so out/ keeps the tables of the last clean run. Otherwise it rewrites the tables in
out/. Python 3 standard library only. It makes no network requests.

Data. The chain recount published with this site's EthenaPay adoption review of October 5, 2026:
every qualifying spend event through block 96,839,679, the last block of October 5, 2026 UTC,
grouped by UTC day and wallet, and each active wallet's USDe balance at block 96,815,525, 15:53:28
UTC on October 5. Wallets appear as position numbers in creation order, never as addresses.

Definitions.
  spend event     one AllowanceSpent log in USDe to either of the card programme's two settlement
                  addresses, counted as a log, never by transaction hash
  week            Monday to Sunday, UTC. The last full week ends on Sunday, October 4, so spend
                  events on October 5 are left out, apart from a count of the wallets with no
                  spend event in the last two weeks that spent again that day
  cohort          the wallets whose first spend event fell in the same week
  week k          the k-th week after the cohort's week. A wallet counts in week k if it had at
                  least one spend event in that week
"""
import csv
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, "inputs")
OUT = os.path.join(HERE, "out")
CUT = date(2026, 10, 4)                 # last day of the last full week
BETA_WEEK = date(2026, 8, 31)           # the week that holds the beta's opening on September 1
LAPSE_FROM = date(2026, 9, 21)          # the last two full weeks, September 21 to October 4
ONE_USDE = 10 ** 18

LOG = []
FAILED = []


def say(msg=""):
    LOG.append(msg)
    print(msg)


def check(name, ok, detail=""):
    say(f"[{'ok' if ok else 'FAIL'}] {name}{' . ' + detail if detail else ''}")
    if not ok:
        FAILED.append(name)


def read_csv(name):
    with open(os.path.join(INP, name), newline="") as f:
        return list(csv.DictReader(f))


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def monday(d):
    return d - timedelta(days=d.weekday())


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def write_csv(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


say("EthenaPay repeat spending by week of first spend")
say(f"Spend events from the first, June 4, 2026, through full weeks ending {CUT}")
say()

# ---------------------------------------------------------------- inputs and their integrity
manifest = read_csv("manifest.csv")
bad = [m["file"] for m in manifest if sha256(os.path.join(INP, m["file"])) != m["sha256"]]
check("every input matches the SHA-256 in manifest.csv", not bad and len(manifest) == 6,
      f"{len(manifest)} files" + (f", mismatched {bad}" if bad else ""))
chain_manifest = {r["file"]: r for r in read_csv("chain_manifest.csv")}
chain_ok = all(sha256(os.path.join(INP, "chain", f)) == chain_manifest[f]["sha256"] for f in chain_manifest)
check("the three chain files match the recount's own manifest, as published with the adoption review", chain_ok and
      len(chain_manifest) == 3, chain_manifest["spend_wallet_days.csv"]["last_run_utc"])
meta = json.load(open(os.path.join(INP, "chain", "meta.json")))
D0 = date.fromisoformat(meta["day_0"])
check("the recount ends at block 96,839,679, with its last spend event on October 5", meta["end_block"] == 96839679 and
      meta["last_spend_event"].startswith("2026-10-05"))

days = defaultdict(set)              # wallet -> spend days through CUT
events_by_week = Counter()
events_by_day = Counter()
wallets_by_week = defaultdict(set)
spent_on_oct5 = set()                # wallets with a spend event on October 5, the day after the cutoff
all_events, all_wallets, last_day, first_day = 0, set(), D0, None
for r in read_csv(os.path.join("chain", "spend_wallet_days.csv")):
    d = D0 + timedelta(days=int(r["day"]))
    w = int(r["wallet"])
    n = int(r["events"])
    all_events += n
    all_wallets.add(w)
    last_day = max(last_day, d)
    first_day = d if first_day is None else min(first_day, d)
    if d <= CUT:
        days[w].add(d)
        events_by_week[monday(d)] += n
        events_by_day[d] += n
        wallets_by_week[monday(d)].add(w)
    elif d == CUT + timedelta(days=1):
        spent_on_oct5.add(w)
check("the spend file holds every spend event and spending wallet in meta.json",
      all_events == meta["spend_events"] and len(all_wallets) == meta["wallets_that_ever_spent"],
      f"{all_events:,} events, {len(all_wallets)} wallets")
check("spend days run from June 4 to October 5", first_day == date(2026, 6, 4) and last_day == date(2026, 10, 5))

activity = {int(r["wallet"]): r for r in read_csv(os.path.join("chain", "wallet_activity.csv"))}
first = {w: min(s) for w, s in days.items()}
mism = [w for w in all_wallets if w not in activity or not activity[w]["first_spend_ts"]]
mism += [w for w in first if datetime.fromtimestamp(int(activity[w]["first_spend_ts"]), timezone.utc).date() != first[w]]
check("each spending wallet's first spend day matches its first_spend_ts in wallet_activity.csv", not mism,
      f"{len(first)} wallets with a spend event through {CUT}")

published = {r["first_day"]: r for r in read_csv("adoption_review_weeks_wallets.csv")}
pub_ok = all(len(wallets_by_week[date.fromisoformat(k)]) == int(v["spending_wallets"]) and
             events_by_week[date.fromisoformat(k)] == int(v["spend_events"]) for k, v in published.items())
check("weekly spending wallets and spend events match the adoption review's published table", pub_ok,
      f"{len(published)} weeks, July 27 to October 4")

# the same review's monthly table: spending wallets, first spends, wallets that had spent in an earlier
# month and spend events, for June to September and October 1 to 4
PERIODS = [("June 2026", date(2026, 6, 1), date(2026, 6, 30)), ("July 2026", date(2026, 7, 1), date(2026, 7, 31)),
           ("August 2026", date(2026, 8, 1), date(2026, 8, 31)), ("September 2026", date(2026, 9, 1), date(2026, 9, 30)),
           ("October 1 to 4, 2026", date(2026, 10, 1), CUT)]
month_check = []
for label, a, b in PERIODS:
    sw = [w for w in days if any(a <= d <= b for d in days[w])]
    month_check.append((label, len(sw), sum(1 for w in sw if a <= first[w] <= b), sum(1 for w in sw if first[w] < a),
                        sum(n for d, n in events_by_day.items() if a <= d <= b)))
pub_months = {r["period"]: r for r in read_csv("adoption_review_months_wallets.csv")}
months_ok = len(pub_months) == len(PERIODS) and all(
    label in pub_months and (int(pub_months[label]["spending_wallets"]), int(pub_months[label]["first_ever_spend_in_period"]),
                             int(pub_months[label]["spent_in_an_earlier_period"]),
                             int(pub_months[label]["spend_events"])) == (sw, fs, ea, ev)
    for label, sw, fs, ea, ev in month_check)
check("monthly spending wallets, first spends, returning wallets and spend events match the adoption review's monthly table",
      months_ok, "June to October 4")

LASTW = monday(CUT)
check("the cutoff is a Sunday, so every week counted is a full week", CUT.weekday() == 6 and LASTW == date(2026, 9, 28))


def active(w, wk):
    return any(wk <= d <= wk + timedelta(days=6) for d in days[w])


def bal(w):
    v = activity[w]["balance_wei_at_last_snapshot"] if w in activity else ""
    return int(v) if v else 0


# ---------------------------------------------------------------- cohorts by week of first spend
cohort = defaultdict(list)
for w, f in first.items():
    cohort[monday(f)].append(w)
weeks = sorted(cohort)
MAXK = 8
cohort_rows = []
for c in weeks:
    ws = cohort[c]
    counts = []
    for k in range(1, MAXK + 1):
        wk = c + timedelta(weeks=k)
        counts.append(sum(1 for w in ws if active(w, wk)) if wk <= LASTW else None)
    cohort_rows.append((c, len(ws), counts))
check("every spending wallet through the cutoff falls in one cohort", sum(n for _, n, _ in cohort_rows) == len(first))

# pooled curves: before the beta week, and the beta weeks with at least one later week
pre = [w for w, f in first.items() if monday(f) < BETA_WEEK]
beta = [w for w, f in first.items() if BETA_WEEK <= monday(f) < LASTW]
latest = [w for w, f in first.items() if monday(f) == LASTW]


def pooled(ws, kmax):
    rows = []
    for k in range(1, kmax + 1):
        elig = [w for w in ws if monday(first[w]) + timedelta(weeks=k) <= LASTW]
        if not elig:
            break
        n = sum(1 for w in elig if active(w, monday(first[w]) + timedelta(weeks=k)))
        rows.append({"k": k, "eligible": len(elig), "spending": n, "share": n / len(elig)})
    return rows


pre_curve = pooled(pre, 5)
beta_curve = pooled(beta, 4)
check("every wallet that first spent before the beta week has five later weeks in the data",
      all(r["eligible"] == len(pre) for r in pre_curve) and len(pre_curve) == 5)

# groups by month of first spend, before the beta week
months = [("June", date(2026, 6, 1), date(2026, 6, 30)), ("July", date(2026, 7, 1), date(2026, 7, 31)),
          ("August 1 to 30", date(2026, 8, 1), date(2026, 8, 30))]
month_rows = []
for label, a, b in months:
    ws = [w for w, f in first.items() if a <= f <= b]
    in_sep = sum(1 for w in ws if any(date(2026, 9, 1) <= d <= date(2026, 9, 30) for d in days[w]))
    last_week = sum(1 for w in ws if active(w, LASTW))
    one_day = sum(1 for w in ws if len(days[w]) == 1)
    month_rows.append({"group": label, "wallets": len(ws), "spent_in_september": in_sep, "spent_in_last_week": last_week,
                       "spent_on_one_day_only": one_day})
check("the three months hold every wallet that first spent before the beta week",
      sum(r["wallets"] for r in month_rows) == len(pre))

# no spend event in the last two weeks: first spend before September 21, none from September 21 to October 4
early = [w for w, f in first.items() if f < LAPSE_FROM]
lapsed = [w for w in early if not any(LAPSE_FROM <= d <= CUT for d in days[w])]
still = [w for w in early if w not in lapsed]
pre_set = set(pre)
first3 = [w for w in early if w not in pre_set]
check("the wallets that first spent before September 21 are the pre-beta wallets and the first three beta cohorts",
      len(first3) == sum(len(cohort[BETA_WEEK + timedelta(weeks=i)]) for i in range(3)) and pre_set <= set(early))
# a longer window for the pre-beta wallets: no spend event from September 1 to the cutoff
quiet_month = [w for w in pre if not any(date(2026, 9, 1) <= d <= CUT for d in days[w])]
# the cohort of the beta week across its four later weeks
c0 = cohort[BETA_WEEK]
c0_any = sum(1 for w in c0 if any(active(w, BETA_WEEK + timedelta(weeks=k)) for k in range(1, 5)))
c0_all = sum(1 for w in c0 if all(active(w, BETA_WEEK + timedelta(weeks=k)) for k in range(1, 5)))
lapsed_stats = {"first_spend_before": str(LAPSE_FROM), "wallets": len(early), "no_spend_in_last_two_weeks": len(lapsed),
                "lapsed_with_balance": sum(1 for w in lapsed if bal(w) > 0),
                "lapsed_with_1_usde_or_more": sum(1 for w in lapsed if bal(w) >= ONE_USDE),
                "lapsed_with_10_usde_or_more": sum(1 for w in lapsed if bal(w) >= 10 * ONE_USDE),
                "lapsed_with_100_usde_or_more": sum(1 for w in lapsed if bal(w) >= 100 * ONE_USDE),
                "lapsed_last_spend_by_month": dict(Counter(max(days[w]).strftime("%B") for w in lapsed)),
                "lapsed_spent_on_october_5": sum(1 for w in lapsed if w in spent_on_oct5),
                "lapsed_one_day_only": sum(1 for w in lapsed if len(days[w]) == 1),
                "pre_beta_wallets": len(pre), "lapsed_pre_beta": sum(1 for w in lapsed if w in pre_set),
                "first_three_beta_cohorts_wallets": len(first3),
                "lapsed_first_three_beta_cohorts": sum(1 for w in lapsed if w not in pre_set),
                "still_spending": len(still), "still_spending_with_balance": sum(1 for w in still if bal(w) > 0),
                "still_spending_with_1_usde_or_more": sum(1 for w in still if bal(w) >= ONE_USDE)}
aug31 = [w for w, f in first.items() if f == BETA_WEEK]
spend_days = Counter()
for w in early:
    n = len(days[w])
    spend_days["1" if n == 1 else "2 to 5" if n <= 5 else "6 to 14" if n <= 14 else "15 or more"] += 1

# a second spend day within seven days, for wallets with seven days of data after the first
elig7 = [w for w, f in first.items() if f + timedelta(days=7) <= CUT]
again7 = sum(1 for w in elig7 if any(0 < (d - first[w]).days <= 7 for d in days[w]))

results = {"cutoff": str(CUT), "wallets_with_spend_through_cutoff": len(first),
           "cohorts": [{"week": str(c), "wallets": n, "week_k": counts} for c, n, counts in cohort_rows],
           "pre_beta": {"wallets": len(pre), "curve": pre_curve},
           "beta": {"wallets": len(beta), "curve": beta_curve, "latest_cohort_wallets": len(latest)},
           "months": month_rows, "first_spend_on_august_31": len(aug31),
           "monthly_check": [{"period": p, "spending_wallets": sw, "first_spend_in_period": fs, "spent_in_an_earlier_period": ea,
                              "spend_events": ev} for p, sw, fs, ea, ev in month_check],
           "lapsed": lapsed_stats, "spend_days_first_spend_before_sep21": dict(spend_days),
           "pre_beta_no_spend_september_1_to_cutoff": {"wallets": len(quiet_month),
                                                        "with_1_usde_or_more": sum(1 for w in quiet_month if bal(w) >= ONE_USDE)},
           "beta_week_cohort": {"wallets": len(c0), "spent_in_any_of_weeks_1_to_4": c0_any, "spent_in_all_four": c0_all},
           "again_within_7_days": {"eligible": len(elig7), "spent_again": again7, "share": again7 / len(elig7)}}

say()
say(f"Wallets with a spend event through {CUT}: {len(first)}")
for c, n, counts in cohort_rows:
    shown = ", ".join(f"{x} ({x / n:.0%})" for x in counts if x is not None)
    say(f"  week of {c}: {n} wallets. Later weeks: {shown}")
say(f"  before the beta week, {len(pre)} wallets: " +
    ", ".join(f"week {r['k']} {r['spending']}/{r['eligible']} {pct(r['share'])}" for r in pre_curve))
say(f"  first spend August 31 to September 27, {len(beta)} wallets: " +
    ", ".join(f"week {r['k']} {r['spending']}/{r['eligible']} {pct(r['share'])}" for r in beta_curve))
for r in month_rows:
    say(f"  first spend {r['group']}: {r['wallets']} wallets, spent in September {r['spent_in_september']}, in the last week "
        f"{r['spent_in_last_week']}, on one day only {r['spent_on_one_day_only']}")
say(f"  first spend on August 31, in the beta week: {len(aug31)} wallet(s)")
for p, sw, fs, ea, ev in month_check:
    say(f"  {p}: {sw} spending wallets, {fs} first spends, {ea} that had spent in an earlier month, {ev:,} spend events")
ls = lapsed_stats
say(f"  first spend before {LAPSE_FROM}: {ls['wallets']} wallets, no spend in the last two weeks {ls['no_spend_in_last_two_weeks']}, "
    f"of which holding USDe {ls['lapsed_with_balance']}, 1 USDe or more {ls['lapsed_with_1_usde_or_more']}, "
    f"spent on October 5 {ls['lapsed_spent_on_october_5']}. Still spending {ls['still_spending']}, all holding USDe: "
    f"{ls['still_spending'] == ls['still_spending_with_balance']}")
say(f"  of the {ls['no_spend_in_last_two_weeks']}: pre-beta {ls['lapsed_pre_beta']} of {ls['pre_beta_wallets']}, first three beta "
    f"cohorts {ls['lapsed_first_three_beta_cohorts']} of {ls['first_three_beta_cohorts_wallets']}, one spend day only "
    f"{ls['lapsed_one_day_only']}, 10 USDe or more {ls['lapsed_with_10_usde_or_more']}, 100 USDe or more "
    f"{ls['lapsed_with_100_usde_or_more']}. Still spending with 1 USDe or more {ls['still_spending_with_1_usde_or_more']}")
qm = results["pre_beta_no_spend_september_1_to_cutoff"]
say(f"  pre-beta wallets with no spend event from 2026-09-01 to {CUT}: {qm['wallets']} of {len(pre)}, of which 1 USDe or more "
    f"{qm['with_1_usde_or_more']}")
say(f"  cohort of the beta week, {len(c0)} wallets: spent in at least one of weeks 1 to 4 {c0_any}, in all four {c0_all}")
say(f"  spend days, first spend before {LAPSE_FROM}: " + ", ".join(f"{k} {v}" for k, v in sorted(spend_days.items())))
say(f"  spent again within 7 days of the first spend day: {again7} of {len(elig7)}, {pct(again7 / len(elig7))}")

say()
if FAILED:
    say(f"{len(FAILED)} check(s) failed: {', '.join(FAILED)}. Nothing was written to out/.")
    sys.exit(1)

os.makedirs(OUT, exist_ok=True)
write_csv("first_spend_cohorts.csv", ["first_spend_week", "wallets"] + [f"week_{k}" for k in range(1, MAXK + 1)] +
          [f"week_{k}_share" for k in range(1, MAXK + 1)],
          [[c, n] + ["" if x is None else x for x in counts] + ["" if x is None else round(x / n, 6) for x in counts]
           for c, n, counts in cohort_rows])
write_csv("weekly_shares.csv", ["group", "wallets", "week_after_first", "wallets_observed", "wallets_spending", "share"],
          [["first spend June 4 to August 30", len(pre), r["k"], r["eligible"], r["spending"], round(r["share"], 6)]
           for r in pre_curve] +
          [["first spend August 31 to September 27", len(beta), r["k"], r["eligible"], r["spending"], round(r["share"], 6)]
           for r in beta_curve])
write_csv("first_spend_months.csv", ["group", "wallets", "spent_in_september", "spent_in_last_week", "spent_on_one_day_only"],
          [[r["group"], r["wallets"], r["spent_in_september"], r["spent_in_last_week"], r["spent_on_one_day_only"]]
           for r in month_rows])
write_csv("weekly_check.csv", ["week", "spending_wallets", "spend_events", "published_spending_wallets", "published_spend_events"],
          [[k, len(wallets_by_week[date.fromisoformat(k)]), events_by_week[date.fromisoformat(k)], v["spending_wallets"],
            v["spend_events"]] for k, v in published.items()])
write_csv("monthly_check.csv", ["period", "spending_wallets", "first_spend_in_period", "spent_in_an_earlier_period", "spend_events",
                                "published_spending_wallets", "published_first_spend_in_period",
                                "published_spent_in_an_earlier_period", "published_spend_events"],
          [[p, sw, fs, ea, ev, pub_months[p]["spending_wallets"], pub_months[p]["first_ever_spend_in_period"],
            pub_months[p]["spent_in_an_earlier_period"], pub_months[p]["spend_events"]] for p, sw, fs, ea, ev in month_check])
with open(os.path.join(OUT, "results.json"), "w") as f:
    json.dump(results, f, indent=1, default=str)
    f.write("\n")
say("All checks passed. Tables written to out/.")
with open(os.path.join(OUT, "run_log.txt"), "w") as f:
    f.write("\n".join(LOG) + "\n")
