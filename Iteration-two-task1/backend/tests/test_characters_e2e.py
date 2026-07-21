"""E2E tests for the characters API using FastAPI TestClient."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_characters_full_lifecycle() -> None:
    """Full lifecycle: create project, list/create/get/update/delete character, 404."""
    from app.main import create_app

    app = create_app()
    with TestClient(app) as c:
        r = c.post("/api/v1/projects/", json={"name": "e2e-character-test"})
        assert r.status_code == 200, r.text
        pid = r.json()["id"]

        try:
            r = c.get(f"/api/v1/projects/{pid}/characters/")
            assert r.status_code == 200 and r.json() == []

            r = c.post(
                f"/api/v1/projects/{pid}/characters/",
                json={"name": "alice", "content": "# profile\n19 yo", "summary": "protag"},
            )
            assert r.status_code == 200, r.text
            cid = r.json()["id"]

            r = c.get(f"/api/v1/projects/{pid}/characters/{cid}")
            assert r.status_code == 200
            assert r.json()["content"].startswith("# profile")

            r = c.post(
                f"/api/v1/projects/{pid}/characters/{cid}/update",
                json={"summary": "protag-updated"},
            )
            assert r.status_code == 200
            assert r.json()["summary"] == "protag-updated"

            r = c.post(f"/api/v1/projects/{pid}/characters/{cid}/delete")
            assert r.status_code == 200
            assert r.json()["status"] == "deleted"

            r = c.get(f"/api/v1/projects/{pid}/characters/nonexistent")
            assert r.status_code == 404
        finally:
            c.delete(f"/api/v1/projects/{pid}")
