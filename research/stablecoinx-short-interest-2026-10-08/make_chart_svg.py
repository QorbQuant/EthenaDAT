#!/usr/bin/env python3
"""
Draws out/chart_short_interest.svg in the site's dark style. Two panels share one time axis,
June 26 to October 8, 2026. The top panel is USDE's daily close. The bottom panel is FINRA's
short interest at each settlement date, as bars, and the axis is marked at those dates. Thin
dashed lines mark the settlement dates in both panels.

Every point, label, the title, the subtitle and the description come from
out/chart_short_interest.csv and out/results.json, which stablecoinx_short_interest_review.py
writes. Run after the main script:  python3 make_chart_svg.py
"""
import csv
import json
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE / "out" / "chart_short_interest.csv")))
res = json.loads((HERE / "out" / "results.json").read_text())
si = [(date.fromisoformat(r["date"]), int(r["short_interest_shares"])) for r in rows if r["short_interest_shares"]]
assert len(rows) == res["window"]["sessions"] == 73
assert [c["short_interest"] for c in res["short_interest"]] == [q for _, q in si]

BG, RULE, TEXT, MUTED = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)",
                         "var(--sx-muted, #99a3b0)")
PRICE = "#3987e5"
SHORT = "#d95926"
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
HALO = f'style="paint-order:stroke;stroke:{BG};stroke-width:4px;stroke-linejoin:round"'
W, H = 800, 466
L, R = 64, 780
D0, D1 = date(2026, 6, 26), date(2026, 10, 8)
TOP_Y0, TOP_Y1 = 92, 252     # price panel
BOT_Y0, BOT_Y1 = 300, 420    # short interest panel
P_MAX, S_MAX = 18, 3.3e6


def X(d):
    return L + (R - L) * (d - D0).days / (D1 - D0).days


def YP(v):
    return TOP_Y1 - (TOP_Y1 - TOP_Y0) * v / P_MAX


def YS(v):
    return BOT_Y1 - (BOT_Y1 - BOT_Y0) * v / S_MAX


def nice(d):
    return d.strftime("%b ") + str(d.day)


def full(d):
    return d.strftime("%B ") + str(d.day)


WORDS = {6: "six", 7: "seven"}


def shares(q):
    return f"{q / 1e6:.2f}M" if q >= 1_000_000 else f"{q / 1e3:.0f}K"


closes = [(date.fromisoformat(r["date"]), float(r["usde_close"])) for r in rows]
low_d, low_v = min(closes, key=lambda x: x[1])
peak_d, peak_v = max(closes, key=lambda x: x[1])
last_d, last_q = si[-1]
check_time = res["last_check_utc"][11:16]
title = f"USDE short interest reached {last_q / 1e6:.2f} million shares on {full(last_d)}"
subtitle = (f"Daily close, and short interest at each settlement date FINRA had published when checked at "
            f"{check_time} UTC on October 9.")
desc = (f"Two panels on one time axis. USDE closed at ${closes[0][1]:.2f} on {full(closes[0][0])}, fell to a low close "
        f"of ${low_v:.2f} on {full(low_d)} and rose to ${peak_v:.2f} on {full(peak_d)} before closing at "
        f"${closes[-1][1]:.2f} on {full(closes[-1][0])}. Short interest at the {WORDS[len(si)]} settlement dates was "
        + ", ".join(f"{q:,}" for _, q in si[:-1]) + f" and {last_q:,} shares.")

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="si-t si-d" font-family="{FONT}">')
a('<title id="si-t">USDE daily close and FINRA short interest, June 26 to October 8, 2026</title>')
a(f'<desc id="si-d">{desc}</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
a(f'<text x="20" y="30" fill="{TEXT}" font-size="16" font-weight="600">{title}</text>')
a(f'<text x="20" y="52" fill="{MUTED}" font-size="12">{subtitle}</text>')
# panel titles
a(f'<text x="{L}" y="{TOP_Y0 - 14}" fill="{TEXT}" font-size="13" font-weight="600">USDE daily close, dollars</text>')
a(f'<text x="{L}" y="{BOT_Y0 - 14}" fill="{TEXT}" font-size="13" font-weight="600">Short interest, million shares</text>')
# grids and axes
for v in (0, 5, 10, 15):
    a(f'<line x1="{L}" x2="{R}" y1="{YP(v):.1f}" y2="{YP(v):.1f}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{L - 8}" y="{YP(v) + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">${v}</text>')
for v in (0, 1e6, 2e6, 3e6):
    a(f'<line x1="{L}" x2="{R}" y1="{YS(v):.1f}" y2="{YS(v):.1f}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{L - 8}" y="{YS(v) + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">{v / 1e6:g}</text>')
# settlement dates, dashed in each panel, with the axis marked at each date and at the last session
for d, _ in si:
    for y0, y1 in ((TOP_Y0, TOP_Y1), (BOT_Y0, BOT_Y1)):
        a(f'<line x1="{X(d):.1f}" x2="{X(d):.1f}" y1="{y0}" y2="{y1}" stroke="{MUTED}" stroke-width="1" '
          f'stroke-dasharray="2 4" opacity="0.6"/>')
    a(f'<line x1="{X(d):.1f}" x2="{X(d):.1f}" y1="{BOT_Y1}" y2="{BOT_Y1 + 5}" stroke="{MUTED}" stroke-width="1"/>')
    a(f'<text x="{X(d):.1f}" y="{BOT_Y1 + 20}" fill="{MUTED}" font-size="11" text-anchor="middle">{nice(d)}</text>')
a(f'<line x1="{R}" x2="{R}" y1="{BOT_Y1}" y2="{BOT_Y1 + 5}" stroke="{MUTED}" stroke-width="1"/>')
a(f'<text x="{R}" y="{BOT_Y1 + 20}" fill="{MUTED}" font-size="11" text-anchor="end">{nice(D1)}</text>')
# price line
pts = " ".join(f"{X(d):.1f},{YP(v):.1f}" for d, v in closes)
a(f'<polyline points="{pts}" fill="none" stroke="{PRICE}" stroke-width="2" stroke-linejoin="round"/>')
for d, v in closes:
    a(f'<g><title>{nice(d)} close ${v:.2f}</title><circle cx="{X(d):.1f}" cy="{YP(v):.1f}" r="5" fill="transparent"/></g>')
a(f'<circle cx="{X(peak_d):.1f}" cy="{YP(peak_v):.1f}" r="4" fill="{PRICE}" stroke="{BG}" stroke-width="2"/>')
a(f'<text x="{X(peak_d) - 8:.1f}" y="{YP(peak_v) + 4:.1f}" fill="{TEXT}" font-size="11" text-anchor="end" {HALO}>'
  f'${peak_v:.2f} on {nice(peak_d)}</text>')
# short interest bars
BW = 14
for d, q in si:
    x = X(d)
    y = YS(q)
    a(f'<g><title>{nice(d)} settlement: {q:,} shares of short interest</title>'
      f'<rect x="{x - BW / 2:.1f}" y="{y:.1f}" width="{BW}" height="{BOT_Y1 - y:.1f}" rx="2" fill="{SHORT}"/></g>')
    a(f'<text x="{x:.1f}" y="{y - 6:.1f}" fill="{TEXT}" font-size="11" text-anchor="middle" {HALO}>{shares(q)}</text>')
a("</svg>")
(HERE / "out" / "chart_short_interest.svg").write_text("\n".join(o) + "\n")
print("wrote out/chart_short_interest.svg")
