#!/usr/bin/env python3
"""
Draws out/chart_usde_by_chain.svg in the site's dark style. Horizontal bars of the USDe on the ten chains that held the
most at about 18:41 UTC on October 12, 2026, largest first, and a last bar for the other 25 chains read.

Colors  one series, so no legend. The ten chains take the first categorical slot of the reference palette, dark step, and
        the bar of the other chains a neutral grey step, so it reads as a remainder. Every bar carries its chain's name and
        its value in text, so identity never rests on colour alone. Text uses the text colours.
Values  USDe in millions to one decimal and the share of the USDe locked on Ethereum to one decimal. Hover text gives the
        exact amount and the share to two decimals.
Every value, label, the title and the description come from out/chart_data.csv and out/results.json, which
usde_chains_review.py writes. Run after the main script, as python3 make_chart_svg.py, with Python 3.8 or later.
"""
import csv
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE / "out" / "chart_data.csv")))
res = json.load(open(HERE / "out" / "results.json"))
assert len(rows) == 11 and rows[-1]["chain"] == "25 other chains"

BG, RULE, TEXT, MUTED = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)", "var(--sx-muted, #99a3b0)")
C_MAIN, C_OTHER = "#3987e5", "#5b6573"
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
W, H = 800, 466
X0, X1 = 170, 640
Y0, BAR, GAP = 80, 21, 8
XMAX = Decimal(600)
BOLD = ' font-weight="600"'


def q(v, places=1):
    return Decimal(v).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def millions(usde):
    return q(Decimal(usde) / Decimal(10 ** 6))


def sx(m):
    return X0 + (X1 - X0) * float(Decimal(m) / XMAX)


top5 = Decimal(res["top5_share_pct"])
title = f"Five chains held USDe equal to {q(top5, 0)}% of the USDe locked on Ethereum"
subtitle = "USDe on each chain at about 18:41 UTC on October 12, 2026, in millions, and its share of the USDe locked on Ethereum"
desc = ("Horizontal bar chart of the USDe on each chain read, connected to Ethena's LayerZero adapter on Ethereum or dropped from it, "
        "at about 18:41 UTC on October 12, 2026, Swellchain's at 06:39 UTC, largest first, in millions of USDe and as a share of the USDe "
        "the adapter held. "
        + " ".join(f"{r['chain']}, {millions(r['usde'])} million, {q(r['share_of_adapter_pct'])}%." for r in rows))

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="uc-t uc-d" font-family="{FONT}">')
a('<title id="uc-t">USDe by chain at about 18:41 UTC on October 12, 2026</title>')
a(f'<desc id="uc-d">{desc}</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
a(f'<text x="20" y="30" fill="{TEXT}" font-size="16"{BOLD}>{title}</text>')
a(f'<text x="20" y="50" fill="{MUTED}" font-size="12">{subtitle}</text>')
YB = Y0 + len(rows) * (BAR + GAP) - GAP
for m in (0, 100, 200, 300, 400, 500, 600):
    x = sx(m)
    a(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{Y0 - 8}" y2="{YB + 6}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{x:.1f}" y="{YB + 20}" fill="{MUTED}" font-size="11" text-anchor="middle">{m}</text>')
for i, r in enumerate(rows):
    y = Y0 + i * (BAR + GAP)
    other = r["chain"] == "25 other chains"
    color = C_OTHER if other else C_MAIN
    m = millions(r["usde"])
    x_end = sx(Decimal(r["usde"]) / Decimal(10 ** 6))
    tip = f"{r['chain']}. {Decimal(r['usde']):,} USDe, {q(r['share_of_adapter_pct'], 2)}% of the USDe locked on Ethereum"
    a(f'<g><title>{tip}</title>')
    a(f'<text x="{X0 - 10}" y="{y + BAR / 2 + 4:.1f}" fill="{TEXT}" font-size="12" text-anchor="end">{r["chain"]}</text>')
    if x_end - X0 >= 4:
        a(f'<path d="M{X0},{y} H{x_end - 4:.1f} a4,4 0 0 1 4,4 V{y + BAR - 4} a4,4 0 0 1 -4,4 H{X0} Z" fill="{color}"/>')
    else:
        a(f'<rect x="{X0}" y="{y}" width="{max(x_end - X0, 2):.1f}" height="{BAR}" fill="{color}"/>')
    a(f'<text x="{max(x_end, X0 + 2) + 8:.1f}" y="{y + BAR / 2 + 4:.1f}" fill="{TEXT}" font-size="12"{BOLD}>{m}'
      f'<tspan fill="{MUTED}" font-weight="400">  ·  {q(r["share_of_adapter_pct"])}%</tspan></text>')
    a('</g>')
a(f'<text x="20" y="{H - 40}" fill="{MUTED}" font-size="10">Supplies read from each chain at about 18:41 UTC on October 12, 2026, Swellchain\'s from a block of 06:39 UTC. Stellar\'s came from the Stellar Expert explorer.</text>')
a(f'<text x="20" y="{H - 26}" fill="{MUTED}" font-size="10">Ethereal\'s figure is the USDe that the adapter\'s peer on Ethereal received less the USDe it sent. The 25 other chains include 10 dropped chains.</text>')
a(f'<text x="20" y="{H - 12}" fill="{MUTED}" font-size="10">The adapter held {Decimal(res["adapter_balance"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP):,} USDe at Ethereum block {res["ethereum_block"]:,}. Plume\'s 2024 network could not be read. Sources read October 12, 2026 UTC.</text>')
a('</svg>')
(HERE / "out" / "chart_usde_by_chain.svg").write_text("\n".join(o) + "\n")
print("wrote out/chart_usde_by_chain.svg |", title)
