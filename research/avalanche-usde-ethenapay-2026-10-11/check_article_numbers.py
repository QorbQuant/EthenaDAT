#!/usr/bin/env python3
"""
Recomputes every computed figure in article_draft.md, metadata.json and the chart's text from the files in inputs/,
with code written apart from avax_usde_review.py, and confirms that each exact phrase appears. It also checks the
article's punctuation rules. Exits with an error if a phrase is missing or an assertion fails, so rerun it after any
edit. Python 3 standard library only. No network.
"""
import csv
import json
import re
import sys
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP, getcontext
from fractions import Fraction
from pathlib import Path

getcontext().prec = 60
HERE = Path(__file__).parent
CH = HERE / "inputs" / "chain"
ARTICLE = (HERE / "article_draft.md").read_text()
META = json.loads((HERE / "metadata.json").read_text())
SVG = (HERE / "out" / "chart_avax_usde_holders.svg").read_text()
TEXT = ARTICLE + "\n" + "\n".join(META[k] for k in ("title", "headline", "description", "imageAlt")) + "\n" + SVG
WEI = 10 ** 18
found, missing = 0, []


def need(phrase, where=TEXT):
    global found
    if phrase in where:
        found += 1
    else:
        missing.append(phrase)


def load(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def money(wei, places=2):
    """USDe from wei, rounded half up, with thousands separators."""
    q = (Fraction(int(wei), WEI) * 10 ** places)
    n = int(q) + (1 if q - int(q) >= Fraction(1, 2) else 0)
    s = f"{n // 10 ** places:,}"
    return s + ("." + str(n % 10 ** places).rjust(places, "0") if places else "")


def share(num, den, places=1):
    q = Fraction(int(num) * 100, int(den)) * 10 ** places
    n = int(q) + (1 if q - int(q) >= Fraction(1, 2) else 0)
    return f"{n // 10 ** places}.{str(n % 10 ** places).rjust(places, '0')}%" if places else f"{n}%"


def millions(wei):
    q = Fraction(int(wei), WEI * 10 ** 4)
    n = int(q) + (1 if q - int(q) >= Fraction(1, 2) else 0)
    return f"{n // 100}.{str(n % 100).rjust(2, '0')}"


def millions3(wei):
    q = Fraction(int(wei), WEI * 10 ** 3)
    n = int(q) + (1 if q - int(q) >= Fraction(1, 2) else 0)
    return f"{n // 1000}.{str(n % 1000).rjust(3, '0')}"


def nice_day(iso):
    d = date.fromisoformat(iso)
    return d.strftime("%B ") + str(d.day)


# ---------------------------------------------------------------- the day-by-day file, read again
daily = load(CH / "daily.csv")
cols = [c for c in daily[0] if c != "date"]
D = {r["date"]: {c: int(r[c]) for c in cols} for r in daily}
dates = [r["date"] for r in daily]
assert dates[0] == "2025-08-08" and dates[-1] == "2026-10-11" and len(dates) == 430
assert all(date.fromisoformat(b) - date.fromisoformat(a) == timedelta(1) for a, b in zip(dates, dates[1:]))
running = 0
for d in dates:                                  # the supply from the mints and burns, independently
    running += D[d]["minted_wei"] - D[d]["burned_wei"]
    assert running == D[d]["supply_wei"]
END = D["2026-10-11"]
supply = END["supply_wei"]
groups = {k: END[k] for k in ("wallets_held_wei", "settlement_held_wei", "reward_accounts_held_wei", "settlement_recipients_held_wei", "other_held_wei")}
assert sum(groups.values()) == supply
meta = json.loads((CH / "meta.json").read_text())
holders = load(CH / "holders.csv")
row = {(r["group"], r["rank"]): r for r in holders}
rh = next(r for r in holders if r["label"] == "rhino.fi bridge contract")
pool = next(r for r in holders if r["label"] == "UniswapV3Pool contract")
listed_other = [r for r in holders if r["group"] == "other"]
recip = [r for r in holders if r["group"] == "settlement_recipients"]

# ---------------------------------------------------------------- lead
W = groups["wallets_held_wei"]
linked = W + groups["settlement_held_wei"] + groups["reward_accounts_held_wei"] + groups["settlement_recipients_held_wei"]
need(f"At the end of October 11, 2026 UTC, {money(supply)} USDe existed on Avalanche C-Chain, the chain of the Avalanche network that runs Ethereum-style smart contracts.")
need("This review calls that total the supply and calls the chain Avalanche for short.")
need(f"EthenaPay wallets held {money(W)} USDe, {share(W, supply)} of the supply.")
first_wallet_day = next(d for d in dates if D[d]["wallets_created"] > 0)
assert first_wallet_day == "2026-05-15" and END["wallets_created"] == meta["wallets"]
need(f"Of the {END['wallets_created']:,} wallets created by the end of October 11, {END['wallets_with_usde']:,} held USDe.")
need(f"Accounts tied to EthenaPay held {money(linked)} USDe, {share(linked, supply)} of the supply.")
need(f"The settlement recipients alone held {money(groups['settlement_recipients_held_wei'])} USDe, {share(groups['settlement_recipients_held_wei'], supply)} of the supply.")
before = D[(date.fromisoformat(first_wallet_day) - timedelta(1)).isoformat()]
multiple = Fraction(supply, before["supply_wei"])
assert 55 <= multiple < Fraction(111, 2)
y25 = [d for d in dates if d < "2026-01-01"]
p25 = max(y25, key=lambda d: D[d]["supply_wei"])
assert Fraction(19, 10) <= Fraction(supply, D[p25]["supply_wei"]) <= Fraction(21, 10)          # about twice the 2025 high
need(f"On May 14, the day before the first wallets were created, {money(before['supply_wei'])} USDe existed on Avalanche. By October 11 the supply was 55 times "
     "as large and about twice its 2025 high.")

# ---------------------------------------------------------------- flows, read again as a matrix
F = {}
for r in load(CH / "flows.csv"):
    F[(r["period"], r["from_group"], r["to_group"])] = (int(r["transfers"]), int(r["usde_wei"]))
periods = meta["flow_periods"]
assert periods == ["2025-08-08 to 2026-05-14", "2026-05-15 to 2026-10-05", "2026-10-06 to 2026-10-11"]


def flow(frm, to, pers=periods[1:], i=1):
    return sum(v[i] for (p, a, b), v in F.items() if p in pers and a in frm and b in to)


ALLG = {"minted", "ethenapay_wallets", "settlement", "reward_accounts", "settlement_recipients", "rhino_fi_bridge_contract", "uniswap_v3_pool", "other_accounts", "burned"}
WAL, SET, REW, REC, RHI, POO, OTH = ({x} for x in ("ethenapay_wallets", "settlement", "reward_accounts", "settlement_recipients", "rhino_fi_bridge_contract", "uniswap_v3_pool", "other_accounts"))
outside = flow({"minted"} | REC | RHI | POO | OTH, WAL)
assert outside == int(meta["wallets_received_from_outside_wei"])
from_rhino = flow(RHI, WAL, periods)
arrived = flow({"minted"}, ALLG)
left = flow(ALLG, {"burned"})
to_rhino = flow({"minted"}, RHI)
assert Fraction(to_rhino, arrived) > Fraction(1, 2)                                              # most of the new USDe
assert flow(RHI, WAL, periods[:1]) == 0                                                        # all of it from May 15 on
need("Most of the new USDe arrived at the rhino.fi bridge contract, the Avalanche contract of a bridge that moves tokens between blockchains.")
assert flow({"minted"}, WAL) > 0
need("Deposits here are the USDe EthenaPay wallets received from accounts other than wallets, settlement addresses and reward accounts, or straight from another chain.")
need(f"From May 15 to October 11 the rhino.fi bridge contract paid {money(from_rhino)} USDe into the wallets, {share(from_rhino, outside)} of their deposits.")

# ---------------------------------------------------------------- holders table
other_accts = groups["other_held_wei"] - int(rh["balance_wei"]) - int(pool["balance_wei"])
n_other = len(listed_other) - 2 + int(row[("other_rest", "")]["holders"])
n_settle = int(row[("settlement", "")]["holders"])
n_reward = int(row[("reward_accounts", "")]["holders"])
assert END["wallets_with_usde"] + n_settle + n_reward + len(recip) + 2 + n_other == END["holders"] == meta["holders_at_end"]
cells = []
for label, n, v in (("EthenaPay wallets", END["wallets_with_usde"], W), ("Settlement recipients", len(recip), groups["settlement_recipients_held_wei"]),
                    ("Settlement addresses", n_settle, groups["settlement_held_wei"]), ("Reward accounts", n_reward, groups["reward_accounts_held_wei"]),
                    ("Uniswap v3 pool", 1, int(pool["balance_wei"])), ("rhino.fi bridge contract", 1, int(rh["balance_wei"])),
                    ("Other accounts", n_other, other_accts)):
    need(f"| {label} | {n:,} | {money(v)} | {share(v, supply)} |")
    cells.append(Decimal(money(v).replace(",", "")))
need(f"| All holders | {END['holders']:,} | {money(supply)} | 100.0% |")
gap = abs(sum(cells) - Decimal(money(supply).replace(",", "")))
assert Decimal("0") < gap <= Decimal("0.01")
need("Each amount is rounded to the cent on its own, so the rows add up to the total only to within a cent.")
assert n_settle == 1
need("One of the two settlement addresses held USDe at the end of the day and the other held none.")
rest = row[("other_rest", "")]
need(f"The {int(rest['holders'])} smallest of the {n_other} other accounts held {money(rest['balance_wei'])} USDe between them.")
ex = (HERE / "inputs" / "web" / "explorer_contracts_2026-10-12.txt").read_text()
assert re.search(r"data 0xddca3f43 fee\(\) read_at 2026-10-12\S+ result 500$", ex, re.M) and "result USDC" in ex
assert re.search(r"data 0x0dfe1681 token0\(\) read_at \S+ result 0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34$", ex, re.M)
assert re.search(r"data 0xd21220a7 token1\(\) read_at \S+ result 0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e$", ex, re.M)
need("The Uniswap v3 pool is a contract that paired USDe with USDC, another dollar token, so that either could be traded for the other.")
need("When read on October 12, the Uniswap v3 pool charged a fee of 0.05% on each trade.")
need("The supply is all the USDe that had arrived on Avalanche less all that had left. It matched the total kept by the token contract")

# ---------------------------------------------------------------- month ends
need("| End of day | Supply | In EthenaPay wallets | Wallets' share | Share held by accounts tied to EthenaPay |")
for iso, label in (("2026-05-14", "May 14"), ("2026-05-31", "May 31"), ("2026-06-30", "June 30"), ("2026-07-31", "July 31"), ("2026-08-31", "August 31"),
                   ("2026-09-30", "September 30"), ("2026-10-11", "October 11")):
    r = D[iso]
    tied = r["wallets_held_wei"] + r["settlement_held_wei"] + r["reward_accounts_held_wei"] + r["settlement_recipients_held_wei"]
    need(f"| {label} | {money(r['supply_wei'])} | {money(r['wallets_held_wei'])} | {share(r['wallets_held_wei'], r['supply_wei'])} | {share(tied, r['supply_wei'])} |")
after = [d for d in dates if D[d]["supply_wei"] > 0 and Fraction(D[d]["wallets_held_wei"], D[d]["supply_wei"]) > Fraction(1, 2)]
first_half = after[0]
assert first_half == "2026-09-02"
need(f"The wallets' USDe first passed half of the supply on September 2, at {share(D[first_half]['wallets_held_wei'], D[first_half]['supply_wei'])}.")
span = [d for d in dates if d >= first_half]
sh = {d: Fraction(D[d]["wallets_held_wei"], D[d]["supply_wei"]) for d in span}
lo, hi = min(span, key=sh.get), max(span, key=sh.get)
below = sum(1 for d in span if sh[d] < Fraction(1, 2))
need(f"From then to October 11 the wallets' share moved between {share(D[lo]['wallets_held_wei'], D[lo]['supply_wei'])} on {nice_day(lo)} and "
     f"{share(D[hi]['wallets_held_wei'], D[hi]['supply_wei'])} on {nice_day(hi)}, and it was below half on {below} of those {len(span)} days.")
steps = [(sh[b] - sh[a], b) for a, b in zip(span, span[1:])]
big = max(steps, key=lambda x: abs(x[0]))
assert big[0] < 0
pts = big[0] * -100 * 10
pts_r = int(pts) + (1 if pts - int(pts) >= Fraction(1, 2) else 0)
need("The share moves whenever USDe enters or leaves the wallets and whenever USDe arrives on Avalanche or leaves it.")
need(f"On {nice_day(big[1])} it fell {pts_r // 10}.{pts_r % 10} points in a day.")

# ---------------------------------------------------------------- the chart's text
chart = load(HERE / "out" / "chart_daily.csv")
assert chart[0]["date"] == first_wallet_day and chart[-1]["date"] == "2026-10-11" and len(chart) == 150
for r in chart:
    d = D[r["date"]]
    assert Decimal(r["ethenapay_wallets_usde"]) == Decimal(money(d["wallets_held_wei"]).replace(",", ""))
    assert Decimal(r["settlement_and_reward_accounts_usde"]) == Decimal(money(d["settlement_held_wei"] + d["reward_accounts_held_wei"] + d["settlement_recipients_held_wei"]).replace(",", ""))
    assert Decimal(r["holders_outside_ethenapay_usde"]) == Decimal(money(d["other_held_wei"]).replace(",", ""))
    assert Decimal(r["supply_usde"]) == Decimal(money(d["supply_wei"]).replace(",", ""))
other_ep = linked - W
outside_ep = groups["other_held_wei"]
assert Decimal(millions3(W)) + Decimal(millions3(other_ep)) + Decimal(millions3(outside_ep)) == Decimal(millions3(supply))   # the labels add up
high = D[p25]["supply_wei"]
need(f"Stacked area chart of {len(chart)} days. The supply of USDe on Avalanche C-Chain rose from {millions3(D[first_wallet_day]['supply_wei'])} million on May 15, 2026, "
     f"the day the first EthenaPay wallets were created, to {millions3(supply)} million on October 11.")
need(f"held more than half of the supply for the first time on September 2 and {millions3(W)} million on October 11.")
need(f"The settlement and reward accounts, the middle band, held {millions3(other_ep)} million on October 11, and holders outside EthenaPay, the top band, "
     f"{millions3(outside_ep)} million. A dashed line marks the 2025 high of {millions3(high)} million.")
since_sep = supply - D["2026-08-31"]["supply_wei"]
assert Fraction(since_sep, supply - D[first_wallet_day]["supply_wei"]) > Fraction(1, 2)
need("Most of the rise came from September on.")
need("The settlement and reward accounts, the middle band, are the settlement addresses, the settlement recipients and the reward accounts together.")
need("Holders outside EthenaPay, the top band, are all holders not tied to EthenaPay, the Uniswap v3 pool and the rhino.fi bridge contract among them.")
need("The chart's data comes from the Routescan explorer, a public website and API that indexes Avalanche.")
need(f"EthenaPay wallets held {share(W, supply)} of the USDe on Avalanche at the end of October 11", SVG)
need(f"All holders {millions3(supply)}M", SVG)
need("Holders outside<tspan", SVG)
need(f">EthenaPay {millions3(outside_ep)}M</tspan>", SVG)
need("Settlement and<tspan", SVG)
need(f">reward accounts {millions3(other_ep)}M</tspan>", SVG)
need(f"EthenaPay wallets {millions3(W)}M", SVG)
need(f"2025 high {millions3(high)}M", SVG)
need(f"for the first time on September 2, {share(D[first_half]['wallets_held_wei'], D[first_half]['supply_wei'])}, and {share(W, supply)} on October 11, {millions3(W)} million.", SVG)
need(f"The settlement and reward accounts, which are the settlement addresses, the settlement recipients and the reward accounts together, held {millions3(other_ep)} "
     "million more", SVG)
need(f"so accounts tied to EthenaPay held {share(linked, supply)}.", SVG)
need(f"Holders outside EthenaPay held {millions3(outside_ep)} million. A dashed line marks the 2025 high of {millions3(high)} million.", SVG)
need(f"The supply rose from {millions3(D[first_wallet_day]['supply_wei'])} million to {millions3(supply)} million, most of it from September on.", META["imageAlt"])
need(f"EthenaPay wallets held {millions3(W)} million on October 11, the settlement and reward accounts {millions3(other_ep)} million and holders outside EthenaPay "
     f"{millions3(outside_ep)} million.", META["imageAlt"])
need(f"A dashed line marks the 2025 high of {millions3(high)} million.", META["imageAlt"])
arrived_from_may = flow({"minted"}, ALLG)
assert Fraction(flow({"minted"}, RHI), arrived_from_may) > Fraction(1, 2)
need(f"EthenaPay wallets held {share(W, supply)} of the {millions(supply)} million USDe on Avalanche on October 11, 2026. Most USDe arriving from May 15 went to the "
     "rhino.fi bridge contract.", META["description"])
assert "Transfers of USDe on Avalanche C-Chain, read from the Routescan explorer API on October 12, 2026 UTC" in ARTICLE and \
    "Transfers of USDe on Avalanche C-Chain, read from the Routescan explorer API on October 12, 2026 UTC" in SVG     # one source line for caption and chart

# ---------------------------------------------------------------- arrivals and the rhino.fi bridge contract
assert arrived - left == supply - before["supply_wei"]
need(f"From May 15 to October 11, {money(arrived)} USDe arrived on Avalanche and {money(left)} USDe left, a net {money(arrived - left)}.")
need(f"Of the USDe that arrived, {money(to_rhino)}, or {share(to_rhino, arrived)}, arrived at the rhino.fi bridge contract, `0x5e023c31e1d3dcd08a1b3e8c96f6ef8aa8fcacd1`.")
rh_in = flow(ALLG, RHI, periods)
rh_minted = flow({"minted"}, RHI, periods)
rh_out = flow(RHI, ALLG, periods)
assert rh_in == int(rh["received_wei"]) and rh_minted == int(rh["minted_to_wei"]) and rh_out == int(rh["sent_wei"]) and flow(RHI, {"burned"}, periods) == 0
assert rh["first_received"] == "2026-03-05"
need(f"From its first USDe on March 5, 2026, {share(rh_minted, rh_in)} of the USDe it received arrived from another chain straight into it, and none of its USDe "
     "left Avalanche.")
need("A bridge of this kind can also pay out on another chain from funds it holds there, which a count on Avalanche does not show.")
need(f"The rhino.fi bridge contract paid {money(from_rhino)} USDe into EthenaPay wallets in {flow(RHI, WAL, periods, 0):,} transfers, {share(from_rhino, rh_out)} of all "
     "the USDe it sent from March 5 on.")
need(f"From May 15 to October 11 the wallets received {money(outside)} USDe in deposits")
need(f"so the rhino.fi bridge contract supplied {share(from_rhino, outside)} of them.")
direct = flow({"minted"}, WAL)
assert direct == 10 * WEI and flow(REC | POO, WAL) == 0
need(f"Other accounts sent {money(flow(OTH, WAL))} USDe, and {direct // WEI} USDe arrived from another chain straight into a wallet.")
pages = (HERE / "inputs" / "web" / "ethena_pay_pages_2026-10-12.txt").read_text()
assert pages.count("No paragraph names rhino.fi") == 2 and len(re.findall(r"^source https://pay\.ethena\.fi/(faq|terms) read_at 2026-10-12\S+ .*hits none$", pages, re.M)) == 2
need("EthenaPay's FAQ and Terms of Use, searched on October 12, named neither rhino.fi nor any bridge.")
assert re.search(r"ContractName USDeOFT", ex) and re.search(r"ContractName DVFDepositContract", ex) and "no other file calls _mint or _burn" in ex
assert "No file other than ERC20.sol calls or overrides _update" in ex
third = ex.split("USDeOFT verified source, third search", 1)[1].split("\n\n", 1)[0]
assert "OFTCore.sol calls _credit in _lzReceive" in third and "OFTCore.sol calls _debit in send" in third and "hits 8, no other call of _credit or _debit" in third
need("When read on October 12, the explorer named the token contract USDeOFT.")
need("When read on October 12, rhino.fi's bridge configuration listed this contract as its contract on Avalanche.")
need("In it USDe is minted, or created, on Avalanche only when it arrives from another chain, and burned, or destroyed, only when it is sent to one.")
need("The explorer showed the contract as a proxy, a contract that runs another contract's code, here one named DVFDepositContract.")

# ---------------------------------------------------------------- card payments
card = flow(WAL, SET)
back = flow(SET, WAL)
to_rec = flow(SET, REC)
from_oth = flow(OTH, SET)
assert flow(ALLG, SET) == card + from_oth
need(f"From May 15 to October 11, {flow(WAL, SET, i=0):,} card payments moved {money(card)} USDe from wallets to the settlement addresses, and other accounts sent them "
     f"{money(from_oth)} USDe in {flow(OTH, SET, i=0)} transfers.")
assert flow(ALLG, SET, periods) == card + from_oth                                              # nothing reached them before May 15
need(f"Of the {money(card + from_oth)} USDe they received, the settlement addresses paid {money(to_rec)} USDe, {share(to_rec, card + from_oth)}, to the settlement "
     f"recipients in {flow(SET, REC, i=0)} transfers.")
need(f"They sent {money(back)} USDe back to wallets in {flow(SET, WAL, i=0):,} transfers, called returns here.")
assert flow(SET, ALLG - WAL - REC) == 0 and flow(SET, ALLG, periods) == back + to_rec
assert card + from_oth - back - to_rec == groups["settlement_held_wei"]
assert flow(SET, {"burned"}, periods) == 0
need("None of their USDe left Avalanche and they sent none to any other account.")
need(f"They held {money(groups['settlement_held_wei'])} USDe at the end of October 11.")
top = recip[0]
assert int(top["sent_wei"]) == 0 and int(top["received_wei"]) == int(top["received_from_settlement_wei"]) and int(top["balance_wei"]) == int(top["received_wei"])
rec_in = flow(SET, REC, periods)
assert sum(int(r["received_wei"]) for r in recip) == rec_in == flow(ALLG, REC, periods)
need(f"The largest settlement recipient received {money(top['received_wei'])} USDe from {nice_day(top['first_received'])}, {top['first_received'][:4]} on, "
     f"{share(top['received_wei'], rec_in)} of what the three received, all of it from the settlement addresses.")
need("It had sent none by the end of October 11.")
senders = [r for r in recip if int(r["sent_wei"]) > 0]
assert len(senders) == 1 and int(senders[0]["sent_wei"]) == 5 * WEI and flow(REC, ALLG, periods) == 5 * WEI and to_rec - groups["settlement_recipients_held_wei"] == 5 * WEI
assert flow(REC, OTH, periods) == 5 * WEI
need("A second settlement recipient passed 5 USDe on to one of the other accounts, so the settlement recipients held 5 USDe less than they received.")
both = groups["settlement_held_wei"] + groups["settlement_recipients_held_wei"]
need(f"Together the settlement addresses and the settlement recipients held {money(both)} USDe, {share(both, supply)} of the supply.")
assert flow(REC, {"burned"}, periods) == 0
assert Fraction(to_rec, card + from_oth) > Fraction(1, 2)                                       # most USDe paid to the settlement addresses

# ---------------------------------------------------------------- wallets' flows
into = flow(ALLG - WAL, WAL)
out = flow(WAL, ALLG - WAL)
assert into - out == W
need(f"From May 15 to October 11, {money(into)} USDe went into wallets and {money(out)} came out, which left the {money(W)} they held at the end of October 11, "
     f"not counting {money(flow(WAL, WAL))} USDe moved from one wallet to another.")
rewards = flow(REW, WAL)
assert outside + back + rewards == into
need(f"Besides the deposits, the wallets received {money(back)} USDe in returns and {money(rewards)} USDe from the reward accounts.")
wd = flow(WAL, ALLG - WAL - SET)
not_other = wd - flow(WAL, OTH)
need(f"Apart from card payments, {money(wd)} USDe went out of the wallets, the flow the cash-flow review calls withdrawals, all but {money(not_other)} of it to other accounts.")
assert not_other == flow(WAL, RHI) + flow(WAL, {"burned"}) and flow(WAL, {"burned"}) == 2 * WEI
need(f"Of the rest, {money(flow(WAL, RHI))} USDe went to the rhino.fi bridge contract and 2 USDe left Avalanche straight from a wallet.")
assert left - flow(OTH, {"burned"}) == 2 * WEI
need(f"Of the {money(left)} USDe that left Avalanche from May 15, all but those 2 left from other accounts.")

# ---------------------------------------------------------------- before EthenaPay
assert meta["deploy_block_time"].startswith("2025-08-08")
need(f"The token contract was created on August 8, 2025, in block {meta['deploy_block']:,}.")
early = [d for d in dates if D[d]["minted_wei"] > 0]
assert early[:2] == ["2025-08-15", "2025-08-18"] and all(D[d]["minted_wei"] < WEI // 1000 for d in early[:2]) and early[2] == "2025-08-19"
need(f"Apart from amounts below a thousandth of a USDe on August 15 and 18, the first USDe arrived on August 19, {money(D['2025-08-19']['minted_wei'], 0)} of it, and "
     f"{money(D['2025-08-28']['minted_wei'])} USDe arrived on August 28.")
assert next(d for d in dates if D[d]["minted_wei"] >= 10 ** 24) == "2025-08-28"
need(f"The supply reached its 2025 high, {money(D[p25]['supply_wei'])} USDe, on {nice_day(p25)}, 2025.")
need(f"On October 29, {money(D['2025-10-29']['burned_wei'])} USDe left, and the year ended with {money(D['2025-12-31']['supply_wei'])} USDe on Avalanche.")
assert min(dates, key=lambda d: D[d]["minted_wei"] - D[d]["burned_wei"]) == "2025-10-29"
e26 = [d for d in dates if "2026-01-01" <= d < first_wallet_day]
p26 = max(e26, key=lambda d: D[d]["supply_wei"])
nxt = (date.fromisoformat(p26) + timedelta(1)).isoformat()
need(f"A second rise took the supply to {money(D[p26]['supply_wei'])} USDe on {nice_day(p26)}, 2026, and {money(D[nxt]['burned_wei'])} USDe left the next day.")
need(f"On May 14, {before['holders']} accounts held the {money(before['supply_wei'])} USDe on Avalanche.")

# ---------------------------------------------------------------- method
need(f"to block {meta['end_block']:,}, the last block of October 11 UTC")
assert meta["end_block_time"] == "2026-10-11T23:59:59Z" and meta["next_block_time"] >= "2026-10-12T00:00:00Z"
fac = sorted((int(b), t) for b, t in re.findall(r"^factory 0x[0-9a-f]{40} created block (\d+) time (\S+)", ex, re.M))
start_block = int(re.search(r"const FACTORY_START = (\d+);", (HERE / "avax_usde_read.cjs").read_text()).group(1))
assert len(fac) == 2 and all(b > start_block for b, _ in fac) and fac[0][1].startswith("2026-05-15") and fac[1][1].startswith("2026-06-10")
need("The first factory contract was created on May 15, 2026 and the second on June 10, so no wallet existed before May 15.")
assert set(meta["records_with_no_value_by_month"]) == {"2025-08", "2025-09"} and meta["records_with_no_value_found_in_their_receipts"] == 0
assert meta["records_with_no_value_empty_amount"] == meta["records_with_no_value_empty_block_hash"] == meta["records_with_no_value"]
need(f"The explorer listed {meta['transfer_records_listed']:,} Transfer records. Of these, {meta['records_with_no_value']}, all from August and September 2025, "
     "had an empty amount and an empty block hash.")
assert meta["records_with_no_value_touching_ethenapay"] == 0
need(f"The other {meta['transfer_logs_kept']:,} records give every account's balance")
tie = meta["tie_to_contract"]
assert int(tie["total_supply_wei"]) - int(tie["minted_after_wei"]) + int(tie["burned_after_wei"]) == supply and meta["end_block"] < tie["block_before"] <= tie["block_after"]
need(f"Its totalSupply, the contract's own total, was {money(tie['total_supply_wei'])} USDe at block {tie['block_after']:,} on October 12.")
need(f"Adding back the {money(tie['burned_after_wei'])} USDe that left after October 11 and up to that block gives {money(supply)}, the count's supply at the end of "
     "October 11.")
assert int(tie["minted_after_wei"]) == 0 and int(tie["burned_after_wei"]) % WEI == 0
rc = load(HERE / "inputs" / "recount" / "daily_chain.csv")
assert len(rc) == 144 and rc[0]["date"] == first_wallet_day and rc[-1]["date"] == "2026-10-05"
assert all(int(r["held_wei"]) == D[r["date"]]["wallets_held_wei"] and int(r["wallets_created"]) == D[r["date"]]["wallets_created"]
           and int(r["funded"]) == D[r["date"]]["wallets_with_usde"] for r in rc)
P1 = [periods[1]]
dep = sum(int(r["deposits_wei"]) for r in rc)
cs = sum(int(r["card_spend_wei"]) for r in rc)
assert dep == flow({"minted"} | REC | RHI | POO | OTH, WAL, P1) and cs == flow(WAL, SET, P1)
assert sum(int(r["withdrawals_wei"]) for r in rc) == flow(WAL, ALLG - WAL - SET, P1) and sum(int(r["reversals_wei"]) for r in rc) == flow(SET, WAL, P1)
assert sum(int(r["yield_wei"]) + int(r["other_rewards_wei"]) for r in rc) == flow(REW, WAL, P1) and sum(int(r["internal_wei"]) for r in rc) == flow(WAL, WAL, P1)
need(f"on all {len(rc)} days from May 15 to October 5")
need(f"deposits of {money(dep)} USDe and card payments of {money(cs)} USDe to October 5, its withdrawals, returns and transfers between wallets, and its two reward "
     "flows taken together.")
need("The published recount's totals over those days matched as well")
need("so the wallets' figures for October 6 to 11 rest on this count alone.")
assert "reversals_wei" in rc[0]
need("The published recount calls the returns reversals.")
events = sum(int(r["spend_events"]) for r in rc)
n_card = flow(WAL, SET, P1, 0)
gaps = [(r["date"], int(r["card_spend_wei"]) - int(r["spend_cents"]) * 10 ** 16) for r in rc if int(r["card_spend_wei"]) != int(r["spend_cents"]) * 10 ** 16]
assert n_card - events == 1 and gaps == [("2026-09-24", 5 * WEI)]
need(f"Over the same days it counted {events:,} spend events, the records logged for card purchases, against {n_card:,} card payments in this count, and its "
     "spend events came to 5 USDe less, all of it on September 24.")
log = (HERE / "out" / "run_log.txt").read_text()
n_ok = sum(1 for l in log.splitlines() if l.startswith("ok"))
assert "FAIL" not in log
need(f"stops before writing its tables if any of its {n_ok} checks fails.")

# ---------------------------------------------------------------- the formulas block
minted_all, burned_all = sum(D[d]["minted_wei"] for d in dates), sum(D[d]["burned_wei"] for d in dates)
need(f"supply on October 11 = USDe arrived to the end of the day - USDe left to the end of the day\n                     = {money(minted_all, 6)} - {money(burned_all, 6)}\n"
     f"                     = {money(supply, 6)}\n")
need(f"tie to the token     = totalSupply at block {tie['block_after']:,} - arrived after October 11\n                       + left after October 11\n"
     f"                     = {money(tie['total_supply_wei'], 6)} - {int(tie['minted_after_wei']) // WEI} + {int(tie['burned_after_wei']) // WEI:,}\n                     = {money(supply, 6)}\n")
need(f"= {money(W)} / {money(supply)}")
need(f"= {money(W)} + {money(groups['settlement_held_wei'])} + {money(groups['settlement_recipients_held_wei'])} + {money(groups['reward_accounts_held_wei'])}")
need(f"= {money(linked)}, or {share(linked, supply)}")
need(f"= {money(from_rhino)} / {money(outside)}")
need(f"= {share(from_rhino, outside)} of deposits")
need(f"= {money(supply)} / {money(before['supply_wei'])}")
mq = multiple * 10
mr = int(mq) + (1 if mq - int(mq) >= Fraction(1, 2) else 0)
need(f"= {mr // 10}.{mr % 10} times")

# ---------------------------------------------------------------- key findings, from layout.json when the packet carries it
LAYOUT_PATH = HERE / "layout.json"
if LAYOUT_PATH.exists():
    FINDINGS = "\n".join(json.loads(LAYOUT_PATH.read_text())["keyFindings"])
    need(f"At the end of October 11, 2026 UTC, EthenaPay wallets held {millions(W)} million of the {millions(supply)} million USDe on Avalanche C-Chain, "
         f"{share(W, supply)}, and accounts tied to EthenaPay held {share(linked, supply)}.", FINDINGS)
    need(f"The supply was 55 times its May 14 level. From May 15 the rhino.fi bridge contract supplied {share(from_rhino, outside)} of the wallets' deposits.", FINDINGS)
    need(f"The chain does not show who controls the three settlement recipients, which held {share(groups['settlement_recipients_held_wei'], supply)}, or why "
         "deposits went through rhino.fi. Wallets are not people.", FINDINGS)
    assert not any(ch in FINDINGS for ch in ("\u2014", "\u2013", ";", ":")), "key findings punctuation"
    assert len(json.loads(LAYOUT_PATH.read_text())["keyFindings"]) == 3

# ---------------------------------------------------------------- page rules
body = re.sub(r"```.*?```", "", ARTICLE, flags=re.S)                       # code may use any character
body = re.sub(r"\]\([^)]*\)", "]", body)                                   # link targets
body = re.sub(r"`[^`]*`", "", body)
body = re.sub(r"\b\d{1,2}:\d{2}(:\d{2})?\b", "", body)                    # clock times
body = re.sub(r"^\|[\s\-:|]+\|$", "", body, flags=re.M)                    # table alignment rows
problems = [ch for ch in ("—", "–", ";") if ch in body] + (["colon"] if ":" in body else [])
assert not problems, problems
for field in ("description", "imageAlt", "headline"):
    assert not any(ch in META[field] for ch in ("—", "–", ";", ":")), field
assert ARTICLE.count("\n# ") + ARTICLE.startswith("# ") == 1, "one H1"
assert ARTICLE.startswith("# " + META["headline"] + "\n"), "the H1 is the metadata headline"
for name in ("EthenaPay's wallets", "Ethena Pay's", "USDe/USDC pool", "Uniswap pool", "all other holders held", "other accounts tied to EthenaPay", "method section",
             "burned none", "Download the"):
    assert name not in ARTICLE and name not in META["imageAlt"] and name not in SVG, name
assert "This article" not in ARTICLE and "this article" not in ARTICLE
assert "https://ethenadash.com/about/" in ARTICLE and "https://ethenadash.com/ethenapay/" in ARTICLE and "https://ethenadash.com/methodology/" in ARTICLE
assert ARTICLE.rstrip().endswith("Analysis of public blockchain data. Not investment advice.")
allowed = {"0x5e023c31e1d3dcd08a1b3e8c96f6ef8aa8fcacd1", "0x833e0ff43a8691f623cb8730ddb3e3180c7de08b"}   # the rhino.fi contract and the Uniswap pool
assert set(re.findall(r"0x[0-9a-fA-F]{40}", ARTICLE)) == allowed, "the only addresses in the article are the two protocol contracts"
assert len(META["description"]) <= 160 and len(META["title"]) <= 60
quotes = re.findall(r"\"[^\"]+\"", re.sub(r"```.*?```", "", ARTICLE, flags=re.S))
assert len(quotes) <= 1, quotes

if missing:
    print(f"{len(missing)} phrases missing:")
    for m in missing:
        print("  ", m)
    sys.exit(1)
print(f"All {found} phrases found, every assertion holds and the page rules pass.")
