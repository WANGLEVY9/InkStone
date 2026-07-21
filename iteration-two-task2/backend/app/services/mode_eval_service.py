from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from statistics import mean
from threading import Lock
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, mongo_db
from app.core.redis_client import redis_client
from app.models.dataset import DatasetAsset
from app.models.result import EvaluationResult
from app.models.task import EvaluationTask
from app.services.dataset_parser_service import DatasetParserService

# Redis key prefixes
_RT_SESSION = "mode:realtime:session:"
_RT_EVENTS = "mode:realtime:events:"
_RT_ALERTS = "mode:realtime:alerts:"
_RT_INDEX = "mode:realtime:sessions"
_OFF_JOB = "mode:offline:job:"
_OFF_INDEX = "mode:offline:jobs"
_BAT_JOB = "mode:batch:job:"
_BAT_INDEX = "mode:batch:jobs"

# Session TTL: active sessions get 30 min, terminated get 2 hours
_TTL_ACTIVE = 1800
_TTL_TERMINATED = 7200


class ModeEvalService:
    _lock = Lock()
    _dangerous_tools = {"delete_database", "shell_exec", "exec", "system", "drop_table"}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _now() -> datetime:
        return datetime.utcnow()

    @classmethod
    def _as_dt(cls, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value))
        except Exception:
            return cls._now()

    @classmethod
    def _float(cls, value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @classmethod
    def _bool(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "ok", "success"}

    @classmethod
    def _session_key(cls, session_id: str) -> str:
        return f"{_RT_SESSION}{session_id}"

    @classmethod
    def _events_key(cls, session_id: str) -> str:
        return f"{_RT_EVENTS}{session_id}"

    @classmethod
    def _alerts_key(cls, session_id: str) -> str:
        return f"{_RT_ALERTS}{session_id}"

    @classmethod
    def _offline_key(cls, job_id: str) -> str:
        return f"{_OFF_JOB}{job_id}"

    @classmethod
    def _batch_key(cls, job_id: str) -> str:
        return f"{_BAT_JOB}{job_id}"

    @classmethod
    def _save_session(cls, session: dict[str, Any]) -> None:
        key = cls._session_key(session["session_id"])
        ttl = _TTL_TERMINATED if session["status"] != "running" else _TTL_ACTIVE
        redis_client.set_json(key, session, ex=ttl)
        redis_client.sadd(_RT_INDEX, session["session_id"])

    @classmethod
    def _load_session(cls, session_id: str) -> dict[str, Any] | None:
        return redis_client.get_json(cls._session_key(session_id))

    @classmethod
    def _refresh_session_ttl(cls, session_id: str, status: str | None = None) -> None:
        key = cls._session_key(session_id)
        if status == "running":
            redis_client.expire(key, _TTL_ACTIVE)
        else:
            redis_client.expire(key, _TTL_TERMINATED)

    # ------------------------------------------------------------------
    # Serialization helpers (unchanged signatures)
    # ------------------------------------------------------------------

    @classmethod
    def _serialize_alert(cls, alert: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": alert["id"],
            "session_id": alert["session_id"],
            "rule": alert["rule"],
            "severity": alert["severity"],
            "message": alert["message"],
            "decision": alert["decision"],
            "created_at": cls._as_dt(alert["created_at"]),
        }

    @classmethod
    def _serialize_stream_event(cls, event: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": event["id"],
            "session_id": event["session_id"],
            "event_type": event.get("event_type", "node_execution"),
            "node": event.get("node", ""),
            "agent_type": event.get("agent_type", "worker"),
            "step": int(event.get("step") or 0),
            "thought": str(event.get("thought") or ""),
            "message": str(event.get("message") or ""),
            "next_agent": str(event.get("next_agent") or ""),
            "tool_calls": list(event.get("tool_calls") or []),
            "state": dict(event.get("state") or {}),
            "duration_sec": cls._float(event.get("duration_sec"), 0.0),
            "decision": event.get("decision", "CONTINUE"),
            "reason": str(event.get("reason") or ""),
            "source": str(event.get("source") or "langgraph-stream"),
            "created_at": cls._as_dt(event.get("created_at")),
        }

    @classmethod
    def _append_stream_event(cls, session_id: str, event: dict[str, Any]) -> None:
        key = cls._events_key(session_id)
        redis_client.rpush(key, json.dumps(event, default=str))
        redis_client.ltrim(key, -500, -1)
        redis_client.expire(key, _TTL_TERMINATED)
        mongo_db["realtime_events"].insert_one(event)

    @classmethod
    def _append_alert(
        cls,
        session_id: str,
        *,
        rule: str,
        severity: str,
        message: str,
        decision: str,
    ) -> dict[str, Any]:
        alert = {
            "id": f"a_{uuid4().hex[:10]}",
            "session_id": session_id,
            "rule": rule,
            "severity": severity,
            "message": message,
            "decision": decision,
            "created_at": cls._now().isoformat(),
        }
        key = cls._alerts_key(session_id)
        redis_client.rpush(key, json.dumps(alert, default=str))
        redis_client.ltrim(key, -300, -1)
        redis_client.expire(key, _TTL_TERMINATED)
        mongo_db["realtime_alerts"].insert_one(alert)
        return alert

    @classmethod
    def _serialize_realtime_session(cls, session: dict[str, Any]) -> dict[str, Any]:
        alert_key = cls._alerts_key(session["session_id"])
        return {
            "session_id": session["session_id"],
            "status": session["status"],
            "agent_name": session["agent_name"],
            "task": session["task"],
            "started_at": cls._as_dt(session["started_at"]),
            "ended_at": cls._as_dt(session["ended_at"]) if session.get("ended_at") else None,
            "step_count": int(session["step_count"]),
            "tool_call_count": int(session["tool_call_count"]),
            "consecutive_same_action": int(session["consecutive_same_action"]),
            "node_switch_count": int(session.get("node_switch_count", 0)),
            "event_count": int(session.get("event_count", 0)),
            "current_node": session.get("current_node"),
            "current_agent_type": session.get("current_agent_type"),
            "latest_decision": session.get("latest_decision", "CONTINUE"),
            "alert_count": redis_client.llen(alert_key),
        }

    # ------------------------------------------------------------------
    # Realtime session lifecycle
    # ------------------------------------------------------------------

    @classmethod
    def start_realtime_session(cls, payload: dict[str, Any]) -> dict[str, Any]:
        with cls._lock:
            requested_id = (payload.get("session_id") or "").strip()
            session_id = requested_id or f"rt_{uuid4().hex[:12]}"
            now = cls._now().isoformat()
            threshold = payload.get("thresholds") or {}
            session = {
                "session_id": session_id,
                "status": "running",
                "agent_name": payload.get("agent_name") or "default-agent",
                "task": payload.get("task") or "",
                "started_at": now,
                "ended_at": None,
                "step_count": 0,
                "tool_call_count": 0,
                "consecutive_same_action": 0,
                "node_switch_count": 0,
                "event_count": 0,
                "current_node": None,
                "current_agent_type": None,
                "last_action": "",
                "latest_decision": "CONTINUE",
                "thresholds": {
                    "max_tool_calls": int(threshold.get("max_tool_calls", 15)),
                    "max_duration_sec": cls._float(threshold.get("max_duration_sec", 30.0), 30.0),
                    "max_same_action": int(threshold.get("max_same_action", 3)),
                    "max_steps": int(threshold.get("max_steps", 80)),
                    "max_same_node": int(threshold.get("max_same_node", 5)),
                    "max_node_switches": int(threshold.get("max_node_switches", 8)),
                },
            }
            cls._save_session(session)
            return cls._serialize_realtime_session(session)

    @classmethod
    def _get_realtime_or_raise(cls, session_id: str) -> dict[str, Any]:
        session = cls._load_session(session_id)
        if session is None:
            raise KeyError("session_not_found")
        return session

    @classmethod
    def on_step_start(cls, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        with cls._lock:
            session = cls._get_realtime_or_raise(session_id)
            session["step_count"] += 1
            action = str(payload.get("action") or "").strip()
            if action:
                if action == session.get("last_action"):
                    session["consecutive_same_action"] += 1
                else:
                    session["consecutive_same_action"] = 1
                    session["last_action"] = action

            if session["consecutive_same_action"] >= session["thresholds"]["max_same_action"]:
                session["status"] = "stopped"
                session["latest_decision"] = "STOP"
                cls._append_alert(
                    session_id,
                    rule="same_action_retry",
                    severity="warning",
                    message="连续重复动作达到阈值，疑似无效重试。",
                    decision="STOP",
                )
            cls._save_session(session)
            return cls._serialize_realtime_session(session)

    @classmethod
    def on_tool_call(cls, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        with cls._lock:
            session = cls._get_realtime_or_raise(session_id)
            tool_name = str(payload.get("tool_name") or "").strip()
            dangerous = bool(payload.get("dangerous")) or tool_name in cls._dangerous_tools

            session["tool_call_count"] += 1
            session["latest_decision"] = "CONTINUE"

            if dangerous:
                session["status"] = "blocked"
                session["latest_decision"] = "BLOCK"
                cls._append_alert(
                    session_id,
                    rule="dangerous_tool",
                    severity="critical",
                    message=f"检测到危险工具调用: {tool_name}",
                    decision="BLOCK",
                )
            elif session["tool_call_count"] > session["thresholds"]["max_tool_calls"]:
                session["status"] = "stopped"
                session["latest_decision"] = "STOP"
                cls._append_alert(
                    session_id,
                    rule="tool_call_overflow",
                    severity="warning",
                    message="工具调用次数超阈值，存在死循环风险。",
                    decision="STOP",
                )

            cls._save_session(session)
            return cls._serialize_realtime_session(session)

    @classmethod
    def on_step_end(cls, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        with cls._lock:
            session = cls._get_realtime_or_raise(session_id)
            duration = cls._float(payload.get("duration_sec"), 0.0)
            session["latest_decision"] = "CONTINUE"
            if duration > session["thresholds"]["max_duration_sec"]:
                session["status"] = "timeout"
                session["latest_decision"] = "TIMEOUT"
                cls._append_alert(
                    session_id,
                    rule="step_timeout",
                    severity="warning",
                    message=f"单步耗时 {duration:.2f}s 超过阈值。",
                    decision="TIMEOUT",
                )
            cls._save_session(session)
            return cls._serialize_realtime_session(session)

    @classmethod
    def _count_recent_node_switches(cls, events: list[dict[str, Any]]) -> int:
        switches = 0
        last = ""
        for event in events:
            node = str(event.get("node") or "").strip()
            if not node:
                continue
            if last and node != last:
                switches += 1
            last = node
        return switches

    @classmethod
    def _load_recent_events_as_dicts(cls, session_id: str, count: int = 40) -> list[dict[str, Any]]:
        key = cls._events_key(session_id)
        raw_items = redis_client.lrange(key, -count, -1)
        result: list[dict[str, Any]] = []
        for item in raw_items:
            if isinstance(item, str):
                try:
                    result.append(json.loads(item))
                except json.JSONDecodeError:
                    pass
            elif isinstance(item, dict):
                result.append(item)
        return result

    @classmethod
    def ingest_stream_event(cls, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        with cls._lock:
            session = cls._get_realtime_or_raise(session_id)

            node = str(payload.get("node") or "").strip()
            if not node:
                raise ValueError("node_required")

            agent_type = str(payload.get("agent_type") or "worker").strip() or "worker"
            step_raw = payload.get("step")
            step = int(step_raw) if step_raw is not None else int(session["step_count"]) + 1
            duration_sec = cls._float(payload.get("duration_sec"), 0.0)
            event_type = str(payload.get("event_type") or "node_execution")
            thought = str(payload.get("thought") or "")
            message = str(payload.get("message") or "")
            next_agent = str(payload.get("next_agent") or "")
            source = str(payload.get("source") or "langgraph-stream")
            state = payload.get("state") if isinstance(payload.get("state"), dict) else {}

            normalized_tool_calls: list[dict[str, Any]] = []
            for item in payload.get("tool_calls") or []:
                if not isinstance(item, dict):
                    continue
                tool_name = str(item.get("name") or item.get("tool_name") or "").strip()
                if not tool_name:
                    continue
                normalized_tool_calls.append(
                    {
                        "name": tool_name,
                        "params": item.get("params") if isinstance(item.get("params"), dict) else {},
                        "dangerous": bool(item.get("dangerous")),
                    }
                )

            session["event_count"] = int(session.get("event_count", 0)) + 1
            session["step_count"] = max(int(session.get("step_count", 0)), step)
            if normalized_tool_calls:
                session["tool_call_count"] = int(session.get("tool_call_count", 0)) + len(normalized_tool_calls)

            previous_node = str(session.get("current_node") or "")
            if previous_node and node != previous_node:
                session["node_switch_count"] = int(session.get("node_switch_count", 0)) + 1
            session["current_node"] = node
            session["current_agent_type"] = agent_type

            decision = "CONTINUE"
            reason = ""
            status = session.get("status", "running")
            threshold = session.get("thresholds") or {}

            dangerous_call = any(
                bool(tool.get("dangerous")) or str(tool.get("name") or "") in cls._dangerous_tools
                for tool in normalized_tool_calls
            )

            if status != "running":
                decision = session.get("latest_decision", "STOP")
                reason = "session_not_running"
            elif dangerous_call:
                status = "blocked"
                decision = "BLOCK"
                reason = "dangerous_tool"
                tool_names = [str(tool.get("name") or "") for tool in normalized_tool_calls]
                cls._append_alert(
                    session_id,
                    rule="dangerous_tool",
                    severity="critical",
                    message=f"LangGraph事件检测到危险工具调用: {', '.join(tool_names)}",
                    decision="BLOCK",
                )
            elif duration_sec > cls._float(threshold.get("max_duration_sec"), 30.0):
                status = "timeout"
                decision = "TIMEOUT"
                reason = "step_timeout"
                cls._append_alert(
                    session_id,
                    rule="step_timeout",
                    severity="warning",
                    message=f"LangGraph单步耗时 {duration_sec:.2f}s 超过阈值。",
                    decision="TIMEOUT",
                )
            elif int(session.get("tool_call_count", 0)) > int(threshold.get("max_tool_calls", 15)):
                status = "stopped"
                decision = "STOP"
                reason = "tool_call_overflow"
                cls._append_alert(
                    session_id,
                    rule="tool_call_overflow",
                    severity="warning",
                    message="工具调用次数超阈值，存在死循环风险。",
                    decision="STOP",
                )
            elif int(session.get("step_count", 0)) > int(threshold.get("max_steps", 80)):
                status = "stopped"
                decision = "STOP"
                reason = "step_overflow"
                cls._append_alert(
                    session_id,
                    rule="step_overflow",
                    severity="warning",
                    message="执行步数超阈值，任务被终止。",
                    decision="STOP",
                )
            else:
                recent_events = cls._load_recent_events_as_dicts(session_id, 5)
                recent_nodes = [str(item.get("node") or "") for item in recent_events]
                same_node_hits = sum(1 for item in recent_nodes if item and item == node)
                if same_node_hits + 1 >= int(threshold.get("max_same_node", 5)):
                    status = "stopped"
                    decision = "STOP"
                    reason = "same_node_loop"
                    cls._append_alert(
                        session_id,
                        rule="same_node_loop",
                        severity="warning",
                        message=f"节点 {node} 连续重复出现，疑似循环。",
                        decision="STOP",
                    )
                else:
                    recent_for_switch_events = cls._load_recent_events_as_dicts(session_id, 11)
                    recent_for_switch = recent_for_switch_events + [{"node": node}]
                    switch_count = cls._count_recent_node_switches(recent_for_switch)
                    if switch_count >= int(threshold.get("max_node_switches", 8)):
                        status = "stopped"
                        decision = "STOP"
                        reason = "agent_oscillation"
                        cls._append_alert(
                            session_id,
                            rule="agent_oscillation",
                            severity="warning",
                            message="多Agent节点切换过于频繁，疑似震荡。",
                            decision="STOP",
                        )

            session["status"] = status
            session["latest_decision"] = decision

            event = {
                "id": f"ev_{uuid4().hex[:10]}",
                "session_id": session_id,
                "event_type": event_type,
                "node": node,
                "agent_type": agent_type,
                "step": step,
                "thought": thought,
                "message": message,
                "next_agent": next_agent,
                "tool_calls": normalized_tool_calls,
                "state": state,
                "duration_sec": duration_sec,
                "decision": decision,
                "reason": reason,
                "source": source,
                "created_at": cls._now().isoformat(),
            }
            cls._append_stream_event(session_id, event)
            cls._save_session(session)

            return {
                "session": cls._serialize_realtime_session(session),
                "event": cls._serialize_stream_event(event),
                "decision": decision,
                "reason": reason,
                "should_stop": decision in {"STOP", "BLOCK", "TIMEOUT"},
            }

    @classmethod
    def end_realtime_session(cls, session_id: str) -> dict[str, Any]:
        with cls._lock:
            session = cls._get_realtime_or_raise(session_id)
            if session["status"] == "running":
                session["status"] = "completed"
            session["ended_at"] = cls._now().isoformat()
            cls._save_session(session)
            return cls._serialize_realtime_session(session)

    @classmethod
    def list_realtime_sessions(cls) -> list[dict[str, Any]]:
        session_ids = redis_client.smembers(_RT_INDEX)
        items: list[dict[str, Any]] = []
        for sid in session_ids:
            session = cls._load_session(sid)
            if session:
                items.append(cls._serialize_realtime_session(session))
        return sorted(items, key=lambda item: item["started_at"], reverse=True)

    @classmethod
    def get_realtime_session_detail(cls, session_id: str) -> dict[str, Any]:
        with cls._lock:
            session = cls._get_realtime_or_raise(session_id)
            raw_alerts = redis_client.lrange(cls._alerts_key(session_id), -30, -1)
            alerts: list[dict[str, Any]] = []
            for a in raw_alerts:
                if isinstance(a, str):
                    try:
                        alerts.append(json.loads(a))
                    except json.JSONDecodeError:
                        pass
                elif isinstance(a, dict):
                    alerts.append(a)

            raw_events = redis_client.lrange(cls._events_key(session_id), -40, -1)
            events: list[dict[str, Any]] = []
            for e in raw_events:
                if isinstance(e, str):
                    try:
                        events.append(json.loads(e))
                    except json.JSONDecodeError:
                        pass
                elif isinstance(e, dict):
                    events.append(e)

            return {
                "session": cls._serialize_realtime_session(session),
                "latest_alerts": [cls._serialize_alert(item) for item in alerts],
                "latest_events": [cls._serialize_stream_event(item) for item in events],
            }

    @classmethod
    def list_realtime_alerts(cls, session_id: str) -> list[dict[str, Any]]:
        raw_alerts = redis_client.lrange(cls._alerts_key(session_id), 0, -1)
        alerts: list[dict[str, Any]] = []
        for a in raw_alerts:
            if isinstance(a, str):
                try:
                    alerts.append(json.loads(a))
                except json.JSONDecodeError:
                    pass
            elif isinstance(a, dict):
                alerts.append(a)
        return [cls._serialize_alert(item) for item in alerts]

    # ------------------------------------------------------------------
    # Trace evaluation (unchanged logic)
    # ------------------------------------------------------------------

    @classmethod
    def evaluate_trace(cls, trace: dict[str, Any], dimension_weights: dict[str, float] | None = None) -> dict[str, Any]:
        steps = trace.get("steps") or []
        step_count = len(steps)
        durations = [cls._float(step.get("duration"), 0.0) for step in steps if isinstance(step, dict)]
        total_duration = round(sum(durations), 4)

        explicit_success = trace.get("success")
        final_result = str(trace.get("final_result") or "")
        expected_result = str(trace.get("expected_result") or "")
        if explicit_success is None:
            if expected_result:
                success = expected_result.lower() in final_result.lower()
            else:
                fail_tokens = ["失败", "无法", "error", "unknown", "not found"]
                success = not any(token in final_result.lower() for token in fail_tokens)
        else:
            success = cls._bool(explicit_success)

        thought_ratio = (
            sum(1 for step in steps if isinstance(step, dict) and str(step.get("thought") or "").strip()) / step_count
            if step_count
            else 0.0
        )
        action_ratio = (
            sum(1 for step in steps if isinstance(step, dict) and step.get("action")) / step_count
            if step_count
            else 0.0
        )

        step_ids = [int(step.get("step", idx + 1)) for idx, step in enumerate(steps) if isinstance(step, dict)]
        monotonic = float(all(step_ids[idx] >= step_ids[idx - 1] for idx in range(1, len(step_ids)))) if step_ids else 0.0
        plan_score = round((thought_ratio * 0.4 + action_ratio * 0.4 + monotonic * 0.2) * 100, 2)

        tool_names: list[str] = []
        dangerous_calls = 0
        for step in steps:
            if not isinstance(step, dict):
                continue
            action = step.get("action") or {}
            tool_name = ""
            if isinstance(action, dict):
                tool_name = str(action.get("tool") or action.get("name") or "").strip()
            elif isinstance(action, str):
                tool_name = action.strip()
            if tool_name:
                tool_names.append(tool_name)
                if tool_name in cls._dangerous_tools:
                    dangerous_calls += 1

        if not tool_names:
            tool_score = 55.0
        else:
            diversity = len(set(tool_names)) / len(tool_names)
            dangerous_penalty = min(0.5, dangerous_calls / max(1, len(tool_names)))
            tool_score = round(max(0.0, (0.65 + 0.35 * diversity - dangerous_penalty) * 100), 2)

        # tool_relevance: how well tool names match the task description
        task_lower = str(trace.get("task", "")).lower()
        task_keywords = set(
            w for w in task_lower.replace("_", " ").replace("-", " ").split()
            if len(w) > 2
        )
        if tool_names and task_keywords:
            tool_keywords = set(
                kw for t in tool_names for kw in t.lower().replace("_", " ").replace("-", " ").split()
                if len(kw) > 2
            )
            overlap = len(task_keywords & tool_keywords)
            relevance_ratio = overlap / max(1, len(task_keywords))
            tool_relevance = round(max(0.0, min(100.0, relevance_ratio * 100 + 30)), 2)
        else:
            tool_relevance = 50.0

        uncertain_tokens = ["maybe", "可能", "猜测", "unknown", "不确定"]
        result_texts = [str(step.get("result") or "") for step in steps if isinstance(step, dict)] + [final_result]
        uncertain_hits = sum(1 for text in result_texts if any(token in text.lower() for token in uncertain_tokens))
        hallucination_score = round(max(0.0, (1 - uncertain_hits / max(1, len(result_texts))) * 100), 2)

        memory_flags = [step.get("memory_hit") for step in steps if isinstance(step, dict) and step.get("memory_hit") is not None]
        if memory_flags:
            memory_score = round(mean(100.0 if cls._bool(flag) else 0.0 for flag in memory_flags), 2)
        else:
            memory_score = 70.0

        if step_count == 0:
            efficiency_score = 0.0
        else:
            step_factor = max(0.0, 1 - max(0, step_count - 8) / 20)
            duration_factor = max(0.0, 1 - max(0.0, total_duration - 15.0) / 45.0)
            efficiency_score = round((step_factor * 0.5 + duration_factor * 0.5) * 100, 2)

        # context_consistency: how consistently each step builds on the previous one
        if step_count < 2:
            context_consistency = 75.0
        else:
            consistent_pairs = 0
            total_pairs = 0
            for i in range(1, len(steps)):
                prev = steps[i - 1] if isinstance(steps[i - 1], dict) else None
                curr = steps[i] if isinstance(steps[i], dict) else None
                if not prev or not curr:
                    continue
                total_pairs += 1
                prev_result = str(prev.get("result") or "").strip().lower()
                curr_thought = str(curr.get("thought") or "").strip().lower()
                # Check if previous step's result is referenced in current step's thought
                if prev_result and curr_thought:
                    prev_keywords = set(w for w in prev_result.split() if len(w) > 3)
                    if prev_keywords:
                        overlap = sum(1 for kw in prev_keywords if kw in curr_thought)
                        if overlap >= max(1, len(prev_keywords) * 0.15):
                            consistent_pairs += 1
            consistency_ratio = consistent_pairs / max(1, total_pairs)
            context_consistency = round(max(0.0, consistency_ratio * 100), 2)

        success_bonus = 8.0 if success else -8.0
        dw = dimension_weights or {}
        overall = round(
            max(
                0.0,
                min(
                    100.0,
                    plan_score * dw.get("plan", 0.18)
                    + tool_score * dw.get("tool", 0.16)
                    + tool_relevance * dw.get("tool_relevance", 0.06)
                    + hallucination_score * dw.get("hallucination", 0.16)
                    + memory_score * dw.get("memory", 0.12)
                    + context_consistency * dw.get("context_consistency", 0.06)
                    + efficiency_score * dw.get("efficiency", 0.20)
                    + success_bonus,
                ),
            ),
            2,
        )

        if success:
            root_cause = "none"
        elif tool_score < 55:
            root_cause = "tool_misuse"
        elif hallucination_score < 60:
            root_cause = "hallucination_risk"
        elif efficiency_score < 50:
            root_cause = "inefficient_plan"
        elif context_consistency < 50:
            root_cause = "inconsistent_context"
        elif tool_relevance < 40:
            root_cause = "irrelevant_tool_use"
        else:
            root_cause = "task_mismatch"

        recommendations: list[str] = []
        if plan_score < 65:
            recommendations.append("优化任务拆解与步骤规划，减少无效思考。")
        if tool_score < 65:
            recommendations.append("强化工具选择策略，避免重复或危险调用。")
        if tool_relevance < 50:
            recommendations.append("工具选择与任务目标关联度低，建议校准工具命名与任务描述的语义对齐。")
        if hallucination_score < 65:
            recommendations.append("补充检索与事实校验，降低幻觉输出风险。")
        if memory_score < 65:
            recommendations.append("提升记忆读取与写入一致性，减少上下文遗失。")
        if context_consistency < 50:
            recommendations.append("步骤间上下文连贯性不足，建议强化中间结果传递与引用机制。")
        if efficiency_score < 65:
            recommendations.append("控制步骤数量与总耗时，优先裁剪低价值动作。")
        if not recommendations:
            recommendations.append("整体表现稳定，可继续针对真实业务场景做压力回归测试。")

        return {
            "session_id": str(trace.get("session_id") or f"s_{uuid4().hex[:8]}"),
            "task": str(trace.get("task") or ""),
            "success": bool(success),
            "scores": {
                "plan": plan_score,
                "tool": tool_score,
                "tool_relevance": tool_relevance,
                "hallucination": hallucination_score,
                "memory": memory_score,
                "context_consistency": context_consistency,
                "efficiency": efficiency_score,
                "overall": overall,
            },
            "metrics": {
                "step_count": step_count,
                "total_duration": total_duration,
                "tool_call_count": len(tool_names),
                "dangerous_call_count": dangerous_calls,
            },
            "root_cause": root_cause,
            "recommendations": recommendations,
        }

    # ------------------------------------------------------------------
    # Offline job lifecycle (Redis-persisted)
    # ------------------------------------------------------------------

    @classmethod
    def submit_offline_job(cls, trace: dict[str, Any]) -> dict[str, Any]:
        with cls._lock:
            now = cls._now().isoformat()
            job_id = f"off_{uuid4().hex[:12]}"
            job = {
                "job_id": job_id,
                "status": "queued",
                "created_at": now,
                "updated_at": now,
                "error": None,
                "report": None,
            }
            cls._save_offline_job(job, trace)
            return cls._serialize_offline_job(job)

    @classmethod
    def _save_offline_job(cls, job: dict[str, Any], trace: dict[str, Any] | None = None) -> None:
        key = cls._offline_key(job["job_id"])
        payload = {**job}
        if trace is not None:
            payload["_trace"] = trace
        redis_client.set_json(key, payload, ex=_TTL_TERMINATED)
        redis_client.sadd(_OFF_INDEX, job["job_id"])

    @classmethod
    def _load_offline_job(cls, job_id: str) -> dict[str, Any] | None:
        return redis_client.get_json(cls._offline_key(job_id))

    @classmethod
    def _serialize_offline_job(cls, job: dict[str, Any]) -> dict[str, Any]:
        return {
            "job_id": job["job_id"],
            "status": job["status"],
            "created_at": cls._as_dt(job["created_at"]),
            "updated_at": cls._as_dt(job["updated_at"]),
            "error": job.get("error"),
            "report": job.get("report"),
        }

    @classmethod
    def process_offline_job(cls, job_id: str) -> None:
        job = cls._load_offline_job(job_id)
        if job is None:
            return
        trace = job.get("_trace") or {}
        job["status"] = "running"
        job["updated_at"] = cls._now().isoformat()
        cls._save_offline_job(job)

        try:
            report = cls.evaluate_trace(trace)
            mongo_db["offline_eval_reports"].insert_one(
                {
                    "job_id": job_id,
                    "trace_session_id": trace.get("session_id"),
                    "created_at": cls._now().isoformat(),
                    "report": report,
                }
            )
            job["status"] = "completed"
            job["report"] = report
            job["updated_at"] = cls._now().isoformat()
            job.pop("_trace", None)
            cls._save_offline_job(job)
        except Exception as exc:
            job["status"] = "failed"
            job["error"] = str(exc)
            job["updated_at"] = cls._now().isoformat()
            cls._save_offline_job(job)

    @classmethod
    def list_offline_jobs(cls) -> list[dict[str, Any]]:
        job_ids = redis_client.smembers(_OFF_INDEX)
        items: list[dict[str, Any]] = []
        for jid in job_ids:
            job = cls._load_offline_job(jid)
            if job:
                items.append(cls._serialize_offline_job(job))
        return sorted(items, key=lambda item: item["created_at"], reverse=True)

    @classmethod
    def get_offline_job(cls, job_id: str) -> dict[str, Any] | None:
        job = cls._load_offline_job(job_id)
        return cls._serialize_offline_job(job) if job else None

    # ------------------------------------------------------------------
    # Batch job lifecycle (Redis-persisted)
    # ------------------------------------------------------------------

    @classmethod
    def submit_batch_job(cls, dataset_id: str, strategy_name: str | None = None,
                         eval_task_id: int | None = None) -> dict[str, Any]:
        with cls._lock:
            now = cls._now().isoformat()
            job_id = f"bat_{uuid4().hex[:12]}"
            job = {
                "job_id": job_id,
                "status": "queued",
                "created_at": now,
                "updated_at": now,
                "dataset_id": dataset_id,
                "strategy_name": strategy_name,
                "eval_task_id": eval_task_id,
                "error": None,
                "summary": None,
                "progress": {"processed": 0, "total": 0},
            }
            cls._save_batch_job(job)
            return cls._serialize_batch_job(job)

    @classmethod
    def _save_batch_job(cls, job: dict[str, Any]) -> None:
        key = cls._batch_key(job["job_id"])
        redis_client.set_json(key, job, ex=_TTL_TERMINATED)
        redis_client.sadd(_BAT_INDEX, job["job_id"])

    @classmethod
    def _load_batch_job(cls, job_id: str) -> dict[str, Any] | None:
        return redis_client.get_json(cls._batch_key(job_id))

    @classmethod
    def _serialize_batch_job(cls, job: dict[str, Any]) -> dict[str, Any]:
        return {
            "job_id": job["job_id"],
            "status": job["status"],
            "created_at": cls._as_dt(job["created_at"]),
            "updated_at": cls._as_dt(job["updated_at"]),
            "error": job.get("error"),
            "summary": job.get("summary"),
            "progress": job.get("progress"),
            "eval_task_id": job.get("eval_task_id"),
        }

    @classmethod
    def _convert_dataset_row_to_trace(cls, row: dict[str, Any], index: int, dataset_id: str) -> dict[str, Any]:
        session_id = str(row.get("session_id") or f"{dataset_id}_{index + 1}")
        task = str(row.get("task") or row.get("instruction") or row.get("question") or "dataset-task")

        if isinstance(row.get("steps"), list):
            steps = row["steps"]
        elif isinstance(row.get("trace"), list):
            steps = row["trace"]
        else:
            tool_name = row.get("tool") or row.get("tool_name") or ""
            action = {"tool": str(tool_name), "params": row.get("params") or {}} if tool_name else {}
            duration = cls._float(row.get("duration"), 0.0)
            if duration <= 0:
                duration = cls._float(row.get("latency_ms"), 0.0) / 1000.0
            steps = [
                {
                    "step": 1,
                    "thought": str(row.get("thought") or ""),
                    "action": action,
                    "result": str(row.get("result") or row.get("answer") or row.get("output") or ""),
                    "duration": round(max(0.0, duration), 4),
                }
            ]

        final_result = str(row.get("final_result") or row.get("answer") or row.get("output") or "")
        trace = {
            "session_id": session_id,
            "task": task,
            "steps": steps,
            "final_result": final_result,
            "success": row.get("success") if "success" in row else row.get("task_success"),
            "expected_result": row.get("expected") or row.get("ground_truth") or row.get("label"),
        }
        return trace

    @classmethod
    def _evaluate_batch_chunk(cls, rows: list[dict[str, Any]], dataset_id: str, dimension_weights: dict[str, float] | None = None) -> list[dict[str, Any]]:
        return [
            cls.evaluate_trace(cls._convert_dataset_row_to_trace(row, idx, dataset_id), dimension_weights)
            for idx, row in enumerate(rows)
        ]

    @classmethod
    def process_batch_job(cls, job_id: str, chunk_size: int = 200) -> None:
        job = cls._load_batch_job(job_id)
        if job is None:
            return
        job["status"] = "running"
        job["updated_at"] = cls._now().isoformat()
        cls._save_batch_job(job)
        dataset_id = str(job.get("dataset_id") or "")
        strategy_name = str(job.get("strategy_name") or "")

        try:
            db: Session = SessionLocal()
            try:
                asset = DatasetParserService.get_asset_by_dataset_id(db, dataset_id)

                # Load strategy dimension_weights if specified
                dimension_weights: dict[str, float] | None = None
                if strategy_name:
                    try:
                        from app.models.strategy import EvaluationStrategy
                        strat = db.scalar(
                            select(EvaluationStrategy).where(EvaluationStrategy.name == strategy_name)
                        )
                        if strat and strat.dimension_weights:
                            dimension_weights = strat.dimension_weights
                    except Exception as exc:
                        print(f"Warning: failed to load strategy '{strategy_name}': {exc}")
            finally:
                db.close()
            if asset is None:
                raise ValueError("dataset not found")

            rows = DatasetParserService.load_asset_rows(asset)
            if not rows:
                raise ValueError("dataset has no valid rows")

            total = min(len(rows), 500)
            reports: list[dict[str, Any]] = []
            processed = 0

            for start in range(0, total, chunk_size):
                chunk = rows[start : start + chunk_size]
                chunk_reports = cls._evaluate_batch_chunk(chunk, dataset_id, dimension_weights)
                reports.extend(chunk_reports)
                processed += len(chunk_reports)

                # Update progress in job
                job = cls._load_batch_job(job_id)
                if job is None:
                    return
                job["status"] = "running"
                job["progress"] = {"processed": processed, "total": total}
                job["updated_at"] = cls._now().isoformat()
                cls._save_batch_job(job)

            if not reports:
                raise ValueError("no valid reports generated")

            success_rate = round(mean(1.0 if report["success"] else 0.0 for report in reports), 4)
            average_scores = {
                score_name: round(mean(report["scores"][score_name] for report in reports), 4)
                for score_name in reports[0]["scores"].keys()
            }
            root_counter = Counter(report["root_cause"] for report in reports)

            summary = {
                "dataset_id": dataset_id,
                "total_traces": len(reports),
                "success_rate": success_rate,
                "average_scores": average_scores,
                "root_cause_distribution": dict(root_counter),
                "sample_reports": reports[:80],
            }

            mongo_db["batch_eval_reports"].insert_one(
                {
                    "job_id": job_id,
                    "dataset_id": dataset_id,
                    "created_at": cls._now().isoformat(),
                    "summary": summary,
                }
            )

            # Persist to EvaluationTask + EvaluationResult so batch results
            # appear in the task management page and results analysis page.
            eval_task_id: int | None = None
            task_db: Session = SessionLocal()
            try:
                task = EvaluationTask(
                    name=f"Batch: {dataset_id[-60:]}" if len(dataset_id) > 60 else f"Batch: {dataset_id}",
                    mode="dataset-batch",
                    eval_mode="dataset-batch",
                    dataset_id=dataset_id,
                    agent_version="v1",
                    status="completed",
                    total_samples=len(reports),
                    completed_samples=len(reports),
                    progress=100,
                    started_at=cls._now(),
                    finished_at=cls._now(),
                )
                task_db.add(task)
                task_db.flush()
                for report in reports:
                    er = EvaluationResult(
                        task_id=task.id,
                        sample_id=report.get("session_id"),
                        scores=report.get("scores", {}),
                        metrics_scores=report.get("scores", {}),
                        status="success" if report.get("success") else "failed",
                        raw_data=report,
                        stats={
                            "root_cause": report.get("root_cause", ""),
                            "job_id": job_id,
                        },
                    )
                    task_db.add(er)
                task_db.commit()
                eval_task_id = task.id
            except Exception as exc:
                task_db.rollback()
                print(f"Warning: failed to persist batch task to DB: {exc}")
            finally:
                task_db.close()

            job = cls._load_batch_job(job_id)
            if job is not None:
                job["status"] = "completed"
                job["summary"] = summary
                job["eval_task_id"] = eval_task_id
                job["updated_at"] = cls._now().isoformat()
                cls._save_batch_job(job)
        except Exception as exc:
            job = cls._load_batch_job(job_id)
            if job is not None:
                job["status"] = "failed"
                job["error"] = str(exc)
                job["updated_at"] = cls._now().isoformat()
                cls._save_batch_job(job)

    @classmethod
    def list_batch_jobs(cls) -> list[dict[str, Any]]:
        job_ids = redis_client.smembers(_BAT_INDEX)
        items: list[dict[str, Any]] = []
        for jid in job_ids:
            job = cls._load_batch_job(jid)
            if job:
                items.append(cls._serialize_batch_job(job))
        return sorted(items, key=lambda item: item["created_at"], reverse=True)

    @classmethod
    def get_batch_job(cls, job_id: str) -> dict[str, Any] | None:
        job = cls._load_batch_job(job_id)
        return cls._serialize_batch_job(job) if job else None
