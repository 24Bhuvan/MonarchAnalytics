# 👑 Monarch Analytics — Business Performance Audit System

A fully automated, end-to-end business audit pipeline that converts raw client data into insights, dashboards, and a branded PowerPoint report.

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install pandas numpy matplotlib seaborn python-pptx plotly dash sqlalchemy

# 2. Add your client data to client_data_intake/
#    (Replace the sample CSV files with real client data)

# 3. Run the full audit pipeline
python run_full_audit.py

# 4. Launch interactive dashboard
python dashboard_app.py
# → Open http://localhost:8050
```

---

## 📁 Project Structure

```
monarch_audit_system/
│
├── client_data_intake/          # Client data templates & instructions
│   ├── 01_sales_data_template.csv
│   ├── 02_marketing_spend_template.csv
│   ├── 03_customer_data_template.csv
│   ├── 04_product_catalog_template.csv
│   ├── 05_operational_metrics_template.csv
│   └── instructions.txt
│
├── audit_workspace/             # Auto-created during pipeline run
│   ├── data/                    # Raw client data (copied from intake)
│   ├── cleaned_data/            # Cleaned & enriched datasets
│   ├── analysis/                # KPI results, conversion tables
│   ├── visualizations/          # PNG charts for report
│   ├── report_outputs/          # Final PowerPoint report
│   └── dashboards/
│
├── analysis/                    # Diagnostic analysis scripts
│   ├── sales_analysis.py
│   ├── marketing_analysis.py
│   ├── customer_analysis.py
│   └── revenue_driver_analysis.py
│
├── validate_client_data.py      # Step 1: Data validation
├── setup_workspace.py           # Step 2: Workspace setup + SQLite init
├── data_cleaning.py             # Step 3: Cleaning pipeline
├── kpi_library.py               # Step 5: All KPI calculations
├── revenue_leak_detector.py     # Step 6: Rule-based leak detection
├── audit_workflow.py            # Checklist & progress tracker
├── dashboard_app.py             # Plotly Dash interactive dashboard
├── generate_report.py           # PowerPoint report generator
└── run_full_audit.py            # 🎯 Master pipeline (run this)
```

---

## 📊 What the Pipeline Produces

| Output | Location |
|---|---|
| Cleaned datasets (5 CSVs) | `audit_workspace/cleaned_data/` |
| Sales funnel chart | `audit_workspace/visualizations/` |
| Revenue trend chart | `audit_workspace/visualizations/` |
| Marketing channel charts | `audit_workspace/visualizations/` |
| CAC vs LTV chart | `audit_workspace/visualizations/` |
| Customer LTV distribution | `audit_workspace/visualizations/` |
| Pareto revenue chart | `audit_workspace/visualizations/` |
| KPI results (JSON) | `audit_workspace/analysis/kpi_results.json` |
| Revenue leak report (JSON) | `audit_workspace/analysis/revenue_leak_report.json` |
| 20-slide PowerPoint report | `audit_workspace/report_outputs/business_audit_report.pptx` |
| Interactive dashboard | http://localhost:8050 |

---

## 🔍 KPIs Calculated (30+)

**Sales:** Lead conversion, opportunity conversion, avg deal value, sales cycle, pipeline velocity

**Marketing:** CAC, ROAS, channel conversion rate, funnel drop-off, CPC, CTR

**Financial:** Gross margin, contribution margin, unit economics, CPA

**Customer:** LTV, churn rate, retention rate, repeat purchase rate, avg order value

---

## ⚠️ Revenue Leak Detection Rules

| Rule | Trigger | Impact |
|---|---|---|
| Sales Funnel Leak | Conversion < 15% | High |
| Marketing Inefficiency | CAC > 40% of LTV | Critical |
| Customer Churn Issue | Retention < 40% | Critical |
| Pricing Problem | Gross Margin < 50% | Medium |
| Low ROAS | ROAS < 2x | Medium |
| Long Sales Cycle | Cycle > 45 days | Medium |

---

## 📋 Audit Checklist

The system tracks a 7-day audit lifecycle:
- **Day 1:** Discovery & data collection
- **Days 2–3:** Data processing & analysis
- **Days 4–5:** KPI calculation & leak detection
- **Days 6–7:** Report generation & delivery

Progress is saved to `audit_workspace/audit_status.json`

---

## 🛠️ Running Individual Modules

```bash
python validate_client_data.py    # Validate data only
python data_cleaning.py           # Clean data only
python kpi_library.py             # Calculate KPIs only
python revenue_leak_detector.py   # Detect leaks only
python generate_report.py         # Generate report only
python dashboard_app.py           # Launch dashboard only
```

---

## 📦 Dependencies

```
pandas>=2.0
numpy>=1.24
matplotlib>=3.7
seaborn>=0.12
python-pptx>=0.6.21
plotly>=5.0
dash>=2.0
sqlalchemy>=2.0
```

---

*Built by Monarch Analytics · data@monarchanalytics.in*
