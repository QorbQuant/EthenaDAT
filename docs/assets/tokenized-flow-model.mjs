// Raw token units keep corporate-action multiplier changes out of issuance.
export const CONTRACT = "0xdfd3ba51d4591f243481a6f26059d1a5ee95252f";
const DAY = 86400000;
const integer = (v) => typeof v === "string" && /^\d+$/.test(v);
export function validFlows(d, now = Date.now()) {
  try {
    if (
      d?.version !== 1 ||
      d.symbol !== "USDEB" ||
      d.chainId !== 56 ||
      d.contract !== CONTRACT ||
      d.reconciled !== true
    )
      return false;
    const start = Date.parse(d.coverageStart),
      end = Date.parse(d.observedAt),
      generated = Date.parse(d.generatedAt);
    if (
      ![start, end, generated].every(Number.isFinite) ||
      start > end ||
      end > generated ||
      generated > now + 30000
    )
      return false;
    if (
      !Number.isSafeInteger(d.blockNumber) ||
      !/^0x[\da-f]{64}$/i.test(d.blockHash) ||
      !Array.isArray(d.events) ||
      !Array.isArray(d.adjustments)
    )
      return false;
    if (
      ![
        d.rawSupply,
        d.rawMinted,
        d.rawBurned,
        d.multiplier,
        d.adjustedSupply,
      ].every(integer)
    )
      return false;
    let minted = 0n,
      burned = 0n,
      last = -1,
      lastIndex = -1;
    for (const e of d.events) {
      if (
        !Number.isSafeInteger(e.t) ||
        e.t < start ||
        e.t > end ||
        !integer(e.rawAmount) ||
        BigInt(e.rawAmount) <= 0n ||
        !["mint", "burn"].includes(e.kind)
      )
        return false;
      if (
        !Number.isSafeInteger(e.block) ||
        e.block < 124478553 ||
        e.block > d.blockNumber ||
        !Number.isSafeInteger(e.logIndex) ||
        e.logIndex < 0 ||
        !/^0x[\da-f]{64}$/i.test(e.tx)
      )
        return false;
      if (e.block < last || (e.block === last && e.logIndex <= lastIndex))
        return false;
      last = e.block;
      lastIndex = e.logIndex;
      if (e.kind === "mint") minted += BigInt(e.rawAmount);
      else burned += BigInt(e.rawAmount);
      if (burned > minted) return false;
    }
    return (
      minted === BigInt(d.rawMinted) &&
      burned === BigInt(d.rawBurned) &&
      minted - burned === BigInt(d.rawSupply) &&
      BigInt(d.multiplier) > 0n &&
      (BigInt(d.rawSupply) * BigInt(d.multiplier)) / 10n ** 18n ===
        BigInt(d.adjustedSupply)
    );
  } catch {
    return false;
  }
}
export function flowWindow(data, range) {
  const end = Date.parse(data.observedAt),
    origin = Date.parse(data.coverageStart);
  const start =
    range === "all"
      ? origin
      : Math.max(origin, end - (range === "24h" ? DAY : 7 * DAY));
  const bins = new Map();
  for (let t = Math.floor(start / DAY) * DAY; t <= end; t += DAY)
    bins.set(t, { t, minted: 0n, burned: 0n });
  let minted = 0n,
    burned = 0n;
  for (const e of data.events) {
    if ((range === "all" ? e.t < start : e.t <= start) || e.t > end) continue;
    const amount = BigInt(e.rawAmount),
      row = bins.get(Math.floor(e.t / DAY) * DAY);
    if (e.kind === "mint") {
      minted += amount;
      row.minted += amount;
    } else {
      burned += amount;
      row.burned += amount;
    }
  }
  const number = (n) => Number(n) / 1e18;
  return {
    start,
    end,
    minted: number(minted),
    burned: number(burned),
    net: number(minted - burned),
    rows: [...bins.values()].map((r) => ({
      t: r.t,
      minted: number(r.minted),
      burned: number(r.burned),
      net: number(r.minted - r.burned),
      partial: r.t < start || r.t + DAY > end,
    })),
  };
}
