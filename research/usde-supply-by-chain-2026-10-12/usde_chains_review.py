#!/usr/bin/env python3
"""USDe on every chain that Ethena's USDe OFT adapter on Ethereum has had as a peer, reconciled with the
USDe the adapter held on Ethereum at 18:41 UTC on October 12, 2026.

Reads the files in inputs/, runs its checks and, if all pass, writes the tables in out/. If any check
fails it writes out/run_log_failed.txt and stops, so out/ keeps the tables of the last clean run.
Python 3.8 or later, standard library only, no network.
"""
import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
IN = os.path.join(HERE, "inputs")
CH = os.path.join(IN, "chain")
WEB = os.path.join(IN, "web")
OUT = os.path.join(HERE, "out")

ADAPTER = "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34"
USDE = "0x4c9edd5852cd905f086c759e8383e09bff1e68b3"
ETH_EID = 30101
WEI = 10 ** 18
SD_TO_WEI = 10 ** 12  # 6 shared decimals to 18 local decimals

# Display names. LayerZero's chain keys on the left.
NAMES = {
    "ethereum": "Ethereum", "bsc": "BNB Chain", "avalanche": "Avalanche", "aptos": "Aptos",
    "arbitrum": "Arbitrum", "optimism": "OP Mainnet", "metis": "Metis", "zksync": "ZKsync Era",
    "solana": "Solana", "kava": "Kava", "mantle": "Mantle", "linea": "Linea", "base": "Base",
    "scroll": "Scroll", "manta": "Manta Pacific", "blast": "Blast", "fraxtal": "Fraxtal", "mode": "Mode",
    "xlayer": "X Layer", "zircuit": "Zircuit", "plume": "Plume's 2024 network", "morph": "Morph",
    "initia": "Initia", "swell": "Swellchain", "ink": "Ink", "ton": "TON", "bera": "Berachain",
    "hyperliquid": "HyperEVM", "plasma": "Plasma", "monad": "Monad", "ethereal": "Ethereal",
    "doma": "Doma", "megaeth": "MegaETH", "tempo": "Tempo", "robinhood": "Robinhood Chain",
    "tron": "Tron", "stellar": "Stellar",
}
# DefiLlama's chain names for the same chains.
LLAMA = {
    "bsc": "BSC", "avalanche": "Avalanche", "arbitrum": "Arbitrum", "optimism": "OP Mainnet",
    "metis": "Metis", "zksync": "ZKsync Era", "solana": "Solana", "kava": "Kava", "mantle": "Mantle",
    "linea": "Linea", "base": "Base", "scroll": "Scroll", "manta": "Manta", "blast": "Blast",
    "fraxtal": "Fraxtal", "mode": "Mode", "xlayer": "X Layer", "zircuit": "Zircuit", "morph": "Morph",
    "swell": "Swellchain", "ink": "Ink", "ton": "TON", "bera": "Berachain", "hyperliquid": "Hyperliquid L1",
    "plasma": "Plasma", "monad": "Monad", "megaeth": "MegaETH", "tempo": "Tempo", "robinhood": "Robinhood Chain",
}
# Ethena's key addresses page, its list of chains, in the page's words, with LayerZero's keys.
DOCS_LIST = {
    "TON": "ton", "Aptos": "aptos", "Berachain": "bera", "Solana": "solana", "Mantle": "mantle",
    "Blast": "blast", "Arbitrum": "arbitrum", "Optimism": "optimism", "Base": "base", "Zircuit": "zircuit",
    "ZKSync": "zksync", "BNB": "bsc", "Linea": "linea", "Manta": "manta", "Scroll": "scroll",
    "Fraxtal": "fraxtal", "Mode": "mode", "XLayer": "xlayer", "Metis": "metis", "Kava": "kava",
    "Morph": "morph", "Swell": "swell",
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


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def fmt_units(raw, decimals, places=None):
    """Exact decimal string of raw / 10**decimals, rounded half up to places if given."""
    neg = raw < 0
    raw = -raw if neg else raw
    if places is not None and places < decimals:
        q = 10 ** (decimals - places)
        raw = (raw + q // 2) // q
        decimals = places
    s = str(raw).rjust(decimals + 1, "0")
    out = s[:-decimals] + "." + s[-decimals:] if decimals else s
    return ("-" if neg else "") + out


def usd(wei, places=2):
    return fmt_units(wei, 18, places)


def pct(num, den, places=2):
    """Percentage num/den, rounded half up, as a string."""
    q = 10 ** places
    v = (num * 100 * q * 2 + den) // (2 * den)
    s = str(v).rjust(places + 1, "0")
    return s[:-places] + "." + s[-places:]


def iso(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_zero32(h):
    return h.startswith("0x") and set(h[2:]) <= {"0"}


def b58(hexstr):
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    n = int(hexstr, 16)
    s = ""
    while n > 0:
        n, r = divmod(n, 58)
        s = alphabet[r] + s
    for i in range(0, len(hexstr), 2):
        if hexstr[i:i + 2] == "00":
            s = "1" + s
        else:
            break
    return s


def stellar_contract_strkey(hexstr):
    raw = bytes([2 << 3]) + bytes.fromhex(hexstr)
    crc = 0
    for b in raw:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    data = raw + bytes([crc & 0xFF, crc >> 8])
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    bits = val = 0
    out = ""
    for b in data:
        val = (val << 8) | b
        bits += 8
        while bits >= 5:
            out += alphabet[(val >> (bits - 5)) & 31]
            bits -= 5
    if bits:
        out += alphabet[(val << (5 - bits)) & 31]
    return out


def parse_utc(s):
    s = s.replace("Z", "+00:00")
    if "." in s:
        head, tail = s.split(".", 1)
        frac, tz = tail[:-6], tail[-6:]
        s = head + "." + frac.ljust(6, "0")[:6] + tz
    return datetime.fromisoformat(s)


def main():
    os.makedirs(OUT, exist_ok=True)
    log("USDe by chain, reconciled with Ethena's USDe OFT adapter on Ethereum")
    log("")

    # ---- inputs ------------------------------------------------------------------------------------
    manifest = read_csv(os.path.join(IN, "manifest.csv"))
    bad = []
    absent = []
    for m in manifest:
        p = os.path.join(HERE, m["path"])
        if not os.path.exists(p) and m["in_download"] == "no":
            absent.append(m["path"])
            continue
        if not os.path.exists(p) or os.path.getsize(p) != int(m["bytes"]) or sha256_file(p) != m["sha256"]:
            bad.append(m["path"])
    check("every input matches its size and SHA-256 in inputs/manifest.csv", not bad,
          "%d files%s%s" % (len(manifest) - len(absent), ", failed " + ", ".join(bad) if bad else "", ", review copy only and absent here " + ", ".join(absent) if absent else ""))

    digests = json.load(open(os.path.join(CH, "browser_digests.json")))
    run = json.load(open(os.path.join(CH, "browser_run.json")))
    browser_files = ["lz_chains.csv", "peer_history.csv", "adapter_peers_at_read.csv", "chains.csv", "peer_matrix.csv",
                     "ethereal_flows.csv", "ethereum.json", "request_log.csv", "lzscan_messages.csv", "lzscan_queries.csv",
                     "lzscan_window.json", "confirm_supply.csv", "arbitrum_peers.csv"]
    full_raw = os.path.exists(os.path.join(CH, "raw_reads_redacted.jsonl"))
    if full_raw:
        browser_files.append("raw_reads_redacted.jsonl")
    bad = [f for f in browser_files if sha256_file(os.path.join(CH, f)) != digests.get(f)]
    check("the browser's files match the SHA-256 digests the browser computed", not bad, "%d files%s" % (len(browser_files), ", failed " + ", ".join(bad) if bad else ""))
    raw_path = os.path.join(CH, "raw_reads_redacted.jsonl" if full_raw else "raw_reads_public.jsonl")
    raw_lines = open(raw_path, encoding="utf-8").read().splitlines()
    public_lines = open(os.path.join(CH, "raw_reads_public.jsonl"), encoding="utf-8").read().splitlines()
    if full_raw:
        kept = [l for l in raw_lines if json.loads(l)["label"] != "initia resources"]
        check("raw_reads_public.jsonl is raw_reads_redacted.jsonl without the Initia resources response", kept == public_lines, "%d of %d lines" % (len(public_lines), len(raw_lines)))
    raw = [json.loads(l) for l in raw_lines]
    check("the read script in browser/ is the one the browser ran", sha256_file(os.path.join(HERE, "browser", "usde_chains_read.js")) == run["read_script_sha256_in_browser"], run["read_script_sha256_in_browser"][:16])
    check("the confirming script in browser/ is the one the browser ran", sha256_file(os.path.join(HERE, "browser", "usde_chains_confirm.js")).startswith(run["confirm_script_sha256_prefix_in_browser"]), run["confirm_script_sha256_prefix_in_browser"])
    check("Stellar Expert's asset record matches the digest the browser computed", sha256_file(os.path.join(CH, "stellar_expert_usde_asset.json")).startswith(run["stellar_read"]["sha256_prefix_in_browser"]))
    check("the DefiLlama extract matches the digest the browser computed", sha256_file(os.path.join(WEB, "defillama_usde_extract_2026-10-12.json")).startswith(run["defillama_extract_sha256_prefix_in_browser"]))

    eth = json.load(open(os.path.join(CH, "ethereum.json")))
    chains = read_csv(os.path.join(CH, "chains.csv"))
    lzc = {r["eid"]: r for r in read_csv(os.path.join(CH, "lz_chains.csv"))}
    history = read_csv(os.path.join(CH, "peer_history.csv"))
    at_read = read_csv(os.path.join(CH, "adapter_peers_at_read.csv"))
    matrix = read_csv(os.path.join(CH, "peer_matrix.csv"))
    arb_peers = read_csv(os.path.join(CH, "arbitrum_peers.csv"))
    ethereal_flows = read_csv(os.path.join(CH, "ethereal_flows.csv"))
    messages = read_csv(os.path.join(CH, "lzscan_messages.csv"))
    window = json.load(open(os.path.join(CH, "lzscan_window.json")))
    confirm = read_csv(os.path.join(CH, "confirm_supply.csv"))
    stellar = json.load(open(os.path.join(CH, "stellar_expert_usde_asset.json")))
    llama = json.load(open(os.path.join(WEB, "defillama_usde_extract_2026-10-12.json")))

    # ---- Ethereum ----------------------------------------------------------------------------------
    log("")
    log("Ethereum")
    A = int(eth["adapter_balance_raw"])
    T = int(eth["usde_total_supply_raw"])
    psm_eth = int(eth["psm_custodian_balance_raw"])
    check("the adapter's token() is USDe on Ethereum", eth["adapter_token"].lower() == USDE)
    check("the adapter reports approvalRequired, so it locks USDe rather than minting it", eth["adapter_approval_required"] == 1)
    check("the adapter's shared decimals are 6 and its conversion rate 10^12", eth["adapter_shared_decimals"] == 6 and int(eth["adapter_decimal_conversion_rate"]) == SD_TO_WEI)
    check("a second RPC gave the same USDe supply and adapter balance at the same block", eth["rpc2_usde_total_supply_raw"] == eth["usde_total_supply_raw"] and eth["rpc2_adapter_balance_raw"] == eth["adapter_balance_raw"], eth["rpc2"])
    snap = [x for x in raw if x["label"] == "snapshot ethereum"]
    ok = False
    if snap:
        req = snap[-1]["request"]
        res = {r["id"]: r.get("result") for r in json.loads(snap[-1]["response"])}
        blk = res[0]
        ok = (int(blk["number"], 16) == eth["block"] and iso(int(blk["timestamp"], 16)) == eth["time_utc"].replace(".000Z", "Z")
              and int(res[1], 16) == T and int(res[2], 16) == A and int(res[3], 16) == psm_eth
              and req[2]["params"][0]["data"].endswith(ADAPTER[2:]) and req[1]["params"][0]["to"] == USDE)
    check("the raw Ethereum response gives the block, its time, USDe's supply, the adapter's balance and the custodian's", ok, "block %d at %s" % (eth["block"], eth["time_utc"]))
    log("  USDe supply %s, adapter %s (%s%%), on Ethereum outside the adapter %s" % (usd(T), usd(A), pct(A, T), usd(T - A)))

    # ---- peer history ------------------------------------------------------------------------------
    log("")
    log("Peer history")
    check("Blockscout and Routescan returned the same %d PeerSet records" % eth["peer_logs"]["blockscout"]["count"],
          eth["peer_logs"]["agree"] and eth["peer_logs"]["blockscout"]["count"] == eth["peer_logs"]["routescan"]["count"] == len(history))
    last = {}
    first = {}
    for h in history:
        e = int(h["eid"])
        last[e] = h
        if not is_zero32(h["peer"]) and e not in first:
            first[e] = h
    union = sorted(last)
    connected = [e for e in union if not is_zero32(last[e]["peer"])]
    removed = [e for e in union if is_zero32(last[e]["peer"])]
    mism = []
    for r in at_read:
        e = int(r["eid"])
        want = last[e]["peer"] if e in last else "0x" + "0" * 64
        if r["peer_rpc1"].lower() != want.lower():
            mism.append(r["eid"])
        if e in last and r["peer_rpc2"].lower() != r["peer_rpc1"].lower():
            mism.append(r["eid"] + " rpc2")
    check("at the read block the adapter's peers match the last PeerSet record for every one of the %d endpoint IDs, on both RPCs" % len(at_read), not mism, ", ".join(mism))
    check("the adapter had %d peers at the read and had removed %d" % (len(connected), len(removed)), len(connected) == 25 and len(removed) == 11 and len(union) == 36)
    by_eid = {int(c["eid"]): c for c in chains}
    check("chains.csv has one row for each of the 36 chains", sorted(by_eid) == union)
    bad = [c["chain_key"] for c in chains if int(c["connected_at_read"]) != (int(c["eid"]) in connected)]
    check("chains.csv marks the same chains connected", not bad, ", ".join(bad))
    bad = []
    for c in chains:
        e = int(c["eid"])
        p = [h for h in history if int(h["eid"]) == e and not is_zero32(h["peer"])][-1]["peer"].lower()
        if c["method"].startswith("evm"):
            if c["oft_or_store"].lower() != "0x" + p[-40:]:
                bad.append(c["chain_key"])
        elif c["method"] == "solana":
            if c["oft_or_store"] != b58(p[2:]):
                bad.append(c["chain_key"])
    check("every EVM contract and the Solana store read is the adapter's last peer for that chain", not bad, ", ".join(bad))

    # ---- chain reads -------------------------------------------------------------------------------
    log("")
    log("Chain reads")
    supply = {}  # eid -> (raw, decimals)
    for c in chains:
        if c["supply_raw"] != "":
            supply[int(c["eid"])] = (int(c["supply_raw"]), int(c["decimals"]))
    stellar_eid = [int(c["eid"]) for c in chains if c["chain_key"] == "stellar"][0]
    stellar_token = lzc[str(stellar_eid)]["usde_token"]
    check("Stellar Expert's asset is the contract LayerZero's metadata gives for USDe on Stellar", stellar["contract"] == stellar_contract_strkey(stellar_token[2:]), stellar["contract"])
    supply[stellar_eid] = (int(stellar["supply"]), int(stellar["decimals"]))
    unread = [c["chain_key"] for c in chains if int(c["eid"]) not in supply]
    check("every chain was read except Plume's 2024 network, whose only RPC did not answer", unread == ["plume"], ", ".join(unread))

    # Raw EVM responses. A batch the RPC answered, or the single calls made where it refused batches.
    def answers(label, url):
        got = {}
        for x in raw:
            if x["label"] != label or x["url"] != url:
                continue
            try:
                resp = json.loads(x["response"])
            except ValueError:
                continue
            reqs = x["request"] if isinstance(x["request"], list) else [x["request"]]
            resps = resp if isinstance(resp, list) else [resp]
            by_id = {r.get("id"): r for r in resps}
            for q in reqs:
                r = by_id.get(q["id"])
                if r is None or "error" in r or "result" not in r:
                    continue
                if q["method"] == "eth_getBlockByNumber":
                    key = ("block", q["params"][0])
                elif q["method"] == "eth_getBalance":
                    key = ("balance", q["params"][0].lower(), q["params"][1])
                else:
                    key = ("call", q["params"][0]["to"].lower(), q["params"][0]["data"], q["params"][1])
                got[key] = r["result"]
        return got

    bad = []
    n_ok = 0
    for c in chains:
        if not c["method"].startswith("evm") or c["supply_raw"] == "":
            continue
        got = answers("snapshot " + c["chain_key"], c["source1"])
        tron = c["chain_type"] == "tron"
        B = "latest" if tron else hex(int(c["read_at"]))
        blk = got.get(("block", B))
        oft = c["oft_or_store"].lower()
        ok = blk is not None and int(blk["number"], 16) == int(c["read_at"]) and iso(int(blk["timestamp"], 16)) == c["read_time_utc"].replace(".000Z", "Z")
        peer = got.get(("call", oft, "0xbb0b6a53" + hex(ETH_EID)[2:].rjust(64, "0"), B))
        ok = ok and peer is not None and peer.lower() == c["chain_side_peer_for_ethereum"].lower()
        if c["method"] == "evm native coin":
            ok = ok and int(got.get(("balance", oft, B), "0x1"), 16) == 0
        else:
            tok = c["contract_read"].lower()
            sup = got.get(("call", tok, "0x18160ddd", B))
            dec = got.get(("call", tok, "0x313ce567", B))
            psm_v = got.get(("call", tok, "0x70a08231" + "d7fcade52afb60fbf0e1e5f72a683f43820f56a0".rjust(64, "0"), B))
            ok = ok and sup is not None and int(sup, 16) == int(c["supply_raw"]) and dec is not None and int(dec, 16) == int(c["decimals"])
            ok = ok and psm_v is not None and int(psm_v, 16) == int(c["psm_custodian_raw"])
        if ok:
            n_ok += 1
        else:
            bad.append(c["chain_key"])
    check("for every EVM chain and Tron the raw responses give the block, its time, the supply, the decimals, the custodian's balance and the contract's peer for Ethereum", not bad, "%d chains%s" % (n_ok, ", failed " + ", ".join(bad) if bad else ""))

    sol = [c for c in chains if c["chain_key"] == "solana"][0]
    sol_raw = [x for x in raw if x["label"] == "solana supply"]
    vals = []
    for x in sol_raw:
        try:
            j = json.loads(x["response"])
            vals.append((x["url"], j["result"]["context"]["slot"], int(j["result"]["value"]["amount"]), j["result"]["value"]["decimals"]))
        except (ValueError, KeyError, TypeError):
            pass
    check("two Solana RPCs gave the same USDe supply", len(vals) == 2 and vals[0][2] == vals[1][2] == int(sol["supply_raw"]) and vals[0][3] == 9, "slots %s" % ", ".join(str(v[1]) for v in vals))
    mint = [x for x in raw if x["label"] == "solana mint"]
    info = json.loads(mint[-1]["response"])["result"]["value"]["data"]["parsed"]["info"]
    check("the Solana mint's authority is the adapter's peer on Solana and it has no freeze authority", info["mintAuthority"] == sol["oft_or_store"] and info["freezeAuthority"] is None, info["mintAuthority"])

    apt = [c for c in chains if c["chain_key"] == "aptos"][0]
    apt_raw = [int(json.loads(x["response"])[0]["vec"][0]) for x in raw if x["label"] == "aptos supply"]
    check("two Aptos endpoints gave the same supply at the same ledger version", len(apt_raw) == 2 and apt_raw[0] == apt_raw[1] == int(apt["supply_raw"]), "version " + apt["read_at"])
    ton = [c for c in chains if c["chain_key"] == "ton"][0]
    ton1 = [json.loads(x["response"])["jetton_masters"][0] for x in raw if x["label"] == "ton supply"][0]
    ton2 = [json.loads(x["response"]) for x in raw if x["label"] == "ton supply 2"][0]
    check("toncenter and tonapi gave the same TON jetton supply", int(ton1["total_supply"]) == int(ton2["total_supply"]) == int(ton["supply_raw"]) and ton1["jetton_content"]["decimals"] == "6")
    ini = [c for c in chains if c["chain_key"] == "initia"][0]
    b1 = [json.loads(x["response"]) for x in raw if x["label"] == "initia bank supply"][0]
    b2 = [json.loads(x["response"]) for x in raw if x["label"] == "initia view supply"][0]
    check("Initia's bank module and its Move view gave the same supply at the same height",
          int(b1["amount"]["amount"]) == int(json.loads(b2["data"])) == int(ini["supply_raw"]) and b1["amount"]["denom"] == "move/" + ini["contract_read"][2:])

    eth_flows = [r for r in ethereal_flows if r["other_eid"] == "all"][0]
    by_other = [r for r in ethereal_flows if r["other_eid"] != "all"]
    eth_c = [c for c in chains if c["chain_key"] == "ethereal"][0]
    check("Ethereal's USDe is what the adapter's peer there received less what it sent, by chain and in all",
          int(eth_flows["received_raw"]) - int(eth_flows["sent_raw"]) == int(eth_c["supply_raw"])
          and sum(int(r["received_raw"]) for r in by_other) == int(eth_flows["received_raw"])
          and sum(int(r["sent_raw"]) for r in by_other) == int(eth_flows["sent_raw"]),
          "%s received, %s sent, %d and %d records" % (usd(int(eth_flows["received_raw"])), usd(int(eth_flows["sent_raw"])), int(eth_flows["received_count"]), int(eth_flows["sent_count"])))

    # Second sources.
    same = []
    for c in chains:
        if c["source2_supply_raw"] != "" and c["supply_raw"] != "":
            if int(c["source2_supply_raw"]) != int(c["supply_raw"]):
                same.append("DIFF " + c["chain_key"])
            else:
                same.append(c["chain_key"])
    conf_same = []
    conf_later = []
    for r in confirm:
        if r["supply_raw"] == "":
            continue
        c = [x for x in chains if x["chain_key"] == r["chain_key"]][0]
        if r["read_at"] == r["block_requested"]:
            conf_same.append((r["chain_key"], int(r["supply_raw"]) == int(c["supply_raw"])))
        else:
            conf_later.append((r["chain_key"], r["rpc"], int(r["read_at"]), int(r["supply_raw"]) - int(c["supply_raw"])))
    two = sorted(set([x for x in same if not x.startswith("DIFF")] + [k for k, ok in conf_same if ok]))
    check("every second read made with the first gave the same supply, at the same block or ledger version except on Solana, three slots later, and TON, less than a second later",
          not [x for x in same if x.startswith("DIFF")] and all(ok for k, ok in conf_same), "%d chains, %s" % (len(two), ", ".join(two)))
    later_diff = [(k, u, b, d) for k, u, b, d in conf_later if d != 0]
    later_same = sorted(set(k for k, u, b, d in conf_later if d == 0))
    check("the later second reads equal the first except Avalanche's, which rose after the first read",
          [k for k, u, b, d in later_diff] in (["avalanche", "avalanche"], ["avalanche"]) and all(d == 29478684469 * SD_TO_WEI for k, u, b, d in later_diff),
          "same at a later block: %s" % ", ".join(later_same))

    # Peers on the other chains.
    bad = []
    for c in chains:
        if c["method"].startswith("evm") and int(c["connected_at_read"]) == 1:
            if c["chain_side_peer_for_ethereum"].lower() != "0x" + ADAPTER[2:].rjust(64, "0"):
                bad.append(c["chain_key"])
    check("every connected EVM chain's contract names the adapter as its peer for Ethereum", not bad, ", ".join(bad))
    errors = [r for r in matrix if r["peer"] == "error"]
    arb_err = [r for r in errors if r["chain_key"] == "arbitrum"]
    check("the peer reads on the other chains failed only on Arbitrum, read again on a second RPC", len(errors) == len(arb_err) == 36 and all(not r["peer"].startswith("error") for r in arb_peers))
    peers_of = {}
    for r in matrix:
        if r["chain_key"] == "arbitrum":
            continue
        if r["peer"] != "error" and not is_zero32(r["peer"]):
            peers_of.setdefault(r["chain_key"], []).append(int(r["eid_read"]))
    for r in arb_peers:
        if not is_zero32(r["peer"]):
            peers_of.setdefault("arbitrum", []).append(int(r["eid_read"]))
    # Peers were read only for Ethereum and the other 35 chains. Every one named must be the adapter, for Ethereum, or
    # the contract the adapter last named for that chain.
    current = {}
    for h in history:
        if not is_zero32(h["peer"]):
            current[int(h["eid"])] = h["peer"].lower()
    named = [(r["chain_key"], int(r["eid_read"]), r["peer"].lower()) for r in matrix
             if r["chain_key"] != "arbitrum" and r["peer"] != "error" and not is_zero32(r["peer"])]
    named += [("arbitrum", int(r["eid_read"]), r["peer"].lower()) for r in arb_peers if not is_zero32(r["peer"])]
    adapter32 = "0x" + ADAPTER[2:].lower().rjust(64, "0")
    wrong = [x for x in named if x[2] != (adapter32 if x[1] == ETH_EID else current.get(x[1]))]
    direct = sorted(set((k, by_eid[e]["chain_key"]) for k, e, p in named if e != ETH_EID))
    eth_direct = sorted(b for a, b in direct if a == "ethereal")
    check("every peer the contracts on the EVM chains and Tron named for Ethereum or the other 35 chains was the adapter or the contract the adapter last named for that chain",
          not wrong and len(eth_direct) == 7 and ("plasma", "tron") in direct and ("tron", "plasma") in direct,
          "%d peers named, Ethereal's contract names %d other chains: %s" % (len(named), len(eth_direct), ", ".join(eth_direct)))
    dis_evm = [c for c in chains if c["method"].startswith("evm") and int(c["connected_at_read"]) == 0 and c["supply_raw"] != ""]
    no_peers = sorted(c["chain_key"] for c in dis_evm if not peers_of.get(c["chain_key"]))
    with_peers = sorted(c["chain_key"] for c in dis_evm if peers_of.get(c["chain_key"]))
    check("on the dropped EVM chains read, only Metis's contract still names a peer, the adapter",
          with_peers == ["metis"] and peers_of["metis"] == [ETH_EID], "no peers on " + ", ".join(no_peers))
    swell = [c for c in chains if c["chain_key"] == "swell"][0]
    swell_age_h = (parse_utc(eth["time_utc"]) - parse_utc(swell["read_time_utc"])).total_seconds() / 3600
    check("Swellchain's only answering RPC served a block about 12 hours old", 11.5 < swell_age_h < 12.5, "block time %s" % swell["read_time_utc"])

    # ---- reconciliation ----------------------------------------------------------------------------
    log("")
    log("Reconciliation")
    wei_of = {e: raw_v * 10 ** (18 - d) for e, (raw_v, d) in supply.items()}
    S = sum(wei_of.values())
    D = A - S
    # Messages: recompute whether each side is in the reads, from each chain's read block, slot or time.
    read_at = {ETH_EID: ("block", eth["block"], parse_utc(eth["time_utc"]))}
    for c in chains:
        e = int(c["eid"])
        if c["chain_key"] == "stellar":
            read_at[e] = ("time", None, parse_utc(run["stellar_read"]["read_utc"]))
        elif c["read_at"] != "":
            kind = "block" if c["method"].startswith("evm") or c["method"] == "solana" else "time"
            read_at[e] = (kind, int(c["read_at"]), parse_utc(c["read_time_utc"]))

    def included(eid, blk, t):
        if eid not in read_at or blk == "":
            return 0
        kind, b, rt = read_at[eid]
        if kind == "block":
            return 1 if int(blk) <= b else 0
        return 1 if parse_utc(t) <= rt else 0

    inflight = 0
    flight_rows = []
    differ_from_browser = []
    for m in messages:
        s_in = included(int(m["src_eid"]), m["src_block"], m["src_time_utc"])
        d_in = included(int(m["dst_eid"]), m["dst_block"], m["dst_time_utc"]) if m["dst_block"] else 0
        if (s_in, d_in) != (int(m["src_in_read"]), int(m["dst_in_read"])):
            differ_from_browser.append((m["src_eid"], m["dst_eid"], m["nonce"]))
        amt = int(m["amount_sd"]) * SD_TO_WEI
        if s_in != d_in:
            inflight += amt * (s_in - d_in)
            flight_rows.append([m["src_eid"], m["dst_eid"], m["nonce"], m["src_time_utc"], m["dst_status"], fmt_units(int(m["amount_sd"]), 6), s_in, d_in])
    stellar_msgs = [(m["src_eid"], m["dst_eid"], m["nonce"]) for m in messages if "30600" in (m["src_eid"], m["dst_eid"])]
    check("recomputed from the read blocks and times, the messages' flags match the browser's except those of Stellar, which the browser read separately",
          sorted(differ_from_browser) == sorted(x for x in differ_from_browser if x in stellar_msgs) and len(differ_from_browser) == 2,
          "%d messages, %d recomputed" % (len(messages), len(differ_from_browser)))
    check("the only message left between chains at the reads is one of 0.9995 USDe from Ethereum to Stellar that failed on arrival",
          len(flight_rows) == 1 and flight_rows[0][:2] == ["30101", "30600"] and flight_rows[0][4] == "SIMULATION_REVERTED" and inflight == 999500 * SD_TO_WEI)
    R = D - inflight
    log("  Sum of %d chains %s, adapter %s, difference %s, in transit %s, unexplained %s" % (len(supply), usd(S, 6), usd(A, 6), fmt_units(D, 18), usd(inflight, 6), fmt_units(R, 18)))
    check("the chains' USDe adds up to the adapter's balance within 100 USDe, less than 0.000005% of it",
          0 <= R < 100 * WEI and R * 100 * 10 ** 6 < 5 * A, "%s USDe unexplained, %s%% of the adapter's balance" % (fmt_units(R, 18), pct(R, A, 7)))
    dusty = [k for k in by_eid if k in wei_of and wei_of[k] % SD_TO_WEI]
    check("every chain's supply is a whole number of millionths of a USDe except Solana's",
          [by_eid[e]["chain_key"] for e in dusty] == ["solana"], "Solana's remainder %s USDe" % fmt_units(wei_of[dusty[0]] % SD_TO_WEI, 18))
    check("the adapter's balance has a remainder below a millionth of a USDe, which only a transfer to it made outside the bridge can leave",
          A % SD_TO_WEI == 471165449406, fmt_units(A % SD_TO_WEI, 18))

    # Custodian.
    psm = {int(c["eid"]): int(c["psm_custodian_raw"]) for c in chains if c["psm_custodian_raw"] not in ("",)}
    held = {by_eid[e]["chain_key"]: v for e, v in psm.items() if v}
    psm_evm = [e for e in psm if by_eid[e]["chain_key"] != "tron"]
    check("Ethena's PSM custodian held USDe only on Avalanche among the %d EVM chains and Tron where its balance was read, and 0.558392 USDe on Ethereum" % len(psm_evm),
          list(held) == ["avalanche"] and psm_eth == 558392 * SD_TO_WEI and len(psm_evm) == 28 and len(psm) == 29,
          "Avalanche %s USDe, not read on %s" % (usd(held["avalanche"], 6), ", ".join(sorted(NAMES[c["chain_key"]] for c in chains if c["psm_custodian_raw"] == ""))))

    # ---- tables ------------------------------------------------------------------------------------
    rows = []
    for c in chains:
        e = int(c["eid"])
        w = wei_of.get(e)
        p = psm.get(e)
        rows.append({
            "eid": e, "key": c["chain_key"], "name": NAMES[c["chain_key"]], "connected": int(c["connected_at_read"]),
            "first": (first[e]["time_utc"][:10] if e in first else ""), "removed": ("" if e in connected else last[e]["time_utc"][:10]),
            "wei": w, "psm": p, "read_at": c["read_at"] if c["chain_key"] != "stellar" else "", "read_time": c["read_time_utc"] if c["chain_key"] != "stellar" else run["stellar_read"]["read_utc"],
            "method": c["method"], "decimals": c["decimals"] if c["decimals"] else (str(stellar["decimals"]) if c["chain_key"] == "stellar" else ""),
        })
    rows.sort(key=lambda r: (-(r["wei"] or -1), r["name"]))
    read_rows = [r for r in rows if r["wei"] is not None]
    top5 = read_rows[:5]
    top5_sum = sum(r["wei"] for r in top5)
    log("  Largest: " + ", ".join("%s %s" % (r["name"], usd(r["wei"], 0)) for r in top5) + " | %s%% of the adapter" % pct(top5_sum, A))
    check("five chains hold more than 85% of the adapter's USDe",
          [r["key"] for r in top5] == ["plasma", "solana", "base", "robinhood", "ton"] and top5_sum * 100 > 85 * A, pct(top5_sum, A) + "%")

    # Dropped chains.
    dropped = [r for r in rows if not r["connected"]]
    sept = [r for r in dropped if r["removed"] in ("2026-09-24", "2026-09-30")]
    sept_sum = sum(r["wei"] for r in sept)
    dropped_read = [r for r in dropped if r["wei"] is not None]
    dropped_sum = sum(r["wei"] for r in dropped_read)
    check("seven chains were dropped on September 24 and 30, 2026, holding %s USDe at the reads" % usd(sept_sum, 2), len(sept) == 7)

    # Ethena's list.
    docs_keys = set(DOCS_LIST.values())
    conn_keys = set(by_eid[e]["chain_key"] for e in connected)
    listed_not_conn = sorted(NAMES[k] for k in docs_keys - conn_keys)
    conn_not_listed = sorted(NAMES[k] for k in conn_keys - docs_keys)
    check("Ethena's list of 22 chains includes %d the adapter no longer accepted and leaves out %d it did" % (len(listed_not_conn), len(conn_not_listed)),
          len(DOCS_LIST) == 22 and len(listed_not_conn) == 8 and len(conn_not_listed) == 11)

    # DefiLlama.
    cur = llama["currentChainBalances"]
    comp = []
    for r in rows:
        name = LLAMA.get(r["key"])
        ours_circ = None if r["wei"] is None else r["wei"] - (r["psm"] or 0)
        theirs = cur.get(name, {}).get("peggedUSD") if name else None
        if theirs is None:
            comp.append([r["name"], usd(ours_circ, 6) if ours_circ is not None else "", "", "", "not listed by DefiLlama"])
            continue
        theirs_micro = int(round(float(theirs) * 10 ** 6))
        ours_micro = (ours_circ + SD_TO_WEI // 2) // SD_TO_WEI if ours_circ is not None else None
        diff_micro = ours_micro - theirs_micro if ours_micro is not None else None
        same = diff_micro is not None and abs(diff_micro) <= 1
        comp.append([r["name"], usd(ours_circ, 6) if ours_circ is not None else "", repr(theirs), fmt_units(diff_micro, 6) if diff_micro is not None else "", "equal to the millionth" if same else "different"])
    eq = [x[0] for x in comp if x[4] == "equal to the millionth"]
    diff = [x[0] for x in comp if x[4] == "different"]
    missing = [x[0] for x in comp if x[4] == "not listed by DefiLlama"]
    extra = sorted(k for k in cur if k not in LLAMA.values() and k != "Ethereum")
    eth_llama = cur["Ethereum"]["peggedUSD"]
    check("DefiLlama's figures match the reads to the millionth on %d chains, net of the custodian's USDe" % len(eq), len(eq) >= 20, ", ".join(eq))
    log("  DefiLlama differs on %s, leaves out %s and adds %s" % (", ".join(diff), ", ".join(missing), ", ".join(extra)))

    # Peer timeline.
    timeline = []
    prev = {}
    added_by_year = {}
    for h in history:
        e = int(h["eid"])
        if is_zero32(h["peer"]):
            action = "removed"
        elif e not in prev:
            action = "set"
            added_by_year[h["time_utc"][:4]] = added_by_year.get(h["time_utc"][:4], 0) + 1
        elif is_zero32(prev[e]):
            action = "set again"
        else:
            action = "changed"
        prev[e] = h["peer"]
        timeline.append([h["time_utc"][:10], h["block"], e, NAMES.get(h["chain_key"], h["chain_key"]), action])

    # ---- stop on failure ---------------------------------------------------------------------------
    failed = [c for c in CHECKS if not c[1]]
    log("")
    log("%d checks, %d failed" % (len(CHECKS), len(failed)))
    if failed:
        with open(os.path.join(OUT, "run_log_failed.txt"), "w") as f:
            f.write("\n".join(LOG) + "\n")
        sys.exit(1)

    # ---- outputs -----------------------------------------------------------------------------------
    write_csv(os.path.join(OUT, "chains_table.csv"),
              ["eid", "chain", "status_at_read", "first_peer_utc_day", "removed_utc_day", "usde", "share_of_adapter_pct", "psm_custodian_usde", "usde_outside_custodian", "read_at", "read_time_utc", "how_read"],
              [[r["eid"], r["name"], "connected" if r["connected"] else "dropped", r["first"], r["removed"],
                usd(r["wei"], 6) if r["wei"] is not None else "not read", pct(r["wei"], A, 4) if r["wei"] is not None else "",
                usd(r["psm"], 6) if r["psm"] is not None else "not read",
                usd(r["wei"] - r["psm"], 6) if r["wei"] is not None and r["psm"] is not None else ("not read" if r["wei"] is not None else ""), r["read_at"], r["read_time"], r["method"]] for r in rows])
    write_csv(os.path.join(OUT, "reconciliation.csv"), ["line", "usde_exact", "usde"],
              [["USDe supply on Ethereum", fmt_units(T, 18), usd(T)],
               ["held by the adapter", fmt_units(A, 18), usd(A)],
               ["on Ethereum outside the adapter", fmt_units(T - A, 18), usd(T - A)],
               ["on the %d chains read" % len(supply), fmt_units(S, 18), usd(S)],
               ["adapter less the chains", fmt_units(D, 18), usd(D)],
               ["in transit at the reads", fmt_units(inflight, 18), usd(inflight, 4)],
               ["unexplained", fmt_units(R, 18), usd(R)]])
    write_csv(os.path.join(OUT, "in_transit.csv"), ["src_eid", "dst_eid", "nonce", "src_time_utc", "dst_status", "usde", "src_in_reads", "dst_in_reads"], flight_rows)
    write_csv(os.path.join(OUT, "dropped_chains.csv"), ["chain", "removed_utc_day", "usde", "read_time_utc", "peers_named_by_its_contract"],
              [[r["name"], r["removed"], usd(r["wei"], 6) if r["wei"] is not None else "not read", r["read_time"],
                ("not read" if r["wei"] is None or not r["method"].startswith("evm") else (", ".join("Ethereum" if e == ETH_EID else NAMES[by_eid[e]["chain_key"]] for e in peers_of.get(r["key"], [])) or "none"))]
               for r in sorted(dropped, key=lambda x: (x["removed"], x["name"]))])
    write_csv(os.path.join(OUT, "defillama_comparison.csv"), ["chain", "reads_less_custodian_usde", "defillama_peggedUSD", "difference_usde", "result"], comp)
    write_csv(os.path.join(OUT, "peer_timeline.csv"), ["utc_day", "block", "eid", "chain", "action"], timeline)
    chart = [[r["name"], usd(r["wei"], 6), pct(r["wei"], A, 4)] for r in read_rows[:10]]
    rest = read_rows[10:]
    chart.append(["%d other chains" % len(rest), usd(sum(r["wei"] for r in rest), 6), pct(sum(r["wei"] for r in rest), A, 4)])
    write_csv(os.path.join(OUT, "chart_data.csv"), ["chain", "usde", "share_of_adapter_pct"], chart)

    results = {
        "ethereum_block": eth["block"], "ethereum_time_utc": eth["time_utc"],
        "snapshot_started_utc": eth["snapshot_started_utc"], "snapshot_finished_utc": eth["snapshot_finished_utc"],
        "usde_supply": fmt_units(T, 18), "adapter_balance": fmt_units(A, 18), "adapter_share_pct": pct(A, T),
        "ethereum_outside_adapter": fmt_units(T - A, 18), "chains_sum": fmt_units(S, 18), "difference": fmt_units(D, 18),
        "in_transit": fmt_units(inflight, 18), "unexplained": fmt_units(R, 18), "unexplained_pct_of_adapter": pct(R, A, 7),
        "chains_in_history": len(union), "chains_connected": len(connected), "chains_dropped": len(removed), "chains_read": len(supply),
        "top5": [[r["name"], usd(r["wei"], 6), pct(r["wei"], A)] for r in top5], "top5_share_pct": pct(top5_sum, A),
        "dropped_sept": [[r["name"], r["removed"], usd(r["wei"], 6)] for r in sept], "dropped_sept_sum": usd(sept_sum, 6),
        "dropped_read_sum": usd(dropped_sum, 6), "swell": usd(wei_of[int(swell["eid"])], 6), "swell_block_time": swell["read_time_utc"],
        "psm_avalanche": usd(held["avalanche"], 6), "psm_ethereum": usd(psm_eth, 6),
        "adapter_dust": fmt_units(A % SD_TO_WEI, 18), "solana_dust": fmt_units(wei_of[dusty[0]] % SD_TO_WEI, 18),
        "ethereal": {"usde": usd(wei_of[int(eth_c["eid"])], 6), "received": usd(int(eth_flows["received_raw"]), 6), "sent": usd(int(eth_flows["sent_raw"]), 6),
                     "received_count": int(eth_flows["received_count"]), "sent_count": int(eth_flows["sent_count"])},
        "docs_listed_not_connected": listed_not_conn, "docs_missing_connected": conn_not_listed,
        "defillama_equal": eq, "defillama_different": diff, "defillama_missing": missing, "defillama_extra": extra,
        "defillama_ethereum": repr(eth_llama), "two_source_chains": two,
        "messages": {"window_start": window["start"], "window_end": window["end"], "usde_messages": len(messages)},
        "added_by_year": added_by_year,
        "inputs_sha256": {m["path"]: m["sha256"] for m in manifest},
    }
    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump(results, f, indent=1)
        f.write("\n")
    with open(os.path.join(OUT, "run_log.txt"), "w") as f:
        f.write("\n".join(LOG) + "\n")
    failed_path = os.path.join(OUT, "run_log_failed.txt")
    if os.path.exists(failed_path):
        os.remove(failed_path)


if __name__ == "__main__":
    main()
