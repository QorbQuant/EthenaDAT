#!/usr/bin/env python3
"""How much of the USDe on Avalanche C-Chain sat in EthenaPay wallets at the end of each UTC day, from the day the
token was deployed on Avalanche, August 8, 2025, to October 11, 2026, and how the USDe reached them.

Reads the files avax_usde_read.cjs wrote in inputs/chain/, the daily file of the chain recount published with the
site's EthenaPay adoption review, the dashboard's daily query and the text kept from the other pages read, checks them,
and works out the supply each group of holders held, its growth since the first EthenaPay wallet, and the flows into
and out of the wallets and the card settlement addresses. If any check fails the script writes its log to
run_log_failed.txt and stops before writing its tables, so out/ keeps the tables of the last clean run.
Python 3 standard library only. No network.
"""
import csv
import hashlib
import json
import re
import sys
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path

getcontext().prec = 60
HERE = Path(__file__).parent
INP = HERE / "inputs"
CH = INP / "chain"
RC = INP / "recount"
WEB = INP / "web"
OUT = HERE / "out"
E18 = Decimal(10) ** 18

USDE = "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34"
USDC = "0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e"
FACTORIES = ["0x313be708df16979d9e5fe9db5ac4969b8add7207", "0xac66ca9a79fb0d3c64cba44cd29610cd58602d6f"]
SETTLE = ["0x6070848bd19c37488d0516058f2933dd992733de", "0x3b3ffd99b87a2dee5ad244b75d5a8e266890fdb8"]
REWARDS = {"0xd0ec8cc7414f27ce85f8dece6b4a58225f273311": "yield", "0xab2b06efa6179e624f5e3b08b64978df114ff24f": "other_reward",
           "0xc9dd0d4351d3841a712f59cb4f1e88c3d500515b": "other_reward"}
RHINO = "0x5e023c31e1d3dcd08a1b3e8c96f6ef8aa8fcacd1"
POOL = "0x833e0ff43a8691f623cb8730ddb3e3180c7de08b"
P0, P1, P2 = "2025-08-08 to 2026-05-14", "2026-05-15 to 2026-10-05", "2026-10-06 to 2026-10-11"
WALLETS, SETTLEMENT, REWARD, RECIP, RH, PL, OTHER, MINT, BURN = ("ethenapay_wallets", "settlement", "reward_accounts", "settlement_recipients",
                                                                "rhino_fi_bridge_contract", "uniswap_v3_pool", "other_accounts", "minted", "burned")
OUTSIDE = {MINT, RECIP, RH, PL, OTHER}          # the recount's deposits come from anything but a wallet, a settlement address or a reward account

log_lines = []
failures = []


def log(msg=""):
    log_lines.append(msg)
    print(msg)


def check(name, ok, detail=""):
    log(("ok    " if ok else "FAIL  ") + name + (f"  ({detail})" if detail else ""))
    if not ok:
        failures.append(name)


def table(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def usd(wei, places=2):
    return (Decimal(wei) / E18).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def pct(part, whole, places=2):
    return (Decimal(part) * 100 / Decimal(whole)).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


R = {}
log("USDe on Avalanche C-Chain and EthenaPay wallets")
log("Inputs")
for m in table(INP / "manifest.csv"):
    p = INP / m["file"]
    check(f"input {m['file']} matches its SHA-256", p.exists() and p.stat().st_size == int(m["bytes"]) and sha(p) == m["sha256"])
script_sha = sha(HERE / "avax_usde_read.cjs")
for m in table(INP / "chain_manifest.csv"):
    p = CH / m["file"]
    check(f"chain file {m['file']} matches its SHA-256", p.exists() and p.stat().st_size == int(m["bytes"]) and sha(p) == m["sha256"])
    check(f"chain file {m['file']} was written by this avax_usde_read.cjs", m["script_sha256"] == script_sha)
meta = json.loads((CH / "meta.json").read_text())
days = table(CH / "daily.csv")
holders = table(CH / "holders.csv")
flows = table(CH / "flows.csv")
recount = table(RC / "daily_chain.csv")
for r in days:
    for k in r:
        if k != "date":
            r[k] = int(r[k])
for r in flows:
    r["transfers"], r["usde_wei"] = int(r["transfers"]), int(r["usde_wei"])
day = {r["date"]: r for r in days}
last = days[-1]

# ---------------------------------------------------------------- the chain read
log()
log("The chain read")
check("the read is of USDe on Avalanche C-Chain", meta["token"] == USDE and meta["chain"] == "Avalanche C-Chain")
check("the read runs from the token's deployment on August 8, 2025 to the last block of October 11, 2026 UTC",
      meta["deploy_block_time"].startswith("2025-08-08") and meta["end_block_time"] == "2026-10-11T23:59:59Z" and meta["next_block_time"] >= "2026-10-12T00:00:00Z"
      and meta["first_day"] == "2025-08-08" and meta["last_day"] == "2026-10-11", f"blocks {meta['deploy_block']:,} to {meta['end_block']:,}")
d0 = date.fromisoformat(meta["first_day"])
check("daily.csv has one row for each of the 430 days", len(days) == meta["days"] == 430 and [r["date"] for r in days] == [(d0 + timedelta(i)).isoformat() for i in range(430)])
run, ok = 0, True
for r in days:
    run += r["minted_wei"] - r["burned_wei"]
    ok &= run == r["supply_wei"]
check("each day's supply is all USDe minted less all USDe burned to the end of that day", ok)
parts = ("wallets_held_wei", "settlement_held_wei", "reward_accounts_held_wei", "settlement_recipients_held_wei", "other_held_wei")
check("the five groups of holders add up to the supply on every day", all(sum(r[k] for k in parts) == r["supply_wei"] for r in days))
check("the days add up to the read's totals", sum(r["transfers"] for r in days) == meta["transfer_logs_kept"] and sum(r["minted_wei"] for r in days) == int(meta["minted_wei"])
      and sum(r["burned_wei"] for r in days) == int(meta["burned_wei"]) and last["supply_wei"] == int(meta["supply_at_end_wei"]),
      f"{meta['transfer_logs_kept']:,} transfer logs, {usd(meta['minted_wei']):,} minted and {usd(meta['burned_wei']):,} burned")
check("the 63 records with no value were all checked against their receipts, none was in one, none touched EthenaPay, all fell in August and September 2025",
      meta["transfer_records_listed"] - meta["transfer_logs_kept"] == meta["records_with_no_value"] == meta["records_with_no_value_checked_against_receipts"] == 63
      and meta["records_with_no_value_found_in_their_receipts"] == 0 and meta["records_with_no_value_touching_ethenapay"] == 0
      and set(meta["records_with_no_value_by_month"]) <= {"2025-08", "2025-09"} and sum(meta["records_with_no_value_by_month"].values()) == 63)
check("each of the 63 records with no value had both an empty amount and an empty block hash",
      meta["records_with_no_value_empty_amount"] == meta["records_with_no_value_empty_block_hash"] == meta["records_with_no_value"] == 63)
tie = meta["tie_to_contract"]
tie_supply = int(tie["total_supply_wei"]) - int(tie["minted_after_wei"]) + int(tie["burned_after_wei"])
check("the supply at the end of October 11 ties to the token contract's totalSupply", tie_supply == last["supply_wei"] == int(tie["supply_at_end_from_contract_wei"]) and tie["equal"] is True
      and meta["end_block"] < tie["block_before"] <= tie["block_after"] and tie["records_with_no_value_after"] == 0,
      f"totalSupply {usd(tie['total_supply_wei']):,} read between blocks {tie['block_before']:,} and {tie['block_after']:,}, with no USDe minted or burned between them, "
      f"plus {usd(tie['burned_after_wei']):,} burned and less {usd(tie['minted_after_wei']):,} minted after October 11 up to block {tie['block_after']:,}")
ex = (WEB / "explorer_contracts_2026-10-12.txt").read_text()
fac = {a: (int(b), t) for a, b, t in re.findall(r"^factory (0x[0-9a-f]{40}) created block (\d+) time (\S+)", ex, re.M)}
start_block = int(re.search(r"const FACTORY_START = (\d+);", (HERE / "avax_usde_read.cjs").read_text()).group(1))
check("both wallet factories were created after the block where the read of their internal transactions starts, the first on May 15, 2026, so the read misses no wallet",
      set(fac) == set(FACTORIES) and all(b > start_block for b, _ in fac.values()) and min(fac.values())[1].startswith("2026-05-15"),
      f"read from block {start_block:,}, factories created in " + ", ".join(f"block {b:,} on {t[:10]}" for b, t in sorted(fac.values())))
check("no wallet existed or held USDe before May 15, 2026", all(r["wallets_created"] == 0 and r["wallets_held_wei"] == 0 for r in days if r["date"] < "2026-05-15")
      and day["2026-05-15"]["wallets_created"] > 0)
other_made = meta["factory_created_not_create2"]
made_by = {a: f for a, f in re.findall(r"^created (0x[0-9a-f]{40}) factory (0x[0-9a-f]{40}) in the transaction that created that factory", ex, re.M)}
check("every contract the factories created is a wallet made with CREATE2 or one of three made with CREATE in a factory's own creating transaction",
      meta["factory_rows_not_creations"] == 0 and sum(meta["factory_rows"]) == meta["wallets"] + len(other_made) and len(other_made) == 3
      and all(x["type"] == "create" and made_by.get(x["address"]) == x["factory"] and x["block"] == fac[x["factory"]][0] for x in other_made)
      and set(made_by) == {x["address"] for x in other_made},
      f"{sum(meta['factory_rows']):,} creations, {meta['wallets']:,} wallets")
sql_text = (RC / "05_daily_metrics_eb01f5d.sql").read_text().lower()
hand = re.findall(r"0x[0-9a-f]{40}", re.search(r"not in \((.*?)\)", sql_text, re.S).group(1))
own = re.search(r"^created (0x[0-9a-f]{40}) factory none, by the account that created the second factory, block (\d+) time (\S+)", ex, re.M)
check("the dashboard's query removes by hand the second factory's two CREATE contracts and a contract the second factory's creator made without a factory, "
      "and not the first factory's CREATE contract",
      len(hand) == 3 and {x["address"] for x in other_made if x["factory"] == FACTORIES[1]} == set(hand) - {own.group(1)}
      and own.group(1) in hand and not any(x["address"] in hand for x in other_made if x["factory"] == FACTORIES[0])
      and int(own.group(2)) < fac[FACTORIES[1]][0], f"made at block {int(own.group(2)):,}, the second factory at {fac[FACTORIES[1]][0]:,}")
moved = dict((a, (int(x), int(y))) for a, x, y in re.findall(r"^transfers (0x[0-9a-f]{40}) from (\d+) to (\d+)$", ex, re.M))
check("none of those four contracts sent or received USDe to the end of October 11",
      set(moved) == {x["address"] for x in other_made} | set(hand) and all(v == (0, 0) for v in moved.values()))

# ---------------------------------------------------------------- holders at the end of October 11
log()
log("Holders at the end of October 11, 2026 UTC")
H = {}
for r in holders:
    H.setdefault(r["group"], []).append(r)
g1 = lambda name: H[name][0]
bal = lambda r: int(r["balance_wei"])
listed_other = H["other"]
listed_recip = H["settlement_recipients"]
check("holders.csv holds no address", not re.search(r"0x[0-9a-fA-F]{40}", (CH / "holders.csv").read_text()))
check("the group balances in holders.csv match the last day of daily.csv",
      bal(g1("ethenapay_wallets")) == last["wallets_held_wei"] and bal(g1("settlement")) == last["settlement_held_wei"]
      and bal(g1("reward_accounts")) == last["reward_accounts_held_wei"]
      and sum(bal(r) for r in listed_recip) + bal(g1("settlement_recipients_rest")) == last["settlement_recipients_held_wei"]
      and sum(bal(r) for r in listed_other) + bal(g1("other_rest")) == last["other_held_wei"])
n_hold = sum(int(r["holders"]) for r in holders)
check("the holders add up to the accounts with USDe at the end of the day", n_hold == meta["holders_at_end"] == last["holders"]
      and int(g1("ethenapay_wallets")["holders"]) == last["wallets_with_usde"], f"{n_hold:,} accounts, {last['wallets_with_usde']:,} of them wallets")
check("the listed holders are ranked by balance, the ten largest holders outside EthenaPay and every settlement recipient",
      all([int(r["rank"]) for r in grp] == list(range(1, len(grp) + 1)) and all(bal(a) >= bal(b) for a, b in zip(grp, grp[1:])) for grp in (listed_other, listed_recip))
      and len(listed_other) == 10)
check("every listed settlement recipient received USDe only from the settlement addresses", len(listed_recip) == meta["settlement_recipients"] == 3
      and int(g1("settlement_recipients_rest")["holders"]) == 0 and all(int(r["received_wei"]) == int(r["received_from_settlement_wei"]) and int(r["minted_to_wei"]) == 0
                                                                       and int(r["received_from_wallets_wei"]) == 0 for r in listed_recip))
rh = next(r for r in listed_other if r["label"] == "rhino.fi bridge contract")
pl = next(r for r in listed_other if r["label"] == "UniswapV3Pool contract")
check("the rhino.fi bridge contract and the Uniswap v3 pool are among the listed holders, and both are contracts", rh["is_contract"] == "1" and pl["is_contract"] == "1",
      f"ranks {rh['rank']} and {pl['rank']}")

# ---------------------------------------------------------------- flows between groups
log()
log("Flows between groups")


def f(frm=None, to=None, periods=(P0, P1, P2), key="usde_wei"):
    frm = {frm} if isinstance(frm, str) else frm
    to = {to} if isinstance(to, str) else to
    return sum(r[key] for r in flows if r["period"] in periods and (frm is None or r["from_group"] in frm) and (to is None or r["to_group"] in to))


check("flows.csv has the read's three periods and counts every transfer log once", meta["flow_periods"] == [P0, P1, P2]
      and {r["period"] for r in flows} == {P0, P1, P2} and f(key="transfers") == meta["transfer_logs_kept"])
check("the flows out of the zero address and into it are the USDe minted and burned", f(MINT) == int(meta["minted_wei"]) and f(to=BURN) == int(meta["burned_wei"])
      and f(to=MINT) == 0 and f(BURN) == 0)
ok = True
for per, first, end in ((P0, None, "2026-05-14"), (P1, "2026-05-14", "2026-10-05"), (P2, "2026-10-05", "2026-10-11")):
    change = day[end]["supply_wei"] - (day[first]["supply_wei"] if first else 0)
    ok &= f(MINT, periods=(per,)) - f(to=BURN, periods=(per,)) == change
check("in each period the USDe minted less the USDe burned equals the change in supply", ok)
end_bal = {WALLETS: bal(g1("ethenapay_wallets")), SETTLEMENT: bal(g1("settlement")), REWARD: bal(g1("reward_accounts")),
           RECIP: last["settlement_recipients_held_wei"], RH: bal(rh), PL: bal(pl), OTHER: last["other_held_wei"] - bal(rh) - bal(pl)}
check("for every group, USDe in less USDe out gives its balance at the end", all(f(to=g) - f(g) == v for g, v in end_bal.items()))
check("the rhino.fi bridge contract's flows match its row in holders.csv",
      f(to=RH) == int(rh["received_wei"]) and f(MINT, RH) == int(rh["minted_to_wei"]) and f(RH) == int(rh["sent_wei"]) and f(RH, WALLETS) == int(rh["sent_to_wallets_wei"])
      and f(WALLETS, RH) == int(rh["received_from_wallets_wei"]) and f(RH, BURN) == int(rh["burned_wei"]) == 0)
check("the Uniswap v3 pool's flows match its row in holders.csv", f(to=PL) == int(pl["received_wei"]) and f(PL) == int(pl["sent_wei"]) and f(MINT, PL) == 0)
check("the settlement addresses sent the three recipients what holders.csv says they received from them",
      f(SETTLEMENT, RECIP) == sum(int(r["received_from_settlement_wei"]) for r in listed_recip))
check("the wallets' deposits match the read's total", f(OUTSIDE, WALLETS) == int(meta["wallets_received_from_outside_wei"]),
      f"{usd(meta['wallets_received_from_outside_wei']):,} USDe")
check("the USDe minted into wallets and burned from them match the daily columns",
      f(MINT, WALLETS) == sum(r["minted_to_wallets_wei"] for r in days) and f(WALLETS, BURN) == sum(r["burned_from_wallets_wei"] for r in days))

# ---------------------------------------------------------------- the published recount, May 15 to October 5
log()
log("The published recount, May 15 to October 5, 2026")
check("the recount covers the 144 days from May 15 to October 5 with no balance below zero",
      len(recount) == 144 and recount[0]["date"] == "2026-05-15" and recount[-1]["date"] == "2026-10-05" and all(int(r["negative_balances"]) == 0 for r in recount))
check("the USDe in wallets matches the recount to the wei on all 144 days", all(day[r["date"]]["wallets_held_wei"] == int(r["held_wei"]) for r in recount),
      f"{usd(recount[-1]['held_wei']):,} USDe on October 5")
check("the wallets created match the recount on all 144 days", all(day[r["date"]]["wallets_created"] == int(r["wallets_created"]) for r in recount))
check("the wallets holding USDe match the recount's funded wallets on all 144 days", all(day[r["date"]]["wallets_with_usde"] == int(r["funded"]) for r in recount))
S = lambda k: sum(int(r[k]) for r in recount)
WD_TO = {BURN, RECIP, RH, PL, OTHER, REWARD}
for name, mine, theirs in (("deposits", f(OUTSIDE, WALLETS, (P1,)), S("deposits_wei")), ("withdrawals", f(WALLETS, WD_TO, (P1,)), S("withdrawals_wei")),
                           ("card spend", f(WALLETS, SETTLEMENT, (P1,)), S("card_spend_wei")), ("returns, the recount's reversals,", f(SETTLEMENT, WALLETS, (P1,)), S("reversals_wei")),
                           ("rewards", f(REWARD, WALLETS, (P1,)), S("yield_wei") + S("other_rewards_wei")), ("transfers between wallets", f(WALLETS, WALLETS, (P1,)), S("internal_wei"))):
    check(f"the {name} from May 15 to October 5 match the recount to the wei", mine == theirs, f"{usd(mine):,} USDe")
spend_events = S("spend_events")
card_n = f(WALLETS, SETTLEMENT, (P1,), "transfers")
gap_days = [(r["date"], int(r["card_spend_wei"]) - int(r["spend_cents"]) * 10 ** 16) for r in recount if int(r["card_spend_wei"]) != int(r["spend_cents"]) * 10 ** 16]
check("the recount's card spend events to October 5 are one fewer than the card payments, and their amounts differ only on September 24, by 5 USDe",
      card_n - spend_events == 1 and gap_days == [("2026-09-24", 5 * 10 ** 18)], f"{spend_events:,} spend events, {card_n:,} card payments")
R["recount_spend"] = {"spend_events": spend_events, "card_payments": card_n, "gap_date": gap_days[0][0], "gap_usde": str(usd(gap_days[0][1]))}

# ---------------------------------------------------------------- the names and addresses used
log()
log("Names and addresses")
sql = (RC / "05_daily_metrics_eb01f5d.sql").read_text().lower()
check("the dashboard's daily query names the two factories, the two settlement addresses, the three reward accounts and USDe",
      all(a in sql for a in FACTORIES + SETTLE + list(REWARDS) + [USDE]) and all(f"({a}, '{lab}')" in sql for a, lab in REWARDS.items()))
js = (HERE / "avax_usde_read.cjs").read_text().lower()
js_const = lambda name: re.findall(r"0x[0-9a-f]{40}", re.search(r"const " + name.lower() + r" = \[(.*?)\];", js, re.S).group(1))
check("the read uses the query's addresses", js_const("FACTORIES") == FACTORIES and js_const("SETTLE") == SETTLE and js_const("REWARDS") == list(REWARDS)
      and f"const usde = '{USDE}'" in js and f"'{RHINO}': 'rhino.fi bridge contract'" in js and f"'{POOL}': 'uniswapv3pool contract'" in js)
rhino_txt = (WEB / "rhino_bridge_configs_avalanche_2026-10-12.txt").read_text()
cfg = json.loads(re.search(r"^AVALANCHE (\{.*\})$", rhino_txt, re.M).group(1))
tok = json.loads(re.search(r"^AVALANCHE_USDE (\[.*\])$", rhino_txt, re.M).group(1))
check("rhino.fi's bridge configuration gives the labeled contract as its Avalanche contract and USDe at the token's address",
      cfg["contractAddress"].lower() == RHINO and cfg["networkId"] == "43114" and tok[0][1]["address"].lower() == USDE and tok[0][1]["decimals"] == 18)
keys_txt = (WEB / "ethena_key_addresses_2026-10-12.txt").read_text()
check("Ethena's key addresses page gives the token's address for USDe on most L2s", "Most L2s" in keys_txt and USDE in keys_txt.lower())
ex = (WEB / "explorer_contracts_2026-10-12.txt").read_text()
name_of = dict(re.findall(r"^address (0x[0-9a-f]{40}) read_at \S+ ContractName (\S+)", ex, re.M))
calls = {(t, d): v for t, d, v in re.findall(r"^to (0x[0-9a-f]{40}) data (0x[0-9a-f]{8}) \S+ read_at \S+ result (\S+)", ex, re.M)}
impl = re.search(r"^address " + RHINO + r" .*Implementation (0x[0-9a-f]{40})", ex, re.M).group(1)
check("the explorer's verified source names USDe's contract USDeOFT, the pool UniswapV3Pool, and the rhino.fi contract a proxy for DVFDepositContract",
      name_of[USDE] == "USDeOFT" and name_of[POOL] == "UniswapV3Pool" and name_of[RHINO] == "TransparentUpgradeableProxy" and name_of[impl] == "DVFDepositContract")
check("the pool pairs USDe with USDC at a fee of 0.05%", calls[(POOL, "0x0dfe1681")] == USDE and calls[(POOL, "0xd21220a7")] == USDC and calls[(POOL, "0xddca3f43")] == "500"
      and calls[(USDE, "0x95d89b41")] == "USDe" and calls[(USDC, "0x95d89b41")] == "USDC" and calls[(USDC, "0x313ce567")] == "6")
pages = (WEB / "ethena_pay_pages_2026-10-12.txt").read_text()
check("EthenaPay's FAQ and Terms of Use, as searched twice, name no bridge", pages.count("No paragraph names rhino.fi") == 2
      and len(re.findall(r"^source https://pay\.ethena\.fi/(?:faq|terms) read_at \S+ page_text_chars \d+ .*hits none$", pages, re.M)) == 2
      and "crosschain" in pages)
check("in USDeOFT's source only LayerZero's OFT contract calls _mint and _burn, and nothing else touches the supply",
      "no other file calls _mint or _burn" in ex and "No file other than ERC20.sol calls or overrides _update" in ex
      and re.search(r"OFT\.sol _mint\( 1, _burn\( 1", ex) and re.search(r"ERC20\.sol _mint\( 1, _burn\( 1, _update\( 4", ex))
third = ex.split("USDeOFT verified source, third search", 1)[1].split("\n\n", 1)[0]
check("in USDeOFT's source _credit is called only in _lzReceive, on a message from another chain, and _debit only in send and in USDeOFT's own _debit",
      "OFTCore.sol calls _credit in _lzReceive" in third and "OFTCore.sol calls _debit in send" in third
      and "USDeOFT.sol defines _debit and calls the parent _debit in it" in third and "hits 8, no other call of _credit or _debit in any file" in third
      and len(re.findall(r" calls ", third)) == 3)

# ---------------------------------------------------------------- results
log()
log("Results")
supply = last["supply_wei"]
end = {"wallets": last["wallets_held_wei"], "settlement": last["settlement_held_wei"], "reward_accounts": last["reward_accounts_held_wei"],
       "settlement_recipients": last["settlement_recipients_held_wei"], "rhino_fi_bridge_contract": bal(rh), "uniswap_v3_pool": bal(pl),
       "other_accounts": end_bal[OTHER]}
linked = end["wallets"] + end["settlement"] + end["reward_accounts"] + end["settlement_recipients"]
accounts = {"wallets": last["wallets_with_usde"], "settlement": int(g1("settlement")["holders"]), "reward_accounts": int(g1("reward_accounts")["holders"]),
            "settlement_recipients": len(listed_recip), "rhino_fi_bridge_contract": 1, "uniswap_v3_pool": 1,
            "other_accounts": len(listed_other) - 2 + int(g1("other_rest")["holders"])}
check("the accounts in each group add up to all holders", sum(accounts.values()) == last["holders"])
R["end"] = {"date": last["date"], "supply_usde": str(usd(supply)), "holders": last["holders"], "wallets_created": last["wallets_created"],
            "groups": {k: {"accounts": accounts[k], "usde": str(usd(v)), "share_pct": str(pct(v, supply))} for k, v in end.items()},
            "ethenapay_linked_usde": str(usd(linked)), "ethenapay_linked_share_pct": str(pct(linked, supply)),
            "ethenapay_linked_accounts": accounts["wallets"] + accounts["settlement"] + accounts["reward_accounts"] + accounts["settlement_recipients"],
            "outside_wallets_usde": str(usd(supply - end["wallets"])), "holders_outside_ethenapay_usde": str(usd(last["other_held_wei"])),
            "holders_outside_ethenapay_share_pct": str(pct(last["other_held_wei"], supply)), "non_wallet_holders": last["holders"] - last["wallets_with_usde"]}
log(f"  supply {usd(supply):,} USDe, wallets {usd(end['wallets']):,} ({pct(end['wallets'], supply)}%), accounts tied to EthenaPay {usd(linked):,} ({pct(linked, supply)}%)")

# growth since the first wallet
before = day["2026-05-14"]
R["growth"] = {"supply_2026_05_14_usde": str(usd(before["supply_wei"])), "holders_2026_05_14": before["holders"],
               "multiple": str((Decimal(supply) / before["supply_wei"]).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)),
               "increase_usde": str(usd(supply - before["supply_wei"]))}
first_half = next(r for r in days if r["supply_wei"] and 2 * r["wallets_held_wei"] > r["supply_wei"])
since = [r for r in days if r["date"] >= first_half["date"]]
lo = min(since, key=lambda r: Decimal(r["wallets_held_wei"]) / r["supply_wei"])
hi = max(since, key=lambda r: Decimal(r["wallets_held_wei"]) / r["supply_wei"])
R["growth"]["wallets_first_above_half"] = {"date": first_half["date"], "share_pct": str(pct(first_half["wallets_held_wei"], first_half["supply_wei"]))}
moves = [(abs(Decimal(b["wallets_held_wei"]) / b["supply_wei"] - Decimal(a["wallets_held_wei"]) / a["supply_wei"]) * 100, b["date"]) for a, b in zip(since, since[1:])]
big_move = max(moves)
R["growth"]["largest_one_day_move"] = {"date": big_move[1], "points": str(big_move[0].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                                       "days_moving_3_points_or_more": sum(1 for x in moves if x[0] >= 3), "day_pairs": len(moves)}
R["growth"]["wallet_share_since"] = {"low_date": lo["date"], "low_pct": str(pct(lo["wallets_held_wei"], lo["supply_wei"])),
                                     "high_date": hi["date"], "high_pct": str(pct(hi["wallets_held_wei"], hi["supply_wei"])),
                                     "days_below_half": sum(1 for r in since if 2 * r["wallets_held_wei"] < r["supply_wei"]), "days": len(since)}
month_ends = ["2025-08-31", "2025-09-30", "2025-10-31", "2025-11-30", "2025-12-31", "2026-01-31", "2026-02-28", "2026-03-31", "2026-04-30", "2026-05-14",
              "2026-05-31", "2026-06-30", "2026-07-31", "2026-08-31", "2026-09-30", "2026-10-11"]
other_ep = lambda r: r["settlement_held_wei"] + r["reward_accounts_held_wei"] + r["settlement_recipients_held_wei"]
month_rows = []
for d in month_ends:
    r = day[d]
    month_rows.append({"date": d, "supply_usde": usd(r["supply_wei"]), "ethenapay_wallets_usde": usd(r["wallets_held_wei"]),
                       "settlement_and_reward_accounts_usde": usd(other_ep(r)), "holders_outside_ethenapay_usde": usd(r["other_held_wei"]),
                       "wallets_share_pct": pct(r["wallets_held_wei"], r["supply_wei"]) if r["supply_wei"] else "",
                       "accounts_tied_to_ethenapay_share_pct": pct(r["wallets_held_wei"] + other_ep(r), r["supply_wei"]) if r["supply_wei"] else "",
                       "holders": r["holders"], "wallets_with_usde": r["wallets_with_usde"], "wallets_created": r["wallets_created"]})
R["month_ends"] = [{k: str(v) for k, v in x.items()} for x in month_rows]

# before EthenaPay
first_mint = next(r for r in days if r["minted_wei"] > 0)
first_1000 = next(r for r in days if r["minted_wei"] >= 1000 * 10 ** 18)
first_million = next(r for r in days if r["minted_wei"] >= 10 ** 24)
y2025 = [r for r in days if r["date"] < "2026-01-01"]
peak25 = max(y2025, key=lambda r: r["supply_wei"])
drop = min(days, key=lambda r: r["minted_wei"] - r["burned_wei"])
early26 = [r for r in days if "2026-01-01" <= r["date"] <= "2026-05-14"]
peak26 = max(early26, key=lambda r: r["supply_wei"])
drop26 = min(early26, key=lambda r: r["minted_wei"] - r["burned_wei"])
check("the largest one-day fall in supply came after the 2025 peak", drop["date"] > peak25["date"] and drop["date"] < "2026-01-01")
R["before"] = {"deploy_block": meta["deploy_block"], "deploy_time": meta["deploy_block_time"], "first_mint_date": first_mint["date"],
               "first_mint_wei": str(first_mint["minted_wei"]), "first_1000_date": first_1000["date"], "first_1000_usde": str(usd(first_1000["minted_wei"])),
               "first_million_date": first_million["date"], "first_million_usde": str(usd(first_million["minted_wei"])),
               "peak_2025_date": peak25["date"], "peak_2025_usde": str(usd(peak25["supply_wei"])), "peak_2025_holders": peak25["holders"],
               "largest_one_day_fall_date": drop["date"], "largest_one_day_fall_net_usde": str(usd(drop["burned_wei"] - drop["minted_wei"])),
               "largest_one_day_fall_burned_usde": str(usd(drop["burned_wei"])), "supply_after_fall_usde": str(usd(drop["supply_wei"])),
               "supply_2025_12_31_usde": str(usd(day["2025-12-31"]["supply_wei"])), "holders_2025_12_31": day["2025-12-31"]["holders"],
               "peak_2026_before_wallets_date": peak26["date"], "peak_2026_before_wallets_usde": str(usd(peak26["supply_wei"])),
               "fall_2026_date": drop26["date"], "fall_2026_burned_usde": str(usd(drop26["burned_wei"])), "supply_after_fall_2026_usde": str(usd(drop26["supply_wei"])),
               "minted_before_wallets_usde": str(usd(f(MINT, periods=(P0,)))), "burned_before_wallets_usde": str(usd(f(to=BURN, periods=(P0,)))),
               "end_over_2025_high": str((Decimal(last["supply_wei"]) / peak25["supply_wei"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))}

# flows from May 15 to October 11
PP = (P1, P2)
minted = f(MINT, periods=PP)
burned = f(to=BURN, periods=PP)
R["since_first_wallet"] = {"minted_usde": str(usd(minted)), "mints": f(MINT, periods=PP, key="transfers"), "burned_usde": str(usd(burned)),
                           "burns": f(to=BURN, periods=PP, key="transfers"), "net_usde": str(usd(minted - burned)),
                           "minted_to": {g: str(usd(f(MINT, g, PP))) for g in (RH, OTHER, REWARD, WALLETS)},
                           "minted_to_rhino_share_pct": str(pct(f(MINT, RH, PP), minted)),
                           "burned_from": {g: str(usd(f(g, BURN, PP))) for g in (OTHER, WALLETS, SETTLEMENT, RH)}}
into_w = {g: f(g, WALLETS, PP) for g in (RH, OTHER, MINT, RECIP, PL, REWARD, SETTLEMENT)}
out_w = {g: f(WALLETS, g, PP) for g in (SETTLEMENT, OTHER, RH, BURN, PL, RECIP, REWARD)}
outside = sum(into_w[g] for g in OUTSIDE)
check("the wallets' flows from May 15 give their balance at the end", sum(into_w.values()) - sum(out_w.values()) == end["wallets"])
R["wallets"] = {"received_from_outside_usde": str(usd(outside)), "rhino_share_of_outside_pct": str(pct(into_w[RH], outside)),
                "into": {g: {"usde": str(usd(v)), "transfers": f(g, WALLETS, PP, "transfers")} for g, v in into_w.items()},
                "out": {g: {"usde": str(usd(v)), "transfers": f(WALLETS, g, PP, "transfers")} for g, v in out_w.items()},
                "between_wallets_usde": str(usd(f(WALLETS, WALLETS, PP))), "in_total_usde": str(usd(sum(into_w.values()))),
                "out_total_usde": str(usd(sum(out_w.values()))), "deposits_to_2026_10_05_usde": str(usd(f(OUTSIDE, WALLETS, (P1,)))),
                "deposits_2026_10_06_to_11_usde": str(usd(f(OUTSIDE, WALLETS, (P2,))))}
into_s = {g: f(g, SETTLEMENT, PP) for g in (WALLETS, OTHER)}
out_s = {g: f(SETTLEMENT, g, PP) for g in (WALLETS, RECIP, BURN, OTHER, RH, PL)}
check("the settlement addresses' flows give their balance at the end, and they burned none",
      sum(into_s.values()) - sum(out_s.values()) == end["settlement"] and out_s[BURN] == 0 and f(SETTLEMENT, BURN) == 0)
check("the settlement addresses received USDe only from May 15 on", f(to=SETTLEMENT, periods=(P0,)) == 0 and f(SETTLEMENT, periods=(P0,)) == 0)
R["settlement"] = {"into": {g: {"usde": str(usd(v)), "transfers": f(g, SETTLEMENT, PP, "transfers")} for g, v in into_s.items()},
                   "out": {g: {"usde": str(usd(v)), "transfers": f(SETTLEMENT, g, PP, "transfers")} for g, v in out_s.items()},
                   "received_usde": str(usd(sum(into_s.values()))),
                   "to_recipients_share_of_received_pct": str(pct(out_s[RECIP], sum(into_s.values()))),
                   "balance_usde": str(usd(end["settlement"])),
                   "card_payments_net_of_returns_usde": str(usd(into_s[WALLETS] - out_s[WALLETS])),
                   "on_avalanche_usde": str(usd(end["settlement"] + end["settlement_recipients"]))}
big = listed_recip[0]
R["recipients"] = {"accounts": len(listed_recip), "held_usde": str(usd(end["settlement_recipients"])), "largest_held_usde": str(usd(bal(big))),
                   "largest_received_usde": str(usd(big["received_wei"])), "largest_sent_usde": str(usd(big["sent_wei"])), "largest_first_received": big["first_received"],
                   "received_usde": str(usd(f(to=RECIP))),
                   "largest_share_of_received_pct": str(pct(big["received_wei"], f(to=RECIP))),
                   "share_of_supply_pct": str(pct(end["settlement_recipients"], supply)),
                   "sent_on_usde": str(usd(f(RECIP)))}
R["rhino"] = {"rank": int(rh["rank"]), "first_received": rh["first_received"], "minted_to_usde": str(usd(rh["minted_to_wei"])), "received_usde": str(usd(rh["received_wei"])),
              "minted_share_of_received_pct": str(pct(rh["minted_to_wei"], rh["received_wei"])), "sent_usde": str(usd(rh["sent_wei"])),
              "sent_to_wallets_usde": str(usd(rh["sent_to_wallets_wei"])), "sent_to_wallets_share_pct": str(pct(rh["sent_to_wallets_wei"], rh["sent_wei"])),
              "sent_to_wallets_transfers": f(RH, WALLETS, key="transfers"), "sent_to_others_usde": str(usd(f(RH, OTHER))),
              "sent_since_first_wallet_usde": str(usd(f(RH, periods=PP))), "to_wallets_share_since_first_wallet_pct": str(pct(f(RH, WALLETS, PP), f(RH, periods=PP))),
              "balance_usde": str(usd(bal(rh))), "minted_to_since_first_wallet_usde": str(usd(f(MINT, RH, PP)))}
R["pool"] = {"rank": int(pl["rank"]), "pair": "USDe/USDC", "fee_pct": "0.05", "balance_usde": str(usd(bal(pl))), "received_usde": str(usd(pl["received_wei"])),
             "sent_usde": str(usd(pl["sent_wei"])), "first_received": pl["first_received"]}
top = listed_other[0]
R["largest_other"] = {"balance_usde": str(usd(bal(top))), "minted_to_usde": str(usd(top["minted_to_wei"])), "first_received": top["first_received"],
                      "sent_usde": str(usd(top["sent_wei"])), "is_contract": top["is_contract"] == "1"}
R["other_rest"] = {"accounts": int(g1("other_rest")["holders"]), "usde": str(usd(bal(g1("other_rest"))))}
R["recount_match"] = {"days": len(recount), "first": recount[0]["date"], "last": recount[-1]["date"], "held_2026_10_05_usde": str(usd(recount[-1]["held_wei"]))}
R["read"] = {k: meta[k] for k in ("deploy_block", "end_block", "wallets", "transfer_records_listed", "transfer_logs_kept", "records_with_no_value", "mints", "burns",
                                  "run_started_utc", "run_finished_utc")}
R["read"]["tie_block"] = tie["block_after"]
R["read"]["tie_block_before"] = tie["block_before"]
R["read"]["factory_creations"] = sum(meta["factory_rows"])
R["read"]["factory_created_not_create2"] = len(other_made)
R["read"]["total_supply_usde"] = str(usd(tie["total_supply_wei"]))
R["read"]["burned_after_usde"] = str(usd(tie["burned_after_wei"]))
log(f"  supply on May 14 {usd(before['supply_wei']):,}, {R['growth']['multiple']} times by October 11")
log(f"  minted from May 15 {usd(minted):,}, {pct(f(MINT, RH, PP), minted)}% of it to the rhino.fi bridge contract, burned {usd(burned):,}")
log(f"  wallets received {usd(outside):,} from outside, {pct(into_w[RH], outside)}% from the rhino.fi bridge contract")
log(f"  card payments {usd(into_s[WALLETS]):,}, returned {usd(out_s[WALLETS]):,}, to the three recipients {usd(out_s[RECIP]):,}, held at the end {usd(end['settlement']):,}")

# ---------------------------------------------------------------- tables
if failures:
    log()
    log(f"{len(failures)} checks failed, nothing written")
    (HERE / "run_log_failed.txt").write_text("\n".join(log_lines) + "\n")
    sys.exit(1)
OUT.mkdir(exist_ok=True)
names = [("wallets", "EthenaPay wallets"), ("settlement", "Settlement addresses"), ("settlement_recipients", "Settlement recipients"),
         ("reward_accounts", "Reward accounts"), ("rhino_fi_bridge_contract", "rhino.fi bridge contract"), ("uniswap_v3_pool", "Uniswap v3 pool"),
         ("other_accounts", "Other accounts")]
with open(OUT / "holders_at_end.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["group", "label", "accounts", "usde", "share_of_supply_pct"])
    for k, label in names:
        w.writerow([k, label, accounts[k], usd(end[k]), pct(end[k], supply)])
    w.writerow(["all", "All holders", last["holders"], usd(supply), "100.00"])
with open(OUT / "month_ends.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(list(month_rows[0]))
    for x in month_rows:
        w.writerow(list(x.values()))
labels = {RH: "rhino.fi bridge contract", OTHER: "other accounts", MINT: "arrived from another chain", RECIP: "settlement recipients",
          PL: "Uniswap v3 pool", REWARD: "reward accounts", SETTLEMENT: "settlement addresses, returns", BURN: "left Avalanche"}
with open(OUT / "wallet_flows.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["direction", "counterparty", "transfers", "usde"])
    for g, v in into_w.items():
        w.writerow(["into wallets", labels[g], f(g, WALLETS, PP, "transfers"), usd(v)])
    for g, v in out_w.items():
        w.writerow(["out of wallets", "settlement addresses, card payments" if g == SETTLEMENT else labels[g], f(WALLETS, g, PP, "transfers"), usd(v)])
    w.writerow(["between wallets", "EthenaPay wallets", f(WALLETS, WALLETS, PP, "transfers"), usd(f(WALLETS, WALLETS, PP))])
with open(OUT / "settlement_flows.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["direction", "counterparty", "transfers", "usde"])
    for g, v in into_s.items():
        w.writerow(["into the settlement addresses", "EthenaPay wallets, card payments" if g == WALLETS else labels[g], f(g, SETTLEMENT, PP, "transfers"), usd(v)])
    for g, v in out_s.items():
        w.writerow(["out of the settlement addresses", "EthenaPay wallets, returns" if g == WALLETS else labels[g], f(SETTLEMENT, g, PP, "transfers"), usd(v)])
with open(OUT / "chart_daily.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["date", "ethenapay_wallets_usde", "settlement_and_reward_accounts_usde", "holders_outside_ethenapay_usde", "supply_usde"])
    for r in days:
        if r["date"] >= "2026-05-15":
            a, b, c = usd(r["wallets_held_wei"]), usd(other_ep(r)), usd(r["other_held_wei"])
            w.writerow([r["date"], a, b, c, usd(r["supply_wei"])])
R["checks_passed"] = sum(1 for l in log_lines if l.startswith("ok"))
(OUT / "results.json").write_text(json.dumps(R, indent=1) + "\n")
log()
log(f"All {R['checks_passed']} checks passed. Tables written to out/.")
(OUT / "run_log.txt").write_text("\n".join(log_lines) + "\n")
