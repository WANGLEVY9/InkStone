from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RealtimeSessionStartRequest(BaseModel):
    session_id: str | None = None
    agent_name: str = "default-agent"
    task: str = ""
    thresholds: dict[str, float] = Field(default_factory=dict)


class RealtimeStepStartRequest(BaseModel):
    step: int | None = None
    thought: str | None = None
    action: str | None = None


class RealtimeToolCallRequest(BaseModel):
    tool_name: str
    params: dict[str, Any] = Field(default_factory=dict)
    dangerous: bool = False


class RealtimeStepEndRequest(BaseModel):
    step: int | None = None
    action: str | None = None
    duration_sec: float = 0.0
    step_result: str | None = None


class RealtimeStreamToolCall(BaseModel):
    name: str
    params: dict[str, Any] = Field(default_factory=dict)
    dangerous: bool = False


class RealtimeStreamEventRequest(BaseModel):
    event_type: str = "node_execution"
    node: str
    agent_type: str = "worker"
    step: int | None = None
    thought: str | None = None
    message: str | None = None
    next_agent: str | None = None
    tool_calls: list[RealtimeStreamToolCall] = Field(default_factory=list)
    state: dict[str, Any] = Field(default_factory=dict)
    duration_sec: float = 0.0
    timestamp: datetime | None = None
    source: str = "langgraph-stream"


class RealtimeStreamEventRead(BaseModel):
    id: str
    session_id: str
    event_type: str
    node: str
    agent_type: str
    step: int
    thought: str = ""
    message: str = ""
    next_agent: str = ""
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    state: dict[str, Any] = Field(default_factory=dict)
    duration_sec: float = 0.0
    decision: str = "CONTINUE"
    reason: str = ""
    source: str = "langgraph-stream"
    created_at: datetime


class RealtimeAlertRead(BaseModel):
    id: str
    session_id: str
    rule: str
    severity: str
    message: str
    decision: str
    created_at: datetime


class RealtimeSessionRead(BaseModel):
    session_id: str
    status: str
    agent_name: str
    task: str
    started_at: datetime
    ended_at: datetime | None = None
    step_count: int
    tool_call_count: int
    consecutive_same_action: int
    node_switch_count: int = 0
    event_count: int = 0
    current_node: str | None = None
    current_agent_type: str | None = None
    latest_decision: str
    alert_count: int


class RealtimeSessionDetailResponse(BaseModel):
    session: RealtimeSessionRead
    latest_alerts: list[RealtimeAlertRead] = Field(default_factory=list)
    latest_events: list[RealtimeStreamEventRead] = Field(default_factory=list)


class RealtimeEventIngestResponse(BaseModel):
    session: RealtimeSessionRead
    event: RealtimeStreamEventRead
    decision: str
    reason: str = ""
    should_stop: bool = False


class RealtimeSessionListResponse(BaseModel):
    total: int
    items: list[RealtimeSessionRead]


class RealtimeAlertsResponse(BaseModel):
    session_id: str
    total: int
    items: list[RealtimeAlertRead]


class StandardTraceStep(BaseModel):
    step: int
    thought: str = ""
    action: dict[str, Any] = Field(default_factory=dict)
    result: str = ""
    duration: float = 0.0
    memory_hit: bool | None = None


class StandardTrace(BaseModel):
    session_id: str
    task: str
    steps: list[StandardTraceStep] = Field(default_factory=list)
    final_result: str = ""
    success: bool | None = None
    expected_result: str | None = None


class OfflineEvalSubmitRequest(BaseModel):
    trace: StandardTrace


class OfflineEvalReport(BaseModel):
    session_id: str
    task: str
    success: bool
    scores: dict[str, float] = Field(default_factory=dict)
    metrics: dict[str, float | int] = Field(default_factory=dict)
    root_cause: str
    recommendations: list[str] = Field(default_factory=list)


class OfflineEvalJobRead(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    error: str | None = None
    report: OfflineEvalReport | None = None


class OfflineEvalJobListResponse(BaseModel):
    total: int
    items: list[OfflineEvalJobRead]


class DatasetBatchRunRequest(BaseModel):
    dataset_id: str
    strategy_name: str | None = None
    eval_task_id: int | None = None


class DatasetBatchSummary(BaseModel):
    dataset_id: str
    total_traces: int
    success_rate: float
    average_scores: dict[str, float] = Field(default_factory=dict)
    root_cause_distribution: dict[str, int] = Field(default_factory=dict)
    sample_reports: list[OfflineEvalReport] = Field(default_factory=list)


class DatasetBatchJobRead(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    error: str | None = None
    summary: DatasetBatchSummary | None = None
    progress: dict | None = None
    eval_task_id: int | None = None


class DatasetBatchJobListResponse(BaseModel):
    total: int
    items: list[DatasetBatchJobRead]
