"""Pre-architecture adapter for LangGraph + MultiAgent mode-1 realtime evaluation.

This script demonstrates how to:
1) start a realtime session in Eval Hub
2) stream LangGraph node updates
3) push each update to /mode-realtime/sessions/{session_id}/events
4) stop execution when Eval Hub returns should_stop=True

Requirements:
- pip install langgraph requests
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

try:
    from langgraph.graph import MessagesState, StateGraph
except Exception as exc:  # pragma: no cover - demo import guard
    raise RuntimeError("Please install langgraph before running this example.") from exc

EVAL_BASE_URL = "http://localhost:8000/api/v1"


def agent_writer(state: MessagesState) -> dict[str, Any]:
    return {"messages": ["writer-agent generated chapter draft."]}


def agent_critic(state: MessagesState) -> dict[str, Any]:
    return {"messages": ["critic-agent reviewed and suggested style edits."]}


def supervisor(state: MessagesState) -> str:
    # Replace with your own routing logic.
    return "writer-agent"


def build_graph():
    builder = StateGraph(MessagesState)
    builder.add_node("supervisor", supervisor)
    builder.add_node("writer-agent", agent_writer)
    builder.add_node("critic-agent", agent_critic)

    builder.add_edge("writer-agent", "supervisor")
    builder.add_edge("critic-agent", "supervisor")
    builder.add_conditional_edges("supervisor", lambda x: x)

    return builder.compile()


def start_eval_session(session_id: str) -> None:
    payload = {
        "session_id": session_id,
        "agent_name": "langgraph-multi-agent",
        "task": "generate web novel chapter",
        "thresholds": {
            "max_tool_calls": 30,
            "max_duration_sec": 60,
            "max_same_action": 4,
            "max_steps": 120,
            "max_same_node": 6,
            "max_node_switches": 10,
        },
    }
    requests.post(f"{EVAL_BASE_URL}/mode-realtime/sessions/start", json=payload, timeout=5).raise_for_status()


def send_realtime_event(session_id: str, step: int, node: str, message: str) -> dict[str, Any]:
    payload = {
        "event_type": "node_execution",
        "node": node,
        "agent_type": "supervisor" if node == "supervisor" else "worker",
        "step": step,
        "thought": "",
        "message": message,
        "next_agent": "",
        "tool_calls": [],
        "state": {},
        "duration_sec": 0.2,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "langgraph-stream",
    }
    resp = requests.post(
        f"{EVAL_BASE_URL}/mode-realtime/sessions/{session_id}/events",
        json=payload,
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()


def end_eval_session(session_id: str) -> None:
    requests.post(f"{EVAL_BASE_URL}/mode-realtime/sessions/{session_id}/end", timeout=5).raise_for_status()


def run_with_stream(prompt: str, session_id: str) -> None:
    graph = build_graph()
    start_eval_session(session_id)

    config = {"configurable": {"thread_id": session_id}}

    try:
        step_no = 0
        for update in graph.stream({"messages": [prompt]}, config=config, stream_mode="updates"):
            if not update:
                continue
            node_name = list(update.keys())[0]
            node_data = list(update.values())[0]
            step_no += 1

            messages = node_data.get("messages", []) if isinstance(node_data, dict) else []
            last_message = str(messages[-1]) if messages else ""

            decision = send_realtime_event(
                session_id=session_id,
                step=step_no,
                node=node_name,
                message=last_message,
            )

            if decision.get("should_stop"):
                print(f"[EvalHub] stop requested: {decision.get('decision')} {decision.get('reason', '')}")
                break
    finally:
        end_eval_session(session_id)


if __name__ == "__main__":
    run_with_stream(prompt="Write chapter 3 in a xianxia tone.", session_id="langgraph-demo-001")
