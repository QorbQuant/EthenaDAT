#!/usr/bin/env python3
"""Recomputes every computed figure in article_draft.md, metadata.json, layout.json's key findings and the chart's
text from the inputs, with code written apart from reserve_fund_review.py, and checks that each phrase appears where
it should. The Uniswap V3 positions are valued here with decimal arithmetic on square-root prices rather than the
integer tick math of univ3.py. Exits with an error if a phrase is missing or a page rule fails.
Python 3.8 or later, no network."""
import csv
import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal as D, getcontext, ROUND_HALF_UP
from fractions import Fraction as Fr
from pathlib import Path

getcontext().prec = 80
HERE = Path(__file__).parent
CH = HERE / "inputs" / "chain"
WEB = HERE / "inputs" / "web"
ARTICLE = (HERE / "article_draft.md").read_text(encoding="utf-8")
META = json.loads((HERE / "metadata.json").read_text(encoding="utf-8"))
LAYOUT = json.loads((HERE / "layout.json").read_text(encoding="utf-8"))
SVG = (HERE / "out" / "chart_reserve_fund_by_month.svg").read_text(encoding="utf-8")
FAILS, FOUND = [], []


def need(phrase, where="article"):
    text = {"article": ARTICLE, "meta": json.dumps(META, ensure_ascii=False), "findings": " ".join(LAYOUT["keyFindings"]), "svg": SVG}[where]
    if phrase in text:
        FOUND.append((where, phrase))
    else:
        FAILS.append("missing in %s: %s" % (where, phrase))


def rule(ok, msg):
    if not ok:
        FAILS.append(msg)


def rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def r2(x, places=2):
    """Round half up and format with thousands separators. Accepts Fraction or Decimal, either sign."""
    x = D(x.numerator) / D(x.denominator) if isinstance(x, Fr) else D(x)
    q = x.copy_abs().quantize(D(1).scaleb(-places), rounding=ROUND_HALF_UP)
    s = "{:,.{p}f}".format(q, p=places)
    return ("-" if x < 0 and q != 0 else "") + s


def pc(x, places=2):
    return r2(D(x.numerator) / D(x.denominator) * 100 if isinstance(x, Fr) else D(x) * 100, places) + "%"


def when(ts):
    d = datetime.fromtimestamp(int(ts), tz=timezone.utc)
    return "%s %d, %d" % (d.strftime("%B"), d.day, d.year)


def h2i(h):
    return int(h, 16) if h and h.startswith("0x") and len(h) > 2 else 0


def w(h, i):
    return int(h[2 + 64 * i:66 + 64 * i], 16)


def sw(h, i):
    v = w(h, i)
    return v - 2 ** 256 if v >> 255 else v


RF = "0x2b5ab59163a6e93b4486f6055d33ca4a115dd4d5"
T = {"USDC": ("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", 6), "USDT": ("0xdac17f958d2ee523a2206206994597c13d831ec7", 6),
     "DAI": ("0x6b175474e89094c44da98b954eedeac495271d0f", 18), "sDAI": ("0x83f20f44975d03b1b09e64809b757c47f942beea", 18),
     "USDS": ("0xdc035d45d973e3ec169d2276ddab16f1e407384f", 18), "sUSDS": ("0xa3931d71877c0e7a3148cb7eb4463524fec27fbd", 18),
     "USDe": ("0x4c9edd5852cd905f086c759e8383e09bff1e68b3", 18), "sUSDe": ("0x9d39a5de30e57443bff2a8307a4256c8797a3497", 18),
     "USDtb": ("0xc139190f447e929f090edeb554d95abb8b18ac1c", 18), "BUIDL": ("0x7712c34205737192402172409a8f7ccef8aa2aec", 6),
     "USTB": ("0x43415eb6ff9db7e26a15b704e7a3edce97d31c4e", 6), "CurveLP": ("0xc2921134073151490193ac7369313c8e0b08e1e7", 18)}
BY_ADDR = {a: (s, d) for s, (a, d) in T.items()}
PAR = ["USDC", "USDT", "DAI", "USDS", "USDe", "USDtb", "BUIDL"]

snap = {r["call"]: r["result"] for r in rows(CH / "snapshot_reads.csv") if r["rpc"] == "https://eth.drpc.org"}
run = json.loads((CH / "run.json").read_text())
bs = rows(CH / "transfers_blockscout_public.csv")
cls = {r["tx"]: r for r in rows(HERE / "inputs" / "classification.csv")}
mread = {}
for r in rows(CH / "month_reads.csv"):
    mread.setdefault(r["month"], {})[r["call"]] = r["result"]
msrc = {r["month"]: r for r in rows(CH / "month_sources.csv")}


def amt(r):
    s, d = BY_ADDR[r["token"]]
    return s, Fr(int(r["value_raw"]), 10 ** d)


real = [r for r in bs if r["token"] in BY_ADDR or r["token"] == "0xc36442b4a4522e871399cd717abdd847ab11fe88"]


def uni_value(m):
    """Tokens and uncollected fees of the fund's Uniswap positions, from decimal square-root prices."""
    total = D(0)
    for pid in (658523, 658530, 680386, 700726):
        p = m.get("positions %d" % pid, "")
        if not p.startswith("0x") or len(p) < 2 + 64 * 12:
            continue
        L = D(w(p, 7))
        lo, hi = sw(p, 5), sw(p, 6)
        a0 = a1 = D(0)
        f0, f1 = D(w(p, 10)), D(w(p, 11))
        if L:
            s0 = m["Uniswap slot0"]
            sp = D(w(s0, 0)) / D(2 ** 96)
            tick = sw(s0, 1)
            sa = D("1.0001") ** (D(lo) / 2)
            sb = D("1.0001") ** (D(hi) / 2)
            if sp <= sa:
                a0 = L * (1 / sa - 1 / sb)
            elif sp < sb:
                a0 = L * (1 / sp - 1 / sb)
                a1 = L * (sp - sa)
            else:
                a1 = L * (sb - sa)
            out = []
            for k, g in ((2, "Uniswap feeGrowthGlobal0X128"), (3, "Uniswap feeGrowthGlobal1X128")):
                G = int(m[g], 16)
                ol, oh = w(m["ticks %d" % lo], k), w(m["ticks %d" % hi], k)
                below = ol if tick >= lo else G - ol
                above = oh if tick < hi else G - oh
                inside = (G - below - above) % 2 ** 256
                last = w(p, 8 if k == 2 else 9)
                out.append(D(((inside - last) % 2 ** 256) * w(p, 7) // 2 ** 128))
            f0 += out[0]
            f1 += out[1]
        total += (a0 + f0) / D(10) ** 18 + (a1 + f1) / D(10) ** 6
    return total


def value(m, nav=None):
    v = D(0)
    for s in PAR:
        v += D(h2i(m.get("balanceOf " + s, "0x"))) / D(10) ** T[s][1]
    for s in ("sDAI", "sUSDS", "sUSDe"):
        if h2i(m.get("balanceOf " + s, "0x")):
            v += D(h2i(m["convertToAssets " + s])) / D(10) ** 18
    lp = D(h2i(m.get("balanceOf CurveLP", "0x")))
    if lp:
        v += lp / D(h2i(m["Curve totalSupply"])) * (D(h2i(m["Curve balances 0"])) / D(10) ** 6 + D(h2i(m["Curve balances 1"])) / D(10) ** 18)
    ustb = D(h2i(m.get("balanceOf USTB", "0x")))
    if ustb:
        v += ustb / D(10) ** 6 * nav
    v += uni_value(m)
    v += D(int(m["eth_getBalance"], 16)) / D(10) ** 18 * D(sw(m["Chainlink ETH/USD latestRoundData"], 1)) / D(10) ** 8
    return v


# ---- the read block ---------------------------------------------------------------------------------------------
blk, ts = run["read_block"], run["snapshot_blocks"]["https://eth.drpc.org"]["time"]
hms = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%H:%M:%S")
need("Read at Ethereum block {:,}, {} UTC on October 12, 2026".format(blk, hms))
need("held assets worth $%s at Ethereum block {:,}, {} UTC on October 12, 2026, with every stablecoin counted at $1".format(blk, hms) % r2(value(snap)))
V = value(snap)
usde = D(h2i(snap["totalSupply USDe"])) / D(10) ** 18
usdtb_sup = D(h2i(snap["totalSupply USDtb"])) / D(10) ** 18
ub = D(h2i(snap["balanceOf USDtb"])) / D(10) ** 18
lp_share = D(h2i(snap["balanceOf CurveLP"])) / D(h2i(snap["Curve totalSupply"]))
pc0 = D(h2i(snap["Curve balances 0"])) / D(10) ** 6
pc1 = D(h2i(snap["Curve balances 1"])) / D(10) ** 18
lpv = lp_share * (pc0 + pc1)
eth_px = D(sw(snap["Chainlink ETH/USD latestRoundData"], 1)) / D(10) ** 8
ethv = D(int(snap["eth_getBalance"], 16)) / D(10) ** 18 * eth_px
small = D(h2i(snap["balanceOf USDS"])) / D(10) ** 18 + D(h2i(snap["balanceOf BUIDL"])) / D(10) ** 6 + D(h2i(snap["balanceOf USDC"])) / D(10) ** 6
need("That was %s of USDe's total supply of %s." % (pc(V / usde), r2(usde)))
need("The fund held %s USDtb and %s of a pool of USDtb and USDC on Curve" % (r2(ub), pc(lp_share, 4)))
need("The pool share was worth $%s." % r2(lpv))
held_usdtb = ub + lp_share * pc1
need("USDtb, held directly and through the pool, made up %s of the fund." % pc(held_usdtb / V))
need("| USDtb | %s | $%s | %s |" % (r2(ub), r2(ub), pc(ub / V)))
need("| Curve pool share, USDtb | %s | $%s | %s |" % (r2(lp_share * pc1), r2(lp_share * pc1), pc(lp_share * pc1 / V)))
need("| Curve pool share, USDC | %s | $%s | %s |" % (r2(lp_share * pc0), r2(lp_share * pc0), pc(lp_share * pc0 / V)))
need("| ETH | 0.3 | $%s | under 0.01%% |" % r2(ethv))
need("| USDS, BUIDL and USDC | %s | $%s | under 0.01%% |" % (r2(small), r2(small)))
need("| Total | | $%s | 100.00%% |" % r2(V))
rule(ethv / V < D("0.0001") and small / V < D("0.0001"), "small lines under 0.01%")
lp_sup = D(h2i(snap["Curve totalSupply"])) / D(10) ** 18
need("At the read block the pool had issued %s, so the fund owned all but %s of it." % (r2(lp_sup), pc(1 - lp_share, 4)))
need("The fund's share was worth $%s more than the coins put in, a gain of %s in 22 months." % (r2(lpv - 19980948), pc((lpv - 19980948) / 19980948)))
need("ETH is valued at $%s, the ETH/USD price that Chainlink's price feed on Ethereum last updated at %s UTC." % (r2(eth_px), datetime.fromtimestamp(w(snap["Chainlink ETH/USD latestRoundData"], 3), tz=timezone.utc).strftime("%H:%M")))
need("The fund's %s USDtb, held directly and through the pool, were %s of USDtb's total supply on Ethereum of %s." % (r2(held_usdtb), pc(held_usdtb / usdtb_sup), r2(usdtb_sup)))
need("held $%s with stablecoins at $1, equal to %s of USDe's supply. USDtb, held directly and through a Curve pool, made up %s of it." % (r2(V), pc(V / usde), pc(held_usdtb / V)), "findings")
need("held $%s million on October 12, 2026, or %s of USDe's supply. USDtb, held directly and in a Curve pool, was %s of it." % (r2(V / 10 ** 6), pc(V / usde), pc(held_usdtb / V)), "meta")
need("it was worth %s million dollars" % r2(V / 10 ** 6), "svg")
need("`0x2b5ab59163a6e93b4486f6055d33ca4a115dd4d5`")

# ---- the sources of the value ------------------------------------------------------------------------------------
cat_sum, cat_n, first, last = {}, {}, {}, {}
for r in real:
    if r["token"] not in BY_ADDR:
        continue
    s, a = amt(r)
    c = cls[r["tx"]]["category"]
    if s in PAR:
        cat_sum[c] = cat_sum.get(c, Fr(0)) + (a if r["to"] == RF else -a)
    cat_n[c] = cat_n.get(c, 0) + 1
    t = int(r["time_unix"])
    first[c] = min(first.get(c, t), t)
    last[c] = max(last.get(c, t), t)
fr_lpv = Fr(h2i(snap["balanceOf CurveLP"]), h2i(snap["Curve totalSupply"])) * (Fr(h2i(snap["Curve balances 0"]), 10 ** 6) + Fr(h2i(snap["Curve balances 1"]), 10 ** 18))
fr_eth = Fr(int(snap["eth_getBalance"], 16), 10 ** 18) * Fr(sw(snap["Chainlink ETH/USD latestRoundData"], 1), 10 ** 8)
cat_sum["curve"] += fr_lpv
total = sum(cat_sum.values()) + fr_eth
rule(r2(total) == r2(V), "the sources add up to the value: %s vs %s" % (r2(total), r2(V)))
need("sent the fund $%s in %d transfers from %s to %s" % (r2(cat_sum["payout"]), cat_n["payout"], when(first["payout"]).replace(", 2024", ""), when(last["payout"])))
need("| sUSDe Payout Fund, %d transfers | %s to %s | %s |" % (cat_n["payout"], when(first["payout"]).replace(", 2024", ""), when(last["payout"]), r2(cat_sum["payout"])))
need("| Safe `0xa2af…cced92`, %d transfers | %s to %s | %s |" % (cat_n["safe_a"], when(first["safe_a"]).replace(", 2024", ""), when(last["safe_a"]), r2(cat_sum["safe_a"])))
for r in [r for r in real if cls[r["tx"]]["category"] == "other_in"]:
    s, a = amt(r)
    need("| An address that is not a contract, %s %s | %s | %s |" % (r2(a, 0), s, when(r["time_unix"]), r2(a)))
three = cat_sum["safe_a"] + cat_sum["other_in"]
need("and two addresses that are not contracts, none of them named on the key addresses page, sent $%s." % r2(three))
need("and a second Safe and two other addresses sent $%s." % r2(three), "findings")
need("the two addresses that sent $%s" % r2(cat_sum["other_in"]))
paid = cat_sum["payout"] + cat_sum["safe_a"] + cat_sum["other_in"]
need("| Paid in | | %s |" % r2(paid))
lines_ = {"savings": "sDAI and sUSDS savings vaults", "interest": "USDtb interest, %d transfers" % cat_n["interest"],
          "uniswap": "Uniswap V3 USDe/USDT positions", "ustb": "Superstate's USTB fund", "curve": "Curve USDtb/USDC pool", "buidl": "BUIDL",
          "usdtb_mint": "USDtb minted for BUIDL and USDC", "swap": "Swaps through CoW Protocol and Curve's router", "safe_b": "Conversions through Safe `0x4423…9d9d`"}
for c, name in lines_.items():
    need("| %s | " % name)
    need(" | %s |" % r2(cat_sum[c]))
earned = sum(cat_sum[c] for c in ("savings", "interest", "uniswap", "ustb", "curve", "buidl"))
costs = sum(cat_sum[c] for c in ("usdtb_mint", "swap", "safe_b"))
need("| Earned | | %s |" % r2(earned))
need("| Costs | | %s |" % r2(costs))
need("| ETH, and transfers under 1 USDC | | %s |" % r2(fr_eth + cat_sum["dust"]))
need("| Total | | %s |" % r2(total))
need("earned $%s, and minting USDtb, swaps and conversions cost $%s." % (r2(earned), r2(-costs)))
need("The fund's positions and the interest on its USDtb earned $%s, and minting USDtb, swaps and conversions cost $%s." % (r2(earned), r2(-costs)), "findings")
need("paid in       = %s + %s + 10,000,000 + 3,239,921\n              = %s" % (r2(cat_sum["payout"], 3), r2(cat_sum["safe_a"], 3), r2(paid)))
need("earned        = %s + %s + %s + %s + %s + %s\n              = %s" % tuple([r2(cat_sum[c], 3) for c in ("savings", "interest", "uniswap", "ustb", "curve", "buidl")] + [r2(earned)]))
need("costs         = %s - %s - %s\n              = %s" % (r2(cat_sum["usdtb_mint"], 3), r2(-cat_sum["swap"], 3), r2(-cat_sum["safe_b"], 3), r2(costs)))
need("total         = %s + %s - %s + %s\n              = %s" % (r2(paid), r2(earned), r2(-costs), r2(fr_eth + cat_sum["dust"]), r2(total)))
need("from February 2 to December 12, 2024", "findings")
need("The sUSDe Payout Fund sent the fund $%s" % r2(cat_sum["payout"]), "findings")
need("wrote that the fund had received no allocation since %s and $%s million before it" % (when(last["payout"]), r2(cat_sum["payout"] / 10 ** 6, 1)))

# Savings, Uniswap, USTB, BUIDL, minting, interest.
dai_in = sum(amt(r)[1] for r in real if r["tx"] == "tx-17")
need("On March 14, 2024, %s DAI went into sDAI." % r2(dai_in))
need("| March 14, 2024 | %s DAI went into sDAI |" % r2(dai_in))
proceeds = sum(amt(r)[1] for r in real if cls[r["tx"]]["category"] == "savings" and r["to"] == RF and amt(r)[0] in PAR)
need("in August and September 2025 for $%s" % r2(proceeds))
rule(proceeds - dai_in == cat_sum["savings"], "savings proceeds less DAI")
ev = rows(CH / "events.csv")
col = [e for e in ev if " Collect " in e["event"]]
dec = [e for e in ev if "DecreaseLiquidity" in e["event"]]
inc = [e for e in ev if "IncreaseLiquidity" in e["event"]]
fees = sum(Fr(w(e["data"], 1), 10 ** 18) + Fr(w(e["data"], 2), 10 ** 6) for e in col) - sum(Fr(w(e["data"], 1), 10 ** 18) + Fr(w(e["data"], 2), 10 ** 6) for e in dec)
need("they earned $%s in fees" % r2(fees))
need("| January 25 to April 2, 2024 | %s USDe and %s USDT went into four Uniswap V3 positions |" % (r2(sum(Fr(w(e["data"], 1), 10 ** 18) for e in inc)), r2(sum(Fr(w(e["data"], 2), 10 ** 6) for e in inc))))
dec13 = [e for e in col if e["block"] in ("21393114", "21393132", "21393151", "21393178")]
need("| December 13 to 24, 2024 | %s USDe and USDT came out of the Uniswap positions" % r2(sum(Fr(w(e["data"], 1), 10 ** 18) + Fr(w(e["data"], 2), 10 ** 6) for e in dec13)))
ustb_rows = [r for r in real if cls[r["tx"]]["category"] == "ustb"]
buy_usdc = sum(amt(r)[1] for r in ustb_rows if r["tx"] in ("tx-87", "tx-91"))
buy_ustb = sum(amt(r)[1] for r in ustb_rows if r["tx"] in ("tx-88", "tx-93"))
sell_usdc = sum(amt(r)[1] for r in ustb_rows if r["tx"] in ("tx-111", "tx-113"))
need("USTB shares, %s of them, were bought in February 2025 for an average %s USDC each and redeemed for %s USDC each on August 26, 2025" % (
    r2(buy_ustb), r2(buy_usdc / buy_ustb, 4), r2(sell_usdc / buy_ustb, 4)))
need("The last Uniswap position was emptied and %s USTB were bought" % r2(buy_ustb))


def tx_sum(txs, sym, direction):
    return sum(amt(r)[1] for r in real if r["tx"] in txs and r["token"] in BY_ADDR and amt(r)[0] == sym and ((r["to"] == RF) == (direction == "in")))


bx = {"tx-60", "tx-61", "tx-62", "tx-66"}
mint_txs = {t for t, c in cls.items() if c["category"] == "usdtb_mint"}
usdc_m, usdtb_m = tx_sum(mint_txs, "USDC", "out"), tx_sum(mint_txs - bx, "USDtb", "in")
buidl_m, usdtb_b = tx_sum(bx, "BUIDL", "out"), tx_sum(bx, "USDtb", "in")
dec_m = {t for t in mint_txs if cls[t]["episode"].startswith("2024-12")}
sep_m = {t for t in mint_txs if cls[t]["episode"].startswith("2025-09")}
rule(dec_m | sep_m == mint_txs and not dec_m & sep_m and bx <= dec_m, "the mints fall in December 2024 and September 2025")
dec_in = tx_sum(dec_m, "BUIDL", "out") + tx_sum(dec_m, "USDC", "out")
sep_in = tx_sum(sep_m, "USDC", "out")
rule(tx_sum(sep_m, "BUIDL", "out") == 0, "no BUIDL in September 2025")
need("USDtb was minted for %s less than the BUIDL and USDC exchanged for it in December 2024, and for $%s less than the %s USDC exchanged for it in September 2025." % (
    pc((dec_in - tx_sum(dec_m, "USDtb", "in")) / dec_in, 1), r2(sep_in - tx_sum(sep_m, "USDtb", "in")), r2(sep_in, 0)))
rule(tx_sum(dec_m, "USDC", "out") + sep_in == usdc_m and tx_sum(bx, "BUIDL", "out") == buidl_m, "mint totals")
need("On October 11, 2024, %s USDC went to BUIDL's contract for %s BUIDL, and on November 1, 2024 the fund received %s new BUIDL with no payment." % (
    r2(tx_sum({"tx-47"}, "USDC", "out"), 0), r2(tx_sum({"tx-48"}, "BUIDL", "in"), 0), r2(tx_sum({"tx-54"}, "BUIDL", "in"))))
rule(cat_sum["buidl"] == tx_sum({"tx-48", "tx-54"}, "BUIDL", "in") - tx_sum({"tx-47"}, "USDC", "out"), "BUIDL line is the dividend less the purchase shortfall")
irows = sorted((r for r in real if cls[r["tx"]]["category"] == "interest"), key=lambda r: int(r["time_unix"]))
rule(len(irows) == 9 and len({r["from"] for r in irows}) == 2 and all(r["from"].startswith("eoa-") for r in irows), "nine interest transfers from two addresses")
need("The nine USDtb transfers came from two addresses that are not contracts.")
l3 = irows[-3:]
need("The last three, of %s and %s USDtb on %s and %s USDtb on %s" % (r2(amt(l3[0])[1], 0), r2(amt(l3[1])[1]), when(l3[1]["time_unix"]), r2(amt(l3[2])[1]), when(l3[2]["time_unix"])))
mint_cp = {r["to"] for r in real if r["tx"] in mint_txs and r["from"] == RF}
rule(len(mint_cp) == 1 and all(r["from"] in mint_cp for r in irows[:6]), "the six earlier interest transfers came from the address that received the BUIDL and USDC for USDtb")
need("The six earlier ones came from the address that also received the BUIDL and USDC exchanged for USDtb")
need("| USDtb interest, %d transfers | %s to %s | %s |" % (len(irows), when(irows[0]["time_unix"]).replace(", 2025", ""), when(irows[-1]["time_unix"]), r2(cat_sum["interest"])))
need("| November 3, 2025 | %s USDtb arrived, the last incoming transfer |" % r2(amt(irows[-1])[1]))
need("No asset arrived after %s" % when(max(int(r["time_unix"]) for r in bs)), "findings")
need("No asset arrived after %s" % when(max(int(r["time_unix"]) for r in bs)))

# ---- the timeline ------------------------------------------------------------------------------------------------
need("| January 24, 2024 | %s USDe, %s USDT and %s USDC arrived from Safe" % (r2(tx_sum({"tx-1"}, "USDe", "in"), 0), r2(tx_sum({"tx-1"}, "USDT", "in")), r2(tx_sum({"tx-1"}, "USDC", "in"), 0)))
need("| October 10 and 11, 2024 | %s USDT was swapped for USDC, and %s USDC went to BUIDL's contract for %s BUIDL |" % (
    r2(tx_sum({"tx-41", "tx-42", "tx-43", "tx-44"}, "USDT", "out"), 0), r2(tx_sum({"tx-47"}, "USDC", "out"), 0), r2(tx_sum({"tx-48"}, "BUIDL", "in"), 0)))
mig = sum(Fr(w(e["data"], 1), 10 ** 18) for e in ev if e["event"] == "sDAI Withdraw")
dep = sum(Fr(w(e["data"], 1), 10 ** 18) for e in ev if e["event"] == "sDAI Deposit")
need("| October 15 to 31, 2024 | %s of the fund's %s sDAI moved into sUSDS |" % (r2(mig, 0), r2(dep)))
need("%s BUIDL and %s USDC were exchanged for USDtb, and %s USDC and %s USDtb went into the Curve pool |" % (
    r2(buidl_m, 0), r2(tx_sum({"tx-68", "tx-69"}, "USDC", "out"), 0), r2(tx_sum({"tx-65"}, "USDC", "out"), 0), r2(tx_sum({"tx-65"}, "USDtb", "out"), 0)))
need("%s LP tokens reached the fund on December 15, 2024 for %s USDC and %s USDtb" % (r2(tx_sum({"tx-65"}, "CurveLP", "in"), 0), r2(tx_sum({"tx-65"}, "USDC", "out"), 0), r2(tx_sum({"tx-65"}, "USDtb", "out"), 0)))
need("and %s USDC was exchanged for USDtb |" % r2(tx_sum({"tx-117", "tx-119", "tx-121", "tx-123", "tx-125", "tx-127", "tx-130"}, "USDC", "out"), 0))

# ---- month ends -------------------------------------------------------------------------------------------------
t1 = int([r for r in real if r["tx"] == "tx-93"][0]["time_unix"])
t2 = int([r for r in real if r["tx"] == "tx-113"][0]["time_unix"])
p1 = D(buy_usdc.numerator) / D(buy_usdc.denominator) / (D(buy_ustb.numerator) / D(buy_ustb.denominator))
p2 = D(sell_usdc.numerator) / D(sell_usdc.denominator) / (D(buy_ustb.numerator) / D(buy_ustb.denominator))
MV = {}
for m in sorted(mread):
    tm = int(msrc[m]["block_time_unix"])
    MV[m] = value(mread[m], p1 + (p2 - p1) * D(tm - t1) / D(t2 - t1))
rule(all(MV[b] > MV[a] for a, b in zip(sorted(MV), sorted(MV)[1:])) and V > MV["2026-09"], "value rose at every month end")
main_me = {r["month"]: r["total_usd"] for r in rows(HERE / "out" / "month_end.csv")}
bad = [m for m in MV if r2(MV[m]).replace(",", "") != main_me[m]]
rule(not bad and len(MV) == 33, "this script's month-end values equal the main script's to the cent: " + ", ".join(bad))
need("and its value rose from every month end to the next")
names = {"2024-02": "February 2024", "2024-12": "December 2024", "2025-09": "September 2025", "2026-03": "March 2026", "2026-09": "September 2026"}
for m, n in names.items():
    us = D(h2i(mread[m]["totalSupply USDe"])) / D(10) ** 18
    need("| %s | $%s | %s | %s |" % (n, r2(MV[m]), r2(us), pc(MV[m] / us)))
need("| October 12, 2026 read block | $%s | %s | %s |" % (r2(V), r2(usde), pc(V / usde)))
ratios = {m: MV[m] / (D(h2i(mread[m]["totalSupply USDe"])) / D(10) ** 18) for m in MV}
rule(max(ratios, key=ratios.get) == "2024-02" and min(ratios, key=ratios.get) == "2025-09", "largest and smallest share months")
need("The fund's value reached $%s at the end of December 2024 and grew %s%% from then to the end of September 2026" % (r2(MV["2024-12"]), r2((MV["2026-09"] / MV["2024-12"] - 1) * 100, 0)))
need("and grew %s%% by September 2026" % r2((MV["2026-09"] / MV["2024-12"] - 1) * 100, 0), "svg")
m9 = mread["2025-09"]
lp9 = D(h2i(m9["balanceOf CurveLP"])) / D(h2i(m9["Curve totalSupply"])) * (D(h2i(m9["Curve balances 0"])) / D(10) ** 6 + D(h2i(m9["Curve balances 1"])) / D(10) ** 18)
eth9 = D(int(m9["eth_getBalance"], 16)) / D(10) ** 18 * D(sw(m9["Chainlink ETH/USD latestRoundData"], 1)) / D(10) ** 8
rule(abs((V - MV["2025-09"]) - (D("169048.07") + (lpv - lp9) + (ethv - eth9))) < D("1e-12"), "the rise since September 2025 is the interest, the pool and ETH")
need("From the end of September 2025 to the read block it rose $%s. The last interest transfer added %s USDtb and the pool share gained $%s, while a lower ETH price cut the value of the fund's 0.3 ETH by $%s." % (
    r2(V - MV["2025-09"]), r2(amt(irows[-1])[1]), r2(lpv - lp9), r2(eth9 - ethv)))
need("It rose from %s in January 2024 to %s in December 2024 and %s in September 2026" % (r2(MV["2024-01"] / 10 ** 6, 1), r2(MV["2024-12"] / 10 ** 6, 1), r2(MV["2026-09"] / 10 ** 6, 1)), "meta")
need("It rose from %s in January 2024 to %s in November 2024 and %s in December 2024, and stayed between %s and %s from January 2025 to September 2026." % (
    r2(MV["2024-01"] / 10 ** 6, 1), r2(MV["2024-11"] / 10 ** 6, 1), r2(MV["2024-12"] / 10 ** 6, 1),
    r2(min(v for m, v in MV.items() if m >= "2025-01") / 10 ** 6, 1), r2(max(v for m, v in MV.items() if m >= "2025-01") / 10 ** 6, 1)))
for m in ("2024-12", "2026-09"):
    rule(">%s</text>" % r2(MV[m] / 10 ** 6, 1) in SVG, "chart label " + m)
for r in rows(HERE / "out" / "month_end.csv"):
    rule("Total %s million dollars" % r2(D(r["total_usd"]) / 10 ** 6) in SVG, "chart hover total " + r["month"])


def u_share(m):
    d = mread[m]
    direct = D(h2i(d["balanceOf USDtb"])) / D(10) ** 18
    pool = D(h2i(d["balanceOf CurveLP"])) / D(h2i(d["Curve totalSupply"])) * D(h2i(d["Curve balances 1"])) / D(10) ** 18 if h2i(d.get("balanceOf CurveLP", "0x")) else D(0)
    return (direct + pool) / MV[m]


win = [m for m in MV if "2024-12" <= m <= "2025-08"]
top = max(win, key=u_share)
rule(u_share(top) < D("0.5"), "USDtb under 50% from December 2024 to August 2025")
need("stayed below 50%% at every month end from December 2024 to August 2025, at most %s in %s" % (pc(u_share(top)), datetime.strptime(top, "%Y-%m").strftime("%B %Y")))
need("USDtb was %s of the fund at the end of September 2025" % pc(u_share("2025-09")))
oct_buidl = D(h2i(mread["2024-10"]["balanceOf BUIDL"])) / D(10) ** 6
need("BUIDL was bought the next day, worth %s of the fund at the end of October 2024" % pc(oct_buidl / MV["2024-10"]))
sdai_aug = D(h2i(mread["2025-08"]["convertToAssets sDAI"])) / D(10) ** 18
need("worth $%s at the end of August 2025" % r2(sdai_aug))

# ---- published figures ------------------------------------------------------------------------------------------
cmp_rows = rows(HERE / "out" / "risk_committee_comparison.csv")
usdtb_direct_v = ub
higher = [r for r in cmp_rows if D(r["onchain_usd"]) - D(r["published_usd"]) < D("-300000")]
others = [r for r in cmp_rows if r not in higher]


def beyond(r):
    pub, mine = D(r["published_usd"]), D(r["onchain_usd"])
    return max(D(0), abs(mine - pub) - D(r["published_precision_musd"]) * 10 ** 6 / 2) / pub


gaps = [beyond(r) for r in others]
rule(len(cmp_rows) == 35 and len({r["source"] for r in cmp_rows}) == 35 and len(higher) == 3 and max(gaps) < D("0.0035"), "published figures and gaps")
rule(all(D(r["beyond_rounding_pct"]) == D(pc(beyond(r), 3)[:-1]) for r in cmp_rows), "gap beyond rounding as the file gives it")
need("The review compared %d published figures for the fund or one of its holdings, from April 2025 to July 2026, with the onchain value at the nearest month end or on the same date." % len(cmp_rows))
need("Allowing for the rounding of each published figure, %d came within 0.35%% of the onchain value and %d within 0.1%%." % (
    len(others), sum(1 for g in gaps if g < D("0.001"))))
need("The other %s were higher." % {3: "three"}[len(higher)])
# The onchain values of the comparison, recomputed here where the basis is a month end of the whole fund, the
# pool position or a vault, or the USDtb balance held from November 3, 2025.
for r in cmp_rows:
    b = r["onchain_basis"]
    if b.startswith("month end ") and r["item"] == "fund":
        rule(r2(MV[b[10:17]]) == r2(D(r["onchain_usd"])), "comparison value " + r["source"])
    elif b.startswith("month end ") and r["item"] == "pool":
        d = mread[b[10:17]]
        pool = D(h2i(d["balanceOf CurveLP"])) / D(h2i(d["Curve totalSupply"])) * (D(h2i(d["Curve balances 0"])) / D(10) ** 6 + D(h2i(d["Curve balances 1"])) / D(10) ** 18)
        rule(r2(pool) == r2(D(r["onchain_usd"])), "comparison value " + r["source"])
    elif b.startswith("month end ") and r["item"] in ("sDAI", "sUSDS"):
        rule(r2(D(h2i(mread[b[10:17]]["convertToAssets " + r["item"]])) / D(10) ** 18) == r2(D(r["onchain_usd"])), "comparison value " + r["source"])
    elif b == "balance from November 3, 2025 to the read block":
        rule(r2(D(r["onchain_usd"])) == r2(usdtb_direct_v), "comparison value " + r["source"])
# Each published figure as the forum passages give it.
forum_flat = " ".join((WEB / "ethena_governance_forum_2026-10-12.txt").read_text(encoding="utf-8").split())
PUBLISHED_AS = {
    "T555 Ethena Labs proposal": "put the fund at $60.9m", "T555 LlamaRisk reply, its dashboard, USTB": "USTB $5.2m",
    "T555 LlamaRisk reply, its dashboard, USDtb": "USDtb $19.2m", "T555 LlamaRisk reply, its dashboard, Curve pool position": "Curve USDtb-USDC LP $20m",
    "T555 LlamaRisk reply, its dashboard, sUSDS": "sUSDS $14.1m", "T555 LlamaRisk reply, its dashboard, sDAI": "sDAI $2.3m",
    "T613 governance update for June 2025": "Reserve Fund $61.1M", "T670 governance update for July 2025": "Reserve Fund $61.2 million",
    "T685 USDtb in the wallet": "$19,710,412 USDtb", "T685 USTB": "$5,319,310 USTB", "T685 Curve pool position": "Curve USDtb-USDC pool $19,995,255",
    "T685 sUSDS": "sUSDS $14,328,881", "T689 governance update for August 2025": "$61.7M in another",
    "T689 governance update for August 2025, other passage": "Reserve Fund $62M in one passage", "T703 total": "about $61.84M",
    "T703 USDtb": "$41.8M of USDtb", "T703 Curve pool position": "pool position of $19.9M", "T704 governance update for September 2025": "Reserve Fund $62m",
    "T709 total": "About $61.88M", "T727 total": "About $62.08M", "T734 governance update for December 2025": "Reserve Fund $62.09 million",
    "T748 total": "About $62M, linked", "T748 USDtb": "USDtb $41.93M", "T748 Curve pool position": "USDtb-USDC $19.99M",
    "T753 governance update, summary": "$62.51 million in the summary", "T753 governance update, body": "$62.54 million in the body",
    "T775 total": "About $62M: USDtb $41.98M", "T775 USDtb": "USDtb $41.98M and USDtb-USDC $20.02M, from LlamaRisk's dashboard of April 2",
    "T775 Curve pool position": "USDtb-USDC $20.02M, from LlamaRisk's dashboard of April 2",
    "T791 attestation of April 23, 2026": "at $62.04M on April 23, 2026", "T791 attestation of April 23, 2026, USDtb": "being $41.98M in USDtb",
    "T791 attestation of April 23, 2026, Curve pool position": "$20.02M in the USDtb/USDC pool position", "T791 attestation of April 30, 2026": "$62.06M on April 30, 2026",
    "T796 governance update for May 2026": "Reserve Fund balance was $62.5M", "T808 governance update for June 2026": "about $62.0M",
}
rule(set(PUBLISHED_AS) == {r["source"] for r in cmp_rows}, "every compared figure has its passage")
for r in cmp_rows:
    ph = PUBLISHED_AS.get(r["source"], "")
    num = ph.split("$")[1].split(" ")[0].rstrip(",:.").replace(",", "") if "$" in ph else "x"
    mult = 10 ** 6 if num[-1] in "mM" or "million" in ph.split("$")[1][:20] else 1
    val = D(num.rstrip("mM")) * mult
    rule(ph in forum_flat and val == D(r["published_usd"]), "published figure %s as the passage gives it" % r["source"])
hg = sorted(D(r["published_usd"]) - D(r["onchain_usd"]) for r in higher)
need("$%s million to $%s million more than the fund held at the nearest month end" % (r2(hg[0] / 10 ** 6), r2(hg[-1] / 10 ** 6)))
att = [r for r in cmp_rows if r["source"].startswith("T791") and r["item"] == "fund"]
rule(all(abs(D(r["onchain_usd"]) - D(r["published_usd"])) < D("25000") for r in att), "attestations in line")
forum = (WEB / "ethena_governance_forum_2026-10-12.txt").read_text(encoding="utf-8")
for phrase in ["BUIDL (Securitize/BlackRock) 40%, USDS (Sky) 29%, USDM (Mountain) 16.5%, USTB", "(Superstate) 14.5%", "the same underlying assets",
               "cash, US Treasury bills and repurchase agreements", "as new tokens each month", "$62.51 million", "$62.54 million", "$62.5M",
               "$62.00M to $62.07M on the 11 dates from February", "and at $62.06M on April 30, 2026", "Chaos Labs' proof-of-reserves",
               "approved but later abandoned", "since 12 December 2024", "$35.7M", "about 169k USDtb", "103k and 500 USDtb", "a floor of about $14M",
               "not to exceed 50% of the fund's capital", "consolidate all Reserve Fund assets into USDtb", "The list named no sDAI", "$41.93M", "$41.98M",
               "$61.84M", "Maker's move to Sky"]:
    rule(phrase in forum, "forum passage missing " + phrase)
toks = rows(CH / "tokens_public.csv")
rule("USDM" not in {t["symbol"].strip().upper() for t in toks}, "no USDM")
docs = (WEB / "ethena_reserve_fund_docs_2026-10-12.txt").read_text(encoding="utf-8")
for phrase in ["put that share at 0% at present", "the Reserve Fund 0x2b5ab59163a6e93b4486f6055d33ca4a115dd4d5, with 4/10 signers",
               "a page saying that access was", "It did not name the Safes 0xa2af0b03aaf167cfc9624c6ef587581b6fcced92",
               "Ethena Labs Research sits", "Blockworks Advisory, LlamaRisk and Kairos", "distributes USDe to the staking rewards"]:
    rule(phrase in docs, "docs passage missing " + phrase)
carried = (WEB / "usde_chain_review_carried_2026-10-12.txt").read_text(encoding="utf-8")
rule("locks USDe on Ethereum" in carried and "counts the USDe locked" in carried, "carried USDe passage")

# ---- other counts -----------------------------------------------------------------------------------------------
rs = rows(CH / "transfers_routescan_public.csv")
need("Blockscout listed %d token transfers of the fund and Routescan %d." % (len(bs), len(rs)))
need("Routescan missed one transfer of %s USDT from the sUSDe Payout Fund" % r2(amt([r for r in bs if r["tx"] == "tx-29"][0])[1], 0))
need("The review grouped the %d transactions" % len(cls))
listed = set(BY_ADDR) | {"0xc36442b4a4522e871399cd717abdd847ab11fe88"}
unl_in = [r for r in bs if r["token"] not in listed and r["to"] == RF]
unl_out = [r for r in bs if r["token"] not in listed and r["from"] == RF]
unl_either = {r["token"] for r in bs + rs if r["token"] not in listed}
need("It left out %d other tokens listed for the fund by two explorers, websites that index a chain's records." % len(unl_either))
need("The %d other tokens are not valued." % len(unl_either))
need("Routescan listed the other %d." % len(unl_either - {r["token"] for r in bs if r["token"] not in listed}))
need("In Blockscout's list, %d of them were sent to the fund and never left it" % len({r["token"] for r in unl_in}))
rule(len(unl_in) == len({r["token"] for r in unl_in}) and not ({r["token"] for r in unl_in} & {r["token"] for r in unl_out}), "untracked tokens never left")
need("and %d are tokens named like USDC, from contracts other than USDC's, whose %d transfers appear as sent from the fund" % (len({r["token"] for r in unl_out}), len(unl_out)))
rule({r["token"] for r in bs if r["token"] not in listed} == {r["token"] for r in unl_in} | {r["token"] for r in unl_out}, "Blockscout's untracked tokens are the 17 and the 5")
syn = [r for r in unl_in if r["token"] == "0x1bab804803159ad84b8854581aa53ac72455614e"]
need("including %s SYND" % r2(Fr(int(syn[0]["value_raw"]), 10 ** 18), 0))
once = {r["call"]: r["result"] for r in rows(CH / "once_reads.csv")}
rule(int(once["getThreshold"], 16) == 4 and once["getOwners count"] == "10", "Safe 4 of 10")
need("here 4 of its 10")
log = (HERE / "out" / "run_log.txt").read_text(encoding="utf-8")
n_checks = int(re.search(r"^all (\d+) checks passed$", log, re.M).group(1))
need("if any of its %d checks fails" % n_checks)
need("Two RPCs gave the same answers to all %d reads at block %s." % (len([r for r in rows(CH / "snapshot_reads.csv") if r["rpc"] == "https://eth.drpc.org"]), "{:,}".format(blk)))
need("Their answers matched for all %d months." % sum(1 for r in msrc.values() if r["same"] == "1"))

# ---- code block -------------------------------------------------------------------------------------------------
need("value         = %s USDtb" % r2(ub, 3))
need("+ 19,980,948 / %s x (%s USDC + %s USDtb)" % (r2(lp_sup, 3), r2(pc0, 3), r2(pc1, 3)))
need("+ 0.3 ETH x %s + %s USDS + 1.5 BUIDL + %s USDC" % (r2(eth_px), r2(D(h2i(snap["balanceOf USDS"])) / D(10) ** 18, 3), r2(D(h2i(snap["balanceOf USDC"])) / D(10) ** 6, 3)))
need("= %s + %s + %s" % (r2(ub, 3), r2(lpv, 3), r2(ethv + small, 3)))
need("USDtb share   = (%s + %s) / %s" % (r2(ub, 3), r2(lp_share * pc1, 3), r2(V)))

# ---- page rules -------------------------------------------------------------------------------------------------
lines = ARTICLE.split("\n")
rule(sum(1 for l in lines if l.startswith("# ")) == 1 and lines[0] == "# " + META["headline"], "one H1, the metadata headline")
rule(len(META["title"]) <= 60 and 120 <= len(META["description"]) <= 160, "title and description lengths")
rule("[Qorban Ferrell · @Degenerate\\_DeFi](https://ethenadash.com/about/) · Published " + datetime.fromisoformat(META["datePublished"]).strftime("%d %B %Y") in ARTICLE, "byline with author link and date")
rule(ARTICLE.rstrip().endswith("Analysis of public blockchain data. Not investment advice."), "closing line")
svg_text = " ".join(re.findall(r">([^<>]+)<", SVG))
readme = (HERE / "README.md").read_text(encoding="utf-8")
for bad_ in ["—", "–", ";", "This article", "on-chain", "FAQ"]:
    rule(bad_ not in ARTICLE, "forbidden text in article: %r" % bad_)
    rule(bad_ not in " ".join(LAYOUT["keyFindings"]) + META["description"] + META["imageAlt"] + LAYOUT["cutoff"] + LAYOUT["chartLabel"], "forbidden text in metadata or layout: %r" % bad_)
    rule(bad_ not in svg_text, "forbidden text in the chart's text: %r" % bad_)
for bad_ in ["—", "–"]:
    rule(bad_ not in readme, "dash in README")
in_code = False
for l in lines:
    if l.startswith("```"):
        in_code = not in_code
        continue
    if in_code or l.startswith("|") or l.startswith("!["):
        continue
    stripped = re.sub(r"\(https?://[^)]*\)|\(/research-assets/[^)]*\)|`[^`]*`|\b\d{1,2}:\d{2}(:\d{2})?\b", "", l)
    rule(":" not in stripped, "colon outside a clock time, link, code or table: " + l[:80])
for f in LAYOUT["keyFindings"] + [META["description"], META["imageAlt"], svg_text]:
    rule(":" not in re.sub(r"\b\d{1,2}:\d{2}(:\d{2})?\b|https?://\S+", "", f), "colon in a finding, description, alt text or the chart's text")
heads = [l[3:] for l in lines if l.startswith("## ")]


def slug(h):
    return re.sub(r"[^a-z0-9]+", "-", h.lower().replace("'", "").replace("$", "").replace(".", "")).strip("-")


rule([slug(h) for h in heads] == [n[1] for n in LAYOUT["navigation"]], "navigation anchors match the headings")
for link in ["https://ethenadash.com/ethenapay/", "https://ethenadash.com/methodology/", "https://ethenadash.com/research/ethenapay-vs-susde-2026-10-08/"]:
    rule(link in ARTICLE, "link missing " + link)
rule(LAYOUT["dashboard"] == "/ethenapay/", "dashboard link")
rule(len(LAYOUT["keyFindings"]) == 3, "three key findings")
for f in LAYOUT["archiveFiles"]:
    rule((HERE / f).exists(), "archive file missing " + f)
for f in ("inputs/chain/tokens.csv", "inputs/chain/transfers_blockscout.csv", "inputs/chain/transfers_routescan.csv", "inputs/chain/counterparties.csv"):
    rule(f not in LAYOUT["archiveFiles"], "a private file is in the download: " + f)
for f in LAYOUT["assets"]:
    rule((HERE / "out" / f).exists(), "asset missing " + f)
for m in re.findall(r"\(/research-assets/ethena-reserve-fund-2026-10-12/([^)]+)\)", ARTICLE):
    rule(m in LAYOUT["assets"] or m == "calculation-files.zip", "linked download not in assets " + m)

# No addresses of accounts, no transaction hashes and no advertised web addresses in the published files. Allowed
# addresses are contracts and Ethena's named multisigs. Addresses inside 32-byte words of call results are checked too.
cps = rows(CH / "counterparties_public.csv")
allowed = {r["counterparty"] for r in cps if r["counterparty"].startswith("0x")}
allowed |= {t["token"] for t in toks} | {a for a, d in T.values()}
allowed |= {"0x3b0aaf6e6fcd4a7ceef8c92c32dfea9e64dc1862", "0x1f98431c8ad98523631ae4a59f267346ea31f984", "0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419",
            "0x435664008f38b0650fbc1c9fc971d0a3bc2f1e47", "0xc36442b4a4522e871399cd717abdd847ab11fe88", "0x4423198f26764a8ce9ac8f1683c476854c885d9d",
            "0xa2af0b03aaf167cfc9624c6ef587581b6fcced92", "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34",
            "0xd7fcade52afb60fbf0e1e5f72a683f43820f56a0"}  # the last: Ethena's published PSM custodian, a constant in the read script as it ran
for f in LAYOUT["archiveFiles"]:
    p = HERE / f
    if p.suffix in (".png", ".zip") or not p.exists():
        continue
    text = p.read_text(encoding="utf-8")
    found = set(a.lower() for a in re.findall(r"0x[0-9a-fA-F]{40}(?![0-9a-fA-F])", text))
    # Address fields inside call results: the owner and coin reads, and the operator and tokens of each position.
    if f in ("inputs/chain/once_reads.csv",):
        for r in rows(p):
            if r["call"].startswith(("ownerOf", "Curve coins")):
                found.add("0x" + r["result"][-40:])
    if f in ("inputs/chain/snapshot_reads.csv", "inputs/chain/month_reads.csv"):
        for r in rows(p):
            if r["call"].startswith("positions ") and r["result"].startswith("0x") and len(r["result"]) >= 2 + 64 * 4:
                for i in (1, 2, 3):
                    found.add("0x" + r["result"][2 + 64 * i + 24:2 + 64 * (i + 1)])
    for a in sorted(found):
        if a not in allowed and not re.fullmatch(r"0x0+[0-9a-f]{0,8}", a):
            FAILS.append("address not on the allowed list in %s: %s" % (f, a))
            break
    if f.startswith(("inputs/", "out/")):
        rule(not re.search(r"\b(?:transaction_hash|transactionHash|txHash)\b", text), "transaction hash field in " + f)
        rule(not re.search(r"0x[0-9a-f]{64}(?![0-9a-f])", text) or f in ("inputs/chain/run.json", "inputs/chain/month_sources.csv", "inputs/chain/snapshot_reads.csv",
                                                                           "inputs/chain/month_reads.csv", "inputs/chain/once_reads.csv", "inputs/chain/events.csv"),
             "64-digit hex in " + f)
for t in toks:
    rule(not re.search(r"https?://|www\.|[a-z0-9-]+\.[a-z]{2,}(?![a-z0-9])", t["symbol"], re.I), "token name with a web address in tokens_public.csv")

if FAILS:
    print("\n".join(FAILS))
    sys.exit(1)
print("%d phrases found, page rules pass" % len(FOUND))
