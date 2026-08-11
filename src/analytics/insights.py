"""
Productivity Insights, Task Health, Period Comparison, and Recommendation Engine for kartavya (Phase 5).

Deterministic calculation functions for:
- Task Health classification (STRONG, STABLE, NEEDS ATTENTION, INACTIVE)
- Period Comparison (Current vs. Previous Equivalent Period)
- Rule-based Productivity Insights
- Smart Focus Today recommendations
- Weekly Summary calculations
"""

from datetime import date, timedelta
from src.config import (
    HEALTH_STRONG_THRESHOLD,
    HEALTH_STABLE_THRESHOLD,
    HEALTH_NEEDS_ATTENTION_THRESHOLD,
)
from src.data.persistence import parse_date
from src.analytics.calculations import (
    calculate_daily_completion,
    calculate_task_performance,
    calculate_workspace_metrics,
    filter_dates_by_range,
)


def calculate_task_health(
    dates: list[date],
    tasks: list,
    completion_matrix: dict[str, dict[str, bool]],
    today_ref: date | None = None,
) -> list[dict]:
    """
    Classifies task health based on historical completion percentage.
    Uses centralized threshold constants from src/config.py.
    """
    dates = dates or []
    tasks = tasks or []
    completion_matrix = completion_matrix or {}
    ref = today_ref or date.today()
    past_dates = [d for d in dates if isinstance(d, date) and d <= ref]
    total_days = len(past_dates)


    health_list = []
    for t in tasks:
        t_id = t["id"] if isinstance(t, dict) else str(t)
        t_name = t["name"] if isinstance(t, dict) else str(t)

        if total_days == 0:
            pct = 0
            completed_count = 0
        else:
            completed_count = sum(
                1 for d in past_dates
                if bool((completion_matrix.get(d.isoformat()) or {}).get(t_id, False))
            )

            pct = round((completed_count / total_days) * 100)

        if pct >= HEALTH_STRONG_THRESHOLD:
            health = "STRONG"
            badge_class = "neo-badge-cyan"
        elif pct >= HEALTH_STABLE_THRESHOLD:
            health = "STABLE"
            badge_class = "neo-badge"
        elif pct >= HEALTH_NEEDS_ATTENTION_THRESHOLD:
            health = "NEEDS ATTENTION"
            badge_class = "neo-badge-coral"
        else:
            health = "INACTIVE"
            badge_class = "neo-badge-outline"

        health_list.append({
            "task": t_name,
            "task_id": t_id,
            "completed_count": completed_count,
            "total_days": total_days,
            "completion_pct": pct,
            "health": health,
            "badge_class": badge_class,
        })

    health_list.sort(key=lambda x: (x["completion_pct"], x["completed_count"]), reverse=True)
    return health_list


def calculate_period_comparison(
    dates: list[date],
    tasks: list,
    completion_matrix: dict[str, dict[str, bool]],
    range_type: str = "7_days",
    custom_start: date | None = None,
    custom_end: date | None = None,
    today_ref: date | None = None,
) -> dict:
    """
    Compares metrics for current period vs. previous equivalent period of the exact same duration.
    Excludes future dates from both periods.
    """
    ref = today_ref or date.today()

    if range_type == "all_time":
        return {
            "has_comparison": False,
            "message": "All-time timeline data active — no prior period comparison available.",
        }

    if range_type == "7_days":
        curr_start = ref - timedelta(days=6)
        curr_end = ref
        prev_start = ref - timedelta(days=13)
        prev_end = ref - timedelta(days=7)
    elif range_type == "30_days":
        curr_start = ref - timedelta(days=29)
        curr_end = ref
        prev_start = ref - timedelta(days=59)
        prev_end = ref - timedelta(days=30)
    elif range_type == "custom":
        s = custom_start or ref
        e = custom_end or ref
        if s > e:
            s, e = e, s
        curr_start = s
        curr_end = e
        duration = (e - s).days + 1
        prev_start = s - timedelta(days=duration)
        prev_end = s - timedelta(days=1)
    else:
        return {"has_comparison": False, "message": "Unknown date range."}

    m_curr = calculate_workspace_metrics(
        dates, tasks, completion_matrix, range_type="custom", custom_start=curr_start, custom_end=curr_end, today_ref=ref
    )
    m_prev = calculate_workspace_metrics(
        dates, tasks, completion_matrix, range_type="custom", custom_start=prev_start, custom_end=prev_end, today_ref=ref
    )

    return {
        "has_comparison": True,
        "range_type": range_type,
        "curr_start": curr_start,
        "curr_end": curr_end,
        "prev_start": prev_start,
        "prev_end": prev_end,
        "current_completion_pct": m_curr["overall_completion_pct"],
        "prev_completion_pct": m_prev["overall_completion_pct"],
        "completion_pct_delta": m_curr["overall_completion_pct"] - m_prev["overall_completion_pct"],
        "current_completed_instances": m_curr["completed_instances"],
        "prev_completed_instances": m_prev["completed_instances"],
        "completed_instances_delta": m_curr["completed_instances"] - m_prev["completed_instances"],
        "current_avg_daily_pct": m_curr["avg_daily_completion_pct"],
        "prev_avg_daily_pct": m_prev["avg_daily_completion_pct"],
        "avg_daily_pct_delta": m_curr["avg_daily_completion_pct"] - m_prev["avg_daily_completion_pct"],
        "current_fully_completed_days": m_curr["fully_completed_days"],
        "prev_fully_completed_days": m_prev["fully_completed_days"],
        "fully_completed_days_delta": m_curr["fully_completed_days"] - m_prev["fully_completed_days"],
    }


def calculate_productivity_insights(
    dates: list[date],
    tasks: list,
    completion_matrix: dict[str, dict[str, bool]],
    today_ref: date | None = None,
) -> list[dict]:
    """
    Generates data-driven productivity insights based on actual user data.
    Does not output generic or fake motivational text.
    """
    ref = today_ref or date.today()
    past_dates = [d for d in dates if isinstance(d, date) and d <= ref]
    if len(past_dates) < 2 or not tasks:
        return []

    insights = []

    # 1. Day of week breakdown
    day_pcts = {i: [] for i in range(7)}  # 0=Monday, 6=Sunday
    for d in past_dates:
        daily = calculate_daily_completion(d, tasks, completion_matrix)
        day_pcts[d.weekday()].append(daily["percentage"])

    day_names = ["Mondays", "Tuesdays", "Wednesdays", "Thursdays", "Fridays", "Saturdays", "Sundays"]
    day_averages = {}
    for w_day, p_list in day_pcts.items():
        if p_list:
            day_averages[w_day] = round(sum(p_list) / len(p_list))

    if day_averages:
        best_w_day = max(day_averages, key=day_averages.get)
        worst_w_day = min(day_averages, key=day_averages.get)

        if day_averages[best_w_day] > 0:
            insights.append({
                "title": "STRONGEST DAY",
                "category": "day_performance",
                "description": f"You achieve your highest task completion rate ({day_averages[best_w_day]}%) on {day_names[best_w_day]}.",
                "badge_class": "neo-badge-cyan",
            })

        if worst_w_day != best_w_day and day_averages[worst_w_day] < day_averages[best_w_day]:
            insights.append({
                "title": "NEEDS ATTENTION",
                "category": "day_performance",
                "description": f"{day_names[worst_w_day]} have your lowest completion rate ({day_averages[worst_w_day]}%).",
                "badge_class": "neo-badge-coral",
            })

    # 2. Task consistency breakdown
    perf = calculate_task_performance(past_dates, tasks, completion_matrix, "all_time", today_ref=ref)
    if perf:
        top_task = perf[0]
        if top_task["completion_pct"] >= 75:
            insights.append({
                "title": "STRONG CONSISTENCY",
                "category": "task_consistency",
                "description": f"'{top_task['task']}' is your most consistent habit, completed on {top_task['completion_pct']}% of tracked days.",
                "badge_class": "neo-badge-cyan",
            })

        low_tasks = [t for t in perf if t["completion_pct"] < 40 and t["total_days"] >= 3]
        if low_tasks:
            lowest = low_tasks[-1]
            insights.append({
                "title": "REPEATEDLY MISSED",
                "category": "task_consistency",
                "description": f"'{lowest['task']}' has remained below {lowest['completion_pct']}% completion across tracked dates.",
                "badge_class": "neo-badge-coral",
            })

    # 3. Trend comparison (7-day trend)
    comp = calculate_period_comparison(dates, tasks, completion_matrix, "7_days", today_ref=ref)
    if comp.get("has_comparison"):
        delta = comp["completion_pct_delta"]
        if delta >= 10:
            insights.append({
                "title": "PRODUCTIVITY BOOST",
                "category": "trend",
                "description": f"Your completion rate improved by +{delta}% compared with the previous 7 days.",
                "badge_class": "neo-badge-cyan",
            })
        elif delta <= -10:
            insights.append({
                "title": "DECLINING MOMENTUM",
                "category": "trend",
                "description": f"Your completion rate dropped by {delta}% compared with the previous 7 days.",
                "badge_class": "neo-badge-coral",
            })

    return insights


def calculate_focus_today_recommendations(
    dates: list[date],
    tasks: list,
    completion_matrix: dict[str, dict[str, bool]],
    reminders: list[dict],
    today_ref: date | None = None,
) -> list[dict]:
    """
    Generates prioritized Focus Today recommendation items for the main dashboard.
    Priority order:
    1. Overdue reminders
    2. High-priority reminders due today/soon
    3. Unfinished tasks today
    4. Tasks with low historical completion (< 50%)
    """
    ref = today_ref or date.today()
    recommendations = []
    seen_keys = set()

    # 1. Overdue reminders
    for rem in reminders:
        if isinstance(rem, dict) and not rem.get("completed", False):
            d_val = parse_date(rem.get("deadline"))
            if isinstance(d_val, date) and d_val < ref:
                key = f"rem_{rem.get('id')}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    recommendations.append({
                        "id": key,
                        "title": rem.get("title", "Overdue Reminder"),
                        "reason": f"OVERDUE ({rem.get('priority', 'Medium')} Priority)",
                        "type": "reminder_overdue",
                        "badge_class": "neo-badge-coral",
                    })

    # 2. High-priority reminders due today
    for rem in reminders:
        if isinstance(rem, dict) and not rem.get("completed", False):
            d_val = parse_date(rem.get("deadline"))
            if isinstance(d_val, date) and d_val == ref and rem.get("priority") == "High":
                key = f"rem_{rem.get('id')}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    recommendations.append({
                        "id": key,
                        "title": rem.get("title", "Important Reminder"),
                        "reason": "DUE TODAY (High Priority)",
                        "type": "reminder_today",
                        "badge_class": "neo-badge-cyan",
                    })

    # 3. Unfinished tasks today
    today_iso = ref.isoformat()
    today_map = completion_matrix.get(today_iso) or {}

    perf = calculate_task_performance(dates, tasks, completion_matrix, "all_time", today_ref=ref)
    perf_map = {p["task"]: p["completion_pct"] for p in perf}

    for t in tasks:
        t_id = t["id"] if isinstance(t, dict) else str(t)
        t_name = t["name"] if isinstance(t, dict) else str(t)

        if not bool(today_map.get(t_id, False)):
            key = f"task_{t_id}"
            if key not in seen_keys:
                seen_keys.add(key)
                hist_pct = perf_map.get(t_name, 100)
                reason = "UNFINISHED TODAY"
                b_class = "neo-badge"
                if hist_pct < 50:
                    reason = f"LOW HISTORICAL COMPLETION ({hist_pct}%)"
                    b_class = "neo-badge-coral"

                recommendations.append({
                    "id": key,
                    "title": t_name,
                    "reason": reason,
                    "type": "task_unfinished",
                    "badge_class": b_class,
                })

    return recommendations[:5]



def calculate_weekly_summary(
    dates: list[date],
    tasks: list[str],
    completion_matrix: dict[str, dict[str, bool]],
    today_ref: date | None = None,
) -> dict:
    """
    Computes a concise weekly summary breakdown for the last 7 days up to today_ref.
    """
    dates = dates or []
    tasks = tasks or []
    completion_matrix = completion_matrix or {}
    ref = today_ref or date.today()
    dates_7 = filter_dates_by_range(dates, "7_days", today_ref=ref)

    if not dates_7 or not tasks:

        return {
            "has_data": False,
            "completed_tasks": 0,
            "avg_completion_pct": 0,
            "fully_completed_days": 0,
            "best_day": "N/A",
            "weakest_day": "N/A",
            "most_completed_task": "N/A",
            "least_completed_task": "N/A",
            "daily_breakdown": [],
        }

    daily_breakdown = []
    total_completed = 0
    day_pct_map = {}

    for d in dates_7:
        daily = calculate_daily_completion(d, tasks, completion_matrix)
        total_completed += daily["completed"]
        day_name = d.strftime("%a")
        daily_breakdown.append({
            "date": d,
            "day_name": day_name,
            "completed": daily["completed"],
            "total": daily["total"],
            "percentage": daily["percentage"],
        })
        day_pct_map[day_name] = daily["percentage"]

    avg_pct = round(sum(d["percentage"] for d in daily_breakdown) / len(daily_breakdown))
    fully_completed_count = sum(1 for d in daily_breakdown if d["percentage"] == 100)

    best_day = max(day_pct_map, key=day_pct_map.get) if day_pct_map else "N/A"
    weakest_day = min(day_pct_map, key=day_pct_map.get) if day_pct_map else "N/A"

    perf = calculate_task_performance(dates_7, tasks, completion_matrix, "custom", custom_start=dates_7[0], custom_end=dates_7[-1], today_ref=ref)
    most_completed = perf[0]["task"] if perf else "N/A"
    least_completed = perf[-1]["task"] if perf else "N/A"

    return {
        "has_data": True,
        "completed_tasks": total_completed,
        "avg_completion_pct": avg_pct,
        "fully_completed_days": fully_completed_count,
        "best_day": best_day,
        "weakest_day": weakest_day,
        "most_completed_task": most_completed,
        "least_completed_task": least_completed,
        "daily_breakdown": daily_breakdown,
    }


def calculate_productivity_patterns(

    dates: list[date],
    tasks: list[dict],
    completion_matrix: dict[str, dict[str, bool]],
    today_ref: date | None = None,
) -> list[dict]:
    """
    Detects deterministic productivity patterns when sufficient historical data exists (>= 3 dates).
    """
    ref = today_ref or date.today()
    past_dates = [d for d in dates if isinstance(d, date) and d <= ref]

    if len(past_dates) < 3 or not tasks:
        return []

    patterns = []
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # 1. Day of Week Pattern
    day_pcts = {i: [] for i in range(7)}
    for d in past_dates:
        daily = calculate_daily_completion(d, tasks, completion_matrix)
        day_pcts[d.weekday()].append(daily["percentage"])

    day_averages = {w: round(sum(p) / len(p)) for w, p in day_pcts.items() if p}
    if len(day_averages) >= 2:
        best_day = max(day_averages, key=day_averages.get)
        worst_day = min(day_averages, key=day_averages.get)
        if day_averages[best_day] > day_averages[worst_day]:
            patterns.append({
                "title": "WEEKDAY PATTERN",
                "category": "weekday",
                "description": f"Highest completion on {day_names[best_day]}s ({day_averages[best_day]}%), lowest on {day_names[worst_day]}s ({day_averages[worst_day]}%).",
                "badge_class": "neo-badge-cyan",
            })

    # 2. Habit Consistency Pattern
    perf = calculate_task_performance(past_dates, tasks, completion_matrix, "all_time", today_ref=ref)
    if perf:
        top_task = perf[0]
        if top_task["completion_pct"] >= 75:
            patterns.append({
                "title": "ANCHOR HABIT",
                "category": "habit",
                "description": f"'{top_task['task']}' is your strongest anchor habit ({top_task['completion_pct']}% completion).",
                "badge_class": "neo-badge-cyan",
            })

        bottom_tasks = [t for t in perf if t["completion_pct"] < 50]
        if bottom_tasks:
            lowest_task = bottom_tasks[-1]
            patterns.append({
                "title": "GROWTH AREA",
                "category": "habit",
                "description": f"'{lowest_task['task']}' has the lowest completion rate ({lowest_task['completion_pct']}%).",
                "badge_class": "neo-badge-coral",
            })

    # 3. Momentum & Trend Pattern
    comp = calculate_period_comparison(dates, tasks, completion_matrix, "7_days", today_ref=ref)
    if comp.get("has_comparison"):
        delta = comp["completion_pct_delta"]
        if delta >= 15:
            patterns.append({
                "title": "STRONG MOMENTUM",
                "category": "trend",
                "description": f"Productivity increased by +{delta}% over the past 7 days compared to the prior week.",
                "badge_class": "neo-badge-cyan",
            })
        elif delta <= -15:
            patterns.append({
                "title": "RECOVERY NEEDED",
                "category": "trend",
                "description": f"Productivity dipped by {delta}% over the past 7 days compared to the prior week.",
                "badge_class": "neo-badge-coral",
            })

    return patterns

