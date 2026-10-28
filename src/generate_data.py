"""
Generate a realistic synthetic e-commerce dataset for the RFM project.

Outputs (data/raw/):
  customers.csv     - one row per customer
  transactions.csv  - one row per customer interaction (purchase event), 20,000+ rows

Customers are drawn from five latent behavioural archetypes so that RFM
analysis has real structure to discover. The archetype label is NOT written
to the output files - the analysis has to recover the segments from behaviour.

Usage:
    python src/generate_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_CUSTOMERS = 3500
SNAPSHOT_DATE = pd.Timestamp("2026-10-01")  # analysis date used for recency
WINDOW_DAYS = 730                           # two years of history

CATEGORIES = {
    "Electronics": (95, 40),
    "Home & Kitchen": (60, 25),
    "Fashion": (45, 20),
    "Beauty": (30, 12),
    "Sports & Outdoors": (55, 22),
    "Books & Media": (18, 7),
}
CHANNELS = ["Web", "Mobile App", "Email Campaign", "Social Ads", "Store"]
CITIES = ["Kanpur", "Lucknow", "Delhi", "Mumbai", "Bengaluru", "Pune",
          "Hyderabad", "Chennai", "Kolkata", "Jaipur"]

# archetype: (share, orders_range, last_purchase_days_ago_range, aov_multiplier)
ARCHETYPES = {
    "champion": (0.12, (12, 28), (1, 30), 1.35),
    "loyal":    (0.22, (6, 14),  (15, 75), 1.00),
    "new":      (0.20, (1, 4),   (1, 60), 0.90),
    "at_risk":  (0.20, (4, 11),  (110, 260), 1.05),
    "lost":     (0.26, (1, 6),   (300, 700), 0.80),
}


def main() -> None:
    rng = np.random.default_rng(SEED)
    out = Path(__file__).resolve().parents[1] / "data" / "raw"
    out.mkdir(parents=True, exist_ok=True)

    names = list(ARCHETYPES)
    shares = np.array([ARCHETYPES[n][0] for n in names])
    assigned = rng.choice(names, size=N_CUSTOMERS, p=shares / shares.sum())

    cust_rows, txn_rows = [], []
    txn_id = 100000
    cat_names = list(CATEGORIES)

    for i, arch in enumerate(assigned, start=1):
        cid = f"C{i:05d}"
        _, (o_lo, o_hi), (d_lo, d_hi), aov_mult = ARCHETYPES[arch]
        n_orders = int(rng.integers(o_lo, o_hi + 1))
        last_ago = int(rng.integers(d_lo, d_hi + 1))
        last_date = SNAPSHOT_DATE - pd.Timedelta(days=last_ago)

        # tenure: earliest possible purchase is bounded by the 2-year window
        max_span = max(0, WINDOW_DAYS - last_ago)
        if arch == "new":
            max_span = min(max_span, 75)
        span = int(rng.integers(0, max_span + 1)) if n_orders > 1 else 0

        offsets = rng.integers(0, span + 1, size=n_orders - 1) if n_orders > 1 else []
        dates = sorted([last_date - pd.Timedelta(days=int(d)) for d in offsets] + [last_date])

        pref = rng.choice(cat_names, p=rng.dirichlet(np.ones(len(cat_names)) * 0.8))
        pref_channel = rng.choice(CHANNELS)
        signup = dates[0] - pd.Timedelta(days=int(rng.integers(0, 30)))

        cust_rows.append({
            "customer_id": cid,
            "signup_date": signup.date(),
            "city": rng.choice(CITIES),
            "age": int(np.clip(rng.normal(34, 9), 18, 70)),
            "gender": rng.choice(["F", "M", "Other"], p=[0.48, 0.48, 0.04]),
            "acquisition_channel": pref_channel,
        })

        for d in dates:
            cat = pref if rng.random() < 0.6 else rng.choice(cat_names)
            mean, sd = CATEGORIES[cat]
            qty = int(rng.choice([1, 1, 1, 2, 2, 3]))
            price = max(5.0, rng.normal(mean, sd) * aov_mult)
            discount = float(rng.choice([0, 0, 0, 0.05, 0.10, 0.20], ))
            amount = round(price * qty * (1 - discount), 2)
            txn_id += 1
            txn_rows.append({
                "transaction_id": f"T{txn_id}",
                "customer_id": cid,
                "transaction_date": d.date(),
                "product_category": cat,
                "quantity": qty,
                "discount_pct": discount,
                "amount": amount,
                "channel": pref_channel if rng.random() < 0.55 else rng.choice(CHANNELS),
            })

    customers = pd.DataFrame(cust_rows)
    txns = pd.DataFrame(txn_rows).sort_values("transaction_date").reset_index(drop=True)

    customers.to_csv(out / "customers.csv", index=False)
    txns.to_csv(out / "transactions.csv", index=False)

    print(f"customers.csv     : {len(customers):,} rows")
    print(f"transactions.csv  : {len(txns):,} rows")
    print(f"date range        : {txns.transaction_date.min()} -> {txns.transaction_date.max()}")
    print(f"total revenue     : {txns.amount.sum():,.2f}")


if __name__ == "__main__":
    main()
