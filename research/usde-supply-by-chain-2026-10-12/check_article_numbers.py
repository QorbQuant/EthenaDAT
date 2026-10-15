#!/usr/bin/env python3
"""Recomputes every computed figure in article_draft.md, metadata.json, layout.json's key findings and the chart's
text from the inputs, with code written apart from usde_chains_review.py, and checks that each phrase appears where
it should. Exits with an error if a phrase is missing or a page rule fails. Python 3.8 or later, no network."""
import csv
import json
import re
import sys
from datetime import datetime
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).parent
CH = HERE / "inputs" / "chain"
WEB = HERE / "inputs" / "web"
ARTICLE = (HERE / "article_draft.md").read_text(encoding="utf-8")
META = json.loads((HERE / "metadata.json").read_text())
LAYOUT = json.loads((HERE / "layout.json").read_text())
SVG = (HERE / "out" / "chart_usde_by_chain.svg").read_text()
FAILS = []
FOUND = []


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


def rnd(x, places):
    """Round a non-negative Fraction half up to places and format with thousands separators."""
    assert x >= 0
    q = Fraction(10) ** places
    n = (x * q * 2 + 1) // 2
    whole, frac = divmod(int(n), int(q))
    s = "{:,}".format(whole)
    return s + ("." + str(frac).rjust(places, "0") if places else "")


def exact(x):
    """Write a Fraction whose denominator is a power of ten in full, with thousands separators."""
    assert x >= 0
    places = 0
    while (x * Fraction(10) ** places).denominator != 1:
        places += 1
        assert places <= 30
    return rnd(x, places)


def pct(x, places=2):
    return rnd(x * 100, places) + "%"


def day(iso):
    d = datetime.strptime(iso[:10], "%Y-%m-%d")
    return "%s %d, %d" % (d.strftime("%B"), d.day, d.year)


def t(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


eth = json.loads((CH / "ethereum.json").read_text())
chains = rows(CH / "chains.csv")
hist = rows(CH / "peer_history.csv")
matrix = rows(CH / "peer_matrix.csv")
msgs = rows(CH / "lzscan_messages.csv")
flows = rows(CH / "ethereal_flows.csv")
confirm = rows(CH / "confirm_supply.csv")
stellar = json.loads((CH / "stellar_expert_usde_asset.json").read_text())
run = json.loads((CH / "browser_run.json").read_text())
llama = json.loads((WEB / "defillama_usde_extract_2026-10-12.json").read_text())
keyaddr = (WEB / "ethena_key_addresses_2026-10-12.txt").read_text()

NAME = {"bsc": "BNB Chain", "avalanche": "Avalanche", "aptos": "Aptos", "arbitrum": "Arbitrum", "optimism": "OP Mainnet",
        "metis": "Metis", "zksync": "ZKsync Era", "solana": "Solana", "kava": "Kava", "mantle": "Mantle", "linea": "Linea",
        "base": "Base", "scroll": "Scroll", "manta": "Manta Pacific", "blast": "Blast", "fraxtal": "Fraxtal", "mode": "Mode",
        "xlayer": "X Layer", "zircuit": "Zircuit", "plume": "Plume's 2024 network", "morph": "Morph", "initia": "Initia",
        "swell": "Swellchain", "ink": "Ink", "ton": "TON", "bera": "Berachain", "hyperliquid": "HyperEVM", "plasma": "Plasma",
        "monad": "Monad", "ethereal": "Ethereal", "doma": "Doma", "megaeth": "MegaETH", "tempo": "Tempo",
        "robinhood": "Robinhood Chain", "tron": "Tron", "stellar": "Stellar"}

# Amounts as exact fractions of one USDe.
A = Fraction(int(eth["adapter_balance_raw"]), 10 ** 18)
T = Fraction(int(eth["usde_total_supply_raw"]), 10 ** 18)
amount = {}
for c in chains:
    if c["chain_key"] == "stellar":
        amount["stellar"] = Fraction(int(stellar["supply"]), 10 ** int(stellar["decimals"]))
    elif c["supply_raw"]:
        amount[c["chain_key"]] = Fraction(int(c["supply_raw"]), 10 ** int(c["decimals"]))
S = sum(amount.values())

# Lead.
need("At 18:41 UTC on October 12, 2026, the adapter held %s USDe. USDe's total supply on Ethereum, which counts the USDe in the adapter, was %s, so the adapter held %s of it" % (rnd(A, 2), rnd(T, 2), pct(A / T)))
need("The USDe on the %d other chains that could be read came to %s, which was %s USDe less than the adapter held" % (len(amount), rnd(S, 2), rnd(A - S, 2)))

# Transfers in transit, from each message's blocks or times against the reads.
read_block = {"30101": int(eth["block"])}
read_time = {}
for c in chains:
    if c["read_at"] and c["method"] in ("evm", "evm native coin", "solana"):
        read_block[c["eid"]] = int(c["read_at"])
    elif c["read_time_utc"]:
        read_time[c["eid"]] = t(c["read_time_utc"])
read_time["30600"] = t(run["stellar_read"]["read_utc"])


def seen(eid, blk, when):
    if eid in read_block:
        return blk != "" and int(blk) <= read_block[eid]
    if eid in read_time:
        return when != "" and t(when) <= read_time[eid]
    return False


transit = Fraction(0)
open_msgs = []
for m in msgs:
    a = Fraction(int(m["amount_sd"]), 10 ** 6)
    sent = seen(m["src_eid"], m["src_block"], m["src_time_utc"])
    got = m["dst_block"] != "" and seen(m["dst_eid"], m["dst_block"], m["dst_time_utc"])
    if sent and not got:
        transit += a
        open_msgs.append(m)
    elif got and not sent:
        transit -= a
        open_msgs.append(m)
rule(len(open_msgs) == 1 and open_msgs[0]["dst_eid"] == "30600" and open_msgs[0]["dst_status"] == "SIMULATION_REVERTED", "expected one undelivered transfer to Stellar")
U = A - S - transit
need("One transfer of %s USDe sent from Ethereum to Stellar had not been delivered, which left %s USDe unexplained, %s of the adapter's balance" % (rnd(transit, 4), rnd(U, 2), pct(U / A, 7)))
need("the 0.9995 USDe sent to Stellar at %s UTC" % open_msgs[0]["src_time_utc"][11:16])
need("listed %d USDe transfers on any route, sent from 18:41 UTC on October 11 to its read at 18:48 UTC on October 12" % len(msgs))

# Largest chains.
order = sorted(amount.items(), key=lambda kv: -kv[1])
top5 = order[:5]
need("Five chains held USDe equal to %s of the USDe locked on Ethereum" % pct(sum(v for k, v in top5) / A))
need("Plasma held %s USDe, Solana %s, Base %s, Robinhood Chain %s and TON %s" % tuple(rnd(amount[k], 2) for k in ["plasma", "solana", "base", "robinhood", "ton"]))
rule([k for k, v in top5] == ["plasma", "solana", "base", "robinhood", "ton"], "top five order")
mid = [amount[k] for k in ["monad", "mantle", "bsc"]]
rule(min(mid) > 78 * 10 ** 6 and max(mid) < 115 * 10 ** 6, "Monad, Mantle and BNB Chain between 78 million and 115 million")
need("Monad, Mantle and BNB Chain held 78 million to 115 million each")
rest = sum(v for k, v in order[8:])
need("the other %d chains read held %s between them" % (len(order) - 8, rnd(rest, 2)))

# Peers.
first = {}
last = {}
for h in hist:
    zero = set(h["peer"][2:]) == {"0"}
    if not zero and h["eid"] not in first:
        first[h["eid"]] = h
    last[h["eid"]] = h
connected = [e for e, h in last.items() if set(h["peer"][2:]) != {"0"}]
dropped = [e for e in last if e not in connected]
need("show that a peer was set for %d chains from %s on and that %d still had one at the reads" % (len(last), day(hist[0]["time_utc"]).split(" ")[0] + " " + hist[0]["time_utc"][:4], len(connected)))
key_of = {c["eid"]: c["chain_key"] for c in chains}
sept = [e for e in dropped if last[e]["time_utc"][:10] in ("2026-09-24", "2026-09-30")]
rule(len(sept) == 7 and sorted(last[e]["time_utc"][:10] for e in sept).count("2026-09-24") == 6, "six on September 24 and one on September 30")
rule([key_of[e] for e in sept if last[e]["time_utc"][:10] == "2026-09-30"] == ["linea"], "Linea on September 30")
need("Ethena dropped six chains from the bridge on September 24, 2026 and Linea on September 30 by removing their peers")
need("Those seven chains still held %s USDe at the reads" % rnd(sum(amount[key_of[e]] for e in sept), 2))
blocks24 = sorted(set(last[e]["block"] for e in sept if last[e]["time_utc"][:10] == "2026-09-24"))
need("Six of the changes were made in a single Ethereum block, %s, on September 24, 2026" % "{:,}".format(int(blocks24[0])))
rule(len(blocks24) == 1, "one block for the six")
need("Ethena dropped %d chains by setting their peer on the adapter to zero" % len(dropped))
dropped_read = [e for e in dropped if key_of[e] in amount]
need("The %d dropped chains read held %s USDe" % (len(dropped_read), rnd(sum(amount[key_of[e]] for e in dropped_read), 2)))

# Peers named by the contracts on the dropped chains.
named = {}
for r in matrix:
    if r["peer"] not in ("error",) and set(r["peer"][2:]) != {"0"}:
        named.setdefault(r["chain_key"], []).append(r["eid_read"])
for e in dropped:
    k = key_of[e]
    row = "| %s | %s | %s | %s |" % (NAME[k], day(last[e]["time_utc"]), rnd(amount[k], 2) if k in amount else "not read",
                                    "not read" if k in ("plume", "initia") else ("Ethereum" if named.get(k) == ["30101"] else ("none" if not named.get(k) else "?")))
    need(row)
no_peer = [key_of[e] for e in sept if not named.get(key_of[e])]
rule(len(no_peer) == 6 and named.get("metis") == ["30101"] and not named.get("swell") and not named.get("doma"), "dropped chains' own peers")
need("named no peer for Ethereum or for any of the other %d chains, so it could not send USDe to any of them" % (len(last) - 1))
eid_of = {c["chain_key"]: c["eid"] for c in chains}
for k in sorted(set(r["chain_key"] for r in matrix)):
    got = set(r["eid_read"] for r in matrix if r["chain_key"] == k)
    rule(got == ({"30101"} | set(last)) - {eid_of[k]}, "peers read for Ethereum and the other 35 chains on " + k)
eth_named = sorted(e for e in named.get("ethereal", []) if e != "30101")
rule(len(eth_named) == 7, "Ethereal's contract names seven other chains")
rule(eid_of["tron"] in named.get("plasma", []) and eid_of["plasma"] in named.get("tron", []), "Plasma and Tron name each other")
need("The adapter's peer on Ethereal also named peers of its own on %s other chains, and the contracts on Plasma and Tron named each other" % {7: "seven"}[len(eth_named)])

# Connected table.
for e in connected:
    k = key_of[e]
    share = amount[k] / A
    s = pct(share) if share * 100 >= Fraction(1, 200) else "under 0.01%"
    need("| %s | %s | %s | %s |" % (NAME[k], day(first[e]["time_utc"]), rnd(amount[k], 2), s))
need("The table lists the %d chains where the adapter had a peer at the reads, with the date a peer was first set for each" % len(connected))

# Custodian.
psm = {c["chain_key"]: Fraction(int(c["psm_custodian_raw"]), 10 ** 18) for c in chains if c["psm_custodian_raw"]}
rule([k for k, v in psm.items() if v] == ["avalanche"], "custodian on Avalanche only")
need("Avalanche's figure includes %s USDe held by Ethena's PSM custodian" % rnd(psm["avalanche"], 2))
psm_evm_others = [c for c in chains if c["psm_custodian_raw"] and c["chain_key"] not in ("avalanche", "tron")]
rule(any(c["chain_key"] == "tron" and c["psm_custodian_raw"] for c in chains), "custodian read on Tron")
need("The custodian held no USDe on the other %d chains that run Ethereum-style smart contracts where its balance was read, or on Tron, and it held %s USDe on Ethereum"
     % (len(psm_evm_others), rnd(Fraction(int(eth["psm_custodian_balance_raw"]), 10 ** 18), 2)))
rule("USDe held at this address is not in circulation" in keyaddr, "key addresses passage on circulation")

# Reconciliation table.
for label, v in [("USDe's total supply on Ethereum, including the adapter's USDe", T), ("Locked in the adapter", A), ("On Ethereum outside the adapter", T - A),
                 ("On the %d other chains read" % len(amount), S), ("Adapter less the chains", A - S), ("Sent from Ethereum to Stellar and not delivered", transit), ("Unexplained", U)]:
    need("| %s | %s |" % (label, rnd(v, 2)))

# Timing. The start rounded to the nearest second, the end rounded up.
from datetime import timedelta
start = t(eth["snapshot_started_utc"])
start_r = (start + timedelta(microseconds=500000)).replace(microsecond=0)
need("started together at %s UTC" % start_r.strftime("%H:%M:%S"))
end = t(eth["snapshot_finished_utc"])
end_up = (end.replace(microsecond=0) + timedelta(seconds=1 if end.microsecond else 0)).strftime("%H:%M:%S")
need("ended by %s UTC" % end_up)

# Remainders below a millionth.
rem_a = Fraction(int(eth["adapter_balance_raw"]) % 10 ** 12, 10 ** 18)
need("Its balance still had %s USDe beyond a whole number of millionths" % ("0." + str(int(eth["adapter_balance_raw"]) % 10 ** 12).rjust(18, "0")))
sol = [c for c in chains if c["chain_key"] == "solana"][0]
sol_rem = int(sol["supply_raw"]) % 1000
rule(sol_rem == 552, "Solana remainder")
need("which had 0.000000%d beyond one" % sol_rem)
others = [k for k, v in amount.items() if (v * 10 ** 6).denominator != 1]
rule(others == ["solana"], "only Solana has a remainder")

# Ethereal.
allf = [r for r in flows if r["other_eid"] == "all"][0]
rec = Fraction(int(allf["received_raw"]), 10 ** 18)
sen = Fraction(int(allf["sent_raw"]), 10 ** 18)
need("it recorded {:,} arrivals of {} USDe and {:,} departures of {} USDe, which left {} USDe on Ethereal".format(int(allf["received_count"]), rnd(rec, 2), int(allf["sent_count"]), rnd(sen, 2), rnd(rec - sen, 2)))
need("Ethereal          = %s received - %s sent" % (rnd(rec, 6), rnd(sen, 6)))
need("                  = %s" % rnd(rec - sen, 6))

# Swellchain.
sw = [c for c in chains if c["chain_key"] == "swell"][0]
need("Swellchain's figure came from a block of %s UTC on October 12" % sw["read_time_utc"][11:16])
need("Swellchain's from a block of %s UTC" % sw["read_time_utc"][11:16], "svg")
need("read Swellchain only at a block from %s UTC on October 12, 2026" % sw["read_time_utc"][11:16], "findings")

# DefiLlama.
cur = llama["currentChainBalances"]
LL = {"bsc": "BSC", "avalanche": "Avalanche", "arbitrum": "Arbitrum", "optimism": "OP Mainnet", "metis": "Metis", "zksync": "ZKsync Era",
      "solana": "Solana", "kava": "Kava", "mantle": "Mantle", "linea": "Linea", "base": "Base", "scroll": "Scroll", "manta": "Manta",
      "blast": "Blast", "fraxtal": "Fraxtal", "mode": "Mode", "xlayer": "X Layer", "zircuit": "Zircuit", "morph": "Morph", "swell": "Swellchain",
      "ink": "Ink", "ton": "TON", "bera": "Berachain", "hyperliquid": "Hyperliquid L1", "plasma": "Plasma", "monad": "Monad", "megaeth": "MegaETH",
      "tempo": "Tempo", "robinhood": "Robinhood Chain"}
same, diffs = [], {}
for k, n in LL.items():
    ours = amount[k] - psm.get(k, 0)
    theirs = Fraction(str(cur[n]["peggedUSD"]))
    d = ours - theirs
    if abs(d) < Fraction(15, 10 ** 7):
        same.append(k)
    else:
        diffs[k] = d
rule(sorted(diffs) == ["base", "robinhood", "solana", "swell"], "DefiLlama differences")
need("gave the same figure to the millionth of a USDe for %d chains when read at %s UTC" % (len(same), llama["read_utc"][11:16]))
unrel = Fraction(str(llama["tokens_last"]["unreleased"]["peggedUSD"]))
psm_both = psm["avalanche"] + Fraction(int(eth["psm_custodian_balance_raw"]), 10 ** 18)
rule(abs(unrel - psm_both) < Fraction(1, 10 ** 6), "DefiLlama's unreleased figure equals the custodian on Avalanche and Ethereum")
need("DefiLlama's latest daily record counted %s USDe as unreleased" % rnd(unrel, 2))
small = min(abs(diffs[k]) for k in ["base", "robinhood", "solana"])
big = max(abs(diffs[k]) for k in ["base", "robinhood", "solana"])
need("DefiLlama's Solana, Base and Robinhood Chain figures differed by %s to %s USDe" % (rnd(small, 2), rnd(big, 2)))
rule(cur["Swellchain"]["peggedUSD"] == 0, "DefiLlama shows no USDe on Swellchain")
need("it listed %s USDe on Movement" % rnd(Fraction(str(cur["Movement"]["peggedUSD"])), 2))
rule(not any(h["chain_key"] == "movement" for h in hist), "Movement absent from the adapter's records")

# Ethena's list.
listed = re.findall(r"^\* (\S+)$", keyaddr, re.M)
need("listed %d chains where Ethena's tokens were available" % len(listed))
rule("datetime 2026-09-17T18:50:03.509Z" in keyaddr, "page date")
need("last updated on September 17, 2026")

# Method.
need("The chains come from the adapter's %d PeerSet records" % len(hist))
need("returned the same %d records" % eth["peer_logs"]["routescan"]["count"])
ap = rows(CH / "adapter_peers_at_read.csv")
need("the adapter's peers for all %d of LayerZero's endpoint IDs" % len(ap))
need("a second RPC gave the same peers for the %d chains" % len(last))
evm_contract = [c for c in chains if c["method"] == "evm" and c["chain_type"] == "evm" and c["supply_raw"]]
need("For %d chains that run Ethereum-style smart contracts and for Tron" % len(evm_contract))
two = [c for c in chains if c["source2_supply_raw"] and c["source2_supply_raw"] == c["supply_raw"]]
two_keys = set(c["chain_key"] for c in two) | set(r["chain_key"] for r in confirm if r["supply_raw"] and r["read_at"] == r["block_requested"])
need("A second source gave the same supply for %d chains" % len(two_keys))
later = [r for r in confirm if r["supply_raw"] and r["read_at"] and r["read_at"] != r["block_requested"]]
av = [r for r in later if r["chain_key"] == "avalanche"]
av_up = Fraction(int(av[0]["supply_raw"]), 10 ** 18) - amount["avalanche"]
need("showed Avalanche's supply up %s USDe ten minutes later" % rnd(av_up, 2))
lz_read = t(run["messages_read_utc"])
av_read = t(av[0]["read_utc"])
rule(round((av_read - lz_read).total_seconds() / 60) == 4, "LayerZero Scan read four minutes before Avalanche's second read")
rule(not any(m["dst_eid"] == "30106" and m["dst_time_utc"] and t(m["dst_time_utc"]) > t([c for c in chains if c["chain_key"] == "avalanche"][0]["read_time_utc"]) for m in msgs), "no listed transfer reached Avalanche after its read")
need("LayerZero Scan, read four minutes before that second read, listed no transfer that explains the rise")

# Code block.
need("locked share      = %s / %s" % (rnd(A, 2), rnd(T, 2)))
need("                  = %s" % pct(A / T))
need("                  = %s - %s" % (exact(A), exact(S)))
need("                  = %s" % exact(A - S))
need("                  = %s - %s" % (exact(A - S), exact(transit)))
need("                  = %s, or %s of the adapter's balance" % (exact(U), pct(U / A, 7)))
need("                  = %s" % pct(sum(v for k, v in top5) / A))

# Checks count.
log = (HERE / "out" / "run_log.txt").read_text()
n_checks = int(re.search(r"^(\d+) checks, 0 failed$", log, re.M).group(1))
need("if any of its %d checks fails" % n_checks)

# Metadata, key findings and chart.
need("held %s billion USDe" % rnd(A / 10 ** 9, 2), "meta")
need("the USDe on %d other chains came within %s USDe of it" % (len(amount), rnd(A - S, 2)), "meta")
need("held %s USDe, %s of USDe's total supply on Ethereum, and the USDe on the %d other chains read added up to it within %s USDe" % (rnd(A, 2), pct(A / T), len(amount), rnd(A - S, 2)), "findings")
need("At 18:41 UTC on October 12, 2026, five chains held USDe equal to %s of the USDe locked on Ethereum" % pct(sum(v for k, v in top5) / A), "findings")
need("could not tell what left %s USDe unexplained" % rnd(U, 2), "findings")
need("Plasma held %s million, Solana %s million, Base %s million, Robinhood Chain %s million and TON %s million" % tuple(rnd(amount[k] / 10 ** 6, 1) for k in ["plasma", "solana", "base", "robinhood", "ton"]), "findings")
need("Five chains held USDe equal to %s%% of the USDe locked on Ethereum" % rnd(sum(v for k, v in top5) / A * 100, 0), "svg")
need("The %d other chains include %d dropped chains" % (len(order) - 10, len([e for e in dropped if key_of[e] in amount and key_of[e] not in [k for k, v in order[:10]]])), "svg")
for k in ["plasma", "solana", "base", "robinhood", "ton", "monad", "mantle", "bsc", "bera", "avalanche"]:
    need("%s, %s million, %s%%." % (NAME[k], rnd(amount[k] / 10 ** 6, 1), rnd(amount[k] / A * 100, 1)), "svg")
    need("%s %s" % (NAME[k], rnd(amount[k] / 10 ** 6, 1)), "meta")
    need("%s %s" % (NAME[k], rnd(amount[k] / 10 ** 6, 1)))
rest10 = sum(v for k, v in order[10:])
need("%d other chains %s" % (len(order) - 10, rnd(rest10 / 10 ** 6, 1)), "meta")
need("%d other chains, %s million, %s%%." % (len(order) - 10, rnd(rest10 / 10 ** 6, 1), rnd(rest10 / A * 100, 1)), "svg")
need("USDe at Ethereum block {:,}".format(int(eth["block"])), "svg")
need("Shares of the adapter's balance at Ethereum block {:,}".format(int(eth["block"])))

# ---- page rules ----------------------------------------------------------------------------------------------------
lines = ARTICLE.split("\n")
rule(sum(1 for l in lines if l.startswith("# ")) == 1 and lines[0] == "# " + META["headline"], "one H1, the metadata headline")
rule(len(META["title"]) <= 60 and 120 <= len(META["description"]) <= 160, "title and description lengths")
rule("[Qorban Ferrell · @Degenerate\\_DeFi](https://ethenadash.com/about/) · Published " + datetime.fromisoformat(META["datePublished"]).strftime("%d %B %Y") in ARTICLE, "byline with author link and date")
rule(ARTICLE.rstrip().endswith("Analysis of public blockchain data. Not investment advice."), "closing line")
for bad in ["—", "–", ";", "This article", "on-chain", "FAQ"]:
    rule(bad not in ARTICLE, "forbidden text in article: %r" % bad)
    rule(bad not in " ".join(LAYOUT["keyFindings"]) + META["description"], "forbidden text in metadata or findings: %r" % bad)
in_code = False
for l in lines:
    if l.startswith("```"):
        in_code = not in_code
        continue
    if in_code or l.startswith("|") or l.startswith("!["):
        continue
    stripped = re.sub(r"\(https?://[^)]*\)|`[^`]*`|\b\d{1,2}:\d{2}(:\d{2})?\b", "", l)
    rule(":" not in stripped, "colon outside a clock time, link, code or table: " + l[:80])
heads = [l[3:] for l in lines if l.startswith("## ")]


def slug(h):
    return re.sub(r"[^a-z0-9]+", "-", h.lower().replace("'", "")).strip("-")


rule([slug(h) for h in heads] == [n[1] for n in LAYOUT["navigation"]], "navigation anchors match the headings")
for link in ["https://ethenadash.com/ethenapay/", "https://ethenadash.com/methodology/", "https://ethenadash.com/research/avalanche-usde-ethenapay-2026-10-11/"]:
    rule(link in ARTICLE, "link missing " + link)
rule(LAYOUT["dashboard"] == "/ethenapay/", "dashboard link")
rule(len(LAYOUT["keyFindings"]) == 3, "three key findings")
for f in LAYOUT["archiveFiles"]:
    rule((HERE / f).exists(), "archive file missing " + f)
for f in LAYOUT["assets"]:
    rule((HERE / "out" / f).exists(), "asset missing " + f)
for m in re.findall(r"\(/research-assets/usde-supply-by-chain-2026-10-12/([^)]+)\)", ARTICLE):
    rule(m in LAYOUT["assets"] or m == "calculation-files.zip", "linked download not in assets " + m)

# No individual addresses or transaction hashes in the published files.
allowed = {"0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34", "0x4c9edd5852cd905f086c759e8383e09bff1e68b3", "0xd7fcade52afb60fbf0e1e5f72a683f43820f56a0"}
for c in chains:
    for v in (c["contract_read"], c["oft_or_store"]):
        if v.startswith("0x") and len(v) == 42:
            allowed.add(v.lower())
for r in rows(CH / "lz_chains.csv"):
    for v in (r["usde_token"], r["usde_proxy"]):
        if v.startswith("0x") and len(v) == 42:
            allowed.add(v.lower())
for h in hist:
    allowed.add("0x" + h["peer"][-40:].lower())
allowed |= set(a.lower() for a in re.findall(r"0x[0-9a-fA-F]{40}(?![0-9a-fA-F])", keyaddr))
for f in LAYOUT["archiveFiles"]:
    p = HERE / f
    if p.suffix in (".png", ".zip") or not p.exists():
        continue
    text = p.read_text(encoding="utf-8")
    for a in re.findall(r"0x[0-9a-fA-F]{40}(?![0-9a-fA-F])", text):
        if a.lower() not in allowed and not re.fullmatch(r"0x0+[0-9a-fA-F]{0,8}", a):
            FAILS.append("address not on the allowed list in %s: %s" % (f, a))
            break
    if f.startswith(("inputs/", "out/")):
        for bad in ['"transactionHash"', '"txHash"', '"transactions":[', '"miner"']:
            rule(bad not in text, "%s in %s" % (bad, f))

if FAILS:
    print("\n".join(FAILS))
    sys.exit(1)
print("%d phrases found, page rules pass" % len(FOUND))
