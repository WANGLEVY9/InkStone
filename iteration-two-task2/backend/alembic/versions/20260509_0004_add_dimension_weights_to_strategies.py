"""add dimension_weights to evaluation_strategies

Revision ID: 20260509_0004
Revises: 20260508_0003
Create Date: 2026-05-09

"""
from typing import Any

import sqlalchemy as sa
from alembic import op

revision = "20260509_0004"
down_revision = "20260508_0003"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "evaluation_strategies",
        sa.Column("dimension_weights", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("evaluation_strategies", "dimension_weights")
