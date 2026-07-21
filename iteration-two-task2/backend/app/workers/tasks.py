import logging

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.task import EvaluationTask
from app.services.evaluation_engine import EvaluationEngine
from app.services.llm_judge_service import build_context, run_llm_judge, save_judge_report
from app.services.mode_eval_service import ModeEvalService

logger = logging.getLogger(__name__)


@celery_app.task(name="execute_evaluation_task")
def execute_evaluation_task(task_id: int) -> dict:
    db = SessionLocal()
    try:
        task = db.get(EvaluationTask, task_id)
        if task is None:
            return {"task_id": task_id, "status": "failed", "message": "task not found"}

        result = EvaluationEngine.execute(db, task)
        # Auto-trigger LLM judge after successful evaluation
        try:
            _trigger_task_llm_judge(task_id)
        except Exception as judge_exc:
            logger.warning("LLM judge auto-trigger failed for task %s: %s", task_id, judge_exc)
        return {"task_id": task_id, "status": "completed", "result_id": result.id}
    except Exception as exc:
        task = db.get(EvaluationTask, task_id)
        if task:
            task.status = "failed"
            db.commit()
        return {"task_id": task_id, "status": "failed", "message": str(exc)}
    finally:
        db.close()


@celery_app.task(name="process_offline_eval_job", bind=True, max_retries=3, default_retry_delay=5)
def process_offline_eval_job(self, job_id: str) -> dict:
    """Process an offline evaluation job asynchronously via Celery."""
    try:
        ModeEvalService.process_offline_job(job_id)
        _trigger_offline_llm_judge(job_id)
        return {"job_id": job_id, "status": "completed"}
    except Exception as exc:
        try:
            self.retry(exc=exc)
        except Exception:
            return {"job_id": job_id, "status": "failed", "error": str(exc)}


@celery_app.task(name="process_batch_eval_job", bind=True, max_retries=3, default_retry_delay=10)
def process_batch_eval_job(self, job_id: str) -> dict:
    """Process a batch evaluation job asynchronously via Celery with chunked processing."""
    try:
        ModeEvalService.process_batch_job(job_id)
        _trigger_batch_llm_judge(job_id)
        return {"job_id": job_id, "status": "completed"}
    except Exception as exc:
        try:
            self.retry(exc=exc)
        except Exception:
            return {"job_id": job_id, "status": "failed", "error": str(exc)}


# ---------------------------------------------------------------------------
# LLM Judge auto-trigger helpers  (fire-and-forget, errors are logged only)
# ---------------------------------------------------------------------------

def _trigger_task_llm_judge(task_id: int) -> None:
    """Run LLM judge on a completed task evaluation in the background."""
    from sqlalchemy import select
    from app.models.result import EvaluationResult

    db = SessionLocal()
    try:
        task = db.get(EvaluationTask, task_id)
        if task is None:
            logger.info("LLM judge: task %s not found, skipping", task_id)
            return
        if task.status != "completed":
            logger.info("LLM judge: task %s status is '%s', not 'completed', skipping", task_id, task.status)
            return

        results = db.scalars(
            select(EvaluationResult).where(EvaluationResult.task_id == task_id)
        ).all()

        logger.info("LLM judge: loaded %d results for task %s", len(results), task_id)

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
        logger.info("LLM judge assessment generated for task %s: status=%s, score=%s",
                     task_id, assessment.get("status"), assessment.get("overall_score"))
        save_judge_report("task", str(task_id), context, assessment)
        logger.info("LLM judge report saved for task %s", task_id)
    except Exception as exc:
        logger.warning("LLM judge auto-trigger for task %s failed: %s", task_id, exc, exc_info=True)
    finally:
        db.close()


def _trigger_offline_llm_judge(job_id: str) -> None:
    """Run LLM judge on a completed offline job."""
    from app.core.redis import redis_client

    try:
        key = f"mode:offline:job:{job_id}"
        job = redis_client.get_json(key)
        if job is None or job.get("status") != "completed":
            return
        report = job.get("report")
        if not report:
            return

        scores = report.get("scores", {})
        metrics = report.get("metrics", {})

        context = build_context(
            scores=scores,
            metrics=metrics,
            trace_summary={
                "step_count": metrics.get("step_count"),
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
    except Exception as exc:
        logger.warning("LLM judge auto-trigger for offline job %s failed: %s", job_id, exc)


def _trigger_batch_llm_judge(job_id: str) -> None:
    """Run LLM judge on a completed batch job."""
    from app.core.redis import redis_client

    try:
        key = f"mode:batch:job:{job_id}"
        job = redis_client.get_json(key)
        if job is None:
            logger.info("LLM judge: batch job %s not found, skipping", job_id)
            return
        if job.get("status") != "completed":
            logger.info("LLM judge: batch job %s status is '%s', not 'completed', skipping", job_id, job.get("status"))
            return
        summary = job.get("summary")
        if not summary:
            logger.info("LLM judge: batch job %s has no summary, skipping", job_id)
            return

        avg_scores = summary.get("average_scores", {})
        root_cause_dist = summary.get("root_cause_distribution", {})

        # Look up strategy info if a strategy was selected
        strategy_info = None
        strategy_name = job.get("strategy_name")
        if strategy_name:
            try:
                from sqlalchemy import select
                from app.models.strategy import EvaluationStrategy
                db_lookup = SessionLocal()
                try:
                    stmt = select(EvaluationStrategy).where(EvaluationStrategy.name == strategy_name)
                    strategy = db_lookup.scalar(stmt)
                    if strategy:
                        strategy_info = {
                            "config": {"weights": strategy.weights,
                                       "dimension_weights": strategy.dimension_weights},
                            "metrics": strategy.metrics,
                            "weights": strategy.weights,
                            "dimension_weights": strategy.dimension_weights,
                            "strategy_name": strategy_name,
                        }
                finally:
                    db_lookup.close()
            except Exception as exc:
                logger.warning("LLM judge: failed to look up strategy '%s': %s", strategy_name, exc)

        context = build_context(
            scores=avg_scores,
            metrics={
                "total_traces": summary.get("total_traces"),
                "success_rate": summary.get("success_rate"),
            },
            task_info={
                "mode": "batch",
                "dataset_id": summary.get("dataset_id"),
                "strategy_name": strategy_name,
            },
            samples_summary={
                "total_traces": summary.get("total_traces"),
                "success_rate": summary.get("success_rate"),
                "root_cause_distribution": root_cause_dist,
            },
            strategy_info=strategy_info,
        )

        assessment = run_llm_judge(context)
        logger.info("LLM judge assessment for batch job %s: status=%s, score=%s",
                     job_id, assessment.get("status"), assessment.get("overall_score"))
        save_judge_report("batch_job", job_id, context, assessment)

        # Also save under the associated task if this job was linked to one
        eval_task_id = job.get("eval_task_id")
        if eval_task_id is not None:
            save_judge_report("task", str(eval_task_id), context, assessment)
            logger.info("LLM judge report saved for task %s (from batch job %s)", eval_task_id, job_id)
    except Exception as exc:
        logger.warning("LLM judge auto-trigger for batch job %s failed: %s", job_id, exc, exc_info=True)
