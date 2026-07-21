import math
from collections.abc import Sequence

import pandas as pd

from app.models.result import EvaluationResult


class AnalysisService:
    @staticmethod
    def _normalize_score(metric: str, value: float) -> float:
        name = metric.lower()
        if "latency" in name or "response_time" in name:
            normalized = max(0.0, 1.0 - (value / 5000.0))
            return round(normalized, 6)
        if name.startswith("llm_judge_"):
            # LLM judge scores are 0-5 in current implementation.
            normalized = max(0.0, min(1.0, value / 5.0))
            return round(normalized, 6)
        if "success" in name and value in (0.0, 1.0):
            return value
        return round(max(0.0, min(1.0, value)), 6)

    @staticmethod
    def _approx_p_value(values: list[float]) -> float | None:
        if len(values) < 2:
            return None
        mean_val = sum(values) / len(values)
        variance = sum((x - mean_val) ** 2 for x in values) / max(len(values) - 1, 1)
        std = math.sqrt(variance)
        if std == 0:
            return 1.0
        # one-sample z-score against 0.5 normalized baseline
        z = abs(mean_val - 0.5) / (std / math.sqrt(len(values)))
        cdf = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        return round(max(0.0, min(1.0, 2.0 * (1.0 - cdf))), 6)

    @staticmethod
    def compare_results(items: Sequence[EvaluationResult]) -> dict:
        if not items:
            return {"summary": {}, "by_metric": {}}

        rows = []
        for item in items:
            row = {"task_id": item.task_id}
            row.update(item.metrics_scores or item.scores)
            rows.append(row)

        frame = pd.DataFrame(rows).fillna(0)
        numeric_cols = [col for col in frame.columns if col != "task_id"]
        summary = {}
        if numeric_cols:
            summary = frame[numeric_cols].describe().to_dict()

        by_metric = {}
        for col in numeric_cols:
            series = pd.to_numeric(frame[col], errors="coerce").fillna(0)
            best_idx = int(series.idxmax())
            best_task = int(frame.iloc[best_idx]["task_id"])
            normalized_values = [
                {
                    "task_id": int(row["task_id"]),
                    "normalized": AnalysisService._normalize_score(
                        col, float(row[col] or 0.0)
                    ),
                }
                for row in frame[["task_id", col]].to_dict(orient="records")
            ]
            p_value = AnalysisService._approx_p_value(
                [float(item["normalized"]) for item in normalized_values]
            )
            by_metric[col] = {
                "values": frame[["task_id", col]].to_dict(orient="records"),
                "best_task": best_task,
                "normalized_values": normalized_values,
                "p_value": p_value,
            }

        return {"summary": summary, "by_metric": by_metric}
