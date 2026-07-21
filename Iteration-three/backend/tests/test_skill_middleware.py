"""Tests for skill middleware: create_load_skill_tool and SkillMiddleware."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from langchain_core.tools import BaseTool

from app.services.skill import SkillService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_service(tmp_path: Path) -> SkillService:
    """Create a SkillService rooted at tmp_path."""
    return SkillService(skills_dir=tmp_path / "skills")


# ---------------------------------------------------------------------------
# create_load_skill_tool tests
# ---------------------------------------------------------------------------


class TestCreateLoadSkillTool:
    """Tests for the create_load_skill_tool factory."""

    def test_returns_tool_named_load_skill(self, tmp_path: Path) -> None:
        from app.core.agent.skill_middleware import create_load_skill_tool

        service = _make_service(tmp_path)
        load_skill = create_load_skill_tool(service)

        assert isinstance(load_skill, BaseTool)
        assert load_skill.name == "load_skill"

    def test_load_existing_skill_returns_content(self, tmp_path: Path) -> None:
        from app.core.agent.skill_middleware import create_load_skill_tool

        service = _make_service(tmp_path)
        service.create_skill("writing", "Improve prose", "Write vivid scenes.")

        load_skill = create_load_skill_tool(service)
        result = load_skill.invoke({"skill_name": "writing"})

        assert "writing" in result
        assert "Write vivid scenes." in result

    def test_load_nonexistent_skill_returns_error_with_available(self, tmp_path: Path) -> None:
        from app.core.agent.skill_middleware import create_load_skill_tool

        service = _make_service(tmp_path)
        service.create_skill("alpha", "First skill", "body alpha")
        service.create_skill("beta", "Second skill", "body beta")

        load_skill = create_load_skill_tool(service)
        result = load_skill.invoke({"skill_name": "nonexistent"})

        assert "not found" in result.lower() or "Not found" in result
        assert "alpha" in result
        assert "beta" in result


# ---------------------------------------------------------------------------
# SkillMiddleware tests
# ---------------------------------------------------------------------------


class TestSkillMiddleware:
    """Tests for the SkillMiddleware class."""

    def test_has_correct_domain(self, tmp_path: Path) -> None:
        from app.core.agent.skill_middleware import SkillMiddleware

        middleware = SkillMiddleware(domain="chapter")
        assert middleware.domain == "chapter"

    def test_domain_none_by_default(self, tmp_path: Path) -> None:
        from app.core.agent.skill_middleware import SkillMiddleware

        middleware = SkillMiddleware()
        assert middleware.domain is None

    def test_has_load_skill_tool(self, tmp_path: Path) -> None:
        from app.core.agent.skill_middleware import SkillMiddleware

        middleware = SkillMiddleware()
        assert len(middleware.tools) == 1

        tool_obj = middleware.tools[0]
        assert isinstance(tool_obj, BaseTool)
        assert tool_obj.name == "load_skill"

    def test_wrap_passes_through_when_no_skills(self, tmp_path: Path) -> None:
        from app.core.agent.skill_middleware import SkillMiddleware

        middleware = SkillMiddleware()
        # Point to an empty skills directory so list_skills returns []
        middleware.skill_service = SkillService(skills_dir=tmp_path / "empty_skills")

        request = MagicMock()
        request.system_prompt = "You are an assistant."
        handler = MagicMock()

        result = middleware.wrap_model_call(request, handler)

        # handler should be called with the original request (no override)
        handler.assert_called_once_with(request)
        assert result is handler.return_value

    def test_wrap_injects_skill_descriptions(self, tmp_path: Path) -> None:
        from app.core.agent.skill_middleware import SkillMiddleware

        middleware = SkillMiddleware(domain=None)
        middleware.skill_service = SkillService(skills_dir=tmp_path / "skills")
        middleware.skill_service.create_skill("test", "Test skill description", "body")

        request = MagicMock()
        request.system_prompt = "You are an assistant."
        request.override.return_value = "modified_request"
        handler = MagicMock()

        result = middleware.wrap_model_call(request, handler)

        # override should have been called with system_message containing skill descriptions
        request.override.assert_called_once()
        call_kwargs = request.override.call_args[1]
        system_msg = call_kwargs["system_message"]
        updated_prompt = system_msg.content
        assert "## Available Skills" in updated_prompt
        assert "test" in updated_prompt
        assert "Test skill description" in updated_prompt
        assert "You are an assistant." in updated_prompt

        # handler should be called with the modified request
        handler.assert_called_once_with("modified_request")
        assert result is handler.return_value

    def test_wrap_injects_multiple_skills(self, tmp_path: Path) -> None:
        from app.core.agent.skill_middleware import SkillMiddleware

        middleware = SkillMiddleware()
        middleware.skill_service = SkillService(skills_dir=tmp_path / "skills")
        middleware.skill_service.create_skill("alpha", "First skill", "body one")
        middleware.skill_service.create_skill("beta", "Second skill", "body two")

        request = MagicMock()
        request.system_prompt = "Base prompt."
        request.override.return_value = "modified"
        handler = MagicMock(return_value="resp")

        middleware.wrap_model_call(request, handler)

        call_kwargs = request.override.call_args[1]
        prompt = call_kwargs["system_message"].content
        assert "alpha" in prompt
        assert "beta" in prompt
        assert "First skill" in prompt
        assert "Second skill" in prompt

    def test_wrap_with_empty_system_prompt(self, tmp_path: Path) -> None:
        from app.core.agent.skill_middleware import SkillMiddleware

        middleware = SkillMiddleware()
        middleware.skill_service = SkillService(skills_dir=tmp_path / "skills")
        middleware.skill_service.create_skill("my_skill", "A skill", "content")

        request = MagicMock()
        request.system_prompt = None
        request.override.return_value = "modified"
        handler = MagicMock(return_value="resp")

        middleware.wrap_model_call(request, handler)

        call_kwargs = request.override.call_args[1]
        prompt = call_kwargs["system_message"].content
        assert "## Available Skills" in prompt
        assert "my_skill" in prompt

    def test_wrap_filters_by_domain(self, tmp_path: Path) -> None:
        from app.core.agent.skill_middleware import SkillMiddleware

        middleware = SkillMiddleware(domain="chapter")
        middleware.skill_service = SkillService(skills_dir=tmp_path / "skills")
        # Global skill (no domain)
        middleware.skill_service.create_skill("global_skill", "Global", "global body")
        # Domain-specific skill
        middleware.skill_service.create_skill("chapter_style", "Chapter style", "chapter body", domain="chapter")

        request = MagicMock()
        request.system_prompt = "Base."
        request.override.return_value = "modified"
        handler = MagicMock(return_value="resp")

        middleware.wrap_model_call(request, handler)

        call_kwargs = request.override.call_args[1]
        prompt = call_kwargs["system_message"].content
        # chapter domain skill should appear
        assert "chapter_style" in prompt
        assert "Chapter style" in prompt
        # global skill should NOT appear
        assert "global_skill" not in prompt
