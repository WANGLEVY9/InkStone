"""Middleware that appends novel-specific context to the orchestrator system prompt.

Injects last 2 chapters, unresolved foreshadowing, and protagonist state
on each model call to provide narrative continuity.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.messages import SystemMessage


class NovelContextMiddleware(AgentMiddleware):
    """Appends novel-specific context to the system prompt on each model call.

    Reads the current system prompt (which may already include skill descriptions
    from SkillMiddleware) and appends the novel context, preserving existing content.

    Args:
        novel_context: Pre-built context string from NovelContextBuilder.
                       If empty, the middleware is a no-op.
    """

    def __init__(self, novel_context: str = "") -> None:
        self.novel_context = novel_context

    def _inject(self, request: ModelRequest[Any]) -> ModelRequest[Any]:
        """Append novel context to the current system prompt."""
        if not self.novel_context:
            return request
        current_prompt = request.system_prompt or ""
        return request.override(
            system_message=SystemMessage(content=current_prompt + "\n\n" + self.novel_context),
        )

    def wrap_model_call(
        self,
        request: ModelRequest[Any],
        handler: Callable[[ModelRequest[Any]], ModelResponse[Any]],
    ) -> ModelResponse[Any]:
        """Sync: append novel context before model call."""
        return handler(self._inject(request))

    async def awrap_model_call(
        self,
        request: ModelRequest[Any],
        handler: Callable[[ModelRequest[Any]], Awaitable[ModelResponse[Any]]],
    ) -> ModelResponse[Any]:
        """Async: append novel context before model call."""
        return await handler(self._inject(request))
