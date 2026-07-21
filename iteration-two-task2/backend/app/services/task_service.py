from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.task import EvaluationTask
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    @staticmethod
    def list_tasks(
        db: Session,
        page: int,
        page_size: int,
        status: str | None,
        method: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[int, Sequence[EvaluationTask]]:
        query = select(EvaluationTask).where(EvaluationTask.deleted_at.is_(None))
        if status:
            query = query.where(EvaluationTask.status == status)
        if method:
            query = query.where(EvaluationTask.method == method)
        if start_time:
            query = query.where(EvaluationTask.created_at >= start_time)
        if end_time:
            query = query.where(EvaluationTask.created_at <= end_time)

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = db.scalars(
            query.order_by(EvaluationTask.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return int(total), items

    @staticmethod
    def get_task(db: Session, task_id: int) -> EvaluationTask | None:
        task = db.get(EvaluationTask, task_id)
        if task is None or task.deleted_at is not None:
            return None
        return task

    @staticmethod
    def create_task(db: Session, payload: TaskCreate) -> EvaluationTask:
        resolved_mode = payload.eval_mode or payload.mode
        resolved_metrics = payload.metrics or payload.config.metrics
        task = EvaluationTask(
            name=payload.name,
            description=payload.description,
            agent_id=payload.agent_id,
            agent_version=payload.agent_version,
            dataset_id=payload.dataset_id,
            mode=resolved_mode,
            eval_mode=resolved_mode,
            method=payload.method,
            dimension=payload.dimension,
            config=payload.config.model_dump(),
            judge_config=payload.judge_config,
            run_config=payload.run_config,
            metrics=resolved_metrics,
            input_payload=payload.input_payload,
            note=payload.note,
            status="draft",
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def update_task(
        db: Session, task: EvaluationTask, payload: TaskUpdate
    ) -> EvaluationTask:
        data = payload.model_dump(exclude_none=True)
        for key, value in data.items():
            if key == "config" and value is not None:
                setattr(task, key, value.model_dump())
            elif key in {"mode", "eval_mode"} and value is not None:
                task.mode = value
                task.eval_mode = value
            else:
                setattr(task, key, value)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete_task(db: Session, task: EvaluationTask) -> None:
        task.deleted_at = datetime.utcnow()
        db.commit()
