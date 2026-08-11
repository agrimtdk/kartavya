"""
Daily Productivity Brief UI Component for kartavya (Phase 6).

Renders a compact "TODAY / DAILY BRIEF" card on the Timeline Dashboard
displaying daily target %, completion %, completed vs remaining tasks, current streak,
unfinished focus tasks, and today's/overdue global reminders.
Uses native Streamlit columns to guarantee zero raw HTML code block leaks.
"""

import html
from datetime import date
import streamlit as st
from src.data.workspace_store import get_active_workspace, get_daily_target_pct, get_focus_tasks
from src.data.reminder_store import get_sorted_reminders, parse_date
from src.analytics.calculations import calculate_daily_completion, calculate_streaks


def render_daily_brief() -> None:
    """Render compact Daily Brief card for active workspace on Timeline Dashboard."""
    active_ws = get_active_workspace()
    dates = active_ws.get("dates") or []
    tasks = active_ws.get("tasks") or []
    completion_matrix = active_ws.get("completion") or {}
    today = date.today()


    # Calculate today's completion
    daily_today = calculate_daily_completion(today, tasks, completion_matrix)
    completed_today = daily_today["completed"]
    total_today = daily_today["total"]
    pct_today = daily_today["percentage"]
    remaining_today = max(0, total_today - completed_today)

    target_pct = get_daily_target_pct()
    to_go_pct = max(0, round(target_pct - pct_today))

    # Calculate streaks
    streaks = calculate_streaks(dates, tasks, completion_matrix, today_ref=today)
    curr_streak = streaks["current_streak"]

    # Today's focus tasks (pinned or unfinished)
    focused_ids = get_focus_tasks(today)
    today_iso = today.isoformat()
    today_map = completion_matrix.get(today_iso, {})

    task_map = {t["id"]: t["name"] for t in tasks if isinstance(t, dict)}
    pinned_focus_names = [task_map[tid] for tid in focused_ids if tid in task_map]
    unfinished_names = [t["name"] for t in tasks if isinstance(t, dict) and not bool(today_map.get(t["id"], False))]

    display_focus = list(dict.fromkeys(pinned_focus_names + unfinished_names))

    # Global reminders status
    sorted_reminders = get_sorted_reminders()
    due_today_reminders = []
    overdue_reminders = []

    for rem in sorted_reminders:
        if not rem.get("completed", False):
            d_val = parse_date(rem.get("deadline"))
            if isinstance(d_val, date):
                diff = (d_val - today).days
                if diff < 0:
                    overdue_reminders.append(rem)
                elif diff == 0:
                    due_today_reminders.append(rem)

    with st.container():
        brief_header = (
            f'<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--border); padding-bottom: 0.4rem; margin-bottom: 0.75rem;">'
            f'<span class="neo-badge neo-badge-coral" style="font-size: 0.85rem; padding: 0.25rem 0.6rem;">🎯 TODAY\'S BRIEF</span>'
            f'<span style="font-size: 0.85rem; font-weight: 800; text-transform: uppercase;">TARGET: {target_pct:.0f}% • CURRENT: {pct_today}% • {to_go_pct}% TO GO</span>'
            f'</div>'
        )
        st.markdown(brief_header, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            card1 = (
                f'<div style="background-color: var(--surface-alt); border: 2px solid var(--border); padding: 0.6rem; text-align: center;">'
                f'<div style="font-size: 1.6rem; font-weight: 900; line-height: 1; color: var(--primary-text);">{pct_today}%</div>'
                f'<div style="font-size: 0.7rem; font-weight: 800; text-transform: uppercase; margin-top: 0.2rem;">COMPLETED</div>'
                f'</div>'
            )
            st.markdown(card1, unsafe_allow_html=True)

        with c2:
            card2 = (
                f'<div style="background-color: var(--surface-alt); border: 2px solid var(--border); padding: 0.6rem; text-align: center;">'
                f'<div style="font-size: 1.6rem; font-weight: 900; line-height: 1;">{completed_today} / {total_today}</div>'
                f'<div style="font-size: 0.7rem; font-weight: 800; text-transform: uppercase; margin-top: 0.2rem;">TASKS DONE</div>'
                f'</div>'
            )
            st.markdown(card2, unsafe_allow_html=True)

        with c3:
            card3 = (
                f'<div style="background-color: var(--surface-alt); border: 2px solid var(--border); padding: 0.6rem; text-align: center;">'
                f'<div style="font-size: 1.6rem; font-weight: 900; line-height: 1; color: var(--highlight-text);">{remaining_today}</div>'
                f'<div style="font-size: 0.7rem; font-weight: 800; text-transform: uppercase; margin-top: 0.2rem;">REMAINING</div>'
                f'</div>'
            )
            st.markdown(card3, unsafe_allow_html=True)

        with c4:
            card4 = (
                f'<div style="background-color: var(--surface-alt); border: 2px solid var(--border); padding: 0.6rem; text-align: center;">'
                f'<div style="font-size: 1.6rem; font-weight: 900; line-height: 1;">🔥 {curr_streak}</div>'
                f'<div style="font-size: 0.7rem; font-weight: 800; text-transform: uppercase; margin-top: 0.2rem;">DAY STREAK</div>'
                f'</div>'
            )
            st.markdown(card4, unsafe_allow_html=True)

        f1, f2 = st.columns(2)

        with f1:
            st.markdown("<div style='margin-top: 0.5rem;'><strong>FOCUS TASKS:</strong></div>", unsafe_allow_html=True)
            if display_focus:
                for t_name in display_focus[:3]:
                    st.markdown(f"• **{t_name}**")
            else:
                st.caption("All tasks completed today! 🎉")

        with f2:
            st.markdown("<div style='margin-top: 0.5rem;'><strong>URGENT REMINDERS:</strong></div>", unsafe_allow_html=True)
            if overdue_reminders or due_today_reminders:
                for r in overdue_reminders[:2]:
                    st.markdown(f"⚠️ **{r['title']}** (OVERDUE)")
                for r in due_today_reminders[:2]:
                    st.markdown(f"🔔 **{r['title']}** (DUE TODAY)")
            else:
                st.caption("No overdue or urgent reminders.")

        st.markdown("<div style='margin-bottom: 1.25rem;'></div>", unsafe_allow_html=True)
