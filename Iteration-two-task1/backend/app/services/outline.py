"""Outline domain service.

Encapsulates CRUD and hierarchy operations for outlines.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.base import BaseContentService

ALLOWED_OUTLINE_UPDATE: dict[str, str] = {
    "title": "title = ?",
    "type": "type = ?",
    "sort_order": "sort_order = ?",
    "parent_id": "parent_id = ?",
}


class OutlineService(BaseContentService):
    """Service for outline metadata and content."""

    async def create(
        self,
        project_id: str,
        outline_id: str,
        title: str,
        content: str,
        outline_type: str = "chapter",
        parent_id: str | None = None,
        sort_order: int = 0,
    ) -> dict[str, Any]:
        """Create an outline: insert metadata and write content file.

        Args:
            project_id: Identifier of the owning project.
            outline_id: Unique identifier for the outline.
            title: Display title of the outline.
            content: Full Markdown content.
            outline_type: Category of the outline (default: "chapter").
            parent_id: Optional parent outline ID for nested structures.
            sort_order: Ordering value among siblings.

        Returns:
            A dictionary containing the created metadata.
        """
        # Validate level constraints (only for hierarchical types; other types like "main" skip validation)
        if outline_type == "root":
            if parent_id is not None:
                raise ValueError("Root outline must not have a parent_id")
            existing_root = await self.get_root(project_id)
            if existing_root:
                raise ValueError(f"Root outline already exists for project {project_id}")
        elif outline_type == "volume":
            if parent_id is None:
                raise ValueError("Volume outline must have a parent_id")
            parent = await self.get(parent_id, project_id)
            if not parent or parent["type"] != "root":
                raise ValueError("Volume outline parent must be a root outline")
        elif outline_type == "chapter":
            if parent_id is None:
                raise ValueError("Chapter outline must have a parent_id")
            parent = await self.get(parent_id, project_id)
            if not parent or parent["type"] != "volume":
                raise ValueError("Chapter outline parent must be a volume outline")
        # Other types (e.g., "main", "section") are treated as flat/legacy outlines

        file_path = Path(project_id) / "outlines" / f"{outline_id}.md"
        await self.storage.write(file_path, content)

        await self.db.execute(
            """
            INSERT INTO outlines_meta (id, project_id, parent_id, title, file_path, type, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (outline_id, project_id, parent_id, title, str(file_path), outline_type, sort_order),
        )
        await self.db.commit()

        # Re-fetch to get DB-populated timestamps
        cursor = await self.db.execute(
            "SELECT * FROM outlines_meta WHERE id = ? AND project_id = ?",
            (outline_id, project_id),
        )
        row = await cursor.fetchone()
        if not row:
            raise RuntimeError(f"Outline {outline_id} not found after insert")
        return dict(row)

    async def get(self, outline_id: str, project_id: str) -> dict[str, Any] | None:
        """Retrieve an outline by ID, merging metadata with Markdown content.

        Args:
            outline_id: Unique identifier of the outline.
            project_id: Identifier of the owning project.

        Returns:
            A dictionary with metadata and content, or None if not found.
        """
        cursor = await self.db.execute(
            "SELECT * FROM outlines_meta WHERE id = ? AND project_id = ?",
            (outline_id, project_id),
        )
        row = await cursor.fetchone()
        if not row:
            return None

        content = await self.storage.read(Path(row["file_path"]))
        return {**dict(row), "content": content}

    async def update(
        self,
        outline_id: str,
        project_id: str,
        content: str,
        **kwargs: str | int | None,
    ) -> dict[str, Any] | None:
        """Update an outline's Markdown content and optionally its metadata.

        Args:
            outline_id: Unique identifier of the outline.
            project_id: Identifier of the owning project.
            content: New Markdown content.
            **kwargs: Optional metadata fields to update (e.g., title, type, sort_order, parent_id).

        Returns:
            The updated outline dictionary, or None if not found.
        """
        cursor = await self.db.execute(
            "SELECT * FROM outlines_meta WHERE id = ? AND project_id = ?",
            (outline_id, project_id),
        )
        row = await cursor.fetchone()
        if not row:
            return None

        await self.storage.write(Path(row["file_path"]), content)
        await self._update_metadata(
            "outlines_meta",
            ALLOWED_OUTLINE_UPDATE,
            outline_id,
            project_id,
            **kwargs,
        )

        result = dict(row)
        result.update({k: v for k, v in kwargs.items() if k in ALLOWED_OUTLINE_UPDATE and v is not None})
        result["content"] = content
        return result

    async def delete(self, outline_id: str, project_id: str) -> bool:
        """Delete an outline and all its descendants (cascade).

        Args:
            outline_id: Unique identifier of the outline.
            project_id: Identifier of the owning project.

        Returns:
            True if the entity existed and was deleted, False otherwise.
        """
        # Collect all descendants (including self) via recursive CTE
        cursor = await self.db.execute(
            """
            WITH RECURSIVE descendants AS (
                SELECT id FROM outlines_meta WHERE id = ? AND project_id = ?
                UNION ALL
                SELECT om.id FROM outlines_meta om
                JOIN descendants d ON om.parent_id = d.id
                WHERE om.project_id = ?
            )
            SELECT id FROM descendants
            """,
            (outline_id, project_id, project_id),
        )
        rows = await cursor.fetchall()
        if not rows:
            return False

        ids_to_delete = [row["id"] for row in rows]

        # Fetch file paths for all nodes to delete
        placeholders = ",".join("?" for _ in ids_to_delete)
        cursor = await self.db.execute(
            f"SELECT id, file_path FROM outlines_meta WHERE id IN ({placeholders}) AND project_id = ?",
            [*ids_to_delete, project_id],
        )
        file_rows = await cursor.fetchall()
        files_to_delete = {row["id"]: Path(row["file_path"]) for row in file_rows}

        # Delete metadata (children first to respect FK)
        for del_id in reversed(ids_to_delete):
            await self.db.execute(
                "DELETE FROM outlines_meta WHERE id = ? AND project_id = ?",
                (del_id, project_id),
            )
        await self.db.commit()

        # Delete files
        for file_path in files_to_delete.values():
            await self.storage.delete(file_path)

        return True

    async def get_children(self, parent_id: str, project_id: str) -> list[dict[str, Any]]:
        """Retrieve child outlines for a given parent, ordered by sort_order.

        Args:
            parent_id: Unique identifier of the parent outline.
            project_id: Identifier of the owning project.

        Returns:
            A list of child outline metadata dictionaries.
        """
        cursor = await self.db.execute(
            "SELECT * FROM outlines_meta WHERE parent_id = ? AND project_id = ? ORDER BY sort_order",
            (parent_id, project_id),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_root(self, project_id: str) -> dict[str, Any] | None:
        """Retrieve the root outline for a project (type='root', no parent).

        Args:
            project_id: Identifier of the owning project.

        Returns:
            The root outline metadata dictionary, or None if not found.
        """
        cursor = await self.db.execute(
            """
            SELECT * FROM outlines_meta
            WHERE project_id = ? AND parent_id IS NULL AND type = 'root' LIMIT 1
            """,
            (project_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def list_all(self, project_id: str) -> list[dict[str, Any]]:
        """List all outline metadata for a project, excluding Markdown content.

        Args:
            project_id: Identifier of the owning project.

        Returns:
            A list of metadata dictionaries.
        """
        cursor = await self.db.execute(
            """
            SELECT id, project_id, parent_id, title, type, sort_order, created_at, updated_at
            FROM outlines_meta WHERE project_id = ?
            """,
            (project_id,),
        )
        return [dict(row) for row in await cursor.fetchall()]

    async def search(self, project_id: str, query: str) -> list[dict[str, Any]]:
        """Search outlines by title using a LIKE query.

        Args:
            project_id: Identifier of the owning project.
            query: Search term to match against outline titles.

        Returns:
            A list of matching metadata dictionaries.
        """
        cursor = await self.db.execute(
            "SELECT * FROM outlines_meta WHERE project_id = ? AND title LIKE ?",
            (project_id, f"%{query}%"),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_tree(self, node_id: str, project_id: str) -> dict[str, Any] | None:
        """Recursively fetch the subtree rooted at node_id (without content).

        Returns a nested dict with children lists, or None if node not found.
        """
        # Fetch all descendants via recursive CTE
        cursor = await self.db.execute(
            """
            WITH RECURSIVE descendants AS (
                SELECT id, parent_id, title, type, sort_order
                FROM outlines_meta
                WHERE id = ? AND project_id = ?
                UNION ALL
                SELECT om.id, om.parent_id, om.title, om.type, om.sort_order
                FROM outlines_meta om
                JOIN descendants d ON om.parent_id = d.id
                WHERE om.project_id = ?
            )
            SELECT id, parent_id, title, type, sort_order FROM descendants
            """,
            (node_id, project_id, project_id),
        )
        rows = await cursor.fetchall()
        if not rows:
            return None

        # Build lookup: id -> node dict
        nodes: dict[str, dict[str, Any]] = {}
        for row in rows:
            nodes[row["id"]] = {
                "id": row["id"],
                "parent_id": row["parent_id"],
                "title": row["title"],
                "type": row["type"],
                "sort_order": row["sort_order"],
                "children": [],
            }

        # Assemble tree
        root = None
        for node in nodes.values():
            if node["id"] == node_id:
                root = node
            parent_id = node["parent_id"]
            if parent_id and parent_id in nodes:
                nodes[parent_id]["children"].append(node)

        # Sort children by sort_order at each level
        def _sort_children(node: dict[str, Any]) -> None:
            node["children"].sort(key=lambda c: c["sort_order"])
            for child in node["children"]:
                _sort_children(child)

        if root:
            _sort_children(root)

            # Remove parent_id from output (not useful in tree context)
            def _clean(node: dict[str, Any]) -> dict[str, Any]:
                return {
                    "id": node["id"],
                    "title": node["title"],
                    "type": node["type"],
                    "sort_order": node["sort_order"],
                    "children": [_clean(c) for c in node["children"]],
                }

            root = _clean(root)

        return root
