"""
Database Store Data Access Layer for kartavya (Phase 9 Public Multi-User Architecture).

Enforces strict user isolation (`WHERE user_id = :current_user_id`) across all CRUD operations.
No database query ever executes without authenticated user ownership verification.
"""

import json
from datetime import date, datetime, timedelta
import uuid
from typing import Any
from src.db.connection import get_db_session, init_db
from src.db.models import User, Workspace, Task, CompletionRecord, Reminder, Goal



def get_or_create_user(email: str, display_name: str, avatar_url: str | None = None) -> dict:
    """Retrieves existing user by email or creates a new User record."""
    clean_email = email.strip().lower()
    with get_db_session() as session:
        user = session.query(User).filter(User.email == clean_email).first()
        if not user:
            user = User(
                id=str(uuid.uuid4()),
                email=clean_email,
                display_name=display_name.strip() or clean_email.split("@")[0],
                avatar_url=avatar_url,
            )
            session.add(user)
            session.flush()

            # Create default 14-day 'Personal' workspace for new user
            today = date.today()
            initial_dates = [(today + timedelta(days=i)).isoformat() for i in range(-7, 7)]
            
            ws_personal = Workspace(
                id=f"ws_{uuid.uuid4().hex[:8]}",
                user_id=user.id,
                name="Personal",
                description="My personal productivity workspace.",
                dates_json=json.dumps(initial_dates),
                daily_target_pct=80.0,
                focus_matrix_json=json.dumps({}),
            )
            session.add(ws_personal)
            session.flush()

            # Add default starter tasks
            t_dsa = Task(
                id=f"task_{ws_personal.id}_dsa",
                workspace_id=ws_personal.id,
                user_id=user.id,
                name="DSA",
                priority="Medium",
                description="",
                recurrence_json=json.dumps({"type": "none", "days": []}),
            )
            t_proj = Task(
                id=f"task_{ws_personal.id}_project",
                workspace_id=ws_personal.id,
                user_id=user.id,
                name="Project",
                priority="Medium",
                description="",
                recurrence_json=json.dumps({"type": "none", "days": []}),
            )
            t_gym = Task(
                id=f"task_{ws_personal.id}_gym",
                workspace_id=ws_personal.id,
                user_id=user.id,
                name="Gym",
                priority="Medium",
                description="",
                recurrence_json=json.dumps({"type": "none", "days": []}),
            )
            session.add_all([t_dsa, t_proj, t_gym])
            session.commit()

        return {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }


# --- WORKSPACE CRUD (User Scoped) ---

def get_user_workspaces(user_id: str) -> list[dict]:
    """Retrieves all workspaces belonging to the authenticated user."""
    with get_db_session() as session:
        workspaces = (
            session.query(Workspace)
            .filter(Workspace.user_id == user_id)
            .order_by(Workspace.created_at.asc())
            .all()
        )
        res = []
        for ws in workspaces:
            tasks = (
                session.query(Task)
                .filter(Task.workspace_id == ws.id, Task.user_id == user_id)
                .order_by(Task.created_at.asc())
                .all()
            )
            t_list = [
                {
                    "id": t.id,
                    "name": t.name,
                    "priority": t.priority,
                    "description": t.description or "",
                    "recurrence": json.loads(t.recurrence_json) if t.recurrence_json else {"type": "none", "days": []},
                }
                for t in tasks
            ]

            # Collect completion records for this workspace
            comps = (
                session.query(CompletionRecord)
                .filter(CompletionRecord.workspace_id == ws.id, CompletionRecord.user_id == user_id)
                .all()
            )
            comp_map = {}
            for c in comps:
                d_str = c.date_val.isoformat()
                if d_str not in comp_map:
                    comp_map[d_str] = {}
                comp_map[d_str][c.task_id] = c.completed

            # Parse dates array
            dates_arr = json.loads(ws.dates_json) if ws.dates_json else []

            res.append(
                {
                    "id": ws.id,
                    "name": ws.name,
                    "description": ws.description or "",
                    "dates": dates_arr,
                    "tasks": t_list,
                    "completion": comp_map,
                    "daily_target_pct": ws.daily_target_pct,
                    "focus_matrix": json.loads(ws.focus_matrix_json) if ws.focus_matrix_json else {},
                }
            )
        return res


def get_workspace(user_id: str, workspace_id: str) -> dict | None:
    """Retrieves a single workspace by ID if it belongs to user_id."""
    workspaces = get_user_workspaces(user_id)
    for ws in workspaces:
        if ws["id"] == workspace_id:
            return ws
    return None


def create_workspace(user_id: str, name: str, description: str = "", daily_target_pct: float = 80.0) -> dict:
    """Creates a new workspace belonging to user_id."""
    with get_db_session() as session:
        count = session.query(Workspace).filter(Workspace.user_id == user_id).count()
        if count >= 10:
            raise ValueError("Maximum limit of 10 workspaces reached.")

        today = date.today()
        initial_dates = [(today + timedelta(days=i)).isoformat() for i in range(-7, 7)]
        ws_id = f"ws_{uuid.uuid4().hex[:8]}"

        ws = Workspace(
            id=ws_id,
            user_id=user_id,
            name=name.strip(),
            description=description.strip(),
            dates_json=json.dumps(initial_dates),
            daily_target_pct=float(daily_target_pct),
            focus_matrix_json=json.dumps({}),
        )
        session.add(ws)
        session.commit()
        return get_workspace(user_id, ws_id)


def update_workspace(user_id: str, workspace_id: str, updates: dict[str, Any]) -> dict | None:
    """Updates fields of a workspace belonging to user_id."""
    with get_db_session() as session:
        ws = session.query(Workspace).filter(Workspace.id == workspace_id, Workspace.user_id == user_id).first()
        if not ws:
            return None

        if "name" in updates:
            ws.name = str(updates["name"]).strip()
        if "description" in updates:
            ws.description = str(updates["description"]).strip()
        if "dates" in updates:
            # Normalize date objects to ISO strings
            raw_dates = updates["dates"]
            norm_dates = [d.isoformat() if isinstance(d, date) else str(d) for d in raw_dates]
            ws.dates_json = json.dumps(sorted(list(set(norm_dates))))
        if "daily_target_pct" in updates:
            ws.daily_target_pct = float(updates["daily_target_pct"])
        if "focus_matrix" in updates:
            ws.focus_matrix_json = json.dumps(updates["focus_matrix"])

        session.commit()
        return get_workspace(user_id, workspace_id)


def delete_workspace(user_id: str, workspace_id: str) -> bool:
    """Deletes a workspace belonging to user_id."""
    with get_db_session() as session:
        count = session.query(Workspace).filter(Workspace.user_id == user_id).count()
        if count <= 1:
            raise ValueError("Minimum 1 workspace required.")

        ws = session.query(Workspace).filter(Workspace.id == workspace_id, Workspace.user_id == user_id).first()
        if not ws:
            return False

        session.delete(ws)
        session.commit()
        return True


# --- TASK & COMPLETION CRUD (User Scoped) ---

def create_task(
    user_id: str,
    workspace_id: str,
    name: str,
    priority: str = "Medium",
    description: str = "",
    recurrence: dict | None = None,
) -> dict:
    """Creates a task inside a workspace belonging to user_id."""
    with get_db_session() as session:
        ws = session.query(Workspace).filter(Workspace.id == workspace_id, Workspace.user_id == user_id).first()
        if not ws:
            raise ValueError("Workspace not found or unauthorized.")

        rec_obj = recurrence if isinstance(recurrence, dict) else {"type": "none", "days": []}
        t_id = f"task_{workspace_id}_{uuid.uuid4().hex[:6]}"

        t = Task(
            id=t_id,
            workspace_id=workspace_id,
            user_id=user_id,
            name=name.strip(),
            priority=priority,
            description=description.strip(),
            recurrence_json=json.dumps(rec_obj),
        )
        session.add(t)
        session.commit()
        return {
            "id": t.id,
            "name": t.name,
            "priority": t.priority,
            "description": t.description,
            "recurrence": rec_obj,
        }


def update_task(user_id: str, workspace_id: str, task_id: str, updates: dict[str, Any]) -> dict | None:
    """Updates a task belonging to user_id."""
    with get_db_session() as session:
        t = session.query(Task).filter(Task.id == task_id, Task.workspace_id == workspace_id, Task.user_id == user_id).first()
        if not t:
            return None

        if "name" in updates:
            t.name = str(updates["name"]).strip()
        if "priority" in updates:
            t.priority = str(updates["priority"])
        if "description" in updates:
            t.description = str(updates["description"]).strip()
        if "recurrence" in updates:
            rec = updates["recurrence"]
            t.recurrence_json = json.dumps(rec if isinstance(rec, dict) else {"type": "none", "days": []})

        session.commit()
        return {
            "id": t.id,
            "name": t.name,
            "priority": t.priority,
            "description": t.description,
            "recurrence": json.loads(t.recurrence_json),
        }


def delete_task(user_id: str, workspace_id: str, task_id: str) -> bool:
    """Deletes a task belonging to user_id."""
    with get_db_session() as session:
        t = session.query(Task).filter(Task.id == task_id, Task.workspace_id == workspace_id, Task.user_id == user_id).first()
        if not t:
            return False

        session.delete(t)
        session.commit()
        return True


def set_completion(
    user_id: str,
    workspace_id: str,
    task_id: str,
    date_val: date,
    completed: bool,
    today_ref: date | None = None,
) -> bool:
    """
    Sets completion status for a task on a date.
    Enforces future date read-only restriction (date_val > today_ref returns False).
    """
    ref_today = today_ref or date.today()
    if date_val > ref_today:
        return False

    with get_db_session() as session:
        # Verify task ownership
        t = session.query(Task).filter(Task.id == task_id, Task.workspace_id == workspace_id, Task.user_id == user_id).first()
        if not t:
            return False

        rec_id = f"comp_{user_id}_{task_id}_{date_val.isoformat()}"
        rec = session.query(CompletionRecord).filter(CompletionRecord.id == rec_id).first()

        if not rec:
            rec = CompletionRecord(
                id=rec_id,
                user_id=user_id,
                workspace_id=workspace_id,
                task_id=task_id,
                date_val=date_val,
                completed=completed,
            )
            session.add(rec)
        else:
            rec.completed = completed

        session.commit()
        return True


# --- REMINDERS CRUD (User Scoped) ---

def get_user_reminders(user_id: str) -> list[dict]:
    """Retrieves all reminders belonging to user_id."""
    with get_db_session() as session:
        reminders = (
            session.query(Reminder)
            .filter(Reminder.user_id == user_id)
            .order_by(Reminder.deadline.asc().nulls_last())
            .all()
        )
        return [
            {
                "id": r.id,
                "title": r.title,
                "description": r.description or "",
                "deadline": r.deadline.isoformat() if r.deadline else None,
                "priority": r.priority,
                "completed": r.completed,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reminders
        ]


def create_reminder(
    user_id: str,
    title: str,
    description: str = "",
    deadline: date | str | None = None,
    priority: str = "Medium",
) -> dict:
    """Creates a new reminder for user_id."""
    with get_db_session() as session:
        r_id = f"rem_{uuid.uuid4().hex[:8]}"

        d_val = None
        if isinstance(deadline, date):
            d_val = deadline
        elif isinstance(deadline, str) and deadline.strip():
            d_val = date.fromisoformat(deadline.strip())

        rem = Reminder(
            id=r_id,
            user_id=user_id,
            title=title.strip(),
            description=description.strip(),
            deadline=d_val,
            priority=priority,
            completed=False,
        )
        session.add(rem)
        session.commit()
        return {
            "id": rem.id,
            "title": rem.title,
            "description": rem.description,
            "deadline": rem.deadline.isoformat() if rem.deadline else None,
            "priority": rem.priority,
            "completed": rem.completed,
        }


def update_reminder(user_id: str, reminder_id: str, updates: dict[str, Any]) -> dict | None:
    """Updates a reminder belonging to user_id."""
    with get_db_session() as session:
        rem = session.query(Reminder).filter(Reminder.id == reminder_id, Reminder.user_id == user_id).first()
        if not rem:
            return None

        if "title" in updates:
            rem.title = str(updates["title"]).strip()
        if "description" in updates:
            rem.description = str(updates["description"]).strip()
        if "deadline" in updates:
            d = updates["deadline"]
            if isinstance(d, date):
                rem.deadline = d
            elif isinstance(d, str) and d.strip():
                rem.deadline = date.fromisoformat(d.strip())
            else:
                rem.deadline = None
        if "priority" in updates:
            rem.priority = str(updates["priority"])
        if "completed" in updates:
            rem.completed = bool(updates["completed"])

        session.commit()
        return {
            "id": rem.id,
            "title": rem.title,
            "description": rem.description,
            "deadline": rem.deadline.isoformat() if rem.deadline else None,
            "priority": rem.priority,
            "completed": rem.completed,
        }


def delete_reminder(user_id: str, reminder_id: str) -> bool:
    """Deletes a reminder belonging to user_id."""
    with get_db_session() as session:
        rem = session.query(Reminder).filter(Reminder.id == reminder_id, Reminder.user_id == user_id).first()
        if not rem:
            return False

        session.delete(rem)
        session.commit()
        return True


# --- GOALS CRUD (User Scoped) ---

def get_user_goals(user_id: str, workspace_id: str | None = None) -> list[dict]:
    """Retrieves all goals belonging to user_id (optionally filtered by workspace_id)."""
    with get_db_session() as session:
        query = session.query(Goal).filter(Goal.user_id == user_id)
        if workspace_id:
            query = query.filter(Goal.workspace_id == workspace_id)

        goals = query.order_by(Goal.created_at.desc()).all()
        return [
            {
                "id": g.id,
                "workspace_id": g.workspace_id,
                "title": g.title,
                "description": g.description or "",
                "target": g.target,
                "progress": g.progress,
                "deadline": g.deadline.isoformat() if g.deadline else None,
                "created_at": g.created_at.isoformat() if g.created_at else None,
            }
            for g in goals
        ]


def create_goal(
    user_id: str,
    workspace_id: str,
    title: str,
    description: str = "",
    target: float = 100.0,
    progress: float = 0.0,
    deadline: date | str | None = None,
) -> dict:
    """Creates a goal belonging to user_id."""
    with get_db_session() as session:
        g_id = f"goal_{uuid.uuid4().hex[:8]}"

        d_val = None
        if isinstance(deadline, date):
            d_val = deadline
        elif isinstance(deadline, str) and deadline.strip():
            d_val = date.fromisoformat(deadline.strip())

        g = Goal(
            id=g_id,
            user_id=user_id,
            workspace_id=workspace_id,
            title=title.strip(),
            description=description.strip(),
            target=float(target),
            progress=float(progress),
            deadline=d_val,
        )
        session.add(g)
        session.commit()
        return {
            "id": g.id,
            "workspace_id": g.workspace_id,
            "title": g.title,
            "description": g.description,
            "target": g.target,
            "progress": g.progress,
            "deadline": g.deadline.isoformat() if g.deadline else None,
        }


def update_goal(user_id: str, workspace_id: str, goal_id: str, updates: dict[str, Any]) -> dict | None:
    """Updates a goal belonging to user_id."""
    with get_db_session() as session:
        g = session.query(Goal).filter(Goal.id == goal_id, Goal.workspace_id == workspace_id, Goal.user_id == user_id).first()
        if not g:
            return None

        if "title" in updates:
            g.title = str(updates["title"]).strip()
        if "description" in updates:
            g.description = str(updates["description"]).strip()
        if "target" in updates:
            g.target = float(updates["target"])
        if "progress" in updates:
            g.progress = float(updates["progress"])
        if "deadline" in updates:
            d = updates["deadline"]
            if isinstance(d, date):
                g.deadline = d
            elif isinstance(d, str) and d.strip():
                g.deadline = date.fromisoformat(d.strip())
            else:
                g.deadline = None

        session.commit()
        return {
            "id": g.id,
            "workspace_id": g.workspace_id,
            "title": g.title,
            "description": g.description,
            "target": g.target,
            "progress": g.progress,
            "deadline": g.deadline.isoformat() if g.deadline else None,
        }


def delete_goal(user_id: str, workspace_id: str, goal_id: str) -> bool:
    """Deletes a goal belonging to user_id."""
    with get_db_session() as session:
        g = session.query(Goal).filter(Goal.id == goal_id, Goal.workspace_id == workspace_id, Goal.user_id == user_id).first()
        if not g:
            return False

        session.delete(g)
        session.commit()
        return True
