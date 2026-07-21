from datetime import datetime

from pydantic import BaseModel, Field


class MetricTemplateCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    template_type: str = "llm_judge"
    description: str | None = None
    prompt_template: str | None = None
    webhook_url: str | None = None
    score_range: dict = Field(default_factory=lambda: {"min": 0, "max": 1})
    is_builtin: bool = False


class MetricTemplateUpdate(BaseModel):
    name: str | None = None
    template_type: str | None = None
    description: str | None = None
    prompt_template: str | None = None
    webhook_url: str | None = None
    score_range: dict | None = None
    is_builtin: bool | None = None


class MetricTemplateRead(BaseModel):
    id: int
    name: str
    template_type: str
    description: str | None
    prompt_template: str | None
    webhook_url: str | None
    score_range: dict
    is_builtin: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
