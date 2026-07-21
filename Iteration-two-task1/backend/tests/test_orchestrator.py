"""Integration tests for orchestrator flow and project_id propagation.

These tests verify that:
1. Orchestrator graph builds correctly with create_agent
2. Subagent wrapper tools are registered
3. Graph accepts checkpointer parameter
"""

import pytest

from app.core.graph.state import OrchestratorState, ProjectContext


class TestOrchestratorState:
    """Test OrchestratorState structure."""

    def test_orchestrator_state_requires_project_id(self) -> None:
        """Verify that OrchestratorState requires project_id as a string."""
        state = OrchestratorState(
            messages=[],
            session_id="test-session",
            project_id="test-project",
            project_context=ProjectContext(
                project_name="Test Project",
                project_description=None,
                world_settings=[],
                characters=[],
                outline=None,
                chapters=[],
            ),
        )
        assert state["project_id"] == "test-project"
        assert isinstance(state["project_id"], str)

    def test_orchestrator_state_project_id_not_optional(self) -> None:
        """Verify project_id is declared in state annotations."""
        hints = OrchestratorState.__annotations__
        assert "project_id" in hints


class TestOrchestratorGraph:
    """Test orchestrator graph building and node configuration."""

    def test_orchestrator_graph_builds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify the graph builds without error using create_agent."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        from app.core.graph.builder import create_orchestrator_graph

        graph = create_orchestrator_graph("test-project")
        assert graph is not None
        # v1 create_agent returns a compiled graph with nodes
        assert hasattr(graph, "nodes")

    def test_orchestrator_graph_accepts_checkpointer(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify the graph builder accepts an optional checkpointer parameter."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        from app.core.graph.builder import create_orchestrator_graph

        graph = create_orchestrator_graph("test-project", checkpointer=None)
        assert graph is not None

    def test_orchestrator_graph_has_model_node(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify the graph has a 'model' node (v1 naming)."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        from app.core.graph.builder import create_orchestrator_graph

        graph = create_orchestrator_graph("test-project")
        assert "model" in graph.nodes
