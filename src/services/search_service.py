"""
Global Search Service Module for kartavya (Phase 6).

Non-modifying search engine that queries Workspaces, Tasks, Reminders, and Goals
across the entire application and returns structured location-aware search results.
"""

from src.data.workspace_store import get_workspaces
from src.data.reminder_store import get_reminders


def global_search(query: str) -> list[dict]:
    """
    Searches across Workspaces, Tasks, Reminders, and Goals.
    Case-insensitive partial matching.
    Returns list of dicts: [{"type": str, "title": str, "context": str, "workspace_name": str, "workspace_id": str}]
    """
    q = query.strip().lower()
    if not q:
        return []

    results = []
    workspaces = get_workspaces()
    reminders = get_reminders()

    # 1. Search Workspaces
    for ws in workspaces:
        ws_name = str(ws.get("name", ""))
        ws_desc = str(ws.get("description", ""))
        if q in ws_name.lower() or q in ws_desc.lower():
            results.append({
                "type": "Workspace",
                "title": ws_name,
                "context": ws_desc or "Workspace Profile",
                "workspace_name": ws_name,
                "workspace_id": ws["id"],
                "badge_class": "neo-badge-coral",
            })

    # 2. Search Tasks in all workspaces
    for ws in workspaces:
        ws_name = str(ws.get("name", ""))
        ws_id = str(ws.get("id", ""))
        for t in ws.get("tasks", []):
            if isinstance(t, dict):
                t_name = str(t.get("name", ""))
                t_desc = str(t.get("description", ""))
                t_prio = str(t.get("priority", "Medium"))
                if q in t_name.lower() or q in t_desc.lower() or q in t_prio.lower():
                    results.append({
                        "type": "Task",
                        "title": t_name,
                        "context": f"{t_prio} Priority {f'• {t_desc}' if t_desc else ''}",
                        "workspace_name": ws_name,
                        "workspace_id": ws_id,
                        "badge_class": "neo-badge-cyan",
                    })

    # 3. Search Reminders
    for rem in reminders:
        r_title = str(rem.get("title", ""))
        r_desc = str(rem.get("description", ""))
        r_prio = str(rem.get("priority", "Medium"))
        if q in r_title.lower() or q in r_desc.lower() or q in r_prio.lower():
            d_val = rem.get("deadline")
            d_str = d_val.isoformat() if hasattr(d_val, "isoformat") else str(d_val or "No deadline")
            results.append({
                "type": "Reminder",
                "title": r_title,
                "context": f"Deadline: {d_str} • {r_prio} Priority",
                "workspace_name": "Global Shell",
                "workspace_id": "global",
                "badge_class": "neo-badge-yellow",
            })

    # 4. Search Goals
    for ws in workspaces:
        ws_name = str(ws.get("name", ""))
        ws_id = str(ws.get("id", ""))
        for g in ws.get("goals", []):
            if isinstance(g, dict):
                g_title = str(g.get("title", ""))
                g_status = str(g.get("status", "active"))
                g_type = str(g.get("goal_type", "task_count"))
                if q in g_title.lower() or q in g_status.lower() or q in g_type.lower():
                    results.append({
                        "type": "Goal",
                        "title": g_title,
                        "context": f"Target: {g.get('target_value', 10)} • Status: {g_status.upper()}",
                        "workspace_name": ws_name,
                        "workspace_id": ws_id,
                        "badge_class": "neo-badge",
                    })

    return results
