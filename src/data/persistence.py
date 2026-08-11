"""
Local Persistence Layer for kartavya (Phase 7 Production Polish & Reliability).

Handles loading, atomic saving, selective backups (no rerun churn),
auto-recovery from corrupted JSON, and idempotent schema upgrades for local JSON file (data/kartavya_data.json).
Isolates file I/O operations from application business logic and Streamlit UI.
"""

import os
import json
import shutil
import re
from datetime import date, datetime
import logging
import streamlit as st
from src.config import (
    PROJECT_ROOT,
    KARTAVYA_MODE,
    KARTAVYA_DATA_DIR,
    MAX_BACKUPS_COUNT,
)
from src.data.validator import validate_kartavya_schema

logger = logging.getLogger(__name__)

# Absolute paths to data storage (based on KARTAVYA_DATA_DIR or PROJECT_ROOT)
DATA_DIR = KARTAVYA_DATA_DIR
DATA_FILE_PATH = os.path.join(DATA_DIR, "kartavya_data.json")
EXAMPLE_DATA_PATH = os.path.join(DATA_DIR, "example_kartavya_data.json")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
LEGACY_BACKUP_FILE_PATH = os.path.join(DATA_DIR, "kartavya_data.json.bak")
TMP_FILE_PATH = os.path.join(DATA_DIR, "kartavya_data.json.tmp")



def parse_date(val: date | datetime | str | tuple | list | None) -> date | None:
    """
    Robustly parses various date formats (date, datetime, ISO string, tuple, list, or Python repr string)
    into a clean datetime.date object, or None if invalid/empty.
    Guaranteed zero circular imports.
    """
    if val is None or val == "":
        return None

    if isinstance(val, (tuple, list)):
        if len(val) > 0:
            return parse_date(val[0])
        return None

    if isinstance(val, datetime):
        return val.date()

    if isinstance(val, date):
        return val

    if isinstance(val, str):
        val_str = val.strip()
        if not val_str:
            return None

        # 1. Standard ISO format YYYY-MM-DD
        try:
            return date.fromisoformat(val_str)
        except (ValueError, TypeError):
            pass

        # 2. Extract YYYY-MM-DD using regex
        iso_match = re.search(r'(\d{4}-\d{2}-\d{2})', val_str)
        if iso_match:
            try:
                return date.fromisoformat(iso_match.group(1))
            except (ValueError, TypeError):
                pass

        # 3. Handle Python repr strings like "(datetime.date(2026, 8, 10),)" or "datetime.date(2026, 8, 10)"
        repr_match = re.search(r'datetime\.date\((\d{4}),\s*(\d{1,2}),\s*(\d{1,2})\)', val_str)
        if repr_match:
            try:
                y = int(repr_match.group(1))
                m = int(repr_match.group(2))
                d = int(repr_match.group(3))
                return date(y, m, d)
            except (ValueError, TypeError):
                pass

    return None


def rotate_backups() -> None:
    """
    Ensures backup directory exists and keeps at most MAX_BACKUPS_COUNT (5) recent backup files.
    Deletes older backup files.
    """
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        backup_files = [
            os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR)
            if f.endswith(".bak") or f.endswith(".json")
        ]
        backup_files.sort(key=lambda p: os.path.getmtime(p))

        while len(backup_files) > MAX_BACKUPS_COUNT:
            oldest = backup_files.pop(0)
            try:
                os.remove(oldest)
                logger.info(f"Rotated out old backup: {oldest}")
            except Exception as e:
                logger.warning(f"Could not remove old backup {oldest}: {e}")
    except Exception as e:
        logger.warning(f"Error during backup rotation: {e}")


def create_backup(reason_tag: str = "manual") -> str | None:
    """
    Explicitly creates a timestamped backup of the current valid kartavya_data.json.
    Called ONLY before destructive operations (Restore, Reset, Migration).
    Does NOT run on standard saves to avoid rerun churn.
    Bypasses disk backups when running in web_demo mode.
    """
    if KARTAVYA_MODE == "web_demo":
        return None

    if not os.path.exists(DATA_FILE_PATH):
        return None

    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"kartavya_data_{timestamp}_{reason_tag}.bak"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)

        shutil.copy2(DATA_FILE_PATH, backup_path)
        logger.info(f"Created backup at {backup_path} ({reason_tag})")
        rotate_backups()
        return backup_path
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return None


def get_available_backups() -> list[dict]:
    """Returns list of existing backup file dictionaries sorted newest first."""
    if not os.path.exists(BACKUP_DIR):
        return []

    backups = []
    for filename in os.listdir(BACKUP_DIR):
        if filename.endswith(".bak") or filename.endswith(".json"):
            full_path = os.path.join(BACKUP_DIR, filename)
            mtime = os.path.getmtime(full_path)
            size = os.path.getsize(full_path)
            backups.append({
                "filename": filename,
                "path": full_path,
                "timestamp": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "size_bytes": size,
            })

    backups.sort(key=lambda b: b["path"], reverse=True)
    return backups


def _migrate_phase2_data(raw_data: dict) -> dict | None:
    """
    Idempotent migrator: Converts Phase 2 single-timeline schema into Phase 3 multi-workspace schema.
    Preserves all existing dates, tasks, and completion matrix intact into a 'Personal' workspace.
    """
    if "dates" not in raw_data or "tasks" not in raw_data or "completion" not in raw_data:
        return None

    create_backup("migrate_v2")

    ws_personal = {
        "id": "ws_personal",
        "name": "Personal",
        "description": "My personal productivity workspace.",
        "dates": raw_data.get("dates", []),
        "tasks": raw_data.get("tasks", []),
        "completion": raw_data.get("completion", {}),
    }

    migrated_payload = {
        "version": 2,
        "active_workspace_id": "ws_personal",
        "workspaces": [ws_personal],
        "reminders": [],
    }

    save_data(
        workspaces=migrated_payload["workspaces"],
        active_ws_id=migrated_payload["active_workspace_id"],
        reminders=migrated_payload["reminders"],
    )

    return migrated_payload


def _migrate_v2_to_v3_data(raw_data: dict) -> dict:
    """
    Idempotent migrator: Adds 'goals': [] to each workspace dictionary for Phase 5.
    Upgrades schema version to 3.
    """
    if not isinstance(raw_data, dict):
        return raw_data

    if raw_data.get("version", 2) < 3:
        create_backup("migrate_v3")

    workspaces = raw_data.get("workspaces", [])
    if isinstance(workspaces, list):
        for ws in workspaces:
            if isinstance(ws, dict) and "goals" not in ws:
                ws["goals"] = []

    raw_data["version"] = 3
    return raw_data


def _migrate_v3_to_v4_data(raw_data: dict) -> dict:
    """
    Idempotent migrator for Phase 6:
    1. Converts existing string tasks into task objects with stable unique IDs:
       {"id": str, "name": str, "priority": "Medium", "description": "", "recurrence": {"type": "none", "days": []}}
    2. Re-keys existing completion matrices from task names to task IDs without changing True/False values.
    3. Adds 'daily_target_pct': 80.0 and 'focus_matrix': {} per workspace.
    4. Upgrades schema version to 4.
    """
    if not isinstance(raw_data, dict):
        return raw_data

    if raw_data.get("version", 3) < 4:
        create_backup("migrate_v4")

    workspaces = raw_data.get("workspaces", [])
    if isinstance(workspaces, list):
        for ws in workspaces:
            if not isinstance(ws, dict):
                continue

            if "daily_target_pct" not in ws:
                ws["daily_target_pct"] = 80.0
            if "focus_matrix" not in ws or not isinstance(ws["focus_matrix"], dict):
                ws["focus_matrix"] = {}

            raw_tasks = ws.get("tasks", [])
            completion = ws.get("completion", {})
            if not isinstance(completion, dict):
                completion = {}
                ws["completion"] = completion

            if isinstance(raw_tasks, list) and any(isinstance(t, str) for t in raw_tasks):
                upgraded_tasks = []
                name_to_id_map = {}

                for idx, t_entry in enumerate(raw_tasks):
                    if isinstance(t_entry, str):
                        t_name = t_entry
                        slug = re.sub(r'[^a-zA-Z0-9]', '_', t_name).lower()
                        stable_id = f"task_{ws.get('id', 'ws')}_{slug}_{idx}"
                        t_obj = {
                            "id": stable_id,
                            "name": t_name,
                            "priority": "Medium",
                            "description": "",
                            "recurrence": {"type": "none", "days": []},
                        }
                        upgraded_tasks.append(t_obj)
                        name_to_id_map[t_name] = stable_id
                    elif isinstance(t_entry, dict) and "name" in t_entry:
                        t_id = t_entry.get("id", f"task_{ws.get('id', 'ws')}_{idx}")
                        t_obj = {
                            "id": t_id,
                            "name": t_entry["name"],
                            "priority": t_entry.get("priority", "Medium"),
                            "description": t_entry.get("description", ""),
                            "recurrence": t_entry.get("recurrence", {"type": "none", "days": []}),
                        }
                        upgraded_tasks.append(t_obj)
                        name_to_id_map[t_entry["name"]] = t_id

                new_completion = {}
                for d_iso, date_map in completion.items():
                    if isinstance(date_map, dict):
                        new_date_map = {}
                        for k, v in date_map.items():
                            mapped_id = name_to_id_map.get(k, k)
                            new_date_map[mapped_id] = bool(v)
                        new_completion[d_iso] = new_date_map
                    else:
                        new_completion[d_iso] = {}

                ws["tasks"] = upgraded_tasks
                ws["completion"] = new_completion

            elif isinstance(raw_tasks, list):
                for idx, t_obj in enumerate(raw_tasks):
                    if isinstance(t_obj, dict):
                        if "id" not in t_obj:
                            t_obj["id"] = f"task_{ws.get('id', 'ws')}_{idx}"
                        if "priority" not in t_obj:
                            t_obj["priority"] = "Medium"
                        if "description" not in t_obj:
                            t_obj["description"] = ""
                        if "recurrence" not in t_obj:
                            t_obj["recurrence"] = {"type": "none", "days": []}

    raw_data["version"] = 4
    return raw_data


def _attempt_backup_recovery() -> dict | None:
    """
    Scans data/backups directory for the most recent valid backup file if primary file is corrupt.
    Returns recovered normalized payload dict or None.
    """
    backups = get_available_backups()
    for b in backups:
        b_path = b["path"]
        try:
            with open(b_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            is_valid, _, _ = validate_kartavya_schema(data)
            if is_valid:
                logger.info(f"Successfully recovered from backup: {b['filename']}")
                st.session_state["kartavya_recovered_from_backup"] = b["filename"]
                return data
        except Exception as e:
            logger.warning(f"Backup file {b_path} corrupt or unparseable: {e}")
    return None


def load_data() -> dict | None:
    """
    Safely loads multi-workspace data, workspace goals, and global reminders.
    In web_demo mode, loads synthetic template from example file without touching kartavya_data.json.
    Performs safe, idempotent schema migrations (v2 -> v3 -> v4) if needed.
    Auto-recovers from recent valid backup if primary JSON file is corrupt.
    """
    if KARTAVYA_MODE == "web_demo":
        target_path = EXAMPLE_DATA_PATH if os.path.exists(EXAMPLE_DATA_PATH) else DATA_FILE_PATH
        if not os.path.exists(target_path):
            return None
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except Exception:
            return None
    else:
        if not os.path.exists(DATA_FILE_PATH):
            return None

        raw_data = None
        try:
            with open(DATA_FILE_PATH, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except Exception as e:
            logger.error(f"Error reading primary kartavya_data.json: {e}. Attempting auto-recovery...")
            raw_data = _attempt_backup_recovery()

    if raw_data is None:
        return None


    # Detect Phase 2 single-timeline schema and perform idempotent migration
    if isinstance(raw_data, dict) and "workspaces" not in raw_data and "dates" in raw_data:
        raw_data = _migrate_phase2_data(raw_data)
        if raw_data is None:
            return None

    if isinstance(raw_data, dict) and raw_data.get("version", 2) < 3:
        raw_data = _migrate_v2_to_v3_data(raw_data)

    if isinstance(raw_data, dict) and raw_data.get("version", 3) < 4:
        raw_data = _migrate_v3_to_v4_data(raw_data)

    # Validate Schema structure non-destructively
    is_valid, err_msg, _ = validate_kartavya_schema(raw_data)
    if not is_valid:
        logger.warning(f"Schema validation failed: {err_msg}. Attempting backup recovery...")
        recovered = _attempt_backup_recovery()
        if recovered:
            raw_data = recovered
        else:
            return None

    normalized_workspaces = []
    for ws in raw_data.get("workspaces", []):
        if not isinstance(ws, dict) or "id" not in ws or "name" not in ws:
            continue

        parsed_dates = []
        for d_str in ws.get("dates", []):
            p_date = parse_date(d_str)
            if p_date:
                parsed_dates.append(p_date)

        normalized_tasks = []
        for idx, t in enumerate(ws.get("tasks", [])):
            if isinstance(t, dict) and "id" in t and "name" in t:
                rec = t.get("recurrence", {"type": "none", "days": []})
                if not isinstance(rec, dict):
                    rec = {"type": "none", "days": []}
                normalized_tasks.append({
                    "id": str(t["id"]),
                    "name": str(t["name"]),
                    "priority": str(t.get("priority", "Medium")),
                    "description": str(t.get("description", "")),
                    "recurrence": {
                        "type": str(rec.get("type", "none")),
                        "days": [int(d) for d in rec.get("days", []) if isinstance(d, (int, float))],
                    },
                })
            elif isinstance(t, str):
                t_name = str(t)
                slug = re.sub(r'[^a-zA-Z0-9]', '_', t_name).lower()
                normalized_tasks.append({
                    "id": f"task_{ws['id']}_{slug}_{idx}",
                    "name": t_name,
                    "priority": "Medium",
                    "description": "",
                    "recurrence": {"type": "none", "days": []},
                })

        raw_goals = ws.get("goals", [])
        normalized_goals = []
        if isinstance(raw_goals, list):
            for g in raw_goals:
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

        raw_comp = ws.get("completion")
        normalized_comp = {}
        if isinstance(raw_comp, dict):
            for d_k, d_v in raw_comp.items():
                if isinstance(d_v, dict):
                    normalized_comp[str(d_k)] = {str(tk): bool(tv) for tk, tv in d_v.items()}
                else:
                    normalized_comp[str(d_k)] = {}

        normalized_workspaces.append({
            "id": str(ws["id"]),
            "name": str(ws["name"]),
            "description": str(ws.get("description", "")),
            "dates": sorted(parsed_dates),
            "tasks": normalized_tasks,
            "completion": normalized_comp,
            "goals": normalized_goals,
            "daily_target_pct": float(ws.get("daily_target_pct", 80.0)),
            "focus_matrix": dict(ws.get("focus_matrix") or {}),
        })


    if not normalized_workspaces:
        return None

    active_ws_id = str(raw_data.get("active_workspace_id", normalized_workspaces[0]["id"]))
    ws_ids = [ws["id"] for ws in normalized_workspaces]
    if active_ws_id not in ws_ids:
        active_ws_id = ws_ids[0]

    raw_reminders = raw_data.get("reminders", [])
    normalized_reminders = []
    if isinstance(raw_reminders, list):
        for rem in raw_reminders:
            if not isinstance(rem, dict) or "id" not in rem or "title" not in rem:
                continue

            d_val = rem.get("deadline")
            parsed_deadline = parse_date(d_val)

            normalized_reminders.append({
                "id": str(rem["id"]),
                "title": str(rem["title"]),
                "description": str(rem.get("description", "")),
                "deadline": parsed_deadline,
                "priority": str(rem.get("priority", "Medium")),
                "completed": bool(rem.get("completed", False)),
                "created_at": str(rem.get("created_at", "")),
            })

    return {
        "version": 4,
        "active_workspace_id": active_ws_id,
        "workspaces": normalized_workspaces,
        "reminders": normalized_reminders,
    }


def save_data(workspaces: list[dict], active_ws_id: str, reminders: list[dict]) -> bool:
    """
    Atomically saves all workspaces, task definitions, workspace goals, and global reminders to local JSON file.
    In web_demo mode, state changes are held in-memory in st.session_state without writing to disk.
    Writes to kartavya_data.json.tmp first and replaces target file to avoid corruption.
    Does NOT create backup churn on standard saves.
    """
    if KARTAVYA_MODE == "web_demo":
        return True

    try:
        os.makedirs(DATA_DIR, exist_ok=True)

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
                elif isinstance(t, str):
                    slug = re.sub(r'[^a-zA-Z0-9]', '_', t).lower()
                    serializable_tasks.append({
                        "id": f"task_{ws['id']}_{slug}",
                        "name": t,
                        "priority": "Medium",
                        "description": "",
                        "recurrence": {"type": "none", "days": []},
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

        # Write to temporary file first
        with open(TMP_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        # Validate temp payload before replacing primary file
        is_valid, err_msg, _ = validate_kartavya_schema(payload)
        if not is_valid:
            logger.error(f"Temp file validation failed before replacement: {err_msg}")
            if os.path.exists(TMP_FILE_PATH):
                os.remove(TMP_FILE_PATH)
            return False

        # Atomic replace with Windows fallback
        try:
            os.replace(TMP_FILE_PATH, DATA_FILE_PATH)
        except Exception:
            with open(TMP_FILE_PATH, "r", encoding="utf-8") as f_src:
                content = f_src.read()
            with open(DATA_FILE_PATH, "w", encoding="utf-8") as f_dst:
                f_dst.write(content)
            if os.path.exists(TMP_FILE_PATH):
                try:
                    os.remove(TMP_FILE_PATH)
                except Exception:
                    pass

        return True

    except Exception as e:
        logger.error(f"Failed to save kartavya_data.json: {e}")
        if os.path.exists(TMP_FILE_PATH):
            try:
                os.remove(TMP_FILE_PATH)
            except Exception:
                pass
        return False
