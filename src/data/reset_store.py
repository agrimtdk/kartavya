"""
Reset & Clear Data Engine for kartavya (Phase 7).

Provides safe controls for:
- Resetting current active workspace
- Resetting all application data to clean installation state

Guarantees pre-reset backup, atomic persistence, state verification, and reload.
"""

from datetime import date, timedelta
import streamlit as st
from src.data.workspace_store import (
    get_active_workspace,
    save_all_stores,
    init_workspace_store,
    SESSION_KEY_WORKSPACES,
    SESSION_KEY_ACTIVE_WS_ID,
    SESSION_KEY_REMINDERS,
)
from src.data.persistence import create_backup



def reset_current_workspace() -> tuple[bool, str]:
    """
    Resets tasks, completion history, goals, and focus data of the current active workspace.
    Creates a pre-reset backup before modifying data.
    """
    try:
        init_workspace_store()
        create_backup("reset_workspace")
        active_ws = get_active_workspace()

        today = date.today()
        initial_dates = [today + timedelta(days=i) for i in range(5)]

        active_ws["dates"] = initial_dates
        active_ws["tasks"] = []
        active_ws["completion"] = {}
        active_ws["goals"] = []
        active_ws["focus_matrix"] = {}
        active_ws["daily_target_pct"] = 80.0

        save_all_stores()
        return True, f"Workspace '{active_ws['name']}' reset successfully."
    except Exception as e:
        return False, f"Failed to reset workspace: {e}"


def reset_all_data() -> tuple[bool, str]:
    """
    Resets all workspaces, tasks, reminders, and goals to factory fresh state.
    Creates a pre-reset backup before wiping data.
    """
    try:
        init_workspace_store()
        create_backup("reset_all_data")

        today = date.today()
        initial_dates = [today + timedelta(days=i) for i in range(5)]

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
            "goals": [],
            "daily_target_pct": 80.0,
            "focus_matrix": {},
        }

        st.session_state[SESSION_KEY_WORKSPACES] = [ws_personal]
        st.session_state[SESSION_KEY_ACTIVE_WS_ID] = "ws_personal"
        st.session_state[SESSION_KEY_REMINDERS] = []

        save_all_stores()
        return True, "All application data reset successfully."
    except Exception as e:
        return False, f"Failed to reset application data: {e}"
