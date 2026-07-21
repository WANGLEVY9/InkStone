"""Tests for ForeshadowingService and foreshadowing tool registration."""

from __future__ import annotations

from typing import Any

import pytest

from app.core.agent.tool_factory import (
    create_all_tools,
    create_foreshadowing_tools,
)
from app.services.foreshadowing import ForeshadowingService


class TestForeshadowingService:
    """Test ForeshadowingService CRUD operations."""

    async def _setup_db(self) -> Any:
        """Create an in-memory SQLite DB with the foreshadowing table."""
        import aiosqlite

        db = await aiosqlite.connect(":memory:")
        db.row_factory = aiosqlite.Row
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS foreshadowing (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                description TEXT NOT NULL,
                foreshadowed_at TEXT DEFAULT '',
                expected_resolve_at TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                target_chapter_id TEXT DEFAULT '',
                related_entities TEXT DEFAULT '[]',
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        return db

    @pytest.mark.asyncio
    async def test_create_and_get(self) -> None:
        """Test creating a foreshadowing entry and retrieving it."""
        db = await self._setup_db()
        service = ForeshadowingService(db)
        result = await service.create(
            project_id="proj-1",
            description="A mysterious key found in the garden",
            foreshadowed_at="Chapter 3",
            expected_resolve_at="Chapter 15",
            related_entities=["char-1"],
        )
        assert result is not None
        assert result["description"] == "A mysterious key found in the garden"
        assert result["status"] == "pending"
        assert result["project_id"] == "proj-1"
        assert result["related_entities"] == ["char-1"]

        # Retrieve by ID
        fetched = await service.get(result["id"], "proj-1")
        assert fetched is not None
        assert fetched["description"] == result["description"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self) -> None:
        """Test get returns None for non-existent foreshadowing."""
        db = await self._setup_db()
        service = ForeshadowingService(db)
        result = await service.get("nonexistent", "proj-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_by_project(self) -> None:
        """Test listing all foreshadowing entries for a project."""
        db = await self._setup_db()
        service = ForeshadowingService(db)
        await service.create(project_id="proj-1", description="First hint")
        await service.create(project_id="proj-1", description="Second hint")
        await service.create(project_id="proj-2", description="Other project")

        entries = await service.list_by_project("proj-1")
        assert len(entries) == 2

        entries_p2 = await service.list_by_project("proj-2")
        assert len(entries_p2) == 1

    @pytest.mark.asyncio
    async def test_list_filter_by_status(self) -> None:
        """Test listing foreshadowing entries filtered by status."""
        db = await self._setup_db()
        service = ForeshadowingService(db)
        e1 = await service.create(project_id="proj-1", description="Hint 1")
        await service.create(project_id="proj-1", description="Hint 2")
        await service.resolve(e1["id"], "proj-1")

        pending = await service.list_by_project("proj-1", status="pending")
        assert len(pending) == 1
        assert pending[0]["description"] == "Hint 2"

        resolved = await service.list_by_project("proj-1", status="resolved")
        assert len(resolved) == 1
        assert resolved[0]["description"] == "Hint 1"

    @pytest.mark.asyncio
    async def test_update(self) -> None:
        """Test updating a foreshadowing entry."""
        db = await self._setup_db()
        service = ForeshadowingService(db)
        entry = await service.create(project_id="proj-1", description="Original")
        updated = await service.update(entry["id"], "proj-1", description="Updated", notes="New notes")
        assert updated is not None
        assert updated["description"] == "Updated"
        assert updated["notes"] == "New notes"

    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        """Test deleting a foreshadowing entry."""
        db = await self._setup_db()
        service = ForeshadowingService(db)
        entry = await service.create(project_id="proj-1", description="To delete")
        deleted = await service.delete(entry["id"], "proj-1")
        assert deleted is True
        assert await service.get(entry["id"], "proj-1") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_false(self) -> None:
        """Test deleting a non-existent entry returns False."""
        db = await self._setup_db()
        service = ForeshadowingService(db)
        result = await service.delete("nonexistent", "proj-1")
        assert result is False

    @pytest.mark.asyncio
    async def test_resolve(self) -> None:
        """Test resolving a foreshadowing entry."""
        db = await self._setup_db()
        service = ForeshadowingService(db)
        entry = await service.create(project_id="proj-1", description="Will be resolved")
        resolved = await service.resolve(entry["id"], "proj-1")
        assert resolved is not None
        assert resolved["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_get_unresolved(self) -> None:
        """Test get_unresolved returns only pending/active entries."""
        db = await self._setup_db()
        service = ForeshadowingService(db)
        e1 = await service.create(project_id="proj-1", description="Pending hint")
        e2 = await service.create(project_id="proj-1", description="Will resolve")
        await service.resolve(e2["id"], "proj-1")

        unresolved = await service.get_unresolved("proj-1")
        assert len(unresolved) == 1
        assert unresolved[0]["id"] == e1["id"]

    @pytest.mark.asyncio
    async def test_search(self) -> None:
        """Test searching foreshadowing entries."""
        db = await self._setup_db()
        service = ForeshadowingService(db)
        await service.create(project_id="proj-1", description="magic sword in the stone")
        await service.create(project_id="proj-1", description="ancient prophecy about the chosen one")
        await service.create(project_id="proj-1", description="hidden treasure map")

        results = await service.search("proj-1", "sword")
        assert len(results) == 1

        results = await service.search("proj-1", "the")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_project_isolation(self) -> None:
        """Test that entries are properly isolated by project."""
        db = await self._setup_db()
        service = ForeshadowingService(db)
        await service.create(project_id="proj-a", description="Project A hint")
        await service.create(project_id="proj-b", description="Project B hint")

        assert len(await service.list_by_project("proj-a")) == 1
        assert len(await service.list_by_project("proj-b")) == 1

        # Cross-project get should fail
        entry_a = (await service.list_by_project("proj-a"))[0]
        cross_get = await service.get(entry_a["id"], "proj-b")
        assert cross_get is None

    @pytest.mark.asyncio
    async def test_related_entities_serialization(self) -> None:
        """Test that related_entities list is properly serialized."""
        db = await self._setup_db()
        service = ForeshadowingService(db)
        entities = ["char-1", "world-setting-3", "item-7"]
        entry = await service.create(
            project_id="proj-1",
            description="Test entities",
            related_entities=entities,
        )
        assert entry["related_entities"] == entities


class TestForeshadowingTools:
    """Test foreshadowing tool registration and signatures."""

    def test_foreshadowing_tools_exist(self) -> None:
        """Foreshadowing tools should include detect_foreshadowing."""
        tools = create_foreshadowing_tools("test-project")
        names = {t.name for t in tools}
        assert names == {
            "create_foreshadowing",
            "list_foreshadowing",
            "resolve_foreshadowing",
            "delete_foreshadowing",
            "get_unresolved_foreshadowing",
            "detect_foreshadowing",
        }

    def test_foreshadowing_tools_are_sync(self) -> None:
        """Foreshadowing tools should be sync functions."""
        tools = create_foreshadowing_tools("test-project")
        for t in tools:
            assert t.coroutine is None, f"{t.name} should be sync"

    def test_detect_foreshadowing_has_correct_params(self) -> None:
        """detect_foreshadowing should accept content and chapter_title."""
        tools = create_foreshadowing_tools("test-project")
        detect = next(t for t in tools if t.name == "detect_foreshadowing")
        import inspect

        sig = inspect.signature(detect.func)
        params = list(sig.parameters.keys())
        assert "content" in params
        assert "chapter_title" in params

    def test_all_tools_includes_foreshadowing(self) -> None:
        """create_all_tools should include foreshadowing tools."""
        tools = create_all_tools("test-project")
        names = {t.name for t in tools}
        assert "create_foreshadowing" in names
        assert "detect_foreshadowing" in names
        assert "get_unresolved_foreshadowing" in names
