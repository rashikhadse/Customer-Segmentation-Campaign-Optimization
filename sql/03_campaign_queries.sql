-- =====================================================================
-- 03_campaign_queries.sql  |  Audience lists and analysis for campaigns
-- Requires the view created in 02_rfm_segmentation.sql
-- =====================================================================

-- 1) Retention: repeat-purchase rate and 90-day activity by segment
SELECT
    segment,
    COUNT(*)                                                       AS customers,
    ROUND(100.0 * SUM(CASE WHEN frequency >= 2 THEN 1 ELSE 0 END) / COUNT(*), 1) AS repeat_rate_pct,
    ROUND(100.0 * SUM(CASE WHEN recency_days <= 90 THEN 1 ELSE 0 END) / COUNT(*), 1) AS active_90d_pct
FROM vw_rfm_segments
GROUP BY segment
ORDER BY customers DESC;

-- 2) Win-back audience: at-risk customers ranked by what they are worth
--    (highest historical spend first, so the best offers go to the best customers)
SELECT
    v.customer_id, c.city, c.acquisition_channel,
    v.recency_days, v.frequency, v.monetary, v.avg_order_value
FROM vw_rfm_segments v
JOIN customers c USING (customer_id)
WHERE v.segment = 'At-Risk Customers'
ORDER BY v.monetary DESC
LIMIT 200;

-- 3) Cross-sell gaps: Champions and Loyal customers who have never bought a category
--    that most of their peers buy
WITH high_value AS (
    SELECT customer_id, segment
    FROM vw_rfm_segments
    WHERE segment IN ('Champions', 'Loyal Customers')
),
categories AS (
    SELECT DISTINCT product_category FROM transactions
),
purchased AS (
    SELECT DISTINCT customer_id, product_category FROM transactions
)
SELECT
    h.segment,
    cat.product_category,
    COUNT(*)                                                    AS customers_not_bought,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY h.segment), 1) AS pct_of_gap_in_segment
FROM high_value h
CROSS JOIN categories cat
LEFT JOIN purchased p
       ON p.customer_id = h.customer_id
      AND p.product_category = cat.product_category
WHERE p.customer_id IS NULL
GROUP BY h.segment, cat.product_category
ORDER BY h.segment, customers_not_bought DESC;

-- 4) Monthly revenue by current segment (feeds the Power BI trend visual)
SELECT
    STRFTIME('%Y-%m-01', t.transaction_date) AS month,
    v.segment,
    ROUND(SUM(t.amount), 2)                  AS revenue,
    COUNT(*)                                 AS orders,
    COUNT(DISTINCT t.customer_id)            AS active_customers
FROM transactions t
JOIN vw_rfm_segments v USING (customer_id)
GROUP BY month, v.segment
ORDER BY month, v.segment;

-- 5) Discount sensitivity: do heavier discounts coincide with bigger baskets?
SELECT
    v.segment,
    t.discount_pct,
    COUNT(*)                     AS orders,
    ROUND(AVG(t.amount), 2)      AS avg_order_value
FROM transactions t
JOIN vw_rfm_segments v USING (customer_id)
GROUP BY v.segment, t.discount_pct
ORDER BY v.segment, t.discount_pct;

-- 6) Top 20 Champions for VIP / referral outreach
SELECT customer_id, frequency, monetary, recency_days
FROM vw_rfm_segments
WHERE segment = 'Champions'
ORDER BY monetary DESC
LIMIT 20;
