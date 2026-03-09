"""
setup_workspace.py
==================
Monarch Analytics — Workspace Setup Script

Creates the full audit workspace directory structure,
copies uploaded client data into the workspace, and
initializes the SQLite audit database.
"""

import os
import shutil
import sqlite3
from datetime import datetime

# ── Directory Structure ───────────────────────────────────────────────────────

WORKSPACE_DIRS = [
    "audit_workspace/data",
    "audit_workspace/cleaned_data",
    "audit_workspace/analysis",
    "audit_workspace/visualizations",
    "audit_workspace/report_outputs",
    "audit_workspace/dashboards",
]

SOURCE_DATA_DIR = "client_data_intake"
DB_PATH = "audit_workspace/monarch_audit.db"


def create_directories():
    """Create all required workspace folders."""
    print("📁 Creating workspace directories...")
    for d in WORKSPACE_DIRS:
        os.makedirs(d, exist_ok=True)
        print(f"   ✅ {d}")


def copy_client_data():
    """Copy client CSV files from intake folder into workspace/data/."""
    print("\n📂 Copying client data into workspace...")
    if not os.path.isdir(SOURCE_DATA_DIR):
        print(f"   ⚠️  Source directory '{SOURCE_DATA_DIR}' not found. Skipping copy.")
        return
    count = 0
    for fname in os.listdir(SOURCE_DATA_DIR):
        if fname.endswith(".csv"):
            src = os.path.join(SOURCE_DATA_DIR, fname)
            dst = os.path.join("audit_workspace/data", fname)
            shutil.copy2(src, dst)
            print(f"   ✅ Copied: {fname}")
            count += 1
    print(f"   Total files copied: {count}")


def init_database():
    """Initialize SQLite database with audit tracking tables."""
    print(f"\n🗄️  Initializing SQLite database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Audit sessions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            started_at TEXT,
            status TEXT DEFAULT 'in_progress',
            completed_at TEXT
        )
    """)

    # KPI results table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS kpi_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            kpi_name TEXT,
            kpi_value REAL,
            category TEXT,
            recorded_at TEXT,
            FOREIGN KEY(session_id) REFERENCES audit_sessions(id)
        )
    """)

    # Revenue leaks table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS revenue_leaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            rule_name TEXT,
            description TEXT,
            impact_score REAL,
            recommended_action TEXT,
            detected_at TEXT,
            FOREIGN KEY(session_id) REFERENCES audit_sessions(id)
        )
    """)

    # Audit workflow steps table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS workflow_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            step_name TEXT,
            status TEXT DEFAULT 'pending',
            completed_at TEXT,
            FOREIGN KEY(session_id) REFERENCES audit_sessions(id)
        )
    """)

    # Insert a new audit session
    cur.execute("""
        INSERT INTO audit_sessions (client_name, started_at, status)
        VALUES (?, ?, ?)
    """, ("Demo Client", datetime.now().isoformat(), "in_progress"))

    conn.commit()
    session_id = cur.lastrowid
    conn.close()

    print(f"   ✅ Database initialized. Session ID: {session_id}")
    return session_id


def setup():
    """Run the full workspace setup."""
    print("\n" + "="*60)
    print("  MONARCH ANALYTICS — WORKSPACE SETUP")
    print("="*60 + "\n")

    create_directories()
    copy_client_data()
    session_id = init_database()

    print("\n" + "="*60)
    print("  ✅ WORKSPACE READY")
    print(f"  Session ID: {session_id}")
    print("="*60 + "\n")

    return session_id


if __name__ == "__main__":
    setup()
