# Campaign Strategy by Segment

Segments come from the RFM scoring in `src/rfm_analysis.py` (snapshot date 2026-10-01). Figures below are from the included dataset; the response-rate and ROI inputs in `excel/rfm_segmentation_report.xlsx` (sheet *Campaign ROI Model*) are planning assumptions to be replaced with real A/B test results.

## Segment snapshot

| Segment | Customers | Share of customers | Share of revenue | Median recency (days) | Median orders | Median spend |
|---|---|---|---|---|---|---|
| Champions | 756 | 21.6% | 52.6% | 22 | 14 | 1,388 |
| Loyal Customers | 1,344 | 38.4% | 25.6% | 49 | 4 | 318 |
| At-Risk Customers | 714 | 20.4% | 16.7% | 247 | 6 | 455 |
| Lost Customers | 686 | 19.6% | 5.1% | 497 | 3 | 140 |

Key reading: about one in five customers (Champions) produces more than half of revenue, while At-Risk customers have a purchase history comparable to Loyal customers but have been silent for 8+ months. They are the most valuable group to recover.

## 1. Champions - protect and amplify

**Goal:** keep them engaged and turn them into advocates.

| Tactic | Detail | KPI |
|---|---|---|
| VIP early access | First access to launches and limited stock; no discount needed | Repeat rate, order frequency |
| Referral programme | Reward both referrer and friend; Champions are the best acquisition channel | Referred sign-ups per 100 Champions |
| Feedback loop | Invite to product panels and reviews | Review volume, NPS |
| Avoid over-discounting | They already buy often; blanket discounts only erode margin | Discount rate on Champion orders |

**Cross-sell:** Champions already buy broadly (68-74% have bought each category). The remaining gap is about 200-240 customers per category, with Home & Kitchen the largest (242 Champions have never bought it). Use personalised category recommendations rather than mass promotion.

## 2. Loyal Customers - grow share of wallet (cross-sell and upsell)

**Goal:** move Loyal customers up to Champions by raising frequency and basket breadth.

The data shows the biggest cross-sell opportunity here: only 39-42% of Loyal customers have bought in any single category, leaving roughly 775-825 customers per category untouched. Beauty (825) and Sports & Outdoors (813) have the widest gaps.

| Tactic | Detail | KPI |
|---|---|---|
| Category bundles | "Complete the set" bundles built from the category they already buy plus the biggest-gap category | Bundle attach rate |
| Loyalty points / tiers | Show progress toward Champion-level rewards | Tier upgrades |
| Replenishment reminders | Triggered at the customer's typical reorder interval | Orders per customer |
| Second-category coupon | Single-use incentive for first purchase in a new category | New-category conversion |

## 3. At-Risk Customers - win back before they churn

**Goal:** re-engage customers who used to buy regularly (median 6 orders) but have not purchased in about 8 months. None have bought in the last 90 days.

| Step | Timing | Content |
|---|---|---|
| 1. "We miss you" | Day 0 | Personal email featuring their most-bought category (Electronics is the top category for this segment, 29% of its revenue) |
| 2. Incentive | Day 7 | Time-limited offer; size it by customer value (see below) |
| 3. Last chance / SMS | Day 14 | Deadline reminder on a second channel |
| 4. Suppress | Day 21 | Non-responders move to the Lost audience, not re-mailed |

**Prioritisation:** rank by historical spend (query 2 in `sql/03_campaign_queries.sql`). The top quartile (179 customers) represents about 172k in lifetime revenue, so they deserve a stronger offer or a personal outreach. Lower-value At-Risk customers get the lighter email-only sequence.

**Measure with a holdout:** keep 10% of the At-Risk audience untouched so reactivation uplift is measured against customers who would have returned anyway.

## 4. Lost Customers - low-cost reactivation, then stop

**Goal:** recover what is cheaply recoverable and avoid wasting budget.

| Tactic | Detail |
|---|---|
| One reactivation email | Strong, simple offer on their top category |
| Survey option | Short "why did you leave?" survey to learn price, product or service reasons |
| Sunset policy | No response after the sequence: suppress from paid channels and email to protect deliverability |

Lost customers are about 20% of the base but only about 5% of revenue, so cost per contact must stay very low; the ROI model assumes email only.

## Measurement plan

| Metric | Where |
|---|---|
| Segment migration (e.g. At-Risk to Loyal) | Re-run the pipeline monthly; compare `segment` per customer |
| Reactivation rate vs holdout | Power BI page "Retention" |
| Incremental revenue per segment | Excel ROI model with actuals pasted in |
| Share of revenue from Champions | Power BI KPI card (dependency risk if it climbs) |
