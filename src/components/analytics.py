"""
Productivity Analytics & Insights Component for kartavya (Phase 5).

Renders workspace-isolated productivity metrics, date range filters, workspace goals,
period comparisons, task health classifications, productivity insights, weekly summary,
and global reminder intelligence.
Full Light Mode compatibility with Neo-Brutalist design tokens.
"""

from datetime import date
import pandas as pd
import streamlit as st
import html
from src.data.workspace_store import get_active_workspace
from src.data.task_store import get_dates, get_tasks
from src.data.reminder_store import get_reminders
from src.analytics.calculations import (
    calculate_workspace_metrics,
    calculate_daily_completion,
    calculate_task_performance,
    calculate_recent_insights,
    calculate_global_reminder_summary,
)
from src.analytics.heatmap import render_productivity_heatmap
from src.analytics.insights import (
    calculate_task_health,
    calculate_period_comparison,
    calculate_productivity_insights,
    calculate_productivity_patterns,
    calculate_weekly_summary,
)
from src.components.goals import render_workspace_goals


def render_analytics_header(active_ws_name: str) -> str:
    """Renders page title and date range filter controls. Returns selected range_type."""
    hdr_html = (
        f'<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; margin-bottom: 1.5rem;">'
        f'<div>'
        f'<h1 style="margin: 0; font-size: 2.2rem;">📊 Productivity Analytics</h1>'
        f'<div style="margin-top: 0.25rem;">'
        f'<span class="neo-badge neo-badge-cyan" style="font-size: 0.8rem; padding: 0.25rem 0.6rem;">WORKSPACE: {html.escape(active_ws_name.upper())}</span>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(hdr_html, unsafe_allow_html=True)

    # Date Range Filter Selector
    filter_col1, filter_col2, filter_col3 = st.columns([2, 1.5, 1.5], gap="small")

    with filter_col1:
        range_option = st.selectbox(
            "📅 Date Range Filter",
            options=[
                "All Time",
                "Last 7 Days",
                "Last 14 Days",
                "Last 30 Days",
                "This Week",
                "This Month",
                "Custom Date Range",
            ],
            index=0,
            key="select_analytics_date_range",
        )

    option_map = {
        "All Time": "all_time",
        "Last 7 Days": "last_7",
        "Last 14 Days": "last_14",
        "Last 30 Days": "last_30",
        "This Week": "this_week",
        "This Month": "this_month",
        "Custom Date Range": "custom",
    }

    custom_start = None
    custom_end = None

    if range_option == "Custom Date Range":
        with filter_col2:
            custom_start = st.date_input(
                "Start Date",
                value=st.session_state.get("_analytics_custom_start", date.today()),
                key="input_analytics_custom_start",
            )
        with filter_col3:
            custom_end = st.date_input(
                "End Date",
                value=st.session_state.get("_analytics_custom_end", date.today()),
                key="input_analytics_custom_end",
            )

    range_type = option_map.get(range_option, "all_time")
    st.session_state["_analytics_custom_start"] = custom_start
    st.session_state["_analytics_custom_end"] = custom_end
    return range_type


def render_empty_analytics_state() -> None:
    """Renders Neo-Brutalist empty state when workspace has no tasks or timeline dates."""
    empty_html = (
        f'<div class="neo-card-yellow" style="text-align: center; padding: 2.5rem 1.5rem; margin-bottom: 2rem;">'
        f'<h2 style="margin-top: 0; color: #000000 !important; font-size: 1.8rem;">⚡ NOT ENOUGH DATA YET</h2>'
        f'<p style="font-size: 1.05rem; font-weight: 600; color: #000000 !important; max-width: 600px; margin: 0.75rem auto 0 auto;">'
        f'Not enough data yet. Start adding tasks and completing daily timeline items to unlock your productivity insights.'
        f'</p>'
        f'</div>'
    )
    st.markdown(empty_html, unsafe_allow_html=True)


def render_summary_metrics(metrics: dict) -> None:
    """Renders 4 Neo-Brutalist summary metric cards."""
    col1, col2, col3, col4 = st.columns(4, gap="medium")

    with col1:
        c1_html = (
            f'<div class="neo-card-yellow" style="min-height: 140px; display: flex; flex-direction: column; justify-content: space-between;">'
            f'<div style="font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; color: #000000 !important;">Overall Completion</div>'
            f'<div style="font-size: 2.5rem; font-weight: 900; line-height: 1.1; color: #000000 !important; margin: 0.4rem 0;">{metrics["overall_completion_pct"]}%</div>'
            f'<div style="font-size: 0.78rem; font-weight: 700; color: #000000 !important;">{metrics["completed_instances"]} / {metrics["total_instances"]} task instances</div>'
            f'</div>'
        )
        st.markdown(c1_html, unsafe_allow_html=True)

    with col2:
        c2_html = (
            f'<div class="neo-card-cyan" style="min-height: 140px; display: flex; flex-direction: column; justify-content: space-between;">'
            f'<div style="font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; color: #000000 !important;">Productivity Streaks</div>'
            f'<div style="font-size: 2.2rem; font-weight: 900; line-height: 1.1; color: #000000 !important; margin: 0.4rem 0;">🔥 {metrics["current_streak"]} <span style="font-size: 1rem; font-weight: 700;">DAYS</span></div>'
            f'<div style="font-size: 0.78rem; font-weight: 700; color: #000000 !important;">Best Streak: 🏆 {metrics["best_streak"]} Days</div>'
            f'</div>'
        )
        st.markdown(c2_html, unsafe_allow_html=True)

    with col3:
        c3_html = (
            f'<div class="neo-card" style="min-height: 140px; display: flex; flex-direction: column; justify-content: space-between;">'
            f'<div style="font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.9;">Daily Consistency</div>'
            f'<div style="font-size: 1.1rem; font-weight: 900; line-height: 1.4; margin: 0.4rem 0;">'
            f'<span style="color: var(--success, #00E676);">100%: {metrics["fully_completed_days"]}d</span> • '
            f'<span style="color: var(--primary, #FFE600);">Partial: {metrics["partially_completed_days"]}d</span> • '
            f'<span style="color: var(--danger, #FF5277);">0%: {metrics["zero_completion_days"]}d</span>'
            f'</div>'
            f'<div style="font-size: 0.78rem; font-weight: 700; opacity: 0.85;">Avg Daily: {metrics["avg_daily_completion_pct"]}%</div>'
            f'</div>'
        )
        st.markdown(c3_html, unsafe_allow_html=True)

    with col4:
        c4_html = (
            f'<div class="neo-card-coral" style="min-height: 140px; display: flex; flex-direction: column; justify-content: space-between;">'
            f'<div style="font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; color: #000000 !important;">Recent Task Volume</div>'
            f'<div style="font-size: 1.1rem; font-weight: 900; line-height: 1.4; color: #000000 !important; margin: 0.4rem 0;">Last 7 Days: {metrics["completed_last_7_days"]} done<br>Last 30 Days: {metrics["completed_last_30_days"]} done</div>'
            f'<div style="font-size: 0.78rem; font-weight: 700; color: #000000 !important;">Defined Tasks: {metrics["total_tasks"]}</div>'
            f'</div>'
        )
        st.markdown(c4_html, unsafe_allow_html=True)


def render_period_comparison(
    dates: list[date],
    tasks: list[str],
    completion_matrix: dict[str, dict[str, bool]],
    range_type: str,
    custom_start: date | None = None,
    custom_end: date | None = None,
) -> None:
    """Renders Period Comparison card (Current Period vs Previous Equivalent Period)."""
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 🔄 Period Comparison")

    comp = calculate_period_comparison(dates, tasks, completion_matrix, range_type, custom_start, custom_end)

    if not comp.get("has_comparison"):
        st.caption(comp.get("message", "No comparison available."))
        return

    delta_pct = comp["completion_pct_delta"]
    pct_sign = "+" if delta_pct >= 0 else ""
    pct_color = "var(--success, #00E676)" if delta_pct >= 0 else "var(--danger, #FF5277)"

    delta_inst = comp["completed_instances_delta"]
    inst_sign = "+" if delta_inst >= 0 else ""

    col_c1, col_c2, col_c3, col_c4 = st.columns(4)

    with col_c1:
        pc1 = (
            f'<div class="neo-card" style="padding: 0.75rem 1rem;">'
            f'<div style="font-size: 0.75rem; font-weight: 800; text-transform: uppercase;">Completion %</div>'
            f'<div style="font-size: 1.6rem; font-weight: 900; margin: 0.2rem 0;">{comp["current_completion_pct"]}%</div>'
            f'<div style="font-size: 0.8rem; font-weight: 800; color: {pct_color};">{pct_sign}{delta_pct}% vs Prev ({comp["prev_completion_pct"]}%)</div>'
            f'</div>'
        )
        st.markdown(pc1, unsafe_allow_html=True)

    with col_c2:
        pc2 = (
            f'<div class="neo-card" style="padding: 0.75rem 1rem;">'
            f'<div style="font-size: 0.75rem; font-weight: 800; text-transform: uppercase;">Tasks Completed</div>'
            f'<div style="font-size: 1.6rem; font-weight: 900; margin: 0.2rem 0;">{comp["current_completed_instances"]}</div>'
            f'<div style="font-size: 0.8rem; font-weight: 800; color: {pct_color};">{inst_sign}{delta_inst} vs Prev ({comp["prev_completed_instances"]})</div>'
            f'</div>'
        )
        st.markdown(pc2, unsafe_allow_html=True)

    with col_c3:
        pc3 = (
            f'<div class="neo-card" style="padding: 0.75rem 1rem;">'
            f'<div style="font-size: 0.75rem; font-weight: 800; text-transform: uppercase;">Avg Daily Completion</div>'
            f'<div style="font-size: 1.6rem; font-weight: 900; margin: 0.2rem 0;">{comp["current_avg_daily_pct"]}%</div>'
            f'<div style="font-size: 0.8rem; font-weight: 800;">Prev: {comp["prev_avg_daily_pct"]}%</div>'
            f'</div>'
        )
        st.markdown(pc3, unsafe_allow_html=True)

    with col_c4:
        pc4 = (
            f'<div class="neo-card" style="padding: 0.75rem 1rem;">'
            f'<div style="font-size: 0.75rem; font-weight: 800; text-transform: uppercase;">100% Completed Days</div>'
            f'<div style="font-size: 1.6rem; font-weight: 900; margin: 0.2rem 0;">{comp["current_fully_completed_days"]}</div>'
            f'<div style="font-size: 0.8rem; font-weight: 800;">Prev: {comp["prev_fully_completed_days"]}</div>'
            f'</div>'
        )
        st.markdown(pc4, unsafe_allow_html=True)


def render_task_health_section(
    dates: list[date],
    tasks: list[str],
    completion_matrix: dict[str, dict[str, bool]],
) -> None:
    """Renders Task Health Classification card."""
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 🩺 Task Health Classification")

    health_data = calculate_task_health(dates, tasks, completion_matrix)

    if not health_data:
        st.caption("No task health data available.")
        return

    cols = st.columns(min(4, len(health_data)))
    for idx, h in enumerate(health_data):
        col_idx = idx % min(4, len(health_data))
        with cols[col_idx]:
            h_card = (
                f'<div class="neo-card" style="padding: 0.75rem 1rem; margin-bottom: 0.75rem;">'
                f'<div style="font-size: 0.95rem; font-weight: 800; margin-bottom: 0.3rem;">{html.escape(h["task"])}</div>'
                f'<div style="margin-bottom: 0.4rem;">'
                f'<span class="neo-badge {h["badge_class"]}" style="font-size: 0.7rem; padding: 0.15rem 0.45rem; margin: 0;">{h["health"]} ({h["completion_pct"]}%)</span>'
                f'</div>'
                f'<div style="font-size: 0.75rem; opacity: 0.8;">Completed {h["completed_count"]} / {h["total_days"]} days</div>'
                f'</div>'
            )
            st.markdown(h_card, unsafe_allow_html=True)


def render_weekly_summary_section(
    dates: list[date],
    tasks: list[str],
    completion_matrix: dict[str, dict[str, bool]],
) -> None:
    """Renders Weekly Summary Card with visual completion breakdown."""
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 📋 Weekly Summary")

    summary = calculate_weekly_summary(dates, tasks, completion_matrix)

    if not summary or not summary.get("has_data"):
        st.caption("No weekly data available.")
        return


    col_s1, col_s2 = st.columns([1.5, 2.5], gap="medium")

    with col_s1:
        s_card = (
            f'<div class="neo-card-yellow" style="padding: 1rem 1.25rem;">'
            f'<h4 style="margin-top: 0; margin-bottom: 0.5rem; color: #000000 !important;">⚡ THIS WEEK AT A GLANCE</h4>'
            f'<div style="font-size: 0.9rem; font-weight: 700; line-height: 1.6; color: #000000 !important;">'
            f'• <strong>Total Tasks Completed:</strong> {summary["completed_tasks"]}<br>'
            f'• <strong>Average Completion:</strong> {summary["avg_completion_pct"]}%<br>'
            f'• <strong>100% Days:</strong> {summary["fully_completed_days"]}<br>'
            f'• <strong>Best Day:</strong> {summary["best_day"]}<br>'
            f'• <strong>Weakest Day:</strong> {summary["weakest_day"]}<br>'
            f'• <strong>Most Completed Task:</strong> {html.escape(summary["most_completed_task"])}<br>'
            f'• <strong>Least Completed Task:</strong> {html.escape(summary["least_completed_task"])}'
            f'</div>'
            f'</div>'
        )
        st.markdown(s_card, unsafe_allow_html=True)

    with col_s2:
        breakdown = summary.get("daily_breakdown", [])
        if breakdown:
            b_df = pd.DataFrame([
                {"Day": d["day_name"], "Completion (%)": d["percentage"]} for d in breakdown
            ])
            b_df.set_index("Day", inplace=True)
            st.bar_chart(b_df, height=200)


def render_productivity_patterns_section(
    dates: list[date],
    tasks: list[dict],
    completion_matrix: dict[str, dict[str, bool]],
) -> None:
    """Renders Productivity Patterns Section."""
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 🧩 Productivity Patterns & Habits")

    patterns = calculate_productivity_patterns(dates, tasks, completion_matrix)

    if not patterns:
        st.caption("Insufficient historical data to detect productivity patterns yet (requires >= 3 dates).")
        return

    cols = st.columns(min(3, len(patterns)))
    for idx, p in enumerate(patterns):
        col_idx = idx % min(3, len(patterns))
        with cols[col_idx]:
            p_card = (
                f'<div class="neo-card" style="padding: 1rem; margin-bottom: 0.75rem;">'
                f'<div style="margin-bottom: 0.4rem;">'
                f'<span class="neo-badge {p["badge_class"]}" style="font-size: 0.7rem; padding: 0.2rem 0.5rem; margin: 0;">{html.escape(p["title"])}</span>'
                f'</div>'
                f'<div style="font-size: 0.9rem; font-weight: 700; line-height: 1.4;">{html.escape(p["description"])}</div>'
                f'</div>'
            )
            st.markdown(p_card, unsafe_allow_html=True)


def render_productivity_insights_section(
    dates: list[date],
    tasks: list[str],
    completion_matrix: dict[str, dict[str, bool]],
) -> None:
    """Renders deterministic Productivity Insights cards."""
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 💡 Deterministic Productivity Insights")

    insights = calculate_productivity_insights(dates, tasks, completion_matrix)

    if not insights:
        st.caption("Insufficient historical data for deep productivity insights yet.")
        return

    cols = st.columns(min(3, len(insights)))
    for idx, item in enumerate(insights):
        col_idx = idx % min(3, len(insights))
        with cols[col_idx]:
            i_card = (
                f'<div class="neo-card" style="padding: 1rem 1.25rem; margin-bottom: 0.75rem;">'
                f'<div style="margin-bottom: 0.4rem;">'
                f'<span class="neo-badge {item["badge_class"]}" style="font-size: 0.75rem; padding: 0.2rem 0.5rem; margin: 0;">{html.escape(item["title"])}</span>'
                f'</div>'
                f'<div style="font-size: 0.9rem; font-weight: 700; line-height: 1.4;">{html.escape(item["description"])}</div>'
                f'</div>'
            )
            st.markdown(i_card, unsafe_allow_html=True)


def render_productivity_chart(
    filtered_dates: list[date],
    tasks: list[str],
    completion_matrix: dict[str, dict[str, bool]],
) -> None:
    """Renders Productivity Over Time line chart."""
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 📈 Productivity Over Time")

    if not filtered_dates or not tasks:
        st.info("Not enough timeline data to render chart.")
        return

    chart_data = []
    for d in filtered_dates:
        daily = calculate_daily_completion(d, tasks, completion_matrix)
        chart_data.append(
            {
                "Date": d.strftime("%Y-%m-%d"),
                "Completion Rate (%)": daily["percentage"],
            }
        )

    chart_df = pd.DataFrame(chart_data)
    chart_df.set_index("Date", inplace=True)
    st.line_chart(chart_df, height=260)


def render_task_performance(
    filtered_dates: list[date],
    tasks: list[str],
    completion_matrix: dict[str, dict[str, bool]],
    range_type: str,
    custom_start: date | None = None,
    custom_end: date | None = None,
) -> None:
    """Renders Task Performance Breakdown sorted by completion percentage."""
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 🎯 Task Performance Breakdown")

    performance = calculate_task_performance(
        filtered_dates, tasks, completion_matrix, range_type, custom_start, custom_end
    )

    if not performance:
        st.caption("No task performance data available.")
        return

    for t_data in performance:
        t_name = html.escape(str(t_data["task"]))
        c_count = t_data["completed_count"]
        t_days = t_data["total_days"]
        pct = t_data["completion_pct"]

        if pct >= 80:
            badge_class = "neo-badge-cyan"
        elif pct >= 40:
            badge_class = "neo-badge"
        else:
            badge_class = "neo-badge-coral"

        safe_t_name = html.escape(t_name)
        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            tp_card = (
                f'<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.25rem;">'
                f'<span style="font-weight: 700; font-size: 0.95rem;">{safe_t_name}</span>'
                f'<span class="neo-badge {badge_class}" style="font-size: 0.7rem; padding: 0.15rem 0.4rem;">{pct}% DONE ({c_count}/{t_days} days)</span>'
                f'</div>'
            )
            st.markdown(tp_card, unsafe_allow_html=True)
            st.progress(pct / 100)


def render_global_reminder_summary() -> None:
    """Renders Global Reminders Summary section completely separate from task analytics."""
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 🔔 Global Reminders Summary")

    reminders = get_reminders()
    summary = calculate_global_reminder_summary(reminders)

    col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns(5, gap="small")

    with col_r1:
        r1 = (
            f'<div class="neo-card" style="padding: 0.75rem 0.5rem; text-align: center;">'
            f'<div style="font-size: 0.7rem; font-weight: 800; text-transform: uppercase;">Total</div>'
            f'<div style="font-size: 1.5rem; font-weight: 900; margin-top: 0.2rem;">{summary["total"]}</div>'
            f'</div>'
        )
        st.markdown(r1, unsafe_allow_html=True)

    with col_r2:
        r2 = (
            f'<div class="neo-card-cyan" style="padding: 0.75rem 0.5rem; text-align: center;">'
            f'<div style="font-size: 0.7rem; font-weight: 800; text-transform: uppercase; color: #000000 !important;">Active</div>'
            f'<div style="font-size: 1.5rem; font-weight: 900; margin-top: 0.2rem; color: #000000 !important;">{summary["active"]}</div>'
            f'</div>'
        )
        st.markdown(r2, unsafe_allow_html=True)

    with col_r3:
        r3 = (
            f'<div class="neo-card-yellow" style="padding: 0.75rem 0.5rem; text-align: center;">'
            f'<div style="font-size: 0.7rem; font-weight: 800; text-transform: uppercase; color: #000000 !important;">Due Today</div>'
            f'<div style="font-size: 1.5rem; font-weight: 900; margin-top: 0.2rem; color: #000000 !important;">{summary["due_today"]}</div>'
            f'</div>'
        )
        st.markdown(r3, unsafe_allow_html=True)

    with col_r4:
        r4 = (
            f'<div class="neo-card-coral" style="padding: 0.75rem 0.5rem; text-align: center;">'
            f'<div style="font-size: 0.7rem; font-weight: 800; text-transform: uppercase; color: #000000 !important;">Overdue</div>'
            f'<div style="font-size: 1.5rem; font-weight: 900; margin-top: 0.2rem; color: #000000 !important;">{summary["overdue"]}</div>'
            f'</div>'
        )
        st.markdown(r4, unsafe_allow_html=True)

    with col_r5:
        r5 = (
            f'<div class="neo-card" style="padding: 0.75rem 0.5rem; text-align: center;">'
            f'<div style="font-size: 0.7rem; font-weight: 800; text-transform: uppercase;">Completed</div>'
            f'<div style="font-size: 1.5rem; font-weight: 900; margin-top: 0.2rem;">{summary["completed"]}</div>'
            f'</div>'
        )
        st.markdown(r5, unsafe_allow_html=True)


def render_analytics() -> None:
    """Main Analytics View Entry Point."""
    active_ws = get_active_workspace()
    ws_name = active_ws.get("name", "Personal")
    dates = active_ws.get("dates") or []
    tasks = active_ws.get("tasks") or []
    completion_matrix = active_ws.get("completion") or {}


    range_type = render_analytics_header(ws_name)

    if not dates or not tasks:
        render_empty_analytics_state()
        render_global_reminder_summary()
        return

    c_start = st.session_state.get("_analytics_custom_start")
    c_end = st.session_state.get("_analytics_custom_end")

    metrics = calculate_workspace_metrics(
        dates, tasks, completion_matrix, range_type=range_type, custom_start=c_start, custom_end=c_end
    )

    render_summary_metrics(metrics)
    render_workspace_goals()
    render_period_comparison(dates, tasks, completion_matrix, range_type, custom_start=c_start, custom_end=c_end)
    render_productivity_heatmap(dates, tasks, completion_matrix)
    render_productivity_patterns_section(dates, tasks, completion_matrix)
    render_productivity_insights_section(dates, tasks, completion_matrix)
    render_task_health_section(dates, tasks, completion_matrix)
    render_weekly_summary_section(dates, tasks, completion_matrix)
    render_productivity_chart(metrics["filtered_dates"], tasks, completion_matrix)
    render_task_performance(
        metrics["filtered_dates"], tasks, completion_matrix, range_type, custom_start=c_start, custom_end=c_end
    )
    render_global_reminder_summary()
