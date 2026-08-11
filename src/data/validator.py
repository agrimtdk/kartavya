"""
Non-Destructive Centralized Data Validation Layer for kartavya (Phase 7).

Evaluates persisted or imported JSON payloads without altering user data.
Distinguishes between:
- Invalid/corrupt data structures
- Missing optional fields (e.g. goals, focus_matrix, daily_target_pct)
- Legacy data requiring schema migration (version < 4)
"""

from typing import Any


def validate_kartavya_schema(data: Any) -> tuple[bool, str, dict[str, Any]]:
    """
    Validates a kartavya state dictionary non-destructively.

    Returns:
        (is_valid, error_message, metadata_dict)
    """
    if not isinstance(data, dict):
        return False, "Root data payload must be a JSON object.", {"is_legacy": False}

    # Check schema version
    ver = data.get("version")
    if ver is None or not isinstance(ver, int):
        return False, "Missing or invalid 'version' attribute in data payload.", {"is_legacy": True, "version": ver}

    if ver > 4:
        return False, f"Unsupported future schema version ({ver}). Maximum supported version is 4.", {"is_legacy": False, "version": ver}

    is_legacy = (ver < 4)

    # Check workspaces list
    workspaces = data.get("workspaces")
    if not isinstance(workspaces, list):
        return False, "Payload must contain a 'workspaces' list.", {"is_legacy": is_legacy, "version": ver}

    if len(workspaces) == 0 and not is_legacy:
        return False, "'workspaces' list cannot be empty.", {"is_legacy": is_legacy, "version": ver}

    for idx, ws in enumerate(workspaces):
        if not isinstance(ws, dict):
            return False, f"Workspace at index {idx} is not a valid object.", {"is_legacy": is_legacy, "version": ver}

        ws_id = ws.get("id")
        ws_name = ws.get("name")
        if not ws_id or not isinstance(ws_id, str):
            return False, f"Workspace at index {idx} has missing or invalid 'id'.", {"is_legacy": is_legacy, "version": ver}
        if not ws_name or not isinstance(ws_name, str):
            return False, f"Workspace '{ws_id}' has missing or invalid 'name'.", {"is_legacy": is_legacy, "version": ver}

        tasks = ws.get("tasks")
        if not isinstance(tasks, list):
            return False, f"Workspace '{ws_name}' tasks attribute must be a list.", {"is_legacy": is_legacy, "version": ver}

        dates = ws.get("dates")
        if not isinstance(dates, list):
            return False, f"Workspace '{ws_name}' dates attribute must be a list.", {"is_legacy": is_legacy, "version": ver}

        completion = ws.get("completion")
        if not isinstance(completion, dict):
            return False, f"Workspace '{ws_name}' completion matrix must be a dictionary.", {"is_legacy": is_legacy, "version": ver}

    # Check reminders list if present
    reminders = data.get("reminders")
    if reminders is not None and not isinstance(reminders, list):
        return False, "'reminders' attribute must be a list.", {"is_legacy": is_legacy, "version": ver}

    return True, "Schema validation successful.", {"is_legacy": is_legacy, "version": ver}
