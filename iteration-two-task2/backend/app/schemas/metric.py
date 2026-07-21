from datetime import datetime

from pydantic import BaseModel, Field


class MetricCreate(BaseModel):
    name: str
    metric_type: str = "explicit"
    logic_type: str = "builtin"
    ragas_config: dict = Field(default_factory=dict)
    description: str | None = None


class MetricRead(BaseModel):
    id: int
    name: str
    metric_type: str
    logic_type: str
    ragas_config: dict
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
