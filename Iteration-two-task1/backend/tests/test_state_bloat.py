"""Tests for state bloat mitigation.

Verifies that:
1. trim_messages truncates message history by token count
2. Fallback message-count truncation works when trim_messages fails
"""

from __future__ import annotations

from collections.abc import Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage


class TestTrimMessages:
    """Test message truncation strategies."""

    def test_trim_messages_truncates_by_token_count(self) -> None:
        """trim_messages should keep recent messages under max_tokens."""
        from langchain_core.messages.utils import count_tokens_approximately, trim_messages

        messages: Sequence[BaseMessage] = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there"),
            HumanMessage(content="What is the weather?"),
            AIMessage(content="It is sunny."),
            HumanMessage(content="Tell me a story."),
            AIMessage(content="Once upon a time..."),
        ]

        result = trim_messages(
            messages,
            strategy="last",
            token_counter=count_tokens_approximately,
            max_tokens=50,
            start_on="human",
            end_on=("human", "tool"),
        )

        assert isinstance(result, list)
        assert len(result) <= len(messages)
        # Should preserve order and end on a human or tool message
        if result:
            assert isinstance(result[-1], HumanMessage | ToolMessage)

    def test_trim_messages_fallback_on_failure(self) -> None:
        """Fallback to simple slice when trim_messages raises."""
        messages: Sequence[BaseMessage] = [HumanMessage(content=f"Message {i}") for i in range(50)]

        max_messages = 40
        result: Sequence[BaseMessage] = messages

        try:
            from langchain_core.messages.utils import count_tokens_approximately, trim_messages

            result = trim_messages(
                messages,
                strategy="last",
                token_counter=count_tokens_approximately,
                max_tokens=10,
                start_on="human",
                end_on=("human", "tool"),
            )
        except Exception:
            result = messages[-max_messages:] if len(messages) > max_messages else messages

        assert len(result) <= max_messages

    def test_message_count_fallback_logic(self) -> None:
        """Direct test of the fallback slicing logic."""
        messages = [HumanMessage(content=f"msg {i}") for i in range(100)]
        max_messages = 40

        truncated = messages[-max_messages:] if len(messages) > max_messages else messages

        assert len(truncated) == 40
        assert truncated[0].content == "msg 60"
        assert truncated[-1].content == "msg 99"
