"""
Data Export Service for kartavya (Phase 7).

Provides versioned JSON export and CSV table exports (Task Timeline, Reminders, Goals).
"""

import json
import csv
import io
from datetime import date
from src.data.workspace_store import get_workspaces, get_active_workspace_id, get_active_workspace
from src.data.reminder_store import get_reminders
from src.data.persistence import parse_date


def export_to_json() -> str:
    """
    Exports all user data as a formatted, versioned JSON string.
    Includes Workspaces, Tasks, Task Metadata, Dates, Completion Matrices, Focus States, Goals, Reminders, Daily Targets.
    """
    workspaces = get_workspaces()
    active_ws_id = get_active_workspace_id()
    reminders = get_reminders()

    serializable_workspaces = []
    for ws in workspaces:
        iso_dates = [
            d.isoformat() if isinstance(d, date) else str(d)
            for d in sorted(ws.get("dates", []))
        ]

        serializable_tasks = []
        for t in ws.get("tasks", []):
            if isinstance(t, dict):
                rec = t.get("recurrence", {"type": "none", "days": []})
                serializable_tasks.append({
                    "id": str(t.get("id", "")),
                    "name": str(t.get("name", "")),
                    "priority": str(t.get("priority", "Medium")),
                    "description": str(t.get("description", "")),
                    "recurrence": {
                        "type": str(rec.get("type", "none")),
                        "days": [int(d) for d in rec.get("days", [])],
                    },
                })

        serializable_goals = []
        for g in ws.get("goals", []):
            if isinstance(g, dict):
                s_date = parse_date(g.get("start_date"))
                e_date = parse_date(g.get("end_date"))
                serializable_goals.append({
                    "id": str(g["id"]),
                    "title": str(g["title"]),
                    "goal_type": str(g.get("goal_type", "task_count")),
                    "target_value": float(g.get("target_value", 10.0)),
                    "start_date": s_date.isoformat() if isinstance(s_date, date) else "",
                    "end_date": e_date.isoformat() if isinstance(e_date, date) else "",
                    "status": str(g.get("status", "active")),
                    "created_at": str(g.get("created_at", "")),
                })

        serializable_workspaces.append({
            "id": str(ws["id"]),
            "name": str(ws["name"]),
            "description": str(ws.get("description", "")),
            "dates": iso_dates,
            "tasks": serializable_tasks,
            "completion": ws.get("completion", {}),
            "goals": serializable_goals,
            "daily_target_pct": float(ws.get("daily_target_pct", 80.0)),
            "focus_matrix": ws.get("focus_matrix", {}),
        })

    serializable_reminders = []
    for rem in reminders:
        d_val = parse_date(rem.get("deadline"))
        iso_deadline = d_val.isoformat() if isinstance(d_val, date) else ""
        serializable_reminders.append({
            "id": str(rem["id"]),
            "title": str(rem["title"]),
            "description": str(rem.get("description", "")),
            "deadline": iso_deadline,
            "priority": str(rem.get("priority", "Medium")),
            "completed": bool(rem.get("completed", False)),
            "created_at": str(rem.get("created_at", "")),
        })

    payload = {
        "version": 4,
        "active_workspace_id": str(active_ws_id),
        "workspaces": serializable_workspaces,
        "reminders": serializable_reminders,
    }

    return json.dumps(payload, indent=2)


def export_to_csv_timeline() -> str:
    """Exports active workspace timeline grid as CSV string."""
    ws = get_active_workspace()
    dates = sorted(ws.get("dates", []))
    tasks = ws.get("tasks", [])
    completion = ws.get("completion", {})

    output = io.StringIO()
    writer = csv.writer(output)

    # Header: Date, Task1 (ID), Task2 (ID)...
    headers = ["Date"] + [(t["name"] if isinstance(t, dict) else str(t)) for t in tasks]
    writer.writerow(headers)

    task_ids = [(t["id"] if isinstance(t, dict) else str(t)) for t in tasks]

    for d in dates:
        d_iso = d.isoformat() if isinstance(d, date) else str(d)
        row = [d_iso]
        d_comp = completion.get(d_iso, {})
        for t_id in task_ids:
            row.append("1" if d_comp.get(t_id, False) else "0")
        writer.writerow(row)

    return output.getvalue()


def export_to_csv_reminders() -> str:
    """Exports global reminders as CSV string."""
    reminders = get_reminders()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Title", "Deadline", "Priority", "Completed", "Description"])

    for rem in reminders:
        d_val = parse_date(rem.get("deadline"))
        writer.writerow([
            rem.get("id", ""),
            rem.get("title", ""),
            d_val.isoformat() if isinstance(d_val, date) else "",
            rem.get("priority", "Medium"),
            "1" if rem.get("completed", False) else "0",
            rem.get("description", ""),
        ])

    return output.getvalue()


def export_to_csv_goals() -> str:
    """Exports all workspace goals as CSV string."""
    workspaces = get_workspaces()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Goal ID", "Workspace", "Title", "Goal Type", "Target Value", "Start Date", "End Date", "Status"])

    for ws in workspaces:
        ws_name = ws.get("name", "")
        for g in ws.get("goals", []):
            if isinstance(g, dict):
                s_date = parse_date(g.get("start_date"))
                e_date = parse_date(g.get("end_date"))
                writer.writerow([
                    g.get("id", ""),
                    ws_name,
                    g.get("title", ""),
                    g.get("goal_type", "task_count"),
                    g.get("target_value", 10.0),
                    s_date.isoformat() if isinstance(s_date, date) else "",
                    e_date.isoformat() if isinstance(e_date, date) else "",
                    g.get("status", "active"),
                ])

    return output.getvalue()
