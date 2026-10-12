#!/usr/bin/env python3
"""
Draws out/chart_book_value.svg in the site's dark style. Three lines from the June 30 close to the
October 8 close, 2026. Token NAV per share at ENA's price at the close, USDE's close, and book value
per Class A share from the June 30 balance sheet, which stays flat until the next 10-Q.

Every point, label, the title and the description come from out/per_share_by_session.csv and
out/results.json, which stablecoinx_book_value_review.py writes. Run after the main script:
python3 make_chart_svg.py
"""
import csv
import json
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE / "out" / "per_share_by_session.csv")))
res = json.loads((HERE / "out" / "results.json").read_text())
pts = [(date.fromisoformat(r["date"]), float(r["ena_per_class_a_share"]), float(r["usde_close"])) for r in rows]
bv = res["book_value_per_class_a_share"]
assert len(pts) == res["sessions"] == 71
first = res["first_close_above_book"]
o8 = res["october8"]
j30 = res["june30"]

BG, RULE, TEXT, MUTED = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)",
                         "var(--sx-muted, #99a3b0)")
C_ENA = "#3987e5"
C_USDE = "#d95926"
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
HALO = f'style="paint-order:stroke;stroke:{BG};stroke-width:4px;stroke-linejoin:round"'
W, H = 800, 466
X0, X1, Y0, Y1 = 64, 600, 104, 412
D0, D1 = date(2026, 6, 30), date(2026, 10, 8)
VMAX = 35.0


def sx(d):
    return X0 + (X1 - X0) * (d - D0).days / (D1 - D0).days


def sy(v):
    return Y1 - (Y1 - Y0) * v / VMAX


def nice(d):
    return d.strftime("%b ") + str(d.day)


def full(d):
    return d.strftime("%B ") + str(d.day)


assert all(0 < e <= VMAX and 0 < u <= VMAX for _, e, u in pts), "a value falls outside the axis"
assert pts[0][0] == D0 and pts[-1][0] == D1
fd = date.fromisoformat(first["date"])
hi = max(pts, key=lambda p: p[1])
title = f"USDE closed above June 30 book value per share from {full(fd)}"
subtitle = (f"Per Class A share, {full(D0)} to {full(D1)}, 2026. Token NAV at ENA's 4 pm price, USDE's close "
            "and the 10-Q's book value.")
desc = (f"Three lines. Token NAV per share at the close, ${pts[0][1]:.2f} on {full(D0)}, a high of ${hi[1]:.2f} on "
        f"{full(hi[0])} and ${pts[-1][1]:.2f} on {full(D1)}. USDE's close, ${pts[0][2]:.2f} on {full(D0)}, "
        f"first above book value on {full(fd)} at ${first['usde_close']:.2f}, and ${pts[-1][2]:.2f} on {full(D1)}. "
        f"Book value per Class A share at June 30, ${bv:.2f}, flat across the chart.")

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="bv-t bv-d" font-family="{FONT}">')
a('<title id="bv-t">StablecoinX book value, token NAV and USDE per Class A share, June 30 to October 8, 2026</title>')
a(f'<desc id="bv-d">{desc}</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
a(f'<text x="20" y="30" fill="{TEXT}" font-size="16" font-weight="600">{title}</text>')
a(f'<text x="20" y="52" fill="{MUTED}" font-size="12">{subtitle}</text>')
# legend row
LY = 78
a(f'<line x1="20" x2="42" y1="{LY - 4}" y2="{LY - 4}" stroke="{C_ENA}" stroke-width="2"/>')
a(f'<text x="48" y="{LY}" fill="{MUTED}" font-size="11">Token NAV per share</text>')
a(f'<line x1="196" x2="218" y1="{LY - 4}" y2="{LY - 4}" stroke="{C_USDE}" stroke-width="2"/>')
a(f'<text x="224" y="{LY}" fill="{MUTED}" font-size="11">USDE close</text>')
a(f'<line x1="310" x2="332" y1="{LY - 4}" y2="{LY - 4}" stroke="{TEXT}" stroke-width="1.5" stroke-dasharray="5 4"/>')
a(f'<text x="338" y="{LY}" fill="{MUTED}" font-size="11">Book value per Class A share at June 30</text>')
# grid
for v in range(0, 36, 5):
    a(f'<line x1="{X0}" x2="{X1}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{X0 - 8}" y="{sy(v) + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">${v}</text>')
for m in (7, 8, 9, 10):
    d = date(2026, m, 1)
    a(f'<line x1="{sx(d):.1f}" x2="{sx(d):.1f}" y1="{Y1}" y2="{Y1 + 5}" stroke="{MUTED}" stroke-width="1"/>')
    a(f'<text x="{sx(d):.1f}" y="{Y1 + 19}" fill="{MUTED}" font-size="11" text-anchor="middle">{d.strftime("%b")} 1</text>')
# book value
a(f'<line x1="{X0}" x2="{X1}" y1="{sy(bv):.1f}" y2="{sy(bv):.1f}" stroke="{TEXT}" stroke-width="1.5" stroke-dasharray="5 4"/>')
# lines
for idx, color in ((1, C_ENA), (2, C_USDE)):
    line = " ".join(f"{sx(p[0]):.1f},{sy(p[idx]):.1f}" for p in pts)
    a(f'<polyline points="{line}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>')
# hover targets, one per session
step = (X1 - X0) / (D1 - D0).days
for d, e, u in pts:
    a(f'<g><title>{nice(d)}, token NAV per share ${e:.2f}, USDE ${u:.2f}, book value ${bv:.2f}</title>'
      f'<rect x="{sx(d) - step * 0.75:.1f}" y="{Y0}" width="{step * 1.5:.1f}" height="{Y1 - Y0}" fill="transparent"/></g>')
# the crossing
cx, cy = sx(fd), sy(first["usde_close"])
a(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="{C_USDE}" stroke="{BG}" stroke-width="2"/>')
a(f'<text x="{cx - 8:.1f}" y="{cy - 10:.1f}" fill="{TEXT}" font-size="11" text-anchor="end" {HALO}>'
  f'{nice(fd)}, ${first["usde_close"]:.2f}</text>')
# end labels
ex = sx(D1) + 10
a(f'<circle cx="{sx(D1):.1f}" cy="{sy(pts[-1][1]):.1f}" r="4" fill="{C_ENA}" stroke="{BG}" stroke-width="2"/>')
a(f'<text x="{ex:.1f}" y="{sy(pts[-1][1]) - 2:.1f}" fill="{C_ENA}" font-size="12" font-weight="600">Token NAV per share</text>')
a(f'<text x="{ex:.1f}" y="{sy(pts[-1][1]) + 13:.1f}" fill="{TEXT}" font-size="11">${pts[-1][1]:.2f} on {nice(D1)}</text>')
a(f'<circle cx="{sx(D1):.1f}" cy="{sy(pts[-1][2]):.1f}" r="4" fill="{C_USDE}" stroke="{BG}" stroke-width="2"/>')
a(f'<text x="{ex:.1f}" y="{sy(pts[-1][2]) - 2:.1f}" fill="{C_USDE}" font-size="12" font-weight="600">USDE</text>')
a(f'<text x="{ex:.1f}" y="{sy(pts[-1][2]) + 13:.1f}" fill="{TEXT}" font-size="11">${pts[-1][2]:.2f} on {nice(D1)}</text>')
a(f'<text x="{ex:.1f}" y="{sy(bv) + 4:.1f}" fill="{TEXT}" font-size="12" font-weight="600">Book value</text>')
a(f'<text x="{ex:.1f}" y="{sy(bv) + 19:.1f}" fill="{TEXT}" font-size="11">${bv:.2f} at June 30</text>')
# start labels, under the book value line and above USDE's line, clear of both
a(f'<text x="{sx(D0) + 6:.1f}" y="{sy(bv) + 17:.1f}" fill="{TEXT}" font-size="11" {HALO}>'
  f'{nice(D0)}, token NAV per share ${pts[0][1]:.2f}</text>')
a(f'<text x="{sx(D0) + 6:.1f}" y="{sy(pts[0][2]) - 12:.1f}" fill="{TEXT}" font-size="11" {HALO}>'
  f'{nice(D0)}, USDE ${pts[0][2]:.2f}</text>')
assert max(u for d, e, u in pts if (d - D0).days <= 25) < bv - 3.5, "start labels would touch USDE's line"
a("</svg>")
(HERE / "out" / "chart_book_value.svg").write_text("\n".join(o) + "\n")
print("wrote out/chart_book_value.svg")
