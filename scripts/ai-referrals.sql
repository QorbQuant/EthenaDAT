-- Identifiable AI-referred page requests, not unique visitors or citation counts.
-- Run in Cloudflare Analytics Engine SQL for this account. Retain exports for
-- long-term comparison. Sampling weights preserve estimated totals.
SELECT
  toDate(timestamp) AS day,
  blob1 AS provider,
  blob2 AS landing_page,
  blob3 AS attribution,
  SUM(_sample_interval * double1) AS page_requests
FROM ethenadash_ai_referrals
WHERE timestamp >= NOW() - INTERVAL '30' DAY
GROUP BY day, provider, landing_page, attribution
ORDER BY day DESC, page_requests DESC
LIMIT 1000
