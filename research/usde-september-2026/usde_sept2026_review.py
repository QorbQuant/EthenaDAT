#!/usr/bin/env python3
"""
StablecoinX (Nasdaq: USDE) September 2026 valuation review.
Reproduces every number in the draft article from dated inputs.

Run from this folder:  python3 usde_sept2026_review.py

Inputs (all in ./inputs)
  ethenadat_data_759f283.json
      EthenaDash dataset exactly as committed in QorbQuant/EthenaDAT at commit
      759f283adff372f05678de909efe099db6791ce6 (2026-10-05T21:53:53Z), file docs/data.json.
      Raw URL: https://raw.githubusercontent.com/QorbQuant/EthenaDAT/759f283adff372f05678de909efe099db6791ce6/docs/data.json
      Fields used: series.date, usde_close (Yahoo Finance), ena_price (CoinGecko daily),
      ena_holdings and shares_outstanding (hand-maintained from SEC filings).
  ena_coingecko_via_defillama.csv
      CoinGecko ENA/USD as served by DefiLlama's price API, fetched 2026-10-05.
      utc0000 = 00:00 UTC stamps, utc2000 = 20:00 UTC stamps (20:00 UTC = 16:00 New York
      while daylight time applies, which covers every date in this file).
      https://coins.llama.fi/chart/coingecko:ethena?start=1788048000&span=40&period=1d
      https://coins.llama.fi/chart/coingecko:ethena?start=1787947200&span=40&period=1d
  kraken_enausd_4h.json
      Kraken ENAUSD 4-hour candles from Aug 28 16:00 UTC, an independent exchange check on both ENA series.
  usde_spglobal_via_stockanalysis.csv
      USDE daily OHLCV from stockanalysis.com (S&P Global Market Intelligence), an
      independent check on the Yahoo closes in the dataset.
  coinbase_ena_usd_hourly_spotchecks.csv
      Coinbase ENA-USD hourly candles at five 20:00 UTC timestamps.

Naming
  "dashboard series" = the dataset's daily ENA price. It is CoinGecko's daily stamp at 00:00 UTC of the
      session date, which is 8 pm New York on the evening before and 20 hours before the 4 pm Nasdaq close.
  "at the close"     = CoinGecko ENA at 20:00 UTC on the session date, the 4 pm New York close.
  "utcday"           = CoinGecko's next daily stamp, 00:00 UTC of the following day, four hours after the close.

Method
  Share price P = E x S x M
      E = ENA price, S = ENA per share = reported ENA / Class A shares,
      M = mNAV = P / (E x S), recomputed from the inputs (never from a rounded ratio).
  Attribution = three-factor Shapley value, the average over all six orders of switching
  E, S and M from their start values to their end values. Identical to shapley() in the
  dashboard's docs/assets/valuation.js. The three contributions sum to the price change.
  This is arithmetic on two endpoints. It is not a statement about why anyone traded.
"""
import csv
import datetime as dt
import json
import math
import statistics as st
from itertools import permutations
from pathlib import Path

HERE = Path(__file__).parent
INP, OUT = HERE / "inputs", HERE / "out"
OUT.mkdir(exist_ok=True)
UTC = dt.timezone.utc

MONTH_START, MONTH_END = "2026-08-31", "2026-09-30"   # last close of August, last close of September
SPLIT = "2026-09-16"                                   # the session where mNAV at the close was lowest in the window (asserted below)


def ts(date, hour):
    y, m, d = map(int, date.split("-"))
    return int(dt.datetime(y, m, d, hour, tzinfo=UTC).timestamp())


def next_day(date):
    y, m, d = map(int, date.split("-"))
    return (dt.date(y, m, d) + dt.timedelta(days=1)).isoformat()


# ----------------------------------------------------------------------------- inputs
D = json.loads((INP / "ethenadat_data_759f283.json").read_text())
S = D["series"]
rec = {d: dict(P=S["usde_close"][i], E=S["ena_price"][i], H=S["ena_holdings"][i],
               N=S["shares_outstanding"][i], W=S["usdew_close"][i])
       for i, d in enumerate(S["date"])}
dates = S["date"]

cg0000, cg2000 = {}, {}
with open(INP / "ena_coingecko_via_defillama.csv") as f:
    for r in csv.DictReader(f):
        (cg0000 if r["series"] == "utc0000" else cg2000)[int(r["unix_ts"])] = float(r["price_usd"])

kraken = json.loads((INP / "kraken_enausd_4h.json").read_text())["rows"]
kr_open = {r[0]: float(r[1]) for r in kraken}

spg = {}
with open(INP / "usde_spglobal_via_stockanalysis.csv") as f:
    for r in csv.DictReader(f):
        spg[r["date"]] = dict(close=float(r["close"]), high=float(r["high"]), volume=int(r["volume"]))

cb = list(csv.DictReader(open(INP / "coinbase_ena_usd_hourly_spotchecks.csv")))


# ----------------------------------------------------------------------------- observations
def obs(date, basis):
    """basis: 'dashboard' = the dashboard series, the dataset's ENA price (00:00 UTC stamp of the session date,
                           which is 8 pm New York the evening before)
              'close'    = CoinGecko ENA at 20:00 UTC on the session date (the Nasdaq close)
              'utcday'   = CoinGecko ENA at 00:00 UTC of the next day (UTC day close, 4h after the Nasdaq close)"""
    r = rec[date]
    if basis == "dashboard":
        E = r["E"]
    elif basis == "close":
        E = cg2000[ts(date, 20)]
    elif basis == "utcday":
        E = cg0000[ts(next_day(date), 0)]
    else:
        raise ValueError(basis)
    Sps = r["H"] / r["N"]
    return dict(date=date, basis=basis, P=r["P"], E=E, S=Sps, M=r["P"] / (E * Sps),
                nav_ps=E * Sps, nav=E * r["H"], cap=r["P"] * r["N"], H=r["H"], N=r["N"])


def shapley(a, b):
    keys = ("E", "S", "M")
    phi = dict.fromkeys(keys, 0.0)
    rows = []
    for order in permutations(keys):
        cur = {k: a[k] for k in keys}
        step = {}
        for k in order:
            before = cur["E"] * cur["S"] * cur["M"]
            cur[k] = b[k]
            step[k] = cur["E"] * cur["S"] * cur["M"] - before
            phi[k] += step[k] / 6
        rows.append(("".join(order), step))
    return phi, rows


def attribute(start, end, basis, label):
    a, b = obs(start, basis), obs(end, basis)
    phi, orders = shapley(a, b)
    dP = b["P"] - a["P"]
    assert abs(sum(phi.values()) - dP) < 1e-9, "Shapley contributions must sum to the price change"
    logs = dict(P=math.log(b["P"] / a["P"]), E=math.log(b["E"] / a["E"]),
                S=math.log(b["S"] / a["S"]), M=math.log(b["M"] / a["M"]))
    return dict(label=label, basis=basis, start=start, end=end, a=a, b=b, dP=dP,
                pctP=b["P"] / a["P"] - 1, pctE=b["E"] / a["E"] - 1, pctS=b["S"] / a["S"] - 1,
                pctM=b["M"] / a["M"] - 1, pctNAV=b["nav_ps"] / a["nav_ps"] - 1,
                phi=phi, share={k: v / dP for k, v in phi.items()}, orders=orders, logs=logs)


def show(r, orders=False):
    a, b = r["a"], r["b"]
    print(f"\n== {r['label']} | {r['start']} -> {r['end']} | ENA basis: {r['basis']}")
    print(f"   USDE close      {a['P']:9.2f} -> {b['P']:9.2f}   {r['dP']:+.2f}  ({r['pctP']*100:+.2f}%)")
    print(f"   ENA price       {a['E']:9.6f} -> {b['E']:9.6f}   ({r['pctE']*100:+.2f}%)")
    print(f"   ENA per share   {a['S']:9.4f} -> {b['S']:9.4f}   ({r['pctS']*100:+.3f}%)")
    print(f"   token NAV/share {a['nav_ps']:9.4f} -> {b['nav_ps']:9.4f}   ({r['pctNAV']*100:+.2f}%)")
    print(f"   mNAV            {a['M']:9.4f} -> {b['M']:9.4f}   ({r['pctM']*100:+.2f}%)")
    p, s = r["phi"], r["share"]
    print(f"   Shapley $/share: ENA {p['E']:+.4f} | ENA per share {p['S']:+.4f} | mNAV {p['M']:+.4f} | sum {sum(p.values()):+.4f}")
    print(f"   share of move:   ENA {s['E']*100:.1f}% | ENA per share {s['S']*100:.1f}% | mNAV {s['M']*100:.1f}%")
    L = r["logs"]
    print(f"   log check:       ln P {L['P']:+.4f} = ln E {L['E']:+.4f} + ln S {L['S']:+.4f} + ln M {L['M']:+.4f}"
          f"  (shares {L['E']/L['P']*100:.1f}% / {L['S']/L['P']*100:.1f}% / {L['M']/L['P']*100:.1f}%)")
    if orders:
        print("   order   dE        dS        dM")
        for name, st_ in r["orders"]:
            print(f"   {name}   {st_['E']:+.4f}  {st_['S']:+.4f}  {st_['M']:+.4f}")


# ----------------------------------------------------------------------------- cross-checks
print("CROSS-CHECKS")
sess = [d for d in dates if "2026-08-28" <= d <= "2026-10-02"]
# 1. dataset ENA equals CoinGecko's 00:00 UTC stamp for the session date
mx = 0.0
for d in sess:
    if ts(d, 0) in cg0000:
        diff = abs(rec[d]["E"] - round(cg0000[ts(d, 0)], 6))
        mx = max(mx, diff)
        assert diff < 1.5e-6, (d, rec[d]["E"], cg0000[ts(d, 0)])
print(f" 1. dashboard series ENA == CoinGecko 00:00 UTC stamp of the session date, to 6 decimals (max abs diff {mx:.1e})"
      f" for {sum(1 for d in sess if ts(d,0) in cg0000)} sessions")
# 2. dataset USDE closes equal S&P Global closes
for d in sess:
    assert abs(rec[d]["P"] - spg[d]["close"]) < 1e-9, (d, rec[d]["P"], spg[d]["close"])
print(f" 2. dataset USDE close == S&P Global close for all {len(sess)} sessions {sess[0]}..{sess[-1]}")
# 3. Kraken exchange candles vs both CoinGecko series
k0, k20 = [], []
for d in sess:
    if ts(d, 0) in kr_open and ts(d, 0) in cg0000:
        k0.append(abs(kr_open[ts(d, 0)] / cg0000[ts(d, 0)] - 1))
    if ts(d, 20) in kr_open:
        k20.append(abs(kr_open[ts(d, 20)] / cg2000[ts(d, 20)] - 1))
assert max(k0) < 0.01 and max(k20) < 0.01
print(f" 3. Kraken 4h candle opens vs CoinGecko: 00:00 UTC max diff {max(k0)*100:.2f}% (n={len(k0)}),"
      f" 20:00 UTC max diff {max(k20)*100:.2f}% (n={len(k20)})")
# 4. Coinbase hourly spot checks at 20:00 UTC
for r in cb:
    t = int(r["unix_ts"]); o = float(r["open"])
    print(f" 4. Coinbase {r['utc']} open {o:.5f} vs CoinGecko {cg2000[t]:.6f}  ({(o/cg2000[t]-1)*100:+.2f}%)")
    assert abs(o / cg2000[t] - 1) < 0.01
# 5. company's own June 30 valuation price vs the dataset rows either side
print(f" 5. Q2 release ENA closing price for June 30: 0.07204. Dataset row 2026-06-30: {rec['2026-06-30']['E']:.6f};"
      f" dataset row 2026-07-01: {rec['2026-07-01']['E']:.6f}")
print(f"    NAV/share on the dataset's June 30 row: {rec['2026-06-30']['E']*rec['2026-06-30']['H']/rec['2026-06-30']['N']:.4f};"
      f" company figure 9.09; 218.4e6/24,029,375 = {218.4e6/24029375:.4f}")
print(f"    tokens implied by $218.4M at $0.07204: {218.4e6/0.07204/1e6:,.1f}M (dataset uses 3,029.0M)")

# ----------------------------------------------------------------------------- headline tables
print("\nSTART AND END OBSERVATIONS")
for basis in ("dashboard", "close", "utcday"):
    for d in (MONTH_START, MONTH_END):
        o = obs(d, basis)
        print(f" {basis:9s} {d}  USDE {o['P']:6.2f}  ENA {o['E']:.6f}  ENA held {o['H']:,.0f}  Class A {o['N']:,.0f}"
              f"  ENA/share {o['S']:.4f}  NAV/share {o['nav_ps']:.4f}  mNAV {o['M']:.4f}"
              f"  token NAV ${o['nav']/1e6:,.1f}M  mkt cap ${o['cap']/1e6:,.1f}M  gap ${(o['nav']-o['cap'])/1e6:,.1f}M")

print("\nATTRIBUTION")
results = {}
for basis in ("dashboard", "close", "utcday"):
    r = attribute(MONTH_START, MONTH_END, basis, "September, month-end to month-end")
    show(r, orders=(basis != "utcday"))
    results[f"month_{basis}"] = r
for basis in ("dashboard", "close"):
    for a, b, lab in ((MONTH_START, SPLIT, "Leg 1, to the mNAV low at the close"),
                      (SPLIT, MONTH_END, "Leg 2, from that low to month end")):
        r = attribute(a, b, basis, lab)
        show(r)
        results[f"{lab[:5].strip().replace(' ', '').lower()}_{basis}"] = r

# closed-form check of the ENA term (Shapley weights 1/3, 1/6, 1/6, 1/3), on both ENA timestamps
print()
for basis, name in (("close", "at the close"), ("dashboard", "dashboard series")):
    a, b = obs(MONTH_START, basis), obs(MONTH_END, basis)
    weight = a["S"] * a["M"] / 3 + (b["S"] * a["M"] + a["S"] * b["M"]) / 6 + b["S"] * b["M"] / 3
    closed = (b["E"] - a["E"]) * weight
    assert abs(closed - results[f"month_{basis}"]["phi"]["E"]) < 1e-9
    print(f" worked inputs, {name}: E0 {a['E']:.6f}  E1 {b['E']:.6f}  S0 {a['S']:.6f}  S1 {b['S']:.6f}  M0 {a['M']:.6f}  M1 {b['M']:.6f}")
    print(f" closed-form ENA term, {name}: ({b['E']:.6f} - {a['E']:.6f}) x {weight:.4f} = {b['E']-a['E']:.6f} x {weight:.4f} = {closed:.4f}")

# the two legs do not add up to the one-step month split (dollar contributions depend on the path)
print()
for basis, name in (("close", "at the close"), ("dashboard", "dashboard series")):
    l1, l2, mo = results[f"leg1_{basis}"]["phi"], results[f"leg2_{basis}"]["phi"], results[f"month_{basis}"]["phi"]
    print(f" legs summed, {name}: ENA {l1['E']+l2['E']:+.4f}  ENA per share {l1['S']+l2['S']:+.4f}  mNAV {l1['M']+l2['M']:+.4f}"
          f"  (sum {sum(l1.values())+sum(l2.values()):+.4f})  vs one step: ENA {mo['E']:+.4f}  ENA per share {mo['S']:+.4f}  mNAV {mo['M']:+.4f}")

# ----------------------------------------------------------------------------- endpoint sensitivity
print("\nENDPOINT SENSITIVITY (share of the USDE change attributed to each factor)")
grid = []
for basis in ("dashboard", "close"):
    for s0 in ("2026-08-28", "2026-08-31", "2026-09-01"):
        for e0 in ("2026-09-29", "2026-09-30", "2026-10-01"):
            r = attribute(s0, e0, basis, "")
            grid.append(dict(basis=basis, start=s0, end=e0, usde_start=r["a"]["P"], usde_end=r["b"]["P"],
                             usde_change=round(r["dP"], 4), usde_pct=round(r["pctP"] * 100, 2),
                             ena_pct=round(r["pctE"] * 100, 2), mnav_start=round(r["a"]["M"], 4),
                             mnav_end=round(r["b"]["M"], 4), d_ena=round(r["phi"]["E"], 4),
                             d_ena_per_share=round(r["phi"]["S"], 4), d_mnav=round(r["phi"]["M"], 4),
                             share_ena=round(r["share"]["E"] * 100, 1), share_mnav=round(r["share"]["M"] * 100, 1)))
            g = grid[-1]
            print(f" {basis:9s} {s0} -> {e0}: USDE {g['usde_pct']:+7.2f}%  ENA {g['ena_pct']:+7.2f}%  mNAV {g['mnav_start']:.3f}->{g['mnav_end']:.3f}"
                  f"  $ENA {g['d_ena']:+.2f}  $mNAV {g['d_mnav']:+.2f}  ENA {g['share_ena']:5.1f}%  mNAV {g['share_mnav']:5.1f}%")
with open(OUT / "endpoint_sensitivity.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(grid[0].keys())); w.writeheader(); w.writerows(grid)

# ----------------------------------------------------------------------------- daily series (chart data)
print("\nDAILY SERIES, 2026-08-31 to 2026-09-30")
print(" date        USDE    ENA 00:00   ENA 20:00   gap%    NAV/sh rec  NAV/sh close  mNAV rec  mNAV close  Kraken20")
daily = []
for d in [x for x in dates if MONTH_START <= x <= MONTH_END]:
    r_, c_ = obs(d, "dashboard"), obs(d, "close")
    row = dict(date=d, usde_close=r_["P"], class_a_shares=int(r_["N"]), ena_reported=int(r_["H"]),
               ena_per_share=round(r_["S"], 4),
               ena_dashboard_0000utc=r_["E"], ena_close_2000utc=round(c_["E"], 6),
               ena_gap_pct=round((c_["E"] / r_["E"] - 1) * 100, 2),
               nav_per_share_dashboard=round(r_["nav_ps"], 4), nav_per_share_close=round(c_["nav_ps"], 4),
               mnav_dashboard=round(r_["M"], 4), mnav_close=round(c_["M"], 4),
               kraken_2000utc_open=kr_open.get(ts(d, 20)))
    daily.append(row)
    print(f" {d}  {row['usde_close']:6.2f}  {row['ena_dashboard_0000utc']:.6f}   {row['ena_close_2000utc']:.6f}  {row['ena_gap_pct']:+6.2f}"
          f"   {row['nav_per_share_dashboard']:8.4f}    {row['nav_per_share_close']:8.4f}     {row['mnav_dashboard']:.4f}    {row['mnav_close']:.4f}    {row['kraken_2000utc_open']}")
with open(OUT / "daily_mnav_two_timestamps.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(daily[0].keys())); w.writeheader(); w.writerows(daily)

# session-to-session noise in mNAV under each timestamp
def abs_changes(key):
    return [abs(daily[i][key] / daily[i - 1][key] - 1) for i in range(1, len(daily))]
for key in ("mnav_dashboard", "mnav_close"):
    ch = abs_changes(key)
    vals = [x[key] for x in daily]
    lo, hi = min(vals), max(vals)
    print(f" {key}: {len(ch)} session-to-session changes, median abs {st.median(ch)*100:.2f}%, mean {st.mean(ch)*100:.2f}%,"
          f" max {max(ch)*100:.2f}%; range {lo:.4f} ({daily[vals.index(lo)]['date']}) to {hi:.4f} ({daily[vals.index(hi)]['date']})")
gaps = [abs(x["ena_gap_pct"]) for x in daily]
print(f" |ENA 20:00 vs 00:00 UTC| across {len(gaps)} sessions: median {st.median(gaps):.2f}%, max {max(gaps):.2f}%")

# ----------------------------------------------------------------------------- bridge (waterfall) data
bridge = []
for basis, name in (("dashboard", "Dashboard series (ENA at 00:00 UTC of the session date)"), ("close", "At the close (ENA at 20:00 UTC, 4 pm New York)")):
    r = results[f"month_{basis}"]
    bridge += [dict(basis=name, step="Aug 31 close", kind="total", value=r["a"]["P"]),
               dict(basis=name, step="ENA price", kind="step", value=round(r["phi"]["E"], 4)),
               dict(basis=name, step="ENA per share", kind="step", value=round(r["phi"]["S"], 4)),
               dict(basis=name, step="mNAV", kind="step", value=round(r["phi"]["M"], 4)),
               dict(basis=name, step="Sep 30 close", kind="total", value=r["b"]["P"])]
with open(OUT / "attribution_bridge.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(bridge[0].keys())); w.writeheader(); w.writerows(bridge)

# ----------------------------------------------------------------------------- other facts quoted in the draft
sept = [d for d in dates if d.startswith("2026-09")]
print("\nOTHER FACTS")
print(" September sessions:", len(sept), "| observations Aug 31..Sep 30:", len(daily))
closes = [rec[d]["P"] for d in sept]
print(f" September closes: low {min(closes)} on {sept[closes.index(min(closes))]}, high {max(closes)} on {sept[closes.index(max(closes))]}")
print(" first close above $11.50:", next(d for d in dates if rec[d]["P"] > 11.5))
ge10 = [d for d in dates if rec[d]["P"] >= 10.0]
print(f" closes at or above $10.00: {len([d for d in ge10 if d <= MONTH_END])} through Sep 30 (first {ge10[0]}),"
      f" {len([d for d in ge10 if d <= '2026-10-02'])} through Oct 2")
print(" closes at or above $18.00 through Oct 2:", len([d for d in dates if d <= "2026-10-02" and rec[d]["P"] >= 18.0]),
      "| highest intraday high in September (S&P Global):", max((spg[d]["high"], d) for d in sept))
print(f" USDEW close: {rec[MONTH_START]['W']:.2f} -> {rec[MONTH_END]['W']:.2f} ({(rec[MONTH_END]['W']/rec[MONTH_START]['W']-1)*100:+.1f}%)")
vol = sum(spg[d]["volume"] for d in sept)
print(f" September share volume (S&P Global): {vol:,} = {vol/24029375:.2f}x the 24,029,375 Class A shares")
print(f" ENA per share: {3029000000/24029375:.4f} -> {3029000000/24139375:.4f} ({(24029375/24139375-1)*100:+.3f}%)")
print(f" Sep 30 mNAV if the 110,000 director shares are left out: {16.08/(rec[MONTH_END]['E']*3029000000/24029375):.4f} (dashboard series),"
      f" {16.08/(cg2000[ts(MONTH_END,20)]*3029000000/24029375):.4f} (close)")
print(f" 5 x 22,000 = {5*22000:,}; 24,029,375 + 110,000 = {24029375+110000:,}")
print(f" 7.5% x 24,029,375 = {0.075*24029375:,.3f} (S-8 registers 1,802,203)")
print(f" warrant cash if all exercised: 11,500,000 x 11.50 + 3,267,679 x 11.50 + 4,356,907 x 15.00 = ${(11500000*11.5+3267679*11.5+4356907*15)/1e6:,.2f}M")
print(f" public warrants x $0.41 (Jun 30 close): 11,500,000 -> ${11500000*0.41:,.2f}; 11,499,988 -> ${11499988*0.41:,.2f}; 10-Q warrant liability $4,715,000")
print(f" public warrants x $5.17 (Sep 30 close): 11,500,000 -> ${11500000*rec[MONTH_END]['W']/1e6:,.3f}M; 11,499,988 -> ${11499988*rec[MONTH_END]['W']/1e6:,.3f}M")
print(f" each 1,000,000 new Class A shares lowers ENA per share by {(1-24139375/25139375)*100:.2f}%")
for d in ("2026-09-25", "2026-09-30"):
    r_, c_ = obs(d, "dashboard"), obs(d, "close")
    print(f" {d}: ENA 00:00 {r_['E']:.6f}, 20:00 {c_['E']:.6f} ({(c_['E']/r_['E']-1)*100:+.2f}%); mNAV {r_['M']:.4f} on the dashboard series, {c_['M']:.4f} at the close")
print(f" Sep 25 first print in the repo (commit 0efe051, ENA 0.260069) on 24,029,375 shares: mNAV {17.25/(0.260069*3029000000/24029375):.4f}")
print(f" Sep 25 second print that evening (commit 04cf641, ENA 0.268311) on 24,029,375 shares: mNAV {17.25/(0.268311*3029000000/24029375):.4f}")
print(f" the same two prints on the 24,110,000 share seed the repo used until Oct 3: mNAV {17.25/(0.260069*3029000000/24110000):.4f} and {17.25/(0.268311*3029000000/24110000):.4f}")
print(f" Sep 30 first print in the repo (commit 8df558b, ENA 0.263804) on 24,139,375 shares: mNAV {16.08/(0.263804*3029000000/24139375):.4f}")
print(f" Sep 25 session: USDE {rec['2026-09-24']['P']} -> {rec['2026-09-25']['P']} ({(rec['2026-09-25']['P']/rec['2026-09-24']['P']-1)*100:+.2f}%)")
listing = [d for d in dates if d <= MONTH_END and rec[d]['P'] is not None and rec[d]['E'] is not None]
mmax = max(listing, key=lambda d: obs(d, 'dashboard')['M'])
print(f" highest dashboard-series mNAV from {listing[0]} to {MONTH_END}: {obs(mmax, 'dashboard')['M']:.4f} on {mmax}")

# ----------------------------------------------------------------------------- further figures quoted in the article
print("\nWINDOW TABLE (all end at the Sep 30 close, ENA priced at the stock close)")
win = []
for s0 in ("2026-08-28", "2026-08-31", "2026-09-01"):
    r = attribute(s0, MONTH_END, "close", "")
    win.append(dict(start=s0, usde_start=r["a"]["P"], mnav_start=round(r["a"]["M"], 4),
                    share_ena=round(r["share"]["E"] * 100, 1), share_count=round(r["share"]["S"] * 100, 1),
                    share_mnav=round(r["share"]["M"] * 100, 1)))
    print(f" opens {s0} at {r['a']['P']:.2f}, mNAV {r['a']['M']:.4f}: ENA {r['share']['E']*100:.1f}%  share count {r['share']['S']*100:.1f}%  mNAV {r['share']['M']*100:.1f}%")
with open(OUT / "window_table.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(win[0].keys())); w.writeheader(); w.writerows(win)
a28, a31 = obs("2026-08-28", "close"), obs("2026-08-31", "close")
print(f" Aug 31 session: USDE {a28['P']} -> {a31['P']} ({(a31['P']/a28['P']-1)*100:+.2f}%), ENA at close {a28['E']:.6f} -> {a31['E']:.6f} ({(a31['E']/a28['E']-1)*100:+.2f}%), mNAV {a28['M']:.4f} -> {a31['M']:.4f}")

print("\nPATH OF mNAV AT THE CLOSE")
c16, c17, c18, c30 = (obs(d, "close") for d in ("2026-09-16", "2026-09-17", "2026-09-18", "2026-09-30"))
print(f" Sep 16 {c16['M']:.4f} -> Sep 17 {c17['M']:.4f} -> Sep 18 {c18['M']:.4f} -> Sep 30 {c30['M']:.4f}")
print(f" Sep 18 -> Sep 30: USDE {(c30['P']/c18['P']-1)*100:+.1f}%, ENA {(c30['E']/c18['E']-1)*100:+.1f}%, mNAV {(c30['M']/c18['M']-1)*100:+.1f}%")
m0 = obs(MONTH_START, "close")
print(f" chained: mNAV {(c16['M']/m0['M']-1)*100:+.2f}% then {(c30['M']/c16['M']-1)*100:+.2f}% = net {(c30['M']/m0['M']-1)*100:+.2f}%")
print(f" Sep 16 ENA at the close: {c16['E']:.5f}")
mins = min(daily, key=lambda x: x["mnav_close"]); print(f" lowest mNAV at the close in the window: {mins['mnav_close']} on {mins['date']}")
assert mins["date"] == SPLIT, "the split date must be the session with the lowest mNAV at the close"
means = {k: st.mean(abs_changes(k)) * 100 for k in ("mnav_dashboard", "mnav_close")}
print(f" mean abs session-to-session change: dashboard series {means['mnav_dashboard']:.1f}%, at the close {means['mnav_close']:.1f}%")

print("\nTOKEN COUNT AND LOCK-UP SCHEDULE")
tok10q = 284954407.29 + 1405754435.84 + 1340695577.81
print(f" 10-Q Note 3 tokens: {tok10q:,.2f}; dataset 3,029,000,000 is {(3029000000/tok10q-1)*100:+.4f}%")
print(f" 10-Q Note 3 values: {23417531.14+115524790.73+110178258.81:,.2f}")
print(f" June 30 NAV/share at $0.07204: dataset tokens {0.07204*3029000000/24029375:.4f}; 10-Q tokens {0.07204*tok10q/24029375:.4f}; company 9.09")
unl = dict(zip(S["date"], S["ena_unlocked"]))
CONTRIB = 284954407.29   # tokens contributed by Ethena, which 10-Q Note 3 describes as locked at June 30, 2026
for d in ("2026-08-31", "2026-09-29", "2026-09-30"):
    print(f" tracker schedule, unlocked ENA on {d}: {unl[d]:,.0f} = {unl[d]/3029000000*100:.1f}% of 3.029B"
          f" | with the contributed tokens counted as locked: {(unl[d]-CONTRIB)/3029000000*100:.1f}%")

print("\nWARRANTS")
w1150, w1500 = 11500000 + 3267679, 4356907
print(f" warrants at $11.50: {w1150:,}; at $15.00: {w1500:,}; total {w1150+w1500:,} = {(w1150+w1500)/24139375*100:.1f}% of 24,139,375")
print(" first close above $15.00:", next(d for d in dates if rec[d]["P"] > 15.0))
sp = 3267679 + 4356907
sp_cash = 3267679 * 11.5 + 4356907 * 15.0
print(f" sponsor warrants: {sp:,} = {sp/(w1150+w1500)*100:.1f}% of the warrant shares; cash if exercised for cash ${sp_cash/1e6:.1f}M"
      f" of ${(w1150*11.5+w1500*15.0)/1e6:.2f}M")
print(f" highest close Aug 31..Sep 30: {max(rec[d]['P'] for d in dates if MONTH_START <= d <= MONTH_END)} (no close at or above $18.00)")
ge10 = [d for d in dates if rec[d]["P"] is not None and rec[d]["P"] >= 10.0]
print(f" tenth close at or above $10.00: {ge10[9]} at {rec[ge10[9]]['P']}; eleventh: {ge10[10]} at {rec[ge10[10]]['P']}")
print(f" resale shares: 4,965,722 + 78,635 + 7,624,586 = {4965722+78635+7624586:,}; sponsor warrant shares {3267679+4356907:,}")
print(f" public warrants x USDEW close: Jun 30 {rec['2026-06-30']['W']:.2f} -> ${11500000*rec['2026-06-30']['W']/1e6:.2f}M; Sep 30 {rec[MONTH_END]['W']:.2f} -> ${11500000*rec[MONTH_END]['W']/1e6:.2f}M")

json.dump({k: {kk: vv for kk, vv in v.items() if kk != "orders"} for k, v in results.items()},
          open(OUT / "results.json", "w"), indent=1)
print("\nwrote attribution_bridge.csv, daily_mnav_two_timestamps.csv, endpoint_sensitivity.csv, window_table.csv, results.json")
