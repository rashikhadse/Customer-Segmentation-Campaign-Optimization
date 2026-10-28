"""
Build a local SQLite database from the raw CSVs, run the SQL scripts, and
cross-check the SQL segmentation against the Python pipeline.

Usage:
    python src/load_to_sqlite.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "customer_segmentation.db"


def main() -> None:
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)

    con.executescript((ROOT / "sql" / "01_schema.sql").read_text())
    for name in ("customers", "transactions"):
        df = pd.read_csv(ROOT / "data" / "raw" / f"{name}.csv")
        df.to_sql(name, con, if_exists="append", index=False)

    # create the view (statement 1) and ignore the trailing SELECT
    script = (ROOT / "sql" / "02_rfm_segmentation.sql").read_text()
    view_sql = script.split("-- ----------")[0]
    con.executescript(view_sql)

    sql_seg = pd.read_sql("SELECT customer_id, r_score, f_score, m_score, segment "
                          "FROM vw_rfm_segments ORDER BY customer_id", con)
    py_seg = pd.read_csv(ROOT / "data" / "processed" / "rfm_customers.csv")[
        ["customer_id", "r_score", "f_score", "m_score", "segment"]
    ].sort_values("customer_id").reset_index(drop=True)

    same = sql_seg.equals(py_seg)
    print(f"SQL view rows: {len(sql_seg):,} | Python rows: {len(py_seg):,}")
    print("SQL and Python segmentation identical:", same)
    if not same:
        diff = (sql_seg != py_seg).any(axis=1).sum()
        print(f"  mismatching rows: {diff}")

    print("\nSQL segment summary:")
    print(pd.read_sql(
        "SELECT segment, COUNT(*) customers, ROUND(SUM(monetary),2) revenue "
        "FROM vw_rfm_segments GROUP BY segment ORDER BY revenue DESC", con
    ).to_string(index=False))
    con.close()


if __name__ == "__main__":
    main()
