#!/usr/bin/env python3
"""
Draws the article's one chart as a static SVG in the EthenaDash palette.

Run after stablecoinx_waiver_review.py:  python3 make_chart_svg.py
Reads   out/chart_locked_schedule.csv   ENA bought under the two token purchase agreements and still locked, at every
                                        date where the count changes, on the dashboard's schedule dates
Writes  out/chart_locked_schedule.svg

Form    one ENA axis that starts at zero and two stepped lines. The gray line is the old 48-month schedule. The blue
        line is the same until October 5, 2026, when the waiver takes it to zero. The gray band under the old line
        after that date is the ENA the old schedule would still have held.
Colors  the site's blue and the mid gray used in the earlier reviews. The pair was run through a palette validator
        against the site's background for the fully diluted review: colour-vision-deficiency separation 21.2,
        normal-vision separation 21.5, both at 3:1 or better against #0d1116. The band is the same gray at 30% opacity.
        A legend names both lines, and each carries a direct label, so identity never rests on color alone.
The SVG needs no script. Colors use the site's CSS variables with the same hex values as fallbacks.
Every plotted value comes straight from the csv. Each step carries its dates and counts as a hover title.
"""
import csv
import datetime as dt
from decimal import Decimal as D
from pathlib import Path

HERE = Path(__file__).parent
rows = [(dt.date.fromisoformat(r["date"]), D(r["locked_original_schedule"]), D(r["locked_after_waiver"]))
        for r in csv.DictReader(open(HERE / "out" / "chart_locked_schedule.csv"))]
WAIVER = dt.date(2026, 10, 5)
assert rows[0][0] == dt.date(2025, 7, 31) and rows[-1] == (dt.date(2029, 9, 30), 0, 0)
assert all(a[1] >= b[1] for a, b in zip(rows[2:], rows[3:])), "the old schedule must only fall after the second purchase"
w_row = [r for r in rows if r[0] == WAIVER][0]
assert w_row[2] == 0 and w_row[1] == D(1558343021)
assert all(r[2] == r[1] for r in rows if r[0] < WAIVER) and all(r[2] == 0 for r in rows if r[0] >= WAIVER)

BG, RULE, TEXT, MUTED, BLUE = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)",
                               "var(--sx-muted, #99a3b0)", "var(--sx-blue, #8aa9cf)")
GRAY = "#5d6877"
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"

W, H = 800, 466
L, R, T, B = 60, 128, 112, 70
pw, ph = W - L - R, H - T - B
X0, X1 = dt.date(2025, 7, 1), dt.date(2029, 10, 31)
YMAX = D("2.5")


def x(d):
    return L + pw * (d - X0).days / (X1 - X0).days


def y(v):
    return T + ph * (1 - float(D(v) / D(10) ** 9 / YMAX))


def bn(v):
    return f"{D(v) / D(10) ** 9:.2f}B"


def long_date(d):
    return f"{d:%B} {d.day}, {d.year}"


def step_path(points, end):
    """points are (date, value) where the value holds from that date. The path ends at date `end`."""
    out = [f"M{x(points[0][0]):.1f},{y(points[0][1]):.1f}"]
    for (d0, v0), (d1, v1) in zip(points, points[1:]):
        out.append(f"L{x(d1):.1f},{y(v0):.1f} L{x(d1):.1f},{y(v1):.1f}")
    out.append(f"L{x(end):.1f},{y(points[-1][1]):.1f}")
    return " ".join(out)


old_pts = [(d, o) for d, o, a in rows if d != WAIVER]
new_pts = [(d, a) for d, o, a in rows if d <= WAIVER]
END = rows[-1][0]

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="lw-t lw-d" font-family="{FONT}">')
a('<title id="lw-t">ENA bought under StablecoinX\'s two token purchase agreements and still locked, on the old schedule and with the October 5, 2026 waiver</title>')
a('<desc id="lw-d">Stepped line chart from July 2025 to September 2029. On the old 48-month schedule the locked count was '
  f'{bn(rows[1][1])} ENA from September 30, 2025, fell in steps from July 31, 2026, stood at {bn(w_row[1])} on October 5, 2026 and '
  'would have reached zero on September 30, 2029. With the waiver it fell from '
  f'{bn(w_row[1])} to zero on October 5, 2026. Dates follow the dashboard\'s assumption that each purchase completed at the end of its month.</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')

a(f'<text x="20" y="30" fill="{TEXT}" font-size="16" font-weight="600">On October 5 the waiver unlocked {bn(w_row[1])} ENA the old schedule held until 2029</text>')
a(f'<text x="20" y="52" fill="{MUTED}" font-size="12">ENA bought under the two token purchase agreements and still locked, on the dashboard\'s schedule dates</text>')

lx, ly = 20, 78
a(f'<line x1="{lx}" x2="{lx + 18}" y1="{ly - 4}" y2="{ly - 4}" stroke="{BLUE}" stroke-width="2"/>')
a(f'<text x="{lx + 24}" y="{ly}" fill="{TEXT}" font-size="12">With the waiver</text>')
a(f'<line x1="{lx + 150}" x2="{lx + 168}" y1="{ly - 4}" y2="{ly - 4}" stroke="{GRAY}" stroke-width="2"/>')
a(f'<text x="{lx + 174}" y="{ly}" fill="{TEXT}" font-size="12">Old 48-month schedule</text>')
a(f'<rect x="{lx + 336}" y="{ly - 10}" width="12" height="12" rx="2" fill="{GRAY}" fill-opacity="0.3"/>')
a(f'<text x="{lx + 354}" y="{ly}" fill="{TEXT}" font-size="12">Still locked on the old schedule after the waiver</text>')

for g in ("0", "0.5", "1.0", "1.5", "2.0", "2.5"):
    yy = T + ph * (1 - float(D(g) / YMAX))
    a(f'<line x1="{L}" x2="{L + pw}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{L - 8}" y="{yy + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">{"0" if g == "0" else g + "B"}</text>')
for yr in (2026, 2027, 2028, 2029):
    xx = x(dt.date(yr, 1, 1))
    a(f'<line x1="{xx:.1f}" x2="{xx:.1f}" y1="{T + ph}" y2="{T + ph + 5}" stroke="{MUTED}" stroke-width="1"/>')
    a(f'<text x="{xx:.1f}" y="{T + ph + 20}" fill="{MUTED}" font-size="11" text-anchor="middle">{yr}</text>')

# the band the waiver released, under the old line from October 5, 2026
band = [f"M{x(WAIVER):.1f},{y(0):.1f}", f"L{x(WAIVER):.1f},{y(w_row[1]):.1f}"]
after = [(d, v) for d, v in old_pts if d > WAIVER]
prev = w_row[1]
for d, v in after:
    band.append(f"L{x(d):.1f},{y(prev):.1f} L{x(d):.1f},{y(v):.1f}")
    prev = v
band.append(f"L{x(END):.1f},{y(0):.1f} Z")
a(f'<path d="{" ".join(band)}" fill="{GRAY}" fill-opacity="0.3"/>')

a(f'<path d="{step_path(old_pts, END)}" fill="none" stroke="{GRAY}" stroke-width="2" stroke-linejoin="round"/>')
# the blue line over the gray one, with a 2px ring in the background color where they overlap
blue = step_path(new_pts, WAIVER) + f" L{x(END):.1f},{y(0):.1f}"
a(f'<path d="{blue}" fill="none" stroke="{BG}" stroke-width="5" stroke-linejoin="round"/>')
a(f'<path d="{blue}" fill="none" stroke="{BLUE}" stroke-width="2" stroke-linejoin="round"/>')

# markers and labels at the waiver
xw, yt, yb = x(WAIVER), y(w_row[1]), y(0)
a(f'<circle cx="{xw:.1f}" cy="{yt:.1f}" r="4.5" fill="{BLUE}" stroke="{BG}" stroke-width="2"/>')
a(f'<circle cx="{xw:.1f}" cy="{yb:.1f}" r="4.5" fill="{BLUE}" stroke="{BG}" stroke-width="2"/>')
a(f'<text x="{xw + 10:.1f}" y="{yt - 26:.1f}" fill="{TEXT}" font-size="12" font-weight="600">October 5, 2026</text>')
a(f'<text x="{xw + 10:.1f}" y="{yt - 11:.1f}" fill="{TEXT}" font-size="12">{bn(w_row[1])} ENA unlocked at once</text>')
# direct labels at the right edge
a(f'<text x="{x(END) + 10:.1f}" y="{y(0) - 22:.1f}" fill="{TEXT}" font-size="12">Old schedule</text>')
a(f'<text x="{x(END) + 10:.1f}" y="{y(0) - 7:.1f}" fill="{MUTED}" font-size="11">ends Sep 30, 2029</text>')
a(f'<text x="{x(dt.date(2025, 9, 30)) + 6:.1f}" y="{y(rows[1][1]) - 8:.1f}" fill="{TEXT}" font-size="12">{bn(rows[1][1])} after the second purchase</text>')

# hover targets: one per step of the old schedule, as wide as the step
spans = [(d0, d1, v_old) for (d0, v_old), (d1, _) in zip(old_pts, old_pts[1:] + [(X1, 0)])]
for d0, d1, v_old in spans:
    v_new = v_old if d0 < WAIVER else D(0)
    tip = (f"From {long_date(d0)} to {long_date(d1 - dt.timedelta(days=1))}. {int(v_old):,} ENA still locked on the old schedule, "
           f"{int(v_new):,} with the waiver.")
    a(f'<g><title>{tip}</title><rect x="{x(d0):.1f}" y="{T}" width="{max(1.0, x(d1) - x(d0)):.1f}" height="{ph}" fill="transparent"/></g>')

a(f'<text x="20" y="{H - 14}" fill="{MUTED}" font-size="11">'
  'EthenaDash from the token purchase agreements and the dashboard\'s tranche file, on the dashboard\'s month-end dates.</text>')
a('</svg>')

out = HERE / "out" / "chart_locked_schedule.svg"
out.write_text("\n".join(o) + "\n", encoding="utf-8")
print("wrote", out.name, f"({out.stat().st_size} bytes)")
print(" plotted", len(rows), "dates; at the waiver", f"{int(w_row[1]):,}", "ENA; first", bn(rows[0][1]), "; peak", bn(rows[1][1]))
