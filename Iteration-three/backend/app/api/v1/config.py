"""System configuration API endpoints."""

from __future__ import annotations

import time

from fastapi import APIRouter
from pydantic import BaseModel

from app.db.connection import get_db
from app.services.config_repository import (
    VALID_KEYS,
    get_all_config,
    mask_value,
    update_config,
)

router = APIRouter(prefix="/config", tags=["config"])


class ConfigItem(BaseModel):
    key: str
    value: str | None = None


class ConfigResponse(BaseModel):
    items: list[ConfigItem]


class ConfigUpdateRequest(BaseModel):
    llm_base_url: str | None = None
    anthropic_api_key: str | None = None
    langsmith_api_key: str | None = None
    langsmith_tracing: bool | None = None
    langsmith_endpoint: str | None = None
    langsmith_project: str | None = None
    llm_model: str | None = None
    llm_max_tokens: int | None = None


def _serialize_config(raw: dict[str, str | None]) -> list[ConfigItem]:
    """Convert raw config dict to masked ConfigItem list."""
    items = []
    for key in sorted(VALID_KEYS):
        value = raw.get(key)
        items.append(ConfigItem(key=key, value=mask_value(key, value)))
    return items


@router.get("", response_model=ConfigResponse)
async def get_config_endpoint() -> ConfigResponse:
    """Return all config values with sensitive fields masked."""
    async with get_db() as db:
        raw = await get_all_config(db)
    return ConfigResponse(items=_serialize_config(raw))


@router.post("/update", response_model=ConfigResponse)
async def update_config_endpoint(req: ConfigUpdateRequest) -> ConfigResponse:
    """Batch update config values. Pass __KEEP_EXISTING__ to skip a field."""
    updates: dict[str, str | None] = {}
    for key, value in req.model_dump(exclude_none=True).items():
        if isinstance(value, bool):
            updates[key] = "true" if value else "false"
        else:
            updates[key] = str(value)

    async with get_db() as db:
        await update_config(db, updates)
        raw = await get_all_config(db)
    return ConfigResponse(items=_serialize_config(raw))


class ConfigTestResponse(BaseModel):
    success: bool
    model: str | None = None
    latency_ms: int | None = None
    error_code: str | None = None
    message: str | None = None


@router.post("/test", response_model=ConfigTestResponse)
async def test_config_endpoint() -> ConfigTestResponse:
    """Test LLM connectivity using current database config."""
    from app.services.llm import create_llm_client

    try:
        llm = create_llm_client()
    except ValueError as e:
        return ConfigTestResponse(
            success=False,
            error_code="config_not_set",
            message=str(e),
        )

    start = time.monotonic()
    try:
        test_llm = llm.bind(max_tokens=1)
        await test_llm.ainvoke("ping")
        latency = int((time.monotonic() - start) * 1000)
        raw_model = getattr(llm, "model", None)
        model_name = raw_model if isinstance(raw_model, str) else None
        return ConfigTestResponse(
            success=True,
            model=model_name,
            latency_ms=latency,
            message="连接成功",
        )
    except Exception as e:
        latency = int((time.monotonic() - start) * 1000)
        return ConfigTestResponse(
            success=False,
            latency_ms=latency,
            error_code="config_test_failed",
            message=str(e),
        )
