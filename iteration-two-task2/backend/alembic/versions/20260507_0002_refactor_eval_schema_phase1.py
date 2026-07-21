"""phase1 eval schema refactor

Revision ID: 20260507_0002
Revises: 20260411_0001
Create Date: 2026-05-07 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260507_0002"
down_revision = "20260411_0001"
branch_labels = None
depends_on = None


def _has_table(inspector, table_name: str) -> bool:
    return inspector.has_table(table_name)


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table_name))


def _create_evaluation_tasks_table() -> None:
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


def _create_evaluation_results_table() -> None:
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


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    op.create_table(
        "agents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("endpoint", sa.String(length=500), nullable=False),
        sa.Column("auth_type", sa.String(length=50), nullable=False),
        sa.Column("auth_config", sa.JSON(), nullable=False),
        sa.Column("timeout_ms", sa.Integer(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agents_name", "agents", ["name"], unique=False)

    op.create_table(
        "agent_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("config_snap", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_versions_agent_id", "agent_versions", ["agent_id"], unique=False)

    op.create_table(
        "metric_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("template_type", sa.String(length=30), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("prompt_template", sa.Text(), nullable=True),
        sa.Column("webhook_url", sa.String(length=500), nullable=True),
        sa.Column("score_range", sa.JSON(), nullable=False),
        sa.Column("is_builtin", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_metric_templates_name", "metric_templates", ["name"], unique=False)

    if not _has_table(inspector, "evaluation_tasks"):
        _create_evaluation_tasks_table()
    else:
        with op.batch_alter_table("evaluation_tasks") as batch_op:
            if not _has_column(inspector, "evaluation_tasks", "description"):
                batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
            if not _has_column(inspector, "evaluation_tasks", "agent_id"):
                batch_op.add_column(sa.Column("agent_id", sa.Integer(), nullable=True))
            if not _has_column(inspector, "evaluation_tasks", "eval_mode"):
                batch_op.add_column(sa.Column("eval_mode", sa.String(length=32), nullable=False, server_default="result"))
            if not _has_column(inspector, "evaluation_tasks", "judge_config"):
                batch_op.add_column(sa.Column("judge_config", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
            if not _has_column(inspector, "evaluation_tasks", "run_config"):
                batch_op.add_column(sa.Column("run_config", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
            if not _has_column(inspector, "evaluation_tasks", "metrics"):
                batch_op.add_column(sa.Column("metrics", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
            if not _has_column(inspector, "evaluation_tasks", "progress"):
                batch_op.add_column(sa.Column("progress", sa.Integer(), nullable=False, server_default="0"))
            if not _has_column(inspector, "evaluation_tasks", "total_samples"):
                batch_op.add_column(sa.Column("total_samples", sa.Integer(), nullable=False, server_default="0"))
            if not _has_column(inspector, "evaluation_tasks", "completed_samples"):
                batch_op.add_column(sa.Column("completed_samples", sa.Integer(), nullable=False, server_default="0"))
            if not _has_column(inspector, "evaluation_tasks", "failed_samples"):
                batch_op.add_column(sa.Column("failed_samples", sa.Integer(), nullable=False, server_default="0"))
            if not _has_column(inspector, "evaluation_tasks", "started_at"):
                batch_op.add_column(sa.Column("started_at", sa.DateTime(), nullable=True))
            if not _has_column(inspector, "evaluation_tasks", "finished_at"):
                batch_op.add_column(sa.Column("finished_at", sa.DateTime(), nullable=True))
            if not _has_column(inspector, "evaluation_tasks", "error_message"):
                batch_op.add_column(sa.Column("error_message", sa.Text(), nullable=True))
            if not _has_column(inspector, "evaluation_tasks", "deleted_at"):
                batch_op.add_column(sa.Column("deleted_at", sa.DateTime(), nullable=True))

    inspector = sa.inspect(bind)
    if not _has_table(inspector, "evaluation_results"):
        _create_evaluation_results_table()
    else:
        with op.batch_alter_table("evaluation_results") as batch_op:
            if not _has_column(inspector, "evaluation_results", "sample_id"):
                batch_op.add_column(sa.Column("sample_id", sa.String(length=255), nullable=True))
            if not _has_column(inspector, "evaluation_results", "user_input"):
                batch_op.add_column(sa.Column("user_input", sa.Text(), nullable=True))
            if not _has_column(inspector, "evaluation_results", "agent_output"):
                batch_op.add_column(sa.Column("agent_output", sa.Text(), nullable=True))
            if not _has_column(inspector, "evaluation_results", "reference_answer"):
                batch_op.add_column(sa.Column("reference_answer", sa.Text(), nullable=True))
            if not _has_column(inspector, "evaluation_results", "contexts"):
                batch_op.add_column(sa.Column("contexts", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
            if not _has_column(inspector, "evaluation_results", "tool_calls"):
                batch_op.add_column(sa.Column("tool_calls", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
            if not _has_column(inspector, "evaluation_results", "reasoning_trace"):
                batch_op.add_column(sa.Column("reasoning_trace", sa.Text(), nullable=True))
            if not _has_column(inspector, "evaluation_results", "metrics_scores"):
                batch_op.add_column(sa.Column("metrics_scores", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
            if not _has_column(inspector, "evaluation_results", "metrics_detail"):
                batch_op.add_column(sa.Column("metrics_detail", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
            if not _has_column(inspector, "evaluation_results", "response_time_ms"):
                batch_op.add_column(sa.Column("response_time_ms", sa.Integer(), nullable=True))
            if not _has_column(inspector, "evaluation_results", "token_input"):
                batch_op.add_column(sa.Column("token_input", sa.Integer(), nullable=True))
            if not _has_column(inspector, "evaluation_results", "token_output"):
                batch_op.add_column(sa.Column("token_output", sa.Integer(), nullable=True))
            if not _has_column(inspector, "evaluation_results", "status"):
                batch_op.add_column(sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"))
            if not _has_column(inspector, "evaluation_results", "error_message"):
                batch_op.add_column(sa.Column("error_message", sa.Text(), nullable=True))
            if not _has_column(inspector, "evaluation_results", "human_label"):
                batch_op.add_column(sa.Column("human_label", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))

        inspector = sa.inspect(bind)
        if not _has_index(inspector, "evaluation_results", "ix_evaluation_results_sample_id"):
            op.create_index("ix_evaluation_results_sample_id", "evaluation_results", ["sample_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("evaluation_results") as batch_op:
        batch_op.drop_index("ix_evaluation_results_sample_id")
        batch_op.drop_column("human_label")
        batch_op.drop_column("error_message")
        batch_op.drop_column("status")
        batch_op.drop_column("token_output")
        batch_op.drop_column("token_input")
        batch_op.drop_column("response_time_ms")
        batch_op.drop_column("metrics_detail")
        batch_op.drop_column("metrics_scores")
        batch_op.drop_column("reasoning_trace")
        batch_op.drop_column("tool_calls")
        batch_op.drop_column("contexts")
        batch_op.drop_column("reference_answer")
        batch_op.drop_column("agent_output")
        batch_op.drop_column("user_input")
        batch_op.drop_column("sample_id")

    with op.batch_alter_table("evaluation_tasks") as batch_op:
        batch_op.drop_column("deleted_at")
        batch_op.drop_column("error_message")
        batch_op.drop_column("finished_at")
        batch_op.drop_column("started_at")
        batch_op.drop_column("failed_samples")
        batch_op.drop_column("completed_samples")
        batch_op.drop_column("total_samples")
        batch_op.drop_column("progress")
        batch_op.drop_column("metrics")
        batch_op.drop_column("run_config")
        batch_op.drop_column("judge_config")
        batch_op.drop_column("eval_mode")
        batch_op.drop_column("agent_id")
        batch_op.drop_column("description")

    op.drop_index("ix_metric_templates_name", table_name="metric_templates")
    op.drop_table("metric_templates")

    op.drop_index("ix_agent_versions_agent_id", table_name="agent_versions")
    op.drop_table("agent_versions")

    op.drop_index("ix_agents_name", table_name="agents")
    op.drop_table("agents")
