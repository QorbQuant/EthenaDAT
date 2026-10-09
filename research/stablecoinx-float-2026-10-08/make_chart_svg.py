#!/usr/bin/env python3
"""
Draws out/chart_turnover.svg, cumulative USDE volume from June 26 to October 8, 2026 as a multiple of the
19,063,653 shares the resale prospectus counted as freely tradable on August 28, in the site's palette.
Every point and label comes from out/chart_turnover.csv and out/results.json, which stablecoinx_float_review.py writes.

Run after the main script:  python3 make_chart_svg.py
"""
import csv
import json
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
pts = list(csv.DictReader(open(HERE / "out" / "chart_turnover.csv")))
res = json.loads((HERE / "out" / "results.json").read_text())
FREE = res["freely_tradable"]
assert len(pts) == 73 and pts[0]["date"] == "2026-06-26" and pts[-1]["date"] == "2026-10-08"
assert int(pts[-1]["cumulative_volume"]) == res["volume_total"]
assert f"{int(pts[-1]['cumulative_volume']) / FREE:.2f}" == res["times_free"] == "19.97"

BG, RULE, TEXT, MUTED = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)", "var(--sx-muted, #99a3b0)")
LINE = "var(--sx-blue, #8aa9cf)"
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
W, H = 800, 466
L, R, T, B = 56, 92, 84, 72
pw, ph = W - L - R, H - T - B
YMAX = 21.0
n = len(pts)


def x(i):
    return L + pw * i / (n - 1)


def y(v):
    return T + ph * (1 - v / YMAX)


def mult(p):
    return int(p["cumulative_volume"]) / FREE


def nice_date(d):
    dd = date.fromisoformat(d)
    return dd.strftime("%B ") + str(dd.day)


o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="to-t to-d" font-family="{FONT}">')
a('<title id="to-t">Cumulative USDE volume as a multiple of the freely tradable shares, June 26 to October 8, 2026</title>')
big = res["big_days"]
desc = (f"Line chart. From June 26 to October 8, 2026, USDE traded {res['volume_total']:,} shares, {res['times_free']} times the "
        f"{FREE:,} shares the resale prospectus counted as freely tradable on August 28. The largest single sessions were "
        + ", ".join(f"{nice_date(d)} with {v[0]:,} shares, {v[1]} times the count" for d, v in big.items()) + ".")
a(f'<desc id="to-d">{desc}</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
a(f'<text x="20" y="30" fill="{TEXT}" font-size="16" font-weight="600">USDE’s volume came to {res["times_free"]} times its freely tradable shares in 73 sessions</text>')
a(f'<text x="20" y="52" fill="{MUTED}" font-size="12">Cumulative volume from June 26 to October 8, 2026, divided by the {FREE:,} shares counted as freely tradable</text>')
for g in range(0, 21, 5):
    gy = y(g)
    a(f'<line x1="{L}" x2="{L + pw}" y1="{gy:.1f}" y2="{gy:.1f}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{L - 8}" y="{gy + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">{g}×</text>')
seen = set()
for i, p in enumerate(pts):
    m = p["date"][:7]
    if m not in seen:
        seen.add(m)
        a(f'<line x1="{x(i):.1f}" x2="{x(i):.1f}" y1="{T + ph}" y2="{T + ph + 5}" stroke="{MUTED}" stroke-width="1"/>')
        if i > 0:
            a(f'<text x="{x(i):.1f}" y="{T + ph + 20}" fill="{MUTED}" font-size="11" text-anchor="middle">{date.fromisoformat(p["date"]).strftime("%B")}</text>')
path = " ".join(f'{"M" if i == 0 else "L"}{x(i):.1f},{y(mult(p)):.1f}' for i, p in enumerate(pts))
a(f'<path d="{path}" fill="none" stroke="{LINE}" stroke-width="2" stroke-linejoin="round"/>')
for i, p in enumerate(pts):
    tip = (f"{nice_date(p['date'])}, 2026. {int(p['volume']):,} shares traded, {int(p['volume']) / FREE * 100:.1f}% of the freely tradable count. "
           f"Cumulative {int(p['cumulative_volume']):,}, {mult(p):.2f} times")
    a(f'<g><title>{tip}</title><circle cx="{x(i):.1f}" cy="{y(mult(p)):.1f}" r="7" fill="transparent"/></g>')
labels = {"2026-07-02": (8, 14), "2026-08-21": (-10, -6), "2026-08-27": (10, 16)}
for d, v in big.items():
    i = next(k for k, p in enumerate(pts) if p["date"] == d)
    cx, cy = x(i), y(mult(pts[i]))
    a(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="{LINE}" stroke="{BG}" stroke-width="2"/>')
    dx, dy = labels[d]
    anchor = "end" if dx < 0 else "start"
    a(f'<text x="{cx + dx:.1f}" y="{cy + dy:.1f}" fill="{TEXT}" font-size="11" text-anchor="{anchor}">{nice_date(d)}, {v[1]}× in one session</text>')
ex, ey = x(n - 1), y(mult(pts[-1]))
a(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="4" fill="{LINE}" stroke="{BG}" stroke-width="2"/>')
a(f'<text x="{ex + 8:.1f}" y="{ey + 4:.1f}" fill="{TEXT}" font-size="12" font-weight="600">{res["times_free"]}×</text>')
a(f'<text x="{ex + 8:.1f}" y="{ey + 19:.1f}" fill="{MUTED}" font-size="11">October 8</text>')
a(f'<text x="20" y="{H - 16}" fill="{MUTED}" font-size="11">Volume from S&amp;P Global Market Intelligence through StockAnalysis, checked against Yahoo Finance. Volume counts a share each time it trades.</text>')
a('</svg>')
svg = "\n".join(o) + "\n"
(HERE / "out" / "chart_turnover.svg").write_text(svg)
print(f"wrote chart_turnover.svg ({len(svg.encode())} bytes)")
print(" end", pts[-1]["date"], pts[-1]["cumulative_volume"], res["times_free"])
