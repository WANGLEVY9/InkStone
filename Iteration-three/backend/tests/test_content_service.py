"""Tests for ContentService project isolation.

These tests verify project isolation at the ContentService layer.
"""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


class TestContentServiceSignature:
    """Verify that ContentService methods have correct signatures."""

    def test_create_world_setting_requires_project_id_first(self) -> None:
        """Verify create_world_setting requires project_id as first argument."""
        import inspect

        from app.services.content import ContentService

        sig = inspect.signature(ContentService.create_world_setting)
        params = list(sig.parameters.keys())

        assert "project_id" in params
        assert params.index("project_id") == 1  # after self

    def test_create_character_requires_project_id_first(self) -> None:
        """Verify create_character requires project_id as first argument."""
        import inspect

        from app.services.content import ContentService

        sig = inspect.signature(ContentService.create_character)
        params = list(sig.parameters.keys())

        assert "project_id" in params
        assert params.index("project_id") == 1

    def test_create_outline_requires_project_id_first(self) -> None:
        """Verify create_outline requires project_id as first argument."""
        import inspect

        from app.services.content import ContentService

        sig = inspect.signature(ContentService.create_outline)
        params = list(sig.parameters.keys())

        assert "project_id" in params
        assert params.index("project_id") == 1

    def test_create_chapter_requires_project_id_first(self) -> None:
        """Verify create_chapter requires project_id as first argument."""
        import inspect

        from app.services.content import ContentService

        sig = inspect.signature(ContentService.create_chapter)
        params = list(sig.parameters.keys())

        assert "project_id" in params
        assert params.index("project_id") == 1

    def test_search_outlines_requires_project_id_first(self) -> None:
        import inspect

        from app.services.content import ContentService

        sig = inspect.signature(ContentService.search_outlines)
        params = list(sig.parameters.keys())
        assert "project_id" in params
        assert params.index("project_id") == 1

    def test_search_chapters_requires_project_id_first(self) -> None:
        import inspect

        from app.services.content import ContentService

        sig = inspect.signature(ContentService.search_chapters)
        params = list(sig.parameters.keys())
        assert "project_id" in params
        assert params.index("project_id") == 1

    def test_search_reviews_requires_project_id_first(self) -> None:
        import inspect

        from app.services.content import ContentService

        sig = inspect.signature(ContentService.search_reviews)
        params = list(sig.parameters.keys())
        assert "project_id" in params
        assert params.index("project_id") == 1

    def test_delete_review_requires_review_id_first(self) -> None:
        import inspect

        from app.services.content import ContentService

        sig = inspect.signature(ContentService.delete_review)
        params = list(sig.parameters.keys())
        assert "review_id" in params
        assert params.index("review_id") == 1


class TestContentServiceQueryMethods:
    """Test ContentService query methods for project context."""

    @pytest.fixture
    def db_with_data(self) -> Generator[str]:
        """Create a test database with sample data."""
        temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_db.close()

        import sqlite3

        schema_path = Path(__file__).parent.parent / "app" / "db" / "schema.sql"
        conn = sqlite3.connect(temp_db.name)
        conn.executescript(schema_path.read_text())

        conn.execute(
            "INSERT INTO world_settings_meta (id, project_id, name, file_path, summary) VALUES (?, ?, ?, ?, ?)",
            ("ws1", "proj1", "Fantasy World", "/path/ws1.md", "A magical world"),
        )
        conn.execute(
            "INSERT INTO characters_meta (id, project_id, name, file_path, summary) VALUES (?, ?, ?, ?, ?)",
            ("char1", "proj1", "Hero", "/path/char1.md", "The protagonist"),
        )
        conn.execute(
            "INSERT INTO outlines_meta (id, project_id, parent_id, title, file_path, type, sort_order) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("outline1", "proj1", None, "Main Plot", "/path/outline1.md", "root", 0),
        )
        conn.execute(
            "INSERT INTO chapters_meta (id, project_id, title, file_path, word_count, status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("ch1", "proj1", "Chapter 1", "/path/ch1.md", 1000, "draft"),
        )
        conn.commit()
        conn.close()

        yield temp_db.name

        Path(temp_db.name).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_get_all_world_settings_returns_project_data(self, db_with_data: str) -> None:
        """Test get_all_world_settings returns only world settings for specified project."""
        import aiosqlite

        from app.services.content import ContentService

        db = await aiosqlite.connect(db_with_data)
        db.row_factory = aiosqlite.Row
        service = ContentService(db)

        result = await service.get_all_world_settings("proj1")

        await db.close()

        assert len(result) == 1
        assert result[0]["id"] == "ws1"
        assert result[0]["name"] == "Fantasy World"
        assert "content" not in result[0]

    @pytest.mark.asyncio
    async def test_get_all_characters_returns_project_data(self, db_with_data: str) -> None:
        """Test get_all_characters returns only characters for specified project."""
        import aiosqlite

        from app.services.content import ContentService

        db = await aiosqlite.connect(db_with_data)
        db.row_factory = aiosqlite.Row
        service = ContentService(db)

        result = await service.get_all_characters("proj1")

        await db.close()

        assert len(result) == 1
        assert result[0]["id"] == "char1"
        assert result[0]["name"] == "Hero"
        assert "content" not in result[0]

    @pytest.mark.asyncio
    async def test_get_root_outline_returns_root_only(self, db_with_data: str) -> None:
        """Test get_root_outline returns only outline with parent_id IS NULL."""
        import aiosqlite

        from app.services.content import ContentService

        db = await aiosqlite.connect(db_with_data)
        db.row_factory = aiosqlite.Row
        service = ContentService(db)

        result = await service.get_root_outline("proj1")

        await db.close()

        assert result is not None
        assert result["id"] == "outline1"
        assert result["parent_id"] is None

    @pytest.mark.asyncio
    async def test_get_all_chapters_returns_project_data(self, db_with_data: str) -> None:
        """Test get_all_chapters returns only chapters for specified project."""
        import aiosqlite

        from app.services.content import ContentService

        db = await aiosqlite.connect(db_with_data)
        db.row_factory = aiosqlite.Row
        service = ContentService(db)

        result = await service.get_all_chapters("proj1")

        await db.close()

        assert len(result) == 1
        assert result[0]["id"] == "ch1"
        assert result[0]["title"] == "Chapter 1"
        assert "content" not in result[0]

    @pytest.mark.asyncio
    async def test_get_all_world_settings_empty_for_nonexistent_project(self, db_with_data: str) -> None:
        """Test get_all_world_settings returns empty list for project with no data."""
        import aiosqlite

        from app.services.content import ContentService

        db = await aiosqlite.connect(db_with_data)
        db.row_factory = aiosqlite.Row
        service = ContentService(db)

        result = await service.get_all_world_settings("nonexistent")

        await db.close()

        assert result == []


class TestContentServiceUpdateMethods:
    """Test ContentService update methods for editing existing content."""

    @pytest.fixture
    def db_with_content(self, tmp_path: Path) -> Generator[tuple[str, Path]]:
        """Create test database with actual content files."""
        import sqlite3

        # Create temp directory structure
        proj_dir = tmp_path / "proj1"
        (proj_dir / "world_settings").mkdir(parents=True)
        (proj_dir / "characters").mkdir(parents=True)
        (proj_dir / "outlines").mkdir(parents=True)
        (proj_dir / "chapters").mkdir(parents=True)

        # Write content files
        (proj_dir / "world_settings" / "ws1.md").write_text("Original world setting content")
        (proj_dir / "characters" / "char1.md").write_text("Original character content")
        (proj_dir / "outlines" / "outline1.md").write_text("Original outline content")
        (proj_dir / "chapters" / "ch1.md").write_text("Original chapter content")

        # Create database
        temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_db.close()

        schema_path = Path(__file__).parent.parent / "app" / "db" / "schema.sql"
        conn = sqlite3.connect(temp_db.name)
        conn.executescript(schema_path.read_text())

        conn.execute(
            "INSERT INTO world_settings_meta (id, project_id, name, file_path, summary) VALUES (?, ?, ?, ?, ?)",
            ("ws1", "proj1", "World1", str(proj_dir / "world_settings" / "ws1.md"), "Original summary"),
        )
        conn.execute(
            "INSERT INTO characters_meta (id, project_id, name, file_path, summary) VALUES (?, ?, ?, ?, ?)",
            ("char1", "proj1", "Character1", str(proj_dir / "characters" / "char1.md"), "Original summary"),
        )
        conn.execute(
            "INSERT INTO outlines_meta (id, project_id, parent_id, title, file_path, type, sort_order) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("outline1", "proj1", None, "Outline1", str(proj_dir / "outlines" / "outline1.md"), "main", 0),
        )
        conn.execute(
            "INSERT INTO chapters_meta (id, project_id, title, file_path, word_count, status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("ch1", "proj1", "Chapter1", str(proj_dir / "chapters" / "ch1.md"), 1000, "draft"),
        )
        conn.commit()
        conn.close()

        yield temp_db.name, tmp_path

        Path(temp_db.name).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_update_world_setting_updates_content_and_summary(self, db_with_content: tuple[str, Path]) -> None:
        """Test update_world_setting replaces content and optionally updates metadata."""
        import aiosqlite

        from app.services.content import ContentService, FileSystemStorage

        db_path, tmp_path = db_with_content
        db = await aiosqlite.connect(db_path)
        db.row_factory = aiosqlite.Row
        storage = FileSystemStorage(tmp_path)
        service = ContentService(db, storage)

        result = await service.update_world_setting(
            "ws1", "proj1", "Updated world setting content", name="New World Name", summary="New summary"
        )

        await db.close()

        assert result is not None
        assert result["content"] == "Updated world setting content"
        assert result["summary"] == "New summary"

    @pytest.mark.asyncio
    async def test_update_world_setting_returns_none_for_nonexistent_id(
        self, db_with_content: tuple[str, Path]
    ) -> None:
        """Test update_world_setting returns None when world_setting_id not found."""
        import aiosqlite

        from app.services.content import ContentService, FileSystemStorage

        db_path, tmp_path = db_with_content
        db = await aiosqlite.connect(db_path)
        db.row_factory = aiosqlite.Row
        storage = FileSystemStorage(tmp_path)
        service = ContentService(db, storage)

        result = await service.update_world_setting("nonexistent", "proj1", "New content")

        await db.close()

        assert result is None

    @pytest.mark.asyncio
    async def test_update_character_updates_content_and_name(self, db_with_content: tuple[str, Path]) -> None:
        """Test update_character replaces content and optionally updates metadata."""
        import aiosqlite

        from app.services.content import ContentService, FileSystemStorage

        db_path, tmp_path = db_with_content
        db = await aiosqlite.connect(db_path)
        db.row_factory = aiosqlite.Row
        storage = FileSystemStorage(tmp_path)
        service = ContentService(db, storage)

        result = await service.update_character(
            "char1", "proj1", "Updated character content", name="New Character Name"
        )

        await db.close()

        assert result is not None
        assert result["content"] == "Updated character content"
        assert result["name"] == "New Character Name"

    @pytest.mark.asyncio
    async def test_update_character_returns_none_for_nonexistent_id(self, db_with_content: tuple[str, Path]) -> None:
        """Test update_character returns None when character_id not found."""
        import aiosqlite

        from app.services.content import ContentService, FileSystemStorage

        db_path, tmp_path = db_with_content
        db = await aiosqlite.connect(db_path)
        db.row_factory = aiosqlite.Row
        storage = FileSystemStorage(tmp_path)
        service = ContentService(db, storage)

        result = await service.update_character("nonexistent", "proj1", "New content")

        await db.close()

        assert result is None

    @pytest.mark.asyncio
    async def test_update_outline_updates_content_and_title(self, db_with_content: tuple[str, Path]) -> None:
        """Test update_outline replaces content and optionally updates metadata."""
        import aiosqlite

        from app.services.content import ContentService, FileSystemStorage

        db_path, tmp_path = db_with_content
        db = await aiosqlite.connect(db_path)
        db.row_factory = aiosqlite.Row
        storage = FileSystemStorage(tmp_path)
        service = ContentService(db, storage)

        result = await service.update_outline("outline1", "proj1", "Updated outline content", title="New Outline Title")

        await db.close()

        assert result is not None
        assert result["content"] == "Updated outline content"

    @pytest.mark.asyncio
    async def test_update_outline_returns_none_for_nonexistent_id(self, db_with_content: tuple[str, Path]) -> None:
        """Test update_outline returns None when outline_id not found."""
        import aiosqlite

        from app.services.content import ContentService, FileSystemStorage

        db_path, tmp_path = db_with_content
        db = await aiosqlite.connect(db_path)
        db.row_factory = aiosqlite.Row
        storage = FileSystemStorage(tmp_path)
        service = ContentService(db, storage)

        result = await service.update_outline("nonexistent", "proj1", "New content")

        await db.close()

        assert result is None


class TestChapterMetadataFields:
    """Tests covering chapter_number / summary / published_at metadata."""

    @pytest.mark.asyncio
    async def test_create_chapter_persists_new_metadata_fields(self, tmp_path: Path) -> None:
        """create_chapter should persist chapter_number / summary / published_at."""
        import sqlite3
        import tempfile

        import aiosqlite

        from app.services.content import ContentService, FileSystemStorage

        temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_db.close()
        schema_path = Path(__file__).parent.parent / "app" / "db" / "schema.sql"
        conn = sqlite3.connect(temp_db.name)
        conn.executescript(schema_path.read_text())
        conn.close()

        db = await aiosqlite.connect(temp_db.name)
        db.row_factory = aiosqlite.Row
        storage = FileSystemStorage(tmp_path)
        service = ContentService(db, storage)

        created = await service.create_chapter(
            project_id="proj1",
            chapter_id="ch_new",
            title="第三章 觉醒",
            content="# 第三章\n\n他睁开了眼睛。",
            word_count=8,
            chapter_number=3,
            summary="主角觉醒",
        )

        assert created["chapter_number"] == 3
        assert created["summary"] == "主角觉醒"

        fetched = await service.get_chapter("ch_new", "proj1")
        await db.close()
        Path(temp_db.name).unlink(missing_ok=True)

        assert fetched is not None
        assert fetched["chapter_number"] == 3
        assert fetched["summary"] == "主角觉醒"
        assert fetched["published_at"] is None

    @pytest.mark.asyncio
    async def test_update_chapter_publishes_with_status_and_timestamp(self, tmp_path: Path) -> None:
        """update_chapter should accept status and published_at together."""
        import sqlite3
        import tempfile

        import aiosqlite

        from app.services.content import ContentService, FileSystemStorage

        temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_db.close()
        schema_path = Path(__file__).parent.parent / "app" / "db" / "schema.sql"
        conn = sqlite3.connect(temp_db.name)
        conn.executescript(schema_path.read_text())
        conn.close()

        db = await aiosqlite.connect(temp_db.name)
        db.row_factory = aiosqlite.Row
        storage = FileSystemStorage(tmp_path)
        service = ContentService(db, storage)

        await service.create_chapter(
            project_id="proj1",
            chapter_id="ch_pub",
            title="Pub",
            content="body",
            chapter_number=1,
        )

        updated = await service.update_chapter(
            "ch_pub",
            "proj1",
            "body",
            status="published",
            published_at="2026-05-02T10:00:00",
        )

        listed = await service.get_all_chapters("proj1")
        await db.close()
        Path(temp_db.name).unlink(missing_ok=True)

        assert updated is not None
        assert updated["status"] == "published"
        assert updated["published_at"] == "2026-05-02T10:00:00"

        assert len(listed) == 1
        assert listed[0]["chapter_number"] == 1
        assert listed[0]["status"] == "published"
        assert listed[0]["published_at"] == "2026-05-02T10:00:00"
        assert "summary" in listed[0]
