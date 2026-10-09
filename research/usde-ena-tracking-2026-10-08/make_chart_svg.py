#!/usr/bin/env python3
"""
Draws out/chart_usde_ena.svg in the site's dark style. Left, each of the 72 daily moves as a dot,
ENA's move across and USDE's up, with the fitted line and a line of equal moves. Right, mNAV at
each 4 pm close from June 26 to October 8, 2026.

Every point, label, the title and the description come from out/chart_data.csv and
out/results.json, which usde_ena_tracking_review.py writes. Run after the main script:
python3 make_chart_svg.py
"""
import csv
import json
import statistics
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE / "out" / "chart_data.csv")))
res = json.loads((HERE / "out" / "results.json").read_text())
moves = [(float(r["ena_move"]), float(r["usde_move"]), r["date"]) for r in rows if r["ena_move"]]
exact = {r["date"]: (Decimal(r["ena_move"]), Decimal(r["usde_move"])) for r in rows if r["ena_move"]}
mnav = [(date.fromisoformat(r["date"]), float(r["mnav_4pm"])) for r in rows]
d = res["daily_kraken"]
assert len(moves) == d["n"] == 72 and len(mnav) == 73

BG, RULE, TEXT, MUTED = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)",
                         "var(--sx-muted, #99a3b0)")
DOT = "#3987e5"
FIT = "#d95926"
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
HALO = f'style="paint-order:stroke;stroke:{BG};stroke-width:4px;stroke-linejoin:round"'
W, H = 800, 466
# left panel, the scatter
SX0, SX1, SY0, SY1 = 74, 384, 92, 410
XMIN, XMAX, YMIN, YMAX = -0.15, 0.30, -0.30, 0.90
# right panel, mNAV
MX0, MX1, MY0, MY1 = 470, 780, 92, 410
D0, D1 = date(2026, 6, 26), date(2026, 10, 8)
NMAX = 0.6


def sx(v):
    return SX0 + (SX1 - SX0) * (v - XMIN) / (XMAX - XMIN)


def sy(v):
    return SY1 - (SY1 - SY0) * (v - YMIN) / (YMAX - YMIN)


def mx(dd):
    return MX0 + (MX1 - MX0) * (dd - D0).days / (D1 - D0).days


def my(v):
    return MY1 - (MY1 - MY0) * v / NMAX


def nice(dd):
    return dd.strftime("%b ") + str(dd.day)


def full(dd):
    return dd.strftime("%B ") + str(dd.day)


def tip(v):
    # two decimals, half up, from the ten-decimal values in chart_data.csv, with a true minus sign
    s = f"{(v * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):+}%"
    return s.replace("-", "−")


def tick(v):
    return f"{v * 100:+.0f}%".replace("+0%", "0%").replace("-", "−")


xs, ys = [m[0] for m in moves], [m[1] for m in moves]
assert XMIN <= min(xs) and max(xs) <= XMAX and YMIN <= min(ys) and max(ys) <= YMAX, "a daily move falls outside the axes"
assert all(0 <= v <= NMAX for _, v in mnav), "an mNAV value falls outside the axis"
mxv, myv = statistics.mean(xs), statistics.mean(ys)
slope = sum((a - mxv) * (b - myv) for a, b in zip(xs, ys)) / sum((a - mxv) ** 2 for a in xs)
icpt = myv - slope * mxv
assert abs(slope - d["beta"]) < 1e-4  # chart_data holds moves rounded to six decimals
lo = min(mnav, key=lambda x: x[1])
hi = max(mnav, key=lambda x: x[1])
title = f"USDE moved the same way as ENA on {d['same_direction']} of {d['n']} days"
subtitle = f"Daily moves from one 4 pm New York close to the next, and mNAV at each close, {full(D0)} to {full(D1)}, 2026."
desc = (f"Left, {d['n']} daily moves, ENA across and USDE up, correlation {d['correlation']:.2f}, fitted slope "
        f"{d['beta']:.2f}. The two axes use different scales. Right, mNAV at the 4 pm close, {mnav[0][1]:.2f}× on "
        f"{full(mnav[0][0])}, a low of {lo[1]:.2f}× on {full(lo[0])}, a high of {hi[1]:.2f}× on {full(hi[0])} and "
        f"{mnav[-1][1]:.2f}× on {full(mnav[-1][0])}.")

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="ue-t ue-d" font-family="{FONT}">')
a('<title id="ue-t">USDE against ENA, daily moves and mNAV, June 26 to October 8, 2026</title>')
a(f'<desc id="ue-d">{desc}</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
a(f'<text x="20" y="30" fill="{TEXT}" font-size="16" font-weight="600">{title}</text>')
a(f'<text x="20" y="52" fill="{MUTED}" font-size="12">{subtitle}</text>')
a(f'<text x="{SX0}" y="{SY0 - 14}" fill="{TEXT}" font-size="13" font-weight="600">Daily move, ENA across and USDE up</text>')
a(f'<text x="{MX0}" y="{MY0 - 14}" fill="{TEXT}" font-size="13" font-weight="600">mNAV at the 4 pm close</text>')
# scatter grid
for v in (-0.2, 0.0, 0.2, 0.4, 0.6, 0.8):
    a(f'<line x1="{SX0}" x2="{SX1}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{SX0 - 8}" y="{sy(v) + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">{tick(v)}</text>')
for v in (-0.1, 0.0, 0.1, 0.2, 0.3):
    a(f'<line x1="{sx(v):.1f}" x2="{sx(v):.1f}" y1="{SY0}" y2="{SY1}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{sx(v):.1f}" y="{SY1 + 18}" fill="{MUTED}" font-size="11" text-anchor="middle">{tick(v)}</text>')
# equal moves and the fitted line, clipped to the panel
def segment(f):
    pts = []
    for xv in (XMIN, XMAX):
        yv = f(xv)
        pts.append((xv, yv))
    (x0, y0), (x1, y1) = pts
    if y1 > YMAX:
        x1 = x0 + (YMAX - y0) * (x1 - x0) / (y1 - y0)
        y1 = YMAX
    if y0 < YMIN:
        x0 = x0 + (YMIN - y0) * (x1 - x0) / (y1 - y0)
        y0 = YMIN
    return x0, y0, x1, y1


x0, y0, x1, y1 = segment(lambda v: v)
a(f'<line x1="{sx(x0):.1f}" y1="{sy(y0):.1f}" x2="{sx(x1):.1f}" y2="{sy(y1):.1f}" stroke="{MUTED}" stroke-width="1.5" '
  f'stroke-dasharray="4 4"/>')
x0, y0, x1, y1 = segment(lambda v: icpt + slope * v)
a(f'<line x1="{sx(x0):.1f}" y1="{sy(y0):.1f}" x2="{sx(x1):.1f}" y2="{sy(y1):.1f}" stroke="{FIT}" stroke-width="2"/>')
for xv, yv, dt in moves:
    ex, ey = exact[dt]
    a(f'<g><title>{nice(date.fromisoformat(dt))}, ENA {tip(ex)}, USDE {tip(ey)}</title>'
      f'<circle cx="{sx(xv):.1f}" cy="{sy(yv):.1f}" r="3.5" fill="{DOT}" fill-opacity="0.8" stroke="{BG}" stroke-width="1"/></g>')
# legend under the scatter
LY = SY1 + 40
a(f'<line x1="{SX0}" x2="{SX0 + 22}" y1="{LY - 4}" y2="{LY - 4}" stroke="{FIT}" stroke-width="2"/>')
a(f'<text x="{SX0 + 28}" y="{LY}" fill="{MUTED}" font-size="11">fitted line, slope {d["beta"]:.2f}</text>')
a(f'<line x1="{SX0 + 170}" x2="{SX0 + 192}" y1="{LY - 4}" y2="{LY - 4}" stroke="{MUTED}" stroke-width="1.5" stroke-dasharray="4 4"/>')
a(f'<text x="{SX0 + 198}" y="{LY}" fill="{MUTED}" font-size="11">equal moves</text>')
big = max(moves, key=lambda m: m[1])
a(f'<text x="{sx(big[0]) - 8:.1f}" y="{sy(big[1]) + 4:.1f}" fill="{TEXT}" font-size="11" text-anchor="end" {HALO}>'
  f'{nice(date.fromisoformat(big[2]))}</text>')
# mNAV panel
for v in (0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6):
    a(f'<line x1="{MX0}" x2="{MX1}" y1="{my(v):.1f}" y2="{my(v):.1f}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{MX0 - 8}" y="{my(v) + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">{v:.1f}</text>')
for m in (7, 8, 9, 10):
    dd = date(2026, m, 1)
    a(f'<line x1="{mx(dd):.1f}" x2="{mx(dd):.1f}" y1="{MY1}" y2="{MY1 + 5}" stroke="{MUTED}" stroke-width="1"/>')
    a(f'<text x="{mx(dd):.1f}" y="{MY1 + 18}" fill="{MUTED}" font-size="11" text-anchor="middle">{dd.strftime("%b")} 1</text>')
pts = " ".join(f"{mx(dd):.1f},{my(v):.1f}" for dd, v in mnav)
a(f'<polyline points="{pts}" fill="none" stroke="{DOT}" stroke-width="2" stroke-linejoin="round"/>')
for dd, v in mnav:
    a(f'<g><title>{nice(dd)}, mNAV {v:.3f}×</title><circle cx="{mx(dd):.1f}" cy="{my(v):.1f}" r="4" fill="transparent"/></g>')
for (dd, v), anchor, dy in ((lo, "start", 16), (hi, "end", -10)):
    a(f'<circle cx="{mx(dd):.1f}" cy="{my(v):.1f}" r="4" fill="{DOT}" stroke="{BG}" stroke-width="2"/>')
    a(f'<text x="{mx(dd) + (6 if anchor == "start" else -6):.1f}" y="{my(v) + dy:.1f}" fill="{TEXT}" font-size="11" '
      f'text-anchor="{anchor}" {HALO}>{v:.2f}× on {nice(dd)}</text>')
a("</svg>")
(HERE / "out" / "chart_usde_ena.svg").write_text("\n".join(o) + "\n")
print("wrote out/chart_usde_ena.svg")
