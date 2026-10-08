-- USDEB, BNB Chain. Raw Transfer events only; never count TransferWithUIAmount twice.
-- The collector substitutes a pinned chain block and its UTC date before execution.
SELECT 'event' AS kind, block_number, block_time, "index" AS log_index,
       tx_hash, block_hash, topic0, topic1, topic2, data
FROM bnb.logs
WHERE block_date >= DATE '2026-09-28'
  AND block_date <= DATE '{{end_date}}'
  AND block_number BETWEEN 124478553 AND {{end_block}}
  AND contract_address = 0xdfd3ba51d4591f243481a6f26059d1a5ee95252f
  AND (
    (topic0 = 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
      AND (topic1 = 0x0000000000000000000000000000000000000000000000000000000000000000
        OR topic2 = 0x0000000000000000000000000000000000000000000000000000000000000000))
    OR topic0 IN (
      0x2205df4534432b2f60654a3fdb48737ffdaf3e9edb1a498bd985bc026b15b055,
      0x62204eb4daab41a604e7262a5dca11bd936210002ddfaa885fad182b677ff92c
    )
  )
UNION ALL
-- Reject a result if Dune's log ingestion has not reached the pinned block.
SELECT 'watermark', max(block_number), max(block_time), CAST(NULL AS BIGINT),
       CAST(NULL AS VARBINARY), CAST(NULL AS VARBINARY), CAST(NULL AS VARBINARY),
       CAST(NULL AS VARBINARY), CAST(NULL AS VARBINARY), CAST(NULL AS VARBINARY)
FROM bnb.logs
WHERE block_date >= DATE '{{end_date}}'
  AND block_number >= {{end_block}} - 200000
ORDER BY block_number, log_index
