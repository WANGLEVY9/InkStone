from sqlalchemy import ForeignKey, JSON, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class EvaluationResult(Base, TimestampMixin):
    __tablename__ = "evaluation_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("evaluation_tasks.id"), index=True)
    sample_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    user_input: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    contexts: Mapped[dict] = mapped_column(JSON, default=dict)
    tool_calls: Mapped[dict] = mapped_column(JSON, default=dict)
    reasoning_trace: Mapped[str | None] = mapped_column(Text, nullable=True)
    metrics_scores: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics_detail: Mapped[dict] = mapped_column(JSON, default=dict)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_input: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_output: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    human_label: Mapped[dict] = mapped_column(JSON, default=dict)
    scores: Mapped[dict] = mapped_column(JSON, default=dict)
    raw_data: Mapped[dict] = mapped_column(JSON, default=dict)
    stats: Mapped[dict] = mapped_column(JSON, default=dict)
