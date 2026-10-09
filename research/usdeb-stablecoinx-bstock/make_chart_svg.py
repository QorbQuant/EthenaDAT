#!/usr/bin/env python3
"""
Draws the article's one chart as a static SVG in the EthenaDash palette.

Run after usdeb_review.py:  python3 make_chart_svg.py
Reads   out/chart_usdeb_supply.csv   USDEB outstanding after every mint and burn, and at the cutoff
Writes  out/chart_usdeb_supply.svg

Form    one supply axis that starts at zero and one stepped line, from 06:00 UTC on October 7, 2026 to the cutoff.
        A dashed rule marks the 12:00 UTC listing. Labels sit on the points the article discusses, the supply before
        trading opened, the peak, the burn and the supply at the cutoff.
Colors  the site's blue for the one series and its muted gray for rules and notes, the pair already used on the site.
The SVG needs no script. Colors use the site's CSS variables with the same hex values as fallbacks.
Every plotted value comes straight from the csv. Each step carries its time, the event and the supply as a hover title.
"""
import csv
import datetime as dt
from decimal import Decimal as D
from pathlib import Path

HERE = Path(__file__).parent
UTC = dt.timezone.utc
rows = [(dt.datetime.fromisoformat(r["utc_time"].replace("Z", "+00:00")), D(r["supply_after"]), r["kind"], D(r["usdeb"]))
        for r in csv.DictReader(open(HERE / "out" / "chart_usdeb_supply.csv"))]
events, cutoff = rows[:-1], rows[-1]
assert cutoff[2] == "cutoff" and cutoff[1] == events[-1][1]
OPEN = dt.datetime(2026, 10, 7, 12, 0, tzinfo=UTC)
pre = [r for r in events if r[0] < OPEN]
peak = max(events, key=lambda r: r[1])
burn = [r for r in events if r[2] == "burn"]
assert len(burn) == 1 and burn[0][0] > peak[0]
burn = burn[0]
import json
_res = json.loads((HERE / "out" / "results.json").read_text())
assert f"{D(_res['share_of_class_a_pct']):.2f}%" == "0.17%"

SHARE = "0.17%"  # 41,856.57 / 24,139,375, from out/results.json; checked below
BG, RULE, TEXT, MUTED, BLUE = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)",
                               "var(--sx-muted, #99a3b0)", "var(--sx-blue, #8aa9cf)")
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
W, H = 800, 466
L, R, T, B = 64, 150, 104, 64
pw, ph = W - L - R, H - T - B
X0, X1 = dt.datetime(2026, 10, 7, 6, 0, tzinfo=UTC), dt.datetime(2026, 10, 9, 0, 0, tzinfo=UTC)
YMAX = D(60000)


def x(t):
    return L + pw * (t - X0).total_seconds() / (X1 - X0).total_seconds()


def y(v):
    return T + ph * (1 - float(D(v) / YMAX))


def n0(v):
    return f"{D(v):,.0f}"


def n2(v):
    return f"{D(v):,.2f}"


def when(t):
    return f"October {t.day}, {t:%H:%M:%S} UTC"


def hm(t):
    return f"{t + dt.timedelta(seconds=30):%H:%M}"


path = [f"M{x(X0):.1f},{y(0):.1f}"]
level = D(0)
for t, after, kind, amt in events:
    path.append(f"L{x(t):.1f},{y(level):.1f} L{x(t):.1f},{y(after):.1f}")
    level = after
path.append(f"L{x(cutoff[0]):.1f},{y(level):.1f}")

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="ub-t ub-d" font-family="{FONT}">')
a(f'<title id="ub-t">USDEB outstanding on BNB Smart Chain after every mint and burn, October 7 to 8, 2026</title>')
a(f'<desc id="ub-d">Stepped line from 06:00 UTC on October 7, 2026. Supply was zero until the first mint at 08:15 UTC and reached '
  f'{n0(pre[-1][1])} USDEB before trading opened at 12:00 UTC. It peaked at {n0(peak[1])} at {hm(peak[0])} UTC and fell to '
  f'{n0(burn[1])} after a burn of {n0(burn[3])} at {hm(burn[0])} UTC, both on October 7, and stood at {n0(cutoff[1])} at '
  f'{hm(cutoff[0])} UTC on October 8.</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
a(f'<text x="20" y="30" fill="{TEXT}" font-size="16" font-weight="600">USDEB supply peaked at {n0(peak[1])} on October 7 and stood at {n0(cutoff[1])} a day later</text>')
a(f'<text x="20" y="52" fill="{MUTED}" font-size="12">USDEB outstanding after every mint and burn on BNB Smart Chain, October 7 and 8, 2026, times in UTC</text>')

for g in range(0, 60001, 10000):
    yy = y(g)
    a(f'<line x1="{L}" x2="{L + pw}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{L - 8}" y="{yy + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">{"0" if g == 0 else f"{g:,}"}</text>')
ticks = [X0 + dt.timedelta(hours=6 * k) for k in range(8)]
for t in ticks:
    xx = x(t)
    lab = (f"Oct {t.day} {t:%H:%M}" if t.hour == 0 or t == X0 else f"{t:%H:%M}")
    a(f'<line x1="{xx:.1f}" x2="{xx:.1f}" y1="{T + ph}" y2="{T + ph + 5}" stroke="{MUTED}" stroke-width="1"/>')
    a(f'<text x="{xx:.1f}" y="{T + ph + 20}" fill="{MUTED}" font-size="11" text-anchor="middle">{lab}</text>')

# the listing
xo = x(OPEN)
a(f'<line x1="{xo:.1f}" x2="{xo:.1f}" y1="{T - 6}" y2="{T + ph}" stroke="{MUTED}" stroke-width="1" stroke-dasharray="3 4"/>')
a(f'<text x="{xo + 6:.1f}" y="{T + ph - 8:.1f}" fill="{MUTED}" font-size="11">Trading opens 12:00 UTC</text>')

a(f'<path d="{" ".join(path)}" fill="none" stroke="{BLUE}" stroke-width="2" stroke-linejoin="round"/>')

# labelled points
lvl_open = pre[-1][1]
a(f'<circle cx="{xo:.1f}" cy="{y(lvl_open):.1f}" r="4" fill="{BLUE}" stroke="{BG}" stroke-width="2"/>')
a(f'<text x="{xo + 8:.1f}" y="{y(lvl_open) + 20:.1f}" fill="{TEXT}" font-size="12">{n0(lvl_open)}</text>')
a(f'<text x="{xo + 8:.1f}" y="{y(lvl_open) + 35:.1f}" fill="{MUTED}" font-size="11">minted before trading</text>')
xp, yp = x(peak[0]), y(peak[1])
a(f'<circle cx="{xp:.1f}" cy="{yp:.1f}" r="4" fill="{BLUE}" stroke="{BG}" stroke-width="2"/>')
a(f'<text x="{xp - 8:.1f}" y="{yp - 22:.1f}" fill="{TEXT}" font-size="12" text-anchor="end">Peak {n0(peak[1])}</text>')
a(f'<text x="{xp - 8:.1f}" y="{yp - 8:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">{hm(peak[0])} UTC, October 7</text>')
xb, yb = x(burn[0]), y(burn[1])
a(f'<circle cx="{xb:.1f}" cy="{yb:.1f}" r="4" fill="{BLUE}" stroke="{BG}" stroke-width="2"/>')
a(f'<text x="{xb + 10:.1f}" y="{yb + 20:.1f}" fill="{TEXT}" font-size="12">Burn of {n0(burn[3])}</text>')
a(f'<text x="{xb + 10:.1f}" y="{yb + 35:.1f}" fill="{MUTED}" font-size="11">{hm(burn[0])} UTC, October 7</text>')
xc, yc = x(cutoff[0]), y(cutoff[1])
a(f'<circle cx="{xc:.1f}" cy="{yc:.1f}" r="4.5" fill="{BLUE}" stroke="{BG}" stroke-width="2"/>')
a(f'<text x="{L + pw + 12:.1f}" y="{yc - 4:.1f}" fill="{TEXT}" font-size="12" font-weight="600">{n0(cutoff[1])} USDEB</text>')
a(f'<text x="{L + pw + 12:.1f}" y="{yc + 12:.1f}" fill="{MUTED}" font-size="11">{hm(cutoff[0])} UTC, October 8</text>')
a(f'<text x="{L + pw + 12:.1f}" y="{yc + 27:.1f}" fill="{MUTED}" font-size="11">{SHARE} of Class A shares</text>')

# hover targets, one per step
spans = [(X0, events[0][0], D(0), "Before the first mint")]
for (t0, s0, k0, a0), (t1, *_r) in zip(events, events[1:] + [cutoff]):
    spans.append((t0, t1, s0, f"{when(t0)}. {k0.capitalize()} of {n2(a0)} USDEB"))
for t0, t1, s0, what in spans:
    tip = f"{what}. {n2(s0)} USDEB outstanding."
    a(f'<g><title>{tip}</title><rect x="{x(t0):.1f}" y="{T}" width="{max(1.0, x(t1) - x(t0)):.1f}" height="{ph}" fill="transparent"/></g>')

a(f'<text x="20" y="{H - 14}" fill="{MUTED}" font-size="11">EthenaDash from USDEB Transfer logs on BNB Smart Chain, reconciled to totalSupply at block 126,523,880.</text>')
a('</svg>')

out = HERE / "out" / "chart_usdeb_supply.svg"
out.write_text("\n".join(o) + "\n", encoding="utf-8")
print("wrote", out.name, f"({out.stat().st_size} bytes)")
print(" plotted", len(events), "events; before trading", n0(lvl_open), "; peak", n0(peak[1]), "; burn", n0(burn[3]), "; cutoff", n0(cutoff[1]))
