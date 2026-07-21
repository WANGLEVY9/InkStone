from datetime import datetime

from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    endpoint: str
    auth_type: str = "none"
    auth_config: dict = Field(default_factory=dict)
    timeout_ms: int = 30000
    metadata: dict = Field(default_factory=dict)


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    endpoint: str | None = None
    auth_type: str | None = None
    auth_config: dict | None = None
    timeout_ms: int | None = None
    metadata: dict | None = None


class AgentRead(BaseModel):
    id: int
    name: str
    description: str | None
    endpoint: str
    auth_type: str
    auth_config: dict
    timeout_ms: int
    metadata: dict = Field(alias="metadata_json")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class AgentConnectivityTestResponse(BaseModel):
    ok: bool
    message: str
    status_code: int | None = None
