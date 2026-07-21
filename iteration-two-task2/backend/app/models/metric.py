from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class MetricDefinition(Base, TimestampMixin):
    __tablename__ = "metric_definitions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    metric_type: Mapped[str] = mapped_column(String(32), default="explicit")
    logic_type: Mapped[str] = mapped_column(String(32), default="builtin")
    ragas_config: Mapped[dict] = mapped_column(JSON, default=dict)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
