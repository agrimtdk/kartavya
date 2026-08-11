"""
Productivity Heatmap Component for kartavya (Phase 6 / Phase 7 Polish).

Generates LeetCode / GitHub-style daily productivity activity heatmap grid
with day-of-week labels, month headers, completion tooltips, and color intensity legend.
Excludes future dates and respects task recurrence rules.
"""

from datetime import date, timedelta
import html
import streamlit as st
from src.data.task_store import is_task_applicable_on_date


def calculate_heatmap_data(
    dates: list[date],
    tasks: list[dict],
    completion_matrix: dict[str, dict[str, bool]],
    today_ref: date | None = None,
) -> list[dict]:
    """
    Computes daily completion intensity levels (0-4) for dates <= today_ref.
    Level 0: 0% completion
    Level 1: 1% - 34% completion
    Level 2: 35% - 69% completion
    Level 3: 70% - 99% completion
    Level 4: 100% completion
    """
    ref = today_ref or date.today()
    past_dates = sorted([d for d in dates if isinstance(d, date) and d <= ref])

    heatmap_items = []
    for d in past_dates:
        d_iso = d.isoformat()
        app_tasks = [t for t in tasks if is_task_applicable_on_date(t, d)]
        total = len(app_tasks)

        if total == 0:
            completed = 0
            pct = 0
            level = 0
        else:
            date_map = completion_matrix.get(d_iso, {})
            completed = sum(1 for t in app_tasks if bool(date_map.get(t["id"], False)))
            pct = round((completed / total) * 100)

            if pct == 0:
                level = 0
            elif pct < 35:
                level = 1
            elif pct < 70:
                level = 2
            elif pct < 100:
                level = 3
            else:
                level = 4

        heatmap_items.append({
            "date": d,
            "date_str": d.strftime("%b %d, %Y"),
            "completed": completed,
            "total": total,
            "pct": pct,
            "level": level,
        })

    return heatmap_items


def render_productivity_heatmap(
    dates: list[date],
    tasks: list[dict],
    completion_matrix: dict[str, dict[str, bool]],
    today_ref: date | None = None,
) -> None:
    """Render Neo-Brutalist Light Mode LeetCode / GitHub-style Productivity Heatmap."""
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 🟩 Productivity Heatmap")

    items = calculate_heatmap_data(dates, tasks, completion_matrix, today_ref=today_ref)

    if not items:
        st.caption("No timeline dates available for heatmap.")
        return

    # Summary metrics
    active_days = sum(1 for item in items if item["completed"] > 0)
    total_completed_tasks = sum(item["completed"] for item in items)

    # Color palette for Level 0 -> Level 4 (Neo-Brutalist Light Mode Greens)
    level_colors = {
        0: "#F4F0EA",  # Surface Alt Off-white
        1: "#D1F4E0",  # Mint Light
        2: "#8AF0B5",  # Mint Medium
        3: "#34D399",  # Green Vibrant
        4: "#00E676",  # Neon Lime Green
    }

    # Map dates to item dict
    item_map = {item["date"]: item for item in items}
    all_dates = sorted([item["date"] for item in items])
    min_date = all_dates[0]
    max_date = all_dates[-1]

    # Align grid start to Monday and end to Sunday
    start_monday = min_date - timedelta(days=min_date.weekday())
    end_sunday = max_date + timedelta(days=6 - max_date.weekday())

    # Build weekly columns (each column = 7 days: Mon -> Sun)
    weeks = []
    curr = start_monday
    while curr <= end_sunday:
        week_days = [curr + timedelta(days=i) for i in range(7)]
        weeks.append(week_days)
        curr += timedelta(days=7)

    # Month header row HTML & Week columns HTML
    month_headers = []
    week_cols_html = []
    prev_month = None

    for week_idx, week in enumerate(weeks):
        # Month header detection (first day of month or first week)
        first_day_of_week = week[0]
        month_str = first_day_of_week.strftime("%b")
        if prev_month != month_str or week_idx == 0:
            month_headers.append(
                f'<div style="width: 16px; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; color: var(--text); overflow: visible; white-space: nowrap;">{month_str}</div>'
            )
            prev_month = month_str
        else:
            month_headers.append('<div style="width: 16px;"></div>')

        # 7 cells for this week
        cell_html_list = []
        for day in week:
            if day in item_map:
                it = item_map[day]
                color = level_colors.get(it["level"], "#F4F0EA")
                tooltip = html.escape(f"{it['date_str']}: {it['pct']}% ({it['completed']}/{it['total']} tasks)")
                border = "2px solid #000000" if it["level"] == 4 else "1px solid #000000"
                cell_html_list.append(
                    f'<div title="{tooltip}" style="width: 16px; height: 16px; background-color: {color}; border: {border}; box-shadow: 1px 1px 0px #000000; border-radius: 2px; cursor: pointer;"></div>'
                )
            else:
                cell_html_list.append(
                    '<div style="width: 16px; height: 16px; background-color: transparent; border: 1px dashed rgba(0,0,0,0.15); border-radius: 2px;"></div>'
                )

        col_inner = "".join(cell_html_list)
        week_cols_html.append(
            f'<div style="display: flex; flex-direction: column; gap: 4px;">{col_inner}</div>'
        )

    month_row_inner = "".join(month_headers)
    week_cols_inner = "".join(week_cols_html)

    summary_banner = (
        f'<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--border); padding-bottom: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem;">'
        f'<span class="neo-badge neo-badge-coral" style="font-size: 0.8rem; padding: 0.25rem 0.55rem;">📊 SUBMISSION ACTIVITY: {active_days} ACTIVE DAYS</span>'
        f'<span style="font-size: 0.8rem; font-weight: 800; text-transform: uppercase;">TOTAL COMPLETED: {total_completed_tasks} TASKS</span>'
        f'</div>'
    )

    day_labels_column = (
        f'<div style="display: flex; flex-direction: column; justify-content: space-between; padding-top: 20px; padding-bottom: 2px; font-size: 0.65rem; font-weight: 800; opacity: 0.75; width: 26px; line-height: 1;">'
        f'<span>Mon</span>'
        f'<span>Wed</span>'
        f'<span>Fri</span>'
        f'<span>Sun</span>'
        f'</div>'
    )

    grid_section = (
        f'<div style="display: flex; gap: 8px; overflow-x: auto; padding-bottom: 0.5rem;">'
        f'{day_labels_column}'
        f'<div style="display: flex; flex-direction: column; gap: 4px;">'
        f'<div style="display: flex; gap: 4px; height: 16px;">{month_row_inner}</div>'
        f'<div style="display: flex; gap: 4px;">{week_cols_inner}</div>'
        f'</div>'
        f'</div>'
    )

    legend_block = (
        f'<div style="display: flex; align-items: center; justify-content: flex-end; gap: 6px; font-size: 0.75rem; font-weight: 800; margin-top: 0.75rem;">'
        f'<span>LESS</span>'
        f'<div style="width: 14px; height: 14px; background-color: {level_colors[0]}; border: 1px solid #000000;"></div>'
        f'<div style="width: 14px; height: 14px; background-color: {level_colors[1]}; border: 1px solid #000000;"></div>'
        f'<div style="width: 14px; height: 14px; background-color: {level_colors[2]}; border: 1px solid #000000;"></div>'
        f'<div style="width: 14px; height: 14px; background-color: {level_colors[3]}; border: 1px solid #000000;"></div>'
        f'<div style="width: 14px; height: 14px; background-color: {level_colors[4]}; border: 2px solid #000000;"></div>'
        f'<span>MORE</span>'
        f'</div>'
    )

    heatmap_card_html = f'<div class="neo-card" style="padding: 1.25rem;">{summary_banner}{grid_section}{legend_block}</div>'

    st.markdown(heatmap_card_html, unsafe_allow_html=True)
