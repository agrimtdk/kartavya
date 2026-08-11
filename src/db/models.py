"""
SQLAlchemy ORM Data Models for kartavya (Phase 9 Public Multi-User Architecture).

Defines relational models with explicit foreign keys, indexes, and constraints for:
- User
- Workspace
- Task
- CompletionRecord
- Reminder
- Goal
"""

from datetime import datetime, date
import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    avatar_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    workspaces = relationship("Workspace", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    completions = relationship("CompletionRecord", back_populates="user", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True, default="")
    dates_json = Column(Text, nullable=False, default="[]")
    daily_target_pct = Column(Float, nullable=False, default=80.0)
    focus_matrix_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="workspaces")
    tasks = relationship("Task", back_populates="workspace", cascade="all, delete-orphan")
    completions = relationship("CompletionRecord", back_populates="workspace", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="workspace", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(64), primary_key=True)
    workspace_id = Column(String(64), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    priority = Column(String(32), nullable=False, default="Medium")
    description = Column(Text, nullable=True, default="")
    recurrence_json = Column(Text, nullable=False, default='{"type":"none","days":[]}')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    workspace = relationship("Workspace", back_populates="tasks")
    user = relationship("User", back_populates="tasks")
    completions = relationship("CompletionRecord", back_populates="task", cascade="all, delete-orphan")


class CompletionRecord(Base):
    __tablename__ = "completion_records"

    id = Column(String(128), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(64), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    date_val = Column(Date, nullable=False, index=True)
    completed = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="completions")
    workspace = relationship("Workspace", back_populates="completions")
    task = relationship("Task", back_populates="completions")

    __table_args__ = (
        UniqueConstraint("user_id", "task_id", "date_val", name="uq_user_task_date"),
        Index("idx_comp_user_ws_date", "user_id", "workspace_id", "date_val"),
    )


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True, default="")
    deadline = Column(Date, nullable=True, index=True)
    priority = Column(String(32), nullable=False, default="Medium")
    completed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="reminders")


class Goal(Base):
    __tablename__ = "goals"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(64), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True, default="")
    target = Column(Float, nullable=False, default=100.0)
    progress = Column(Float, nullable=False, default=0.0)
    deadline = Column(Date, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="goals")
    workspace = relationship("Workspace", back_populates="goals")
