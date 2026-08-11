"""
Global Reminder Store Module for kartavya (Phase 9 Public Multi-User Architecture).

Owns global reminders list across all workspaces.
Routes mutations to user-scoped database store when authenticated.
Calculates dynamic deadline urgency on render without storing calculated fields.
"""

import uuid
from datetime import date, datetime
import streamlit as st
from src.data.persistence import parse_date
from src.data.workspace_store import init_workspace_store, save_all_stores, SESSION_KEY_REMINDERS
from src.services.auth_service import get_current_user
from src.db.db_store import (
    get_user_reminders as db_get_user_reminders,
    create_reminder as db_create_reminder,
    update_reminder as db_update_reminder,
    delete_reminder as db_delete_reminder,
)

PRIORITY_WEIGHTS = {"High": 3, "Medium": 2, "Low": 1}


def get_deadline_status(deadline_input: date | datetime | str | tuple | list | None) -> tuple[str, str]:
    """Calculates dynamic deadline status relative to date.today()."""
    deadline_date = parse_date(deadline_input)
    if not isinstance(deadline_date, date):
        return "NO DEADLINE", "none"

    today = date.today()
    diff = (deadline_date - today).days

    if diff < 0:
        days_abs = abs(diff)
        unit = "DAY" if days_abs == 1 else "DAYS"
        return f"OVERDUE BY {days_abs} {unit}", "overdue"
    elif diff == 0:
        return "DUE TODAY", "today"
    else:
        unit = "DAY" if diff == 1 else "DAYS"
        return f"{diff} {unit} LEFT", "upcoming"


def get_reminders() -> list[dict]:
    """Returns canonical list of global reminder dictionaries for current user."""
    user = get_current_user()
    if user:
        rems = db_get_user_reminders(user["id"])
        st.session_state[SESSION_KEY_REMINDERS] = rems
        return rems

    init_workspace_store()
    return st.session_state.get(SESSION_KEY_REMINDERS, [])


def get_sorted_reminders() -> list[dict]:
    """Returns a sorted DISPLAY COPY of reminders."""
    reminders = get_reminders()
    today = date.today()

    def sort_key(rem: dict):
        completed = rem.get("completed", False)
        priority = rem.get("priority", "Medium")
        p_weight = PRIORITY_WEIGHTS.get(priority, 2)
        d_date = parse_date(rem.get("deadline"))

        if d_date and isinstance(d_date, date):
            diff = (d_date - today).days
            if diff < 0:
                urgency_score = 1
                days_factor = diff
            elif diff == 0:
                urgency_score = 2
                days_factor = 0
            else:
                urgency_score = 3
                days_factor = diff
        else:
            urgency_score = 4
            days_factor = 999999

        return (
            1 if completed else 0,
            urgency_score,
            days_factor,
            -p_weight,
        )

    return sorted(reminders, key=sort_key)


def add_reminder(
    title: str,
    description: str = "",
    deadline: date | datetime | str | tuple | list | None = None,
    priority: str = "Medium",
) -> tuple[bool, str]:
    """Adds a new global reminder."""
    trimmed_title = title.strip()
    if not trimmed_title:
        return False, "Reminder title cannot be empty."

    valid_priority = priority if priority in PRIORITY_WEIGHTS else "Medium"
    parsed_deadline = parse_date(deadline)

    user = get_current_user()
    if user:
        db_create_reminder(user["id"], trimmed_title, description.strip(), parsed_deadline, valid_priority)
        get_reminders()
        return True, f"Reminder '{trimmed_title}' added."

    init_workspace_store()
    rem_id = f"rem_{uuid.uuid4().hex[:8]}"
    new_rem = {
        "id": rem_id,
        "title": trimmed_title,
        "description": description.strip(),
        "deadline": parsed_deadline,
        "priority": valid_priority,
        "completed": False,
        "created_at": datetime.now().isoformat(),
    }

    if SESSION_KEY_REMINDERS not in st.session_state:
        st.session_state[SESSION_KEY_REMINDERS] = []

    st.session_state[SESSION_KEY_REMINDERS].append(new_rem)
    save_all_stores()
    return True, f"Reminder '{trimmed_title}' added."


def edit_reminder(
    rem_id: str,
    title: str,
    description: str = "",
    deadline: date | datetime | str | tuple | list | None = None,
    priority: str = "Medium",
) -> tuple[bool, str]:
    """Edits an existing global reminder."""
    trimmed_title = title.strip()
    if not trimmed_title:
        return False, "Reminder title cannot be empty."

    valid_priority = priority if priority in PRIORITY_WEIGHTS else "Medium"
    parsed_deadline = parse_date(deadline)

    user = get_current_user()
    if user:
        res = db_update_reminder(
            user["id"],
            rem_id,
            {"title": trimmed_title, "description": description.strip(), "deadline": parsed_deadline, "priority": valid_priority},
        )
        if res:
            get_reminders()
            return True, "Reminder updated successfully."
        return False, "Reminder not found or unauthorized."

    init_workspace_store()
    reminders = get_reminders()
    for rem in reminders:
        if rem["id"] == rem_id:
            rem["title"] = trimmed_title
            rem["description"] = description.strip()
            rem["deadline"] = parsed_deadline
            rem["priority"] = valid_priority
            save_all_stores()
            return True, "Reminder updated successfully."

    return False, "Reminder not found."


def delete_reminder(rem_id: str) -> tuple[bool, str]:
    """Deletes a global reminder."""
    user = get_current_user()
    if user:
        ok = db_delete_reminder(user["id"], rem_id)
        if ok:
            get_reminders()
            return True, "Reminder deleted successfully."
        return False, "Reminder not found or unauthorized."

    init_workspace_store()
    reminders = get_reminders()
    target = None
    for rem in reminders:
        if rem["id"] == rem_id:
            target = rem
            break

    if target:
        reminders.remove(target)
        save_all_stores()
        return True, "Reminder deleted successfully."

    return False, "Reminder not found."


def toggle_reminder_status(rem_id: str) -> bool:
    """Toggles completed status of a global reminder."""
    user = get_current_user()
    if user:
        rems = get_reminders()
        for r in rems:
            if r["id"] == rem_id:
                new_state = not r.get("completed", False)
                db_update_reminder(user["id"], rem_id, {"completed": new_state})
                get_reminders()
                return True
        return False

    init_workspace_store()
    reminders = get_reminders()
    for rem in reminders:
        if rem["id"] == rem_id:
            rem["completed"] = not rem.get("completed", False)
            save_all_stores()
            return True

    return False
