#!/usr/bin/env python3
"""
Draws out/chart_mnav_peers.svg in the site's dark style. Horizontal bars of token-only mNAV, the share price divided by
token NAV per share, for the five crypto treasury companies at the October 9, 2026 close, lowest first, with a dashed
line at 1, where the share price equals token NAV per share.

Colors  one series, so no legend. StablecoinX's bar takes the first categorical slot of the reference palette, dark step,
        and the other four a neutral grey step, so the bar the review is about stands out. The palette validator passes
        both on contrast against #0d1116, 3:1 or better, and on separation for colour-vision deficiency, and flags the grey
        for low chroma, which is intended for a context colour. Every bar carries its company's name and its value in
        text, so identity never rests on colour alone. Text uses the text colours, and white inside a bar.
Values  mNAV to two decimals with the multiplication sign, as in the article. Hover text gives the inputs and dates.
Every value, label, the title and the description come from out/companies.csv, which dat_mnav_review.py writes. Run
after the main script, as python3 make_chart_svg.py, with Python 3.8 or later.
"""
import csv
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE / "out" / "companies.csv")))
assert [r["ticker"] for r in rows] == ["HYPD", "USDE", "FWDI", "MSTR", "ASST"]

BG, RULE, TEXT, MUTED = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)", "var(--sx-muted, #99a3b0)")
C_MAIN, C_OTHER = "#3987e5", "#5b6573"
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
W, H = 800, 466
X0, X1 = 250, 700
Y0, BAR, GAP = 112, 32, 18
XMAX = Decimal("1.25")
BOLD = ' font-weight="600"'


def q(v, places=2):
    return Decimal(v).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def sx(v):
    return X0 + (X1 - X0) * float(Decimal(v) / XMAX)


def money(v, places=2):
    return f"${q(v, places):,}"


def day(iso):
    d = date.fromisoformat(iso)
    return f"{d:%B} {d.day}, {d.year}"


label = {"HYPD": "Hyperion DeFi (HYPD)", "USDE": "StablecoinX (USDE)", "FWDI": "Forward Industries (FWDI)", "MSTR": "Strategy (MSTR)",
         "ASST": "Strive (ASST)"}
by = {r["ticker"]: r for r in rows}
title = "StablecoinX was second lowest of five crypto treasury companies on token-only mNAV"
subtitle = "Share price divided by token NAV per share at 4 pm New York time on October 9, 2026"
desc = ("Horizontal bar chart of five crypto treasury companies, which hold one crypto token as their main treasury asset. Token-only mNAV, the share "
        "price divided by the value of the reported tokens per common share, at the October 9, 2026 close. "
        + " ".join(f"{label[r['ticker']]}, which holds {r['token']}, {q(r['mnav'])}." for r in rows)
        + " A dashed line marks 1, where the share price equals token NAV per share.")

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="mp-t mp-d" font-family="{FONT}">')
a('<title id="mp-t">Token-only mNAV of five crypto treasury companies at the October 9, 2026 close</title>')
a(f'<desc id="mp-d">{desc}</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
a(f'<text x="20" y="30" fill="{TEXT}" font-size="16"{BOLD}>{title}</text>')
a(f'<text x="20" y="52" fill="{MUTED}" font-size="12">{subtitle}</text>')
YB = Y0 + len(rows) * (BAR + GAP) - GAP
for v in ("0", "0.25", "0.5", "0.75", "1", "1.25"):
    x = sx(v)
    dash = ' stroke-dasharray="4 3"' if v == "1" else ""
    color, width = (TEXT, 1.5) if v == "1" else (RULE, 1)
    a(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{Y0 - 14}" y2="{YB + 8}" stroke="{color}" stroke-width="{width}"{dash}/>')
    a(f'<text x="{x:.1f}" y="{YB + 26}" fill="{MUTED}" font-size="11" text-anchor="middle">{v}×</text>')
a(f'<text x="{sx("1") - 6:.1f}" y="{Y0 - 18}" fill="{TEXT}" font-size="11" text-anchor="end">Share price equals token NAV per share</text>')
for i, r in enumerate(rows):
    y = Y0 + i * (BAR + GAP)
    color = C_MAIN if r["ticker"] == "USDE" else C_OTHER
    x_end = sx(r["mnav"])
    tip = (f"{label[r['ticker']]}. {int(r['tokens']):,} {r['token']} reported as of {day(r['tokens_as_of'])}, {int(r['shares']):,} common shares as of "
           f"{day(r['shares_as_of'])}. Close {money(r['close_2026_10_09'])}. {r['token']} {money(r['token_price_kraken_2000utc'], 4 if r['token'] == 'ENA' else 2)}"
           f", the last Kraken trade before 20:00 UTC. Token NAV per share {money(r['token_nav_per_share'])}, mNAV {q(r['mnav'], 3)}")
    a(f'<g><title>{tip}</title>')
    a(f'<text x="{X0 - 12}" y="{y + BAR / 2 - 3:.1f}" fill="{TEXT}" font-size="13" text-anchor="end">{label[r["ticker"]]}</text>')
    a(f'<text x="{X0 - 12}" y="{y + BAR / 2 + 13:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">holds {r["token"]}</text>')
    a(f'<path d="M{X0},{y} H{x_end - 4:.1f} a4,4 0 0 1 4,4 V{y + BAR - 4} a4,4 0 0 1 -4,4 H{X0} Z" fill="{color}"/>')
    inside = x_end < sx("1") and x_end + 8 + 48 > sx("1") - 4      # a label outside would cross the line at 1
    if inside:
        a(f'<text x="{x_end - 8:.1f}" y="{y + BAR / 2 + 5:.1f}" fill="#ffffff" font-size="14"{BOLD} text-anchor="end">{q(r["mnav"])}×</text>')
    else:
        a(f'<text x="{x_end + 8:.1f}" y="{y + BAR / 2 + 5:.1f}" fill="{TEXT}" font-size="14"{BOLD}>{q(r["mnav"])}×</text>')
    a('</g>')
x1 = sx("1")
a(f'<line x1="{x1:.1f}" x2="{x1:.1f}" y1="{Y0 - 14}" y2="{YB + 8}" stroke="{TEXT}" stroke-width="1.5" stroke-dasharray="4 3"/>')   # over the bars
a(f'<text x="20" y="{H - 54}" fill="{MUTED}" font-size="10">Token NAV per share is each company\'s token count from its SEC filings to October 9 times the token\'s last Kraken trade</text>')
a(f'<text x="20" y="{H - 40}" fill="{MUTED}" font-size="10">before 20:00 UTC, divided by common shares from its filings. Cash, other assets, debt and preferred stock are left out.</text>')
a(f'<text x="20" y="{H - 26}" fill="{MUTED}" font-size="10">Closes from S&amp;P Global Market Intelligence through StockAnalysis, matched with Yahoo Finance. Sources read October 12, 2026 UTC.</text>')
a('</svg>')
(HERE / "out" / "chart_mnav_peers.svg").write_text("\n".join(o) + "\n")
print("wrote out/chart_mnav_peers.svg", ", ".join(f"{r['ticker']} {q(r['mnav'])}" for r in rows))
