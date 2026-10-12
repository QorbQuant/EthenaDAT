# AI visibility measurement

The site records successful canonical HTML GET requests with an identifiable AI
referrer or an exact, recognized utm_source. It excludes known crawler/preview
user agents, prefetches, local development, HEAD, redirects, API/download/asset
requests, and navigation from the site itself.

Cloudflare Analytics Engine dataset: `ethenadash_ai_referrals`.

- blob1: recognized provider (ChatGPT, Perplexity, Claude, Copilot, Gemini)
- blob2: canonical landing path from the page registry
- blob3: `referrer` or `campaign`
- double1: 1 page request
- index1: provider

Run `scripts/ai-referrals.sql` in the account's Analytics Engine SQL interface,
or the SQL API using an Account Analytics Read token. No token belongs in this
repository or in the browser. Use sampling-weighted totals. Cloudflare currently
retains Analytics Engine observations for three months; export reports if needed.

These are attributed page requests, not unique people, sessions or citation
counts. Bots can spoof browser headers and campaign tags can be copied. Some AI
apps omit both referrers and tags, so totals undercount traffic. Citation without
a click cannot appear here. The dataset does not store IPs, identifiers, full
referrers, user agents or query strings and sets no cookies. Do not send synthetic
browser-looking AI traffic to production when validating this feature.

To check actual citations, manually ask the same small set of questions in fresh
search-enabled chats, record the date, engine, exact prompt and returned source
URLs. Suggested prompts: What does StablecoinX mNAV measure? How many wallets use
EthenaPay? What is USDEB net issuance? Does Lighter's StablecoinX perp track USDE?
Keep those observations separate from referral totals and Google indexing.

Technical crawl eligibility can be checked with `scripts/check_seo.py`. User-agent
checks do not establish that the real crawler visited or indexed a page. No
training-bot policy was changed for this feature.
