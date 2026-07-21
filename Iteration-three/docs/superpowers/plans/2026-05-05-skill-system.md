# Skill System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a global, prompt-driven Skill system that lets users define specialized prompts (writing styles, genre conventions, narrative techniques) and have agents load them on-demand via LangChain's progressive disclosure pattern.

**Architecture:** Skills are markdown files with YAML frontmatter stored in `backend/data/skills/`. A `SkillService` handles CRUD. A `SkillMiddleware` (LangChain `AgentMiddleware`) dynamically injects available skill names/descriptions into the system prompt at each model call, and a `load_skill` tool lets agents load full skill content on-demand. Both orchestrator and sub-agents get domain-scoped middleware.

**Tech Stack:** Python 3.13, FastAPI, LangChain (`create_agent`, `AgentMiddleware`), PyYAML, Pytest

**Spec:** `docs/superpowers/specs/2026-05-05-skill-system-design.md`

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `backend/pyproject.toml` | Add `pyyaml` dependency |
| Create | `backend/app/services/skill.py` | SkillService: CRUD for skill files, frontmatter parsing |
| Create | `backend/tests/test_skill_service.py` | Unit tests for SkillService |
| Create | `backend/app/api/v1/skills.py` | FastAPI router: 5 endpoints for skill CRUD |
| Create | `backend/tests/test_skills_api.py` | API tests for skill endpoints |
| Modify | `backend/app/main.py` | Register skills router |
| Create | `backend/app/core/agent/skill_middleware.py` | `create_load_skill_tool` + `SkillMiddleware` class |
| Create | `backend/tests/test_skill_middleware.py` | Tests for middleware injection and tool |
| Modify | `backend/app/core/graph/builder.py` | Add SkillMiddleware to orchestrator |
| Modify | `backend/app/core/agent/langchain_subagents.py` | Add domain SkillMiddleware to all 5 sub-agents |
| Create | `backend/data/skills/wuxia-writing.md` | Example skill file |
| Create | `backend/data/skills/noir-detective.md` | Example skill file |

---

### Task 1: Add pyyaml Dependency

**Files:**
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Add pyyaml to dependencies**

In `backend/pyproject.toml`, add `pyyaml` to the `dependencies` list:

```toml
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.7.0",
    "langchain>=1.0.0",
    "langchain-core>=0.3.0",
    "langchain-anthropic>=0.3.0",
    "langgraph>=0.4.0",
    "aiosqlite>=0.20.0",
    "aiofiles>=23.0.0",
    "python-dotenv>=1.0.0",
    "langgraph-checkpoint-sqlite>=3.0.3",
    "pyyaml>=6.0",
]
```

- [ ] **Step 2: Sync dependencies**

Run from `backend/`:

```bash
uv sync
```

Expected: pyyaml installed successfully.

- [ ] **Step 3: Verify import**

```bash
cd backend && python -c "import yaml; print(yaml.__version__)"
```

Expected: prints version (e.g., `6.0.3`).

- [ ] **Step 4: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock
git commit -m "build: add pyyaml as explicit dependency"
```

---

### Task 2: SkillService

**Files:**
- Create: `backend/app/services/skill.py`
- Create: `backend/tests/test_skill_service.py`

- [ ] **Step 1: Write failing tests for SkillService**

Create `backend/tests/test_skill_service.py`:

```python
"""Tests for SkillService — file-based skill CRUD with YAML frontmatter."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from app.services.skill import SkillService


@pytest.fixture()
def skill_dir(tmp_path: Path) -> Path:
    """Create a temporary skills directory."""
    return tmp_path / "skills"


@pytest.fixture()
def service(skill_dir: Path) -> SkillService:
    """Create a SkillService with a temporary directory."""
    return SkillService(skills_dir=skill_dir)


class TestParseFrontmatter:
    """Tests for YAML frontmatter parsing."""

    def test_parse_valid_frontmatter(self, service: SkillService) -> None:
        content = "---\nname: test-skill\ndescription: A test skill\ndomain: chapter\ntags: [test]\n---\n\nBody content here."
        result = service._parse_file("test-skill.md", content)
        assert result is not None
        assert result["name"] == "test-skill"
        assert result["description"] == "A test skill"
        assert result["domain"] == "chapter"
        assert result["tags"] == ["test"]
        assert result["content"] == "Body content here."

    def test_parse_no_frontmatter(self, service: SkillService) -> None:
        content = "Just some content without frontmatter."
        result = service._parse_file("bad.md", content)
        assert result is None

    def test_parse_missing_name(self, service: SkillService) -> None:
        content = "---\ndescription: No name\n---\n\nBody."
        result = service._parse_file("noname.md", content)
        assert result is None

    def test_parse_missing_description(self, service: SkillService) -> None:
        content = "---\nname: no-desc\n---\n\nBody."
        result = service._parse_file("nodesc.md", content)
        assert result is None

    def test_parse_no_domain_is_global(self, service: SkillService) -> None:
        content = "---\nname: global-skill\ndescription: Global\n---\n\nBody."
        result = service._parse_file("global.md", content)
        assert result is not None
        assert result["domain"] is None

    def test_parse_empty_tags(self, service: SkillService) -> None:
        content = "---\nname: no-tags\ndescription: No tags\n---\n\nBody."
        result = service._parse_file("notags.md", content)
        assert result is not None
        assert result["tags"] == []


class TestListSkills:
    """Tests for listing skills with domain filtering."""

    def test_list_empty(self, service: SkillService) -> None:
        assert service.list_skills() == []

    def test_list_global_only(self, service: SkillService, skill_dir: Path) -> None:
        skill_dir.mkdir(parents=True)
        (skill_dir / "global.md").write_text(
            "---\nname: global-skill\ndescription: Global\n---\n\nBody.",
            encoding="utf-8",
        )
        (skill_dir / "domain.md").write_text(
            "---\nname: domain-skill\ndescription: Domain\ndomain: chapter\n---\n\nBody.",
            encoding="utf-8",
        )
        result = service.list_skills()
        assert len(result) == 1
        assert result[0]["name"] == "global-skill"

    def test_list_by_domain(self, service: SkillService, skill_dir: Path) -> None:
        skill_dir.mkdir(parents=True)
        (skill_dir / "ch1.md").write_text(
            "---\nname: ch-skill\ndescription: Chapter\ndomain: chapter\n---\n\nBody.",
            encoding="utf-8",
        )
        (skill_dir / "w1.md").write_text(
            "---\nname: world-skill\ndescription: World\ndomain: world\n---\n\nBody.",
            encoding="utf-8",
        )
        result = service.list_skills(domain="chapter")
        assert len(result) == 1
        assert result[0]["name"] == "ch-skill"

    def test_list_ignores_invalid_files(self, service: SkillService, skill_dir: Path) -> None:
        skill_dir.mkdir(parents=True)
        (skill_dir / "bad.md").write_text("no frontmatter here", encoding="utf-8")
        (skill_dir / "good.md").write_text(
            "---\nname: good\ndescription: Good\n---\n\nBody.",
            encoding="utf-8",
        )
        result = service.list_skills()
        assert len(result) == 1
        assert result[0]["name"] == "good"


class TestGetSkill:
    """Tests for getting a single skill."""

    def test_get_existing(self, service: SkillService, skill_dir: Path) -> None:
        skill_dir.mkdir(parents=True)
        (skill_dir / "my-skill.md").write_text(
            "---\nname: my-skill\ndescription: My skill\n---\n\nFull body.",
            encoding="utf-8",
        )
        result = service.get_skill("my-skill")
        assert result is not None
        assert result["name"] == "my-skill"
        assert result["content"] == "Full body."

    def test_get_nonexistent(self, service: SkillService) -> None:
        assert service.get_skill("nope") is None


class TestCreateSkill:
    """Tests for creating skill files."""

    def test_create_new(self, service: SkillService, skill_dir: Path) -> None:
        result = service.create_skill(
            name="new-skill",
            description="A new skill",
            content="Skill body content.",
            domain="chapter",
            tags=["test"],
        )
        assert result["name"] == "new-skill"
        assert result["description"] == "A new skill"
        assert result["domain"] == "chapter"
        assert result["tags"] == ["test"]
        assert result["content"] == "Skill body content."
        # Verify file exists
        assert (skill_dir / "new-skill.md").exists()

    def test_create_global_skill(self, service: SkillService) -> None:
        result = service.create_skill(
            name="global",
            description="Global skill",
            content="Body.",
        )
        assert result["domain"] is None
        assert result["tags"] == []

    def test_create_duplicate_raises(self, service: SkillService) -> None:
        service.create_skill(name="dup", description="First", content="Body.")
        with pytest.raises(ValueError, match="already exists"):
            service.create_skill(name="dup", description="Second", content="Body.")


class TestUpdateSkill:
    """Tests for updating skill files."""

    def test_update_description(self, service: SkillService) -> None:
        service.create_skill(name="upd", description="Old", content="Body.")
        result = service.update_skill("upd", description="New description")
        assert result is not None
        assert result["description"] == "New description"

    def test_update_content(self, service: SkillService) -> None:
        service.create_skill(name="upd2", description="D", content="Old body.")
        result = service.update_skill("upd2", content="New body.")
        assert result is not None
        assert result["content"] == "New body."

    def test_update_nonexistent(self, service: SkillService) -> None:
        assert service.update_skill("nope", description="X") is None


class TestDeleteSkill:
    """Tests for deleting skill files."""

    def test_delete_existing(self, service: SkillService, skill_dir: Path) -> None:
        service.create_skill(name="del", description="Delete me", content="Body.")
        assert service.delete_skill("del") is True
        assert not (skill_dir / "del.md").exists()

    def test_delete_nonexistent(self, service: SkillService) -> None:
        assert service.delete_skill("nope") is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run from `backend/`:

```bash
uv run pytest tests/test_skill_service.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.skill'`.

- [ ] **Step 3: Implement SkillService**

Create `backend/app/services/skill.py`:

```python
"""SkillService — file-based skill CRUD with YAML frontmatter parsing.

Skills are markdown files with YAML frontmatter stored in a directory.
Each file represents one skill with metadata (name, description, domain, tags)
and content (the markdown body).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class SkillService:
    """Manages skill files stored as markdown with YAML frontmatter."""

    def __init__(self, skills_dir: Path | None = None) -> None:
        self.skills_dir = skills_dir or Path(__file__).resolve().parents[3] / "data" / "skills"

    def _parse_file(self, filename: str, raw: str) -> dict[str, Any] | None:
        """Parse a markdown file with YAML frontmatter.

        Returns parsed skill dict or None if the file is invalid.
        """
        if not raw.startswith("---"):
            return None

        # Split frontmatter from body
        parts = raw.split("---", 2)
        if len(parts) < 3:
            return None

        frontmatter_str = parts[1].strip()
        body = parts[2].strip()

        try:
            meta = yaml.safe_load(frontmatter_str)
        except yaml.YAMLError:
            return None

        if not isinstance(meta, dict):
            return None

        name = meta.get("name")
        description = meta.get("description")
        if not name or not description:
            return None

        return {
            "name": str(name),
            "description": str(description),
            "domain": meta.get("domain") or None,
            "tags": meta.get("tags") or [],
            "content": body,
        }

    def _read_skill_file(self, path: Path) -> dict[str, Any] | None:
        """Read and parse a single skill file."""
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None
        return self._parse_file(path.name, raw)

    def list_skills(self, domain: str | None = None) -> list[dict[str, Any]]:
        """List skills, optionally filtered by domain.

        If domain is None, returns only global skills (domain is empty/None).
        If domain is set, returns skills matching that domain.
        """
        if not self.skills_dir.is_dir():
            return []

        results: list[dict[str, Any]] = []
        for path in sorted(self.skills_dir.glob("*.md")):
            skill = self._read_skill_file(path)
            if skill is None:
                continue
            if domain is None:
                # Global skills: domain is None or empty
                if skill["domain"] is None:
                    results.append(skill)
            else:
                if skill["domain"] == domain:
                    results.append(skill)
        return results

    def get_skill(self, name: str) -> dict[str, Any] | None:
        """Get a single skill by name."""
        path = self.skills_dir / f"{name}.md"
        if not path.exists():
            return None
        return self._read_skill_file(path)

    def create_skill(
        self,
        name: str,
        description: str,
        content: str,
        domain: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new skill file.

        Raises ValueError if a skill with the same name already exists.
        """
        path = self.skills_dir / f"{name}.md"
        if path.exists():
            raise ValueError(f"Skill '{name}' already exists")

        self.skills_dir.mkdir(parents=True, exist_ok=True)

        frontmatter: dict[str, Any] = {
            "name": name,
            "description": description,
        }
        if domain:
            frontmatter["domain"] = domain
        if tags:
            frontmatter["tags"] = tags

        file_content = f"---\n{yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)}---\n\n{content}"
        path.write_text(file_content, encoding="utf-8")

        return {
            "name": name,
            "description": description,
            "domain": domain,
            "tags": tags or [],
            "content": content,
        }

    def update_skill(self, name: str, **kwargs: Any) -> dict[str, Any] | None:
        """Update an existing skill file.

        Supported kwargs: description, content, domain, tags.
        Returns the updated skill dict or None if not found.
        """
        existing = self.get_skill(name)
        if existing is None:
            return None

        # Merge updates
        description = kwargs.get("description", existing["description"])
        content = kwargs.get("content", existing["content"])
        domain = kwargs.get("domain", existing["domain"])
        tags = kwargs.get("tags", existing["tags"])

        frontmatter: dict[str, Any] = {
            "name": name,
            "description": description,
        }
        if domain:
            frontmatter["domain"] = domain
        if tags:
            frontmatter["tags"] = tags

        path = self.skills_dir / f"{name}.md"
        file_content = f"---\n{yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)}---\n\n{content}"
        path.write_text(file_content, encoding="utf-8")

        return {
            "name": name,
            "description": description,
            "domain": domain,
            "tags": tags or [],
            "content": content,
        }

    def delete_skill(self, name: str) -> bool:
        """Delete a skill file. Returns True if deleted, False if not found."""
        path = self.skills_dir / f"{name}.md"
        if not path.exists():
            return False
        path.unlink()
        return True
```

- [ ] **Step 4: Run tests to verify they pass**

Run from `backend/`:

```bash
uv run pytest tests/test_skill_service.py -v
```

Expected: All 15 tests PASS.

- [ ] **Step 5: Run type check**

```bash
cd backend && uv run mypy app/services/skill.py
```

Expected: Success (no errors).

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/skill.py backend/tests/test_skill_service.py
git commit -m "feat(skill): add SkillService with frontmatter parsing and CRUD"
```

---

### Task 3: Skill API Routes

**Files:**
- Create: `backend/app/api/v1/skills.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_skills_api.py`

- [ ] **Step 1: Write failing API tests**

Create `backend/tests/test_skills_api.py`:

```python
"""Tests for the Skill API endpoints."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def skill_dir(tmp_path: Path) -> Path:
    """Temporary skills directory."""
    return tmp_path / "skills"


@pytest.fixture()
def client(skill_dir: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create a TestClient with a temporary skills directory."""
    from app.api.v1.skills import skill_service as svc

    monkeypatch.setattr(svc, "skills_dir", skill_dir)
    from app.main import app

    return TestClient(app)


class TestListSkills:
    def test_list_empty(self, client: TestClient) -> None:
        resp = client.get("/api/v1/skills")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_with_domain_filter(self, client: TestClient, skill_dir: Path) -> None:
        skill_dir.mkdir(parents=True)
        (skill_dir / "ch.md").write_text(
            "---\nname: ch\ndescription: Chapter skill\ndomain: chapter\n---\n\nBody.",
            encoding="utf-8",
        )
        (skill_dir / "g.md").write_text(
            "---\nname: g\ndescription: Global\n---\n\nBody.",
            encoding="utf-8",
        )
        resp = client.get("/api/v1/skills?domain=chapter")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "ch"


class TestGetSkill:
    def test_get_existing(self, client: TestClient, skill_dir: Path) -> None:
        skill_dir.mkdir(parents=True)
        (skill_dir / "my-skill.md").write_text(
            "---\nname: my-skill\ndescription: Test\n---\n\nBody.",
            encoding="utf-8",
        )
        resp = client.get("/api/v1/skills/my-skill")
        assert resp.status_code == 200
        assert resp.json()["name"] == "my-skill"

    def test_get_not_found(self, client: TestClient) -> None:
        resp = client.get("/api/v1/skills/nonexistent")
        assert resp.status_code == 404


class TestCreateSkill:
    def test_create(self, client: TestClient) -> None:
        resp = client.post("/api/v1/skills", json={
            "name": "new-skill",
            "description": "A new skill",
            "content": "Body content.",
            "domain": "chapter",
            "tags": ["test"],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "new-skill"
        assert data["domain"] == "chapter"

    def test_create_duplicate(self, client: TestClient) -> None:
        client.post("/api/v1/skills", json={
            "name": "dup",
            "description": "First",
            "content": "Body.",
        })
        resp = client.post("/api/v1/skills", json={
            "name": "dup",
            "description": "Second",
            "content": "Body.",
        })
        assert resp.status_code == 409


class TestUpdateSkill:
    def test_update(self, client: TestClient) -> None:
        client.post("/api/v1/skills", json={
            "name": "upd",
            "description": "Old",
            "content": "Body.",
        })
        resp = client.post("/api/v1/skills/upd/update", json={
            "description": "New description",
        })
        assert resp.status_code == 200
        assert resp.json()["description"] == "New description"

    def test_update_not_found(self, client: TestClient) -> None:
        resp = client.post("/api/v1/skills/nope/update", json={
            "description": "X",
        })
        assert resp.status_code == 404


class TestDeleteSkill:
    def test_delete(self, client: TestClient) -> None:
        client.post("/api/v1/skills", json={
            "name": "del",
            "description": "Delete me",
            "content": "Body.",
        })
        resp = client.post("/api/v1/skills/del/delete")
        assert resp.status_code == 200
        # Verify deleted
        resp = client.get("/api/v1/skills/del")
        assert resp.status_code == 404

    def test_delete_not_found(self, client: TestClient) -> None:
        resp = client.post("/api/v1/skills/nope/delete")
        assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run from `backend/`:

```bash
uv run pytest tests/test_skills_api.py -v
```

Expected: FAIL (import error or 404s since routes don't exist yet).

- [ ] **Step 3: Create Pydantic models and API router**

Create `backend/app/api/v1/skills.py`:

```python
"""Skill CRUD API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.skill import SkillService

router = APIRouter(prefix="/skills", tags=["skills"])
skill_service = SkillService()


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------


class SkillCreate(BaseModel):
    name: str
    description: str
    content: str
    domain: str | None = None
    tags: list[str] | None = None


class SkillUpdate(BaseModel):
    description: str | None = None
    content: str | None = None
    domain: str | None = None
    tags: list[str] | None = None


class SkillResponse(BaseModel):
    name: str
    description: str
    domain: str | None = None
    tags: list[str] = []


class SkillDetailResponse(SkillResponse):
    content: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=list[SkillResponse])
def list_skills(domain: str | None = None) -> list[dict[str, Any]]:
    """List all skills, optionally filtered by domain."""
    return skill_service.list_skills(domain=domain)


@router.get("/{skill_name}", response_model=SkillDetailResponse)
def get_skill(skill_name: str) -> dict[str, Any]:
    """Get a single skill by name."""
    skill = skill_service.get_skill(skill_name)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")
    return skill


@router.post("", response_model=SkillDetailResponse, status_code=201)
def create_skill(body: SkillCreate) -> dict[str, Any]:
    """Create a new skill."""
    try:
        return skill_service.create_skill(
            name=body.name,
            description=body.description,
            content=body.content,
            domain=body.domain,
            tags=body.tags,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{skill_name}/update", response_model=SkillDetailResponse)
def update_skill(skill_name: str, body: SkillUpdate) -> dict[str, Any]:
    """Update an existing skill."""
    updates = body.model_dump(exclude_none=True)
    result = skill_service.update_skill(skill_name, **updates)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")
    return result


@router.post("/{skill_name}/delete")
def delete_skill(skill_name: str) -> dict[str, bool]:
    """Delete a skill."""
    if not skill_service.delete_skill(skill_name):
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")
    return {"deleted": True}
```

- [ ] **Step 4: Register router in main.py**

In `backend/app/main.py`, add the import and router registration. The import goes with the other router imports (after line 17):

```python
from app.api.v1.skills import router as skills_router
```

And the registration goes with the other `include_router` calls (after the reviews router):

```python
    app.include_router(skills_router, prefix="/api/v1")
```

- [ ] **Step 5: Run API tests**

Run from `backend/`:

```bash
uv run pytest tests/test_skills_api.py -v
```

Expected: All tests PASS.

- [ ] **Step 6: Run type check and lint**

```bash
cd backend && uv run mypy app/api/v1/skills.py app/main.py && uv run ruff check app/api/v1/skills.py
```

Expected: No errors.

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/v1/skills.py backend/app/main.py backend/tests/test_skills_api.py
git commit -m "feat(skill): add Skill CRUD API endpoints"
```

---

### Task 4: load_skill Tool + SkillMiddleware

**Files:**
- Create: `backend/app/core/agent/skill_middleware.py`
- Create: `backend/tests/test_skill_middleware.py`

- [ ] **Step 1: Write failing tests for middleware**

Create `backend/tests/test_skill_middleware.py`:

```python
"""Tests for SkillMiddleware and load_skill tool."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.core.agent.skill_middleware import SkillMiddleware, create_load_skill_tool
from app.services.skill import SkillService


@pytest.fixture()
def skill_dir(tmp_path: Path) -> Path:
    return tmp_path / "skills"


@pytest.fixture()
def service(skill_dir: Path) -> SkillService:
    return SkillService(skills_dir=skill_dir)


class TestLoadSkillTool:
    """Tests for the load_skill tool function."""

    def test_load_existing_skill(self, service: SkillService, skill_dir: Path) -> None:
        skill_dir.mkdir(parents=True)
        (skill_dir / "test.md").write_text(
            "---\nname: test\ndescription: Test\n---\n\nSkill body.",
            encoding="utf-8",
        )
        tool = create_load_skill_tool(service)
        result = tool.invoke({"skill_name": "test"})
        assert "Skill body." in result
        assert "test" in result

    def test_load_nonexistent_skill(self, service: SkillService) -> None:
        tool = create_load_skill_tool(service)
        result = tool.invoke({"skill_name": "nope"})
        assert "not found" in result.lower()


class TestSkillMiddleware:
    """Tests for SkillMiddleware initialization."""

    def test_init_global(self) -> None:
        middleware = SkillMiddleware(domain=None)
        assert middleware.domain is None
        assert len(middleware.tools) == 1
        assert middleware.tools[0].name == "load_skill"

    def test_init_domain(self) -> None:
        middleware = SkillMiddleware(domain="chapter")
        assert middleware.domain == "chapter"

    def test_no_skills_passes_through(self, skill_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """When no skills exist, middleware should not modify the request."""
        middleware = SkillMiddleware(domain=None)
        # Override the skill service to use empty dir
        middleware.skill_service = SkillService(skills_dir=skill_dir)

        request = MagicMock()
        request.messages = [MagicMock()]
        handler = MagicMock(return_value="response")

        result = middleware.wrap_model_call(request, handler)
        handler.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

Run from `backend/`:

```bash
uv run pytest tests/test_skill_middleware.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.core.agent.skill_middleware'`.

- [ ] **Step 3: Implement SkillMiddleware**

Create `backend/app/core/agent/skill_middleware.py`:

```python
"""Skill middleware for LangChain agents.

Provides:
- create_load_skill_tool: factory for the load_skill @tool function
- SkillMiddleware: AgentMiddleware that injects skill descriptions into system prompt
"""

from __future__ import annotations

from typing import Any

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.messages import SystemMessage
from langchain.tools import tool

from app.services.skill import SkillService


def create_load_skill_tool(skill_service: SkillService) -> Any:
    """Create the load_skill tool bound to a SkillService instance."""

    @tool
    def load_skill(skill_name: str) -> str:
        """Load a skill's full content into context.

        Use this when you need specialized guidance for a specific domain or style.
        """
        skill = skill_service.get_skill(skill_name)
        if not skill:
            available = ", ".join(s["name"] for s in skill_service.list_skills())
            return f"Skill '{skill_name}' not found. Available: {available}"
        return f"Loaded skill: {skill_name}\n\n{skill['content']}"

    return load_skill


class SkillMiddleware(AgentMiddleware):
    """Injects skill descriptions into system prompt and registers load_skill tool.

    The middleware reads the current skill list from disk on each model call,
    ensuring newly created skills are automatically visible without rebuilding tools.

    Args:
        domain: If None, loads global skills (for orchestrator).
                If set (e.g., "chapter"), loads domain-specific skills (for sub-agents).
    """

    def __init__(self, domain: str | None = None) -> None:
        super().__init__()
        self.domain = domain
        self.skill_service = SkillService()
        self.tools = [create_load_skill_tool(self.skill_service)]

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Any,
    ) -> Any:
        # Read current skills dynamically each call
        skills = self.skill_service.list_skills(domain=self.domain)
        if not skills:
            return handler(request)

        skills_list = "\n".join(
            f"- **{s['name']}**: {s['description']}" for s in skills
        )
        skills_addendum = (
            f"\n\n## Available Skills\n\n{skills_list}\n\n"
            "Use the load_skill tool when you need specialized guidance."
        )

        # Inject into system_prompt field of the request
        current_prompt = request.system_prompt or ""
        updated = request.override(
            system_prompt=current_prompt + skills_addendum,
        )

        return handler(updated)
```

- [ ] **Step 4: Run tests to verify they pass**

Run from `backend/`:

```bash
uv run pytest tests/test_skill_middleware.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Run type check**

```bash
cd backend && uv run mypy app/core/agent/skill_middleware.py
```

Expected: No errors.

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/agent/skill_middleware.py backend/tests/test_skill_middleware.py
git commit -m "feat(skill): add load_skill tool and SkillMiddleware"
```

---

### Task 5: Integrate into Orchestrator

**Files:**
- Modify: `backend/app/core/graph/builder.py`

- [ ] **Step 1: Add SkillMiddleware to orchestrator**

In `backend/app/core/graph/builder.py`, add the import (after the existing imports):

```python
from app.core.agent.skill_middleware import SkillMiddleware
```

In `create_orchestrator_graph()`, after creating `read_tools` and before the `return create_agent(...)` call, add:

```python
    # Skill middleware — injects global skill descriptions into system prompt
    skill_middleware = SkillMiddleware(domain=None)
```

Then modify the `create_agent` call to include the middleware:

```python
    return create_agent(
        model=llm,
        tools=[
            delegate_to_world_builder,
            delegate_to_character,
            delegate_to_plot,
            delegate_to_chapter,
            delegate_to_review,
            *read_tools,
            *skill_middleware.tools,
        ],
        system_prompt=ORCHESTRATOR_SYSTEM,
        checkpointer=checkpointer,
        middleware=[skill_middleware],
    )
```

- [ ] **Step 2: Run existing orchestrator tests**

Run from `backend/`:

```bash
uv run pytest tests/test_orchestrator.py -v
```

Expected: All existing tests still PASS (middleware is a no-op when no skills exist).

- [ ] **Step 3: Run lint and type check**

```bash
cd backend && uv run ruff check app/core/graph/builder.py && uv run mypy app/core/graph/builder.py
```

Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add backend/app/core/graph/builder.py
git commit -m "feat(skill): integrate SkillMiddleware into orchestrator"
```

---

### Task 6: Integrate into Sub-agents

**Files:**
- Modify: `backend/app/core/agent/langchain_subagents.py`

- [ ] **Step 1: Add domain SkillMiddleware to all 5 sub-agents**

In `backend/app/core/agent/langchain_subagents.py`, add the import:

```python
from app.core.agent.skill_middleware import SkillMiddleware
```

Then modify each factory function. The pattern for each is the same — add a domain-scoped middleware and pass both its tools and itself to `create_agent`. Here are all 5:

```python
def create_world_builder_agent(project_id: str) -> Any:
    """Create WorldBuilder agent with project_id-scoped tools."""
    read_tools = create_read_tools(project_id)
    tools = create_world_tools(project_id) + read_tools
    skill_middleware = SkillMiddleware(domain="world")
    return create_agent(
        model=create_llm_client(streaming=False),
        tools=[*tools, *skill_middleware.tools],
        system_prompt=WORLD_BUILDER_SYSTEM_PROMPT,
        middleware=[skill_middleware],
    )


def create_character_agent(project_id: str) -> Any:
    """Create Character agent with project_id-scoped tools."""
    read_tools = create_read_tools(project_id)
    tools = create_character_tools(project_id) + read_tools
    skill_middleware = SkillMiddleware(domain="character")
    return create_agent(
        model=create_llm_client(streaming=False),
        tools=[*tools, *skill_middleware.tools],
        system_prompt=CHARACTER_SYSTEM_PROMPT,
        middleware=[skill_middleware],
    )


def create_plot_agent(project_id: str) -> Any:
    """Create Plot agent with project_id-scoped tools."""
    read_tools = create_read_tools(project_id)
    tools = create_plot_tools(project_id) + read_tools
    skill_middleware = SkillMiddleware(domain="plot")
    return create_agent(
        model=create_llm_client(streaming=False),
        tools=[*tools, *skill_middleware.tools],
        system_prompt=PLOT_SYSTEM_PROMPT,
        middleware=[skill_middleware],
    )


def create_chapter_agent(project_id: str) -> Any:
    """Create Chapter agent with project_id-scoped tools."""
    read_tools = create_read_tools(project_id)
    tools = create_chapter_tools(project_id) + read_tools
    skill_middleware = SkillMiddleware(domain="chapter")
    return create_agent(
        model=create_llm_client(streaming=False),
        tools=[*tools, *skill_middleware.tools],
        system_prompt=CHAPTER_SYSTEM_PROMPT,
        middleware=[skill_middleware],
    )


def create_review_agent(project_id: str) -> Any:
    """Create Review agent with project_id-scoped tools."""
    read_tools = create_read_tools(project_id)
    tools = create_review_tools(project_id) + read_tools
    skill_middleware = SkillMiddleware(domain="review")
    return create_agent(
        model=create_llm_client(streaming=False),
        tools=[*tools, *skill_middleware.tools],
        system_prompt=REVIEW_SYSTEM_PROMPT,
        middleware=[skill_middleware],
    )
```

- [ ] **Step 2: Run existing sub-agent and tool tests**

Run from `backend/`:

```bash
uv run pytest tests/test_tools.py tests/test_orchestrator.py -v
```

Expected: All existing tests still PASS.

- [ ] **Step 3: Run lint and type check**

```bash
cd backend && uv run ruff check app/core/agent/langchain_subagents.py && uv run mypy app/core/agent/langchain_subagents.py
```

Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add backend/app/core/agent/langchain_subagents.py
git commit -m "feat(skill): integrate domain SkillMiddleware into all sub-agents"
```

---

### Task 7: Example Skill Files

**Files:**
- Create: `backend/data/skills/wuxia-writing.md`
- Create: `backend/data/skills/noir-detective.md`

- [ ] **Step 1: Create wuxia-writing skill**

Create `backend/data/skills/wuxia-writing.md`:

```markdown
---
name: wuxia-writing
description: 金庸武侠小说写作风格，注重武打场面描写、江湖恩怨和侠义精神
domain: chapter
tags: [武侠, 写作风格, 金庸]
---

# 武侠写作指南

## 文风特征
- 使用半文半白的语言风格
- 武打场面注重招式名称和意境描写
- 人物对话要有江湖气概

## 常用元素
- 门派、武功秘籍、江湖恩怨
- 侠义精神：路见不平拔刀相助
- 师徒关系、兄弟情义

## 写作要点
- 环境描写要营造古风意境
- 打斗场面要有节奏感，动静结合
- 人物心理描写要含蓄内敛
```

- [ ] **Step 2: Create noir-detective skill**

Create `backend/data/skills/noir-detective.md`:

```markdown
---
name: noir-detective
description: 硬汉派侦探小说风格，黑色电影氛围，第一人称叙述
domain: chapter
tags: [悬疑, 推理, noir, 硬汉派]
---

# Noir Detective Writing Guide

## Style
- First-person narration, cynical and world-weary
- Short, punchy sentences mixed with longer atmospheric ones
- Heavy use of metaphor and simile, often dark or ironic

## Atmosphere
- Rain-soaked streets, dimly lit offices, smoky bars
- Urban decay, moral ambiguity
- Femme fatale, corrupt officials, desperate clients

## Plot Elements
- A case that starts simple but unravels into something bigger
- The detective gets beaten up but keeps going
- No one is telling the whole truth
```

- [ ] **Step 3: Verify skills are loadable**

```bash
cd backend && python -c "
from app.services.skill import SkillService
svc = SkillService()
skills = svc.list_skills(domain='chapter')
print(f'Found {len(skills)} chapter skills:')
for s in skills:
    print(f'  - {s[\"name\"]}: {s[\"description\"]}')
"
```

Expected: Found 2 chapter skills: noir-detective, wuxia-writing.

- [ ] **Step 4: Commit**

```bash
git add -f backend/data/skills/wuxia-writing.md backend/data/skills/noir-detective.md
git commit -m "feat(skill): add example wuxia-writing and noir-detective skills"
```

---

### Task 8: Full Test Suite Verification

- [ ] **Step 1: Run the complete test suite**

Run from `backend/`:

```bash
uv run pytest -v
```

Expected: All tests PASS (including existing tests + new skill tests).

- [ ] **Step 2: Run type check on all modified files**

```bash
cd backend && uv run mypy app
```

Expected: No errors.

- [ ] **Step 3: Run lint and format check**

```bash
cd backend && uv run ruff check app tests && uv run ruff format --check app tests
```

Expected: No errors.

- [ ] **Step 4: Commit any fixes**

If any fixes were needed:

```bash
git add -A
git commit -m "fix(skill): address type check and lint issues"
```
