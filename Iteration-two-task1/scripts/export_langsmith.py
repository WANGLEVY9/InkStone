"""Export LangSmith runs to DSL-compliant JSON for evaluation platform.

Usage:
    # Export 5 most recent orchestrator runs (default)
    python scripts/export_langsmith.py

    # Export 10 most recent runs
    python scripts/export_langsmith.py --limit 10

    # Export to custom output directory
    python scripts/export_langsmith.py --output ./eval_data

    # Export a specific run by ID
    python scripts/export_langsmith.py --run-id 019e08bf-7d8f-7b73-88eb-db7758234d8d

Environment:
    LANGSMITH_API_KEY must be set (in .env or environment).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Load .env if available
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from langsmith import Client


# ---------------------------------------------------------------------------
# DSL mapping helpers
# ---------------------------------------------------------------------------

def _build_turns_from_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group flat messages into conversation turns.

    Each turn = one human message + all subsequent AI/tool messages
    until the next human message.
    """
    turns: list[dict[str, Any]] = []
    current_turn: dict[str, Any] | None = None

    for msg in messages:
        msg_type = msg.get("type", "")

        if msg_type == "human":
            # Start a new turn
            if current_turn is not None:
                turns.append(current_turn)
            current_turn = {
                "user_input": msg.get("content", ""),
                "responses": [],
            }
        elif current_turn is not None:
            entry: dict[str, Any] = {"type": msg_type}

            if msg_type == "ai":
                entry["role"] = "assistant"
                entry["name"] = msg.get("name", "orchestrator")
                # Extract text and thinking from content blocks
                content = msg.get("content", "")
                if isinstance(content, list):
                    texts = []
                    thinking = None
                    for block in content:
                        if not isinstance(block, dict):
                            continue
                        if block.get("type") == "text":
                            texts.append(block.get("text", ""))
                        elif block.get("type") == "thinking":
                            thinking = block.get("thinking", "")
                        elif block.get("type") == "tool_use":
                            entry.setdefault("tool_calls", []).append({
                                "id": block.get("id", ""),
                                "name": block.get("name", ""),
                                "input": block.get("input", {}),
                            })
                    entry["content"] = "".join(texts)
                    if thinking:
                        entry["thinking"] = thinking
                else:
                    entry["content"] = str(content)

                # Token usage per AI message
                usage = msg.get("usage_metadata")
                if usage:
                    entry["tokens"] = {
                        "input": usage.get("input_tokens", 0),
                        "output": usage.get("output_tokens", 0),
                        "total": usage.get("total_tokens", 0),
                    }
                # Model info
                rm = msg.get("response_metadata", {})
                if rm:
                    entry["model"] = rm.get("model_name")
                    entry["stop_reason"] = rm.get("stop_reason")

            elif msg_type == "tool":
                entry["role"] = "tool"
                entry["tool_call_id"] = msg.get("tool_call_id", "")
                entry["name"] = msg.get("name", "")
                entry["content"] = msg.get("content", "")

            current_turn["responses"].append(entry)

    if current_turn is not None:
        turns.append(current_turn)

    return turns


def _build_tool_calls_from_children(child_runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract tool call info from child runs with run_type='tool'."""
    tool_calls = []
    for child in child_runs:
        if child.get("run_type") != "tool":
            continue
        tc: dict[str, Any] = {
            "name": child.get("name", ""),
            "latency_ms": round((child.get("latency_s") or 0) * 1000, 1),
            "success": child.get("status") == "success",
        }
        if child.get("error"):
            tc["error"] = child["error"]
        tool_calls.append(tc)
    return tool_calls


def _build_trace_steps(child_runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build trace steps from child run hierarchy.

    Groups child runs into logical steps: each LLM call or tool invocation
    is one step, ordered chronologically.
    """
    steps = []
    for i, child in enumerate(child_runs):
        step: dict[str, Any] = {
            "step_index": i + 1,
            "step_name": child.get("name", ""),
            "step_type": child.get("run_type", ""),
            "latency_ms": round((child.get("latency_s") or 0) * 1000, 1),
            "success": child.get("status") == "success",
        }
        if child.get("total_tokens"):
            step["token_usage"] = child["total_tokens"]
        if child.get("model_name"):
            step["model"] = child["model_name"]
        if child.get("error"):
            step["error"] = child["error"]
        steps.append(step)
    return steps


def _to_dsl_sample(run_data: dict[str, Any]) -> dict[str, Any]:
    """Convert a LangSmith run export to DSL SampleOutput format.

    Maps to multi_turn_conversation mode per the DSL spec.
    """
    outputs = run_data.get("outputs") or {}
    messages = outputs.get("messages", [])
    child_runs = run_data.get("child_runs", [])

    # Build turns
    turns = _build_turns_from_messages(messages)

    # Compute total latency in ms
    latency_s = run_data.get("latency_s") or 0
    response_time_ms = round(latency_s * 1000, 1)

    # Token totals
    input_tokens = run_data.get("input_tokens") or 0
    output_tokens = run_data.get("output_tokens") or 0

    # Success status
    success = run_data.get("status") == "success"

    sample: dict[str, Any] = {
        "sample_id": run_data.get("run_id", ""),
        "input": {
            "mode": "multi_turn_conversation",
            "turns": [{"user_input": t["user_input"]} for t in turns],
            "session_id": run_data.get("metadata", {}).get("thread_id", ""),
            "project_id": (run_data.get("inputs", {}).get("project_id")),
        },
        "output": {
            "turns": turns,
            "full_response": _extract_full_text(messages),
        },
        "runtime": {
            "response_time_ms": response_time_ms,
            "tokens_input": input_tokens,
            "tokens_output": output_tokens,
            "success": success,
        },
        "tools": {
            "tool_calls": _build_tool_calls_from_children(child_runs),
            "tool_summary": {
                "total_calls": len([c for c in child_runs if c.get("run_type") == "tool"]),
                "successful_calls": len([c for c in child_runs if c.get("run_type") == "tool" and c.get("status") == "success"]),
            },
        },
        "trace": {
            "steps": _build_trace_steps(child_runs),
        },
        "metadata": {
            "model": _extract_model_name(child_runs),
            "start_time": run_data.get("start_time"),
            "end_time": run_data.get("end_time"),
            "first_token_time": run_data.get("first_token_time"),
            "child_run_count": run_data.get("child_run_count", 0),
            "langsmith_trace_id": run_data.get("langsmith", {}).get("trace_id"),
            "langsmith_url": run_data.get("langsmith", {}).get("url"),
        },
    }

    # Add error info if failed
    if not success:
        sample["runtime"]["error"] = run_data.get("metadata", {}).get("error", "unknown error")

    return sample


def _extract_full_text(messages: list[dict[str, Any]]) -> str:
    """Extract the final assistant text response from messages."""
    for msg in reversed(messages):
        if msg.get("type") != "ai":
            continue
        content = msg.get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
            text = "".join(parts)
            if text.strip():
                return text
    return ""


def _extract_model_name(child_runs: list[dict[str, Any]]) -> str | None:
    """Get the model name from the first LLM child run."""
    for child in child_runs:
        if child.get("model_name"):
            return child["model_name"]
    return None


# ---------------------------------------------------------------------------
# LangSmith fetcher
# ---------------------------------------------------------------------------

def _run_to_child_data(run: Any) -> dict[str, Any]:
    """Convert a LangSmith Run object to a child run dict."""
    # Compute latency from start/end time if direct field not available
    latency_s = getattr(run, "latency", None)
    if latency_s is None and run.start_time and run.end_time:
        latency_s = (run.end_time - run.start_time).total_seconds()

    # Token fields: prefer input_tokens/output_tokens, fallback to prompt/completion
    input_tokens = getattr(run, "input_tokens", None) or getattr(run, "prompt_tokens", 0) or 0
    output_tokens = getattr(run, "output_tokens", None) or getattr(run, "completion_tokens", 0) or 0

    child_data: dict[str, Any] = {
        "id": str(run.id),
        "name": run.name,
        "run_type": run.run_type,
        "parent_run_id": str(run.parent_run_id) if run.parent_run_id else None,
        "start_time": run.start_time.isoformat() if run.start_time else None,
        "end_time": run.end_time.isoformat() if run.end_time else None,
        "latency_s": latency_s,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": run.total_tokens or (input_tokens + output_tokens),
        "status": run.status,
        "error": run.error,
    }
    if run.run_type == "llm" and run.outputs:
        # LangSmith LLM runs store data in generations[0][0].message.kwargs
        gens = run.outputs.get("generations", [])
        if gens and gens[0]:
            gen = gens[0][0] if isinstance(gens[0], list) else gens[0]
            msg = gen.get("message", {})
            kwargs = msg.get("kwargs", {}) if isinstance(msg, dict) else {}
            rm = kwargs.get("response_metadata", {})
            if rm:
                child_data["model_name"] = rm.get("model_name")
                child_data["model_provider"] = rm.get("model_provider")
                child_data["stop_reason"] = rm.get("stop_reason")
            um = kwargs.get("usage_metadata", {})
            if um:
                child_data["input_tokens"] = um.get("input_tokens", input_tokens)
                child_data["output_tokens"] = um.get("output_tokens", output_tokens)
                child_data["total_tokens"] = um.get("total_tokens", child_data["total_tokens"])
        # Also check extra.invocation_params for model name
        if not child_data.get("model_name") and run.extra:
            inv = run.extra.get("invocation_params", {})
            child_data["model_name"] = inv.get("model")
    return child_data


def fetch_run_full(client: Client, run_id: str) -> dict[str, Any]:
    """Fetch a run with all child runs and timing data.

    Uses list_runs(trace_id=...) for efficient batch fetching
    instead of individual read_run calls per child.
    """
    run = client.read_run(run_id)
    trace_id = str(run.trace_id)

    # Batch-fetch all runs in this trace (single API call)
    # select outputs to get model_name from LLM response_metadata
    all_runs = list(client.list_runs(
        trace_id=trace_id,
        select=["name", "run_type", "start_time", "end_time",
                "total_tokens", "prompt_tokens", "completion_tokens",
                "status", "error", "parent_run_id", "outputs",
                "first_token_time"],
    ))

    # Build child_runs list (exclude the root run itself)
    child_runs = []
    for r in all_runs:
        if str(r.id) == run_id:
            continue
        child_runs.append(_run_to_child_data(r))

    # Sort child runs by start_time for chronological order
    child_runs.sort(key=lambda x: x.get("start_time") or "")

    return {
        "run_id": str(run.id),
        "run_name": run.name,
        "status": run.status,
        "run_type": run.run_type,
        "start_time": run.start_time.isoformat() if run.start_time else None,
        "end_time": run.end_time.isoformat() if run.end_time else None,
        "latency_s": run.latency,
        "first_token_time": run.first_token_time.isoformat() if run.first_token_time else None,
        "input_tokens": run.input_tokens,
        "output_tokens": run.output_tokens,
        "total_tokens": run.total_tokens,
        "prompt_tokens": run.prompt_tokens,
        "completion_tokens": run.completion_tokens,
        "inputs": run.inputs,
        "outputs": run.outputs,
        "metadata": run.metadata,
        "child_runs": child_runs,
        "child_run_count": len(child_runs),
        "langsmith": {
            "trace_id": trace_id,
            "session_id": str(run.session_id),
            "url": run.url,
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Export LangSmith runs to DSL-compliant JSON")
    parser.add_argument("--limit", type=int, default=5, help="Number of recent runs to export (default: 5)")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output directory (default: scripts/../eval_exports)")
    parser.add_argument("--run-id", type=str, default=None, help="Export a specific run by ID")
    parser.add_argument("--project", type=str, default="default", help="LangSmith project name (default: default)")
    parser.add_argument("--no-raw", action="store_true", help="Skip saving raw LangSmith data")
    args = parser.parse_args()

    api_key = os.environ.get("LANGSMITH_API_KEY")
    if not api_key:
        print("Error: LANGSMITH_API_KEY not set. Add it to backend/.env or set as environment variable.")
        sys.exit(1)

    client = Client()
    output_dir = Path(args.output) if args.output else Path(__file__).resolve().parent.parent / "eval_exports"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.run_id:
        run_ids = [args.run_id]
    else:
        runs = list(client.list_runs(
            project_name=args.project,
            is_root=True,
            filter='eq(name, "orchestrator")',
            limit=args.limit,
        ))
        run_ids = [str(r.id) for r in runs]
        print(f"Found {len(run_ids)} orchestrator runs in project '{args.project}'")

    for run_id in run_ids:
        print(f"  Exporting {run_id}...")

        # Fetch full data with child runs
        run_data = fetch_run_full(client, run_id)

        # Save raw data (default, skip with --no-raw)
        if not args.no_raw:
            raw_path = output_dir / f"raw-{run_id}.json"
            with open(raw_path, "w", encoding="utf-8") as f:
                json.dump(run_data, f, ensure_ascii=False, indent=2, default=str)

        # Convert to DSL format and save
        dsl_sample = _to_dsl_sample(run_data)
        dsl_path = output_dir / f"dsl-{run_id}.json"
        with open(dsl_path, "w", encoding="utf-8") as f:
            json.dump(dsl_sample, f, ensure_ascii=False, indent=2, default=str)

        status = run_data.get("status", "?")
        latency = run_data.get("latency_s", 0)
        tokens = run_data.get("total_tokens", 0)
        turns = len(dsl_sample.get("output", {}).get("turns", []))
        print(f"    status={status}, latency={latency:.1f}s, tokens={tokens}, turns={turns}")
        print(f"    -> {dsl_path}")

    print(f"\nExported {len(run_ids)} run(s) to {output_dir}")


if __name__ == "__main__":
    main()
