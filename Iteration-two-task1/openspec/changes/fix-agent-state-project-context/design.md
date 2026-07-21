# Fix Agent State Project Context - Design

## Problem Analysis

### Bug Location 1: chat.py:85
```python
initial_state: OrchestratorState = {
    ...
    "project_context": {"world_settings": [], "characters": [], "outline": None, "chapters": []},  # <- 硬编码为空！
    ...
}
```

### Bug Location 2: builder.py orchestrator_node
`ORCHESTRATOR_USER_TEMPLATE` 已定义但从未使用，导致 LLM 收不到项目上下文。

---

## Solution Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    chat_stream_endpoint                              │
│  1. 验证 session.project_id == URL.project_id                       │
│  2. 加载项目上下文（新增）                                           │
│  3. 创建 initial_state                                               │
└─────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  新增: load_project_context(project_id) → ProjectContext             │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  ContentService:                                            │   │
│  │  - get_all_world_settings(project_id) → list[dict]         │   │
│  │  - get_all_characters(project_id) → list[dict]             │   │
│  │  - get_root_outline(project_id) → dict | None               │   │
│  │  - get_all_chapters(project_id) → list[dict]               │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  orchestrator_node (修改)                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ messages = [                                                 │   │
│  │   {"role": "system", "content": ORCHESTRATOR_SYSTEM},      │   │
│  │   {"role": "user", "content": ORCHESTRATOR_USER_TEMPLATE   │   │
│  │     .format(project_context=state["project_context"], ...)} │   │
│  │ ] + conversation_history                                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## File Modifications

### 1. content.py - 新增查询方法

```python
async def get_all_world_settings(self, project_id: str) -> list[dict]:
    """获取项目所有世界观的元数据（不含content）"""
    cursor = await self.db.execute(
        "SELECT id, project_id, name, summary, created_at, updated_at
         FROM world_settings_meta WHERE project_id = ?",
        (project_id,)
    )
    return [dict(row) for row in await cursor.fetchall()]

async def get_all_characters(self, project_id: str) -> list[dict]:
    """获取项目所有角色的元数据（不含content）"""
    cursor = await self.db.execute(
        "SELECT id, project_id, world_setting_id, name, summary,
                created_at, updated_at
         FROM characters_meta WHERE project_id = ?",
        (project_id,)
    )
    return [dict(row) for row in await cursor.fetchall()]

async def get_root_outline(self, project_id: str) -> dict | None:
    """获取项目根大纲（parent_id IS NULL）"""
    cursor = await self.db.execute(
        "SELECT * FROM outlines_meta
         WHERE project_id = ? AND parent_id IS NULL LIMIT 1",
        (project_id,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None

async def get_all_chapters(self, project_id: str) -> list[dict]:
    """获取项目所有章节的元数据（不含content）"""
    cursor = await self.db.execute(
        "SELECT id, project_id, outline_id, title, word_count, status,
                created_at, updated_at
         FROM chapters_meta WHERE project_id = ?",
        (project_id,)
    )
    return [dict(row) for row in await cursor.fetchall()]
```

### 2. chat.py - 加载并注入上下文

```python
async def chat_stream_endpoint(...):
    # ... 验证逻辑 ...

    # 新增：加载项目上下文
    async with get_db() as db:
        content_service = ContentService(db)
        world_settings = await content_service.get_all_world_settings(project_id)
        characters = await content_service.get_all_characters(project_id)
        outline = await content_service.get_root_outline(project_id)
        chapters = await content_service.get_all_chapters(project_id)

    # 修改：使用实际数据
    initial_state: OrchestratorState = {
        "messages": messages,
        "session_id": session_id,
        "project_id": project_id,
        "project_context": {
            "world_settings": world_settings,
            "characters": characters,
            "outline": outline,
            "chapters": chapters,
        },
        "pending_tool_calls": [],
        "streaming_tokens": "",
        "tool_results": [],
    }
```

### 3. builder.py - 使用模板注入上下文

```python
async def orchestrator_node(state: OrchestratorState) -> dict[str, Any]:
    """Main orchestrator node - LLM decides tool calls based on intent."""

    # 构建用户消息，包含项目上下文
    user_message = ORCHESTRATOR_USER_TEMPLATE.format(
        world_settings=state["project_context"]["world_settings"],
        characters=state["project_context"]["characters"],
        outline=state["project_context"]["outline"],
        chapters=state["project_context"]["chapters"],
        user_request=state["messages"][-1].content if state["messages"] else "",
    )

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": ORCHESTRATOR_SYSTEM},
        {"role": "user", "content": user_message},
    ]

    # 添加对话历史（ToolMessages 需要特殊处理）
    for m in state["messages"]:
        if isinstance(m, ToolMessage):
            messages.append({
                "role": "tool",
                "content": m.content,
                "tool_call_id": m.tool_call_id,
                "name": m.name,
            })
        elif hasattr(m, "content"):
            messages.append({
                "role": m.type if hasattr(m, "type") else "user",
                "content": m.content,
            })

    # ... 其余逻辑不变 ...
```

### 4. orchestrator.py - 确保模板格式正确

```python
ORCHESTRATOR_USER_TEMPLATE = """Current project context:
- World settings: {world_settings}
- Characters: {characters}
- Outline: {outline}
- Chapters: {chapters}

User request: {user_request}

What is the user's intent and which tools should be used?"""
```

---

## Data Flow

```
User Request
    │
    ▼
chat_stream_endpoint()
    │
    ├─► verify_project_binding()
    │
    ├─► ContentService.get_all_world_settings() ──► List[WorldSettingMeta]
    ├─► ContentService.get_all_characters() ──────► List[CharacterMeta]
    ├─► ContentService.get_root_outline() ────────► OutlineMeta | None
    └─► ContentService.get_all_chapters() ────────► List[ChapterMeta]
    │
    ▼
initial_state.project_context = {
    "world_settings": [...],  # 完整列表
    "characters": [...],       # 完整列表
    "outline": {...} | None,   # 根大纲
    "chapters": [...],         # 完整列表
}
    │
    ▼
orchestrator_node()
    │
    └─► ORCHESTRATOR_USER_TEMPLATE.format(project_context=...)
        │
        ▼
        LLM 收到完整上下文
```

---

## Token 预算考虑

为避免 context 过大导致 token 溢出，采取以下策略：

| 数据类型 | 存储内容 | Token 估算 |
|---------|---------|-----------|
| world_settings | `{id, name, summary}` | ~100 chars/条 |
| characters | `{id, name, summary, world_setting_id}` | ~80 chars/条 |
| outline | `{id, title, type, parent_id}` | ~100 chars |
| chapters | `{id, title, word_count, status}` | ~60 chars/条 |

假设项目有：10 个世界观 + 20 个角色 + 1 个大纲 + 50 章
总 token 约：10×100 + 20×80 + 100 + 50×60 = 1000 + 1600 + 100 + 3000 = ~5700 chars ≈ ~1500 tokens

在可接受范围内。如需进一步优化，可限制返回数量或使用 summary 而非完整数据。

---

## 测试策略

### 单元测试
1. `test_content_service.py` - 测试新增的 4 个查询方法
2. `test_builder.py` - 验证 orchestrator_node 正确使用模板

### 集成测试
1. `test_e2e_chat.py` - 验证带项目上下文的对话流程

### 测试场景
1. 新项目（无任何数据）→ project_context 全为空
2. 有数据的项目 → project_context 正确填充
3. 大项目（大量数据）→ 不超出 token 限制
