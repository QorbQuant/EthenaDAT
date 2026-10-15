#!/usr/bin/env python3
"""Ethena's reserve fund, the Safe at 0x2b5ab59163a6e93b4486f6055d33ca4a115dd4d5 that Ethena's key addresses
page names as the Reserve Fund, read at Ethereum block 26,178,998 (21:10:59 UTC on October 12, 2026) and at
the end of every month from January 2024 to September 2026, with every token transfer it made.

Reads the files in inputs/, runs its checks and, if all pass, writes the tables in out/. If any check fails
it writes out/run_log_failed.txt and stops, so out/ keeps the tables of the last clean run.
Python 3.8 or later, standard library only, no network.
"""
import csv
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import univ3  # noqa: E402  (Uniswap V3 position math, in this folder)

IN = os.path.join(HERE, "inputs")
CH = os.path.join(IN, "chain")
WEB = os.path.join(IN, "web")
OUT = os.path.join(HERE, "out")

RF = "0x2b5ab59163a6e93b4486f6055d33ca4a115dd4d5"          # Reserve Fund, Ethena's key addresses page
PAYOUT = "0x71e4f98e8f20c88112489de3dded4489802a3a87"      # sUSDe Payout Fund, the same page
SAFE_A = "0xa2af0b03aaf167cfc9624c6ef587581b6fcced92"      # a Safe the page does not name
SAFE_B = "0x4423198f26764a8ce9ac8f1683c476854c885d9d"      # another Safe the page does not name
ZERO = "0x0000000000000000000000000000000000000000"
CURVE = "0xc2921134073151490193ac7369313c8e0b08e1e7"       # Curve USDtb/USDC pool and its LP token
NPM = "0xc36442b4a4522e871399cd717abdd847ab11fe88"         # Uniswap V3 NonfungiblePositionManager
UNI_POOL = "0x435664008f38b0650fbc1c9fc971d0a3bc2f1e47"    # Uniswap V3 USDe/USDT 0.01% pool
GPV2 = "0x9008d19f58aabd9ed0d60971565aa8510560ab41"        # CoW Protocol settlement
CURVE_ROUTER = "0xf0d4c12a5768d806021f80a262b4d39d26c58b8d"
MIGRATION = "0xf86141a5657cf52aeb3e30ebcca5ad3a8f714b89"   # Sky's MigrationActions
BUIDL_IN = "0x9da8e89993f8a2b6fbd97771093988936b74e26f"    # contract that took the fund's USDc for BUIDL
POSITIONS = [658523, 658530, 680386, 700726]
READ_BLOCK = 26178998

# Labels of counterparties that are not contracts, as the browser numbered them in order of first appearance.
MINT_CP = "eoa-6"                    # received the BUIDL and USDC exchanged for USDtb, sent eight interest transfers
INTEREST_CPS = {"eoa-6", "eoa-14"}   # sent the USDtb interest transfers
USTB_PAY = {"eoa-8", "eoa-11"}       # received USDC for USTB
USTB_REDEEM = {"eoa-10"}             # sent USDC for redeemed USTB
OTHER_IN = {"eoa-2", "eoa-7"}        # sent 3,239,921 USDT and 10,000,000 USDC
BUIDL_RETURN = {"eoa-4"}             # returned the 1 USDC test sent to BUIDL's contract
DUST = {"eoa-5", "eoa-9", "eoa-12"}  # sent under 1 USDC to the fund, or received transfers of 0 USDC
DELEGATED = "eoa-20"                 # the counterparty Blockscout marked as a contract that holds an EIP-7702 delegation

# The browser's files that stay out of the download, and their public copies.
PRIVATE = {"tokens.csv": "tokens_public.csv", "transfers_blockscout.csv": "transfers_blockscout_public.csv",
           "transfers_routescan.csv": "transfers_routescan_public.csv", "counterparties.csv": "counterparties_public.csv"}

# symbol, address, decimals, how the review values it
TOKENS = [
    ("USDC", "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", 6, "dollar"),
    ("USDT", "0xdac17f958d2ee523a2206206994597c13d831ec7", 6, "dollar"),
    ("DAI", "0x6b175474e89094c44da98b954eedeac495271d0f", 18, "dollar"),
    ("sDAI", "0x83f20f44975d03b1b09e64809b757c47f942beea", 18, "vault"),
    ("USDS", "0xdc035d45d973e3ec169d2276ddab16f1e407384f", 18, "dollar"),
    ("sUSDS", "0xa3931d71877c0e7a3148cb7eb4463524fec27fbd", 18, "vault"),
    ("USDe", "0x4c9edd5852cd905f086c759e8383e09bff1e68b3", 18, "dollar"),
    ("sUSDe", "0x9d39a5de30e57443bff2a8307a4256c8797a3497", 18, "vault"),
    ("USDtb", "0xc139190f447e929f090edeb554d95abb8b18ac1c", 18, "dollar"),
    ("BUIDL", "0x7712c34205737192402172409a8f7ccef8aa2aec", 6, "dollar"),
    ("USTB", "0x43415eb6ff9db7e26a15b704e7a3edce97d31c4e", 6, "fund"),
    ("CurveLP", CURVE, 18, "lp"),
]
SYM = {a: s for s, a, d, k in TOKENS}
ADDR = {s: a for s, a, d, k in TOKENS}
DEC = {s: d for s, a, d, k in TOKENS}
KIND = {s: k for s, a, d, k in TOKENS}
DOLLAR = [s for s, a, d, k in TOKENS if k == "dollar"]

# SHA-256 of the browser scripts, checked in the browser against these files before each run.
SCRIPTS = {
    "browser/reserve_fund_read.js": "131ac50f84d29ba71bf126489050aadee8669660602e269dceaf6708eef216e7",
    "browser/safe_transactions.js": "331d655f2a698c0255d56520c659fb750593c10e94accc150ce89ff03a705db9",
    "browser/bundle_files.js": "f250d3a14f61fa038a7c766033b16a39afd5a687e5ef7e0f21ef3a03fe15b9c8",
}

CATEGORIES = {
    "payout": ("in", "Allocations from the sUSDe Payout Fund"),
    "safe_a": ("in", "Transfers from Safe 0xa2af...cced92"),
    "other_in": ("in", "Transfers from addresses that are not contracts"),
    "interest": ("in", "USDtb interest transfers"),
    "dust": ("in", "Transfers under 1 USDC of unknown purpose"),
    "savings": ("sleeve", "sDAI and sUSDS savings vaults"),
    "ustb": ("sleeve", "Superstate USTB"),
    "uniswap": ("sleeve", "Uniswap V3 USDe/USDT positions"),
    "buidl": ("sleeve", "BUIDL, bought and its dividend"),
    "curve": ("sleeve", "Curve USDtb/USDC pool"),
    "usdtb_mint": ("sleeve", "USDtb minted for BUIDL and USDC"),
    "swap": ("sleeve", "Swaps through CoW Protocol and Curve's router"),
    "safe_b": ("sleeve", "Conversions through Safe 0x4423...9d9d"),
}

CHECKS = []
LOG = []


def log(msg=""):
    LOG.append(msg)
    print(msg)


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    log(("PASS " if ok else "FAIL ") + name + (" | " + detail if detail else ""))
    return ok


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def word(h, i):
    return int(h[2 + 64 * i:2 + 64 * (i + 1)], 16)


def sword(h, i):
    v = word(h, i)
    return v - (1 << 256) if v >= 1 << 255 else v


def as_int(result):
    """An eth_call result as a number, or None for an empty result or an error."""
    if not result or not result.startswith("0x") or result == "0x":
        return None
    return int(result, 16)


def units(raw, decimals):
    return F(raw, 10 ** decimals)


def fmt(x, places=2, sep=True):
    """A Fraction rounded half up (away from zero), with thousands separators."""
    neg = x < 0
    x = -x if neg else x
    q = 10 ** places
    n = (x * q * 2 + 1) // 2
    whole, frac = divmod(int(n), q)
    s = ("{:,}".format(whole) if sep else str(whole)) + ("." + str(frac).rjust(places, "0") if places else "")
    return "-" + s if neg and n else s


def plain(x, places=6):
    return fmt(x, places, sep=False)


def pct(x, places=2):
    return fmt(x * 100, places)


def iso(ts):
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def day(ts):
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")


def canon(rows):
    """The canonical text the browser hashed to compare two RPCs' answers at one block."""
    return "\n".join(sorted(r[0] + "=" + r[1] for r in rows))


def sanitize(name):
    """Token names that contain a web address are not repeated."""
    if re.search(r"https?://|www\.|[a-z0-9-]+\.[a-z]{2,}(?![a-z0-9])", name, re.I):
        return "[name contains a web address]"
    return name


# ------------------------------------------------------------------------------------------------------
# Valuation of one set of reads, at a month end or at the read block.

def value_reads(d, ustb_nav=None):
    """Value the fund from the results of one block's reads. Dollar tokens count at $1, vault shares at
    convertToAssets, the Curve LP token at the fund's share of the pool's two coins, the Uniswap positions
    at their tokens plus uncollected fees, ETH at Chainlink's ETH/USD answer and USTB at ustb_nav."""
    bal = {}
    for s, a, dec, k in TOKENS:
        v = as_int(d.get("balanceOf " + s))
        bal[s] = units(v, dec) if v else F(0)
    lines = {}
    for s in DOLLAR:
        lines[s] = bal[s]
    for v, base in (("sDAI", "DAI"), ("sUSDS", "USDS"), ("sUSDe", "USDe")):
        c = d.get("convertToAssets " + v)
        lines[v] = units(as_int(c), 18) if bal[v] and c and c.startswith("0x") else F(0)
    lines["USTB"] = bal["USTB"] * ustb_nav if bal["USTB"] else F(0)
    lp = {"usdc": F(0), "usdtb": F(0), "share": F(0)}
    if bal["CurveLP"]:
        c0 = units(as_int(d["Curve balances 0"]), 6)
        c1 = units(as_int(d["Curve balances 1"]), 18)
        ts = units(as_int(d["Curve totalSupply"]), 18)
        lp = {"usdc": bal["CurveLP"] / ts * c0, "usdtb": bal["CurveLP"] / ts * c1, "share": bal["CurveLP"] / ts,
              "pool_usdc": c0, "pool_usdtb": c1, "lp_supply": ts}
    lines["CurveLP"] = lp["usdc"] + lp["usdtb"]
    uni = F(0)
    uni_detail = {}
    s0 = d.get("Uniswap slot0")
    for pid in POSITIONS:
        p = d.get("positions %d" % pid)
        if not p or not p.startswith("0x") or len(p) < 2 + 64 * 12:
            continue
        liq, tl, tu = word(p, 7), sword(p, 5), sword(p, 6)
        owed0, owed1 = word(p, 10), word(p, 11)
        a0 = a1 = 0
        if liq:
            sp, tick = word(s0, 0), sword(s0, 1)
            a0, a1 = univ3.amounts_for_liquidity(sp, univ3.get_sqrt_ratio_at_tick(tl), univ3.get_sqrt_ratio_at_tick(tu), liq)
            lo, up = d["ticks %d" % tl], d["ticks %d" % tu]
            g0, g1 = as_int(d["Uniswap feeGrowthGlobal0X128"]), as_int(d["Uniswap feeGrowthGlobal1X128"])
            in0 = univ3.fee_growth_inside(tick, tl, tu, word(lo, 2), word(up, 2), g0)
            in1 = univ3.fee_growth_inside(tick, tl, tu, word(lo, 3), word(up, 3), g1)
            owed0 = univ3.fees_owed(liq, in0, word(p, 8), owed0)
            owed1 = univ3.fees_owed(liq, in1, word(p, 9), owed1)
        v = units(a0 + owed0, 18) + units(a1 + owed1, 6)
        uni_detail[pid] = (liq, a0, a1, owed0, owed1)
        uni += v
    lines["Uniswap"] = uni
    cl = d["Chainlink ETH/USD latestRoundData"]
    eth_price = F(sword(cl, 1), 10 ** 8)
    eth = F(int(d["eth_getBalance"], 16), 10 ** 18)
    lines["ETH"] = eth * eth_price
    total = sum(lines.values(), F(0))
    usde_supply = units(as_int(d["totalSupply USDe"]), 18)
    usdtb_supply = units(as_int(d["totalSupply USDtb"]), 18) if as_int(d.get("totalSupply USDtb")) else F(0)
    return {"bal": bal, "lines": lines, "lp": lp, "uni": uni_detail, "eth": eth, "eth_price": eth_price,
            "eth_updated": word(cl, 3), "total": total, "usde_supply": usde_supply, "usdtb_supply": usdtb_supply}


GROUPS = [
    ("USDtb", ["USDtb"]),
    ("Curve USDtb/USDC pool", ["CurveLP"]),
    ("BUIDL and USTB", ["BUIDL", "USTB"]),
    ("sDAI and sUSDS", ["sDAI", "sUSDS", "sUSDe"]),
    ("Uniswap V3 positions", ["Uniswap"]),
    ("Other stablecoins and ETH", ["USDC", "USDT", "DAI", "USDS", "USDe", "ETH"]),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    failed_log = os.path.join(OUT, "run_log_failed.txt")
    if os.path.exists(failed_log):
        os.remove(failed_log)
    log("Ethena reserve fund review, run at " + datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))

    # ---- inputs ---------------------------------------------------------------------------------------
    manifest = read_csv(os.path.join(IN, "manifest.csv"))
    bad, present = [], 0
    for m in manifest:
        p = os.path.join(HERE, m["path"])
        if not os.path.exists(p):
            if m["in_download"] == "yes":
                bad.append(m["path"] + " missing")
            continue
        present += 1
        if os.path.getsize(p) != int(m["bytes"]) or sha256_file(p) != m["sha256"]:
            bad.append(m["path"])
    check("every input present matches its size and SHA-256 in inputs/manifest.csv", not bad,
          "%d files%s" % (present, ", failed " + ", ".join(bad) if bad else ""))
    digests = json.load(open(os.path.join(CH, "browser_digests.json"), encoding="utf-8"))
    bad, n = [], 0
    for name, want in sorted(digests.items()):
        p = os.path.join(CH, name)
        if not os.path.exists(p):
            if name not in PRIVATE:
                bad.append(name + " missing")
            continue
        n += 1
        if sha256_file(p) != want:
            bad.append(name)
    raw_present = all(os.path.exists(os.path.join(CH, k)) for k in PRIVATE)
    check("the browser's files present match the SHA-256 digests the browser computed", not bad,
          "%d files%s%s" % (n, ", failed " + ", ".join(bad) if bad else "", "" if raw_present else ", the four private files not in this copy"))
    bad = [k for k, v in SCRIPTS.items() if sha256_file(os.path.join(HERE, k)) != v]
    check("the scripts in browser/ match the SHA-256 digests recorded when the browser ran them", not bad, ", ".join(bad))

    # The public copies. Names that contain a web address are replaced, and the one counterparty that
    # Blockscout marked as a contract but that holds an EIP-7702 delegation is labeled eoa-20.
    tokens_pub = read_csv(os.path.join(CH, "tokens_public.csv"))
    pub_text = {k: open(os.path.join(CH, v), encoding="utf-8", newline="").read() for k, v in PRIVATE.items()}
    ok = all(sanitize(t["symbol"]) == t["symbol"] for t in tokens_pub)
    cps_pub = read_csv(os.path.join(CH, "counterparties_public.csv"))
    ok = ok and any(r["counterparty"] == DELEGATED for r in cps_pub) and all(
        not r["counterparty"].startswith("0x") or not r["label"].split(" ", 1)[-1].startswith("eoa-") for r in cps_pub)
    detail = "private files not in this copy, public files checked on their own"
    if raw_present:
        raw_tok = read_csv(os.path.join(CH, "tokens.csv"))
        ok = ok and len(raw_tok) == len(tokens_pub) and all(
            a["token"] == b["token"] and a["decimals"] == b["decimals"] and a["type"] == b["type"] and b["symbol"] == sanitize(a["symbol"])
            for a, b in zip(raw_tok, tokens_pub))
        # The delegated account's row is relabeled and sorted among the labels, so its place does not hint at its address.
        raw_cp = open(os.path.join(CH, "counterparties.csv"), encoding="utf-8", newline="").read().split("\n")
        pub_cp = pub_text["counterparties.csv"].split("\n")
        gone = [l for l in raw_cp if l not in pub_cp]
        addr = gone[0].split(",")[0] if len(gone) == 1 else "none"
        body = [DELEGATED + "," + DELEGATED if l == addr + "," + addr + " contract" else l for l in raw_cp[1:-1]]
        ok = ok and len(gone) == 1 and raw_cp[1:-1] == sorted(raw_cp[1:-1]) and pub_cp == [raw_cp[0]] + sorted(body) + [""]
        for name in ("transfers_blockscout.csv", "transfers_routescan.csv"):
            raw_t = open(os.path.join(CH, name), encoding="utf-8", newline="").read()
            ok = ok and raw_t.replace(addr, DELEGATED) == pub_text[name] and raw_t.count(addr) == 1
        ok = ok and not any(addr in t for t in pub_text.values())
        detail = "%d token names replaced, one counterparty relabeled" % sum(1 for a in raw_tok if sanitize(a["symbol"]) != a["symbol"])
    check("the public copies equal the browser's token list, transfer lists and counterparties with token names that contain a web address replaced and the one delegated account labeled eoa-20",
          ok, detail)

    run = json.load(open(os.path.join(CH, "run.json"), encoding="utf-8"))
    docs = open(os.path.join(WEB, "ethena_reserve_fund_docs_2026-10-12.txt"), encoding="utf-8").read()
    check("the read block is %s and the fund is the multisig with 4/10 signers that the key addresses page names as the Reserve Fund" % "{:,}".format(READ_BLOCK),
          run["read_block"] == READ_BLOCK and run["reserve_fund"] == RF and ("the Reserve Fund " + RF + ", with 4/10 signers") in docs)

    # ---- snapshot -------------------------------------------------------------------------------------
    snap = read_csv(os.path.join(CH, "snapshot_reads.csv"))
    by_rpc = defaultdict(dict)
    for r in snap:
        by_rpc[r["rpc"]][r["call"]] = r["result"]
    rpcs = run["latest_rpcs"]
    blocks = run["snapshot_blocks"]
    same_block = len({(blocks[u]["number"], blocks[u]["hash"]) for u in rpcs}) == 1 and blocks[rpcs[0]]["number"] == READ_BLOCK
    same_results = by_rpc[rpcs[0]] == by_rpc[rpcs[1]] and len(by_rpc[rpcs[0]]) == 23
    snap_time = blocks[rpcs[0]]["time"]
    check("two RPCs served the same block and gave the same answer to all 23 reads", same_block and same_results,
          "block %d at %s" % (READ_BLOCK, iso(snap_time)))
    S = by_rpc[rpcs[0]]
    check("no read at the block returned an error", all(v.startswith("0x") for v in S.values()))

    # ---- once reads -----------------------------------------------------------------------------------
    once = {r["call"]: r for r in read_csv(os.path.join(CH, "once_reads.csv"))}
    threshold = as_int(once["getThreshold"]["result"])
    owners = int(once["getOwners count"]["result"])
    nonce = as_int(once["nonce"]["result"])
    v = once["VERSION"]["result"]
    version = bytes.fromhex(v[2 + 128:2 + 128 + 2 * word(v, 1)]).decode()
    check("the Safe needs 4 of its 10 owners to sign, as the key addresses page says, and runs Safe version 1.3.0",
          threshold == 4 and owners == 10 and version == "1.3.0", "threshold %d, owners %d, version %s" % (threshold, owners, version))
    safe_tx = read_csv(os.path.join(CH, "safe_transactions.csv"))
    executed = sum(int(r["transactions"]) for r in safe_tx if r["status"] == "ok" and r["method"] == "execTransaction")
    reverted_exec = sum(int(r["transactions"]) for r in safe_tx if r["status"] == "error" and r["method"] == "execTransaction")
    other_failed = sum(int(r["transactions"]) for r in safe_tx if r["status"] == "error" and r["method"] != "execTransaction")
    sent_to_safe = sum(int(r["transactions"]) for r in safe_tx)
    check("the Safe's nonce, %d, equals the number of its executed transactions in Blockscout's list" % nonce,
          nonce == executed == 82 and sent_to_safe == run["fund_transactions_sent_to_safe"] == 146,
          "%d executed, %d reverted, %d other failed calls, %d sent to the Safe in all" % (executed, reverted_exec, other_failed, sent_to_safe))
    owners_ok = all(once["ownerOf %d" % pid]["result"][-40:] == RF[2:] for pid in POSITIONS)
    check("the fund owns the four Uniswap V3 positions", owners_ok and run["position_ids"] == POSITIONS)
    coins_ok = once["Curve coins 0"]["result"][-40:] == ADDR["USDC"][2:] and once["Curve coins 1"]["result"][-40:] == ADDR["USDtb"][2:]
    check("the Curve pool's coins are USDC and USDtb", coins_ok)
    check("every tracked token's decimals match the review's table", all(as_int(once["decimals " + s]["result"]) == DEC[s] for s in DEC))
    pool_ok = run["uniswap_pool"] == UNI_POOL and run["uniswap_pool_tokens"] == [ADDR["USDe"], ADDR["USDT"], 100] and UNI_POOL in docs
    check("the positions are in the USDe/USDT pool with a 0.01% fee that the key addresses page lists", pool_ok)

    # ---- month ends -----------------------------------------------------------------------------------
    msrc = read_csv(os.path.join(CH, "month_sources.csv"))
    mreads = defaultdict(list)
    for r in read_csv(os.path.join(CH, "month_reads.csv")):
        mreads[r["month"]].append((r["call"], r["result"]))
    labels = [m["month"] for m in msrc]
    expected = ["%d-%02d" % (y, mo) for y in (2024, 2025, 2026) for mo in range(1, 13)][:33]
    check("the month ends run from January 2024 to September 2026", labels == expected, "%d months" % len(labels))
    bad = []
    for m in msrc:
        ts, bt, nt = int(m["month_end_unix"]), int(m["block_time_unix"]), int(m["next_block_time_unix"])
        if not (bt <= ts < nt) or m["block_by_time"] != m["block_primary"] or m["block_primary"] != m["block_second"]:
            bad.append(m["month"] + " block")
        if m["hash_primary"] != m["hash_second"] or m["sha256_primary"] != m["sha256_second"] or m["same"] != "1":
            bad.append(m["month"] + " sources")
        if sha256_text(canon(mreads[m["month"]])) != m["sha256_primary"]:
            bad.append(m["month"] + " digest")
    check("each month end is read at the last block at or before 23:59:59 UTC, and two archive RPCs gave identical answers there", not bad, ", ".join(bad))
    errors = [(m, c) for m in mreads for c, r in mreads[m] if r.startswith("error") and not (c.startswith("positions ") and "Invalid token ID" in r)]
    check("the only errors in the month-end reads are for positions not yet created", not errors, str(errors[:3]))
    M = {m: dict(mreads[m]) for m in mreads}
    mblock = {m["month"]: int(m["block_primary"]) for m in msrc}
    mtime = {m["month"]: int(m["block_time_unix"]) for m in msrc}

    # ---- transfers ------------------------------------------------------------------------------------
    bs = read_csv(os.path.join(CH, "transfers_blockscout_public.csv"))
    rs = read_csv(os.path.join(CH, "transfers_routescan_public.csv"))
    check("Blockscout listed %d token transfers of the fund in %d pages" % (len(bs), run["blockscout_pages"]),
          len(bs) == run["blockscout_transfers"] == 182)
    key = lambda r: (r["block"], r["token"], r["value_raw"], r["token_id"], r["from"], r["to"])
    keyt = lambda r: (r["tx"],) + key(r)
    cb, cr = Counter(map(keyt, bs)), Counter(map(keyt, rs))
    only_b, only_r = cb - cr, cr - cb
    listed = set(SYM) | {NPM}
    bs_keys = Counter(map(key, bs))
    repeated = [k for k in only_r if k[2] in listed]
    unl = [k for k in only_r if k[2] not in listed]
    ok = (len(only_b) == 1 and list(only_b)[0][0] == "tx-29"
          and len(repeated) == 6 and all(bs_keys[k[1:]] == 1 for k in repeated)
          and all(n == 1 for n in only_r.values()))
    check("Routescan's list differs from Blockscout's only by missing one transfer, repeating six tracked-token rows under a second transaction label, and adding untracked tokens",
          ok, "missing %s, %d repeated rows, %d untracked-token rows, of which %d repeat Blockscout rows" % (
              ", ".join(k[0] for k in only_b), len(repeated), len(unl), sum(1 for k in unl if bs_keys[k[1:]] >= 1)))
    real = [r for r in bs if r["token"] in listed]
    unlisted_rows = [r for r in bs if r["token"] not in listed]
    log("tracked-token transfers %d, untracked-token transfers %d" % (len(real), len(unlisted_rows)))

    def cp(r):
        return r["from"] if r["to"] == RF else r["to"]

    def direction(r):
        return "in" if r["to"] == RF else "out"

    # ---- classification ------------------------------------------------------------------------------
    cls_rows = read_csv(os.path.join(IN, "classification.csv"))
    cls = {r["tx"]: r for r in cls_rows}
    txs = sorted({r["tx"] for r in real}, key=lambda s: int(s[3:]))
    check("every transaction that moved a tracked token is classified exactly once, and nothing else is",
          len(cls_rows) == len(cls) and sorted(cls, key=lambda s: int(s[3:])) == txs and all(c["category"] in CATEGORIES for c in cls.values()),
          "%d transactions, %d rows" % (len(txs), len(cls_rows)))
    legs = defaultdict(list)
    for r in real:
        legs[r["tx"]].append(r)

    def one_each(L):
        return sum(1 for r in L if direction(r) == "out") == 1 and sum(1 for r in L if direction(r) == "in") == 1

    T_ = lambda r, s: r["token"] == ADDR[s]
    rules = {
        "payout": lambda L: all(cp(r) == PAYOUT and direction(r) == "in" for r in L),
        "safe_a": lambda L: all(cp(r) == SAFE_A and direction(r) == "in" for r in L),
        "safe_b": lambda L: len(L) == 1 and cp(L[0]) == SAFE_B and (T_(L[0], "USDT") or T_(L[0], "USDe")),
        "other_in": lambda L: len(L) == 1 and cp(L[0]) in OTHER_IN and direction(L[0]) == "in" and (T_(L[0], "USDT") or T_(L[0], "USDC")),
        "interest": lambda L: all(cp(r) in INTEREST_CPS and direction(r) == "in" and T_(r, "USDtb") for r in L),
        "dust": lambda L: all(cp(r) in DUST and T_(r, "USDC") and (int(r["value_raw"]) < 10 ** 6 if direction(r) == "in" else int(r["value_raw"]) == 0) for r in L),
        "swap": lambda L: one_each(L) and all(cp(r) in (GPV2, CURVE_ROUTER) and any(T_(r, s) for s in ("USDC", "USDT", "DAI", "USDe")) for r in L),
        "uniswap": lambda L: all((cp(r) == UNI_POOL and (T_(r, "USDe") or T_(r, "USDT"))) or (r["token"] == NPM and r["from"] == ZERO) for r in L),
        "curve": lambda L: all((cp(r) == CURVE and direction(r) == "out") or (r["token"] == CURVE and r["from"] == ZERO) for r in L),
        "savings": lambda L: all((T_(r, "DAI") and cp(r) == ADDR["sDAI"] and direction(r) == "out")
                                 or (T_(r, "sUSDS") and cp(r) in (ZERO, GPV2))
                                 or (T_(r, "USDS") and cp(r) == ADDR["sUSDS"] and direction(r) == "in")
                                 or (T_(r, "sDAI") and cp(r) == GPV2 and direction(r) == "out")
                                 or (T_(r, "USDC") and cp(r) == GPV2 and direction(r) == "in") for r in L),
        "buidl": lambda L: all((T_(r, "USDC") and direction(r) == "out" and cp(r) == BUIDL_IN)
                               or (T_(r, "USDC") and direction(r) == "in" and cp(r) in BUIDL_RETURN)
                               or (T_(r, "BUIDL") and r["from"] == ZERO) for r in L),
        "usdtb_mint": lambda L: one_each(L) and all(((T_(r, "USDC") or T_(r, "BUIDL")) and direction(r) == "out" and cp(r) == MINT_CP)
                                                     or (T_(r, "USDtb") and r["from"] == ZERO) for r in L),
        "ustb": lambda L: all((T_(r, "USTB") and cp(r) == ZERO) or (T_(r, "USDC") and direction(r) == "out" and cp(r) in USTB_PAY)
                              or (T_(r, "USDC") and direction(r) == "in" and cp(r) in USTB_REDEEM) for r in L),
    }
    bad = [t for t in txs if not rules[cls[t]["category"]](legs[t])]
    check("every transaction's legs fit its category: the counterparties, tokens and directions the category allows", not bad, ", ".join(bad))

    # ---- events ---------------------------------------------------------------------------------------
    ev = read_csv(os.path.join(CH, "events.csv"))
    check("the event-log queries in the blocks found by the explorers and by the sDAI balance search all answered",
          all(q[1] == "ok" for q in run["event_queries"]), "; ".join("%s %d" % (q[0], q[2]) for q in run["event_queries"]))
    sdai_ev = []  # (block, signed shares, assets, event) with the fund as owner
    for e in ev:
        if e["event"] == "sDAI Deposit" and e["topic2"].startswith(RF):
            sdai_ev.append((int(e["block"]), word(e["data"], 1), word(e["data"], 0), e))
        elif e["event"] == "sDAI Withdraw" and e["topic3"].startswith(RF):
            sdai_ev.append((int(e["block"]), -word(e["data"], 1), word(e["data"], 0), e))
    dep = [x for x in sdai_ev if x[1] > 0]
    wd = [x for x in sdai_ev if x[1] < 0]
    dai_in_tx17 = sum(int(r["value_raw"]) for r in legs["tx-17"] if T_(r, "DAI"))
    dep_ok = len(dep) == 1 and dep[0][2] == dai_in_tx17 and dep[0][0] == int(legs["tx-17"][0]["block"])
    check("the fund's one sDAI deposit used the DAI it sent in the same block", dep_ok,
          "%s DAI for %s sDAI" % (fmt(units(dep[0][2], 18)), fmt(units(dep[0][1], 18))) if dep else "no deposit")
    susds_dep = {int(e["block"]): (word(e["data"], 0), word(e["data"], 1)) for e in ev if e["event"] == "sUSDS Deposit"}
    susds_mints = {int(r["block"]): int(r["value_raw"]) for r in real if T_(r, "sUSDS") and r["from"] == ZERO}
    mig_ok = len(wd) == 3 and all(x[3]["topic1"].startswith(MIGRATION) and x[3]["topic2"].startswith(MIGRATION) and
                                  susds_dep.get(x[0], (None,))[0] == x[2] and susds_mints.get(x[0]) == susds_dep[x[0]][1] for x in wd)
    check("the three sDAI withdrawals went through Sky's MigrationActions, and each block's sUSDS deposit took the same assets and minted the sUSDS the fund received",
          mig_ok, ", ".join("%s sDAI on %s" % (fmt(units(-x[1], 18)), day(int(x[3]["time_unix"]))) for x in wd))

    # ---- balances -------------------------------------------------------------------------------------
    deltas = defaultdict(list)  # token symbol -> [(block, signed raw)]
    for r in real:
        if r["token"] == NPM:
            continue
        v = int(r["value_raw"])
        deltas[SYM[r["token"]]].append((int(r["block"]), v if r["to"] == RF else -v))
    for b, sh, _, _ in sdai_ev:
        deltas["sDAI"].append((b, sh))

    def balance_at(sym, block):
        return sum(v for b, v in deltas[sym] if b <= block)

    bad = []
    for m in labels:
        for s, a, dec, k in TOKENS:
            got = as_int(M[m].get("balanceOf " + s))
            if (got or 0) != balance_at(s, mblock[m]):
                bad.append("%s %s" % (m, s))
    for s, a, dec, k in TOKENS:
        if (as_int(S["balanceOf " + s]) or 0) != balance_at(s, READ_BLOCK):
            bad.append("read block " + s)
    check("for all 12 tracked tokens, Blockscout's transfers, with sDAI's Deposit and Withdraw records, add up to the balance read at each of the 33 month ends and at the read block",
          not bad, "; ".join(bad[:5]))

    # Each position's own tokens net to what the fund still held of them at the read block.
    def cat_units(cats, sym):
        return sum((units(int(r["value_raw"]), DEC[sym]) * (1 if direction(r) == "in" else -1)
                    for r in real if cls[r["tx"]]["category"] in cats and T_(r, sym)), F(0))
    sdai_events = sum((units(x[1], 18) for x in sdai_ev), F(0))
    nft_in = sum(1 for r in real if r["token"] == NPM and r["to"] == RF)
    closure = {
        "sDAI": (cat_units({"savings"}, "sDAI") + sdai_events, F(0)),
        "sUSDS": (cat_units({"savings"}, "sUSDS"), F(0)),
        "USTB": (cat_units({"ustb"}, "USTB"), F(0)),
        "BUIDL": (cat_units({"buidl", "usdtb_mint"}, "BUIDL"), units(as_int(S["balanceOf BUIDL"]), 6)),
        "CurveLP": (cat_units({"curve"}, "CurveLP"), units(as_int(S["balanceOf CurveLP"]), 18)),
    }
    bad = [k for k, (a, b) in closure.items() if a != b] + ([] if nft_in == 4 and all(cls[r["tx"]]["category"] == "uniswap" for r in real if r["token"] == NPM) else ["NFT"])
    check("each position's own tokens, counted within its category, net to what the fund held of them at the read block", not bad, ", ".join(bad))

    # Uniswap events and transfers.
    uni_ev = defaultdict(list)
    for e in ev:
        if e["event"].startswith("NPM "):
            kind, pid = e["event"].split()[1], int(e["event"].split()[2])
            uni_ev[pid].append((int(e["block"]), kind, word(e["data"], 0), word(e["data"], 1), word(e["data"], 2), e))
    bad = []
    for b in sorted({int(r["block"]) for r in real if cp(r) == UNI_POOL}):
        sel = [r for r in real if int(r["block"]) == b and cp(r) == UNI_POOL]
        out0 = sum(int(r["value_raw"]) for r in sel if T_(r, "USDe") and direction(r) == "out")
        out1 = sum(int(r["value_raw"]) for r in sel if T_(r, "USDT") and direction(r) == "out")
        in0 = sum(int(r["value_raw"]) for r in sel if T_(r, "USDe") and direction(r) == "in")
        in1 = sum(int(r["value_raw"]) for r in sel if T_(r, "USDT") and direction(r) == "in")
        inc = [x for pid in uni_ev for x in uni_ev[pid] if x[0] == b and x[1] == "IncreaseLiquidity"]
        col = [x for pid in uni_ev for x in uni_ev[pid] if x[0] == b and x[1] == "Collect"]
        if (sum(x[3] for x in inc), sum(x[4] for x in inc)) != (out0, out1) or (sum(x[3] for x in col), sum(x[4] for x in col)) != (in0, in1):
            bad.append(str(b))
        if col and not all(x[5]["collect_recipient"].startswith(RF) for x in col):
            bad.append(str(b) + " recipient")
    liq_bad = []
    for m in labels:
        for pid in POSITIONS:
            p = M[m].get("positions %d" % pid, "")
            want = sum(x[2] if x[1] == "IncreaseLiquidity" else -x[2] for x in uni_ev[pid] if x[0] <= mblock[m] and x[1] != "Collect")
            have = word(p, 7) if p.startswith("0x") and len(p) >= 2 + 64 * 12 else None
            if (have is None and any(x[0] <= mblock[m] for x in uni_ev[pid])) or (have is not None and have != want):
                liq_bad.append("%s %d" % (m, pid))
    check("every Uniswap deposit and withdrawal matches the position manager's IncreaseLiquidity and Collect records, and each position's liquidity at every month end matches its records",
          not bad and not liq_bad, ", ".join(bad + liq_bad))
    snap_pos_empty = all(word(S["positions %d" % pid], 7) == 0 and word(S["positions %d" % pid], 10) == 0 and word(S["positions %d" % pid], 11) == 0 for pid in POSITIONS)
    check("at the read block all four positions held no liquidity and no uncollected tokens", snap_pos_empty)
    curve_ev = [e for e in ev if e["event"] == "Curve AddLiquidity"]
    c = curve_ev[0]["data"] if curve_ev else "0x" + "0" * 640
    # AddLiquidity(provider indexed, token_amounts uint256[], fees uint256[], invariant, token_supply)
    curve_ok = (len(curve_ev) == 1 and word(c, 4) == 2 and word(c, 5) == 9990474 * 10 ** 6 and word(c, 6) == 9990474 * 10 ** 18
                and sum(int(r["value_raw"]) for r in legs["tx-65"] if r["token"] == CURVE) == 19980948 * 10 ** 18
                and word(c, 3) == 19980948 * 10 ** 18)
    check("the fund's one Curve deposit added 9,990,474 USDC and 9,990,474 USDtb and minted 19,980,948 LP tokens, the pool's whole supply then", curve_ok)

    # ---- untracked tokens -----------------------------------------------------------------------------
    names = {t["token"]: t for t in tokens_pub}
    real_usdc_out = {units(int(r["value_raw"]), 6) for r in real if T_(r, "USDC") and direction(r) == "out"}

    def norm(name):
        return name.replace("С", "C").replace("Ѕ", "S").strip().upper()

    unl_out = [r for r in unlisted_rows if r["from"] == RF]
    unl_in = [r for r in unlisted_rows if r["to"] == RF]
    look = all(norm(names[r["token"]]["symbol"]) == "USDC" and r["token"] != ADDR["USDC"]
               and units(int(r["value_raw"]), int(names[r["token"]]["decimals"])) in real_usdc_out for r in unl_out)
    never_left = len({r["token"] for r in unl_in}) == len(unl_in) and not ({r["token"] for r in unl_in} & {r["token"] for r in unl_out})
    check("in Blockscout's list, %d transfers of tokens named like USDC from contracts other than USDC's appear as sent from the fund, each in the amount of a real USDC transfer from it, and %d other tokens were sent to the fund and never left"
          % (len(unl_out), len({r["token"] for r in unl_in})), look and never_left and len(unl_out) == 13)
    untracked_either = {r["token"] for r in unlisted_rows} | {r["token"] for r in rs if r["token"] not in listed}
    log("untracked tokens: %d in Blockscout's list, %d in either explorer's list" % (len({r["token"] for r in unlisted_rows}), len(untracked_either)))
    names_all = {norm(t["symbol"]) for t in tokens_pub}
    check("no token named USDM, which the Risk Committee's October 2024 vote gave 16.5%, appears among the tokens either explorer listed for the fund",
          "USDM" not in names_all, "%d tokens listed" % len(tokens_pub))

    # ---- valuation at the read block -----------------------------------------------------------------
    snapv = value_reads(S)
    lines = snapv["lines"]
    total = snapv["total"]
    lp = snapv["lp"]
    usdtb_held = lines["USDtb"] + lp["usdtb"]
    log("value at the read block %s; USDtb %s; pool share %s%% worth %s (USDC %s, USDtb %s)" % (
        fmt(total), fmt(lines["USDtb"]), pct(lp["share"], 4), fmt(lines["CurveLP"]), fmt(lp["usdc"]), fmt(lp["usdtb"])))
    check("at the read block the fund's value at $1 a stablecoin was $62.10 million, and USDtb and the Curve pool share made up all but under $1,000 of it",
          fmt(total) == "62,096,266.02" and total - lines["USDtb"] - lines["CurveLP"] < 1000,
          "other lines %s" % fmt(total - lines["USDtb"] - lines["CurveLP"]))
    ratio = total / snapv["usde_supply"]
    check("the fund equaled %s%% of USDe's total supply on Ethereum, %s USDe" % (pct(ratio), fmt(snapv["usde_supply"])), pct(ratio) == "1.31")
    usdtb_share = usdtb_held / total
    check("USDtb, held directly and through the pool, was %s%% of the fund's value and %s%% of USDtb's total supply on Ethereum" % (pct(usdtb_share), pct(usdtb_held / snapv["usdtb_supply"])),
          pct(usdtb_share) == "85.85")
    log("ETH %s at $%s, updated %s" % (fmt(snapv["eth"], 4), fmt(snapv["eth_price"]), iso(snapv["eth_updated"])))

    # ---- USTB at month ends ---------------------------------------------------------------------------
    def tx_time(t):
        return int(legs[t][0]["time_unix"])
    buy_usdc = sum(int(r["value_raw"]) for t in ("tx-87", "tx-91") for r in legs[t] if T_(r, "USDC"))
    buy_ustb = sum(int(r["value_raw"]) for t in ("tx-88", "tx-93") for r in legs[t] if T_(r, "USTB"))
    sell_ustb = sum(int(r["value_raw"]) for t in ("tx-110", "tx-112") for r in legs[t] if T_(r, "USTB"))
    sell_usdc = sum(int(r["value_raw"]) for t in ("tx-111", "tx-113") for r in legs[t] if T_(r, "USDC"))
    p1, t1 = F(buy_usdc, buy_ustb), tx_time("tx-93")
    p2, t2 = F(sell_usdc, sell_ustb), tx_time("tx-113")
    ustb_months = [m for m in labels if (as_int(M[m].get("balanceOf USTB")) or 0) > 0]
    check("the fund bought %s USTB for %s USDC and redeemed the same amount for %s USDC, and held USTB only at month ends between the two" % (
        fmt(units(buy_ustb, 6), 6), fmt(units(buy_usdc, 6)), fmt(units(sell_usdc, 6))),
          buy_ustb == sell_ustb and all(t1 <= mtime[m] <= t2 for m in ustb_months),
          "price %s then %s USDC per USTB, months %s" % (fmt(p1, 4), fmt(p2, 4), ", ".join(ustb_months)))

    def ustb_nav(ts):
        return p1 + (p2 - p1) * F(ts - t1, t2 - t1)

    # ---- month-end values -----------------------------------------------------------------------------
    month_rows, chart_rows = [], []
    mvals = {}
    for m in labels:
        has_ustb = m in ustb_months
        nav = ustb_nav(mtime[m]) if has_ustb else None
        v = value_reads(M[m], nav)
        mvals[m] = v
        g = {name: sum((v["lines"][k] for k in keys), F(0)) for name, keys in GROUPS}
        month_rows.append([m, mblock[m], iso(mtime[m])] + [plain(g[name], 2) for name, _ in GROUPS] +
                          [plain(v["total"], 2), plain(v["usde_supply"], 2), pct(v["total"] / v["usde_supply"], 3),
                           "yes" if has_ustb else "no", fmt(nav, 6) if nav else ""])
        chart_rows.append([m] + [plain(g[name] / 10 ** 6, 3) for name, _ in GROUPS] + [plain(v["total"] / 10 ** 6, 3)])
    peak_ratio_m = max(labels, key=lambda m: mvals[m]["total"] / mvals[m]["usde_supply"])
    low_ratio_m = min(labels, key=lambda m: mvals[m]["total"] / mvals[m]["usde_supply"])
    log("highest month-end share of USDe %s%% in %s; lowest %s%% in %s" % (
        pct(mvals[peak_ratio_m]["total"] / mvals[peak_ratio_m]["usde_supply"], 3), peak_ratio_m,
        pct(mvals[low_ratio_m]["total"] / mvals[low_ratio_m]["usde_supply"], 3), low_ratio_m))
    falls = [(a, b) for a, b in zip(labels, labels[1:]) if mvals[b]["total"] <= mvals[a]["total"]]
    rises = [mvals[b]["total"] - mvals[a]["total"] for a, b in zip(labels, labels[1:])]
    check("the fund's value rose from every month end to the next, and the read block's value is above September 2026's",
          not falls and total > mvals[labels[-1]]["total"], "smallest rise %s" % fmt(min(rises)) if not falls else ", ".join("%s to %s" % x for x in falls))
    flat = [m for m in labels if m >= "2025-09"]
    rng = (min(mvals[m]["total"] for m in flat), max(mvals[m]["total"] for m in flat))
    check("from September 2025 to September 2026 every month-end value was between $61.8 million and $62.1 million",
          rng[0] > 61800000 and rng[1] < 62100000, "%s to %s" % (fmt(rng[0]), fmt(rng[1])))
    usdtb_share_m = {m: (mvals[m]["lines"]["USDtb"] + mvals[m]["lp"]["usdtb"]) / mvals[m]["total"] for m in labels}
    window = [m for m in labels if "2024-12" <= m <= "2025-08"]
    top = max(window, key=lambda m: usdtb_share_m[m])
    check("from December 2024 to August 2025 USDtb, held directly and through the pool, stayed below 50%% of the fund at every month end, highest at %s%% in %s"
          % (pct(usdtb_share_m[top]), top), usdtb_share_m[top] < F(1, 2))

    # ---- flows and the sources of the fund's value ----------------------------------------------------
    flow_rows = []
    cat_net = defaultdict(F)    # stablecoins and BUIDL in less out, at $1, by category
    for r in sorted(real, key=lambda r: (int(r["block"]), int(r["log_index"]))):
        c = cls[r["tx"]]["category"]
        if r["token"] == NPM:
            amt, par = "", F(0)
        else:
            s = SYM[r["token"]]
            amt = units(int(r["value_raw"]), DEC[s])
            par = amt if s in DOLLAR else F(0)
        cat_net[c] += par if direction(r) == "in" else -par
        flow_rows.append([day(r["time_unix"]), r["block"], r["log_index"], r["tx"], c, direction(r),
                          SYM.get(r["token"], "Uniswap V3 position"),
                          r["token_id"] if r["token"] == NPM else plain(amt, DEC[SYM[r["token"]]]),
                          cp(r), cls[r["tx"]]["note"]])
    eth_value = lines["ETH"]
    pieces = []
    for c, (kind, name) in CATEGORIES.items():
        pieces.append((c, kind, name, cat_net[c] + (lines["CurveLP"] if c == "curve" else 0)))
    pieces.append(("eth", "in", "ETH held since January 2024, at Chainlink's price", eth_value))
    recon = sum(p[3] for p in pieces)
    check("the inflows, the result of every exchange and position, and ETH add up to the fund's value at the read block, to the unit",
          recon == total, "%s vs %s" % (fmt(recon, 6), fmt(total, 6)))
    payout_rows = [r for r in real if cls[r["tx"]]["category"] == "payout"]
    payout_sum = sum(units(int(r["value_raw"]), DEC[SYM[r["token"]]]) for r in payout_rows)
    last_payout = max(int(r["time_unix"]) for r in payout_rows)
    check("the sUSDe Payout Fund sent %d transfers worth %s, the last on %s, matching Blockworks Advisory's $35.7M and 12 December 2024"
          % (len(payout_rows), fmt(payout_sum), day(last_payout)), fmt(payout_sum / 10 ** 6, 1) == "35.7" and day(last_payout) == "2024-12-12")
    outs = [r for r in real if direction(r) == "out"]
    bad = [r["tx"] for r in outs if CATEGORIES[cls[r["tx"]]["category"]][0] != "sleeve" and not (cls[r["tx"]]["category"] == "dust" and int(r["value_raw"]) == 0)]
    check("every tracked token that left the fund went into a swap, a conversion or a pool or vault position, apart from transfers of 0 USDC", not bad, ", ".join(bad))
    last_in = max(int(r["time_unix"]) for r in real if direction(r) == "in")
    last_any_list = max(int(r["time_unix"]) for r in bs + rs)
    eth_bal = {M[m]["eth_getBalance"] for m in labels} | {S["eth_getBalance"]}
    check("no transfer of any token in either explorer's list came after November 3, 2025, and the fund held 0.3 ETH at every month end and at the read block",
          day(last_in) == day(last_any_list) == "2025-11-03" and eth_bal == {hex(3 * 10 ** 17)}, iso(last_any_list))
    interest_rows = [r for r in real if cls[r["tx"]]["category"] == "interest"]
    interest_sum = sum(units(int(r["value_raw"]), 18) for r in interest_rows)
    log("USDtb interest transfers %d, %s USDtb, %s to %s, from %s" % (len(interest_rows), fmt(interest_sum), day(min(int(r["time_unix"]) for r in interest_rows)),
                                                                     day(last_in), ", ".join("%s %d" % (k, n) for k, n in sorted(Counter(cp(r) for r in interest_rows).items()))))
    contributed = sum((a for c, k, n, a in pieces if c in ("payout", "safe_a", "other_in")), F(0))
    gains = sum((a for c, k, n, a in pieces if c in ("interest", "savings", "ustb", "uniswap", "buidl", "curve")), F(0))
    costs = sum((a for c, k, n, a in pieces if c in ("swap", "usdtb_mint", "safe_b")), F(0))
    small = sum((a for c, k, n, a in pieces if c in ("eth", "dust")), F(0))
    log("paid in %s, earned %s, costs %s, ETH and transfers under 1 USDC %s" % (fmt(contributed), fmt(gains), fmt(costs), fmt(small)))
    other_rows = [r for r in real if cls[r["tx"]]["category"] == "other_in"]
    log("transfers from addresses that are not contracts: " + "; ".join("%s %s on %s" % (fmt(units(int(r["value_raw"]), DEC[SYM[r["token"]]])), SYM[r["token"]], day(r["time_unix"])) for r in other_rows))
    since = mvals["2025-09"]
    d_total = total - since["total"]
    d_curve = lines["CurveLP"] - since["lines"]["CurveLP"]
    d_eth = lines["ETH"] - since["lines"]["ETH"]
    last_interest = sum(units(int(r["value_raw"]), 18) for r in interest_rows if day(r["time_unix"]) == "2025-11-03")
    d_rest = d_total - d_curve - last_interest - d_eth
    check("from the end of September 2025 to the read block the value rose by the last interest transfer, the pool share's gain and the change in the ETH's value, to the unit",
          d_rest == 0, "rise %s, interest %s, pool %s, ETH %s" % (fmt(d_total), fmt(last_interest), fmt(d_curve), fmt(d_eth)))
    migrated = sum(-x[1] for x in wd)
    sdai_left = dep[0][1] - migrated
    log("sDAI: %s shares deposited, %s migrated, %s sold on 2025-09-04" % (fmt(units(dep[0][1], 18)), fmt(units(migrated, 18)), fmt(units(sdai_left, 18))))
    mint_rows = [r for t in txs if cls[t]["category"] == "usdtb_mint" for r in legs[t]]
    usdtb_from_buidl = sum(units(int(r["value_raw"]), 18) for t in ("tx-60", "tx-61", "tx-62", "tx-66") for r in legs[t] if T_(r, "USDtb"))
    buidl_out = sum(units(int(r["value_raw"]), 6) for t in ("tx-60", "tx-61", "tx-62", "tx-66") for r in legs[t] if T_(r, "BUIDL"))
    usdtb_for_usdc = sum(units(int(r["value_raw"]), 18) for r in mint_rows if T_(r, "USDtb")) - usdtb_from_buidl
    usdc_for_usdtb = sum(units(int(r["value_raw"]), 6) for r in mint_rows if T_(r, "USDC"))
    log("USDtb minted: %s for %s BUIDL, %s for %s USDC" % (fmt(usdtb_from_buidl), fmt(buidl_out), fmt(usdtb_for_usdc), fmt(usdc_for_usdtb)))

    # Uniswap fees from the position manager's records: Collect less DecreaseLiquidity.
    dec0 = sum(x[3] for pid in uni_ev for x in uni_ev[pid] if x[1] == "DecreaseLiquidity")
    dec1 = sum(x[4] for pid in uni_ev for x in uni_ev[pid] if x[1] == "DecreaseLiquidity")
    col0 = sum(x[3] for pid in uni_ev for x in uni_ev[pid] if x[1] == "Collect")
    col1 = sum(x[4] for pid in uni_ev for x in uni_ev[pid] if x[1] == "Collect")
    inc0 = sum(x[3] for pid in uni_ev for x in uni_ev[pid] if x[1] == "IncreaseLiquidity")
    inc1 = sum(x[4] for pid in uni_ev for x in uni_ev[pid] if x[1] == "IncreaseLiquidity")
    uni_fees = units(col0 - dec0, 18) + units(col1 - dec1, 6)
    uni_principal = units(dec0 - inc0, 18) + units(dec1 - inc1, 6)
    check("the Uniswap line from the transfers equals the Collect amounts less the IncreaseLiquidity amounts in the position manager's records",
          uni_fees + uni_principal == cat_net["uniswap"], "fees %s, tokens %s" % (fmt(uni_fees), fmt(uni_principal)))

    # ---- comparison with published figures --------------------------------------------------------------
    usdtb_direct = lines["USDtb"]
    me = lambda m: mvals[m]["total"]
    lp_m = lambda m: mvals[m]["lines"]["CurveLP"]
    D_ = lambda x: F(str(x)) * 10 ** 6
    comp = [
        ("2025-04-25", "T555 Ethena Labs proposal", "fund", D_("60.9"), "0.1", me("2025-04"), "month end 2025-04"),
        ("2025-04-25", "T555 LlamaRisk reply, its dashboard, USTB", "USTB", D_("5.2"), "0.1", mvals["2025-04"]["lines"]["USTB"], "month end 2025-04, USTB at the interpolated price"),
        ("2025-04-25", "T555 LlamaRisk reply, its dashboard, USDtb", "USDtb", D_("19.2"), "0.1", mvals["2025-04"]["lines"]["USDtb"], "month end 2025-04"),
        ("2025-04-25", "T555 LlamaRisk reply, its dashboard, Curve pool position", "pool", D_("20"), "1", lp_m("2025-04"), "month end 2025-04"),
        ("2025-04-25", "T555 LlamaRisk reply, its dashboard, sUSDS", "sUSDS", D_("14.1"), "0.1", mvals["2025-04"]["lines"]["sUSDS"], "month end 2025-04"),
        ("2025-04-25", "T555 LlamaRisk reply, its dashboard, sDAI", "sDAI", D_("2.3"), "0.1", mvals["2025-04"]["lines"]["sDAI"], "month end 2025-04"),
        ("2025-07-03", "T613 governance update for June 2025", "fund", D_("61.1"), "0.1", me("2025-06"), "month end 2025-06"),
        ("2025-08-12", "T670 governance update for July 2025", "fund", D_("61.2"), "0.1", me("2025-07"), "month end 2025-07"),
        ("2025-08-26", "T685 USDtb in the wallet", "USDtb", F(19710412), "0.000001", F(balance_at("USDtb", 23225622), 10 ** 18), "balance from August 15 to September 3, 2025"),
        ("2025-08-26", "T685 USTB", "USTB", F(5319310), "0.000001", units(sell_usdc, 6), "USDC received for it on August 26, 2025"),
        ("2025-08-26", "T685 Curve pool position", "pool", F(19995255), "0.000001", lp_m("2025-08"), "month end 2025-08"),
        ("2025-08-26", "T685 sUSDS", "sUSDS", F(14328881), "0.000001", mvals["2025-08"]["lines"]["sUSDS"], "month end 2025-08"),
        ("2025-09-04", "T689 governance update for August 2025", "fund", D_("61.7"), "0.1", me("2025-08"), "month end 2025-08"),
        ("2025-09-04", "T689 governance update for August 2025, other passage", "fund", D_("62"), "1", me("2025-08"), "month end 2025-08"),
        ("2025-10-09", "T703 total", "fund", D_("61.84"), "0.01", me("2025-09"), "month end 2025-09"),
        ("2025-10-09", "T703 USDtb", "USDtb", D_("41.8"), "0.1", mvals["2025-09"]["lines"]["USDtb"], "month end 2025-09"),
        ("2025-10-09", "T703 Curve pool position", "pool", D_("19.9"), "0.1", lp_m("2025-09"), "month end 2025-09"),
        ("2025-10-09", "T704 governance update for September 2025", "fund", D_("62"), "1", me("2025-09"), "month end 2025-09"),
        ("2025-11-03", "T709 total", "fund", D_("61.88"), "0.01", me("2025-10"), "month end 2025-10"),
        ("2025-12-09", "T727 total", "fund", D_("62.08"), "0.01", me("2025-11"), "month end 2025-11"),
        ("2026-01-15", "T734 governance update for December 2025", "fund", D_("62.09"), "0.01", me("2025-12"), "month end 2025-12"),
        ("2026-02-07", "T748 total", "fund", D_("62"), "1", me("2026-01"), "month end 2026-01"),
        ("2026-02-07", "T748 USDtb", "USDtb", D_("41.93"), "0.01", usdtb_direct, "balance from November 3, 2025 to the read block"),
        ("2026-02-07", "T748 Curve pool position", "pool", D_("19.99"), "0.01", lp_m("2026-01"), "month end 2026-01"),
        ("2026-03-06", "T753 governance update, summary", "fund", D_("62.51"), "0.01", me("2026-02"), "month end 2026-02"),
        ("2026-03-06", "T753 governance update, body", "fund", D_("62.54"), "0.01", me("2026-02"), "month end 2026-02"),
        ("2026-04-02", "T775 total", "fund", D_("62"), "1", me("2026-03"), "month end 2026-03"),
        ("2026-04-02", "T775 USDtb", "USDtb", D_("41.98"), "0.01", usdtb_direct, "balance from November 3, 2025 to the read block"),
        ("2026-04-02", "T775 Curve pool position", "pool", D_("20.02"), "0.01", lp_m("2026-03"), "month end 2026-03"),
        ("2026-04-23", "T791 attestation of April 23, 2026", "fund", D_("62.04"), "0.01", me("2026-04"), "month end 2026-04"),
        ("2026-04-23", "T791 attestation of April 23, 2026, USDtb", "USDtb", D_("41.98"), "0.01", usdtb_direct, "balance from November 3, 2025 to the read block"),
        ("2026-04-23", "T791 attestation of April 23, 2026, Curve pool position", "pool", D_("20.02"), "0.01", lp_m("2026-04"), "month end 2026-04"),
        ("2026-04-30", "T791 attestation of April 30, 2026", "fund", D_("62.06"), "0.01", me("2026-04"), "month end 2026-04"),
        ("2026-06-05", "T796 governance update for May 2026", "fund", D_("62.5"), "0.1", me("2026-05"), "month end 2026-05"),
        ("2026-07-17", "T808 governance update for June 2026", "fund", D_("62.0"), "0.1", me("2026-06"), "month end 2026-06"),
    ]
    higher = {"T753 governance update, summary", "T753 governance update, body", "T796 governance update for May 2026"}
    gap = {src: (mine - pub) / pub for d_, src, what, pub, prec, mine, basis in comp}
    # The gap beyond rounding counts only what lies beyond half the published figure's last digit, so $62.0 million
    # matches anything from $61.95 million to $62.05 million.
    beyond = {src: max(F(0), abs(mine - pub) - F(prec) * 10 ** 6 / 2) / pub for d_, src, what, pub, prec, mine, basis in comp}
    rest = [src for src in beyond if src not in higher]
    worst = max(rest, key=lambda s_: beyond[s_])
    within = sum(1 for s_ in rest if beyond[s_] < F(1, 1000))
    hi_gaps = sorted(pub - mine for d_, src, what, pub, prec, mine, basis in comp if src in higher)
    check("of the %d published figures, the %d other than three governance update figures are within 0.35%% of the onchain values beyond their rounding and %d within 0.1%%, and the three are $0.4 million to $0.5 million above them"
          % (len(comp), len(rest), within), len(comp) == len(set(gap)) == 35 and beyond[worst] < F(35, 10000)
          and all(F(4, 10) * 10 ** 6 < g < F(5, 10) * 10 ** 6 for g in hi_gaps),
          "largest other gap beyond rounding %s%% (%s), higher figures by %s" % (pct(beyond[worst], 3), worst, ", ".join(fmt(g) for g in hi_gaps)))
    comp_rows = [[d_, src, what, plain(pub, 2), prec, plain(mine, 2), plain(mine - pub, 2), pct(gap[src], 3), pct(beyond[src], 3), basis]
                 for d_, src, what, pub, prec, mine, basis in comp]
    sdai_aug = mvals["2025-08"]["lines"]["sDAI"]
    check("at the end of August 2025 the fund still held sDAI worth %s, which the August 2025 update's list left out" % fmt(sdai_aug),
          sdai_aug > 2300000 and "The list named no sDAI" in open(os.path.join(WEB, "ethena_governance_forum_2026-10-12.txt"), encoding="utf-8").read())

    # ---- write ----------------------------------------------------------------------------------------
    if not all(ok for _, ok, _ in CHECKS):
        with open(failed_log, "w", encoding="utf-8") as f:
            f.write("\n".join(LOG) + "\n")
        print("\n%d of %d checks failed; out/ not updated" % (sum(1 for c in CHECKS if not c[1]), len(CHECKS)))
        sys.exit(1)

    hold = [
        ["USDtb held directly", plain(lines["USDtb"], 6), "USDtb", "1", plain(lines["USDtb"], 2), pct(lines["USDtb"] / total, 4)],
        ["Curve USDtb/USDC pool, USDC side", plain(lp["usdc"], 6), "USDC", "1", plain(lp["usdc"], 2), pct(lp["usdc"] / total, 4)],
        ["Curve USDtb/USDC pool, USDtb side", plain(lp["usdtb"], 6), "USDtb", "1", plain(lp["usdtb"], 2), pct(lp["usdtb"] / total, 4)],
        ["ETH", plain(snapv["eth"], 6), "ETH", plain(snapv["eth_price"], 2), plain(lines["ETH"], 2), pct(lines["ETH"] / total, 4)],
        ["USDS", plain(snapv["bal"]["USDS"], 6), "USDS", "1", plain(lines["USDS"], 2), pct(lines["USDS"] / total, 4)],
        ["BUIDL", plain(snapv["bal"]["BUIDL"], 6), "BUIDL", "1", plain(lines["BUIDL"], 2), pct(lines["BUIDL"] / total, 4)],
        ["USDC", plain(snapv["bal"]["USDC"], 6), "USDC", "1", plain(lines["USDC"], 2), pct(lines["USDC"] / total, 4)],
        ["Uniswap V3 positions (4, empty)", "0", "", "", "0.00", "0.0000"],
        ["Total", "", "", "", plain(total, 2), "100.0000"],
    ]
    write_csv(os.path.join(OUT, "holdings.csv"), ["line", "amount", "unit", "price_usd", "value_usd", "share_pct"], hold)
    write_csv(os.path.join(OUT, "month_end.csv"), ["month", "block", "block_time_utc"] + [name for name, _ in GROUPS] +
              ["total_usd", "usde_supply", "fund_share_of_usde_pct", "ustb_held", "ustb_price_estimate"], month_rows)
    write_csv(os.path.join(OUT, "chart_data.csv"), ["month"] + [name + " ($M)" for name, _ in GROUPS] + ["total ($M)"], chart_rows)
    write_csv(os.path.join(OUT, "flows.csv"), ["date_utc", "block", "log_index", "tx", "category", "direction", "token", "amount", "counterparty", "note"], flow_rows)
    src_rows = [[c, kind, name, plain(amount, 2)] for c, kind, name, amount in pieces]
    src_rows += [["paid_in", "subtotal", "Paid in by the sUSDe Payout Fund, Safe 0xa2af...cced92 and the two addresses", plain(contributed, 2)],
                 ["earned", "subtotal", "Earned by the vaults, funds, pools and USDtb interest", plain(gains, 2)],
                 ["costs", "subtotal", "Cost of minting USDtb, swaps and conversions", plain(costs, 2)],
                 ["total", "", "Value at the read block", plain(total, 2)]]
    write_csv(os.path.join(OUT, "sources_of_value.csv"), ["category", "kind", "line", "usd"], src_rows)
    write_csv(os.path.join(OUT, "risk_committee_comparison.csv"),
              ["date", "source", "item", "published_usd", "published_precision_musd", "onchain_usd", "difference_usd", "difference_pct",
               "beyond_rounding_pct", "onchain_basis"], comp_rows)
    unl_b = Counter((r["token"], "in" if r["to"] == RF else "out") for r in unlisted_rows)
    unl_r = Counter((r["token"], "in" if r["to"] == RF else "out") for r in rs if r["token"] not in listed)
    write_csv(os.path.join(OUT, "unlisted_tokens.csv"), ["token", "name_as_listed", "direction", "transfers_blockscout", "transfers_routescan"],
              [[t, names[t]["symbol"] if t in names else "", d_, unl_b[(t, d_)], unl_r[(t, d_)]] for (t, d_) in sorted(set(unl_b) | set(unl_r))])
    # Episodes: every classified transaction grouped by its episode and category, with the tokens sent and received.
    ep = defaultdict(lambda: {"first": None, "last": None, "flows": defaultdict(F)})
    for r in real:
        e = ep[(cls[r["tx"]]["episode"], cls[r["tx"]]["category"])]
        t = int(r["time_unix"])
        e["first"] = t if e["first"] is None else min(e["first"], t)
        e["last"] = t if e["last"] is None else max(e["last"], t)
        if r["token"] == NPM:
            e["flows"][("in", "Uniswap V3 position")] += 1
        else:
            s_ = SYM[r["token"]]
            e["flows"][(direction(r), s_)] += units(int(r["value_raw"]), DEC[s_])
    ep_rows = []
    for (episode, c), e in sorted(ep.items(), key=lambda kv: (kv[1]["first"], kv[0][1])):
        outs_ = "; ".join("%s %s" % (plain(v_, 6), sym) for (d_, sym), v_ in sorted(e["flows"].items()) if d_ == "out")
        ins_ = "; ".join("%s %s" % (plain(v_, 6) if sym != "Uniswap V3 position" else int(v_), sym) for (d_, sym), v_ in sorted(e["flows"].items()) if d_ == "in")
        ep_rows.append([episode, c, day(e["first"]), day(e["last"]), outs_, ins_])
    write_csv(os.path.join(OUT, "episodes.csv"), ["episode", "category", "first_utc", "last_utc", "sent", "received"], ep_rows)
    buidl_oct = mvals["2024-10"]["lines"]["BUIDL"]
    log("Uniswap deposits %s USDe and %s USDT; BUIDL bought %s, %s%% of the fund at the end of October 2024" % (
        fmt(units(inc0, 18)), fmt(units(inc1, 6)), fmt(buidl_oct), pct(buidl_oct / mvals["2024-10"]["total"])))
    res = {
        "read_block": READ_BLOCK, "read_block_time_utc": iso(snap_time), "value_usd": plain(total, 2),
        "usdtb_direct": plain(lines["USDtb"], 6), "pool_share_pct": pct(lp["share"], 4), "pool_value_usd": plain(lines["CurveLP"], 2),
        "pool_usdc": plain(lp["usdc"], 6), "pool_usdtb": plain(lp["usdtb"], 6), "pool_cost_usd": "19980948",
        "usde_supply": plain(snapv["usde_supply"], 6), "fund_share_of_usde_pct": pct(ratio, 4),
        "usdtb_supply": plain(snapv["usdtb_supply"], 6), "usdtb_held": plain(usdtb_held, 6),
        "usdtb_share_of_fund_pct": pct(usdtb_share, 4), "usdtb_share_of_supply_pct": pct(usdtb_held / snapv["usdtb_supply"], 4),
        "eth": plain(snapv["eth"], 6), "eth_price": plain(snapv["eth_price"], 2), "eth_price_updated_utc": iso(snapv["eth_updated"]),
        "payout_transfers": len(payout_rows), "payout_sum": plain(payout_sum, 6), "last_payout_utc": iso(last_payout),
        "interest_transfers": len(interest_rows), "interest_sum": plain(interest_sum, 6), "last_inflow_utc": iso(last_in),
        "peak_ratio_month": peak_ratio_m, "peak_ratio_pct": pct(mvals[peak_ratio_m]["total"] / mvals[peak_ratio_m]["usde_supply"], 4),
        "low_ratio_month": low_ratio_m, "low_ratio_pct": pct(mvals[low_ratio_m]["total"] / mvals[low_ratio_m]["usde_supply"], 4),
        "ustb_buy_price": plain(p1, 6), "ustb_sell_price": plain(p2, 6), "ustb_units": plain(units(buy_ustb, 6), 6),
        "uniswap_fees": plain(uni_fees, 6), "uniswap_token_change": plain(uni_principal, 6),
        "uniswap_deposit_usde": plain(units(inc0, 18), 6), "uniswap_deposit_usdt": plain(units(inc1, 6), 6),
        "paid_in": plain(contributed, 6), "earned": plain(gains, 6), "costs": plain(costs, 6), "eth_and_dust": plain(small, 6),
        "change_since_sep_2025": plain(d_total, 6), "change_curve_since_sep_2025": plain(d_curve, 6), "change_eth_since_sep_2025": plain(d_eth, 6),
        "last_interest": plain(last_interest, 6), "sdai_deposited": plain(units(dep[0][1], 18), 6), "dai_deposited": plain(units(dep[0][2], 18), 6),
        "sdai_migrated": plain(units(migrated, 18), 6), "sdai_sold": plain(units(sdai_left, 18), 6), "sdai_aug_2025": plain(sdai_aug, 2),
        "usdtb_from_buidl": plain(usdtb_from_buidl, 6), "buidl_out": plain(buidl_out, 6), "usdtb_for_usdc": plain(usdtb_for_usdc, 6), "usdc_for_usdtb": plain(usdc_for_usdtb, 6),
        "usdtb_share_month_pct": {m: pct(usdtb_share_m[m], 2) for m in labels}, "usdtb_share_top_before_sep_2025": [top, pct(usdtb_share_m[top], 2)],
        "month_values": {m: plain(mvals[m]["total"], 2) for m in labels},
        "month_ratio_pct": {m: pct(mvals[m]["total"] / mvals[m]["usde_supply"], 4) for m in labels},
        "published_count": len(comp), "published_other_count": len(rest), "published_other_largest_beyond_rounding": [worst, pct(beyond[worst], 3)],
        "published_other_within_01_beyond_rounding": within,
        "published_higher_by": [plain(g, 2) for g in hi_gaps],
        "sources": {c: plain(a, 6) for c, k, n, a in pieces},
        "safe": {"threshold": threshold, "owners": owners, "version": version, "nonce": nonce, "executed": executed,
                 "reverted_exec": reverted_exec, "other_failed": other_failed, "sent_to_safe": sent_to_safe},
        "transfers": {"blockscout": len(bs), "tracked": len(real), "untracked": len(unlisted_rows), "routescan": len(rs),
                      "transactions_classified": len(txs), "lookalike_usdc_out": len(unl_out), "lookalike_usdc_tokens": len({r["token"] for r in unl_out}),
                      "other_tokens_in": len({r["token"] for r in unl_in}), "untracked_tokens_blockscout": len({r["token"] for r in unlisted_rows}),
                      "untracked_tokens_either": len({r["token"] for r in unlisted_rows} | {r["token"] for r in rs if r["token"] not in listed})},
        "checks": len(CHECKS),
    }
    with open(os.path.join(OUT, "results.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, sort_keys=True)
        f.write("\n")
    log("\nall %d checks passed" % len(CHECKS))
    with open(os.path.join(OUT, "run_log.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(LOG) + "\n")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # any failure before the tables are written leaves a log and keeps out/ as it was
        import traceback
        LOG.append("stopped with an error: " + repr(exc))
        LOG.append(traceback.format_exc())
        with open(os.path.join(OUT, "run_log_failed.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(LOG) + "\n")
        print("stopped with an error; out/ not updated. See out/run_log_failed.txt")
        sys.exit(1)
