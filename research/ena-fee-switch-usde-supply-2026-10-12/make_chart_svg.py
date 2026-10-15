#!/usr/bin/env python3
"""
Draws out/chart_usde_supply_milestones.svg in the site's dark style. USDe's total supply on Ethereum at the end of
every UTC day from January 1, 2024, and its 14 day trailing average, against the supply milestones of the ENA
fee switch.

Colors  two series in the first two categorical slots of the reference palette, dark steps, validated on the
        site's surface #0d1116. A legend names both lines, the milestones are labeled where they sit, and each
        day's hover text gives both values, so identity never rests on color alone. The milestone lines and the
        band of days when the 14 day average was at or above the first milestone use the neutral text colors.
Values  billions of USDe, read as dollars. The peak and the last day are labeled.
Every value, label, the title and the description come from out/chart_data.csv and out/results.json, which
fee_switch_supply.py writes. Run after the main script, as python3 make_chart_svg.py, with Python 3.8 or later.
"""
import csv
import json
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE / "out" / "chart_data.csv", encoding="utf-8")))
res = json.load(open(HERE / "out" / "results.json", encoding="utf-8"))
assert rows[0]["day"] == "2024-01-01" and rows[-1]["day"] == res["last_day"] and len(rows) == res["days"]

BG, RULE, TEXT, MUTED = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)", "var(--sx-muted, #99a3b0)")
BAND = "var(--sx-rule, #29313a)"
DAILY, AVG = "#3987e5", "#d95926"
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
HALO = f'style="paint-order:stroke;stroke:{BG};stroke-width:4px;stroke-linejoin:round"'
W, H = 800, 466
X0, X1 = 52, 724
YT, YB = 112, 376
YMAX = 16
D0, D1 = date.fromisoformat(rows[0]["day"]), date.fromisoformat(rows[-1]["day"])
MILESTONES = [("7.5", "5%"), ("10", "10%"), ("15", "15%")]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def x(d):
    return X0 + (X1 - X0) * (d - D0).days / (D1 - D0).days


def y(v):
    return YB - (YB - YT) * float(v) / YMAX


def full(d):
    return "%s %d, %d" % (MONTHS[d.month - 1], d.day, d.year)


def short(d):
    return "%s %d, %d" % (MONTHS[d.month - 1][:3], d.day, d.year)


def b2(v):
    return str(Decimal(v).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


pts = [(date.fromisoformat(r["day"]), Decimal(r["usde_supply_billion"]), Decimal(r["avg_14d_billion"]) if r["avg_14d_billion"] else None) for r in rows]
assert all(0 < p[1] < YMAX for p in pts)
top = max(pts, key=lambda p: p[1])
last = pts[-1]
need = Decimal(res["growth14_needed_pct"]).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
a14_first, a14_last = date.fromisoformat(res["active14_first"]), date.fromisoformat(res["active14_last"])
title = "USDe's 14 day average supply had to rise %s%% to reach the first ENA buyback milestone" % need
subtitle = "USDe's total supply on Ethereum at the end of each UTC day, January 1, 2024 to %s, in billions" % full(D1)
desc = ("Two lines, USDe's total supply on Ethereum at the end of each day and its 14 day trailing average, from %s to %s, "
        "in billions of USDe, with dashed lines at the fee switch milestones of 7.5, 10 and 15 billion. Day-end supply peaked at %s billion "
        "on %s. The 14 day average was at or above 7.5 billion from %s to %s. On %s day-end supply was %s billion and the 14 day average "
        "%s billion.") % (full(D0), full(D1), b2(top[1]), full(top[0]), full(a14_first), full(a14_last), full(D1), b2(last[1]), b2(last[2]))

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="fs-t fs-d" font-family="{FONT}">')
a(f'<title id="fs-t">USDe supply against the ENA fee switch milestones, {full(D0)} to {full(D1)}</title>')
a(f'<desc id="fs-d">{desc}</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
a(f'<text x="20" y="30" fill="{TEXT}" font-size="16" font-weight="600">{title}</text>')
a(f'<text x="20" y="52" fill="{MUTED}" font-size="12">{subtitle}</text>')
# legend
LY = 80
a(f'<line x1="20" x2="42" y1="{LY - 4}" y2="{LY - 4}" stroke="{DAILY}" stroke-width="2"/>')
a(f'<text x="48" y="{LY}" fill="{MUTED}" font-size="12">Day-end supply</text>')
a(f'<line x1="150" x2="172" y1="{LY - 4}" y2="{LY - 4}" stroke="{AVG}" stroke-width="2"/>')
a(f'<text x="178" y="{LY}" fill="{MUTED}" font-size="12">14 day trailing average</text>')
a(f'<rect x="336" y="{LY - 11}" width="14" height="12" fill="{BAND}"/>')
a(f'<text x="356" y="{LY}" fill="{MUTED}" font-size="12">14 day average at or above 7.5 billion</text>')
# band of days when the 14 day average was at or above the first milestone
a(f'<rect x="{x(a14_first):.1f}" y="{YT}" width="{x(a14_last) - x(a14_first):.1f}" height="{YB - YT}" fill="{BAND}" fill-opacity="0.75"/>')
# grid and axis labels
for v in range(0, YMAX + 1, 4):
    a(f'<line x1="{X0}" x2="{X1}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{X0 - 8}" y="{y(v) + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">{v}</text>')
for yr in (2024, 2025, 2026):
    for m in (1, 7):
        d = date(yr, m, 1)
        if D0 <= d <= D1:
            a(f'<line x1="{x(d):.1f}" x2="{x(d):.1f}" y1="{YB}" y2="{YB + 5}" stroke="{MUTED}" stroke-width="1"/>')
            a(f'<text x="{x(d):.1f}" y="{YB + 20}" fill="{MUTED}" font-size="11" text-anchor="middle">{MONTHS[m - 1][:3]} {yr}</text>')
# milestones
for v, take in MILESTONES:
    a(f'<line x1="{X0}" x2="{X1}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{MUTED}" stroke-width="1" stroke-dasharray="4 4"/>')
    a(f'<text x="{X1 + 6}" y="{y(v) + 4:.1f}" fill="{MUTED}" font-size="11">{v}B, {take}</text>')
a(f'<text x="{X1 + 6}" y="{y(16) + 4:.1f}" fill="{MUTED}" font-size="11">Take rate</text>')


def path(vals):
    segs, cur = [], []
    for d, v in vals:
        if v is None:
            if cur:
                segs.append(cur)
            cur = []
            continue
        cur.append("%.1f,%.1f" % (x(d), y(v)))
    if cur:
        segs.append(cur)
    return " ".join("M" + " L".join(s) for s in segs)


a(f'<path d="{path([(p[0], p[1]) for p in pts])}" fill="none" stroke="{DAILY}" stroke-width="2" stroke-linejoin="round"/>')
a(f'<path d="{path([(p[0], p[2]) for p in pts])}" fill="none" stroke="{AVG}" stroke-width="2" stroke-linejoin="round"/>')
# labels for the peak and the last day
a(f'<circle cx="{x(top[0]):.1f}" cy="{y(top[1]):.1f}" r="4" fill="{DAILY}" stroke="{BG}" stroke-width="2"/>')
a(f'<text x="{x(top[0]) + 8:.1f}" y="{y(top[1]) - 8:.1f}" fill="{TEXT}" font-size="12" font-weight="600" {HALO}>{b2(top[1])}B on {short(top[0])}</text>')
a(f'<circle cx="{x(last[0]):.1f}" cy="{y(last[1]):.1f}" r="4" fill="{DAILY}" stroke="{BG}" stroke-width="2"/>')
# The last day's label sits above both lines over its whole width, with a leader down to the point, and below the
# first milestone's line.
LABEL_W = 132
lx = x(last[0]) - 4
over = [y(v) for d, v1, v2 in pts for v in (v1, v2) if v is not None and lx - LABEL_W <= x(d) <= lx + 4]
ly = min(over) - 8
assert ly - 12 > y("7.5") + 2, "the last day's label would touch the first milestone's line"
a(f'<line x1="{x(last[0]):.1f}" x2="{x(last[0]):.1f}" y1="{y(last[1]) - 6:.1f}" y2="{ly + 2:.1f}" stroke="{MUTED}" stroke-width="1"/>')
a(f'<text x="{lx - 2:.1f}" y="{ly:.1f}" fill="{TEXT}" font-size="12" font-weight="600" text-anchor="end" {HALO}>{b2(last[1])}B on {short(last[0])}</text>')
# hover, one column per day
step = (X1 - X0) / (D1 - D0).days
for d, v, av in pts:
    t = "%s, supply %s billion" % (short(d), b2(v)) + (", 14 day average %s billion" % b2(av) if av is not None else "")
    a(f'<rect x="{x(d) - step / 2:.2f}" y="{YT}" width="{step:.2f}" height="{YB - YT}" fill="transparent"><title>{t}</title></rect>')
a(f'<text x="20" y="{H - 50}" fill="{MUTED}" font-size="11">Reads at the last block of each UTC day on two archive RPCs that gave identical answers, with USDe counted as one dollar.</text>')
a(f'<text x="20" y="{H - 34}" fill="{MUTED}" font-size="11">The total supply on Ethereum included the USDe locked there to back USDe on other chains.</text>')
a(f'<text x="20" y="{H - 18}" fill="{MUTED}" font-size="11">Milestones and take rates are those of the ENA holder vote that closed on September 2, 2026.</text>')
a('</svg>')
(HERE / "out" / "chart_usde_supply_milestones.svg").write_text("\n".join(o) + "\n", encoding="utf-8")
print("wrote out/chart_usde_supply_milestones.svg |", title)
