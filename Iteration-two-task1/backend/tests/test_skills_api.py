"""Tests for Skills API endpoints."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create a TestClient with a temporary skills directory."""
    from app.api.v1.skills import skill_service as svc

    monkeypatch.setattr(svc, "skills_dir", tmp_path)
    from app.main import app

    return TestClient(app)


class TestListSkills:
    """Test GET /skills endpoint."""

    def test_list_empty(self, client: TestClient) -> None:
        """Empty skills directory returns an empty list."""
        resp = client.get("/api/v1/skills")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_with_domain_filter(self, client: TestClient) -> None:
        """Domain filter returns only matching skills."""
        # Create two skills with different domains
        client.post(
            "/api/v1/skills",
            json={"name": "skill-a", "description": "desc a", "content": "body", "domain": "chapter"},
        )
        client.post(
            "/api/v1/skills",
            json={"name": "skill-b", "description": "desc b", "content": "body", "domain": "plot"},
        )

        resp = client.get("/api/v1/skills", params={"domain": "chapter"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "skill-a"

    def test_list_returns_no_content_field(self, client: TestClient) -> None:
        """List response should not include content field."""
        client.post(
            "/api/v1/skills",
            json={"name": "skill-c", "description": "desc", "content": "secret body"},
        )

        resp = client.get("/api/v1/skills")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert "content" not in data[0]


class TestGetSkill:
    """Test GET /skills/{skill_name} endpoint."""

    def test_get_existing(self, client: TestClient) -> None:
        """Get an existing skill returns 200 with content."""
        client.post(
            "/api/v1/skills",
            json={"name": "my-skill", "description": "a skill", "content": "hello world"},
        )

        resp = client.get("/api/v1/skills/my-skill")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "my-skill"
        assert data["description"] == "a skill"
        assert data["content"] == "hello world"

    def test_get_nonexistent(self, client: TestClient) -> None:
        """Get a nonexistent skill returns 404."""
        resp = client.get("/api/v1/skills/nope")
        assert resp.status_code == 404


class TestCreateSkill:
    """Test POST /skills endpoint."""

    def test_create_returns_201(self, client: TestClient) -> None:
        """Creating a new skill returns 201 with full detail."""
        payload = {
            "name": "new-skill",
            "description": "a new skill",
            "content": "prompt content",
            "domain": "chapter",
            "tags": ["writing", "prose"],
        }
        resp = client.post("/api/v1/skills", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "new-skill"
        assert data["description"] == "a new skill"
        assert data["content"] == "prompt content"
        assert data["domain"] == "chapter"
        assert data["tags"] == ["writing", "prose"]

    def test_create_duplicate_returns_409(self, client: TestClient) -> None:
        """Creating a skill with a duplicate name returns 409."""
        payload = {
            "name": "dup-skill",
            "description": "first",
            "content": "body",
        }
        resp1 = client.post("/api/v1/skills", json=payload)
        assert resp1.status_code == 201

        resp2 = client.post("/api/v1/skills", json=payload)
        assert resp2.status_code == 409


class TestUpdateSkill:
    """Test POST /skills/{skill_name}/update endpoint."""

    def test_update_returns_200(self, client: TestClient) -> None:
        """Updating an existing skill returns 200 with updated fields."""
        client.post(
            "/api/v1/skills",
            json={"name": "upd-skill", "description": "old", "content": "old body"},
        )

        resp = client.post(
            "/api/v1/skills/upd-skill/update",
            json={"description": "new description", "content": "new body"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "upd-skill"
        assert data["description"] == "new description"
        assert data["content"] == "new body"

    def test_update_nonexistent_returns_404(self, client: TestClient) -> None:
        """Updating a nonexistent skill returns 404."""
        resp = client.post(
            "/api/v1/skills/nope/update",
            json={"description": "new"},
        )
        assert resp.status_code == 404


class TestDeleteSkill:
    """Test POST /skills/{skill_name}/delete endpoint."""

    def test_delete_returns_200(self, client: TestClient) -> None:
        """Deleting an existing skill returns 200."""
        client.post(
            "/api/v1/skills",
            json={"name": "del-skill", "description": "to delete", "content": "body"},
        )

        resp = client.post("/api/v1/skills/del-skill/delete")
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] is True

    def test_delete_nonexistent_returns_404(self, client: TestClient) -> None:
        """Deleting a nonexistent skill returns 404."""
        resp = client.post("/api/v1/skills/nope/delete")
        assert resp.status_code == 404


class TestSkillRouterRegistered:
    """Test that the skill router is registered in main app."""

    def test_skill_router_in_app(self) -> None:
        """Skill router should be included in the app."""
        from app.main import create_app

        app = create_app()
        routes = [r.path for r in app.routes]  # type: ignore[attr-defined]
        assert any("skills" in r for r in routes)
