"""
data_cleaning.py
================
Monarch Analytics — Data Cleaning Pipeline

Loads all raw CSVs from audit_workspace/data/,
applies cleaning transformations, and saves
cleaned versions to audit_workspace/cleaned_data/.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

RAW_DIR = "audit_workspace/data"
CLEAN_DIR = "audit_workspace/cleaned_data"


# ── Utility Helpers ───────────────────────────────────────────────────────────

def parse_dates(df: pd.DataFrame, date_cols: list) -> pd.DataFrame:
    """Convert date columns to datetime, coercing bad values."""
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", format="%Y-%m-%d")
    return df


def normalize_text(df: pd.DataFrame, text_cols: list) -> pd.DataFrame:
    """Lowercase and strip whitespace from text columns."""
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower()
    return df


def convert_numeric(df: pd.DataFrame, num_cols: list) -> pd.DataFrame:
    """Force numeric columns to float, coercing errors to NaN."""
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def remove_duplicates(df: pd.DataFrame, name: str) -> pd.DataFrame:
    """Remove fully duplicate rows."""
    before = len(df)
    df = df.drop_duplicates()
    after = len(df)
    if before != after:
        print(f"   Removed {before - after} duplicate rows from {name}")
    return df


def fill_missing(df: pd.DataFrame, num_cols: list) -> pd.DataFrame:
    """Fill numeric NaN with median; leave categoricals blank."""
    for col in num_cols:
        if col in df.columns and df[col].isnull().any():
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
    return df


# ── Per-Dataset Cleaners ──────────────────────────────────────────────────────

def clean_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and enrich sales data."""
    df = remove_duplicates(df, "sales")
    df = parse_dates(df, ["date", "lead_date", "close_date"])
    df = normalize_text(df, ["channel", "deal_stage", "lead_source"])
    df = convert_numeric(df, ["revenue"])
    df = fill_missing(df, ["revenue"])

    # Derived columns
    df["sales_cycle_days"] = (df["close_date"] - df["lead_date"]).dt.days
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["year"] = df["date"].dt.year
    df["is_won"] = df["deal_stage"] == "closed_won"
    df["is_lost"] = df["deal_stage"] == "closed_lost"

    return df


def clean_marketing(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and enrich marketing spend data."""
    df = remove_duplicates(df, "marketing")
    df = parse_dates(df, ["date"])
    df = normalize_text(df, ["channel", "campaign"])
    df = convert_numeric(df, ["spend", "impressions", "clicks", "conversions", "revenue_generated"])
    df = fill_missing(df, ["spend", "impressions", "clicks", "conversions", "revenue_generated"])

    # Derived metrics
    df["click_through_rate"] = (df["clicks"] / df["impressions"].replace(0, np.nan)).round(4)
    df["conversion_rate"] = (df["conversions"] / df["clicks"].replace(0, np.nan)).round(4)
    df["cost_per_click"] = (df["spend"] / df["clicks"].replace(0, np.nan)).round(2)
    df["roas"] = (df["revenue_generated"] / df["spend"].replace(0, np.nan)).round(2)
    df["month"] = df["date"].dt.to_period("M").astype(str)

    return df


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and enrich customer data."""
    df = remove_duplicates(df, "customers")
    df = parse_dates(df, ["first_purchase_date", "last_purchase_date"])
    df = normalize_text(df, ["segment", "location"])
    df = convert_numeric(df, ["total_orders", "total_revenue"])
    df = fill_missing(df, ["total_orders", "total_revenue"])

    # Derived columns
    df["avg_order_value"] = (df["total_revenue"] / df["total_orders"].replace(0, np.nan)).round(2)
    df["customer_age_days"] = (pd.Timestamp.now() - df["first_purchase_date"]).dt.days
    df["days_since_last_purchase"] = (pd.Timestamp.now() - df["last_purchase_date"]).dt.days
    df["is_churned"] = df["days_since_last_purchase"] > 180  # 6 months = churned

    return df


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    """Clean product catalog."""
    df = remove_duplicates(df, "products")
    df = normalize_text(df, ["category"])
    df = convert_numeric(df, ["price", "cost", "margin"])
    df = fill_missing(df, ["price", "cost", "margin"])

    # Validate margin
    df["computed_margin"] = ((df["price"] - df["cost"]) / df["price"].replace(0, np.nan)).round(4)

    return df


def clean_operations(df: pd.DataFrame) -> pd.DataFrame:
    """Clean operational metrics."""
    df = remove_duplicates(df, "operations")
    df = parse_dates(df, ["date"])
    df = normalize_text(df, ["department", "metric_name"])
    df = convert_numeric(df, ["metric_value"])
    df["month"] = df["date"].dt.to_period("M").astype(str)
    return df


# ── Main Cleaner ──────────────────────────────────────────────────────────────

CLEANING_MAP = {
    "01_sales_data_template.csv": clean_sales,
    "02_marketing_spend_template.csv": clean_marketing,
    "03_customer_data_template.csv": clean_customers,
    "04_product_catalog_template.csv": clean_products,
    "05_operational_metrics_template.csv": clean_operations,
}

OUTPUT_NAMES = {
    "01_sales_data_template.csv": "sales_clean.csv",
    "02_marketing_spend_template.csv": "marketing_clean.csv",
    "03_customer_data_template.csv": "customers_clean.csv",
    "04_product_catalog_template.csv": "products_clean.csv",
    "05_operational_metrics_template.csv": "operations_clean.csv",
}


def run_cleaning():
    """Execute the full data cleaning pipeline."""
    print("\n" + "="*60)
    print("  MONARCH ANALYTICS — DATA CLEANING PIPELINE")
    print("="*60 + "\n")

    os.makedirs(CLEAN_DIR, exist_ok=True)
    summary = {}

    for fname, cleaner_fn in CLEANING_MAP.items():
        raw_path = os.path.join(RAW_DIR, fname)
        out_name = OUTPUT_NAMES[fname]
        out_path = os.path.join(CLEAN_DIR, out_name)

        print(f"🔧 Cleaning: {fname}")

        if not os.path.isfile(raw_path):
            print(f"   ⚠️  File not found, skipping.\n")
            continue

        df = pd.read_csv(raw_path)
        df.columns = df.columns.str.strip().str.lower()
        original_rows = len(df)

        df_clean = cleaner_fn(df)
        df_clean.to_csv(out_path, index=False)

        summary[fname] = {
            "input_rows": original_rows,
            "output_rows": len(df_clean),
            "output_file": out_path
        }
        print(f"   ✅ {original_rows} rows → {len(df_clean)} rows saved to {out_name}\n")

    print("="*60)
    print("  ✅ DATA CLEANING COMPLETE")
    print("="*60 + "\n")
    return summary


if __name__ == "__main__":
    run_cleaning()
