from fastapi import APIRouter, HTTPException

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.schemas.mode_eval import (
    OfflineEvalJobListResponse,
    OfflineEvalJobRead,
    OfflineEvalSubmitRequest,
)
from app.services.mode_eval_service import ModeEvalService

router = APIRouter()
settings = get_settings()


@router.post("/jobs/submit", response_model=OfflineEvalJobRead)
def submit_offline_eval_job(payload: OfflineEvalSubmitRequest) -> OfflineEvalJobRead:
    job = ModeEvalService.submit_offline_job(payload.trace.model_dump())
    if settings.use_celery:
        celery_app.send_task("process_offline_eval_job", args=[job["job_id"]])
    else:
        ModeEvalService.process_offline_job(job["job_id"])
        try:
            from app.workers.tasks import _trigger_offline_llm_judge
            _trigger_offline_llm_judge(job["job_id"])
        except Exception:
            pass
    return OfflineEvalJobRead(**job)


@router.get("/jobs", response_model=OfflineEvalJobListResponse)
def list_offline_eval_jobs() -> OfflineEvalJobListResponse:
    items = ModeEvalService.list_offline_jobs()
    return OfflineEvalJobListResponse(total=len(items), items=[OfflineEvalJobRead(**item) for item in items])


@router.get("/jobs/{job_id}", response_model=OfflineEvalJobRead)
def get_offline_eval_job(job_id: str) -> OfflineEvalJobRead:
    data = ModeEvalService.get_offline_job(job_id)
    if data is None:
        raise HTTPException(status_code=404, detail="job not found")
    return OfflineEvalJobRead(**data)
