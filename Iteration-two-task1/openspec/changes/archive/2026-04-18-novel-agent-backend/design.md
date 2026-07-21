# Novel Agent Backend Design

## System Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                              │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  /api/v1/projects/{project_id}/sessions/{session_id}/chat/stream │   │
│  └────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent (Per-Project Isolated)            │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │              LangGraph StateGraph (project_id bound)              │   │
│  │  ┌──────────────┐    ┌──────────────────────────────────┐       │   │
│  │  │ orchestrator │───▶│ dynamic_tool_dispatcher           │       │   │
│  │  │   _node      │    │  (receives project_id from state) │       │   │
│  │  └──────────────┘    └───────────────┬───────────────────┘       │   │
│  │                                        │                           │   │
│  │  ┌─────────────────────────────────────┼─────────────────────┐    │   │
│  │  │        8 Sub-Agent Tools (project_id implicit)              │    │   │
│  │  │                                                           │    │   │
│  │  │ create_world_setting        write_chapter                 │    │   │
│  │  │ create_character            review_content                │    │   │
│  │  │ search_world_setting        update_project                │    │   │
│  │  │ search_characters                                          │    │   │
│  │  │ create_outline                                             │    │   │
│  │  └───────────────────────────────────────────────────────────┘    │   │
│  └────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────┘
                                      │
          ┌────────────────────────────┴────────────────────────────┐
          ▼                                                         ▼
┌─────────────────────────┐                    ┌─────────────────────────────────────────┐
│       SQLite DB         │                    │         File System (project isolated)   │
│                         │                    │                                         │
│  Session.project_id =   │                    │  backend/data/{project_id}/             │
│    URL.project_id ✓    │                    │    ├── project.json                     │
│                         │                    │    ├── world_settings/{id}.md           │
│  ALL queries include:   │                    │    ├── characters/{id}.md               │
│  WHERE project_id = ?   │                    │    ├── outlines/{id}.md                 │
│                         │                    │    └── chapters/{id}.md                 │
└─────────────────────────┘                    └─────────────────────────────────────────┘
```

---

## Directory Structure

```
backend/
├── app/
│   ├── main.py                      # FastAPI app entry
│   ├── config.py                    # Settings
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── projects.py           # /projects/{project_id} routes
│   │       └── chat.py              # /projects/{project_id}/sessions/{session_id}/chat/stream
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py      # Orchestrator Agent
│   │   │   ├── tools/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py          # Base tool class
│   │   │   │   ├── world.py         # create/search world_setting
│   │   │   │   ├── character.py     # create/search character
│   │   │   │   ├── plot.py          # create/search outline
│   │   │   │   ├── chapter.py       # write_chapter
│   │   │   │   ├── review.py        # review_content
│   │   │   │   └── project.py       # update_project
│   │   │   └── registry.py          # Tool registry
│   │   ├── graph/
│   │   │   ├── __init__.py
│   │   │   ├── state.py             # OrchestratorState
│   │   │   ├── builder.py           # LangGraph builder
│   │   │   └── streaming.py         # Streaming handlers
│   │   └── prompts/
│   │       ├── __init__.py
│   │       ├── orchestrator.py      # Orchestrator prompt
│   │       └── tools/
│   │           ├── world.py
│   │           ├── character.py
│   │           ├── plot.py
│   │           ├── chapter.py
│   │           └── review.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py            # aiosqlite connection
│   │   └── schema.sql               # SQLite schema
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py                # Pydantic models
│   └── services/
│       ├── __init__.py
│       └── llm.py                    # LLM client factory
├── data/                              # 项目内容文件存储
│   └── {project_id}/
│       ├── project.json               # 项目元数据
│       ├── world_settings/
│       │   ├── {id}.md              # 世界观正文
│       │   └── {id}.meta.json       # 搜索用元数据
│       ├── characters/
│       │   ├── {id}.md
│       │   └── {id}.meta.json
│       ├── outlines/
│       │   └── {id}.md
│       └── chapters/
│           ├── {id}.md
│           └── {id}.meta.json
└── novel.db                          # SQLite 数据库文件
```

---

## Storage Strategy: Hybrid SQLite + File System

### Storage Allocation

| Data Type | Storage | Reason |
|-----------|---------|--------|
| projects | SQLite | 轻量元数据，需要快速查询 |
| chat_sessions | SQLite | 会话管理，需要关联查询 |
| chat_history | SQLite | 快速读写，消息流 |
| world_settings | Markdown + SQLite meta | 内容结构灵活，需要直接编辑 |
| characters | Markdown + SQLite meta | 内容灵活，关系复杂 |
| outlines | Markdown + SQLite meta | 支持嵌套结构 |
| chapters | Markdown + SQLite meta | 主要写作内容 |
| reviews | SQLite | 元数据为主，轻量 |

### File Storage Format

**World Settings (`{id}.md`)**:
```markdown
# 世界设定：{name}

## 地理
{geography_content}

## 文化
{culture_content}

## 历史
{history_content}

## 魔法体系
{magic_system_content}
```

**Character (`{id}.md`)**:
```markdown
# 角色：{name}

## 基本信息
- 性格：{personality}
- 外貌：{appearance}

## 背景故事
{background}

## 关系网络
{relationships_markdown}
```

**Outline (`{id}.md`)**:
```markdown
# {title}
类型：{type}

{content}

## 子节点
- [[child_outline_id_1]]
- [[child_outline_id_2]]
```

**Chapter (`{id}.md`)**:
```markdown
# {title}

{chapter_content}
```

### SQLite Schema (Metadata Only)

```sql
-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    data_path TEXT NOT NULL,      -- 相对于 backend/data/ 的路径
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat history table
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT REFERENCES chat_sessions(id),
    role TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    tool_calls TEXT,    -- JSON array of tool calls made
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- World settings metadata (content in .md file)
CREATE TABLE IF NOT EXISTS world_settings_meta (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    name TEXT NOT NULL,
    file_path TEXT NOT NULL,       -- 相对于项目 data_path
    summary TEXT,                  -- 用于搜索的摘要
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Characters metadata (content in .md file)
CREATE TABLE IF NOT EXISTS characters_meta (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    world_setting_id TEXT REFERENCES world_settings_meta(id),
    name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Outlines metadata (content in .md file, supports nesting)
CREATE TABLE IF NOT EXISTS outlines_meta (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    parent_id TEXT REFERENCES outlines_meta(id),
    title TEXT NOT NULL,
    file_path TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'arc', 'chapter', 'scene'
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chapters metadata (content in .md file)
CREATE TABLE IF NOT EXISTS chapters_meta (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    outline_id TEXT UNIQUE REFERENCES outlines_meta(id),
    title TEXT NOT NULL,
    file_path TEXT NOT NULL,
    word_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'draft',  -- 'draft', 'review', 'published'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reviews table
CREATE TABLE IF NOT EXISTS reviews (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    content_type TEXT NOT NULL,  -- 'world_setting', 'character', 'outline', 'chapter'
    content_id TEXT NOT NULL,
    issues TEXT,                  -- JSON array
    suggestions TEXT,              -- JSON array
    overall_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Content Service Layer

```python
# services/content.py
import aiosqlite
from pathlib import Path
from typing import Protocol

class ContentStorage(Protocol):
    """Protocol for content storage operations"""
    async def read(self, file_path: Path) -> str: ...
    async def write(self, file_path: Path, content: str) -> None: ...
    async def delete(self, file_path: Path) -> None: ...

class FileSystemStorage:
    """Markdown file storage"""
    def __init__(self, base_path: Path):
        self.base_path = base_path

    async def read(self, file_path: Path) -> str:
        full_path = self.base_path / file_path
        return await aiosqlite.path.read_text(full_path)

    async def write(self, file_path: Path, content: str) -> None:
        full_path = self.base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        await aiosqlite.path.write_text(full_path, content)

class ContentService:
    """Unified content access layer"""
    def __init__(self, db: aiosqlite.Connection, storage: FileSystemStorage):
        self.db = db
        self.storage = storage

    # World Settings
    async def create_world_setting(self, project_id: str, name: str, content: str) -> dict:
        # 1. Insert meta to SQLite
        # 2. Write content to .md file
        # 3. Return created record
        pass

    async def get_world_setting(self, id: str) -> dict | None:
        # 1. Get meta from SQLite
        # 2. Read content from .md file
        # 3. Return merged result
        pass

    async def search_world_settings(self, project_id: str, query: str) -> list[dict]:
        # 1. SQLite FTS or LIKE on summary
        # 2. Return matching records
        pass

    # Similar for characters, outlines, chapters...
```

---

## LangGraph State Design

```python
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import add_messages

class ProjectContext(TypedDict):
    """Project context passed between tools - all scoped to project_id"""
    world_settings: list[dict]      # 已创建的世界观
    characters: list[dict]           # 已创建的角色
    outline: dict | None             # 当前大纲
    chapters: list[dict]             # 已写的章节

class OrchestratorState(TypedDict):
    """Main state for the orchestrator graph - project_id is IMMUTABLE once set"""
    messages: Annotated[list[BaseMessage], add_messages]
    session_id: str
    project_id: str  # Required - set at session creation, never changes
    project_context: ProjectContext
    pending_tool_calls: list[dict]   # 待执行的工具调用
    streaming_tokens: str             # 用于流式输出的累积 token
```

**Isolation Guarantee**: `project_id` 在 OrchestratorState 中是必填字段，且在会话生命周期内不可变。所有工具通过 `OrchestratorState.project_id` 获取当前项目上下文，无法访问其他项目的数据。

---

## Streaming API Design

### Endpoint: POST /api/v1/projects/{project_id}/sessions/{session_id}/chat/stream

**Project Isolation**: URL 中的 `project_id` 和 `session_id` 都是必选的，所有操作都在该项目上下文中执行。

**Request:**
```json
{
  "message": "帮我创建一个玄幻小说的世界观"
}
```

**Note**: `project_id` 和 `session_id` 都不在请求体中。如果 `session_id` 不属于该 `project_id`，返回 `403 Forbidden`。

**Response:** SSE (Server-Sent Events)

```
event: intent
data: {"intent": "create_world", "confidence": 0.95}

event: tool_start
data: {"tool": "create_world_setting", "tool_call_id": "call_123"}

event: token
data: {"token": "某"}

event: token
data: {"token": "世"}

event: tool_end
data: {"tool": "create_world_setting", "result": {...}}

event: message
data: {"content": "我已经为你创建了一个玄幻世界观...", "tool_calls": [...]}

event: done
data: {}
```

**Event Types:**
| Event | 说明 |
|-------|------|
| `intent` | 识别的用户意图 |
| `tool_start` | 工具开始执行 |
| `token` | LLM 输出的 token |
| `tool_end` | 工具执行完成 |
| `message` | 最终消息 |
| `error` | 错误信息 |
| `done` | 流结束 |

### API Isolation Verification

```
Request Flow:
1. Client → POST /api/v1/projects/{project_id}/sessions/{session_id}/chat/stream
2. API validates project_id exists
3. Verify session.project_id == project_id → 403 if mismatch
4. Load project_context for session.project_id
5. OrchestratorState.project_id = session.project_id (immutable)
6. All tool calls operate within project_id scope
```

### Session Lifecycle

| 操作 | 说明 |
|------|------|
| Create Session | POST /projects/{project_id}/sessions |
| Get Sessions | GET /projects/{project_id}/sessions |
| Chat | POST /projects/{project_id}/sessions/{session_id}/chat/stream |
| Delete Session | DELETE /projects/{project_id}/sessions/{session_id} |

---

## Tool Registry Pattern

```python
from typing import Callable
from dataclasses import dataclass

@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: type  # Pydantic model
    handler: Callable

class ToolRegistry:
    """Central registry for all sub-agent tools"""
    _tools: dict[str, ToolDefinition] = {}

    @classmethod
    def register(cls, name: str, description: str, parameters: type):
        def decorator(func: Callable):
            cls._tools[name] = ToolDefinition(
                name=name,
                description=description,
                parameters=parameters,
                handler=func
            )
            return func
        return decorator

    @classmethod
    def get_tool(cls, name: str) -> ToolDefinition | None:
        return cls._tools.get(name)

    @classmethod
    def get_all_tools(cls) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters.model_json_schema()
            }
            for t in cls._tools.values()
        ]
```

---

## LLM Client Factory

```python
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from app.config import settings

def create_llm_client(
    provider: str = "anthropic",
    model: str = "claude-sonnet-4-20250514",
    base_url: str | None = None,
    api_key: str | None = None,
    streaming: bool = True
):
    """Factory for creating LLM clients"""
    if provider == "anthropic":
        return ChatAnthropic(
            model=model,
            base_url=base_url or os.environ.get("ANTHROPIC_BASE_URL"),
            api_key=api_key or settings.ANTHROPIC_API_KEY,
            streaming=streaming
        )
    elif provider == "openai":
        return ChatOpenAI(
            model=model,
            base_url=base_url,
            api_key=api_key,
            streaming=streaming
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")
```

---

## Configuration Updates

### config.py 新增字段

```python
class Settings(BaseSettings):
    # ... existing fields ...

    # LLM Provider
    LLM_PROVIDER: str = "anthropic"  # or "openai"
    LLM_BASE_URL: str | None = None  # Custom API endpoint (e.g., https://api.minimaxi.com/anthropic)
    LLM_MODEL: str = "claude-sonnet-4-20250514"

    # SQLite
    DATABASE_URL: str = "sqlite+aiosqlite:///./novel.db"
```

### .env 配置示例

```bash
# LLM Provider (Anthropic compatible)
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_BASE_URL=https://api.minimaxi.com/anthropic  # Optional, for compatible APIs
LLM_MODEL=claude-sonnet-4-20250514
```

---

## Dependencies (pyproject.toml)

```toml
[project]
name = "novel-generator"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.7.0",
    "langgraph>=0.4.0",
    "langchain-core>=0.3.0",
    "langchain-anthropic>=0.3.0",
    "aiosqlite>=0.20.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.25.0",
    "pytest-cov>=6.0.0",
    "httpx>=0.28.0",
    "ruff>=0.9.0",
    "mypy>=1.14.0",
]
```
