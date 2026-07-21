"""Tool factory for creating LangChain tools with project_id bound via closure.

Since @tool decorator functions are defined at module level and cannot receive
context at definition time, we use a factory pattern to create tools with
project_id pre-bound through closure.
"""

# NOTE: Tools are synchronous by design. LangGraph runs sync tools in a
# thread pool, so asyncio.run() is safe here (no nested event loop).
# Async migration is planned for a future iteration.

from __future__ import annotations

import asyncio
import json
import sqlite3
import uuid
from typing import Any

from langchain.tools import tool

from app.db.connection import get_db
from app.services.content import ContentService

VALID_DOMAINS = {"world", "character", "outline", "chapter", "review"}

_DOMAIN_DISPLAY_KEYS: dict[str, str] = {
    "world": "name",
    "character": "name",
    "outline": "title",
    "chapter": "title",
    "review": "content_type",
}


def _format_error(operation: str, details: str) -> str:
    """Format a consistent error string for tool failures."""
    return f"Error: {operation} failed - {details}"


def create_world_tools(project_id: str) -> list[Any]:
    """Create world setting tools bound to a specific project_id.

    Args:
        project_id: The project ID to scope all operations to

    Returns:
        List of bound tool functions
    """

    @tool
    def create_world_setting(name: str, content: str) -> str:
        """Create a new world setting.

        Args:
            name: Name of the world setting
            content: World setting content in markdown format

        Returns:
            Confirmation message with the created world setting ID
        """
        world_setting_id = str(uuid.uuid4())
        try:

            async def _create() -> dict[str, Any]:
                async with get_db() as db:
                    service = ContentService(db)
                    result = await service.create_world_setting(
                        project_id=project_id,
                        world_setting_id=world_setting_id,
                        name=name,
                        content=content,
                        summary=content[:200] if len(content) > 200 else content,
                    )
                return result

            asyncio.run(_create())
            return f"Successfully created world setting '{name}' (ID: {world_setting_id})."
        except (sqlite3.Error, RuntimeError, OSError, PermissionError) as exc:
            return _format_error("create_world_setting", f"Database error: {exc}")
        except Exception as exc:
            return _format_error("create_world_setting", f"Unexpected error: {exc}")

    @tool
    def search_world_setting(query: str) -> str:
        """Search existing world settings by name or content summary.

        Use this tool when you need to find existing world settings for reference
        or to check for consistency before creating new settings.

        Args:
            query: Search query to match against world setting names or summaries

        Returns:
            JSON string with list of matching world settings
        """
        try:

            async def _search() -> list[dict[str, Any]]:
                async with get_db() as db:
                    service = ContentService(db)
                    results = await service.search_world_settings(project_id, query)
                return results

            results = asyncio.run(_search())
            if not results:
                return "No world settings found matching the query."
            return f"Found {len(results)} world setting(s):\n" + "\n".join(
                f"- {r.get('name', 'Unnamed')} (ID: {r.get('id', 'N/A')})" for r in results
            )
        except (sqlite3.Error, RuntimeError) as exc:
            return _format_error("search_world_setting", f"Database error: {exc}")
        except Exception as exc:
            return _format_error("search_world_setting", f"Unexpected error: {exc}")

    @tool
    def edit_world_setting(
        world_setting_id: str,
        content: str,
        name: str = "",
        summary: str = "",
    ) -> str:
        """Update an existing world setting with revised content.

        Use this tool when the user wants to modify an existing world setting.

        Args:
            world_setting_id: ID of the world setting to edit
            content: Revised world setting content in markdown format
            name: Optional new name for the world setting
            summary: Optional new summary (first 200 chars of content if not provided)

        Returns:
            JSON string with the update result
        """
        kwargs: dict[str, Any] = {}
        if name:
            kwargs["name"] = name
        if summary:
            kwargs["summary"] = summary
        try:

            async def _edit() -> dict[str, Any] | None:
                async with get_db() as db:
                    service = ContentService(db)
                    result = await service.update_world_setting(
                        world_setting_id=world_setting_id,
                        project_id=project_id,
                        content=content,
                        **kwargs,
                    )
                return result

            result = asyncio.run(_edit())
            if result is None:
                return _format_error("edit_world_setting", f"World setting '{world_setting_id}' not found")
            return f"Successfully updated world setting '{name or world_setting_id}'."
        except (sqlite3.Error, RuntimeError, OSError, PermissionError) as exc:
            return _format_error("edit_world_setting", f"Database or filesystem error: {exc}")
        except Exception as exc:
            return _format_error("edit_world_setting", f"Unexpected error: {exc}")

    @tool
    def delete_world_setting(world_setting_id: str) -> str:
        """Delete an existing world setting.

        WARNING: This permanently removes the world setting and its content file.
        Confirm with the user before calling this tool.

        Args:
            world_setting_id: ID of the world setting to delete

        Returns:
            Confirmation message or error
        """
        try:

            async def _delete() -> bool:
                async with get_db() as db:
                    service = ContentService(db)
                    return await service.delete_world_setting(world_setting_id, project_id)

            result = asyncio.run(_delete())
            if not result:
                return _format_error("delete_world_setting", f"World setting '{world_setting_id}' not found")
            return f"Successfully deleted world setting '{world_setting_id}'."
        except (sqlite3.Error, RuntimeError, OSError, PermissionError) as exc:
            return _format_error("delete_world_setting", f"Database or filesystem error: {exc}")
        except Exception as exc:
            return _format_error("delete_world_setting", f"Unexpected error: {exc}")

    return [create_world_setting, search_world_setting, edit_world_setting, delete_world_setting]


def create_character_tools(project_id: str) -> list[Any]:
    """Create character tools bound to a specific project_id.

    Args:
        project_id: The project ID to scope all operations to

    Returns:
        List of bound tool functions
    """

    @tool
    def create_character(name: str, content: str) -> str:
        """Create a new character.

        Args:
            name: Character name
            content: Character content in markdown format

        Returns:
            Confirmation message with the created character ID
        """
        character_id = str(uuid.uuid4())
        try:

            async def _create() -> dict[str, Any]:
                async with get_db() as db:
                    service = ContentService(db)
                    result = await service.create_character(
                        project_id=project_id,
                        character_id=character_id,
                        name=name,
                        content=content,
                        summary=content[:200] if len(content) > 200 else content,
                    )
                return result

            asyncio.run(_create())
            return f"Successfully created character '{name}' (ID: {character_id})."
        except (sqlite3.Error, RuntimeError, OSError, PermissionError) as exc:
            return _format_error("create_character", f"Database error: {exc}")
        except Exception as exc:
            return _format_error("create_character", f"Unexpected error: {exc}")

    @tool
    def search_characters(query: str) -> str:
        """Search existing characters by name or summary.

        Use this tool when you need to find existing characters for reference
        or to ensure consistency when creating new characters.

        Args:
            query: Search query to match against character names or summaries

        Returns:
            JSON string with list of matching characters
        """
        try:

            async def _search() -> list[dict[str, Any]]:
                async with get_db() as db:
                    service = ContentService(db)
                    results = await service.search_characters(project_id, query)
                return results

            results = asyncio.run(_search())
            if not results:
                return "No characters found matching the query."
            return f"Found {len(results)} character(s):\n" + "\n".join(
                f"- {r.get('name', 'Unnamed')} (ID: {r.get('id', 'N/A')})" for r in results
            )
        except (sqlite3.Error, RuntimeError) as exc:
            return _format_error("search_characters", f"Database error: {exc}")
        except Exception as exc:
            return _format_error("search_characters", f"Unexpected error: {exc}")

    @tool
    def edit_character(
        character_id: str,
        content: str,
        name: str = "",
        summary: str = "",
    ) -> str:
        """Update an existing character with revised content.

        Use this tool when the user wants to modify an existing character.

        Args:
            character_id: ID of the character to edit
            content: Revised character content in markdown format
            name: Optional new name for the character
            summary: Optional new summary (first 200 chars of content if not provided)

        Returns:
            JSON string with the update result
        """
        kwargs: dict[str, Any] = {}
        if name:
            kwargs["name"] = name
        if summary:
            kwargs["summary"] = summary
        try:

            async def _edit() -> dict[str, Any] | None:
                async with get_db() as db:
                    service = ContentService(db)
                    result = await service.update_character(
                        character_id=character_id,
                        project_id=project_id,
                        content=content,
                        **kwargs,
                    )
                return result

            result = asyncio.run(_edit())
            if result is None:
                return _format_error("edit_character", f"Character '{character_id}' not found")
            return f"Successfully updated character '{name or character_id}'."
        except (sqlite3.Error, RuntimeError, OSError, PermissionError) as exc:
            return _format_error("edit_character", f"Database or filesystem error: {exc}")
        except Exception as exc:
            return _format_error("edit_character", f"Unexpected error: {exc}")

    @tool
    def delete_character(character_id: str) -> str:
        """Delete an existing character.

        WARNING: This permanently removes the character and its content file.
        Confirm with the user before calling this tool.

        Args:
            character_id: ID of the character to delete

        Returns:
            Confirmation message or error
        """
        try:

            async def _delete() -> bool:
                async with get_db() as db:
                    service = ContentService(db)
                    return await service.delete_character(character_id, project_id)

            result = asyncio.run(_delete())
            if not result:
                return _format_error("delete_character", f"Character '{character_id}' not found")
            return f"Successfully deleted character '{character_id}'."
        except (sqlite3.Error, RuntimeError, OSError, PermissionError) as exc:
            return _format_error("delete_character", f"Database or filesystem error: {exc}")
        except Exception as exc:
            return _format_error("delete_character", f"Unexpected error: {exc}")

    return [create_character, search_characters, edit_character, delete_character]


def create_plot_tools(project_id: str) -> list[Any]:
    """Create plot/outline tools bound to a specific project_id.

    Args:
        project_id: The project ID to scope all operations to

    Returns:
        List of bound tool functions
    """

    @tool
    def create_outline(
        title: str,
        content: str,
        outline_type: str = "chapter",
        parent_id: str = "",
        sort_order: int = 0,
    ) -> str:
        """Create a story outline.

        Outline hierarchy:
        1. root — top-level outline (parent_id="", only one per project)
        2. volume — under root (parent_id=root's ID)
        3. chapter — under volume (parent_id=volume's ID)

        Use get_outline_tree() first to discover existing outlines and their IDs.

        Args:
            title: Title of the outline
            content: Outline content in markdown format
            outline_type: "root", "volume", or "chapter"
            parent_id: ID of the parent outline. Empty string for root.
            sort_order: Display order among siblings (0-based, lower = first)

        Returns:
            Confirmation message with the created outline ID
        """
        outline_id = str(uuid.uuid4())
        effective_parent_id = parent_id if parent_id else None
        try:

            async def _create() -> dict[str, Any]:
                async with get_db() as db:
                    service = ContentService(db)
                    result = await service.create_outline(
                        project_id=project_id,
                        outline_id=outline_id,
                        title=title,
                        content=content,
                        outline_type=outline_type,
                        parent_id=effective_parent_id,
                        sort_order=sort_order,
                    )
                return result

            asyncio.run(_create())
            return f"Successfully created {outline_type} outline '{title}' (ID: {outline_id})."
        except (sqlite3.Error, RuntimeError, OSError, PermissionError) as exc:
            return _format_error("create_outline", f"Database error: {exc}")
        except Exception as exc:
            return _format_error("create_outline", f"Unexpected error: {exc}")

    @tool
    def edit_outline(
        outline_id: str,
        content: str,
        title: str = "",
        sort_order: int = -1,
    ) -> str:
        """Update an existing story outline with revised content.

        Use this tool when you want to modify an existing outline.

        Args:
            outline_id: ID of the outline to edit
            content: Revised outline content in markdown format
            title: Optional new title for the outline (empty = keep current)
            sort_order: New sort order (-1 = keep current)

        Returns:
            JSON string with the update result
        """
        kwargs: dict[str, Any] = {}
        if title:
            kwargs["title"] = title
        if sort_order >= 0:
            kwargs["sort_order"] = sort_order
        try:

            async def _edit() -> dict[str, Any] | None:
                async with get_db() as db:
                    service = ContentService(db)
                    result = await service.update_outline(
                        outline_id=outline_id,
                        project_id=project_id,
                        content=content,
                        **kwargs,
                    )
                return result

            result = asyncio.run(_edit())
            if result is None:
                return _format_error("edit_outline", f"Outline '{outline_id}' not found")
            return f"Successfully updated outline '{title or outline_id}'."
        except (sqlite3.Error, RuntimeError, OSError, PermissionError) as exc:
            return _format_error("edit_outline", f"Database or filesystem error: {exc}")
        except Exception as exc:
            return _format_error("edit_outline", f"Unexpected error: {exc}")

    @tool
    def delete_outline(outline_id: str) -> str:
        """Delete an existing outline.

        WARNING: This permanently removes the outline and all its child outlines.
        Confirm with the user before calling this tool.

        Args:
            outline_id: ID of the outline to delete

        Returns:
            Confirmation message or error
        """
        try:

            async def _delete() -> bool:
                async with get_db() as db:
                    service = ContentService(db)
                    return await service.delete_outline(outline_id, project_id)

            result = asyncio.run(_delete())
            if not result:
                return _format_error("delete_outline", f"Outline '{outline_id}' not found")
            return f"Successfully deleted outline '{outline_id}'."
        except (sqlite3.Error, RuntimeError, OSError, PermissionError) as exc:
            return _format_error("delete_outline", f"Database or filesystem error: {exc}")
        except Exception as exc:
            return _format_error("delete_outline", f"Unexpected error: {exc}")

    return [create_outline, edit_outline, delete_outline]


def create_chapter_tools(project_id: str) -> list[Any]:
    """Create chapter tools bound to a specific project_id.

    Args:
        project_id: The project ID to scope all operations to

    Returns:
        List of bound tool functions
    """

    @tool
    def write_chapter(title: str, content: str) -> str:
        """Write chapter content.

        Args:
            title: Title of the chapter
            content: Chapter content in markdown format

        Returns:
            Confirmation message with the created chapter ID
        """
        chapter_id = str(uuid.uuid4())
        try:

            async def _write() -> dict[str, Any]:
                async with get_db() as db:
                    service = ContentService(db)
                    result = await service.create_chapter(
                        project_id=project_id,
                        chapter_id=chapter_id,
                        title=title,
                        content=content,
                        word_count=len(content.split()),
                    )
                return result

            asyncio.run(_write())
            return f"Successfully wrote chapter '{title}' (ID: {chapter_id})."
        except (sqlite3.Error, RuntimeError, OSError, PermissionError) as exc:
            return _format_error("write_chapter", f"Database error: {exc}")
        except Exception as exc:
            return _format_error("write_chapter", f"Unexpected error: {exc}")

    @tool
    def edit_chapter(
        chapter_id: str,
        content: str,
        title: str = "",
        word_count: int = 0,
        status: str = "",
    ) -> str:
        """Update an existing chapter with revised content.

        Use this tool when the user wants to modify an existing chapter.

        Args:
            chapter_id: ID of the chapter to edit
            content: Revised chapter content in markdown format
            title: Optional new title for the chapter
            word_count: Optional new word count
            status: Optional new status (draft, revised, final)

        Returns:
            JSON string with the update result
        """
        kwargs: dict[str, Any] = {}
        if title:
            kwargs["title"] = title
        if status:
            kwargs["status"] = status
        if word_count > 0:
            kwargs["word_count"] = word_count
        try:

            async def _edit() -> dict[str, Any] | None:
                async with get_db() as db:
                    service = ContentService(db)
                    result = await service.update_chapter(
                        chapter_id=chapter_id,
                        project_id=project_id,
                        content=content,
                        **kwargs,
                    )
                return result

            result = asyncio.run(_edit())
            if result is None:
                return _format_error("edit_chapter", f"Chapter '{chapter_id}' not found")
            return f"Successfully updated chapter '{title or chapter_id}'."
        except (sqlite3.Error, RuntimeError, OSError, PermissionError) as exc:
            return _format_error("edit_chapter", f"Database or filesystem error: {exc}")
        except Exception as exc:
            return _format_error("edit_chapter", f"Unexpected error: {exc}")

    @tool
    def delete_chapter(chapter_id: str) -> str:
        """Delete an existing chapter.

        WARNING: This permanently removes the chapter and its content file.
        Confirm with the user before calling this tool.

        Args:
            chapter_id: ID of the chapter to delete

        Returns:
            Confirmation message or error
        """
        try:

            async def _delete() -> bool:
                async with get_db() as db:
                    service = ContentService(db)
                    return await service.delete_chapter(chapter_id, project_id)

            result = asyncio.run(_delete())
            if not result:
                return _format_error("delete_chapter", f"Chapter '{chapter_id}' not found")
            return f"Successfully deleted chapter '{chapter_id}'."
        except (sqlite3.Error, RuntimeError, OSError, PermissionError) as exc:
            return _format_error("delete_chapter", f"Database or filesystem error: {exc}")
        except Exception as exc:
            return _format_error("delete_chapter", f"Unexpected error: {exc}")

    return [write_chapter, edit_chapter, delete_chapter]


def create_review_tools(project_id: str) -> list[Any]:
    """Create review tools bound to a specific project_id.

    Args:
        project_id: The project ID to scope all operations to

    Returns:
        List of bound tool functions
    """

    @tool
    def review_content(content_type: str, title: str, content: str) -> str:
        """Save a review for existing content.

        Args:
            content_type: Type of content being reviewed (chapter, outline, character)
            title: Title of the content being reviewed
            content: Review content in markdown format

        Returns:
            Confirmation message with the created review ID
        """
        review_id = str(uuid.uuid4())
        try:

            async def _review() -> dict[str, Any]:
                async with get_db() as db:
                    service = ContentService(db)
                    result = await service.create_review(
                        review_id=review_id,
                        project_id=project_id,
                        content_type=content_type,
                        content_id=title,
                        issues=[],
                        suggestions=[content],
                    )
                return result

            asyncio.run(_review())
            return f"Review completed for {content_type}: '{title}' (ID: {review_id})."
        except (sqlite3.Error, RuntimeError) as exc:
            return _format_error("review_content", f"Database error: {exc}")
        except Exception as exc:
            return _format_error("review_content", f"Unexpected error: {exc}")

    @tool
    def delete_review(review_id: str) -> str:
        """Delete an existing review.

        WARNING: This permanently removes the review.
        Confirm with the user before calling this tool.

        Args:
            review_id: ID of the review to delete

        Returns:
            Confirmation message or error
        """
        try:

            async def _delete() -> bool:
                async with get_db() as db:
                    service = ContentService(db)
                    return await service.delete_review(review_id, project_id)

            result = asyncio.run(_delete())
            if not result:
                return _format_error("delete_review", f"Review '{review_id}' not found")
            return f"Successfully deleted review '{review_id}'."
        except (sqlite3.Error, RuntimeError) as exc:
            return _format_error("delete_review", f"Database error: {exc}")
        except Exception as exc:
            return _format_error("delete_review", f"Unexpected error: {exc}")

    return [review_content, delete_review]


def create_read_tools(project_id: str) -> list[Any]:
    """Create generic read tools bound to a specific project_id.

    These tools provide unified read access across all 5 content domains
    (world, character, outline, chapter, review) and replace the old
    per-domain supervisor tools.

    Args:
        project_id: The project ID to scope all operations to

    Returns:
        List of 3 bound read-only tool functions
    """

    @tool
    def query_content(domain: str, query: str = "") -> str:
        """List or search content in a given domain.

        Use this tool to discover existing content before creating or referencing items.

        Args:
            domain: Content domain - one of "world", "character", "outline", "chapter", "review"
            query: Optional search keyword. Leave empty to list all items in the domain.

        Returns:
            Formatted list of matching items with name/title and ID.
        """
        if domain not in VALID_DOMAINS:
            valid = ", ".join(sorted(VALID_DOMAINS))
            return _format_error("query_content", f"Invalid domain '{domain}'. Must be one of: {valid}")
        try:

            async def _query() -> list[dict[str, Any]]:
                async with get_db() as db:
                    service = ContentService(db)
                    if query:
                        search_dispatch: dict[str, Any] = {
                            "world": service.search_world_settings,
                            "character": service.search_characters,
                            "outline": service.search_outlines,
                            "chapter": service.search_chapters,
                            "review": service.search_reviews,
                        }
                        fn = search_dispatch.get(domain)
                        if fn is None:
                            return []
                        results: list[dict[str, Any]] = await fn(project_id, query)
                        return results
                    else:
                        list_dispatch: dict[str, Any] = {
                            "world": service.get_all_world_settings,
                            "character": service.get_all_characters,
                            "outline": service.get_all_outlines,
                            "chapter": service.get_all_chapters,
                            "review": service.get_all_reviews,
                        }
                        fn = list_dispatch.get(domain)
                        if fn is None:
                            return []
                        all_results: list[dict[str, Any]] = await fn(project_id)
                        return all_results

            results = asyncio.run(_query())
            if not results:
                return f"No {domain} content found{' matching the query' if query else ''}."

            name_key = _DOMAIN_DISPLAY_KEYS.get(domain, "name")

            lines = [f"{domain.title()} ({len(results)} total):"]
            for r in results:
                display = r.get(name_key, "Untitled")
                item_id = r.get("id", "N/A")
                summary = r.get("summary", "")
                line = f"- {display} (ID: {item_id})"
                if summary:
                    truncated = summary[:100]
                    line += f"  {truncated}{'...' if len(summary) > 100 else ''}"
                lines.append(line)
            return "\n".join(lines)
        except (sqlite3.Error, RuntimeError) as exc:
            return _format_error("query_content", f"Database error: {exc}")
        except Exception as exc:
            return _format_error("query_content", f"Unexpected error: {exc}")

    @tool
    def get_content(domain: str, content_id: str) -> str:
        """Retrieve full content by ID from a given domain.

        Use this tool to read the complete content of a specific item.

        Args:
            domain: Content domain - one of "world", "character", "outline", "chapter", "review"
            content_id: The unique ID of the content to retrieve

        Returns:
            Full content string including name/title and body, or error if not found.
        """
        if domain not in VALID_DOMAINS:
            valid = ", ".join(sorted(VALID_DOMAINS))
            return _format_error("get_content", f"Invalid domain '{domain}'. Must be one of: {valid}")
        try:

            async def _get() -> dict[str, Any] | None:
                async with get_db() as db:
                    service = ContentService(db)
                    dispatch = {
                        "world": lambda: service.get_world_setting(content_id, project_id),
                        "character": lambda: service.get_character(content_id, project_id),
                        "outline": lambda: service.get_outline(content_id, project_id),
                        "chapter": lambda: service.get_chapter(content_id, project_id),
                        "review": lambda: service.get_review(content_id, project_id),
                    }
                    fn = dispatch.get(domain)
                    if fn is None:
                        return None
                    return await fn()

            result = asyncio.run(_get())
            if result is None:
                return _format_error("get_content", f"{domain.title()} '{content_id}' not found")

            name_key = _DOMAIN_DISPLAY_KEYS.get(domain, "name")
            display = result.get(name_key, "Untitled")
            content = result.get("content", "")
            return f"{display} (ID: {content_id}):\n\n{content}"
        except (sqlite3.Error, RuntimeError) as exc:
            return _format_error("get_content", f"Database error: {exc}")
        except Exception as exc:
            return _format_error("get_content", f"Unexpected error: {exc}")

    @tool
    def get_outline_tree(outline_id: str = "") -> str:
        """Get the outline hierarchy as a tree structure.

        Use this tool to understand the story structure and chapter organization.

        Args:
            outline_id: Optional outline ID to get a subtree. Leave empty to get the root tree.

        Returns:
            JSON string of the tree structure, or message if no outline exists.
        """
        try:

            async def _tree() -> dict[str, Any] | None:
                async with get_db() as db:
                    service = ContentService(db)
                    if outline_id:
                        return await service.get_outline_tree(outline_id, project_id)
                    root = await service.get_root_outline(project_id)
                    if root is None:
                        return None
                    return await service.get_outline_tree(root["id"], project_id)

            tree = asyncio.run(_tree())
            if tree is None:
                return "No outline tree found."
            return json.dumps(tree, indent=2, ensure_ascii=False)
        except (sqlite3.Error, RuntimeError) as exc:
            return _format_error("get_outline_tree", f"Database error: {exc}")
        except Exception as exc:
            return _format_error("get_outline_tree", f"Unexpected error: {exc}")

    return [query_content, get_content, get_outline_tree]


def create_all_tools(project_id: str) -> list[Any]:
    """Create all tools bound to a specific project_id.

    Args:
        project_id: The project ID to scope all operations to

    Returns:
        List of all bound tool functions
    """
    tools: list[Any] = []
    tools.extend(create_world_tools(project_id))
    tools.extend(create_character_tools(project_id))
    tools.extend(create_plot_tools(project_id))
    tools.extend(create_chapter_tools(project_id))
    tools.extend(create_review_tools(project_id))
    return tools
