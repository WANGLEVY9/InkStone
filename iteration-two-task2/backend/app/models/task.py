from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class EvaluationTask(Base, TimestampMixin):
    __tablename__ = "evaluation_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    agent_version: Mapped[str] = mapped_column(String(64))
    dataset_id: Mapped[str] = mapped_column(String(64))
    mode: Mapped[str] = mapped_column(String(32), default="result")
    eval_mode: Mapped[str] = mapped_column(String(32), default="result")
    method: Mapped[str] = mapped_column(String(32), default="explicit")
    dimension: Mapped[str] = mapped_column(String(32), default="effectiveness")
    status: Mapped[str] = mapped_column(String(24), default="draft", index=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    judge_config: Mapped[dict] = mapped_column(JSON, default=dict)
    run_config: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics: Mapped[list] = mapped_column(JSON, default=list)
    input_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    progress: Mapped[int] = mapped_column(default=0)
    total_samples: Mapped[int] = mapped_column(default=0)
    completed_samples: Mapped[int] = mapped_column(default=0)
    failed_samples: Mapped[int] = mapped_column(default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
