from collections.abc import Callable


def metric_response_time(payload: dict) -> float:
    return float(payload.get("response_time_ms", 0))


def metric_token_usage(payload: dict) -> float:
    return float(payload.get("token_usage", 0))


def metric_tool_accuracy(payload: dict) -> float:
    total = max(float(payload.get("tool_calls_total", 0)), 1.0)
    success = float(payload.get("tool_calls_success", 0))
    return round(success / total, 4)


def metric_task_success(payload: dict) -> float:
    return 1.0 if payload.get("task_success", False) else 0.0


BUILTIN_METRICS: dict[str, Callable[[dict], float]] = {
    "response_time": metric_response_time,
    "token_usage": metric_token_usage,
    "tool_accuracy": metric_tool_accuracy,
    "task_success": metric_task_success,
}
