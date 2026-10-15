#!/usr/bin/env python3
"""
Draws out/chart_reserve_fund_by_month.svg in the site's dark style. Stacked bars of the reserve fund's value at the end
of each month from January 2024 to September 2026, in millions of dollars, split into six groups of holdings.

Colors  six series, stacked from the bottom in a fixed order. The five named holdings take the first five categorical
        slots of the reference palette, dark steps, validated as an adjacent set on the site's surface #0d1116, and the
        remainder, other stablecoins and ETH, a neutral gray step, so it reads as a remainder. A legend names every group,
        each bar's hover text gives every group's value, and the downloads give the table, so identity never rests on
        color alone. A 2px surface gap separates stacked segments. Text uses the text colors.
Values  millions of dollars. Two totals are labeled, December 2024 and September 2026, the months the title names.
Every value, label, the title and the description come from out/chart_data.csv and out/results.json, which
reserve_fund_review.py writes. Run after the main script, as python3 make_chart_svg.py, with Python 3.8 or later.
"""
import csv
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE / "out" / "chart_data.csv", encoding="utf-8")))
exact = {r["month"]: r for r in csv.DictReader(open(HERE / "out" / "month_end.csv", encoding="utf-8"))}
res = json.load(open(HERE / "out" / "results.json", encoding="utf-8"))
GROUPS = ["USDtb", "Curve USDtb/USDC pool", "BUIDL and USTB", "sDAI and sUSDS", "Uniswap V3 positions", "Other stablecoins and ETH"]
LEGEND = GROUPS
COLORS = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#5b6573"]
assert len(rows) == 33 and rows[0]["month"] == "2024-01" and rows[-1]["month"] == "2026-09"
assert [k[:-5] for k in list(rows[0])[1:7]] == GROUPS

BG, RULE, TEXT, MUTED = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)", "var(--sx-muted, #99a3b0)")
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
W, H = 800, 466
X0, X1 = 52, 784
YT, YB = 108, 366
YMAX = Decimal(70)
SLOT = (X1 - X0) / len(rows)
BARW = 14
BOLD = ' font-weight="600"'
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def q(v, places=1):
    return Decimal(v).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def sy(m):
    return YB - (YB - YT) * float(Decimal(m) / YMAX)


def label(month):
    y, m = month.split("-")
    return MONTHS[int(m) - 1] + " " + y


dec = Decimal(rows[[r["month"] for r in rows].index("2024-12")]["total ($M)"])
sep = Decimal(rows[-1]["total ($M)"])
growth = (sep / dec - 1) * 100
title = f"The reserve fund passed $60 million in December 2024 and grew {q(growth, 0)}% by September 2026"
subtitle = "Value at the end of each month, January 2024 to September 2026, in millions of dollars, with stablecoins at $1"
desc = ("Stacked bar chart of the value of Ethena's reserve fund at the end of each month from January 2024 to September 2026, "
        "in millions of dollars, split into USDtb, the Curve USDtb/USDC pool position, BUIDL and USTB, sDAI and sUSDS, "
        "Uniswap V3 positions, and other stablecoins and ETH. Month-end totals in millions of dollars, "
        + ", ".join(f"{label(r['month'])} {q(r['total ($M)'])}" for r in rows) + ".")

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="rf-t rf-d" font-family="{FONT}">')
a('<title id="rf-t">Ethena\'s reserve fund at the end of each month, January 2024 to September 2026</title>')
a(f'<desc id="rf-d">{desc}</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
a(f'<text x="20" y="30" fill="{TEXT}" font-size="16"{BOLD}>{title}</text>')
a(f'<text x="20" y="50" fill="{MUTED}" font-size="12">{subtitle}</text>')
# Legend, two rows of three.
for i, name in enumerate(LEGEND):
    lx = 20 + (i % 3) * 230
    ly = 72 + (i // 3) * 18
    a(f'<rect x="{lx}" y="{ly - 9}" width="10" height="10" rx="2" fill="{COLORS[i]}"/>')
    a(f'<text x="{lx + 16}" y="{ly}" fill="{TEXT}" font-size="12">{name}</text>')
# Grid and axis.
for m in range(0, 71, 10):
    y = sy(m)
    a(f'<line x1="{X0}" x2="{X1}" y1="{y:.1f}" y2="{y:.1f}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{X0 - 8}" y="{y + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">{m}</text>')
# Bars.
for i, r in enumerate(rows):
    cx = X0 + SLOT * (i + 0.5)
    x = cx - BARW / 2
    vals = [Decimal(r[g + " ($M)"]) for g in GROUPS]
    total = Decimal(r["total ($M)"])
    ex = exact[r["month"]]
    def mm(x):
        v = q(Decimal(x) / 10 ** 6, 2)
        return str(v) if v > 0 else "under 0.01"
    parts = ", ".join(f"{LEGEND[k]} {mm(ex[g])}" for k, g in enumerate(GROUPS) if Decimal(ex[g]) > 0)
    a(f'<g><title>{label(r["month"])}. Total {q(Decimal(ex["total_usd"]) / 10 ** 6, 2)} million dollars. {parts}</title>')
    base = Decimal(0)
    drawn = [k for k, v in enumerate(vals) if sy(0) - sy(v) >= 0.5]
    for k, v in enumerate(vals):
        if k not in drawn:
            base += v
            continue
        y1, y0 = sy(base + v), sy(base)
        top = k == drawn[-1]
        h = y0 - y1
        if top and h > 4:
            a(f'<path d="M{x:.1f},{y0:.1f} V{y1 + 3:.1f} a3,3 0 0 1 3,-3 H{x + BARW - 3:.1f} a3,3 0 0 1 3,3 V{y0:.1f} Z" '
              f'fill="{COLORS[k]}" stroke="{BG}" stroke-width="1"/>')
        else:
            a(f'<rect x="{x:.1f}" y="{y1:.1f}" width="{BARW}" height="{h:.1f}" fill="{COLORS[k]}" stroke="{BG}" stroke-width="1"/>')
        base += v
    # A hit area as tall as the plot, so the hover text works anywhere above the bar.
    a(f'<rect x="{cx - SLOT / 2:.1f}" y="{YT}" width="{SLOT:.1f}" height="{YB - YT}" fill="transparent"/>')
    a('</g>')
    if r["month"] in ("2024-12", "2026-09"):
        a(f'<text x="{cx:.1f}" y="{sy(total) - 7:.1f}" fill="{TEXT}" font-size="12"{BOLD} text-anchor="middle">{q(total)}</text>')
    if r["month"].endswith("-01") or r["month"].endswith("-07"):
        a(f'<line x1="{cx:.1f}" x2="{cx:.1f}" y1="{YB}" y2="{YB + 5}" stroke="{MUTED}" stroke-width="1"/>')
        a(f'<text x="{cx:.1f}" y="{YB + 19}" fill="{MUTED}" font-size="11" text-anchor="middle">{label(r["month"])}</text>')
a(f'<line x1="{X0}" x2="{X1}" y1="{YB}" y2="{YB}" stroke="{MUTED}" stroke-width="1"/>')
notes = [
    "Archive reads at the last block of each month, on two RPCs that gave identical answers. Stablecoins and BUIDL at $1, sDAI and sUSDS at their vaults'",
    "conversion rates, the Curve position at the fund's share of the pool's USDC and USDtb, Uniswap positions at their tokens and uncollected fees,",
    "ETH at Chainlink's ETH/USD price, USTB at a price interpolated between the fund's purchase and redemption prices.",
    f"The fund is the Safe 0x2b5ab59163a6e93b4486f6055d33ca4a115dd4d5. At Ethereum block {res['read_block']:,} on October 12, 2026 it was worth {q(Decimal(res['value_usd']) / 10 ** 6, 2)} million dollars.",
]
for k, t in enumerate(notes):
    a(f'<text x="20" y="{H - 55 + 13 * k}" fill="{MUTED}" font-size="10">{t}</text>')
a('</svg>')
(HERE / "out" / "chart_reserve_fund_by_month.svg").write_text("\n".join(o) + "\n", encoding="utf-8")
print("wrote out/chart_reserve_fund_by_month.svg |", title)
