"""
Productivity Analytics & Insights Calculation Engine for kartavya (Phase 4).

Provides pure, deterministic, non-mutating calculation functions for workspace productivity metrics,
daily completion timelines, task performance breakdowns, streak calculations, and global reminder summaries.
Operates on canonical workspace and task store data without persisting calculated fields.
"""

from datetime import date, datetime, timedelta
import re


def parse_date_obj(val: date | datetime | str | tuple | list | None) -> date | None:
    """Safely converts various date formats into a datetime.date object."""
    if val is None or val == "":
        return None

    if isinstance(val, (tuple, list)):
        if len(val) > 0:
            return parse_date_obj(val[0])
        return None

    if isinstance(val, datetime):
        return val.date()

    if isinstance(val, date):
        return val

    if isinstance(val, str):
        val_str = val.strip()
        if not val_str:
            return None
        try:
            return date.fromisoformat(val_str)
        except (ValueError, TypeError):
            pass

        iso_match = re.search(r'(\d{4}-\d{2}-\d{2})', val_str)
        if iso_match:
            try:
                return date.fromisoformat(iso_match.group(1))
            except (ValueError, TypeError):
                pass

        repr_match = re.search(r'datetime\.date\((\d{4}),\s*(\d{1,2}),\s*(\d{1,2})\)', val_str)
        if repr_match:
            try:
                return date(int(repr_match.group(1)), int(repr_match.group(2)), int(repr_match.group(3)))
            except (ValueError, TypeError):
                pass

    return None


def filter_dates_by_range(
    dates: list[date],
    range_type: str = "all_time",
    custom_start: date | None = None,
    custom_end: date | None = None,
    today_ref: date | None = None,
) -> list[date]:
    """
    Filters a list of timeline dates according to date range filter settings.
    Does NOT mutate input list or underlying data.
    """
    if not dates:
        return []

    sorted_dates = sorted([d for d in dates if isinstance(d, date)])
    if not sorted_dates:
        return []

    ref = today_ref or date.today()

    if range_type == "7_days":
        start_cutoff = ref - timedelta(days=6)
        return [d for d in sorted_dates if start_cutoff <= d <= ref]
    elif range_type == "30_days":
        start_cutoff = ref - timedelta(days=29)
        return [d for d in sorted_dates if start_cutoff <= d <= ref]
    elif range_type == "custom":
        start = custom_start or sorted_dates[0]
        end = custom_end or sorted_dates[-1]
        if start > end:
            start, end = end, start
        return [d for d in sorted_dates if start <= d <= end]
    else:  # "all_time"
        return sorted_dates


def calculate_daily_completion(
    date_obj: date,
    tasks: list,
    completion_matrix: dict[str, dict[str, bool]],
) -> dict:
    """
    Calculates completed count, total applicable tasks, and completion percentage for a specific date.
    Excludes non-applicable recurring tasks from the total denominator.
    Returns dict: {'completed': int, 'total': int, 'percentage': int}.
    """
    from src.data.task_store import is_task_applicable_on_date

    app_tasks = []
    for t in tasks:
        t_obj = t if isinstance(t, dict) else {"id": str(t), "name": str(t)}
        if is_task_applicable_on_date(t_obj, date_obj):
            app_tasks.append(t_obj)

    total = len(app_tasks)
    if total == 0:
        return {"completed": 0, "total": 0, "percentage": 0}

    d_iso = date_obj.isoformat()
    day_map = completion_matrix.get(d_iso) or {}
    completed = sum(1 for t in app_tasks if bool(day_map.get(t["id"], False)))

    pct = round((completed / total) * 100)
    return {"completed": completed, "total": total, "percentage": pct}


def calculate_streaks(
    dates: list[date],
    tasks: list,
    completion_matrix: dict[str, dict[str, bool]],
    today_ref: date | None = None,
) -> dict[str, int]:
    """
    Calculates current productivity streak and best (historical max) productivity streak.
    Streak Day Criteria: 100% of applicable tasks completed on a day with total_tasks > 0.
    Future dates (> today_ref) never contribute to streaks.
    Current streak = consecutive successful days up to today or yesterday.
    Returns dict: {'current_streak': int, 'best_streak': int}.
    """
    if not dates or not tasks:
        return {"current_streak": 0, "best_streak": 0}

    ref = today_ref or date.today()
    eligible_dates = sorted([d for d in dates if isinstance(d, date) and d <= ref])
    if not eligible_dates:
        return {"current_streak": 0, "best_streak": 0}

    date_success = {}
    for d in eligible_dates:
        daily = calculate_daily_completion(d, tasks, completion_matrix)
        date_success[d] = (daily["total"] > 0 and daily["percentage"] == 100)

    best_streak = 0
    curr_run = 0
    prev_date = None

    for d in eligible_dates:
        if date_success[d]:
            if prev_date is not None and d == prev_date + timedelta(days=1):
                curr_run += 1
            else:
                curr_run = 1
            if curr_run > best_streak:
                best_streak = curr_run
        else:
            curr_run = 0
        prev_date = d

    current_streak = 0
    anchor = None
    if ref in date_success and date_success[ref]:
        anchor = ref
    elif (ref - timedelta(days=1)) in date_success and date_success[ref - timedelta(days=1)]:
        anchor = ref - timedelta(days=1)

    if anchor is not None:
        curr_d = anchor
        while curr_d in date_success and date_success[curr_d]:
            current_streak += 1
            curr_d = curr_d - timedelta(days=1)

    return {"current_streak": current_streak, "best_streak": best_streak}


def calculate_workspace_metrics(
    dates: list[date],
    tasks: list,
    completion_matrix: dict[str, dict[str, bool]],
    range_type: str = "all_time",
    custom_start: date | None = None,
    custom_end: date | None = None,
    today_ref: date | None = None,
) -> dict:
    """
    Computes comprehensive productivity metrics for a workspace over the selected date range.
    Does not mutate underlying state.
    """
    ref = today_ref or date.today()
    filtered_dates = filter_dates_by_range(dates, range_type, custom_start, custom_end, ref)
    total_tasks = len(tasks)

    from src.data.task_store import is_task_applicable_on_date
    total_instances = 0
    for d in filtered_dates:
        total_instances += sum(1 for t in tasks if is_task_applicable_on_date(t if isinstance(t, dict) else {"id": str(t), "name": str(t)}, d))

    if total_instances == 0:
        streaks = calculate_streaks(dates, tasks, completion_matrix, ref)
        return {
            "range_type": range_type,
            "filtered_dates": [],
            "overall_completion_pct": 0,
            "completed_instances": 0,
            "total_instances": 0,
            "total_tasks": total_tasks,
            "fully_completed_days": 0,
            "partially_completed_days": 0,
            "zero_completion_days": 0,
            "avg_daily_completion_pct": 0,
            "current_streak": streaks["current_streak"],
            "best_streak": streaks["best_streak"],
            "completed_last_7_days": 0,
            "completed_last_30_days": 0,
        }

    completed_instances = 0
    fully_completed_days = 0
    partially_completed_days = 0
    zero_completion_days = 0
    daily_percentages = []

    for d in filtered_dates:
        daily = calculate_daily_completion(d, tasks, completion_matrix)
        c_count = daily["completed"]
        pct = daily["percentage"]
        completed_instances += c_count
        daily_percentages.append(pct)

        if pct == 100:
            fully_completed_days += 1
        elif pct > 0:
            partially_completed_days += 1
        else:
            zero_completion_days += 1

    overall_pct = round((completed_instances / total_instances) * 100) if total_instances > 0 else 0
    avg_daily_pct = round(sum(daily_percentages) / len(daily_percentages)) if daily_percentages else 0

    streaks = calculate_streaks(dates, tasks, completion_matrix, ref)

    dates_7 = filter_dates_by_range(dates, "7_days", today_ref=ref)
    completed_7 = sum(calculate_daily_completion(d, tasks, completion_matrix)["completed"] for d in dates_7)

    dates_30 = filter_dates_by_range(dates, "30_days", today_ref=ref)
    completed_30 = sum(calculate_daily_completion(d, tasks, completion_matrix)["completed"] for d in dates_30)

    return {
        "range_type": range_type,
        "filtered_dates": filtered_dates,
        "overall_completion_pct": overall_pct,
        "completed_instances": completed_instances,
        "total_instances": total_instances,
        "total_tasks": total_tasks,
        "fully_completed_days": fully_completed_days,
        "partially_completed_days": partially_completed_days,
        "zero_completion_days": zero_completion_days,
        "avg_daily_completion_pct": avg_daily_pct,
        "current_streak": streaks["current_streak"],
        "best_streak": streaks["best_streak"],
        "completed_last_7_days": completed_7,
        "completed_last_30_days": completed_30,
    }


def calculate_task_performance(
    dates: list[date],
    tasks: list,
    completion_matrix: dict[str, dict[str, bool]],
    range_type: str = "all_time",
    custom_start: date | None = None,
    custom_end: date | None = None,
    today_ref: date | None = None,
) -> list[dict]:
    """
    Calculates task-by-task performance breakdown sorted by completion percentage descending.
    Returns list of dicts: [{'task': str, 'task_id': str, 'completed_count': int, 'total_days': int, 'completion_pct': int}]
    """
    from src.data.task_store import is_task_applicable_on_date

    ref = today_ref or date.today()
    filtered_dates = filter_dates_by_range(dates, range_type, custom_start, custom_end, ref)

    performance = []
    for t in tasks:
        t_obj = t if isinstance(t, dict) else {"id": str(t), "name": str(t)}
        t_id = t_obj["id"]
        t_name = t_obj["name"]

        app_dates = [d for d in filtered_dates if is_task_applicable_on_date(t_obj, d)]
        total_days = len(app_dates)

        if total_days == 0:
            pct = 0
            completed_count = 0
        else:
            completed_count = sum(
                1 for d in app_dates
                if bool((completion_matrix.get(d.isoformat()) or {}).get(t_id, False))
            )
            pct = round((completed_count / total_days) * 100)

        performance.append(
            {
                "task": t_name,
                "task_id": t_id,
                "completed_count": completed_count,
                "total_days": total_days,
                "completion_pct": pct,
            }
        )

    performance.sort(key=lambda x: (x["completion_pct"], x["completed_count"]), reverse=True)
    return performance



def calculate_recent_insights(
    dates: list[date],
    tasks: list[str],
    completion_matrix: dict[str, dict[str, bool]],
    today_ref: date | None = None,
) -> dict:
    """
    Calculates compact recent activity & productivity insights.
    Returns dict containing recent completed tasks, most recent 100% completed day,
    recent day completion %, current streak, and 7-day average completion %.
    """
    ref = today_ref or date.today()
    sorted_dates = sorted([d for d in dates if isinstance(d, date)])
    past_or_today_dates = [d for d in sorted_dates if d <= ref]

    most_recent_day = past_or_today_dates[-1] if past_or_today_dates else None
    recent_completion_pct = 0
    recent_completed_tasks = []

    if most_recent_day:
        daily = calculate_daily_completion(most_recent_day, tasks, completion_matrix)
        recent_completion_pct = daily["percentage"]
        d_iso = most_recent_day.isoformat()
        date_map = completion_matrix.get(d_iso) or {}
        recent_completed_tasks = [t for t in tasks if bool(date_map.get(t["id"] if isinstance(t, dict) else str(t), False))]


    # Most recent 100% completed day
    most_recent_100_day = None
    for d in reversed(past_or_today_dates):
        if calculate_daily_completion(d, tasks, completion_matrix)["percentage"] == 100 and len(tasks) > 0:
            most_recent_100_day = d
            break

    # 7-day average
    dates_7 = filter_dates_by_range(dates, "7_days", today_ref=ref)
    pcts_7 = [calculate_daily_completion(d, tasks, completion_matrix)["percentage"] for d in dates_7]
    avg_7_day = round(sum(pcts_7) / len(pcts_7)) if pcts_7 else 0

    streaks = calculate_streaks(dates, tasks, completion_matrix, ref)

    return {
        "most_recent_day": most_recent_day,
        "recent_completion_pct": recent_completion_pct,
        "recent_completed_tasks": recent_completed_tasks,
        "most_recent_100_day": most_recent_100_day,
        "current_streak": streaks["current_streak"],
        "avg_7_day_pct": avg_7_day,
    }


def calculate_global_reminder_summary(reminders: list[dict], today_ref: date | None = None) -> dict:
    """
    Computes global reminder summary completely isolated from workspace task analytics.
    Returns dict: {'total': int, 'active': int, 'completed': int, 'overdue': int, 'due_today': int, 'upcoming': int}.
    """
    ref = today_ref or date.today()

    total = len(reminders)
    active = 0
    completed = 0
    overdue = 0
    due_today = 0
    upcoming = 0

    for rem in reminders:
        if not isinstance(rem, dict):
            continue

        is_completed = bool(rem.get("completed", False))
        if is_completed:
            completed += 1
        else:
            active += 1
            d_val = parse_date_obj(rem.get("deadline"))
            if isinstance(d_val, date):
                diff = (d_val - ref).days
                if diff < 0:
                    overdue += 1
                elif diff == 0:
                    due_today += 1
                else:
                    upcoming += 1

    return {
        "total": total,
        "active": active,
        "completed": completed,
        "overdue": overdue,
        "due_today": due_today,
        "upcoming": upcoming,
    }
