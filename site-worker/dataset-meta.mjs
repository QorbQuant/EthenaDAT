export const DATASETS = {
  "/data/stablecoinx-valuation/": {
    key: "valuation",
    name: "StablecoinX valuation data",
    description:
      "Recorded USDE stock prices, ENA prices, reported holdings, Class A shares, token NAV per share and mNAV. Download the historical observations.",
    dashboard: "/stablecoinx/",
    guide: "/research/stablecoinx-mnav/",
    definition:
      "mNAV equals the recorded USDE stock price divided by token NAV per Class A share. Token NAV is reported ENA holdings multiplied by the recorded ENA price.",
    limits:
      "Token NAV excludes cash, other assets, debt and liabilities. Class A shares are not fully diluted shares. Holdings are carried forward between disclosures. Stock closes and ENA daily observations use different clocks; this is not the matched-close series used in the tracking review. Quotes may be delayed.",
    sources: [
      ["StablecoinX filings", "https://www.sec.gov/edgar/browse/?CIK=2080215"],
      ["USDE market prices", "https://finance.yahoo.com/quote/USDE/history/"],
      ["ENA prices", "https://www.coingecko.com/en/coins/ethena"],
    ],
  },
  "/data/ethenapay-spending/": {
    key: "spending",
    name: "EthenaPay spending data",
    description:
      "Daily USDe card spending, successful spend events and spending wallets on Avalanche. Dated observations, definitions and downloadable data.",
    dashboard: "/ethenapay/",
    guide: "/research/ethenapay-spend-events/",
    definition:
      "Card spend is the USDe amount in successful AllowanceSpent logs emitted by EthenaPay wallets to either of the two programme settlement addresses. Spending wallets are distinct emitting addresses within each UTC day.",
    limits:
      "Count log events, not transaction hashes or individual purchases. Exclude the settlement-to-issuer transfer to avoid double counting. Wallets are not verified people. Daily wallet counts cannot be added to obtain weekly unique wallets. The snapshot day may be incomplete, even when viewed later.",
    sources: [
      ["EthenaPay", "https://pay.ethena.fi/"],
      ["Dune", "https://dune.com/"],
      [
        "Avalanche USDe contract",
        "https://snowtrace.io/token/0x5d3a1Ff2b6BAb83b63cd9AD0787074081a52ef34",
      ],
    ],
  },
  "/data/usdeb-supply/": {
    key: "supply",
    name: "USDEB supply and net issuance data",
    description:
      "StablecoinX bStock supply, daily mints, burns and net issuance on BNB Chain. Reconciled onchain observations with CSV and JSON downloads.",
    dashboard: "/stablecoinx/#tokenized-panel",
    guide: "/research/usdeb-stablecoinx-bstock/",
    definition:
      "Net issuance is raw USDEB units minted minus raw units burned. From deployment, total mints minus total burns equal raw supply. Displayed supply equals raw supply multiplied by the corporate-action multiplier.",
    limits:
      "Issuance is not dollar inflow, net stock buying or a company equity raise. Conversions can use existing stock holdings. Multiplier changes are separate from mints and burns. Reconciliation verifies token accounting, not custody of the backing shares. First and last UTC days may be partial.",
    sources: [
      [
        "USDEB contract",
        "https://bscscan.com/token/0xdfd3ba51d4591f243481a6f26059d1a5ee95252f",
      ],
      [
        "Binance bStocks guide",
        "https://www.binance.com/en/academy/articles/what-are-bstocks-a-guide-to-tokenized-stocks-on-binance",
      ],
      ["Dune", "https://dune.com/"],
    ],
  },
  "/data/stablecoinx-perpetuals/": {
    key: "perpetuals",
    name: "StablecoinX perpetual market data",
    description:
      "Lighter StablecoinX mark price, open interest, traded volume and settled hourly funding. Timestamped snapshots and recent hourly observations.",
    dashboard: "/stablecoinx/#lighter-panel",
    guide: "/research/stablecoinx-perp-lighter-2026-10-08/",
    definition:
      "Lighter market 229 is the STABLECOINX perpetual. Open interest in dollars equals outstanding contracts times mark price. Funding is the settled hourly rate in percentage points; positive means longs pay shorts.",
    limits:
      "Mark price, last trade and the stock close are different observations. This perpetual does not create company shares. Funding is not an annualized yield or a directional forecast. Trade prices and funding history can update independently; missing values are unavailable, not zero. Recent history is a rolling window, not a complete archive.",
    sources: [
      [
        "Lighter STABLECOINX market",
        "https://app.lighter.xyz/trade/STABLECOINX",
      ],
      ["Lighter API documentation", "https://apidocs.lighter.xyz/"],
    ],
  },
};
export const DATA_PAGES = Object.fromEntries(
  Object.entries(DATASETS).map(([path, d]) => [
    path,
    { ...d, title: d.name + " | EthenaDash", dataset: true },
  ]),
);
DATA_PAGES["/data/"] = {
  name: "Data library",
  title: "Ethena & StablecoinX Data Downloads | EthenaDash",
  description:
    "Citable datasets for StablecoinX valuation, EthenaPay spending, USDEB net issuance and Lighter perpetual markets, with dates, definitions and downloads.",
};
