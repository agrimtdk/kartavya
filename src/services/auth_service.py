"""
Authentication & User Session Management Service for kartavya (Phase 9 Public Multi-User Architecture).

Encapsulates user identity resolution, Streamlit st.user / st.login integration,
strict multi-tenant session purging on logout, and local dev switching.
"""

import os
import logging
import streamlit as st
from src.config import KARTAVYA_MODE
from src.db.db_store import get_or_create_user

logger = logging.getLogger(__name__)

SESSION_KEY_AUTH_USER = "kartavya_auth_user"
SESSION_KEY_DEV_USER = "kartavya_dev_user_email"
SESSION_KEY_LOGGED_OUT = "kartavya_explicitly_logged_out"


def is_authenticated() -> bool:
    """Returns True if a user is currently authenticated."""
    return get_current_user() is not None


def get_current_user() -> dict | None:
    """
    Resolves the canonical authenticated user dictionary for the current session.
    - If user explicitly clicked Logout, returns None until re-authenticated.
    - In Production: Resolves via Streamlit st.user (Google OAuth).
    - In Local Dev Mode: Resolves via local session state dev user unless explicitly logged out.
    """
    if st.session_state.get(SESSION_KEY_LOGGED_OUT, False):
        return None

    # 1. Native Streamlit st.user (Google OAuth / OpenID Connect)
    try:
        if hasattr(st, "user") and st.user and getattr(st.user, "email", None):
            email = str(st.user.email).strip().lower()
            name = str(getattr(st.user, "name", "") or email.split("@")[0])
            avatar = str(getattr(st.user, "picture", "") or getattr(st.user, "avatar", ""))
            
            user_data = get_or_create_user(email, name, avatar if avatar else None)
            st.session_state[SESSION_KEY_AUTH_USER] = user_data
            return user_data
    except Exception as e:
        logger.debug(f"st.user resolution note: {e}")

    # 2. Checked stored session auth user
    if SESSION_KEY_AUTH_USER in st.session_state and st.session_state[SESSION_KEY_AUTH_USER]:
        return st.session_state[SESSION_KEY_AUTH_USER]

    return None


def login_user(email: str, display_name: str = "", avatar_url: str | None = None) -> dict:
    """Explicitly logs in a user by email."""
    if SESSION_KEY_LOGGED_OUT in st.session_state:
        del st.session_state[SESSION_KEY_LOGGED_OUT]

    purge_user_session_state()
    clean_email = email.strip().lower()
    user_data = get_or_create_user(clean_email, display_name.strip() or clean_email.split("@")[0], avatar_url)
    st.session_state[SESSION_KEY_AUTH_USER] = user_data
    return user_data


def switch_dev_user(target_email: str) -> None:
    """Switch active user in local development mode (User A vs User B testing)."""
    if KARTAVYA_MODE == "production":
        return  # Never allow dev switching in production mode

    if SESSION_KEY_LOGGED_OUT in st.session_state:
        del st.session_state[SESSION_KEY_LOGGED_OUT]

    st.session_state[SESSION_KEY_DEV_USER] = target_email.strip().lower()
    purge_user_session_state()

    user = get_or_create_user(target_email.strip().lower(), "User A" if "user_a" in target_email else "User B")
    st.session_state[SESSION_KEY_AUTH_USER] = user
    st.rerun()


def purge_user_session_state() -> None:
    """Completely purges all user-specific state from st.session_state."""
    keys_to_clear = list(st.session_state.keys())
    for key in keys_to_clear:
        if key != SESSION_KEY_LOGGED_OUT:
            del st.session_state[key]


def logout_user() -> None:
    """Logs out the current user and clears session state completely."""
    purge_user_session_state()
    st.session_state[SESSION_KEY_LOGGED_OUT] = True

    try:
        if hasattr(st, "logout"):
            st.logout()
    except Exception as e:
        logger.warning(f"st.logout call warning: {e}")

    st.rerun()
