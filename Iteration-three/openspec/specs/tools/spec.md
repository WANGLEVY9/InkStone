# tools Specification

## Purpose
TBD - created by archiving change novel-agent-backend. Update Purpose after archive.
## Requirements
### Requirement: Project Isolation for All Tools
All tools MUST obtain project_id from OrchestratorState, NOT as explicit parameters. This prevents cross-project data access.

#### Scenario: Tool signature has no project_id
- GIVEN a tool implementation
- WHEN inspecting the tool signature
- THEN project_id is NOT a parameter

#### Scenario: Project isolation - database query
- GIVEN tool execution context with project_id
- WHEN querying any data
- THEN filter by project_id from state

### Requirement: create_world_setting Tool
The system MUST create world setting content and persist to SQLite metadata + Markdown file.

#### Scenario: Create world setting
- GIVEN a valid user_input for world creation
- WHEN create_world_setting tool is invoked
- THEN persist metadata to SQLite and content to world_settings/{id}.md

### Requirement: create_character Tool
The system MUST create character with metadata in SQLite and content in Markdown file.

#### Scenario: Create character with world binding
- GIVEN user_input and optional world_setting_id
- WHEN create_character tool is invoked
- THEN create character record filtered by project_id from state

### Requirement: search_world_setting Tool
The system MUST search world settings filtered by project_id from state.

#### Scenario: Search returns only current project data
- GIVEN a search query and project_id from state
- WHEN search_world_setting tool is invoked
- THEN return only world_settings belonging to the current project

### Requirement: search_characters Tool
The system MUST search characters filtered by project_id from state.

#### Scenario: Search characters project isolation
- GIVEN a search query
- WHEN search_characters tool is invoked
- THEN return only characters from the same project_id in state

### Requirement: create_outline Tool
The system MUST create plot outlines with hierarchical structure.

#### Scenario: Create nested outline
- GIVEN user_input and optional parent_outline_id
- WHEN create_outline tool is invoked
- THEN create outline record with project_id from state

### Requirement: write_chapter Tool
The system MUST write chapter content linked to an outline.

#### Scenario: Write chapter with outline binding
- GIVEN outline_id and optional user_input
- WHEN write_chapter tool is invoked
- THEN create chapter linked to outline, filtered by project_id from state

### Requirement: review_content Tool
The system MUST review existing content for quality and consistency.

#### Scenario: Review content with project isolation
- GIVEN content_type, content_id, and review_criteria
- WHEN review_content tool is invoked
- THEN verify content belongs to project_id from state before reviewing

### Requirement: update_project Tool
The system MUST update project metadata.

#### Scenario: Update project metadata
- GIVEN a dictionary of updates
- WHEN update_project tool is invoked
- THEN update only fields for project_id from state

### Requirement: Error Handling
All tools MUST return consistent JSON with success, error, and result fields.

#### Scenario: Tool returns structured error
- GIVEN an error condition during tool execution
- WHEN tool returns
- THEN return {"success": false, "error": "...", "result": null}

