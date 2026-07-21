## Why

实现一个 agent 驱动的网络小说后端系统。当前项目骨架已完成（FastAPI + Python 3.13），但核心 agent 逻辑为空。用户需要一个能够通过自然语言对话生成网络小说的系统，支持世界观的动态创建、角色管理、剧情大纲规划和章节写作。

核心价值：
- 通过 LLM 动态路由，用户无需关心底层实现细节
- 流式输出提供实时反馈，改善用户体验
- SQLite 持久化确保项目状态和聊天历史不丢失

## What Changes

在 `backend/app/core/` 下新增三层架构：

1. **Agent 层** (`core/agent/`)
   - Orchestrator Agent：LLM 驱动的调度器，根据用户意图动态调用子工具
   - 8 个子 Agent 工具：create_world_setting, create_character, search_world_setting, search_characters, create_outline, write_chapter, review_content, update_project

2. **Graph 层** (`core/graph/`)
   - LangGraph 工作流定义
   - 状态管理（聊天历史、项目上下文）
   - 流式事件处理

3. **Prompts 层** (`core/prompts/`)
   - Agent 提示词模板
   - 工具调用描述

同时新增：
- SQLite 数据库层（会话、聊天历史、项目数据）
- FastAPI 流式聊天接口 (`/api/v1/chat/stream`)

## Capabilities

### New Capabilities

- **orchestrator-agent**: LLM 驱动的动态路由 Agent，根据用户消息意图调用合适的子工具
- **world-setting-agent**: 创建和搜索世界观设定（地理、文化、历史、魔法体系等）
- **character-agent**: 创建和搜索角色（名称、性格、背景、关系图谱）
- **plot-agent**: 创建和搜索剧情大纲（主线、支线、章节规划）
- **chapter-agent**: 章节写作（风格一致性、内容质量）
- **review-agent**: 内容审核（一致性检查、质量评估）
- **editor-agent**: 内容编辑修订
- **streaming-chat-api**: SSE 流式聊天接口，支持实时 token 输出
- **session-persistence**: SQLite 持久化存储会话和项目状态

### Modified Capabilities

- `main.py`: 新增 `/api/v1/chat/stream` 端点
- `config.py`: 新增 LLM base_url 配置项

## Impact

- **新增依赖**: langgraph, langchain-core, langchain-anthropic, aiosqlite, fastapi-sse
- **修改文件**: backend/app/main.py, backend/app/config.py, backend/pyproject.toml
- **新增文件**: core/agent/*, core/graph/*, core/prompts/*, db/schema.sql
- **API 变更**: 新增 `/api/v1/chat/stream` POST 接口
- **数据库**: SQLite 文件 `novel.db`
