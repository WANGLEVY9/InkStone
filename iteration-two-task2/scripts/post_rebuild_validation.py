import json
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

BASE = "http://localhost:8000/api/v1"
REPORT_PATH = Path("e:/Codes/2026-SEIII/iteration-two-task2/VALIDATION_REPORT.md")
TIMEOUT = 15


def request_json(method: str, path: str, payload: dict | None = None) -> tuple[int, dict | list | str]:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw


def poll_task_result(task_id: int, max_wait_seconds: int = 40) -> dict | None:
    deadline = time.time() + max_wait_seconds
    while time.time() < deadline:
        code, data = request_json("GET", f"/results/task/{task_id}")
        if code == 200 and isinstance(data, list) and len(data) > 0:
            return data[0]
        time.sleep(1.0)
    return None


def main() -> int:
    lines: list[str] = []
    lines.append("# 重建后联调验收报告")
    lines.append("")
    lines.append(f"- 生成时间: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"- 目标地址: {BASE}")
    lines.append("")

    checks: list[tuple[str, bool, str]] = []

    # 1) health check
    code, health = request_json("GET", "/health/")
    health_ok = code == 200 and isinstance(health, dict)
    checks.append(("基础健康检查", health_ok, f"HTTP {code}, body={health}"))

    # 2) save strategy (db persistence)
    tag = int(time.time() * 1000)
    strategy_name = f"auto-strategy-{tag}"
    save_payload = {
        "name": strategy_name,
        "metrics": ["task_success", "response_time"],
        "weights": {"task_success": 0.6, "response_time": 0.4},
        "description": "auto validation strategy",
    }
    code, save_data = request_json("POST", "/strategies/", save_payload)
    save_ok = code in (200, 201) and isinstance(save_data, dict) and save_data.get("name") == strategy_name
    checks.append(("策略保存接口", save_ok, f"HTTP {code}, body={save_data}"))

    code, list_data = request_json("GET", "/strategies/")
    listed = code == 200 and isinstance(list_data, list) and any(item.get("name") == strategy_name for item in list_data if isinstance(item, dict))
    checks.append(("策略落库可查询", listed, f"HTTP {code}, found={listed}"))

    # 3) dimension plugin + strategy score
    task_payload = {
        "name": f"auto-task-{tag}",
        "agent_version": "v1",
        "dataset_id": "auto-ds",
        "mode": "result",
        "method": "explicit",
        "dimension": "performance",
        "config": {
            "metrics": ["response_time", "token_usage", "task_success"],
            "strategy": strategy_name,
            "enable_process_trace": False,
        },
        "input_payload": {
            "response_time_ms": 220,
            "token_usage": 300,
            "task_success": True,
            "process_success_ratio": 0.9,
            "question": "q",
            "answer": "a",
            "ground_truth": "a",
            "contexts": ["ctx"],
        },
    }

    code, task_data = request_json("POST", "/tasks/", task_payload)
    task_created = code in (200, 201) and isinstance(task_data, dict) and isinstance(task_data.get("id"), int)
    checks.append(("任务创建", task_created, f"HTTP {code}, body={task_data}"))

    task_id = task_data.get("id") if isinstance(task_data, dict) else None
    if not task_created or task_id is None:
        result = None
        exec_data = None
        code = 0
    else:
        code, exec_data = request_json("POST", f"/tasks/{task_id}/execute")
        exec_ok = code in (200, 201) and isinstance(exec_data, dict)
        checks.append(("任务执行触发", exec_ok, f"HTTP {code}, body={exec_data}"))
        result = poll_task_result(task_id)

    got_result = isinstance(result, dict)
    checks.append(("结果轮询", got_result, "拿到结果" if got_result else "超时未拿到结果"))

    has_dimension_plugin = False
    has_dimension_metric = False
    has_strategy_score = False
    if got_result:
        raw_data = result.get("raw_data", {}) if isinstance(result, dict) else {}
        scores = result.get("scores", {}) if isinstance(result, dict) else {}
        engine_details = raw_data.get("engine_details", {}) if isinstance(raw_data, dict) else {}
        has_dimension_plugin = isinstance(engine_details, dict) and "dimension_plugin" in engine_details
        has_dimension_metric = isinstance(scores, dict) and any(str(k).startswith("dimension_") for k in scores.keys())
        has_strategy_score = isinstance(scores, dict) and "strategy_score" in scores

    checks.append(("维度插件明细存在", has_dimension_plugin, f"value={has_dimension_plugin}"))
    checks.append(("维度插件分存在", has_dimension_metric, f"value={has_dimension_metric}"))
    checks.append(("策略分存在", has_strategy_score, f"value={has_strategy_score}"))

    passed = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)

    lines.append("## 验收结果")
    lines.append("")
    for name, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        lines.append(f"- [{status}] {name}: {detail}")

    lines.append("")
    lines.append(f"- 汇总: {passed}/{total} 通过")

    if got_result:
        lines.append("")
        lines.append("## 核心输出快照")
        lines.append("")
        lines.append("- result.scores:")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(result.get("scores", {}), ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")
        lines.append("- result.raw_data.engine_details:")
        lines.append("")
        lines.append("```json")
        raw_data = result.get("raw_data", {}) if isinstance(result, dict) else {}
        details = raw_data.get("engine_details", {}) if isinstance(raw_data, dict) else {}
        lines.append(json.dumps(details, ensure_ascii=False, indent=2))
        lines.append("```")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
