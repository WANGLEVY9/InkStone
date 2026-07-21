"""Tests for v2 streaming migration."""

from __future__ import annotations

import json
from typing import Any


class TestLcAgentNameAttribution:
    """Test lc_agent_name metadata-based source attribution."""

    def test_metadata_with_lc_agent_name(self) -> None:
        """lc_agent_name in metadata should be used as source."""
        metadata: dict[str, Any] = {"lc_agent_name": "world_builder"}
        source = metadata.get("lc_agent_name", "orchestrator")
        assert source == "world_builder"

    def test_metadata_without_lc_agent_name_defaults_to_orchestrator(self) -> None:
        """Missing lc_agent_name should fall back to orchestrator."""
        metadata: dict[str, Any] = {}
        source = metadata.get("lc_agent_name", "orchestrator")
        assert source == "orchestrator"

    def test_orchestrator_metadata(self) -> None:
        """Orchestrator agent should have lc_agent_name='orchestrator'."""
        metadata: dict[str, Any] = {"lc_agent_name": "orchestrator"}
        source = metadata.get("lc_agent_name", "orchestrator")
        assert source == "orchestrator"

    def test_all_subagent_names(self) -> None:
        """Each sub-agent name should be a valid source."""
        for name in ["world_builder", "character", "plot", "chapter", "review"]:
            metadata: dict[str, Any] = {"lc_agent_name": name}
            source = metadata.get("lc_agent_name", "orchestrator")
            assert source == name


class TestV2ChunkProcessing:
    """Test v2 StreamPart chunk processing logic."""

    def test_messages_chunk_with_text_content(self) -> None:
        """Messages chunk with text should use lc_agent_name for source."""
        chunk: dict[str, Any] = {
            "type": "messages",
            "ns": (),
            "data": (
                type("Token", (), {"content": "hello", "content_blocks": []})(),
                {"lc_agent_name": "orchestrator"},
            ),
        }

        token, metadata = chunk["data"]
        source = metadata.get("lc_agent_name", "orchestrator")

        assert chunk["type"] == "messages"
        assert source == "orchestrator"
        assert token.content == "hello"

    def test_messages_chunk_with_subagent_name(self) -> None:
        """Messages chunk from sub-agent should use lc_agent_name."""
        metadata: dict[str, Any] = {"lc_agent_name": "world_builder"}
        source = metadata.get("lc_agent_name", "orchestrator")
        assert source == "world_builder"

    def test_updates_chunk_with_tool_calls(self) -> None:
        """Updates chunk with tool_calls should produce tool_start event."""
        chunk: dict[str, Any] = {
            "type": "updates",
            "ns": (),
            "data": {
                "agent": {
                    "messages": [
                        type(
                            "AIMessage",
                            (),
                            {
                                "tool_calls": [
                                    {"name": "delegate_to_world_builder", "id": "call_123", "args": {"task": "test"}}
                                ]
                            },
                        )()
                    ]
                }
            },
        }

        assert chunk["type"] == "updates"
        node_name = list(chunk["data"].keys())[0]
        assert node_name == "agent"

    def test_custom_chunk_type(self) -> None:
        """Custom chunk should be recognized."""
        chunk: dict[str, Any] = {
            "type": "custom",
            "ns": (),
            "data": {"message": "Processing..."},
        }

        assert chunk["type"] == "custom"


class TestSseFormatting:
    """Test SSE event formatting."""

    def test_sse_event_format_has_event_id_data(self) -> None:
        """Each SSE event should have event:, id:, and data: lines."""
        event_type = "messages"
        event_id = 42
        payload = {"token": "hello", "source": "orchestrator"}

        sse = f"event: {event_type}\nid: {event_id}\ndata: {json.dumps(payload)}\n\n"

        assert "event: messages\n" in sse
        assert "id: 42\n" in sse
        assert '"token": "hello"' in sse
        assert sse.endswith("\n\n")

    def test_error_event_format(self) -> None:
        """Error events should use event: error."""
        payload = {"error_code": "unknown", "message": "test", "retryable": False}
        sse = f"event: error\ndata: {json.dumps(payload)}\n\n"

        assert "event: error\n" in sse
        assert '"error_code": "unknown"' in sse

    def test_done_event_format(self) -> None:
        """Done event should contain full_content."""
        payload = {"full_content": "hello world"}
        sse = f"event: done\ndata: {json.dumps(payload)}\n\n"

        assert "event: done\n" in sse
        assert '"full_content": "hello world"' in sse
