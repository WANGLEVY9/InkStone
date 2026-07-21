# 跨对话知识共享系统 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建项目级知识库系统，实现从 AI 生成内容中自动提取结构化知识、冲突检测、用户增量确认、跨会话知识注入的完整链路。

**Architecture:** 在现有 SQLite 中新增 5 张知识表，结构化为嵌入索引辅以向量语义检索。后端新增 KnowledgeService 处理 CRUD/冲突检测/语义搜索，KnowledgeExtractor 调用 LLM 提取知识。前端新增增量确认面板。知识摘要自动注入 project_context 实现跨会话加载。

**Tech Stack:** Python 3.13 + FastAPI + aiosqlite, sentence-transformers, React 18 + TypeScript + Ant Design 6

---

### Task 1: 初始化 — 创建开发分支

- [ ] **Step 1: 创建并切换到新分支**

```bash
git checkout -b feat/cross-session-knowledge-sharing
```

- [ ] **Step 2: 确认分支已创建**

```bash
git branch
```
Expected: `* feat/cross-session-knowledge-sharing` 已高亮为当前分支

---

### Task 2: 数据库 Schema — 新增 5 张知识表

**Files:**
- Modify: `backend/app/db/schema.sql`

- [ ] **Step 1: 在 schema.sql 末尾追加 5 张新表**

在 `schema.sql` 末尾追加：

```sql
-- ============================================================
-- 跨对话知识共享系统
-- ============================================================

-- 通用结构化事实（角色属性、世界设定条目等）
CREATE TABLE IF NOT EXISTS knowledge_facts (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    fact_key TEXT NOT NULL,
    fact_value TEXT NOT NULL,
    summary TEXT NOT NULL,
    embedding BLOB,
    source_session_id TEXT,
    confidence REAL DEFAULT 1.0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_kf_project ON knowledge_facts(project_id);
CREATE INDEX IF NOT EXISTS idx_kf_entity ON knowledge_facts(project_id, entity_type, entity_id);

-- 时间线事件
CREATE TABLE IF NOT EXISTS knowledge_events (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    chapter_number INTEGER,
    sequence INTEGER DEFAULT 0,
    event_type TEXT NOT NULL DEFAULT 'plot',
    involved_entities TEXT,
    embedding BLOB,
    source_session_id TEXT,
    is_confirmed INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_ke_project ON knowledge_events(project_id);
CREATE INDEX IF NOT EXISTS idx_ke_timeline ON knowledge_events(project_id, chapter_number, sequence);

-- 角色关系
CREATE TABLE IF NOT EXISTS knowledge_relationships (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    source_entity_id TEXT NOT NULL,
    target_entity_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    description TEXT,
    strength INTEGER DEFAULT 5,
    source_session_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_kr_project ON knowledge_relationships(project_id);
CREATE INDEX IF NOT EXISTS idx_kr_entities ON knowledge_relationships(project_id, source_entity_id, target_entity_id);

-- 伏笔追踪
CREATE TABLE IF NOT EXISTS knowledge_foreshadowing (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    description TEXT NOT NULL,
    expected_resolve_chapter INTEGER,
    actual_resolve_chapter INTEGER,
    status TEXT NOT NULL DEFAULT 'pending',
    priority TEXT NOT NULL DEFAULT 'normal',
    related_chapter_id TEXT,
    resolved_by_chapter_id TEXT,
    embedding BLOB,
    source_session_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_kf2_project ON knowledge_foreshadowing(project_id);
CREATE INDEX IF NOT EXISTS idx_kf2_status ON knowledge_foreshadowing(project_id, status);

-- 增量变更日志
CREATE TABLE IF NOT EXISTS knowledge_delta_log (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    target_table TEXT NOT NULL,
    record_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_kdl_project ON knowledge_delta_log(project_id);
CREATE INDEX IF NOT EXISTS idx_kdl_session ON knowledge_delta_log(project_id, session_id);
CREATE INDEX IF NOT EXISTS idx_kdl_status ON knowledge_delta_log(project_id, status);
```

- [ ] **Step 3: 运行测试验证数据库初始化正常**

```bash
cd backend && uv run pytest tests/test_database.py -v
```
Expected: 全部 PASS。如果数据库在测试中被重建，新表应被创建。

- [ ] **Step 4: 提交**

```bash
git add backend/app/db/schema.sql
git commit -m "feat(db): add 5 knowledge tables for cross-session knowledge sharing"
```

---

### Task 3: KnowledgeService — 知识库 CRUD + 冲突检测 + 语义搜索

**Files:**
- Create: `backend/app/services/knowledge.py`
- Test: `backend/tests/test_knowledge_service.py`
- Modify: `backend/pyproject.toml` (add sentence-transformers)

- [ ] **Step 1: 编写 KnowledgeService 的测试**

创建 `backend/tests/test_knowledge_service.py`：

```python
"""Tests for KnowledgeService."""
from __future__ import annotations

import pytest
import uuid

from app.services.knowledge import KnowledgeService


@pytest.fixture
async def knowledge_service(db):
    return KnowledgeService(db)


@pytest.fixture
def sample_project_id():
    return str(uuid.uuid4())


@pytest.mark.asyncio
async def test_store_and_retrieve_fact(knowledge_service, sample_project_id):
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
async def test_get_facts_filtered_by_entity(knowledge_service, sample_project_id):
    """Should filter facts by entity_type and entity_id."""
    await knowledge_service.store_fact(sample_project_id, "character", "char-1", "age", "20", "test")
    await knowledge_service.store_fact(sample_project_id, "character", "char-2", "age", "18", "test")

    facts = await knowledge_service.get_facts(sample_project_id, entity_type="character", entity_id="char-1")
    assert len(facts) == 1
    assert facts[0]["entity_id"] == "char-1"


@pytest.mark.asyncio
async def test_timeline_events(knowledge_service, sample_project_id):
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
    # Should be ordered by chapter_number ascending
    assert len(events) == 2
    assert events[0]["chapter_number"] == 1
    assert events[1]["chapter_number"] == 5


@pytest.mark.asyncio
async def test_store_and_resolve_relationship(knowledge_service, sample_project_id):
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


@pytest.mark.asyncio
async def test_foreshadowing_lifecycle(knowledge_service, sample_project_id):
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

    await knowledge_service.resolve_foreshadowing(fid, actual_resolve_chapter=10, resolved_by_chapter_id="ch-10")
    items = await knowledge_service.get_foreshadowing(sample_project_id)
    assert items[0]["status"] == "resolved"


@pytest.mark.asyncio
async def test_delta_log_lifecycle(knowledge_service, sample_project_id):
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


@pytest.mark.asyncio
async def test_semantic_search(knowledge_service, sample_project_id):
    """Should return results ordered by similarity."""
    # Store two items with different content
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

    results = await knowledge_service.semantic_search(sample_project_id, "余杭镇", top_k=5)
    assert len(results) >= 1
    assert results[0]["entity_id"] == "char-1"  # 李逍遥更相关


@pytest.mark.asyncio
async def test_get_knowledge_summary(knowledge_service, sample_project_id):
    """Should return structured summary with all knowledge types."""
    await knowledge_service.store_event(sample_project_id, "事件A", "desc", 1, source_session_id="s1")
    await knowledge_service.store_fact(sample_project_id, "character", "c1", "key", "val", "摘要", source_session_id="s1")
    await knowledge_service.store_relationship(sample_project_id, "c1", "c2", "friend", "desc", source_session_id="s1")
    await knowledge_service.store_foreshadowing(sample_project_id, "伏笔", 10, "ch-1", source_session_id="s1")

    summary = await knowledge_service.get_knowledge_summary(sample_project_id)
    assert "recent_events" in summary
    assert "key_facts" in summary
    assert "active_relationships" in summary
    assert "pending_foreshadowing" in summary


@pytest.mark.asyncio
async def test_batch_confirm_deltas(knowledge_service, sample_project_id):
    """Should confirm/reject multiple deltas at once."""
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
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && uv run pytest tests/test_knowledge_service.py -v
```
Expected: 全部失败（ModuleNotFoundError/ImportError），因为 `KnowledgeService` 还不存在。

- [ ] **Step 3: 实现 KnowledgeService**

创建 `backend/app/services/knowledge.py`：

```python
"""Knowledge service: CRUD, conflict detection, and semantic search for project knowledge base.

This service manages five knowledge tables (facts, events, relationships,
foreshadowing, delta_log) and provides cross-session knowledge sharing capabilities.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from app.db.connection import get_db


class KnowledgeService:
    """Service for managing project-level knowledge base operations."""

    def __init__(self, db) -> None:
        self.db = db

    # ── Facts ──

    async def store_fact(
        self,
        project_id: str,
        entity_type: str,
        entity_id: str | None,
        fact_key: str,
        fact_value: str,
        summary: str,
        source_session_id: str | None = None,
        compute_embedding: bool = False,
    ) -> str:
        fid = str(uuid.uuid4())
        embedding = None
        if compute_embedding:
            embedding = await self._compute_embedding(summary)
        await self.db.execute(
            """INSERT INTO knowledge_facts (id, project_id, entity_type, entity_id, fact_key, fact_value, summary, embedding, source_session_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (fid, project_id, entity_type, entity_id, fact_key, fact_value, summary, embedding, source_session_id),
        )
        await self.db.commit()
        return fid

    async def get_facts(
        self,
        project_id: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM knowledge_facts WHERE project_id = ? AND is_active = 1"
        params: list[Any] = [project_id]
        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)
        if entity_id:
            query += " AND entity_id = ?"
            params.append(entity_id)
        query += " ORDER BY created_at DESC"
        cursor = await self.db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # ── Events (Timeline) ──

    async def store_event(
        self,
        project_id: str,
        title: str,
        description: str,
        chapter_number: int | None = None,
        sequence: int = 0,
        event_type: str = "plot",
        involved_entities: str | None = None,
        source_session_id: str | None = None,
        compute_embedding: bool = False,
    ) -> str:
        eid = str(uuid.uuid4())
        embedding = None
        if compute_embedding:
            embedding = await self._compute_embedding(f"{title}: {description}")
        await self.db.execute(
            """INSERT INTO knowledge_events (id, project_id, title, description, chapter_number, sequence, event_type, involved_entities, embedding, source_session_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (eid, project_id, title, description, chapter_number, sequence, event_type, involved_entities, embedding, source_session_id),
        )
        await self.db.commit()
        return eid

    async def get_timeline(
        self,
        project_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        cursor = await self.db.execute(
            """SELECT * FROM knowledge_events
               WHERE project_id = ? AND is_confirmed = 1
               ORDER BY chapter_number ASC, sequence ASC
               LIMIT ? OFFSET ?""",
            (project_id, limit, offset),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # ── Relationships ──

    async def store_relationship(
        self,
        project_id: str,
        source_entity_id: str,
        target_entity_id: str,
        relationship_type: str,
        description: str | None = None,
        strength: int = 5,
        source_session_id: str | None = None,
    ) -> str:
        rid = str(uuid.uuid4())
        await self.db.execute(
            """INSERT INTO knowledge_relationships (id, project_id, source_entity_id, target_entity_id, relationship_type, description, strength, source_session_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (rid, project_id, source_entity_id, target_entity_id, relationship_type, description, strength, source_session_id),
        )
        await self.db.commit()
        return rid

    async def get_relationships(
        self,
        project_id: str,
        entity_id: str | None = None,
    ) -> list[dict[str, Any]]:
        if entity_id:
            cursor = await self.db.execute(
                """SELECT * FROM knowledge_relationships
                   WHERE project_id = ? AND (source_entity_id = ? OR target_entity_id = ?)
                   ORDER BY strength DESC""",
                (project_id, entity_id, entity_id),
            )
        else:
            cursor = await self.db.execute(
                "SELECT * FROM knowledge_relationships WHERE project_id = ? ORDER BY strength DESC",
                (project_id,),
            )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # ── Foreshadowing ──

    async def store_foreshadowing(
        self,
        project_id: str,
        description: str,
        expected_resolve_chapter: int | None = None,
        related_chapter_id: str | None = None,
        priority: str = "normal",
        source_session_id: str | None = None,
        compute_embedding: bool = False,
    ) -> str:
        fid = str(uuid.uuid4())
        embedding = None
        if compute_embedding:
            embedding = await self._compute_embedding(description)
        await self.db.execute(
            """INSERT INTO knowledge_foreshadowing (id, project_id, description, expected_resolve_chapter, related_chapter_id, priority, embedding, source_session_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (fid, project_id, description, expected_resolve_chapter, related_chapter_id, priority, embedding, source_session_id),
        )
        await self.db.commit()
        return fid

    async def get_foreshadowing(
        self,
        project_id: str,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        if status:
            cursor = await self.db.execute(
                "SELECT * FROM knowledge_foreshadowing WHERE project_id = ? AND status = ? ORDER BY created_at DESC",
                (project_id, status),
            )
        else:
            cursor = await self.db.execute(
                "SELECT * FROM knowledge_foreshadowing WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,),
            )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def resolve_foreshadowing(
        self,
        foreshadowing_id: str,
        actual_resolve_chapter: int | None = None,
        resolved_by_chapter_id: str | None = None,
    ) -> bool:
        await self.db.execute(
            """UPDATE knowledge_foreshadowing
               SET status = 'resolved', actual_resolve_chapter = ?, resolved_by_chapter_id = ?, updated_at = datetime('now')
               WHERE id = ?""",
            (actual_resolve_chapter, resolved_by_chapter_id, foreshadowing_id),
        )
        await self.db.commit()
        return True

    # ── Delta Log (Incremental Update Confirmation) ──

    async def create_delta(
        self,
        project_id: str,
        session_id: str,
        operation: str,
        target_table: str,
        summary: str,
        record_id: str | None = None,
        old_value: str | None = None,
        new_value: str | None = None,
    ) -> str:
        did = record_id or str(uuid.uuid4())
        await self.db.execute(
            """INSERT INTO knowledge_delta_log (id, project_id, session_id, operation, target_table, record_id, summary, old_value, new_value)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (did, project_id, session_id, operation, target_table, did, summary, old_value, new_value),
        )
        await self.db.commit()
        return did

    async def get_pending_deltas(
        self,
        project_id: str,
        session_id: str | None = None,
    ) -> list[dict[str, Any]]:
        if session_id:
            cursor = await self.db.execute(
                "SELECT * FROM knowledge_delta_log WHERE project_id = ? AND session_id = ? AND status = 'pending' ORDER BY created_at ASC",
                (project_id, session_id),
            )
        else:
            cursor = await self.db.execute(
                "SELECT * FROM knowledge_delta_log WHERE project_id = ? AND status = 'pending' ORDER BY created_at ASC",
                (project_id,),
            )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def confirm_delta(self, delta_id: str) -> bool:
        # Get the delta record first
        cursor = await self.db.execute("SELECT * FROM knowledge_delta_log WHERE id = ?", (delta_id,))
        row = await cursor.fetchone()
        if not row:
            return False
        delta = dict(row)
        # Update delta status
        await self.db.execute(
            "UPDATE knowledge_delta_log SET status = 'confirmed' WHERE id = ?",
            (delta_id,),
        )
        # Activate the target record if it's a create operation
        if delta["operation"] == "create":
            target_table = delta["target_table"]
            await self.db.execute(
                f"UPDATE {target_table} SET is_active = 1, is_confirmed = 1 WHERE id = ?",
                (delta["record_id"],),
            )
        await self.db.commit()
        return True

    async def reject_delta(self, delta_id: str) -> bool:
        cursor = await self.db.execute("SELECT * FROM knowledge_delta_log WHERE id = ?", (delta_id,))
        row = await cursor.fetchone()
        if not row:
            return False
        delta = dict(row)
        await self.db.execute(
            "UPDATE knowledge_delta_log SET status = 'rejected' WHERE id = ?",
            (delta_id,),
        )
        # Delete the target record for create operations
        if delta["operation"] == "create":
            target_table = delta["target_table"]
            record_id = delta["record_id"]
            await self.db.execute(f"DELETE FROM {target_table} WHERE id = ? AND is_confirmed = 0", (record_id,))
        await self.db.commit()
        return True

    async def batch_confirm(self, project_id: str | None = None, session_id: str | None = None) -> int:
        conditions = ["status = 'pending'"]
        params: list[Any] = []
        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)
        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)
        where = " AND ".join(conditions)

        # Get all pending deltas first
        cursor = await self.db.execute(f"SELECT * FROM knowledge_delta_log WHERE {where}", params)
        rows = await cursor.fetchall()
        deltas = [dict(row) for row in rows]

        count = 0
        for delta in deltas:
            await self.db.execute(
                "UPDATE knowledge_delta_log SET status = 'confirmed' WHERE id = ?",
                (delta["id"],),
            )
            if delta["operation"] == "create":
                target_table = delta["target_table"]
                await self.db.execute(
                    f"UPDATE {target_table} SET is_active = 1, is_confirmed = 1 WHERE id = ?",
                    (delta["record_id"],),
                )
            count += 1

        if count > 0:
            await self.db.commit()
        return count

    # ── Semantic Search ──

    async def semantic_search(
        self,
        project_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        query_embedding = await self._compute_embedding(query)
        if query_embedding is None:
            return []

        # Fetch all active facts with embeddings
        cursor = await self.db.execute(
            "SELECT id, entity_type, entity_id, summary, embedding FROM knowledge_facts WHERE project_id = ? AND is_active = 1 AND embedding IS NOT NULL",
            (project_id,),
        )
        rows = await cursor.fetchall()

        results: list[dict[str, Any]] = []
        query_vec = self._deserialize_embedding(query_embedding)

        for row in rows:
            row_dict = dict(row)
            stored_emb = row_dict.get("embedding")
            if stored_emb is None:
                continue
            stored_vec = self._deserialize_embedding(stored_emb)
            sim = self._cosine_similarity(query_vec, stored_vec)
            row_dict["similarity"] = round(sim, 4)
            results.append(row_dict)

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    # ── Knowledge Summary (for project_context injection) ──

    async def get_knowledge_summary(self, project_id: str) -> dict[str, Any]:
        """Build a structured summary of all knowledge for the project.

        Used to inject into project_context for cross-session awareness.
        """
        # Recent confirmed events (last 20)
        cursor = await self.db.execute(
            """SELECT id, title, description, chapter_number, event_type, involved_entities
               FROM knowledge_events
               WHERE project_id = ? AND is_confirmed = 1
               ORDER BY chapter_number DESC, sequence DESC
               LIMIT 20""",
            (project_id,),
        )
        recent_events = [dict(r) for r in await cursor.fetchall()]

        # Key facts (active, limit 50)
        cursor = await self.db.execute(
            """SELECT id, entity_type, entity_id, fact_key, fact_value, summary
               FROM knowledge_facts
               WHERE project_id = ? AND is_active = 1
               ORDER BY updated_at DESC
               LIMIT 50""",
            (project_id,),
        )
        key_facts = [dict(r) for r in await cursor.fetchall()]

        # Active relationships (limit 30)
        cursor = await self.db.execute(
            """SELECT * FROM knowledge_relationships
               WHERE project_id = ?
               ORDER BY strength DESC
               LIMIT 30""",
            (project_id,),
        )
        active_relationships = [dict(r) for r in await cursor.fetchall()]

        # Pending foreshadowing (not yet resolved)
        cursor = await self.db.execute(
            """SELECT id, description, expected_resolve_chapter, priority, related_chapter_id
               FROM knowledge_foreshadowing
               WHERE project_id = ? AND status = 'pending'
               ORDER BY created_at DESC
               LIMIT 20""",
            (project_id,),
        )
        pending_foreshadowing = [dict(r) for r in await cursor.fetchall()]

        return {
            "recent_events": recent_events,
            "key_facts": key_facts,
            "active_relationships": active_relationships,
            "pending_foreshadowing": pending_foreshadowing,
        }

    # ── Embedding helpers ──

    _model = None  # Lazy-loaded singleton

    @classmethod
    async def _get_model(cls):
        """Lazy-load sentence-transformers model."""
        if cls._model is None:
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer("all-MiniLM-L6-v2")
        return cls._model

    async def _compute_embedding(self, text: str) -> bytes | None:
        try:
            model = await self._get_model()
            emb = model.encode(text, normalize_embeddings=True)
            return self._serialize_embedding(emb)
        except Exception:
            return None

    def _serialize_embedding(self, vec) -> bytes:
        import struct
        return struct.pack(f"{len(vec)}f", *vec)

    def _deserialize_embedding(self, blob: bytes):
        import struct
        n = len(blob) // 4
        return list(struct.unpack(f"{n}f", blob))

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        import math
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    # ── Conflict Detection ──

    async def detect_conflicts(
        self,
        project_id: str,
        extracted_facts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Detect conflicts between extracted facts and existing knowledge.

        Checks for:
        - Same entity + same fact_key with conflicting values
        - Timeline contradictions (character appears after death)
        - Relationship type conflicts
        """
        conflicts: list[dict[str, Any]] = []

        for fact in extracted_facts:
            entity_type = fact.get("entity_type", "")
            entity_id = fact.get("entity_id", "")
            fact_key = fact.get("fact_key", "")
            fact_value = fact.get("fact_value", "")

            if not entity_id or not fact_key:
                continue

            existing = await self.get_facts(project_id, entity_type=entity_type, entity_id=entity_id)
            for old in existing:
                if old["fact_key"] == fact_key and old["fact_value"] != fact_value:
                    conflicts.append({
                        "type": "fact_mismatch",
                        "summary": f"实体「{entity_id}」的 {fact_key} 冲突：现有={old['fact_value']}，新={fact_value}",
                        "severity": "warning",
                        "old_value": old["fact_value"],
                        "new_value": fact_value,
                    })

        # Timeline conflict: character appears after death
        death_events = []
        cursor = await self.db.execute(
            "SELECT * FROM knowledge_facts WHERE project_id = ? AND fact_key = 'death_status' AND fact_value = ? AND is_active = 1",
            (project_id, json.dumps("dead")),
        )
        death_events = [dict(r) for r in await cursor.fetchall()]

        for fact in extracted_facts:
            entity_id = fact.get("entity_id", "")
            if entity_id and any(d["entity_id"] == entity_id for d in death_events):
                conflicts.append({
                    "type": "timeline_contradiction",
                    "summary": f"角色「{entity_id}」已被标记为死亡，但新提取内容提到其活跃",
                    "severity": "error",
                })

        return conflicts
```

- [ ] **Step 4: 添加 sentence-transformers 依赖**

在 `backend/pyproject.toml` 的 `[project.dependencies]` 中追加：

```toml
sentence-transformers>=3.0.0
```

- [ ] **Step 5: 安装依赖并运行测试**

```bash
cd backend && uv sync && uv run pytest tests/test_knowledge_service.py -v
```
Expected: 全部 PASS。如果 sentence-transformers 首次下载模型可能需要一些时间。

- [ ] **Step 6: 提交**

```bash
git add backend/app/services/knowledge.py backend/tests/test_knowledge_service.py backend/pyproject.toml
git commit -m "feat(services): add KnowledgeService with CRUD, conflict detection, and semantic search"
```

---

### Task 4: KnowledgeExtractor — LLM 提取结构化知识

**Files:**
- Create: `backend/app/services/knowledge_extractor.py`
- Test: `backend/tests/test_knowledge_extractor.py`

- [ ] **Step 1: 编写测试**

创建 `backend/tests/test_knowledge_extractor.py`：

```python
"""Tests for KnowledgeExtractor."""
from __future__ import annotations

import json
import pytest

from app.services.knowledge_extractor import KnowledgeExtractor, ExtractionResult
from app.services.llm import create_llm_client


@pytest.fixture
def extractor():
    llm = create_llm_client(streaming=False)
    return KnowledgeExtractor(llm=llm)


@pytest.mark.asyncio
async def test_extract_returns_valid_structure(extractor):
    """Should return ExtractionResult with expected keys."""
    messages_content = """
用户：写一下李逍遥在余杭镇的场景。

AI：李逍遥从小在余杭镇的客栈长大，由婶婶抚养。他性格活泼好动，梦想成为一名大侠。
一天，他在客栈门口遇到了一位受伤的神秘少女（赵灵儿）。逍遥将她救下并悉心照料，
两人之间产生了微妙的情愫。这位少女实际上是从南诏国逃出的公主，身负女娲血脉。
"""
    result = await extractor.extract(messages_content)
    assert isinstance(result, dict)
    assert "time_events" in result
    assert "facts" in result
    assert "relationships" in result
    assert "foreshadowing" in result


@pytest.mark.asyncio
async def test_extract_empty_content(extractor):
    """Should handle empty content gracefully."""
    result = await extractor.extract("这是无关紧要的闲聊内容。")
    assert isinstance(result, dict)
    assert result["time_events"] == []
    assert result["facts"] == []


@pytest.mark.asyncio
async def test_extract_character_facts(extractor):
    """Should extract character facts like cultivation level, background."""
    content = "李逍遥现在已经达到金丹期修为，他的师父是酒剑仙。"
    result = await extractor.extract(content)
    facts = result.get("facts", [])
    character_facts = [f for f in facts if f.get("entity_type") == "character"]
    assert len(character_facts) > 0
```

- [ ] **Step 2: 实现 KnowledgeExtractor**

创建 `backend/app/services/knowledge_extractor.py`：

```python
"""Knowledge extraction from AI-generated text using LLM calls.

Extracts structured knowledge (facts, events, relationships, foreshadowing)
from natural language content produced during chat conversations.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import BaseMessage

from app.services.llm import create_llm_client

logger = logging.getLogger("knowledge_extractor")

EXTRACTION_SYSTEM_PROMPT = """You are a novel knowledge extractor. Extract structured knowledge from the given novel writing text.

Output ONLY a valid JSON object with these keys (use empty arrays if nothing found):

1. "time_events": Array of objects with {title, description, chapter_number (int or null), involved_entities (string or null), event_type ("plot"|"character_change"|"world_change")}
2. "facts": Array of objects with {entity_type ("character"|"world_setting"|"plot_event"|"custom"), entity_id (string), fact_key (string), fact_value (string), summary (string)}
3. "relationships": Array of objects with {source_entity_id (string), target_entity_id (string), relationship_type (string), description (string or null)}
4. "foreshadowing": Array of objects with {description (string), related_chapter_id (string or null)}

Rules:
- entity_id should be the character or entity name in Chinese (e.g., "李逍遥", "蜀山")
- fact_key uses snake_case English (e.g., "cultivation_level", "background", "personality", "death_status", "identity")
- fact_value stores the actual value as a JSON string
- summary is a Chinese sentence describing the fact
- Only extract information that is explicitly stated or strongly implied in the text
- Do NOT invent or hallucinate information

Example:
Input: "李逍遥现在已经是金丹期修士了，他拜酒剑仙为师。"
Output: {"time_events": [], "facts": [{"entity_type": "character", "entity_id": "李逍遥", "fact_key": "cultivation_level", "fact_value": "金丹期", "summary": "李逍遥修为达到金丹期"}, {"entity_type": "character", "entity_id": "李逍遥", "fact_key": "master", "fact_value": "酒剑仙", "summary": "李逍遥拜酒剑仙为师"}], "relationships": [{"source_entity_id": "李逍遥", "target_entity_id": "酒剑仙", "relationship_type": "master", "description": "酒剑仙是李逍遥的师父"}], "foreshadowing": []}
"""


class ExtractionResult(dict):
    time_events: list[dict[str, Any]]
    facts: list[dict[str, Any]]
    relationships: list[dict[str, Any]]
    foreshadowing: list[dict[str, Any]]


class KnowledgeExtractor:
    """Uses an LLM to extract structured knowledge from text content."""

    def __init__(self, llm=None) -> None:
        self.llm = llm or create_llm_client(streaming=False)

    async def extract(self, text: str) -> ExtractionResult:
        """Extract structured knowledge from text content.

        Args:
            text: The text content to extract knowledge from (user message + AI response).

        Returns:
            ExtractionResult with time_events, facts, relationships, foreshadowing arrays.

        Raises:
            ValueError: If LLM response cannot be parsed as valid JSON.
        """
        try:
            result = await self.llm.ainvoke([
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract knowledge from this text:\n\n{text}"},
            ])
            content = result.content if hasattr(result, "content") else str(result)
            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                content = "".join(text_parts)

            # Try to extract JSON from the response
            content_str = str(content).strip()
            # Handle potential markdown code blocks
            if "```json" in content_str:
                content_str = content_str.split("```json")[1].split("```")[0].strip()
            elif "```" in content_str:
                content_str = content_str.split("```")[1].split("```")[0].strip()

            parsed = json.loads(content_str)
            return ExtractionResult(
                time_events=parsed.get("time_events", []),
                facts=parsed.get("facts", []),
                relationships=parsed.get("relationships", []),
                foreshadowing=parsed.get("foreshadowing", []),
            )
        except (json.JSONDecodeError, Exception) as exc:
            logger.warning("Knowledge extraction failed: %s", exc)
            return ExtractionResult(time_events=[], facts=[], relationships=[], foreshadowing=[])
```

- [ ] **Step 3: 运行测试**

```bash
cd backend && uv run pytest tests/test_knowledge_extractor.py -v
```
Expected: 测试通过（需要有效的 ANTHROPIC_API_KEY）

- [ ] **Step 4: 提交**

```bash
git add backend/app/services/knowledge_extractor.py backend/tests/test_knowledge_extractor.py
git commit -m "feat(services): add KnowledgeExtractor for LLM-based structured knowledge extraction"
```

---

### Task 5: Knowledge API Routes

**Files:**
- Create: `backend/app/api/v1/knowledge.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_knowledge_api.py`

- [ ] **Step 1: 为 Knowledge API 编写测试**

创建 `backend/tests/test_knowledge_api.py`：

```python
"""Tests for Knowledge API routes."""
from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def project_id(db):
    from app.services.project_repository import create_project
    project = await create_project(db, "测试项目")
    return project["id"]


@pytest.mark.asyncio
async def test_get_knowledge_summary(client, project_id):
    response = await client.get(f"/api/v1/projects/{project_id}/knowledge/summary")
    assert response.status_code == 200
    data = response.json()
    assert "recent_events" in data
    assert "key_facts" in data


@pytest.mark.asyncio
async def test_get_pending_deltas_empty(client, project_id):
    response = await client.get(f"/api/v1/projects/{project_id}/knowledge/deltas")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_timeline(client, project_id):
    response = await client.get(f"/api/v1/projects/{project_id}/knowledge/timeline")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

- [ ] **Step 2: 实现 Knowledge API 路由**

创建 `backend/app/api/v1/knowledge.py`：

```python
"""Knowledge base API routes for cross-session knowledge sharing."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.db.connection import get_db
from app.services.knowledge import KnowledgeService
from pydantic import BaseModel

router = APIRouter(prefix="/projects/{project_id}/knowledge", tags=["knowledge"])


class ConfirmRequest(BaseModel):
    delta_ids: list[str] | None = None
    session_id: str | None = None


class RejectRequest(BaseModel):
    delta_ids: list[str] | None = None
    session_id: str | None = None


class SearchRequest(BaseModel):
    query: str


async def get_knowledge_service():
    async with get_db() as db:
        yield KnowledgeService(db)


@router.get("/summary")
async def get_knowledge_summary(
    project_id: str,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> dict[str, Any]:
    """Get structured knowledge summary for project context injection."""
    summary = await service.get_knowledge_summary(project_id)
    return summary


@router.get("/timeline")
async def get_timeline(
    project_id: str,
    limit: int = 50,
    offset: int = 0,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> list[dict[str, Any]]:
    """Get project timeline events ordered by chapter."""
    return await service.get_timeline(project_id, limit=limit, offset=offset)


@router.get("/facts")
async def get_facts(
    project_id: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> list[dict[str, Any]]:
    """Get knowledge facts, optionally filtered by entity."""
    return await service.get_facts(project_id, entity_type=entity_type, entity_id=entity_id)


@router.get("/relationships")
async def get_relationships(
    project_id: str,
    entity_id: str | None = None,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> list[dict[str, Any]]:
    """Get character relationships."""
    return await service.get_relationships(project_id, entity_id=entity_id)


@router.get("/foreshadowing")
async def get_foreshadowing(
    project_id: str,
    status: str | None = None,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> list[dict[str, Any]]:
    """Get foreshadowing records."""
    return await service.get_foreshadowing(project_id, status=status)


@router.get("/deltas")
async def get_pending_deltas(
    project_id: str,
    session_id: str | None = None,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> list[dict[str, Any]]:
    """Get pending knowledge deltas for user confirmation."""
    return await service.get_pending_deltas(project_id, session_id=session_id)


@router.post("/deltas/confirm")
async def confirm_deltas(
    project_id: str,
    request: ConfirmRequest,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> dict[str, Any]:
    """Confirm pending knowledge deltas."""
    if request.delta_ids:
        count = 0
        for did in request.delta_ids:
            if await service.confirm_delta(did):
                count += 1
    elif request.session_id:
        count = await service.batch_confirm(project_id=project_id, session_id=request.session_id)
    else:
        count = await service.batch_confirm(project_id=project_id)
    return {"confirmed": count}


@router.post("/deltas/reject")
async def reject_deltas(
    project_id: str,
    request: RejectRequest,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> dict[str, Any]:
    """Reject pending knowledge deltas."""
    count = 0
    if request.delta_ids:
        for did in request.delta_ids:
            if await service.reject_delta(did):
                count += 1
    elif request.session_id:
        pending = await service.get_pending_deltas(project_id, session_id=request.session_id)
        for delta in pending:
            if await service.reject_delta(delta["id"]):
                count += 1
    return {"rejected": count}


@router.post("/search")
async def semantic_search(
    project_id: str,
    request: SearchRequest,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> list[dict[str, Any]]:
    """Semantic search across all knowledge."""
    return await service.semantic_search(project_id, request.query)
```

- [ ] **Step 3: 在 main.py 中注册路由**

修改 `backend/app/main.py`，在已有路由注册后追加：

```python
from app.api.v1.knowledge import router as knowledge_router

app.include_router(knowledge_router, prefix="/api/v1")
```

- [ ] **Step 4: 运行测试**

```bash
cd backend && uv run pytest tests/test_knowledge_api.py -v
```
Expected: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add backend/app/api/v1/knowledge.py backend/app/main.py backend/tests/test_knowledge_api.py
git commit -m "feat(api): add Knowledge API routes for cross-session knowledge sharing"
```

---

### Task 6: 集成到聊天流程 + ProjectContext

**Files:**
- Modify: `backend/app/api/v1/chat.py`
- Modify: `backend/app/core/graph/state.py`

- [ ] **Step 1: 在 ProjectContext 中新增 knowledge_summary 字段**

修改 `backend/app/core/graph/state.py`，在 `ProjectContext` 中追加：

```python
knowledge_summary: dict | None
```

接口变为：
```python
class ProjectContext(TypedDict):
    project_name: str
    project_description: str | None
    world_settings: list[dict[str, str]]
    characters: list[dict[str, str]]
    outline: dict[str, str] | None
    chapters: list[dict[str, str]]
    knowledge_summary: dict | None  # NEW
```

- [ ] **Step 2: 在 chat_stream_endpoint 中集成知识摘要加载**

修改 `backend/app/api/v1/chat.py` 的 `chat_stream_endpoint` 函数，在 `asyncio.gather` 后增加知识摘要加载：

```python
from app.services.knowledge import KnowledgeService

# 在现有的 asyncio.gather 之后添加
knowledge_service = KnowledgeService(db)  # db is still in context at this point
knowledge_summary = await knowledge_service.get_knowledge_summary(project_id)
```

然后在 `initial_state` 中追加 `knowledge_summary`：

```python
initial_state: OrchestratorState = {
    ...
    "project_context": {
        ...
        "knowledge_summary": knowledge_summary,  # NEW
    },
}
```

- [ ] **Step 3: 在流结束后触发知识提取**

修改 `stream_with_save` 内部，在发送 `done` 事件前增加：

```python
# 在 `if not stream_error:` 块中，发送 done 事件之前：
# 知识提取（不影响主流程，失败时不报错）
try:
    if combined_content:
        from app.services.knowledge_extractor import KnowledgeExtractor
        from app.services.knowledge import KnowledgeService

        extractor = KnowledgeExtractor()
        extraction = await extractor.extract(f"用户：{request.message}\n\nAI：{combined_content}")

        if extraction["facts"] or extraction["time_events"] or extraction["relationships"]:
            ks = KnowledgeService()
            async with get_db() as db:
                ks.db = db
                # Check for conflicts
                conflicts = await ks.detect_conflicts(project_id, extraction["facts"])

                # Create delta log entries
                for fact in extraction["facts"]:
                    fact_id = await ks.store_fact(
                        project_id=project_id,
                        entity_type=fact.get("entity_type", "custom"),
                        entity_id=fact.get("entity_id"),
                        fact_key=fact.get("fact_key", "unknown"),
                        fact_value=fact.get("fact_value", ""),
                        summary=fact.get("summary", ""),
                        source_session_id=session_id,
                    )
                    await ks.create_delta(
                        project_id=project_id,
                        session_id=session_id,
                        operation="create",
                        target_table="knowledge_facts",
                        record_id=fact_id,
                        summary=f"新增: {fact.get('summary', '')}",
                        new_value=json.dumps(fact),
                    )

                for event in extraction["time_events"]:
                    event_id = await ks.store_event(
                        project_id=project_id,
                        title=event.get("title", ""),
                        description=event.get("description", ""),
                        chapter_number=event.get("chapter_number"),
                        event_type=event.get("event_type", "plot"),
                        involved_entities=event.get("involved_entities"),
                        source_session_id=session_id,
                    )
                    await ks.create_delta(
                        project_id=project_id,
                        session_id=session_id,
                        operation="create",
                        target_table="knowledge_events",
                        record_id=event_id,
                        summary=f"新增事件: {event.get('title', '')}",
                        new_value=json.dumps(event),
                    )

                for rel in extraction["relationships"]:
                    rel_id = await ks.store_relationship(
                        project_id=project_id,
                        source_entity_id=rel.get("source_entity_id", ""),
                        target_entity_id=rel.get("target_entity_id", ""),
                        relationship_type=rel.get("relationship_type", "custom"),
                        description=rel.get("description"),
                        source_session_id=session_id,
                    )
                    await ks.create_delta(
                        project_id=project_id,
                        session_id=session_id,
                        operation="create",
                        target_table="knowledge_relationships",
                        record_id=rel_id,
                        summary=f"新增关系: {rel.get('source_entity_id')} - {rel.get('relationship_type')} - {rel.get('target_entity_id')}",
                        new_value=json.dumps(rel),
                    )

                if conflicts:
                    # Include conflict info in the delta events
                    yield f"event: knowledge_conflicts\nid: {next_id()}\ndata: {json.dumps(safe_json_value({'conflicts': conflicts}))}\n\n"

except Exception:
    logger.warning("知识提取失败，不影响主流程", exc_info=True)
```

- [ ] **Step 4: 运行现有测试确保无回归**

```bash
cd backend && uv run pytest tests/test_chat_error_handling.py tests/test_v2_streaming.py -v
```
Expected: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add backend/app/core/graph/state.py backend/app/api/v1/chat.py
git commit -m "feat(chat): integrate knowledge extraction and cross-session context injection"
```

---

### Task 7: 前端类型定义 + API Client

**Files:**
- Modify: `frontend/src/types/index.ts`
- Create: `frontend/src/api/knowledge.ts`

- [ ] **Step 1: 新增知识库类型定义**

在 `frontend/src/types/index.ts` 中追加：

```typescript
// ── Knowledge Base Types ──

export interface KnowledgeFact {
  id: string;
  project_id: string;
  entity_type: string;
  entity_id: string | null;
  fact_key: string;
  fact_value: string;
  summary: string;
  source_session_id: string | null;
  confidence: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeEvent {
  id: string;
  project_id: string;
  title: string;
  description: string;
  chapter_number: number | null;
  sequence: number;
  event_type: string;
  involved_entities: string | null;
  source_session_id: string | null;
  is_confirmed: boolean;
  created_at: string;
}

export interface KnowledgeRelationship {
  id: string;
  project_id: string;
  source_entity_id: string;
  target_entity_id: string;
  relationship_type: string;
  description: string | null;
  strength: number;
  created_at: string;
}

export interface KnowledgeForeshadowing {
  id: string;
  project_id: string;
  description: string;
  expected_resolve_chapter: number | null;
  actual_resolve_chapter: number | null;
  status: string;
  priority: string;
  related_chapter_id: string | null;
  created_at: string;
}

export interface KnowledgeDelta {
  id: string;
  project_id: string;
  session_id: string;
  operation: string;
  target_table: string;
  record_id: string;
  summary: string;
  status: string;
  created_at: string;
}

export interface KnowledgeSummary {
  recent_events: KnowledgeEvent[];
  key_facts: KnowledgeFact[];
  active_relationships: KnowledgeRelationship[];
  pending_foreshadowing: KnowledgeForeshadowing[];
}

export interface KnowledgeConflict {
  type: string;
  summary: string;
  severity: string;
  old_value?: string;
  new_value?: string;
}
```

- [ ] **Step 2: 创建前端 API Client**

创建 `frontend/src/api/knowledge.ts`：

```typescript
import client from './client';
import type {
  KnowledgeSummary,
  KnowledgeEvent,
  KnowledgeFact,
  KnowledgeRelationship,
  KnowledgeForeshadowing,
  KnowledgeDelta,
} from '@/types';

export const knowledgeApi = {
  getSummary: (projectId: string) =>
    client.get<KnowledgeSummary>(`/projects/${projectId}/knowledge/summary`),

  getTimeline: (projectId: string, params?: { limit?: number; offset?: number }) =>
    client.get<KnowledgeEvent[]>(`/projects/${projectId}/knowledge/timeline`, { params }),

  getFacts: (projectId: string, params?: { entity_type?: string; entity_id?: string }) =>
    client.get<KnowledgeFact[]>(`/projects/${projectId}/knowledge/facts`, { params }),

  getRelationships: (projectId: string, params?: { entity_id?: string }) =>
    client.get<KnowledgeRelationship[]>(`/projects/${projectId}/knowledge/relationships`, { params }),

  getForeshadowing: (projectId: string, params?: { status?: string }) =>
    client.get<KnowledgeForeshadowing[]>(`/projects/${projectId}/knowledge/foreshadowing`, { params }),

  getDeltas: (projectId: string, params?: { session_id?: string }) =>
    client.get<KnowledgeDelta[]>(`/projects/${projectId}/knowledge/deltas`, { params }),

  confirmDeltas: (projectId: string, data: { delta_ids?: string[]; session_id?: string }) =>
    client.post<{ confirmed: number }>(`/projects/${projectId}/knowledge/deltas/confirm`, data),

  rejectDeltas: (projectId: string, data: { delta_ids?: string[]; session_id?: string }) =>
    client.post<{ rejected: number }>(`/projects/${projectId}/knowledge/deltas/reject`, data),

  search: (projectId: string, query: string) =>
    client.post<Array<KnowledgeFact & { similarity: number }>>(
      `/projects/${projectId}/knowledge/search`,
      { query },
    ),
};
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/types/index.ts frontend/src/api/knowledge.ts
git commit -m "feat(frontend): add knowledge base types and API client"
```

---

### Task 8: KnowledgeConfirmPanel — 增量确认面板

**Files:**
- Create: `frontend/src/components/knowledge/KnowledgeConfirmPanel.tsx`

- [ ] **Step 1: 实现增量确认面板组件**

创建 `frontend/src/components/knowledge/KnowledgeConfirmPanel.tsx`：

```tsx
import { useState, useEffect } from 'react';
import { Badge, Button, Drawer, List, Tag, Space, Typography, message, Alert } from 'antd';
import { CheckOutlined, CloseOutlined, BulbOutlined } from '@ant-design/icons';
import { knowledgeApi } from '@/api/knowledge';
import type { KnowledgeDelta } from '@/types';

const { Text } = Typography;

const OPERATION_LABELS: Record<string, { color: string; text: string }> = {
  create: { color: 'green', text: '新增' },
  update: { color: 'orange', text: '变更' },
  delete: { color: 'red', text: '删除' },
};

interface KnowledgeConfirmPanelProps {
  projectId: string;
  sessionId?: string;
  visible: boolean;
  onClose: () => void;
}

const KnowledgeConfirmPanel = ({ projectId, sessionId, visible, onClose }: KnowledgeConfirmPanelProps) => {
  const [deltas, setDeltas] = useState<KnowledgeDelta[]>([]);
  const [loading, setLoading] = useState(false);
  const [confirming, setConfirming] = useState(false);

  const loadDeltas = async () => {
    setLoading(true);
    try {
      const params = sessionId ? { session_id: sessionId } : undefined;
      const res = await knowledgeApi.getDeltas(projectId, params);
      setDeltas(res.data);
    } catch {
      message.error('加载待确认知识失败');
    }
    setLoading(false);
  };

  useEffect(() => {
    if (visible) {
      loadDeltas();
    }
  }, [visible, projectId]);

  const handleConfirmAll = async () => {
    setConfirming(true);
    try {
      const params = sessionId ? { session_id: sessionId } : {};
      const res = await knowledgeApi.confirmDeltas(projectId, params);
      message.success(`已确认 ${res.data.confirmed} 条知识`);
      setDeltas([]);
      onClose();
    } catch {
      message.error('确认失败');
    }
    setConfirming(false);
  };

  const handleConfirmOne = async (deltaId: string) => {
    try {
      const res = await knowledgeApi.confirmDeltas(projectId, { delta_ids: [deltaId] });
      if (res.data.confirmed > 0) {
        message.success('已确认');
        setDeltas(prev => prev.filter(d => d.id !== deltaId));
      }
    } catch {
      message.error('确认失败');
    }
  };

  const handleRejectOne = async (deltaId: string) => {
    try {
      const res = await knowledgeApi.rejectDeltas(projectId, { delta_ids: [deltaId] });
      if (res.data.rejected > 0) {
        message.info('已驳回');
        setDeltas(prev => prev.filter(d => d.id !== deltaId));
      }
    } catch {
      message.error('驳回失败');
    }
  };

  const pendingCount = deltas.length;

  return (
    <>
      {/* Trigger badge */}
      {pendingCount > 0 && !visible && (
        <Badge count={pendingCount} size="small">
          <Button
            type="text"
            icon={<BulbOutlined />}
            onClick={() => {}} // controlled by parent
          />
        </Badge>
      )}

      <Drawer
        title={`待确认的知识点 (${pendingCount})`}
        open={visible}
        onClose={onClose}
        placement="bottom"
        height="auto"
        style={{ maxHeight: '50vh' }}
        extra={
          <Space>
            <Button onClick={onClose}>稍后处理</Button>
            <Button
              type="primary"
              icon={<CheckOutlined />}
              loading={confirming}
              onClick={handleConfirmAll}
              disabled={pendingCount === 0}
            >
              全部确认
            </Button>
          </Space>
        }
      >
        {pendingCount > 0 ? (
          <Alert
            message="确认后这些知识将在后续对话中被 AI 自动参考"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        ) : null}

        <List
          loading={loading}
          dataSource={deltas}
          renderItem={(delta) => {
            const op = OPERATION_LABELS[delta.operation] || { color: 'default', text: delta.operation };
            return (
              <List.Item
                actions={[
                  <Button
                    type="link"
                    icon={<CheckOutlined />}
                    onClick={() => handleConfirmOne(delta.id)}
                    size="small"
                  >
                    确认
                  </Button>,
                  <Button
                    type="link"
                    danger
                    icon={<CloseOutlined />}
                    onClick={() => handleRejectOne(delta.id)}
                    size="small"
                  >
                    驳回
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  avatar={<Tag color={op.color}>{op.text}</Tag>}
                  title={<Text>{delta.summary}</Text>}
                  description={
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      来自会话 · {new Date(delta.created_at).toLocaleString('zh-CN')}
                    </Text>
                  }
                />
              </List.Item>
            );
          }}
          locale={{ emptyText: '暂无可确认的知识点' }}
        />
      </Drawer>
    </>
  );
};

export default KnowledgeConfirmPanel;
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/knowledge/KnowledgeConfirmPanel.tsx
git commit -m "feat(ui): add KnowledgeConfirmPanel for incremental knowledge confirmation"
```

---

### Task 9: 前端集成 — ChatCore + SecondaryNav

**Files:**
- Modify: `frontend/src/components/ai/ChatCore.tsx`
- Modify: `frontend/src/components/layout/SecondaryNav.tsx`

- [ ] **Step 1: 在 ChatCore 中集成确认面板**

在 `ChatCore.tsx` 中，在流结束后展示 `KnowledgeConfirmPanel`：

1. 在文件顶部导入：
```tsx
import KnowledgeConfirmPanel from '@/components/knowledge/KnowledgeConfirmPanel';
import { knowledgeApi } from '@/api/knowledge';
```

2. 在组件内部增加状态：
```tsx
const [showKnowledgePanel, setShowKnowledgePanel] = useState(false);
const [hasPendingKnowledge, setHasPendingKnowledge] = useState(false);
```

3. 在 SSE 流完成（handleStreamComplete 或类似函数中），收到 done 事件后检查是否有待确认知识：
```tsx
// 在流结束后检查知识增量
if (projectId && sessionId) {
  try {
    const res = await knowledgeApi.getDeltas(projectId, { session_id: sessionId });
    if (res.data.length > 0) {
      setHasPendingKnowledge(true);
      setShowKnowledgePanel(true);
    }
  } catch {
    // 静默失败
  }
}
```

4. 在 ChatCore 渲染部分末尾追加：
```tsx
{projectId && (
  <KnowledgeConfirmPanel
    projectId={projectId}
    sessionId={sessionId}
    visible={showKnowledgePanel}
    onClose={() => {
      setShowKnowledgePanel(false);
      setHasPendingKnowledge(false);
    }}
  />
)}
```

5. 可选：在聊天框附近显示按钮徽章：
```tsx
{hasPendingKnowledge && !showKnowledgePanel && (
  <Badge count="新知" size="small" style={{ marginRight: 8 }}>
    <Button
      size="small"
      icon={<BulbOutlined />}
      onClick={() => setShowKnowledgePanel(true)}
    >
      待确认
    </Button>
  </Badge>
)}
```

- [ ] **Step 2: 在 SecondaryNav 中新增"知识库"导航项**

修改 `frontend/src/components/layout/SecondaryNav.tsx`，在现有菜单项中追加：

```tsx
// 在 menuItems 数组中新增：
{
  key: 'knowledge',
  icon: <DatabaseOutlined />,
  label: '知识库',
  onClick: () => navigate(`/projects/${projectId}/knowledge`),
}
```

导入新增图标：
```tsx
import { DatabaseOutlined } from '@ant-design/icons';
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/ai/ChatCore.tsx frontend/src/components/layout/SecondaryNav.tsx
git commit -m "feat(ui): integrate KnowledgeConfirmPanel into ChatCore and add knowledge nav to SecondaryNav"
```

---

### Task 10: 运行完整测试套件 + 最终验证

- [ ] **Step 1: 运行所有后端测试**

```bash
cd backend && uv run pytest -v
```
Expected: 全部 PASS。如果部分测试因 ANTHROPIC_API_KEY 不可用而跳过，是可以接受的。

- [ ] **Step 2: 运行类型检查**

```bash
cd backend && uv run mypy app
```
Expected: 无新增类型错误

- [ ] **Step 3: 运行 Lint**

```bash
cd backend && uv run ruff check app tests
```
Expected: 无新增 lint 错误

- [ ] **Step 4: 运行前端类型检查**

```bash
cd frontend && npm run type-check
```
Expected: 无新增类型错误

- [ ] **Step 5: 最终提交**

```bash
git add -A
git commit -m "chore: finalize cross-session knowledge sharing implementation"
```

- [ ] **Step 6: 推送并创建 MR**

```bash
git push -u origin feat/cross-session-knowledge-sharing
```
Expected: 提示创建 MR 的 URL。

```bash
# 如果使用 glab
glab mr create --title "feat: cross-session knowledge sharing system" --description "实现跨对话知识共享系统，包含知识提取、冲突检测、增量确认和跨会话加载" --label "feature"
```
