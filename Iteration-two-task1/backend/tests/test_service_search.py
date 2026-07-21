"""Tests for search methods on OutlineService, ChapterService, ReviewService
and delete method on ReviewService."""

import gc
import tempfile
from collections.abc import Generator
from pathlib import Path

import aiosqlite
import pytest


@pytest.fixture
def db_path() -> Generator[str]:
    """Create a temp SQLite DB with schema and test data, yield its path."""
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()

    import sqlite3

    schema_path = Path(__file__).parent.parent / "app" / "db" / "schema.sql"
    conn = sqlite3.connect(temp_db.name)
    conn.executescript(schema_path.read_text())

    # Outlines for project "p1"
    conn.execute(
        "INSERT INTO outlines_meta (id, project_id, parent_id, title, file_path, type, sort_order) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("o1", "p1", None, "The Great War Begins", "p1/outlines/o1.md", "root", 0),
    )
    conn.execute(
        "INSERT INTO outlines_meta (id, project_id, parent_id, title, file_path, type, sort_order) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("o2", "p1", None, "Peace Treaty Signed", "p1/outlines/o2.md", "root", 1),
    )

    # Chapters for project "p1"
    conn.execute(
        "INSERT INTO chapters_meta (id, project_id, title, file_path, word_count, status, chapter_number, summary) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("c1", "p1", "Dragon Awakens", "p1/chapters/c1.md", 500, "draft", 1, "A dragon appears"),
    )
    conn.execute(
        "INSERT INTO chapters_meta (id, project_id, title, file_path, word_count, status, chapter_number, summary) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("c2", "p1", "The Castle", "p1/chapters/c2.md", 600, "draft", 2, "A brave knight enters"),
    )

    # Review for project "p1"
    conn.execute(
        "INSERT INTO reviews (id, project_id, content_type, content_id, issues, suggestions, overall_score) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("r1", "p1", "chapter", "c1", '["issue1"]', '["suggestion1"]', 8.5),
    )

    # Extra outline for a different project (for isolation tests)
    conn.execute(
        "INSERT INTO outlines_meta (id, project_id, parent_id, title, file_path, type, sort_order) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("o3", "p2", None, "War and Peace in Another World", "p2/outlines/o3.md", "root", 0),
    )

    # Extra chapter for a different project
    conn.execute(
        "INSERT INTO chapters_meta (id, project_id, title, file_path, word_count, status, chapter_number, summary) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("c3", "p2", "Dragon Tales", "p2/chapters/c3.md", 400, "draft", 1, "Another dragon story"),
    )

    # Extra review for a different project
    conn.execute(
        "INSERT INTO reviews (id, project_id, content_type, content_id, issues, suggestions, overall_score) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("r2", "p2", "chapter", "c3", "[]", "[]", 7.0),
    )

    conn.commit()
    conn.close()

    yield temp_db.name

    gc.collect()
    try:
        Path(temp_db.name).unlink(missing_ok=True)
    except PermissionError:
        pass  # Windows file locking from unclosed aiosqlite handles


async def _connect(db_path: str) -> aiosqlite.Connection:
    """Helper to open an aiosqlite connection with Row factory."""
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    return db


# ---------------------------------------------------------------------------
# OutlineService.search
# ---------------------------------------------------------------------------


class TestOutlineServiceSearch:
    """Tests for OutlineService.search(project_id, query)."""

    async def test_search_by_title_match(self, db_path: str) -> None:
        """Searching by 'war' should return outlines whose title contains 'war'."""
        from app.services.outline import OutlineService

        db = await _connect(db_path)
        service = OutlineService(db)

        results = await service.search("p1", "war")

        await db.close()

        assert len(results) == 1
        assert results[0]["id"] == "o1"
        assert "war" in results[0]["title"].lower()

    async def test_search_no_match(self, db_path: str) -> None:
        """Searching for a non-existent term returns an empty list."""
        from app.services.outline import OutlineService

        db = await _connect(db_path)
        service = OutlineService(db)

        results = await service.search("p1", "nonexistent_xyz")

        await db.close()

        assert results == []

    async def test_search_project_isolation(self, db_path: str) -> None:
        """Searching 'war' in p1 should not return results from p2."""
        from app.services.outline import OutlineService

        db = await _connect(db_path)
        service = OutlineService(db)

        results_p1 = await service.search("p1", "war")
        results_p2 = await service.search("p2", "war")

        await db.close()

        # p1 has "The Great War Begins", p2 has "War and Peace in Another World"
        p1_ids = {r["id"] for r in results_p1}
        p2_ids = {r["id"] for r in results_p2}

        assert "o1" in p1_ids
        assert "o3" not in p1_ids
        assert "o3" in p2_ids
        assert "o1" not in p2_ids

    async def test_search_case_insensitive_like(self, db_path: str) -> None:
        """LIKE query matches case-insensitively in SQLite by default."""
        from app.services.outline import OutlineService

        db = await _connect(db_path)
        service = OutlineService(db)

        results = await service.search("p1", "Peace")

        await db.close()

        assert len(results) == 1
        assert results[0]["id"] == "o2"


# ---------------------------------------------------------------------------
# ChapterService.search
# ---------------------------------------------------------------------------


class TestChapterServiceSearch:
    """Tests for ChapterService.search(project_id, query)."""

    async def test_search_by_title_match(self, db_path: str) -> None:
        """Searching 'dragon' should match chapter with 'dragon' in title."""
        from app.services.chapter import ChapterService

        db = await _connect(db_path)
        service = ChapterService(db)

        results = await service.search("p1", "dragon")

        await db.close()

        assert len(results) == 1
        assert results[0]["id"] == "c1"

    async def test_search_by_summary_match(self, db_path: str) -> None:
        """Searching 'knight' should match chapter with 'knight' in summary."""
        from app.services.chapter import ChapterService

        db = await _connect(db_path)
        service = ChapterService(db)

        results = await service.search("p1", "knight")

        await db.close()

        assert len(results) == 1
        assert results[0]["id"] == "c2"

    async def test_search_no_match(self, db_path: str) -> None:
        """Searching for a non-existent term returns an empty list."""
        from app.services.chapter import ChapterService

        db = await _connect(db_path)
        service = ChapterService(db)

        results = await service.search("p1", "nonexistent_xyz")

        await db.close()

        assert results == []

    async def test_search_project_isolation(self, db_path: str) -> None:
        """Searching 'dragon' in p1 should not return results from p2."""
        from app.services.chapter import ChapterService

        db = await _connect(db_path)
        service = ChapterService(db)

        results = await service.search("p1", "dragon")

        await db.close()

        p1_ids = {r["id"] for r in results}
        assert "c1" in p1_ids
        assert "c3" not in p1_ids


# ---------------------------------------------------------------------------
# ReviewService.search
# ---------------------------------------------------------------------------


class TestReviewServiceSearch:
    """Tests for ReviewService.search(project_id, query)."""

    async def test_search_by_content_type(self, db_path: str) -> None:
        """Searching 'chapter' should return reviews with content_type='chapter'."""
        from app.services.review import ReviewService

        db = await _connect(db_path)
        service = ReviewService(db)

        results = await service.search("p1", "chapter")

        await db.close()

        assert len(results) == 1
        assert results[0]["id"] == "r1"
        assert results[0]["content_type"] == "chapter"

    async def test_search_by_content_id(self, db_path: str) -> None:
        """Searching 'c1' should match reviews with content_id='c1'."""
        from app.services.review import ReviewService

        db = await _connect(db_path)
        service = ReviewService(db)

        results = await service.search("p1", "c1")

        await db.close()

        assert len(results) == 1
        assert results[0]["id"] == "r1"

    async def test_search_no_match(self, db_path: str) -> None:
        """Searching for a non-existent term returns an empty list."""
        from app.services.review import ReviewService

        db = await _connect(db_path)
        service = ReviewService(db)

        results = await service.search("p1", "nonexistent_xyz")

        await db.close()

        assert results == []

    async def test_search_project_isolation(self, db_path: str) -> None:
        """Searching 'chapter' in p1 should not return results from p2."""
        from app.services.review import ReviewService

        db = await _connect(db_path)
        service = ReviewService(db)

        results_p1 = await service.search("p1", "chapter")
        results_p2 = await service.search("p2", "chapter")

        await db.close()

        p1_ids = {r["id"] for r in results_p1}
        p2_ids = {r["id"] for r in results_p2}

        assert "r1" in p1_ids
        assert "r2" not in p1_ids
        assert "r2" in p2_ids
        assert "r1" not in p2_ids


# ---------------------------------------------------------------------------
# ReviewService.delete
# ---------------------------------------------------------------------------


class TestReviewServiceDelete:
    """Tests for ReviewService.delete(review_id, project_id)."""

    async def test_delete_existing_review(self, db_path: str) -> None:
        """Deleting an existing review returns True."""
        from app.services.review import ReviewService

        db = await _connect(db_path)
        service = ReviewService(db)

        result = await service.delete("r1", "p1")

        await db.close()

        assert result is True

    async def test_delete_nonexistent_review(self, db_path: str) -> None:
        """Deleting a non-existent review returns False."""
        from app.services.review import ReviewService

        db = await _connect(db_path)
        service = ReviewService(db)

        result = await service.delete("nonexistent", "p1")

        await db.close()

        assert result is False

    async def test_delete_wrong_project(self, db_path: str) -> None:
        """Deleting a review with wrong project_id returns False and does not delete."""
        from app.services.review import ReviewService

        db = await _connect(db_path)
        service = ReviewService(db)

        # r1 belongs to p1, not p2
        result = await service.delete("r1", "p2")

        # Verify it still exists under p1
        still_exists = await service.get("r1", "p1")

        await db.close()

        assert result is False
        assert still_exists is not None

    async def test_delete_removes_review(self, db_path: str) -> None:
        """After deletion, get returns None for the deleted review."""
        from app.services.review import ReviewService

        db = await _connect(db_path)
        service = ReviewService(db)

        await service.delete("r1", "p1")
        result = await service.get("r1", "p1")

        await db.close()

        assert result is None
