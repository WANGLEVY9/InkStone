"""Tests for generic read tools (query_content, get_content, get_outline_tree)."""

import inspect

from app.core.agent.tool_factory import create_read_tools


class TestReadToolSignatures:
    """Verify read tools have correct names and signatures."""

    def test_read_tools_count(self) -> None:
        """create_read_tools should return exactly 3 tools."""
        tools = create_read_tools("test-project")
        assert len(tools) == 3

    def test_read_tools_names(self) -> None:
        """Read tools should have expected names."""
        tools = create_read_tools("test-project")
        names = {t.name for t in tools}
        assert names == {"query_content", "get_content", "get_outline_tree"}

    def test_read_tools_are_sync(self) -> None:
        """Read tools should be sync (coroutine is None)."""
        tools = create_read_tools("test-project")
        for t in tools:
            assert t.coroutine is None, f"{t.name} should be sync"

    def test_query_content_has_domain_param(self) -> None:
        """query_content should have domain and query parameters."""
        tools = create_read_tools("test-project")
        query_tool = next(t for t in tools if t.name == "query_content")
        sig = inspect.signature(query_tool.func)
        params = list(sig.parameters.keys())
        assert "domain" in params
        assert "query" in params

    def test_get_content_has_domain_and_content_id_params(self) -> None:
        """get_content should have domain and content_id parameters."""
        tools = create_read_tools("test-project")
        get_tool = next(t for t in tools if t.name == "get_content")
        sig = inspect.signature(get_tool.func)
        params = list(sig.parameters.keys())
        assert "domain" in params
        assert "content_id" in params

    def test_get_outline_tree_has_optional_outline_id(self) -> None:
        """get_outline_tree should have optional outline_id parameter."""
        tools = create_read_tools("test-project")
        tree_tool = next(t for t in tools if t.name == "get_outline_tree")
        sig = inspect.signature(tree_tool.func)
        params = list(sig.parameters.keys())
        assert "outline_id" in params
        assert sig.parameters["outline_id"].default == ""

    def test_project_id_not_in_params(self) -> None:
        """project_id should be captured via closure, not as parameter."""
        tools = create_read_tools("test-project")
        for t in tools:
            sig = inspect.signature(t.func)
            assert "project_id" not in sig.parameters, f"{t.name} should not have project_id as parameter"
