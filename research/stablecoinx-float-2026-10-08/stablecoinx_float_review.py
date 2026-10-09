#!/usr/bin/env python3
"""
Who holds StablecoinX's Class A shares, how many could trade freely, and how USDE traded against that count.

Reads the files in inputs/, runs every check below, stops on the first failure and writes the tables in out/.
Python 3 standard library only. No network.

    python3 stablecoinx_float_review.py
"""
import csv
import hashlib
import json
import statistics
from collections import OrderedDict
from datetime import date, timedelta
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).parent
IN, OUT = HERE / "inputs", HERE / "out"
OUT.mkdir(exist_ok=True)
LOG = []


def log(*parts):
    line = " ".join(str(p) for p in parts)
    LOG.append(line)
    print(line)


def check(cond, what):
    if not cond:
        raise SystemExit(f"CHECK FAILED: {what}")
    log("  ok", what)


def rows(name):
    with open(IN / name, newline="") as f:
        return list(csv.DictReader(f))


def pct(a, b, places=2):
    return f"{float(F(a) / F(b) * 100):.{places}f}"


# ---------------------------------------------------------------- pinned inputs
log("1. Pinned inputs")
for r in rows("manifest.csv"):
    digest = hashlib.sha256((IN / r["file"]).read_bytes()).hexdigest()
    check(digest == r["sha256"], f"{r['file']} matches its SHA-256 in manifest.csv")

facts = {r["key"]: r["value"] for r in rows("filing_facts.csv")}
N = {k: int(v) for k, v in facts.items() if v.isdigit()}
check(round(float(facts["ena_contributed"]) * float(facts["contribution_price_per_ena"])) == N["contribution_agreement_value_usd"],
      "284,954,407.29 ENA at $0.21056 is the contribution agreement's $60 million")

# ---------------------------------------------------------------- the merger's share table
log("2. The merger's share table, page F-16 of the resale prospectus")
table = OrderedDict((r["line"], int(r["shares"])) for r in rows("merger_share_table.csv"))
tlgy_class_a = table["Class A common stock of TLGY"]
check(table["TLGY Class A common stock outstanding prior to the Merger"] + table["Sponsor forfeiture"]
      + table["Redemption of TLGY Class A common stock"] == tlgy_class_a, "TLGY's lines add up to 635,939")
financing = (tlgy_class_a + table["PIPE shares"] + table["Ethena contribution shares"]
             + table["TLGY Class B common stock outstanding prior to the Merger"])
check(financing == table["Merger and PIPE financing shares"], "the financing subtotal is 23,329,375")
total_a = financing + table["Legacy Stablecoin X Assets Shares"] + table["Issuance of common stock to advisors"]
check(total_a == table["Class A Common Stock immediately after the Merger"] == N["class_a_outstanding_aug28"],
      "the table adds up to the 24,029,375 Class A shares the prospectus reports at August 28")
check(table["PIPE shares"] == N["placement_shares_total"], "the table's placement shares equal the 20,775,272 in the prospectus summary")
check(table["Ethena contribution shares"] == N["ethena_contribution_shares"], "contribution shares 1,813,164")
check(table["Legacy Stablecoin X Assets Shares"] == N["legacy_sc_assets_shares"], "SC Assets founders' shares 700,000")
check(-table["Sponsor forfeiture"] == N["tlgy_founder_shares_exchanged"] - N["tlgy_insider_retained_shares"],
      "the forfeiture is the 5,449,700 founder shares less the 644,590 retained")

tlgy_origin = tlgy_class_a + table["TLGY Class B common stock outstanding prior to the Merger"]
public_left = tlgy_origin - N["tlgy_insider_retained_shares"]
log(f"  TLGY-origin Class A {tlgy_origin:,}, of which TLGY's insiders retained {N['tlgy_insider_retained_shares']:,} "
    f"and public holders kept {public_left:,}")
public_before = table["TLGY Class A common stock outstanding prior to the Merger"] - (N["tlgy_founder_shares_exchanged"]
                                                                                    - table["TLGY Class B common stock outstanding prior to the Merger"])
check(public_before - (-table["Redemption of TLGY Class A common stock"]) == public_left,
      "public shares before redemption less the table's redemptions leave the same 96,349")
log(f"  public shares before the table's redemption {public_before:,}. The closing 8-K reports {N['public_shares_redeemed_8k']:,} "
    f"redeemed, {-table['Redemption of TLGY Class A common stock'] - N['public_shares_redeemed_8k']:,} fewer than the table")

# ---------------------------------------------------------------- freely tradable and restricted
log("3. Freely tradable and restricted shares at August 28")
placement_other = N["placement_shares_total"] - N["ethena_placement_shares"]
rebuilt_free = placement_other + public_left
check(rebuilt_free == N["freely_tradable_aug28"], "placement shares less Ethena's plus TLGY's public remainder equal the prospectus's 19,063,653")
ethena_a = N["ethena_contribution_shares"] + N["ethena_placement_shares"]
restricted = ethena_a + N["legacy_sc_assets_shares"] + N["tlgy_insider_retained_shares"]
check(restricted == N["bc_shares_offered_for_resale"], "Ethena, the founders and TLGY's insiders hold the 4,965,722 shares offered for resale")
check(restricted + rebuilt_free == N["class_a_outstanding_aug28"], "restricted plus freely tradable equal the Class A count")

holders = rows("holders_2026-08-28.csv")
by_group = OrderedDict()
for h in holders:
    g = by_group.setdefault(h["group"], {"a": 0, "b": 0, "rec": 0})
    g["a"] += int(h["class_a_shares"])
    g["b"] += int(h["class_b_shares"])
    g["rec"] += int(h["record_holders"] or 0)
check(by_group["placement"]["a"] == placement_other and by_group["public"]["a"] == public_left, "holder file matches the derived free groups")
check(by_group["ethena"]["a"] == ethena_a, "holder file Ethena 3,621,132")
check(by_group["founders"]["a"] == N["legacy_sc_assets_shares"], "holder file founders 700,000")
check(by_group["tlgy_insiders"]["a"] == N["tlgy_insider_retained_shares"], "holder file TLGY's insiders 644,590")
class_b = sum(g["b"] for g in by_group.values())
check(class_b == N["class_b_outstanding"], "Class B held by Ethena, the founders and TLGY's insiders adds up to 3,157,754")
check(by_group["ethena"]["b"] + by_group["founders"]["b"] + by_group["tlgy_insiders"]["b"] == class_b, "only the restricted holders hold Class B")
rec_b = by_group["ethena"]["rec"] + by_group["founders"]["rec"] + by_group["tlgy_insiders"]["rec"]
check(rec_b == N["holders_of_record_class_b"], "the 23 Class B holders of record are the 23 restricted holders")
for g in ("founders", "tlgy_insiders"):
    check(by_group[g]["a"] == by_group[g]["b"], f"{g} hold one Class B share for each Class A share")

directors = N["director_restricted_shares_each"] * N["directors_with_awards"]
class_a_oct8 = N["class_a_outstanding_aug28"] + directors
check(class_a_oct8 == N["dashboard_class_a_oct8"] == by_group["directors"]["a"] + N["class_a_outstanding_aug28"],
      "24,029,375 plus the directors' 110,000 is the dashboard's 24,139,375")
dash = json.loads((IN / "data_1cc3b05.json").read_text())
check(int(dash["shares_outstanding"]) == class_a_oct8 and dash["series"]["date"][-1] == "2026-10-08",
      "the dashboard dataset at 1cc3b05 carries 24,139,375 on its October 8 row")
f4 = [f for f in dash["insiders"] if f["form"] == "4"]
check(len(f4) == 8 and all(t["code"] == "A" for f in f4 for t in f["transactions"]),
      "the dashboard's insider feed holds eight Forms 4, all acquisitions, with no sale")
locked = N["legacy_sc_assets_shares"] + N["tlgy_insider_retained_shares"]

# ---------------------------------------------------------------- selling stockholders and votes
log("4. Selling stockholders, warrants and votes")
ss = rows("selling_stockholders_2026-08-28.csv")
for r in ss:
    check(int(r["offered_total"]) == int(r["shares"]) + int(r["rsus"]) + int(r["warrants"]), f"row adds up, {r['holder']}")
check(sum(int(r["offered_total"]) for r in ss) == N["total_offered_by_selling_holders"], "the table adds up to 12,668,943")
check(sum(int(r["shares"]) for r in ss) == N["bc_shares_offered_for_resale"], "its shares add up to 4,965,722")
check(sum(int(r["rsus"]) for r in ss) == N["rsu_shares_offered"], "its RSUs add up to 78,635")
sw = sum(int(r["warrants"]) for r in ss)
check(sw == N["warrant_shares_offered_by_selling_holders"] == N["tranche_a_sponsor_warrants"] + N["tranche_b_sponsor_warrants"],
      "its warrants add up to 7,624,586, Tranche A plus Tranche B")
cpc_par = next(r for r in ss if "Parallel" in r["holder"])
check(int(cpc_par["warrants"]) == 2_000_689 and int(cpc_par["warrants"]) + 999_000 == 2_999_689,
      "the parallel fund's warrants derive as 2,000,689, 999,000 below the 2,999,689 in footnotes (4) and (7)")

votes = OrderedDict([
    ("Ethena (Ethena OpCo Ltd)", by_group["ethena"]["b"]),
    ("Officers and directors", N["officers_directors_class_b"]),
    ("TLGY's former chairman", N["tlgy_former_chairman_class_b"]),
])
votes["Other former TLGY holders"] = class_b - sum(votes.values())
check(pct(votes["Ethena (Ethena OpCo Ltd)"], class_b) == facts["ethena_class_b_pct"], "Ethena 57.42% of Class B")
check(pct(votes["Officers and directors"], class_b) == facts["officers_directors_class_b_pct"], "officers and directors 34.71%")
check(pct(votes["TLGY's former chairman"], class_b) == facts["tlgy_former_chairman_class_b_pct"], "TLGY's former chairman 4.91%")
check(N["officers_directors_class_b"] == 323_750 + 323_750 + 52_500 + 215_891 + 180_239,
      "officers and directors' 1,096,130 are the founders' 700,000 and the two CPC funds' 396,130")
check(N["tlgy_former_chairman_class_b"] == 63_149 + 50_196 + 41_766, "TLGY's former chairman's 155,111 are TLGY Sponsors, TLGY Holdings and the trust")
check(pct(N["tlgy_insider_retained_shares"], class_b) == "20.41", "TLGY's insiders 20.41%, as the closing 8-K says")
log("  votes " + ", ".join(f"{k} {v:,} ({pct(v, class_b)}%)" for k, v in votes.items()))

# ---------------------------------------------------------------- volume
log("5. Daily volume, first USDE session to October 8")
spg = {r["date"]: r for r in rows("usde_daily_spglobal_stockanalysis.csv")}
yah = {r["date"]: r for r in rows("usde_daily_yahoo.csv")}
first = facts["first_trading_day"]
days = sorted(d for d in spg if d >= first)
check(days[0] == "2026-06-26" and days[-1] == "2026-10-08" and len(days) == 73, "73 sessions from June 26 to October 8")
check(sorted(yah) == days, "Yahoo has the same 73 sessions")
check(all(abs(float(spg[d]["close"]) - float(yah[d]["close"])) < 0.005 for d in days), "closes agree to the cent on every session")
check(all(abs(float(spg[d]["close"]) - c) < 0.005 for d, c in zip(dash["series"]["date"], dash["series"]["usde_close"])
          if d in spg), "S&P Global closes match the dashboard's series")
vol = {d: int(spg[d]["volume"]) for d in days}
voly = {d: int(yah[d]["volume"]) for d in days}
total = sum(vol.values())
totaly = sum(voly.values())
free = N["freely_tradable_aug28"]
maxdiff = max(abs(voly[d] - vol[d]) / vol[d] for d in days)
check(abs(totaly - total) / total < 0.001, "the two sources' totals agree within 0.1%")
log(f"  total {total:,} shares (Yahoo {totaly:,}, {totaly - total:+,}). Largest daily gap {maxdiff * 100:.2f}%")
multiple = F(total, free)
log(f"  {float(multiple):.4f} times the freely tradable count")
months = OrderedDict()
for d in days:
    m = months.setdefault(d[:7], [])
    m.append(vol[d])
month_rows = []
for m, v in months.items():
    adv = F(sum(v), len(v))
    month_rows.append({
        "month": m, "sessions": len(v), "volume": sum(v), "average_daily": f"{float(adv):.0f}",
        "average_daily_pct_of_free": f"{float(adv / free * 100):.1f}", "highest_day": max(v),
        "times_free_in_month": f"{float(F(sum(v), free)):.2f}",
    })
    log(f"  {m} sessions {len(v)} volume {sum(v):,} average {float(adv):,.0f} ({float(adv / free * 100):.1f}% of free) top {max(v):,}")
check(sum(r["volume"] for r in month_rows) == total, "months add up to the total")
avg_all = F(total, len(days))
log(f"  all sessions average {float(avg_all):,.0f} = {float(avg_all / free * 100):.1f}% of free")
big = [(d, vol[d]) for d in days if vol[d] > free]
check([d for d, _ in big] == ["2026-07-02", "2026-08-21", "2026-08-27"], "three sessions traded more than the freely tradable count")
for d, v in big:
    log(f"  {d} {v:,} = {float(F(v, free)):.2f} times")
median = statistics.median(vol.values())
log(f"  median session {median:,} = {float(F(median) / free * 100):.1f}% of free")
sept = month_rows[3]
check(sept["month"] == "2026-09", "September row")
sept_adv = F(sept["volume"], sept["sessions"])
eff_day, eff_time = facts["resale_registration_effective"].split("T")
check(eff_time == "16:00", "the registration took effect at 4:00 pm, when the session closed")
since_effective = [d for d in days if d > eff_day]
check(since_effective[0] == "2026-09-15", "the first session after it was September 15")
vol_since = sum(vol[d] for d in since_effective)
log(f"  from September 15 to October 8, {len(since_effective)} sessions, {vol_since:,} shares")
median_locked = F(locked) / F(median)
log(f"  locked shares {locked:,} = {float(median_locked * 100):.1f}% of the median session")

cum = 0
daily = []
for d in days:
    cum += vol[d]
    daily.append({"date": d, "close": spg[d]["close"], "volume_spglobal": vol[d], "volume_yahoo": voly[d],
                  "volume_pct_of_free": f"{vol[d] / free * 100:.2f}", "cumulative_volume": cum,
                  "cumulative_times_free": f"{cum / free:.4f}"})
check(daily[-1]["cumulative_volume"] == total, "cumulative ends at the total")

# ---------------------------------------------------------------- 13F
log("6. Form 13F reports for June 30, 2026")
f13 = rows("13f_june30_2026.csv")
cls_a = [r for r in f13 if r["cusip"].upper() == "85238K100"]
wts_all = [r for r in f13 if r["cusip"].upper() == "85238K118" and "counted once" not in r["note"]]
wts = [r for r in wts_all if r["put_call"] == ""]
check(sum(int(r["shares"]) for r in wts_all) == 5_957_302 and len(wts_all) - len(wts) == 1,
      "28 managers' warrant rows add up to 5,957,302, one of them a call row of 30,000")
held_13f = sum(int(r["shares"]) for r in cls_a)
check(len(cls_a) == 7 and held_13f == 1_531_657, "seven managers reported 1,531,657 Class A shares")
check(all(r["period"] == "2026-06-30" for r in f13), "all report June 30")
wt_total = sum(int(r["shares"]) for r in wts)
check(len({r["filer_cik"] for r in wts}) == 27 and wt_total == 5_927_302, "without the call row, 27 managers reported 5,927,302 public warrants")
from_elsewhere = held_13f - sum(vol[d] for d in days if d <= "2026-06-30") - public_left
check(from_elsewhere == 400_342, "at least 400,342 of the managers' shares came from neither the first three sessions nor TLGY's public holders")
log(f"  Class A {held_13f:,} = {pct(held_13f, free)}% of free, {pct(held_13f, N['class_a_outstanding_aug28'])}% of Class A")
log(f"  warrants {wt_total:,} = {pct(wt_total, N['public_warrants'])}% of public warrants")
top = sorted(cls_a, key=lambda r: -int(r["shares"]))

# ---------------------------------------------------------------- filings and dates
log("7. Filings and dates")
ed = rows("edgar_filings_2026-10-09.csv")
forms = [r["form"] for r in ed]
check(not any(f.startswith(("SC 13", "SCHEDULE 13", "144")) for f in forms), "no Schedule 13D or 13G and no Form 144 on the list")
check(sum(f == "4" for f in forms) == 8 and sum(f == "3" for f in forms) == 8, "eight Forms 3 and eight Forms 4")
check("EFFECT" in forms, "the EFFECT notice is on the list")
closing = date.fromisoformat(facts["closing_date"])
lockup_end = date(closing.year, closing.month + N["lockup_months_after_closing"], closing.day)
check(lockup_end == date(2026, 12, 25) and lockup_end.weekday() == 4, "six months after June 25, 2026 is Friday, December 25, 2026, Christmas Day")
first_after = lockup_end + timedelta(days=3)
check(first_after == date(2026, 12, 28) and first_after.weekday() == 0, "the first session after it is Monday, December 28")
f10 = date.fromisoformat(facts["form10_information_filed"])
r144 = date(f10.year + 1, f10.month, f10.day)
check(r144 == date(2027, 7, 2), "a year after the July 2, 2026 Form 10 information is July 2, 2027")
q3_due = date(2026, 9, 30) + timedelta(days=45)
check(q3_due == date(2026, 11, 14), "45 days after September 30 is November 14")

# ---------------------------------------------------------------- outputs
groups = [
    ("Placement investors other than Ethena", placement_other, "Freely tradable"),
    ("TLGY public holders who did not redeem", public_left, "Freely tradable"),
    ("Ethena (Ethena OpCo Ltd)", ethena_a, "Registered for resale from 4:00 pm on September 14. Affiliate. The prospectus says no contractual lock-up"),
    ("SC Assets' original shareholders", N["legacy_sc_assets_shares"], "Registered for resale. The prospectus and the 8-K say locked up to December 25, 2026"),
    ("TLGY's insiders", N["tlgy_insider_retained_shares"], "Registered for resale. The prospectus and the 8-K say locked up to December 25, 2026"),
    ("Directors' restricted stock", directors, "Granted September 30, 2026. Vests in four quarterly steps from October 1"),
]
with open(OUT / "holders_reconciled.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["holder_group", "class_a_shares", "pct_of_class_a_aug28", "pct_of_class_a_oct8", "class_b_shares", "status"])
    bmap = {"Ethena (Ethena OpCo Ltd)": by_group["ethena"]["b"], "SC Assets' original shareholders": by_group["founders"]["b"],
            "TLGY's insiders": by_group["tlgy_insiders"]["b"]}
    for name, n, status in groups:
        w.writerow([name, n, pct(n, N["class_a_outstanding_aug28"]) if name != "Directors' restricted stock" else "",
                    pct(n, class_a_oct8), bmap.get(name, 0), status])
    w.writerow(["Total", class_a_oct8, "", "100.00", class_b, ""])
with open(OUT / "daily_volume.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(daily[0]))
    w.writeheader()
    w.writerows(daily)
with open(OUT / "volume_by_month.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(month_rows[0]))
    w.writeheader()
    w.writerows(month_rows)
with open(OUT / "votes_class_b.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["holder", "class_b_shares", "pct_of_votes"])
    for k, v in votes.items():
        w.writerow([k, v, pct(v, class_b)])
with open(OUT / "form13f_class_a_june30.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["manager", "class_a_shares", "filed", "accession"])
    for r in top:
        w.writerow([r["filer"], r["shares"], r["filed"], r["accession"]])
with open(OUT / "chart_turnover.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "volume", "cumulative_volume", "cumulative_times_free"])
    for r in daily:
        w.writerow([r["date"], r["volume_spglobal"], r["cumulative_volume"], r["cumulative_times_free"]])

results = OrderedDict([
    ("class_a_aug28", N["class_a_outstanding_aug28"]), ("class_a_oct8", class_a_oct8),
    ("freely_tradable", free), ("freely_tradable_pct_aug28", pct(free, N["class_a_outstanding_aug28"])),
    ("freely_tradable_pct_oct8", pct(free, class_a_oct8)),
    ("placement_other", placement_other), ("public_left", public_left), ("ethena_class_a", ethena_a),
    ("restricted", restricted), ("restricted_pct_aug28", pct(restricted, N["class_a_outstanding_aug28"])),
    ("locked_to_dec25", locked), ("directors", directors), ("class_b", class_b),
    ("votes_pct", {k: pct(v, class_b) for k, v in votes.items()}),
    ("sessions", len(days)), ("volume_total", total), ("average_session", f"{float(avg_all):.0f}"),
    ("average_session_pct_free", f"{float(avg_all / free * 100):.1f}"), ("volume_total_yahoo", totaly),
    ("times_free", f"{float(multiple):.2f}"), ("median_session", median),
    ("median_pct_of_free", f"{float(F(median) / free * 100):.1f}"),
    ("big_days", {d: [v, f"{float(F(v, free)):.2f}"] for d, v in big}),
    ("months", month_rows), ("locked_pct_median_session", f"{float(median_locked * 100):.1f}"),
    ("free_or_ethena_oct8", free + ethena_a), ("free_or_ethena_pct_oct8", pct(free + ethena_a, class_a_oct8, 1)),
    ("from_elsewhere_13f", from_elsewhere),
    ("sessions_since_effective", len(since_effective)), ("volume_since_effective", vol_since),
    ("f13_class_a", held_13f), ("f13_class_a_pct_free", pct(held_13f, free)),
    ("f13_class_a_pct_class_a", pct(held_13f, N["class_a_outstanding_aug28"])),
    ("f13_managers_class_a", len(cls_a)), ("f13_warrants", wt_total), ("f13_warrant_managers", len(wts)),
    ("f13_warrants_pct_public", pct(wt_total, N["public_warrants"])),
    ("lockup_end", lockup_end.isoformat()), ("rule144_earliest", r144.isoformat()),
    ("redemption_gap", -table["Redemption of TLGY Class A common stock"] - N["public_shares_redeemed_8k"]),
])
(OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
(OUT / "run_log.txt").write_text("\n".join(LOG) + "\n")
print("wrote out/")
