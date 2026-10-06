-- EthenaPay — headline KPIs (single row)
--
-- These cannot be derived by summing 05_daily_metrics.sql: lifetime distinct
-- spenders is not the sum of daily distinct spenders, and the 7d/30d windows need
-- their own DISTINCT. Run this alongside the daily query.
--
-- It also computes the funnel (deployed -> funded -> ever spent) and balance
-- concentration, so the dashboard shows the same figures whether it is reading
-- Dune or the on-chain snapshot.

WITH wallets AS (
    SELECT ct.address AS wallet, CAST(ct.block_time AS date) AS created_date
    FROM avalanche_c.creation_traces ct
    WHERE ct."from" IN (
            0x313be708df16979d9e5fe9db5ac4969b8add7207,  -- v1 pilot factory
            0xac66ca9a79fb0d3c64cba44cd29610cd58602d6f   -- v2 current factory
        )
      AND ct.address NOT IN (
            0xc831ea25deb7654679a438c78c4c5d1c313c8448,
            0xb4446da2e3970776dcfd44e78b034c8243f91c75,
            0xddaffdb1c5f0774ee734cf3491aafd4f0a678127
        )
),

spend AS (
    SELECT
        l.block_time,
        l.tx_hash,
        l.contract_address                                  AS wallet,
        CAST(bytearray_to_uint256(l.data) AS double) / 1e18 AS amount_usde
    FROM avalanche_c.logs l
    WHERE l.topic0 = 0xa575fb45e6259a68f4974e75c94adc55a35f2c06eee07709e964a4407e7dcfeb
      AND l.topic1 = 0x0000000000000000000000005d3a1ff2b6bab83b63cd9ad0787074081a52ef34
      AND bytearray_substring(l.topic2, 13, 20) IN (
            0x6070848bd19c37488d0516058f2933dd992733de,
            0x3b3ffd99b87a2dee5ad244b75d5a8e266890fdb8
          )
),

-- Per-wallet USDe balance, as inflow minus outflow. Equivalent to calling
-- balanceOf on every wallet, but expressed in SQL over transfer history.
balances AS (
    SELECT wallet, SUM(delta) AS balance_usde
    FROM (
        SELECT t.to AS wallet,  CAST(t.value AS double) / 1e18 AS delta
        FROM erc20_avalanche_c.evt_Transfer t
        WHERE t.contract_address = 0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34
        UNION ALL
        SELECT t."from" AS wallet, -CAST(t.value AS double) / 1e18 AS delta
        FROM erc20_avalanche_c.evt_Transfer t
        WHERE t.contract_address = 0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34
    ) m
    WHERE m.wallet IN (SELECT wallet FROM wallets)
    GROUP BY wallet
),

cashback AS (
    SELECT SUM(CAST(tr.value AS double) / 1e18) AS cashback_avax_total,
           COUNT(*)                             AS cashback_payments_total
    FROM avalanche_c.traces tr
    JOIN wallets w ON w.wallet = tr.to
    WHERE tr."from" = 0x37dea6fe8bc3d8d8c47fa3dac98c39a88585a71d
      AND tr.value > UINT256 '0'
      AND tr.call_type = 'call'
      AND tr.success
      AND tr.tx_success
),

bal_stats AS (
    SELECT
        COUNT(*) FILTER (WHERE balance_usde > 0)                   AS funded_wallets,
        SUM(GREATEST(balance_usde, 0))                             AS tvl_usde,
        -- concentration: a headline TVL driven by ten accounts is not retail growth
        SUM(GREATEST(balance_usde, 0)) FILTER (
            WHERE rn <= 10)                                        AS top10_usde
    FROM (SELECT wallet, balance_usde,
                 ROW_NUMBER() OVER (ORDER BY balance_usde DESC) AS rn
          FROM balances) b
),

spend_stats AS (
    SELECT
        COUNT(*)                                        AS lifetime_spend_count,
        SUM(amount_usde)                                AS lifetime_spend_usde,
        COUNT(DISTINCT wallet)                          AS lifetime_spenders,
        COUNT(DISTINCT CASE WHEN block_time >= CURRENT_DATE - INTERVAL '30' DAY THEN wallet END) AS mau_30d,
        COUNT(DISTINCT CASE WHEN block_time >= CURRENT_DATE - INTERVAL '7'  DAY THEN wallet END) AS wau_7d,
        SUM(CASE WHEN block_time >= CURRENT_DATE - INTERVAL '30' DAY THEN amount_usde ELSE 0 END) AS spend_usde_30d,
        AVG(amount_usde)                                AS avg_spend_usde,
        APPROX_PERCENTILE(amount_usde, 0.5)             AS median_spend_usde
    FROM spend
)

SELECT
    (SELECT COUNT(*) FROM wallets)                                      AS total_users,
    (SELECT COUNT(*) FROM wallets WHERE created_date >= CURRENT_DATE - INTERVAL '30' DAY)
                                                                        AS new_users_30d,
    bs.funded_wallets,
    ss.lifetime_spenders,
    ss.lifetime_spend_count,
    ss.lifetime_spend_usde,
    ss.spend_usde_30d,
    ss.mau_30d,
    ss.wau_7d,
    ss.avg_spend_usde,
    ss.median_spend_usde,
    -- highest number of spend events sharing one transaction; >1 means batching
    (SELECT MAX(n) FROM (SELECT COUNT(*) AS n FROM spend GROUP BY tx_hash) x)
                                                                        AS max_logs_per_tx,
    -- share of spend events that sit inside a multi-event transaction
    (SELECT CAST(SUM(CASE WHEN n > 1 THEN n ELSE 0 END) AS double) / NULLIF(SUM(n), 0)
     FROM (SELECT COUNT(*) AS n FROM spend GROUP BY tx_hash) y)
                                                                        AS batched_spend_share,
    bs.tvl_usde,
    bs.top10_usde / NULLIF(bs.tvl_usde, 0)                              AS top10_balance_share,
    cb.cashback_avax_total,
    cb.cashback_payments_total,
    CAST(ss.lifetime_spenders AS double)
        / NULLIF((SELECT COUNT(*) FROM wallets), 0)                     AS activation_rate,
    CAST(bs.funded_wallets AS double)
        / NULLIF((SELECT COUNT(*) FROM wallets), 0)                     AS funding_rate
FROM spend_stats ss
CROSS JOIN bal_stats bs
CROSS JOIN cashback  cb
