"""
kpi_library.py
==============
Monarch Analytics — KPI Calculation Library

Centralized module to calculate all 30+ KPIs
and return them as structured JSON.
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

CLEAN_DIR = "audit_workspace/cleaned_data"


def load_all_data() -> dict:
    """Load all cleaned datasets into a dictionary."""
    datasets = {}
    files = {
        "sales": "sales_clean.csv",
        "marketing": "marketing_clean.csv",
        "customers": "customers_clean.csv",
        "products": "products_clean.csv",
        "operations": "operations_clean.csv",
    }
    for key, fname in files.items():
        path = os.path.join(CLEAN_DIR, fname)
        if os.path.isfile(path):
            datasets[key] = pd.read_csv(path)
    return datasets


# ── Sales KPIs ────────────────────────────────────────────────────────────────

def calc_sales_kpis(sales: pd.DataFrame) -> dict:
    """Calculate all sales funnel KPIs."""
    won = sales[sales["deal_stage"] == "closed_won"]
    proposals = sales[sales["deal_stage"].isin(["proposal", "closed_won", "closed_lost"])]

    total_leads = len(sales)
    deals_won = len(won)

    lead_conv = deals_won / total_leads if total_leads else 0
    opp_conv = deals_won / len(proposals) if len(proposals) else 0
    avg_deal = won["revenue"].mean() if deals_won else 0

    sales["sales_cycle_days"] = pd.to_numeric(
        pd.to_datetime(sales.get("close_date", pd.NaT), errors="coerce").sub(
            pd.to_datetime(sales.get("lead_date", pd.NaT), errors="coerce")
        ).dt.days, errors="coerce"
    )
    avg_cycle = sales.loc[sales["deal_stage"] == "closed_won", "sales_cycle_days"].dropna().mean()
    avg_cycle = avg_cycle if not pd.isna(avg_cycle) else 0
    total_rev = won["revenue"].sum()
    pipeline_vel = total_rev / avg_cycle if avg_cycle else 0

    return {
        "lead_conversion_rate": round(lead_conv, 4),
        "opportunity_conversion_rate": round(opp_conv, 4),
        "average_deal_value": round(float(avg_deal), 2),
        "sales_cycle_length_days": round(float(avg_cycle), 1),
        "pipeline_velocity": round(float(pipeline_vel), 2),
        "total_deals_won": deals_won,
        "total_revenue": round(float(total_rev), 2),
        "win_rate": round(lead_conv, 4),
    }


# ── Marketing KPIs ────────────────────────────────────────────────────────────

def calc_marketing_kpis(marketing: pd.DataFrame, customers: pd.DataFrame) -> dict:
    """Calculate all marketing efficiency KPIs."""
    total_spend = marketing["spend"].sum()
    total_rev = marketing["revenue_generated"].sum()
    total_clicks = marketing["clicks"].sum()
    total_conv = marketing["conversions"].sum()
    total_cust = len(customers)

    cac = total_spend / total_cust if total_cust else 0
    roas = total_rev / total_spend if total_spend else 0
    cvr = total_conv / total_clicks if total_clicks else 0
    funnel_dropoff = 1 - cvr

    return {
        "customer_acquisition_cost": round(float(cac), 2),
        "return_on_ad_spend": round(float(roas), 2),
        "channel_conversion_rate": round(float(cvr), 4),
        "funnel_dropoff_rate": round(float(funnel_dropoff), 4),
        "total_marketing_spend": round(float(total_spend), 2),
        "marketing_revenue_generated": round(float(total_rev), 2),
        "cost_per_click": round(float(total_spend / total_clicks if total_clicks else 0), 2),
        "total_conversions": int(total_conv),
    }


# ── Financial KPIs ────────────────────────────────────────────────────────────

def calc_financial_kpis(products: pd.DataFrame, customers: pd.DataFrame, marketing: pd.DataFrame) -> dict:
    """Calculate financial health KPIs."""
    gross_margin = products["margin"].mean()
    total_rev = customers["total_revenue"].sum()
    total_spend = marketing["spend"].sum()
    total_cust = len(customers)

    contribution_margin = gross_margin - (total_spend / total_rev if total_rev else 0)
    cpa = total_spend / total_cust if total_cust else 0
    unit_economics = total_rev / total_cust if total_cust else 0

    return {
        "gross_margin": round(float(gross_margin), 4),
        "contribution_margin": round(float(contribution_margin), 4),
        "unit_economics_revenue_per_customer": round(float(unit_economics), 2),
        "cost_per_acquisition": round(float(cpa), 2),
        "avg_product_price": round(float(products["price"].mean()), 2),
        "avg_product_cost": round(float(products["cost"].mean()), 2),
    }


# ── Customer KPIs ─────────────────────────────────────────────────────────────

def calc_customer_kpis(customers: pd.DataFrame) -> dict:
    """Calculate customer lifetime and retention KPIs."""
    total = len(customers)
    churned = customers["is_churned"].sum() if "is_churned" in customers.columns else 0
    retention = 1 - (churned / total) if total else 0
    churn_rate = churned / total if total else 0
    repeat_rate = len(customers[customers["total_orders"] > 1]) / total if total else 0

    avg_order_val = customers["avg_order_value"].mean() if "avg_order_value" in customers.columns else customers["total_revenue"].mean()
    avg_orders = customers["total_orders"].mean()
    retention_period = 2.0
    ltv = avg_order_val * avg_orders * retention_period

    return {
        "customer_lifetime_value": round(float(ltv), 2),
        "churn_rate": round(float(churn_rate), 4),
        "retention_rate": round(float(retention), 4),
        "repeat_purchase_rate": round(float(repeat_rate), 4),
        "average_order_value": round(float(avg_order_val), 2),
        "average_orders_per_customer": round(float(avg_orders), 2),
        "total_customers": int(total),
        "active_customers": int(total - churned),
        "churned_customers": int(churned),
    }


# ── Master KPI Calculator ─────────────────────────────────────────────────────

def calculate_all_kpis() -> dict:
    """
    Run all KPI calculations and return structured JSON.
    Also saves results to audit_workspace/analysis/kpi_results.json
    """
    print("\n📐 Calculating KPIs...")
    datasets = load_all_data()

    kpis = {
        "calculated_at": datetime.now().isoformat(),
        "sales": calc_sales_kpis(datasets["sales"]) if "sales" in datasets else {},
        "marketing": calc_marketing_kpis(datasets["marketing"], datasets["customers"])
                     if "marketing" in datasets and "customers" in datasets else {},
        "financial": calc_financial_kpis(datasets["products"], datasets["customers"], datasets["marketing"])
                     if all(k in datasets for k in ["products", "customers", "marketing"]) else {},
        "customer": calc_customer_kpis(datasets["customers"]) if "customers" in datasets else {},
    }

    # Save to file
    os.makedirs("audit_workspace/analysis", exist_ok=True)
    out_path = "audit_workspace/analysis/kpi_results.json"
    with open(out_path, "w") as f:
        json.dump(kpis, f, indent=2)

    # Print summary
    s = kpis.get("sales", {})
    m = kpis.get("marketing", {})
    c = kpis.get("customer", {})
    f = kpis.get("financial", {})

    print(f"   💼 Sales — Conversion: {s.get('lead_conversion_rate',0)*100:.1f}%, Avg Deal: ₹{s.get('average_deal_value',0):,.0f}")
    print(f"   📣 Marketing — CAC: ₹{m.get('customer_acquisition_cost',0):,.0f}, ROAS: {m.get('return_on_ad_spend',0):.1f}x")
    print(f"   👥 Customer — LTV: ₹{c.get('customer_lifetime_value',0):,.0f}, Churn: {c.get('churn_rate',0)*100:.1f}%")
    print(f"   💰 Finance — Gross Margin: {f.get('gross_margin',0)*100:.1f}%")
    print(f"   ✅ KPIs saved to {out_path}")

    return kpis


if __name__ == "__main__":
    calculate_all_kpis()
