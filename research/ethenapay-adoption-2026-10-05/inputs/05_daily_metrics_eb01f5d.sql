-- EthenaPay — unified daily metrics
--
-- This is THE dashboard query. One query, one API call, one row per day, covering
-- signups, card spend, deposits/withdrawals, balance held, cashback and yield. The
-- per-domain files (01–04) exist to document and test each metric in isolation;
-- this one is what production reads.
--
-- All definitions and the counting rules they follow are in dune/README.md.

WITH wallets AS (
    SELECT
        ct.address                   AS wallet,
        CAST(ct.block_time AS date)  AS created_date
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

settlements(addr) AS (
    VALUES (0x6070848bd19c37488d0516058f2933dd992733de),
           (0x3b3ffd99b87a2dee5ad244b75d5a8e266890fdb8)
),

-- USDe paid INTO user wallets by the programme. Before 2026-10-05 all of this
-- was counted as deposits. Identified by tracing who pays many wallets in small
-- batched amounts, then testing what each payout tracks (see README):
--   yield        Merkl campaign Safe — claims arrive via the Merkl Distributor,
--                which pulls USDe from this Safe. Per-wallet payouts correlate
--                0.998 with USDe balance held over time, ~4.1% APY.
--   other_reward Paid only to wallets that also receive Merkl yield, at ~12% of
--                it, daily batches. Balance-linked but purpose unconfirmed, so it
--                is kept out of `yield`. The pilot Safe paid $8.65 in Jun–Jul.
reward_payers(addr, kind) AS (
    VALUES (0xd0ec8cc7414f27ce85f8dece6b4a58225f273311, 'yield'),
           (0xab2b06efa6179e624f5e3b08b64978df114ff24f, 'other_reward'),
           (0xc9dd0d4351d3841a712f59cb4f1e88c3d500515b, 'other_reward')
),

-- Cashback is native AVAX from Safes. The current Safe took over on 2026-07-15;
-- the earlier one paid 2026-05-20 → 07-14 and was missed until 2026-10-05.
cashback_payers(addr) AS (
    VALUES (0x37dea6fe8bc3d8d8c47fa3dac98c39a88585a71d),
           (0xfdc9d265ba3cdac512c7fe7e30417cc29487ff7b)
),

avax_price AS (
    SELECT CAST(minute AS date) AS d, AVG(price) AS px
    FROM prices.usd
    WHERE blockchain = 'avalanche_c'
      AND contract_address = 0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7   -- WAVAX
      AND minute >= TIMESTAMP '2026-05-01'
    GROUP BY 1
),

-- ---------- signups ----------
signups AS (
    SELECT created_date AS d, COUNT(*) AS new_users
    FROM wallets
    GROUP BY 1
),

-- ---------- card spend (AllowanceSpent; one row = one spend) ----------
spend AS (
    SELECT
        CAST(l.block_time AS date)                          AS d,
        l.contract_address                                  AS wallet,
        l.tx_hash,
        bytearray_substring(l.topic2, 13, 20)                AS settlement,
        CAST(bytearray_to_uint256(l.data) AS double) / 1e18  AS amount_usde
    FROM avalanche_c.logs l
    WHERE l.topic0 = 0xa575fb45e6259a68f4974e75c94adc55a35f2c06eee07709e964a4407e7dcfeb
      AND l.topic1 = 0x0000000000000000000000005d3a1ff2b6bab83b63cd9ad0787074081a52ef34
      AND bytearray_substring(l.topic2, 13, 20) IN (
            0x6070848bd19c37488d0516058f2933dd992733de,
            0x3b3ffd99b87a2dee5ad244b75d5a8e266890fdb8
          )
),
spend_daily AS (
    SELECT
        d,
        COUNT(*)                                                     AS spend_count,
        COUNT(DISTINCT wallet)                                       AS active_wallets,
        SUM(amount_usde)                                             AS spend_usde,
        SUM(CASE WHEN settlement = 0x6070848bd19c37488d0516058f2933dd992733de
                 THEN amount_usde ELSE 0 END)                        AS spend_usde_current,
        SUM(CASE WHEN settlement = 0x3b3ffd99b87a2dee5ad244b75d5a8e266890fdb8
                 THEN amount_usde ELSE 0 END)                        AS spend_usde_retired,
        AVG(amount_usde)                                             AS avg_spend_usde,
        CAST(COUNT(*) AS double) / NULLIF(COUNT(DISTINCT tx_hash),0) AS logs_per_tx
    FROM spend
    GROUP BY 1
),

-- ---------- USDe flows in and out of user wallets ----------
usde AS (
    SELECT
        CAST(t.evt_block_time AS date) AS d,
        t."from", t.to,
        CAST(t.value AS double) / 1e18 AS amount_usde
    FROM erc20_avalanche_c.evt_Transfer t
    WHERE t.contract_address = 0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34
),
flows AS (
    SELECT
        u.d,
        u.amount_usde,
        COALESCE(win.wallet, wout.wallet) AS wallet,
        CASE
            WHEN win.wallet IS NOT NULL AND wout.wallet IS NOT NULL THEN 'internal'
            WHEN win.wallet IS NOT NULL AND sf.addr     IS NOT NULL THEN 'reversal'
            WHEN win.wallet IS NOT NULL AND rp.kind     IS NOT NULL THEN rp.kind
            WHEN win.wallet IS NOT NULL                             THEN 'deposit'
            WHEN wout.wallet IS NOT NULL AND st.addr    IS NOT NULL THEN 'card_spend'
            WHEN wout.wallet IS NOT NULL                            THEN 'withdrawal'
        END AS flow_type
    FROM usde u
    LEFT JOIN wallets     win  ON win.wallet  = u.to
    LEFT JOIN wallets     wout ON wout.wallet = u."from"
    LEFT JOIN settlements sf   ON sf.addr     = u."from"
    LEFT JOIN settlements st   ON st.addr     = u.to
    LEFT JOIN reward_payers rp ON rp.addr     = u."from"
    WHERE win.wallet IS NOT NULL OR wout.wallet IS NOT NULL
),
flow_daily AS (
    SELECT
        d,
        SUM(CASE WHEN flow_type='deposit'    THEN amount_usde ELSE 0 END) AS deposits_usde,
        SUM(CASE WHEN flow_type='withdrawal' THEN amount_usde ELSE 0 END) AS withdrawals_usde,
        SUM(CASE WHEN flow_type='reversal'   THEN amount_usde ELSE 0 END) AS reversals_usde,
        SUM(CASE WHEN flow_type='yield'      THEN amount_usde ELSE 0 END) AS yield_usde,
        SUM(CASE WHEN flow_type='other_reward' THEN amount_usde ELSE 0 END) AS other_rewards_usde,
        COUNT(DISTINCT CASE WHEN flow_type='deposit' THEN wallet END)     AS depositing_wallets,
        COUNT(DISTINCT CASE WHEN flow_type='yield'   THEN wallet END)     AS yield_wallets,
        SUM(CASE WHEN flow_type='deposit'    THEN amount_usde
                 WHEN flow_type='reversal'   THEN amount_usde
                 WHEN flow_type='yield'      THEN amount_usde
                 WHEN flow_type='other_reward' THEN amount_usde
                 WHEN flow_type='withdrawal' THEN -amount_usde
                 WHEN flow_type='card_spend' THEN -amount_usde
                 ELSE 0 END)                                              AS net_flow_usde
    FROM flows
    GROUP BY 1
),

-- ---------- cashback (native AVAX internal calls, NOT ERC20 transfers) ----------
cashback_daily AS (
    SELECT
        CAST(tr.block_time AS date)              AS d,
        SUM(CAST(tr.value AS double)/1e18)       AS cashback_avax,
        -- valued at that day's average AVAX price, i.e. what it was worth when paid
        SUM(CAST(tr.value AS double)/1e18 * px.px) AS cashback_usd,
        COUNT(DISTINCT tr.to)                    AS cashback_wallets
    FROM avalanche_c.traces tr
    JOIN wallets w ON w.wallet = tr.to
    JOIN cashback_payers cp ON cp.addr = tr."from"
    LEFT JOIN avax_price px ON px.d = CAST(tr.block_time AS date)
    WHERE tr.block_time >= TIMESTAMP '2026-05-01'
      AND tr.value > UINT256 '0'
      AND tr.call_type = 'call'
      AND tr.success
      AND tr.tx_success
    GROUP BY 1
),

calendar AS (
    SELECT d FROM (SELECT d FROM signups
                   UNION SELECT d FROM spend_daily
                   UNION SELECT d FROM flow_daily
                   UNION SELECT d FROM cashback_daily) x
)

SELECT
    c.d                                                       AS day,
    COALESCE(s.new_users, 0)                                  AS new_users,
    SUM(COALESCE(s.new_users,0)) OVER (ORDER BY c.d
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)     AS cumulative_users,
    COALESCE(sp.active_wallets, 0)                            AS active_wallets,
    COALESCE(sp.spend_count, 0)                               AS spend_count,
    COALESCE(sp.spend_usde, 0)                                AS spend_usde,
    COALESCE(sp.spend_usde_current, 0)                        AS spend_usde_current,
    COALESCE(sp.spend_usde_retired, 0)                        AS spend_usde_retired,
    sp.avg_spend_usde,
    sp.logs_per_tx,
    COALESCE(f.deposits_usde, 0)                              AS deposits_usde,
    COALESCE(f.withdrawals_usde, 0)                           AS withdrawals_usde,
    COALESCE(f.reversals_usde, 0)                             AS reversals_usde,
    COALESCE(f.depositing_wallets, 0)                         AS depositing_wallets,
    COALESCE(f.net_flow_usde, 0)                              AS net_flow_usde,
    -- running net flow = USDe currently held across all user wallets
    SUM(COALESCE(f.net_flow_usde,0)) OVER (ORDER BY c.d
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)     AS tvl_usde,
    COALESCE(f.yield_usde, 0)                                 AS yield_usde,
    COALESCE(f.yield_wallets, 0)                              AS yield_wallets,
    COALESCE(f.other_rewards_usde, 0)                         AS other_rewards_usde,
    COALESCE(cb.cashback_avax, 0)                             AS cashback_avax,
    COALESCE(cb.cashback_usd, 0)                              AS cashback_usd,
    COALESCE(cb.cashback_wallets, 0)                          AS cashback_wallets
FROM calendar c
LEFT JOIN signups        s  ON s.d  = c.d
LEFT JOIN spend_daily    sp ON sp.d = c.d
LEFT JOIN flow_daily     f  ON f.d  = c.d
LEFT JOIN cashback_daily cb ON cb.d = c.d
ORDER BY c.d
