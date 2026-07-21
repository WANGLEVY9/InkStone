import json
import os
from typing import Any, Dict, List, Tuple, Optional
import re
from collections import Counter

import requests


DATASET_PATH = "eval_dataset.json"

# 大模型API配置：使用智谱AI的glm-4-flash（免费模型，需要API密钥）
# 与 Indicator-two 保持完全一致的配置方式
GLM_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
# API 密钥优先从环境变量读取，避免把敏感信息写入仓库；请在运行前设置环境变量 GLM_API_KEY
GLM_API_KEY = os.getenv("GLM_API_KEY")


def char_ngrams(text: str, n: int = 2) -> List[str]:
    """
    将文本转换为字符级 n-gram 序列
    """
    if not text:
        return []
    # 去掉空白字符，保留中文和常见符号
    normalized = re.sub(r"\s+", "", text.lower())
    if len(normalized) < n:
        return [normalized] if normalized else []
    return [normalized[i : i + n] for i in range(len(normalized) - n + 1)]


def evaluate_factual_correctness_with_llm(ground_truth: str, final_answer: str) -> Dict[str, float]:
    """
    使用 LLM 模拟 Ragas FactualCorrectness 指标：
    - 让模型在内部将 ground_truth 和 final_answer 分解为若干事实性“claim”；
    - 通过自然语言推理判断哪些回答中的 claim 得到参考支持；
    - 输出基于 TP/FP/FN 的 precision、recall、f1（范围 0~1）。

    这里采用一个连续分数 score∈[0,1] 近似 F1，并将该分数同时赋给 precision/recall/f1，
    以获得更平滑、可解释的结果。
    """
    prompt = f"""
    你是一个评估事实正确性的专家，需要参考 Ragas 的 FactualCorrectness 指标思想。
    现在有一段“参考答案 reference”和一段“模型回答 response”，请你在内部完成以下步骤：
    1. 将 reference 拆分为若干事实性陈述（claims）；
    2. 将 response 拆分为若干事实性陈述（claims）；
    3. 判断 response 中的每个 claim 是否被 reference 支持；
    4. 综合考虑 TP/FP/FN，给出一个总体的事实正确性分数 score（0~1，越高越好）。

    非常重要：
    - 只输出一个 0~1 之间的数字，保留两位小数；
    - 不要输出任何文字解释或其它内容。

    【reference】:
    {ground_truth}

    【response】:
    {final_answer}
    """

    raw = call_llm(prompt)

    score = 0.0
    if raw:
        # 提取第一个 0~1 之间的数字
        m = re.search(r"\b([01](?:\.\d+)?)\b", raw.strip())
        if m:
            try:
                v = float(m.group(1))
                if 0.0 <= v <= 1.0:
                    score = v
            except ValueError:
                score = 0.0

    return {"precision": score, "recall": score, "f1": score}


def compute_factual_overlap(ground_truth: str, final_answer: str) -> Dict[str, float]:
    """
    事实正确性：基于 LLM 的 claim 分解与自然语言推理，
    输出与 Ragas FactualCorrectness 类似的 precision、recall 和 F1。
    """
    # 如需退回纯规则算法，可在此改为调用基于 char_ngrams 的版本。
    return evaluate_factual_correctness_with_llm(ground_truth, final_answer)


def build_glm_prompt(user_query: str, ground_truth: str, final_answer: str) -> str:
    return (
        "你是一个评估外卖 Agent 任务完成度的评测助手。\n"
        "请根据下面的信息判断 Agent 的 final_answer 是否满足 ground_truth 描述的任务目标，"
        "并只输出一个 JSON 对象，格式如下：\n"
        "{\n"
        '  "score": 浮点数，范围在[0,1]，1表示完全满足, 0表示完全不满足,\n'
        '  "reason": "简要中文说明"\n'
        "}\n\n"
        f"【用户请求 user_query】:\n{user_query}\n\n"
        f"【期望结果 ground_truth】:\n{ground_truth}\n\n"
        f"【Agent 最终回答 final_answer】:\n{final_answer}\n"
    )


def call_llm(prompt: str) -> str:
    """
    调用glm-4-flash API进行评估。：
    1. 准备请求头：Authorization (Bearer + API Key)，Content-Type (application/json)。
    2. 准备请求体：JSON，包括model="glm-4-flash"，messages，temperature、max_tokens 等。
    3. 发送POST请求到GLM_API_URL。
    4. 处理响应：检查status_code==200，解析JSON，提取choices[0].message.content，strip()处理。
    5. 错误处理：HTTP错误或解析失败时，打印日志，返回默认"0"。
    """
    if not GLM_API_KEY:
        print("Error: 未找到 GLM_API_KEY 环境变量，请先设置智谱 API 密钥。")
        return "0"

    headers = {
        "Authorization": f"Bearer {GLM_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "glm-4-flash",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 32,
    }
    try:
        response = requests.post(GLM_API_URL, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
        return content
    except requests.exceptions.Timeout:
        print("API call timed out; returning 0 by default")
        return "0"
    except requests.exceptions.RequestException as e:
        print(f"API call failed: {e}")
        return "0"  # 默认不满足
    except (KeyError, ValueError):
        print("Unexpected response format")
        return "0"


def evaluate_goal_satisfaction_with_llm(
    user_query: str, ground_truth: str, final_answer: str
) -> float:
    """
    使用 glm-4-flash 评估 final_answer 是否满足 ground_truth。

    返回 (score, reason)，其中 score∈[0,1]。
    完全参考 Indicator-two 的二元判断风格：
    - 只让模型输出 1 或 0（字符串），不带解释；
    - 我们再将其转换为 float。
    """
    prompt = f"""
    你是一个严格的评估者。请判断Agent的最终回答是否完全满足任务的ground truth描述。
    - Ground Truth: {ground_truth}
    - Final Answer: {final_answer}

    规则：
    - 如果最终回答明确达成ground_truth的所有要求（如成功下单、支付、查询状态等），输出1。
    - 如果缺少关键步骤（如未支付但ground_truth要求支付）、或结果不匹配，输出0。
    - 只输出1或0，不要输出任何其他内容或解释。
    """

    score_str = call_llm(prompt)

    try:
        score = float(score_str)
    except ValueError:
        return 0.0

    # 只接受 0 或 1，其它情况按 0 处理
    if score not in (0.0, 1.0):
        return 0.0

    return score


def compute_step_coverage(steps: List[Dict[str, Any]], expected_steps: List[Dict[str, Any]]) -> float:
    """
    其他指标 1：step_coverage
    衡量实际 steps 覆盖期望步骤数量的程度，len(steps)/len(expected_steps)，上限为 1。
    """
    if not expected_steps:
        return 1.0
    return min(len(steps) / len(expected_steps), 1.0)


def compute_observation_match_ratio(
    steps: List[Dict[str, Any]], expected_steps: List[Dict[str, Any]]
) -> float:
    """
    其他指标 2：observation_match_ratio
    对齐位置的 observation 完全相等的比例。
    """
    total = min(len(steps), len(expected_steps))
    if total == 0:
        return 1.0

    matches = 0
    for i in range(total):
        obs = str(steps[i].get("observation", "")).strip()
        exp_obs = str(expected_steps[i].get("observation", "")).strip()
        if obs == exp_obs:
            matches += 1
    return matches / total


def compute_tool_sequence_jaccard(
    steps: List[Dict[str, Any]], expected_steps: List[Dict[str, Any]]
) -> float:
    """
    其他指标 3：tool_sequence_jaccard
    比较两个轨迹中 tool_call 序列的 Jaccard 相似度（基于集合，而非顺序）。
    """
    tools_actual = {s.get("tool_call", "") for s in steps if s.get("tool_call")}
    tools_expected = {s.get("tool_call", "") for s in expected_steps if s.get("tool_call")}

    if not tools_actual and not tools_expected:
        return 1.0
    union = tools_actual | tools_expected
    inter = tools_actual & tools_expected
    if not union:
        return 1.0
    return len(inter) / len(union)


def evaluate_sample(sample: Dict[str, Any]) -> Dict[str, Any]:
    """
    对单个 task 样本进行多指标评估。
    """
    ground_truth = str(sample.get("ground_truth", ""))
    final_answer = str(sample.get("final_answer", ""))
    user_query = str(sample.get("user_query", ""))
    steps = sample.get("steps", []) or []
    expected_steps = sample.get("expected_steps", []) or []

    factual = compute_factual_overlap(ground_truth, final_answer)
    goal_score = evaluate_goal_satisfaction_with_llm(user_query, ground_truth, final_answer)

    step_coverage = compute_step_coverage(steps, expected_steps)
    obs_match = compute_observation_match_ratio(steps, expected_steps)
    tool_jaccard = compute_tool_sequence_jaccard(steps, expected_steps)

    return {
        "task_id": sample.get("task_id"),
        # 1. 事实正确性相关（FactualCorrectnessresponse）
        "factual_precision": factual["precision"],
        "factual_recall": factual["recall"],
        "factual_f1": factual["f1"],
        # 2. LLM 判断任务完成度（distinct 于 Indicator-two 的 goal_attainment 名称）
        "goal_satisfaction_llm": goal_score,
        # 3. 其他自定义指标（Indicator-two 中未出现过的名字）
        "step_coverage": step_coverage,
        "observation_match_ratio": obs_match,
        "tool_sequence_jaccard": tool_jaccard,
    }


def aggregate_metrics(sample_scores: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    计算各数值型指标的简单平均。
    """
    if not sample_scores:
        return {}

    numeric_keys = [
        "factual_precision",
        "factual_recall",
        "factual_f1",
        "goal_satisfaction_llm",
        "step_coverage",
        "observation_match_ratio",
        "tool_sequence_jaccard",
    ]

    sums = {k: 0.0 for k in numeric_keys}
    count = 0
    for s in sample_scores:
        count += 1
        for k in numeric_keys:
            v = s.get(k)
            if isinstance(v, (int, float)):
                sums[k] += float(v)

    averages = {k: (sums[k] / count if count > 0 else 0.0) for k in numeric_keys}
    return averages


def main():
    # 读取评估数据集
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    sample_scores: List[Dict[str, Any]] = []
    for sample in dataset:
        score = evaluate_sample(sample)
        sample_scores.append(score)

    avg_metrics = aggregate_metrics(sample_scores)

    report = {
        "metrics": {
            "factual_correctness_response": {
                "description": (
                    "事实正确性（Factual Correctness）：使用 LLM 将参考答案和模型回答分解为事实性 claims，"
                    "通过自然语言推理估计整体事实正确性得分，思想参考 Ragas FactualCorrectness 指标。"
                ),
                "average_precision": avg_metrics.get("factual_precision", 0.0),
                "average_recall": avg_metrics.get("factual_recall", 0.0),
                "average_f1": avg_metrics.get("factual_f1", 0.0),
                "selection_reason": "从事实维度评估 final_answer 是否忠实于 ground_truth，直接对应 Ragas 中的 factual 类指标。",
                "implementation": "LLM prompt 生成 0~1 连续事实正确性分数，以该分数近似 precision/recall/F1，解析失败回退为0。",
            },
            "goal_satisfaction_llm": {
                "description": "任务完成度（Goal Satisfaction，LLM 判定）：使用 glm-4-flash 判断 final_answer 是否满足 ground_truth。",
                "average_score": avg_metrics.get("goal_satisfaction_llm", 0.0),
                "selection_reason": "衡量 Agent 是否整体达成用户任务目标，直接对应任务完成度。",
                "implementation": "LLM 二元判断（输出0或1），将多个样本分数取平均，异常或非0/1输出按0处理。",
            },
            "step_coverage": {
                "description": "步骤覆盖率（Step Coverage）：实际 steps 数量与 expected_steps 数量的覆盖比例，衡量执行步骤是否过少或过多。",
                "average_score": avg_metrics.get("step_coverage", 0.0),
                "selection_reason": "从轨迹长度层面衡量规划合理性，检测明显的缺失步骤或冗余步骤。",
                "implementation": "规则-based 计算 len(steps)/len(expected_steps)，上限裁剪为1。",
            },
            "observation_match_ratio": {
                "description": "观测一致率（Observation Match Ratio）：与 expected_steps 对齐位置上 observation 完全相同的比例，衡量工具调用结果是否一致。",
                "average_score": avg_metrics.get("observation_match_ratio", 0.0),
                "selection_reason": "细粒度衡量每一步工具调用的结果是否与期望轨迹保持一致。",
                "implementation": "规则-based 精确字符串匹配 observation，按对齐位置统计匹配比例。",
            },
            "tool_sequence_jaccard": {
                "description": "工具序列相似度（Tool Sequence Jaccard）：实际与期望轨迹中 tool_call 集合的 Jaccard 相似度，衡量整体工具选择是否接近。",
                "average_score": avg_metrics.get("tool_sequence_jaccard", 0.0),
                "selection_reason": "在集合层面衡量 Agent 所选工具种类是否与期望规划相符，补充 step 级别指标。",
                "implementation": "规则-based 计算实际与期望 tool_call 集合的 Jaccard 相似度 = |交集|/|并集|。",
            },
        },
        "sample_scores": sample_scores,
    }

    # 打印到控制台，便于直接查看
    print(json.dumps(report, ensure_ascii=False, indent=2))

    # 同时写入本目录下的评估报告文件（避免覆盖 Indicator-two 的报告）
    output_path = "evaluation_report_indicator_one.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
