"""
customer_analysis.py
====================
Monarch Analytics — Customer Behaviour & LTV Analysis
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CLEAN_DIR = "audit_workspace/cleaned_data"
VIZ_DIR = "audit_workspace/visualizations"


def load_data():
    df = pd.read_csv(os.path.join(CLEAN_DIR, "customers_clean.csv"),
                     parse_dates=["first_purchase_date", "last_purchase_date"])
    return df


def compute_metrics(df: pd.DataFrame) -> dict:
    """Compute all customer health metrics."""
    total = len(df)
    churned = df["is_churned"].sum()
    retention_rate = 1 - (churned / total) if total else 0
    churn_rate = churned / total if total else 0
    repeat_buyers = df[df["total_orders"] > 1]
    repeat_purchase_rate = len(repeat_buyers) / total if total else 0

    avg_order_value = df["avg_order_value"].mean()
    avg_orders = df["total_orders"].mean()
    retention_period = 2.0  # years
    ltv = avg_order_value * avg_orders * retention_period

    return {
        "total_customers": total,
        "churned_customers": int(churned),
        "active_customers": int(total - churned),
        "retention_rate": round(retention_rate, 4),
        "churn_rate": round(churn_rate, 4),
        "repeat_purchase_rate": round(repeat_purchase_rate, 4),
        "average_order_value": round(avg_order_value, 2),
        "average_orders_per_customer": round(avg_orders, 2),
        "customer_lifetime_value": round(ltv, 2),
        "retention_period_years": retention_period,
    }


def plot_ltv_distribution(df: pd.DataFrame):
    """Histogram of customer total revenue (LTV proxy)."""
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#0D1B2A")
    ax.set_facecolor("#0D1B2A")

    ax.hist(df["total_revenue"], bins=15, color="#2E86AB", edgecolor="white", linewidth=0.5, alpha=0.85)
    ax.axvline(df["total_revenue"].mean(), color="#F4A261", linestyle="--", linewidth=2,
               label=f"Mean: ₹{df['total_revenue'].mean():,.0f}")
    ax.axvline(df["total_revenue"].median(), color="#2ECC71", linestyle="--", linewidth=2,
               label=f"Median: ₹{df['total_revenue'].median():,.0f}")

    ax.set_title("Customer Lifetime Value Distribution", color="white", fontsize=14, fontweight="bold")
    ax.set_xlabel("Total Revenue per Customer (₹)", color="white")
    ax.set_ylabel("Number of Customers", color="white")
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#1B4F72")
    ax.legend(facecolor="#1B4F72", labelcolor="white")

    plt.tight_layout()
    out = os.path.join(VIZ_DIR, "ltv_distribution.png")
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print("   📊 Saved: ltv_distribution.png")


def plot_segment_revenue(df: pd.DataFrame):
    """Revenue breakdown by customer segment."""
    seg = df.groupby("segment")["total_revenue"].sum().sort_values(ascending=False).reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.patch.set_facecolor("#0D1B2A")

    seg_colors = {"enterprise": "#2ECC71", "mid_market": "#F4A261", "smb": "#E63946"}
    colors = [seg_colors.get(s, "#A8DADC") for s in seg["segment"]]

    # Bar chart
    ax1 = axes[0]
    ax1.set_facecolor("#0D1B2A")
    bars = ax1.bar(seg["segment"], seg["total_revenue"], color=colors, edgecolor="white", linewidth=0.5)
    for bar, val in zip(bars, seg["total_revenue"]):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(seg["total_revenue"])*0.02,
                 f"₹{val:,.0f}", ha="center", va="bottom", color="white", fontsize=10, fontweight="bold")
    ax1.set_title("Revenue by Customer Segment", color="white", fontsize=13, fontweight="bold")
    ax1.set_ylabel("Total Revenue (₹)", color="white")
    ax1.tick_params(colors="white")
    ax1.spines[:].set_color("#1B4F72")

    # Pie chart
    ax2 = axes[1]
    ax2.set_facecolor("#0D1B2A")
    wedges, texts, autotexts = ax2.pie(seg["total_revenue"], labels=seg["segment"],
                                        colors=colors, autopct="%1.1f%%", startangle=90,
                                        textprops={"color": "white"})
    for at in autotexts:
        at.set_color("white")
        at.set_fontweight("bold")
    ax2.set_title("Revenue Share by Segment", color="white", fontsize=13, fontweight="bold")

    plt.tight_layout()
    out = os.path.join(VIZ_DIR, "customer_cohort_retention.png")
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print("   📊 Saved: customer_cohort_retention.png")


def run():
    print("\n👥 Running Customer Analysis...")
    os.makedirs(VIZ_DIR, exist_ok=True)
    df = load_data()
    metrics = compute_metrics(df)
    plot_ltv_distribution(df)
    plot_segment_revenue(df)
    print(f"   ✅ Customer analysis complete. LTV: ₹{metrics['customer_lifetime_value']:,.0f}, Retention: {metrics['retention_rate']*100:.1f}%")
    return metrics


if __name__ == "__main__":
    run()
