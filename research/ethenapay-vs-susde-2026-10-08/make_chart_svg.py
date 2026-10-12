#!/usr/bin/env python3
"""
Draws out/chart_susde_vs_ethenapay.svg in the site's dark style. One point per UTC day from September 1 to October 8,
2026, sUSDe's rate a year after compounding, from the change in its share price over the day. Three step lines show
the rates EthenaPay's payments were set at that day, after compounding, the Pro and VIP rate within their caps, the
rate on the first $5,000 of a Standard balance, and the base rate that balance above a cap earned.

Every point, label, the title and the description come from out/chart_points.csv and out/results.json, which
susde_vs_ethenapay_review.py writes. Run after the main script, as python3 make_chart_svg.py
"""
import csv
import json
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE / "out" / "chart_points.csv")))
res = json.loads((HERE / "out" / "results.json").read_text())
dc = res["days_compared"]
assert len(rows) == dc["days"] == 38 and dc["susde_above_base"] == dc["susde_below_six"] == 38

BG, RULE, TEXT, MUTED = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)", "var(--sx-muted, #99a3b0)")
C_SUSDE, C_STD, C_SIX = "#3987e5", "#d95926", "#199e70"   # first three categorical slots, dark steps, validated on #0d1116
C_BASE = "#99a3b0"
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
HALO = f'style="paint-order:stroke;stroke:{BG};stroke-width:4px;stroke-linejoin:round"'
W, H = 800, 466
X0, X1, Y0, Y1 = 64, 640, 108, 392
YMIN, YMAX = 3.75, 6.25
d0 = date.fromisoformat(rows[0]["day"])
n = len(rows)


def sx(i):
    return X0 + (X1 - X0) * (i + 0.5) / n


def sy(v):
    return Y1 - (Y1 - Y0) * (float(v) - YMIN) / (YMAX - YMIN)


def label_day(s):
    d = date.fromisoformat(s)
    return d.strftime("%b ") + str(d.day)


def full_day(s):
    d = date.fromisoformat(s)
    return d.strftime("%B ") + str(d.day)


vals = [float(r["susde_after_compounding_pct"]) for r in rows]
assert all(YMIN < v < YMAX for v in vals) and all(YMIN < float(r[k]) < YMAX for r in rows for k in ("ethenapay_base_pct", "ethenapay_standard_pct", "ethenapay_six_pct"))
lo = min(range(n), key=lambda i: vals[i])
hi = max(range(n), key=lambda i: vals[i])
title = "sUSDe paid more than EthenaPay's base rate and less than its Pro and VIP rate every day"
subtitle = "Rate a year after compounding, each UTC day from September 1 to October 8, 2026"
last = rows[-1]
desc = (f"Line chart of {n} days. sUSDe's rate a year after compounding, from the change in its share price over each UTC day, ranged between "
        f"{vals[lo]:.2f}% on {full_day(rows[lo]['day'])} and {vals[hi]:.2f}% on {full_day(rows[hi]['day'])}. Three step lines show the rates "
        f"EthenaPay's payments were set at. Within their caps the Pro and VIP rate was {float(rows[0]['ethenapay_six_pct']):.2f}% until September 15 and "
        f"{float(last['ethenapay_six_pct']):.2f}% from September 17, and the rate on the first $5,000 of a Standard balance was {float(rows[0]['ethenapay_standard_pct']):.2f}% "
        f"and then {float(last['ethenapay_standard_pct']):.2f}%. Balance above a cap earned the base rate, {float(rows[0]['ethenapay_base_pct']):.1f}% until "
        f"September 16 and {float(last['ethenapay_base_pct']):.1f}% from September 17. On September 16 the Boost had already fallen and the base not yet "
        f"risen, so both tier lines dip. sUSDe stayed above the base rate and below the Pro and VIP rate on every day, and paid more than the Standard rate "
        f"on {dc['susde_above_standard']} days.")

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="sv-t sv-d" font-family="{FONT}">')
a('<title id="sv-t">sUSDe\'s daily rate against EthenaPay\'s rates, September 1 to October 8, 2026</title>')
a(f'<desc id="sv-d">{desc}</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
a(f'<text x="20" y="30" fill="{TEXT}" font-size="16" font-weight="600">{title}</text>')
a(f'<text x="20" y="52" fill="{MUTED}" font-size="12">{subtitle}</text>')
LY = 78
a(f'<line x1="20" x2="42" y1="{LY - 4}" y2="{LY - 4}" stroke="{C_SUSDE}" stroke-width="2"/><circle cx="31" cy="{LY - 4}" r="3" fill="{C_SUSDE}"/>')
a(f'<text x="48" y="{LY}" fill="{MUTED}" font-size="11">sUSDe</text>')
for x, label, color, dash in ((110, "EthenaPay Pro and VIP, within cap", C_SIX, ""), (330, "EthenaPay Standard, first $5,000", C_STD, ""),
                              (546, "EthenaPay base rate", C_BASE, ' stroke-dasharray="5 3"')):
    a(f'<line x1="{x}" x2="{x + 22}" y1="{LY - 4}" y2="{LY - 4}" stroke="{color}" stroke-width="2"{dash}/>')
    a(f'<text x="{x + 28}" y="{LY}" fill="{MUTED}" font-size="11">{label}</text>')
for v in (4.0, 4.5, 5.0, 5.5, 6.0):
    a(f'<line x1="{X0}" x2="{X1}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{X0 - 8}" y="{sy(v) + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">{v:.1f}%</text>')
for i, r in enumerate(rows):
    if (date.fromisoformat(r["day"]) - d0).days % 7 == 0:
        a(f'<line x1="{sx(i):.1f}" x2="{sx(i):.1f}" y1="{Y1}" y2="{Y1 + 5}" stroke="{RULE}" stroke-width="1"/>')
        a(f'<text x="{sx(i):.1f}" y="{Y1 + 19}" fill="{MUTED}" font-size="11" text-anchor="middle">{label_day(r["day"])}</text>')
a(f'<text x="{X0 - 50}" y="{Y0 - 12}" fill="{MUTED}" font-size="11">Rate a year after compounding</text>')
a(f'<text x="20" y="{H - 10}" fill="{MUTED}" font-size="10">sUSDe, Deposit and Withdraw records of its staking contract on Ethereum. EthenaPay, the rates its '
  'payments were set at, from the Daily Boost review.</text>')


def steps(key):
    pts = []
    for i, r in enumerate(rows):
        x_l, x_r = X0 + (X1 - X0) * i / n, X0 + (X1 - X0) * (i + 1) / n
        pts += [(x_l, sy(r[key])), (x_r, sy(r[key]))]
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


a(f'<polyline points="{steps("ethenapay_six_pct")}" fill="none" stroke="{C_SIX}" stroke-width="2" stroke-linejoin="round"/>')
a(f'<polyline points="{steps("ethenapay_standard_pct")}" fill="none" stroke="{C_STD}" stroke-width="2" stroke-linejoin="round"/>')
a(f'<polyline points="{steps("ethenapay_base_pct")}" fill="none" stroke="{C_BASE}" stroke-width="2" stroke-dasharray="5 3" stroke-linejoin="round"/>')
a('<polyline points="' + " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(vals)) + f'" fill="none" stroke="{C_SUSDE}" stroke-width="2" stroke-linejoin="round"/>')
for i, (r, v) in enumerate(zip(rows, vals)):
    a(f'<g><title>{label_day(r["day"])}, sUSDe {v:.2f}%, EthenaPay Pro and VIP {float(r["ethenapay_six_pct"]):.2f}%, Standard '
      f'{float(r["ethenapay_standard_pct"]):.2f}%, base {float(r["ethenapay_base_pct"]):.1f}%</title>'
      f'<circle cx="{sx(i):.1f}" cy="{sy(v):.1f}" r="8" fill="transparent"/>'
      f'<circle cx="{sx(i):.1f}" cy="{sy(v):.1f}" r="3" fill="{C_SUSDE}" stroke="{BG}" stroke-width="1"/></g>')
# end labels to the right of the plot
lx = X1 + 10
a(f'<text x="{lx}" y="{sy(last["ethenapay_six_pct"]) + 4:.1f}" fill="{C_SIX}" font-size="11">Pro and VIP {float(last["ethenapay_six_pct"]):.2f}%</text>')
a(f'<text x="{lx}" y="{sy(last["ethenapay_standard_pct"]) - 6:.1f}" fill="{C_STD}" font-size="11">Standard {float(last["ethenapay_standard_pct"]):.2f}%</text>')
a(f'<text x="{lx}" y="{sy(vals[-1]) + 14:.1f}" fill="{C_SUSDE}" font-size="11">sUSDe {vals[-1]:.2f}%</text>')
a(f'<text x="{lx}" y="{sy(last["ethenapay_base_pct"]) + 4:.1f}" fill="{C_BASE}" font-size="11">Base {float(last["ethenapay_base_pct"]):.1f}%</text>')
# the two extremes of sUSDe
a(f'<text x="{sx(lo):.1f}" y="{sy(vals[lo]) + 18:.1f}" fill="{TEXT}" font-size="11" text-anchor="middle" {HALO}>{vals[lo]:.2f}%</text>')
a(f'<text x="{sx(hi):.1f}" y="{sy(vals[hi]) - 10:.1f}" fill="{TEXT}" font-size="11" text-anchor="middle" {HALO}>{vals[hi]:.2f}%</text>')
a('</svg>')
(HERE / "out" / "chart_susde_vs_ethenapay.svg").write_text("\n".join(o) + "\n")
print(f"wrote out/chart_susde_vs_ethenapay.svg, {n} days")
