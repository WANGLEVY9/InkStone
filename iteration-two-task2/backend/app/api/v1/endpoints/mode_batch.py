from fastapi import APIRouter, HTTPException

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.schemas.mode_eval import (
    DatasetBatchJobListResponse,
    DatasetBatchJobRead,
    DatasetBatchRunRequest,
)
from app.services.mode_eval_service import ModeEvalService

router = APIRouter()
settings = get_settings()


@router.post("/jobs/run", response_model=DatasetBatchJobRead)
def run_dataset_batch_job(
    payload: DatasetBatchRunRequest,
) -> DatasetBatchJobRead:
    job = ModeEvalService.submit_batch_job(
        payload.dataset_id,
        strategy_name=payload.strategy_name,
        eval_task_id=payload.eval_task_id,
    )
    if settings.use_celery:
        celery_app.send_task("process_batch_eval_job", args=[job["job_id"]])
    else:
        ModeEvalService.process_batch_job(job["job_id"])
        try:
            from app.workers.tasks import _trigger_batch_llm_judge
            _trigger_batch_llm_judge(job["job_id"])
        except Exception:
            pass
    return DatasetBatchJobRead(**job)


@router.get("/jobs", response_model=DatasetBatchJobListResponse)
def list_batch_jobs() -> DatasetBatchJobListResponse:
    items = ModeEvalService.list_batch_jobs()
    return DatasetBatchJobListResponse(total=len(items), items=[DatasetBatchJobRead(**item) for item in items])


@router.get("/jobs/{job_id}", response_model=DatasetBatchJobRead)
def get_batch_job(job_id: str) -> DatasetBatchJobRead:
    data = ModeEvalService.get_batch_job(job_id)
    if data is None:
        raise HTTPException(status_code=404, detail="job not found")
    return DatasetBatchJobRead(**data)
