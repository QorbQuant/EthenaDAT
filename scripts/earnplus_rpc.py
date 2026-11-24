"""Read Earn+ vault accounting at one pinned Avalanche block, without an API key.

Usage: python3 fetch_snapshot.py [--block 100155043] [--output snapshot.json]
Amounts are USDe, not independently marked USD. No transactions are submitted.
"""
import argparse
import json
import os
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path
from functools import lru_cache
from urllib.request import Request, urlopen

VAULT = "0x6aab14c53980b9aa1ce632a7e46a6e5e62e60f55"
LP = "0xcb5c7b865da0867769c1263dc80088d93fd3fb79"
USDE = "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34"
IMPLEMENTATION = "0x9477b3d072ee952690e52751e6ac1217d0c2882a"
STRATEGY = "0xe08af7283607f7884012c79fc585763eae5de506"
SPOKE = "0xaf22446124e566e54845f65b722e4dcbf12b650a"
SPOKE_IMPLEMENTATION = "0x87d4385e72e668c2fc5bae9120069ff8312f7373"
IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"


@lru_cache(maxsize=64)
def selector(rpc, signature):
    req = Request(rpc, data=json.dumps(dict(jsonrpc="2.0", id=1, method="web3_sha3", params=["0x" + signature.encode().hex()])).encode(), headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=30) as response:
        value = json.load(response)
    if "error" in value:
        raise RuntimeError("Function hashing failed")
    return value["result"][:10]



def exposure_values(gross_raw, nav_raw, active_raw, decimals=18):
    if not 0 <= active_raw <= nav_raw or gross_raw < 0:
        raise ValueError("Invalid exposure allocation inputs")
    if nav_raw == 0 and gross_raw != 0:
        raise ValueError("Cannot attribute exposure against zero NAV")
    with localcontext() as context:
        context.prec = 60
        gross = Decimal(gross_raw) / (Decimal(10) ** decimals)
        allocated = gross * Decimal(active_raw) / Decimal(nav_raw) if nav_raw else Decimal(0)
        multiple = Decimal(gross_raw) / Decimal(nav_raw) if nav_raw else Decimal(0)
        return dict(strategySuppliedUsde=format(gross, "f"),
                    activeExposureUsde=format(allocated, "f"),
                    exposureMultiple=format(multiple, "f"))


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
        data = selector(rpc, signature) + arguments
        value = call("eth_call", [{"to": address, "data": data}, tag])
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

    exposure = None
    try:
        spoke_impl = "0x" + call("eth_getStorageAt", [SPOKE, IMPLEMENTATION_SLOT, tag])[-40:]
        if spoke_impl != SPOKE_IMPLEMENTATION:
            raise ValueError("Unreviewed Aave Spoke implementation")
        if int(read(VAULT, "whitelistedSubAccounts(address)", STRATEGY[2:].rjust(64, "0")), 16) != 2:
            raise ValueError("Reviewed strategy account is no longer enabled")
        reserve_count = int(read(SPOKE, "getReserveCount()"), 16)
        if reserve_count == 0:
            # Before activation the Spoke had no listed reserves, so its
            # supplied USDe is verifiably zero, not a failed observation.
            supplied = 0
        else:
            reserve = read(SPOKE, "getReserve(uint256)", "0" * 64)
            if "0x" + reserve[26:66] != USDE or int(reserve[194:258], 16) != decimals:
                raise ValueError("Unexpected Aave reserve asset or decimals")
            supplied = int(read(SPOKE, "getUserSuppliedAssets(uint256,address)", "0" * 64 + STRATEGY[2:].rjust(64, "0")), 16)
        exposure = dict(strategyAccount=STRATEGY, spoke=SPOKE, reserveId=0, reserveCount=reserve_count,
                        spokeImplementation=spoke_impl, observedAt=iso(observed),
                        **exposure_values(supplied, nav, nav - pending_gross, decimals))
    except Exception:
        # Exposure is optional: an unreviewed strategy change or a failed read
        # must never manufacture zero or discard otherwise valid vault accounting.
        pass

    return dict(
        exposure=exposure,
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
