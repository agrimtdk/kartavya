"""
Goal Store Module for kartavya (Phase 9 Public Multi-User Architecture).

Manages CRUD operations and persistent state for workspace-isolated productivity goals.
Routes mutations to user-scoped database store when authenticated.
"""

import uuid
from datetime import date, datetime
from src.data.workspace_store import get_workspaces, save_all_stores, get_active_workspace_id
from src.data.persistence import parse_date
from src.services.auth_service import get_current_user
from src.db.db_store import (
    get_user_goals as db_get_user_goals,
    create_goal as db_create_goal,
    update_goal as db_update_goal,
    delete_goal as db_delete_goal,
)


def get_workspace_goals(ws_id: str | None = None) -> list[dict]:
    """Returns list of goal dictionaries for specified workspace ID."""
    target_id = ws_id or get_active_workspace_id()
    user = get_current_user()

    if user:
        goals = db_get_user_goals(user["id"], target_id)
        # Adapt database goal fields to UI dictionary structure
        adapted = []
        for g in goals:
            p_end = parse_date(g.get("deadline")) or date.today()
            adapted.append({
                "id": g["id"],
                "title": g["title"],
                "goal_type": "task_count",
                "target_value": g.get("target", 100.0),
                "start_date": parse_date(g.get("created_at")) or date.today(),
                "end_date": p_end,
                "status": "completed" if g.get("progress", 0.0) >= g.get("target", 100.0) else "active",
                "created_at": g.get("created_at"),
            })
        return adapted

    workspaces = get_workspaces()
    for ws in workspaces:
        if ws["id"] == target_id:
            if "goals" not in ws or not isinstance(ws["goals"], list):
                ws["goals"] = []
            return ws["goals"]

    return []


def add_workspace_goal(
    ws_id: str,
    title: str,
    goal_type: str,
    target_value: float,
    start_date: date | str,
    end_date: date | str,
) -> tuple[bool, str, str | None]:
    """Creates a new goal for the specified workspace."""
    trimmed_title = title.strip()
    if not trimmed_title:
        return False, "Goal title cannot be empty.", None

    if target_value <= 0:
        return False, "Target value must be greater than zero.", None

    p_start = parse_date(start_date) or date.today()
    p_end = parse_date(end_date) or date.today()
    if p_start > p_end:
        p_start, p_end = p_end, p_start

    user = get_current_user()
    if user:
        g_obj = db_create_goal(
            user["id"],
            ws_id,
            trimmed_title,
            description="",
            target=float(target_value),
            progress=0.0,
            deadline=p_end,
        )
        return True, f"Goal '{trimmed_title}' created successfully.", g_obj["id"]

    goal_id = f"goal_{uuid.uuid4().hex[:8]}"
    new_goal = {
        "id": goal_id,
        "title": trimmed_title,
        "goal_type": goal_type,
        "target_value": float(target_value),
        "start_date": p_start,
        "end_date": p_end,
        "status": "active",
        "created_at": datetime.now().isoformat(),
    }

    workspaces = get_workspaces()
    for ws in workspaces:
        if ws["id"] == ws_id:
            if "goals" not in ws:
                ws["goals"] = []
            ws["goals"].append(new_goal)
            save_all_stores()
            return True, f"Goal '{trimmed_title}' created successfully.", goal_id

    return False, "Workspace not found.", None


def edit_workspace_goal(
    ws_id: str,
    goal_id: str,
    title: str,
    target_value: float,
    start_date: date | str,
    end_date: date | str,
    status: str = "active",
) -> tuple[bool, str]:
    """Updates an existing workspace goal."""
    trimmed_title = title.strip()
    if not trimmed_title:
        return False, "Goal title cannot be empty."

    if target_value <= 0:
        return False, "Target value must be greater than zero."

    p_start = parse_date(start_date) or date.today()
    p_end = parse_date(end_date) or date.today()
    if p_start > p_end:
        p_start, p_end = p_end, p_start

    user = get_current_user()
    if user:
        res = db_update_goal(
            user["id"],
            ws_id,
            goal_id,
            {"title": trimmed_title, "target": float(target_value), "deadline": p_end},
        )
        if res:
            return True, "Goal updated successfully."
        return False, "Goal not found or unauthorized."

    goals = get_workspace_goals(ws_id)
    for g in goals:
        if g["id"] == goal_id:
            g["title"] = trimmed_title
            g["target_value"] = float(target_value)
            g["start_date"] = p_start
            g["end_date"] = p_end
            if status in ["active", "completed", "archived"]:
                g["status"] = status
            save_all_stores()
            return True, "Goal updated successfully."

    return False, "Goal not found."


def delete_workspace_goal(ws_id: str, goal_id: str) -> tuple[bool, str]:
    """Deletes a goal from the specified workspace."""
    user = get_current_user()
    if user:
        ok = db_delete_goal(user["id"], ws_id, goal_id)
        if ok:
            return True, "Goal deleted successfully."
        return False, "Goal not found or unauthorized."

    workspaces = get_workspaces()
    for ws in workspaces:
        if ws["id"] == ws_id:
            goals = ws.get("goals", [])
            target = next((g for g in goals if g["id"] == goal_id), None)
            if target:
                goals.remove(target)
                save_all_stores()
                return True, f"Goal '{target['title']}' deleted successfully."

    return False, "Goal not found."


def toggle_goal_status(ws_id: str, goal_id: str) -> tuple[bool, str]:
    """Toggles goal status between active and completed/archived."""
    goals = get_workspace_goals(ws_id)
    for g in goals:
        if g["id"] == goal_id:
            current_status = g.get("status", "active")
            new_status = "completed" if current_status == "active" else "active"
            g["status"] = new_status
            
            user = get_current_user()
            if user:
                target_val = g.get("target_value", 100.0)
                new_prog = target_val if new_status == "completed" else 0.0
                db_update_goal(user["id"], ws_id, goal_id, {"progress": new_prog})

            save_all_stores()
            return True, f"Goal status changed to '{new_status}'."

    return False, "Goal not found."
