#!/usr/bin/env python3
"""
Draws the article's one chart as a static SVG in the EthenaDash palette.

Run after usde_sept2026_review.py:  python3 make_chart_svg.py
Reads   out/daily_mnav_two_timestamps.csv   (22 sessions, Aug 31 to Sep 30, 2026)
Writes  out/chart_mnav_two_timestamps.svg

The SVG needs no script. Colors use the site's CSS variables with the same hex values as
fallbacks, so it matches the dark theme when inlined in a page and still renders when opened alone.
Every plotted value comes straight from the csv. Nothing is smoothed or interpolated.
"""
import csv
from pathlib import Path

HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE / "out" / "daily_mnav_two_timestamps.csv")))
dates = [r["date"] for r in rows]
dash = [float(r["mnav_dashboard"]) for r in rows]
close = [float(r["mnav_close"]) for r in rows]
assert len(rows) == 22 and dates[0] == "2026-08-31" and dates[-1] == "2026-09-30"

# palette (site tokens with literal fallbacks)
BG, RULE, TEXT, MUTED, BLUE = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)",
                               "var(--sx-muted, #99a3b0)", "var(--sx-blue, #8aa9cf)")
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"

W, H = 800, 466
L, R, T, B = 52, 172, 84, 78            # plot margins (the right margin holds the end labels)
Y0, Y1 = 0.30, 0.65
pw, ph = W - L - R, H - T - B


def x(i):
    return L + pw * i / (len(rows) - 1)


def y(v):
    return T + ph * (Y1 - v) / (Y1 - Y0)


def path(vals):
    return " ".join(f"{'M' if i == 0 else 'L'}{x(i):.1f},{y(v):.1f}" for i, v in enumerate(vals))


def label(d):
    m = {"08": "Aug", "09": "Sep"}[d[5:7]]
    return f"{m} {int(d[8:])}"


def mult(v):
    return f"{v:.2f}×"


i_low = close.index(min(close))          # Sep 16, the low at the close
i_peak = dash.index(max(dash))           # Sep 25, the dashboard-series high
assert dates[i_low] == "2026-09-16" and dates[i_peak] == "2026-09-25"

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="mnav-t mnav-d" '
  f'font-family="{FONT}">')
a('<title id="mnav-t">USDE mNAV by session on two ENA timestamps, August 31 to September 30, 2026</title>')
a('<desc id="mnav-d">Line chart. With ENA priced at the 4 pm New York stock close, mNAV starts at '
  f'{close[0]:.2f}, falls to {close[i_low]:.2f} on September 16 and ends September at {close[-1]:.2f}. '
  f'On the dashboard series, which prices ENA 20 hours earlier, it peaks at {dash[i_peak]:.2f} on September 25 '
  f'and ends at {dash[-1]:.2f}.</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')

# title block
a(f'<text x="{L - 36}" y="30" fill="{TEXT}" font-size="16" font-weight="600">'
  f'Priced at the close, mNAV fell to {mult(close[i_low])} and ended September at {mult(close[-1])}</text>')
a(f'<text x="{L - 36}" y="52" fill="{MUTED}" font-size="12">'
  'USDE share price ÷ token NAV per share, by session, Aug 31 to Sep 30, 2026</text>')

# gridlines and y labels
for g in (0.30, 0.40, 0.50, 0.60):
    a(f'<line x1="{L}" x2="{L + pw}" y1="{y(g):.1f}" y2="{y(g):.1f}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{L - 8}" y="{y(g) + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">{mult(g)}</text>')

# x labels at the annotated sessions
for i in (0, 5, i_low, i_peak, len(rows) - 1):
    a(f'<line x1="{x(i):.1f}" x2="{x(i):.1f}" y1="{T + ph}" y2="{T + ph + 5}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{x(i):.1f}" y="{T + ph + 20}" fill="{MUTED}" font-size="11" text-anchor="middle">{label(dates[i])}</text>')

# the two series
a(f'<path d="{path(dash)}" fill="none" stroke="{MUTED}" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>')
a(f'<path d="{path(close)}" fill="none" stroke="{BLUE}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>')


def dot(i, v, color, r=3.5):
    a(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="{r}" fill="{color}" stroke="{BG}" stroke-width="1.5"/>')


def note(i, v, text, color, dx=0, dy=-10, anchor="middle", weight="400"):
    a(f'<text x="{x(i) + dx:.1f}" y="{y(v) + dy:.1f}" fill="{color}" font-size="12" font-weight="{weight}" '
      f'text-anchor="{anchor}">{text}</text>')


# annotated points
dot(0, close[0], BLUE)
note(0, max(close[0], dash[0]), mult(close[0]), TEXT, dx=2, dy=-12, anchor="start")
dot(i_low, close[i_low], BLUE)
note(i_low, close[i_low], f"{mult(close[i_low])} on Sep 16", TEXT, dy=22, weight="600")
dot(i_peak, dash[i_peak], MUTED)
dot(i_peak, close[i_peak], BLUE)
# both Sep 25 readings sit to the right of the peak, clear of the lines
note(i_peak, dash[i_peak], f"{mult(dash[i_peak])} on the dashboard series", MUTED, dx=11, dy=4, anchor="start")
note(i_peak, dash[i_peak], f"{mult(close[i_peak])} at the close", BLUE, dx=11, dy=21, anchor="start", weight="600")
dot(len(rows) - 1, dash[-1], MUTED)
dot(len(rows) - 1, close[-1], BLUE)

# end labels in the right margin
xe = x(len(rows) - 1) + 12
a(f'<text x="{xe:.1f}" y="{y(dash[-1]) - 2:.1f}" fill="{MUTED}" font-size="12">Dashboard series {mult(dash[-1])}</text>')
a(f'<text x="{xe:.1f}" y="{y(close[-1]) + 12:.1f}" fill="{BLUE}" font-size="12" font-weight="600">At the close {mult(close[-1])}</text>')

# source line
a(f'<text x="{L - 36}" y="{H - 30}" fill="{MUTED}" font-size="11">'
  'EthenaDash dataset at commit 759f283 and CoinGecko ENA at 20:00 UTC, the 4 pm New York close.</text>')
a(f'<text x="{L - 36}" y="{H - 14}" fill="{MUTED}" font-size="11">'
  'The dashboard series prices ENA 20 hours earlier, at 8 pm New York the evening before.</text>')
a('</svg>')

out = HERE / "out" / "chart_mnav_two_timestamps.svg"
out.write_text("\n".join(o) + "\n", encoding="utf-8")
print("wrote", out.name, f"({out.stat().st_size} bytes)")
print(" plotted:", ", ".join(f"{label(d)} {b:.4f}/{c:.4f}" for d, b, c in zip(dates, dash, close)))
