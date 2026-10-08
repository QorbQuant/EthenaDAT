import { validFlows } from "../docs/assets/tokenized-flow-model.mjs";
import bundled from "../output/usdeb-flows.json" with { type: "json" };
const URL =
  "https://raw.githubusercontent.com/QorbQuant/EthenaDAT/main/output/usdeb-flows.json";
export async function tokenizedFlowsResponse(
  ctx,
  fetcher = fetch,
  cache = globalThis.caches?.default,
  now = Date.now(),
) {
  const key = new Request("https://ethenadash.com/__feed/usdeb-flows-v1");
  let saved;
  const usable = (d) =>
    validFlows(d, now) && now - Date.parse(d.observedAt) < 7 * 86400000;
  const response = (d, fallback = false) =>
    Response.json(
      {
        ...d,
        stale: fallback || now - Date.parse(d.observedAt) > 36 * 3600000,
      },
      {
        headers: {
          "Cache-Control": fallback ? "no-store" : "public, max-age=300",
          "X-Content-Type-Options": "nosniff",
        },
      },
    );
  try {
    saved = await (await cache?.match(key))?.json();
  } catch {}
  if (saved && usable(saved.data) && now - saved.savedAt < 300000)
    return response(saved.data);
  try {
    const r = await fetcher(URL, {
      signal: AbortSignal.timeout(5000),
      headers: { Accept: "application/json" },
    });
    if (!r.ok) throw Error("Flow feed unavailable");
    const d = await r.json();
    if (!usable(d)) throw Error("Invalid or expired flow feed");
    if (cache)
      ctx.waitUntil(
        cache.put(
          key,
          Response.json(
            { data: d, savedAt: now },
            { headers: { "Cache-Control": "public, max-age=604800" } },
          ),
        ),
      );
    return response(d);
  } catch {
    const fallback = [saved?.data, bundled]
      .filter(usable)
      .sort((a, b) => Date.parse(b.observedAt) - Date.parse(a.observedAt))[0];
    return fallback
      ? response(fallback, true)
      : Response.json(
          { error: "USDEB supply history is temporarily unavailable" },
          { status: 503, headers: { "Cache-Control": "no-store" } },
        );
  }
}
