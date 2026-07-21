from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class MetricTemplate(Base, TimestampMixin):
    __tablename__ = "metric_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    template_type: Mapped[str] = mapped_column(String(30), nullable=False, default="llm_judge")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    webhook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    score_range: Mapped[dict] = mapped_column(JSON, default=lambda: {"min": 0, "max": 1})
    is_builtin: Mapped[bool] = mapped_column(default=False)
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
