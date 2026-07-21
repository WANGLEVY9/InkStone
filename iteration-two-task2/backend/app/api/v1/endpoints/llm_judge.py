"""API endpoints for LLM-as-a-Judge evaluation."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.database import SessionLocal, get_db, mongo_db
from app.models.result import EvaluationResult
from app.models.task import EvaluationTask
from app.services.llm_judge_service import (
    build_context,
    load_judge_report,
    run_llm_judge,
    save_judge_report,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/judge/task/{task_id}")
def trigger_task_llm_judge(task_id: int) -> dict:
    """Trigger LLM-as-a-Judge on a completed task-based evaluation."""
    db = next(get_db())
    try:
        task = db.get(EvaluationTask, task_id)
        if task is None:
            raise HTTPException(404, "task not found")
        if task.status != "completed":
            raise HTTPException(400, "task is not completed yet")

        results = db.scalars(
            select(EvaluationResult).where(EvaluationResult.task_id == task_id)
        ).all()

        # Aggregate scores if there are results; otherwise pass empty data.
        all_scores: dict[str, list[float]] = {}
        for r in results:
            for k, v in (r.scores or {}).items():
                all_scores.setdefault(k, []).append(float(v))

        avg_scores = {k: round(sum(v) / len(v), 4) for k, v in all_scores.items()} if all_scores else {}

        response_times = [r.response_time_ms for r in results if r.response_time_ms is not None]
        token_inputs = [r.token_input for r in results if r.token_input is not None]
        token_outputs = [r.token_output for r in results if r.token_output is not None]
        success_count = sum(1 for r in results if r.status == "success")
        total_count = len(results)

        context = build_context(
            scores=avg_scores,
            metrics={
                "avg_response_time_ms": round(sum(response_times) / len(response_times), 2) if response_times else None,
                "avg_token_input": round(sum(token_inputs) / len(token_inputs), 2) if token_inputs else None,
                "avg_token_output": round(sum(token_outputs) / len(token_outputs), 2) if token_outputs else None,
                "success_rate": round(success_count / total_count, 4) if total_count else 0,
                "total_results": total_count,
            },
            task_info={
                "name": task.name,
                "mode": task.mode,
                "method": task.method,
                "dimension": task.dimension,
                "total_samples": task.total_samples,
                "completed_samples": task.completed_samples,
                "failed_samples": task.failed_samples,
            },
            samples_summary={
                "total": total_count,
                "success": success_count,
                "failed": total_count - success_count,
            },
            strategy_info={
                "config": task.config,
                "metrics": task.metrics,
                "judge_config": task.judge_config,
                "weights": (task.config or {}).get("weights", {}),
                "dimension_weights": (task.config or {}).get("dimension_weights", {}),
            },
        )

        assessment = run_llm_judge(context)
        save_judge_report("task", str(task_id), context, assessment)
        return {"ref_type": "task", "ref_id": str(task_id), "assessment": assessment}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("LLM judge trigger failed unexpectedly: %s", exc, exc_info=True)
        raise HTTPException(500, detail=f"LLM judge error: {exc}") from exc
    finally:
        db.close()


@router.post("/judge/offline/{job_id}")
def trigger_offline_llm_judge(job_id: str) -> dict:
    """Trigger LLM-as-a-Judge on an offline evaluation job."""
    from app.core.redis import redis_client

    key = f"mode:offline:job:{job_id}"
    job = redis_client.get_json(key)
    if job is None:
        raise HTTPException(404, "offline job not found")
    if job.get("status") != "completed":
        raise HTTPException(400, "job is not completed yet")
    report = job.get("report")
    if not report:
        raise HTTPException(404, "no report found for this job")

    scores = report.get("scores", {})
    metrics = report.get("metrics", {})

    context = build_context(
        scores=scores,
        metrics=metrics,
        trace_summary={
            "step_count": metrics.get("step_count"),
            "total_duration_ms": metrics.get("total_duration"),
            "tool_call_count": metrics.get("tool_call_count"),
            "dangerous_call_count": metrics.get("dangerous_call_count"),
            "success": report.get("success"),
        },
        task_info={
            "mode": "offline",
            "session_id": report.get("session_id"),
            "task": report.get("task"),
        },
    )

    assessment = run_llm_judge(context)
    save_judge_report("offline_job", job_id, context, assessment)
    return {"ref_type": "offline_job", "ref_id": job_id, "assessment": assessment}


@router.post("/judge/batch/{job_id}")
def trigger_batch_llm_judge(job_id: str) -> dict:
    """Trigger LLM-as-a-Judge on a batch evaluation job."""
    from app.core.redis import redis_client

    key = f"mode:batch:job:{job_id}"
    job = redis_client.get_json(key)
    if job is None:
        raise HTTPException(404, "batch job not found")
    if job.get("status") != "completed":
        raise HTTPException(400, "job is not completed yet")
    summary = job.get("summary")
    if not summary:
        raise HTTPException(404, "no summary found for this job")

    avg_scores = summary.get("average_scores", {})
    root_cause_dist = summary.get("root_cause_distribution", {})

    context = build_context(
        scores=avg_scores,
        metrics={
            "total_traces": summary.get("total_traces"),
            "success_rate": summary.get("success_rate"),
        },
        task_info={
            "mode": "batch",
            "dataset_id": summary.get("dataset_id"),
            "strategy_name": job.get("strategy_name"),
        },
        samples_summary={
            "total_traces": summary.get("total_traces"),
            "success_rate": summary.get("success_rate"),
            "root_cause_distribution": root_cause_dist,
        },
    )

    assessment = run_llm_judge(context)
    save_judge_report("batch_job", job_id, context, assessment)
    return {"ref_type": "batch_job", "ref_id": job_id, "assessment": assessment}


@router.get("/judge/result/{ref_type}/{ref_id}")
def get_judge_result(ref_type: str, ref_id: str) -> dict:
    """Retrieve a previously computed LLM judge result."""
    doc = load_judge_report(ref_type, ref_id)
    if doc is None:
        raise HTTPException(404, "LLM judge result not found. Trigger evaluation first via POST.")
    return doc
