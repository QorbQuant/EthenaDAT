// USDEB contract published in Binance's October 7, 2026 listing announcement.
export const TOKEN = "0xdfd3ba51d4591f243481a6f26059d1a5ee95252f";
const RPC = "https://bsc-dataseed.bnbchain.org";
const HEX = /^0x[0-9a-f]+$/i;
function uint(value) {
  if (typeof value !== "string" || !HEX.test(value))
    throw Error("Invalid chain result");
  return BigInt(value);
}
function word(value) {
  if (typeof value !== "string" || !/^0x[0-9a-f]{64}$/i.test(value))
    throw Error("Invalid contract result");
  return uint(value);
}
function symbol(value) {
  if (typeof value !== "string" || !/^0x[0-9a-f]{192}$/i.test(value))
    return null;
  if (
    BigInt("0x" + value.slice(2, 66)) !== 32n ||
    BigInt("0x" + value.slice(66, 130)) !== 5n
  )
    return null;
  return value.slice(130, 140).toLowerCase() === "5553444542" ? "USDEB" : null;
}
export function normalizeTokenized(block, values, now = Date.now()) {
  if (symbol(values.symbol) !== "USDEB" || word(values.decimals) !== 18n)
    throw Error("Unexpected token identity");
  const raw = word(values.supply),
    multiplier = word(values.multiplier),
    ui = word(values.uiSupply);
  if (multiplier <= 0n || (raw * multiplier) / 10n ** 18n !== ui)
    throw Error("Inconsistent scaled supply");
  const blockNumber = Number(uint(block.number)),
    timestamp = Number(uint(block.timestamp)) * 1000;
  if (
    !Number.isSafeInteger(blockNumber) ||
    !Number.isSafeInteger(timestamp) ||
    timestamp > now + 30000 ||
    now - timestamp > 300000
  )
    throw Error("Stale chain block");
  const supply = Number(ui) / 1e18;
  if (!Number.isFinite(supply) || supply < 0) throw Error("Invalid supply");
  return {
    symbol: "USDEB",
    chainId: 56,
    contract: TOKEN,
    blockNumber,
    observedAt: new Date(timestamp).toISOString(),
    fetchedAt: new Date(now).toISOString(),
    rawSupply: raw.toString(),
    decimals: 18,
    multiplier: multiplier.toString(),
    supply,
  };
}
export async function tokenizedResponse(
  ctx,
  fetcher = fetch,
  cache = globalThis.caches?.default,
  now = Date.now(),
) {
  const key = new Request("https://ethenadash.com/__feed/usdeb-supply-v1");
  let previous;
  try {
    const stored = await (await cache?.match(key))?.json();
    if (
      stored?.symbol === "USDEB" &&
      stored.contract === TOKEN &&
      Number.isFinite(stored.supply) &&
      stored.supply >= 0 &&
      Number.isFinite(Date.parse(stored.observedAt)) &&
      Date.parse(stored.observedAt) <= now + 30000
    )
      previous = stored;
  } catch {}
  const respond = (data, stale = false) =>
    Response.json(
      { ...data, stale },
      {
        headers: {
          "Cache-Control": stale ? "no-store" : "public, max-age=60",
          "X-Content-Type-Options": "nosniff",
        },
      },
    );
  if (previous && now - Date.parse(previous.observedAt) < 120000)
    return respond(previous);
  const rpc = async (calls) => {
    const r = await fetcher(RPC, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: AbortSignal.timeout(5000),
      body: JSON.stringify(
        calls.map(([method, params], id) => ({
          jsonrpc: "2.0",
          id,
          method,
          params,
        })),
      ),
    });
    if (!r.ok) throw Error("Chain data unavailable");
    const rows = await r.json();
    if (!Array.isArray(rows) || rows.length !== calls.length)
      throw Error("Incomplete RPC batch");
    return calls.map((_, id) => {
      const matches = rows.filter((r) => r?.id === id);
      if (matches.length !== 1 || matches[0].error || matches[0].result == null)
        throw Error("Failed RPC call");
      return matches[0].result;
    });
  };
  try {
    const [chain, block] = await rpc([
      ["eth_chainId", []],
      ["eth_getBlockByNumber", ["latest", false]],
    ]);
    if (uint(chain) !== 56n) throw Error("Unexpected chain");
    uint(block.number);
    const fields = {
      symbol: "0x95d89b41",
      decimals: "0x313ce567",
      supply: "0x18160ddd",
      multiplier: "0xa60bf13d",
      uiSupply: "0x9bea6429",
    };
    const results = await rpc(
      Object.values(fields).map((data) => [
        "eth_call",
        [{ to: TOKEN, data }, block.number],
      ]),
    );
    const data = normalizeTokenized(
      block,
      Object.fromEntries(
        Object.keys(fields).map((key, i) => [key, results[i]]),
      ),
      now,
    );
    if (cache)
      ctx.waitUntil(
        cache.put(
          key,
          Response.json(data, {
            headers: { "Cache-Control": "public, max-age=21600" },
          }),
        ),
      );
    return respond(data);
  } catch {
    if (previous && now - Date.parse(previous.observedAt) <= 6 * 3600000)
      return respond(previous, true);
    return Response.json(
      { error: "USDEB chain data is temporarily unavailable" },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }
}
