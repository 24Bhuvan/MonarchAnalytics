"""
revenue_leak_detector.py
========================
Monarch Analytics — Revenue Leak Detection Engine

Rule-based system that flags business problems
by comparing KPIs against industry benchmarks.
"""

import os
import json
from datetime import datetime

OUTPUT_PATH = "audit_workspace/analysis/revenue_leak_report.json"

# ── Industry Benchmarks ───────────────────────────────────────────────────────

BENCHMARKS = {
    "conversion_rate": 0.15,        # 15% lead-to-sale benchmark
    "ltv_to_cac_max_ratio": 0.40,   # CAC should not exceed 40% of LTV
    "min_retention_rate": 0.40,     # 40% minimum retention
    "min_gross_margin": 0.50,       # 50% minimum gross margin
    "min_roas": 2.0,                # 2x minimum ROAS
    "max_sales_cycle_days": 45,     # 45 days max ideal sales cycle
    "min_repeat_purchase_rate": 0.30,
}


# ── Detection Rules ───────────────────────────────────────────────────────────

def rule_sales_funnel_leak(kpis: dict) -> dict | None:
    """Rule 1: Low lead-to-sale conversion flags a sales funnel problem."""
    rate = kpis.get("sales", {}).get("lead_conversion_rate", 1.0)
    benchmark = BENCHMARKS["conversion_rate"]
    if rate < benchmark:
        shortfall = benchmark - rate
        impact = round(shortfall * kpis.get("sales", {}).get("total_revenue", 0), 2)
        return {
            "rule": "sales_funnel_leak",
            "flag": "⚠️  SALES FUNNEL LEAK",
            "description": (f"Lead-to-sale conversion rate is {rate*100:.1f}%, "
                            f"below the {benchmark*100:.0f}% benchmark."),
            "current_value": rate,
            "benchmark": benchmark,
            "impact_score": 8,
            "estimated_revenue_impact": impact,
            "recommended_action": (
                "Audit each funnel stage. Focus on lead qualification, "
                "improve demo-to-proposal conversion, and implement follow-up cadence."
            )
        }
    return None


def rule_marketing_inefficiency(kpis: dict) -> dict | None:
    """Rule 2: CAC > 40% of LTV flags unsustainable marketing spend."""
    cac = kpis.get("marketing", {}).get("customer_acquisition_cost", 0)
    ltv = kpis.get("customer", {}).get("customer_lifetime_value", 1)
    ratio = cac / ltv if ltv else 0
    threshold = BENCHMARKS["ltv_to_cac_max_ratio"]
    if ratio > threshold:
        return {
            "rule": "marketing_inefficiency",
            "flag": "⚠️  MARKETING INEFFICIENCY",
            "description": (f"CAC (₹{cac:,.0f}) is {ratio*100:.0f}% of LTV (₹{ltv:,.0f}). "
                            f"Threshold is {threshold*100:.0f}%."),
            "current_value": ratio,
            "benchmark": threshold,
            "impact_score": 9,
            "estimated_revenue_impact": round((ratio - threshold) * ltv * kpis.get("customer", {}).get("total_customers", 0), 2),
            "recommended_action": (
                "Shift budget to highest-ROAS channels. Improve organic/referral mix. "
                "Reduce paid channel dependency and optimize targeting."
            )
        }
    return None


def rule_customer_churn(kpis: dict) -> dict | None:
    """Rule 3: Low retention flags a churn problem."""
    retention = kpis.get("customer", {}).get("retention_rate", 1.0)
    threshold = BENCHMARKS["min_retention_rate"]
    if retention < threshold:
        churned = kpis.get("customer", {}).get("churned_customers", 0)
        ltv = kpis.get("customer", {}).get("customer_lifetime_value", 0)
        impact = churned * ltv
        return {
            "rule": "customer_churn_issue",
            "flag": "⚠️  CUSTOMER CHURN ISSUE",
            "description": (f"Retention rate is {retention*100:.1f}%, "
                            f"below the {threshold*100:.0f}% threshold. "
                            f"{churned} customers have churned."),
            "current_value": retention,
            "benchmark": threshold,
            "impact_score": 9,
            "estimated_revenue_impact": round(impact, 2),
            "recommended_action": (
                "Implement customer success program. Add 30/60/90 day check-ins. "
                "Launch loyalty program and monitor NPS. Identify churn triggers in exit interviews."
            )
        }
    return None


def rule_pricing_problem(kpis: dict) -> dict | None:
    """Rule 4: Low gross margin flags a pricing or cost problem."""
    margin = kpis.get("financial", {}).get("gross_margin", 1.0)
    threshold = BENCHMARKS["min_gross_margin"]
    if margin < threshold:
        rev = kpis.get("sales", {}).get("total_revenue", 0)
        impact = (threshold - margin) * rev
        return {
            "rule": "pricing_problem",
            "flag": "⚠️  PRICING / MARGIN PROBLEM",
            "description": (f"Gross margin is {margin*100:.1f}%, "
                            f"below the {threshold*100:.0f}% industry threshold."),
            "current_value": margin,
            "benchmark": threshold,
            "impact_score": 7,
            "estimated_revenue_impact": round(impact, 2),
            "recommended_action": (
                "Review pricing strategy. Identify high-cost low-margin products. "
                "Consider value-based pricing and bundle premium offerings."
            )
        }
    return None


def rule_low_roas(kpis: dict) -> dict | None:
    """Rule 5: ROAS below 2x flags ad spend waste."""
    roas = kpis.get("marketing", {}).get("return_on_ad_spend", 10.0)
    threshold = BENCHMARKS["min_roas"]
    if roas < threshold:
        spend = kpis.get("marketing", {}).get("total_marketing_spend", 0)
        return {
            "rule": "low_roas",
            "flag": "⚠️  LOW ADVERTISING RETURN",
            "description": f"ROAS is {roas:.1f}x, below the {threshold}x minimum benchmark.",
            "current_value": roas,
            "benchmark": threshold,
            "impact_score": 7,
            "estimated_revenue_impact": round((threshold - roas) * spend, 2),
            "recommended_action": (
                "Pause underperforming ad sets. Reallocate to top-performing campaigns. "
                "A/B test creatives and tighten audience targeting."
            )
        }
    return None


def rule_long_sales_cycle(kpis: dict) -> dict | None:
    """Rule 6: Sales cycle too long reduces pipeline velocity."""
    cycle = kpis.get("sales", {}).get("sales_cycle_length_days", 0)
    threshold = BENCHMARKS["max_sales_cycle_days"]
    if cycle > threshold:
        return {
            "rule": "long_sales_cycle",
            "flag": "⚠️  LONG SALES CYCLE",
            "description": f"Average sales cycle is {cycle:.0f} days, above the {threshold}-day benchmark.",
            "current_value": cycle,
            "benchmark": threshold,
            "impact_score": 5,
            "estimated_revenue_impact": 0,
            "recommended_action": (
                "Introduce sales enablement tools. Streamline proposal approval process. "
                "Define decision-maker outreach strategy to reduce deal stall time."
            )
        }
    return None


# ── Runner ────────────────────────────────────────────────────────────────────

RULES = [
    rule_sales_funnel_leak,
    rule_marketing_inefficiency,
    rule_customer_churn,
    rule_pricing_problem,
    rule_low_roas,
    rule_long_sales_cycle,
]


def run_detection(kpis: dict = None) -> dict:
    """Execute all detection rules and output a revenue leak report."""
    print("\n🚨 Running Revenue Leak Detection...")

    if kpis is None:
        kpi_path = "audit_workspace/analysis/kpi_results.json"
        if os.path.isfile(kpi_path):
            with open(kpi_path) as f:
                kpis = json.load(f)
        else:
            print("   ⚠️  KPI results not found. Run kpi_library.py first.")
            return {}

    leaks = []
    for rule_fn in RULES:
        result = rule_fn(kpis)
        if result:
            result["detected_at"] = datetime.now().isoformat()
            leaks.append(result)
            print(f"   {result['flag']} (Impact Score: {result['impact_score']}/10)")

    if not leaks:
        print("   ✅ No revenue leaks detected — business metrics are within benchmarks!")

    total_impact = sum(l.get("estimated_revenue_impact", 0) for l in leaks)

    report = {
        "generated_at": datetime.now().isoformat(),
        "total_leaks_detected": len(leaks),
        "total_estimated_revenue_impact": round(total_impact, 2),
        "leaks": sorted(leaks, key=lambda x: x["impact_score"], reverse=True),
        "benchmarks_used": BENCHMARKS,
    }

    os.makedirs("audit_workspace/analysis", exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(report, f, indent=2)

    print(f"   📋 {len(leaks)} leaks detected | Est. impact: ₹{total_impact:,.0f}")
    print(f"   ✅ Leak report saved to {OUTPUT_PATH}")

    return report


if __name__ == "__main__":
    run_detection()
