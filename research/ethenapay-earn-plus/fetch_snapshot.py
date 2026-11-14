"""Read Earn+ vault accounting at one pinned Avalanche block, without an API key.

Usage: python3 fetch_snapshot.py [--block 100155043] [--output snapshot.json]
Amounts are USDe, not independently marked USD. No transactions are submitted.
"""
import argparse
import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.request import Request, urlopen

VAULT = "0x6aab14c53980b9aa1ce632a7e46a6e5e62e60f55"
LP = "0xcb5c7b865da0867769c1263dc80088d93fd3fb79"
USDE = "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34"
IMPLEMENTATION = "0x9477b3d072ee952690e52751e6ac1217d0c2882a"
IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"


def collect(block=None, rpc=None):
    rpc = rpc or os.environ.get("AVALANCHE_RPC_URL", "https://api.avax.network/ext/bc/C/rpc")

    def call(method, params):
        payload = json.dumps(dict(jsonrpc="2.0", id=1, method=method, params=params)).encode()
        req = Request(rpc, data=payload, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=30) as response:
            result = json.load(response)
        if "error" in result:
            raise RuntimeError(f"{method} failed: {result['error']}")
        return result["result"]

    if int(call("eth_chainId", []), 16) != 43114:
        raise ValueError("Expected Avalanche C-Chain")
    tag = hex(block) if block is not None else call("eth_blockNumber", [])
    header = call("eth_getBlockByNumber", [tag, False])
    implementation = "0x" + call("eth_getStorageAt", [VAULT, IMPLEMENTATION_SLOT, tag])[-40:]
    if implementation.lower() != IMPLEMENTATION:
        raise ValueError("Vault implementation changed; review accounting before publishing")
    reads = {}

    def read(address, signature, arguments=""):
        selector = call("web3_sha3", ["0x" + signature.encode().hex()])[:10]
        value = call("eth_call", [{"to": address, "data": selector + arguments}, tag])
        reads[address + ":" + signature] = value
        return value

    if "0x" + read(VAULT, "asset()")[-40:] != USDE:
        raise ValueError("Unexpected underlying asset")
    if "0x" + read(VAULT, "lpTokenAddress()")[-40:] != LP:
        raise ValueError("Unexpected share token")
    decimals = int(read(USDE, "decimals()"), 16)
    nav = int(read(VAULT, "getTotalAssets()"), 16)
    liability = int(read(VAULT, "globalLiabilityShares()"), 16)
    queued = read(VAULT, "previewRedemption(uint256,bool)", f"{liability:064x}{0:064x}")
    pending_gross = int(queued[2:66], 16)
    pending_after_fee = int(queued[66:130], 16)
    if not 0 <= pending_after_fee <= pending_gross <= nav:
        raise ValueError("Withdrawal liabilities do not reconcile with NAV")
    updated = int(read(VAULT, "assetsUpdatedOn()"), 16)
    observed = int(header["timestamp"], 16)
    if updated > observed:
        raise ValueError("Accounting timestamp is after observation")

    def amount(value):
        return format(Decimal(value) / (Decimal(10) ** decimals), "f")

    def iso(stamp):
        return datetime.fromtimestamp(stamp, timezone.utc).isoformat()

    return dict(
        chainId=43114, vault=VAULT, shareToken=LP, asset=USDE,
        implementation=implementation, blockNumber=int(tag, 16), blockHash=header["hash"],
        observedAt=iso(observed), accountingUpdatedAt=iso(updated),
        accountingAgeSeconds=observed - updated, units="USDe",
        vaultReportedNavUsde=amount(nav), pendingWithdrawalGrossUsde=amount(pending_gross),
        pendingWithdrawalAfterFeeUsde=amount(pending_after_fee),
        activeEarnBalanceUsde=amount(nav - pending_gross),
        valuationBasis="Vault-reported NAV; external strategy valuation updated by operator",
        scope="Whole vault excluding queued withdrawal shares; not restricted to factory wallets",
        reads=reads,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(collect(args.block), indent=2) + "\n"
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end="")
