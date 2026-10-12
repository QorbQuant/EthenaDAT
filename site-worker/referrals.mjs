// Store only a known provider, canonical page and attribution method. No visitor IDs,
// IP addresses, query strings, full referrers or cookies are written to this dataset.
const providers = [
  ["chatgpt.com", "ChatGPT"],
  ["chat.openai.com", "ChatGPT"],
  ["perplexity.ai", "Perplexity"],
  ["claude.ai", "Claude"],
  ["copilot.microsoft.com", "Copilot"],
  ["gemini.google.com", "Gemini"],
];
const campaign = new Map(
  providers.flatMap(([host, name]) => [
    [host, name],
    [name.toLowerCase(), name],
  ]),
);
export function classifyReferral(request) {
  if (
    request.method !== "GET" ||
    !request.headers.get("accept")?.includes("text/html")
  )
    return null;
  const ua = request.headers.get("user-agent") || "";
  if (
    !ua ||
    /bot|crawler|spider|preview|chatgpt-user|perplexity-user|curl|wget|python|headless/i.test(
      ua,
    )
  )
    return null;
  if (
    /prefetch|prerender/i.test(
      (request.headers.get("purpose") || "") +
        " " +
        (request.headers.get("sec-purpose") || ""),
    )
  )
    return null;
  const mode = request.headers.get("sec-fetch-dest");
  if (mode && mode !== "document") return null;
  let host = "";
  try {
    host = new URL(request.headers.get("referer")).hostname.toLowerCase();
  } catch {}
  if (host === "ethenadash.com" || host.endsWith(".ethenadash.com"))
    return null;
  const provider = providers.find(
    ([domain]) => host === domain || host.endsWith("." + domain),
  );
  if (provider) return { provider: provider[1], method: "referrer" };
  const named = campaign.get(
    (new URL(request.url).searchParams.get("utm_source") || "").toLowerCase(),
  );
  return named ? { provider: named, method: "campaign" } : null;
}
export function recordReferral(request, env, path) {
  const referral = classifyReferral(request);
  if (!referral || !env.AI_REFERRALS) return;
  try {
    env.AI_REFERRALS.writeDataPoint({
      indexes: [referral.provider],
      blobs: [referral.provider, path, referral.method],
      doubles: [1],
    });
  } catch {
    /* Analytics cannot interrupt a page response. */
  }
}
