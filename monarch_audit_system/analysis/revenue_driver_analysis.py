"""
revenue_driver_analysis.py
==========================
Monarch Analytics — Revenue Driver & Pareto Analysis
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CLEAN_DIR = "audit_workspace/cleaned_data"
VIZ_DIR = "audit_workspace/visualizations"
ANALYSIS_DIR = "audit_workspace/analysis"


def load_data():
    sales = pd.read_csv(os.path.join(CLEAN_DIR, "sales_clean.csv"), parse_dates=["date"])
    customers = pd.read_csv(os.path.join(CLEAN_DIR, "customers_clean.csv"))
    products = pd.read_csv(os.path.join(CLEAN_DIR, "products_clean.csv"))
    return sales, customers, products


def compute_drivers(sales: pd.DataFrame, customers: pd.DataFrame) -> dict:
    won = sales[sales["deal_stage"] == "closed_won"]

    top_products = won.groupby("product_id")["revenue"].sum().sort_values(ascending=False)
    top_channels = won.groupby("channel")["revenue"].sum().sort_values(ascending=False)

    cust_rev = customers.sort_values("total_revenue", ascending=False)
    top_20pct_idx = max(1, int(len(cust_rev) * 0.2))
    top_cust_rev = cust_rev.head(top_20pct_idx)["total_revenue"].sum()
    total_cust_rev = cust_rev["total_revenue"].sum()
    pareto_pct = (top_cust_rev / total_cust_rev * 100) if total_cust_rev else 0

    return {
        "top_products": top_products.head(5).to_dict(),
        "top_channels": top_channels.to_dict(),
        "pareto_top_20pct_revenue_share": round(pareto_pct, 1),
        "total_revenue": round(won["revenue"].sum(), 2),
    }


def plot_pareto(customers: pd.DataFrame):
    """Pareto chart showing top customers driving revenue."""
    cust_sorted = customers.sort_values("total_revenue", ascending=False).reset_index(drop=True)
    cust_sorted["cumulative_pct"] = (cust_sorted["total_revenue"].cumsum() /
                                      cust_sorted["total_revenue"].sum() * 100)
    cust_sorted["customer_pct"] = (np.arange(1, len(cust_sorted) + 1) / len(cust_sorted) * 100)

    fig, ax1 = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor("#0D1B2A")
    ax1.set_facecolor("#0D1B2A")

    ax1.bar(cust_sorted.index, cust_sorted["total_revenue"], color="#2E86AB",
            edgecolor="none", alpha=0.8, label="Revenue per Customer")
    ax1.set_ylabel("Revenue (₹)", color="#2E86AB")
    ax1.tick_params(axis="y", colors="#2E86AB")
    ax1.tick_params(axis="x", colors="white")
    ax1.spines[:].set_color("#1B4F72")

    ax2 = ax1.twinx()
    ax2.set_facecolor("#0D1B2A")
    ax2.plot(cust_sorted.index, cust_sorted["cumulative_pct"], color="#F4A261",
             linewidth=2.5, label="Cumulative Revenue %")
    ax2.axhline(y=80, color="#E63946", linestyle="--", linewidth=1.5, alpha=0.7)
    ax2.set_ylabel("Cumulative Revenue %", color="#F4A261")
    ax2.tick_params(axis="y", colors="#F4A261")
    ax2.spines[:].set_color("#1B4F72")

    ax1.set_title("Pareto Revenue Analysis — Top Customers Driving Revenue",
                  color="white", fontsize=14, fontweight="bold", pad=15)
    ax1.set_xlabel("Customers (ranked by revenue)", color="white")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, facecolor="#1B4F72", labelcolor="white", loc="center right")

    plt.tight_layout()
    out = os.path.join(VIZ_DIR, "pareto_revenue_chart.png")
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print("   📊 Saved: pareto_revenue_chart.png")


def run():
    print("\n💰 Running Revenue Driver Analysis...")
    os.makedirs(VIZ_DIR, exist_ok=True)
    sales, customers, products = load_data()
    drivers = compute_drivers(sales, customers)
    plot_pareto(customers)
    print(f"   ✅ Revenue driver analysis complete. Top 20% customers = {drivers['pareto_top_20pct_revenue_share']}% of revenue")
    return drivers


if __name__ == "__main__":
    run()
