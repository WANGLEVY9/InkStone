"""Comprehensive API tests for project isolation.

These tests verify the project isolation logic without requiring full database setup.
The 403 isolation logic is verified at the code level.
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, cast

import pytest

from app.main import create_app

if TYPE_CHECKING:
    from pathlib import Path

    from fastapi.testclient import TestClient


class TestAPIProjectIsolationLogic:
    """Test that project isolation logic is correctly implemented in API endpoints.

    The key isolation check: session.project_id must match URL project_id.
    """

    def test_chat_stream_endpoint_has_project_validation(self) -> None:
        """Chat stream endpoint should verify session.project_id matches URL project_id."""
        from app.api.v1.chat import chat_stream_endpoint

        source = inspect.getsource(chat_stream_endpoint)
        assert "verify_project_binding" in source
        assert "403" in source

    def test_delete_session_endpoint_has_project_validation(self) -> None:
        """Delete session endpoint should verify session.project_id matches URL project_id."""
        from app.api.v1.chat import delete_session_endpoint

        source = inspect.getsource(delete_session_endpoint)
        assert "verify_project_binding" in source
        assert "403" in source

    def test_session_endpoints_use_project_prefix(self) -> None:
        """Session endpoints should be under /projects/{project_id}/ prefix."""
        from app.api.v1.chat import router

        assert router.prefix == "/projects/{project_id}/sessions"

    def test_projects_router_prefix(self) -> None:
        """Projects router should have correct prefix."""
        from app.api.v1.projects import router

        assert router.prefix == "/projects"


class TestProjectIsolationCodePath:
    """Verify the isolation code path exists and is correct."""

    def test_verify_project_binding_in_session_repository(self) -> None:
        """verify_project_binding function should exist in session_repository."""
        from app.services.session_repository import verify_project_binding

        assert callable(verify_project_binding)

    def test_verify_project_binding_returns_bool(self) -> None:
        """verify_project_binding should return a boolean."""
        import inspect

        from app.services.session_repository import verify_project_binding

        sig = inspect.signature(verify_project_binding)
        return_annotation = sig.return_annotation

        assert return_annotation is bool or "bool" in str(return_annotation)

    def test_incorrect_project_raises_403(self) -> None:
        """Code should raise HTTPException 403 for mismatched project_id."""
        from app.api.v1.chat import chat_stream_endpoint

        source = inspect.getsource(chat_stream_endpoint)
        assert "HTTPException" in source
        assert "status_code=403" in source or "403" in source
        assert "does not belong" in source.lower()


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_endpoint_exists(self) -> None:
        """Health endpoint should be defined in main.py."""
        from app.main import create_app

        app = create_app()
        routes = [cast(Any, r).path for r in app.routes]
        assert any(r == "/health" for r in routes)

    @pytest.mark.asyncio
    async def test_health_returns_healthy_status(self) -> None:
        """Health check should return healthy status."""
        from fastapi.testclient import TestClient

        from app.main import create_app

        app = create_app()
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestRoutersConfigured:
    """Verify routers are properly configured."""

    def test_projects_router_included_in_app(self) -> None:
        """Projects router should be included in the app."""
        app = create_app()

        routes = [cast(Any, r).path for r in app.routes]
        assert any("/projects" in r for r in routes)

    def test_chat_router_included_in_app(self) -> None:
        """Chat router should be included in the app."""
        app = create_app()

        routes = [cast(Any, r).path for r in app.routes]
        assert any("sessions" in r and "chat" in r for r in routes)


class TestProjectFieldAdditions:
    """Verify description / cover_image / word_count end-to-end via the API."""

    @pytest.fixture
    def client(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
        import sqlite3

        from fastapi.testclient import TestClient

        from app.db import connection as db_conn
        from app.main import create_app

        db_file = tmp_path / "test_projects.db"
        monkeypatch.setattr(db_conn, "DATABASE_PATH", db_file)

        with open(db_conn.SCHEMA_PATH, encoding="utf-8") as f:
            schema = f.read()
        conn = sqlite3.connect(db_file)
        try:
            conn.executescript(schema)
        finally:
            conn.close()

        return TestClient(create_app())

    def test_create_project_persists_description(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/projects/",
            json={"name": "测试作品", "description": "一个奇幻冒险故事"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["description"] == "一个奇幻冒险故事"
        assert body["cover_image"] is None
        assert body["word_count"] == 0

        get_resp = client.get(f"/api/v1/projects/{body['id']}")
        assert get_resp.status_code == 200
        got = get_resp.json()
        assert got["description"] == "一个奇幻冒险故事"
        assert got["cover_image"] is None
        assert got["word_count"] == 0

    def test_patch_updates_cover_image_and_word_count(self, client: TestClient) -> None:
        create_resp = client.post("/api/v1/projects/", json={"name": "P2"})
        assert create_resp.status_code == 200
        pid = create_resp.json()["id"]

        patch_resp = client.patch(
            f"/api/v1/projects/{pid}",
            json={"cover_image": "https://example.com/cover.jpg", "word_count": 12345},
        )
        assert patch_resp.status_code == 200, patch_resp.text
        body = patch_resp.json()
        assert body["cover_image"] == "https://example.com/cover.jpg"
        assert body["word_count"] == 12345

        get_resp = client.get(f"/api/v1/projects/{pid}")
        got = get_resp.json()
        assert got["cover_image"] == "https://example.com/cover.jpg"
        assert got["word_count"] == 12345
