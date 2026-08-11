"""
Goal Analytics & Progress Calculation Engine for kartavya (Phase 5).

Calculates dynamic, non-mutating goal progress from canonical workspace task data,
respecting start/end dates, excluding future dates (> today_ref), and detecting expiration.
"""

from datetime import date
from src.data.persistence import parse_date
from src.analytics.calculations import calculate_daily_completion, calculate_streaks


def calculate_goal_progress(
    goal: dict,
    dates: list[date],
    tasks: list[str],
    completion_matrix: dict[str, dict[str, bool]],
    today_ref: date | None = None,
) -> dict:
    """
    Calculates dynamic progress metrics for a single workspace goal.
    Does NOT mutate input data or store calculated progress fields.
    """
    ref = today_ref or date.today()

    g_id = str(goal.get("id", ""))
    title = str(goal.get("title", ""))
    g_type = str(goal.get("goal_type", "task_count"))
    target = float(goal.get("target_value", 10.0))

    s_date = parse_date(goal.get("start_date")) or ref
    e_date = parse_date(goal.get("end_date")) or ref
    if s_date > e_date:
        s_date, e_date = e_date, s_date

    is_expired = ref > e_date

    # Filter dates between start_date and min(end_date, today_ref)
    cutoff_end = min(e_date, ref)
    eligible_dates = [d for d in dates if isinstance(d, date) and s_date <= d <= cutoff_end]

    current_val = 0.0

    if g_type == "task_count":
        for d in eligible_dates:
            daily = calculate_daily_completion(d, tasks, completion_matrix)
            current_val += daily["completed"]

    elif g_type == "completion_pct":
        if eligible_dates:
            pcts = [calculate_daily_completion(d, tasks, completion_matrix)["percentage"] for d in eligible_dates]
            current_val = round(sum(pcts) / len(pcts), 1)
        else:
            current_val = 0.0

    elif g_type == "day_count":
        count_days = 0
        for d in eligible_dates:
            daily = calculate_daily_completion(d, tasks, completion_matrix)
            if daily["completed"] > 0:
                count_days += 1
        current_val = float(count_days)

    elif g_type == "streak":
        streaks = calculate_streaks(dates, tasks, completion_matrix, ref)
        current_val = float(streaks["current_streak"])

    # Progress percentage capped at 100%
    if target > 0:
        progress_pct = min(100, round((current_val / target) * 100))
    else:
        progress_pct = 0

    is_achieved = current_val >= target
    remaining_val = max(0.0, round(target - current_val, 1))

    days_remaining = max(0, (e_date - ref).days)
    elapsed_days = max(1, (ref - s_date).days + 1)
    current_daily_pace = round(current_val / elapsed_days, 2)
    required_pace = round(remaining_val / max(1, days_remaining), 2) if days_remaining > 0 else 0.0

    raw_status = str(goal.get("status", "active"))
    if raw_status == "archived":
        final_status = "archived"
        pace_status = "ARCHIVED"
        pace_badge_class = "neo-badge-outline"
    elif is_achieved:
        final_status = "completed"
        pace_status = "COMPLETED"
        pace_badge_class = "neo-badge-cyan"
    elif is_expired:
        final_status = "expired"
        pace_status = "EXPIRED"
        pace_badge_class = "neo-badge-coral"
    else:
        final_status = "active"
        if current_daily_pace >= required_pace or progress_pct >= 85:
            pace_status = "ON TRACK"
            pace_badge_class = "neo-badge-cyan"
        elif current_daily_pace >= 0.5 * required_pace:
            pace_status = "AT RISK"
            pace_badge_class = "neo-badge-yellow"
        else:
            pace_status = "BEHIND"
            pace_badge_class = "neo-badge-coral"

    return {
        "goal_id": g_id,
        "title": title,
        "goal_type": g_type,
        "target_value": target,
        "current_value": current_val,
        "progress_pct": progress_pct,
        "remaining_value": remaining_val,
        "start_date": s_date,
        "end_date": e_date,
        "days_remaining": days_remaining,
        "elapsed_days": elapsed_days,
        "current_daily_pace": current_daily_pace,
        "required_pace": required_pace,
        "pace_status": pace_status,
        "pace_badge_class": pace_badge_class,
        "is_expired": is_expired,
        "is_achieved": is_achieved,
        "status": final_status,
    }



def calculate_all_goals_progress(
    goals: list[dict],
    dates: list[date],
    tasks: list[str],
    completion_matrix: dict[str, dict[str, bool]],
    today_ref: date | None = None,
) -> list[dict]:
    """
    Calculates progress for a list of workspace goals.
    Returns list of goal progress dictionaries.
    """
    ref = today_ref or date.today()
    return [
        calculate_goal_progress(g, dates, tasks, completion_matrix, ref)
        for g in goals
        if isinstance(g, dict)
    ]
