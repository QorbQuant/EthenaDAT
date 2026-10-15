#!/usr/bin/env python3
"""
Draws out/chart_usde_redemptions_april_2026.svg in the site's dark style. USDe's total supply on Ethereum at the
end of every UTC day from January 31 to May 31, 2026, split into the USDe held by sUSDe, the USDe in sUSDe's
cooldown silo and the USDe outside both, stacked so that the top of the stack is the total supply.

Colors  three bands in the first three categorical slots of the reference palette, dark steps, validated on the
        site's surface #0d1116. A legend names all three, each band is labeled on the chart, and each day's hover
        text gives all four values, so identity never rests on color alone. The markers for the cooldown change and
        the exploit use the neutral text colors.
Values  billions of USDe, read as dollars.
Every value, label, the title and the description come from out/chart_data.csv and out/results.json, which
redemption_waves.py writes. Run after the main script, as python3 make_chart_svg.py, with Python 3.8 or later.
"""
import csv
import json
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

HERE = Path(__file__).parent
rows = list(csv.DictReader(open(HERE / "out" / "chart_data.csv", encoding="utf-8")))
res = json.load(open(HERE / "out" / "results.json", encoding="utf-8"))
assert rows[0]["day"] == "2026-01-31" and rows[-1]["day"] == "2026-05-31" and len(rows) == 121

BG, RULE, TEXT, MUTED = ("var(--sx-bg, #0d1116)", "var(--sx-rule, #29313a)", "var(--sx-text, #eeeae3)", "var(--sx-muted, #99a3b0)")
HELD, SILO, OUTSIDE = "#3987e5", "#d95926", "#199e70"
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
HALO = f'style="paint-order:stroke;stroke:{BG};stroke-width:4px;stroke-linejoin:round"'
W, H = 800, 466
X0, X1 = 52, 716
YT, YB = 112, 376
YMAX = 7
D0, D1 = date.fromisoformat(rows[0]["day"]), date.fromisoformat(rows[-1]["day"])
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def x(d):
    return X0 + (X1 - X0) * (d - D0).days / (D1 - D0).days


def y(v):
    return YB - (YB - YT) * float(v) / YMAX


def full(d):
    return "%s %d, %d" % (MONTHS[d.month - 1], d.day, d.year)


def short(d):
    return "%s %d" % (MONTHS[d.month - 1][:3], d.day)


def b2(v):
    return str(Decimal(v).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


pts = [(date.fromisoformat(r["day"]), Decimal(r["held_by_susde_billion"]), Decimal(r["cooldown_silo_billion"]), Decimal(r["outside_susde_billion"]),
        Decimal(r["usde_supply_billion"])) for r in rows]
assert all(0 < p[4] < YMAX for p in pts)
wave = res["waves"]["april_2026"]
fall = Decimal(wave["change_pct"]).copy_abs() * 100
exploit, cut = date(2026, 4, 18), date.fromisoformat(res["cooldown"]["first_1_day"])
peak = max(pts, key=lambda p: p[2])
assert peak[0].isoformat() == res["silo_peak_april"]
p18 = next(p for p in pts if p[0] == exploit)
low = next(p for p in pts if p[0].isoformat() == wave["last_day"])
last = pts[-1]
title = "USDe's supply fell %s%% in the nine days after the rsETH exploit" % fall.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
subtitle = "USDe's total supply on Ethereum at the end of each UTC day, %s to %s, in billions, by where it was held" % (full(D0)[:-6], full(D1))
desc = ("Stacked areas of USDe's total supply on Ethereum at the end of each day from %s to %s, in billions of USDe, split into the USDe "
        "held by sUSDe, the USDe in sUSDe's cooldown silo and the USDe outside both. sUSDe's cooldown was cut from seven days to one on %s. "
        "At the end of %s, the day of the rsETH exploit, supply was %s billion, of which sUSDe held %s billion. At the end of %s it was %s "
        "billion, of which sUSDe held %s billion. The silo peaked at %s billion on %s. On %s supply was %s billion, of which sUSDe held %s "
        "billion.") % (full(D0), full(D1), full(cut), full(exploit), b2(p18[4]), b2(p18[1]), full(low[0]), b2(low[4]), b2(low[1]), b2(peak[2]),
                       full(peak[0]), full(last[0]), b2(last[4]), b2(last[1]))

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="rw-t rw-d" font-family="{FONT}">')
a(f'<title id="rw-t">Where USDe was held, {full(D0)} to {full(D1)}</title>')
a(f'<desc id="rw-d">{desc}</desc>')
a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
a(f'<text x="20" y="30" fill="{TEXT}" font-size="16" font-weight="600">{title}</text>')
a(f'<text x="20" y="52" fill="{MUTED}" font-size="12">{subtitle}</text>')
# legend
LY = 80
for lx, color, label in ((20, HELD, "Held by sUSDe"), (149, SILO, "In the cooldown silo"), (306, OUTSIDE, "Outside sUSDe")):
    a(f'<rect x="{lx}" y="{LY - 11}" width="14" height="12" rx="2" fill="{color}"/>')
    a(f'<text x="{lx + 20}" y="{LY}" fill="{MUTED}" font-size="12">{label}</text>')
# grid and axis labels
for v in range(0, YMAX + 1):
    a(f'<line x1="{X0}" x2="{X1}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{RULE}" stroke-width="1"/>')
    a(f'<text x="{X0 - 8}" y="{y(v) + 4:.1f}" fill="{MUTED}" font-size="11" text-anchor="end">{v}</text>')
for m in (2, 3, 4, 5):
    d = date(2026, m, 1)
    a(f'<line x1="{x(d):.1f}" x2="{x(d):.1f}" y1="{YB}" y2="{YB + 5}" stroke="{MUTED}" stroke-width="1"/>')
    a(f'<text x="{x(d):.1f}" y="{YB + 20}" fill="{MUTED}" font-size="11" text-anchor="middle">{short(d)}, 2026</text>')


def band(lo, hi):
    top = " L".join("%.1f,%.1f" % (x(d), y(v)) for d, v in hi)
    bottom = " L".join("%.1f,%.1f" % (x(d), y(v)) for d, v in reversed(lo))
    return "M" + top + " L" + bottom + " Z"


base = [(p[0], Decimal(0)) for p in pts]
h = [(p[0], p[1]) for p in pts]
hs = [(p[0], p[1] + p[2]) for p in pts]
tot = [(p[0], p[1] + p[2] + p[3]) for p in pts]
assert all(abs(t[1] - p[4]) <= Decimal("0.0003") for t, p in zip(tot, pts))
a(f'<path d="{band(base, h)}" fill="{HELD}"/>')
a(f'<path d="{band(h, hs)}" fill="{SILO}"/>')
a(f'<path d="{band(hs, tot)}" fill="{OUTSIDE}"/>')
# a thin surface line between the bands
for edge in (h, hs):
    a('<path d="M' + " L".join("%.1f,%.1f" % (x(d), y(v)) for d, v in edge) + f'" fill="none" stroke="{BG}" stroke-width="1"/>')
# markers for the cooldown change and the exploit
for d, label in ((cut, "Cooldown cut to 1 day, %s" % short(cut)), (exploit, "rsETH exploit, %s" % short(exploit))):
    a(f'<line x1="{x(d):.1f}" x2="{x(d):.1f}" y1="{YT}" y2="{YB}" stroke="{TEXT}" stroke-width="1" stroke-dasharray="3 3"/>')
    a(f'<text x="{x(d) + 5:.1f}" y="{YT + 10}" fill="{TEXT}" font-size="11" {HALO}>{label}</text>')
# direct labels: each band at the right end, and the silo at its peak
mid_out = (last[1] + last[2] + last[4]) / 2
a(f'<text x="{X1 + 6}" y="{y(mid_out) + 4:.1f}" fill="{TEXT}" font-size="11">Outside</text>')
a(f'<text x="{X1 + 6}" y="{y(mid_out) + 18:.1f}" fill="{TEXT}" font-size="11">{b2(last[3])}B</text>')
a(f'<text x="{X1 + 6}" y="{y(last[1] / 2) + 4:.1f}" fill="{TEXT}" font-size="11">sUSDe</text>')
a(f'<text x="{X1 + 6}" y="{y(last[1] / 2) + 18:.1f}" fill="{TEXT}" font-size="11">{b2(last[1])}B</text>')
px, py = x(peak[0]), y(peak[1] + peak[2])
a(f'<line x1="{px:.1f}" x2="{px + 30:.1f}" y1="{py:.1f}" y2="{py - 22:.1f}" stroke="{TEXT}" stroke-width="1"/>')
a(f'<text x="{px + 33:.1f}" y="{py - 22:.1f}" fill="{TEXT}" font-size="11" {HALO}>Silo {b2(peak[2])}B on {short(peak[0])}</text>')
# hover, one column per day
step = (X1 - X0) / (D1 - D0).days
for d, hv, sv, ov, tv in pts:
    t = "%s, 2026, supply %s billion, held by sUSDe %s, in the silo %s, outside sUSDe %s" % (short(d), b2(tv), b2(hv), b2(sv), b2(ov))
    a(f'<rect x="{x(d) - step / 2:.2f}" y="{YT}" width="{step:.2f}" height="{YB - YT}" fill="transparent"><title>{t}</title></rect>')
a(f'<text x="20" y="{H - 50}" fill="{MUTED}" font-size="11">Reads at the last block of each UTC day on two archive RPCs that gave identical answers, with USDe counted as one dollar.</text>')
a(f'<text x="20" y="{H - 34}" fill="{MUTED}" font-size="11">The silo holds the USDe of unstaked sUSDe until its cooldown ends. Held by sUSDe includes rewards not yet vested.</text>')
a(f'<text x="20" y="{H - 18}" fill="{MUTED}" font-size="11">Outside sUSDe is the rest of the supply on Ethereum, including the USDe locked there to back USDe on other chains.</text>')
a('</svg>')
(HERE / "out" / "chart_usde_redemptions_april_2026.svg").write_text("\n".join(o) + "\n", encoding="utf-8")
print("wrote out/chart_usde_redemptions_april_2026.svg |", title)
