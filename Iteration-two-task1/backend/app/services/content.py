"""Content service facade for the AI-powered web novel generation platform.

Provides a unified access layer for creative content (world settings, characters,
outlines, chapters, and reviews) backed by SQLite metadata and Markdown file storage.

This module re-exports storage classes and exposes ``ContentService`` as a
backward-compatible facade that delegates to domain-specific services.
"""

from __future__ import annotations

from typing import Any

import aiosqlite

from app.services.chapter import ChapterService
from app.services.character import CharacterService
from app.services.outline import OutlineService
from app.services.review import ReviewService
from app.services.storage import ContentStorage, FileSystemStorage
from app.services.world import WorldSettingService

# Re-export storage classes for backward compatibility
__all__ = ["ContentService", "ContentStorage", "FileSystemStorage"]


class ContentService:
    """Unified content access layer combining SQLite metadata with file storage.

    This facade delegates all operations to domain-specific services while
    maintaining the exact same public API as the original monolithic class.
    """

    def __init__(self, db: aiosqlite.Connection, storage: FileSystemStorage | None = None):
        """Initialize the service with a database connection and optional storage backend.

        Args:
            db: An aiosqlite connection for metadata queries.
            storage: File storage backend; defaults to FileSystemStorage.
        """
        self.db = db
        self.storage = storage or FileSystemStorage()
        self._world = WorldSettingService(db, self.storage)
        self._character = CharacterService(db, self.storage)
        self._outline = OutlineService(db, self.storage)
        self._chapter = ChapterService(db, self.storage)
        self._review = ReviewService(db, self.storage)

    # ------------------------------------------------------------------
    # World settings
    # ------------------------------------------------------------------

    async def create_world_setting(
        self, project_id: str, world_setting_id: str, name: str, content: str, summary: str = ""
    ) -> dict[str, Any]:
        """Create a world setting."""
        return await self._world.create(project_id, world_setting_id, name, content, summary)

    async def get_world_setting(self, world_setting_id: str, project_id: str) -> dict[str, Any] | None:
        """Retrieve a world setting by ID."""
        return await self._world.get(world_setting_id, project_id)

    async def update_world_setting(
        self,
        world_setting_id: str,
        project_id: str,
        content: str,
        **kwargs: str | None,
    ) -> dict[str, Any] | None:
        """Update a world setting."""
        return await self._world.update(world_setting_id, project_id, content, **kwargs)

    async def delete_world_setting(self, world_setting_id: str, project_id: str) -> bool:
        """Delete a world setting and its content file."""
        return await self._world.delete(world_setting_id, project_id)

    async def search_world_settings(self, project_id: str, query: str) -> list[dict[str, Any]]:
        """Search world settings by name or summary."""
        return await self._world.search(project_id, query)

    async def get_all_world_settings(self, project_id: str) -> list[dict[str, Any]]:
        """List all world settings for a project."""
        return await self._world.list_all(project_id)

    # ------------------------------------------------------------------
    # Characters
    # ------------------------------------------------------------------

    async def create_character(
        self,
        project_id: str,
        character_id: str,
        name: str,
        content: str,
        summary: str = "",
    ) -> dict[str, Any]:
        """Create a character."""
        return await self._character.create(project_id, character_id, name, content, summary)

    async def get_character(self, character_id: str, project_id: str) -> dict[str, Any] | None:
        """Retrieve a character by ID."""
        return await self._character.get(character_id, project_id)

    async def update_character(
        self,
        character_id: str,
        project_id: str,
        content: str,
        **kwargs: str | None,
    ) -> dict[str, Any] | None:
        """Update a character."""
        return await self._character.update(character_id, project_id, content, **kwargs)

    async def delete_character(self, character_id: str, project_id: str) -> bool:
        """Delete a character and its content file."""
        return await self._character.delete(character_id, project_id)

    async def search_characters(self, project_id: str, query: str) -> list[dict[str, Any]]:
        """Search characters by name or summary."""
        return await self._character.search(project_id, query)

    async def get_all_characters(self, project_id: str) -> list[dict[str, Any]]:
        """List all characters for a project."""
        return await self._character.list_all(project_id)

    # ------------------------------------------------------------------
    # Outlines
    # ------------------------------------------------------------------

    async def create_outline(
        self,
        project_id: str,
        outline_id: str,
        title: str,
        content: str,
        outline_type: str = "chapter",
        parent_id: str | None = None,
        sort_order: int = 0,
    ) -> dict[str, Any]:
        """Create an outline."""
        return await self._outline.create(project_id, outline_id, title, content, outline_type, parent_id, sort_order)

    async def get_outline(self, outline_id: str, project_id: str) -> dict[str, Any] | None:
        """Retrieve an outline by ID."""
        return await self._outline.get(outline_id, project_id)

    async def update_outline(
        self,
        outline_id: str,
        project_id: str,
        content: str,
        **kwargs: str | int | None,
    ) -> dict[str, Any] | None:
        """Update an outline."""
        return await self._outline.update(outline_id, project_id, content, **kwargs)

    async def delete_outline(self, outline_id: str, project_id: str) -> bool:
        """Delete an outline and its content file."""
        return await self._outline.delete(outline_id, project_id)

    async def get_outline_children(self, parent_id: str, project_id: str) -> list[dict[str, Any]]:
        """Retrieve child outlines for a given parent."""
        return await self._outline.get_children(parent_id, project_id)

    async def get_root_outline(self, project_id: str) -> dict[str, Any] | None:
        """Retrieve the root outline for a project."""
        return await self._outline.get_root(project_id)

    async def get_all_outlines(self, project_id: str) -> list[dict[str, Any]]:
        """List all outlines for a project."""
        return await self._outline.list_all(project_id)

    async def get_outline_tree(self, outline_id: str, project_id: str) -> dict[str, Any] | None:
        """Retrieve the subtree rooted at outline_id (without content)."""
        return await self._outline.get_tree(outline_id, project_id)

    async def search_outlines(self, project_id: str, query: str) -> list[dict[str, Any]]:
        """Search outlines by title."""
        return await self._outline.search(project_id, query)

    # ------------------------------------------------------------------
    # Chapters
    # ------------------------------------------------------------------

    async def create_chapter(
        self,
        project_id: str,
        chapter_id: str,
        title: str,
        content: str,
        word_count: int = 0,
        chapter_number: int | None = None,
        summary: str | None = None,
        published_at: str | None = None,
    ) -> dict[str, Any]:
        """Create a chapter."""
        return await self._chapter.create(
            project_id, chapter_id, title, content, word_count, chapter_number, summary, published_at
        )

    async def get_chapter(self, chapter_id: str, project_id: str) -> dict[str, Any] | None:
        """Retrieve a chapter by ID."""
        return await self._chapter.get(chapter_id, project_id)

    async def update_chapter(
        self,
        chapter_id: str,
        project_id: str,
        content: str,
        **kwargs: str | int | None,
    ) -> dict[str, Any] | None:
        """Update a chapter."""
        return await self._chapter.update(chapter_id, project_id, content, **kwargs)

    async def delete_chapter(self, chapter_id: str, project_id: str) -> bool:
        """Delete a chapter and its content file."""
        return await self._chapter.delete(chapter_id, project_id)

    async def get_all_chapters(self, project_id: str) -> list[dict[str, Any]]:
        """List all chapters for a project."""
        return await self._chapter.list_all(project_id)

    async def search_chapters(self, project_id: str, query: str) -> list[dict[str, Any]]:
        """Search chapters by title or summary."""
        return await self._chapter.search(project_id, query)

    # ------------------------------------------------------------------
    # Reviews
    # ------------------------------------------------------------------

    async def create_review(
        self,
        review_id: str,
        project_id: str,
        content_type: str,
        content_id: str,
        issues: list[str],
        suggestions: list[str],
        overall_score: float | None = None,
    ) -> dict[str, Any]:
        """Create a review."""
        return await self._review.create(
            review_id, project_id, content_type, content_id, issues, suggestions, overall_score
        )

    async def get_review(self, review_id: str, project_id: str) -> dict[str, Any] | None:
        """Retrieve a single review by ID."""
        return await self._review.get(review_id, project_id)

    async def get_reviews_by_content(self, project_id: str, content_type: str, content_id: str) -> list[dict[str, Any]]:
        """Retrieve all reviews for a specific content item."""
        return await self._review.get_by_content(project_id, content_type, content_id)

    async def get_all_reviews(self, project_id: str, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """List all reviews for a project."""
        return await self._review.list_all(project_id, limit, offset)

    async def search_reviews(self, project_id: str, query: str) -> list[dict[str, Any]]:
        """Search reviews by content_type or content_id."""
        return await self._review.search(project_id, query)

    async def delete_review(self, review_id: str, project_id: str) -> bool:
        """Delete a review by ID."""
        return await self._review.delete(review_id, project_id)
