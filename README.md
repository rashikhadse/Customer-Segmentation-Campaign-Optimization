# Customer Segmentation & Campaign Optimization

A data-driven customer analytics project focused on **customer segmentation, retention, and targeted marketing strategy** using **RFM analysis, Python, SQL, Excel, and Power BI**.

The project analyzes customer purchasing behavior to identify high-value customers, loyal customers, customers at risk of churn, and inactive customers, and translates these segments into actionable marketing strategies.

---

## 📌 Business Problem

Not all customers contribute equally to a business.

Some customers purchase frequently and generate significant revenue, while others have become inactive or are at risk of leaving. Treating every customer with the same marketing strategy can result in inefficient spending and missed retention opportunities.

This project answers:

- Who are the most valuable customers?
- Which customers are loyal and should be rewarded?
- Which customers are at risk of becoming inactive?
- Which customers have already become inactive?
- How can marketing strategies be customized for each segment?
- Which customer segments contribute the most to overall business value?

---

## 🎯 Objectives

1. Analyze customer purchasing behavior.
2. Segment customers based on **Recency, Frequency, and Monetary (RFM)** metrics.
3. Identify high-value and at-risk customer groups.
4. Develop targeted marketing strategies for each customer segment.
5. Build an interactive Power BI dashboard for monitoring customer behavior and segment performance.
6. Convert analytical findings into actionable **retention, cross-sell, and reactivation strategies**.

---

## 🛠️ Tech Stack

| Tool | Purpose |
|---|---|
| **Python** | Data cleaning, preprocessing and customer analysis |
| **Pandas / NumPy** | Data manipulation and numerical analysis |
| **SQL** | Customer-level aggregation and analytical queries |
| **Excel** | Initial exploration and data validation |
| **Power BI** | Interactive dashboard and visualization |
| **Matplotlib / Seaborn** | Exploratory data visualization |

---

## 📊 Analysis Framework

### 1. Data Preparation

The raw customer transaction data was cleaned and prepared for analysis.

Key steps included:

- Handling missing values
- Removing duplicate records
- Standardizing data formats
- Validating transaction dates
- Checking customer-level records
- Creating customer-level aggregates

---

### 2. RFM Analysis

Customers were evaluated using three behavioral metrics:

### Recency

**How recently did the customer make a purchase?**

Lower recency indicates a more recently active customer.

### Frequency

**How often does the customer purchase?**

Higher frequency indicates stronger customer engagement.

### Monetary

**How much has the customer spent?**

Higher monetary value indicates greater customer contribution.

The three metrics were combined to create an RFM-based customer segmentation framework.

---

## 👥 Customer Segments

Customers were classified into actionable groups such as:

| Segment | Customer Characteristics | Marketing Strategy |
|---|---|---|
| 🏆 **Champions** | Recent, frequent and high-value customers | VIP rewards, early access, premium offers |
| 💙 **Loyal Customers** | Consistent purchasing behavior | Loyalty programs, cross-sell and upsell |
| ⚠️ **At-Risk Customers** | Previously valuable but becoming inactive | Personalized offers, reminders, win-back campaigns |
| 🔄 **Potential Loyalists** | Recently active with developing purchase frequency | Engagement campaigns and loyalty incentives |
| 💤 **Lost Customers** | Low recent activity and weak engagement | Reactivation campaigns and targeted discounts |

---

## 💡 Marketing Strategy

The segmentation is used to move from **“who are our customers?”** to **“what should we do about them?”**

### 🏆 Champions

Focus on retention rather than aggressive discounts.

**Strategies:**
- VIP rewards
- Early access to new products
- Exclusive launches
- Premium product recommendations
- Referral programs

### 💙 Loyal Customers

Increase customer lifetime value.

**Strategies:**
- Cross-selling
- Upselling
- Loyalty points
- Personalized product recommendations
- Bundled offers

### ⚠️ At-Risk Customers

Prevent valuable customers from becoming inactive.

**Strategies:**
- Personalized email campaigns
- Limited-time offers
- Product reminders
- Win-back campaigns
- Re-engagement messaging

### 💤 Lost Customers

Attempt selective reactivation while controlling marketing costs.

**Strategies:**
- Targeted reactivation offers
- Personalized discounts
- New-product announcements
- “We miss you” campaigns

---

## 📈 Power BI Dashboard

The interactive dashboard provides a consolidated view of:

- Customer segment distribution
- Customer value
- Purchase frequency
- Recency
- Monetary contribution
- Segment-level revenue
- Customer retention indicators
- High-value customer groups
- At-risk customer groups

### Dashboard Questions

The dashboard is designed to help answer:

> **Who should we retain?**

> **Who should we re-engage?**

> **Which customers generate the most value?**

> **Which customer segments deserve different marketing strategies?**

---

## 🔍 Key Business Insights

The analysis can be used to identify:

- High-value customers who contribute disproportionately to revenue.
- Customers with strong historical value but declining recent activity.
- Segments with opportunities for cross-selling and upselling.
- Customers who require retention or reactivation campaigns.
- Differences in purchasing behavior across customer segments.

The goal is to transform customer-level transaction data into **actionable marketing decisions** rather than simply reporting historical sales.

---

## 📁 Project Structure

```text
customer-segmentation-campaign-optimization/
│
├── data/
│   └── customer_transactions.csv
│
├── notebooks/
│   └── customer_segmentation.ipynb
│
├── sql/
│   └── customer_analysis.sql
│
├── powerbi/
│   └── customer_segmentation_dashboard.pbix
│
├── images/
│   └── dashboard.png
│
├── README.md
└── requirements.txt
```

---

## 🚀 Project Workflow

```text
Raw Transaction Data
        ↓
Data Cleaning & Validation
        ↓
Customer-Level Aggregation
        ↓
RFM Calculation
        ↓
Customer Scoring
        ↓
Customer Segmentation
        ↓
Marketing Strategy
        ↓
Power BI Dashboard
        ↓
Business Recommendations
```

---

## 📌 Example SQL Analysis

Customer-level purchasing behavior can be aggregated using SQL:

```sql
SELECT
    customer_id,
    MAX(order_date) AS last_purchase_date,
    COUNT(DISTINCT order_id) AS purchase_frequency,
    SUM(order_amount) AS monetary_value
FROM transactions
GROUP BY customer_id;
```

These metrics form the foundation for the RFM analysis.

---

## 🧮 RFM Framework

For each customer:

**Recency** = Reference Date − Last Purchase Date

**Frequency** = Number of Purchases

**Monetary** = Total Customer Spend

Customers are then scored and mapped into meaningful behavioral segments.

---

## 📊 Business Impact

This project demonstrates how customer transaction data can support:

- **Customer retention**
- **Targeted marketing**
- **Customer lifetime value optimization**
- **Cross-selling and upselling**
- **Win-back campaigns**
- **Marketing resource allocation**
- **Data-driven customer relationship management**

---

## 🔮 Future Improvements

Potential extensions include:

- Customer Lifetime Value (CLV) prediction
- Churn prediction using machine learning
- Customer propensity modeling
- Personalized recommendation systems
- Campaign response prediction
- A/B testing framework
- Marketing ROI analysis
- Automated Power BI reporting
- Customer cohort and retention analysis

---

## 👩‍💻 Author

**Rashi Rahul Khadse**

B.Tech — Electronics & Communication Engineering

Interested in **Marketing Analytics, Growth, Consumer Insights, Product Analytics, and Data-Driven Strategy**.
