#!/usr/bin/env python3
"""
Draws out/chart_repeat_spending.svg in the site's dark style. Two lines, the share of wallets with a
spend event in each week after the week of their first spend, for wallets that first spent before
the beta week and for those that first spent in the beta's first four weeks.

Every point, label, the title and the description come from out/weekly_shares.csv, which
ethenapay_repeat_spending_review.py writes. Run after the main script: python3 make_chart_svg.py
"""
import csv
from pathlib import Path

HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE / "out" / "weekly_shares.csv")))
groups = {}
for r in rows:
    groups.setdefault(r["group"], []).append(r)
PRE, BETA = "first spend June 4 to August 30", "first spend August 31 to September 27"
assert set(groups) == {PRE, BETA}
pre, beta = groups[PRE], groups[BETA]
assert [int(r["week_after_first"]) for r in pre] == [1, 2, 3, 4, 5]
assert [int(r["week_after_first"]) for r in beta] == [1, 2, 3, 4]

BG, RULE, TEXT, MUTED = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)",
                         "var(--sx-muted, #99a3b0)")
C_BETA = "#3987e5"
C_PRE = "#d95926"
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
HALO = f'style="paint-order:stroke;stroke:{BG};stroke-width:4px;stroke-linejoin:round"'
W, H = 800, 466
X0, X1, Y0, Y1 = 74, 600, 92, 404
KMIN, KMAX = 1, 5


def sx(k):
    return X0 + (X1 - X0) * (k - KMIN) / (KMAX - KMIN)


def sy(v):
    return Y1 - (Y1 - Y0) * v


def share(r):
    return float(r["share"])


b1 = beta[0]
title = "Four in five wallets of the first four beta cohorts spent again the next week"
subtitle = "Share of wallets with a spend event in each week after their first spend, weeks to October 4, 2026."
assert round(share(b1) * 5) == 4
desc = (f"Two lines. Wallets that first spent from August 31 to September 27, {beta[0]['wallets']} in all, "
        + ", ".join(f"{share(r):.0%} in week {r['week_after_first']} of {r['wallets_observed']} observed" for r in beta)
        + f". Wallets that first spent from June 4 to August 30, {pre[0]['wallets']} in all, "
        + ", ".join(f"{share(r):.0%} in week {r['week_after_first']}" for r in pre) + ".")

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="rs-t rs-d" font-family="{FONT}">')
a('<title id="rs-t">EthenaPay repeat spending by week of first spend, to October 4, 2026</title>')
a(f'<desc id="rs-d">{desc}</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
a(f'<text x="20" y="30" fill="{TEXT}" font-size="16" font-weight="600">{title}</text>')
a(f'<text x="20" y="52" fill="{MUTED}" font-size="12">{subtitle}</text>')
for v in (0, 0.2, 0.4, 0.6, 0.8, 1.0):
    a(f'<line x1="{X0}" x2="{X1}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{X0 - 8}" y="{sy(v) + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">{v * 100:.0f}%</text>')
for k in range(KMIN, KMAX + 1):
    a(f'<line x1="{sx(k):.1f}" x2="{sx(k):.1f}" y1="{Y1}" y2="{Y1 + 5}" stroke="{MUTED}" stroke-width="1"/>')
    a(f'<text x="{sx(k):.1f}" y="{Y1 + 19}" fill="{MUTED}" font-size="11" text-anchor="middle">{k}</text>')
a(f'<text x="{(X0 + X1) / 2:.1f}" y="{Y1 + 40}" fill="{MUTED}" font-size="11" text-anchor="middle">'
  'Weeks after the week of first spend</text>')

for series, color, name in ((pre, C_PRE, "pre"), (beta, C_BETA, "beta")):
    pts = " ".join(f"{sx(int(r['week_after_first'])):.1f},{sy(share(r)):.1f}" for r in series)
    a(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>')
    for r in series:
        k = int(r["week_after_first"])
        a(f'<g><title>Week {k}, {r["wallets_spending"]} of {r["wallets_observed"]} wallets, {share(r):.1%}</title>'
          f'<circle cx="{sx(k):.1f}" cy="{sy(share(r)):.1f}" r="4" fill="{color}" stroke="{BG}" stroke-width="2"/></g>')
        above = name == "beta" or k == KMAX
        a(f'<text x="{sx(k):.1f}" y="{sy(share(r)) + (-10 if above else 18):.1f}" fill="{TEXT}" font-size="11" '
          f'text-anchor="middle" {HALO}>{share(r):.0%}</text>')

# direct labels to the right of each line's last point
lb, lp = beta[-1], pre[-1]
a(f'<text x="{sx(int(lb["week_after_first"])) + 24:.1f}" y="{sy(share(lb)) - 30:.1f}" fill="{C_BETA}" font-size="12" '
  f'font-weight="600">First spend Aug 31 to Sep 27</text>')
a(f'<text x="{sx(int(lb["week_after_first"])) + 24:.1f}" y="{sy(share(lb)) - 16:.1f}" fill="{MUTED}" font-size="11">'
  f'{lb["wallets"]} wallets, {lb["wallets_observed"]} observed in week {lb["week_after_first"]}</text>')
a(f'<text x="{sx(int(lp["week_after_first"])) + 12:.1f}" y="{sy(share(lp)) + 4:.1f}" fill="{C_PRE}" font-size="12" '
  f'font-weight="600">First spend Jun 4 to Aug 30</text>')
a(f'<text x="{sx(int(lp["week_after_first"])) + 12:.1f}" y="{sy(share(lp)) + 18:.1f}" fill="{MUTED}" font-size="11">'
  f'{lp["wallets"]} wallets</text>')
a("</svg>")
(HERE / "out" / "chart_repeat_spending.svg").write_text("\n".join(o) + "\n")
print("wrote out/chart_repeat_spending.svg")
