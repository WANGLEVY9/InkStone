# Orchestrator Agent Spec

## ADDED Requirements

### Requirement: Intent Recognition
Orchestrator Agent MUST classify user intent from messages and route to appropriate tools.

#### Scenario: Intent classification - create world
- GIVEN a user message "create a fantasy world with magic"
- WHEN sent to orchestrator
- THEN route to create_world_setting tool

#### Scenario: Intent classification - create character
- GIVEN a user message "add a hero named Arthas"
- WHEN sent to orchestrator
- THEN route to create_character tool

#### Scenario: Intent classification - general chat
- GIVEN a user message "hello, how are you"
- WHEN sent to orchestrator
- THEN respond directly without tool invocation

### Requirement: Dynamic Tool Dispatching
Orchestrator Agent MUST dynamically invoke sub-agent tools based on classified intent.

#### Scenario: Tool dispatching
- GIVEN an intent classification result
- WHEN intent is "create_outline"
- THEN invoke create_outline tool with user input

### Requirement: Project Isolation
Orchestrator Agent MUST bind all operations to project_id from session, preventing cross-project access.

#### Scenario: Project isolation enforced
- GIVEN session belongs to project-a
- WHEN accessing /projects/project-b/sessions/xxx/chat/stream
- THEN return 403 Forbidden

### Requirement: Streaming Output
Orchestrator Agent MUST stream LLM output via SSE with token-by-token delivery.

#### Scenario: Streaming tokens
- GIVEN a valid chat request
- WHEN LLM generates response
- THEN stream tokens via SSE as they are generated

### Requirement: Session Persistence
Orchestrator Agent MUST persist chat history to SQLite and support session recovery.

#### Scenario: Session recovery
- GIVEN an existing session_id
- WHEN user sends a new message
- THEN load previous chat history from SQLite
