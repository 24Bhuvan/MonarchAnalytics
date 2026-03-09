"""
validate_client_data.py
=======================
Monarch Analytics — Data Validation Script

Validates all uploaded client CSV files before the audit pipeline begins.
Checks for: file existence, column structure, missing values, date formats.
Outputs a structured validation report.
"""

import os
import pandas as pd
import json
from datetime import datetime

# ── Configuration ────────────────────────────────────────────────────────────

DATA_DIR = "client_data_intake"

REQUIRED_FILES = {
    "01_sales_data_template.csv": [
        "date", "customer_id", "product_id", "revenue", "channel",
        "sales_rep", "deal_stage", "lead_source", "lead_date", "close_date"
    ],
    "02_marketing_spend_template.csv": [
        "date", "channel", "campaign", "spend", "impressions",
        "clicks", "conversions", "revenue_generated"
    ],
    "03_customer_data_template.csv": [
        "customer_id", "first_purchase_date", "last_purchase_date",
        "total_orders", "total_revenue", "segment", "location"
    ],
    "04_product_catalog_template.csv": [
        "product_id", "product_name", "category", "price", "cost", "margin"
    ],
    "05_operational_metrics_template.csv": [
        "date", "department", "metric_name", "metric_value"
    ],
}

DATE_COLUMNS = {
    "01_sales_data_template.csv": ["date", "lead_date", "close_date"],
    "02_marketing_spend_template.csv": ["date"],
    "03_customer_data_template.csv": ["first_purchase_date", "last_purchase_date"],
    "05_operational_metrics_template.csv": ["date"],
}

NUMERIC_COLUMNS = {
    "01_sales_data_template.csv": ["revenue"],
    "02_marketing_spend_template.csv": ["spend", "impressions", "clicks", "conversions", "revenue_generated"],
    "03_customer_data_template.csv": ["total_orders", "total_revenue"],
    "04_product_catalog_template.csv": ["price", "cost", "margin"],
    "05_operational_metrics_template.csv": ["metric_value"],
}


# ── Validation Functions ──────────────────────────────────────────────────────

def check_file_exists(filename: str) -> dict:
    """Check whether a required file exists in the data directory."""
    path = os.path.join(DATA_DIR, filename)
    exists = os.path.isfile(path)
    return {"check": "file_exists", "passed": exists,
            "detail": f"{'Found' if exists else 'MISSING'}: {path}"}


def check_columns(df: pd.DataFrame, filename: str, required_cols: list) -> dict:
    """Verify all required columns are present in the dataframe."""
    actual_cols = set(df.columns.str.strip().str.lower())
    required_set = set(required_cols)
    missing = required_set - actual_cols
    extra = actual_cols - required_set
    passed = len(missing) == 0
    detail = []
    if missing:
        detail.append(f"Missing columns: {sorted(missing)}")
    if extra:
        detail.append(f"Extra columns (ignored): {sorted(extra)}")
    if passed:
        detail.append("All required columns present.")
    return {"check": "column_structure", "passed": passed, "detail": " | ".join(detail)}


def check_missing_values(df: pd.DataFrame, required_cols: list) -> dict:
    """Report missing values across required columns."""
    issues = {}
    for col in required_cols:
        if col in df.columns:
            missing_count = df[col].isnull().sum()
            if missing_count > 0:
                issues[col] = int(missing_count)
    passed = len(issues) == 0
    detail = f"Missing values found: {issues}" if issues else "No critical missing values."
    return {"check": "missing_values", "passed": passed, "detail": detail, "missing_counts": issues}


def check_date_format(df: pd.DataFrame, date_cols: list) -> dict:
    """Validate that date columns follow YYYY-MM-DD format."""
    issues = {}
    for col in date_cols:
        if col not in df.columns:
            continue
        # Drop NaN before checking (optional fields may be blank)
        non_null = df[col].dropna()
        bad_rows = []
        for idx, val in non_null.items():
            try:
                datetime.strptime(str(val).strip(), "%Y-%m-%d")
            except ValueError:
                bad_rows.append({"row": int(idx) + 2, "value": str(val)})
        if bad_rows:
            issues[col] = bad_rows[:5]  # show first 5 bad rows only
    passed = len(issues) == 0
    detail = f"Date format issues: {issues}" if issues else "All dates are YYYY-MM-DD."
    return {"check": "date_format", "passed": passed, "detail": detail}


def check_numeric_columns(df: pd.DataFrame, numeric_cols: list) -> dict:
    """Validate that numeric columns contain valid numbers."""
    issues = {}
    for col in numeric_cols:
        if col not in df.columns:
            continue
        converted = pd.to_numeric(df[col], errors="coerce")
        bad_count = converted.isnull().sum() - df[col].isnull().sum()
        if bad_count > 0:
            issues[col] = int(bad_count)
    passed = len(issues) == 0
    detail = f"Non-numeric values in: {issues}" if issues else "All numeric columns are valid."
    return {"check": "numeric_columns", "passed": passed, "detail": detail}


# ── Main Validation Runner ────────────────────────────────────────────────────

def validate_all() -> dict:
    """Run all validation checks on every required file and produce a report."""
    report = {
        "audit_id": f"VAL-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "validated_at": datetime.now().isoformat(),
        "overall_passed": True,
        "files": {}
    }

    print("\n" + "="*60)
    print("  MONARCH ANALYTICS — DATA VALIDATION")
    print("="*60)

    for filename, required_cols in REQUIRED_FILES.items():
        print(f"\n📄 Validating: {filename}")
        file_report = {"checks": [], "row_count": 0, "passed": True}

        # 1. File existence
        exists_check = check_file_exists(filename)
        file_report["checks"].append(exists_check)
        status = "✅" if exists_check["passed"] else "❌"
        print(f"  {status} File exists: {exists_check['detail']}")

        if not exists_check["passed"]:
            file_report["passed"] = False
            report["overall_passed"] = False
            report["files"][filename] = file_report
            continue

        # Load file
        path = os.path.join(DATA_DIR, filename)
        df = pd.read_csv(path)
        df.columns = df.columns.str.strip().str.lower()
        file_report["row_count"] = len(df)
        print(f"  📊 Rows loaded: {len(df)}")

        # 2. Column check
        col_check = check_columns(df, filename, required_cols)
        file_report["checks"].append(col_check)
        status = "✅" if col_check["passed"] else "❌"
        print(f"  {status} Columns: {col_check['detail']}")
        if not col_check["passed"]:
            file_report["passed"] = False
            report["overall_passed"] = False

        # 3. Missing values
        mv_check = check_missing_values(df, required_cols)
        file_report["checks"].append(mv_check)
        status = "✅" if mv_check["passed"] else "⚠️ "
        print(f"  {status} Missing values: {mv_check['detail']}")

        # 4. Date format
        if filename in DATE_COLUMNS:
            date_check = check_date_format(df, DATE_COLUMNS[filename])
            file_report["checks"].append(date_check)
            status = "✅" if date_check["passed"] else "❌"
            print(f"  {status} Date format: {date_check['detail']}")
            if not date_check["passed"]:
                file_report["passed"] = False
                report["overall_passed"] = False

        # 5. Numeric columns
        if filename in NUMERIC_COLUMNS:
            num_check = check_numeric_columns(df, NUMERIC_COLUMNS[filename])
            file_report["checks"].append(num_check)
            status = "✅" if num_check["passed"] else "❌"
            print(f"  {status} Numeric cols: {num_check['detail']}")
            if not num_check["passed"]:
                file_report["passed"] = False
                report["overall_passed"] = False

        report["files"][filename] = file_report

    # Summary
    print("\n" + "="*60)
    overall = "✅ ALL CHECKS PASSED" if report["overall_passed"] else "❌ VALIDATION FAILED — FIX ERRORS BEFORE PROCEEDING"
    print(f"  RESULT: {overall}")
    print("="*60 + "\n")

    # Save report
    report_path = "audit_workspace/validation_report.json"
    os.makedirs("audit_workspace", exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"📁 Validation report saved to: {report_path}\n")

    return report


if __name__ == "__main__":
    validate_all()
