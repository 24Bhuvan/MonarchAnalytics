"""
run_full_audit.py
=================
Monarch Analytics — Master Pipeline Orchestrator

Executes the complete end-to-end audit pipeline:
  1. Validate client data
  2. Setup workspace
  3. Clean data
  4. Run analysis scripts
  5. Calculate KPIs
  6. Detect revenue leaks
  7. Generate visualizations
  8. Generate PowerPoint report
  9. Print audit checklist

Usage:
  python run_full_audit.py
"""

import sys
import os
import time
from datetime import datetime

# Add project root to path so all modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SEPARATOR = "=" * 60


def section(title):
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(f"{SEPARATOR}")


def step(msg):
    print(f"\n▶  {msg}")


def done(msg=""):
    print(f"   ✅ {msg}" if msg else "   ✅ Done")


def run():
    start_time = time.time()

    print(f"\n{'='*60}")
    print("  MONARCH ANALYTICS — FULL AUDIT PIPELINE")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    # ── Step 1: Validate Client Data ─────────────────────────────────────────
    section("STEP 1/9 — Validating Client Data")
    from validate_client_data import validate_all
    validation = validate_all()
    if not validation.get("overall_passed"):
        print("\n❌ Data validation failed. Please fix errors before proceeding.")
        print("   Check: audit_workspace/validation_report.json")
        sys.exit(1)
    done("Data validation passed")

    # ── Step 2: Setup Workspace ───────────────────────────────────────────────
    section("STEP 2/9 — Setting Up Workspace")
    from setup_workspace import setup
    setup()
    done("Workspace ready")

    # ── Step 3: Clean Data ────────────────────────────────────────────────────
    section("STEP 3/9 — Cleaning Datasets")
    from data_cleaning import run_cleaning
    run_cleaning()
    done("All datasets cleaned")

    # ── Step 4: Run Analysis Scripts ──────────────────────────────────────────
    section("STEP 4/9 — Running Analysis Scripts")

    step("Sales Analysis...")
    sys.path.insert(0, "analysis")
    from analysis.sales_analysis import run as run_sales
    sales_metrics = run_sales()

    step("Marketing Analysis...")
    from analysis.marketing_analysis import run as run_marketing
    mkt_metrics = run_marketing()

    step("Customer Analysis...")
    from analysis.customer_analysis import run as run_customers
    cust_metrics = run_customers()

    step("Revenue Driver Analysis...")
    from analysis.revenue_driver_analysis import run as run_drivers
    driver_metrics = run_drivers()

    done("All analysis scripts complete")

    # ── Step 5: Calculate KPIs ────────────────────────────────────────────────
    section("STEP 5/9 — Calculating KPIs")
    from kpi_library import calculate_all_kpis
    kpis = calculate_all_kpis()
    done("KPI calculations complete")

    # ── Step 6: Revenue Leak Detection ───────────────────────────────────────
    section("STEP 6/9 — Detecting Revenue Leaks")
    from revenue_leak_detector import run_detection
    leaks = run_detection(kpis)
    done(f"{leaks.get('total_leaks_detected', 0)} revenue leaks detected")

    # ── Step 7: Update Workflow ────────────────────────────────────────────────
    section("STEP 7/9 — Updating Audit Checklist")
    from audit_workflow import load_status, save_status, auto_complete_pipeline_tasks, print_status
    auto_complete_pipeline_tasks()
    print_status()
    done("Checklist updated")

    # ── Step 8: Generate PowerPoint Report ───────────────────────────────────
    section("STEP 8/9 — Generating PowerPoint Report")
    from generate_report import generate_report
    report_path = generate_report(kpis=kpis, leaks=leaks, drivers=driver_metrics)
    done(f"Report saved: {report_path}")

    # ── Step 9: Summary ───────────────────────────────────────────────────────
    elapsed = round(time.time() - start_time, 1)

    section("STEP 9/9 — AUDIT COMPLETE")
    s = kpis.get("sales", {})
    m = kpis.get("marketing", {})
    c = kpis.get("customer", {})

    print(f"""
  📊 AUDIT SUMMARY
  ─────────────────────────────────────────────────────
  Total Revenue Analyzed:    ₹{s.get('total_revenue', 0):>12,.0f}
  Lead-to-Sale Conversion:   {s.get('lead_conversion_rate', 0)*100:>10.1f}%
  Average Deal Value:        ₹{s.get('average_deal_value', 0):>12,.0f}
  ROAS:                      {m.get('return_on_ad_spend', 0):>12.1f}x
  CAC:                       ₹{m.get('customer_acquisition_cost', 0):>12,.0f}
  Customer LTV:              ₹{c.get('customer_lifetime_value', 0):>12,.0f}
  Retention Rate:            {c.get('retention_rate', 0)*100:>10.1f}%
  Revenue Leaks Detected:    {leaks.get('total_leaks_detected', 0):>12}
  Revenue at Risk:           ₹{leaks.get('total_estimated_revenue_impact', 0):>12,.0f}
  ─────────────────────────────────────────────────────

  📁 OUTPUT FILES
  ─────────────────────────────────────────────────────
  Cleaned Data:     audit_workspace/cleaned_data/
  Charts:           audit_workspace/visualizations/
  KPI Results:      audit_workspace/analysis/kpi_results.json
  Leak Report:      audit_workspace/analysis/revenue_leak_report.json
  Audit Report:     {report_path}
  ─────────────────────────────────────────────────────

  ⏱️  Pipeline completed in {elapsed}s

  🚀 To launch interactive dashboard:
     python dashboard_app.py
     → http://localhost:8050
{SEPARATOR}
""")


if __name__ == "__main__":
    run()
