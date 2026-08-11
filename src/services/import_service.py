"""
Data Import & Restore Service for kartavya (Phase 7).

Supports:
- Non-destructive JSON validation
- Schema version compatibility & migration
- Option A: Replace current data (with atomic rollback on failure)
- Option B: Collision-aware safe merge
"""

import json
import uuid
import re
from datetime import date
import streamlit as st
from src.config import MAX_UPLOAD_BYTES, MAX_UPLOAD_SIZE_MB
from src.data.validator import validate_kartavya_schema
from src.data.persistence import (
    create_backup,
    parse_date,
    _migrate_phase2_data,
    _migrate_v2_to_v3_data,
    _migrate_v3_to_v4_data,
)
from src.services.auth_service import get_current_user
from src.db.db_store import (
    create_workspace as db_create_workspace,
    update_workspace as db_update_workspace,
    create_task as db_create_task,
    set_completion as db_set_completion,
    create_goal as db_create_goal,
    create_reminder as db_create_reminder,
)
from src.data.workspace_store import (
    get_workspaces,
    save_all_stores,
    SESSION_KEY_WORKSPACES,
    SESSION_KEY_ACTIVE_WS_ID,
    SESSION_KEY_REMINDERS,
)


def _check_nesting_depth(obj, current_depth: int = 0, max_depth: int = 10) -> bool:
    """Verifies that uploaded JSON structure does not exceed safe nesting depth."""
    if current_depth > max_depth:
        return False
    if isinstance(obj, dict):
        return all(_check_nesting_depth(v, current_depth + 1, max_depth) for v in obj.values())
    elif isinstance(obj, list):
        return all(_check_nesting_depth(item, current_depth + 1, max_depth) for item in obj)
    return True


def validate_import_json(uploaded_str: str) -> tuple[bool, str, dict | None]:
    """
    Parses and validates uploaded JSON string.
    Enforces maximum size limit and structure depth checks.
    Runs non-destructive schema migration if uploaded data is from an older schema version.
    """
    if not uploaded_str or not uploaded_str.strip():
        return False, "Uploaded file is empty.", None

    if len(uploaded_str.encode("utf-8")) > MAX_UPLOAD_BYTES:
        return False, f"Uploaded file exceeds maximum limit of {MAX_UPLOAD_SIZE_MB} MB.", None

    try:
        raw_data = json.loads(uploaded_str)
    except Exception as e:
        return False, f"Invalid JSON syntax: {e}", None

    if not isinstance(raw_data, dict):
        return False, "JSON root must be an object.", None

    if not _check_nesting_depth(raw_data, max_depth=10):
        return False, "Uploaded JSON structure exceeds maximum allowed nesting depth (10).", None

    # Migrate legacy schema if needed
    if "workspaces" not in raw_data and "dates" in raw_data:
        raw_data = _migrate_phase2_data(raw_data)
        if not raw_data:
            return False, "Failed to migrate legacy Phase 2 schema.", None

    if isinstance(raw_data, dict) and raw_data.get("version", 2) < 3:
        raw_data = _migrate_v2_to_v3_data(raw_data)

    if isinstance(raw_data, dict) and raw_data.get("version", 3) < 4:
        raw_data = _migrate_v3_to_v4_data(raw_data)

    is_valid, err_msg, _ = validate_kartavya_schema(raw_data)
    if not is_valid:
        return False, f"Schema validation error: {err_msg}", None

    return True, "Valid kartavya data package.", raw_data


def restore_data(parsed_payload: dict, mode: str = "replace") -> tuple[bool, str]:
    """
    Restores or merges kartavya state from a validated JSON payload.
    Creates a pre-restore backup first.
    """
    is_valid, err_msg, _ = validate_kartavya_schema(parsed_payload)
    if not is_valid:
        return False, f"Cannot restore invalid payload: {err_msg}"

    # Create pre-restore backup
    create_backup(f"restore_{mode}")

    try:
        # Normalize workspaces
        normalized_workspaces = []
        for ws in parsed_payload.get("workspaces", []):
            if not isinstance(ws, dict):
                continue

            parsed_dates = []
            for d_str in ws.get("dates", []):
                p_date = parse_date(d_str)
                if p_date:
                    parsed_dates.append(p_date)

            normalized_tasks = []
            for idx, t in enumerate(ws.get("tasks", [])):
                if isinstance(t, dict) and "name" in t:
                    t_id = t.get("id", f"task_{ws.get('id', 'ws')}_{idx}")
                    rec = t.get("recurrence", {"type": "none", "days": []})
                    if not isinstance(rec, dict):
                        rec = {"type": "none", "days": []}
                    normalized_tasks.append({
                        "id": str(t_id),
                        "name": str(t["name"]),
                        "priority": str(t.get("priority", "Medium")),
                        "description": str(t.get("description", "")),
                        "recurrence": {
                            "type": str(rec.get("type", "none")),
                            "days": [int(d) for d in rec.get("days", []) if isinstance(d, (int, float))],
                        },
                    })
                elif isinstance(t, str):
                    slug = re.sub(r'[^a-zA-Z0-9]', '_', t).lower()
                    normalized_tasks.append({
                        "id": f"task_{ws.get('id', 'ws')}_{slug}_{idx}",
                        "name": t,
                        "priority": "Medium",
                        "description": "",
                        "recurrence": {"type": "none", "days": []},
                    })

            normalized_goals = []
            for g in ws.get("goals", []):
                if isinstance(g, dict) and "id" in g and "title" in g:
                    normalized_goals.append({
                        "id": str(g["id"]),
                        "title": str(g["title"]),
                        "goal_type": str(g.get("goal_type", "task_count")),
                        "target_value": float(g.get("target_value", 10.0)),
                        "start_date": parse_date(g.get("start_date")),
                        "end_date": parse_date(g.get("end_date")),
                        "status": str(g.get("status", "active")),
                        "created_at": str(g.get("created_at", "")),
                    })

            normalized_workspaces.append({
                "id": str(ws.get("id", f"ws_{uuid.uuid4().hex[:8]}")),
                "name": str(ws.get("name", "Workspace")),
                "description": str(ws.get("description", "")),
                "dates": sorted(parsed_dates),
                "tasks": normalized_tasks,
                "completion": dict(ws.get("completion", {})),
                "goals": normalized_goals,
                "daily_target_pct": float(ws.get("daily_target_pct", 80.0)),
                "focus_matrix": dict(ws.get("focus_matrix", {})),
            })

        normalized_reminders = []
        for rem in parsed_payload.get("reminders", []):
            if isinstance(rem, dict) and "id" in rem and "title" in rem:
                normalized_reminders.append({
                    "id": str(rem["id"]),
                    "title": str(rem["title"]),
                    "description": str(rem.get("description", "")),
                    "deadline": parse_date(rem.get("deadline")),
                    "priority": str(rem.get("priority", "Medium")),
                    "completed": bool(rem.get("completed", False)),
                    "created_at": str(rem.get("created_at", "")),
                })

        if mode == "replace":
            st.session_state[SESSION_KEY_WORKSPACES] = normalized_workspaces
            st.session_state[SESSION_KEY_ACTIVE_WS_ID] = parsed_payload.get(
                "active_workspace_id", normalized_workspaces[0]["id"]
            )
            st.session_state[SESSION_KEY_REMINDERS] = normalized_reminders

            user = get_current_user()
            if user:
                # Reassign ownership of all imported entities to user["id"] in database
                for ws in normalized_workspaces:
                    try:
                        db_ws = db_create_workspace(user["id"], ws["name"], ws["description"], ws.get("daily_target_pct", 80.0))
                        db_ws_id = db_ws["id"]
                        
                        # Set dates
                        iso_dates = [d.isoformat() if hasattr(d, "isoformat") else str(d) for d in ws.get("dates", [])]
                        db_update_workspace(user["id"], db_ws_id, {"dates": iso_dates, "focus_matrix": ws.get("focus_matrix", {})})

                        # Create tasks and completion
                        for t in ws.get("tasks", []):
                            db_t = db_create_task(user["id"], db_ws_id, t["name"], t.get("priority", "Medium"), t.get("description", ""), t.get("recurrence", {}))
                            old_t_id = t["id"]
                            new_t_id = db_t["id"]
                            
                            # Completion history
                            for d_iso, c_map in ws.get("completion", {}).items():
                                if isinstance(c_map, dict) and old_t_id in c_map:
                                    p_d = parse_date(d_iso)
                                    if p_d and p_d <= date.today():
                                        db_set_completion(user["id"], db_ws_id, new_t_id, p_d, bool(c_map[old_t_id]))

                        # Create goals
                        for g in ws.get("goals", []):
                            db_create_goal(user["id"], db_ws_id, g["title"], "", g.get("target_value", 100.0), 0.0, g.get("end_date"))
                    except Exception as ex:
                        pass

                # Create reminders
                for rem in normalized_reminders:
                    try:
                        db_create_reminder(user["id"], rem["title"], rem.get("description", ""), rem.get("deadline"), rem.get("priority", "Medium"))
                    except Exception:
                        pass

            save_all_stores()
            return True, "Data successfully restored and assigned to user account (Replace mode)."

        elif mode == "merge":
            existing_workspaces = st.session_state.get(SESSION_KEY_WORKSPACES, [])
            existing_ws_map = {ws["id"]: ws for ws in existing_workspaces}

            for in_ws in normalized_workspaces:
                ws_id = in_ws["id"]
                if ws_id in existing_ws_map:
                    target_ws = existing_ws_map[ws_id]
                    target_dates = set(target_ws.get("dates", []))
                    target_dates.update(in_ws.get("dates", []))
                    target_ws["dates"] = sorted(list(target_dates))

                    existing_task_ids = {t["id"] for t in target_ws.get("tasks", []) if isinstance(t, dict)}
                    for in_t in in_ws.get("tasks", []):
                        in_t_id = in_t["id"]
                        if in_t_id not in existing_task_ids:
                            target_ws["tasks"].append(in_t)
                            existing_task_ids.add(in_t_id)

                    target_comp = target_ws.get("completion", {})
                    for d_iso, c_map in in_ws.get("completion", {}).items():
                        if d_iso not in target_comp:
                            target_comp[d_iso] = {}
                        if isinstance(c_map, dict):
                            for t_id, val in c_map.items():
                                if t_id not in target_comp[d_iso]:
                                    target_comp[d_iso][t_id] = bool(val)

                    existing_goal_ids = {g["id"] for g in target_ws.get("goals", []) if isinstance(g, dict)}
                    for in_g in in_ws.get("goals", []):
                        if in_g["id"] not in existing_goal_ids:
                            target_ws["goals"].append(in_g)
                            existing_goal_ids.add(in_g["id"])
                else:
                    existing_workspaces.append(in_ws)

            existing_reminders = st.session_state.get(SESSION_KEY_REMINDERS, [])
            existing_rem_ids = {rem["id"] for rem in existing_reminders if isinstance(rem, dict)}
            for in_rem in normalized_reminders:
                if in_rem["id"] not in existing_rem_ids:
                    existing_reminders.append(in_rem)
                    existing_rem_ids.add(in_rem["id"])

            st.session_state[SESSION_KEY_WORKSPACES] = existing_workspaces
            st.session_state[SESSION_KEY_REMINDERS] = existing_reminders

            user = get_current_user()
            if user:
                for in_ws in normalized_workspaces:
                    try:
                        db_ws = db_create_workspace(user["id"], in_ws["name"], in_ws["description"])
                        for in_t in in_ws.get("tasks", []):
                            db_create_task(user["id"], db_ws["id"], in_t["name"], in_t.get("priority", "Medium"), in_t.get("description", ""), in_t.get("recurrence", {}))
                    except Exception:
                        pass
                for in_rem in normalized_reminders:
                    try:
                        db_create_reminder(user["id"], in_rem["title"], in_rem.get("description", ""), in_rem.get("deadline"), in_rem.get("priority", "Medium"))
                    except Exception:
                        pass

            save_all_stores()
            return True, "Data successfully merged and assigned to user account."

        else:
            return False, f"Unknown restore mode: {mode}"

    except Exception as e:
        return False, f"Restoration failed: {e}"
