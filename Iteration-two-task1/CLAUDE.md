# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

AI-powered web novel generation platform that uses LangChain/LangGraph to orchestrate multiple specialized sub-agents (world-builder, character, plot, chapter, review) under a single supervisor. Long-form content is generated with consistency tracking across world-building, characters, plot, and chapters.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.13 + FastAPI |
| Frontend | React 18 + TypeScript + Vite |
| UI Library | Ant Design 6 (`antd`) |
| Agent Framework | LangChain + LangGraph |
| Persistence | SQLite (`aiosqlite`) for metadata + Markdown files for content |
| Checkpointing | `langgraph-checkpoint-sqlite` (`AsyncSqliteSaver`) |
| Package Manager | `uv` (Python), `npm` (Node) |
| LLM Provider | Anthropic Claude (`langchain-anthropic`) - the only supported provider in [llm.py](backend/app/services/llm.py) |

RULE: 涉及到前端的组件时，阅读 https://ant.design/llms-full.txt 并理解 Ant Design 组件库，在编写 Ant Design 代码时使用这些知识。

## Architecture

### Sub-Agents (5)

Implemented in [backend/app/core/agent/langchain_subagents.py](backend/app/core/agent/langchain_subagents.py) via `langchain.agents.create_agent`. Each is created per-call (no globals) with project-scoped tools:

- **world_builder**: Geography, culture, history, magic systems
- **character**: Profiles, relationships, personality
- **plot**: Story outlines, chapter breakdowns
- **chapter**: Actual prose writing
- **review**: Quality and consistency feedback

> Note: README/legacy docs mention an `EditorAgent`. It is not implemented in code; revisions are handled by re-invoking the chapter or review agent.

### Orchestrator (Subagents-as-Tools Pattern)

[backend/app/core/graph/builder.py](backend/app/core/graph/builder.py) uses `langchain.agents.create_agent` to build the orchestrator. Each sub-agent is wrapped as a `@tool` function (`delegate_to_world_builder`, `delegate_to_character`, etc.) that calls `subagent.ainvoke()` and returns the result. The orchestrator LLM decides which delegate tool to call based on the user's request.

### Critical Invariant: Closure-Bound `project_id`

Tools and sub-agents are **never** module-level singletons. [tool_factory.py](backend/app/core/agent/tool_factory.py) exposes `create_world_tools(project_id)`, `create_character_tools(project_id)`, etc., each of which uses Python closure to bake `project_id` into every `@tool` function. Sub-agent factories in [langchain_subagents.py](backend/app/core/agent/langchain_subagents.py) follow the same pattern. This is required for:

1. Thread/async safety
2. Project isolation - a tool call in project A cannot accidentally read/write project B
3. Allowing multiple concurrent chat sessions for different projects

When adding new tools or agents, follow this factory pattern - **do not** create module-level tool singletons that take `project_id` as an argument.

### State

[backend/app/core/graph/state.py](backend/app/core/graph/state.py) defines `OrchestratorState` (TypedDict). `project_id` is **immutable** once set. `project_context` carries metadata (no full content) for world settings, characters, outline, chapters, and is loaded fresh per request from SQLite in `chat_stream_endpoint` before invoking the graph.

### API Routes (`/api/v1`)

All content routers are nested under `/projects/{project_id}` for project isolation:

| Router | Path | File |
|--------|------|------|
| Projects | `/projects` | [projects.py](backend/app/api/v1/projects.py) |
| Chat (SSE) | `/projects/{project_id}/sessions[/{session_id}/chat/stream]` | [chat.py](backend/app/api/v1/chat.py) |
| World | `/projects/{project_id}/world` | [world.py](backend/app/api/v1/world.py) |
| Characters | `/projects/{project_id}/characters` | [characters.py](backend/app/api/v1/characters.py) |
| Outlines | `/projects/{project_id}/outlines` | [outlines.py](backend/app/api/v1/outlines.py) |
| Chapters | `/projects/{project_id}/chapters` | [chapters.py](backend/app/api/v1/chapters.py) |
| Reviews | `/projects/{project_id}/reviews` | [reviews.py](backend/app/api/v1/reviews.py) |

`update`/`delete` for content resources use `POST /{id}/update` and `POST /{id}/delete` (not PATCH/DELETE) for consistency.

### Services Layer

[backend/app/services/](backend/app/services/) was split from a monolithic `content.py` into per-domain services:

- [storage.py](backend/app/services/storage.py): `ContentStorage` Protocol + `FileSystemStorage` impl for `.md` files in `backend/data/{project_id}/`
- [world.py](backend/app/services/world.py), [character.py](backend/app/services/character.py), [outline.py](backend/app/services/outline.py), [chapter.py](backend/app/services/chapter.py), [review.py](backend/app/services/review.py): per-domain SQLite + file CRUD
- [content.py](backend/app/services/content.py): `ContentService` facade that composes the above (kept for backward compat)
- [llm.py](backend/app/services/llm.py): `create_llm_client` factory + `extract_content` helper
- `*_repository.py` (project, session, chat_history): SQLite-only repositories without file storage

### Database

SQLite at `backend/novel.db`. Schema in [schema.sql](backend/app/db/schema.sql) - metadata only, content lives as Markdown in `backend/data/{project_id}/`. Connection management in [connection.py](backend/app/db/connection.py) uses a single shared `aiosqlite.Connection` (see `_get_global_db`); `get_db()` and `get_transaction()` are async context managers that yield it.

LangGraph checkpoints share the same SQLite file via `AsyncSqliteSaver` ([checkpointer.py](backend/app/db/checkpointer.py)), initialized in FastAPI lifespan.

### Error Handling & Retry

[errors.py](backend/app/core/errors.py) classifies LLM exceptions into `AIError` with `error_code` + `retryable` flag. [retry.py](backend/app/core/retry.py) provides `with_retry()` async helper using exponential backoff with jitter. `tool_factory._invoke_llm_with_retry()` is the sync equivalent used inside tools. Retry tunables come from env: `LLM_MAX_RETRIES` (default 3), `LLM_RETRY_BASE_DELAY` (default 1.0).

## Frontend Architecture

Frontend implementation: [frontend/](frontend/) - React 18 + TypeScript + Vite + Ant Design 6

### Key Design Decisions

- **Layout**: Classic sidebar layout using Ant Design `Layout` + `Sider` + `Menu`
- **AI Chat**: Floating Action Button (`FloatButton`) with expandable `Drawer` panel
- **Content Tags**: Parsed from Markdown YAML frontmatter using `gray-matter`
- **Outline Editor**: Ant Design `Tree` with built-in `draggable` support
- **Markdown Editor**: `@uiw/react-md-editor` for world/character/chapter editing
- **Theming**: Ant Design ConfigProvider with Design Tokens (`theme.useToken()`)

### Frontend Module Structure

```
frontend/src/
├── api/                    # Axios API clients per domain
├── components/
│   ├── layout/             # AppLayout, IconSidebar, SecondaryNav
│   ├── ai/                 # AIFab, ChatPanel, MessageBubble, ThinkingBlock
│   ├── common/             # MarkdownEditor, PageHeader, EmptyState
│   └── cards/              # ProjectCard, WorldCard, CharacterCard
├── pages/                  # Route-level page components
├── hooks/                  # Custom hooks (useProject, useAIChat, useSSE)
├── contexts/               # React Context (ProjectContext, AIContext)
├── types/                  # TypeScript type definitions
└── utils/                  # format.ts, constants.ts
```

### Frontend Routes

| Path | Page | Description |
|------|------|-------------|
| `/` | Dashboard | Project list and creation |
| `/projects/:id/world` | WorldList | World settings management |
| `/projects/:id/world/:worldId` | WorldEdit | World setting editor |
| `/projects/:id/characters` | CharacterList | Character management |
| `/projects/:id/characters/:charId` | CharacterEdit | Character editor |
| `/projects/:id/outline` | OutlineEditor | Tree-based outline editor |
| `/projects/:id/chapters` | ChapterList | Chapter management |
| `/projects/:id/chapters/:chapterId` | ChapterEdit | Chapter editor |
| `/projects/:id/reviews` | ReviewList | Review reports |
| `/projects/:id/settings` | ProjectSettings | Project settings |

## Commands

### Frontend (run from `frontend/`)
```bash
npm install                                    # Install deps
npm run dev                                    # Dev server (port 5173)
npm run build                                  # Production build
npm run type-check                             # TypeScript check
npm run lint                                   # ESLint
```

### Backend (run from `backend/`)
```bash
uv sync                                          # Install deps
uv run uvicorn app.main:app --reload             # Dev server (port 8000)
uv run pytest                                    # Run all tests
uv run pytest tests/test_tools.py                # Run a single test file
uv run pytest tests/test_tools.py::test_name -v  # Run a single test by name
uv run pytest -k "characters"                    # Run tests matching keyword
uv run pytest --cov=app --cov-report=term        # With coverage
uv run mypy app                                  # Strict type-check (`tool.mypy.strict = true`)
uv run ruff check app tests                      # Lint
uv run ruff format app tests                     # Format
uv run ruff format --check app tests             # Format check (CI mode)
```

### Combined dev environment
```bash
python start-dev.py                              # Starts backend (8000) + agent-tester (8080)
```
[start-dev.py](start-dev.py) launches `uvicorn` for the backend and a `python -m http.server` for the standalone HTML test UI in [agent-tester/](agent-tester/).

### Frontend dev (separate terminal)
```bash
cd frontend && npm run dev                       # Starts frontend dev server (5173)
```

### Docker
The repo ships a backend Dockerfile ([backend/Dockerfile](backend/Dockerfile)) but **does not include a `docker-compose.yml`**. Build images individually if needed.

## Environment Variables

`backend/.env` (template at [backend/.env.example](backend/.env.example), parsed by [config.py](backend/app/config.py)):

| Variable | Default | Purpose |
|----------|---------|---------|
| `ANTHROPIC_API_KEY` | (required) | Claude API key - empty string raises `ValueError` from `create_llm_client` |
| `LLM_PROVIDER` | `anthropic` | Only `anthropic` is implemented |
| `LLM_MODEL` | `claude-sonnet-4-20250514` | Anthropic model id |
| `LLM_BASE_URL` | _(none)_ | Optional override for proxy endpoints |
| `DATABASE_URL` | `sqlite+aiosqlite:///./novel.db` | SQLite path |
| `CORS_ORIGINS` | `[5173, 3000, 8080]` localhost | CORS allowed origins (list) |
| `DEBUG` | `false` | Toggle |
| `LLM_MAX_RETRIES` | `3` | Read directly via `os.environ` in [errors.py](backend/app/core/errors.py) |
| `LLM_RETRY_BASE_DELAY` | `1.0` | Same |

There is no `SECRET_KEY` / JWT layer - the API does not authenticate clients.

## Git Workflow with Claude Code

### Feature Isolation via Worktrees

Use `EnterWorktree` for any non-trivial feature or bugfix. This creates a branch + isolated directory under `.claude/worktrees/` and keeps the original workspace untouched.

- **When to use**: new features, experimental refactors, parallel reviews, or any task that may span multiple commits.
- **When to skip**: one-line fixes, README updates, or changes that touch a single file and are committed immediately.
- **Exit**: `ExitWorktree` with `keep` preserves the directory for later; `remove` deletes it after the branch is merged or abandoned.

### Commit Granularity

Prefer **atomic commits** — each commit should represent one logical unit that passes tests and type-checks independently.

- Good: `feat(api): add POST /characters endpoint` + `test(api): cover character creation edge cases`
- Avoid: bundling unrelated refactors, bug fixes, and formatting into a single commit.

Claude Code will prompt for commits at natural boundaries (after a passing test suite, before switching domains, or at the end of a plan step). You can direct it with:
- `"Commit after each file"`
- `"Commit at the end"`
- `"Split this into logical commits"`

### Commit Message Style

Follow the repository's existing style (visible in `git log`). General template:

```
<type>(<scope>): <imperative description>

<body explaining why, not what>
```

Common types: `feat`, `fix`, `refactor`, `test`, `docs`, `style`.

### Rhythm: Plan → Code → Verify → Commit

1. **Plan**: For multi-file or architectural changes, enter `Plan` mode first. Confirm the approach before writing code.
2. **Code**: Implement in the worktree, one module at a time.
3. **Verify**: Run the relevant subset of `pytest`, `mypy`, and `ruff` before claiming completion.
4. **Commit**: Stage only the files related to the current logical unit. If pre-commit hooks fail, fix all errors before committing.

## Tests

`backend/tests/` (15+ files). Notable patterns:

- `test_*_api.py` - FastAPI route tests (TestClient + isolated SQLite)
- `test_orchestrator.py` - Graph wiring without LLM calls
- `test_tools.py` - Tool registration / signature verification
- `test_tool_error_handling.py`, `test_chat_error_handling.py` - LLM failure paths
- `test_retry.py` - `with_retry` exponential backoff behaviour
- `test_state_bloat.py` - Guards against unbounded state growth in long sessions
- `test_content_service.py` - CRUD facade
- `test_database.py` - Schema migration / connection lifecycle
- `test_characters_e2e.py` - End-to-end flow

`pytest.ini_options.asyncio_mode = "auto"` so `async def test_...` works without explicit markers.

## Repository-Specific Conventions

- **No mocks/stubs without authorization**: When you can't implement something, raise `NotImplementedError` rather than silently returning fake data. (See user memory `feedback_no_mock_stub.md`.)
- **`pre-commit` runs full mypy**: Hook 失败时修好所有错误再提交，不使用 `--no-verify`。
- **Hosting is GitLab, not GitHub**: CI lives in [.gitlab-ci.yml](.gitlab-ci.yml). The `glab` CLI is available for GitLab API operations.
- **Mirror sources for CI**: Both Dockerfiles and `.gitlab-ci.yml` use Nanjing University mirrors (`mirror.nju.edu.cn`) for npm/pypi to work around network constraints.

## OpenSpec

[openspec/](openspec/) tracks feature changes via the `openspec` workflow (proposals, design, tasks, archived changes). The `openspec-*` and `opsx:*` skills are available for creating and applying changes.

## Module Map

```
backend/app/
├── main.py                       # FastAPI entry, lifespan, CORS, router registration
├── config.py                     # Pydantic Settings (env loader)
├── api/v1/                       # 7 routers (see API table above)
├── core/
│   ├── agent/
│   │   ├── tool_factory.py       # create_*_tools(project_id) factories - the heart of project scoping
│   │   └── langchain_subagents.py# create_*_agent(project_id) factories
│   ├── graph/
│   │   ├── builder.py            # create_orchestrator_graph - subagents-as-tools wiring
│   │   └── state.py              # OrchestratorState, ProjectContext TypedDicts
│   ├── prompts/orchestrator.py   # ORCHESTRATOR_SYSTEM prompt
│   ├── errors.py                 # AIError, classify_llm_error, RetryConfig
│   ├── retry.py                  # with_retry async helper
│   ├── logging_utils.py          # get_logger, log_ai_error, log_stream_complete
│   └── serialization_utils.py    # safe_json_value (for SSE payloads)
├── services/                     # Per-domain content services + repositories (see Services Layer)
└── db/
    ├── connection.py             # Shared aiosqlite connection + get_db / get_transaction
    ├── checkpointer.py           # AsyncSqliteSaver singleton
    └── schema.sql                # Metadata schema (8 tables)

frontend/
├── src/
│   ├── api/                    # Axios API clients per domain
│   ├── components/
│   │   ├── layout/             # AppLayout, IconSidebar, SecondaryNav
│   │   ├── ai/                 # AIFab, ChatPanel, MessageBubble, ThinkingBlock
│   │   ├── common/             # MarkdownEditor, PageHeader, EmptyState
│   │   └── cards/              # ProjectCard, WorldCard, CharacterCard
│   ├── pages/                  # Route-level page components
│   ├── hooks/                  # Custom hooks
│   ├── contexts/               # React Context
│   ├── types/                  # TypeScript types
│   └── utils/                  # format.ts, constants.ts
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── .env.development

agent-tester/index.html           # Standalone Vue 3 + marked HTML page for ad-hoc agent testing
docs/                             # API.md, evaluation_report.md, specs/, plans/
```