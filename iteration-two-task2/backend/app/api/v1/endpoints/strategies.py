from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.strategy_service import StrategyService

router = APIRouter()


class StrategyPayload(BaseModel):
    name: str
    weights: dict[str, float]
    metrics: list[str]
    description: str | None = None
    dimension_weights: dict[str, float] | None = None


@router.get("/")
def list_strategies(db: Session = Depends(get_db)) -> list[dict]:
    return StrategyService.list_strategies(db)


@router.post("/")
def save_strategy(payload: StrategyPayload, db: Session = Depends(get_db)) -> dict:
    return StrategyService.save_strategy(db, payload.model_dump())
