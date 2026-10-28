-- =====================================================================
-- 02_rfm_segmentation.sql  |  RFM scoring and segment assignment
--
-- Scores use NTILE(5): 1 = worst, 5 = best.
--   Recency   : fewer days since last purchase = higher score
--   Frequency : more orders                    = higher score
--   Monetary  : more revenue                   = higher score
-- customer_id is used as the tie-breaker so results are reproducible
-- and match the Python pipeline exactly.
--
-- Snapshot date is fixed at 2026-10-01 (change in the `params` CTE).
-- Dialect note: the recency line uses SQLite's julianday().
--   PostgreSQL : (p.snapshot_date - b.last_purchase)
--   SQL Server : DATEDIFF(day, b.last_purchase, p.snapshot_date)
--   MySQL      : DATEDIFF(p.snapshot_date, b.last_purchase)
-- =====================================================================

DROP VIEW IF EXISTS vw_rfm_segments;

CREATE VIEW vw_rfm_segments AS
WITH params AS (
    SELECT DATE('2026-10-01') AS snapshot_date
),
base AS (
    SELECT
        t.customer_id,
        MAX(t.transaction_date)         AS last_purchase,
        COUNT(*)                        AS frequency,
        ROUND(SUM(t.amount), 2)         AS monetary
    FROM transactions t
    GROUP BY t.customer_id
),
metrics AS (
    SELECT
        b.customer_id,
        b.last_purchase,
        CAST(julianday(p.snapshot_date) - julianday(b.last_purchase) AS INT) AS recency_days,
        b.frequency,
        b.monetary,
        ROUND(b.monetary * 1.0 / b.frequency, 2) AS avg_order_value
    FROM base b
    CROSS JOIN params p
),
scored AS (
    SELECT
        m.*,
        NTILE(5) OVER (ORDER BY recency_days DESC, customer_id) AS r_score,
        NTILE(5) OVER (ORDER BY frequency,        customer_id) AS f_score,
        NTILE(5) OVER (ORDER BY monetary,         customer_id) AS m_score
    FROM metrics m
)
SELECT
    s.*,
    s.r_score * 100 + s.f_score * 10 + s.m_score AS rfm_score,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions'
        WHEN r_score >= 3                  THEN 'Loyal Customers'
        WHEN f_score >= 3                  THEN 'At-Risk Customers'
        ELSE                                    'Lost Customers'
    END AS segment
FROM scored s;

-- ---------------------------------------------------------------------
-- Segment summary
-- ---------------------------------------------------------------------
SELECT
    segment,
    COUNT(*)                                             AS customers,
    ROUND(AVG(recency_days), 1)                          AS avg_recency_days,
    ROUND(AVG(frequency), 1)                             AS avg_frequency,
    ROUND(AVG(monetary), 2)                              AS avg_monetary,
    ROUND(SUM(monetary), 2)                              AS total_revenue,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)   AS pct_customers,
    ROUND(100.0 * SUM(monetary) / SUM(SUM(monetary)) OVER (), 1) AS pct_revenue
FROM vw_rfm_segments
GROUP BY segment
ORDER BY total_revenue DESC;
