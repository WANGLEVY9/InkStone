from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.result import EvaluationResult
from app.schemas.result import CompareRequest, CompareResponse, ResultLabelUpdate, ResultRead
from app.services.analysis_service import AnalysisService

router = APIRouter()


@router.get("/task/{task_id}", response_model=list[ResultRead])
def list_task_results(task_id: int, db: Session = Depends(get_db)) -> list[ResultRead]:
    items = db.scalars(
        select(EvaluationResult)
        .where(EvaluationResult.task_id == task_id)
        .order_by(EvaluationResult.id.desc())
    ).all()
    return [ResultRead.model_validate(item) for item in items]


@router.get("/{result_id}", response_model=ResultRead)
def get_result(result_id: int, db: Session = Depends(get_db)) -> ResultRead:
    result = db.get(EvaluationResult, result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="result not found")
    return ResultRead.model_validate(result)


@router.patch("/{result_id}/label", response_model=ResultRead)
def update_result_label(
    result_id: int, payload: ResultLabelUpdate, db: Session = Depends(get_db)
) -> ResultRead:
    result = db.get(EvaluationResult, result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="result not found")
    result.human_label = payload.human_label
    db.commit()
    db.refresh(result)
    return ResultRead.model_validate(result)


@router.post("/compare", response_model=CompareResponse)
def compare_results(
    payload: CompareRequest, db: Session = Depends(get_db)
) -> CompareResponse:
    items = db.scalars(
        select(EvaluationResult).where(EvaluationResult.task_id.in_(payload.task_ids))
    ).all()
    data = AnalysisService.compare_results(items)
    return CompareResponse(summary=data["summary"], by_metric=data["by_metric"])
