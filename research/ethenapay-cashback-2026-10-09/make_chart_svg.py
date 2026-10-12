#!/usr/bin/env python3
"""
Draws out/chart_cashback_schedules.svg in the site's dark style. One dot per EthenaPay wallet with $10 or more of card
payments from September 1 to 28, 2026 and some cashback paid in the batches from September 3 to October 1. The dot sits
at the wallet's card payments and its cashback in dollars at the Chainlink AVAX / USD price in force at each transfer,
both on log scales. Three lines show what the Standard, Pro and VIP schedules on the Ethena Pay Pricing page pay for
a month's spend.

Every point, label, the title and the description come from out/chart_points.csv, out/chart_lines.csv and
out/results.json, which ethenapay_cashback_review.py writes. Run after the main script: python3 make_chart_svg.py
"""
import csv
import json
import math
from pathlib import Path

HERE = Path(__file__).parent
pts = [(float(r["card_spend_september_1_to_28"]), float(r["cashback_usd_paid_september_3_to_october_1"]), r["within_5pct_of"], r["wallet"])
       for r in csv.DictReader(open(HERE / "out" / "chart_points.csv"))]
lines = [(float(r["card_spend"]), float(r["standard_usd"]), float(r["pro_usd"]), float(r["vip_usd"]))
         for r in csv.DictReader(open(HERE / "out" / "chart_lines.csv"))]
res = json.loads((HERE / "out" / "results.json").read_text())
hv = res["heavy"]
capped = [p for p in pts if p[2] == "standard ceiling"]
assert len(capped) == hv["standard_ceiling_within_5pct"] == 28
assert sum(1 for p in pts if p[2] == "vip") == hv["vip_within_5pct"] and sum(1 for p in pts if p[2] == "pro") == hv["pro_within_5pct"]

BG, RULE, TEXT, MUTED = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)", "var(--sx-muted, #99a3b0)")
C_STD, C_PRO, C_VIP = "#3987e5", "#d95926", "#199e70"   # first three categorical slots, dark steps, validated on #0d1116
C_DOT = "#99a3b0"
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
HALO = f'style="paint-order:stroke;stroke:{BG};stroke-width:4px;stroke-linejoin:round"'
W, H = 800, 466
X0, X1, Y0, Y1 = 70, 760, 108, 388
XMIN, XMAX = 1.0, math.log10(200000)     # $10 to $200,000
YMIN, YMAX = -1.0, math.log10(3000)      # $0.10 to $3,000


def sx(v):
    return X0 + (X1 - X0) * (math.log10(v) - XMIN) / (XMAX - XMIN)


def sy(v):
    return Y1 - (Y1 - Y0) * (math.log10(v) - YMIN) / (YMAX - YMIN)


def money(v, places=0):
    return f"${v:,.{places}f}"


assert all(10 <= x <= 200000 and 0.1 <= y <= 3000 for x, y, _, _ in pts), "a dot falls outside the axes"
big = res["heavy"]["largest_spending_wallet"]
title = "Twenty-eight heavy-spending wallets were paid about $115, the Standard tier's ceiling"
subtitle = "Each dot is a wallet, its card payments September 1 to 28 against its cashback paid September 3 to October 1"
desc = (f"The chart has {len(pts)} dots, one per EthenaPay wallet with $10 or more of card payments from September 1 to 28, 2026 and cashback paid in the "
        f"batches from September 3 to October 1, placed by its card payments on a log scale from $10 to $200,000 and its cashback in dollars, "
        f"at the Chainlink AVAX / USD price in force at each transfer, on a log scale from $0.10 to $3,000. Three lines show what each tier's "
        f"schedule pays for a month's spend. Standard pays 4% to $2,500 and 1% to $4,000, then nothing, so it stops at $115. Pro pays 4.5% to "
        f"$8,000 and VIP 5% to $20,000, with lower rates above. Light-spending wallets sit close to the Standard line. Twenty-eight wallets with "
        f"{money(min(p[0] for p in capped), 2)} to {money(max(p[0] for p in capped), 2)} of card payments from September 1 to 28 "
        f"sit on the flat Standard line, paid {money(float(hv['standard_ceiling_min_paid']), 2)} to {money(float(hv['standard_ceiling_max_paid']), 2)}. "
        f"Of the other wallets with $4,000 or more, {hv['vip_within_5pct']} sit within 5% of the VIP line, among them the largest-spending wallet, "
        f"{money(float(big['month_spend']), 2)} in September and {money(float(big['paid']), 2)} of cashback, and {hv['pro_within_5pct']} within 5% of the Pro line.")

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="cb-t cb-d" font-family="{FONT}">')
a('<title id="cb-t">EthenaPay cashback paid for September 2026 against each wallet\'s card payments, with the three tier schedules</title>')
a(f'<desc id="cb-d">{desc}</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
a(f'<text x="20" y="30" fill="{TEXT}" font-size="16" font-weight="600">{title}</text>')
a(f'<text x="20" y="52" fill="{MUTED}" font-size="12">{subtitle}</text>')
# legend row
LY = 78
a(f'<circle cx="26" cy="{LY - 4}" r="3.5" fill="{C_DOT}"/>')
a(f'<text x="36" y="{LY}" fill="{MUTED}" font-size="11">Wallet ({len(pts)})</text>')
for x, label, color in ((120, "Standard schedule", C_STD), (262, "Pro schedule", C_PRO), (378, "VIP schedule", C_VIP)):
    a(f'<line x1="{x}" x2="{x + 22}" y1="{LY - 4}" y2="{LY - 4}" stroke="{color}" stroke-width="2"/>')
    a(f'<text x="{x + 28}" y="{LY}" fill="{MUTED}" font-size="11">{label}</text>')
# grid and axes
for v, lab in ((0.1, "$0.10"), (1, "$1"), (10, "$10"), (100, "$100"), (1000, "$1,000")):
    a(f'<line x1="{X0}" x2="{X1}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{X0 - 8}" y="{sy(v) + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">{lab}</text>')
for v in (10, 100, 1000, 10000, 100000):
    a(f'<line x1="{sx(v):.1f}" x2="{sx(v):.1f}" y1="{Y0}" y2="{Y1}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{sx(v):.1f}" y="{Y1 + 19}" fill="{MUTED}" font-size="11" text-anchor="middle">{money(v)}</text>')
a(f'<text x="{X1}" y="{Y1 + 38}" fill="{MUTED}" font-size="11" text-anchor="end">Card payments, September 1 to 28, USDe, log scale</text>')
a(f'<text x="{X0 - 50}" y="{Y0 - 12}" fill="{MUTED}" font-size="11">Cashback paid, $ at Chainlink\'s AVAX price, log scale</text>')
a(f'<text x="20" y="{H - 10}" fill="{MUTED}" font-size="10">Transfers on Avalanche C-Chain, read to the end of October 9 UTC. '
  'Schedules, Ethena Pay Pricing page, Section 3.1.</text>')
# dots first, so the schedule lines stay on top, each with its own hover title
for xv, yv, fit, w in sorted(pts, key=lambda p: p[0]):
    note = {"standard ceiling": ", within 5% of $115", "pro": ", within 5% of the Pro schedule", "vip": ", within 5% of the VIP schedule"}.get(fit, "")
    a(f'<g><title>Wallet {w}, card payments {money(xv, 2)}, cashback {money(yv, 2)}{note}</title>'
      f'<circle cx="{sx(xv):.1f}" cy="{sy(yv):.1f}" r="8" fill="transparent"/>'
      f'<circle cx="{sx(xv):.1f}" cy="{sy(yv):.1f}" r="3.5" fill="{C_DOT}" fill-opacity="0.75" stroke="{BG}" stroke-width="1"/></g>')
# schedule lines, from the first point where they reach $0.10
for idx, color in ((3, C_VIP), (2, C_PRO), (1, C_STD)):
    seg = [(p[0], p[idx]) for p in lines if 0.1 <= p[idx] and p[0] <= 200000]
    a('<polyline points="' + " ".join(f"{sx(xv):.1f},{sy(yv):.1f}" for xv, yv in seg)
      + f'" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>')
# line labels
a(f'<text x="{X1 - 4}" y="{sy(115) - 10:.1f}" fill="{C_STD}" font-size="11" text-anchor="end" {HALO}>Standard stops at $115 a month</text>')
a(f'<text x="{sx(30000):.1f}" y="{sy(1450) - 10:.1f}" fill="{C_VIP}" font-size="11" text-anchor="end" {HALO}>VIP, 5% to $20,000</text>')
a(f'<text x="{X1 - 4}" y="{sy(660) + 18:.1f}" fill="{C_PRO}" font-size="11" text-anchor="end" {HALO}>Pro, 4.5% to $8,000</text>')
a(f'<text x="{sx(12):.1f}" y="{sy(55):.1f}" fill="{MUTED}" font-size="11" {HALO}>Light-spending wallets sit near the Standard line</text>')
a('</svg>')
(HERE / "out" / "chart_cashback_schedules.svg").write_text("\n".join(o) + "\n")
print(f"wrote out/chart_cashback_schedules.svg, {len(pts)} dots")
