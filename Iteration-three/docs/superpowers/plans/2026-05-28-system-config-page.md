# System Config Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a global system settings page where users can view and edit LLM configuration (API keys, model, base URL, etc.) via the frontend, with hot-reload and connection testing.

**Architecture:** New `app_config` key-value table in SQLite stores all settings. A `ConfigService` reads/writes config from the DB. The existing `create_llm_client()` in `llm.py` is modified to read from `ConfigService` instead of `os.getenv`. The frontend gets a new `/settings` route with its own `SystemLayout` (IconSidebar only, no project context). Sensitive fields (API keys) are masked in GET responses and use password inputs with `__KEEP_EXISTING__` sentinel for unchanged values.

**Tech Stack:** Python 3.13 + FastAPI + aiosqlite (backend), React 18 + TypeScript + Ant Design 6 (frontend)

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `backend/app/services/config_repository.py` | DB read/write for `app_config` table |
| Create | `backend/app/api/v1/config.py` | GET/POST/POST-test router |
| Create | `backend/tests/test_config_api.py` | Backend tests |
| Modify | `backend/app/db/schema.sql` | Add `app_config` table |
| Modify | `backend/app/services/llm.py` | Read from ConfigService instead of env vars |
| Modify | `backend/app/core/errors.py` | Add `CONFIG_NOT_SET` error code |
| Modify | `backend/app/main.py` | Register config router |
| Create | `frontend/src/api/config.ts` | API client for config endpoints |
| Create | `frontend/src/components/layout/SystemLayout.tsx` | Layout with only IconSidebar |
| Create | `frontend/src/pages/settings/SystemSettings.tsx` | Config form page |
| Modify | `frontend/src/types/index.ts` | Add config types |
| Modify | `frontend/src/App.tsx` | Add `/settings` route |
| Modify | `frontend/src/components/layout/IconSidebar.tsx` | Add system settings button |
| Modify | `frontend/src/hooks/useProjectChat.ts` | Handle `config_not_set` error |

---

### Task 1: Backend — Schema & Config Repository

**Files:**
- Modify: `backend/app/db/schema.sql`
- Create: `backend/app/services/config_repository.py`
- Create: `backend/tests/test_config_api.py` (tests 1–4)

- [ ] **Step 1: Add `app_config` table to schema.sql**

Append to `backend/app/db/schema.sql`:

```sql
-- Application configuration (global key-value store)
CREATE TABLE IF NOT EXISTS app_config (
    key   TEXT PRIMARY KEY NOT NULL,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

- [ ] **Step 2: Write tests for config repository**

Create `backend/tests/test_config_api.py`:

```python
"""Tests for config repository and API endpoints."""

from __future__ import annotations

import pytest
import aiosqlite
from pathlib import Path


@pytest.fixture()
async def db(tmp_path: Path) -> aiosqlite.Connection:
    """Create an in-memory-like SQLite database with the schema applied."""
    db_path = tmp_path / "test.db"
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    schema = Path(__file__).parent.parent / "app" / "db" / "schema.sql"
    async with open(schema) as f:
        await db.executescript(await f.read())
    await db.commit()
    yield db
    await db.close()


class TestConfigRepository:
    """Tests for config_repository functions."""

    async def test_get_config_returns_none_when_empty(self, db: aiosqlite.Connection) -> None:
        from app.services.config_repository import get_config

        result = await get_config(db, "anthropic_api_key")
        assert result is None

    async def test_update_and_get_config(self, db: aiosqlite.Connection) -> None:
        from app.services.config_repository import update_config, get_config

        await update_config(db, {"anthropic_api_key": "sk-test123", "llm_model": "claude-sonnet"})
        val = await get_config(db, "anthropic_api_key")
        assert val == "sk-test123"
        val2 = await get_config(db, "llm_model")
        assert val2 == "claude-sonnet"

    async def test_get_all_config(self, db: aiosqlite.Connection) -> None:
        from app.services.config_repository import update_config, get_all_config

        await update_config(db, {"llm_model": "claude-sonnet", "llm_max_tokens": "65536"})
        result = await get_all_config(db)
        assert result["llm_model"] == "claude-sonnet"
        assert result["llm_max_tokens"] == "65536"

    async def test_update_config_skips_none_values(self, db: aiosqlite.Connection) -> None:
        from app.services.config_repository import update_config, get_config

        await update_config(db, {"llm_model": "old-model"})
        await update_config(db, {"llm_model": None, "llm_max_tokens": "1024"})
        assert await get_config(db, "llm_model") == "old-model"
        assert await get_config(db, "llm_max_tokens") == "1024"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_config_api.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.config_repository'`

- [ ] **Step 4: Implement config_repository.py**

Create `backend/app/services/config_repository.py`:

```python
"""Repository functions for the app_config key-value store."""

from __future__ import annotations

import aiosqlite

VALID_KEYS = {
    "llm_base_url",
    "anthropic_api_key",
    "langsmith_api_key",
    "langsmith_tracing",
    "llm_model",
    "llm_max_tokens",
}

SENSITIVE_KEYS = {"anthropic_api_key", "langsmith_api_key"}

KEEP_SENTINEL = "__KEEP_EXISTING__"


def mask_value(key: str, value: str | None) -> str | None:
    """Mask sensitive config values for API responses."""
    if value is None or key not in SENSITIVE_KEYS:
        return value
    if len(value) < 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


async def get_config(db: aiosqlite.Connection, key: str) -> str | None:
    """Read a single config value from the database."""
    async with db.execute("SELECT value FROM app_config WHERE key = ?", (key,)) as cursor:
        row = await cursor.fetchone()
        return row[0] if row else None


async def get_all_config(db: aiosqlite.Connection) -> dict[str, str | None]:
    """Read all config values. Returns dict keyed by config key."""
    result: dict[str, str | None] = {k: None for k in VALID_KEYS}
    async with db.execute("SELECT key, value FROM app_config") as cursor:
        async for row in cursor:
            if row[0] in VALID_KEYS:
                result[row[0]] = row[1]
    return result


async def update_config(db: aiosqlite.Connection, updates: dict[str, str | None]) -> None:
    """Batch upsert config values. None values are skipped."""
    for key, value in updates.items():
        if key not in VALID_KEYS:
            continue
        if value is None or value == KEEP_SENTINEL:
            continue
        await db.execute(
            "INSERT INTO app_config (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
            (key, value),
        )
    await db.commit()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_config_api.py::TestConfigRepository -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/db/schema.sql backend/app/services/config_repository.py backend/tests/test_config_api.py
git commit -m "feat(config): add app_config schema and config repository"
```

---

### Task 2: Backend — Config API Router

**Files:**
- Create: `backend/app/api/v1/config.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_config_api.py` (tests 5–9)

- [ ] **Step 1: Write tests for config API endpoints**

Append to `backend/tests/test_config_api.py`:

```python
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create a TestClient with a temporary database."""
    from app.main import app
    return TestClient(app)


class TestGetConfig:
    """Test GET /config endpoint."""

    def test_get_config_empty_returns_defaults(self, client: TestClient) -> None:
        resp = client.get("/api/v1/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        items = {item["key"]: item["value"] for item in data["items"]}
        assert items["llm_model"] is None
        assert items["anthropic_api_key"] is None

    def test_get_config_masks_sensitive_keys(self, client: TestClient) -> None:
        from app.db.connection import get_db
        from app.services.config_repository import update_config

        # Seed a config value
        async def seed():
            async with get_db() as db:
                await update_config(db, {"anthropic_api_key": "sk-ant-1234567890abcdef"})

        import asyncio
        asyncio.get_event_loop().run_until_complete(seed())

        resp = client.get("/api/v1/config")
        assert resp.status_code == 200
        items = {item["key"]: item["value"] for item in resp.json()["items"]}
        assert items["anthropic_api_key"] == "sk-a...cdef"


class TestUpdateConfig:
    """Test POST /config/update endpoint."""

    def test_update_config_persists_values(self, client: TestClient) -> None:
        resp = client.post("/api/v1/config/update", json={
            "llm_model": "claude-sonnet-4-20250514",
            "llm_max_tokens": 32768,
        })
        assert resp.status_code == 200
        data = resp.json()
        items = {item["key"]: item["value"] for item in data["items"]}
        assert items["llm_model"] == "claude-sonnet-4-20250514"

    def test_update_config_keep_existing_skips(self, client: TestClient) -> None:
        # First, set a value
        client.post("/api/v1/config/update", json={"anthropic_api_key": "sk-original"})

        # Then send KEEP_EXISTING
        resp = client.post("/api/v1/config/update", json={
            "anthropic_api_key": "__KEEP_EXISTING__",
            "llm_model": "new-model",
        })
        assert resp.status_code == 200
        # Verify the original key was preserved
        resp2 = client.get("/api/v1/config")
        items = {item["key"]: item["value"] for item in resp2.json()["items"]}
        # The key should still have the original value (masked)
        assert items["anthropic_api_key"] is not None
        assert items["llm_model"] == "new-model"


class TestConfigRouterRegistered:
    """Test that the config router is registered in main app."""

    def test_config_router_in_app(self) -> None:
        from app.main import create_app
        app = create_app()
        routes = [r.path for r in app.routes]  # type: ignore[attr-defined]
        assert any("config" in r for r in routes)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_config_api.py::TestGetConfig -v`
Expected: FAIL — 404 (no config router registered yet)

- [ ] **Step 3: Implement config.py router**

Create `backend/app/api/v1/config.py`:

```python
"""System configuration API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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
```

- [ ] **Step 4: Register config router in main.py**

In `backend/app/main.py`, add the import after the other router imports (around line 24):

```python
from app.api.v1.config import router as config_router  # noqa: E402
```

Then add the router registration after line 78:

```python
    app.include_router(config_router, prefix="/api/v1")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_config_api.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/v1/config.py backend/app/main.py backend/tests/test_config_api.py
git commit -m "feat(config): add config API router with GET and POST update"
```

---

### Task 3: Backend — Config Test Endpoint

**Files:**
- Modify: `backend/app/api/v1/config.py`
- Modify: `backend/tests/test_config_api.py` (tests 10–11)

- [ ] **Step 1: Write tests for test connection endpoint**

Append to `backend/tests/test_config_api.py`:

```python
class TestConfigTestEndpoint:
    """Test POST /config/test endpoint."""

    def test_test_endpoint_success(self, client: TestClient) -> None:
        """When LLM call succeeds, return success with latency."""
        with patch("app.services.llm.create_llm_client") as mock_create:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=AsyncMock(content="pong"))
            mock_create.return_value = mock_llm

            resp = client.post("/api/v1/config/test")
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["latency_ms"] is not None
            assert data["latency_ms"] >= 0

    def test_test_endpoint_auth_failure(self, client: TestClient) -> None:
        """When LLM returns 401, return error with code."""
        with patch("app.services.llm.create_llm_client") as mock_create:
            mock_create.side_effect = ValueError("ANTHROPIC_API_KEY is not set")

            resp = client.post("/api/v1/config/test")
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is False
            assert data["error_code"] == "config_not_set"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_config_api.py::TestConfigTestEndpoint -v`
Expected: FAIL — 404 (endpoint not implemented yet)

- [ ] **Step 3: Implement test endpoint**

Add to `backend/app/api/v1/config.py` — add imports and a new endpoint:

Add `import time` at the top of the file, and add this endpoint after the `update_config_endpoint`:

```python
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
        resp = await llm.ainvoke("ping")
        latency = int((time.monotonic() - start) * 1000)
        model_name = getattr(llm, "model", None)
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_config_api.py::TestConfigTestEndpoint -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/config.py backend/tests/test_config_api.py
git commit -m "feat(config): add test connection endpoint"
```

---

### Task 4: Backend — Modify LLM Client to Read from DB

**Files:**
- Modify: `backend/app/services/llm.py`
- Modify: `backend/tests/test_config_api.py` (tests 12–13)

- [ ] **Step 1: Write tests for LLM client reading from DB**

Append to `backend/tests/test_config_api.py`:

```python
class TestLLMClientReadsFromDB:
    """Test that create_llm_client reads config from database."""

    async def test_llm_client_reads_from_db(self, db: aiosqlite.Connection) -> None:
        """After saving config to DB, create_llm_client should use those values."""
        from app.services.config_repository import update_config
        from app.services.llm import create_llm_client

        await update_config(db, {
            "anthropic_api_key": "sk-test-key-from-db",
            "llm_model": "claude-custom-model",
        })

        with patch("app.services.llm._read_config_from_db", return_value={
            "anthropic_api_key": "sk-test-key-from-db",
            "llm_model": "claude-custom-model",
            "llm_base_url": None,
            "llm_max_tokens": "65536",
        }):
            client = create_llm_client()
            assert client.model == "claude-custom-model"

    def test_llm_client_raises_when_unconfigured(self) -> None:
        """create_llm_client should raise ValueError when API key is missing."""
        from app.services.llm import create_llm_client

        with patch("app.services.llm._read_config_from_db", return_value={
            "anthropic_api_key": None,
            "llm_model": "claude-sonnet",
            "llm_base_url": None,
            "llm_max_tokens": "65536",
        }):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                create_llm_client()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_config_api.py::TestLLMClientReadsFromDB -v`
Expected: FAIL — `_read_config_from_db` does not exist

- [ ] **Step 3: Modify llm.py to read from ConfigService**

Replace the entire content of `backend/app/services/llm.py`:

```python
"""LLM service for creating configured client instances.

Provides a factory for LangChain-compatible LLM clients and helpers for
extracting plain text from various response formats. Config is read from
the database (app_config table) with fallback to environment variables.
"""

from __future__ import annotations

import os
from typing import Any

from langchain_anthropic import ChatAnthropic
from pydantic import SecretStr


def _read_config_from_db() -> dict[str, str | None]:
    """Read LLM config from the database synchronously.

    This is a synchronous helper that creates a new event loop if needed,
    since create_llm_client may be called from both sync and async contexts.
    """
    import asyncio
    import aiosqlite
    from app.db.connection import DATABASE_PATH

    async def _fetch() -> dict[str, str | None]:
        db = await aiosqlite.connect(DATABASE_PATH)
        db.row_factory = aiosqlite.Row
        try:
            result: dict[str, str | None] = {}
            for key in ("anthropic_api_key", "llm_model", "llm_base_url", "llm_max_tokens"):
                async with db.execute("SELECT value FROM app_config WHERE key = ?", (key,)) as cur:
                    row = await cur.fetchone()
                    result[key] = row[0] if row else None
            return result
        finally:
            await db.close()

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're inside an async context — use a thread to avoid nested loops
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, _fetch()).result()
    else:
        return asyncio.run(_fetch())


def create_llm_client(
    provider: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    streaming: bool = True,
    tags: list[str] | None = None,
) -> Any:
    """Create a configured LangChain LLM client.

    Reads configuration from the database (app_config table). Falls back
    to environment variables if database values are not set.

    Args:
        provider: LLM provider name (default: env ``LLM_PROVIDER`` or ``anthropic``).
        model: Model identifier (default: from DB or env ``LLM_MODEL``).
        base_url: Custom API base URL (default: from DB or env ``LLM_BASE_URL``).
        api_key: API key for authentication (default: from DB or env ``ANTHROPIC_API_KEY``).
        streaming: Whether to enable streaming mode.
        tags: Optional list of tags to attach to LLM invocations.

    Returns:
        A LangChain chat model instance (e.g. ``ChatAnthropic``).

    Raises:
        ValueError: If ``api_key`` is empty or the provider is unsupported.
    """
    db_config = _read_config_from_db()

    actual_provider = provider or os.getenv("LLM_PROVIDER", "anthropic")
    actual_model = model or db_config.get("llm_model") or os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")
    actual_base_url = base_url or db_config.get("llm_base_url") or os.getenv("LLM_BASE_URL")
    actual_api_key = (
        api_key
        or db_config.get("anthropic_api_key")
        or os.getenv("ANTHROPIC_API_KEY", "").strip()
    )
    max_tokens_str = db_config.get("llm_max_tokens") or os.getenv("LLM_MAX_TOKENS", "65536")

    if not actual_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set")

    if actual_provider == "anthropic":
        return ChatAnthropic(  # type: ignore[call-arg]
            model=actual_model,
            api_key=SecretStr(actual_api_key),
            base_url=actual_base_url,
            timeout=float(os.getenv("LLM_TIMEOUT", "86400.0")),
            max_retries=3,
            max_tokens=int(max_tokens_str),
            tags=tags if tags else None,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {actual_provider}")


def extract_content(response: Any) -> str:
    """Extract plain text from an LLM response.

    Handles multiple content shapes: raw strings, lists of strings, and
    LangChain-style dict blocks with ``type`` / ``text`` keys.

    Args:
        response: An LLM response object exposing a ``content`` attribute.

    Returns:
        Concatenated text extracted from the response.
    """
    content = response.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif "text" in block:
                    parts.append(str(block["text"]))
        return "\n".join(parts)
    return str(content)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_config_api.py -v`
Expected: PASS

- [ ] **Step 5: Run full backend test suite to check for regressions**

Run: `cd backend && uv run pytest -v --timeout=30`
Expected: All existing tests still pass

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/llm.py backend/tests/test_config_api.py
git commit -m "feat(config): modify LLM client to read config from database"
```

---

### Task 5: Backend — Add CONFIG_NOT_SET Error Code

**Files:**
- Modify: `backend/app/core/errors.py`

- [ ] **Step 1: Add CONFIG_NOT_SET to ErrorCode enum**

In `backend/app/core/errors.py`, add after `CONTEXT_WINDOW_EXCEEDED`:

```python
    CONFIG_NOT_SET = "config_not_set"
```

- [ ] **Step 2: Run existing error tests**

Run: `cd backend && uv run pytest tests/test_tool_error_handling.py -v`
Expected: PASS (no regressions)

- [ ] **Step 3: Commit**

```bash
git add backend/app/core/errors.py
git commit -m "feat(config): add CONFIG_NOT_SET error code"
```

---

### Task 6: Frontend — Types & API Client

**Files:**
- Modify: `frontend/src/types/index.ts`
- Create: `frontend/src/api/config.ts`

- [ ] **Step 1: Add config types to types/index.ts**

Append to `frontend/src/types/index.ts`:

```typescript
// ── System Config ──
export interface ConfigItem {
  key: string;
  value: string | null;
}

export interface ConfigResponse {
  items: ConfigItem[];
}

export interface UpdateConfigRequest {
  llm_base_url?: string | null;
  anthropic_api_key?: string | null;
  langsmith_api_key?: string | null;
  langsmith_tracing?: boolean | null;
  llm_model?: string | null;
  llm_max_tokens?: number | null;
}

export interface ConfigTestResponse {
  success: boolean;
  model?: string | null;
  latency_ms?: number | null;
  error_code?: string | null;
  message?: string | null;
}
```

- [ ] **Step 2: Create config API client**

Create `frontend/src/api/config.ts`:

```typescript
import client from './client';
import type { ConfigResponse, UpdateConfigRequest, ConfigTestResponse } from '@/types';

export const KEEP_EXISTING = '__KEEP_EXISTING__';

export const configApi = {
  get: () => client.get<ConfigResponse>('/config'),
  update: (data: UpdateConfigRequest) => client.post<ConfigResponse>('/config/update', data),
  test: () => client.post<ConfigTestResponse>('/config/test'),
};
```

- [ ] **Step 3: Run TypeScript type check**

Run: `cd frontend && npm run type-check`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/api/config.ts
git commit -m "feat(config): add frontend types and API client for system config"
```

---

### Task 7: Frontend — SystemLayout Component

**Files:**
- Create: `frontend/src/components/layout/SystemLayout.tsx`

- [ ] **Step 1: Create SystemLayout.tsx**

Create `frontend/src/components/layout/SystemLayout.tsx`:

```tsx
import { Layout, theme } from 'antd';
import { Outlet } from 'react-router-dom';
import IconSidebar from './IconSidebar';

const { Content } = Layout;

const SystemLayout = () => {
  const { token: { colorBgContainer } } = theme.useToken();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <IconSidebar />
      <Layout style={{ marginLeft: 64 }}>
        <Content style={{
          padding: 24,
          background: colorBgContainer,
          height: '100vh',
          overflow: 'auto',
          display: 'flex',
          flexDirection: 'column',
        }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default SystemLayout;
```

Note: This is identical to `DashboardLayout` except `overflow: 'auto'` instead of `overflow: 'hidden'` — the config form needs scrolling.

- [ ] **Step 2: Run TypeScript type check**

Run: `cd frontend && npm run type-check`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/layout/SystemLayout.tsx
git commit -m "feat(config): add SystemLayout component for settings page"
```

---

### Task 8: Frontend — IconSidebar System Settings Button

**Files:**
- Modify: `frontend/src/components/layout/IconSidebar.tsx`

- [ ] **Step 1: Add system settings button to IconSidebar**

In `frontend/src/components/layout/IconSidebar.tsx`, make the following changes:

1. Add `ApiOutlined` to the import from `@ant-design/icons`:

```tsx
import { HomeOutlined, SettingOutlined, ApiOutlined } from '@ant-design/icons';
```

2. Add a `isSystemSettings` variable after the `isSettings` line:

```tsx
const isSystemSettings = location.pathname === '/settings';
```

3. Replace the bottom section (from `<div style={{ flex: 1 }} />` to the end of the flex column) with:

```tsx
        <div style={{ flex: 1 }} />

        <SidebarItem
          icon={<ApiOutlined />}
          label="系统设置"
          active={isSystemSettings}
          onClick={() => navigate('/settings')}
        />

        {settingsPath && (
          <SidebarItem
            icon={<SettingOutlined />}
            label="设置"
            active={isSettings}
            onClick={() => navigate(settingsPath)}
          />
        )}
```

This places the system settings button above the project settings button, both at the bottom of the sidebar.

- [ ] **Step 2: Run TypeScript type check**

Run: `cd frontend && npm run type-check`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/layout/IconSidebar.tsx
git commit -m "feat(config): add system settings button to IconSidebar"
```

---

### Task 9: Frontend — SystemSettings Page

**Files:**
- Create: `frontend/src/pages/settings/SystemSettings.tsx`

- [ ] **Step 1: Create SystemSettings.tsx**

Create `frontend/src/pages/settings/SystemSettings.tsx`:

```tsx
import { useState, useEffect } from 'react';
import { Form, Input, InputNumber, Switch, Button, Space, Spin } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useAppMessage } from '@/hooks/useAppMessage';
import { configApi, KEEP_EXISTING } from '@/api/config';
import PageHeader from '@/components/common/PageHeader';
import PageContainer from '@/components/common/PageContainer';
import type { ConfigResponse } from '@/types';

const SENSITIVE_KEYS = new Set(['anthropic_api_key', 'langsmith_api_key']);

const SystemSettings = () => {
  const navigate = useNavigate();
  const { message } = useAppMessage();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [maskedPlaceholders, setMaskedPlaceholders] = useState<Record<string, string>>({});

  useEffect(() => {
    configApi.get().then(res => {
      const data: ConfigResponse = res.data;
      const formValues: Record<string, unknown> = {};
      const placeholders: Record<string, string> = {};

      for (const item of data.items) {
        if (SENSITIVE_KEYS.has(item.key)) {
          // Sensitive: store masked value as placeholder, leave input empty
          if (item.value) {
            placeholders[item.key] = `已设置 (${item.value})`;
          }
          formValues[item.key] = '';
        } else if (item.key === 'langsmith_tracing') {
          formValues[item.key] = item.value === 'true';
        } else if (item.key === 'llm_max_tokens') {
          formValues[item.key] = item.value ? parseInt(item.value, 10) : undefined;
        } else {
          formValues[item.key] = item.value || '';
        }
      }

      form.setFieldsValue(formValues);
      setMaskedPlaceholders(placeholders);
      setLoading(false);
    }).catch(() => {
      message.error('加载配置失败');
      setLoading(false);
    });
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const values = await form.validateFields();

      // Replace empty sensitive fields with KEEP_EXISTING sentinel
      const payload: Record<string, unknown> = {};
      for (const [key, value] of Object.entries(values)) {
        if (SENSITIVE_KEYS.has(key) && (value === '' || value === undefined)) {
          payload[key] = KEEP_EXISTING;
        } else {
          payload[key] = value;
        }
      }

      await configApi.update(payload);
      message.success('配置已保存');
      setHasChanges(false);

      // Reload to get fresh masked values
      const res = await configApi.get();
      const placeholders: Record<string, string> = {};
      for (const item of res.data.items) {
        if (SENSITIVE_KEYS.has(item.key) && item.value) {
          placeholders[item.key] = `已设置 (${item.value})`;
        }
      }
      setMaskedPlaceholders(placeholders);
      // Clear sensitive fields after save
      for (const key of SENSITIVE_KEYS) {
        form.setFieldValue(key, '');
      }
    } catch {
      // validation error
    }
    setSaving(false);
  };

  const handleTest = async () => {
    setTesting(true);
    try {
      const res = await configApi.test();
      const data = res.data;
      if (data.success) {
        message.success(`连接成功，延迟 ${data.latency_ms} ms`);
      } else {
        message.error(data.message || '连接测试失败');
      }
    } catch {
      message.error('连接测试失败');
    }
    setTesting(false);
  };

  if (loading) {
    return (
      <PageContainer>
        <div style={{ textAlign: 'center', paddingTop: 120 }}>
          <Spin size="large" />
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <PageHeader title="系统设置" subtitle="LLM 配置" />

      <Form
        form={form}
        layout="vertical"
        style={{ maxWidth: 600 }}
        onValuesChange={() => setHasChanges(true)}
      >
        <Form.Item
          name="llm_base_url"
          label="LLM Base URL"
          rules={[
            { required: true, message: '请输入 LLM Base URL' },
            { type: 'url', message: '请输入有效的 URL' },
          ]}
        >
          <Input placeholder="https://api.anthropic.com" />
        </Form.Item>

        <Form.Item
          name="anthropic_api_key"
          label="Anthropic API Key"
        >
          <Input.Password
            placeholder={maskedPlaceholders.anthropic_api_key || '请输入 API Key'}
          />
        </Form.Item>

        <Form.Item name="langsmith_api_key" label="LangSmith API Key">
          <Input.Password
            placeholder={maskedPlaceholders.langsmith_api_key || '可选'}
          />
        </Form.Item>

        <Form.Item
          name="langsmith_tracing"
          label="LangSmith Tracing"
          valuePropName="checked"
        >
          <Switch />
        </Form.Item>

        <Form.Item
          name="llm_model"
          label="LLM Model"
          rules={[{ required: true, message: '请输入模型名称' }]}
        >
          <Input placeholder="claude-sonnet-4-20250514" />
        </Form.Item>

        <Form.Item
          name="llm_max_tokens"
          label="LLM Max Tokens"
          rules={[{ required: true, message: '请输入最大 token 数' }]}
        >
          <InputNumber min={1} style={{ width: '100%' }} placeholder="65536" />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" loading={saving} onClick={handleSave}>
              保存
            </Button>
            <Button
              loading={testing}
              disabled={hasChanges}
              onClick={handleTest}
            >
              测试连接
            </Button>
            <Button onClick={() => navigate('/')}>返回</Button>
          </Space>
        </Form.Item>
      </Form>
    </PageContainer>
  );
};

export default SystemSettings;
```

- [ ] **Step 2: Run TypeScript type check**

Run: `cd frontend && npm run type-check`
Expected: PASS

- [ ] **Step 3: Run lint**

Run: `cd frontend && npm run lint`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/settings/SystemSettings.tsx
git commit -m "feat(config): add SystemSettings page with form and test connection"
```

---

### Task 10: Frontend — Route Registration

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Add /settings route to App.tsx**

In `frontend/src/App.tsx`:

1. Add imports after the existing imports:

```tsx
import SystemLayout from '@/components/layout/SystemLayout';
import SystemSettings from '@/pages/settings/SystemSettings';
```

2. Add a new `<Route>` block between the `DashboardLayout` and `AppLayout` routes:

```tsx
              <Route element={<SystemLayout />}>
                <Route path="/settings" element={<SystemSettings />} />
              </Route>
```

The final route structure should be:

```tsx
            <Routes>
              <Route element={<DashboardLayout />}>
                <Route path="/" element={<Dashboard />} />
              </Route>
              <Route element={<SystemLayout />}>
                <Route path="/settings" element={<SystemSettings />} />
              </Route>
              <Route element={<AppLayout />}>
                {/* ... existing project routes ... */}
              </Route>
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
```

- [ ] **Step 2: Run TypeScript type check**

Run: `cd frontend && npm run type-check`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat(config): register /settings route with SystemLayout"
```

---

### Task 11: Frontend — config_not_set Error Handling

**Files:**
- Modify: `frontend/src/hooks/useProjectChat.ts`

- [ ] **Step 1: Add config_not_set error interception**

In `frontend/src/hooks/useProjectChat.ts`, find the SSE error handling logic (where `error` events are processed). Add a check for `config_not_set` error code.

Look for the pattern where `event.data.error_code` or similar is checked. Add this logic:

```typescript
// In the error event handler, add config_not_set detection:
if (data.error_code === 'config_not_set') {
  // Show a user-friendly message with a link to settings
  const errorEvent: ChatTimelineEvent = {
    type: 'error',
    content: 'LLM 配置不完整，请先前往 [系统设置](/settings) 配置 API 密钥。',
  };
  // Append to timeline
  // ... existing error append logic
}
```

The exact integration point depends on the current SSE error handling structure. The key is:
1. Detect `error_code === 'config_not_set'` in the SSE error event
2. Display a message with a link to `/settings`
3. Stop further processing (don't retry)

- [ ] **Step 2: Run TypeScript type check**

Run: `cd frontend && npm run type-check`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useProjectChat.ts
git commit -m "feat(config): handle config_not_set error with redirect to settings"
```

---

### Task 12: End-to-End Verification

- [ ] **Step 1: Start backend and test API manually**

```bash
cd backend && uv run uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
# Test GET config
curl http://localhost:8000/api/v1/config

# Test POST update
curl -X POST http://localhost:8000/api/v1/config/update \
  -H "Content-Type: application/json" \
  -d '{"llm_model": "claude-sonnet-4-20250514", "anthropic_api_key": "sk-test"}'

# Test GET again (should show masked key)
curl http://localhost:8000/api/v1/config

# Test connection
curl -X POST http://localhost:8000/api/v1/config/test
```

- [ ] **Step 2: Start frontend and test UI**

```bash
cd frontend && npm run dev
```

Navigate to `http://localhost:5173/settings` and verify:
- Page loads with form fields
- API key field shows masked placeholder when configured
- Save button works
- Test connection button works (disabled when form has unsaved changes)
- Back button returns to dashboard

- [ ] **Step 3: Run full test suites**

```bash
cd backend && uv run pytest -v
cd frontend && npm run type-check && npm run lint
```

- [ ] **Step 4: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix(config): address end-to-end verification findings"
```
