#!/usr/bin/env python3
"""
Draws the article's one chart as a static SVG in the EthenaDash palette.

Run after ethenapay_adoption_review.py:  python3 make_chart_svg.py
Reads   out/weeks_wallets.csv              (seven-day periods ending 2026-10-04)
Writes  out/chart_weekly_spending_wallets.svg

Form    stacked columns. Each column is the number of distinct wallets with a qualifying spend event in one
        seven-day period. The lower segment is the wallets that also spent in the period before, the upper
        segment the wallets that did not.
Colors  the site's blue for the lower segment and a mid gray for the upper one. The pair was run through a
        palette validator against the site's background: colour-vision-deficiency separation 21.2, normal-vision
        separation 21.5, both fills at 3:1 or better against #0d1116. The two series are also named in a legend.
The SVG needs no script. Colors use the site's CSS variables with the same hex values as fallbacks.
Every plotted value comes straight from the csv. Each column carries its figures as a hover title.
"""
import csv
from pathlib import Path

HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE / "out" / "weeks_wallets.csv")))
rows = [r for r in rows if r["also_spent_in_previous_period"] != ""]      # the first period has no period before it
assert len(rows) == 9 and rows[0]["first_day"] == "2026-08-03" and rows[-1]["last_day"] == "2026-10-04"
tot = [int(r["spending_wallets"]) for r in rows]
kept = [int(r["also_spent_in_previous_period"]) for r in rows]
new = [int(r["not_in_previous_period"]) for r in rows]
assert all(k + n == t for k, n, t in zip(kept, new, tot))

BG, RULE, TEXT, MUTED, BLUE = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)",
                               "var(--sx-muted, #99a3b0)", "var(--sx-blue, #8aa9cf)")
GRAY = "#5d6877"
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"

W, H = 800, 466
L, R, T, B = 56, 28, 112, 84
pw, ph = W - L - R, H - T - B
YMAX = 700
BAR = 24                                    # column width in px
slot = pw / len(rows)


def cx(i):
    return L + slot * (i + 0.5)


def y(v):
    return T + ph * (1 - v / YMAX)


def month_day(iso):
    m = {"08": "Aug", "09": "Sep", "10": "Oct"}[iso[5:7]]
    return f"{m} {int(iso[8:])}"


i_pre = next(i for i, r in enumerate(rows) if r["last_day"] == "2026-08-30")      # last full period before the beta
i_beta = i_pre + 1                                                                 # the period that holds September 1
i_last = len(rows) - 1

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="wk-t wk-d" font-family="{FONT}">')
a('<title id="wk-t">Distinct EthenaPay spending wallets by seven-day period, August 3 to October 4, 2026</title>')
a('<desc id="wk-d">Stacked column chart. Distinct wallets with a qualifying spend event rose from '
  f'{tot[0]} in the seven days to August 9 to {tot[i_pre]} in the last full period before the beta and {tot[i_last]} in the seven days to October 4. '
  f'In the latest period {kept[i_last]} of the wallets had also spent in the period before and {new[i_last]} had not.</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')

# title block
a(f'<text x="20" y="30" fill="{TEXT}" font-size="16" font-weight="600">'
  f'{tot[i_last]} wallets spent in the seven days to October 4, 2026, up from {tot[i_pre]} before the beta</text>')
a(f'<text x="20" y="52" fill="{MUTED}" font-size="12">'
  'Distinct EthenaPay wallets with a spend event, by seven-day period</text>')

# legend, in text tokens with a swatch beside each name
lx, ly = 20, 76
a(f'<rect x="{lx}" y="{ly - 9}" width="10" height="10" rx="2" fill="{BLUE}"/>')
a(f'<text x="{lx + 16}" y="{ly}" fill="{TEXT}" font-size="12">Also spent in the previous seven days</text>')
a(f'<rect x="{lx + 246}" y="{ly - 9}" width="10" height="10" rx="2" fill="{GRAY}"/>')
a(f'<text x="{lx + 262}" y="{ly}" fill="{TEXT}" font-size="12">Did not</text>')

# gridlines and y labels (solid hairlines)
for g in (0, 200, 400, 600):
    a(f'<line x1="{L}" x2="{L + pw}" y1="{y(g):.1f}" y2="{y(g):.1f}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{L - 8}" y="{y(g) + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">{g}</text>')

# columns: square at the baseline, 4px rounded at the top, a 2px gap in the background color between the segments
for i, r in enumerate(rows):
    x0 = cx(i) - BAR / 2
    yb, yk, yt = y(0), y(kept[i]), y(tot[i])
    tip = (f"{month_day(r['first_day'])} to {month_day(r['last_day'])}. {tot[i]} spending wallets. "
           f"{kept[i]} also spent in the previous seven days and {new[i]} did not.")
    a(f'<g><title>{tip}</title>')
    a(f'<rect x="{x0:.1f}" y="{yk + 1:.1f}" width="{BAR}" height="{yb - yk - 1:.1f}" fill="{BLUE}"/>')
    rr = 4
    a(f'<path d="M{x0:.1f},{yk - 1:.1f} L{x0:.1f},{yt + rr:.1f} Q{x0:.1f},{yt:.1f} {x0 + rr:.1f},{yt:.1f} L{x0 + BAR - rr:.1f},{yt:.1f} '
      f'Q{x0 + BAR:.1f},{yt:.1f} {x0 + BAR:.1f},{yt + rr:.1f} L{x0 + BAR:.1f},{yk - 1:.1f} Z" fill="{GRAY}"/>')
    a(f'<rect x="{L + slot * i:.1f}" y="{T}" width="{slot:.1f}" height="{ph}" fill="transparent"/>')        # hover target as wide as the slot
    a('</g>')
    a(f'<text x="{cx(i):.1f}" y="{T + ph + 20}" fill="{MUTED}" font-size="11" text-anchor="middle">{month_day(r["last_day"])}</text>')

# direct labels on three columns only
for i in (i_pre, i_beta, i_last):
    a(f'<text x="{cx(i):.1f}" y="{y(tot[i]) - 8:.1f}" fill="{TEXT}" font-size="12" font-weight="600" text-anchor="middle">{tot[i]}</text>')
a(f'<text x="{cx(i_beta):.1f}" y="{y(tot[i_beta]) - 26:.1f}" fill="{MUTED}" font-size="11" text-anchor="middle">beta opened Sep 1</text>')

# axis note and source line
a(f'<text x="{L}" y="{T + ph + 40}" fill="{MUTED}" font-size="11">Each column covers seven full UTC days and is labeled with its last day.</text>')
a(f'<text x="20" y="{H - 14}" fill="{MUTED}" font-size="11">'
  'Chain recount of USDe spend events to the two settlement addresses. Data through October 4, 2026. Wallets are not verified people.</text>')
a('</svg>')

out = HERE / "out" / "chart_weekly_spending_wallets.svg"
out.write_text("\n".join(o) + "\n", encoding="utf-8")
print("wrote", out.name, f"({out.stat().st_size} bytes)")
print(" plotted:", ", ".join(f"{month_day(r['last_day'])} {k}+{n}={t}" for r, k, n, t in zip(rows, kept, new, tot)))
