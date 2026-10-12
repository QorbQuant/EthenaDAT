#!/usr/bin/env python3
"""
Draws out/chart_usdew_vs_usde.svg in the site's dark style. One dot per session from June 29 to October 9,
2026, USDEW's close against USDE's close, in two groups split at USDE's first close at or above $10.00.
Two lines from the warrant terms. The value a holder would receive in a $10.00 call announced on October 9,
from the make-whole table, and the exercise value, USDE's price less the $11.50 exercise price.

Every point, label, the title and the description come from out/usdew_by_session.csv, out/chart_curves.csv
and out/results.json, which usdew_warrant_pricing_review.py writes. Run after the main script:
python3 make_chart_svg.py
"""
import csv
import json
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
rows = [r for r in csv.DictReader(open(HERE / "out" / "usdew_by_session.csv")) if r["usdew_close"]]
curve = list(csv.DictReader(open(HERE / "out" / "chart_curves.csv")))
res = json.loads((HERE / "out" / "results.json").read_text())
first10 = date.fromisoformat(res["first_close_at_or_above_10"])
pts = [(date.fromisoformat(r["date"]), float(r["usde_close"]), float(r["usdew_close"]),
        float(r["call_value"]) if r["call_value"] else None) for r in rows]
assert len(pts) == res["window"]["sessions_with_both"] == 71

BG, RULE, TEXT, MUTED = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)",
                         "var(--sx-muted, #99a3b0)")
C_BEFORE = "#3987e5"
C_AFTER = "#d95926"
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
HALO = f'style="paint-order:stroke;stroke:{BG};stroke-width:4px;stroke-linejoin:round"'
W, H = 800, 466
X0, X1, Y0, Y1 = 64, 760, 104, 412
XMAX, YMAX = 18.0, 7.0


def sx(v):
    return X0 + (X1 - X0) * v / XMAX


def sy(v):
    return Y1 - (Y1 - Y0) * v / YMAX


def nice(d):
    return d.strftime("%b ") + str(d.day)


def full(d):
    return d.strftime("%B ") + str(d.day)


assert all(0 < s <= XMAX and 0 < w <= YMAX for _, s, w, _ in pts), "a point falls outside the axes"
o9 = res["october9"]
pk = res["peak"]
lo = res["usdew_vs_call_value_from_first10"]["low"]
after = [p for p in pts if p[0] >= first10]
before = [p for p in pts if p[0] < first10]
second = after[1][0]
assert all(p[2] < p[3] for p in after[1:]) and after[0][2] > after[0][3]
mid_end = date(2026, 10, 7)
assert all(p[2] < p[3] for p in after if second <= p[0] <= mid_end)
assert all(abs(p[2] / p[3] - 1) < 0.005 for p in after if p[0] > mid_end)
title = f"USDEW closed below its estimated call value from {full(second)} to {full(mid_end)}"
subtitle = (f"USDEW's close against USDE's close at each session, {full(pts[0][0])} to {full(pts[-1][0])}, 2026. "
            "The call line uses October 9's months to expiry.")
desc = (f"{len(pts)} dots, one per session. {len(before)} sessions before {full(first10)}, with USDE between "
        f"${min(p[1] for p in before):.2f} and ${max(p[1] for p in before):.2f} and USDEW between "
        f"${min(p[2] for p in before):.2f} and ${max(p[2] for p in before):.2f}. {len(after)} sessions from "
        f"{full(first10)}, with USDE between ${min(p[1] for p in after):.2f} and ${max(p[1] for p in after):.2f}, all but "
        f"the first below the call line. From {full(second)} to {full(mid_end)} each sat below its own session's call value, by as "
        f"much as {abs(lo['usdew_vs_call_value']) * 100:.1f}% on {full(date.fromisoformat(lo['date']))}, and on October 8 and 9 "
        f"within 0.5% of it. On October 9 USDEW closed at "
        f"${o9['usdew_close']:.2f} against a call value of "
        f"${o9['call_value']:.2f}. The call line rises from ${float(next(c for c in curve if c['call_value_at_october_9'])['call_value_at_october_9']):.2f} "
        f"at $10 to ${float(curve[-1]['call_value_at_october_9']):.2f} at $18, where it meets the exercise value line, "
        "which starts at the $11.50 exercise price.")

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="wp-t wp-d" font-family="{FONT}">')
a('<title id="wp-t">USDEW against USDE at each close, with the estimated $10 call value and the exercise value, June 29 to October 9, 2026</title>')
a(f'<desc id="wp-d">{desc}</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
a(f'<text x="20" y="30" fill="{TEXT}" font-size="16" font-weight="600">{title}</text>')
a(f'<text x="20" y="52" fill="{MUTED}" font-size="12">{subtitle}</text>')
# legend row
LY = 78
a(f'<circle cx="26" cy="{LY - 4}" r="4" fill="{C_BEFORE}"/>')
a(f'<text x="36" y="{LY}" fill="{MUTED}" font-size="11">Sessions before {nice(first10)}</text>')
a(f'<circle cx="190" cy="{LY - 4}" r="4" fill="{C_AFTER}"/>')
a(f'<text x="200" y="{LY}" fill="{MUTED}" font-size="11">Sessions from {nice(first10)}</text>')
a(f'<line x1="346" x2="368" y1="{LY - 4}" y2="{LY - 4}" stroke="{TEXT}" stroke-width="2"/>')
a(f'<text x="374" y="{LY}" fill="{MUTED}" font-size="11">Call value, estimated</text>')
a(f'<line x1="500" x2="522" y1="{LY - 4}" y2="{LY - 4}" stroke="{MUTED}" stroke-width="1.5" stroke-dasharray="5 4"/>')
a(f'<text x="528" y="{LY}" fill="{MUTED}" font-size="11">Exercise value, USDE less $11.50</text>')
# grid and axes
for v in range(0, 8):
    a(f'<line x1="{X0}" x2="{X1}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{X0 - 8}" y="{sy(v) + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">${v}</text>')
for v in range(0, 19, 2):
    a(f'<line x1="{sx(v):.1f}" x2="{sx(v):.1f}" y1="{Y1}" y2="{Y1 + 5}" stroke="{MUTED}" stroke-width="1"/>')
    a(f'<text x="{sx(v):.1f}" y="{Y1 + 19}" fill="{MUTED}" font-size="11" text-anchor="middle">${v}</text>')
a(f'<text x="{X1}" y="{Y1 + 40}" fill="{MUTED}" font-size="11" text-anchor="end">USDE close</text>')
a(f'<text x="20" y="{Y1 + 40}" fill="{MUTED}" font-size="10">Closes, S&amp;P Global Market Intelligence via StockAnalysis. '
  'Make-whole table, StablecoinX warrant agreement.</text>')
a(f'<text x="{X0 - 44}" y="{Y0 - 10}" fill="{MUTED}" font-size="11">USDEW close</text>')
# the two call triggers
for v, lab in ((10, "$10 test price"), (18, "$18 test price")):
    a(f'<line x1="{sx(v):.1f}" x2="{sx(v):.1f}" y1="{Y0}" y2="{Y1}" stroke="{MUTED}" stroke-width="1" stroke-dasharray="2 4"/>')
    a(f'<text x="{sx(v) - 6:.1f}" y="{Y0 + 12}" fill="{MUTED}" font-size="11" text-anchor="end">{lab}</text>')
# exercise value and call value lines
ex = [(float(c["usde_price"]), float(c["exercise_value"])) for c in curve]
a('<polyline points="' + " ".join(f"{sx(s):.1f},{sy(v):.1f}" for s, v in ex if s >= 11.5)
  + f'" fill="none" stroke="{MUTED}" stroke-width="1.5" stroke-dasharray="5 4"/>')
cv = [(float(c["usde_price"]), float(c["call_value_at_october_9"])) for c in curve
      if c["call_value_at_october_9"]]
a('<polyline points="' + " ".join(f"{sx(s):.1f},{sy(v):.1f}" for s, v in cv)
  + f'" fill="none" stroke="{TEXT}" stroke-width="2" stroke-linejoin="round"/>')
# dots, each with its own hover title
for d, s, w, tv in pts:
    color = C_AFTER if d >= first10 else C_BEFORE
    extra = f", call value ${tv:.2f}" if tv is not None else ""
    a(f'<g><title>{nice(d)}, USDE ${s:.2f}, USDEW ${w:.2f}{extra}</title>'
      f'<circle cx="{sx(s):.1f}" cy="{sy(w):.1f}" r="8" fill="transparent"/>'
      f'<circle cx="{sx(s):.1f}" cy="{sy(w):.1f}" r="4" fill="{color}" stroke="{BG}" stroke-width="1.5"/></g>')
# labels
px, py = sx(pk["usde_close"]), sy(pk["usdew_close"])
a(f'<text x="{px - 10:.1f}" y="{py - 10:.1f}" fill="{TEXT}" font-size="11" text-anchor="end" {HALO}>'
  f'{nice(date.fromisoformat(pk["date"]))}, USDE ${pk["usde_close"]:.2f}, USDEW ${pk["usdew_close"]:.2f}</text>')
qx, qy = sx(o9["usde_close"]), sy(o9["usdew_close"])
# the October 9 label sits in the empty upper left, with a leader to its dot
tx, ty = sx(4.5), sy(5.0)
a(f'<line x1="{tx + 182:.1f}" y1="{ty + 10:.1f}" x2="{qx - 5:.1f}" y2="{qy - 5:.1f}" stroke="{MUTED}" stroke-width="1"/>')
a(f'<text x="{tx:.1f}" y="{ty:.1f}" fill="{TEXT}" font-size="11" {HALO}>Oct 9, USDEW ${o9["usdew_close"]:.2f}</text>')
a(f'<text x="{tx:.1f}" y="{ty + 14:.1f}" fill="{TEXT}" font-size="11" {HALO}>against a call value of ${o9["call_value"]:.2f}</text>')


def on_line(s):
    for (a0, v0), (a1, v1) in zip(cv, cv[1:]):
        if a0 <= s <= a1:
            return v0 + (v1 - v0) * (s - a0) / (a1 - a0)


assert all(w < on_line(s) for d, s, w, tv in after[1:]), "a dot from the second session on sits on or above the call line"
lx = 15.0
ly = next(v for s, v in cv if abs(s - lx) < 1e-9)
a(f'<text x="{sx(lx) + 4:.1f}" y="{sy(ly) - 10:.1f}" fill="{TEXT}" font-size="11" text-anchor="end" {HALO}>'
  f'Call value</text>')
a(f'<text x="{sx(14.2) + 10:.1f}" y="{sy(14.2 - 11.5) + 16:.1f}" fill="{MUTED}" font-size="11" {HALO}>Exercise value</text>')
a("</svg>")
(HERE / "out" / "chart_usdew_vs_usde.svg").write_text("\n".join(o) + "\n")
print("wrote out/chart_usdew_vs_usde.svg")
