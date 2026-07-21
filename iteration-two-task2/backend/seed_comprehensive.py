"""
Comprehensive demo data seeder — creates 24 diverse evaluation tasks with
varied metrics, strategies, evaluation modes, and simulated results.

Usage:
    docker compose cp seed_comprehensive.py backend:/app/
    docker compose exec backend python seed_comprehensive.py
"""

import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure we can import from the backend package
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.dataset import DatasetAsset
from app.models.strategy import EvaluationStrategy
from app.models.task import EvaluationTask
from app.models.result import EvaluationResult

SEED_TAG = "comprehensive-seed-v1"
NOW = datetime.now(timezone.utc)
RNG = random.Random(20260508)

# ── Dataset definitions ─────────────────────────────────────────────────
DATASETS = [
    {"dataset_id": "ds_chat_service_v2", "name": "在线客服对话数据集", "filename": "chat_service_v2.json"},
    {"dataset_id": "ds_tool_use_v3", "name": "工具调用评测集 V3", "filename": "tool_use_v3.json"},
    {"dataset_id": "ds_rag_knowledge_v2", "name": "RAG 知识库问答集", "filename": "rag_knowledge_v2.json"},
    {"dataset_id": "ds_safety_adv_v1", "name": "安全对抗测试集", "filename": "safety_adversarial_v1.json"},
    {"dataset_id": "ds_code_gen_v2", "name": "代码生成评测集 V2", "filename": "code_gen_v2.json"},
    {"dataset_id": "ds_long_context_v2", "name": "长上下文理解评测", "filename": "long_context_v2.json"},
    {"dataset_id": "ds_multi_turn_v1", "name": "多轮对话评测集", "filename": "multi_turn_v1.json"},
    {"dataset_id": "ds_translation_v1", "name": "翻译质量评测集", "filename": "translation_v1.json"},
]

# ── Strategy definitions ─────────────────────────────────────────────────
STRATEGIES = [
    {
        "name": "balanced_default",
        "weights": {"effectiveness": 0.4, "safety": 0.3, "performance": 0.3},
        "metrics": ["task_success", "answer_relevancy", "response_time"],
        "description": "均衡策略 — 效果、安全、性能加权均衡",
    },
    {
        "name": "effectiveness_first",
        "weights": {"effectiveness": 0.6, "safety": 0.2, "performance": 0.2},
        "metrics": ["task_success", "faithfulness", "answer_relevancy", "context_recall"],
        "description": "效果优先 — 侧重回答质量与事实一致性",
    },
    {
        "name": "safety_first",
        "weights": {"effectiveness": 0.15, "safety": 0.7, "performance": 0.15},
        "metrics": ["llm_judge_safety", "llm_judge_hallucination", "task_success"],
        "description": "安全优先 — 侧重安全合规、幻觉检测",
    },
    {
        "name": "performance_first",
        "weights": {"effectiveness": 0.2, "safety": 0.1, "performance": 0.7},
        "metrics": ["response_time", "token_usage", "tool_accuracy", "task_success"],
        "description": "性能优先 — 侧重响应延迟与工具调用效率",
    },
    {
        "name": "comprehensive",
        "weights": {"effectiveness": 0.35, "safety": 0.35, "performance": 0.3},
        "metrics": ["task_success", "answer_relevancy", "faithfulness", "llm_judge_reasoning", "llm_judge_safety"],
        "description": "综合评估 — 全维度深度评估",
    },
    {
        "name": "lightweight",
        "weights": {"effectiveness": 0.5, "safety": 0.0, "performance": 0.5},
        "metrics": ["task_success", "response_time"],
        "description": "轻量快速 — 仅显式指标，适合日常回归",
    },
]

# ── Task repertoire ──────────────────────────────────────────────────────
# Each task spec defines a unique evaluation scenario.
TASK_SPECS = [
    # (name, mode, method, dimension, strategy_name, metrics_list, dataset_idx, samples)
    ("客服多轮对话质量评估", "result", "explicit", "effectiveness", "balanced_default",
     ["task_success", "answer_relevancy", "response_time"], 0, 20),
    ("工具调用准确率评测", "result", "explicit", "effectiveness", "effectiveness_first",
     ["task_success", "tool_accuracy", "response_time"], 1, 15),
    ("RAG 知识库问答事实一致性", "result", "fuzzy", "effectiveness", "balanced_default",
     ["faithfulness", "answer_relevancy", "context_recall", "task_success"], 2, 25),
    ("Agent 安全合规深度检查", "result", "fuzzy", "safety", "safety_first",
     ["llm_judge_safety", "llm_judge_hallucination", "task_success"], 3, 18),
    ("长上下文检索问答质量", "result", "explicit", "effectiveness", "effectiveness_first",
     ["context_recall", "answer_relevancy", "faithfulness"], 5, 22),
    ("多轮对话推理链评估", "process", "fuzzy", "effectiveness", "comprehensive",
     ["llm_judge_reasoning", "task_success", "llm_judge_interaction"], 6, 12),
    ("代码生成可执行率测试", "process", "explicit", "performance", "performance_first",
     ["task_success", "response_time", "token_usage"], 4, 20),
    ("Agent 幻觉检测专项", "result", "fuzzy", "effectiveness", "safety_first",
     ["llm_judge_hallucination", "faithfulness", "task_success"], 2, 16),
    ("工具调用链路稳定性测试", "process", "explicit", "performance", "performance_first",
     ["tool_accuracy", "response_time", "task_success"], 1, 14),
    ("智能问答交互体验评估", "result", "fuzzy", "effectiveness", "comprehensive",
     ["llm_judge_interaction", "llm_judge_reasoning", "task_success"], 0, 20),
    ("NL2SQL 生成准确率评测", "result", "explicit", "effectiveness", "effectiveness_first",
     ["task_success", "response_time"], 4, 18),
    ("Agent 端到端性能基准", "process", "explicit", "performance", "performance_first",
     ["response_time", "token_usage", "task_success"], 1, 30),
    ("对抗性提示安全测试", "result", "fuzzy", "safety", "safety_first",
     ["llm_judge_safety", "task_success", "llm_judge_hallucination"], 3, 15),
    ("多语言翻译质量评估", "result", "fuzzy", "effectiveness", "balanced_default",
     ["llm_judge_reasoning", "answer_relevancy", "task_success"], 7, 12),
    ("文档问答召回率专项", "result", "explicit", "effectiveness", "effectiveness_first",
     ["context_recall", "faithfulness", "task_success"], 5, 20),
    ("Agent 工具链端到端综合测试", "process", "fuzzy", "performance", "comprehensive",
     ["task_success", "response_time", "tool_accuracy", "llm_judge_reasoning"], 1, 10),
    ("隐私数据泄露检测", "result", "fuzzy", "safety", "safety_first",
     ["llm_judge_safety", "llm_judge_hallucination"], 3, 14),
    ("常规回归 — 轻量级评测", "result", "explicit", "effectiveness", "lightweight",
     ["task_success", "response_time"], 0, 25),
    ("复杂推理链深度分析", "process", "fuzzy", "effectiveness", "comprehensive",
     ["llm_judge_reasoning", "task_success", "llm_judge_interaction"], 6, 8),
    ("全维度综合评测", "result_and_process", "fuzzy", "effectiveness", "comprehensive",
     ["task_success", "answer_relevancy", "faithfulness", "llm_judge_reasoning", "llm_judge_safety"], 2, 16),
    ("多 Agent 协作效率评估", "process", "explicit", "performance", "performance_first",
     ["response_time", "tool_accuracy", "task_success"], 1, 12),
    ("非结构化数据理解评测", "result", "explicit", "effectiveness", "lightweight",
     ["task_success", "response_time"], 5, 20),
    ("行业知识问答准确率", "result", "fuzzy", "effectiveness", "effectiveness_first",
     ["answer_relevancy", "faithfulness", "context_recall", "task_success"], 2, 24),
    ("会话式 AI 安全红线测试", "result", "fuzzy", "safety", "safety_first",
     ["llm_judge_safety", "task_success"], 3, 10),
]

AGENT_VERSIONS = ["agent-chat-v2.1", "agent-tool-v3.0", "agent-rag-v1.5", "agent-code-v2.0", "agent-chat-v1.8"]


# ── Score simulation helpers ──────────────────────────────────────────────

def _simulate_scores(task_spec: tuple, success_ratio: float) -> dict[str, float]:
    """Generate simulated scores based on task configuration."""
    _, mode, method, dimension, strategy_name, metrics, _, _ = task_spec
    scores: dict[str, float] = {}

    # Base explicit metrics
    if "task_success" in metrics:
        scores["task_success"] = round(RNG.uniform(0.55, 0.98) * success_ratio, 4)
    if "response_time" in metrics:
        # simulated normalized score (lower is better → invert)
        rt_ms = RNG.uniform(120, 3200)
        scores["response_time"] = round(max(0, 1.0 - rt_ms / 5000), 4)
    if "token_usage" in metrics:
        tu = RNG.uniform(80, 600)
        scores["token_usage"] = round(max(0, 1.0 - tu / 1000), 4)
    if "tool_accuracy" in metrics:
        scores["tool_accuracy"] = round(RNG.uniform(0.4, 0.96) * success_ratio, 4)

    # Ragas metrics (when explicit + effectiveness)
    if "answer_relevancy" in metrics:
        scores["answer_relevancy"] = round(RNG.uniform(0.45, 0.95), 4)
    if "faithfulness" in metrics:
        scores["faithfulness"] = round(RNG.uniform(0.40, 0.93), 4)
    if "context_recall" in metrics:
        scores["context_recall"] = round(RNG.uniform(0.35, 0.92), 4)

    # LLM Judge metrics (when method == fuzzy)
    if method == "fuzzy":
        if "llm_judge_reasoning" in metrics:
            scores["llm_judge_reasoning"] = round(RNG.uniform(1.8, 4.9), 2)
        if "llm_judge_safety" in metrics:
            scores["llm_judge_safety"] = round(RNG.uniform(2.0, 5.0), 2)
        if "llm_judge_hallucination" in metrics:
            scores["llm_judge_hallucination"] = round(RNG.uniform(1.5, 4.8), 2)
        if "llm_judge_interaction" in metrics:
            scores["llm_judge_interaction"] = round(RNG.uniform(2.2, 5.0), 2)

    # Dimension plugin scores
    if dimension == "effectiveness":
        scores["dimension_effectiveness"] = round(RNG.uniform(2.0, 4.9), 2)
    elif dimension == "safety":
        scores["dimension_safety"] = round(RNG.uniform(2.0, 5.0), 2)
        scores["dimension_safety_alignment"] = round(RNG.uniform(2.5, 5.0), 2)
        scores["dimension_safety_privacy"] = round(RNG.uniform(2.5, 5.0), 2)
    elif dimension == "performance":
        scores["dimension_performance"] = round(RNG.uniform(1.8, 4.8), 2)
        scores["dimension_performance_latency"] = round(RNG.uniform(1.5, 4.9), 2)
        scores["dimension_performance_stability"] = round(RNG.uniform(1.8, 4.7), 2)

    # Strategy score (weighted average of numeric values)
    if scores:
        scores["strategy_score"] = round(
            sum(float(v) for v in scores.values()) / len(scores), 4
        )

    return scores


def _get_judge_config(method: str, metrics: list[str]) -> dict:
    """Generate judge config based on method and metrics."""
    base = {"provider": "openai", "model": "gpt-4o-mini", "temperature": 0}
    if method == "fuzzy":
        if any("safety" in m for m in metrics):
            return {**base, "prompt_template": "safety_eval_v2", "threshold": 3.0}
        if any("reasoning" in m for m in metrics):
            return {**base, "prompt_template": "reasoning_eval_v1", "threshold": 2.5}
        return {**base, "prompt_template": "general_fuzzy_v1", "threshold": 2.0}
    return {}


def _get_run_config(task_spec: tuple) -> dict:
    _, mode, method, dimension, strategy_name, metrics, _, _ = task_spec
    return {
        "executor": "mock",
        "batch_size": RNG.choice([4, 8, 16]),
        "timeout_seconds": RNG.choice([30, 60, 120]),
        "enable_cache": RNG.choice([True, False]),
        "seed_tag": SEED_TAG,
    }


# ── Main seeding logic ────────────────────────────────────────────────────

def seed():
    db = SessionLocal()
    try:
        # ── 1. Create datasets ──
        print("Creating datasets...")
        created_datasets = []
        for spec in DATASETS:
            existed = db.query(DatasetAsset).filter(
                DatasetAsset.dataset_id == spec["dataset_id"]
            ).first()
            if existed:
                created_datasets.append(existed)
                continue
            asset = DatasetAsset(
                dataset_id=spec["dataset_id"],
                name=spec["name"],
                filename=spec["filename"],
                content_type="application/json",
                file_path=f"seed://{spec['filename']}",
                parser_summary={
                    "sample_count": RNG.randint(40, 200),
                    "columns": ["question", "answer", "ground_truth", "response_time_ms", "token_usage", "success"],
                    "parsed_metrics": ["task_success", "response_time", "token_usage", "answer_relevancy"],
                    "numeric_snapshot": {"response_time_ms": round(RNG.uniform(400, 1200), 1), "token_usage": RNG.randint(200, 500)},
                    "findings": [f"{spec['name']} — 用于多维评测展示。"],
                },
                note=SEED_TAG,
            )
            db.add(asset)
            db.flush()
            created_datasets.append(asset)
            print(f"  + Dataset: {spec['dataset_id']}")

        # ── 2. Create strategies ──
        print("Creating strategies...")
        for spec in STRATEGIES:
            existed = db.query(EvaluationStrategy).filter(
                EvaluationStrategy.name == spec["name"]
            ).first()
            if existed:
                continue
            strategy = EvaluationStrategy(
                name=spec["name"],
                weights=spec["weights"],
                metrics=spec["metrics"],
                description=spec["description"],
            )
            db.add(strategy)
            db.flush()
            print(f"  + Strategy: {spec['name']}")

        # ── 3. Create tasks + results ──
        print("Creating tasks and results...")
        created_tasks = 0

        for idx, spec in enumerate(TASK_SPECS):
            name, mode, method, dimension, strategy_name, metrics, ds_idx, sample_count = spec

            dataset_id = DATASETS[ds_idx]["dataset_id"]
            agent_version = RNG.choice(AGENT_VERSIONS)
            is_successful = (idx % 7) != 0  # ~85% success rate
            status = "completed" if is_successful else "failed"
            success_ratio = 0.85 if is_successful else 0.45

            # Stagger creation times
            hours_ago = max(1, len(TASK_SPECS) - idx) * 3 + RNG.randint(0, 6)
            finished_at = NOW - timedelta(hours=hours_ago)
            started_at = finished_at - timedelta(minutes=RNG.randint(5, 45))

            failed = 0 if is_successful else RNG.randint(1, max(2, sample_count // 3))
            completed = sample_count - failed

            task_name = f"{name}"

            # Generate a demo question/answer
            question = f"评测场景 #{idx + 1}: 针对「{name}」执行自动化评估，请根据配置参数输出结构化结果。"
            answer = f"已完成「{name}」评测流程，共 {sample_count} 个样本。指标分布详见 scores。"

            task = EvaluationTask(
                name=task_name,
                description=f"场景化评测任务 #{idx + 1} — {name}。模式: {mode}, 方法: {method}, 维度: {dimension}",
                agent_id=RNG.choice([None, 1, 2, 3]),
                agent_version=agent_version,
                dataset_id=dataset_id,
                mode=mode,
                eval_mode=mode,
                method=method,
                dimension=dimension,
                status=status,
                config={
                    "metrics": metrics,
                    "strategy": strategy_name,
                    "enable_process_trace": mode in ("process", "result_and_process"),
                },
                judge_config=_get_judge_config(method, metrics),
                run_config=_get_run_config(spec),
                metrics=metrics,
                input_payload={
                    "question": question,
                    "answer": answer,
                    "ground_truth": f"基准答案 {idx + 1}: 需覆盖准确性、稳定性、安全性。",
                    "response_time_ms": RNG.randint(200, 2800),
                    "token_usage": RNG.randint(100, 800),
                    "success": is_successful,
                },
                progress=100,
                total_samples=sample_count,
                completed_samples=completed,
                failed_samples=failed,
                started_at=started_at,
                finished_at=finished_at,
                error_message=None if is_successful else f"模拟失败: {RNG.choice(['tool_timeout', 'api_error', 'invalid_response'])}",
                note=SEED_TAG,
            )
            task.created_at = started_at
            task.updated_at = finished_at
            db.add(task)
            db.flush()

            # ── 4. Create result records for this task ──
            result_count = max(5, min(sample_count, 25))
            for ridx in range(result_count):
                r_success = (ridx % 5) != 0  # 80% individual success
                scores = _simulate_scores(spec, 0.9 if r_success else 0.4)
                result_rt = RNG.randint(80, 3500)

                result = EvaluationResult(
                    task_id=task.id,
                    sample_id=f"{task.id}_sample_{ridx + 1:03d}",
                    user_input=f"评测输入 #{ridx + 1} for task #{idx + 1}",
                    agent_output=f"Agent 输出 #{ridx + 1}: {RNG.choice(['正常完成', '部分响应', '拒绝回答', '超时'])}",
                    reference_answer=f"参考答案 #{ridx + 1}: 预期正确输出",
                    contexts={"items": [f"ctx_{idx}_{ridx}_a", f"ctx_{idx}_{ridx}_b"]},
                    tool_calls={
                        "calls": [
                            {"name": RNG.choice(["search", "calculator", "sql_query", "code_execute", "weather_api"]),
                             "success": r_success,
                             "latency_ms": RNG.randint(30, 500)}
                        ]
                    },
                    reasoning_trace=f"trace-{task.id}-{ridx}" if mode in ("process", "result_and_process") else None,
                    metrics_scores=scores,
                    metrics_detail={"normalized": {k: float(v) for k, v in scores.items()}, "seed_tag": SEED_TAG},
                    response_time_ms=result_rt,
                    token_input=RNG.randint(50, 400),
                    token_output=RNG.randint(80, 600),
                    status="completed" if r_success else "failed",
                    error_message=None if r_success else f"sample_error_{RNG.randint(1, 5)}",
                    human_label={"label": "auto_seeded", "labeler_id": "system"},
                    scores=scores,
                    raw_data={
                        "mode": mode,
                        "method": method,
                        "dimension": dimension,
                        "dataset_id": dataset_id,
                        "engine_details": {"source": "comprehensive_seed", "seed_tag": SEED_TAG},
                    },
                    stats={
                        "finished_at": finished_at.isoformat(),
                        "score_count": len(scores),
                        "sample_count": result_count,
                    },
                )
                result.created_at = finished_at - timedelta(seconds=RNG.randint(0, 300))
                result.updated_at = finished_at
                db.add(result)

            created_tasks += 1
            print(f"  + Task #{idx + 1:02d}: 「{task_name}」 ({mode}/{method}/{dimension}) → {result_count} results")

        db.commit()
        print(f"\n✅ Seeding complete! Created {created_tasks} tasks with simulated results.")
        print(f"   Strategies: {len(STRATEGIES)}, Datasets: {len(DATASETS)}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
