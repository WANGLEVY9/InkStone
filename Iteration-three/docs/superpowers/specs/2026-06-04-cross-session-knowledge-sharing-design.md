# 跨对话知识共享系统设计文档

## 背景

当前系统每次对话时从 SQLite 加载项目上下文的静态快照（世界观、角色、大纲、章节列表），但缺少：

1. **结构化知识提取** — AI 生成的内容中包含的时间线事件、角色关系、伏笔等无法被结构化存储和复用
2. **跨会话记忆** — 用户在新对话中提到之前讨论过的内容时，Agent 无法感知
3. **冲突检测** — 当生成内容与已有知识矛盾时，系统无法主动发现和提醒
4. **增量更新确认** — 对话中产生的新信息，用户没有机会逐条确认后再写入全局

本设计构建一个项目级知识库系统，以结构化存储为主、语义向量检索为辅，覆盖知识提取→冲突检测→用户确认→跨会话加载的完整链路。

---

## 存储方案

### 选型决策

| 层面 | 选型 | 理由 |
|------|------|------|
| 数据库 | 现有 SQLite (`backend/novel.db`) | 项目已在使用，元数据和知识无需分离 |
| 向量 | BLOB 字段 + Python 余弦相似度 | 万级数据 < 100ms，无需外部向量数据库 |
| 嵌入模型 | `all-MiniLM-L6-v2` (384维, ~80MB) | CPU 10ms/条，首次使用自动下载 |

### 新增 Python 依赖

- `sentence-transformers` — 生成文本嵌入向量

### 新增数据表

#### `knowledge_facts` — 通用结构化事实

存储角色属性、世界设定条目等键值对式知识。

```sql
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
```

#### `knowledge_events` — 时间线事件

记录按章节排序的情节事件，用于时间线冲突检测。

```sql
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
```

#### `knowledge_relationships` — 角色关系

```sql
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
```

#### `knowledge_foreshadowing` — 伏笔追踪

```sql
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
```

#### `knowledge_delta_log` — 增量变更日志

每次对话产生的知识变更先写入此表（`pending`），用户确认后才标记生效。

```sql
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

---

## 后端服务层

### `KnowledgeService` (新增: `backend/app/services/knowledge.py`)

对外 API：

```python
class KnowledgeService:
    # 知识提取与写入
    async def extract_and_store(session_id, project_id, messages) -> list[DeltaLog]:
        """调用 LLM 从对话中提取结构化知识，检测冲突，写入 delta_log"""
    
    # 结构化查询
    async def get_timeline(project_id, limit=50) -> list[Event]:
    async def get_facts(project_id, entity_type=None, entity_id=None) -> list[Fact]:
    async def get_relationships(project_id, entity_id=None) -> list[Relationship]:
    async def get_foreshadowing(project_id, status=None) -> list[Foreshadowing]:
    
    # 语义搜索
    async def semantic_search(project_id, query, top_k=5) -> list[SearchResult]:
    
    # 冲突检测
    async def detect_conflicts(project_id, extracted_facts) -> list[Conflict]:
    
    # 增量更新确认
    async def get_pending_deltas(project_id, session_id=None) -> list[DeltaLog]:
    async def confirm_delta(delta_id):
    async def reject_delta(delta_id):
    async def batch_confirm(session_id, delta_ids=None):
    
    # 跨会话摘要
    async def get_knowledge_summary(project_id) -> dict:
        """生成 knowledge_summary 用于注入 project_context"""
    
    # 嵌入
    async def _compute_embedding(text) -> bytes:
    async def _compute_similarity(a_embedding, b_embedding) -> float:
```

### `KnowledgeExtractor` (新增: `backend/app/services/knowledge_extractor.py`)

专门负责用 LLM 从文本中提取结构化知识。

```python
class KnowledgeExtractor:
    EXTRACTION_PROMPT = """你是一个小说知识提取器。从以下 AI 生成的文本中提取知识。
    
请以 JSON 格式输出提取的知识条目：

1. time_events: 时间线事件 [{title, description, chapter_number, involved_entities, event_type}]
2. facts: 事实断言 [{entity_type, entity_id, fact_key, fact_value, summary}]
3. relationships: 关系 [{source_entity_id, target_entity_id, relationship_type, description}]
4. foreshadowing: 伏笔 [{description, related_chapter_id}]

如果没有提取到相关内容，返回空数组。
只返回格式正确的 JSON，不要其他文字。
"""
    
    async def extract(messages: list[BaseMessage]) -> ExtractionResult:
        """调用 LLM 提取结构化知识"""
    
    class ExtractionResult(TypedDict):
        time_events: list
        facts: list
        relationships: list
        foreshadowing: list
```

### 冲突检测器 (内置于 `KnowledgeService`)

```python
async def detect_conflicts(project_id, extracted) -> list[Conflict]:
    conflicts = []
    for fact in extracted.facts:
        existing = await get_matching_facts(project_id, fact)
        for old in existing:
            if values_conflict(old.fact_value, fact.fact_value):
                conflicts.append(Conflict(
                    type="fact_mismatch",
                    summary=f"角色「{entity_id}」的 {fact_key} 冲突：现有={old_value}，新={fact_value}",
                    old_value=old.fact_value,
                    new_value=fact.fact_value,
                ))
    # 时间线冲突：同一章节同一角色出现两次且状态矛盾
    # 关系冲突：A-B 关系类型矛盾
    return conflicts
```

### 集成到聊天流程 (`chat.py` 修改)

在 `chat_stream_endpoint` 中，流结束后（`done` 事件前）增加知识提取步骤：

```python
# 在 stream_with_save() 中，收到 done 前：
try:
    if full_content:
        knowledge = KnowledgeService()
        deltas = await knowledge.extract_and_store(
            session_id=session_id,
            project_id=project_id,
            messages=truncated_history + [HumanMessage(content=request.message)] + [AIMessage(content="".join(full_content))],
        )
        if deltas:
            yield ...  # 发送 knowledge_delta 事件
except Exception:
    logger.warning("知识提取失败", exc_info=True)
    # 不影响主流程
```

---

## API 路由

新增：`backend/app/api/v1/knowledge.py`

| 方法 | 路径 | 功能 |
|------|------|------|
| `GET` | `/projects/{id}/knowledge/summary` | 获取知识摘要 |
| `GET` | `/projects/{id}/knowledge/timeline` | 获取时间线 |
| `GET` | `/projects/{id}/knowledge/facts` | 查询事实 (支持 entity_type, entity_id 筛选) |
| `GET` | `/projects/{id}/knowledge/relationships` | 查询关系 |
| `GET` | `/projects/{id}/knowledge/foreshadowing` | 查询伏笔 |
| `GET` | `/projects/{id}/knowledge/deltas` | 查询待确认变更 (支持 session_id 筛选) |
| `POST` | `/projects/{id}/knowledge/deltas/confirm` | 确认变更 |
| `POST` | `/projects/{id}/knowledge/deltas/reject` | 驳回变更 |
| `POST` | `/projects/{id}/knowledge/search` | 语义搜索 |

路由注册在 `main.py` 中，与现有路由一致。

---

## 前端

### 新增 API Client: `frontend/src/api/knowledge.ts`

```typescript
export const knowledgeApi = {
  getSummary: (projectId: string) => client.get(`/projects/${projectId}/knowledge/summary`),
  getTimeline: (projectId: string) => client.get(`/projects/${projectId}/knowledge/timeline`),
  getFacts: (projectId: string, params?: { entity_type?: string; entity_id?: string }) =>
    client.get(`/projects/${projectId}/knowledge/facts`, { params }),
  getRelationships: (projectId: string) => client.get(`/projects/${projectId}/knowledge/relationships`),
  getForeshadowing: (projectId: string) => client.get(`/projects/${projectId}/knowledge/foreshadowing`),
  getDeltas: (projectId: string, sessionId?: string) =>
    client.get(`/projects/${projectId}/knowledge/deltas`, { params: { session_id: sessionId } }),
  confirmDeltas: (projectId: string, data: { delta_ids?: string[]; session_id?: string }) =>
    client.post(`/projects/${projectId}/knowledge/deltas/confirm`, data),
  rejectDeltas: (projectId: string, data: { delta_ids?: string[]; session_id?: string }) =>
    client.post(`/projects/${projectId}/knowledge/deltas/reject`, data),
  search: (projectId: string, query: string) =>
    client.post(`/projects/${projectId}/knowledge/search`, { query }),
};
```

### 新增类型: `frontend/src/types/index.ts`

```typescript
export interface KnowledgeFact { ... }
export interface KnowledgeEvent { ... }
export interface KnowledgeRelationship { ... }
export interface KnowledgeForeshadowing { ... }
export interface KnowledgeDelta { id: string; operation: string; summary: string; status: string; created_at: string; }
export interface KnowledgeSummary { recent_events: KnowledgeEvent[]; key_facts: KnowledgeFact[]; pending_foreshadowing: KnowledgeForeshadowing[]; active_relationships: KnowledgeRelationship[]; }
```

### 新增组件

#### `KnowledgeConfirmPanel` — 增量确认面板

- 浮在聊天页面底部的 Toast/Banner，显示"本次对话产生了 N 条新知识"
- 点击展开 Drawer，列出所有 `pending` 状态的 delta
- 每条显示 `summary` + `[确认] [驳回]` 按钮
- 底部有"全部确认"和"全部驳回"批量操作

#### `KnowledgeTimeline` — 时间线面板（可选）

- 项目页面左侧/右侧可展开的时间线视图
- 按章节号排序显示事件
- 筛选：按角色/事件类型

#### `KnowledgeBadge` — 知识库入口徽章

- 在项目页面的 `SecondaryNav` 新增"知识库"导航项
- 有未确认变更时显示红点徽章

---

## 效果示意

```
[聊天中] 用户发送消息 → AI 流式回复 → 回复完成
                                          ↓
                      ├─ 有知识变更 ──→ 底部出现提示条:
                      |                  "📋 本次对话产生了 3 条可记录的知识点"
                      |                   [查看详情]
                      |                   ↓
                      |                Drawer 展开:
                      |                ├── [新增] 李逍遥 修为=金丹期  [确认] [驳回]
                      |                ├── [新增] 赵灵儿 身世=女娲后人 [确认] [驳回]
                      |                └── [变更] 林月如 生死=存活 → 昏迷 [确认] [驳回] ⚠️
                      |
                      └─ 无变更 ──→ 静默，用户无感知
                      
[下次对话] project_context 自动注入:
  - 知识摘要包含李逍遥修为、赵灵儿身世、林月如状态
  - Agent 回复时自动参考这些知识，减少矛盾
```

---

## 文件清单

### 新增文件

| 文件 | 说明 |
|------|------|
| `backend/app/services/knowledge.py` | `KnowledgeService` — 知识库 CRUD + 冲突检测 + 语义搜索 |
| `backend/app/services/knowledge_extractor.py` | `KnowledgeExtractor` — LLM 调用提取结构化知识 |
| `backend/app/api/v1/knowledge.py` | Knowledge API 路由 |
| `frontend/src/api/knowledge.ts` | 前端 API client |
| `frontend/src/components/knowledge/KnowledgeConfirmPanel.tsx` | 增量确认面板 |

### 修改文件

| 文件 | 修改内容 |
|------|----------|
| `backend/app/db/schema.sql` | 新增 5 张表 |
| `backend/app/services/content.py` | `ContentService` 新增知识库相关方法（可选） |
| `backend/app/api/v1/chat.py` | 流结束后触发知识提取 |
| `backend/app/core/graph/state.py` | `ProjectContext` 新增 `knowledge_summary` 字段 |
| `backend/app/main.py` | 注册 knowledge router |
| `backend/pyproject.toml` | 新增 `sentence-transformers` 依赖 |
| `frontend/src/types/index.ts` | 新增知识库类型 |
| `frontend/src/components/layout/SecondaryNav.tsx` | 新增"知识库"导航项 |
| `frontend/src/components/ai/ChatCore.tsx` | 集成 `KnowledgeConfirmPanel` |
