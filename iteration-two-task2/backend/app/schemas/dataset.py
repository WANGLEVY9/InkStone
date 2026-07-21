from datetime import datetime

from pydantic import BaseModel, Field


class DatasetRead(BaseModel):
    id: int
    dataset_id: str
    name: str
    filename: str
    content_type: str
    parser_summary: dict
    note: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DatasetListResponse(BaseModel):
    total: int
    items: list[DatasetRead]


class DatasetUploadResponse(BaseModel):
    dataset: DatasetRead
    parsed_metrics: list[str] = Field(default_factory=list)
    recommended_task_payload: dict = Field(default_factory=dict)


class DatasetRealtimeAnalysisResponse(BaseModel):
    dataset_id: str
    timeline: list[dict] = Field(default_factory=list)
    live_metrics: dict = Field(default_factory=dict)
    findings: list[str] = Field(default_factory=list)


class DatasetPreviewResponse(BaseModel):
    dataset_id: str
    total: int
    items: list[dict] = Field(default_factory=list)
