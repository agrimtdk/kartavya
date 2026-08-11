"""
Timeline UI Component for kartavya (Phase 6 with Stable Task IDs & Priorities).

Renders spreadsheet-style daily task timeline grid for active workspace,
interactive checkboxes with workspace-isolated keys and canonical state sync by task_id,
task priority badges, notes tooltips, recurrence indicators, and task/date management controls.
"""

import html
from datetime import date
import streamlit as st
from src.data.workspace_store import get_active_workspace_id
from src.data.task_store import (
    get_dates,
    get_tasks,
    get_task_by_id,
    add_previous_day,
    add_future_day,
    add_task,
    rename_task,
    update_task_metadata,
    remove_task,
    get_completion,
    set_completion,
    get_daily_completion,
    is_task_applicable_on_date,
)
from src.config import PRIORITY_CHOICES, PRIORITY_MEDIUM, PRIORITY_HIGH, PRIORITY_LOW, MAX_TASK_NAME_LEN


def on_checkbox_change(d_iso: str, t_id: str, chk_key: str) -> None:
    """Callback to sync checkbox widget state directly into active workspace canonical completion matrix by task_id."""
    d_obj = date.fromisoformat(d_iso)
    if d_obj > date.today():
        return
    new_val = st.session_state.get(chk_key, False)
    set_completion(d_obj, t_id, new_val)


def render_timeline_controls() -> None:
    """Render control buttons for adding previous/future days, adding tasks, editing tasks, and removing tasks."""
    st.markdown("### 🛠️ Timeline Controls")

    col_btn1, col_btn2, col_btn3, col_btn4, col_btn5 = st.columns([1, 1, 1, 1, 1], gap="small")

    with col_btn1:
        if st.button("⬅️ PREVIOUS DAY", use_container_width=True, key="btn_add_prev_day"):
            prev_date = add_previous_day()
            st.toast(f"Added previous date: {prev_date.strftime('%b %d, %Y')}", icon="📅")
            st.rerun()

    with col_btn2:
        if st.button("FUTURE DAY ➡️", use_container_width=True, key="btn_add_fut_day"):
            next_date = add_future_day()
            st.toast(f"Added future date: {next_date.strftime('%b %d, %Y')}", icon="📅")
            st.rerun()

    with col_btn3:
        with st.popover("➕ ADD TASK", use_container_width=True):
            st.markdown("#### Quick Add New Task")
            new_name = st.text_input("Task Name", placeholder="e.g. Reading, Python, LeetCode", max_chars=MAX_TASK_NAME_LEN, key="input_new_task_name")
            new_prio = st.selectbox("Priority", options=PRIORITY_CHOICES, index=1, key="select_new_task_prio")
            new_desc = st.text_area("Task Notes / Description (Optional)", placeholder="e.g. Finish graph BFS problems", key="input_new_task_desc")

            if st.button("Confirm Add Task", use_container_width=True, key="btn_confirm_add_task"):
                success, msg = add_task(new_name, new_prio, new_desc)
                if success:
                    st.toast(msg, icon="⚡")
                    st.rerun()
                else:
                    st.error(msg)

    with col_btn4:
        tasks = get_tasks()
        if not tasks:
            st.button("✏️ EDIT TASK", use_container_width=True, disabled=True, key="btn_edit_task_disabled")
        else:
            with st.popover("✏️ EDIT TASK", use_container_width=True):
                st.markdown("#### Edit Task Details")
                task_options = {t["id"]: f"{t['name']} ({t.get('priority', 'Medium')})" for t in tasks}
                selected_t_id = st.selectbox(
                    "Select Task to Edit",
                    options=list(task_options.keys()),
                    format_func=lambda x: task_options[x],
                    key="select_edit_task_id",
                )
                sel_task = get_task_by_id(selected_t_id) if selected_t_id else tasks[0]

                if sel_task:
                    edit_name = st.text_input("Task Name", value=sel_task["name"], max_chars=MAX_TASK_NAME_LEN, key="input_edit_task_name")
                    edit_prio = st.selectbox("Priority", options=PRIORITY_CHOICES, index=PRIORITY_CHOICES.index(sel_task.get("priority", "Medium")), key="select_edit_task_prio")
                    edit_desc = st.text_area("Description / Notes", value=sel_task.get("description", ""), key="input_edit_task_desc")

                    # Recurrence settings
                    cur_rec = sel_task.get("recurrence", {"type": "none", "days": []})
                    rec_type_opts = ["none", "daily", "weekdays", "weekly", "custom_weekdays"]
                    cur_type_idx = rec_type_opts.index(cur_rec.get("type", "none")) if cur_rec.get("type", "none") in rec_type_opts else 0
                    rec_type = st.selectbox("Recurrence Pattern", options=rec_type_opts, index=cur_type_idx, key="select_edit_task_rec_type")

                    custom_days = cur_rec.get("days", [])
                    if rec_type == "custom_weekdays":
                        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                        selected_days = st.multiselect(
                            "Active Days",
                            options=list(range(7)),
                            default=custom_days,
                            format_func=lambda d: day_names[d],
                            key="select_edit_task_rec_days",
                        )
                        custom_days = selected_days
                    elif rec_type == "weekly":
                        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                        default_day = custom_days[0] if custom_days else 0
                        sel_day = st.selectbox("Day of Week", options=list(range(7)), index=default_day, format_func=lambda d: day_names[d], key="select_edit_task_rec_day")
                        custom_days = [sel_day]

                    if st.button("Save Task Changes", use_container_width=True, key="btn_confirm_edit_task"):
                        rec_payload = {"type": rec_type, "days": custom_days}
                        success, msg = update_task_metadata(selected_t_id, edit_name, edit_prio, edit_desc, rec_payload)
                        if success:
                            st.toast(msg, icon="✅")
                            st.rerun()
                        else:
                            st.error(msg)

    with col_btn5:
        tasks = get_tasks()
        if not tasks:
            st.button("🗑️ REMOVE TASK", use_container_width=True, disabled=True, key="btn_remove_task_disabled")
        else:
            with st.popover("🗑️ REMOVE TASK", use_container_width=True):
                st.markdown("#### Remove Task")
                task_options = {t["id"]: t["name"] for t in tasks}
                del_t_id = st.selectbox(
                    "Select Task to Delete",
                    options=list(task_options.keys()),
                    format_func=lambda x: task_options[x],
                    key="select_delete_task_id",
                )

                st.warning("⚠️ Deleting a task will remove its definition and completion history.")
                confirm_del = st.checkbox("Confirm task deletion", key="chk_confirm_delete_task")

                if st.button("Confirm Delete Task", use_container_width=True, key="btn_confirm_delete_task"):
                    if confirm_del and del_t_id:
                        success, msg = remove_task(del_t_id)
                        if success:
                            st.toast(msg, icon="🗑️")
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.error("Check the confirmation box first.")


def trigger_confetti_and_sound():
    import streamlit.components.v1 as components
    st.balloons()
    js = """
    <script>
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gainNode = ctx.createGain();
        osc.connect(gainNode);
        gainNode.connect(ctx.destination);
        osc.type = 'sine';
        osc.frequency.setValueAtTime(523.25, ctx.currentTime);
        osc.frequency.setValueAtTime(659.25, ctx.currentTime + 0.15);
        osc.frequency.setValueAtTime(783.99, ctx.currentTime + 0.3);
        osc.frequency.setValueAtTime(1046.50, ctx.currentTime + 0.45);
        gainNode.gain.setValueAtTime(0, ctx.currentTime);
        gainNode.gain.linearRampToValueAtTime(0.5, ctx.currentTime + 0.05);
        gainNode.gain.setValueAtTime(0.5, ctx.currentTime + 0.4);
        gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.5);
        osc.start(ctx.currentTime);
        osc.stop(ctx.currentTime + 1.5);
    } catch(e) {}
    </script>
    """
    components.html(js, height=0, width=0)



def render_timeline_grid() -> None:
    """Render spreadsheet-like daily task timeline grid with priorities, recurrence indicators, and interactive checkboxes."""
    dates = get_dates()
    tasks = get_tasks()
    ws_id = get_active_workspace_id()
    
    from src.data.workspace_store import get_active_workspace
    active_ws = get_active_workspace()
    completion_matrix = active_ws.get("completion") or {}

    today = date.today()
    today_iso = today.isoformat()
    daily_today = get_daily_completion(today, tasks_list=tasks, completion_matrix=completion_matrix)
    confetti_key = f"confetti_today_{ws_id}_{today_iso}"
    
    if daily_today["percentage"] == 100 and daily_today["total"] > 0:
        if not st.session_state.get(confetti_key, False):
            trigger_confetti_and_sound()
            st.session_state[confetti_key] = True
    else:
        st.session_state[confetti_key] = False

    if not tasks:
        st.markdown(
            """
            <div class="neo-card-yellow" style="text-align: center; padding: 2rem 1.5rem;">
                <h2 style="font-size: 1.8rem; margin-bottom: 0.5rem; color: var(--primary-text) !important;">📋 NO TASKS IN THIS WORKSPACE YET</h2>
                <p style="font-size: 1.05rem; font-weight: 600; margin-bottom: 1rem; color: var(--primary-text) !important;">
                    Click <strong>➕ ADD TASK</strong> above to create your first task column for this workspace.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 📅 DAILY TIMELINE")

    st.markdown('<div class="neo-timeline-wrapper">', unsafe_allow_html=True)

    col_widths = [2.2] + [1.3] * len(tasks) + [1.5]

    # --- Fixed Task Column Headers (Always visible above scrollable date rows) ---
    headers = st.columns(col_widths, gap="small")

    with headers[0]:
        st.markdown(
            '<div style="font-weight:900; font-size:0.95rem; text-transform:uppercase; padding:0.4rem 0; color:var(--text);">DATE</div>',
            unsafe_allow_html=True,
        )

    for idx, t_obj in enumerate(tasks):
        t_id = t_obj["id"]
        t_name = t_obj["name"]
        prio = t_obj.get("priority", PRIORITY_MEDIUM)
        desc = t_obj.get("description", "")
        rec = t_obj.get("recurrence", {})

        prio_badge_class = "neo-badge-coral" if prio == PRIORITY_HIGH else ("neo-badge-cyan" if prio == PRIORITY_MEDIUM else "neo-badge-outline")
        rec_type = rec.get("type", "none")
        rec_label = f" 🔁 {rec_type.upper()}" if rec_type != "none" else ""

        safe_name = html.escape(t_name)
        safe_desc = html.escape(desc) if desc else ""
        tooltip = html.escape(f"{t_name} ({prio} Priority){f': {desc}' if desc else ''}")

        with headers[idx + 1]:
            st.markdown(
                f"""
                <div title="{tooltip}" style="background-color:var(--surface); color:var(--text); border:2px solid var(--border); box-shadow:2px 2px 0px var(--shadow); padding:0.35rem 0.4rem; text-align:center;">
                    <div style="font-weight:900; font-size:0.85rem; text-transform:uppercase; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{safe_name}</div>
                    <div style="margin-top:0.15rem;">
                        <span class="neo-badge {prio_badge_class}" style="font-size:0.6rem; padding:0.1rem 0.3rem; margin:0;">{prio[:1]}</span>
                        <span style="font-size:0.6rem; font-weight:800;">{rec_label}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with headers[-1]:
        st.markdown(
            '<div style="font-weight:900; font-size:0.95rem; text-transform:uppercase; text-align:center; padding:0.4rem 0; color:var(--text);">DAILY %</div>',
            unsafe_allow_html=True,
        )

    # --- Timeline Date Rows (Internal Scroll Window ~14 Days) ---
    today = date.today()

    st.markdown('<div style="border-bottom: 2px solid var(--border); margin: 0.4rem 0 0.5rem 0;"></div>', unsafe_allow_html=True)

    with st.container(height=520):
        for d in dates:
            row_cols = st.columns(col_widths, gap="small")
            is_today = d == today
            is_future = d > today
            date_fmt = d.strftime("%d %b %Y").upper()
            day_fmt = d.strftime("%A").upper()
            d_iso = d.isoformat()

            # Date Cell
            with row_cols[0]:
                if is_today:
                    date_cell_html = f'<div id="timeline-today-row" style="padding:0.2rem 0;"><span class="neo-badge">TODAY</span><br><strong style="font-size:0.95rem; display:block; line-height:1.1; color:var(--text);">{date_fmt}</strong><span style="font-size:0.75rem; font-weight:700; color:var(--text-muted);">{day_fmt}</span></div>'
                elif is_future:
                    date_cell_html = f'<div style="padding:0.2rem 0;"><span class="neo-badge neo-badge-cyan" style="font-size:0.65rem; padding:0.15rem 0.4rem; margin:0;">PLANNED</span><br><strong style="font-size:0.95rem; display:block; line-height:1.1; color:var(--text);">{date_fmt}</strong><span style="font-size:0.75rem; font-weight:700; color:var(--text-muted);">{day_fmt}</span></div>'
                else:
                    date_cell_html = f'<div style="padding:0.2rem 0;"><strong style="font-size:0.95rem; display:block; line-height:1.1; color:var(--text);">{date_fmt}</strong><span style="font-size:0.75rem; font-weight:700; color:var(--text-muted);">{day_fmt}</span></div>'

                st.markdown(date_cell_html, unsafe_allow_html=True)

            # Task Checkboxes / Applicability Badges
            for idx, t_obj in enumerate(tasks):
                t_id = t_obj["id"]
                t_name = t_obj["name"]
                is_app = is_task_applicable_on_date(t_obj, d)

                with row_cols[idx + 1]:
                    if is_app:
                        chk_key = f"chk_{ws_id}_{d_iso}_{t_id}"
                        canonical_val = get_completion(d, t_id, completion_matrix=completion_matrix)

                        st.checkbox(
                            label=t_name,
                            value=canonical_val,
                            key=chk_key,
                            on_change=on_checkbox_change,
                            args=(d_iso, t_id, chk_key),
                            label_visibility="collapsed",
                            disabled=is_future,
                        )
                    else:
                        st.markdown(
                            '<div style="padding:0.35rem 0; text-align:center;"><span class="neo-badge-outline" style="font-size:0.7rem; opacity:0.5; margin:0;">[OFF]</span></div>',
                            unsafe_allow_html=True,
                        )

            # Daily Completion % Cell
            daily_stats = get_daily_completion(d, tasks_list=tasks, completion_matrix=completion_matrix)
            pct = daily_stats["percentage"]

            if pct == 100:
                badge_class = "neo-badge"
                badge_text = "100% 🎉"
            elif pct >= 50:
                badge_class = "neo-badge-cyan"
                badge_text = f"{pct}%"
            elif pct > 0:
                badge_class = "neo-badge-coral"
                badge_text = f"{pct}%"
            else:
                badge_class = "neo-badge-outline"
                badge_text = "0%"

            with row_cols[-1]:
                if pct == 100 and d == today:
                    st.markdown(
                        f'<div style="padding:0.35rem 0; text-align:center;"><span id="badge_100_today" class="neo-badge {badge_class}" style="font-size:0.8rem; margin:0; cursor:pointer;" title="Click to celebrate!">{badge_text}</span></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div style="padding:0.35rem 0; text-align:center;"><span class="neo-badge {badge_class}" style="font-size:0.8rem; margin:0;">{badge_text}</span></div>',
                        unsafe_allow_html=True,
                    )

            st.markdown(
                '<div style="border-bottom: 2px solid var(--divider); margin: 0.3rem 0 0.5rem 0;"></div>',
                unsafe_allow_html=True,
            )

    import streamlit.components.v1 as components
    components.html(
        """
        <script>
            function attachConfetti() {
                const badge = window.parent.document.getElementById("badge_100_today");
                if (badge && !badge.dataset.confettiAttached) {
                    badge.dataset.confettiAttached = "true";
                    badge.onclick = function() {
                        try {
                            const ctx = new (window.parent.AudioContext || window.parent.webkitAudioContext)();
                            const osc = ctx.createOscillator();
                            const gainNode = ctx.createGain();
                            osc.connect(gainNode);
                            gainNode.connect(ctx.destination);
                            osc.type = 'sine';
                            osc.frequency.setValueAtTime(523.25, ctx.currentTime);
                            osc.frequency.setValueAtTime(659.25, ctx.currentTime + 0.15);
                            osc.frequency.setValueAtTime(783.99, ctx.currentTime + 0.3);
                            osc.frequency.setValueAtTime(1046.50, ctx.currentTime + 0.45);
                            gainNode.gain.setValueAtTime(0, ctx.currentTime);
                            gainNode.gain.linearRampToValueAtTime(0.5, ctx.currentTime + 0.05);
                            gainNode.gain.setValueAtTime(0.5, ctx.currentTime + 0.4);
                            gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.5);
                            osc.start(ctx.currentTime);
                            osc.stop(ctx.currentTime + 1.5);

                            const script = window.parent.document.createElement("script");
                            script.src = "https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js";
                            script.onload = function() {
                                window.parent.confetti({
                                    particleCount: 150,
                                    spread: 90,
                                    origin: { y: 0.6 }
                                });
                            };
                            window.parent.document.head.appendChild(script);
                        } catch(e) {}
                    };
                }
            }
            
            function scrollToToday() {
                const els = window.parent.document.querySelectorAll('div[data-testid="stMarkdownContainer"] strong');
                for (let el of els) {
                    if (el.innerText.includes("TODAY")) {
                        el.scrollIntoView({ behavior: "smooth", block: "center" });
                        break;
                    }
                }
            }
            
            setTimeout(attachConfetti, 500);
            setTimeout(scrollToToday, 500);
        </script>
        """,
        height=0,
        width=0,
    )
    st.markdown('</div>', unsafe_allow_html=True)



def render_timeline() -> None:
    """Render complete timeline section: controls and grid."""
    render_timeline_controls()
    render_timeline_grid()
