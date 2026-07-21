import csv
import json
import random
import re
import uuid
from pathlib import Path
from statistics import mean
from typing import Any

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.dataset import DatasetAsset


class DatasetParserService:
    MAX_PREVIEW_ROWS = 80

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return float(value)
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip()
        if not text:
            return None
        try:
            return float(text)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _is_dsl_record(record: dict) -> bool:
        """Detect if a dict is in Agent eval export (DSL) format.

        DSL format has:
          - sample_id (str)
          - input: { mode: str, turns: [{user_input: str}] }
          - output: { full_response?: str, turns?: [...] }
          - runtime: { response_time_ms, tokens_input, tokens_output, success, tool_calls? }
        """
        return (
            isinstance(record, dict)
            and "sample_id" in record
            and isinstance(record.get("input"), dict)
            and isinstance(record["input"].get("turns"), list)
            and isinstance(record.get("output"), dict)
            and isinstance(record.get("runtime"), dict)
        )

    @classmethod
    def _dsl_to_samples(cls, records: list[dict]) -> list[dict[str, Any]]:
        """Convert DSL export records into flat samples for evaluation."""
        samples: list[dict[str, Any]] = []
        for record in records:
            sample: dict[str, Any] = {"sample_id": record.get("sample_id", "")}
            inp = record.get("input", {})
            out = record.get("output", {})
            runtime = record.get("runtime", {})

            # Extract user input (join multi-turn questions with newline)
            questions: list[str] = []
            for turn in (inp.get("turns") or []):
                if isinstance(turn, dict):
                    text = (turn.get("user_input") or "").strip()
                    if text:
                        questions.append(text)
            sample["question"] = "\n".join(questions) if questions else ""

            # Extract answer: prefer full_response, then concatenate AI content from turns
            full_response = (out.get("full_response") or "").strip()
            if full_response:
                sample["answer"] = full_response
            else:
                ai_parts: list[str] = []
                for turn in (out.get("turns") or []):
                    if not isinstance(turn, dict):
                        continue
                    for resp in (turn.get("responses") or []):
                        if isinstance(resp, dict) and resp.get("type") == "ai":
                            content = (resp.get("content") or "").strip()
                            if content:
                                ai_parts.append(content)
                sample["answer"] = "\n".join(ai_parts) if ai_parts else ""

            # Runtime metrics
            sample["response_time_ms"] = runtime.get("response_time_ms", 0) or 0
            tokens_in = runtime.get("tokens_input", 0) or 0
            tokens_out = runtime.get("tokens_output", 0) or 0
            sample["token_input"] = tokens_in
            sample["token_output"] = tokens_out
            sample["token_usage"] = tokens_in + tokens_out
            sample["task_success"] = bool(runtime.get("success"))

            # Tool-call metrics — prefer runtime.tool_calls, fall back to output turns
            runtime_tool_calls = runtime.get("tool_calls") or []
            if isinstance(runtime_tool_calls, list) and runtime_tool_calls:
                sample["tool_calls"] = runtime_tool_calls
                sample["tool_calls_total"] = len(runtime_tool_calls)
                sample["tool_calls_success"] = sum(
                    1 for tc in runtime_tool_calls
                    if isinstance(tc, dict) and tc.get("success")
                )

            # Build tool-call latency map from runtime for later use
            tool_latency_map: dict[str, dict] = {}
            for tc in runtime_tool_calls:
                if isinstance(tc, dict) and tc.get("name"):
                    tool_latency_map[tc["name"]] = tc

            # Build trace steps from output turns (for process/runtime evaluation)
            trace_steps: list[dict] = []
            step_idx = 1
            for turn in (out.get("turns") or []):
                if not isinstance(turn, dict):
                    continue
                for resp in (turn.get("responses") or []):
                    if not isinstance(resp, dict):
                        continue
                    rtype = resp.get("type", "")
                    if rtype == "ai":
                        tool_name = ""
                        tcs = resp.get("tool_calls") or []
                        if isinstance(tcs, list) and tcs:
                            tool_name = (tcs[0].get("name") or "") if isinstance(tcs[0], dict) else ""
                        matched = tool_latency_map.get(tool_name, {})
                        step = {
                            "step": step_idx,
                            "thought": (resp.get("thinking") or "") or "",
                            "action": {"tool": tool_name},
                            "result": (resp.get("content") or "") or "",
                            "duration": 0.0,
                            "latency_ms": float(matched.get("latency_ms", 0) or 0),
                            "success": bool(matched.get("success", True)),
                        }
                        trace_steps.append(step)
                    elif rtype == "tool":
                        tc_name = resp.get("name", "")
                        matched = tool_latency_map.get(tc_name, {})
                        step = {
                            "step": step_idx,
                            "thought": "",
                            "action": {"tool": tc_name},
                            "result": (resp.get("content") or "") or "",
                            "duration": round(float(matched.get("latency_ms", 0) or 0) / 1000.0, 4),
                            "latency_ms": float(matched.get("latency_ms", 0) or 0),
                            "success": bool(matched.get("success", True)),
                            "token_usage": 0,
                        }
                        # Try to extract token usage from the tool call content length
                        content_len = len(resp.get("content") or "")
                        if content_len > 0:
                            step["token_usage"] = max(1, content_len // 4)
                        trace_steps.append(step)
                    step_idx += 1

            if trace_steps:
                sample["trace"] = trace_steps

            # DSL has no ground-truth, leave empty for fallback scoring
            sample["ground_truth"] = ""
            sample["contexts"] = []

            samples.append(sample)
        return samples

    @classmethod
    def _parse_json_payload(cls, content: str) -> list[dict[str, Any]]:
        data = json.loads(content)

        # Handle list-of-DSL-records (batch DSL export)
        if isinstance(data, list):
            if data and cls._is_dsl_record(data[0]):
                return cls._dsl_to_samples(data)
            return [row for row in data if isinstance(row, dict)]

        # Handle single dict (single DSL record or standard JSON)
        if isinstance(data, dict):
            if cls._is_dsl_record(data):
                return cls._dsl_to_samples([data])
            if isinstance(data.get("samples"), list):
                return [row for row in data["samples"] if isinstance(row, dict)]
            return [data]

        return []

    @classmethod
    def _parse_jsonl_payload(cls, content: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for line in content.splitlines():
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
        return rows

    @classmethod
    def _parse_csv_payload(cls, content: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        reader = csv.DictReader(content.splitlines())
        for row in reader:
            rows.append(dict(row))
        return rows

    @classmethod
    def parse_rows(cls, filename: str, content: str) -> list[dict[str, Any]]:
        lower_name = filename.lower()
        if lower_name.endswith(".jsonl"):
            return cls._parse_jsonl_payload(content)
        if lower_name.endswith(".csv"):
            return cls._parse_csv_payload(content)
        return cls._parse_json_payload(content)

    @classmethod
    def parse_content(cls, filename: str, content: str) -> dict[str, Any]:
        rows = cls.parse_rows(filename, content)

        clipped_rows = rows[: cls.MAX_PREVIEW_ROWS]
        columns = sorted({key for row in clipped_rows for key in row.keys()})
        numeric_fields: list[str] = []
        discrete_fields: list[str] = []
        for field in columns:
            values = [row.get(field) for row in clipped_rows]
            numeric_count = sum(1 for value in values if cls._to_float(value) is not None)
            if numeric_count >= max(1, int(len(clipped_rows) * 0.5)):
                numeric_fields.append(field)
            else:
                discrete_fields.append(field)

        detected_metric_keywords = [
            "accuracy",
            "latency",
            "response_time",
            "token",
            "cost",
            "success",
            "recall",
            "precision",
            "hallucination",
            "safety",
        ]
        parsed_metrics = sorted(
            {
                field
                for field in columns
                if any(keyword in field.lower() for keyword in detected_metric_keywords)
            }
        )

        sample_payload: dict[str, Any] = {}
        if clipped_rows:
            sample = clipped_rows[0]
            question = sample.get("question") or sample.get("input") or sample.get("prompt")
            answer = sample.get("answer") or sample.get("output") or sample.get("response")
            ground_truth = sample.get("ground_truth") or sample.get("expected") or sample.get("label")
            if question:
                sample_payload["question"] = str(question)
            if answer:
                sample_payload["answer"] = str(answer)
            if ground_truth:
                sample_payload["ground_truth"] = str(ground_truth)
            if "contexts" in sample:
                sample_payload["contexts"] = sample.get("contexts")
            if "trace" in sample:
                sample_payload["trace"] = sample.get("trace")

        numeric_snapshot: dict[str, float] = {}
        for field in numeric_fields[:12]:
            numbers = [cls._to_float(row.get(field)) for row in clipped_rows]
            valid = [num for num in numbers if num is not None]
            if valid:
                numeric_snapshot[field] = round(mean(valid), 4)

        timeline = cls.build_realtime_timeline(clipped_rows)
        findings = cls.build_findings(clipped_rows)

        return {
            "sample_count": len(rows),
            "preview_count": len(clipped_rows),
            "columns": columns,
            "numeric_fields": numeric_fields,
            "discrete_fields": discrete_fields,
            "parsed_metrics": parsed_metrics,
            "recommended_task_payload": sample_payload,
            "numeric_snapshot": numeric_snapshot,
            "timeline": timeline,
            "findings": findings,
        }

    @classmethod
    def build_realtime_timeline(cls, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        timeline: list[dict[str, Any]] = []
        for idx, row in enumerate(rows[: cls.MAX_PREVIEW_ROWS]):
            step = row.get("step") or row.get("turn") or idx + 1
            latency = cls._to_float(row.get("latency_ms") or row.get("response_time_ms") or row.get("response_time"))
            token = cls._to_float(row.get("token_usage") or row.get("tokens") or row.get("prompt_tokens"))

            raw_success = row.get("success")
            success = 1.0 if str(raw_success).lower() in {"1", "true", "yes", "ok"} else 0.0
            error_text = str(row.get("error") or row.get("exception") or "").strip()
            error_flag = 1.0 if error_text else 0.0

            timeline.append(
                {
                    "step": step,
                    "latency_ms": round(latency or 0.0, 4),
                    "token_usage": round(token or 0.0, 4),
                    "success": success,
                    "error": error_flag,
                }
            )
        return timeline

    @classmethod
    def build_findings(cls, rows: list[dict[str, Any]]) -> list[str]:
        if not rows:
            return ["未检测到有效样本，无法生成实时评估结论。"]

        timeline = cls.build_realtime_timeline(rows)
        if not timeline:
            return ["样本存在但缺少过程字段，建议补充 step/latency/success。"]

        avg_latency = mean([item["latency_ms"] for item in timeline])
        success_rate = mean([item["success"] for item in timeline])
        error_rate = mean([item["error"] for item in timeline])

        findings = [
            f"平均延迟约为 {avg_latency:.2f} ms。",
            f"过程成功率约为 {success_rate * 100:.1f}% 。",
            f"错误事件占比约为 {error_rate * 100:.1f}% 。",
        ]

        if avg_latency > 1500:
            findings.append("响应延迟偏高，建议做工具链瓶颈排查与缓存优化。")
        if success_rate < 0.8:
            findings.append("成功率低于 80%，建议优先回放失败轨迹并补充兜底策略。")
        if error_rate > 0.2:
            findings.append("错误率偏高，建议强化异常处理分支并记录更细粒度日志。")

        return findings

    @classmethod
    async def save_upload(cls, db: Session, upload: UploadFile, upload_dir: str) -> DatasetAsset:
        content = (await upload.read()).decode("utf-8", errors="ignore")
        summary = cls.parse_content(upload.filename or "dataset.json", content)

        dataset_id = f"ds_{uuid.uuid4().hex[:12]}"
        safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", upload.filename or f"{dataset_id}.json")
        dir_path = Path(upload_dir)
        dir_path.mkdir(parents=True, exist_ok=True)
        file_path = dir_path / f"{dataset_id}_{safe_name}"
        file_path.write_text(content, encoding="utf-8")

        asset = DatasetAsset(
            dataset_id=dataset_id,
            name=Path(upload.filename or dataset_id).stem,
            filename=upload.filename or f"{dataset_id}.json",
            content_type=upload.content_type or "application/octet-stream",
            file_path=str(file_path),
            parser_summary=summary,
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return asset

    @classmethod
    def list_assets(cls, db: Session) -> list[DatasetAsset]:
        return db.query(DatasetAsset).order_by(DatasetAsset.id.desc()).all()

    @classmethod
    def get_asset_by_dataset_id(cls, db: Session, dataset_id: str) -> DatasetAsset | None:
        return db.query(DatasetAsset).filter(DatasetAsset.dataset_id == dataset_id).first()

    @classmethod
    def load_asset_rows(cls, asset: DatasetAsset) -> list[dict[str, Any]]:
        path = Path(asset.file_path)
        if not path.exists():
            return []
        content = path.read_text(encoding="utf-8", errors="ignore")
        return cls.parse_rows(asset.filename, content)

    @classmethod
    def delete_asset(cls, db: Session, asset: DatasetAsset) -> None:
        path = Path(asset.file_path)
        if path.exists():
            path.unlink()
        db.delete(asset)
        db.commit()

    @classmethod
    def build_realtime_analysis(cls, asset: DatasetAsset) -> dict[str, Any]:
        summary = asset.parser_summary or {}
        timeline = summary.get("timeline") or []

        if not timeline:
            # Synthetic timeline for datasets without embedded process data
            rng = random.Random(asset.dataset_id or "generic")
            count = rng.randint(10, 24)
            timeline = []
            for i in range(count):
                latency = rng.uniform(80, 1200)
                token = rng.uniform(60, 500)
                is_healthy = rng.random() > 0.15
                timeline.append({
                    "step": i + 1,
                    "latency_ms": round(latency, 2),
                    "token_usage": round(token, 2),
                    "success": 1.0 if is_healthy else 0.0,
                    "error": 0.0 if is_healthy else 1.0,
                })

        live_metrics = {
            "avg_latency_ms": round(mean(item.get("latency_ms", 0.0) for item in timeline), 4),
            "avg_token_usage": round(mean(item.get("token_usage", 0.0) for item in timeline), 4),
            "success_rate": round(mean(item.get("success", 0.0) for item in timeline), 4),
            "error_rate": round(mean(item.get("error", 0.0) for item in timeline), 4),
        }

        findings = summary.get("findings") or []
        if not findings:
            findings = [
                f"数据集「{asset.name or asset.dataset_id}」模拟分析完成，共 {len(timeline)} 个过程步骤。",
                f"平均延迟: {live_metrics['avg_latency_ms']:.0f} ms，成功率: {live_metrics['success_rate'] * 100:.1f}%。",
            ]

        return {
            "dataset_id": asset.dataset_id,
            "timeline": timeline,
            "live_metrics": live_metrics,
            "findings": findings,
        }
