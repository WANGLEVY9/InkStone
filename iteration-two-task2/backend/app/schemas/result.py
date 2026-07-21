from datetime import datetime

from pydantic import BaseModel


class ResultRead(BaseModel):
    id: int
    task_id: int
    sample_id: str | None = None
    status: str
    metrics_scores: dict
    metrics_detail: dict
    human_label: dict
    scores: dict
    raw_data: dict
    stats: dict
    response_time_ms: int | None = None
    token_input: int | None = None
    token_output: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompareRequest(BaseModel):
    task_ids: list[int]


class CompareResponse(BaseModel):
    summary: dict
    by_metric: dict


class ResultLabelUpdate(BaseModel):
    human_label: dict
