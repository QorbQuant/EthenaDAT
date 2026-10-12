#!/usr/bin/env python3
"""StablecoinX's book value at June 30, 2026, set against the market value of its ENA.

Reads the files in inputs/ and runs every check. If any check fails it stops before writing
anything, so out/ keeps the tables of the last clean run. Otherwise it rewrites the tables in
out/. Python 3 standard library only. It makes no network requests.

Inputs.
  filing_facts.csv   Figures and policies from the second-quarter 10-Q, the results release of
                     August 14, the 8-K of August 24, the resale prospectus of September 14, the
                     closing 8-K of July 2 and five Forms 4 of October 2, each with its location.
  Kraken ENA/USD     Daily candles for ENA's lowest trade by UTC day, and the 4-hour candle from
                     16:00 to 20:00 UTC for ENA's price at the 4 pm New York close.
  USDE and USDEW     Daily closes from S&P Global Market Intelligence through StockAnalysis.
  Dashboard series   This site's dataset at commit dda5a00, for the Class A share count by date
                     and a cross-check of USDE's closes.
  EDGAR list         The company's filings from June 25, 2026, read on October 9.

Book value is total stockholders' equity. Per share it uses Class A shares only, because the 10-Q
leaves Class B shares out of loss per share, as votes without a claim on dividends or assets.
Every date in the window fell in daylight saving time, so the 4 pm close was 20:00 UTC.
"""
import csv
import hashlib
import json
import math
import os
import sys
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.join(HERE, "inputs")
OUT = os.path.join(HERE, "out")
FIRST, LAST = date(2026, 6, 30), date(2026, 10, 8)
MERGER = date(2026, 6, 25)
Q3 = (date(2026, 7, 1), date(2026, 9, 30))

LOG = []
FAILED = []


def say(msg=""):
    LOG.append(msg)
    print(msg)


def check(name, ok, detail=""):
    say(f"[{'ok' if ok else 'FAIL'}] {name}{' . ' + detail if detail else ''}")
    if not ok:
        FAILED.append(name)


def read_csv(name):
    with open(os.path.join(INP, name), newline="") as f:
        return list(csv.DictReader(f))


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def r2(x):
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def money(x):
    return f"{x:,.0f}"


# ---------------------------------------------------------------- inputs and hashes
say("StablecoinX book value review")
say(f"Window {FIRST} to {LAST}")
say()
manifest = read_csv("manifest.csv")
for m in manifest:
    p = os.path.join(INP, m["file"])
    ok = os.path.exists(p) and sha256(p) == m["sha256"] and os.path.getsize(p) == int(m["bytes"])
    check(f"input {m['file']} matches its recorded SHA-256 and size", ok)
listed = {m["file"] for m in manifest}
present = {f for f in os.listdir(INP) if f != "manifest.csv"}
check("every input file is in the manifest and every manifest entry exists", listed == present,
      f"{len(listed)} files")

facts = {}
for r in read_csv("filing_facts.csv"):
    check(f"fact {r['id']} appears once", r["id"] not in facts)
    facts[r["id"]] = r
sources = {r["key"]: r for r in read_csv("sources.csv")}
check("every fact cites a listed source", all(r["source_key"] in sources for r in facts.values()))


def n(key):
    return Decimal(facts[key]["value"])


# ---------------------------------------------------------------- the balance sheet adds up
say()
say("Balance sheet at June 30, 2026")
cur_assets = ["cash", "digital_assets_receivable_related_party", "digital_assets_restricted", "prepaid_insurance",
              "prepaid_and_other_current"]
cur_liabs = ["sponsor_convertible_demand_notes", "demand_notes_related_party", "accounts_payable",
             "accounts_payable_related_party", "accrued_expenses"]
equity = ["class_a_par", "class_b_par", "additional_paid_in_capital", "accumulated_deficit"]
check("current assets add up", sum(n(k) for k in cur_assets) == n("total_current_assets"))
check("total assets add up",
      n("total_current_assets") + n("digital_intangible_assets") + n("intangible_assets_net") == n("total_assets"))
check("current liabilities add up", sum(n(k) for k in cur_liabs) == n("total_current_liabilities"))
check("total liabilities add up", n("total_current_liabilities") + n("warrant_liability") == n("total_liabilities"))
check("equity adds up", sum(n(k) for k in equity) == n("total_stockholders_equity"))
check("liabilities and equity equal total assets",
      n("total_liabilities") + n("total_stockholders_equity") == n("total_assets") == n("total_liabilities_and_equity"))
check("Note 8 software adds up to intangible assets, net",
      n("software_license_net") + n("capitalized_software") == n("intangible_assets_net"))
check("Note 5 restricted ETH equals the balance sheet line", n("eth_restricted_fair_value") == n("digital_assets_restricted"))
check("Note 4 DVN revenue equals the receivable from Ethena",
      n("dvn_revenue_q2") == n("digital_assets_receivable_related_party"))
class_a = n("class_a_shares_june30")
class_b = n("class_b_shares_cover")
check("Class A shares at June 30 equal the cover count of August 12", class_a == n("class_a_shares_cover"))
check("par values match the share counts at $0.0001",
      round(class_a * Decimal("0.0001")) == n("class_a_par") and round(class_b * Decimal("0.0001")) == n("class_b_par"))

book = n("total_stockholders_equity")
ena_net = n("digital_intangible_assets")
other_assets = n("total_assets") - ena_net - n("cash")
other_liabs = n("demand_notes_related_party") + n("accounts_payable") + n("accounts_payable_related_party")
non_ena_net = book - ena_net
check("non-ENA net assets equal cash plus other assets less total liabilities",
      non_ena_net == n("cash") + other_assets - n("total_liabilities"))
bv_share = book / class_a
bv_share_ab = book / (class_a + class_b)
say(f"  book value {money(book)}, per Class A share {bv_share:.6f}, per Class A and B share {bv_share_ab:.6f}")
say(f"  ENA {money(ena_net)}, everything else net {money(non_ena_net)}, {non_ena_net / class_a:.6f} per share")

# ---------------------------------------------------------------- ENA at cost less impairment
say()
say("ENA carrying value")
lots = [("contribution", n("ena_tokens_contribution"), n("ena_value_contribution")),
        ("initial PIPE", n("ena_tokens_pipe_initial"), n("ena_value_pipe_initial")),
        ("additional PIPE", n("ena_tokens_pipe_additional"), n("ena_value_pipe_additional"))]
tokens = sum(t for _, t, _ in lots)
cost = sum(v for _, _, v in lots)
check("the three lots sum to 3,031,404,420.94 ENA", tokens == Decimal("3031404420.94"))
check("their June 25 values sum to the gross carrying amount within $1", abs(cost - n("ena_gross_carrying")) <= 1,
      f"{cost} against {n('ena_gross_carrying')}")
lot_prices = [v / t for _, t, v in lots]
for (name, t, v), p in zip(lots, lot_prices):
    say(f"  {name}: {t} ENA, ${v}, ${p:.8f} a token")
check("each lot was valued at the same price per token, to within $0.000001",
      max(lot_prices) - min(lot_prices) < Decimal("0.000001"))
check("gross less accumulated impairments equals the net carrying amount",
      n("ena_gross_carrying") - n("ena_accumulated_impairments") == n("ena_net_carrying") == ena_net)
check("the second quarter's impairment expense equals the accumulated impairments and rounds to Note 2's $36.2 million",
      n("impairment_q2") == n("ena_accumulated_impairments") and
      (n("impairment_q2") / 10**5).quantize(Decimal("1"), rounding=ROUND_HALF_UP) == n("impairment_q2_text") * 10)
cost_per_token = n("ena_gross_carrying") / tokens
carry_per_token = ena_net / tokens
say(f"  cost {cost_per_token:.8f} a token, carrying value {carry_per_token:.8f} a token")

daily = read_csv("kraken_enausd_daily.csv")
daily_by = {r["date_utc"]: r for r in daily}
check("Kraken daily candles run without a gap from June 25 to October 9",
      [date.fromisoformat(r["date_utc"]) for r in daily] ==
      [date.fromordinal(d) for d in range(MERGER.toordinal(), date(2026, 10, 9).toordinal() + 1)])
check("each Kraken candle starts at 00:00 UTC on its date",
      all(int(r["time_unix"]) == (date.fromisoformat(r["date_utc"]).toordinal() - date(1970, 1, 1).toordinal()) * 86400
          for r in daily))


def lowest(d0, d1):
    rows = [r for r in daily if d0 <= date.fromisoformat(r["date_utc"]) <= d1]
    low = min(Decimal(r["low"]) for r in rows)
    days = [r["date_utc"] for r in rows if Decimal(r["low"]) == low]
    return low, days


low_q2, low_q2_days = lowest(MERGER, date(2026, 6, 30))
low_q3, low_q3_days = lowest(*Q3)
say(f"  Kraken's lowest trade June 25 to June 30, ${low_q2} on {low_q2_days}")
say(f"  Kraken's lowest trade July 1 to September 30, ${low_q3} on {low_q3_days}")
check("the carrying value per token is within half a Kraken price step, $0.00005, of Kraken's lowest trade "
      "from the merger to June 30", abs(carry_per_token - low_q2) < Decimal("0.00005"),
      f"{carry_per_token:.6f} against {low_q2}")
check("the carrying value per token is above Kraken's lowest trade, so the company's price was not that trade",
      carry_per_token > low_q2, f"{carry_per_token - low_q2:.8f} above")
check("that lowest trade came on June 30", low_q2_days == ["2026-06-30"])
check("Kraken's lowest trade in the third quarter was above the carrying value per token", low_q3 > carry_per_token,
      f"{low_q3} on {low_q3_days[0]}, {(low_q3 / carry_per_token - 1) * 100:.2f}% above")
low_since, low_since_days = lowest(MERGER, date(2026, 10, 9))
check("no Kraken trade from June 25 to October 9 was below $0.0702", low_since == low_q2 and low_since_days == ["2026-06-30"])

# ---------------------------------------------------------------- the release's figures
say()
say("Results release of August 14")
rel_value = tokens * n("release_ena_price")
rel_per_share = rel_value / class_a
say(f"  {tokens} ENA x ${n('release_ena_price')} = {money(rel_value)}, {rel_per_share:.4f} per Class A share")
check("the release's $218.4 million reproduces with the 10-Q's token count",
      (rel_value / 10**5).quantize(Decimal("1"), rounding=ROUND_HALF_UP) == 2184)
check("the release's $9.09 per share reproduces on 24,029,375 Class A shares", r2(rel_per_share) == n("release_value_per_share"))
rel_less_carrying = rel_value - ena_net
book_less_release = book - rel_value
check("book value less the release's value equals the non-ENA net assets less the gap between the two ENA prices",
      book_less_release == non_ena_net - rel_less_carrying, f"{book_less_release:.2f}")
say(f"  release less carrying value {money(rel_less_carrying)}, book value less release {money(book_less_release)}")
check("the release's $218.4 million does not reproduce with 3,029,000,000 ENA",
      (3029000000 * n("release_ena_price") / 10**5).quantize(Decimal("1"), rounding=ROUND_HALF_UP) != 2184)
check("Kraken's June 30 daily close is within $0.0001 of the release's closing price",
      abs(Decimal(daily_by["2026-06-30"]["close"]) - n("release_ena_price")) <= Decimal("0.0001"),
      f"{daily_by['2026-06-30']['close']} against {n('release_ena_price')}")

# ---------------------------------------------------------------- warrants and sponsor notes
say()
say("Warrant liability and sponsor notes")
usdew = {r["date"]: Decimal(r["close"]) for r in read_csv("usdew_daily_spglobal_stockanalysis.csv")}
public = n("public_warrants_at_closing")
w_jun30 = public * usdew["2026-06-30"]
w_assumed_price = n("warrant_liability_assumed") / public
check("the June 30 warrant liability equals 11,499,988 public warrants at USDEW's June 30 close of $0.41, "
      "to the nearest $1,000", round(w_jun30, -3) == n("warrant_liability"), f"{w_jun30}")
check("the liability assumed at the merger, $6.9 million, is $0.60 a public warrant",
      w_assumed_price.quantize(Decimal("0.01")) == Decimal("0.60"), f"{w_assumed_price:.6f}")
check("the drop from $6.9 million to $4.715 million equals the second quarter's warrant gain",
      n("warrant_liability_assumed") - n("warrant_liability") == n("warrant_fair_value_gain_q2"))
w_sep30 = public * usdew["2026-09-30"]
w_rise = w_sep30 - n("warrant_liability")
say(f"  public warrants at USDEW's September 30 close of ${usdew['2026-09-30']}: {money(w_sep30)}, "
    f"{money(w_rise)} more than June 30, {w_rise / book * 100:.2f}% of June 30 book value")
notes = n("sponsor_convertible_demand_notes")
check("the notes on the balance sheet round to the 8-K's $6.9 million of original principal",
      (notes / 10**5).quantize(Decimal("1"), rounding=ROUND_HALF_UP) == 69)
tranche_a_calc = notes * n("sponsor_tranche_a_share") / 100 / n("sponsor_tranche_a_warrant_price")
tranche_b_calc = notes * n("sponsor_tranche_b_share") / 100 / n("sponsor_tranche_b_warrant_price")
cash_part = notes * n("sponsor_cash_share") / 100
check("47.5% of $6,879,325 at $1.00 a warrant gives the 3,267,679 Tranche A warrants",
      math.floor(tranche_a_calc) == n("tranche_a_warrants"), f"{tranche_a_calc}")
check("47.5% of $6,879,325 at $0.75 a warrant gives the 4,356,907 Tranche B warrants to within two",
      abs(tranche_b_calc - n("tranche_b_warrants")) < 2, f"{tranche_b_calc:.2f}")
check("the three parts of the settlement add up to 100%",
      n("sponsor_cash_share") + n("sponsor_tranche_a_share") + n("sponsor_tranche_b_share") == 100)
say(f"  cash part {cash_part:.2f}")

# ---------------------------------------------------------------- share counts after June 30
say()
say("Class A shares by date")
dash = {r["date"]: r for r in read_csv("dashboard_series_dda5a00.csv")}
awards = n("director_award_shares") * n("director_awards")
steps = []
prev = None
for d in sorted(dash):
    s = Decimal(dash[d]["shares_outstanding"])
    if prev is not None and s != prev[1]:
        steps.append((d, prev[1], s))
    prev = (d, s)
check("the dashboard's Class A count is 24,029,375 from June 30 to September 29",
      all(Decimal(dash[d]["shares_outstanding"]) == class_a for d in dash if "2026-06-30" <= d <= "2026-09-29"))
check("its one step after June 30 is on September 30, by the five directors' 110,000 restricted shares",
      [s for s in steps if s[0] > "2026-06-30"] == [("2026-09-30", class_a, class_a + awards)], f"{steps}")
check("the dashboard carries 3,029,000,000 ENA on every date",
      all(Decimal(r["ena_holdings"]) == 3029000000 for r in dash.values()))

# ---------------------------------------------------------------- each session, June 30 to October 8
say()
say("Sessions")
usde = {r["date"]: Decimal(r["close"]) for r in read_csv("usde_daily_spglobal_stockanalysis.csv")}
k4 = {}
for r in read_csv("kraken_enausd_4h_20utc_00utc.csv"):
    if r["start_utc"].endswith("T16:00:00Z"):
        k4[r["start_utc"][:10]] = Decimal(r["close"])
sessions = sorted(d for d in usde if FIRST.isoformat() <= d <= LAST.isoformat())
check("71 sessions from June 30 to October 8", len(sessions) == 71, f"{len(sessions)}")
check("every session has Kraken's 16:00 to 20:00 UTC candle", all(d in k4 for d in sessions))
check("every session is in the dashboard series", all(d in dash for d in sessions))
check("the dashboard's USDE close matches S&P Global's on every session to the cent",
      all(abs(Decimal(dash[d]["usde_close"]) - usde[d]) < Decimal("0.005") for d in sessions))
w_sessions = [d for d in sessions if d in usdew]
check("S&P Global has a USDEW close for 69 of the 71 sessions, all but July 17 and August 18",
      len(w_sessions) == 69 and sorted(set(sessions) - set(w_sessions)) == ["2026-07-17", "2026-08-18"])
check("the dashboard's USDEW close matches S&P Global's at those 69 sessions to the cent",
      all(abs(Decimal(dash[d]["usdew_close"]) - usdew[d]) < Decimal("0.005") for d in w_sessions))
rows = []
for d in sessions:
    sh = Decimal(dash[d]["shares_outstanding"])
    ena_value = tokens * k4[d]
    ena_ps = ena_value / sh
    rows.append({"date": d, "usde_close": usde[d], "ena_price_20utc": k4[d], "class_a_shares": sh,
                 "ena_value": ena_value, "ena_per_share": ena_ps, "book_per_share": bv_share,
                 "price_to_book": usde[d] / bv_share, "mnav": usde[d] / ena_ps,
                 "carrying_per_share": ena_net / sh})
first_above = next(r for r in rows if r["usde_close"] > bv_share)
after = [r for r in rows if r["date"] >= first_above["date"]]
check("USDE stayed above June 30 book value per share at every close from its first close above it",
      all(r["usde_close"] > bv_share for r in after), f"from {first_above['date']}, {len(after)} sessions")
lo_pb = min(rows, key=lambda r: r["price_to_book"])
hi_pb = max(rows, key=lambda r: r["price_to_book"])
hi_ena = max(rows, key=lambda r: r["ena_per_share"])
check("USDE closed below token NAV per share at every session", all(r["mnav"] < 1 for r in rows))
j30, o8 = rows[0], rows[-1]
check("the window runs from June 30 to October 8", j30["date"] == "2026-06-30" and o8["date"] == "2026-10-08")
check("ENA's price at the June 30 and October 8 closes is $0.0707 and $0.2043",
      j30["ena_price_20utc"] == Decimal("0.0707") and o8["ena_price_20utc"] == Decimal("0.2043"))
for r in (j30, first_above, lo_pb, hi_pb, hi_ena, o8):
    say(f"  {r['date']}: USDE {r['usde_close']}, ENA {r['ena_price_20utc']}, ENA per share {r['ena_per_share']:.4f}, "
        f"price to book {r['price_to_book']:.4f}, mNAV {r['mnav']:.4f}")
ratio_oct8 = o8["ena_value"] / ena_net
mnav_dash_count = o8["usde_close"] / (Decimal(3029000000) * o8["ena_price_20utc"] / o8["class_a_shares"])
say(f"  October 8 market value {money(o8['ena_value'])}, {ratio_oct8:.4f} times the carrying value; "
    f"mNAV with 3,029,000,000 ENA {mnav_dash_count:.4f}")
check("token NAV per share at the June 30 close is within 1% of book value per share",
      abs(j30["ena_per_share"] / bv_share - 1) < Decimal("0.01"), f"{j30['ena_per_share']:.4f}")

# ---------------------------------------------------------------- filings after June 30
say()
say("Filings")
fil = read_csv("edgar_filings_2026-10-09.csv")
check("31 filings from June 25 in the list read on October 9", len(fil) == 31)
latest = max(r["filing_date"] for r in fil)
check("no filing after October 2, the five Forms 4", latest == "2026-10-02" and
      sorted(r["form"] for r in fil if r["filing_date"] == latest) == ["4"] * 5)
tenq = [r for r in fil if r["form"] == "10-Q"]
check("one 10-Q since the merger, filed August 14", [r["filing_date"] for r in tenq] == ["2026-08-14"])
check("the 10-Q read is that filing", tenq[0]["accession_number"].replace("-", "") in sources["q2"]["address"].replace("-", ""))
check("the August 24 8-K read is in the list",
      any(r["accession_number"].replace("-", "") in sources["w8k"]["address"] for r in fil if r["form"] == "8-K"))

if FAILED:
    say()
    say(f"{len(FAILED)} check(s) failed. Nothing written.")
    sys.exit(1)

# ---------------------------------------------------------------- write
os.makedirs(OUT, exist_ok=True)
say()
say("All checks passed. Writing out/.")
lines = [
    ("asset", "ENA, at cost less impairment", ena_net),
    ("asset", "Cash", n("cash")),
    ("asset", "Other assets", other_assets),
    ("asset", "Total assets", n("total_assets")),
    ("liability", "Convertible notes owed to former sponsors", notes),
    ("liability", "Accrued expenses", n("accrued_expenses")),
    ("liability", "Warrant liability", n("warrant_liability")),
    ("liability", "Other liabilities", other_liabs),
    ("liability", "Total liabilities", n("total_liabilities")),
    ("equity", "Book value", book),
]
check_assets = sum(v for g, l, v in lines if g == "asset" and not l.startswith("Total"))
check_liabs = sum(v for g, l, v in lines if g == "liability" and not l.startswith("Total"))
assert check_assets == n("total_assets") and check_liabs == n("total_liabilities")
with open(os.path.join(OUT, "balance_sheet.csv"), "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["group", "line", "usd", "usd_millions", "per_class_a_share"])
    for g, l, v in lines:
        w.writerow([g, l, int(v), f"{v / 10**6:.1f}", f"{v / class_a:.4f}"])
with open(os.path.join(OUT, "per_share_by_session.csv"), "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["date", "usde_close", "ena_price_20utc", "class_a_shares", "ena_market_value", "ena_per_class_a_share",
                "book_value_per_class_a_share_june30", "price_to_book", "mnav"])
    for r in rows:
        w.writerow([r["date"], f"{r['usde_close']:.2f}", f"{r['ena_price_20utc']:.4f}", int(r["class_a_shares"]),
                    f"{r['ena_value']:.0f}", f"{r['ena_per_share']:.4f}", f"{r['book_per_share']:.4f}",
                    f"{r['price_to_book']:.4f}", f"{r['mnav']:.4f}"])


def row_out(r):
    return {"date": r["date"], "usde_close": float(r["usde_close"]), "ena_price_20utc": float(r["ena_price_20utc"]),
            "class_a_shares": int(r["class_a_shares"]), "ena_market_value": float(r["ena_value"]),
            "ena_per_share": float(r["ena_per_share"]), "price_to_book": float(r["price_to_book"]),
            "mnav": float(r["mnav"])}


res = {
    "window": [FIRST.isoformat(), LAST.isoformat()],
    "sessions": len(rows),
    "book_value": int(book),
    "class_a_shares_june30": int(class_a),
    "class_b_shares": int(class_b),
    "book_value_per_class_a_share": float(bv_share),
    "book_value_per_class_a_and_b_share": float(bv_share_ab),
    "ena_net_carrying": int(ena_net),
    "ena_per_class_a_share_at_carrying": float(ena_net / class_a),
    "non_ena_net_assets": int(non_ena_net),
    "non_ena_net_assets_per_share": float(non_ena_net / class_a),
    "cash": int(n("cash")),
    "other_assets": int(other_assets),
    "total_liabilities": int(n("total_liabilities")),
    "other_liabilities": int(other_liabs),
    "tokens": str(tokens),
    "ena_cost": str(cost),
    "cost_per_token": float(cost_per_token),
    "carrying_per_token": float(carry_per_token),
    "lot_prices": [float(p) for p in lot_prices],
    "kraken_low_merger_to_june30": [float(low_q2), low_q2_days],
    "kraken_low_q3": [float(low_q3), low_q3_days],
    "q3_low_above_carrying_pct": float((low_q3 / carry_per_token - 1) * 100),
    "release_value": float(rel_value),
    "release_value_per_share": float(rel_per_share),
    "release_less_carrying": float(rel_less_carrying),
    "book_less_release": float(book_less_release),
    "carrying_above_kraken_low": float(carry_per_token - low_q2),
    "warrants_sep30_rise": float(w_rise),
    "warrants_sep30_rise_share_of_book": float(w_rise / book),
    "warrants_june30": float(w_jun30),
    "warrant_price_assumed": float(w_assumed_price),
    "warrants_sep30_at_close": float(w_sep30),
    "usdew_june30": float(usdew["2026-06-30"]),
    "usdew_sep30": float(usdew["2026-09-30"]),
    "sponsor_cash_part": float(cash_part),
    "tranche_a_calc": float(tranche_a_calc),
    "tranche_b_calc": float(tranche_b_calc),
    "director_awards_total": int(awards),
    "june30": row_out(j30),
    "first_close_above_book": row_out(first_above),
    "sessions_above_book": len(after),
    "lowest_price_to_book": row_out(lo_pb),
    "highest_price_to_book": row_out(hi_pb),
    "highest_ena_per_share": row_out(hi_ena),
    "october8": row_out(o8),
    "october8_value_over_carrying": float(ratio_oct8),
    "october8_mnav_with_3029m": float(mnav_dash_count),
    "october8_dashboard_mnav": float(Decimal(dash["2026-10-08"]["mnav"])),
    "october8_dashboard_ena_price": float(Decimal(dash["2026-10-08"]["ena_price"])),
}
with open(os.path.join(OUT, "results.json"), "w") as f:
    json.dump(res, f, indent=2)
    f.write("\n")
with open(os.path.join(OUT, "run_log.txt"), "w") as f:
    f.write("\n".join(LOG) + "\n")
print("wrote out/balance_sheet.csv, out/per_share_by_session.csv, out/results.json, out/run_log.txt")
