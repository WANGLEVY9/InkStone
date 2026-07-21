# LangGraph 流式与 HITL 重构计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构 LangGraph 流式处理，添加 HITL（Human-in-the-Loop）支持，优化工具流式输出

**Architecture:**
- 使用 LangGraph 官方 `stream_mode=["messages", "updates"]` + `version="v2"` 替代废弃的 `astream_events`
- 工具使用 `get_stream_writer()` 实现流式输出
- 通过 `interrupt()` 实现人工审批节点，使用 `Command(resume=...)` 恢复执行
- Checkpointer 持久化确保中断后可恢复

**Tech Stack:** LangGraph, FastAPI, SSE, SQLite/AIOSQLite

---

## 文件结构

```
backend/app/core/graph/
├── streaming.py          # 重写：基于 astream + stream_mode 的新流式实现
├── builder.py            # 修改：添加 interrupt 节点，配置 checkpointer
└── state.py              # 修改：添加 interrupt 相关状态字段

backend/app/core/agent/
└── tool_factory.py       # 重写：async 工具，LLM 流式调用，interrupt 支持

backend/app/api/v1/
└── chat.py               # 修改：适配新流式 API，添加 interrupt resume 端点

backend/app/db/
└── checkpointer.py       # 可能需要：确保 SqliteSaver checkpointer 正确配置
```

---

## Task 1: 重写 streaming.py - 基于 astream 的新流式实现

**Files:**
- Modify: `backend/app/core/graph/streaming.py`

**Current (deprecated):**
```python
async for event in graph.astream_events(initial_state, version="v1"):
    # on_chat_model_stream, on_tool_start, on_tool_end, on_chain_end
```

**Target (LangGraph v2):**
```python
async for chunk in graph.astream(initial_state, stream_mode=["messages", "updates"], version="v2"):
    # messages: (AIMessageChunk, metadata)
    # updates: {"node_name": state_diff}
```

- [ ] **Step 1: 编写测试用例**

```python
# tests/test_streaming.py
import pytest
from app.core.graph.streaming import stream_response

@pytest.mark.asyncio
async def test_stream_response_messages_and_updates():
    """验证 stream_mode=["messages", "updates"] 正确处理"""
    # 测试代码...
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd backend && uv run pytest tests/test_streaming.py::test_stream_response_messages_and_updates -v`
Expected: FAIL - stream_response 尚未实现

- [ ] **Step 3: 重写 stream_response 函数**

```python
async def stream_response(graph: Any, initial_state: OrchestratorState) -> AsyncGenerator[str]:
    """Stream SSE events using LangGraph v2 stream_mode.

    使用 stream_mode=["messages", "updates"] 替代废弃的 astream_events。
    - messages: 流式 LLM token
    - updates: 节点状态更新，用于检测 __interrupt__
    """
    async for chunk in graph.astream(
        initial_state,
        stream_mode=["messages", "updates"],
        version="v2",
        config={"configurable": {"thread_id": initial_state.get("session_id", "")}},
    ):
        if chunk.get("type") == "messages":
            msg, metadata = chunk["data"]
            if hasattr(msg, "content") and msg.content:
                yield f"event: token\ndata: {json.dumps({'token': msg.content})}\n\n"
        elif chunk.get("type") == "updates":
            data = chunk["data"]
            if "__interrupt__" in data:
                interrupt_info = data["__interrupt__"][0].value
                yield f"event: interrupt\ndata: {json.dumps(interrupt_info)}\n\n"
            else:
                node_name = list(data.keys())[0] if data else "unknown"
                yield f"event: node_update\ndata: {json.dumps({'node': node_name})}\n\n"
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd backend && uv run pytest tests/test_streaming.py::test_stream_response_messages_and_updates -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/app/core/graph/streaming.py tests/test_streaming.py
git commit -m "refactor: 重写 streaming.py 使用 LangGraph v2 stream_mode"
```

---

## Task 2: 修改 tool_factory.py - async 工具与流式 LLM

**Files:**
- Modify: `backend/app/core/agent/tool_factory.py`

**问题:** 当前工具使用 `asyncio.run()` 阻塞事件循环，且 LLM 调用不流式

- [ ] **Step 1: 编写测试**

```python
# tests/test_tools_async.py
@pytest.mark.asyncio
async def test_world_tools_async():
    """验证工具支持 async 调用"""
    from app.core.agent.tool_factory import create_world_tools
    tools = create_world_tools("test-project")
    # 测试...
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd backend && uv run pytest tests/test_tools_async.py -v`
Expected: FAIL

- [ ] **Step 3: 将工具改为 async 函数**

示例 - `create_world_setting` 工具改造：

```python
async def _create_world_setting_impl(
    name: str,
    genre: str = "fantasy",
    requirements: str = "",
    project_id: str = "",  # 通过闭包绑定
) -> str:
    """异步实现，支持流式 LLM 调用"""
    from app.core.prompts.tools.world import WORLD_SETTING_SYSTEM, WORLD_SETTING_USER_TEMPLATE
    from app.services.llm import create_llm_client

    user_prompt = WORLD_SETTING_USER_TEMPLATE.format(
        genre=genre, name=name, requirements=requirements,
    )

    # 使用流式 LLM
    llm = create_llm_client(streaming=True)
    messages = [
        {"role": "system", "content": WORLD_SETTING_SYSTEM},
        {"role": "user", "content": user_prompt},
    ]

    content_chunks = []
    async for chunk in llm.astream(messages):
        content = chunk.content if hasattr(chunk, "content") else str(chunk)
        if content:
            content_chunks.append(content)
            # 可选：使用 get_stream_writer() 实时推送
    content = "".join(content_chunks)
    # ... 后续保存逻辑
```

- [ ] **Step 4: 添加 interrupt 支持（可选，用于需要人工审批的操作）**

```python
from langgraph.types import interrupt, Command

def approve_content(content: str, content_type: str) -> str:
    """人工审批节点 - 用于敏感操作如发送邮件、发布内容"""
    interrupt({
        "action": "approve_content",
        "content": content,
        "content_type": content_type,
        "message": f"请审批 {content_type} 内容",
    })
```

- [ ] **Step 5: 运行测试验证**

Run: `cd backend && uv run pytest tests/test_tools_async.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add backend/app/core/agent/tool_factory.py
git commit -m "refactor: tool_factory 支持 async 和流式 LLM"
```

---

## Task 3: 修改 builder.py - 添加 interrupt 节点和 CheckpointSaver

**Files:**
- Modify: `backend/app/core/graph/builder.py`

- [ ] **Step 1: 添加审批节点示例**

```python
from langgraph.types import interrupt, Command

def approval_node(state: OrchestratorState):
    """人工审批节点 - 暂停等待用户响应"""
    approval_request = interrupt({
        "action": "human_approval",
        "message": "是否继续执行？",
    })
    return {}
```

- [ ] **Step 2: 在图中插入 interrupt 节点（用于需要人工确认的关键步骤）**

```python
# 在 write_chapter 之类的高风险操作前添加审批点
workflow = create_supervisor(
    [...],
)
# 可选：添加人工审批边
# workflow.add_edge("agent", "approval_node")
# workflow.add_edge("approval_node", END)
```

- [ ] **Step 3: 确保 checkpointer 配置正确**

```python
checkpointer = await get_checkpointer()
graph = create_orchestrator_graph(project_id, checkpointer=checkpointer)
```

- [ ] **Step 4: 测试 interrupt 和 resume**

```python
# tests/test_hitl.py
@pytest.mark.asyncio
async def test_interrupt_and_resume():
    """测试 interrupt 暂停和 Command(resume=...) 恢复"""
    graph = create_orchestrator_graph("test-project", checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "test-thread"}}

    # 触发 interrupt
    initial_state = {...}
    async for chunk in graph.astream(initial_state, stream_mode=["messages", "updates"]):
        if chunk.get("type") == "updates" and "__interrupt__" in chunk.get("data", {}):
            break

    # 使用 Command resume 恢复
    resumed = graph.invoke(Command(resume={"approved": True}), config)
```

- [ ] **Step 5: 提交**

```bash
git add backend/app/core/graph/builder.py tests/test_hitl.py
git commit -m "feat: 添加 HITL interrupt 支持"
```

---

## Task 4: 修改 chat.py - 适配新流式 API，添加 resume 端点

**Files:**
- Modify: `backend/app/api/v1/chat.py`

- [ ] **Step 1: 添加 interrupt resume 端点**

```python
@router.post("/{session_id}/chat/resume")
async def chat_resume_endpoint(
    project_id: str,
    session_id: str,
    resume_data: dict[str, Any],  # 用户的审批决定
) -> StreamingResponse:
    """从 interrupt 恢复执行"""
    checkpointer = await get_checkpointer()
    graph = create_orchestrator_graph(project_id, checkpointer=checkpointer)
    config = {"configurable": {"thread_id": session_id}}

    from langgraph.types import Command
    resume_command = Command(resume=resume_data)

    async def stream_resume():
        async for chunk in graph.astream(
            resume_command,
            stream_mode=["messages", "updates"],
            version="v2",
            config=config,
        ):
            # 处理 chunk...
            yield f"event: token\ndata: {...}\n\n"

    return StreamingResponse(stream_resume(), media_type="text/event-stream")
```

- [ ] **Step 2: 修改 chat_stream_endpoint 使用新流式 API**

将 `graph.astream_events` 替换为 `graph.astream` + `stream_mode=["messages", "updates"]`

- [ ] **Step 3: 测试**

Run: `cd backend && uv run pytest tests/test_e2e_chat.py -v`

- [ ] **Step 4: 提交**

```bash
git add backend/app/api/v1/chat.py
git commit -m "feat: 添加 chat resume 端点，适配新流式 API"
```

---

## Task 5: 更新 state.py - 添加 interrupt 相关状态

**Files:**
- Modify: `backend/app/core/graph/state.py`

- [ ] **Step 1: 添加 pending_approval 字段**

```python
class OrchestratorState(TypedDict):
    # ... existing fields ...
    pending_approval: dict[str, Any] | None  # 当前等待审批的请求
    approved_actions: list[dict[str, Any]]   # 已审批的操作记录
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/core/graph/state.py
git commit -m "refactor: state.py 添加 HITL 相关字段"
```

---

## 验证检查清单

- [ ] `astream_events` 已废弃，替换为 `astream` + `stream_mode=["messages", "updates"]`
- [ ] `version="v2"` 已使用
- [ ] 工具支持 async 和流式 LLM 调用
- [ ] `interrupt()` 可暂停工作流并等待用户响应
- [ ] `Command(resume=...)` 可恢复中断的工作流
- [ ] Checkpointer 正确配置，中断后可恢复
- [ ] 新流式端点正确发送 SSE 事件：`token`, `interrupt`, `node_update`, `error`
- [ ] 所有测试通过

---

## 执行选项

**1. Subagent-Driven (recommended)** - 每个 Task 由独立的 subagent 执行，任务间有检查点

**2. Inline Execution** - 在当前 session 中使用 executing-plans 批量执行，有检查点

**Which approach?**
