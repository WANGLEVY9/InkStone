"""bootstrap missing core tables

Revision ID: 20260508_0003
Revises: 20260507_0002
Create Date: 2026-05-08 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260508_0003"
down_revision = "20260507_0002"
branch_labels = None
depends_on = None


def _has_table(inspector, table_name: str) -> bool:
    return inspector.has_table(table_name)


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "dataset_assets"):
        op.create_table(
            "dataset_assets",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("dataset_id", sa.String(length=64), nullable=False),
            sa.Column("name", sa.String(length=160), nullable=False),
            sa.Column("filename", sa.String(length=255), nullable=False),
            sa.Column("content_type", sa.String(length=120), nullable=False, server_default="application/octet-stream"),
            sa.Column("file_path", sa.String(length=320), nullable=False),
            sa.Column("parser_summary", sa.JSON(), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_dataset_assets_dataset_id", "dataset_assets", ["dataset_id"], unique=True)
        op.create_index("ix_dataset_assets_name", "dataset_assets", ["name"], unique=False)
        inspector = sa.inspect(bind)

    if not _has_table(inspector, "evaluation_tasks"):
        op.create_table(
            "evaluation_tasks",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("agent_id", sa.Integer(), nullable=True),
            sa.Column("agent_version", sa.String(length=64), nullable=False),
            sa.Column("dataset_id", sa.String(length=64), nullable=False),
            sa.Column("mode", sa.String(length=32), nullable=False, server_default="result"),
            sa.Column("eval_mode", sa.String(length=32), nullable=False, server_default="result"),
            sa.Column("method", sa.String(length=32), nullable=False, server_default="explicit"),
            sa.Column("dimension", sa.String(length=32), nullable=False, server_default="effectiveness"),
            sa.Column("status", sa.String(length=24), nullable=False, server_default="draft"),
            sa.Column("config", sa.JSON(), nullable=True),
            sa.Column("judge_config", sa.JSON(), nullable=True),
            sa.Column("run_config", sa.JSON(), nullable=True),
            sa.Column("metrics", sa.JSON(), nullable=True),
            sa.Column("input_payload", sa.JSON(), nullable=True),
            sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_samples", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("completed_samples", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("failed_samples", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("finished_at", sa.DateTime(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_evaluation_tasks_name", "evaluation_tasks", ["name"], unique=False)
        op.create_index("ix_evaluation_tasks_status", "evaluation_tasks", ["status"], unique=False)
        op.create_index("ix_evaluation_tasks_agent_id", "evaluation_tasks", ["agent_id"], unique=False)
        inspector = sa.inspect(bind)
    else:
        if not _has_column(inspector, "evaluation_tasks", "note"):
            op.add_column("evaluation_tasks", sa.Column("note", sa.Text(), nullable=True))
        if not _has_column(inspector, "evaluation_tasks", "input_payload"):
            op.add_column(
                "evaluation_tasks",
                sa.Column("input_payload", sa.JSON(), nullable=True),
            )

    if not _has_table(inspector, "evaluation_results"):
        op.create_table(
            "evaluation_results",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("task_id", sa.Integer(), nullable=False),
            sa.Column("sample_id", sa.String(length=255), nullable=True),
            sa.Column("user_input", sa.Text(), nullable=True),
            sa.Column("agent_output", sa.Text(), nullable=True),
            sa.Column("reference_answer", sa.Text(), nullable=True),
            sa.Column("contexts", sa.JSON(), nullable=True),
            sa.Column("tool_calls", sa.JSON(), nullable=True),
            sa.Column("reasoning_trace", sa.Text(), nullable=True),
            sa.Column("metrics_scores", sa.JSON(), nullable=True),
            sa.Column("metrics_detail", sa.JSON(), nullable=True),
            sa.Column("response_time_ms", sa.Integer(), nullable=True),
            sa.Column("token_input", sa.Integer(), nullable=True),
            sa.Column("token_output", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("human_label", sa.JSON(), nullable=True),
            sa.Column("scores", sa.JSON(), nullable=True),
            sa.Column("raw_data", sa.JSON(), nullable=True),
            sa.Column("stats", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.ForeignKeyConstraint(["task_id"], ["evaluation_tasks.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_evaluation_results_task_id", "evaluation_results", ["task_id"], unique=False)
        op.create_index("ix_evaluation_results_sample_id", "evaluation_results", ["sample_id"], unique=False)
        inspector = sa.inspect(bind)
    else:
        for name in ("scores", "raw_data", "stats"):
            if not _has_column(inspector, "evaluation_results", name):
                op.add_column(
                    "evaluation_results",
                    sa.Column(name, sa.JSON(), nullable=True),
                )

    inspector = sa.inspect(bind)
    if _has_table(inspector, "evaluation_tasks"):
        if not _has_index(inspector, "evaluation_tasks", "ix_evaluation_tasks_name"):
            op.create_index("ix_evaluation_tasks_name", "evaluation_tasks", ["name"], unique=False)
        if not _has_index(inspector, "evaluation_tasks", "ix_evaluation_tasks_status"):
            op.create_index("ix_evaluation_tasks_status", "evaluation_tasks", ["status"], unique=False)
        if not _has_index(inspector, "evaluation_tasks", "ix_evaluation_tasks_agent_id"):
            op.create_index("ix_evaluation_tasks_agent_id", "evaluation_tasks", ["agent_id"], unique=False)

    if _has_table(inspector, "evaluation_results"):
        if not _has_index(inspector, "evaluation_results", "ix_evaluation_results_task_id"):
            op.create_index("ix_evaluation_results_task_id", "evaluation_results", ["task_id"], unique=False)
        if not _has_index(inspector, "evaluation_results", "ix_evaluation_results_sample_id"):
            op.create_index("ix_evaluation_results_sample_id", "evaluation_results", ["sample_id"], unique=False)


def downgrade() -> None:
    # healing migration: keep downgrade conservative
    pass
