from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class EvaluationStrategy(Base, TimestampMixin):
    __tablename__ = "evaluation_strategies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    weights: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics: Mapped[list] = mapped_column(JSON, default=list)
    dimension_weights: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=None)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
