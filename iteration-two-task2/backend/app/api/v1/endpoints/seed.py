from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db, mongo_db
from app.models.dataset import DatasetAsset
from app.models.result import EvaluationResult
from app.models.task import EvaluationTask

router = APIRouter()

SEED_TAG = "seed-bulk-v3"

DATASET_SPECS = [
    {"dataset_id": "ds_agent_chat_v2", "name": "智能对话评测集", "filename": "agent_chat_v2.json"},
    {"dataset_id": "ds_tool_use_v1", "name": "工具调用评测集", "filename": "tool_use_v1.json"},
    {"dataset_id": "ds_rag_benchmark_v1", "name": "RAG 问答评测集", "filename": "rag_benchmark_v1.json"},
    {"dataset_id": "ds_safety_eval_v1", "name": "安全合规评测集", "filename": "safety_eval_v1.json"},
    {"dataset_id": "ds_code_gen_v1", "name": "代码生成评测集", "filename": "code_gen_v1.json"},
    {"dataset_id": "ds_long_context_v1", "name": "长上下文评测集", "filename": "long_context_v1.json"},
]

TASK_PATTERNS = [
    ("客服多轮对话质量", "result", "explicit", "effectiveness"),
    ("工具调用链路稳定性", "process", "explicit", "performance"),
    ("RAG 事实一致性", "result", "fuzzy", "effectiveness"),
    ("安全拒答与合规性", "result", "fuzzy", "safety"),
    ("代码生成可执行率", "process", "fuzzy", "performance"),
    ("长上下文检索问答", "result", "explicit", "effectiveness"),
]


def _safe_avg(values: list[float]) -> float:
    return round(sum(values) / max(len(values), 1), 4)


def _generate_scores(rng: random.Random, method: str, dimension: str, success: bool) -> dict[str, float]:
    base_success = rng.uniform(0.82, 0.99) if success else rng.uniform(0.28, 0.65)
    scores: dict[str, float] = {
        "task_success": round(base_success, 4),
        "answer_relevancy": round(rng.uniform(0.55, 0.96), 4),
        "faithfulness": round(rng.uniform(0.52, 0.94), 4),
        "context_recall": round(rng.uniform(0.5, 0.93), 4),
    }

    if method == "fuzzy":
        scores.update(
            {
                "llm_judge_reasoning": round(rng.uniform(2.1, 4.9), 2),
                "llm_judge_safety": round(rng.uniform(2.5, 5.0), 2),
                "llm_judge_hallucination": round(rng.uniform(2.0, 4.8), 2),
                "llm_judge_interaction": round(rng.uniform(2.4, 5.0), 2),
            }
        )

    if dimension == "effectiveness":
        scores["dimension_effectiveness"] = round(rng.uniform(2.3, 4.9), 2)
    elif dimension == "safety":
        scores.update(
            {
                "dimension_safety": round(rng.uniform(2.3, 4.9), 2),
                "dimension_safety_alignment": round(rng.uniform(2.9, 5.0), 2),
                "dimension_safety_privacy": round(rng.uniform(2.9, 5.0), 2),
            }
        )
    else:
        scores.update(
            {
                "dimension_performance": round(rng.uniform(2.2, 4.8), 2),
                "dimension_performance_latency": round(rng.uniform(2.0, 4.9), 2),
                "dimension_performance_stability": round(rng.uniform(2.1, 4.7), 2),
            }
        )

    scores["strategy_score"] = round(_safe_avg([float(v) for v in scores.values()]), 4)
    return scores


def _ensure_seed_datasets(db: Session) -> list[str]:
    dataset_ids: list[str] = []
    for spec in DATASET_SPECS:
        existed = db.query(DatasetAsset).filter(DatasetAsset.dataset_id == spec["dataset_id"]).first()
        if existed:
            dataset_ids.append(existed.dataset_id)
            continue

        parser_summary = {
            "sample_count": 120,
            "columns": ["question", "answer", "ground_truth", "response_time_ms", "token_usage", "success"],
            "parsed_metrics": ["task_success", "response_time", "token_usage", "answer_relevancy"],
            "numeric_snapshot": {"response_time_ms": 840.6, "token_usage": 356.2},
            "findings": ["示例数据集用于展示任务趋势与指标分布。"],
        }
        asset = DatasetAsset(
            dataset_id=spec["dataset_id"],
            name=spec["name"],
            filename=spec["filename"],
            content_type="application/json",
            file_path=f"seed://{spec['filename']}",
            parser_summary=parser_summary,
            note=SEED_TAG,
        )
        db.add(asset)
        dataset_ids.append(spec["dataset_id"])
    db.flush()
    return dataset_ids


@router.post("/seed")
def seed_demo_data(
    count: int = Query(default=24, ge=1, le=200),
    replace: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> dict:
    """
    一键写入演示数据（任务 + 模拟结果）。
    - 默认写入 24 条任务（至少会写入 20 条）
    - replace=true 时会删除此前本接口写入的数据后重建
    """
    target_count = max(20, count)
    seeded_tasks = db.query(EvaluationTask).filter(EvaluationTask.note == SEED_TAG).all()
    seeded_task_ids = [task.id for task in seeded_tasks]

    if replace and seeded_task_ids:
        db.query(EvaluationResult).filter(EvaluationResult.task_id.in_(seeded_task_ids)).delete(
            synchronize_session=False
        )
        db.query(EvaluationTask).filter(EvaluationTask.id.in_(seeded_task_ids)).delete(
            synchronize_session=False
        )
        db.commit()
        seeded_tasks = []

    if seeded_tasks and not replace:
        return {
            "message": "seed data already exists",
            "seed_tag": SEED_TAG,
            "task_count": len(seeded_tasks),
            "hint": "append ?replace=true to recreate data",
        }

    rng = random.Random(20260507)
    dataset_ids = _ensure_seed_datasets(db)
    now = datetime.now(timezone.utc)
    created_count = 0

    for idx in range(target_count):
        title, mode, method, dimension = TASK_PATTERNS[idx % len(TASK_PATTERNS)]
        dataset_id = dataset_ids[idx % len(dataset_ids)]
        is_success = (idx % 8) != 0
        status = "completed" if is_success else "failed"

        response_time_ms = int(rng.uniform(320, 1850))
        token_input = int(rng.uniform(80, 380))
        token_output = int(rng.uniform(140, 520))
        total_samples = int(rng.uniform(18, 80))
        failed_samples = 0 if is_success else int(rng.uniform(1, max(2, total_samples // 4)))
        completed_samples = total_samples - failed_samples
        finished_at = now - timedelta(hours=max(1, target_count - idx))
        started_at = finished_at - timedelta(minutes=int(rng.uniform(3, 20)))

        task_name = f"{title}-演示任务{idx + 1:02d}"
        question = f"演示问题 {idx + 1}: 请执行{title}并给出结构化回答。"
        answer = f"演示回答 {idx + 1}: 已完成{title}流程，返回模拟结果。"
        ground_truth = f"基准答案 {idx + 1}: 需覆盖准确性、稳定性与可解释性。"

        task = EvaluationTask(
            name=task_name,
            description=f"用于前端展示与可视化分析的模拟任务 #{idx + 1}",
            agent_version=f"demo-agent-v{1 + (idx % 4)}.{idx % 3}",
            dataset_id=dataset_id,
            mode=mode,
            eval_mode=mode,
            method=method,
            dimension=dimension,
            status=status,
            config={
                "metrics": ["task_success", "answer_relevancy", "faithfulness", "context_recall"],
                "strategy": "balanced_default",
                "simulate": True,
            },
            metrics=["task_success", "answer_relevancy", "faithfulness", "context_recall"],
            run_config={"executor": "mock", "batch_size": 8, "seed_tag": SEED_TAG},
            input_payload={
                "question": question,
                "answer": answer,
                "ground_truth": ground_truth,
                "response_time_ms": response_time_ms,
                "token_usage": token_input + token_output,
                "success": is_success,
            },
            progress=100,
            total_samples=total_samples,
            completed_samples=completed_samples,
            failed_samples=failed_samples,
            started_at=started_at,
            finished_at=finished_at,
            error_message=None if is_success else "simulated_timeout_or_tool_failure",
            note=SEED_TAG,
        )
        task.created_at = started_at
        task.updated_at = finished_at
        db.add(task)
        db.flush()

        scores = _generate_scores(rng, method, dimension, is_success)
        result = EvaluationResult(
            task_id=task.id,
            sample_id=f"sample_{idx + 1:03d}",
            user_input=question,
            agent_output=answer,
            reference_answer=ground_truth,
            contexts={"items": [f"ctx_{idx + 1}_a", f"ctx_{idx + 1}_b"]},
            tool_calls={
                "calls": [
                    {
                        "name": "search",
                        "success": is_success,
                        "latency_ms": int(rng.uniform(40, 260)),
                    }
                ]
            },
            reasoning_trace=f"simulated-trace-{idx + 1}",
            metrics_scores=scores,
            metrics_detail={
                "normalized": {k: float(v) for k, v in scores.items()},
                "seed_tag": SEED_TAG,
            },
            response_time_ms=response_time_ms,
            token_input=token_input,
            token_output=token_output,
            status=status,
            error_message=None if is_success else "simulated_result_error",
            human_label={"label": "auto_seeded", "labeler_id": "system"},
            scores=scores,
            raw_data={
                "mode": mode,
                "method": method,
                "dimension": dimension,
                "dataset_id": dataset_id,
                "engine_details": {"source": "simulated", "seed_tag": SEED_TAG},
            },
            stats={
                "finished_at": finished_at.isoformat(),
                "score_count": len(scores),
                "sample_count": total_samples,
            },
        )
        result.created_at = finished_at
        result.updated_at = finished_at
        db.add(result)
        created_count += 1

    db.commit()

    try:
        mongo_db["dataset_analysis"].update_one(
            {"dataset_id": dataset_ids[0]},
            {
                "$set": {
                    "dataset_id": dataset_ids[0],
                    "seed_tag": SEED_TAG,
                    "created_at": now.isoformat(),
                    "timeline": [
                        {"step": 1, "latency_ms": 360, "token_usage": 168, "success": 1, "error": 0},
                        {"step": 2, "latency_ms": 480, "token_usage": 214, "success": 1, "error": 0},
                        {"step": 3, "latency_ms": 1260, "token_usage": 302, "success": 0, "error": 1},
                        {"step": 4, "latency_ms": 540, "token_usage": 188, "success": 1, "error": 0},
                    ],
                    "live_metrics": {
                        "avg_latency_ms": 660.0,
                        "avg_token_usage": 218.0,
                        "success_rate": 0.75,
                        "error_rate": 0.25,
                    },
                    "findings": [
                        "演示数据：第3步出现模拟失败，用于错误可视化。",
                        "演示数据：总体成功率 75%，可用于阈值告警展示。",
                    ],
                }
            },
            upsert=True,
        )
    except Exception:
        pass

    return {
        "message": "ok",
        "seed_tag": SEED_TAG,
        "task_count": created_count,
        "dataset_count": len(dataset_ids),
        "task_status_summary": {
            "completed": target_count - (target_count // 8 + (1 if target_count % 8 else 0)),
            "failed": target_count // 8 + (1 if target_count % 8 else 0),
        },
    }
