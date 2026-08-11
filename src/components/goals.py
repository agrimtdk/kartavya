"""
Workspace Productivity Goals UI Component for kartavya (Phase 6 with Pace Warnings).

Renders Goal Manager, goal progress cards, pace warning badges (ON TRACK, AT RISK, BEHIND),
days remaining, required daily pace, and modal forms for adding, editing, deleting, and archiving goals.
"""

from datetime import date, timedelta
import html
import streamlit as st
from src.data.workspace_store import get_active_workspace_id, get_active_workspace
from src.data.goal_store import (
    get_workspace_goals,
    add_workspace_goal,
    edit_workspace_goal,
    delete_workspace_goal,
    toggle_goal_status,
)
from src.analytics.goals import calculate_all_goals_progress


from src.config import MAX_TITLE_LEN


def render_workspace_goals() -> None:
    """Render workspace goals header, Add Goal popover, pace warnings, and dynamic goal progress cards."""
    ws_id = get_active_workspace_id()
    active_ws = get_active_workspace()
    dates = active_ws.get("dates") or []
    tasks = active_ws.get("tasks") or []
    completion_matrix = active_ws.get("completion") or {}
    today = date.today()


    st.markdown("### 🎯 Workspace Goals")

    # Add Goal Popover Button
    with st.popover("➕ ADD GOAL", use_container_width=True):
        st.markdown("#### Create Workspace Goal")
        g_title = st.text_input(
            "Goal Title",
            placeholder="e.g. Complete 50 tasks this month, Maintain 80% completion",
            max_chars=MAX_TITLE_LEN,
            key="input_add_goal_title",
        )

        g_type = st.selectbox(
            "Goal Type",
            options=["task_count", "completion_pct", "day_count", "streak"],
            format_func=lambda x: {
                "task_count": "Complete X Task Instances",
                "completion_pct": "Maintain X% Average Completion",
                "day_count": "Productive on X Different Days",
                "streak": "Maintain a Streak of X Days",
            }[x],
            key="select_add_goal_type",
        )
        g_target = st.number_input(
            "Target Value",
            min_value=1.0,
            value=50.0 if g_type == "task_count" else (80.0 if g_type == "completion_pct" else 7.0),
            step=1.0,
            key="input_add_goal_target",
        )
        col_sd, col_ed = st.columns(2)
        with col_sd:
            g_start = st.date_input("Start Date", value=today, key="input_add_goal_start")
        with col_ed:
            g_end = st.date_input("End Date", value=today + timedelta(days=30), key="input_add_goal_end")

        if st.button("Confirm Create Goal", use_container_width=True, key="btn_confirm_add_goal"):
            success, msg, _ = add_workspace_goal(
                ws_id, g_title, g_type, g_target, g_start, g_end
            )
            if success:
                st.toast(msg, icon="🎯")
                st.rerun()
            else:
                st.error(msg)

    raw_goals = get_workspace_goals(ws_id)
    if not raw_goals:
        st.caption("No productivity goals created for this workspace yet.")
        return

    goals_progress = calculate_all_goals_progress(raw_goals, dates, tasks, completion_matrix, today_ref=today)

    st.markdown("<div style='margin-top: 0.75rem;'></div>", unsafe_allow_html=True)

    for g_prog in goals_progress:
        g_id = g_prog["goal_id"]
        g_title = g_prog["title"]
        g_type = g_prog["goal_type"]
        target = g_prog["target_value"]
        current = g_prog["current_value"]
        pct = g_prog["progress_pct"]
        status = g_prog["status"]
        pace_status = g_prog.get("pace_status", "ON TRACK")
        pace_badge_class = g_prog.get("pace_badge_class", "neo-badge-cyan")
        days_rem = g_prog.get("days_remaining", 0)
        req_pace = g_prog.get("required_pace", 0.0)

        # Format label units
        if g_type == "task_count":
            unit_str = f"{int(current)} / {int(target)} TASKS"
        elif g_type == "completion_pct":
            unit_str = f"CURRENT {current}% / TARGET {target}%"
        elif g_type == "day_count":
            unit_str = f"{int(current)} / {int(target)} DAYS"
        else:
            unit_str = f"CURRENT {int(current)} / TARGET {int(target)} DAYS STREAK"

        safe_g_title = html.escape(g_title)

        st.markdown(
            f"""
            <div class="neo-card" style="padding: 1rem; margin-bottom: 0.75rem;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 0.5rem; margin-bottom: 0.4rem;">
                    <div>
                        <strong style="font-size: 1.05rem;">{safe_g_title}</strong>
                        <div style="font-size: 0.8rem; opacity: 0.8; margin-top: 0.2rem;">
                            {unit_str} • ⏳ <strong>{days_rem} Days Left</strong> {f'• Req Pace: {req_pace}/day' if req_pace > 0 else ''}
                        </div>
                    </div>
                    <div>
                        <span class="neo-badge {pace_badge_class}" style="font-size: 0.7rem; padding: 0.2rem 0.5rem; margin: 0;">
                            {pace_status}
                        </span>
                    </div>
                </div>
                <div style="margin: 0.5rem 0;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.75rem; font-weight: 700; margin-bottom: 0.2rem;">
                        <span>Progress</span>
                        <span>{pct}%</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.progress(pct / 100.0)

        # Action controls for goals
        c_act1, c_act2, c_act3 = st.columns([1, 1, 1], gap="small")
        with c_act1:
            with st.popover("✏️ Edit Goal", use_container_width=True):
                st.markdown("#### Edit Goal")
                eg_title = st.text_input("Title", value=g_title, key=f"edit_g_title_{g_id}")
                eg_target = st.number_input("Target Value", min_value=1.0, value=float(target), key=f"edit_g_target_{g_id}")
                eg_start = st.date_input("Start Date", value=g_prog["start_date"], key=f"edit_g_start_{g_id}")
                eg_end = st.date_input("End Date", value=g_prog["end_date"], key=f"edit_g_end_{g_id}")

                if st.button("Save Goal Changes", use_container_width=True, key=f"btn_save_g_{g_id}"):
                    success, msg = edit_workspace_goal(
                        ws_id, g_id, eg_title, eg_target, eg_start, eg_end, status=status
                    )
                    if success:
                        st.toast(msg, icon="✅")
                        st.rerun()
                    else:
                        st.error(msg)

        with c_act2:
            if st.button(
                "Unarchive" if status == "archived" else "Archive Goal",
                key=f"btn_toggle_g_{g_id}",
                use_container_width=True,
            ):
                toggle_goal_status(ws_id, g_id)
                st.rerun()

        with c_act3:
            if st.button("🗑️ Delete", key=f"btn_del_g_{g_id}", use_container_width=True):
                success, msg = delete_workspace_goal(ws_id, g_id)
                if success:
                    st.toast(msg, icon="🗑️")
                    st.rerun()
                else:
                    st.error(msg)
