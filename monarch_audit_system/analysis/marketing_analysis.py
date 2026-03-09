"""
marketing_analysis.py
=====================
Monarch Analytics — Marketing Efficiency Analysis

Computes CAC, ROAS, conversion rates and generates channel comparison charts.
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

CLEAN_DIR = "audit_workspace/cleaned_data"
VIZ_DIR = "audit_workspace/visualizations"
ANALYSIS_DIR = "audit_workspace/analysis"

CHANNEL_COLORS = {"google_ads": "#4285F4", "facebook": "#1877F2",
                  "linkedin": "#0A66C2", "email": "#F4A261", "other": "#A8DADC"}


def load_data():
    df_mkt = pd.read_csv(os.path.join(CLEAN_DIR, "marketing_clean.csv"), parse_dates=["date"])
    df_cust = pd.read_csv(os.path.join(CLEAN_DIR, "customers_clean.csv"))
    return df_mkt, df_cust


def compute_metrics(df_mkt: pd.DataFrame, df_cust: pd.DataFrame) -> dict:
    """Calculate marketing efficiency metrics."""
    total_spend = df_mkt["spend"].sum()
    total_revenue = df_mkt["revenue_generated"].sum()
    total_conversions = df_mkt["conversions"].sum()
    total_customers = len(df_cust)

    cac = total_spend / total_customers if total_customers else 0
    roas = total_revenue / total_spend if total_spend else 0
    conversion_rate = df_mkt["conversion_rate"].mean()

    avg_order = df_cust["avg_order_value"].mean()
    avg_orders = df_cust["total_orders"].mean()
    retention_period = 2.0  # Assumed years
    avg_ltv = avg_order * avg_orders * retention_period

    # By channel
    by_channel = df_mkt.groupby("channel").agg(
        spend=("spend", "sum"),
        conversions=("conversions", "sum"),
        revenue=("revenue_generated", "sum"),
        clicks=("clicks", "sum"),
    ).reset_index()
    by_channel["roas"] = (by_channel["revenue"] / by_channel["spend"].replace(0, np.nan)).round(2)
    by_channel["cpc"] = (by_channel["spend"] / by_channel["clicks"].replace(0, np.nan)).round(2)
    by_channel["conv_rate"] = (by_channel["conversions"] / by_channel["clicks"].replace(0, np.nan)).round(4)
    by_channel["cac_est"] = (by_channel["spend"] / by_channel["conversions"].replace(0, np.nan)).round(2)

    return {
        "total_spend": round(total_spend, 2),
        "total_revenue_generated": round(total_revenue, 2),
        "total_conversions": int(total_conversions),
        "overall_cac": round(cac, 2),
        "overall_roas": round(roas, 2),
        "average_conversion_rate": round(conversion_rate, 4),
        "estimated_ltv": round(avg_ltv, 2),
        "ltv_to_cac_ratio": round(avg_ltv / cac, 2) if cac else 0,
        "by_channel": by_channel.to_dict(orient="records"),
    }


def plot_channel_performance(df_mkt: pd.DataFrame):
    """Bar chart: ROAS and spend by channel."""
    by_ch = df_mkt.groupby("channel").agg(
        spend=("spend", "sum"),
        revenue=("revenue_generated", "sum")
    ).reset_index()
    by_ch["roas"] = (by_ch["revenue"] / by_ch["spend"]).round(2)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor("#0D1B2A")

    colors = [CHANNEL_COLORS.get(ch, "#A8DADC") for ch in by_ch["channel"]]

    # Spend by channel
    ax1 = axes[0]
    ax1.set_facecolor("#0D1B2A")
    bars = ax1.bar(by_ch["channel"], by_ch["spend"], color=colors, edgecolor="white", linewidth=0.5)
    ax1.set_title("Marketing Spend by Channel", color="white", fontsize=13, fontweight="bold")
    ax1.set_ylabel("Spend (₹)", color="white")
    ax1.tick_params(colors="white", axis="both")
    ax1.spines[:].set_color("#1B4F72")
    for bar, val in zip(bars, by_ch["spend"]):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(by_ch["spend"])*0.01,
                 f"₹{val:,.0f}", ha="center", va="bottom", color="white", fontsize=9)

    # ROAS by channel
    ax2 = axes[1]
    ax2.set_facecolor("#0D1B2A")
    bars2 = ax2.bar(by_ch["channel"], by_ch["roas"], color=colors, edgecolor="white", linewidth=0.5)
    ax2.axhline(y=2.0, color="#E63946", linestyle="--", linewidth=1.5, label="ROAS Target (2x)")
    ax2.set_title("ROAS by Channel", color="white", fontsize=13, fontweight="bold")
    ax2.set_ylabel("ROAS", color="white")
    ax2.tick_params(colors="white", axis="both")
    ax2.spines[:].set_color("#1B4F72")
    ax2.legend(facecolor="#1B4F72", labelcolor="white", fontsize=9)
    for bar, val in zip(bars2, by_ch["roas"]):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                 f"{val:.1f}x", ha="center", va="bottom", color="white", fontsize=9)

    plt.tight_layout()
    out_path = os.path.join(VIZ_DIR, "channel_performance.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print("   📊 Saved: channel_performance.png")


def plot_cac_vs_ltv(metrics: dict):
    """CAC vs LTV comparison chart."""
    cac = metrics["overall_cac"]
    ltv = metrics["estimated_ltv"]

    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor("#0D1B2A")
    ax.set_facecolor("#0D1B2A")

    categories = ["CAC", "LTV", "LTV:CAC Ratio"]
    values_plot = [cac, ltv, metrics["ltv_to_cac_ratio"] * 1000]
    bar_colors = ["#E63946", "#2ECC71", "#F4A261"]

    bars = ax.bar(["Customer Acquisition Cost", "Lifetime Value"], [cac, ltv],
                  color=["#E63946", "#2ECC71"], edgecolor="white", linewidth=0.5, width=0.4)

    for bar, val in zip(bars, [cac, ltv]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(cac, ltv)*0.02,
                f"₹{val:,.0f}", ha="center", va="bottom", color="white", fontsize=13, fontweight="bold")

    ratio_text = f"LTV:CAC Ratio = {metrics['ltv_to_cac_ratio']:.1f}x\n(Target: ≥ 3x)"
    ax.text(0.98, 0.92, ratio_text, transform=ax.transAxes, ha="right", va="top",
            color="#A8DADC", fontsize=11, bbox=dict(boxstyle="round,pad=0.4", facecolor="#1B4F72", alpha=0.8))

    ax.set_title("CAC vs Customer Lifetime Value", color="white", fontsize=15, fontweight="bold", pad=15)
    ax.set_ylabel("Value (₹)", color="white")
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#1B4F72")

    plt.tight_layout()
    out_path = os.path.join(VIZ_DIR, "cac_vs_ltv.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print("   📊 Saved: cac_vs_ltv.png")


def plot_marketing_funnel(df_mkt: pd.DataFrame):
    """Marketing conversion funnel."""
    totals = {
        "Impressions": df_mkt["impressions"].sum(),
        "Clicks": df_mkt["clicks"].sum(),
        "Conversions": df_mkt["conversions"].sum(),
    }

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("#0D1B2A")
    ax.set_facecolor("#0D1B2A")

    stages = list(totals.keys())
    values = list(totals.values())
    funnel_colors = ["#2E86AB", "#F4A261", "#2ECC71"]

    bars = ax.barh(stages[::-1], values[::-1], color=funnel_colors, height=0.5,
                   edgecolor="white", linewidth=0.5)

    for bar, val in zip(bars, values[::-1]):
        ax.text(bar.get_width() + max(values)*0.005, bar.get_y() + bar.get_height()/2,
                f"{val:,}", va="center", color="white", fontsize=12, fontweight="bold")

    ctr = totals["Clicks"] / totals["Impressions"] * 100
    cvr = totals["Conversions"] / totals["Clicks"] * 100
    ax.text(0.98, 0.08, f"CTR: {ctr:.2f}%  |  CVR: {cvr:.2f}%",
            transform=ax.transAxes, ha="right", color="#A8DADC", fontsize=11,
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#1B4F72", alpha=0.8))

    ax.set_title("Marketing Conversion Funnel", color="white", fontsize=15, fontweight="bold", pad=15)
    ax.tick_params(colors="white", labelsize=11)
    ax.spines[:].set_color("#1B4F72")

    plt.tight_layout()
    out_path = os.path.join(VIZ_DIR, "marketing_funnel.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print("   📊 Saved: marketing_funnel.png")


def run():
    """Main entry point for marketing analysis."""
    print("\n📣 Running Marketing Analysis...")
    os.makedirs(VIZ_DIR, exist_ok=True)
    df_mkt, df_cust = load_data()
    metrics = compute_metrics(df_mkt, df_cust)
    plot_channel_performance(df_mkt)
    plot_cac_vs_ltv(metrics)
    plot_marketing_funnel(df_mkt)
    print(f"   ✅ Marketing analysis complete. ROAS: {metrics['overall_roas']}x, CAC: ₹{metrics['overall_cac']:,.0f}")
    return metrics


if __name__ == "__main__":
    run()
