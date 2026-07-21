"""Tests for tool error handling in tool_factory.

These tests verify that:
1. Database errors are caught and returned as error strings (not raised)
2. CRUD tools accept content directly and save without LLM calls
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch


class TestCreateWorldSettingErrorHandling:
    """Test error handling in create_world_setting tool."""

    def test_db_failure_returns_error_string(self) -> None:
        """When DB fails, should return error string not raise."""
        from app.core.agent.tool_factory import create_world_tools

        tools = create_world_tools("test-project")
        create_tool = next(t for t in tools if t.name == "create_world_setting")

        with patch("app.core.agent.tool_factory.get_db") as mock_get_db:
            mock_get_db.side_effect = RuntimeError("Database locked")

            result = create_tool.func(name="Test World", content="World content here")

        assert result.startswith("Error:")
        assert "Database error" in result


class TestSearchWorldSettingErrorHandling:
    """Test error handling in search_world_setting tool."""

    def test_db_error_returns_error_string(self) -> None:
        """When DB fails, should return error string not raise."""
        from app.core.agent.tool_factory import create_world_tools

        tools = create_world_tools("test-project")
        search_tool = next(t for t in tools if t.name == "search_world_setting")

        with patch("app.core.agent.tool_factory.get_db") as mock_get_db:
            mock_get_db.side_effect = RuntimeError("Database connection failed")

            result = search_tool.func(query="test")

        assert result.startswith("Error:")
        assert "Database error" in result


class TestEditWorldSettingErrorHandling:
    """Test error handling in edit_world_setting tool."""

    def test_not_found_returns_error_string(self) -> None:
        """When world setting not found, should return error string."""
        from app.core.agent.tool_factory import create_world_tools

        tools = create_world_tools("test-project")
        edit_tool = next(t for t in tools if t.name == "edit_world_setting")

        with patch("app.core.agent.tool_factory.ContentService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_world_setting = AsyncMock(return_value=None)
            mock_service_class.return_value = mock_service

            result = edit_tool.func(world_setting_id="nonexistent", content="new content")

        assert result.startswith("Error:")
        assert "not found" in result

    def test_db_error_returns_error_string(self) -> None:
        """When DB fails, should return error string not raise."""
        from app.core.agent.tool_factory import create_world_tools

        tools = create_world_tools("test-project")
        edit_tool = next(t for t in tools if t.name == "edit_world_setting")

        with patch("app.core.agent.tool_factory.get_db") as mock_get_db:
            mock_get_db.side_effect = RuntimeError("Database connection failed")

            result = edit_tool.func(world_setting_id="ws-1", content="new content")

        assert result.startswith("Error:")
        assert "Database or filesystem error" in result


class TestCreateCharacterErrorHandling:
    """Test error handling in create_character tool."""

    def test_db_failure_returns_error_string(self) -> None:
        """When DB fails, should return error string not raise."""
        from app.core.agent.tool_factory import create_character_tools

        tools = create_character_tools("test-project")
        create_tool = next(t for t in tools if t.name == "create_character")

        with patch("app.core.agent.tool_factory.get_db") as mock_get_db:
            mock_get_db.side_effect = RuntimeError("Database locked")

            result = create_tool.func(name="Test Character", content="Character content here")

        assert result.startswith("Error:")
        assert "Database error" in result


class TestSearchCharactersErrorHandling:
    """Test error handling in search_characters tool."""

    def test_db_error_returns_error_string(self) -> None:
        """When DB fails, should return error string not raise."""
        from app.core.agent.tool_factory import create_character_tools

        tools = create_character_tools("test-project")
        search_tool = next(t for t in tools if t.name == "search_characters")

        with patch("app.core.agent.tool_factory.get_db") as mock_get_db:
            mock_get_db.side_effect = RuntimeError("Database connection failed")

            result = search_tool.func(query="test")

        assert result.startswith("Error:")
        assert "Database error" in result


class TestEditCharacterErrorHandling:
    """Test error handling in edit_character tool."""

    def test_not_found_returns_error_string(self) -> None:
        """When character not found, should return error string."""
        from app.core.agent.tool_factory import create_character_tools

        tools = create_character_tools("test-project")
        edit_tool = next(t for t in tools if t.name == "edit_character")

        with patch("app.core.agent.tool_factory.ContentService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_character = AsyncMock(return_value=None)
            mock_service_class.return_value = mock_service

            result = edit_tool.func(character_id="nonexistent", content="new content")

        assert result.startswith("Error:")
        assert "not found" in result


class TestCreateOutlineErrorHandling:
    """Test error handling in create_outline tool."""

    def test_db_failure_returns_error_string(self) -> None:
        """When DB fails, should return error string not raise."""
        from app.core.agent.tool_factory import create_plot_tools

        tools = create_plot_tools("test-project")
        create_tool = next(t for t in tools if t.name == "create_outline")

        with patch("app.core.agent.tool_factory.get_db") as mock_get_db:
            mock_get_db.side_effect = RuntimeError("Database locked")

            result = create_tool.func(title="Test Outline", content="Outline content here")

        assert result.startswith("Error:")
        assert "Database error" in result


class TestEditOutlineErrorHandling:
    """Test error handling in edit_outline tool."""

    def test_not_found_returns_error_string(self) -> None:
        """When outline not found, should return error string."""
        from app.core.agent.tool_factory import create_plot_tools

        tools = create_plot_tools("test-project")
        edit_tool = next(t for t in tools if t.name == "edit_outline")

        with patch("app.core.agent.tool_factory.ContentService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_outline = AsyncMock(return_value=None)
            mock_service_class.return_value = mock_service

            result = edit_tool.func(outline_id="nonexistent", content="new content")

        assert result.startswith("Error:")
        assert "not found" in result


class TestWriteChapterErrorHandling:
    """Test error handling in write_chapter tool."""

    def test_db_failure_returns_error_string(self) -> None:
        """When DB fails, should return error string not raise."""
        from app.core.agent.tool_factory import create_chapter_tools

        tools = create_chapter_tools("test-project")
        write_tool = next(t for t in tools if t.name == "write_chapter")

        with patch("app.core.agent.tool_factory.get_db") as mock_get_db:
            mock_get_db.side_effect = RuntimeError("Database locked")

            result = write_tool.func(title="Test Chapter", content="Chapter content here")

        assert result.startswith("Error:")
        assert "Database error" in result


class TestEditChapterErrorHandling:
    """Test error handling in edit_chapter tool."""

    def test_not_found_returns_error_string(self) -> None:
        """When chapter not found, should return error string."""
        from app.core.agent.tool_factory import create_chapter_tools

        tools = create_chapter_tools("test-project")
        edit_tool = next(t for t in tools if t.name == "edit_chapter")

        with patch("app.core.agent.tool_factory.ContentService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.update_chapter = AsyncMock(return_value=None)
            mock_service_class.return_value = mock_service

            result = edit_tool.func(chapter_id="nonexistent", content="new content")

        assert result.startswith("Error:")
        assert "not found" in result


class TestReviewContentErrorHandling:
    """Test error handling in review_content tool."""

    def test_db_failure_returns_error_string(self) -> None:
        """When DB fails, should return error string not raise."""
        from app.core.agent.tool_factory import create_review_tools

        tools = create_review_tools("test-project")
        review_tool = next(t for t in tools if t.name == "review_content")

        with patch("app.core.agent.tool_factory.get_db") as mock_get_db:
            mock_get_db.side_effect = RuntimeError("Database locked")

            result = review_tool.func(content_type="chapter", title="Test", content="Some content")

        assert result.startswith("Error:")
        assert "Database error" in result


class TestReadToolsErrorHandling:
    """Test error handling in create_read_tools read-only tools."""

    def test_query_content_db_error(self) -> None:
        """When DB fails, should return error string."""
        from app.core.agent.tool_factory import create_read_tools

        tools = create_read_tools("test-project")
        query_tool = next(t for t in tools if t.name == "query_content")

        with patch("app.core.agent.tool_factory.get_db") as mock_get_db:
            mock_get_db.side_effect = RuntimeError("Database connection failed")

            result = query_tool.func(domain="world")

        assert result.startswith("Error:")
        assert "Database error" in result

    def test_get_content_db_error(self) -> None:
        """When DB fails, should return error string."""
        from app.core.agent.tool_factory import create_read_tools

        tools = create_read_tools("test-project")
        get_tool = next(t for t in tools if t.name == "get_content")

        with patch("app.core.agent.tool_factory.get_db") as mock_get_db:
            mock_get_db.side_effect = RuntimeError("Database connection failed")

            result = get_tool.func(domain="character", content_id="test-id")

        assert result.startswith("Error:")
        assert "Database error" in result

    def test_get_outline_tree_db_error(self) -> None:
        """When DB fails, should return error string."""
        from app.core.agent.tool_factory import create_read_tools

        tools = create_read_tools("test-project")
        tree_tool = next(t for t in tools if t.name == "get_outline_tree")

        with patch("app.core.agent.tool_factory.get_db") as mock_get_db:
            mock_get_db.side_effect = RuntimeError("Database connection failed")

            result = tree_tool.func()

        assert result.startswith("Error:")
        assert "Database error" in result


class TestContextWindowExceeded:
    """Test that context window exceeded errors are classified correctly."""

    def test_context_window_error_not_retryable(self) -> None:
        """Context window errors should not be retryable."""
        from app.core.errors import ErrorCode, classify_llm_error

        exc = Exception("Context window exceeded: 250k tokens")
        result = classify_llm_error(exc)

        assert result.error_code == ErrorCode.CONTEXT_WINDOW_EXCEEDED
        assert result.retryable is False

    def test_token_limit_error_not_retryable(self) -> None:
        """Token limit errors should not be retryable."""
        from app.core.errors import ErrorCode, classify_llm_error

        exc = Exception("Token limit reached")
        result = classify_llm_error(exc)

        assert result.error_code == ErrorCode.CONTEXT_WINDOW_EXCEEDED
        assert result.retryable is False
