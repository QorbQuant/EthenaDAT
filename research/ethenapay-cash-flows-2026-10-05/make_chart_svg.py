#!/usr/bin/env python3
"""
Draws out/chart_cash_flows.svg, a waterfall of USDe into and out of EthenaPay wallets from May 15 to October 5, 2026,
in the site's palette. Every bar and label comes from out/chart_bridge.csv, which ethenapay_cash_flows.py writes.

Run after the main script:  python3 make_chart_svg.py
"""
import csv
import json
from decimal import Decimal as D
from pathlib import Path

HERE = Path(__file__).parent
bars = [(r["bar"], D(r["usde"]), r["kind"]) for r in csv.DictReader(open(HERE / "out" / "chart_bridge.csv"))]
res = json.loads((HERE / "out" / "results.json").read_text())
assert [b[0] for b in bars] == ["Deposits", "Withdrawals", "Card spend", "Reversals", "USDe rewards", "Held on October 5"]
start, end = bars[0][1], bars[-1][1]
assert abs(start + sum(b[1] for b in bars[1:-1]) - end) < D("0.02"), "the steps add up to the closing balance"
pct = lambda v: f"{abs(v) / start * 100:.0f}%"
assert pct(bars[1][1]) == "43%" and pct(bars[2][1]) == "22%" and pct(end) == "36%"
assert f"{D(res['held_pct_of_deposits']):.2f}" == "36.00"

BG, RULE, TEXT, MUTED = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)", "var(--sx-muted, #99a3b0)")
IN_C, OUT_C, TOTAL_C = "var(--sx-blue, #8aa9cf)", "#d9925f", "var(--sx-muted, #99a3b0)"   # copper checked for colour-blind separation from the blue
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
W, H = 800, 466
L, R, T, B = 64, 24, 104, 72
pw, ph = W - L - R, H - T - B
YMAX = D(12_000_000)
slot = pw / len(bars)
bw = slot * 0.56


def y(v):
    return T + ph * (1 - float(D(v) / YMAX))


def n0(v):
    return f"{abs(v):,.0f}"


o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="cf-t cf-d" font-family="{FONT}">')
a('<title id="cf-t">USDe into and out of EthenaPay wallets, May 15 to October 5, 2026</title>')
desc = (f"Waterfall. Deposits of {n0(start)} USDe, less withdrawals of {n0(bars[1][1])} and card spend of {n0(bars[2][1])}, plus reversals of "
        f"{n0(bars[3][1])} and USDe rewards of {n0(bars[4][1])}, left {n0(end)} USDe held at the end of October 5, 2026.")
a(f'<desc id="cf-d">{desc}</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
a(f'<text x="20" y="30" fill="{TEXT}" font-size="16" font-weight="600">EthenaPay wallets withdrew {pct(bars[1][1])} of the USDe deposited '
  f'and spent {pct(bars[2][1])} on the card</text>')
a(f'<text x="20" y="52" fill="{MUTED}" font-size="12">USDe into and out of EthenaPay wallets on Avalanche, May 15 to October 5, 2026</text>')
for g in range(0, 13, 2):
    gy = y(D(g) * 1_000_000)
    a(f'<line x1="{L}" x2="{L + pw}" y1="{gy:.1f}" y2="{gy:.1f}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{L - 8}" y="{gy + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">{"0" if g == 0 else f"{g}M"}</text>')
level = D(0)
prev_top = None
for i, (label, v, kind) in enumerate(bars):
    x0 = L + slot * i + (slot - bw) / 2
    if kind == "total":
        lo, hi = D(0), v
        level = v
        color = TOTAL_C
        text = n0(v)
    else:
        lo, hi = (level, level + v) if v > 0 else (level + v, level)
        level += v
        color = IN_C if v > 0 else OUT_C
        text = ("+" if v > 0 else "−") + n0(v)
    ytop, ybot = y(hi), y(lo)
    hgt = max(2.0, ybot - ytop)
    if hgt == 2.0 and kind != "total":
        ytop = ybot - 2.0
    a(f'<g><title>{label}, {text} USDe</title><rect x="{x0:.1f}" y="{ytop:.1f}" width="{bw:.1f}" height="{hgt:.1f}" fill="{color}" rx="2"/></g>')
    if prev_top is not None and kind != "total":
        a(f'<line x1="{x0 - (slot - bw):.1f}" x2="{x0:.1f}" y1="{y(prev_top):.1f}" y2="{y(prev_top):.1f}" stroke="{MUTED}" stroke-dasharray="2 3" stroke-width="1"/>')
    prev_top = level
    a(f'<text x="{x0 + bw / 2:.1f}" y="{ytop - 8:.1f}" fill="{TEXT}" font-size="12" text-anchor="middle">{text}</text>')
    a(f'<text x="{x0 + bw / 2:.1f}" y="{T + ph + 18:.1f}" fill="{MUTED}" font-size="11" text-anchor="middle">{label.replace(" on October 5", "")}</text>')
    if label.startswith("Held"):
        a(f'<text x="{x0 + bw / 2:.1f}" y="{T + ph + 32:.1f}" fill="{MUTED}" font-size="11" text-anchor="middle">on October 5</text>')
a(f'<text x="20" y="{H - 14}" fill="{MUTED}" font-size="11">EthenaDash count of every USDe transfer touching an EthenaPay wallet, checked day by day against the dashboard’s Dune series.</text>')
a('</svg>')
svg = "\n".join(o) + "\n"
(HERE / "out" / "chart_cash_flows.svg").write_text(svg)
print(f"wrote chart_cash_flows.svg ({len(svg.encode())} bytes)")
print(" bars", ", ".join(f"{b[0]} {b[1]:,.2f}" for b in bars))
