"""Skill middleware for LangChain agents.

Provides:
- create_load_skill_tool: factory for the load_skill @tool function
- SkillMiddleware: AgentMiddleware that injects skill descriptions into system prompt
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.tools import tool
from langchain_core.messages import SystemMessage

from app.services.skill import SkillService


def create_load_skill_tool(skill_service: SkillService) -> Any:
    """Create the load_skill tool bound to a SkillService instance.

    Args:
        skill_service: The SkillService instance to use for loading skills.

    Returns:
        A LangChain ``@tool`` function named ``load_skill``.
    """

    @tool
    def load_skill(skill_name: str) -> str:
        """Load a skill's full content into context.

        Use this when you need specialized guidance for a specific domain or style.

        Args:
            skill_name: Name of the skill to load.

        Returns:
            The full skill content, or an error message listing available skills.
        """
        skill = skill_service.get_skill(skill_name)
        if not skill:
            available = ", ".join(s["name"] for s in skill_service.list_all_skills())
            return f"Skill '{skill_name}' not found. Available: {available}"
        return f"Loaded skill: {skill_name}\n\n{skill['content']}"

    return load_skill


class SkillMiddleware(AgentMiddleware):
    """Injects skill descriptions into system prompt and registers load_skill tool.

    The middleware reads the current skill list from disk on each model call,
    ensuring newly created skills are automatically visible without rebuilding tools.

    Args:
        domain: If ``None``, loads global skills (for orchestrator).
                If set (e.g., ``"chapter"``), loads domain-specific skills (for sub-agents).
    """

    def __init__(self, domain: str | None = None) -> None:
        self.domain = domain
        self.skill_service = SkillService()
        self.tools = [create_load_skill_tool(self.skill_service)]

    def _build_skills_addendum(self) -> str | None:
        """Build the skills addendum for the system prompt.

        Returns:
            The addendum string if skills exist, or ``None`` if no skills found.
        """
        skills = self.skill_service.list_skills(domain=self.domain)
        if not skills:
            return None
        skills_list = "\n".join(f"- **{s['name']}**: {s['description']}" for s in skills)
        return (
            f"\n\n## Available Skills\n\n{skills_list}\n\nUse the load_skill tool when you need specialized guidance."
        )

    def _inject_skills(
        self,
        request: ModelRequest[Any],
    ) -> ModelRequest[Any]:
        """Inject skill descriptions into the request's system prompt.

        Returns:
            The updated request if skills exist, or the original request unchanged.
        """
        addendum = self._build_skills_addendum()
        if addendum is None:
            return request
        current_prompt = request.system_prompt or ""
        return request.override(
            system_message=SystemMessage(content=current_prompt + addendum),
        )

    def wrap_model_call(
        self,
        request: ModelRequest[Any],
        handler: Callable[[ModelRequest[Any]], ModelResponse[Any]],
    ) -> ModelResponse[Any]:
        """Sync: inject skill descriptions into system prompt before model call."""
        return handler(self._inject_skills(request))

    async def awrap_model_call(
        self,
        request: ModelRequest[Any],
        handler: Callable[[ModelRequest[Any]], Awaitable[ModelResponse[Any]]],
    ) -> ModelResponse[Any]:
        """Async: inject skill descriptions into system prompt before model call."""
        return await handler(self._inject_skills(request))
