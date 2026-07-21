# project-context-loading Specification

## Purpose
修复 Orchestrator Agent 无法感知项目已有数据的问题。通过在每次调用时向 LLM 注入完整的项目上下文（世界观、角色、大纲、章节），使 LLM 能够参考已有内容保持生成一致性。

## Requirements

### Requirement: Project Context Loading
Orchestrator Agent MUST load existing project data (world settings, characters, outline, chapters) from database and inject into LLM context.

#### Scenario: Load project context for new project
- GIVEN a new project with no world settings, characters, outline, or chapters
- WHEN user sends a chat message
- THEN project_context should be empty lists/null
- AND LLM should receive empty context

#### Scenario: Load project context for existing project
- GIVEN a project with 2 world settings, 5 characters, 1 outline, 10 chapters
- WHEN user sends a chat message
- THEN project_context should contain all 2 world settings, all 5 characters, the outline, and all 10 chapters
- AND LLM should receive populated context

### Requirement: Context Injection via Template
Orchestrator Agent MUST use ORCHESTRATOR_USER_TEMPLATE to format and inject project context into LLM messages.

#### Scenario: Template injection
- GIVEN project_context with world settings and characters
- WHEN orchestrator_node is invoked
- THEN messages should include a user message formatted with ORCHESTRATOR_USER_TEMPLATE
- AND template should contain all project context fields

### Requirement: No Content Bloat
Orchestrator Agent MUST NOT load full markdown content into project_context to avoid token overflow.

#### Scenario: Metadata only
- GIVEN any content type (world_setting, character, outline, chapter)
- WHEN loading project_context
- THEN only metadata fields (id, name, summary, etc.) should be loaded
- AND full content field should NOT be loaded

### Requirement: ContentService Query Methods
ContentService MUST provide methods to query all project data without requiring query parameters.

#### Scenario: get_all_world_settings
- GIVEN a project_id
- WHEN called
- THEN return all world settings for that project as list of dicts
- AND each dict should contain id, project_id, name, summary, created_at, updated_at

#### Scenario: get_all_characters
- GIVEN a project_id
- WHEN called
- THEN return all characters for that project as list of dicts
- AND each dict should contain id, project_id, world_setting_id, name, summary

#### Scenario: get_root_outline
- GIVEN a project_id
- WHEN called
- THEN return the root outline (parent_id IS NULL) for that project
- AND return None if no root outline exists

#### Scenario: get_all_chapters
- GIVEN a project_id
- WHEN called
- THEN return all chapters for that project as list of dicts
- AND each dict should contain id, project_id, outline_id, title, word_count, status

## Invariants

1. **Project Isolation Preserved**: All queries MUST include project_id filter
2. **Context Never Empty for Existing Projects**: If project has data, context reflects actual state
3. **Token Budget**: Context data should be ~1500 tokens max for typical project
4. **Backward Compatible**: If no data exists, behavior matches current (empty context)
