"""
Global Reminders UI Component for kartavya (Phase 6 with Grouped Calendar Filter Views).

Renders global reminders, priority badges, dynamic deadline status,
Grouped Calendar Views (All, Overdue, Today, Tomorrow, This Week, Later, Completed),
Quick Add Reminder modal, and edit/delete/complete action controls.
"""

import html
from datetime import date, timedelta
import streamlit as st
from src.data.reminder_store import (
    get_sorted_reminders,
    get_deadline_status,
    add_reminder,
    edit_reminder,
    delete_reminder,
    toggle_reminder_status,
    parse_date,
)
from src.config import MAX_TITLE_LEN


def render_reminders() -> None:
    """Render global reminders section, add reminder popover, calendar filter tabs, and reminder cards."""
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 🔔 Global Reminders")

    # Add Reminder Popover Button
    with st.popover("➕ ADD REMINDER", use_container_width=True):
        st.markdown("#### Add Global Reminder")
        rem_title = st.text_input(
            "Title",
            placeholder="e.g. Submit Report, Pay Bill, Contest",
            max_chars=MAX_TITLE_LEN,
            key="input_add_rem_title",
        )

        rem_deadline = st.date_input(
            "Deadline Date",
            value=date.today(),
            key="input_add_rem_deadline",
        )
        rem_priority = st.selectbox(
            "Priority",
            options=["High", "Medium", "Low"],
            index=1,
            key="select_add_rem_priority",
        )
        rem_desc = st.text_area(
            "Description (Optional)",
            placeholder="Reminder details...",
            key="input_add_rem_desc",
            height=80,
        )

        if st.button("Confirm Add Reminder", use_container_width=True, key="btn_confirm_add_rem"):
            success, msg = add_reminder(rem_title, rem_desc, rem_deadline, rem_priority)
            if success:
                st.toast(msg, icon="🔔")
                st.rerun()
            else:
                st.error(msg)

    sorted_reminders = get_sorted_reminders()

    if not sorted_reminders:
        st.caption("No reminders set yet.")
        return

    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)

    # Calendar Filter View Tabs
    tab_all, tab_overdue, tab_today, tab_tomorrow, tab_week, tab_later, tab_done = st.tabs(
        ["All", "Overdue", "Today", "Tomorrow", "This Week", "Later", "Completed"]
    )

    today = date.today()
    tomorrow = today + timedelta(days=1)
    end_of_week = today + timedelta(days=6)

    def filter_reminders_by_category(cat: str) -> list[dict]:
        res = []
        for r in sorted_reminders:
            is_comp = r.get("completed", False)
            d_val = parse_date(r.get("deadline"))

            if cat == "done":
                if is_comp:
                    res.append(r)
                continue

            if is_comp:
                continue

            if cat == "all":
                res.append(r)
            elif cat == "overdue":
                if isinstance(d_val, date) and d_val < today:
                    res.append(r)
            elif cat == "today":
                if isinstance(d_val, date) and d_val == today:
                    res.append(r)
            elif cat == "tomorrow":
                if isinstance(d_val, date) and d_val == tomorrow:
                    res.append(r)
            elif cat == "week":
                if isinstance(d_val, date) and today <= d_val <= end_of_week:
                    res.append(r)
            elif cat == "later":
                if isinstance(d_val, date) and d_val > end_of_week:
                    res.append(r)
        return res

    tab_map = [
        (tab_all, "all"),
        (tab_overdue, "overdue"),
        (tab_today, "today"),
        (tab_tomorrow, "tomorrow"),
        (tab_week, "week"),
        (tab_later, "later"),
        (tab_done, "done"),
    ]

    for tab_obj, cat in tab_map:
        with tab_obj:
            cat_list = filter_reminders_by_category(cat)
            if not cat_list:
                st.caption(f"No {cat.replace('_', ' ')} reminders.")
                continue

            for rem in cat_list:
                r_id = rem["id"]
                is_completed = rem.get("completed", False)
                title = rem.get("title", "")
                desc = rem.get("description", "")
                priority = rem.get("priority", "Medium")
                raw_deadline = rem.get("deadline")
                parsed_deadline = parse_date(raw_deadline)

                p_badge_class = "neo-badge-coral" if priority == "High" else ("neo-badge-cyan" if priority == "Medium" else "neo-badge-outline")
                status_text, category = get_deadline_status(parsed_deadline)
                d_badge_class = "neo-badge-coral" if category == "overdue" else ("neo-badge" if category == "today" else "neo-badge-cyan")

                safe_title = html.escape(title)
                safe_desc = html.escape(desc) if desc else ""

                title_display = f"<s>{safe_title}</s>" if is_completed else f"<strong>{safe_title}</strong>"
                card_opacity = "opacity: 0.65;" if is_completed else ""

                with st.container():
                    st.markdown(
                        f"""
                        <div class="neo-card" style="padding: 0.75rem 1rem; margin-bottom: 0.6rem; {card_opacity}">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 0.5rem; margin-bottom: 0.4rem;">
                                <div style="font-size: 0.95rem; line-height: 1.2;">
                                    {title_display}
                                </div>
                                <div>
                                    <span class="neo-badge {p_badge_class}" style="font-size: 0.65rem; padding: 0.15rem 0.4rem; margin: 0;">{priority}</span>
                                </div>
                            </div>
                            <div style="margin-bottom: 0.4rem;">
                                <span class="neo-badge {d_badge_class}" style="font-size: 0.65rem; padding: 0.15rem 0.4rem; margin: 0;">{status_text}</span>
                            </div>
                            {f'<div style="font-size: 0.75rem; opacity: 0.85; margin-bottom: 0.4rem;">{safe_desc}</div>' if safe_desc else ''}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    col_act1, col_act2, col_act3 = st.columns([1.2, 1, 0.8], gap="small")

                    with col_act1:
                        chk_state = is_completed
                        if st.checkbox(
                            "Done" if is_completed else "Mark Done",
                            value=chk_state,
                            key=f"chk_rem_{r_id}_{cat}",
                        ):
                            if not is_completed:
                                toggle_reminder_status(r_id)
                                st.rerun()
                        else:
                            if is_completed:
                                toggle_reminder_status(r_id)
                                st.rerun()

                    with col_act2:
                        with st.popover("✏️ Edit", use_container_width=True, key=f"pop_edit_rem_{r_id}_{cat}"):
                            st.markdown("#### Edit Reminder")
                            e_title = st.text_input("Title", value=title, key=f"edit_rem_title_{r_id}_{cat}")
                            e_deadline = st.date_input(
                                "Deadline",
                                value=parsed_deadline if isinstance(parsed_deadline, date) else date.today(),
                                key=f"edit_rem_date_{r_id}_{cat}",
                            )
                            e_priority = st.selectbox(
                                "Priority",
                                options=["High", "Medium", "Low"],
                                index=["High", "Medium", "Low"].index(priority) if priority in ["High", "Medium", "Low"] else 1,
                                key=f"edit_rem_prio_{r_id}_{cat}",
                            )
                            e_desc = st.text_area("Description", value=desc, key=f"edit_rem_desc_{r_id}_{cat}", height=70)

                            if st.button("Save", use_container_width=True, key=f"btn_save_rem_{r_id}_{cat}"):
                                success, msg = edit_reminder(r_id, e_title, e_desc, e_deadline, e_priority)
                                if success:
                                    st.toast(msg, icon="✅")
                                    st.rerun()
                                else:
                                    st.error(msg)

                    with col_act3:
                        if st.button("🗑️", key=f"btn_del_rem_{r_id}_{cat}", use_container_width=True):
                            success, msg = delete_reminder(r_id)
                            if success:
                                st.toast(msg, icon="🗑️")
                                st.rerun()
