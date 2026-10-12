#!/usr/bin/env python3
"""
Draws out/chart_avax_usde_holders.svg in the site's dark style. A stacked area of the USDe on Avalanche C-Chain at the
end of each UTC day from May 15, the day of the first EthenaPay wallets, to October 11, 2026, split into EthenaPay
wallets, the settlement and reward accounts and the holders outside EthenaPay. The three parts add up to the supply, so
the top edge is the supply. A dashed line marks the supply's 2025 high.

Colors  the first three categorical slots of the reference palette, dark steps. Run through the palette validator against
        #0d1116, every check passes, worst adjacent colour-vision-deficiency separation 9.4 and normal-vision
        separation 26.5, all three at 3:1 or better. A legend names each band and the end labels repeat the names beside
        a swatch, so identity never rests on colour alone. Text uses the text colours, never a band's colour.
Values  the labels in millions to three decimals, so the end labels of the three bands add up to the label of the supply.
        The hover text gives each day's amounts to the cent, each rounded on its own, so they add up to within a cent.
Every value, label, the title and the description come from out/chart_daily.csv and out/results.json, which
avax_usde_review.py writes. Run after the main script, as python3 make_chart_svg.py, with Python 3.8 or later.
"""
import csv
import json
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE / "out" / "chart_daily.csv")))
res = json.loads((HERE / "out" / "results.json").read_text())
assert rows[0]["date"] == "2026-05-15" and rows[-1]["date"] == res["end"]["date"] == "2026-10-11" and len(rows) == 150
W_, O_, X_ = ([Decimal(r[k]) for r in rows] for k in ("ethenapay_wallets_usde", "settlement_and_reward_accounts_usde", "holders_outside_ethenapay_usde"))
SUP = [Decimal(r["supply_usde"]) for r in rows]
assert all(abs(a + b + c - s) <= Decimal("0.02") for a, b, c, s in zip(W_, O_, X_, SUP))   # rounded to the cent apiece
HIGH = Decimal(res["before"]["peak_2025_usde"])

BG, RULE, TEXT, MUTED = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)", "var(--sx-muted, #99a3b0)")
C_W, C_O, C_X = "#3987e5", "#d95926", "#199e70"   # first three categorical slots, dark steps, validated on #0d1116
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
W, H = 800, 466
X0, X1, Y0, Y1 = 64, 628, 108, 380
YMAX = Decimal(12_000_000)
n = len(rows)
BOLD = ' font-weight="600"'


def sx(i):
    return X0 + (X1 - X0) * i / (n - 1)


def sy(v):
    return Y1 - (Y1 - Y0) * float(Decimal(v) / YMAX)


def m(v, places=3):
    return f"{(Decimal(v) / 1_000_000).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)}M"


def mn(v):
    return f"{(Decimal(v) / 1_000_000).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)} million"


def cents(v):
    return f"{Decimal(v).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}"


def day_label(s):
    d = date.fromisoformat(s)
    return d.strftime("%b ") + str(d.day)


def full_day(s):
    d = date.fromisoformat(s)
    return d.strftime("%B ") + str(d.day)


end = res["end"]
g = end["groups"]
share = Decimal(g["wallets"]["share_pct"]).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
linked = Decimal(end["ethenapay_linked_share_pct"]).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
first = res["growth"]["wallets_first_above_half"]
first_pct = Decimal(first["share_pct"]).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
title = f"EthenaPay wallets held {share}% of the USDe on Avalanche at the end of October 11"
subtitle = "USDe on Avalanche C-Chain at the end of each UTC day, May 15 to October 11, 2026, stacked by holder"
desc = (f"Stacked area chart of {n} days. The supply of USDe on Avalanche C-Chain rose from {mn(SUP[0])} on May 15, 2026, the day the first "
        f"EthenaPay wallets were created, to {mn(SUP[-1])} on October 11. EthenaPay wallets held more than half of it for the first time on "
        f"{full_day(first['date'])}, {first_pct}%, and {share}% on October 11, {mn(W_[-1])}. The settlement and reward accounts, which are the "
        f"settlement addresses, the settlement recipients and the reward accounts together, held {mn(O_[-1])} more, so accounts tied to EthenaPay held "
        f"{linked}%. Holders outside EthenaPay held {mn(X_[-1])}. A dashed line marks the 2025 high of {mn(HIGH)}.")

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="au-t au-d" font-family="{FONT}">')
a('<title id="au-t">USDe on Avalanche C-Chain by holder, May 15 to October 11, 2026</title>')
a(f'<desc id="au-d">{desc}</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
a(f'<text x="20" y="30" fill="{TEXT}" font-size="16"{BOLD}>{title}</text>')
a(f'<text x="20" y="52" fill="{MUTED}" font-size="12">{subtitle}</text>')
LY = 78
lx = 20
for label, color, width in (("EthenaPay wallets", C_W, 136), ("Settlement and reward accounts", C_O, 226), ("Holders outside EthenaPay", C_X, 0)):
    a(f'<rect x="{lx}" y="{LY - 9}" width="10" height="10" rx="2" fill="{color}"/>')
    a(f'<text x="{lx + 16}" y="{LY}" fill="{TEXT}" font-size="12">{label}</text>')
    lx += width
for v in (0, 3, 6, 9, 12):
    y = sy(v * 1_000_000)
    a(f'<line x1="{X0}" x2="{X1}" y1="{y:.1f}" y2="{y:.1f}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{X0 - 8}" y="{y + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">{v}M</text>' if v else
      f'<text x="{X0 - 8}" y="{y + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">0</text>')
a(f'<text x="{X0 - 50}" y="{Y0 - 12}" fill="{MUTED}" font-size="11">USDe</text>')
for i, r in enumerate(rows):
    if r["date"].endswith("-01") or i in (0, n - 1):
        if 0 < i < n - 1 and sx(n - 1) - sx(i) < 60:      # a month tick this close to the last day's is left out
            continue
        a(f'<line x1="{sx(i):.1f}" x2="{sx(i):.1f}" y1="{Y1}" y2="{Y1 + 5}" stroke="{RULE}" stroke-width="1"/>')
        anchor = "start" if i == 0 else "end" if i == n - 1 else "middle"
        a(f'<text x="{sx(i):.1f}" y="{Y1 + 19}" fill="{MUTED}" font-size="11" text-anchor="{anchor}">{day_label(r["date"])}</text>')

cum1 = W_
cum2 = [w + o_ for w, o_ in zip(W_, O_)]
cum3 = [w + o_ + x for w, o_, x in zip(W_, O_, X_)]


def band(lower, upper, color):
    top = " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(upper))
    bot = " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in reversed(list(enumerate(lower))))
    a(f'<polygon points="{top} {bot}" fill="{color}"/>')


band([Decimal(0)] * n, cum1, C_W)
band(cum1, cum2, C_O)
band(cum2, cum3, C_X)
for edge in (cum1, cum2):        # a 1px gap in the background colour between the bands, thin enough to keep a thin band visible
    a('<polyline points="' + " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(edge)) + f'" fill="none" stroke="{BG}" stroke-width="1" stroke-linejoin="round"/>')
a('<polyline points="' + " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(cum3)) + f'" fill="none" stroke="{TEXT}" stroke-width="1" stroke-opacity="0.5" stroke-linejoin="round"/>')
yh = sy(HIGH)
a(f'<line x1="{X0}" x2="{X1}" y1="{yh:.1f}" y2="{yh:.1f}" stroke="{TEXT}" stroke-width="1" stroke-opacity="0.7" stroke-dasharray="4 3"/>')
a(f'<text x="{X0 + 6}" y="{yh - 6:.1f}" fill="{MUTED}" font-size="10">2025 high {m(HIGH)}</text>')
step = (X1 - X0) / (n - 1)
for i, r in enumerate(rows):
    a(f'<rect x="{sx(i) - step / 2:.1f}" y="{Y0}" width="{step:.2f}" height="{Y1 - Y0}" fill="transparent"><title>{day_label(r["date"])}, supply {cents(SUP[i])} USDe. '
      f'EthenaPay wallets {cents(W_[i])}, settlement and reward accounts {cents(O_[i])}, holders outside EthenaPay {cents(X_[i])}</title></rect>')

# end labels to the right of the plot, each beside a swatch, kept 15px apart, 28px after a label on two lines
want = [("All holders", None, sy(cum3[-1]), m(SUP[-1])), ("Holders outside|EthenaPay", C_X, sy((cum2[-1] + cum3[-1]) / 2), m(X_[-1])),
        ("Settlement and|reward accounts", C_O, sy((cum1[-1] + cum2[-1]) / 2), m(O_[-1])), ("EthenaPay wallets", C_W, sy(cum1[-1] / 2), m(W_[-1]))]
ys = []
for k, (_, _, y, _) in enumerate(want):
    ys.append(max(y, ys[-1] + (28 if "|" in want[k - 1][0] else 15)) if ys else y)
for (label, color, _, val), y in zip(want, ys):
    x = X1 + 10
    if color:
        a(f'<rect x="{x}" y="{y - 8:.1f}" width="8" height="8" rx="2" fill="{color}"/>')
    first_line, _, second = label.partition("|")
    text = (f'{first_line}<tspan x="{x + 12}" dy="13">{second} {val}</tspan>' if second else f"{label} {val}")
    weight = BOLD if color is None else ""
    a(f'<text x="{x + (12 if color else 0)}" y="{y:.1f}" fill="{TEXT if color is None else MUTED}" font-size="11"{weight}>{text}</text>')
a(f'<text x="20" y="{H - 40}" fill="{MUTED}" font-size="10">Settlement and reward accounts are the two settlement addresses, the three settlement recipients and the '
  'three reward accounts.</text>')
a(f'<text x="20" y="{H - 26}" fill="{MUTED}" font-size="10">Holders outside EthenaPay include the rhino.fi bridge contract and the Uniswap v3 pool. The dashed line '
  'marks the 2025 high.</text>')
a(f'<text x="20" y="{H - 12}" fill="{MUTED}" font-size="10">Transfers of USDe on Avalanche C-Chain, read from the Routescan explorer API on October 12, 2026 UTC. '
  'Wallets are not people.</text>')
a('</svg>')
(HERE / "out" / "chart_avax_usde_holders.svg").write_text("\n".join(o) + "\n")
print(f"wrote out/chart_avax_usde_holders.svg, {n} days, end labels at", ", ".join(f"{y:.0f}" for y in ys))
