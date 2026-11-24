# EthenaPay Earn+ integration research

Verified November 13, 2026. The dashboard implementation uses `fetch_earnplus.py` and `scripts/earnplus_rpc.py` to publish `docs/earnplus.json`. It maintains UTC day-end history in `output/earnplus-history.json` and refreshes independently of Dune in the scheduled data workflow.

## Identified contracts

All addresses are Avalanche C-Chain, chain ID 43114.

| Role | Address |
| --- | --- |
| Earn+ vault proxy | `0x6AaB14C53980B9aA1Ce632a7e46a6E5E62e60f55` |
| Receipt token, Ethena USD+ Avalanche, pUSDe | `0xcb5c7b865da0867769c1263dc80088d93fd3fb79` |
| Underlying USDe, 18 decimals | `0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34` |
| Implementation verified during research | `0x9477b3d072ee952690e52751e6ac1217d0c2882a` |

Primary attribution: https://www.upshift.finance/blog/what-is-ethena-pay-earn-plus

Product explanation: https://pay.ethena.fi/blog/earn-launch

Verified implementation source and ABI: Routescan Avalanche Etherscan-compatible API, `contract/getsourcecode` and `contract/getabi`. The proxy uses EIP-1967 implementation storage.

## Correct balance calculation

This is not a standard ERC-4626 `totalAssets()` vault. Use:

1. `getTotalAssets()` for vault-reported NAV after collectable fees.
2. `globalLiabilityShares()` for shares queued for withdrawal.
3. `previewRedemption(queuedShares, false)` for the queued shares' gross asset value and net payout after withdrawal fees.
4. Active Earn+ balance = vault-reported NAV minus the **gross** queued asset value.

The receipt token shares remain in total supply while queued. Its `balanceOf(vault)` matched `globalLiabilityShares()` at the observed current block. Simply multiplying total supply by share price includes queued withdrawals. Simply reading USDe `balanceOf(vault)` misses deployed strategy capital.

This is whole-vault accounting, not a factory-wallet-only ownership calculation. Seed/admin holdings, external holders or changes to eligibility can affect comparisons. For an exact EthenaPay-wallet ownership metric, join receipt-token holder balances to the existing factory wallet set and account separately for queued shares.

`externalAssets` is updated by the owner/operator. This is a verifiable onchain reading of a **reported valuation**, not an independent real-time mark of every strategy position. Publish `assetsUpdatedOn()` beside the observation timestamp and flag aged accounting. Never silently label it live strategy NAV.

## Reconciliation

November 12 UTC day-end, block 100155043:

| Measure | USDe |
| --- | ---: |
| Reported vault NAV | 8,782,014.913891786660705568 |
| Gross queued withdrawals | 133,386.984530596180941015 |
| Active Earn+ balance | 8,648,627.929361190479764553 |
| Paymentscan displayed Earn+ deposits | 8,648,627.42 |

Reported NAV matches Paymentscan's `nav_usde` at displayed precision. Active Earn+ balance is within 0.51 USDe of its `ethena_pay_earn_usde` figure. The residual is not explained by this research and should not be claimed as an exact match. Paymentscan data was obtained from the public `card-analytics-data["ethena"]` hydration on https://paymentscan.xyz/cards/ethena-pay, field `ethenaEarnLeverage`.

Current observation in saved evidence, November 13 at 21:07:16 UTC:

- Reported NAV: 9,000,137.993900835435025370 USDe.
- Gross queued withdrawals: approximately 124,974.99 USDe.
- Active Earn+ balance: approximately 8,875,163.01 USDe.
- External valuation updated November 13 at 09:05:54 UTC, approximately 12 hours before observation.

See raw fixed-block reads and `verified-day-end.json` for exact reproducible values.

## Dashboard integration

- Add **Earn+ balance** beside the existing **Liquid USDe balance** card. Describe it as active vault balance including accrued returns, excluding queued withdrawals. Do not imply cumulative deposited principal.
- Add a separate **Pending Earn+ withdrawals** value so assets remain visible while moving back to liquid wallets. A total tracked-assets metric may include liquid balance + active Earn+ + pending gross value only after ownership scope and timestamps reconcile.
- Add a liquid/Earn+/pending balance chart with UTC day-end reads. Backfill the vault at each historical day's final block, then retain daily snapshots. Do not reconstruct NAV solely by cumulating deposits minus withdrawals, because returns and fees change share value.
- Add **Gross USDe exposure**, **USDT debt**, **Leverage** and **Health factor** only after identifying and reading current strategy accounts and Aave positions. Never estimate actual exposure by multiplying deposits by the launch target of 11x.
- Paymentscan's November 12 gross USDe supplied was 92,108,857.44 and debt 83,791,550.35. These are comparison-provider figures, not independently reproduced here. Its attributed `ethena_pay_aave_usde` was 90,709,842.57, distinct from full-strategy gross supply.
- Transfers from a liquid wallet into Earn+ are internal allocations, not spending or external customer withdrawals. Existing liquid-wallet flow categories need a separate Earn+ transfer bucket and a reconciliation check.
- Keep Earn+ in a separate feed, so an RPC error cannot break card-spend data. Retain the last successful observation with an aged-data label, never substitute zero. The collector requires no API key or Dune credits.

## Event accounting for later flows and wallet counts

Use verified ABI events and count log entries, not transaction hashes:

- `Deposit(address,uint256,uint256,address,address)`: asset, amount and shares are in data; sender and receiver are indexed. Verify the asset and use receiver for share ownership. Separate production cohort activity from pre-launch test/seed events.
- `WithdrawalRequested(uint256,address,address)`: request only, not settled cash outflow.
- `WithdrawalProcessed(uint256,address)`: settled queued withdrawal.
- `Withdraw(address,address,address,uint256,uint256)`: immediate redemption.

The reviewed implementation emits `WithdrawalProcessed` for queued settlement and `Withdraw` for immediate redemption. Do not count the request and settlement as two withdrawals. Depositor addresses are wallets, not verified people. Holder transfers also affect current-holder balances.

## Run

```sh
python3 research/ethenapay-earn-plus/fetch_snapshot.py --block 100155043
python3 research/ethenapay-earn-plus/fetch_snapshot.py --output /tmp/earn-plus-current.json
```

The standard-library collector pins every accounting read to one block, checks chain/asset/share token/implementation, preserves exact decimal strings, and fails closed if the implementation changes. Historical reads require an archive-capable RPC; the public Avalanche endpoint worked for the verified day-end block.


## Exposure chart added November 24, 2026

The same fixed-block collector now reads the enabled strategy account `0xe08af7283607f7884012c79fc585763eae5de506` on the Aave Ethena Ecosystem Spoke `0xaf22446124e566e54845f65b722e4dcbf12b650a`. The vault's `SubAccountEnabled` event identifies this account, and `whitelistedSubAccounts(account) == 2` is checked at every observation. The retired account `0x9f75c5b1da75ba108110a56023d0b367113af62b` was disabled before this chart's October 25 start.

The reviewed Spoke implementation is `0x87d4385e72e668c2fc5bae9120069ff8312f7373`. Reserve 0 is verified as Avalanche USDe with 18 decimals. `getUserSuppliedAssets(0, strategy)` supplies the gross position. No 11x target multiplier is used.

- Active attributed exposure = supplied USDe * active Earn+ balance / reported vault NAV.
- Exposure multiple = supplied USDe / reported vault NAV, equal to attributed exposure / active balance when the latter is positive.
- Both series are overlaid from zero, never stacked or summed as customer funds.
- Exposure is denominated in USDe. It is not the net vault balance or independently marked USD.
- On October 25 the Spoke had no listed reserves (`getReserveCount() == 0`), so gross exposure is a verified zero. A reverted/unknown reserve read is not interpreted as zero.
- Missing exposure is stored as null. Valid vault accounting continues to publish if strategy reads fail or the reviewed implementation/account mapping changes. The chart leaves missing exposure as a gap and shows an unavailable label.

The 30 completed daily positions through November 23 were independently read at the same block as each cached balance. All gross supplied figures matched Paymentscan's published `aave_usde_supplied` to the displayed cent. Maximum attributed-exposure difference was 5.36 USDe, consistent with the small previously observed balance-scope difference, but its cause remains unverified. See `exposure-reconciliation.json`. Paymentscan is a comparison source, not the production feed.

Primary references: [Aave proposal 532](https://app.aave.com/governance/v3/proposal/?proposalId=532), the Spoke's verified Routescan ABI, and [Aave ISpoke interface](https://github.com/aave/aave-v4/blob/main/src/spoke/interfaces/ISpoke.sol).
