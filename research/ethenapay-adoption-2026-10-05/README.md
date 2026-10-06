# EthenaPay adoption review

Published October 6, 2026. Chain cutoff: October 5, 2026 at 15:53 UTC. Full weeks end October 4; full months end September.

The article distinguishes deployed wallets, wallets receiving USDe and wallets emitting qualifying spend events. Wallets are not verified people and spend events are not transaction hashes or verified retail purchases.

## Reproduce the calculations

Python 3, with no third-party dependencies:

```sh
python3 ethenapay_adoption_review.py
python3 check_article_numbers.py
python3 make_chart_svg.py
```

The first command verifies pinned input hashes and rebuilds the tables and results in `out/`. The second checks 123 numerical claims against those results. The third rebuilds the SVG chart. `chart_preview.png` is the social preview image and is available separately on the article page.

## Reproduce the chain inputs

Node.js 18 or later, with network access to the public Avalanche RPC and Routescan endpoints:

```sh
node test_chain_recount.cjs ./chain_recount.cjs
node chain_recount.cjs
python3 ethenapay_adoption_review.py
python3 check_article_numbers.py
```

The recount reads historical deployments, USDe transfers and AllowanceSpent events. It also checks reconstructed cutoff balances against balanceOf calls for all 14,047 wallets. It makes no transactions. It rebuilds the six aggregate files in `inputs/chain/`; raw address-level logs are not included in this download. Running the network recount is required to reconstruct those aggregates from the chain instead of using the supplied copies.

Before publication, a fresh network recount reproduced all six supplied chain files byte for byte. The article retains the unresolved dashboard and third-party tracker differences; successful reproduction does not resolve those differences.

The article links the original product announcements, dashboard and methodology. Input manifests identify pinned historical snapshots. Weekly, monthly, cohort and concentration tables are in `out/`.

## Chain scope

- Network: Avalanche C-Chain, chain ID 43114.
- Blocks scanned: 85,400,000 through 96,839,679. Article cutoff: 96,815,525.
- USDe (18 decimals): `0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34`.
- Factory v1: `0x313be708df16979d9e5fe9db5ac4969b8add7207`.
- Factory v2: `0xac66ca9a79fb0d3c64cba44cd29610cd58602d6f`.
- Current settlement: `0x6070848bd19c37488d0516058f2933dd992733de`.
- Retired settlement: `0x3b3ffd99b87a2dee5ad244b75d5a8e266890fdb8`.
- Event: `AllowanceSpent(address indexed token, address indexed to, uint256 amount)`. The emitting address identifies the wallet. The filter requires USDe and either settlement destination.

The onward settlement transfer is excluded. Earlier-snapshot balances and daily balances require the network recount to recreate, since this package contains the aggregate results rather than the full raw transfer history.
