import csv
import io
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.core.database import get_db
from app.core.database import SessionLocal
from app.models.result import EvaluationResult
from app.schemas.eval import ExecuteResponse
from app.schemas.result import CompareRequest, CompareResponse
from app.schemas.task import TaskCreate, TaskListResponse, TaskRead, TaskUpdate
from app.services.analysis_service import AnalysisService
from app.services.evaluation_engine import EvaluationEngine
from app.services.task_service import TaskService
from app.api.v1.endpoints.ws_manager import broadcast_sync, connect, disconnect

router = APIRouter()
settings = get_settings()

def _task_ws_payload(task) -> dict:
    return {
        "id": task.id,
        "name": task.name,
        "status": task.status,
        "progress": task.progress,
        "total_samples": task.total_samples,
        "completed_samples": task.completed_samples,
        "failed_samples": task.failed_samples,
        "error_message": task.error_message,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "finished_at": task.finished_at.isoformat() if task.finished_at else None,
    }


@router.get("/", response_model=TaskListResponse)
def list_tasks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=200, ge=1, le=1000),
    status: str | None = None,
    method: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    db: Session = Depends(get_db),
) -> TaskListResponse:
    total, items = TaskService.list_tasks(
        db,
        page=page,
        page_size=page_size,
        status=status,
        method=method,
        start_time=start_time,
        end_time=end_time,
    )
    return TaskListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[TaskRead.model_validate(item) for item in items],
    )


@router.post("/", response_model=TaskRead)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> TaskRead:
    return TaskRead.model_validate(TaskService.create_task(db, payload))


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, db: Session = Depends(get_db)) -> TaskRead:
    task = TaskService.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return TaskRead.model_validate(task)


@router.put("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)
) -> TaskRead:
    task = TaskService.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    updated = TaskService.update_task(db, task, payload)
    return TaskRead.model_validate(updated)


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)) -> dict:
    task = TaskService.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    TaskService.delete_task(db, task)
    return {"message": "deleted"}


def _run_task(task_id: int, db: Session) -> ExecuteResponse:
    task = TaskService.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    if task.status == "cancelled":
        raise HTTPException(status_code=400, detail="task is cancelled")

    task.status = "pending"
    task.started_at = datetime.utcnow()
    task.error_message = None
    db.commit()
    broadcast_sync(f"task-{task.id}", "task_queued", {"task": _task_ws_payload(task)})

    if settings.use_celery:
        worker_task = celery_app.send_task("execute_evaluation_task", args=[task_id])
        return ExecuteResponse(
            task_id=task_id, message="queued", worker_task_id=worker_task.id
        )

    local_db = SessionLocal()
    try:
        local_task = TaskService.get_task(local_db, task_id)
        if local_task is None:
            raise HTTPException(status_code=404, detail="task not found")
        EvaluationEngine.execute(local_db, local_task)
        try:
            from app.workers.tasks import _trigger_task_llm_judge
            _trigger_task_llm_judge(task_id)
        except Exception:
            pass
    finally:
        local_db.close()
    return ExecuteResponse(task_id=task_id, message="completed", worker_task_id=None)


@router.post("/{task_id}/execute", response_model=ExecuteResponse)
def execute_task(task_id: int, db: Session = Depends(get_db)) -> ExecuteResponse:
    return _run_task(task_id, db)


@router.post("/{task_id}/run", response_model=ExecuteResponse)
def run_task(task_id: int, db: Session = Depends(get_db)) -> ExecuteResponse:
    return _run_task(task_id, db)


@router.post("/{task_id}/cancel")
def cancel_task(task_id: int, db: Session = Depends(get_db)) -> dict:
    task = TaskService.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    if task.status in {"completed", "failed"}:
        raise HTTPException(status_code=400, detail="task already finished")

    task.status = "cancelled"
    task.finished_at = datetime.utcnow()
    db.commit()
    broadcast_sync(f"task-{task.id}", "task_cancelled", {"task": _task_ws_payload(task)})
    return {"message": "cancelled"}


@router.post("/{task_id}/clone", response_model=TaskRead)
def clone_task(task_id: int, db: Session = Depends(get_db)) -> TaskRead:
    task = TaskService.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")

    cloned = TaskService.create_task(
        db,
        TaskCreate(
            name=f"{task.name} (copy)",
            description=task.description,
            agent_id=task.agent_id,
            agent_version=task.agent_version,
            dataset_id=task.dataset_id,
            mode=task.mode,  # compatibility input
            method=task.method,
            dimension=task.dimension,
            config=task.config,
            judge_config=task.judge_config,
            run_config=task.run_config,
            metrics=task.metrics,
            input_payload=task.input_payload,
            note=task.note,
        ),
    )
    return TaskRead.model_validate(cloned)


@router.get("/{task_id}/stats")
def get_task_stats(task_id: int, db: Session = Depends(get_db)) -> dict:
    task = TaskService.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")

    items = db.scalars(
        select(EvaluationResult).where(EvaluationResult.task_id == task_id)
    ).all()
    if not items:
        return {"task_id": task_id, "result_count": 0, "avg_scores": {}}

    score_totals: dict[str, float] = {}
    score_counts: dict[str, int] = {}
    for item in items:
        score_source = item.metrics_scores or item.scores or {}
        for metric, value in score_source.items():
            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                continue
            score_totals[metric] = score_totals.get(metric, 0.0) + numeric_value
            score_counts[metric] = score_counts.get(metric, 0) + 1

    avg_scores = {
        metric: round(score_totals[metric] / score_counts[metric], 4)
        for metric in score_totals
        if score_counts.get(metric, 0) > 0
    }
    return {
        "task_id": task_id,
        "result_count": len(items),
        "status": task.status,
        "progress": task.progress,
        "avg_scores": avg_scores,
    }


@router.get("/{task_id}/results", response_model=list[dict])
def list_task_results(
    task_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[dict]:
    task = TaskService.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")

    rows = db.scalars(
        select(EvaluationResult)
        .where(EvaluationResult.task_id == task_id)
        .order_by(EvaluationResult.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return [
        {
            "id": row.id,
            "task_id": row.task_id,
            "sample_id": row.sample_id,
            "status": row.status,
            "metrics_scores": row.metrics_scores or row.scores,
            "scores": row.scores,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
        for row in rows
    ]


@router.get("/{task_id}/results/export")
def export_task_results(
    task_id: int,
    format: str = Query(default="csv"),
    db: Session = Depends(get_db),
) -> Response:
    task = TaskService.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")

    rows = db.scalars(
        select(EvaluationResult)
        .where(EvaluationResult.task_id == task_id)
        .order_by(EvaluationResult.id.asc())
    ).all()
    if format not in {"csv", "excel"}:
        raise HTTPException(status_code=400, detail="unsupported export format")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "result_id",
            "task_id",
            "sample_id",
            "status",
            "user_input",
            "agent_output",
            "reference_answer",
            "metrics_scores",
            "created_at",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row.id,
                row.task_id,
                row.sample_id or "",
                row.status,
                row.user_input or "",
                row.agent_output or "",
                row.reference_answer or "",
                row.metrics_scores or row.scores,
                row.created_at.isoformat() if row.created_at else "",
            ]
        )
    csv_body = output.getvalue()
    filename = f"task_{task_id}_results.csv"
    return Response(
        content=csv_body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/compare", response_model=CompareResponse)
def compare_tasks(payload: CompareRequest, db: Session = Depends(get_db)) -> CompareResponse:
    if not payload.task_ids:
        raise HTTPException(status_code=400, detail="task_ids cannot be empty")
    items = db.scalars(
        select(EvaluationResult).where(EvaluationResult.task_id.in_(payload.task_ids))
    ).all()
    data = AnalysisService.compare_results(items)
    return CompareResponse(summary=data["summary"], by_metric=data["by_metric"])


@router.websocket("/{task_id}/ws")
async def task_progress_ws(websocket: WebSocket, task_id: int) -> None:
    session_id = f"task-{task_id}"
    await connect(session_id, websocket)
    try:
        db = SessionLocal()
        try:
            task = TaskService.get_task(db, task_id)
            if task is None:
                await websocket.send_text(
                    json.dumps({"event": "error", "data": {"message": "task not found"}})
                )
                return
            await websocket.send_text(
                json.dumps({"event": "task_init", "data": {"task": _task_ws_payload(task)}})
            )
        finally:
            db.close()

        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)
                if data.get("type") == "ping":
                    await websocket.send_text(json.dumps({"event": "pong"}))
            except ValueError:
                continue
    except WebSocketDisconnect:
        pass
    finally:
        disconnect(session_id, websocket)
