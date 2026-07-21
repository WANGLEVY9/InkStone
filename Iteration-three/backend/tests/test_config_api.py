"""Tests for config repository and API endpoints."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

import aiosqlite
import pytest
from fastapi.testclient import TestClient

from app.services.config_repository import mask_value


@pytest.fixture()
async def db(tmp_path: Path) -> AsyncGenerator[aiosqlite.Connection]:
    """Create an in-memory-like SQLite database with the schema applied."""
    db_path = tmp_path / "test.db"
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    schema = Path(__file__).parent.parent / "app" / "db" / "schema.sql"
    await db.executescript(schema.read_text())
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
        from app.services.config_repository import get_config, update_config

        await update_config(db, {"anthropic_api_key": "sk-test123", "llm_model": "claude-sonnet"})
        val = await get_config(db, "anthropic_api_key")
        assert val == "sk-test123"
        val2 = await get_config(db, "llm_model")
        assert val2 == "claude-sonnet"

    async def test_get_all_config(self, db: aiosqlite.Connection) -> None:
        from app.services.config_repository import get_all_config, update_config

        await update_config(db, {"llm_model": "claude-sonnet", "llm_max_tokens": "65536"})
        result = await get_all_config(db)
        assert result["llm_model"] == "claude-sonnet"
        assert result["llm_max_tokens"] == "65536"

    async def test_update_config_skips_none_values(self, db: aiosqlite.Connection) -> None:
        from app.services.config_repository import get_config, update_config

        await update_config(db, {"llm_model": "old-model"})
        await update_config(db, {"llm_model": None, "llm_max_tokens": "1024"})
        assert await get_config(db, "llm_model") == "old-model"
        assert await get_config(db, "llm_max_tokens") == "1024"

    async def test_update_config_keep_sentinel_preserves_value(self, db: aiosqlite.Connection) -> None:
        from app.services.config_repository import get_config, update_config

        await update_config(db, {"llm_model": "original-value"})
        await update_config(db, {"llm_model": "__KEEP_EXISTING__"})
        assert await get_config(db, "llm_model") == "original-value"

    async def test_update_config_rejects_invalid_keys(self, db: aiosqlite.Connection) -> None:
        from app.services.config_repository import get_all_config, update_config

        await update_config(db, {"not_a_real_key": "value"})
        result = await get_all_config(db)
        assert "not_a_real_key" not in result

    async def test_update_config_partial(self, db: aiosqlite.Connection) -> None:
        """Partial update only changes specified fields."""
        from app.services.config_repository import get_config, update_config

        await update_config(db, {"llm_model": "model-a", "llm_max_tokens": "1024"})
        await update_config(db, {"llm_model": "model-b"})
        assert await get_config(db, "llm_model") == "model-b"
        assert await get_config(db, "llm_max_tokens") == "1024"


class TestMaskValue:
    """Tests for the mask_value helper."""

    def test_sensitive_key_long_value(self) -> None:
        assert mask_value("anthropic_api_key", "sk-ant-1234567890abcdef") == "sk-a...cdef"

    def test_sensitive_key_short_value(self) -> None:
        assert mask_value("anthropic_api_key", "short") == "***"

    def test_non_sensitive_key_passthrough(self) -> None:
        assert mask_value("llm_model", "claude-sonnet") == "claude-sonnet"

    def test_none_input(self) -> None:
        assert mask_value("anthropic_api_key", None) is None


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create a TestClient backed by a temporary database."""
    import sqlite3

    from app.db import connection as db_conn
    from app.main import create_app

    db_file = tmp_path / "test_config.db"
    monkeypatch.setattr(db_conn, "DATABASE_PATH", db_file)
    # Reset cached connection so _get_global_db() picks up the new path
    monkeypatch.setattr(db_conn, "_db_connection", None)

    with open(db_conn.SCHEMA_PATH, encoding="utf-8") as f:
        schema = f.read()
    conn = sqlite3.connect(db_file)
    try:
        conn.executescript(schema)
    finally:
        conn.close()

    return TestClient(create_app())


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

    async def test_get_config_masks_sensitive_keys(self, client: TestClient) -> None:
        from app.db.connection import get_db
        from app.services.config_repository import update_config

        # Seed a config value
        async with get_db() as db:
            await update_config(db, {"anthropic_api_key": "sk-ant-1234567890abcdef"})

        resp = client.get("/api/v1/config")
        assert resp.status_code == 200
        items = {item["key"]: item["value"] for item in resp.json()["items"]}
        assert items["anthropic_api_key"] == "sk-a...cdef"


class TestUpdateConfig:
    """Test POST /config/update endpoint."""

    def test_update_config_persists_values(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/config/update",
            json={
                "llm_model": "claude-sonnet-4-20250514",
                "llm_max_tokens": 32768,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        items = {item["key"]: item["value"] for item in data["items"]}
        assert items["llm_model"] == "claude-sonnet-4-20250514"

    def test_update_config_keep_existing_skips(self, client: TestClient) -> None:
        # First, set a value
        client.post("/api/v1/config/update", json={"anthropic_api_key": "sk-original"})

        # Then send KEEP_EXISTING
        resp = client.post(
            "/api/v1/config/update",
            json={
                "anthropic_api_key": "__KEEP_EXISTING__",
                "llm_model": "new-model",
            },
        )
        assert resp.status_code == 200
        # Verify the original key was preserved
        resp2 = client.get("/api/v1/config")
        items = {item["key"]: item["value"] for item in resp2.json()["items"]}
        # The key should still have the original value (masked)
        assert items["anthropic_api_key"] is not None
        assert items["llm_model"] == "new-model"


class TestConfigTestEndpoint:
    """Test POST /config/test endpoint."""

    def test_test_endpoint_success(self, client: TestClient) -> None:
        """When LLM call succeeds, return success with latency."""
        from unittest.mock import AsyncMock, MagicMock, patch

        with patch("app.services.llm.create_llm_client") as mock_create:
            mock_llm = MagicMock()
            bound_llm = AsyncMock()
            bound_llm.ainvoke = AsyncMock(return_value=AsyncMock(content="pong"))
            mock_llm.bind.return_value = bound_llm
            mock_create.return_value = mock_llm

            resp = client.post("/api/v1/config/test")
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["latency_ms"] is not None
            assert data["latency_ms"] >= 0

    def test_test_endpoint_auth_failure(self, client: TestClient) -> None:
        """When LLM returns 401, return error with code."""
        from unittest.mock import patch

        with patch("app.services.llm.create_llm_client") as mock_create:
            mock_create.side_effect = ValueError("ANTHROPIC_API_KEY is not set")

            resp = client.post("/api/v1/config/test")
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is False
            assert data["error_code"] == "config_not_set"


class TestConfigRouterRegistered:
    """Test that the config router is registered in main app."""

    def test_config_router_in_app(self) -> None:
        from app.main import create_app

        app = create_app()
        routes = [r.path for r in app.routes]  # type: ignore[attr-defined]
        assert any("config" in r for r in routes)


class TestLLMClientReadsFromDB:
    """Test that create_llm_client reads config from database."""

    async def test_llm_client_reads_from_db(self, db: aiosqlite.Connection) -> None:
        """After saving config to DB, create_llm_client should use those values."""
        from unittest.mock import patch

        from app.services.config_repository import update_config
        from app.services.llm import create_llm_client

        await update_config(
            db,
            {
                "anthropic_api_key": "sk-test-key-from-db",
                "llm_model": "claude-custom-model",
            },
        )

        with patch(
            "app.services.llm._read_config_from_db",
            return_value={
                "anthropic_api_key": "sk-test-key-from-db",
                "llm_model": "claude-custom-model",
                "llm_base_url": None,
                "llm_max_tokens": "65536",
            },
        ):
            client = create_llm_client()
            assert client.model == "claude-custom-model"

    def test_llm_client_raises_when_unconfigured(self) -> None:
        """create_llm_client should raise ValueError when API key is missing."""
        from unittest.mock import patch

        from app.services.llm import create_llm_client

        with (
            patch(
                "app.services.llm._read_config_from_db",
                return_value={
                    "anthropic_api_key": None,
                    "llm_model": "claude-sonnet",
                    "llm_base_url": None,
                    "llm_max_tokens": "65536",
                },
            ),
            patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}, clear=False),
        ):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                create_llm_client()
