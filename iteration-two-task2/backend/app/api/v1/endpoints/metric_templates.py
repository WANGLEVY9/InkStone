from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.metric_template import MetricTemplate
from app.schemas.metric_template import (
    MetricTemplateCreate,
    MetricTemplateRead,
    MetricTemplateUpdate,
)

router = APIRouter()


@router.get("/", response_model=list[MetricTemplateRead])
def list_metric_templates(db: Session = Depends(get_db)) -> list[MetricTemplateRead]:
    items = db.scalars(select(MetricTemplate).order_by(MetricTemplate.id.desc())).all()
    return [MetricTemplateRead.model_validate(item) for item in items]


@router.post("/", response_model=MetricTemplateRead)
def create_metric_template(
    payload: MetricTemplateCreate, db: Session = Depends(get_db)
) -> MetricTemplateRead:
    item = MetricTemplate(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return MetricTemplateRead.model_validate(item)


@router.get("/{template_id}", response_model=MetricTemplateRead)
def get_metric_template(template_id: int, db: Session = Depends(get_db)) -> MetricTemplateRead:
    item = db.get(MetricTemplate, template_id)
    if item is None:
        raise HTTPException(status_code=404, detail="metric template not found")
    return MetricTemplateRead.model_validate(item)


@router.put("/{template_id}", response_model=MetricTemplateRead)
def update_metric_template(
    template_id: int, payload: MetricTemplateUpdate, db: Session = Depends(get_db)
) -> MetricTemplateRead:
    item = db.get(MetricTemplate, template_id)
    if item is None:
        raise HTTPException(status_code=404, detail="metric template not found")
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return MetricTemplateRead.model_validate(item)


@router.delete("/{template_id}")
def delete_metric_template(template_id: int, db: Session = Depends(get_db)) -> dict:
    item = db.get(MetricTemplate, template_id)
    if item is None:
        raise HTTPException(status_code=404, detail="metric template not found")
    db.delete(item)
    db.commit()
    return {"message": "deleted"}
