"""Unit tests for LangChain @tool decorated functions from tool_factory.

These tests verify that:
1. All tools from tool_factory are properly created and async
2. Tools receive project_id through closure binding
3. Tool names and descriptions are properly set
"""

import inspect

import pytest

from app.core.agent.tool_factory import (
    create_all_tools,
    create_chapter_tools,
    create_character_tools,
    create_plot_tools,
    create_review_tools,
    create_world_tools,
)


class TestToolSignatures:
    """Verify tool_factory creates async tools with correct signatures."""

    def test_create_world_setting_is_sync(self) -> None:
        """World setting tools should be sync functions."""
        tools = create_world_tools("test-project")
        for t in tools:
            assert t.coroutine is None, f"{t.name} should be sync (coroutine is None)"

    def test_create_character_tools_is_sync(self) -> None:
        """Character tools should be sync functions."""
        tools = create_character_tools("test-project")
        for t in tools:
            assert t.coroutine is None, f"{t.name} should be sync (coroutine is None)"

    def test_create_plot_tools_is_sync(self) -> None:
        """Plot tools should be sync functions."""
        tools = create_plot_tools("test-project")
        for t in tools:
            assert t.coroutine is None, f"{t.name} should be sync (coroutine is None)"

    def test_create_chapter_tools_is_sync(self) -> None:
        """Chapter tools should be sync functions."""
        tools = create_chapter_tools("test-project")
        for t in tools:
            assert t.coroutine is None, f"{t.name} should be sync (coroutine is None)"

    def test_create_review_tools_is_sync(self) -> None:
        """Review tools should be sync functions."""
        tools = create_review_tools("test-project")
        for t in tools:
            assert t.coroutine is None, f"{t.name} should be sync (coroutine is None)"

    def test_all_tools_have_name(self) -> None:
        """All tools should have a name property."""
        tools = create_all_tools("test-project")
        for t in tools:
            assert hasattr(t, "name"), f"{t} should have name attribute"
            assert isinstance(t.name, str), f"{t.name} should be str"
            assert len(t.name) > 0, f"{t.name} should not be empty"

    def test_all_tools_have_description(self) -> None:
        """All tools should have a description property."""
        tools = create_all_tools("test-project")
        for t in tools:
            assert hasattr(t, "description"), f"{t} should have description attribute"
            assert isinstance(t.description, str), f"{t.description} should be str"

    def test_world_tools_correct_names(self) -> None:
        """World tools should have expected names."""
        tools = create_world_tools("test-project")
        names = {t.name for t in tools}
        assert names == {
            "create_world_setting",
            "search_world_setting",
            "edit_world_setting",
            "delete_world_setting",
        }

    def test_character_tools_correct_names(self) -> None:
        """Character tools should have expected names."""
        tools = create_character_tools("test-project")
        names = {t.name for t in tools}
        assert names == {
            "create_character",
            "search_characters",
            "edit_character",
            "delete_character",
        }

    def test_plot_tools_correct_names(self) -> None:
        """Plot tools should have expected names."""
        tools = create_plot_tools("test-project")
        names = {t.name for t in tools}
        assert names == {
            "create_outline",
            "edit_outline",
            "delete_outline",
        }

    def test_chapter_tools_correct_names(self) -> None:
        """Chapter tools should have expected names."""
        tools = create_chapter_tools("test-project")
        names = {t.name for t in tools}
        assert names == {
            "write_chapter",
            "edit_chapter",
            "delete_chapter",
        }

    def test_review_tools_correct_names(self) -> None:
        """Review tools should have expected names."""
        tools = create_review_tools("test-project")
        names = {t.name for t in tools}
        assert names == {"review_content", "delete_review"}

    def test_project_id_bound_via_closure(self) -> None:
        """project_id should be bound to tools via closure, not as parameter."""
        tools = create_world_tools("my-test-project-id")
        create_tool = next(t for t in tools if t.name == "create_world_setting")
        # @tool wraps sync function - actual function is at .func
        sig = inspect.signature(create_tool.func)
        params = list(sig.parameters.keys())
        assert "project_id" not in params, "project_id should not be a parameter - it's captured in closure"


class TestSubagentFactory:
    """Test that subagent factories use langchain.agents.create_agent."""

    def test_create_world_builder_returns_graph(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """create_world_builder_agent should return a compiled graph."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        from app.core.agent.langchain_subagents import create_world_builder_agent

        agent = create_world_builder_agent("test-project")
        assert agent is not None
        # v1 create_agent returns a compiled graph with nodes
        assert hasattr(agent, "nodes")
