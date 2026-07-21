from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


TaskStatus = Literal["draft", "pending", "running", "completed", "failed", "cancelled"]
EvalMode = Literal["result", "process", "result_and_process", "dataset-batch"]
EvalMethod = Literal["explicit", "fuzzy"]
EvalDimension = Literal["effectiveness", "safety", "performance"]


class TaskConfig(BaseModel):
    metrics: list[str] = Field(default_factory=list)
    strategy: str = "default"
    enable_process_trace: bool = False


class TaskCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None
    agent_id: int | None = None
    agent_version: str = "v1"
    dataset_id: str
    mode: EvalMode = "result"
    eval_mode: EvalMode | None = None
    method: EvalMethod = "explicit"
    dimension: EvalDimension = "effectiveness"
    config: TaskConfig = Field(default_factory=TaskConfig)
    judge_config: dict = Field(default_factory=dict)
    run_config: dict = Field(default_factory=dict)
    metrics: list[str] = Field(default_factory=list)
    input_payload: dict = Field(default_factory=dict)
    note: str | None = None


class TaskUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    agent_id: int | None = None
    agent_version: str | None = None
    dataset_id: str | None = None
    mode: EvalMode | None = None
    eval_mode: EvalMode | None = None
    method: EvalMethod | None = None
    dimension: EvalDimension | None = None
    status: TaskStatus | None = None
    config: TaskConfig | None = None
    judge_config: dict | None = None
    run_config: dict | None = None
    metrics: list[str] | None = None
    input_payload: dict | None = None
    note: str | None = None


class TaskRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    agent_id: int | None = None
    agent_version: str
    dataset_id: str
    mode: EvalMode
    eval_mode: EvalMode
    method: EvalMethod
    dimension: EvalDimension
    status: TaskStatus
    config: dict
    judge_config: dict
    run_config: dict
    metrics: list[str]
    input_payload: dict
    progress: int
    total_samples: int
    completed_samples: int
    failed_samples: int
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None
    note: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[TaskRead]
