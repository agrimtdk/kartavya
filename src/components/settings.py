"""
Settings & Data Management UI Component for kartavya (Phase 9 Public Multi-User Architecture).

Provides user-facing controls for:
- Account Profile, Authentication Status & One-Click Logout
- Import Existing kartavya Data (Migration Tool)
- App Information & Schema Version
- Versioned JSON and CSV Data Export
- Automatic Backups log & single-click Backup Restoration
- Workspace Productivity Target Configuration
"""

import json
import streamlit as st
from src.config import SCHEMA_VERSION, APP_NAME, APP_SUBTITLE, KARTAVYA_MODE
from src.data.workspace_store import get_workspaces, get_active_workspace, set_daily_target_pct, get_daily_target_pct
from src.data.reminder_store import get_reminders
from src.data.reset_store import reset_current_workspace, reset_all_data
from src.data.persistence import get_available_backups, create_backup
from src.services.export_service import (
    export_to_json,
    export_to_csv_timeline,
    export_to_csv_reminders,
    export_to_csv_goals,
)
from src.services.import_service import validate_import_json, restore_data
from src.services.auth_service import get_current_user, logout_user


def render_settings_page() -> None:
    """Renders the main Settings & Data Management view."""
    st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <div style="font-size: 2.2rem; font-weight: 900; line-height: 1.1; font-family: 'Space Grotesk', sans-serif;">
                ⚙️ Settings & Data Management
            </div>
            <div style="font-size: 0.95rem; font-weight: 600; color: var(--text-muted); margin-top: 0.3rem;">
                Account Profile, System Configuration, Data Migration & Safety Controls
            </div>
        </div>
    """, unsafe_allow_html=True)

    tab_acc, tab_gen, tab_data, tab_prod = st.tabs([
        "👤 ACCOUNT",
        "ℹ️ GENERAL",
        "💾 DATA MANAGEMENT",
        "🎯 PRODUCTIVITY SETTINGS",
    ])

    # 1. ACCOUNT TAB
    with tab_acc:
        user = get_current_user()
        if not user:
            st.warning("No user authenticated.")
        else:
            st.markdown(
                f"""
                <div class="neo-card-cyan" style="margin-top: 0.5rem; margin-bottom: 1.25rem;">
                    <div style="display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;">
                        <div style="font-size: 2.5rem; line-height: 1;">👤</div>
                        <div>
                            <h3 style="margin: 0; font-size: 1.5rem;">{user['display_name']}</h3>
                            <div style="font-weight: 700; font-size: 0.95rem; opacity: 0.9;">{user['email']}</div>
                            <div style="margin-top: 0.4rem;">
                                <span class="neo-badge">STATUS: AUTHENTICATED</span>
                                <span class="neo-badge neo-badge-coral" style="margin-left: 0.4rem;">ID: {user['id'][:8]}...</span>
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_a1, col_a2 = st.columns(2)
            with col_a1:
                st.markdown("### 🚪 Account Session")
                st.caption("Log out of your session. All user-specific session state will be safely cleared.")
                if st.button("🚪 LOG OUT NOW", type="primary", use_container_width=True, key="btn_account_logout"):
                    logout_user()

            with col_a2:
                st.markdown("### 📥 Import Existing kartavya Data")
                st.caption("Migrate your previous kartavya JSON file into your account.")
                
                uploaded_file = st.file_uploader(
                    "Upload kartavya JSON file",
                    type=["json"],
                    key="account_json_migrator",
                )
                if uploaded_file is not None:
                    try:
                        raw_str = uploaded_file.getvalue().decode("utf-8")
                        is_valid, msg, payload = validate_import_json(raw_str)
                        if not is_valid:
                            st.error(msg)
                        else:
                            st.success(msg)
                            mode_opt = st.radio("Migration Mode", options=["replace", "merge"], format_func=lambda x: "Replace Account Data" if x == "replace" else "Merge with Existing Workspaces", key="account_import_mode")
                            if st.button("⚡ IMPORT TO ACCOUNT NOW", use_container_width=True, key="btn_confirm_account_import"):
                                ok, res_msg = restore_data(payload, mode=mode_opt)
                                if ok:
                                    st.success(res_msg)
                                    st.rerun()
                                else:
                                    st.error(res_msg)
                    except Exception as ex:
                        st.error(f"Import error: {ex}")

    # 2. GENERAL TAB
    with tab_gen:
        workspaces = get_workspaces()
        active_ws = get_active_workspace()
        reminders = get_reminders()

        st.markdown(f"""
            <div class="neo-card-yellow" style="margin-top: 0.5rem;">
                <div style="font-size: 1.6rem; font-weight: 900;">{APP_NAME}</div>
                <div style="font-size: 1rem; font-weight: 700;">{APP_SUBTITLE}</div>
                <hr style="border-top: 2px solid #000; margin: 0.75rem 0;" />
                <div style="font-size: 0.9rem; font-weight: 600;">
                    • <b>Schema Version:</b> v{SCHEMA_VERSION}<br/>
                    • <b>Mode:</b> {KARTAVYA_MODE.upper()}<br/>
                    • <b>Total Workspaces:</b> {len(workspaces)}<br/>
                    • <b>Active Workspace:</b> {active_ws.get('name', 'N/A')}<br/>
                    • <b>Global Reminders:</b> {len(reminders)}
                </div>
            </div>
        """, unsafe_allow_html=True)

    # 3. DATA MANAGEMENT TAB
    with tab_data:
        st.markdown("### 📥 Export Data")
        st.caption("Download complete versioned JSON snapshot or CSV spreadsheets for external reporting.")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            json_str = export_to_json()
            st.download_button(
                label="💾 EXPORT JSON",
                data=json_str,
                file_name="kartavya_export.json",
                mime="application/json",
                use_container_width=True,
            )
        with c2:
            csv_tl = export_to_csv_timeline()
            st.download_button(
                label="📊 TIMELINE CSV",
                data=csv_tl,
                file_name="kartavya_timeline.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with c3:
            csv_rem = export_to_csv_reminders()
            st.download_button(
                label="🔔 REMINDERS CSV",
                data=csv_rem,
                file_name="kartavya_reminders.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with c4:
            csv_goals = export_to_csv_goals()
            st.download_button(
                label="🎯 GOALS CSV",
                data=csv_goals,
                file_name="kartavya_goals.csv",
                mime="text/csv",
                use_container_width=True,
            )

        st.markdown("<hr/>", unsafe_allow_html=True)

        st.markdown("### 🛡️ Automatic Backups")
        st.caption("Timestamped backups created before destructive operations or schema upgrades.")

        backups = get_available_backups()
        if not backups:
            st.info("No automatic backup files found yet.")
        else:
            for b in backups:
                bc1, bc2 = st.columns([3, 1])
                with bc1:
                    st.markdown(f"📁 **`{b['filename']}`** ({round(b['size_bytes']/1024, 1)} KB) — *{b['timestamp']}*")
                with bc2:
                    with st.popover("↩️ RESTORE", use_container_width=True):
                        st.write(f"Restore from `{b['filename']}`?")
                        if st.button(f"CONFIRM RESTORE {b['filename'][:15]}", key=f"btn_res_{b['filename']}"):
                            try:
                                with open(b['path'], "r", encoding="utf-8") as f_b:
                                    b_data = json.load(f_b)
                                is_v, v_msg, _ = validate_import_json(json.dumps(b_data))
                                if is_v:
                                    restore_data(b_data, mode="replace")
                                    st.success(f"Restored from {b['filename']}!")
                                    st.rerun()
                                else:
                                    st.error(f"Backup invalid: {v_msg}")
                            except Exception as ex:
                                st.error(f"Backup restore error: {ex}")

        st.markdown("<hr/>", unsafe_allow_html=True)

        st.markdown("### ⚠️ Danger Zone & Reset Controls")
        st.caption("Destructive controls to reset active workspace or wipe local data.")

        r_col1, r_col2 = st.columns(2)
        with r_col1:
            with st.popover("🗑️ RESET CURRENT WORKSPACE", use_container_width=True):
                st.markdown(f"**Reset Workspace `{active_ws.get('name')}`?**")
                st.write("This will remove all tasks, completion history, goals, and focus data for this workspace.")
                if st.button("🚨 CONFIRM RESET WORKSPACE NOW", key="btn_confirm_reset_ws"):
                    ok, msg = reset_current_workspace()
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        with r_col2:
            with st.popover("🚨 RESET ALL APPLICATION DATA", use_container_width=True):
                st.markdown("**Reset ALL Application Data?**")
                st.write("This will wipe all workspaces, tasks, completion history, goals, and reminders. Factory reset.")
                confirm_txt = st.text_input("Type 'RESET ALL' to confirm:", key="confirm_reset_all_input")
                if confirm_txt.strip() == "RESET ALL":
                    if st.button("💥 CONFIRM FACTORY RESET ALL DATA", key="btn_confirm_reset_all"):
                        ok, msg = reset_all_data()
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                else:
                    st.caption("Type 'RESET ALL' above to enable the factory reset button.")

    # 4. PRODUCTIVITY TAB
    with tab_prod:
        st.markdown("### 🎯 Workspace Daily Target")
        st.caption("Configure the daily target task completion percentage for the active workspace.")

        curr_target = get_daily_target_pct()
        new_target = st.slider(
            "Target Daily Completion Percentage (%)",
            min_value=10,
            max_value=100,
            value=int(curr_target),
            step=5,
            key="daily_target_slider",
        )

        if new_target != curr_target:
            set_daily_target_pct(float(new_target))
            st.success(f"Daily completion target updated to {new_target}%!")
