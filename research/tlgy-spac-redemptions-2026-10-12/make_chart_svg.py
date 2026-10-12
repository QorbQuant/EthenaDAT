#!/usr/bin/env python3
"""
Draws out/chart_tlgy_redemptions.svg in the site's dark style, two panels on one dollar scale.
Left, what a TLGY public share was worth in cash. The trust's value a share at the IPO and in each filing that gives
it, and the cash a share paid for the redemptions at each of the six votes, December 2021 to June 2026.
Right, USDE's daily close from its first session on June 26 to October 9, 2026, against the cash a share paid at
the merger.

Every point, label, the title and the description come from out/trust_a_share.csv,
out/usde_against_merger_cash.csv and out/results.json, which tlgy_redemption_review.py writes.
Run after the main script. python3 make_chart_svg.py
"""
import csv
import json
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
trust = list(csv.DictReader(open(HERE / "out" / "trust_a_share.csv")))
usde = list(csv.DictReader(open(HERE / "out" / "usde_against_merger_cash.csv")))
res = json.loads((HERE / "out" / "results.json").read_text())
T = [(date.fromisoformat(r["date"]), r["kind"], float(r["value_a_share"])) for r in trust]
U = [(date.fromisoformat(r["date"]), float(r["usde_close"]), r["at_or_above"] == "1") for r in usde]
M = res["usde"]["merger_cash_a_share"]
V = res["votes"]
assert len(U) == res["usde"]["sessions"] == 74 and len(T) == 16

BG, RULE, TEXT, MUTED = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)",
                         "var(--sx-muted, #99a3b0)")
C_TRUST = "#3987e5"
C_USDE = "#d95926"
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
HALO = f'style="paint-order:stroke;stroke:{BG};stroke-width:4px;stroke-linejoin:round"'
W, H = 800, 466
Y0, Y1, YMAX = 124, 404, 18.0
L0, L1 = 58, 418
R0, R1 = 452, 772
LD0, LD1 = date(2021, 11, 1), date(2026, 8, 15)
RD0, RD1 = date(2026, 6, 19), date(2026, 10, 16)


def sy(v):
    return Y1 - (Y1 - Y0) * v / YMAX


def lx(d):
    return L0 + (L1 - L0) * (d - LD0).days / (LD1 - LD0).days


def rx(d):
    return R0 + (R1 - R0) * (d - RD0).days / (RD1 - RD0).days


WORD = {8: "eight", 9: "nine", 10: "ten"}


def short(d):
    return d.strftime("%b ") + str(d.day)


def monthyear(d):
    return d.strftime("%b %Y")


def full(d):
    return d.strftime("%B ") + str(d.day) + d.strftime(", %Y")


assert all(0 < v <= YMAX for _, _, v in T) and all(0 < c <= YMAX for _, c, _ in U), "a point falls outside the axes"
assert all(LD0 < d < LD1 for d, _, _ in T) and all(RD0 < d < RD1 for d, _, _ in U)
pays = [(d, v) for d, k, v in T if k == "redemption"]
assert [round(v, 2) for _, v in pays] == [10.40, 10.96, 11.38, 12.12, 13.20, 13.35]
below = sum(1 for _, _, a in U if not a)
first, low, high, last = res["usde"]["first"], res["usde"]["low"], res["usde"]["high"], res["usde"]["last"]

title = (f"Redemptions paid ${pays[0][1]:.2f} to ${pays[-1][1]:.2f} a share. USDE closed below ${M:.2f} "
         f"in {below} of {len(U)} sessions")
subtitle = ("Left, cash a TLGY public share from the 2021 IPO to the 2026 merger. "
            "Right, USDE's close from its first session on June 26.")
desc = (f"Two panels on one dollar scale. Left, the trust's value a public share, ${T[0][2]:.2f} at the IPO on "
        f"{full(T[0][0])}, rising at every report date and extension vote to ${pays[-1][1]:.2f} paid at the merger closing on "
        f"{full(pays[-1][0])}. Filled dots mark the cash a share paid for redemptions at the six votes, " +
        ", ".join(f"${v:.2f}" for _, v in pays) + ". Hollow dots mark the trust's value a share at the IPO and at "
        f"{WORD[sum(1 for _, k, _ in T if k == 'report')]} report dates. "
        f"Right, USDE's close at {len(U)} sessions from {full(U[0][0])} to {full(U[-1][0])}, against a dashed line at "
        f"${M:.2f}. It closed at ${first['close']:.2f} on its first day, fell to ${low['close']:.2f} on "
        f"{full(date.fromisoformat(low['date']))}, rose to ${high['close']:.2f} on {full(date.fromisoformat(high['date']))} and "
        f"closed at ${last['close']:.2f} on {full(date.fromisoformat(last['date']))}. It closed at or above the dashed line "
        f"in {len(U) - below} sessions, all from September 22 to October 7. A dotted line marks the $10.00 IPO unit price "
        "in both panels.")

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="tr-t tr-d" font-family="{FONT}">')
a("<title id=\"tr-t\">TLGY's trust value a public share and the cash a share paid for redemptions at each vote, "
  "December 2021 to June 2026, "
  "and USDE's close against the merger's cash a share, June 26 to October 9, 2026</title>")
a(f'<desc id="tr-d">{desc}</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
a(f'<text x="20" y="30" fill="{TEXT}" font-size="16" font-weight="600">{title}</text>')
a(f'<text x="20" y="52" fill="{MUTED}" font-size="12">{subtitle}</text>')
# legend row
LY = 78
a(f'<circle cx="26" cy="{LY - 4}" r="4.5" fill="{C_TRUST}"/>')
a(f'<text x="36" y="{LY}" fill="{MUTED}" font-size="11">Redemption cash a share</text>')
a(f'<circle cx="190" cy="{LY - 4}" r="3.5" fill="{BG}" stroke="{C_TRUST}" stroke-width="1.5"/>')
a(f'<text x="200" y="{LY}" fill="{MUTED}" font-size="11">Trust value a share in a filing</text>')
a(f'<line x1="372" x2="394" y1="{LY - 4}" y2="{LY - 4}" stroke="{C_USDE}" stroke-width="2"/>')
a(f'<text x="400" y="{LY}" fill="{MUTED}" font-size="11">USDE close</text>')
a(f'<line x1="478" x2="500" y1="{LY - 4}" y2="{LY - 4}" stroke="{TEXT}" stroke-width="1.5" stroke-dasharray="6 4"/>')
a(f'<text x="506" y="{LY}" fill="{MUTED}" font-size="11">${M:.2f} paid at the merger</text>')
a(f'<line x1="652" x2="674" y1="{LY - 4}" y2="{LY - 4}" stroke="{MUTED}" stroke-width="1" stroke-dasharray="2 4"/>')
a(f'<text x="680" y="{LY}" fill="{MUTED}" font-size="11">$10.00 unit price</text>')
# panel headings
a(f'<text x="{L0}" y="{Y0 - 12}" fill="{TEXT}" font-size="12" font-weight="600">In the trust</text>')
a(f'<text x="{R0}" y="{Y0 - 12}" fill="{TEXT}" font-size="12" font-weight="600">After the merger</text>')
# shared y grid, labels on the left only
for v in range(0, 19, 2):
    for x0, x1 in ((L0, L1), (R0, R1)):
        a(f'<line x1="{x0}" x2="{x1}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{L0 - 8}" y="{sy(v) + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">${v}</text>')
# x ticks
for yr in range(2022, 2027):
    d = date(yr, 1, 1)
    a(f'<line x1="{lx(d):.1f}" x2="{lx(d):.1f}" y1="{Y1}" y2="{Y1 + 5}" stroke="{MUTED}" stroke-width="1"/>')
    a(f'<text x="{lx(d):.1f}" y="{Y1 + 19}" fill="{MUTED}" font-size="11" text-anchor="middle">{yr}</text>')
for m in (7, 8, 9, 10):
    d = date(2026, m, 1)
    a(f'<line x1="{rx(d):.1f}" x2="{rx(d):.1f}" y1="{Y1}" y2="{Y1 + 5}" stroke="{MUTED}" stroke-width="1"/>')
    a(f'<text x="{rx(d):.1f}" y="{Y1 + 19}" fill="{MUTED}" font-size="11" text-anchor="middle">{d.strftime("%b")}</text>')
a(f'<text x="20" y="{Y1 + 46}" fill="{MUTED}" font-size="10">SEC filings of TLGY Acquisition Corp. and StablecoinX Inc. '
  'Closes, S&amp;P Global Market Intelligence via StockAnalysis.</text>')
# reference lines
for x0, x1 in ((L0, L1), (R0, R1)):
    a(f'<line x1="{x0}" x2="{x1}" y1="{sy(10):.1f}" y2="{sy(10):.1f}" stroke="{MUTED}" stroke-width="1" stroke-dasharray="2 4"/>')
a(f'<line x1="{R0}" x2="{R1}" y1="{sy(M):.1f}" y2="{sy(M):.1f}" stroke="{TEXT}" stroke-width="1.5" stroke-dasharray="6 4"/>')
# left panel, the trust
a('<polyline points="' + " ".join(f"{lx(d):.1f},{sy(v):.1f}" for d, _, v in T)
  + f'" fill="none" stroke="{C_TRUST}" stroke-width="1.5" stroke-opacity="0.6" stroke-linejoin="round"/>')
names = {round(v["a_share"], 4): v["name"] for v in V.values()}
for d, k, v in T:
    if k == "redemption":
        what = "Merger closing" if names[round(v, 4)] == "Merger" else f"{names[round(v, 4)]} vote"
        tip = f"{what}, {short(d)}, {d.year}, ${v:.2f} a share paid"
        dot = f'<circle cx="{lx(d):.1f}" cy="{sy(v):.1f}" r="4.5" fill="{C_TRUST}" stroke="{BG}" stroke-width="1.5"/>'
    else:
        tip = (f"IPO, {short(d)}, {d.year}, ${v:.2f} a unit in trust" if k == "ipo"
               else f"{short(d)}, {d.year}, trust ${v:.2f} a share")
        dot = f'<circle cx="{lx(d):.1f}" cy="{sy(v):.1f}" r="3.5" fill="{BG}" stroke="{C_TRUST}" stroke-width="1.5"/>'
    a(f'<g><title>{tip}</title><circle cx="{lx(d):.1f}" cy="{sy(v):.1f}" r="9" fill="transparent"/>{dot}</g>')
# value labels for the votes, staggered above and below the line so they do not collide
offs = [(0, -12, "middle"), (0, 22, "middle"), (0, -12, "middle"), (0, -12, "middle"), (-6, 22, "end"), (6, -12, "end")]
for (d, v), (dx, dy, anchor) in zip(pays, offs):
    a(f'<text x="{lx(d) + dx:.1f}" y="{sy(v) + dy:.1f}" fill="{TEXT}" font-size="11" text-anchor="{anchor}" {HALO}>${v:.2f}</text>')
a(f'<text x="{lx(T[0][0]) + 2:.1f}" y="{sy(T[0][2]) + 22:.1f}" fill="{MUTED}" font-size="11" {HALO}>${T[0][2]:.2f} IPO</text>')
# right panel, USDE
a('<polyline points="' + " ".join(f"{rx(d):.1f},{sy(c):.1f}" for d, c, _ in U)
  + f'" fill="none" stroke="{C_USDE}" stroke-width="2" stroke-linejoin="round"/>')
for d, c, at in U:
    tip = f"{short(d)}, USDE ${c:.2f}, " + ("at or above" if at else "below") + f" ${M:.2f}"
    a(f'<g><title>{tip}</title><circle cx="{rx(d):.1f}" cy="{sy(c):.1f}" r="5" fill="transparent"/>'
      + (f'<circle cx="{rx(d):.1f}" cy="{sy(c):.1f}" r="2.5" fill="{C_USDE}"/>' if at else "") + "</g>")
a(f'<text x="{rx(date(2026, 9, 19)):.1f}" y="{sy(15.4):.1f}" fill="{TEXT}" font-size="11" text-anchor="end" {HALO}>'
  f'{len(U) - below} closes at or above ${M:.2f}</text>')
for pt, dy, anchor, dx in ((first, -10, "start", 4), (low, 16, "middle", 0), (high, -10, "middle", 0), (last, 16, "end", 6)):
    d = date.fromisoformat(pt["date"])
    a(f'<circle cx="{rx(d):.1f}" cy="{sy(pt["close"]):.1f}" r="3.5" fill="{C_USDE}" stroke="{BG}" stroke-width="1.5"/>')
    a(f'<text x="{rx(d) + dx:.1f}" y="{sy(pt["close"]) + dy:.1f}" fill="{TEXT}" font-size="11" text-anchor="{anchor}" {HALO}>'
      f'{short(d)} ${pt["close"]:.2f}</text>')
a("</svg>")
(HERE / "out" / "chart_tlgy_redemptions.svg").write_text("\n".join(o) + "\n")
print("wrote out/chart_tlgy_redemptions.svg")
