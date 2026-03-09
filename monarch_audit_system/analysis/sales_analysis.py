"""
sales_analysis.py
=================
Monarch Analytics — Sales Funnel & Performance Analysis

Computes all sales KPIs and generates funnel charts.
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

CLEAN_DIR = "audit_workspace/cleaned_data"
VIZ_DIR = "audit_workspace/visualizations"
ANALYSIS_DIR = "audit_workspace/analysis"

# Brand colors
COLORS = ["#1B4F72", "#2E86AB", "#A8DADC", "#F4A261", "#E63946"]


def load_data():
    """Load cleaned sales data."""
    path = os.path.join(CLEAN_DIR, "sales_clean.csv")
    df = pd.read_csv(path, parse_dates=["date", "lead_date", "close_date"])
    return df


def compute_funnel_metrics(df: pd.DataFrame) -> dict:
    """Calculate key sales funnel conversion metrics."""
    total_leads = len(df)
    won = df[df["deal_stage"] == "closed_won"]
    lost = df[df["deal_stage"] == "closed_lost"]
    proposals = df[df["deal_stage"].isin(["proposal", "closed_won", "closed_lost"])]

    lead_to_proposal = len(proposals) / total_leads if total_leads else 0
    proposal_to_win = len(won) / len(proposals) if len(proposals) else 0
    lead_to_win = len(won) / total_leads if total_leads else 0

    avg_deal_value = won["revenue"].mean() if len(won) else 0
    avg_cycle = won["sales_cycle_days"].dropna().mean() if len(won) else 0

    total_revenue = won["revenue"].sum()
    pipeline_velocity = (total_revenue / avg_cycle) if avg_cycle else 0

    metrics = {
        "total_leads": total_leads,
        "proposals_sent": len(proposals),
        "deals_won": len(won),
        "deals_lost": len(lost),
        "lead_to_opportunity_conversion": round(lead_to_proposal, 4),
        "opportunity_to_sale_conversion": round(proposal_to_win, 4),
        "overall_lead_to_sale_conversion": round(lead_to_win, 4),
        "average_deal_value": round(avg_deal_value, 2),
        "average_sales_cycle_days": round(avg_cycle, 1),
        "pipeline_velocity": round(pipeline_velocity, 2),
        "total_revenue": round(total_revenue, 2),
    }
    return metrics


def plot_sales_funnel(metrics: dict):
    """Generate a visual sales funnel chart."""
    os.makedirs(VIZ_DIR, exist_ok=True)

    stages = ["Total Leads", "Proposals Sent", "Deals Won"]
    values = [metrics["total_leads"], metrics["proposals_sent"], metrics["deals_won"]]

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("#0D1B2A")
    ax.set_facecolor("#0D1B2A")

    bar_colors = ["#2E86AB", "#F4A261", "#2ECC71"]
    bars = ax.barh(stages[::-1], values[::-1], color=bar_colors, edgecolor="white", linewidth=0.5, height=0.5)

    for bar, val in zip(bars, values[::-1]):
        ax.text(bar.get_width() + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{val}", va="center", ha="left", color="white", fontsize=12, fontweight="bold")

    ax.set_title("Sales Funnel Analysis", color="white", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Count", color="white", fontsize=11)
    ax.tick_params(colors="white", labelsize=11)
    ax.spines[:].set_color("#1B4F72")
    ax.xaxis.label.set_color("white")

    # Conversion rate annotations
    conv_text = (
        f"Lead → Proposal: {metrics['lead_to_opportunity_conversion']*100:.1f}%\n"
        f"Proposal → Win: {metrics['opportunity_to_sale_conversion']*100:.1f}%\n"
        f"Overall Conversion: {metrics['overall_lead_to_sale_conversion']*100:.1f}%"
    )
    ax.text(0.98, 0.05, conv_text, transform=ax.transAxes, ha="right", va="bottom",
            color="#A8DADC", fontsize=10, bbox=dict(boxstyle="round,pad=0.4", facecolor="#1B4F72", alpha=0.8))

    plt.tight_layout()
    out_path = os.path.join(VIZ_DIR, "sales_funnel_chart.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"   📊 Saved: sales_funnel_chart.png")


def plot_revenue_trend(df: pd.DataFrame):
    """Generate monthly revenue trend chart."""
    won = df[df["deal_stage"] == "closed_won"].copy()
    monthly = won.groupby("month")["revenue"].sum().reset_index()
    monthly = monthly.sort_values("month")

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor("#0D1B2A")
    ax.set_facecolor("#0D1B2A")

    ax.plot(monthly["month"], monthly["revenue"], color="#F4A261", linewidth=2.5, marker="o",
            markersize=8, markerfacecolor="#E63946")
    ax.fill_between(range(len(monthly)), monthly["revenue"], alpha=0.15, color="#F4A261")

    ax.set_xticks(range(len(monthly)))
    ax.set_xticklabels(monthly["month"], rotation=30, ha="right", color="white")
    ax.set_title("Monthly Revenue Trend", color="white", fontsize=16, fontweight="bold", pad=15)
    ax.set_ylabel("Revenue (₹)", color="white")
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#1B4F72")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x:,.0f}"))

    plt.tight_layout()
    out_path = os.path.join(VIZ_DIR, "revenue_trend.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"   📊 Saved: revenue_trend.png")


def save_conversion_table(metrics: dict):
    """Export conversion metrics to CSV."""
    os.makedirs(ANALYSIS_DIR, exist_ok=True)
    rows = [
        {"metric": "Total Leads", "value": metrics["total_leads"], "unit": "count"},
        {"metric": "Proposals Sent", "value": metrics["proposals_sent"], "unit": "count"},
        {"metric": "Deals Won", "value": metrics["deals_won"], "unit": "count"},
        {"metric": "Lead to Opportunity Conversion", "value": f"{metrics['lead_to_opportunity_conversion']*100:.1f}%", "unit": "rate"},
        {"metric": "Opportunity to Sale Conversion", "value": f"{metrics['opportunity_to_sale_conversion']*100:.1f}%", "unit": "rate"},
        {"metric": "Overall Lead to Sale Conversion", "value": f"{metrics['overall_lead_to_sale_conversion']*100:.1f}%", "unit": "rate"},
        {"metric": "Average Deal Value", "value": f"₹{metrics['average_deal_value']:,.0f}", "unit": "currency"},
        {"metric": "Average Sales Cycle", "value": f"{metrics['average_sales_cycle_days']} days", "unit": "days"},
        {"metric": "Pipeline Velocity", "value": f"₹{metrics['pipeline_velocity']:,.0f}/day", "unit": "currency/day"},
        {"metric": "Total Revenue", "value": f"₹{metrics['total_revenue']:,.0f}", "unit": "currency"},
    ]
    pd.DataFrame(rows).to_csv(os.path.join(ANALYSIS_DIR, "conversion_table.csv"), index=False)
    print(f"   📋 Saved: conversion_table.csv")


def run():
    """Main entry point for sales analysis."""
    print("\n🔍 Running Sales Analysis...")
    df = load_data()
    metrics = compute_funnel_metrics(df)
    plot_sales_funnel(metrics)
    plot_revenue_trend(df)
    save_conversion_table(metrics)
    print(f"   ✅ Sales analysis complete. Deals won: {metrics['deals_won']}, Revenue: ₹{metrics['total_revenue']:,.0f}")
    return metrics


if __name__ == "__main__":
    run()
