# Power BI Dashboard - Build Guide

A `.pbix` file is a binary that has to be authored in Power BI Desktop, so this folder gives you everything needed to build it in about 30-45 minutes: clean data, the data model, every DAX measure, and a page-by-page layout. Save your finished file as `powerbi/Customer_Segmentation_Dashboard.pbix` and add a screenshot to `images/dashboard.png`, then reference it from the main README.

## 1. Load the data

Get Data > Text/CSV, load these files from `data/processed/`:

| File | Table name | Grain |
|---|---|---|
| `rfm_customers.csv` | `rfm_customers` | one row per customer (RFM scores, segment, city, channel) |
| `transactions_with_segment.csv` | `transactions_with_segment` | one row per purchase, tagged with segment |
| `segment_summary.csv` | `segment_summary` | one row per segment |
| `category_by_segment.csv` | `category_by_segment` | segment x product category |
| `cross_sell_gaps.csv` | `cross_sell_gaps` | segment x category penetration |
| `cohort_retention.csv` | `cohort_retention` | acquisition-quarter cohort x quarters since |
| `monthly_segment_revenue.csv` | `monthly_segment_revenue` | month x segment |

Check data types in Power Query: dates as *Date*, `amount`/`monetary` as *Fixed decimal number*, scores as *Whole number*.

## 2. Data model

Star-style model, all relationships single direction (dimension to fact):

```
DimDate[Date]        1 --> *  transactions_with_segment[transaction_date]
rfm_customers[customer_id]  1 --> *  transactions_with_segment[customer_id]
```

`segment_summary`, `category_by_segment`, `cross_sell_gaps`, `cohort_retention` and `monthly_segment_revenue` are pre-aggregated and can stay unrelated; they power single visuals. Create `DimDate` and the measures from `dax_measures.md`, mark `DimDate` as a date table, and add the `Segment Order` column.

## 3. Report pages

**Page 1 - Executive Overview**
- KPI cards: Total Customers, Total Revenue, Avg Order Value, Repeat Purchase Rate, Active Rate (90d)
- Donut or bar: Customers by segment (`Customer % of Total`)
- Clustered bar: Revenue % of Total by segment (shows the contrast: roughly 22% of customers produce 53% of revenue)
- Line chart: Total Revenue by month, legend = segment
- Slicers: segment, city, acquisition channel, year

**Page 2 - Customer Value and Purchase Frequency**
- Scatter: x = `recency_days`, y = `frequency`, size = `monetary`, legend = segment
- Table: segment with Avg Recency, Avg Purchase Frequency, Avg Customer Value, Revenue per Customer
- Histogram-style column chart: customers by `f_score` (1-5)
- Matrix heatmap: rows = `f_score`, columns = `r_score`, values = customer count (conditional formatting background)

**Page 3 - Retention**
- Cohort matrix from `cohort_retention`: rows = cohort, columns = quarters_since, values = retention (colour scale)
- Cards: At-Risk Customers, At-Risk Revenue at Stake
- Bar: Repeat Purchase Rate by segment
- Table: top 50 at-risk customers by `monetary` (Top N filter) with city and last purchase date, this is the win-back call list

**Page 4 - Segment Contribution and Cross-sell**
- Stacked column: category revenue by segment (`category_by_segment`)
- Matrix: `cross_sell_gaps` penetration by segment x category, colour scale (low penetration = opportunity)
- Bar: customers not yet bought, by category, filtered to Loyal Customers
- Text box: recommended campaign per segment (copy from `docs/campaign_strategy.md`)

## 4. Formatting tips
- Use the segment colours from `dax_measures.md` (Segment Color) for every visual so a segment always has the same colour.
- Sort segments with the `Segment Order` column.
- Turn on *Sync slicers* so filters carry across pages.
- Add a page-navigation bar with bookmarks or buttons.
- Keep titles descriptive ("Revenue share vs customer share") rather than generic.

## 5. Refreshing
Re-run `python src/rfm_analysis.py` to regenerate the CSVs, then click Refresh in Power BI. If you connect to a database instead, point Get Data at the `vw_rfm_segments` view created by `sql/02_rfm_segmentation.sql`.
