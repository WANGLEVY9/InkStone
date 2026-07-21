"""Tests for NovelContextBuilder."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.services.novel_context_builder import NovelContextBuilder, _is_protagonist


class TestProtagonistDetection:
    """Test protagonist keyword matching."""

    def test_protagonist_keyword_in_name(self) -> None:
        assert _is_protagonist("主角李逍遥", "A brave swordsman") is True
        assert _is_protagonist("protagonist_li", "The main hero") is True
        assert _is_protagonist("Main Character", "Hero of the story") is True

    def test_non_protagonist(self) -> None:
        assert _is_protagonist("张三", "A minor character") is False
        assert _is_protagonist("王奶奶", "Village elder") is False

    def test_protagonist_keyword_in_summary(self) -> None:
        assert _is_protagonist("李逍遥", "The protagonist of the story") is True
        assert _is_protagonist("赵云", "Main character in this arc") is True

    def test_empty_name_and_summary(self) -> None:
        assert _is_protagonist("", "") is False


class TestNovelContextBuilder:
    """Test NovelContextBuilder.build_context()."""

    @pytest.mark.asyncio
    async def test_empty_context_with_no_data(self) -> None:
        """Build context with no chapters, no foreshadowing, no characters."""
        import aiosqlite

        db = await aiosqlite.connect(":memory:")
        db.row_factory = aiosqlite.Row

        # Create required tables
        await db.execute(
            "CREATE TABLE IF NOT EXISTS foreshadowing ("
            "id TEXT PRIMARY KEY, project_id TEXT NOT NULL, description TEXT NOT NULL, "
            "foreshadowed_at TEXT DEFAULT '', expected_resolve_at TEXT DEFAULT '', "
            "status TEXT DEFAULT 'pending', target_chapter_id TEXT DEFAULT '', "
            "related_entities TEXT DEFAULT '[]', notes TEXT DEFAULT '', "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        await db.execute(
            "CREATE TABLE IF NOT EXISTS chapters_meta ("
            "id TEXT PRIMARY KEY, project_id TEXT NOT NULL, title TEXT NOT NULL, "
            "file_path TEXT NOT NULL, word_count INTEGER DEFAULT 0, status TEXT DEFAULT 'draft', "
            "chapter_number INTEGER DEFAULT 1, summary TEXT, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )

        builder = NovelContextBuilder(db)
        context = await builder.build_context(
            project_id="proj-1",
            characters=[],
            chapters_meta=[],
        )
        assert context == ""

    @pytest.mark.asyncio
    async def test_context_with_foreshadowing_only(self) -> None:
        """Build context with only foreshadowing entries."""
        import aiosqlite

        db = await aiosqlite.connect(":memory:")
        db.row_factory = aiosqlite.Row
        await db.execute(
            "CREATE TABLE IF NOT EXISTS foreshadowing ("
            "id TEXT PRIMARY KEY, project_id TEXT NOT NULL, description TEXT NOT NULL, "
            "foreshadowed_at TEXT DEFAULT '', expected_resolve_at TEXT DEFAULT '', "
            "status TEXT DEFAULT 'pending', target_chapter_id TEXT DEFAULT '', "
            "related_entities TEXT DEFAULT '[]', notes TEXT DEFAULT '', "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        # Add a foreshadowing entry directly
        await db.execute(
            "INSERT INTO foreshadowing (id, project_id, description, status) VALUES (?, ?, ?, ?)",
            ("f-1", "proj-1", "A mysterious key", "pending"),
        )
        await db.commit()

        builder = NovelContextBuilder(db)
        context = await builder.build_context(
            project_id="proj-1",
            characters=[],
            chapters_meta=[],
        )
        assert "未回收伏笔" in context
        assert "A mysterious key" in context

    @pytest.mark.asyncio
    async def test_context_with_protagonist(self) -> None:
        """Build context with protagonist character."""
        import aiosqlite

        db = await aiosqlite.connect(":memory:")
        db.row_factory = aiosqlite.Row
        await db.execute(
            "CREATE TABLE IF NOT EXISTS foreshadowing ("
            "id TEXT PRIMARY KEY, project_id TEXT NOT NULL, description TEXT NOT NULL, "
            "foreshadowed_at TEXT DEFAULT '', expected_resolve_at TEXT DEFAULT '', "
            "status TEXT DEFAULT 'pending', target_chapter_id TEXT DEFAULT '', "
            "related_entities TEXT DEFAULT '[]', notes TEXT DEFAULT '', "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )

        builder = NovelContextBuilder(db)
        context = await builder.build_context(
            project_id="proj-1",
            characters=[
                {"name": "主角李逍遥", "summary": "A brave young swordsman"},
                {"name": "赵灵儿", "summary": "A mysterious maiden"},
            ],
            chapters_meta=[],
        )
        assert "主角状态" in context
        assert "李逍遥" in context
        assert "赵灵儿" not in context  # Not detected as protagonist

    @pytest.mark.asyncio
    async def test_context_with_chapters_no_content(self) -> None:
        """Build context with chapter metadata but no actual content files."""
        import aiosqlite

        db = await aiosqlite.connect(":memory:")
        db.row_factory = aiosqlite.Row
        await db.execute(
            "CREATE TABLE IF NOT EXISTS foreshadowing ("
            "id TEXT PRIMARY KEY, project_id TEXT NOT NULL, description TEXT NOT NULL, "
            "foreshadowed_at TEXT DEFAULT '', expected_resolve_at TEXT DEFAULT '', "
            "status TEXT DEFAULT 'pending', target_chapter_id TEXT DEFAULT '', "
            "related_entities TEXT DEFAULT '[]', notes TEXT DEFAULT '', "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )

        builder = NovelContextBuilder(db)
        # Mock the content property to return a service that returns None for get_chapter
        mock_content = AsyncMock()
        mock_content.get_chapter = AsyncMock(return_value=None)
        builder._content_service = mock_content

        context = await builder.build_context(
            project_id="proj-1",
            characters=[],
            chapters_meta=[{"id": "ch-1", "title": "Chapter One", "chapter_number": 1}],
        )
        # No chapter content, no foreshadowing, no protagonist
        assert context == ""

    @pytest.mark.asyncio
    async def test_context_chapter_sorting(self) -> None:
        """Chapters should be sorted by chapter_number, taking last 2."""
        import aiosqlite

        db = await aiosqlite.connect(":memory:")
        db.row_factory = aiosqlite.Row
        await db.execute(
            "CREATE TABLE IF NOT EXISTS foreshadowing ("
            "id TEXT PRIMARY KEY, project_id TEXT NOT NULL, description TEXT NOT NULL, "
            "foreshadowed_at TEXT DEFAULT '', expected_resolve_at TEXT DEFAULT '', "
            "status TEXT DEFAULT 'pending', target_chapter_id TEXT DEFAULT '', "
            "related_entities TEXT DEFAULT '[]', notes TEXT DEFAULT '', "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        chapters_meta = [
            {"id": "ch-1", "title": "Ch1", "chapter_number": 1},
            {"id": "ch-2", "title": "Ch2", "chapter_number": 2},
            {"id": "ch-3", "title": "Ch3", "chapter_number": 3},
        ]

        builder = NovelContextBuilder(db)
        # Mock content service to return None for all get_chapter calls
        mock_content = AsyncMock()
        mock_content.get_chapter = AsyncMock(return_value=None)
        builder._content_service = mock_content

        context = await builder.build_context(
            project_id="proj-1",
            characters=[],
            chapters_meta=chapters_meta,
        )
        # No chapter content, no foreshadowing, no protagonist
        assert context == ""

        # Verify that get_chapter was called for the last 2 chapters only
        assert mock_content.get_chapter.call_count == 2
        # The last 2 chapters by chapter_number are ch-2 and ch-3
        called_args = [call.args for call in mock_content.get_chapter.call_args_list]
        called_ids = [args[0] for args in called_args]  # chapter_id is first positional arg
        assert "ch-2" in called_ids
        assert "ch-3" in called_ids
        assert "ch-1" not in called_ids


class TestNovelContextIntegration:
    """Test the NovelContextBuilder integration with chat.py."""

    def test_imports(self) -> None:
        """Verify the import path works."""
        from app.services.novel_context_builder import NovelContextBuilder

        assert NovelContextBuilder is not None
