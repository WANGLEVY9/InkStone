"""Tests for KnowledgeExtractor."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.knowledge_extractor import KnowledgeExtractor


@pytest.fixture
def extractor() -> KnowledgeExtractor:
    llm = MagicMock()
    llm.ainvoke = AsyncMock(
        return_value=MagicMock(content=('{"time_events": [], "facts": [], "relationships": [], "foreshadowing": []}'))
    )
    return KnowledgeExtractor(llm=llm)


@pytest.mark.asyncio
async def test_extract_returns_valid_structure(extractor: KnowledgeExtractor) -> None:
    """Should return ExtractionResult with expected keys."""
    content = """
用户：写一下李逍遥在余杭镇的场景。

AI：李逍遥从小在余杭镇的客栈长大，由婶婶抚养。他性格活泼好动，梦想成为一名大侠。
一天，他在客栈门口遇到了一位受伤的神秘少女（赵灵儿）。逍遥将她救下并悉心照料，
两人之间产生了微妙的情愫。这位少女实际上是从南诏国逃出的公主，身负女娲血脉。
"""
    result = await extractor.extract(content)
    assert isinstance(result, dict)
    assert "time_events" in result
    assert "facts" in result
    assert "relationships" in result
    assert "foreshadowing" in result


@pytest.mark.asyncio
async def test_extract_empty_content(extractor: KnowledgeExtractor) -> None:
    """Should handle empty/generic content gracefully."""
    result = await extractor.extract("这是无关紧要的闲聊内容。")
    assert isinstance(result, dict)
    assert result["time_events"] == []
    assert result["facts"] == []
