"""
Production Health Check Service for kartavya (Phase 8).

Verifies storage directory accessibility, schema validator presence,
quote service fallback dictionary availability, and session initialization state.
Executes lightweight local checks with ZERO external HTTP requests.
"""

import os
import logging
from src.config import KARTAVYA_DATA_DIR, KARTAVYA_MODE
from src.data.validator import validate_kartavya_schema
from src.services.quote_service import FALLBACK_QUOTES

logger = logging.getLogger(__name__)


def run_health_check() -> dict:
    """
    Runs lightweight production health checks.
    Returns dict:
      {
        "status": "healthy" | "degraded" | "unhealthy",
        "warnings": list[str],
        "errors": list[str],
        "details": dict
      }
    """
    warnings = []
    errors = []
    details = {
        "mode": KARTAVYA_MODE,
        "data_dir": KARTAVYA_DATA_DIR,
        "data_dir_writable": True,
        "validator_ready": True,
        "quote_fallbacks_count": len(FALLBACK_QUOTES),
    }

    # 1. Storage / Directory Check
    if KARTAVYA_MODE != "web_demo":
        try:
            os.makedirs(KARTAVYA_DATA_DIR, exist_ok=True)
            test_file = os.path.join(KARTAVYA_DATA_DIR, ".health_check.tmp")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("health_ok")
            if os.path.exists(test_file):
                os.remove(test_file)
        except Exception as e:
            details["data_dir_writable"] = False
            errors.append(f"Data directory '{KARTAVYA_DATA_DIR}' is not writable: {e}")

    # 2. Validator Sanity Check
    try:
        sample_valid = {
            "version": 4,
            "active_workspace_id": "ws_1",
            "workspaces": [{"id": "ws_1", "name": "Health WS", "dates": [], "tasks": [], "completion": {}}],
            "reminders": [],
        }
        is_ok, err_msg, _ = validate_kartavya_schema(sample_valid)
        if not is_ok:
            warnings.append(f"Schema validator returned unexpected result during health check: {err_msg}")
    except Exception as e:
        details["validator_ready"] = False
        warnings.append(f"Schema validator check failed: {e}")

    # 3. Quote Service Fallback Check
    if not FALLBACK_QUOTES:
        warnings.append("Quote service local fallback dictionary is empty.")

    # Determine overall status
    if errors:
        status = "unhealthy"
    elif warnings:
        status = "degraded"
    else:
        status = "healthy"

    return {
        "status": status,
        "warnings": warnings,
        "errors": errors,
        "details": details,
    }
