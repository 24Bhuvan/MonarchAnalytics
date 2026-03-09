"""
audit_workflow.py
=================
Monarch Analytics — Audit Checklist & Workflow Manager

Tracks the lifecycle of each audit through
daily checkpoints and saves progress to audit_status.json.
"""

import os
import json
from datetime import datetime

STATUS_FILE = "audit_workspace/audit_status.json"

CHECKLIST = {
    "day_1": {
        "label": "Day 1 — Discovery",
        "tasks": [
            {"id": "d1_t1", "name": "Founder / Stakeholder Interview Completed"},
            {"id": "d1_t2", "name": "Data Sources Identified"},
            {"id": "d1_t3", "name": "Data Access Obtained"},
            {"id": "d1_t4", "name": "Client Data Intake Folder Sent"},
        ]
    },
    "day_2_3": {
        "label": "Days 2–3 — Data Processing",
        "tasks": [
            {"id": "d2_t1", "name": "Datasets Consolidated into Workspace"},
            {"id": "d2_t2", "name": "Data Validation Passed"},
            {"id": "d2_t3", "name": "Data Cleaned and Normalized"},
            {"id": "d2_t4", "name": "Analysis Scripts Executed"},
            {"id": "d2_t5", "name": "Visualizations Generated"},
        ]
    },
    "day_4_5": {
        "label": "Days 4–5 — Analysis",
        "tasks": [
            {"id": "d4_t1", "name": "KPI Calculations Completed"},
            {"id": "d4_t2", "name": "Revenue Leak Detection Run"},
            {"id": "d4_t3", "name": "Opportunity Areas Identified"},
            {"id": "d4_t4", "name": "Dashboard Generated"},
        ]
    },
    "day_6_7": {
        "label": "Days 6–7 — Delivery",
        "tasks": [
            {"id": "d6_t1", "name": "Report Generated (PowerPoint)"},
            {"id": "d6_t2", "name": "Report Reviewed Internally"},
            {"id": "d6_t3", "name": "Leadership Presentation Prepared"},
            {"id": "d6_t4", "name": "Audit Delivered to Client"},
        ]
    }
}


def load_status() -> dict:
    """Load existing status or initialize fresh."""
    if os.path.isfile(STATUS_FILE):
        with open(STATUS_FILE) as f:
            return json.load(f)
    return init_status()


def init_status() -> dict:
    """Create a fresh audit status file."""
    status = {
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "overall_progress_pct": 0,
        "phases": {}
    }
    for phase_key, phase in CHECKLIST.items():
        status["phases"][phase_key] = {
            "label": phase["label"],
            "tasks": {
                t["id"]: {"name": t["name"], "status": "pending", "completed_at": None}
                for t in phase["tasks"]
            }
        }
    return status


def save_status(status: dict):
    """Persist status to JSON file."""
    os.makedirs("audit_workspace", exist_ok=True)
    status["last_updated"] = datetime.now().isoformat()
    total_tasks = sum(len(p["tasks"]) for p in status["phases"].values())
    done_tasks = sum(
        1 for p in status["phases"].values()
        for t in p["tasks"].values() if t["status"] == "completed"
    )
    status["overall_progress_pct"] = round(done_tasks / total_tasks * 100, 1) if total_tasks else 0
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)


def mark_complete(task_id: str):
    """Mark a specific task as completed."""
    status = load_status()
    for phase in status["phases"].values():
        if task_id in phase["tasks"]:
            phase["tasks"][task_id]["status"] = "completed"
            phase["tasks"][task_id]["completed_at"] = datetime.now().isoformat()
            save_status(status)
            print(f"   ✅ Task completed: {phase['tasks'][task_id]['name']}")
            return
    print(f"   ⚠️  Task ID not found: {task_id}")


def auto_complete_pipeline_tasks():
    """Automatically mark all pipeline execution tasks as complete."""
    pipeline_tasks = ["d2_t1", "d2_t2", "d2_t3", "d2_t4", "d2_t5",
                      "d4_t1", "d4_t2", "d4_t3", "d4_t4", "d6_t1"]
    for tid in pipeline_tasks:
        mark_complete(tid)


def print_status():
    """Print a readable checklist to console."""
    status = load_status()
    print("\n" + "="*60)
    print("  MONARCH ANALYTICS — AUDIT CHECKLIST")
    print(f"  Progress: {status['overall_progress_pct']}%")
    print("="*60)
    for phase_data in status["phases"].values():
        print(f"\n  📅 {phase_data['label']}")
        for task in phase_data["tasks"].values():
            icon = "✅" if task["status"] == "completed" else "☐ "
            completed = f" [{task['completed_at'][:10]}]" if task["completed_at"] else ""
            print(f"     {icon}  {task['name']}{completed}")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    status = load_status()
    save_status(status)
    print_status()
