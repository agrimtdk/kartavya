"""
Task Store Module for kartavya (Phase 9 Public Multi-User Architecture).

Operates on the active workspace object provided by workspace_store.py.
Maintains canonical completion state matrix keyed by stable task_id.
Supports task priorities, descriptions, and recurring task rules.
Routes mutations to user-scoped database store when authenticated.
"""

import uuid
import re
from datetime import date, timedelta
import streamlit as st
from src.data.workspace_store import (
    get_active_workspace,
    get_active_workspace_id,
    save_all_stores,
    init_workspace_store,
)
from src.services.auth_service import get_current_user
from src.db.db_store import (
    create_task as db_create_task,
    update_task as db_update_task,
    delete_task as db_delete_task,
    set_completion as db_set_completion,
    update_workspace as db_update_workspace,
)
from src.config import PRIORITY_CHOICES, PRIORITY_MEDIUM


def is_task_applicable_on_date(task_obj: dict | str, date_obj: date) -> bool:
    """Evaluates whether a recurring or standard task applies to a specific date."""
    if not isinstance(task_obj, dict):
        return True

    rec = task_obj.get("recurrence", {})
    if not isinstance(rec, dict):
        return True

    rec_type = str(rec.get("type", "none")).lower()
    days = rec.get("days", [])

    if rec_type == "none" or rec_type == "daily":
        return True

    w_day = date_obj.weekday()

    if rec_type == "weekdays":
        return w_day < 5  # Mon-Fri

    if rec_type in ["weekly", "custom_weekdays"]:
        if not days:
            return True
        return w_day in days

    return True


def init_task_store() -> None:
    """Ensures workspace store and active workspace timeline matrix are initialized."""
    init_workspace_store()
    active_ws = get_active_workspace()

    if active_ws.get("_task_store_initialized"):
        return

    if "dates" not in active_ws:
        active_ws["dates"] = [date.today() + timedelta(days=i) for i in range(-7, 7)]
    if "tasks" not in active_ws:
        active_ws["tasks"] = []
    if "completion" not in active_ws:
        active_ws["completion"] = {}

    normalized_tasks = []
    name_to_id_map = {}
    ws_id = active_ws.get("id", "ws")

    for idx, t in enumerate(active_ws.get("tasks", [])):
        if isinstance(t, dict) and "id" in t and "name" in t:
            normalized_tasks.append(t)
            name_to_id_map[t["name"]] = t["id"]
        elif isinstance(t, str):
            slug = re.sub(r'[^a-zA-Z0-9]', '_', t).lower()
            stable_id = f"task_{ws_id}_{slug}_{idx}"
            t_obj = {
                "id": stable_id,
                "name": t,
                "priority": "Medium",
                "description": "",
                "recurrence": {"type": "none", "days": []},
            }
            normalized_tasks.append(t_obj)
            name_to_id_map[t] = stable_id

    active_ws["tasks"] = normalized_tasks

    if not isinstance(active_ws.get("completion"), dict):
        active_ws["completion"] = {}
    completion = active_ws["completion"]

    if isinstance(completion, dict):
        for d_iso, date_map in list(completion.items()):
            if isinstance(date_map, dict):
                new_date_map = {}
                for k, v in date_map.items():
                    mapped_id = name_to_id_map.get(k, k)
                    new_date_map[mapped_id] = bool(v)
                completion[d_iso] = new_date_map
            else:
                completion[d_iso] = {}

    dates = active_ws.get("dates", [])
    for d in dates:
        d_iso = d.isoformat() if isinstance(d, date) else str(d)
        if d_iso not in completion or not isinstance(completion[d_iso], dict):
            completion[d_iso] = {}
        for t in normalized_tasks:
            t_id = t["id"]
            if t_id not in completion[d_iso]:
                completion[d_iso][t_id] = False
                
    active_ws["_task_store_initialized"] = True


def get_dates() -> list[date]:
    """Get sorted list of timeline dates for the active workspace."""
    init_task_store()
    active_ws = get_active_workspace()
    return sorted(active_ws["dates"])


def get_tasks() -> list[dict]:
    """Get list of defined task objects for the active workspace."""
    init_task_store()
    active_ws = get_active_workspace()
    return list(active_ws["tasks"])


def get_task_by_id(task_id: str) -> dict | None:
    """Returns task object dictionary matching task_id, or None."""
    tasks = get_tasks()
    for t in tasks:
        t_id = t["id"] if isinstance(t, dict) else str(t)
        if t_id == task_id:
            return t
    return None


def get_completion(date_obj: date, task_id: str, today_ref: date | None = None, completion_matrix: dict | None = None) -> bool:
    """Check completion status for active workspace task using optional pre-loaded matrix."""
    t_ref = today_ref or date.today()
    if date_obj > t_ref:
        return False

    if completion_matrix is None:
        init_task_store()
        active_ws = get_active_workspace()
        completion_matrix = active_ws.get("completion") or {}

    d_iso = date_obj.isoformat()
    date_map = completion_matrix.get(d_iso) or {}
    return bool(date_map.get(task_id, False))


def set_completion(date_obj: date, task_id: str, value: bool, today_ref: date | None = None) -> bool:
    """
    Set completion status for active workspace task.
    Rejects modification if date_obj is in the future.
    """
    t_ref = today_ref or date.today()
    if date_obj > t_ref:
        return False

    init_task_store()
    active_ws = get_active_workspace()
    ws_id = active_ws["id"]
    user = get_current_user()

    d_iso = date_obj.isoformat()
    if "completion" not in active_ws or not isinstance(active_ws["completion"], dict):
        active_ws["completion"] = {}

    if d_iso not in active_ws["completion"] or not isinstance(active_ws["completion"][d_iso], dict):
        active_ws["completion"][d_iso] = {}

    new_val = bool(value)
    active_ws["completion"][d_iso][task_id] = new_val

    if user:
        db_set_completion(user["id"], ws_id, task_id, date_obj, new_val, today_ref=t_ref)

    save_all_stores()
    return True


def add_previous_day() -> date:
    """Appends previous chronological date to active workspace timeline."""
    init_task_store()
    active_ws = get_active_workspace()
    dates = get_dates()

    earliest_date = dates[0] if dates else date.today()
    prev_date = earliest_date - timedelta(days=1)
    prev_iso = prev_date.isoformat()

    if prev_date not in active_ws["dates"]:
        active_ws["dates"].append(prev_date)
        active_ws["dates"].sort()

    if prev_iso not in active_ws["completion"]:
        active_ws["completion"][prev_iso] = {}

    tasks = get_tasks()
    for t in tasks:
        t_id = t["id"] if isinstance(t, dict) else str(t)
        if t_id not in active_ws["completion"][prev_iso]:
            active_ws["completion"][prev_iso][t_id] = False

    user = get_current_user()
    if user:
        iso_dates = [d.isoformat() for d in active_ws["dates"]]
        db_update_workspace(user["id"], active_ws["id"], {"dates": iso_dates})

    save_all_stores()
    return prev_date


def add_future_day() -> date:
    """Appends next chronological date to active workspace timeline."""
    init_task_store()
    active_ws = get_active_workspace()
    dates = get_dates()

    latest_date = dates[-1] if dates else date.today()
    next_date = latest_date + timedelta(days=1)
    next_iso = next_date.isoformat()

    if next_date not in active_ws["dates"]:
        active_ws["dates"].append(next_date)
        active_ws["dates"].sort()

    if next_iso not in active_ws["completion"]:
        active_ws["completion"][next_iso] = {}

    tasks = get_tasks()
    for t in tasks:
        t_id = t["id"] if isinstance(t, dict) else str(t)
        if t_id not in active_ws["completion"][next_iso]:
            active_ws["completion"][next_iso][t_id] = False

    user = get_current_user()
    if user:
        iso_dates = [d.isoformat() for d in active_ws["dates"]]
        db_update_workspace(user["id"], active_ws["id"], {"dates": iso_dates})

    save_all_stores()
    return next_date


add_day = add_future_day


def add_task(
    name: str,
    priority: str = PRIORITY_MEDIUM,
    description: str = "",
    recurrence: dict | None = None,
) -> tuple[bool, str]:
    """Adds a new task to the active workspace."""
    init_task_store()
    active_ws = get_active_workspace()
    ws_id = active_ws["id"]
    trimmed_name = name.strip()

    if not trimmed_name:
        return False, "Task name cannot be empty."

    existing_tasks = get_tasks()
    if any((t["name"] if isinstance(t, dict) else str(t)).lower() == trimmed_name.lower() for t in existing_tasks):
        return False, f"Task '{trimmed_name}' already exists in workspace."

    if priority not in PRIORITY_CHOICES:
        priority = PRIORITY_MEDIUM

    rec = recurrence if isinstance(recurrence, dict) else {"type": "none", "days": []}
    user = get_current_user()

    if user:
        t_dict = db_create_task(user["id"], ws_id, trimmed_name, priority, description, rec)
        init_workspace_store()
        return True, f"Task '{trimmed_name}' added successfully."

    task_id = f"task_{ws_id}_{uuid.uuid4().hex[:8]}"
    new_task = {
        "id": task_id,
        "name": trimmed_name,
        "priority": priority,
        "description": description.strip(),
        "recurrence": rec,
    }
    active_ws["tasks"].append(new_task)

    dates = get_dates()
    for d in dates:
        d_iso = d.isoformat()
        if d_iso not in active_ws["completion"]:
            active_ws["completion"][d_iso] = {}
        active_ws["completion"][d_iso][task_id] = False

    save_all_stores()
    return True, f"Task '{trimmed_name}' added successfully."


def rename_task(task_id: str, new_name: str) -> tuple[bool, str]:
    """Renames a task without changing stable ID."""
    trimmed_name = new_name.strip()
    if not trimmed_name:
        return False, "Task name cannot be empty."

    active_ws = get_active_workspace()
    ws_id = active_ws["id"]
    user = get_current_user()

    if user:
        res = db_update_task(user["id"], ws_id, task_id, {"name": trimmed_name})
        if res:
            init_workspace_store()
            return True, f"Task renamed to '{trimmed_name}'."
        return False, "Task not found or unauthorized."

    tasks = get_tasks()
    target = next((t for t in tasks if (t["id"] if isinstance(t, dict) else str(t)) == task_id), None)
    if not target or not isinstance(target, dict):
        return False, "Task not found."

    target["name"] = trimmed_name
    save_all_stores()
    return True, f"Task renamed to '{trimmed_name}'."


def update_task_metadata(
    task_id: str,
    name: str,
    priority: str,
    description: str,
    recurrence: dict,
) -> tuple[bool, str]:
    """Updates task name, priority, description, and recurrence."""
    active_ws = get_active_workspace()
    ws_id = active_ws["id"]
    user = get_current_user()

    trimmed_name = name.strip()
    if not trimmed_name:
        return False, "Task name cannot be empty."

    if user:
        res = db_update_task(
            user["id"],
            ws_id,
            task_id,
            {"name": trimmed_name, "priority": priority, "description": description, "recurrence": recurrence},
        )
        if res:
            init_workspace_store()
            return True, "Task updated successfully."
        return False, "Task not found or unauthorized."

    tasks = get_tasks()
    target = next((t for t in tasks if (t["id"] if isinstance(t, dict) else str(t)) == task_id), None)
    if not target or not isinstance(target, dict):
        return False, "Task not found."

    target["name"] = trimmed_name
    if priority in PRIORITY_CHOICES:
        target["priority"] = priority
    target["description"] = description.strip()
    if isinstance(recurrence, dict):
        target["recurrence"] = recurrence

    save_all_stores()
    return True, "Task updated successfully."


def remove_task(task_id: str) -> bool:
    """Removes a task from active workspace."""
    active_ws = get_active_workspace()
    ws_id = active_ws["id"]
    user = get_current_user()

    if user:
        ok = db_delete_task(user["id"], ws_id, task_id)
        if ok:
            init_workspace_store()
            return True
        return False

    init_task_store()
    tasks = get_tasks()
    target = next((t for t in tasks if (t["id"] if isinstance(t, dict) else str(t)) == task_id), None)
    if target:
        active_ws["tasks"].remove(target)
        dates = get_dates()
        for d in dates:
            d_iso = d.isoformat()
            if d_iso in active_ws["completion"]:
                active_ws["completion"][d_iso].pop(task_id, None)
            chk_key = f"chk_{ws_id}_{d_iso}_{task_id}"
            st.session_state.pop(chk_key, None)

        save_all_stores()
        return True

    return False


def get_daily_completion(date_obj: date, today_ref: date | None = None, tasks_list: list | None = None, completion_matrix: dict | None = None) -> dict:
    """Calculates completion stats for a date in active workspace using pre-loaded matrices."""
    t_ref = today_ref or date.today()
    tasks = tasks_list if tasks_list is not None else get_tasks()
    applicable_tasks = [t for t in tasks if is_task_applicable_on_date(t, date_obj)]
    total = len(applicable_tasks)
    if total == 0 or date_obj > t_ref:
        return {"completed": 0, "total": total, "percentage": 0}

    completed = sum(
        1 for t in applicable_tasks
        if get_completion(date_obj, t["id"] if isinstance(t, dict) else str(t), today_ref=t_ref, completion_matrix=completion_matrix)
    )
    pct = round((completed / total) * 100)
    return {"completed": completed, "total": total, "percentage": pct}


def get_overall_completion(today_ref: date | None = None) -> dict:
    """Calculates overall completion stats for active workspace using optimized single-load matrices."""
    t_ref = today_ref or date.today()
    dates = get_dates()
    tasks = get_tasks()
    
    init_task_store()
    active_ws = get_active_workspace()
    completion_matrix = active_ws.get("completion") or {}

    total_possible = 0
    total_completed = 0

    for d in dates:
        app_tasks = [t for t in tasks if is_task_applicable_on_date(t, d)]
        total_possible += len(app_tasks)
        if d <= t_ref:
            total_completed += sum(
                1 for t in app_tasks
                if get_completion(d, t["id"] if isinstance(t, dict) else str(t), today_ref=t_ref, completion_matrix=completion_matrix)
            )

    if total_possible == 0:
        return {"completed": 0, "total": 0, "percentage": 0}

    pct = round((total_completed / total_possible) * 100)
    return {"completed": total_completed, "total": total_possible, "percentage": pct}
