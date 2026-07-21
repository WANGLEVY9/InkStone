"""
Comprehensive demo data seeder — Part 2: adds 30 new evaluation tasks with
novel scenarios not covered in Part 1 (finance, healthcare, legal, education,
code review, creative, etc.)

Usage:
    docker compose cp seed_comprehensive_p2.py backend:/app/
    docker compose exec backend python seed_comprehensive_p2.py
"""

import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.dataset import DatasetAsset
from app.models.strategy import EvaluationStrategy
from app.models.task import EvaluationTask
from app.models.result import EvaluationResult

SEED_TAG = "comprehensive-seed-v2"
NOW = datetime.now(timezone.utc)
RNG = random.Random(20260509)

# ── 8 new datasets ───────────────────────────────────────────────────────
NEW_DATASETS = [
    {"dataset_id": "ds_finance_qa_v1", "name": "金融合规问答集", "filename": "finance_qa_v1.json"},
    {"dataset_id": "ds_medical_diag_v1", "name": "医疗诊断对话集", "filename": "medical_diag_v1.json"},
    {"dataset_id": "ds_legal_contract_v1", "name": "法律合同审查集", "filename": "legal_contract_v1.json"},
    {"dataset_id": "ds_edu_exam_v1", "name": "教育考试问答集", "filename": "edu_exam_v1.json"},
    {"dataset_id": "ds_code_review_v1", "name": "代码审查评测集", "filename": "code_review_v1.json"},
    {"dataset_id": "ds_creative_write_v1", "name": "创意写作评测集", "filename": "creative_write_v1.json"},
    {"dataset_id": "ds_reasoning_v1", "name": "逻辑推理评测集", "filename": "reasoning_v1.json"},
    {"dataset_id": "ds_content_mod_v1", "name": "内容审核评测集", "filename": "content_moderation_v1.json"},
]

# ── 4 new strategies ────────────────────────────────────────────────────
NEW_STRATEGIES = [
    {
        "name": "accuracy_focused",
        "weights": {"effectiveness": 0.7, "safety": 0.15, "performance": 0.15},
        "metrics": ["task_success", "faithfulness", "llm_judge_reasoning"],
        "description": "精准优先 — 侧重任务完成准确度与推理正确性",
    },
    {
        "name": "safety_heavy",
        "weights": {"effectiveness": 0.1, "safety": 0.8, "performance": 0.1},
        "metrics": ["llm_judge_safety", "llm_judge_hallucination"],
        "description": "安全重载 — 极端侧重安全合规，适用于红线场景",
    },
    {
        "name": "latency_sensitive",
        "weights": {"effectiveness": 0.2, "safety": 0.1, "performance": 0.7},
        "metrics": ["response_time", "token_usage", "task_success"],
        "description": "延迟敏感 — 适用于实时交互场景",
    },
    {
        "name": "creative_quality",
        "weights": {"effectiveness": 0.5, "safety": 0.3, "performance": 0.2},
        "metrics": ["llm_judge_interaction", "llm_judge_reasoning", "task_success"],
        "description": "创意质量 — 侧重交互体验与内容创新性",
    },
]

# ── 30 new task specs ──────────────────────────────────────────────────
TASK_SPECS = [
    # (name, mode, method, dimension, strategy_name, metrics_list, dataset_idx)
    # === Financial & Compliance ===
    ("金融合规问答准确率评估", "result", "explicit", "effectiveness", "accuracy_focused",
     ["task_success", "faithfulness", "response_time"], 0),
    ("金融风控场景安全审查", "result", "fuzzy", "safety", "safety_heavy",
     ["llm_judge_safety", "llm_judge_hallucination", "task_success"], 0),
    ("金融报告生成效率评测", "process", "explicit", "performance", "latency_sensitive",
     ["response_time", "token_usage", "task_success"], 0),

    # === Medical & Healthcare ===
    ("医疗诊断建议准确性", "result", "explicit", "effectiveness", "accuracy_focused",
     ["task_success", "faithfulness", "answer_relevancy"], 1),
    ("医疗隐私合规检查", "result", "fuzzy", "safety", "safety_heavy",
     ["llm_judge_safety", "llm_judge_hallucination"], 1),
    ("医疗问诊对话流畅度", "result", "fuzzy", "effectiveness", "creative_quality",
     ["llm_judge_interaction", "task_success", "answer_relevancy"], 1),

    # === Legal ===
    ("法律合同条款审查准确率", "result", "explicit", "effectiveness", "accuracy_focused",
     ["task_success", "faithfulness", "context_recall"], 2),
    ("法律文书生成合规性", "result", "fuzzy", "safety", "safety_first",
     ["llm_judge_safety", "llm_judge_reasoning", "task_success"], 2),
    ("法律案例检索相关性", "result", "explicit", "effectiveness", "effectiveness_first",
     ["context_recall", "answer_relevancy", "faithfulness"], 2),

    # === Education ===
    ("教育试题批改准确率", "result", "explicit", "effectiveness", "accuracy_focused",
     ["task_success", "answer_relevancy", "response_time"], 3),
    ("教学对话推理质量", "process", "fuzzy", "effectiveness", "comprehensive",
     ["llm_judge_reasoning", "llm_judge_interaction", "task_success"], 3),
    ("个性化学习推荐效果", "result", "fuzzy", "effectiveness", "balanced_default",
     ["answer_relevancy", "task_success", "llm_judge_interaction"], 3),

    # === Code & Engineering ===
    ("代码审查缺陷检出率", "result", "explicit", "effectiveness", "accuracy_focused",
     ["task_success", "tool_accuracy", "response_time"], 4),
    ("代码重构安全合规检测", "result", "fuzzy", "safety", "safety_heavy",
     ["llm_judge_safety", "llm_judge_hallucination", "task_success"], 4),
    ("CI/CD 流水线集成效率", "process", "explicit", "performance", "performance_first",
     ["response_time", "tool_accuracy", "task_success"], 4),

    # === Reasoning & Logic ===
    ("数学推理题解答准确率", "result", "explicit", "effectiveness", "accuracy_focused",
     ["task_success", "faithfulness", "response_time"], 6),
    ("逻辑谬误检测评估", "result", "fuzzy", "effectiveness", "comprehensive",
     ["llm_judge_reasoning", "task_success", "faithfulness"], 6),
    ("多步推理过程评估", "process", "fuzzy", "effectiveness", "comprehensive",
     ["llm_judge_reasoning", "task_success", "llm_judge_interaction"], 6),

    # === Creative Writing ===
    ("创意故事生成质量", "result", "fuzzy", "effectiveness", "creative_quality",
     ["llm_judge_interaction", "llm_judge_reasoning", "task_success"], 5),
    ("营销文案风格一致性", "result", "fuzzy", "effectiveness", "creative_quality",
     ["llm_judge_interaction", "task_success", "answer_relevancy"], 5),
    ("多风格内容生成适配", "result_and_process", "fuzzy", "effectiveness", "creative_quality",
     ["llm_judge_interaction", "llm_judge_reasoning", "task_success"], 5),

    # === Content Moderation & Safety ===
    ("有害内容识别准确率", "result", "explicit", "safety", "safety_heavy",
     ["task_success", "llm_judge_safety"], 7),
    ("对抗性越狱检测", "result", "fuzzy", "safety", "safety_heavy",
     ["llm_judge_safety", "llm_judge_hallucination", "task_success"], 7),
    ("偏见与歧视检测评估", "result", "fuzzy", "safety", "safety_first",
     ["llm_judge_safety", "llm_judge_reasoning"], 7),

    # === Performance & Latency ===
    ("高并发场景响应延迟评测", "process", "explicit", "performance", "latency_sensitive",
     ["response_time", "token_usage", "task_success"], 0),
    ("流式输出首字延迟测量", "process", "explicit", "performance", "latency_sensitive",
     ["response_time", "task_success"], 1),
    ("批处理吞吐量评估", "process", "explicit", "performance", "performance_first",
     ["response_time", "token_usage", "task_success"], 3),

    # === Advanced Agent Scenarios ===
    ("Agent 自我纠错能力评估", "process", "fuzzy", "effectiveness", "comprehensive",
     ["llm_judge_reasoning", "task_success", "llm_judge_interaction"], 6),
    ("多 Agent 协作一致性测试", "process", "fuzzy", "effectiveness", "comprehensive",
     ["task_success", "llm_judge_reasoning", "tool_accuracy"], 1),
    ("工具编排与规划质量", "result_and_process", "fuzzy", "performance", "performance_first",
     ["tool_accuracy", "response_time", "task_success", "llm_judge_reasoning"], 4),
]

AGENT_VERSIONS = ["agent-finance-v1", "agent-medical-v2", "agent-legal-v1",
                   "agent-edu-v1", "agent-code-v3.1", "agent-creative-v1",
                   "agent-reasoning-v2", "agent-moderation-v1"]


def _simulate_scores(task_spec, success_ratio: float) -> dict[str, float]:
    _, mode, method, dimension, strategy_name, metrics, _ = task_spec
    scores: dict[str, float] = {}

    if "task_success" in metrics:
        scores["task_success"] = round(RNG.uniform(0.50, 0.99) * success_ratio, 4)
    if "response_time" in metrics:
        rt_ms = RNG.uniform(80, 4000)
        scores["response_time"] = round(max(0, 1.0 - rt_ms / 5000), 4)
    if "token_usage" in metrics:
        tu = RNG.uniform(50, 900)
        scores["token_usage"] = round(max(0, 1.0 - tu / 1200), 4)
    if "tool_accuracy" in metrics:
        scores["tool_accuracy"] = round(RNG.uniform(0.35, 0.98) * success_ratio, 4)

    if "answer_relevancy" in metrics:
        scores["answer_relevancy"] = round(RNG.uniform(0.40, 0.96), 4)
    if "faithfulness" in metrics:
        scores["faithfulness"] = round(RNG.uniform(0.35, 0.94), 4)
    if "context_recall" in metrics:
        scores["context_recall"] = round(RNG.uniform(0.30, 0.91), 4)

    if method == "fuzzy":
        if "llm_judge_reasoning" in metrics:
            scores["llm_judge_reasoning"] = round(RNG.uniform(1.5, 5.0), 2)
        if "llm_judge_safety" in metrics:
            scores["llm_judge_safety"] = round(RNG.uniform(1.8, 5.0), 2)
        if "llm_judge_hallucination" in metrics:
            scores["llm_judge_hallucination"] = round(RNG.uniform(1.2, 4.9), 2)
        if "llm_judge_interaction" in metrics:
            scores["llm_judge_interaction"] = round(RNG.uniform(2.0, 5.0), 2)

    if dimension == "effectiveness":
        scores["dimension_effectiveness"] = round(RNG.uniform(1.8, 5.0), 2)
    elif dimension == "safety":
        scores["dimension_safety"] = round(RNG.uniform(1.5, 5.0), 2)
        if RNG.random() > 0.4:
            scores["dimension_safety_alignment"] = round(RNG.uniform(2.0, 5.0), 2)
            scores["dimension_safety_privacy"] = round(RNG.uniform(2.0, 5.0), 2)
    elif dimension == "performance":
        scores["dimension_performance"] = round(RNG.uniform(1.5, 4.9), 2)
        if RNG.random() > 0.3:
            scores["dimension_performance_latency"] = round(RNG.uniform(1.2, 5.0), 2)
            scores["dimension_performance_stability"] = round(RNG.uniform(1.5, 4.8), 2)

    if scores:
        scores["strategy_score"] = round(
            sum(float(v) for v in scores.values()) / len(scores), 4
        )

    return scores


def _get_judge_config(method: str, metrics: list[str]) -> dict:
    base = {"provider": "openai", "model": "gpt-4o-mini", "temperature": 0}
    if method == "fuzzy":
        if any("safety" in m for m in metrics):
            return {**base, "prompt_template": "safety_deep_eval_v2", "threshold": 2.5}
        if any("reasoning" in m for m in metrics):
            return {**base, "prompt_template": "reasoning_deep_eval_v2", "threshold": 2.0}
        if any("interaction" in m for m in metrics):
            return {**base, "prompt_template": "interaction_quality_v1", "threshold": 2.5}
        return {**base, "prompt_template": "general_fuzzy_v2", "threshold": 2.0}
    return {}


def _get_run_config(task_spec) -> dict:
    _, mode, method, dimension, strategy_name, metrics, _ = task_spec
    return {
        "executor": "mock",
        "batch_size": RNG.choice([4, 8, 16, 32]),
        "timeout_seconds": RNG.choice([15, 30, 60, 120]),
        "enable_cache": RNG.choice([True, False]),
        "enable_parallel": RNG.choice([True, False]),
        "seed_tag": SEED_TAG,
    }


def seed():
    db = SessionLocal()
    try:
        # ── 1. Create datasets ──
        print("Creating datasets...")
        for spec in NEW_DATASETS:
            existed = db.query(DatasetAsset).filter(
                DatasetAsset.dataset_id == spec["dataset_id"]
            ).first()
            if existed:
                print(f"  ~ Dataset exists: {spec['dataset_id']}")
                continue
            asset = DatasetAsset(
                dataset_id=spec["dataset_id"],
                name=spec["name"],
                filename=spec["filename"],
                content_type="application/json",
                file_path=f"seed://{spec['filename']}",
                parser_summary={
                    "sample_count": RNG.randint(50, 300),
                    "columns": ["question", "answer", "ground_truth", "response_time_ms", "token_usage", "success", "domain"],
                    "parsed_metrics": ["task_success", "response_time", "faithfulness", "answer_relevancy"],
                    "numeric_snapshot": {"response_time_ms": round(RNG.uniform(300, 1500), 1), "token_usage": RNG.randint(150, 600)},
                    "findings": [f"{spec['name']} — Part 2 新增专业领域评测数据集。"],
                },
                note=SEED_TAG,
            )
            db.add(asset)
            db.flush()
            print(f"  + Dataset: {spec['dataset_id']}")

        # ── 2. Create strategies ──
        print("Creating strategies...")
        for spec in NEW_STRATEGIES:
            existed = db.query(EvaluationStrategy).filter(
                EvaluationStrategy.name == spec["name"]
            ).first()
            if existed:
                print(f"  ~ Strategy exists: {spec['name']}")
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
            name, mode, method, dimension, strategy_name, metrics, ds_idx = spec

            dataset_id = NEW_DATASETS[ds_idx]["dataset_id"]
            agent_version = RNG.choice(AGENT_VERSIONS)
            is_successful = (idx % 8) != 0  # ~87.5% success
            status = "completed" if is_successful else "failed"
            sample_count = RNG.randint(8, 30)
            success_ratio = 0.88 if is_successful else 0.35

            hours_ago = max(1, (len(TASK_SPECS) - idx) * 2 + RNG.randint(0, 8))
            finished_at = NOW - timedelta(hours=hours_ago)
            started_at = finished_at - timedelta(minutes=RNG.randint(3, 50))

            failed = 0 if is_successful else RNG.randint(1, max(2, sample_count // 4))
            completed = sample_count - failed

            question = f"Part 2 场景 #{idx + 1:02d}: 执行「{name}」自动化评估，输出结构化评测结果。"
            answer = f"已完成「{name}」评测，{sample_count} 个样本处理完毕。"

            task = EvaluationTask(
                name=name,
                description=f"Part 2 评测任务 #{idx + 1:02d} — {name}。模式: {mode}, 方法: {method}, 维度: {dimension}, 策略: {strategy_name}",
                agent_id=RNG.choice([1, 2, 3, 4, 5]),
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
                    "ground_truth": f"基准答案 #{idx + 1:02d}: 需覆盖 {', '.join(metrics)} 维度。",
                    "response_time_ms": RNG.randint(100, 3500),
                    "token_usage": RNG.randint(80, 900),
                    "success": is_successful,
                    "domain": dataset_id.split("_")[1],
                },
                progress=100,
                total_samples=sample_count,
                completed_samples=completed,
                failed_samples=failed,
                started_at=started_at,
                finished_at=finished_at,
                error_message=None if is_successful else f"模拟失败: {RNG.choice(['execution_timeout', 'invalid_output_format', 'safety_trigger', 'tool_execution_error'])}",
                note=SEED_TAG,
            )
            task.created_at = started_at
            task.updated_at = finished_at
            db.add(task)
            db.flush()

            # ── Result records ──
            result_count = min(sample_count, 20)
            for ridx in range(result_count):
                r_success = (ridx % 4) != 0  # 75% individual success
                scores = _simulate_scores(spec, 0.92 if r_success else 0.38)

                result = EvaluationResult(
                    task_id=task.id,
                    sample_id=f"{task.id}_sample_{ridx + 1:03d}",
                    user_input=f"评测输入 #{ridx + 1} for 「{name}」",
                    agent_output=f"Agent 输出 #{ridx + 1}: {RNG.choice(['正常完成', '高质量响应', '部分完成', '拒绝回答', '超时', '不符合格式'])}",
                    reference_answer=f"参考答案 #{ridx + 1}: {RNG.choice(['预期标准输出', '合规响应模板', '正确推理路径', '安全拒答'])}",
                    contexts={"items": [f"ctx_{idx}_{ridx}_a", f"ctx_{idx}_{ridx}_b"]},
                    tool_calls={
                        "calls": [
                            {"name": RNG.choice(["search", "calculator", "sql_query", "code_execute",
                                                  "weather_api", "stock_api", "medical_db", "legal_search"]),
                             "success": r_success,
                             "latency_ms": RNG.randint(20, 600)}
                        ]
                    },
                    reasoning_trace=f"trace-{task.id}-{ridx}" if mode in ("process", "result_and_process") else None,
                    metrics_scores=scores,
                    metrics_detail={"normalized": {k: float(v) for k, v in scores.items()}, "seed_tag": SEED_TAG},
                    response_time_ms=RNG.randint(60, 4000),
                    token_input=RNG.randint(40, 500),
                    token_output=RNG.randint(60, 800),
                    status="completed" if r_success else "failed",
                    error_message=None if r_success else f"sample_error_{RNG.choice(['timeout', 'invalid', 'unsafe', 'incorrect'])}",
                    human_label={"label": "auto_seeded", "labeler_id": "system"},
                    scores=scores,
                    raw_data={
                        "mode": mode,
                        "method": method,
                        "dimension": dimension,
                        "dataset_id": dataset_id,
                        "strategy": strategy_name,
                        "engine_details": {"source": "comprehensive_seed_v2", "seed_tag": SEED_TAG},
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
            print(f"  + Task #{idx + 1:02d}: 「{name}」 ({mode}/{method}/{dimension}) → {result_count} results")

        db.commit()
        print(f"\n✅ Part 2 seeding complete! Created {created_tasks} new tasks.")
        print(f"   New datasets: {len(NEW_DATASETS)}, New strategies: {len(NEW_STRATEGIES)}")
        print(f"   Overall total should now be ~{24 + created_tasks} tasks.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
