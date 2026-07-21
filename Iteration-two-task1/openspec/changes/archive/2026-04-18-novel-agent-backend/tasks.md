# Implementation Tasks

## Phase 1: Project Setup

- [x] 1.1 Update `pyproject.toml` with all required dependencies
- [x] 1.2 Update `config.py` with new settings (LLM_PROVIDER, LLM_BASE_URL, LLM_MODEL)
- [x] 1.3 Verify `backend/.env` has required LLM configuration (ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, LLM_MODEL)
- [x] 1.4 Create `backend/app/db/schema.sql` with SQLite schema (metadata only)
- [x] 1.5 Create `backend/app/db/connection.py` with aiosqlite connection pool

## Phase 2: Storage Layer (Project Isolation Enforced)

- [x] 2.1 Create `services/content.py` with ContentService and FileSystemStorage
- [x] 2.2 Create `services/project_repository.py` with project-scoped queries (ALL queries MUST include project_id filter)
- [x] 2.3 Create `services/session_repository.py` with session.project_id binding verification
- [x] 2.4 Implement Project model (SQLite: create, get, update, list)
- [x] 2.5 Implement ChatSession model with project_id binding (SQLite: create, get, verify_project_binding, list_by_project)
- [x] 2.6 Implement ChatHistory model (SQLite: create, list_by_session - always filtered by session.project_id)
- [x] 2.7 Implement WorldSetting: SQLite meta + Markdown content (create, get, search, update, delete - project_id required)
- [x] 2.8 Implement Character: SQLite meta + Markdown content (create, get, search, update, delete - project_id required)
- [x] 2.9 Implement Outline: SQLite meta + Markdown content, nested (create, get, search, update, delete, get_children - project_id required)
- [x] 2.10 Implement Chapter: SQLite meta + Markdown content (create, get, update, delete - project_id required)
- [x] 2.11 Implement Review model (SQLite: create, get_by_content - project_id required)

## Phase 3: LLM Service

- [x] 3.1 Create `services/llm.py` with client factory
- [x] 3.2 Add `ChatAnthropic` (or compatible) client creation
- [x] 3.3 Add streaming support configuration
- [x] 3.4 Add base_url override support for compatible APIs

## Phase 4: Prompts

- [x] 4.1 Create `prompts/orchestrator.py` with intent classification prompt
- [x] 4.2 Create `prompts/tools/world.py` for world_setting creation
- [x] 4.3 Create `prompts/tools/character.py` for character creation
- [x] 4.4 Create `prompts/tools/plot.py` for outline creation
- [x] 4.5 Create `prompts/tools/chapter.py` for chapter writing
- [x] 4.6 Create `prompts/tools/review.py` for content review

## Phase 5: Tool Registry & Base Classes (Project Isolation)

- [x] 5.1 Create `core/agent/tools/base.py` with BaseTool abstract class (no project_id in signature)
- [x] 5.2 Create `core/agent/registry.py` with ToolRegistry singleton
- [x] 5.3 Implement `create_world_setting` tool (project_id from State, not parameter)
- [x] 5.4 Implement `create_character` tool (project_id from State, not parameter)
- [x] 5.5 Implement `search_world_setting` tool (project_id from State, SQLite filtered)
- [x] 5.6 Implement `search_characters` tool (project_id from State, SQLite filtered)
- [x] 5.7 Implement `create_outline` tool (project_id from State, not parameter)
- [x] 5.8 Implement `write_chapter` tool (project_id from State, not parameter)
- [x] 5.9 Implement `review_content` tool (project_id from State, not parameter)
- [x] 5.10 Implement `update_project` tool (project_id from State, not parameter)

## Phase 6: LangGraph Orchestrator

- [x] 6.1 Create `core/graph/state.py` with OrchestratorState TypedDict (project_id: str, NOT Optional)
- [x] 6.2 Create `core/graph/builder.py` with StateGraph construction
- [x] 6.3 Implement `orchestrator_node` with LLM + tool calling (project_id bound to state)
- [x] 6.4 Implement `dynamic_tool_dispatcher` node (receives project_id from state, passes to tools)
- [x] 6.5 Add streaming support in `core/graph/streaming.py`
- [x] 6.6 Compile and export the graph

## Phase 7: API Endpoint (Project Isolation)

- [x] 7.1 Create `api/v1/projects.py` with project-scoped router `/projects/{project_id}`
- [x] 7.2 Create `api/v1/chat.py` with endpoint `/projects/{project_id}/sessions/{session_id}/chat/stream`
- [x] 7.3 Implement session validation: session.project_id MUST match URL project_id (return 403 if mismatch)
- [x] 7.4 Implement session creation endpoint `POST /projects/{project_id}/sessions`
- [x] 7.5 Implement SSE event generation
- [x] 7.6 Wire up orchestrator graph to endpoint (orchestrator receives project_id from session)
- [x] 7.7 Add error handling with proper SSE error events (403 for isolation violations)

## Phase 8: Integration & Testing

- [x] 8.1 Write unit tests for ContentService (read/write markdown files) - DONE
- [x] 8.2 Write unit tests for all tool implementations (verify no project_id in signatures) - DONE
- [x] 8.3 Write integration tests for database operations (verify project_id filtering) - DONE
- [x] 8.4 Write integration tests for orchestrator flow (verify project_id propagation) - DONE
- [x] 8.5 Test streaming output end-to-end - DONE (basic tests pass)
- [x] 8.6 Test session persistence and recovery - DONE (basic tests pass)
- [x] 8.7 Test markdown file editing directly (via file system) - DONE (basic tests pass)
- [x] 8.8 **Test project isolation**: verify tools cannot access data from other projects - DONE
- [x] 8.9 **Test API isolation**: verify session with wrong project_id returns 403 - DONE

## Phase 9: Cleanup

- [x] 9.1 Update `main.py` to include projects router
- [x] 9.2 Add health check enhancements
- [x] 9.3 Run ruff/mypy checks
- [x] 9.4 Verify all imports work correctly
