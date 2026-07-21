"""Review domain service.

Encapsulates CRUD and listing operations for reviews with JSON
serialization helpers for list fields.
"""

from __future__ import annotations

import json
from typing import Any

import aiosqlite

from app.services.base import BaseContentService


class ReviewService(BaseContentService):
    """Service for review records."""

    @staticmethod
    def _serialize_lists(data: list[str]) -> str:
        """Serialize a list of strings to a JSON string.

        Args:
            data: List of strings to serialize.

        Returns:
            JSON-encoded string.
        """
        return json.dumps(data)

    @staticmethod
    def _deserialize_lists(value: str | None) -> list[str]:
        """Deserialize a JSON string back to a list of strings.

        Args:
            value: JSON-encoded string or None.

        Returns:
            Python list, or empty list if value is None/empty.
        """
        if not value:
            return []
        return json.loads(value)  # type: ignore[no-any-return]

    def _deserialize_row(self, row: aiosqlite.Row) -> dict[str, Any]:
        """Convert a database row into a dict with deserialized list fields.

        Args:
            row: aiosqlite Row object.

        Returns:
            Dictionary with issues and suggestions as Python lists.
        """
        result: dict[str, Any] = dict(row)
        result["issues"] = self._deserialize_lists(result.get("issues"))
        result["suggestions"] = self._deserialize_lists(result.get("suggestions"))
        return result

    async def create(
        self,
        review_id: str,
        project_id: str,
        content_type: str,
        content_id: str,
        issues: list[str],
        suggestions: list[str],
        overall_score: float | None = None,
    ) -> dict[str, Any]:
        """Create a review record in SQLite, serializing lists to JSON.

        Args:
            review_id: Unique identifier for the review.
            project_id: Identifier of the owning project.
            content_type: Type of content being reviewed (e.g., "chapter").
            content_id: Identifier of the content being reviewed.
            issues: List of identified issues.
            suggestions: List of improvement suggestions.
            overall_score: Optional numeric score for the review.

        Returns:
            A dictionary representing the created review.
        """
        await self.db.execute(
            """
            INSERT INTO reviews (id, project_id, content_type, content_id, issues, suggestions, overall_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review_id,
                project_id,
                content_type,
                content_id,
                self._serialize_lists(issues),
                self._serialize_lists(suggestions),
                overall_score,
            ),
        )
        await self.db.commit()

        return {
            "id": review_id,
            "project_id": project_id,
            "content_type": content_type,
            "content_id": content_id,
            "issues": issues,
            "suggestions": suggestions,
            "overall_score": overall_score,
        }

    async def get(self, review_id: str, project_id: str) -> dict[str, Any] | None:
        """Retrieve a single review by ID, deserializing JSON fields.

        Args:
            review_id: Unique identifier of the review.
            project_id: Identifier of the owning project.

        Returns:
            A review dictionary with issues and suggestions as lists, or None if not found.
        """
        cursor = await self.db.execute(
            "SELECT * FROM reviews WHERE id = ? AND project_id = ?",
            (review_id, project_id),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return self._deserialize_row(row)

    async def get_by_content(self, project_id: str, content_type: str, content_id: str) -> list[dict[str, Any]]:
        """Retrieve all reviews for a specific content item, deserializing JSON fields.

        Args:
            project_id: Identifier of the owning project.
            content_type: Type of content being reviewed.
            content_id: Identifier of the content being reviewed.

        Returns:
            A list of review dictionaries with issues and suggestions as lists.
        """
        cursor = await self.db.execute(
            """
            SELECT * FROM reviews WHERE project_id = ? AND content_type = ? AND content_id = ?
            """,
            (project_id, content_type, content_id),
        )
        rows = await cursor.fetchall()
        return [self._deserialize_row(row) for row in rows]

    async def list_all(self, project_id: str, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Retrieve all reviews for a project, deserializing JSON fields.

        Args:
            project_id: Identifier of the owning project.
            limit: Maximum number of reviews to return.
            offset: Number of reviews to skip for pagination.

        Returns:
            A list of review dictionaries with issues and suggestions as lists.
        """
        cursor = await self.db.execute(
            "SELECT * FROM reviews WHERE project_id = ? LIMIT ? OFFSET ?",
            (project_id, limit, offset),
        )
        rows = await cursor.fetchall()
        return [self._deserialize_row(row) for row in rows]

    async def search(self, project_id: str, query: str) -> list[dict[str, Any]]:
        """Search reviews by content_type or content_id using a LIKE query.

        Args:
            project_id: Identifier of the owning project.
            query: Search term to match against content_type or content_id.

        Returns:
            A list of matching review dictionaries with deserialized list fields.
        """
        cursor = await self.db.execute(
            "SELECT * FROM reviews WHERE project_id = ? AND (content_type LIKE ? OR content_id LIKE ?)",
            (project_id, f"%{query}%", f"%{query}%"),
        )
        rows = await cursor.fetchall()
        return [self._deserialize_row(row) for row in rows]

    async def delete(self, review_id: str, project_id: str) -> bool:
        """Delete a review by ID and project.

        Args:
            review_id: Unique identifier of the review.
            project_id: Identifier of the owning project.

        Returns:
            True if the review existed and was deleted, False otherwise.
        """
        cursor = await self.db.execute(
            "DELETE FROM reviews WHERE id = ? AND project_id = ?",
            (review_id, project_id),
        )
        await self.db.commit()
        return cursor.rowcount > 0
