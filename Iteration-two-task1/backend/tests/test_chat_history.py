"""Tests for chat history message conversion."""

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.api.v1.chat import _messages_to_history_dicts


def test_thinking_from_additional_kwargs() -> None:
    """Thinking content from additional_kwargs is extracted."""
    msg = AIMessage(content="Hello", additional_kwargs={"thinking": "Let me think..."})
    result = _messages_to_history_dicts([msg])
    assert len(result) == 1
    assert result[0]["thinking_content"] == "Let me think..."


def test_thinking_from_content_blocks() -> None:
    """Thinking content from structured content blocks is extracted."""
    msg = AIMessage(
        content=[
            {"type": "thinking", "thinking": "Let me reason about this..."},
            {"type": "text", "text": "Here is my answer."},
        ]
    )
    result = _messages_to_history_dicts([msg])
    assert len(result) == 1
    assert result[0]["thinking_content"] == "Let me reason about this..."


def test_thinking_additional_kwargs_takes_priority() -> None:
    """When both sources have thinking, additional_kwargs wins."""
    msg = AIMessage(
        content=[{"type": "thinking", "thinking": "From content blocks"}, {"type": "text", "text": "Answer"}],
        additional_kwargs={"thinking": "From kwargs"},
    )
    result = _messages_to_history_dicts([msg])
    assert result[0]["thinking_content"] == "From kwargs"


def test_no_thinking() -> None:
    """Messages without thinking have None thinking_content."""
    msg = AIMessage(content="Just text")
    result = _messages_to_history_dicts([msg])
    assert result[0]["thinking_content"] is None


def test_user_message() -> None:
    """User messages are converted correctly."""
    msg = HumanMessage(content="Hello")
    result = _messages_to_history_dicts([msg])
    assert result[0]["role"] == "user"
    assert result[0]["content"] == "Hello"


def test_tool_message() -> None:
    """Tool messages include tool_call_id."""
    msg = ToolMessage(content="result", tool_call_id="tc_123", name="test_tool")
    result = _messages_to_history_dicts([msg])
    assert result[0]["role"] == "tool"
    assert result[0]["tool_call_id"] == "tc_123"
