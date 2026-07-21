from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.strategy import EvaluationStrategy


class StrategyService:
    @classmethod
    def list_strategies(cls, db: Session) -> list[dict]:
        items = db.scalars(
            select(EvaluationStrategy).order_by(EvaluationStrategy.id.desc())
        ).all()
        return [
            {
                "id": item.id,
                "name": item.name,
                "weights": item.weights,
                "metrics": item.metrics,
                "dimension_weights": item.dimension_weights,
                "description": item.description,
            }
            for item in items
        ]

    @classmethod
    def save_strategy(cls, db: Session, payload: dict) -> dict:
        strategy = db.scalar(
            select(EvaluationStrategy).where(EvaluationStrategy.name == payload["name"])
        )
        if strategy is None:
            strategy = EvaluationStrategy(
                name=payload["name"],
                weights=payload.get("weights", {}),
                metrics=payload.get("metrics", []),
                dimension_weights=payload.get("dimension_weights"),
                description=payload.get("description"),
            )
            db.add(strategy)
        else:
            strategy.weights = payload.get("weights", {})
            strategy.metrics = payload.get("metrics", [])
            strategy.dimension_weights = payload.get("dimension_weights")
            strategy.description = payload.get("description")

        db.commit()
        db.refresh(strategy)
        return {
            "id": strategy.id,
            "name": strategy.name,
            "weights": strategy.weights,
            "metrics": strategy.metrics,
            "dimension_weights": strategy.dimension_weights,
            "description": strategy.description,
        }
