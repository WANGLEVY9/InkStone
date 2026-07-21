# lc_agent_name Streaming Attribution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace fragile `tags`/`langgraph_node` source attribution with LangChain's first-class `lc_agent_name` metadata field in the SSE streaming pipeline.

**Architecture:** Add `name` parameter to all `create_agent()` calls so LangChain attaches `lc_agent_name` to streaming metadata. Replace the two-dictionary fallback lookup in `chat.py` with a single `metadata.get("lc_agent_name", "orchestrator")` call. Delete the now-unused `TAG_TO_SOURCE` and `NODE_TO_SOURCE` dictionaries.

**Tech Stack:** Python 3.13, LangChain (`create_agent`), FastAPI SSE streaming

---

### Task 1: Update sub-agent factories with `name` parameter

**Files:**
- Modify: `backend/app/core/agent/langchain_subagents.py:168-173,188-193,208-213,228-233,248-253`

- [ ] **Step 1: Add `name` and remove `tags` in `create_world_builder_agent`**

In `backend/app/core/agent/langchain_subagents.py`, change lines 168-173:

```python
    return create_agent(
        model=create_llm_client(streaming=True),
        tools=[*tools, *skill_middleware.tools],
        system_prompt=WORLD_BUILDER_SYSTEM_PROMPT,
        name="world_builder",
        middleware=[skill_middleware],
    )
```

- [ ] **Step 2: Add `name` and remove `tags` in `create_character_agent`**

Change lines 188-193:

```python
    return create_agent(
        model=create_llm_client(streaming=True),
        tools=[*tools, *skill_middleware.tools],
        system_prompt=CHARACTER_SYSTEM_PROMPT,
        name="character",
        middleware=[skill_middleware],
    )
```

- [ ] **Step 3: Add `name` and remove `tags` in `create_plot_agent`**

Change lines 208-213:

```python
    return create_agent(
        model=create_llm_client(streaming=True),
        tools=[*tools, *skill_middleware.tools],
        system_prompt=PLOT_SYSTEM_PROMPT,
        name="plot",
        middleware=[skill_middleware],
    )
```

- [ ] **Step 4: Add `name` and remove `tags` in `create_chapter_agent`**

Change lines 228-233:

```python
    return create_agent(
        model=create_llm_client(streaming=True),
        tools=[*tools, *skill_middleware.tools],
        system_prompt=CHAPTER_SYSTEM_PROMPT,
        name="chapter",
        middleware=[skill_middleware],
    )
```

- [ ] **Step 5: Add `name` and remove `tags` in `create_review_agent`**

Change lines 248-253:

```python
    return create_agent(
        model=create_llm_client(streaming=True),
        tools=[*tools, *skill_middleware.tools],
        system_prompt=REVIEW_SYSTEM_PROMPT,
        name="review",
        middleware=[skill_middleware],
    )
```

- [ ] **Step 6: Run lint and type check**

Run: `cd backend && uv run ruff check app/core/agent/langchain_subagents.py && uv run mypy app/core/agent/langchain_subagents.py`
Expected: No errors

- [ ] **Step 7: Commit**

```bash
git add backend/app/core/agent/langchain_subagents.py
git commit -m "feat(agent): add name param to sub-agent create_agent calls

Replaces tags-based streaming attribution with lc_agent_name.
Each sub-agent now carries its name in streaming metadata."
```

---

### Task 2: Update orchestrator with `name` parameter

**Files:**
- Modify: `backend/app/core/graph/builder.py:46,114-129`

- [ ] **Step 1: Fix docstring and add `name` to orchestrator `create_agent`**

In `backend/app/core/graph/builder.py`:

Fix docstring on line 46 — change `streaming=False` to `streaming=True`:

```python
        model: Optional LLM model. If not provided, creates one via
            ``create_llm_client`` with ``streaming=True``.
```

Add `name="orchestrator"` to the `create_agent` call at line 114:

```python
    return create_agent(
        model=llm,
        tools=[
            delegate_to_world_builder,
            delegate_to_character,
            delegate_to_plot,
            delegate_to_chapter,
            delegate_to_review,
            *read_tools,
            *skill_tools,
            *skill_middleware.tools,
        ],
        system_prompt=ORCHESTRATOR_SYSTEM,
        name="orchestrator",
        checkpointer=checkpointer,
        middleware=[skill_middleware],
    )
```

- [ ] **Step 2: Run lint and type check**

Run: `cd backend && uv run ruff check app/core/graph/builder.py && uv run mypy app/core/graph/builder.py`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add backend/app/core/graph/builder.py
git commit -m "feat(graph): add name='orchestrator' to create_agent call

Enables lc_agent_name in streaming metadata for orchestrator tokens.
Also fixes docstring: streaming=True, not False."
```

---

### Task 3: Replace attribution logic in chat.py

**Files:**
- Modify: `backend/app/api/v1/chat.py:38-55,268-274`

- [ ] **Step 1: Delete `NODE_TO_SOURCE` and `TAG_TO_SOURCE` dictionaries**

In `backend/app/api/v1/chat.py`, delete lines 38-55 (the two dictionaries):

```python
# DELETE these lines:
# Map langgraph_node names to human-readable source identifiers
NODE_TO_SOURCE: dict[str, str] = {
    "agent": "orchestrator",
    "delegate_to_world_builder": "world_builder",
    "delegate_to_character": "character",
    "delegate_to_plot": "plot",
    "delegate_to_chapter": "chapter",
    "delegate_to_review": "review",
}

# Map LLM tags to source identifiers (used when sub-agents are @tool wrappers)
TAG_TO_SOURCE: dict[str, str] = {
    "world_builder": "world_builder",
    "character": "character",
    "plot": "plot",
    "chapter": "chapter",
    "review": "review",
}
```

- [ ] **Step 2: Replace attribution logic in streaming loop**

Replace the 7-line attribution block (lines 268-274) with a single line:

```python
                    source = metadata.get("lc_agent_name", "orchestrator")
```

The surrounding context should look like:

```python
                if chunk_type == "messages":
                    token, metadata = chunk_data
                    source = metadata.get("lc_agent_name", "orchestrator")
```

- [ ] **Step 3: Run lint and type check**

Run: `cd backend && uv run ruff check app/api/v1/chat.py && uv run mypy app/api/v1/chat.py`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/chat.py
git commit -m "feat(chat): use lc_agent_name for streaming source attribution

Replace fragile TAG_TO_SOURCE/NODE_TO_SOURCE dictionaries with
LangChain's first-class lc_agent_name metadata field.
Single-line attribution: metadata.get('lc_agent_name', 'orchestrator')"
```

---

### Task 4: Update tests

**Files:**
- Modify: `backend/tests/test_v2_streaming.py`

- [ ] **Step 1: Rewrite `TestNodeToSourceMapping` to test `lc_agent_name` attribution**

Replace the entire `TestNodeToSourceMapping` class with a test that verifies `lc_agent_name`-based attribution:

```python
class TestLcAgentNameAttribution:
    """Test lc_agent_name metadata-based source attribution."""

    def test_metadata_with_lc_agent_name(self) -> None:
        """lc_agent_name in metadata should be used as source."""
        metadata: dict[str, Any] = {"lc_agent_name": "world_builder"}
        source = metadata.get("lc_agent_name", "orchestrator")
        assert source == "world_builder"

    def test_metadata_without_lc_agent_name_defaults_to_orchestrator(self) -> None:
        """Missing lc_agent_name should fall back to orchestrator."""
        metadata: dict[str, Any] = {}
        source = metadata.get("lc_agent_name", "orchestrator")
        assert source == "orchestrator"

    def test_orchestrator_metadata(self) -> None:
        """Orchestrator agent should have lc_agent_name='orchestrator'."""
        metadata: dict[str, Any] = {"lc_agent_name": "orchestrator"}
        source = metadata.get("lc_agent_name", "orchestrator")
        assert source == "orchestrator"

    def test_all_subagent_names(self) -> None:
        """Each sub-agent name should be a valid source."""
        for name in ["world_builder", "character", "plot", "chapter", "review"]:
            metadata: dict[str, Any] = {"lc_agent_name": name}
            source = metadata.get("lc_agent_name", "orchestrator")
            assert source == name
```

- [ ] **Step 2: Update `TestV2ChunkProcessing` to use `lc_agent_name`**

Replace `test_messages_chunk_with_text_content` and `test_messages_chunk_with_subagent_node`:

```python
    def test_messages_chunk_with_text_content(self) -> None:
        """Messages chunk with text should use lc_agent_name for source."""
        chunk: dict[str, Any] = {
            "type": "messages",
            "ns": (),
            "data": (
                type("Token", (), {"content": "hello", "content_blocks": []})(),
                {"lc_agent_name": "orchestrator"},
            ),
        }

        token, metadata = chunk["data"]
        source = metadata.get("lc_agent_name", "orchestrator")

        assert chunk["type"] == "messages"
        assert source == "orchestrator"
        assert token.content == "hello"

    def test_messages_chunk_with_subagent_name(self) -> None:
        """Messages chunk from sub-agent should use lc_agent_name."""
        metadata: dict[str, Any] = {"lc_agent_name": "world_builder"}
        source = metadata.get("lc_agent_name", "orchestrator")
        assert source == "world_builder"
```

- [ ] **Step 3: Run tests**

Run: `cd backend && uv run pytest tests/test_v2_streaming.py -v`
Expected: All tests pass

- [ ] **Step 4: Run full test suite**

Run: `cd backend && uv run pytest`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_v2_streaming.py
git commit -m "test: update streaming tests for lc_agent_name attribution

Replace NODE_TO_SOURCE/TAG_TO_SOURCE test references with
lc_agent_name metadata-based assertions."
```

---

### Task 5: Verify end-to-end

- [ ] **Step 1: Run full lint + type check + tests**

Run: `cd backend && uv run ruff check app tests && uv run mypy app && uv run pytest`
Expected: All pass

- [ ] **Step 2: Verify no remaining references to old dicts**

Run: `cd backend && grep -r "TAG_TO_SOURCE\|NODE_TO_SOURCE" app/ tests/`
Expected: No matches

- [ ] **Step 3: Final commit (if needed)**

If any cleanup was needed, commit it. Otherwise this step is a no-op.
