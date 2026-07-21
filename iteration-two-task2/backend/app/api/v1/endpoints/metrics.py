from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.metric import MetricDefinition
from app.schemas.metric import MetricCreate, MetricRead

router = APIRouter()


@router.get("/", response_model=list[MetricRead])
def list_metrics(db: Session = Depends(get_db)) -> list[MetricRead]:
    items = db.scalars(
        select(MetricDefinition).order_by(MetricDefinition.id.desc())
    ).all()
    return [MetricRead.model_validate(item) for item in items]


@router.post("/", response_model=MetricRead)
def create_metric(payload: MetricCreate, db: Session = Depends(get_db)) -> MetricRead:
    metric = MetricDefinition(
        name=payload.name,
        metric_type=payload.metric_type,
        logic_type=payload.logic_type,
        ragas_config=payload.ragas_config,
        description=payload.description,
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return MetricRead.model_validate(metric)


@router.delete("/{metric_id}")
def delete_metric(metric_id: int, db: Session = Depends(get_db)) -> dict:
    metric = db.get(MetricDefinition, metric_id)
    if metric is None:
        raise HTTPException(status_code=404, detail="metric not found")
    db.delete(metric)
    db.commit()
    return {"message": "deleted"}
