"""
Login & Authentication Landing Component for kartavya (Phase 9 Public Multi-User Architecture).

Renders clean Neo-Brutalist Light Mode landing UI, Google OAuth trigger,
Direct Email Sign-In form, and Dev Mode user switcher for local multi-user testing.
"""

import streamlit as st
from src.config import APP_NAME, DEFAULT_TAGLINE, KARTAVYA_MODE
from src.services.auth_service import login_user, switch_dev_user


def render_login_view() -> None:
    """Renders Neo-Brutalist Light Mode authentication landing page."""
    col_l1, col_l2, col_l3 = st.columns([1, 2.8, 1])

    with col_l2:
        st.markdown('<div style="height: 1.5rem;"></div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="neo-card-yellow" style="padding: 2.2rem; text-align: center; margin-top: 1rem;">
                <h1 style="font-size: 3.5rem; margin: 0; line-height: 1; text-transform: lowercase; color: var(--primary-text) !important;">⚡ {APP_NAME}</h1>
                <p style="font-weight: 800; font-size: 1.2rem; margin: 0.75rem 0 1rem 0; letter-spacing: 0.02em; color: var(--primary-text) !important;">
                    {DEFAULT_TAGLINE}
                </p>
                <div style="font-size: 0.95rem; font-weight: 600; line-height: 1.5; opacity: 0.95; margin-bottom: 1rem;">
                    Personal Productivity & Daily Task Management Workspace.<br>
                    Keep track of daily routines, focus priorities, multi-workspace timelines, reminders, and goals with strict data privacy.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="neo-card" style="padding: 1.8rem; margin-top: 1.25rem;">', unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; margin-top: 0;'>🔐 ACCOUNT AUTHENTICATION</h3>", unsafe_allow_html=True)

        # 1. Native Streamlit Google OAuth Login Button (Production Only)
        if KARTAVYA_MODE == "production":
            if hasattr(st, "login"):
                try:
                    if st.button("🔑 CONTINUE WITH GOOGLE OAUTH", use_container_width=True, type="primary", key="btn_oauth_google"):
                        st.login("google")
                except Exception as e:
                    st.error("⚠️ Google OAuth is not configured.")
                    st.info("Please configure `.streamlit/secrets.toml` with your Google Client ID and Secret.")

        # Local Testing Fallback
        if KARTAVYA_MODE == "local":
            st.markdown("<hr style='margin: 1.5rem 0 1rem 0;'>", unsafe_allow_html=True)
            st.markdown("<div style='text-align: center; font-weight: 800; margin-bottom: 1rem; color: #666;'>🛠️ LOCAL TESTING ONLY</div>", unsafe_allow_html=True)
            if st.button("👤 AUTO-LOGIN AS LOCAL DEV", use_container_width=True, key="btn_local_fallback"):
                switch_dev_user("dev_user_a@kartavya.local")

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div style="text-align: center; margin-top: 1.5rem; font-size: 0.8rem; font-weight: 600; color: var(--text-muted);">
                🔒 <strong>Zero Data Leakage Guarantee</strong>: All workspaces, tasks, reminders, and goals are strictly isolated per user account.
            </div>
            """,
            unsafe_allow_html=True,
        )
