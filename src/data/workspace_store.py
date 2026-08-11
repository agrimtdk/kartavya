"""
Workspace Store Module for kartavya (Phase 9 Public Multi-User Architecture).

Owns workspace collection, active workspace tracking, and workspace lifecycle mutations.
Integrates user-scoped database CRUD operations with local JSON fallback.
"""

import uuid
from datetime import date, timedelta
import streamlit as st
from src.data.persistence import parse_date, load_data, save_data
from src.services.auth_service import get_current_user
from src.db.db_store import (
    get_user_workspaces as db_get_user_workspaces,
    create_workspace as db_create_workspace,
    update_workspace as db_update_workspace,
    delete_workspace as db_delete_workspace,
)

SESSION_KEY_WORKSPACES = "kartavya_workspaces"
SESSION_KEY_ACTIVE_WS_ID = "kartavya_active_ws_id"
SESSION_KEY_REMINDERS = "kartavya_reminders"

MIN_WORKSPACES = 1
MAX_WORKSPACES = 10


def save_all_stores() -> None:
    """Persists local session state to JSON file when in fallback mode."""
    if (
        SESSION_KEY_WORKSPACES in st.session_state
        and SESSION_KEY_ACTIVE_WS_ID in st.session_state
    ):
        workspaces = st.session_state[SESSION_KEY_WORKSPACES]
        active_ws_id = st.session_state[SESSION_KEY_ACTIVE_WS_ID]
        reminders = st.session_state.get(SESSION_KEY_REMINDERS, [])
        save_data(workspaces, active_ws_id, reminders)


def init_workspace_store(force: bool = False) -> None:
    if force:
        if SESSION_KEY_WORKSPACES in st.session_state:
            del st.session_state[SESSION_KEY_WORKSPACES]
    
    if (
        SESSION_KEY_WORKSPACES in st.session_state
        and SESSION_KEY_ACTIVE_WS_ID in st.session_state
    ):
        return

    user = get_current_user()
    if user:
        ws_list = db_get_user_workspaces(user["id"])
        if not ws_list:
            db_create_workspace(user["id"], "Personal", "My personal productivity workspace.")
            ws_list = db_get_user_workspaces(user["id"])

        for ws in ws_list:
            parsed_dates = []
            for d in ws.get("dates", []):
                p_d = parse_date(d)
                if p_d:
                    parsed_dates.append(p_d)
            ws["dates"] = sorted(parsed_dates)

        st.session_state[SESSION_KEY_WORKSPACES] = ws_list

        valid_ids = [w["id"] for w in ws_list]
        if SESSION_KEY_ACTIVE_WS_ID not in st.session_state or st.session_state[SESSION_KEY_ACTIVE_WS_ID] not in valid_ids:
            st.session_state[SESSION_KEY_ACTIVE_WS_ID] = ws_list[0]["id"]
        return
    saved_data = load_data()
    if (
        saved_data is not None
        and isinstance(saved_data, dict)
        and "workspaces" in saved_data
        and isinstance(saved_data["workspaces"], list)
        and len(saved_data["workspaces"]) > 0
    ):
        st.session_state[SESSION_KEY_WORKSPACES] = saved_data["workspaces"]
        st.session_state[SESSION_KEY_ACTIVE_WS_ID] = saved_data.get(
            "active_workspace_id", saved_data["workspaces"][0]["id"]
        )
        st.session_state[SESSION_KEY_REMINDERS] = saved_data.get("reminders", [])
    else:
        today = date.today()
        initial_dates = [today + timedelta(days=i) for i in range(-7, 7)]
        ws_personal = {
            "id": "ws_personal",
            "name": "Personal",
            "description": "My personal productivity workspace.",
            "dates": initial_dates,
            "tasks": [
                {"id": "task_ws_personal_dsa_0", "name": "DSA", "priority": "Medium", "description": "", "recurrence": {"type": "none", "days": []}},
                {"id": "task_ws_personal_project_1", "name": "Project", "priority": "Medium", "description": "", "recurrence": {"type": "none", "days": []}},
                {"id": "task_ws_personal_gym_2", "name": "Gym", "priority": "Medium", "description": "", "recurrence": {"type": "none", "days": []}},
            ],
            "completion": {},
            "daily_target_pct": 80.0,
            "focus_matrix": {},
        }
        st.session_state[SESSION_KEY_WORKSPACES] = [ws_personal]
        st.session_state[SESSION_KEY_ACTIVE_WS_ID] = "ws_personal"
        st.session_state[SESSION_KEY_REMINDERS] = []
        save_all_stores()


def get_workspaces() -> list[dict]:
    """Returns list of workspace dictionaries for current user."""
    init_workspace_store()
    return st.session_state[SESSION_KEY_WORKSPACES]


def get_active_workspace_id() -> str:
    """Returns the ID of the currently active workspace."""
    init_workspace_store()
    return st.session_state[SESSION_KEY_ACTIVE_WS_ID]


def get_active_workspace() -> dict:
    """Returns the active workspace dictionary."""
    init_workspace_store()
    active_id = st.session_state[SESSION_KEY_ACTIVE_WS_ID]
    workspaces = st.session_state[SESSION_KEY_WORKSPACES]

    for ws in workspaces:
        if ws["id"] == active_id:
            return ws

    if workspaces:
        st.session_state[SESSION_KEY_ACTIVE_WS_ID] = workspaces[0]["id"]
        return workspaces[0]

    init_workspace_store()
    return st.session_state[SESSION_KEY_WORKSPACES][0]


def set_active_workspace(ws_id: str) -> None:
    """Switches the active workspace."""
    init_workspace_store()
    workspaces = st.session_state[SESSION_KEY_WORKSPACES]
    ws_ids = [ws["id"] for ws in workspaces]

    if ws_id in ws_ids and ws_id != st.session_state[SESSION_KEY_ACTIVE_WS_ID]:
        st.session_state[SESSION_KEY_ACTIVE_WS_ID] = ws_id
        save_all_stores()


def create_workspace(name: str, description: str = "") -> tuple[bool, str, str | None]:
    """Creates a new workspace belonging to the current user."""
    user = get_current_user()
    if user:
        try:
            new_ws = db_create_workspace(user["id"], name, description)
            init_workspace_store(force=True)
            st.session_state[SESSION_KEY_ACTIVE_WS_ID] = new_ws["id"]
            return True, f"Workspace '{name}' created successfully.", new_ws["id"]
        except Exception as e:
            return False, str(e), None

    init_workspace_store()
    workspaces = st.session_state[SESSION_KEY_WORKSPACES]
    if len(workspaces) >= MAX_WORKSPACES:
        return False, f"Maximum limit of {MAX_WORKSPACES} workspaces reached.", None

    trimmed_name = name.strip()
    if not trimmed_name:
        return False, "Workspace name cannot be empty.", None

    new_id = f"ws_{uuid.uuid4().hex[:8]}"
    today = date.today()
    initial_dates = [today + timedelta(days=i) for i in range(-7, 7)]

    new_ws = {
        "id": new_id,
        "name": trimmed_name,
        "description": description.strip(),
        "dates": initial_dates,
        "tasks": [],
        "completion": {},
        "daily_target_pct": 80.0,
        "focus_matrix": {},
    }

    workspaces.append(new_ws)
    st.session_state[SESSION_KEY_ACTIVE_WS_ID] = new_id
    save_all_stores()
    return True, f"Workspace '{trimmed_name}' created successfully.", new_id


def rename_workspace(ws_id: str, new_name: str, new_description: str = "") -> tuple[bool, str]:
    """Renames and updates description of an existing workspace."""
    trimmed_name = new_name.strip()
    if not trimmed_name:
        return False, "Workspace name cannot be empty."

    user = get_current_user()
    if user:
        res = db_update_workspace(user["id"], ws_id, {"name": trimmed_name, "description": new_description.strip()})
        if res:
            init_workspace_store(force=True)
            return True, "Workspace updated successfully."
        return False, "Workspace not found or unauthorized."

    init_workspace_store()
    workspaces = st.session_state[SESSION_KEY_WORKSPACES]
    for ws in workspaces:
        if ws["id"] == ws_id:
            ws["name"] = trimmed_name
            ws["description"] = new_description.strip()
            save_all_stores()
            return True, "Workspace updated successfully."

    return False, "Workspace not found."


def delete_workspace(ws_id: str) -> tuple[bool, str]:
    """Deletes a workspace. Enforces minimum 1 workspace rule."""
    user = get_current_user()
    if user:
        try:
            ok = db_delete_workspace(user["id"], ws_id)
            if ok:
                init_workspace_store(force=True)
                return True, "Workspace deleted successfully."
            return False, "Workspace not found or unauthorized."
        except Exception as e:
            return False, str(e)

    init_workspace_store()
    workspaces = st.session_state[SESSION_KEY_WORKSPACES]
    if len(workspaces) <= MIN_WORKSPACES:
        return False, "Cannot delete the final remaining workspace."

    target_ws = None
    for ws in workspaces:
        if ws["id"] == ws_id:
            target_ws = ws
            break

    if not target_ws:
        return False, "Workspace not found."

    workspaces.remove(target_ws)
    if st.session_state[SESSION_KEY_ACTIVE_WS_ID] == ws_id:
        st.session_state[SESSION_KEY_ACTIVE_WS_ID] = workspaces[0]["id"]

    save_all_stores()
    return True, "Workspace deleted successfully."


def get_daily_target_pct(ws_id: str | None = None) -> float:
    """Returns daily completion target percentage for specified or active workspace."""
    target_id = ws_id or get_active_workspace_id()
    workspaces = get_workspaces()
    for ws in workspaces:
        if ws["id"] == target_id:
            return float(ws.get("daily_target_pct", 80.0))
    return 80.0


def set_daily_target_pct(target_pct: float, ws_id: str | None = None) -> tuple[bool, str]:
    """Updates daily completion target percentage for specified or active workspace."""
    target_id = ws_id or get_active_workspace_id()
    val = max(1.0, min(100.0, float(target_pct)))

    user = get_current_user()
    if user:
        res = db_update_workspace(user["id"], target_id, {"daily_target_pct": val})
        if res:
            init_workspace_store()
            return True, f"Daily completion target updated to {val:.0f}%."
        return False, "Workspace not found."

    workspaces = get_workspaces()
    for ws in workspaces:
        if ws["id"] == target_id:
            ws["daily_target_pct"] = val
            save_all_stores()
            return True, f"Daily completion target updated to {val:.0f}%."
    return False, "Workspace not found."


def get_focus_tasks(date_obj: date, ws_id: str | None = None) -> list[str]:
    """Returns list of task IDs manually pinned as Focus for the specified date."""
    target_id = ws_id or get_active_workspace_id()
    workspaces = get_workspaces()
    d_iso = date_obj.isoformat()
    for ws in workspaces:
        if ws["id"] == target_id:
            focus_map = ws.get("focus_matrix", {})
            return list(focus_map.get(d_iso, []))
    return []


def is_task_focused_today(date_obj: date, task_id: str, ws_id: str | None = None) -> bool:
    """Checks if a task ID is manually pinned as Focus for date_obj."""
    focused_ids = get_focus_tasks(date_obj, ws_id)
    return task_id in focused_ids


def toggle_focus_task(date_obj: date, task_id: str, ws_id: str | None = None) -> tuple[bool, str]:
    """Toggles manual Focus status for a task ID on a specific date."""
    target_id = ws_id or get_active_workspace_id()
    workspaces = get_workspaces()
    d_iso = date_obj.isoformat()

    user = get_current_user()
    for ws in workspaces:
        if ws["id"] == target_id:
            focus_matrix = dict(ws.get("focus_matrix", {}))
            focus_list = list(focus_matrix.get(d_iso, []))

            if task_id in focus_list:
                focus_list.remove(task_id)
                msg = "Task removed from Focus."
            else:
                focus_list.append(task_id)
                msg = "Task pinned to Focus."

            focus_matrix[d_iso] = focus_list
            ws["focus_matrix"] = focus_matrix

            if user:
                db_update_workspace(user["id"], target_id, {"focus_matrix": focus_matrix})

            save_all_stores()
            return True, msg

    return False, "Workspace not found."
