# DAX Measures

Create a table called `_Measures` (Home > Enter Data, one blank column, then delete the column) and add the measures below. Table names assume the data model in `powerbi/README.md`: `rfm_customers`, `transactions_with_segment`, `segment_summary`, `DimDate`.

## Core KPIs

```dax
Total Customers = DISTINCTCOUNT ( rfm_customers[customer_id] )

Total Revenue = SUM ( transactions_with_segment[amount] )

Total Orders = COUNTROWS ( transactions_with_segment )

Avg Order Value = DIVIDE ( [Total Revenue], [Total Orders] )

Revenue per Customer = DIVIDE ( [Total Revenue], [Total Customers] )
```

## Purchase frequency and customer value

```dax
Avg Purchase Frequency = AVERAGE ( rfm_customers[frequency] )

Avg Recency (days) = AVERAGE ( rfm_customers[recency_days] )

Avg Customer Value = AVERAGE ( rfm_customers[monetary] )
```

## Segment contribution

```dax
Revenue % of Total =
DIVIDE (
    [Total Revenue],
    CALCULATE ( [Total Revenue], ALL ( rfm_customers[segment] ) )
)

Customer % of Total =
DIVIDE (
    [Total Customers],
    CALCULATE ( [Total Customers], ALL ( rfm_customers[segment] ) )
)

Champions Revenue % =
DIVIDE (
    CALCULATE ( [Total Revenue], rfm_customers[segment] = "Champions" ),
    CALCULATE ( [Total Revenue], ALL ( rfm_customers[segment] ) )
)
```

## Retention

```dax
Repeat Customers =
CALCULATE (
    DISTINCTCOUNT ( rfm_customers[customer_id] ),
    rfm_customers[frequency] >= 2
)

Repeat Purchase Rate = DIVIDE ( [Repeat Customers], [Total Customers] )

Active Customers (90d) =
CALCULATE (
    DISTINCTCOUNT ( rfm_customers[customer_id] ),
    rfm_customers[recency_days] <= 90
)

Active Rate (90d) = DIVIDE ( [Active Customers (90d)], [Total Customers] )

At-Risk Customers =
CALCULATE (
    DISTINCTCOUNT ( rfm_customers[customer_id] ),
    rfm_customers[segment] = "At-Risk Customers"
)

At-Risk Revenue at Stake =
CALCULATE (
    SUM ( rfm_customers[monetary] ),
    rfm_customers[segment] = "At-Risk Customers"
)
```

## Time intelligence (requires `DimDate` marked as a date table)

```dax
Revenue MoM % =
VAR Prev = CALCULATE ( [Total Revenue], DATEADD ( DimDate[Date], -1, MONTH ) )
RETURN DIVIDE ( [Total Revenue] - Prev, Prev )

Revenue YTD = TOTALYTD ( [Total Revenue], DimDate[Date] )

Active Customers in Month =
DISTINCTCOUNT ( transactions_with_segment[customer_id] )
```

DimDate calculated table:

```dax
DimDate =
ADDCOLUMNS (
    CALENDAR ( DATE ( 2024, 10, 1 ), DATE ( 2026, 12, 31 ) ),
    "Year", YEAR ( [Date] ),
    "Month Number", MONTH ( [Date] ),
    "Month", FORMAT ( [Date], "MMM yyyy" ),
    "Quarter", "Q" & QUARTER ( [Date] ) & " " & YEAR ( [Date] )
)
```

## Dynamic segment colouring (conditional formatting by rules)

```dax
Segment Color =
SWITCH (
    SELECTEDVALUE ( rfm_customers[segment] ),
    "Champions",         "#1D7A4B",
    "Loyal Customers",   "#2F6DB5",
    "At-Risk Customers", "#D98A1F",
    "Lost Customers",    "#B5443A",
    "#7F8793"
)
```

## Segment sort order

Add a calculated column on `rfm_customers` so segments sort best to worst, then set *Sort by column* on `segment`:

```dax
Segment Order =
SWITCH (
    rfm_customers[segment],
    "Champions", 1,
    "Loyal Customers", 2,
    "At-Risk Customers", 3,
    "Lost Customers", 4
)
```
