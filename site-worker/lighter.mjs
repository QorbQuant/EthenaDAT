// Public market data only. Kept separate from the equity/NAV data pipeline.
const API = "https://mainnet.zklighter.elliot.ai/api/v1/";
const MARKET = 229;
const HOUR = 3600000;
const number = (v) =>
  (typeof v === "number" || (typeof v === "string" && v.trim() !== "")) &&
  Number.isFinite(Number(v))
    ? Number(v)
    : null;
const nonnegative = (v) =>
  number(v) >= 0 && number(v) !== null ? number(v) : null;

export function normalizeLighter(details, fundings, candles, now = Date.now()) {
  const m = details?.order_book_details?.find(
    (v) =>
      v.market_id === MARKET &&
      v.symbol === "STABLECOINX" &&
      v.market_type === "perp",
  );
  if (
    details?.code !== 200 ||
    !m ||
    m.status !== "active" ||
    !(number(m.mark_price) > 0)
  )
    throw Error("StablecoinX market snapshot unavailable");
  const sorted = (rows) =>
    [...new Map(rows.map((r) => [r.t, r])).values()].sort((a, b) => a.t - b.t);
  const funding = sorted(
    (fundings?.code === 200 && Array.isArray(fundings.fundings)
      ? fundings.fundings
      : []
    ).flatMap((r) => {
      if (!r) return [];
      const t = number(r.timestamp) * 1000,
        rate = nonnegative(r.rate);
      if (
        !t ||
        t > now ||
        t < now - 7 * 24 * HOUR ||
        rate === null ||
        !["long", "short"].includes(r.direction)
      )
        return [];
      // REST rates are percentage points; direction identifies the paying side.
      // Example: rate=0.0004 means 0.0004% per hour, not 0.04%.
      return [{ t, ratePct: rate * (r.direction === "short" ? -1 : 1) }];
    }),
  );
  const prices = sorted(
    (candles?.code === 200 && Array.isArray(candles.c)
      ? candles.c
      : []
    ).flatMap((r) => {
      if (!r) return [];
      const t = number(r.t),
        close = number(r.c);
      return t && t <= now && t >= now - 7 * 24 * HOUR && close > 0
        ? [{ t, close }]
        : [];
    }),
  );
  const markPrice = number(m.mark_price),
    oi = nonnegative(m.open_interest);
  return {
    marketId: MARKET,
    symbol: "STABLECOINX",
    fetchedAt: new Date(now).toISOString(),
    markPrice,
    indexPrice: number(m.index_price),
    lastTradePrice: number(m.last_trade_price),
    // orderBookDetails returns base contracts; market_stats WS returns USD.
    openInterestContracts: oi,
    openInterestUsd: oi === null ? null : oi * markPrice,
    volume24hUsd: nonnegative(m.daily_quote_token_volume),
    funding,
    prices,
    latestFunding: funding.at(-1) || null,
  };
}

export async function lighterResponse(
  ctx,
  fetcher = fetch,
  cache = globalThis.caches?.default,
  now = Date.now(),
) {
  const key = new Request(
    "https://ethenadash.com/__feed/lighter-stablecoinx-v1",
  );
  let previous;
  try {
    previous = await (await cache?.match(key))?.json();
    if (
      previous?.symbol !== "STABLECOINX" ||
      !(previous.markPrice > 0) ||
      !Number.isFinite(Date.parse(previous.fetchedAt))
    )
      previous = null;
  } catch {
    previous = null;
  }
  const response = (data, stale = false) =>
    Response.json(
      { ...data, stale },
      {
        headers: {
          "Cache-Control": stale ? "no-store" : "public, max-age=30",
          "X-Content-Type-Options": "nosniff",
        },
      },
    );
  if (previous && now - Date.parse(previous.fetchedAt) < 60000)
    return response(previous);
  const end = Math.floor(now / 1000);
  const query = new URLSearchParams({
    market_id: MARKET,
    resolution: "1h",
    start_timestamp: end - 7 * 86400,
    end_timestamp: end,
    count_back: 170,
  });
  const get = async (path) => {
    const r = await fetcher(API + path, {
      signal: AbortSignal.timeout(5000),
      headers: { Accept: "application/json" },
    });
    if (!r.ok) {
      const error = Error("Lighter upstream HTTP " + r.status);
      const retry = r.headers.get("Retry-After");
      error.retryAt =
        retry && /^\d+$/.test(retry)
          ? now + Number(retry) * 1000
          : Date.parse(retry);
      throw error;
    }
    return r.json();
  };
  const history = (field, path) => {
    const last =
      previous?.historyFetchedAt?.[field] ||
      (previous?.[field]?.length ? Date.parse(previous.fetchedAt) : 0);
    const due = Math.max(last + 300000, previous?.historyRetryAt?.[field] || 0);
    return now < due
      ? Promise.resolve({ skipped: true })
      : get(path + "?" + query);
  };
  try {
    const results = await Promise.allSettled([
      get("orderBookDetails?market_id=" + MARKET),
      history("funding", "fundings"),
      history("prices", "candles"),
    ]);
    results.forEach((result, i) => {
      if (result.status === "rejected")
        console.warn(
          "Lighter source failed",
          ["market", "funding", "candles"][i],
          String(result.reason),
        );
      else if (!result.value?.skipped && result.value?.code !== 200)
        console.warn(
          "Lighter source rejected",
          ["market", "funding", "candles"][i],
          result.value?.code,
        );
    });
    const data = normalizeLighter(
      ...results.map((r) => (r.status === "fulfilled" ? r.value : null)),
      now,
    );
    data.historyDelayed = {};
    data.historyFetchedAt = { ...previous?.historyFetchedAt };
    data.historyRetryAt = { ...previous?.historyRetryAt };
    // A brief history outage should not erase a previously verified chart.
    for (const [i, field] of ["funding", "prices"].entries()) {
      const result = results[i + 1],
        skipped = result.value?.skipped;
      const complete = data[field].length > 0;
      data.historyDelayed[field] = skipped
        ? !!previous?.historyDelayed?.[field]
        : !complete;
      if (complete) {
        data.historyFetchedAt[field] = now;
        data.historyRetryAt[field] = 0;
      } else {
        if (previous?.[field]?.length) data[field] = previous[field];
        if (!skipped)
          data.historyRetryAt[field] = Math.max(
            now + 300000,
            result.reason?.retryAt || 0,
          );
        if (!data.historyFetchedAt[field] && previous?.[field]?.length)
          data.historyFetchedAt[field] = Date.parse(previous.fetchedAt);
      }
    }
    data.latestFunding = data.funding.at(-1) || null;
    if (cache)
      ctx.waitUntil(
        cache.put(
          key,
          Response.json(data, {
            headers: { "Cache-Control": "public, max-age=21600" },
          }),
        ),
      );
    return response(data);
  } catch {
    if (previous && now - Date.parse(previous.fetchedAt) <= 6 * HOUR)
      return response(previous, true);
    return Response.json(
      { error: "Lighter data is temporarily unavailable" },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }
}
