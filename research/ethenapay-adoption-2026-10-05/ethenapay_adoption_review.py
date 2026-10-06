#!/usr/bin/env python3
"""
EthenaPay adoption review, October 2026. Reproduces every figure in the article.

Part A reads nine dated snapshots of the dashboard dataset. Part B reads the chain recount in inputs/chain.

Run from this folder:  python3 ethenapay_adoption_review.py

Inputs (all in ./inputs, pinned by commit in inputs/manifest.csv)
  ethenapay_<commit>.json
      Nine versions of docs/ethenapay.json from the public repo QorbQuant/EthenaDAT, each exactly as
      committed. Every version is one run of the two Dune queries in QorbQuant/ethenaPay (dune/05 and dune/06).
      "headline" is one row of point-in-time figures. "series" is one row per UTC day since 2026-05-15.
  ethenapay_chain_snapshot_33fe499.json
      public/snapshot.json from QorbQuant/ethenaPay, built on 2026-09-11 from the Routescan explorer API and a
      public RPC node. It is a second implementation of the same definitions that does not use Dune.
  05_daily_metrics_<commit>.sql, 06_kpi_headline_<commit>.sql
      The query text before and after its only change in the period (2026-10-05).

Definitions used here (from the SQL)
  wallets created   contracts deployed by the two wallet factories. Deployed addresses, not people.
  funded wallets    wallets whose USDe balance is above zero when the query runs. No minimum balance.
  spending wallets  wallets with at least one AllowanceSpent event into a settlement address, ever.
  spend events      AllowanceSpent log events (USDe, either settlement address). Never transaction hashes.
  30-day and 7-day spending wallets   distinct wallets with a spend event since 00:00 UTC thirty (seven) days
                    before the run date. The window therefore holds 30 (7) full days plus the part of the run day.
  USDe held         sum of positive USDe balances across the wallets.
  top-10 share      the ten largest balances divided by USDe held.

Rules kept
  No average or median purchase size. Daily spending-wallet counts are never added up into a monthly figure.
  The last day of every snapshot is a partial day and is left out of every period comparison.
"""
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
INP, OUT = HERE / "inputs", HERE / "out"
OUT.mkdir(exist_ok=True)

# ----------------------------------------------------------------------------- inputs, pinned and hashed
manifest = list(csv.DictReader(open(INP / "manifest.csv")))
snaps = []
for m in manifest:
    raw = (INP / m["file"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == m["sha256"], f"{m['file']} does not match the manifest hash"
    d = json.loads(raw)
    snaps.append(dict(meta=m, data=d))
dune = [s for s in snaps if s["meta"]["repo"] == "QorbQuant/EthenaDAT"]
chain = next(s for s in snaps if s["meta"]["repo"] == "QorbQuant/ethenaPay")
assert len(dune) == 9
FIRST, LAST = dune[0], dune[-1]


def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(dt.timezone.utc)


def H(s, k):
    return s["data"]["headline"][k]


def label(s):
    t = ts(s["data"]["generated_at"])
    return t.strftime("%b %-d %H:%M")


print("INPUTS")
for s in snaps:
    m = s["meta"]
    print(f" {m['file']:42s} commit {m['commit'][:7]}  generated {s['data']['generated_at']:27s} source {s['data'].get('source')}")

# ----------------------------------------------------------------------------- 1. headline at each snapshot
FIELDS = ["wallets_created", "funded_wallets", "spending_wallets", "mau_30d", "wau_7d", "lifetime_spend_count",
          "lifetime_spend_usde", "spend_usde_30d", "tvl_usde", "top10_balance_share", "batched_spend_share", "max_logs_per_tx"]
rows = []
for s in dune:
    r = dict(generated_at=s["data"]["generated_at"], commit=s["meta"]["commit"][:7])
    for k in FIELDS:
        r[k] = H(s, k)
    r["funded_share_of_created"] = r["funded_wallets"] / r["wallets_created"]
    r["spending_share_of_created"] = r["spending_wallets"] / r["wallets_created"]
    r["top10_usde"] = r["top10_balance_share"] * r["tvl_usde"]
    r["rest_usde"] = r["tvl_usde"] - r["top10_usde"]
    r["funded_outside_top10"] = r["funded_wallets"] - 10
    r["spent_30d_share_of_ever"] = r["mau_30d"] / r["spending_wallets"]
    r["spent_7d_share_of_ever"] = r["wau_7d"] / r["spending_wallets"]
    # the dataset's own rates must equal the ratios of its counts
    assert abs(H(s, "funding_rate") - r["funded_share_of_created"]) < 1e-9
    assert abs(H(s, "activation_rate") - r["spending_share_of_created"]) < 1e-9
    rows.append(r)

print("\nHEADLINE AT EACH SNAPSHOT (Dune)")
print(" generated (UTC)    created  funded  ever-spent  30d    7d   events  spend $      USDe held    top10   top10 $      rest $      funded/created  spent/created")
for r in rows:
    print(f" {r['generated_at'][:16]}  {r['wallets_created']:7.0f} {r['funded_wallets']:7.0f} {r['spending_wallets']:8.0f} {r['mau_30d']:7.0f} {r['wau_7d']:5.0f} "
          f"{r['lifetime_spend_count']:7.0f} {r['lifetime_spend_usde']:11,.0f} {r['tvl_usde']:12,.0f}  {r['top10_balance_share']*100:5.2f}%  "
          f"{r['top10_usde']:11,.0f} {r['rest_usde']:11,.0f}   {r['funded_share_of_created']*100:6.2f}%        {r['spending_share_of_created']*100:5.2f}%")
with open(OUT / "snapshots.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    for r in rows:
        w.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()})

a, b = rows[0], rows[-1]
days_between = (ts(b["generated_at"]) - ts(a["generated_at"])).total_seconds() / 86400
print(f"\nFIRST TO LAST SNAPSHOT ({a['generated_at']} to {b['generated_at']}, {days_between:.2f} days)")
for k, name in [("wallets_created", "wallets created"), ("funded_wallets", "funded wallets"), ("spending_wallets", "wallets that ever spent"),
                ("mau_30d", "30-day spending wallets"), ("wau_7d", "7-day spending wallets"), ("lifetime_spend_count", "spend events"),
                ("lifetime_spend_usde", "spend, USDe"), ("tvl_usde", "USDe held"), ("top10_usde", "USDe in the ten largest wallets"),
                ("rest_usde", "USDe in all other wallets"), ("funded_outside_top10", "funded wallets outside the ten largest")]:
    print(f" {name:40s} {a[k]:14,.2f} -> {b[k]:14,.2f}   change {b[k]-a[k]:+14,.2f}   x{b[k]/a[k]:.3f}   ({(b[k]/a[k]-1)*100:+.1f}%)")
print(f" top-10 share                             {a['top10_balance_share']*100:.2f}% -> {b['top10_balance_share']*100:.2f}%")
print(f" funded share of created                  {a['funded_share_of_created']*100:.2f}% -> {b['funded_share_of_created']*100:.2f}%")
print(f" ever-spent share of created              {a['spending_share_of_created']*100:.2f}% -> {b['spending_share_of_created']*100:.2f}%")
print(f" share of all spend events that fall after the first snapshot: {(b['lifetime_spend_count']-a['lifetime_spend_count'])/b['lifetime_spend_count']*100:.1f}%"
      f" ({b['lifetime_spend_count']-a['lifetime_spend_count']:,.0f} of {b['lifetime_spend_count']:,.0f})")
print(f" created wallets per funded wallet, last snapshot: {b['wallets_created']/b['funded_wallets']:.1f}; per wallet that ever spent: {b['wallets_created']/b['spending_wallets']:.1f}")
print(f" last snapshot: 30-day spending wallets are {b['spent_30d_share_of_ever']*100:.1f}% of wallets that ever spent; 7-day are {b['spent_7d_share_of_ever']*100:.1f}%;"
      f" 7-day over 30-day {b['wau_7d']/b['mau_30d']*100:.1f}%")
print(f" first snapshot: {a['spent_30d_share_of_ever']*100:.1f}% and {a['spent_7d_share_of_ever']*100:.1f}%")
print(f" batched share of spend events: {a['batched_spend_share']*100:.2f}% -> {b['batched_spend_share']*100:.2f}%; most events in one transaction: {b['max_logs_per_tx']:.0f}")

# the two runs on Oct 5 straddle the only change to the query text
o1, o2 = rows[-2], rows[-1]
gap_min = (ts(o2["generated_at"]) - ts(o1["generated_at"])).total_seconds() / 60
print(f"\nTWO RUNS {gap_min:.0f} MINUTES APART ON OCT 5, ONE ON EACH VERSION OF THE QUERY")
for k in ("wallets_created", "funded_wallets", "spending_wallets", "mau_30d", "wau_7d", "lifetime_spend_count", "tvl_usde", "top10_balance_share"):
    print(f" {k:22s} {o1[k]:16,.4f}  {o2[k]:16,.4f}")
assert o1["funded_wallets"] == o2["funded_wallets"] and o1["spending_wallets"] == o2["spending_wallets"]

# ----------------------------------------------------------------------------- 2. Dune against the chain-built snapshot, same morning
print(f"\nDUNE ({FIRST['data']['generated_at']}) AGAINST THE CHAIN-BUILT SNAPSHOT ({chain['data']['generated_at']})")
gap = (ts(FIRST["data"]["generated_at"]) - ts(chain["data"]["generated_at"])).total_seconds() / 60
print(f" the Dune run is {gap:.0f} minutes later")
pairs = [("wallets_created", "wallets_created"), ("funded_wallets", "funded_wallets"), ("spending_wallets", "spending_wallets"),
         ("lifetime_spend_count", "lifetime_spend_count"), ("lifetime_spend_usde", "lifetime_spend_usde"), ("mau_30d", "mau_30d"),
         ("wau_7d", "wau_7d"), ("tvl_usde", "tvl_usde"), ("top10_balance_share", "top10_balance_share"), ("max_logs_per_tx", "max_logs_per_tx")]
xcheck = []
for kd, kc in pairs:
    vd, vc = H(FIRST, kd), chain["data"]["headline"][kc]
    xcheck.append(dict(metric=kd, dune=vd, chain_snapshot=vc, diff=vd - vc, diff_pct=round((vd / vc - 1) * 100, 3)))
    print(f" {kd:22s} Dune {vd:16,.4f}   chain {vc:16,.4f}   diff {vd-vc:+12,.4f}  ({(vd/vc-1)*100:+.2f}%)")
with open(OUT / "dune_vs_chain_sep11.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(xcheck[0].keys())); w.writeheader(); w.writerows(xcheck)

# ----------------------------------------------------------------------------- 3. daily series (latest snapshot)
S = LAST["data"]["series"]
N = len(S["date"])
day = {S["date"][i]: {k: S[k][i] for k in S if k != "date"} for i in range(N)}
dates = S["date"]
PARTIAL = dates[-1]                       # the run day, 2026-10-05, is incomplete
LAST_FULL = dates[-2]
gen = ts(LAST["data"]["generated_at"])
assert PARTIAL == gen.strftime("%Y-%m-%d") and LAST_FULL == "2026-10-04"
print(f"\nDAILY SERIES: {dates[0]} to {dates[-1]} ({N} days). {PARTIAL} is partial (run at {gen:%H:%M} UTC). Last full day {LAST_FULL}.")
print(f" sum of daily spend events {sum(S['spend_count']):,.0f} against headline {H(LAST,'lifetime_spend_count'):,.0f};"
      f" sum of new wallets {sum(S['new_wallets']):,.0f} against headline {H(LAST,'wallets_created'):,.0f}")
assert sum(S["new_wallets"]) == H(LAST, "wallets_created")
assert abs(sum(S["spend_count"]) - H(LAST, "lifetime_spend_count")) <= 25     # the two queries run moments apart

# Which fields read the same on every full day in every later snapshot, and which were restated.
# The query changed once in the period (2026-10-05, "stop counting rewards as deposits"), so deposit fields may differ.
print("\nRESTATEMENT CHECK (full days, each earlier snapshot against the latest, every field the two share)")
USED_FROM_SERIES = ("new_wallets", "cumulative_wallets", "active_wallets", "spend_count", "spend_usde", "withdrawals_usde", "tvl_usde")
for s in dune[:-1]:
    ser = s["data"]["series"]
    full = ser["date"][:-1]
    same, changed = [], []
    for k in ser:
        if k == "date" or k not in S:
            continue
        n_diff = sum(1 for i, d in enumerate(full) if abs(ser[k][i] - day[d][k]) > 0.005)
        (changed if n_diff else same).append((k, n_diff))
    print(f" {s['data']['generated_at'][:16]}  {len(full)} full days  identical: {', '.join(k for k, _ in same)}"
          + (f"  |  restated: {', '.join(f'{k} on {n} days' for k, n in changed)}" if changed else "  |  restated: none"))
    assert not [k for k, _ in changed if k in USED_FROM_SERIES], "a field this review uses was restated"
print(" every field this review takes from the daily series (" + ", ".join(USED_FROM_SERIES) + ") reads the same in all nine snapshots")

first_spend = next(d for d in dates if day[d]["spend_count"] > 0)
print(f"\n first day with a spend event: {first_spend}")
big = sorted(dates, key=lambda d: -day[d]["new_wallets"])[:6]
print(" largest wallet-creation days: " + ", ".join(f"{d} {day[d]['new_wallets']:,.0f}" for d in big))
through_aug = sum(day[d]["new_wallets"] for d in dates if d <= "2026-08-31")
sep12 = day["2026-09-01"]["new_wallets"] + day["2026-09-02"]["new_wallets"]
print(f" wallets created through Aug 31: {through_aug:,.0f}; on Sep 1 and 2: {sep12:,.0f} = {sep12/H(LAST,'wallets_created')*100:.1f}% of all wallets;"
      f" Sep 3 to {LAST_FULL}: {sum(day[d]['new_wallets'] for d in dates if '2026-09-03' <= d <= LAST_FULL):,.0f}")


def period(d0, d1, name):
    ds = [d for d in dates if d0 <= d <= d1]
    n = len(ds)
    act = [day[d]["active_wallets"] for d in ds]
    return dict(period=name, first_day=d0, last_day=d1, days=n,
                new_wallets=sum(day[d]["new_wallets"] for d in ds),
                spend_events=sum(day[d]["spend_count"] for d in ds),
                spend_events_per_day=sum(day[d]["spend_count"] for d in ds) / n,
                spend_usde=sum(day[d]["spend_usde"] for d in ds),
                daily_spending_wallets_low=min(act), daily_spending_wallets_high=max(act),
                daily_spending_wallets_mean=sum(act) / n,
                deposits_usde=sum(day[d]["deposits_usde"] for d in ds),
                withdrawals_usde=sum(day[d]["withdrawals_usde"] for d in ds),
                usde_held_end=day[d1]["tvl_usde"])


def show(table, title, fname):
    print(f"\n{title}")
    print(" period                  days  new wallets  spend events   per day   spend USDe   daily spending wallets low/high/mean   deposits     withdrawals   USDe held at end")
    for r in table:
        print(f" {r['period']:22s} {r['days']:4d} {r['new_wallets']:11,.0f} {r['spend_events']:13,.0f} {r['spend_events_per_day']:9.1f} {r['spend_usde']:12,.0f}"
              f"      {r['daily_spending_wallets_low']:4.0f} / {r['daily_spending_wallets_high']:4.0f} / {r['daily_spending_wallets_mean']:6.1f}"
              f"          {r['deposits_usde']:12,.0f} {r['withdrawals_usde']:12,.0f} {r['usde_held_end']:14,.0f}")
    with open(OUT / fname, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0].keys())); w.writeheader()
        for r in table:
            w.writerow({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})


months = [period("2026-06-01", "2026-06-30", "June 2026"), period("2026-07-01", "2026-07-31", "July 2026"),
          period("2026-08-01", "2026-08-31", "August 2026"), period("2026-09-01", "2026-09-30", "September 2026"),
          period("2026-10-01", LAST_FULL, "October 1 to 4, 2026")]
show(months, "FULL CALENDAR MONTHS (October holds four full days)", "months.csv")
aug, sep = months[2], months[3]
print(f" September against August: spend events x{sep['spend_events']/aug['spend_events']:.2f}, spend USDe x{sep['spend_usde']/aug['spend_usde']:.2f},"
      f" mean daily spending wallets x{sep['daily_spending_wallets_mean']/aug['daily_spending_wallets_mean']:.2f}, new wallets x{sep['new_wallets']/aug['new_wallets']:.1f}")

# seven-day periods that end on the last full day, so every period has the same weekdays
end = dt.date.fromisoformat(LAST_FULL)
weeks = []
for kback in range(7, -1, -1):
    d1 = end - dt.timedelta(days=7 * kback)
    d0 = d1 - dt.timedelta(days=6)
    weeks.append(period(d0.isoformat(), d1.isoformat(), f"{d0:%b %-d} to {d1:%b %-d}"))
show(weeks, "SEVEN-DAY PERIODS ENDING ON THE LAST FULL DAY", "weeks.csv")
w_last, w_first_sep = weeks[-1], weeks[-5]
print(f" latest period against the period four weeks earlier ({w_first_sep['period']}): spend events x{w_last['spend_events']/w_first_sep['spend_events']:.2f},"
      f" mean daily spending wallets x{w_last['daily_spending_wallets_mean']/w_first_sep['daily_spending_wallets_mean']:.2f}")

# days on which USDe held moved by more than $400k, with the flows behind them
print("\nLARGEST ONE-DAY WITHDRAWALS AND DEPOSITS (full days)")
for d in sorted([d for d in dates if d <= LAST_FULL], key=lambda d: -day[d]["withdrawals_usde"])[:6]:
    print(f" {d}: withdrawals {day[d]['withdrawals_usde']:12,.0f}  deposits {day[d]['deposits_usde']:12,.0f}  USDe held at end of day {day[d]['tvl_usde']:12,.0f}")
for d in sorted([d for d in dates if d <= LAST_FULL], key=lambda d: -day[d]["deposits_usde"])[:6]:
    print(f" {d}: deposits {day[d]['deposits_usde']:12,.0f}  withdrawals {day[d]['withdrawals_usde']:12,.0f}  USDe held at end of day {day[d]['tvl_usde']:12,.0f}")
peak = max((d for d in dates if d <= LAST_FULL), key=lambda d: day[d]["tvl_usde"])
print(f" highest end-of-day USDe held: {day[peak]['tvl_usde']:,.0f} on {peak}; on Aug 31 {day['2026-08-31']['tvl_usde']:,.0f}; on {LAST_FULL} {day[LAST_FULL]['tvl_usde']:,.0f}")

with open(OUT / "daily_series.csv", "w", newline="") as f:
    cols = ["new_wallets", "cumulative_wallets", "active_wallets", "spend_count", "spend_usde", "deposits_usde", "withdrawals_usde", "tvl_usde"]
    w = csv.writer(f); w.writerow(["date", "partial_day"] + cols)
    for d in dates:
        w.writerow([d, "yes" if d == PARTIAL else "no"] + [round(day[d][c], 2) for c in cols])


# =============================================================================================================
# PART B. THE CHAIN RECOUNT
# Files in inputs/chain were written by chain_recount.cjs, which reads Avalanche C-Chain directly (explorer API
# and RPC) and uses no Dune table. Wallets appear there as a position number in creation order, never as an address.
# =============================================================================================================
CH = INP / "chain"
for m in csv.DictReader(open(INP / "chain_manifest.csv")):
    assert hashlib.sha256((CH / m["file"]).read_bytes()).hexdigest() == m["sha256"], f"{m['file']} does not match the chain manifest hash"
    # the manifest names the script that produced the file; when that script is in this folder it must be the same one
    script = HERE / m["produced_by"]
    assert not script.exists() or hashlib.sha256(script.read_bytes()).hexdigest() == m["script_sha256"], f"{m['produced_by']} is not the script that produced {m['file']}"

if (INP / "sql_manifest.csv").exists():
    for m in csv.DictReader(open(INP / "sql_manifest.csv")):
        if (INP / m["file"]).exists():                        # the query text is reference material; no figure is computed from it
            assert hashlib.sha256((INP / m["file"]).read_bytes()).hexdigest() == m["sha256"], f"{m['file']} does not match the sql manifest hash"

DAY = 86400
D0 = dt.date(2026, 5, 15)                                     # day 0 in the chain files
DAY0 = int(dt.datetime(2026, 5, 15, tzinfo=dt.timezone.utc).timestamp()) // DAY
E18 = 10 ** 18


def dnum(s):
    return (dt.date.fromisoformat(s) - D0).days


def dstr(d):
    return (D0 + dt.timedelta(days=d)).isoformat()


def usd(wei):
    return wei / E18


_w = list(csv.DictReader(open(CH / "wallets_created.csv")))
created = [int(r["created_ts"]) for r in _w]                  # creation time of wallet number i
factory = [int(r["factory"]) for r in _w]                     # 0 = the first (pilot) factory, 1 = the second factory
NW = len(created)
assert [int(r["wallet"]) for r in _w] == list(range(NW)) and created == sorted(created)
created_day = [t // DAY - DAY0 for t in created]

WD = [tuple(int(x) for x in r) for r in list(csv.reader(open(CH / "spend_wallet_days.csv")))[1:]]   # day, segment, wallet, events, cents
ACT = {}
for r in csv.DictReader(open(CH / "wallet_activity.csv")):
    ACT[int(r["wallet"])] = dict(first_in=int(r["first_usde_in_ts"]) if r["first_usde_in_ts"] else None, kind=r["first_in_kind"],
                                 first_spend=int(r["first_spend_ts"]) if r["first_spend_ts"] else None, bal=int(r["balance_wei_at_last_snapshot"]))
CDAY = {r["date"]: r for r in csv.DictReader(open(CH / "daily_chain.csv"))}
CS = json.load(open(CH / "snapshots_chain.json"))
CM = json.load(open(CH / "meta.json"))
assert len(CS) == 9 and [c["id"] for c in CS] == [s["meta"]["commit"][:7] for s in dune]
CUT = CS[-1]
CUT_TS, CUT_BLOCK = CUT["cut_ts"], CUT["cut_block"]
J_LAST = 8                                                    # a spend row belongs to snapshot j when its segment is j or lower

print("\n" + "=" * 110)
print("PART B. CHAIN RECOUNT")
assert NW == CM["wallets"]
print(f" read through block {CM['end_block']:,} (the last block of 2026-10-05 UTC): {CM['wallets']:,} wallets, {CM['spend_events']:,} qualifying spend events,"
      f" {CM['usde_transfers_touching_wallets']:,} USDe transfers touching a wallet out of {CM['usde_transfers_scanned']:,} scanned")
print(f" contracts created by the factories: {CM['factory_created_contracts']:,} = {CM['wallets']:,} wallets (CREATE2) + {len(CM['other_factory_contracts'])} others (plain CREATE)")
for o in CM["other_factory_contracts"]:
    print(f"   other contract {o['address']} from the {o['factory']} factory at {o['time']}")
# The comparison of transfers with events uses counts and sums. It does not pair each event with its transfer.
print(f" USDe transfers from wallets to the two settlement addresses: {CM['wallet_to_settlement_transfers']:,}, against {CM['spend_events']:,} spend events."
      f" The transfers sum to {usd(int(CM['wallet_to_settlement_wei']) - int(CM['spend_wei'])):.2f} USDe more than the events")
_off = [(d, int(r["card_spend_wei"]) - int(r["spend_cents"]) * 10 ** 16) for d, r in CDAY.items() if int(r["card_spend_wei"]) != int(r["spend_cents"]) * 10 ** 16]
assert _off == [("2026-09-24", 5 * E18)] and CM["wallet_to_settlement_transfers"] - CM["spend_events"] == 1
print(f"   on every day the two daily sums are equal, except {_off[0][0]}, when the transfers sum to {usd(_off[0][1]):.2f} USDe more")
SA = {x["role"]: x for x in CM["settlement_addresses"]}
assert SA["retired"]["spend_events"] == CM["spend_events_retired_settlement"] and SA["current"]["spend_events"] == CM["spend_events_current_settlement"]
assert SA["retired"]["last_spend_event"] < SA["current"]["first_spend_event"]              # the retired address stopped before the current one started
assert int(SA["retired"]["spend_cents"]) + int(SA["current"]["spend_cents"]) == int(CM["spend_wei"]) // 10 ** 16
print(f" settlement addresses: the retired one received {SA['retired']['spend_events']} spend events, {int(SA['retired']['spend_cents']) / 100:,.2f} USDe, from {SA['retired']['first_spend_event']} to {SA['retired']['last_spend_event']};")
print(f"   the current one received {SA['current']['spend_events']:,} events, {int(SA['current']['spend_cents']) / 100:,.2f} USDe, from {SA['current']['first_spend_event']}")
# the repo's own chain-built snapshot of September 11 splits spend by settlement address and agrees on the retired one
_rs = chain["data"]["headline"]["spend_by_settlement"]["retired"]
_rd = [x["day"] for x in chain["data"]["series"] if x["spend_usde_retired"]]
assert abs(_rs - int(SA["retired"]["spend_cents"]) / 100) < 0.006 and _rd[0] == SA["retired"]["first_spend_event"][:10] and _rd[-1] == SA["retired"]["last_spend_event"][:10]
assert [x["day"] for x in chain["data"]["series"] if x["spend_usde_current"]][0] == SA["current"]["first_spend_event"][:10]
print(f"   the repo's chain-built snapshot of September 11 shows the same {_rs:,.2f} USDe to the retired address, on {len(_rd)} days from {_rd[0]} to {_rd[-1]}")
bc = CM["balance_check"]
print(f" balanceOf at block {bc['block']:,} for {bc['wallets_checked']:,} wallets: {bc['mismatch_count']} differ from the balance built from transfers;"
      f" {bc['wallets_with_balance']:,} hold a balance, {usd(int(bc['sum_wei'])):,.2f} USDe in total")
assert bc["mismatch_count"] == 0 and bc["block"] == CUT_BLOCK

# ----------------------------------------------------------------------------- B1. chain against the dashboard at each of the nine snapshots
print("\nB1. CHAIN AGAINST THE DASHBOARD AT EACH SNAPSHOT")
print(" The chain figures are read at the block of the last spend event the dashboard had counted (the cut block).")
print(" snapshot          cut time (UTC)   lag s  created      funded       ever spent   30-day       7-day        spend USDe                 USDe held                    top-10 share")
print("                                           dash/chain   dash/chain   dash/chain   dash/chain   dash/chain   dash / chain               dash / chain                 dash / chain")
cmp_rows = []
for j, (s, c) in enumerate(zip(dune, CS)):
    run_day = dnum(s["data"]["generated_at"][:10])
    pre = [r for r in WD if r[1] <= j]
    ev = sum(r[3] for r in pre)
    cents = sum(r[4] for r in pre)
    ever = {r[2] for r in pre}
    w30 = {r[2] for r in pre if r[0] >= run_day - 30}
    w7 = {r[2] for r in pre if r[0] >= run_day - 7}
    cents30 = sum(r[4] for r in pre if r[0] >= run_day - 30)
    b, g = c["balances_at_cut_block"], c["balances_at_generated_time"]
    held, held_gen = usd(int(b["held_wei"])), usd(int(g["held_wei"]))
    top10 = int(b["top10_wei"]) / int(b["held_wei"])
    # the files in this packet reproduce the browser-side figures
    assert ev == c["spend_events"] == H(s, "lifetime_spend_count") and str(cents) == c["spend_cents"]
    assert len(ever) == c["wallets_ever_spent"] and len(w30) == c["wallets_spent_30d"] and len(w7) == c["wallets_spent_7d"] and str(cents30) == c["spend_cents_30d"]
    # and the chain reproduces the dashboard exactly on every spend measure
    assert len(ever) == H(s, "spending_wallets") and len(w30) == H(s, "mau_30d") and len(w7) == H(s, "wau_7d")
    assert abs(cents / 100 - H(s, "lifetime_spend_usde")) < 0.006 and abs(cents30 / 100 - H(s, "spend_usde_30d")) < 0.006
    assert c["max_events_in_one_transaction"] == H(s, "max_logs_per_tx")
    assert abs(c["events_in_multi_event_transactions"] / ev - H(s, "batched_spend_share")) < 1e-9
    assert c["boundary_between_blocks"]
    # balances agree to within the minutes between the two Dune tables, and the share to a hundredth of a point
    assert min(abs(held - H(s, "tvl_usde")), abs(held_gen - H(s, "tvl_usde"))) < 20 and abs(top10 - H(s, "top10_balance_share")) < 0.0002
    d_created = H(s, "wallets_created") - c["wallets_created_at_cut_block"]
    d_funded = H(s, "funded_wallets") - b["funded"]
    assert d_created in (1, 2) and d_funded in (1, 2) and b["negative_balances"] == 0
    cmp_rows.append(dict(snapshot=c["id"], generated=c["generated"], cut_time=c["cut_time"], cut_block=c["cut_block"], seconds_before_generated=c["seconds_before_generated"],
                         created_dashboard=int(H(s, "wallets_created")), created_chain=c["wallets_created_at_cut_block"], created_chain_at_generated=c["wallets_created_at_generated_time"],
                         funded_dashboard=int(H(s, "funded_wallets")), funded_chain=b["funded"], funded_chain_float_sum=b["float_funded"],
                         funded_chain_at_generated=g["funded"], funded_chain_float_sum_at_generated=g["float_funded"],
                         usde_held_changed_before_run="yes" if b["held_wei"] != g["held_wei"] else "no",
                         a_balance_statistic_changed_before_run="yes" if any(b[k] != g[k] for k in g if k != "float_held") else "no",
                         holding_1_usde_or_more_chain=b["ge_1"],
                         ever_spent_dashboard=int(H(s, "spending_wallets")), ever_spent_chain=len(ever),
                         spent_30d_dashboard=int(H(s, "mau_30d")), spent_30d_chain=len(w30), spent_7d_dashboard=int(H(s, "wau_7d")), spent_7d_chain=len(w7),
                         spend_events=ev, spend_usde_dashboard=round(H(s, "lifetime_spend_usde"), 2), spend_usde_chain=cents / 100,
                         usde_held_dashboard=round(H(s, "tvl_usde"), 2), usde_held_chain=round(held, 2), usde_held_chain_at_generated=round(held_gen, 2),
                         top10_share_dashboard=round(H(s, "top10_balance_share"), 6), top10_share_chain=round(top10, 6)))
    r = cmp_rows[-1]
    print(f" {c['generated'][:16]}  {c['cut_time'][5:16]}  {c['seconds_before_generated']:5d}  {r['created_dashboard']:5d}/{r['created_chain']:5d}  {r['funded_dashboard']:5d}/{r['funded_chain']:5d}"
          f"  {r['ever_spent_dashboard']:5d}/{r['ever_spent_chain']:5d}  {r['spent_30d_dashboard']:5d}/{r['spent_30d_chain']:5d}  {r['spent_7d_dashboard']:5d}/{r['spent_7d_chain']:5d}"
          f"  {r['spend_usde_dashboard']:12,.2f}/{r['spend_usde_chain']:12,.2f}  {r['usde_held_dashboard']:12,.2f}/{r['usde_held_chain']:12,.2f}  {r['top10_share_dashboard']*100:6.3f}%/{r['top10_share_chain']*100:6.3f}%")
with open(OUT / "chain_vs_dashboard_snapshots.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(cmp_rows[0].keys())); w.writeheader(); w.writerows(cmp_rows)
print(" at all nine snapshots the chain gives the same wallets that ever spent, the same 30-day and 7-day wallets and the same spend to the cent")
odd = [r for r in cmp_rows if abs(r["usde_held_dashboard"] - r["usde_held_chain"]) > 0.006]
assert len(odd) == 1
print(f" USDe held equals the dashboard to the cent at {len(cmp_rows) - 1} snapshots. At the snapshot generated {odd[0]['generated']} the dashboard shows {odd[0]['usde_held_dashboard']:,.2f},"
      f" the chain at the cut block {odd[0]['usde_held_chain']:,.2f} ({odd[0]['usde_held_dashboard'] - odd[0]['usde_held_chain']:+.2f}) and the chain at the run time {odd[0]['usde_held_chain_at_generated']:,.2f}")
moved = sum(1 for r in cmp_rows if r["usde_held_changed_before_run"] == "yes")
any_moved = sum(1 for r in cmp_rows if r["a_balance_statistic_changed_before_run"] == "yes")
lags = [r["seconds_before_generated"] for r in cmp_rows]
print(f" the cut block is {min(lags)} to {max(lags)} seconds before the run time; USDe held changed between the two at {moved} of the nine snapshots,"
      f" and some balance statistic changed at {any_moved}")
print(f" wallets created: the dashboard is higher by {sorted(set(r['created_dashboard'] - r['created_chain'] for r in cmp_rows))} (one factory-created contract is a beacon, not a wallet)")
c_two = [r for r in cmp_rows if r["created_dashboard"] - r["created_chain"] == 2]
assert all(r["created_chain_at_generated"] > r["created_chain"] for r in c_two)
print(f"   the gap is two at {len(c_two)} snapshots ({', '.join(r['generated'][:16] for r in c_two)}); at each of them a wallet was created between the cut block and the run time")
print(f" funded wallets: the dashboard is higher by {sorted(set(r['funded_dashboard'] - r['funded_chain'] for r in cmp_rows))};"
      f" summing balances in floating point, as the query does, raises the exact count by {sorted(set(r['funded_chain_float_sum'] - r['funded_chain'] for r in cmp_rows))}")
f_two = [r for r in cmp_rows if r["funded_dashboard"] - r["funded_chain"] == 2]
f_explained = [r for r in f_two if r["funded_chain_float_sum_at_generated"] == r["funded_dashboard"]]
assert all(r["funded_chain_float_sum"] == r["funded_dashboard"] for r in cmp_rows if r not in f_two)
print(f"   the gap is two at {len(f_two)} snapshots. At {len(f_explained)} of them ({', '.join(r['generated'][:16] for r in f_explained)}) the floating-point count at the run time equals the dashboard."
      f" At the other {len(f_two) - len(f_explained)} one wallet is unexplained")
print("   snapshot           dashboard  exact at cut  float at cut  exact at run  float at run")
for r in cmp_rows:
    print(f"   {r['generated'][:16]}   {r['funded_dashboard']:8d}  {r['funded_chain']:12d}  {r['funded_chain_float_sum']:12d}  {r['funded_chain_at_generated']:12d}  {r['funded_chain_float_sum_at_generated']:12d}")

# ----------------------------------------------------------------------------- B2. chain against the dashboard, day by day
print("\nB2. CHAIN AGAINST THE DASHBOARD, EVERY FULL DAY")
worst = dict(new_wallets=0, spend_count=0, active_wallets=0, spend_usde=0.0, deposits_usde=0.0, withdrawals_usde=0.0, reversals_usde=0.0, yield_usde=0.0, other_rewards_usde=0.0, tvl_usde=0.0)
full_days = [d for d in dates if d <= LAST_FULL]
for d in full_days:
    c, q = CDAY[d], day[d]
    pairs2 = dict(new_wallets=int(c["new_wallets_v1"]) + int(c["new_wallets_v2"]), spend_count=int(c["spend_events"]), active_wallets=int(c["spending_wallets"]),
                  spend_usde=int(c["spend_cents"]) / 100, deposits_usde=usd(int(c["deposits_wei"])), withdrawals_usde=usd(int(c["withdrawals_wei"])),
                  reversals_usde=usd(int(c["reversals_wei"])), yield_usde=usd(int(c["yield_wei"])), other_rewards_usde=usd(int(c["other_rewards_wei"])),
                  tvl_usde=usd(int(c["held_wei"])))
    for k, v in pairs2.items():
        diff = abs(q[k] - v)
        if k == "new_wallets" and d == "2026-05-15":
            assert q[k] - v == 1                               # the beacon contract, created with the first factory
            continue
        worst[k] = max(worst[k], diff)
print(f" {len(full_days)} days in the dashboard's daily series from {full_days[0]} to {full_days[-1]}. Largest difference on any day:")
print("  " + ", ".join(f"{k} {v:.4f}" for k, v in worst.items()))
assert worst["new_wallets"] == 0 and worst["spend_count"] == 0 and worst["active_wallets"] == 0 and worst["spend_usde"] < 0.01
assert max(worst[k] for k in ("deposits_usde", "withdrawals_usde", "reversals_usde", "yield_usde", "other_rewards_usde")) < 0.01 and worst["tvl_usde"] < 0.01
missing = [d for d in CDAY if d <= LAST_FULL and d not in day]
assert all(int(CDAY[d]["spend_events"]) == 0 and int(CDAY[d]["new_wallets_v1"]) + int(CDAY[d]["new_wallets_v2"]) == 0 for d in missing)
print(f"  days absent from the dashboard series because nothing happened on them: {missing}")
print("  new wallets, spend events and daily spending wallets are identical on every day; the only exception is one extra 'wallet' on 2026-05-15, the beacon contract")

# ----------------------------------------------------------------------------- B3. participation at the cutoff
print(f"\nB3. PARTICIPATION AT THE CUTOFF (block {CUT_BLOCK:,}, {CUT['cut_time']})")
print(" The dashboard notes that created, holding and ever spent are not sequential stages. The same holds here: four wallets that spent hold nothing now.")
created_cut = sum(1 for t in created if t <= CUT_TS)
ever_in = {w for w, a in ACT.items() if a["first_in"] is not None and a["first_in"] <= CUT_TS}
funded = {w for w, a in ACT.items() if a["bal"] > 0}
ever_spent = {r[2] for r in WD if r[1] <= J_LAST}
bcut = CUT["balances_at_cut_block"]
held_wei = sum(ACT[w]["bal"] for w in funded)
assert created_cut == CUT["wallets_created_at_cut_block"] and len(ever_in) == bcut["wallets_ever_received"]
assert len(funded) == bcut["funded"] == bc["wallets_with_balance"] and held_wei == int(bcut["held_wei"]) == int(bc["sum_wei"])
assert len(ever_spent) == CUT["wallets_ever_spent"] and not (ever_spent - ever_in)
ge = lambda x: sum(1 for w in funded if ACT[w]["bal"] >= x * E18)
assert ge(1) == bcut["ge_1"] and ge(100) == bcut["ge_100"] and ge(1000) == bcut["ge_1k"] and ge(10000) == bcut["ge_10k"] and ge(100000) == bcut["ge_100k"]
run_day_last = dnum(LAST["data"]["generated_at"][:10])
LF = dnum(LAST_FULL)
w30_last = {r[2] for r in WD if r[1] <= J_LAST and r[0] >= run_day_last - 30}
w7_last = {r[2] for r in WD if r[1] <= J_LAST and r[0] >= run_day_last - 7}
full7 = {r[2] for r in WD if LF - 6 <= r[0] <= LF}                 # the seven full days that end on the last full day
run_day_only = w7_last - full7
assert full7 <= w7_last and all(any(r[2] == w and r[0] == run_day_last and r[1] <= J_LAST for r in WD) for w in run_day_only)
funnel = [("wallets created", created_cut), ("ever received USDe", len(ever_in)), ("hold a balance above zero", len(funded)),
          ("hold 1 USDe or more", ge(1)), ("hold 100 USDe or more", ge(100)), ("ever spent", len(ever_spent)),
          ("spent in the 30-day window", len(w30_last)), ("spent in the 7-day window", len(w7_last))]
for name, v in funnel:
    print(f" {name:30s} {v:6,d}   {v/created_cut*100:6.2f}% of created")
print(f" never received any USDe: {created_cut - len(ever_in):,} = {(created_cut - len(ever_in))/created_cut*100:.1f}% of created; created wallets per wallet that ever received USDe: {created_cut/len(ever_in):.1f}")
print(f" of the {len(ever_in):,} that ever received USDe: {len(ever_spent):,} ever spent ({len(ever_spent)/len(ever_in)*100:.1f}%); {len(ever_in - funded)} are empty again")
print(f" of the {len(funded):,} holding a balance: {len(funded - ever_spent)} never spent; of the {len(ever_spent)} that ever spent: {len(ever_spent - funded)} are empty")
print(f" hold under 1 USDe: {len(funded) - ge(1)}; of which under one cent: {sum(1 for w in funded if ACT[w]['bal'] < E18 // 100)}")
print(f" the dashboard's 7-day window ({dstr(run_day_last - 7)} to the cutoff) holds {len(w7_last)} wallets; the seven full days {dstr(LF - 6)} to {LAST_FULL} hold {len(full7)};"
      f" {len(run_day_only)} wallets spent on {dstr(run_day_last)} before the cutoff and on none of the seven days before")
print(f" the dashboard's 30-day window starts {dstr(run_day_last - 30)} and holds {len(w30_last)}; every wallet in the 7-day window still held USDe at the cutoff: {w7_last <= funded}")
kinds = {k: sum(1 for w in ever_in if ACT[w]["kind"] == k) for k in ("d", "i", "r", "y", "o")}
print(f" first USDe came from outside the programme for {kinds['d']}, from another programme wallet for {kinds['i']}, from other sources for {kinds['r'] + kinds['y'] + kinds['o']}")
g_in = [(ACT[w]["first_in"] - created[w]) / DAY for w in ever_in]
g_sp = [(ACT[w]["first_spend"] - ACT[w]["first_in"]) / DAY for w in ever_spent]
first_spend_cut_ok = all(ACT[w]["first_spend"] <= CUT_TS for w in ever_spent)
assert first_spend_cut_ok
print(f" first USDe arrived within a day of creation for {sum(1 for g in g_in if g < 1)} of {len(g_in)} ({sum(1 for g in g_in if g < 1)/len(g_in)*100:.1f}%), within seven days for {sum(1 for g in g_in if g < 7)} ({sum(1 for g in g_in if g < 7)/len(g_in)*100:.1f}%), after more than thirty days for {sum(1 for g in g_in if g >= 30)}")
print(f" first spend came within a day of the first USDe for {sum(1 for g in g_sp if g < 1)} of {len(g_sp)} ({sum(1 for g in g_sp if g < 1)/len(g_sp)*100:.1f}%), within seven days for {sum(1 for g in g_sp if g < 7)} ({sum(1 for g in g_sp if g < 7)/len(g_sp)*100:.1f}%)")
with open(OUT / "participation.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["measure", "wallets", "share_of_created"])
    for name, v in funnel:
        w.writerow([name, v, round(v / created_cut, 6)])

# ----------------------------------------------------------------------------- B4. cohorts by creation date
print("\nB4. COHORTS BY CREATION DATE, AS OF THE CUTOFF")
by_day_created = {}
for i, d in enumerate(created_day):
    by_day_created.setdefault(d, []).append(i)
print(" busiest creation days: " + ", ".join(f"{dstr(d)} {len(v):,}" for d, v in sorted(by_day_created.items(), key=lambda kv: -len(kv[1]))[:6]))
for dname in ("2026-05-15", "2026-09-01", "2026-09-02"):
    ids = by_day_created[dnum(dname)]
    tss = [created[i] for i in ids]
    gaps = sorted(b - a for a, b in zip(tss, tss[1:]))
    hrs = [0] * 24
    for t in tss:
        hrs[(t % DAY) // 3600] += 1
    print(f"  {dname}: {len(ids):,} wallets, median gap {gaps[len(gaps)//2]} s; per UTC hour {hrs}")
sep1 = by_day_created[dnum("2026-09-01")]
before_noon = sum(1 for i in sep1 if created[i] % DAY < 12 * 3600)
print(f"  2026-09-01: {before_noon} wallets before 12:00 UTC and {len(sep1) - before_noon:,} after")
end_aug = sum(1 for d in created_day if d <= dnum("2026-08-31"))
may = sum(1 for d in created_day if d <= dnum("2026-05-31"))
print(f"  wallets at the end of August: {end_aug:,}, of which created May 15 to 31: {may:,} ({len(by_day_created[dnum('2026-05-15')])} on May 15 alone, {sum(1 for d in created_day if d <= dnum('2026-05-19')):,} by May 19) and June to August: {end_aug - may}")
print(f"  first qualifying spend event: {CM['first_spend_event']}; every May wallet came from the first factory: {all(factory[i] == 0 for i, d in enumerate(created_day) if d <= dnum('2026-05-31'))}")
cohorts = [("May 15 to 31", "2026-05-15", "2026-05-31"), ("June 1 to August 31", "2026-06-01", "2026-08-31"), ("September 1 and 2", "2026-09-01", "2026-09-02"),
           ("September 3 to 30", "2026-09-03", "2026-09-30"), ("October 1 to the cutoff", "2026-10-01", "2026-10-05")]
coh_rows = []
for name, a, b in cohorts:
    ws = [i for i in range(NW) if dnum(a) <= created_day[i] <= dnum(b) and created[i] <= CUT_TS]
    r = dict(cohort=name, created=len(ws), ever_received=sum(1 for w in ws if w in ever_in), holding_balance=sum(1 for w in ws if w in funded),
             holding_1_usde_or_more=sum(1 for w in ws if w in funded and ACT[w]["bal"] >= E18), ever_spent=sum(1 for w in ws if w in ever_spent))
    r["ever_received_share"] = round(r["ever_received"] / r["created"], 6); r["ever_spent_share"] = round(r["ever_spent"] / r["created"], 6)
    coh_rows.append(r)
    print(f" {name:26s} created {r['created']:6,d}  ever received USDe {r['ever_received']:5d} ({r['ever_received_share']*100:5.2f}%)  holding 1 USDe or more {r['holding_1_usde_or_more']:5d}"
          f"  ever spent {r['ever_spent']:5d} ({r['ever_spent_share']*100:5.2f}%)")
assert sum(r["created"] for r in coh_rows) == created_cut and sum(r["ever_spent"] for r in coh_rows) == len(ever_spent)
print(f"  share of all wallets created on September 1 and 2: {coh_rows[2]['created']/created_cut*100:.1f}%;"
      f" created from June 1 on: {created_cut - coh_rows[0]['created']:,}, of which ever received USDe {len(ever_in) - coh_rows[0]['ever_received']:,}"
      f" ({(len(ever_in) - coh_rows[0]['ever_received'])/(created_cut - coh_rows[0]['created'])*100:.1f}%)")
print(" like for like: within 14 days of creation, for wallets created by September 20 so that every wallet has had its 14 days")
for name, a, b in [("May 15 to 31", "2026-05-15", "2026-05-31"), ("June 1 to August 31", "2026-06-01", "2026-08-31"), ("September 1 and 2", "2026-09-01", "2026-09-02"), ("September 3 to 20", "2026-09-03", "2026-09-20")]:
    ws = [i for i in range(NW) if dnum(a) <= created_day[i] <= dnum(b)]
    assert all(created[i] + 14 * DAY <= CUT_TS for i in ws)
    rin = sum(1 for w in ws if w in ACT and ACT[w]["first_in"] is not None and ACT[w]["first_in"] - created[w] <= 14 * DAY)
    rsp = sum(1 for w in ws if w in ACT and ACT[w]["first_spend"] is not None and ACT[w]["first_spend"] - created[w] <= 14 * DAY)
    coh_rows.append(dict(cohort=name + " (within 14 days of creation)", created=len(ws), ever_received=rin, ever_spent=rsp,
                         ever_received_share=round(rin / len(ws), 6), ever_spent_share=round(rsp / len(ws), 6)))
    print(f"  {name:24s} created {len(ws):6,d}  received USDe within 14 days {rin:5d} ({rin/len(ws)*100:5.2f}%)  spent within 14 days {rsp:5d} ({rsp/len(ws)*100:5.2f}%)")
s12 = [i for i in range(NW) if dnum("2026-09-01") <= created_day[i] <= dnum("2026-09-02")]
s12_in = [w for w in s12 if w in ever_in]
s12_14 = sum(1 for w in s12_in if ACT[w]["first_in"] - created[w] <= 14 * DAY)
print(f"  of the {len(s12_in)} wallets from September 1 and 2 that had received USDe by the cutoff, {s12_14} received it within 14 days of creation and {len(s12_in) - s12_14} later")
with open(OUT / "cohorts.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["cohort", "created", "ever_received", "ever_received_share", "holding_balance", "holding_1_usde_or_more", "ever_spent", "ever_spent_share"])
    w.writeheader(); w.writerows(coh_rows)
# ----------------------------------------------------------------------------- B4b. the chain at the time of each public statement about access
import bisect
print("\nB4b. THE CHAIN AT THE TIME OF EACH PUBLIC STATEMENT ABOUT ACCESS")
# Each statement is summarized in this review's words. The post time is the time X shows for the post, read on 2026-10-06.
STATEMENTS = [("2026-09-01T11:59:55Z", "@ethena", "2094757140493910168", "the beta opens to a first group of 400 users, to widen each week"),
              ("2026-09-10T07:49:38Z", "@EthenaPay", "2097955643462394195", "waitlisted users will be added every day, 100 of them the next day"),
              ("2026-09-25T14:34:45Z", "@EthenaPay", "2103493415174619587", "1,600 people have the app and the number is growing"),
              ("2026-09-28T17:32:05Z", "@EthenaPay", "2104625202730856677", "readers are invited to download the app and join the waitlist")]
# A wallet address can receive USDe before its contract is deployed. One did. It counts from the later of the two times.
first_in_sorted = sorted(max(a["first_in"], created[w]) for w, a in ACT.items() if a["first_in"] is not None)
first_spend_sorted = sorted(a["first_spend"] for a in ACT.values() if a["first_spend"] is not None)
early_funded = [w for w, a in ACT.items() if a["first_in"] is not None and a["first_in"] < created[w]]
print(f" wallets that received USDe before their contract was deployed: {len(early_funded)}")
tl_rows = []
for when, account, status_id, quote in STATEMENTS + [(CUT["cut_time"], "", "", "the cutoff of this review")]:
    t = int(ts(when).timestamp())
    tl_rows.append(dict(time_utc=when, account=account, x_status_id=status_id, statement=quote, wallets_created=bisect.bisect_right(created, t),
                        ever_received_usde=bisect.bisect_right(first_in_sorted, t), ever_spent=bisect.bisect_right(first_spend_sorted, t)))
    r = tl_rows[-1]
    print(f" {when}  created {r['wallets_created']:6,d}  ever received USDe {r['ever_received_usde']:5,d}  ever spent {r['ever_spent']:4d}   {account} {quote}")
assert tl_rows[-1]["wallets_created"] == created_cut and tl_rows[-1]["ever_received_usde"] == len(ever_in) and tl_rows[-1]["ever_spent"] == len(ever_spent)
with open(OUT / "timeline.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(tl_rows[0].keys())); w.writeheader(); w.writerows(tl_rows)
sep25 = tl_rows[2]
print(f" on September 25 the 1,600 in the post is {1600/sep25['wallets_created']*100:.1f}% of the wallets created (one in {sep25['wallets_created']/1600:.1f}) and {1600/sep25['ever_received_usde']:.2f} times the wallets that had received USDe")
launch = tl_rows[0]
noon = int(ts("2026-09-01T12:00:00Z").timestamp()); midnight = int(ts("2026-09-02T00:00:00Z").timestamp())
print(f" wallets created from 12:00 to 24:00 UTC on September 1: {bisect.bisect_left(created, midnight) - bisect.bisect_left(created, noon):,}; between the first post of the thread and 12:00: {bisect.bisect_left(created, noon) - launch['wallets_created']}")
h11, h13 = noon - 3600, noon + 3600
print(f" wallets created from 11:00 to 12:00 UTC that day: {bisect.bisect_left(created, noon) - bisect.bisect_left(created, h11)}; from 12:00 to 13:00: {bisect.bisect_left(created, h13) - bisect.bisect_left(created, noon)}")
for d in ("2026-09-24", "2026-09-25"):
    cum = sum(int(CDAY[x]["spend_cents"]) for x in CDAY if x <= d) / 100
    print(f" end of {d}: lifetime spend {cum:,.2f} USDe, wallets created {int(CDAY[d]['wallets_created']):,}, ever received {int(CDAY[d]['wallets_ever_received'])}, ever spent {int(CDAY[d]['wallets_ever_spent'])}")

v1n, v2n = factory.count(0), factory.count(1)
print(f" factories: v1 created {v1n:,} wallets from {dstr(min(d for d, f in zip(created_day, factory) if f == 0))} to {dstr(max(d for d, f in zip(created_day, factory) if f == 0))};"
      f" v2 created {v2n:,} from {dstr(min(d for d, f in zip(created_day, factory) if f == 1))}")
aug_created = [len(by_day_created.get(d, [])) for d in range(dnum("2026-08-01"), dnum("2026-08-31") + 1)]
sep_rest = [len(by_day_created.get(d, [])) for d in range(dnum("2026-09-03"), dnum("2026-09-30") + 1)]
print(f" wallets created per day: August {min(aug_created)} to {max(aug_created)} (total {sum(aug_created)}); September 3 to 30 {min(sep_rest)} to {max(sep_rest)} (total {sum(sep_rest):,}, median {sorted(sep_rest)[len(sep_rest)//2]})")

# ----------------------------------------------------------------------------- B5. distinct spending wallets by calendar month
print("\nB5. DISTINCT SPENDING WALLETS BY CALENDAR MONTH (full days only; October holds four)")
mrows, seen, prev = [], set(), None
month_defs = [("June 2026", "2026-06-01", "2026-06-30"), ("July 2026", "2026-07-01", "2026-07-31"), ("August 2026", "2026-08-01", "2026-08-31"),
              ("September 2026", "2026-09-01", "2026-09-30"), ("October 1 to 4, 2026", "2026-10-01", LAST_FULL)]
assert all(r[0] >= dnum("2026-06-01") for r in WD)
for name, a, b in month_defs:
    rows_m = [r for r in WD if dnum(a) <= r[0] <= dnum(b)]
    ws = {r[2] for r in rows_m}
    days_active = {}
    for r in rows_m:
        days_active.setdefault(r[2], set()).add(r[0])
    new = ws - seen
    kept = len(ws & prev) if prev is not None else None
    ev_m, cents_m = sum(r[3] for r in rows_m), sum(r[4] for r in rows_m)
    m_dash = next(x for x in months if x["period"] == name)
    assert ev_m == m_dash["spend_events"] and abs(cents_m / 100 - m_dash["spend_usde"]) < 0.01      # same totals as the dashboard series
    buckets = [sum(1 for s_ in days_active.values() if lo <= len(s_) <= hi) for lo, hi in ((1, 1), (2, 5), (6, 14), (15, 31))]
    tx_m = sum(int(CDAY[d]["spend_transactions"]) for d in CDAY if a <= d <= b)       # a transaction falls on one day, so daily counts add up
    mrows.append(dict(period=name, days=dnum(b) - dnum(a) + 1, spending_wallets=len(ws), first_ever_spend_in_period=len(new), spent_in_an_earlier_period=len(ws) - len(new),
                      previous_period_wallets=len(prev) if prev is not None else None, of_which_spent_again=kept,
                      spend_events=ev_m, distinct_transactions=tx_m, spend_usde=cents_m / 100,
                      wallets_active_1_day=buckets[0], wallets_active_2_to_5_days=buckets[1], wallets_active_6_to_14_days=buckets[2], wallets_active_15_or_more_days=buckets[3]))
    r = mrows[-1]
    print(f" {name:22s} {r['spending_wallets']:4d} wallets ({r['first_ever_spend_in_period']:4d} first spend, {r['spent_in_an_earlier_period']:4d} earlier)"
          + (f"  {kept} of the previous period's {len(prev)} spent again ({kept/len(prev)*100:.0f}%)" if prev is not None else "")
          + f"  events {ev_m:6,d} in {tx_m:6,d} transactions  USDe {cents_m/100:12,.2f}  days active 1 / 2-5 / 6-14 / 15+: {buckets}")
    seen |= ws; prev = ws
with open(OUT / "months_wallets.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(mrows[0].keys())); w.writeheader(); w.writerows(mrows)
ma, ms = mrows[2], mrows[3]
print(f" September against August: spending wallets x{ms['spending_wallets']/ma['spending_wallets']:.2f}, spend events x{ms['spend_events']/ma['spend_events']:.2f}, spend USDe x{ms['spend_usde']/ma['spend_usde']:.2f}")
print(f" September: {ms['wallets_active_6_to_14_days'] + ms['wallets_active_15_or_more_days']} of {ms['spending_wallets']} wallets spent on six or more days"
      f" ({(ms['wallets_active_6_to_14_days'] + ms['wallets_active_15_or_more_days'])/ms['spending_wallets']*100:.1f}%); {ms['wallets_active_15_or_more_days']} on fifteen or more ({ms['wallets_active_15_or_more_days']/ms['spending_wallets']*100:.1f}%)")
sep_w, aug_w = set(), set()
for r in WD:
    if dnum("2026-09-01") <= r[0] <= dnum("2026-09-30"): sep_w.add(r[2])
    if dnum("2026-08-01") <= r[0] <= dnum("2026-08-31"): aug_w.add(r[2])
first_seen = {}
for r in sorted(WD):
    first_seen.setdefault(r[2], r[0])
skipped_aug = sum(1 for w in sep_w if first_seen[w] < dnum("2026-08-01") and w not in aug_w)
print(f" September wallets that had spent before August and not in August: {skipped_aug} (so first-time plus returning-from-August is {ms['first_ever_spend_in_period']} + {ms['of_which_spent_again']} = {ms['first_ever_spend_in_period'] + ms['of_which_spent_again']}, not {ms['spending_wallets']})")
print(f" the dashboard's daily spending wallets for September add up to {sum(day[d]['active_wallets'] for d in dates if '2026-09-01' <= d <= '2026-09-30'):,.0f}, which is not a count of wallets; the month had {ms['spending_wallets']} distinct ones")

# ----------------------------------------------------------------------------- B6. distinct spending wallets in seven-day periods ending on the last full day
print(f"\nB6. DISTINCT SPENDING WALLETS IN SEVEN-DAY PERIODS ENDING {LAST_FULL}")
wrows, wsets, prevw = [], [], None
for kback in range(9, -1, -1):
    b = LF - 7 * kback; a = b - 6
    rows_w = [r for r in WD if a <= r[0] <= b]
    ws = {r[2] for r in rows_w}
    ev_w, cents_w = sum(r[3] for r in rows_w), sum(r[4] for r in rows_w)
    assert ev_w == sum(day[dstr(d)]["spend_count"] for d in range(a, b + 1) if dstr(d) in day)
    kept = len(ws & prevw) if prevw is not None else None
    wrows.append(dict(period=f"{D0 + dt.timedelta(days=a):%b %-d} to {D0 + dt.timedelta(days=b):%b %-d}", first_day=dstr(a), last_day=dstr(b), spending_wallets=len(ws),
                      also_spent_in_previous_period=kept, not_in_previous_period=(len(ws) - kept) if kept is not None else None,
                      previous_period_wallets=len(prevw) if prevw is not None else None,
                      share_of_previous_period_that_spent_again=round(kept / len(prevw), 6) if kept is not None else None,
                      spend_events=ev_w, spend_usde=cents_w / 100))
    r = wrows[-1]
    print(f" {r['period']:18s} {len(ws):4d} wallets" + (f"  {kept:3d} also in the previous period ({kept/len(prevw)*100:4.1f}% of its {len(prevw):3d}), {len(ws)-kept:3d} not" if kept is not None else " " * 64)
          + f"  events {ev_w:5,d}  USDe {cents_w/100:10,.0f}")
    wsets.append(ws); prevw = ws
with open(OUT / "weeks_wallets.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(wrows[0].keys())); w.writeheader(); w.writerows(wrows)
wl_, w4 = wrows[-1], wrows[-5]
print(f" latest period against the period four weeks earlier ({w4['period']}): spending wallets x{wl_['spending_wallets']/w4['spending_wallets']:.2f},"
      f" spend events x{wl_['spend_events']/w4['spend_events']:.2f}, spend USDe x{wl_['spend_usde']/w4['spend_usde']:.2f}")
base_ws, last_ws = wsets[-5], wsets[-1]
ev_not_base = sum(r[3] for r in WD if LF - 6 <= r[0] <= LF and r[2] not in base_ws)
print(f" of the latest period's {wl_['spend_events']:,} events, {ev_not_base:,} ({ev_not_base/wl_['spend_events']*100:.1f}%) came from the {len(last_ws - base_ws)} wallets with no spend event in {w4['period']};"
      f" {wl_['spend_events'] - ev_not_base:,} came from the {len(last_ws & base_ws)} wallets that also spent then")
print(f" {w4['period']} holds September 1, the day the beta opened, and one day before it")
w5 = wrows[-6]
print(f" against the last period before the beta ({w5['period']}): spending wallets x{wl_['spending_wallets']/w5['spending_wallets']:.2f}, spend events x{wl_['spend_events']/w5['spend_events']:.2f}")
ret = [r["share_of_previous_period_that_spent_again"] for r in wrows[-5:]]
print(" share of the previous period's wallets that spent again, last five periods: " + ", ".join(f"{x*100:.1f}%" for x in ret) + f"  (lowest {min(ret)*100:.1f}%, highest {max(ret)*100:.1f}%)")
t30 = lambda e: len({r[2] for r in WD if e - 29 <= r[0] <= e})
print(f" thirty full days ending {LAST_FULL}: {t30(LF)} distinct spending wallets; thirty full days ending 2026-09-04: {t30(dnum('2026-09-04'))}")

# ----------------------------------------------------------------------------- B7. how concentrated the spend is, by wallet, at the cutoff
print("\nB7. SPEND BY WALLET AT THE CUTOFF")
by_w = {}
for d, seg, wlt, n, c in WD:
    if seg <= J_LAST:
        o = by_w.setdefault(wlt, [0, 0]); o[0] += n; o[1] += c
tot_ev, tot_c = sum(v[0] for v in by_w.values()), sum(v[1] for v in by_w.values())
assert tot_ev == H(LAST, "lifetime_spend_count") and len(by_w) == H(LAST, "spending_wallets")
by_usde = sorted(by_w.values(), key=lambda v: (-v[1], -v[0]))
by_events = sorted(by_w.values(), key=lambda v: (-v[0], -v[1]))
conc = []
for k in (1, 5, 10, 20, 50, 100):
    conc.append(dict(top_wallets=k, share_of_wallets=round(k / len(by_w), 6), usde_of_top_by_usde=sum(v[1] for v in by_usde[:k]) / 100,
                     share_of_spend_usde=round(sum(v[1] for v in by_usde[:k]) / tot_c, 6), their_share_of_events=round(sum(v[0] for v in by_usde[:k]) / tot_ev, 6),
                     share_of_events_of_top_by_events=round(sum(v[0] for v in by_events[:k]) / tot_ev, 6)))
    r = conc[-1]
    print(f" top {k:3d} wallets by USDe spent: {r['usde_of_top_by_usde']:12,.0f} USDe = {r['share_of_spend_usde']*100:5.1f}% of spend with {r['their_share_of_events']*100:5.1f}% of events;"
          f" top {k:3d} by events hold {r['share_of_events_of_top_by_events']*100:5.1f}% of events")
half, kh = 0, 0
for v in by_usde:
    half += v[1]; kh += 1
    if half * 2 >= tot_c:
        break
print(f" wallets needed to reach half of all USDe spent: {kh} of {len(by_w)} ({kh/len(by_w)*100:.1f}%); the largest spender by USDe has {by_usde[0][0]} events and {by_usde[0][1]/100:,.2f} USDe")
ev_b = [sum(1 for v in by_w.values() if lo <= v[0] <= hi) for lo, hi in ((1, 1), (2, 5), (6, 20), (21, 100), (101, 10 ** 9))]
print(f" wallets by lifetime events 1 / 2-5 / 6-20 / 21-100 / 101+: {ev_b}; five or fewer: {ev_b[0]+ev_b[1]} ({(ev_b[0]+ev_b[1])/len(by_w)*100:.1f}%); more than twenty: {ev_b[3]+ev_b[4]} ({(ev_b[3]+ev_b[4])/len(by_w)*100:.1f}%)")
few = [w for w, v in by_w.items() if v[0] <= 5]
recent = [w for w in few if ACT[w]["first_spend"] >= CUT_TS - 14 * DAY]
print(f" of the {len(few)} wallets with five or fewer events, {len(recent)} first spent in the 14 days before the cutoff")
with open(OUT / "spend_concentration.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(conc[0].keys())); w.writeheader(); w.writerows(conc)

# ----------------------------------------------------------------------------- B8. balances at the cutoff
print("\nB8. USDe BALANCES AT THE CUTOFF")
bals = sorted((ACT[w]["bal"] for w in funded), reverse=True)
edges = [("under 0.01", 0, E18 // 100), ("0.01 to 1", E18 // 100, E18), ("1 to 10", E18, 10 * E18), ("10 to 100", 10 * E18, 100 * E18), ("100 to 1,000", 100 * E18, 1000 * E18),
         ("1,000 to 10,000", 1000 * E18, 10000 * E18), ("10,000 to 100,000", 10000 * E18, 100000 * E18), ("100,000 and over", 100000 * E18, 10 ** 40)]
brows = []
for name, lo, hi in edges:
    sel = [x for x in bals if lo <= x < hi]
    brows.append(dict(balance_usde=name, wallets=len(sel), usde=round(usd(sum(sel)), 2), share_of_wallets=round(len(sel) / len(bals), 6), share_of_usde_held=round(sum(sel) / held_wei, 6)))
    print(f" {name:18s} {len(sel):5d} wallets ({len(sel)/len(bals)*100:5.1f}%)  {usd(sum(sel)):14,.2f} USDe ({sum(sel)/held_wei*100:6.2f}%)")
assert sum(r["wallets"] for r in brows) == len(bals)
with open(OUT / "balance_distribution.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(brows[0].keys())); w.writeheader(); w.writerows(brows)
top = lambda k: sum(bals[:k])
print(f" USDe held {usd(held_wei):,.2f}; largest wallet {usd(bals[0]):,.0f} ({bals[0]/held_wei*100:.1f}%); ten largest {usd(top(10)):,.0f} ({top(10)/held_wei*100:.2f}%);"
      f" fifty largest {top(50)/held_wei*100:.1f}%; hundred largest {top(100)/held_wei*100:.1f}%")
n10k, n1k = ge(10000), ge(1000)
print(f" {n10k} wallets with 10,000 USDe or more hold {top(n10k)/held_wei*100:.1f}%; {n1k} with 1,000 or more hold {top(n1k)/held_wei*100:.1f}%;"
      f" the other {len(bals) - n1k} hold {usd(held_wei - top(n1k)):,.0f} USDe ({(held_wei - top(n1k))/held_wei*100:.1f}%)")
never = funded - ever_spent
print(f" funded wallets that never spent: {len(never)} holding {usd(sum(ACT[w]['bal'] for w in never)):,.0f} USDe ({sum(ACT[w]['bal'] for w in never)/held_wei*100:.1f}% of USDe held)")
top10_ids = [w for w, _ in bcut["top20"][:10]]
assert sorted(ACT[w]["bal"] for w in top10_ids) == sorted(bals[:10])
spent_top10 = sum(by_w.get(w, [0, 0])[1] for w in top10_ids) / 100
low4 = sorted(top10_ids, key=lambda w: by_w.get(w, [0, 0])[1])[:4]
print(f" the ten largest balances belong to wallets that spent {spent_top10:,.2f} USDe in all ({spent_top10*100/tot_c*100:.1f}% of lifetime spend); {sum(1 for w in top10_ids if w not in by_w)} of them never spent")
print(f" four of the ten hold {usd(sum(ACT[w]['bal'] for w in low4)):,.0f} USDe and spent {sum(by_w.get(w, [0, 0])[1] for w in low4)/100:,.2f} USDe between them")
rank_spend = sorted(by_w, key=lambda w: (-by_w[w][1], -by_w[w][0], w))
spend_rank = {w: i + 1 for i, w in enumerate(rank_spend)}
rank_bal = sorted(funded, key=lambda w: (-ACT[w]["bal"], w))
assert set(rank_bal[:10]) == set(top10_ids)
print(" the ten largest balances, with each wallet's rank by USDe spent, USDe spent and events:")
for i, w in enumerate(rank_bal[:10]):
    print(f"   balance rank {i+1:2d}: {usd(ACT[w]['bal']):12,.0f} USDe   spend rank {str(spend_rank.get(w, 'none')):>4s}   spent {by_w.get(w, [0, 0])[1]/100:10,.2f} USDe in {by_w.get(w, [0, 0])[0]:3d} events")
print(f" ten largest balances that are also among the ten largest spenders: {len(set(rank_bal[:10]) & set(rank_spend[:10]))}; hundred largest balances among the hundred largest spenders: {len(set(rank_bal[:100]) & set(rank_spend[:100]))}")
big = [w for w in funded if ACT[w]["bal"] >= 1000 * E18]
print(f" wallets holding 1,000 USDe or more: {len(big)}, of which spent in the dashboard's 7-day window: {sum(1 for w in big if w in w7_last)}, ever spent: {sum(1 for w in big if w in ever_spent)}")
never_sorted = sorted(never, key=lambda w: -ACT[w]["bal"])
print(f" the two largest balances that never spent hold {usd(sum(ACT[w]['bal'] for w in never_sorted[:2])):,.0f} of the {usd(sum(ACT[w]['bal'] for w in never)):,.0f} USDe held by wallets that never spent")

# ----------------------------------------------------------------------------- B9. the ten largest wallets against all the others, over time
print("\nB9. THE TEN LARGEST WALLETS AGAINST ALL THE OTHERS")
trow = []
for c in CS:
    b = c["balances_at_cut_block"]
    h, t10, t1 = int(b["held_wei"]), int(b["top10_wei"]), int(b["top1_wei"])
    trow.append(dict(snapshot=c["generated"], funded=b["funded"], holding_1_or_more=b["ge_1"], holding_100_or_more=b["ge_100"], holding_1000_or_more=b["ge_1k"],
                     holding_10000_or_more=b["ge_10k"], holding_100000_or_more=b["ge_100k"], usde_held=round(usd(h), 2), ten_largest=round(usd(t10), 2),
                     all_others=round(usd(h - t10), 2), top10_share=round(t10 / h, 6), top1_share=round(t1 / h, 6), top50_share=round(int(b["top50_wei"]) / h, 6)))
    r = trow[-1]
    print(f" {c['generated'][:16]}  funded {r['funded']:5d}  1+ {r['holding_1_or_more']:5d}  100+ {r['holding_100_or_more']:4d}  1,000+ {r['holding_1000_or_more']:4d}  10,000+ {r['holding_10000_or_more']:3d}"
          f"  100,000+ {r['holding_100000_or_more']:2d}  held {r['usde_held']:12,.0f}  ten largest {r['ten_largest']:12,.0f}  others {r['all_others']:12,.0f}  top-10 {r['top10_share']*100:5.2f}%  top-1 {r['top1_share']*100:5.1f}%")
with open(OUT / "top10_vs_rest_snapshots.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(trow[0].keys())); w.writeheader(); w.writerows(trow)
fa, la = trow[0], trow[-1]
print(f" first to last snapshot: USDe held {fa['usde_held']:,.0f} to {la['usde_held']:,.0f} ({(la['usde_held']/fa['usde_held']-1)*100:+.1f}%); ten largest {fa['ten_largest']:,.0f} to {la['ten_largest']:,.0f}"
      f" ({(la['ten_largest']/fa['ten_largest']-1)*100:+.1f}%); all others {fa['all_others']:,.0f} to {la['all_others']:,.0f} (x{la['all_others']/fa['all_others']:.2f})")
print(f"  wallets holding 1,000 USDe or more {fa['holding_1000_or_more']} to {la['holding_1000_or_more']}; 1 USDe or more {fa['holding_1_or_more']} to {la['holding_1_or_more']}; top-1 share {fa['top1_share']*100:.1f}% to {la['top1_share']*100:.1f}%")
hi_s, lo_s = max(trow, key=lambda r: r["usde_held"]), min(trow, key=lambda r: r["usde_held"])
print(f"  across the nine snapshots USDe held was highest at {hi_s['usde_held']:,.0f} ({hi_s['snapshot'][:10]}) and lowest at {lo_s['usde_held']:,.0f} ({lo_s['snapshot'][:10]})")
print("  snapshot run times (UTC): " + ", ".join(c["generated"][11:16] for c in CS))
print(" the ten largest wallets of the first snapshot, then and at the cutoff")
old10 = CS[0]["balances_at_cut_block"]["top20"][:10]
then = sum(int(x) for _, x in old10); now = sum(ACT[w]["bal"] for w, _ in old10)
for wlt, x in old10:
    print(f"   wallet {wlt:5d} created {dstr(created_day[wlt])}  {usd(int(x)):12,.0f} -> {usd(ACT[wlt]['bal']):12,.0f}   lifetime spend {by_w.get(wlt, [0, 0])[1]/100:10,.2f} USDe in {by_w.get(wlt, [0, 0])[0]} events"
          + ("   still among the ten largest" if wlt in top10_ids else ""))
two = [w for w, x in old10 if int(x) > 900000 * E18]
print(f"   together {usd(then):,.0f} -> {usd(now):,.0f} ({usd(now - then):+,.0f}); {sum(1 for w, _ in old10 if w in top10_ids)} of the ten are still among the ten largest")
print(f"   the two wallets above 900,000 USDe held {usd(sum(int(x) for w, x in old10 if w in two)):,.0f} then and {usd(sum(ACT[w]['bal'] for w in two)):,.0f} at the cutoff")
for wlt in two:
    seen = []
    for c in CS:
        hit = [int(x) for w_, x in c["balances_at_cut_block"]["top20"] if w_ == wlt]
        seen.append(f"{c['generated'][5:10]} {usd(hit[0]):,.0f}" if hit else f"{c['generated'][5:10]} not in the twenty largest")
    print(f"   wallet {wlt}: " + "; ".join(seen) + f"; at the cutoff {usd(ACT[wlt]['bal']):,.0f}, with {by_w.get(wlt, [0, 0])[0]} spend events")
drows = []
for d in sorted(CDAY):
    if "2026-08-31" <= d <= LAST_FULL:
        c = CDAY[d]; h, t10 = int(c["held_wei"]), int(c["top10_wei"])
        drows.append(dict(date=d, usde_held=round(usd(h), 2), ten_largest=round(usd(t10), 2), all_others=round(usd(h - t10), 2), top10_share=round(t10 / h, 6),
                          largest_wallet=round(usd(int(c["top1_wei"])), 2), funded=int(c["funded"]), holding_1_or_more=int(c["ge_1"]), holding_100000_or_more=int(c["ge_100k"]),
                          deposits=round(usd(int(c["deposits_wei"])), 2), withdrawals=round(usd(int(c["withdrawals_wei"])), 2)))
with open(OUT / "top10_vs_rest_daily.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(drows[0].keys())); w.writeheader(); w.writerows(drows)
for d in ("2026-08-31", "2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04", "2026-09-14", "2026-09-15", "2026-09-16", "2026-09-21", "2026-09-22", "2026-10-04"):
    r = next(x for x in drows if x["date"] == d)
    print(f"  end of {d}: held {r['usde_held']:12,.0f}  ten largest {r['ten_largest']:12,.0f}  others {r['all_others']:12,.0f}  largest wallet {r['largest_wallet']:10,.0f}  funded {r['funded']:5d}  deposits {r['deposits']:11,.0f}  withdrawals {r['withdrawals']:11,.0f}")
dd = {x["date"]: x for x in drows}
print(f"  ten largest balances: end of Sep 14 {dd['2026-09-14']['ten_largest']:,.0f}, end of Sep 16 {dd['2026-09-16']['ten_largest']:,.0f} (change {dd['2026-09-16']['ten_largest'] - dd['2026-09-14']['ten_largest']:+,.0f});"
      f" largest single balance: end of Sep 21 {dd['2026-09-21']['largest_wallet']:,.0f}, end of Sep 22 {dd['2026-09-22']['largest_wallet']:,.0f}")
top_wd = sorted((d for d in dates if d <= LAST_FULL), key=lambda d: -day[d]["withdrawals_usde"])[:3]
print(f"  the three days with the largest withdrawals in the dashboard series: {sorted(top_wd)}")
print("  balances at the end of each week in the spending table")
wk_rows = []
for kback in range(5, -1, -1):
    d = dstr(LF - 7 * kback); c = CDAY[d]; h, t10 = int(c["held_wei"]), int(c["top10_wei"])
    wk_rows.append(dict(day_end=d, usde_held=round(usd(h), 2), ten_largest=round(usd(t10), 2), all_others=round(usd(h - t10), 2), top10_share=round(t10 / h, 6),
                        funded_wallets=int(c["funded"]), holding_1_or_more=int(c["ge_1"]), holding_1000_or_more=int(c["ge_1k"])))
    r = wk_rows[-1]
    print(f"   end of {d}: held {r['usde_held']:12,.0f}  ten largest {r['ten_largest']:12,.0f}  others {r['all_others']:12,.0f}  top-10 {r['top10_share']*100:5.1f}%  funded {r['funded_wallets']:5d}")
with open(OUT / "balances_week_ends.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(wk_rows[0].keys())); w.writeheader(); w.writerows(wk_rows)
assert all(b["all_others"] > a["all_others"] for a, b in zip(wk_rows, wk_rows[1:]))          # all other wallets grew at every week end
pk10 = max(drows, key=lambda x: x["ten_largest"])
wa, wb = wk_rows[0], wk_rows[-1]
print(f"   ten largest balances were highest at the end of {pk10['date']}: {pk10['ten_largest']:,.0f}; all others rose at every week end, from {wa['all_others']:,.0f} to {wb['all_others']:,.0f} (x{wb['all_others']/wa['all_others']:.1f});"
      f" funded wallets {wa['funded_wallets']} to {wb['funded_wallets']:,}; ten largest {wa['ten_largest']:,.0f} to {wb['ten_largest']:,.0f} (x{wb['ten_largest']/wa['ten_largest']:.1f})")
cross = next(x["date"] for x in drows if x["all_others"] > x["ten_largest"])
print(f"  first day on which all other wallets together held more than the ten largest: {cross}")
peak_c = max(drows, key=lambda x: x["usde_held"])
print(f"  highest end-of-day USDe held: {peak_c['usde_held']:,.0f} on {peak_c['date']}, of which {peak_c['ten_largest']:,.0f} in the ten largest")

# ----------------------------------------------------------------------------- B10. AllowanceSpent events that the counting rule leaves out
od = CM["other_destinations"]
print("\nB10. USDe AllowanceSpent EVENTS THAT DO NOT GO TO A SETTLEMENT ADDRESS (not counted as spend)")
print(f" all USDe AllowanceSpent logs from block 0: {od['usde_allowance_spent_logs_block_0_to_end']:,}; to a settlement address {od['to_a_settlement_address']:,};"
      f" to any other destination {od['to_any_other_destination']}, of which {od['other_from_programme_wallets']} from programme wallets ({od['programme_wallets_with_other_destination_events']} wallets,"
      f" {od['of_which_never_spent_to_a_settlement_address']} of them with no qualifying spend)")
to_wallets = [x for x in od["destinations"] if x["destination_is_programme_wallet"]]
elsewhere = [x for x in od["destinations"] if not x["destination_is_programme_wallet"]]
print(f" {sum(x['events_from_programme_wallets'] for x in to_wallets)} of them went to {len(to_wallets)} destinations that are programme wallets themselves;"
      f" {sum(x['events_from_programme_wallets'] for x in elsewhere)} went to {len(elsewhere)} other addresses")
for x in elsewhere:
    print(f"  {x['destination']}  {x['events_from_programme_wallets']:3d} events from {x['programme_wallets']:2d} wallets  {float(x['usde_from_programme_wallets']):10,.2f} USDe  {x['first'][:10]} to {x['last'][:10]}"
          f"  wallets with no qualifying spend: {x['of_which_never_spent_to_a_settlement_address']}")
assert sum(x["events_from_programme_wallets"] for x in od["destinations"]) == od["other_from_programme_wallets"]
assert od["other_from_programme_wallets"] + od["other_from_addresses_that_are_not_programme_wallets"] == od["to_any_other_destination"]
print(f" the remaining {od['other_from_addresses_that_are_not_programme_wallets']} events to other destinations were emitted by addresses that are not programme wallets;"
      f" {od['other_destinations_with_no_event_from_a_programme_wallet']} destinations received events only from such addresses and are not listed")
print(f" the other-destination events run through block {CM['end_block']:,}, the end of October 5, past the cutoff of this review")
print(f" share of all USDe AllowanceSpent events from programme wallets that the two-address rule counts: {od['to_a_settlement_address']/(od['to_a_settlement_address'] + od['other_from_programme_wallets'])*100:.2f}%")

fu = CM["first_usde_received_at_last_snapshot"]
print("\nB11. WHO SENT EACH WALLET ITS FIRST USDe, AT THE CUTOFF")
print(f" wallets that had received USDe: {fu['wallets']:,}; first USDe from outside the programme: {fu['from_outside_the_programme']}; from another programme wallet: {fu['from_another_programme_wallet']};"
      f" from a reversal or reward: {fu['from_a_reversal_or_reward']}")
print(f" programme wallets that sent some wallet its first USDe: {fu['programme_wallets_that_sent_a_first_usde']}; the largest such sender first-funded {fu['first_funded_by_the_largest_such_sender']} wallets"
      f" (five largest: {fu['first_funded_by_each_of_the_five_largest']})")
assert fu["wallets"] == len(ever_in) and fu["from_another_programme_wallet"] == kinds["i"] and fu["from_outside_the_programme"] == kinds["d"]

# ----------------------------------------------------------------------------- B12. an outside tracker against the recount
print("\nB12. PAYMENTSCAN AGAINST THE RECOUNT")
print(" Paymentscan's figures were read on paymentscan.xyz/cards/ethena-pay on 2026-10-06 at 04:41 and again at 07:02 UTC. They are typed in below as read.")
PAYMENTSCAN = [("July 2026", "2026-07-01", "2026-07-31", "$62.94K", 1034, 48), ("August 2026", "2026-08-01", "2026-08-31", "$259.8K", 4002, 116),
               ("September 2026", "2026-09-01", "2026-09-30", "$1.588M", 17387, 673), ("October 1 to 5, 2026", "2026-10-01", "2026-10-05", "$520.1K", 5698, 597),
               ("all months", "2026-05-15", "2026-10-05", "$2.431M", 28121, 810)]
d13 = dnum(SA["current"]["first_spend_event"][:10])                       # the day the current settlement address started, 2026-07-13
ev13, cents13, tx13 = sum(r[3] for r in WD if r[0] == d13), sum(r[4] for r in WD if r[0] == d13), int(CDAY[dstr(d13)]["spend_transactions"])
retired_last = int(ts(SA["retired"]["last_spend_event"]).timestamp())
ret13_ev = SA["retired"]["spend_events"] - sum(r[3] for r in WD if r[0] < d13)      # retired-address events and cents on that one shared day
ret13_cents = int(SA["retired"]["spend_cents"]) - sum(r[4] for r in WD if r[0] < d13)
assert 0 < ret13_ev < ev13 and 0 < ret13_cents < cents13
ps_rows = []
for name, a, b, ps_vol, ps_tx, ps_addr in PAYMENTSCAN:
    sel = [r for r in WD if dnum(a) <= r[0] <= dnum(b)]
    has13 = dnum(a) <= d13 <= dnum(b)
    cur_cents = sum(r[4] for r in sel if r[0] > d13) + ((cents13 - ret13_cents) if has13 else 0)
    tx_after = sum(int(CDAY[d]["spend_transactions"]) for d in CDAY if a <= d <= b and dnum(d) > d13)
    tx_lo, tx_hi = tx_after + ((tx13 - ret13_ev) if has13 else 0), tx_after + ((tx13 - 1) if has13 else 0)   # the retired events of July 13 sit in one to five transactions
    after, on13 = {r[2] for r in sel if r[0] > d13}, {r[2] for r in sel if r[0] == d13}
    # a wallet seen on July 13 only is counted for the current address when its first ever spend came after the retired address had stopped
    sure = {w for w in on13 - after if ACT[w]["first_spend"] > retired_last}
    w_after, w_from = len(after | sure), len(after | on13)
    ps_rows.append(dict(period=name, paymentscan_volume=ps_vol, paymentscan_transactions=ps_tx, paymentscan_active_addresses=ps_addr,
                        recount_spending_wallets=len({r[2] for r in sel}), recount_spend_events=sum(r[3] for r in sel),
                        recount_distinct_transactions=sum(int(CDAY[d]["spend_transactions"]) for d in CDAY if a <= d <= b), recount_spend_usde=sum(r[4] for r in sel) / 100,
                        current_address_only_usde=cur_cents / 100, current_address_only_transactions_low=tx_lo, current_address_only_transactions_high=tx_hi,
                        current_address_only_wallets_low=w_after, current_address_only_wallets_high=w_from))
    r = ps_rows[-1]
    print(f" {name:22s} Paymentscan {ps_vol:>8s} {ps_tx:6,d} tx {ps_addr:4d} addresses | recount, all addresses {r['recount_spend_usde']:13,.2f} USDe {r['recount_spend_events']:6,d} events {r['recount_distinct_transactions']:6,d} tx {r['recount_spending_wallets']:4d} wallets"
          f" | current address only {r['current_address_only_usde']:13,.2f} USDe {tx_lo:6,d} to {tx_hi:6,d} tx {w_after:4d} to {w_from:4d} wallets")
with open(OUT / "paymentscan_check.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(ps_rows[0].keys())); w.writeheader(); w.writerows(ps_rows)
jul, aug, sep, octo, allm = ps_rows
assert aug["recount_spending_wallets"] == aug["paymentscan_active_addresses"] and sep["recount_spending_wallets"] == sep["paymentscan_active_addresses"]
assert aug["recount_distinct_transactions"] == aug["paymentscan_transactions"] and octo["recount_distinct_transactions"] == octo["paymentscan_transactions"]
assert jul["current_address_only_wallets_low"] == jul["current_address_only_wallets_high"] == jul["paymentscan_active_addresses"]
assert jul["current_address_only_transactions_low"] == jul["paymentscan_transactions"]
assert octo["recount_spending_wallets"] == octo["paymentscan_active_addresses"] and allm["current_address_only_wallets_high"] == allm["paymentscan_active_addresses"]
assert f"{jul['current_address_only_usde'] / 1e3:.2f}" == "62.94" and f"{aug['recount_spend_usde'] / 1e3:.1f}" == "259.8" and f"{sep['recount_spend_usde'] / 1e6:.3f}" == "1.588"
assert f"{octo['recount_spend_usde'] / 1e3:.1f}" == "520.1" and f"{allm['current_address_only_usde'] / 1e6:.3f}" == "2.431"
jul_only_before = len({r[2] for r in WD if dnum("2026-07-01") <= r[0] <= dnum("2026-07-31")}) - jul["current_address_only_wallets_high"]
only13 = [w for w in {r[2] for r in WD if r[0] == d13} if not any(r[2] == w and dnum("2026-07-01") <= r[0] <= dnum("2026-07-31") and r[0] != d13 for r in WD)]
print(f" July: {jul_only_before} of the {jul['recount_spending_wallets']} wallets spent only before {dstr(d13)}. {len(only13)} spent in July on that day only, first at"
      f" {dt.datetime.fromtimestamp(ACT[only13[0]]['first_spend'], dt.timezone.utc):%H:%M:%S} UTC, after the retired address's last event at {SA['retired']['last_spend_event'][11:19]}")
print(f" September: Paymentscan shows {sep['recount_distinct_transactions'] - sep['paymentscan_transactions']} fewer transactions than the recount's distinct transactions. Not explained")
print(f" all months: Paymentscan's transaction total is {allm['current_address_only_transactions_low'] - allm['paymentscan_transactions']} below the lowest current-address count, the same September gap")
print(" every other Paymentscan figure equals the recount for the current settlement address alone, with July's transactions at the low end of the recount's range.")
print(" That Paymentscan counts transactions and follows only that address is an inference")

json.dump(dict(snapshots=rows, months=months, weeks=weeks, dune_vs_chain_sep11=xcheck, chain_vs_dashboard=cmp_rows, participation=funnel, cohorts=coh_rows,
               months_wallets=mrows, weeks_wallets=wrows, spend_concentration=conc, balance_distribution=brows, top10_vs_rest=trow, timeline=tl_rows, balances_week_ends=wk_rows,
               paymentscan_check=ps_rows),
          open(OUT / "results.json", "w"), indent=1)
print("\nwrote snapshots.csv, dune_vs_chain_sep11.csv, months.csv, weeks.csv, daily_series.csv, chain_vs_dashboard_snapshots.csv, participation.csv, cohorts.csv, timeline.csv,")
print("      months_wallets.csv, weeks_wallets.csv, spend_concentration.csv, balance_distribution.csv, top10_vs_rest_snapshots.csv, top10_vs_rest_daily.csv,")
print("      balances_week_ends.csv, paymentscan_check.csv, results.json")
