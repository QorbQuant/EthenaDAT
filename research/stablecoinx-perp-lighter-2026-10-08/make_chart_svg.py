#!/usr/bin/env python3
"""
Draws out/chart_off_hours.svg, two scatter panels in the site's dark style. Each dot is one
stretch between sessions, from a close to the next open, between August 26 and October 8,
2026. Across, how far the perp's mark price sat from USDE's prior close at 4 am New York time
(left) and at 9 am (right). Up, how far USDE's next open sat from that close. A dot on the
dashed diagonal opened where the mark was. A dot on the solid zero line opened at the prior
close. Dots are small and partly transparent so that close pairs stay visible.

Every point and label comes from out/chart_off_hours.csv and out/results.json, which
stablecoinx_perp_review.py writes. Run after the main script:  python3 make_chart_svg.py
"""
import csv
import json
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE / "out" / "chart_off_hours.csv")))
res = json.loads((HERE / "out" / "results.json").read_text())
s = res["off_hours"]["all"]
assert len(rows) == s["count"] == 30
assert sum(int(r["open_nearer_perp_4am"]) for r in rows) == s["near_4am"] == 17
assert sum(int(r["open_nearer_perp_9am"]) for r in rows) == s["near_9am"] == 23

BG, RULE, TEXT, MUTED = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)",
                         "var(--sx-muted, #99a3b0)")
NEAR_PERP = "#3987e5"  # validated pair on #0d1116, also told apart by fill
NEAR_CLOSE = "#d95926"
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
W, H = 800, 466
T, SIDE = 104, 300  # top of the plot areas and their side, equal scales
PANELS = [(64, "4am", "4 am"), (464, "9am", "9 am")]
LO, HI = -15, 30
R, RING, OPACITY = 4, 1.75, 0.85  # 8 px markers, partly transparent so close pairs stay visible
HALO = f'style="paint-order:stroke;stroke:{BG};stroke-width:4px;stroke-linejoin:round"'  # keeps lines off the labels


def nice(d):
    dd = date.fromisoformat(d)
    return dd.strftime("%b ") + str(dd.day)


def X(x0, v):
    return x0 + SIDE * (v - LO) / (HI - LO)


def Y(v):
    return T + SIDE * (1 - (v - LO) / (HI - LO))


o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="oh-t oh-d" font-family="{FONT}">')
a("<title id=\"oh-t\">USDE's next open against the mark of Lighter's StablecoinX perp at 4 am and 9 am New York "
  "time, August 26 to October 8, 2026</title>")
a(f'<desc id="oh-d">Two scatter charts of the {s["count"]} stretches between a close and the next open. With the '
  f'perp\'s mark at 4 am, the open sat nearer the mark than the prior close {s["near_4am"]} times. With the mark at 9 am, '
  f'{s["near_9am"]} times. The largest move came over the weekend of September 19 and 20, when the mark sat 29% above '
  f'Friday\'s close at 4 am on Monday and USDE opened 28% above it.</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
a(f'<text x="20" y="30" fill="{TEXT}" font-size="16" font-weight="600">By 9 am the perp&#8217;s mark was a closer guide to '
  f'USDE&#8217;s next open than at 4 am</text>')
a(f'<text x="20" y="52" fill="{MUTED}" font-size="12">Each dot is one stretch from a close to the next open, August 26 to '
  f'October 8, 2026. Each move runs from USDE&#8217;s prior close.</text>')
lx = 20
a(f'<circle cx="{lx + 5}" cy="72" r="{R}" fill="{NEAR_PERP}" fill-opacity="{OPACITY}"/>')
a(f'<text x="{lx + 16}" y="76" fill="{TEXT}" font-size="12">Open nearer the mark</text>')
a(f'<circle cx="{lx + 160}" cy="72" r="{R}" fill="none" stroke="{NEAR_CLOSE}" stroke-width="{RING}"/>')
a(f'<text x="{lx + 171}" y="76" fill="{TEXT}" font-size="12">Open nearer the prior close</text>')
a(f'<line x1="{lx + 340}" x2="{lx + 360}" y1="72" y2="72" stroke="{MUTED}" stroke-dasharray="4 3"/>')
a(f'<text x="{lx + 366}" y="76" fill="{MUTED}" font-size="12">Open equal to the mark</text>')
a(f'<line x1="{lx + 515}" x2="{lx + 535}" y1="72" y2="72" stroke="{MUTED}"/>')
a(f'<text x="{lx + 541}" y="76" fill="{MUTED}" font-size="12">Open equal to the prior close</text>')
for x0, key, label in PANELS:
    near = s[f"near_{key}"]
    a(f'<text x="{x0}" y="{T - 10}" fill="{TEXT}" font-size="13" font-weight="600">Perp&#8217;s mark at {label} New York '
      f'time</text>')
    for g in range(-10, HI + 1, 10):
        a(f'<line x1="{x0}" x2="{x0 + SIDE}" y1="{Y(g):.1f}" y2="{Y(g):.1f}" stroke="{RULE}" stroke-width="1"/>')
        a(f'<line x1="{X(x0, g):.1f}" x2="{X(x0, g):.1f}" y1="{T}" y2="{T + SIDE}" stroke="{RULE}" stroke-width="1"/>')
        lab = f"{g:+d}%" if g else "0%"
        a(f'<text x="{X(x0, g):.1f}" y="{T + SIDE + 16}" fill="{MUTED}" font-size="11" text-anchor="middle">{lab}</text>')
        a(f'<text x="{x0 - 8}" y="{Y(g) + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">{lab}</text>')
    a(f'<line x1="{X(x0, LO):.1f}" y1="{Y(LO):.1f}" x2="{X(x0, HI):.1f}" y2="{Y(HI):.1f}" stroke="{MUTED}" '
      f'stroke-width="1" stroke-dasharray="4 3"/>')
    a(f'<line x1="{x0}" x2="{x0 + SIDE}" y1="{Y(0):.1f}" y2="{Y(0):.1f}" stroke="{MUTED}" stroke-width="1"/>')
    a(f'<text x="{x0 + SIDE / 2}" y="{T + SIDE + 34}" fill="{MUTED}" font-size="12" text-anchor="middle">Perp&#8217;s mark '
      f'against the prior close</text>')
    for r in rows:
        x, y = float(r[f"perp_{key}_vs_close_pct"]), float(r["open_vs_close_pct"])
        hit = r[f"open_nearer_perp_{key}"] == "1"
        tip = (f"{nice(r['from_session'])} close to {nice(r['to_session'])} open ({r['kind']}). Open {y:+.1f}%, "
               f"mark at {label} {x:+.1f}%")
        dot = (f'<circle cx="{X(x0, x):.1f}" cy="{Y(y):.1f}" r="{R}" fill="{NEAR_PERP}" fill-opacity="{OPACITY}" '
               f'stroke="{BG}" stroke-width="1.5"/>'
               if hit else
               f'<circle cx="{X(x0, x):.1f}" cy="{Y(y):.1f}" r="{R}" fill="none" stroke="{NEAR_CLOSE}" '
               f'stroke-opacity="{OPACITY}" stroke-width="{RING}"/>')
        a(f'<g><title>{tip}</title>{dot}<circle cx="{X(x0, x):.1f}" cy="{Y(y):.1f}" r="10" fill="transparent"/></g>')
    big = next(r for r in rows if r["to_session"] == "2026-09-21")
    bx, by = X(x0, float(big[f"perp_{key}_vs_close_pct"])), Y(float(big["open_vs_close_pct"]))
    a(f'<text x="{bx - 10:.1f}" y="{by + 4:.1f}" fill="{TEXT}" font-size="11" text-anchor="end" {HALO}>Weekend of Sep 19</text>')
    a(f'<text x="{x0 + SIDE - 8}" y="{T + SIDE - 10}" fill="{TEXT}" font-size="12" text-anchor="end" {HALO}>{near} of 30 '
      f'opens nearer the mark</text>')
a(f'<text transform="translate(16 {T + SIDE / 2:.1f}) rotate(-90)" fill="{MUTED}" font-size="12" text-anchor="middle">'
  f'USDE&#8217;s next open against the prior close</text>')
a("</svg>")
(HERE / "out" / "chart_off_hours.svg").write_text("\n".join(o) + "\n")
print("wrote out/chart_off_hours.svg")
