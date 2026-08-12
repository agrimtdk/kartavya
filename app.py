"""
kartavya — Personal Productivity & Daily Task Management Workspace.
Main Streamlit Application Entry Point.
Phase 9: Public Multi-User Architecture & Security Release.
"""

import os
import time

# Enforce IST (Indian Standard Time) globally for date.today() and datetime.now()
os.environ["TZ"] = "Asia/Kolkata"
if hasattr(time, "tzset"):
    time.tzset()

import random
import streamlit as st
from src.config import APP_NAME, KARTAVYA_MODE
from src.theme import init_theme, apply_theme
from src.components.header import render_header
from src.components.progress import render_overall_progress
from src.components.timeline import render_timeline
from src.components.workspace import render_workspace_navigator
from src.components.reminders import render_reminders
from src.components.analytics import render_analytics
from src.components.daily_brief import render_daily_brief
from src.components.focus_today import render_focus_today
from src.components.settings import render_settings_page
from src.components.login_view import render_login_view
from src.services.health_service import run_health_check
from src.services.auth_service import is_authenticated, get_current_user
from src.db.connection import DatabaseConnectionError, init_db


def configure_page() -> None:
    """Set up Streamlit page settings."""
    st.set_page_config(
        page_title="kartavya — Personal Workspace",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def render_sidebar() -> None:
    """Render application sidebar with navigation switcher, workspace navigator, reminders, and health status."""
    with st.sidebar:
        st.markdown(
            f"""
            <div style="padding: 0.5rem 0 1rem 0;">
                <span class="neo-badge neo-badge-coral" style="font-size: 0.85rem; padding: 0.35rem 0.75rem;">
                    ⚡ {APP_NAME.upper()} ({KARTAVYA_MODE.upper()})
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Main Navigation Switcher
        st.radio(
            "🧭 View Navigation",
            options=["⚡ Timeline Dashboard", "📊 Productivity Analytics", "⚙️ Settings & Data"],
            key="nav_view_selector",
        )

        st.markdown("<hr>", unsafe_allow_html=True)

        # Dynamic Workspace Navigator Component
        render_workspace_navigator()

        # Global Reminders Component
        render_reminders()

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### 🚦 SYSTEM MODE & HEALTH")

        mode_badge = "neo-badge" if KARTAVYA_MODE == "local" else ("neo-badge-cyan" if KARTAVYA_MODE == "web_demo" else "neo-badge-coral")
        st.markdown(
            f"""
            <div style="margin-bottom: 0.75rem;">
                <span style="font-weight: 700; font-size: 0.85rem;">MODE:</span>
                <span class="{mode_badge}" style="font-size: 0.75rem;">{KARTAVYA_MODE.upper()}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        health = run_health_check()
        if health["status"] == "healthy":
            st.success("✅ System Health: Normal", icon="🛡️")
        elif health["status"] == "degraded":
            st.warning("⚠️ System Health: Degraded Mode", icon="⚠️")
            for w in health["details"].get("warnings", []):
                st.caption(f"• {w}")
        else:
            st.error("🚨 System Health: Unhealthy", icon="🚨")


def render_footer() -> None:
    """Render footer with version info, author credits, and playful random hex color generator."""
    import secrets
    if "footer_hex_color" not in st.session_state:
        st.session_state["footer_hex_color"] = f"#{secrets.token_hex(3).upper()}"

    cur_hex = st.session_state["footer_hex_color"]

    st.markdown('<div class="neo-footer" style="text-align: center; margin-top: 2rem;">', unsafe_allow_html=True)

    col_f1, col_f2, col_f3 = st.columns([2, 3, 2])
    with col_f2:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; justify-content: center; gap: 0.6rem; background-color: var(--surface); border: 2.5px solid var(--border); box-shadow: 3px 3px 0px var(--shadow); padding: 0.35rem 0.75rem; border-radius: 2px; margin-bottom: 0.4rem;">
                <span style="display: inline-block; width: 1.1rem; height: 1.1rem; background-color: {cur_hex}; border: 2px solid #000; border-radius: 2px;"></span>
                <span style="font-weight: 800; font-family: monospace; font-size: 0.9rem; color: var(--text);">HEX: {cur_hex}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🎲 ROLL RANDOM COLOR", use_container_width=True, key="btn_roll_hex_color"):
            st.session_state["footer_hex_color"] = f"#{secrets.token_hex(3).upper()}"
            st.rerun()

    st.markdown(
        """
        <div style="margin-top: 0.5rem;">
            <strong>kartavya v0.9</strong> • Built with ❤️ by <a href="https://linkedin.com/in/agrimtdk" target="_blank" style="color: var(--text); text-decoration: underline; font-weight: 700;">Agrim Sharma</a> 🇮🇳
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def on_top_nav_change() -> None:
    """Callback to sync top navigation bar selection into canonical session state."""
    if "top_nav_radio_bar" in st.session_state:
        st.session_state["nav_view_selector"] = st.session_state["top_nav_radio_bar"]


def render_main_dashboard() -> None:
    """Render header, view router (Dashboard / Analytics / Settings), and footer."""
    # Production Health Check (non-blocking)
    health = run_health_check()
    if health["status"] == "unhealthy":
        for err in health["errors"]:
            st.error(f"🚨 **System Health Error**: {err}")
    elif health["status"] == "degraded":
        for warn in health["warnings"]:
            st.warning(f"⚠️ **Health Warning**: {warn}")

    # Non-blocking backup recovery notification
    recovered_file = st.session_state.get("kartavya_recovered_from_backup")
    if recovered_file:
        st.warning(f"🛡️ **Auto-Recovery Triggered**: Primary JSON file was corrupt. Workspace state was safely restored from backup `{recovered_file}`.")

    render_header()

    # Top Horizontal View Navigation Bar
    nav_options = ["⚡ Timeline Dashboard", "📊 Productivity Analytics", "⚙️ Settings & Data"]
    current_view = st.session_state.get("nav_view_selector", "⚡ Timeline Dashboard")
    cur_idx = nav_options.index(current_view) if current_view in nav_options else 0

    selected_view = st.radio(
        "Top Navigation",
        options=nav_options,
        index=cur_idx,
        key="top_nav_radio_bar",
        horizontal=True,
        label_visibility="collapsed",
        on_change=on_top_nav_change,
    )

    view = current_view
    if view == "📊 Productivity Analytics":
        render_analytics()
    elif view == "⚙️ Settings & Data":
        render_settings_page()
    else:
        render_daily_brief()
        render_focus_today()
        render_overall_progress()
        render_timeline()

    render_footer()


def main() -> None:
    """Main application lifecycle with Phase 9 authentication gate & DB error handling."""
    configure_page()
    init_theme()
    apply_theme()

    try:
        init_db()
        if not is_authenticated():
            render_login_view()
        else:
            render_sidebar()
            render_main_dashboard()
    except DatabaseConnectionError as e:
        st.markdown(
            """
            <div class="neo-card-coral" style="padding: 2rem; margin-top: 3rem; text-align: center;">
                <h2 style="margin-top: 0;">🔌 SERVICE CONNECTION NOTICE</h2>
                <div style="font-size: 1.1rem; font-weight: 700; margin: 1rem 0;">
                    Kartavya is temporarily unable to connect to its data service. Please try again.
                </div>
                <div style="font-size: 0.85rem; opacity: 0.8;">
                    If this error persists, please check your network connection or server database configuration.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception as e:
        st.error("Kartavya encountered an unexpected error. Please refresh the page.")
        st.caption(f"Error note: {e}")


if __name__ == "__main__":
    main()
