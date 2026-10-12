#!/usr/bin/env python3
"""
Draws out/chart_boost_rates.svg in the site's dark style. One dot per EthenaPay wallet that held 100 USDe or more
on average on October 8, 2026 and received a Boost payment for that day. The dot sits at the wallet's time-weighted
balance, on a log scale, and the Boost it received as a yearly rate before compounding. Wallets that never sent USDe
to a settlement address through October 9 are drawn in a second color. Three lines show the tiers in Ethena Pay's
terms: 0.5% a year on the first $5,000, 1.5% on the whole balance, and 1.5% on the first $100,000.

Every point, label, the title and the description come from out/chart_points.csv, out/chart_lines.csv and
out/results.json, which ethenapay_boost_review.py writes. Run after the main script: python3 make_chart_svg.py
"""
import csv
import json
import math
from pathlib import Path

HERE = Path(__file__).parent
pts = [(float(r["twa_usde"]), float(r["topup_rate_simple_pct"]), r["series"]) for r in csv.DictReader(open(HERE / "out" / "chart_points.csv"))]
lines = list(csv.DictReader(open(HERE / "out" / "chart_lines.csv")))
res = json.loads((HERE / "out" / "results.json").read_text())
day = res["day_detail"]["2026-10-08"]
never = res["never_through_oct9_on_oct8"]

used = [p for p in pts if p[2] == "used the card"]
nev = [p for p in pts if p[2] == "never used the card"]
assert len(pts) == day["tested"] - 1 == 584, "one tested wallet was unpaid on October 8"
assert len(nev) == never["paid"] == 59 and len(used) == 525

BG, RULE, TEXT, MUTED = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)",
                         "var(--sx-muted, #99a3b0)")
C_USED = "#3987e5"
C_NEVER = "#d95926"
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
HALO = f'style="paint-order:stroke;stroke:{BG};stroke-width:4px;stroke-linejoin:round"'
W, H = 800, 466
X0, X1, Y0, Y1 = 64, 760, 108, 390
LMIN, LMAX = 2.0, 6.0          # $100 to $1,000,000
YMAX = 2.0


def sx(v):
    return X0 + (X1 - X0) * (math.log10(v) - LMIN) / (LMAX - LMIN)


def sy(v):
    return Y1 - (Y1 - Y0) * min(v, YMAX) / YMAX


def money(v):
    return f"${v:,.0f}"


assert all(100 <= x <= 10 ** LMAX for x, _, _ in pts), "a balance falls outside the axis"
over = sorted((p for p in pts if p[1] > YMAX), key=lambda p: p[0])
std = float(res["models_simple_pct"]["standard_0_5"])
six = float(res["models_simple_pct"]["six_1_5"])
title = "On October 8 the Boost followed the tier caps, with or without card use"
whole = day["groups"]["six_1_5"]["wallets"] + day["groups"]["six_1_5_within_5pct"]["wallets"]
capped = float(day["groups"]["six_1_5_cap_100k"]["twa"])
subtitle = "Each dot is a wallet with 100 USDe or more. Boost for October 8 as a yearly rate before compounding, so 1.5% shows as 1.49%"
desc = (f"{len(pts)} dots, one per wallet that held 100 USDe or more on average on October 8, 2026 and received a Boost payment for that day, "
        f"placed by its time-weighted balance on a log scale from $100 to $1,000,000 and the Boost as a yearly rate before compounding. "
        f"{len(used)} wallets had used the card at some time and {len(nev)} had never sent USDe to a settlement address through October 9. "
        f"Most dots sit on one of three lines from Ethena Pay's terms. {std:.2f}% a year on balances up to $5,000, and above that {std:.2f}% times "
        f"5,000 divided by the balance. {six:.2f}% a year on the whole balance, the line of {whole} wallets, {day['six_over_100k_uncapped']} of them above "
        f"$100,000. {six:.2f}% a year on the first $100,000, one wallet at {money(capped)}. Wallets that never used the card sit on the same "
        f"lines, the largest at {money(float(never['largest_twa_usde']))} on the 1.5% line. {len(over)} wallets above 2% are drawn at the top "
        f"edge, at {over[0][1]:.2f}% and {over[1][1]:.2f}%.")

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="bo-t bo-d" font-family="{FONT}">')
a('<title id="bo-t">EthenaPay Daily Boost paid for October 8, 2026 against each wallet\'s balance, with the tier lines from Ethena Pay\'s terms</title>')
a(f'<desc id="bo-d">{desc}</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
a(f'<text x="20" y="30" fill="{TEXT}" font-size="16" font-weight="600">{title}</text>')
a(f'<text x="20" y="52" fill="{MUTED}" font-size="12">{subtitle}</text>')
# legend row
LY = 78
a(f'<circle cx="26" cy="{LY - 4}" r="4" fill="{C_USED}"/>')
a(f'<text x="36" y="{LY}" fill="{MUTED}" font-size="11">Used the card at some time ({len(used)})</text>')
a(f'<circle cx="236" cy="{LY - 4}" r="4" fill="{C_NEVER}"/>')
a(f'<text x="246" y="{LY}" fill="{MUTED}" font-size="11">Never used the card, through October 9 ({len(nev)})</text>')
a(f'<line x1="514" x2="536" y1="{LY - 4}" y2="{LY - 4}" stroke="{TEXT}" stroke-width="1.5" stroke-dasharray="5 4"/>')
a(f'<text x="542" y="{LY}" fill="{MUTED}" font-size="11">Tier rates and caps in the terms</text>')
# grid and axes
for v in (0, 0.5, 1.0, 1.5, 2.0):
    a(f'<line x1="{X0}" x2="{X1}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{X0 - 8}" y="{sy(v) + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">{v:g}%</text>')
for e in range(2, 7):
    v = 10 ** e
    a(f'<line x1="{sx(v):.1f}" x2="{sx(v):.1f}" y1="{Y0}" y2="{Y1}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{sx(v):.1f}" y="{Y1 + 19}" fill="{MUTED}" font-size="11" text-anchor="middle">{money(v)}</text>')
a(f'<text x="{X1}" y="{Y1 + 38}" fill="{MUTED}" font-size="11" text-anchor="end">Time-weighted balance on October 8, USDe, log scale</text>')
a(f'<text x="{X0 - 44}" y="{Y0 - 12}" fill="{MUTED}" font-size="11">Boost, % a year</text>')
a(f'<text x="20" y="{H - 10}" fill="{MUTED}" font-size="10">Payments on Avalanche C-Chain, read to the end of October 9 UTC. '
  'Rates and caps, Ethena Pay FAQ, terms and pricing page.</text>')
# tier lines
for col in ("standard_0_5_cap_5k_pct", "six_1_5_cap_100k_pct", "six_1_5_pct"):
    seg = [(float(r["twa_usde"]), float(r[col])) for r in lines]
    if col == "six_1_5_cap_100k_pct":
        seg = [p for p in seg if p[0] >= 100000]
    a('<polyline points="' + " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in seg)
      + f'" fill="none" stroke="{TEXT}" stroke-width="1.5" stroke-dasharray="5 4" stroke-linejoin="round"/>')
# dots, wallets that used the card first, each with its own hover title
for group, color in ((used, C_USED), (nev, C_NEVER)):
    for x, y, s in group:
        if y > YMAX:
            continue
        a(f'<g><title>Balance {money(x)}, Boost {y:.3f}% a year, {s}</title>'
          f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="8" fill="transparent"/>'
          f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="3.5" fill="{color}" stroke="{BG}" stroke-width="1"/></g>')
# the wallets above 2%, drawn as triangles on the top edge
for x, y, s in over:
    cx, cy = sx(x), Y0
    color = C_NEVER if s == "never used the card" else C_USED
    a(f'<g><title>Balance {money(x)}, Boost {y:.2f}% a year, {s}, above the chart</title>'
      f'<polygon points="{cx - 5:.1f},{cy + 6:.1f} {cx + 5:.1f},{cy + 6:.1f} {cx:.1f},{cy - 3:.1f}" fill="{color}"/></g>')
a(f'<text x="{sx(over[-1][0]) + 10:.1f}" y="{Y0 + 6:.1f}" fill="{MUTED}" font-size="11" {HALO}>'
  f'{len(over)} wallets at {over[0][1]:.2f}% and {over[1][1]:.2f}%, above the chart</text>')
# line labels
a(f'<text x="{sx(130):.1f}" y="{sy(six) + 22:.1f}" fill="{TEXT}" font-size="11" {HALO}>1.5% a year on the whole balance, the 6% group</text>')
a(f'<text x="{sx(130):.1f}" y="{sy(std) + 22:.1f}" fill="{TEXT}" font-size="11" {HALO}>0.5% a year on the first $5,000, Standard</text>')
a(f'<text x="{sx(11000):.1f}" y="{sy(0.36):.1f}" fill="{MUTED}" font-size="11" {HALO}>Above $5,000, a fixed 0.068 USDe a day</text>')
a(f'<text x="{sx(160000):.1f}" y="{sy(1.18):.1f}" fill="{MUTED}" font-size="11" {HALO}>1.5% on the first $100,000</text>')
a('</svg>')
(HERE / "out" / "chart_boost_rates.svg").write_text("\n".join(o) + "\n")
print(f"wrote out/chart_boost_rates.svg, {len(pts)} dots")
