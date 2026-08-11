"""
Focus Today Smart Recommendation & Manual Planning UI Component for kartavya (Phase 6).

Renders prioritized focus items based on overdue reminders, high-priority deadlines,
unfinished tasks, and low-completion habits.
Allows users to manually toggle any workspace task as "Focus for Today".
"""

import html
from datetime import date
import streamlit as st
from src.data.workspace_store import (
    get_active_workspace,
    get_focus_tasks,
    toggle_focus_task,
)
from src.data.reminder_store import get_sorted_reminders
from src.analytics.insights import calculate_focus_today_recommendations


def render_focus_today() -> None:
    """Render Focus Today recommendations and manual focus manager on Timeline Dashboard."""
    active_ws = get_active_workspace()
    dates = active_ws.get("dates") or []
    tasks = active_ws.get("tasks") or []
    completion_matrix = active_ws.get("completion") or {}
    reminders = get_sorted_reminders()
    today = date.today()

    recs = calculate_focus_today_recommendations(dates, tasks, completion_matrix, reminders, today_ref=today)
    pinned_focus_ids = get_focus_tasks(today)

    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(
            """
            <div style="margin-top: 0.5rem; margin-bottom: 0.5rem;">
                <h3 style="margin: 0; font-size: 1.25rem;">📌 FOCUS TODAY</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_h2:
        if tasks:
            with st.popover("📌 MANAGE FOCUS", use_container_width=True):
                st.markdown("#### Select Tasks for Today's Focus")
                for t in tasks:
                    if isinstance(t, dict):
                        t_id = t["id"]
                        t_name = t["name"]
                        is_focused = t_id in pinned_focus_ids
                        if st.checkbox(f"📌 {t_name}", value=is_focused, key=f"chk_focus_pin_{t_id}"):
                            if not is_focused:
                                toggle_focus_task(today, t_id)
                                st.rerun()
                        else:
                            if is_focused:
                                toggle_focus_task(today, t_id)
                                st.rerun()

    if not recs and not pinned_focus_ids:
        st.caption("No urgent focus items for today.")
        return

    # Add manually pinned tasks to recommendations view
    combined_items = []
    task_map = {t["id"]: t for t in tasks if isinstance(t, dict)}
    for pid in pinned_focus_ids:
        if pid in task_map:
            t = task_map[pid]
            combined_items.append({
                "id": f"pin_{pid}",
                "title": t["name"],
                "reason": "PINNED FOR TODAY",
                "badge_class": "neo-badge-purple",
            })

    for r in recs:
        if not any(ci["title"].lower() == r["title"].lower() for ci in combined_items):
            combined_items.append(r)

    display_items = combined_items[:4]
    cols = st.columns(len(display_items)) if display_items else []

    for idx, item in enumerate(display_items):
        safe_title = html.escape(item['title'])
        safe_reason = html.escape(item['reason'])
        with cols[idx]:
            st.markdown(
                f"""
                <div class="neo-card-purple" style="padding: 0.75rem 0.9rem; margin-bottom: 0.75rem; height: 100%;">
                    <div style="font-size: 0.7rem; font-weight: 800; opacity: 0.7; margin-bottom: 0.2rem;">
                        FOCUS #{idx+1:02d}
                    </div>
                    <div style="font-size: 0.95rem; font-weight: 800; line-height: 1.2; margin-bottom: 0.4rem;">
                        {safe_title}
                    </div>
                    <div>
                        <span class="neo-badge {item['badge_class']}" style="font-size: 0.65rem; padding: 0.15rem 0.4rem; margin: 0;">
                            {safe_reason}
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
