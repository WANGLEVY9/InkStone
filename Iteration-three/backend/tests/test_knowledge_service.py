"""Tests for KnowledgeService (CRUD, conflict detection, semantic search)."""

from __future__ import annotations

import struct
from pathlib import Path
from uuid import uuid4

import aiosqlite
import pytest

from app.services.knowledge import KnowledgeService


def _fake_embedding(text: str) -> bytes:
    """Deterministic embedding for tests (no HuggingFace download)."""
    dim = 8
    vec = [0.0] * dim
    if "余杭镇" in text:
        vec[0] = 1.0
    if "南诏" in text or "赵灵儿" in text:
        vec[1] = 1.0
    norm = sum(x * x for x in vec) ** 0.5 or 1.0
    normalized = [x / norm for x in vec]
    return struct.pack(f"{dim}f", *normalized)


async def _fake_compute_embedding(_self: KnowledgeService, text: str) -> bytes | None:
    return _fake_embedding(text)


SCHEMA_PATH = Path(__file__).parent.parent / "app" / "db" / "schema.sql"


@pytest.fixture
async def db() -> aiosqlite.Connection:
    """Create an in-memory SQLite database with the production schema."""
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        await conn.executescript(f.read())
    await conn.commit()
    yield conn
    await conn.close()


@pytest.fixture
async def knowledge_service(db: aiosqlite.Connection) -> KnowledgeService:
    """Create a KnowledgeService backed by the in-memory database."""
    return KnowledgeService(db)


@pytest.fixture
def sample_project_id() -> str:
    """Generate a unique project ID for each test."""
    return str(uuid4())


# ---------------------------------------------------------------------------
# Facts
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_store_and_retrieve_fact(
    knowledge_service: KnowledgeService,
    sample_project_id: str,
) -> None:
    """Should store a fact and retrieve it by project_id."""
    fact_id = await knowledge_service.store_fact(
        project_id=sample_project_id,
        entity_type="character",
        entity_id="char-1",
        fact_key="cultivation_level",
        fact_value='"金丹期"',
        summary="李逍遥修为达到金丹期",
        source_session_id="session-1",
    )
    assert fact_id is not None

    facts = await knowledge_service.get_facts(sample_project_id)
    assert len(facts) == 1
    assert facts[0]["fact_key"] == "cultivation_level"


@pytest.mark.asyncio
async def test_get_facts_filtered_by_entity(
    knowledge_service: KnowledgeService,
    sample_project_id: str,
) -> None:
    """Should filter facts by entity_type and entity_id."""
    await knowledge_service.store_fact(
        sample_project_id,
        "character",
        "char-1",
        "age",
        "20",
        "test",
    )
    await knowledge_service.store_fact(
        sample_project_id,
        "character",
        "char-2",
        "age",
        "18",
        "test",
    )

    facts = await knowledge_service.get_facts(
        sample_project_id,
        entity_type="character",
        entity_id="char-1",
    )
    assert len(facts) == 1
    assert facts[0]["entity_id"] == "char-1"


# ---------------------------------------------------------------------------
# Events (Timeline)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_timeline_events(
    knowledge_service: KnowledgeService,
    sample_project_id: str,
) -> None:
    """Should store and retrieve timeline events ordered by chapter."""
    await knowledge_service.store_event(
        project_id=sample_project_id,
        title="拜月教主现身",
        description="拜月教主在蜀山出现",
        chapter_number=5,
        source_session_id="session-1",
    )
    await knowledge_service.store_event(
        project_id=sample_project_id,
        title="李逍遥出发",
        description="李逍遥从余杭镇出发",
        chapter_number=1,
        source_session_id="session-1",
    )

    events = await knowledge_service.get_timeline(sample_project_id)
    assert len(events) == 2
    assert events[0]["chapter_number"] == 1
    assert events[1]["chapter_number"] == 5


# ---------------------------------------------------------------------------
# Relationships
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_store_and_resolve_relationship(
    knowledge_service: KnowledgeService,
    sample_project_id: str,
) -> None:
    """Should store and retrieve character relationships."""
    rel_id = await knowledge_service.store_relationship(
        project_id=sample_project_id,
        source_entity_id="char-1",
        target_entity_id="char-2",
        relationship_type="master",
        description="李逍遥是赵灵儿的师父",
        source_session_id="session-1",
    )
    assert rel_id is not None

    rels = await knowledge_service.get_relationships(sample_project_id)
    assert len(rels) == 1
    assert rels[0]["relationship_type"] == "master"


# ---------------------------------------------------------------------------
# Foreshadowing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_foreshadowing_lifecycle(
    knowledge_service: KnowledgeService,
    sample_project_id: str,
) -> None:
    """Should create foreshadowing and update status."""
    fid = await knowledge_service.store_foreshadowing(
        project_id=sample_project_id,
        description="赵灵儿在梦境中看到一片桃花林",
        expected_resolve_chapter=10,
        related_chapter_id="ch-3",
        source_session_id="session-1",
    )
    assert fid is not None

    items = await knowledge_service.get_foreshadowing(sample_project_id)
    assert len(items) == 1
    assert items[0]["status"] == "pending"

    await knowledge_service.resolve_foreshadowing(
        fid,
        actual_resolve_chapter=10,
        resolved_by_chapter_id="ch-10",
    )
    items = await knowledge_service.get_foreshadowing(sample_project_id)
    assert items[0]["status"] == "resolved"


# ---------------------------------------------------------------------------
# Delta Log
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delta_log_lifecycle(
    knowledge_service: KnowledgeService,
    sample_project_id: str,
) -> None:
    """Should create pending delta, confirm it, and filter by status."""
    delta_id = await knowledge_service.create_delta(
        project_id=sample_project_id,
        session_id="session-1",
        operation="create",
        target_table="knowledge_facts",
        summary="新增: 李逍遥修为=金丹期",
        new_value='{"fact_key": "cultivation_level", "fact_value": "金丹期"}',
    )
    assert delta_id is not None

    pending = await knowledge_service.get_pending_deltas(sample_project_id)
    assert len(pending) == 1

    await knowledge_service.confirm_delta(delta_id)
    pending = await knowledge_service.get_pending_deltas(sample_project_id)
    assert len(pending) == 0


# ---------------------------------------------------------------------------
# Semantic Search
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_semantic_search(
    knowledge_service: KnowledgeService,
    sample_project_id: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Should return results ordered by similarity."""
    monkeypatch.setattr(KnowledgeService, "_compute_embedding", _fake_compute_embedding)
    await knowledge_service.store_fact(
        project_id=sample_project_id,
        entity_type="character",
        entity_id="char-1",
        fact_key="background",
        fact_value='"出生在余杭镇，由婶婶抚养长大"',
        summary="李逍遥在余杭镇的客栈长大",
        source_session_id="session-1",
        compute_embedding=True,
    )
    await knowledge_service.store_fact(
        project_id=sample_project_id,
        entity_type="character",
        entity_id="char-2",
        fact_key="background",
        fact_value='"南诏国公主，女娲后人"',
        summary="赵灵儿是南诏国公主",
        source_session_id="session-1",
        compute_embedding=True,
    )

    results = await knowledge_service.semantic_search(
        sample_project_id,
        "余杭镇",
        top_k=5,
    )
    assert len(results) >= 1
    assert results[0]["entity_id"] == "char-1"


# ---------------------------------------------------------------------------
# Knowledge Summary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_knowledge_summary(
    knowledge_service: KnowledgeService,
    sample_project_id: str,
) -> None:
    """Should return structured summary with all knowledge types."""
    await knowledge_service.store_event(
        sample_project_id,
        "事件A",
        "desc",
        1,
        source_session_id="s1",
    )
    await knowledge_service.store_fact(
        sample_project_id,
        "character",
        "c1",
        "key",
        "val",
        "摘要",
        source_session_id="s1",
    )
    await knowledge_service.store_relationship(
        sample_project_id,
        "c1",
        "c2",
        "friend",
        "desc",
        source_session_id="s1",
    )
    await knowledge_service.store_foreshadowing(
        sample_project_id,
        "伏笔",
        10,
        "ch-1",
        source_session_id="s1",
    )

    summary = await knowledge_service.get_knowledge_summary(sample_project_id)
    assert "recent_events" in summary
    assert "key_facts" in summary
    assert "active_relationships" in summary
    assert "pending_foreshadowing" in summary


# ---------------------------------------------------------------------------
# Batch Confirm
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_batch_confirm_deltas(
    knowledge_service: KnowledgeService,
    sample_project_id: str,
) -> None:
    """Should confirm multiple deltas at once."""
    ids = []
    for i in range(3):
        did = await knowledge_service.create_delta(
            project_id=sample_project_id,
            session_id="session-1",
            operation="create",
            target_table="knowledge_facts",
            summary=f"新增条目{i}",
        )
        ids.append(did)

    await knowledge_service.batch_confirm(session_id="session-1")
    pending = await knowledge_service.get_pending_deltas(sample_project_id)
    assert len(pending) == 0
