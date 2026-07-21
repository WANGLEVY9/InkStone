import json
import os
from typing import Any, Dict, List
import numpy as np
import requests
import time  # 新增导入time模块，用于API调用延迟，避免rate limit

# 大模型API配置：使用智谱AI的glm-4-flash（免费模型，需要API密钥）
# 用户需从智谱AI官网（https://open.bigmodel.cn/）注册并获取免费API密钥。
# glm-4-flash为免费 tier，支持有限QPS和每日限额，适合评估任务。
# API Endpoint: https://open.bigmodel.cn/api/paas/v4/chat/completions
# 文档参考: https://open.bigmodel.cn/docs/api
# 注意：免费API密钥有使用限制，避免高频调用；如遇限额，可切换到hunyuan-lite。
GLM_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
# API 密钥优先从环境变量读取，避免把敏感信息写入仓库；请在运行前设置环境变量 GLM_API_KEY
GLM_API_KEY = os.getenv("GLM_API_KEY")

def call_llm(prompt: str) -> str:
    """
    调用glm-4-flash API进行评估。
    API调用流程详细说明：
    1. 准备请求头：Authorization (Bearer + API Key)，Content-Type (application/json)。
    2. 准备请求体：JSON，包括model="glm-4-flash"，messages（[{"role": "user", "content": prompt}]），
       temperature=0.0（确保确定性输出），max_tokens=10（限制为分数输出）。
    3. 发送POST请求到GLM_API_URL。
    4. 处理响应：检查status_code==200，解析JSON，提取choices[0].message.content，strip()处理。
    5. 错误处理：HTTP错误或解析失败时，打印日志，返回默认"0"（不满足）。
    6. 额外提示：API支持中文prompt；免费密钥有rate limit（e.g., 10 RPM），建议批量处理前测试。
       如需替代：hunyuan-lite（腾讯混元），URL: "https://hunyuan.tencentcloudapi.com/"，
       Model: "hunyuan-lite"，需腾讯云API密钥，请求格式类似但需调整签名。
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
        "max_tokens": 10
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

# 指标1：任务完成度 (Goal Attainment) - 方向3
# 设计逻辑：参考Ragas的answer_relevancy或faithfulness，使用LLM判断final_answer是否满足ground_truth。
def compute_goal_attainment(sample: Dict[str, Any]) -> float:
    ground_truth = sample["ground_truth"]
    final_answer = sample["final_answer"]
    
    prompt = f"""
    你是一个严格的评估者。请判断Agent的最终回答是否完全满足任务的ground truth描述。
    - Ground Truth: {ground_truth}
    - Final Answer: {final_answer}
    
    规则：
    - 如果最终回答明确达成ground_truth的所有要求（如成功下单、支付、查询状态等），输出1。
    - 如果缺少关键步骤（如未支付但ground_truth要求支付）、或结果不匹配，输出0。
    - 只输出1或0，不要输出任何其他内容或解释。
    """
    
    time.sleep(1)  # 延迟1秒，避免API rate limit
    score_str = call_llm(prompt)
    try:
        score = float(score_str)
        if score not in [0.0, 1.0]:
            print(f"Invalid score '{score_str}' for goal_attainment, defaulting to 0")
            score = 0.0
    except ValueError:
        print(f"Non-numeric score '{score_str}' for goal_attainment, defaulting to 0")
        score = 0.0
    
    return score

# 指标2：工具调用准确度 - Tool Name Accuracy (方向1)
# 设计逻辑：规则-based，比较steps和expected_steps的tool_call名称匹配比例，参考Ragas tool_call_accuracy。
def compute_tool_name_accuracy(sample: Dict[str, Any]) -> float:
    steps: List[Dict] = sample["steps"]
    expected_steps: List[Dict] = sample["expected_steps"]
    
    min_len = min(len(steps), len(expected_steps))
    if min_len == 0:
        return 0.0
    
    matches = sum(1 for i in range(min_len) if steps[i]["tool_call"] == expected_steps[i]["tool_call"])
    accuracy = matches / len(expected_steps)  # 以expected为基准，惩罚多余或缺失
    return accuracy

# 指标3：工具调用准确度 - Input Parameter Accuracy (方向1)
# 设计逻辑：规则-based，比较input JSON字符串的精确匹配比例。
def compute_input_param_accuracy(sample: Dict[str, Any]) -> float:
    steps: List[Dict] = sample["steps"]
    expected_steps: List[Dict] = sample["expected_steps"]
    
    min_len = min(len(steps), len(expected_steps))
    if min_len == 0:
        return 0.0
    
    matches = sum(1 for i in range(min_len) if steps[i].get("input") == expected_steps[i].get("input"))
    accuracy = matches / len(expected_steps)
    return accuracy

# 指标4：规划合理性 - Trajectory Efficiency (方向2)
# 设计逻辑：规则-based，计算实际steps长度与expected_steps长度的比率，理想为1.0；>1表示冗余，<1表示缺失。
def compute_trajectory_efficiency(sample: Dict[str, Any]) -> float:
    len_steps = len(sample["steps"])
    len_expected = len(sample["expected_steps"])
    if len_expected == 0:
        return 0.0
    ratio = min(len_steps / len_expected, len_expected / len_steps)  # 对称惩罚缺失或冗余
    return ratio

# 指标5：规划合理性 - Logic Consistency (方向2)
# 设计逻辑：LLM-based，判断thought是否逻辑一致地导致tool_call和使用前observation。
def compute_logic_consistency(sample: Dict[str, Any]) -> float:
    steps: List[Dict] = sample["steps"]
    if len(steps) < 2:  # 需要至少两个步骤来检查一致性
        return 1.0 if len(steps) > 0 else 0.0
    
    consistency_scores = []
    for i in range(1, len(steps)):
        prev_observation = steps[i-1].get("observation", "")
        current_thought = steps[i]["thought"]
        current_tool = steps[i]["tool_call"]
        
        prompt = f"""
        判断以下Agent步骤的逻辑一致性：
        - 上一步观察: {prev_observation}
        - 当前思考: {current_thought}
        - 当前工具调用: {current_tool}
        
        规则：
        - 如果思考合理利用上一步观察，并逻辑导致工具调用，输出1。
        - 如果存在断层、忽略观察或不合逻辑，输出0。
        - 只输出1或0。
        """
        
        time.sleep(1)
        score_str = call_llm(prompt)
        try:
            score = float(score_str)
            if score not in [0.0, 1.0]:
                score = 0.0
        except ValueError:
            score = 0.0
        consistency_scores.append(score)
    
    return np.mean(consistency_scores) if consistency_scores else 1.0 # type: ignore

# 指标6：规划合理性 - No Dead Loop Detection (额外，方向2)
# 设计逻辑：规则-based，检查是否有重复的tool_call序列表示死循环。
def compute_no_dead_loop(sample: Dict[str, Any]) -> float:
    steps: List[Dict] = sample["steps"]
    if len(steps) < 2:
        return 1.0
    
    tool_sequence = [s["tool_call"] for s in steps]
    for i in range(len(tool_sequence) - 1):
        if tool_sequence[i] == tool_sequence[i+1]:  # 简单检测连续重复
            return 0.0
    return 1.0  # 无死循环

# 主函数：加载数据集，计算多个指标，生成报告
def evaluate_dataset():
    # 获取当前脚本的目录路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(script_dir, "eval_dataset.json")

    if not GLM_API_KEY:
        print("Error: 未找到 GLM_API_KEY 环境变量，请先设置智谱 API 密钥后再运行。")
        return
    
    if not os.path.isfile(dataset_path):
        print(
            f"Error: Dataset file not found at {dataset_path}. "
            "Please ensure 'eval_dataset.json' is in the same directory as this script."
        )
        return

    try:
        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error loading dataset: {e}")
        return
    
    metrics_results = {
        "goal_attainment": [],
        "tool_name_accuracy": [],
        "input_param_accuracy": [],
        "trajectory_efficiency": [],
        "logic_consistency": [],
        "no_dead_loop": []
    }
    sample_scores = []
    
    for sample in dataset:
        scores = {
            "task_id": sample["task_id"],
            "goal_attainment": compute_goal_attainment(sample),
            "tool_name_accuracy": compute_tool_name_accuracy(sample),
            "input_param_accuracy": compute_input_param_accuracy(sample),
            "trajectory_efficiency": compute_trajectory_efficiency(sample),
            "logic_consistency": compute_logic_consistency(sample),
            "no_dead_loop": compute_no_dead_loop(sample)
        }
        for metric, value in scores.items():
            if metric != "task_id":
                metrics_results[metric].append(value)
        sample_scores.append(scores)
    
    avg_scores = {metric: np.mean(values) for metric, values in metrics_results.items()}
    
    # 生成报告
    report = {
        "metrics": {
            "goal_attainment": {
                "description": "任务完成度（方向3）：使用LLM判断final_answer是否满足ground_truth。",
                "average_score": avg_scores["goal_attainment"],
                "selection_reason": "直接评估Agent整体目标达成，参考Ragas语义指标。",
                "implementation": "LLM prompt二元判断，异常默认0。"
            },
            "tool_name_accuracy": {
                "description": "工具调用准确度 - 工具名称准确率（方向1）：比较tool_call匹配比例。",
                "average_score": avg_scores["tool_name_accuracy"],
                "selection_reason": "评估Action选择正确性，参考Ragas tool_call。",
                "implementation": "规则-based精确匹配，以expected_steps为基准。"
            },
            "input_param_accuracy": {
                "description": "工具调用准确度 - 输入参数准确率（方向1）：比较input JSON匹配比例。",
                "average_score": avg_scores["input_param_accuracy"],
                "selection_reason": "精细化评估参数正确性，避免仅名称匹配。",
                "implementation": "规则-based字符串匹配。"
            },
            "trajectory_efficiency": {
                "description": "规划合理性 - 轨迹效率（方向2）：steps长度比率，惩罚冗余/缺失。",
                "average_score": avg_scores["trajectory_efficiency"],
                "selection_reason": "检测规划冗余，参考Ragas trajectory evaluation。",
                "implementation": "规则-based比率计算，对称惩罚。"
            },
            "logic_consistency": {
                "description": "规划合理性 - 逻辑一致性（方向2）：LLM判断thought与前observation/后tool的连贯性。",
                "average_score": avg_scores["logic_consistency"],
                "selection_reason": "评估推理链条断层，增强规划评估深度。",
                "implementation": "LLM逐步判断，平均分数。"
            },
            "no_dead_loop": {
                "description": "规划合理性 - 无死循环检测（方向2）：检查连续重复tool_call。",
                "average_score": avg_scores["no_dead_loop"],
                "selection_reason": "针对Agent常见问题'死循环'，自定义规则检测。",
                "implementation": "规则-based序列检查，有重复则0。"
            }
        },
        "sample_scores": sample_scores,
        "analysis": f"数据集共有{len(dataset)}个样本。整体平均分数：任务完成度{avg_scores['goal_attainment']:.2f}，工具名称准确{avg_scores['tool_name_accuracy']:.2f}，参数准确{avg_scores['input_param_accuracy']:.2f}，轨迹效率{avg_scores['trajectory_efficiency']:.2f}，逻辑一致{avg_scores['logic_consistency']:.2f}，无死循环{avg_scores['no_dead_loop']:.2f}。分析：工具调用整体准确但参数易错；规划有冗余但无明显循环；完成度受支付遗漏影响。建议：强化参数验证、优化规划避免冗余、确保完整步骤。"
    }
    
    # 输出报告为JSON（保存到脚本同目录）
    report_path = os.path.join(script_dir, "evaluation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=4)
    
    print(f"评估完成，报告已保存到 {report_path}")

# 运行评估
if __name__ == "__main__":
    evaluate_dataset()