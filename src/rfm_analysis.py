"""
RFM customer segmentation pipeline.

Steps
  1. Load customers + transactions
  2. Compute Recency / Frequency / Monetary per customer
  3. Score each dimension 1-5 (NTILE-style quintiles, identical to sql/02_rfm_segmentation.sql)
  4. Assign segments: Champions, Loyal Customers, At-Risk Customers, Lost Customers
  5. Export CSVs for Power BI, a formatted Excel workbook, and charts

Usage:
    python src/rfm_analysis.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
IMG = ROOT / "images"
XLSX = ROOT / "excel" / "rfm_segmentation_report.xlsx"

SNAPSHOT_DATE = pd.Timestamp("2026-10-01")
SEGMENT_ORDER = ["Champions", "Loyal Customers", "At-Risk Customers", "Lost Customers"]
SEGMENT_COLORS = {
    "Champions": "#1D7A4B",
    "Loyal Customers": "#2F6DB5",
    "At-Risk Customers": "#D98A1F",
    "Lost Customers": "#B5443A",
}


# --------------------------------------------------------------------------- #
# Core logic
# --------------------------------------------------------------------------- #
def ntile(series: pd.Series, buckets: int = 5) -> pd.Series:
    """SQL NTILE(): rank rows (ties broken by order given) and split into buckets.

    The first `n % buckets` buckets receive one extra row, exactly like NTILE.
    Returns scores 1..buckets in ascending order of the series.
    """
    n = len(series)
    order = np.lexsort((series.index.values, series.values))  # value asc, then index asc
    base, rem = divmod(n, buckets)
    sizes = [base + 1 if i < rem else base for i in range(buckets)]
    scores = np.empty(n, dtype=int)
    pos = 0
    for b, size in enumerate(sizes, start=1):
        scores[order[pos:pos + size]] = b
        pos += size
    return pd.Series(scores, index=series.index)


def assign_segment(r: int, f: int) -> str:
    """Segment rules (R and F scores, 1 = worst, 5 = best).

    Champions        R >= 4 and F >= 4   bought recently and buy often
    Loyal Customers  R >= 3 (not above)  still active; repeat or developing buyers
    At-Risk          R <= 2 and F >= 3   used to buy regularly, gone quiet
    Lost Customers   R <= 2 and F <= 2   low engagement and long inactive
    """
    if r >= 4 and f >= 4:
        return "Champions"
    if r >= 3:
        return "Loyal Customers"
    if f >= 3:
        return "At-Risk Customers"
    return "Lost Customers"


def build_rfm(customers: pd.DataFrame, txns: pd.DataFrame) -> pd.DataFrame:
    agg = (
        txns.groupby("customer_id")
        .agg(
            last_purchase=("transaction_date", "max"),
            first_purchase=("transaction_date", "min"),
            frequency=("transaction_id", "count"),
            monetary=("amount", "sum"),
        )
        .reset_index()
    )
    agg["recency_days"] = (SNAPSHOT_DATE - agg["last_purchase"]).dt.days
    agg["avg_order_value"] = (agg["monetary"] / agg["frequency"]).round(2)
    agg["monetary"] = agg["monetary"].round(2)

    agg = agg.sort_values("customer_id").reset_index(drop=True)
    # NTILE ordering mirrors the SQL: R by recency DESC, F and M ascending
    agg["r_score"] = ntile(-agg["recency_days"])
    agg["f_score"] = ntile(agg["frequency"])
    agg["m_score"] = ntile(agg["monetary"])
    agg["rfm_score"] = agg["r_score"] * 100 + agg["f_score"] * 10 + agg["m_score"]
    agg["segment"] = [assign_segment(r, f) for r, f in zip(agg["r_score"], agg["f_score"])]

    out = agg.merge(customers, on="customer_id", how="left")
    return out


def segment_summary(rfm: pd.DataFrame) -> pd.DataFrame:
    g = rfm.groupby("segment")
    s = g.agg(
        customers=("customer_id", "count"),
        avg_recency_days=("recency_days", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        total_revenue=("monetary", "sum"),
        avg_order_value=("avg_order_value", "mean"),
        repeat_rate=("frequency", lambda x: (x >= 2).mean()),
        active_90d_rate=("recency_days", lambda x: (x <= 90).mean()),
    )
    s["customer_share"] = s["customers"] / s["customers"].sum()
    s["revenue_share"] = s["total_revenue"] / s["total_revenue"].sum()
    s = s.reindex(SEGMENT_ORDER).reset_index()
    return s.round(4)


# --------------------------------------------------------------------------- #
# Extra analyses used by the dashboard and campaign design
# --------------------------------------------------------------------------- #
def monthly_segment_revenue(txns: pd.DataFrame, rfm: pd.DataFrame) -> pd.DataFrame:
    t = txns.merge(rfm[["customer_id", "segment"]], on="customer_id")
    t["month"] = t["transaction_date"].dt.to_period("M").dt.to_timestamp()
    out = (
        t.groupby(["month", "segment"])
        .agg(revenue=("amount", "sum"), orders=("transaction_id", "count"),
             active_customers=("customer_id", "nunique"))
        .reset_index()
    )
    out["revenue"] = out["revenue"].round(2)
    return out


def category_by_segment(txns: pd.DataFrame, rfm: pd.DataFrame) -> pd.DataFrame:
    t = txns.merge(rfm[["customer_id", "segment"]], on="customer_id")
    c = (
        t.groupby(["segment", "product_category"])
        .agg(revenue=("amount", "sum"), orders=("transaction_id", "count"),
             customers=("customer_id", "nunique"))
        .reset_index()
    )
    seg_tot = c.groupby("segment")["revenue"].transform("sum")
    c["revenue_share_in_segment"] = (c["revenue"] / seg_tot).round(4)
    c["revenue"] = c["revenue"].round(2)
    return c


def cross_sell_gaps(txns: pd.DataFrame, rfm: pd.DataFrame) -> pd.DataFrame:
    """For Champions + Loyal customers: how many have NOT yet bought each category."""
    high = rfm[rfm["segment"].isin(["Champions", "Loyal Customers"])]
    bought = txns[txns["customer_id"].isin(high["customer_id"])]
    cats = sorted(txns["product_category"].unique())
    rows = []
    for seg in ["Champions", "Loyal Customers"]:
        ids = set(high.loc[high["segment"] == seg, "customer_id"])
        for cat in cats:
            buyers = set(bought.loc[(bought["product_category"] == cat) &
                                    (bought["customer_id"].isin(ids)), "customer_id"])
            rows.append({
                "segment": seg,
                "product_category": cat,
                "customers_bought": len(buyers),
                "customers_not_bought": len(ids) - len(buyers),
                "penetration": round(len(buyers) / len(ids), 4),
            })
    return pd.DataFrame(rows)


def cohort_retention(txns: pd.DataFrame, rfm: pd.DataFrame) -> pd.DataFrame:
    """Share of each acquisition-quarter cohort that purchased in each later quarter."""
    t = txns.copy()
    t["q"] = t["transaction_date"].dt.to_period("Q")
    first_q = t.groupby("customer_id")["q"].min().rename("cohort")
    t = t.merge(first_q, on="customer_id")
    t["quarters_since"] = (t["q"] - t["cohort"]).apply(lambda x: x.n)
    sizes = t.groupby("cohort")["customer_id"].nunique()
    act = t.groupby(["cohort", "quarters_since"])["customer_id"].nunique().reset_index()
    act["cohort_size"] = act["cohort"].map(sizes)
    act["retention"] = (act["customer_id"] / act["cohort_size"]).round(4)
    act = act.rename(columns={"customer_id": "active_customers"})
    act["cohort"] = act["cohort"].astype(str)
    return act


# --------------------------------------------------------------------------- #
# Charts
# --------------------------------------------------------------------------- #
def make_charts(rfm: pd.DataFrame, summary: pd.DataFrame, monthly: pd.DataFrame) -> None:
    IMG.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    colors = [SEGMENT_COLORS[s] for s in summary["segment"]]

    # 1. customer share vs revenue share
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(summary))
    w = 0.38
    ax.bar(x - w / 2, summary["customer_share"] * 100, w, label="% of customers", color="#9AA5B1")
    ax.bar(x + w / 2, summary["revenue_share"] * 100, w, label="% of revenue", color=colors)
    for i, (c, r) in enumerate(zip(summary["customer_share"], summary["revenue_share"])):
        ax.text(i - w / 2, c * 100 + 0.8, f"{c:.0%}", ha="center", fontsize=9)
        ax.text(i + w / 2, r * 100 + 0.8, f"{r:.0%}", ha="center", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(summary["segment"])
    ax.set_ylabel("Share (%)")
    ax.set_title("Customer share vs revenue share by segment")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(IMG / "segment_contribution.png", dpi=150)
    plt.close(fig)

    # 2. recency vs frequency scatter
    fig, ax = plt.subplots(figsize=(8, 5))
    for seg in SEGMENT_ORDER:
        d = rfm[rfm["segment"] == seg]
        ax.scatter(d["recency_days"], d["frequency"], s=10, alpha=0.45,
                   color=SEGMENT_COLORS[seg], label=seg)
    ax.set_xlabel("Recency (days since last purchase)")
    ax.set_ylabel("Frequency (orders)")
    ax.set_title("Customers by recency and frequency")
    ax.legend(frameon=False, markerscale=2)
    fig.tight_layout()
    fig.savefig(IMG / "rfm_scatter.png", dpi=150)
    plt.close(fig)

    # 3. monthly revenue by segment (stacked)
    pivot = monthly.pivot(index="month", columns="segment", values="revenue").fillna(0)
    pivot = pivot[[s for s in SEGMENT_ORDER if s in pivot.columns]]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.stackplot(pivot.index, pivot.T.values, labels=pivot.columns,
                 colors=[SEGMENT_COLORS[s] for s in pivot.columns], alpha=0.9)
    ax.set_ylabel("Revenue")
    ax.set_title("Monthly revenue by current segment")
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(IMG / "monthly_revenue_by_segment.png", dpi=150)
    plt.close(fig)

    # 4. RFM heatmap of mean monetary by R and F
    heat = rfm.pivot_table(index="f_score", columns="r_score", values="customer_id",
                           aggfunc="count").fillna(0).sort_index(ascending=False)
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(heat.values, cmap="Blues")
    ax.set_xticks(range(heat.shape[1]))
    ax.set_xticklabels(heat.columns)
    ax.set_yticks(range(heat.shape[0]))
    ax.set_yticklabels(heat.index)
    for i in range(heat.shape[0]):
        for j in range(heat.shape[1]):
            ax.text(j, i, int(heat.values[i, j]), ha="center", va="center", fontsize=9)
    ax.set_xlabel("Recency score (5 = most recent)")
    ax.set_ylabel("Frequency score (5 = most frequent)")
    ax.set_title("Customer count by R and F score")
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(IMG / "rf_heatmap.png", dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Excel report
# --------------------------------------------------------------------------- #
HEADER_FILL = PatternFill("solid", fgColor="1F3A5F")
HEADER_FONT = Font(bold=True, color="FFFFFF")
INPUT_FONT = Font(color="0000FF")
THIN = Side(style="thin", color="D0D5DB")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def write_df(ws, df: pd.DataFrame, start_row: int = 1, formats: dict | None = None) -> None:
    formats = formats or {}
    for j, col in enumerate(df.columns, start=1):
        c = ws.cell(row=start_row, column=j, value=col.replace("_", " ").title())
        c.fill, c.font, c.border = HEADER_FILL, HEADER_FONT, BORDER
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for i, row in enumerate(df.itertuples(index=False), start=start_row + 1):
        for j, v in enumerate(row, start=1):
            if isinstance(v, pd.Timestamp):
                v = v.to_pydatetime()
            elif isinstance(v, (np.integer,)):
                v = int(v)
            elif isinstance(v, (np.floating,)):
                v = float(v)
            c = ws.cell(row=i, column=j, value=v)
            c.border = BORDER
            fmt = formats.get(df.columns[j - 1])
            if fmt:
                c.number_format = fmt
    for j, col in enumerate(df.columns, start=1):
        width = max(len(str(col)), *(len(str(v)) for v in df[col].head(200))) + 3
        ws.column_dimensions[get_column_letter(j)].width = min(max(width, 12), 30)
    ws.freeze_panes = ws.cell(row=start_row + 1, column=1)


def build_excel(rfm, summary, cross_sell, categories) -> None:
    XLSX.parent.mkdir(exist_ok=True)
    wb = Workbook()

    # ---- Segment Summary ----
    ws = wb.active
    ws.title = "Segment Summary"
    ws["A1"] = "RFM Segment Summary"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Snapshot date: {SNAPSHOT_DATE.date()}  |  Customers: {len(rfm):,}"
    ws["A2"].font = Font(italic=True, color="666666")
    write_df(ws, summary, start_row=4, formats={
        "avg_recency_days": "0.0", "avg_frequency": "0.0", "avg_monetary": "#,##0.00",
        "total_revenue": "#,##0", "avg_order_value": "#,##0.00", "repeat_rate": "0.0%",
        "active_90d_rate": "0.0%", "customer_share": "0.0%", "revenue_share": "0.0%",
        "customers": "#,##0",
    })
    ws.freeze_panes = "B5"
    n = len(summary)
    # live totals row
    tr = 5 + n
    ws.cell(row=tr, column=1, value="Total").font = Font(bold=True)
    ws.cell(row=tr, column=2, value=f"=SUM(B5:B{tr-1})").number_format = "#,##0"
    ws.cell(row=tr, column=6, value=f"=SUM(F5:F{tr-1})").number_format = "#,##0"
    for col in (2, 6):
        ws.cell(row=tr, column=col).font = Font(bold=True)

    chart = BarChart()
    chart.type = "col"
    chart.title = "Revenue by segment"
    chart.y_axis.title = "Revenue"
    chart.add_data(Reference(ws, min_col=6, min_row=4, max_row=4 + n), titles_from_data=True)
    chart.set_categories(Reference(ws, min_col=1, min_row=5, max_row=4 + n))
    chart.legend = None
    chart.height, chart.width = 8, 16
    ws.add_chart(chart, f"A{tr + 3}")

    # ---- Customer RFM ----
    ws2 = wb.create_sheet("Customer RFM")
    cols = ["customer_id", "segment", "recency_days", "frequency", "monetary",
            "avg_order_value", "r_score", "f_score", "m_score", "rfm_score",
            "last_purchase", "city", "acquisition_channel"]
    write_df(ws2, rfm[cols].sort_values(["segment", "monetary"], ascending=[True, False]),
             formats={"monetary": "#,##0.00", "avg_order_value": "#,##0.00",
                      "last_purchase": "yyyy-mm-dd"})
    ws2.auto_filter.ref = ws2.dimensions

    # ---- Cross-sell ----
    ws3 = wb.create_sheet("Cross-Sell Gaps")
    write_df(ws3, cross_sell, formats={"penetration": "0.0%", "customers_bought": "#,##0",
                                       "customers_not_bought": "#,##0"})

    # ---- Category mix ----
    ws4 = wb.create_sheet("Category by Segment")
    write_df(ws4, categories, formats={"revenue": "#,##0", "revenue_share_in_segment": "0.0%"})

    # ---- Campaign ROI model (formulas; blue = editable assumption) ----
    ws5 = wb.create_sheet("Campaign ROI Model")
    ws5["A1"] = "Campaign ROI model (illustrative - change blue cells to your own assumptions)"
    ws5["A1"].font = Font(bold=True, size=13)
    heads = ["Segment", "Campaign", "Customers Targeted", "Cost per Contact",
             "Response Rate", "Avg Order Value", "Orders per Responder",
             "Campaign Cost", "Responders", "Incremental Revenue", "Net Return", "ROI"]
    for j, h in enumerate(heads, 1):
        c = ws5.cell(row=3, column=j, value=h)
        c.fill, c.font, c.border = HEADER_FILL, HEADER_FONT, BORDER
        c.alignment = Alignment(horizontal="center", wrap_text=True)

    s = summary.set_index("segment")
    plan = [
        ("Champions", "VIP early access + referral", 0.50, 0.12, 1.6),
        ("Loyal Customers", "Cross-sell bundles + loyalty points", 0.40, 0.08, 1.3),
        ("At-Risk Customers", "Win-back offer + reminder sequence", 0.60, 0.05, 1.2),
        ("Lost Customers", "Low-cost reactivation email", 0.08, 0.015, 1.0),
    ]
    for i, (seg, camp, cpc, resp, opr) in enumerate(plan, start=4):
        ws5.cell(row=i, column=1, value=seg)
        ws5.cell(row=i, column=2, value=camp)
        ws5.cell(row=i, column=3, value=int(s.loc[seg, "customers"]))
        ws5.cell(row=i, column=4, value=cpc).font = INPUT_FONT
        ws5.cell(row=i, column=5, value=resp).font = INPUT_FONT
        ws5.cell(row=i, column=6, value=float(round(s.loc[seg, "avg_order_value"], 2))).font = INPUT_FONT
        ws5.cell(row=i, column=7, value=opr).font = INPUT_FONT
        ws5.cell(row=i, column=8, value=f"=C{i}*D{i}")
        ws5.cell(row=i, column=9, value=f"=C{i}*E{i}")
        ws5.cell(row=i, column=10, value=f"=I{i}*F{i}*G{i}")
        ws5.cell(row=i, column=11, value=f"=J{i}-H{i}")
        ws5.cell(row=i, column=12, value=f"=IF(H{i}=0,0,K{i}/H{i})")
        for col in range(1, 13):
            ws5.cell(row=i, column=col).border = BORDER
        ws5.cell(row=i, column=4).number_format = "0.000"
        ws5.cell(row=i, column=5).number_format = "0.0%"
        ws5.cell(row=i, column=6).number_format = "#,##0.00"
        for col in (8, 10, 11):
            ws5.cell(row=i, column=col).number_format = "#,##0"
        ws5.cell(row=i, column=12).number_format = "0.0x"
    ws5.cell(row=8, column=1, value="Total").font = Font(bold=True)
    for col, L in ((3, "C"), (8, "H"), (9, "I"), (10, "J"), (11, "K")):
        c = ws5.cell(row=8, column=col, value=f"=SUM({L}4:{L}7)")
        c.font = Font(bold=True)
        c.number_format = "#,##0"
    ws5.cell(row=8, column=12, value="=IF(H8=0,0,K8/H8)").number_format = "0.0x"
    ws5.cell(row=8, column=12).font = Font(bold=True)
    ws5["A10"] = ("Note: cost per contact, response rate and orders per responder are planning "
                  "assumptions, not measured results. Replace them with A/B-test data once "
                  "campaigns run.")
    ws5["A10"].font = Font(italic=True, color="666666")
    for j, w in enumerate([20, 36, 14, 12, 12, 14, 14, 14, 12, 16, 14, 10], 1):
        ws5.column_dimensions[get_column_letter(j)].width = w
    ws5.row_dimensions[3].height = 32

    wb.save(XLSX)


# --------------------------------------------------------------------------- #
def main() -> None:
    PROC.mkdir(parents=True, exist_ok=True)
    customers = pd.read_csv(RAW / "customers.csv", parse_dates=["signup_date"])
    txns = pd.read_csv(RAW / "transactions.csv", parse_dates=["transaction_date"])

    rfm = build_rfm(customers, txns)
    summary = segment_summary(rfm)
    monthly = monthly_segment_revenue(txns, rfm)
    categories = category_by_segment(txns, rfm)
    cross = cross_sell_gaps(txns, rfm)
    cohorts = cohort_retention(txns, rfm)

    # processed data for Power BI
    rfm.to_csv(PROC / "rfm_customers.csv", index=False)
    summary.to_csv(PROC / "segment_summary.csv", index=False)
    monthly.to_csv(PROC / "monthly_segment_revenue.csv", index=False)
    categories.to_csv(PROC / "category_by_segment.csv", index=False)
    cross.to_csv(PROC / "cross_sell_gaps.csv", index=False)
    cohorts.to_csv(PROC / "cohort_retention.csv", index=False)
    txns.merge(rfm[["customer_id", "segment"]], on="customer_id").to_csv(
        PROC / "transactions_with_segment.csv", index=False)

    make_charts(rfm, summary, monthly)
    build_excel(rfm, summary, cross, categories)

    pd.set_option("display.width", 200, "display.max_columns", 20)
    print(f"Interactions analysed: {len(txns):,} | Customers: {len(rfm):,}\n")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
