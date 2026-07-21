# Agent 评估复现实验报告

## 1. 指标选择原因

为了系统评估外卖 Agent 的能力，本实验从 **工具调用正确性、规划合理性和任务完成度** 三个维度设计评估指标。指标设计参考了 **Ragas Agent Evaluation** 的思想，并结合本任务场景进行简化实现。

最终选取了 **6 个评估指标**：

| 评估维度    | 指标名称                     | 指标作用              |
| ------- | ------------------------ | ----------------- |
| 工具调用正确性 | Tool Name Accuracy       | 判断 Agent 是否调用正确工具 |
| 工具调用正确性 | Input Parameter Accuracy | 判断工具调用参数是否正确      |
| 规划合理性   | Trajectory Efficiency    | 判断执行步骤是否冗余或缺失     |
| 规划合理性   | Logic Consistency        | 判断推理过程是否逻辑连贯      |
| 规划合理性   | No Dead Loop             | 判断是否出现循环调用工具      |
| 任务完成度   | Goal Attainment          | 判断最终任务是否完成        |

### 1.1 Tool Name Accuracy

该指标用于评估 **Agent 在每一步是否选择了正确的工具**。
在 Agent 系统中，工具选择错误会导致任务流程偏离，因此工具调用准确率是评估 Agent 能力的重要指标。

该指标参考 **Ragas 的 Tool Call Accuracy 指标**，通过比较实际调用的工具与期望工具进行计算。

---

### 1.2 Input Parameter Accuracy

在 Agent 系统中，即使工具名称正确，如果 **输入参数错误** 也会导致执行失败。

因此本实验设计该指标，用于评估：

* 参数是否正确
* 参数是否完整

该指标通过比较实际调用参数与期望参数是否一致进行计算。

---

### 1.3 Trajectory Efficiency

Agent 在执行任务时需要规划执行步骤。
如果步骤过多或过少，说明规划能力存在问题。

因此设计 **Trajectory Efficiency** 指标，用于评估：

* 是否存在冗余步骤
* 是否存在缺失步骤

该指标通过比较 **实际步骤数与期望步骤数的比例** 计算。

---

### 1.4 Logic Consistency

Agent 通常通过以下结构进行推理：

```
Observation → Thought → Tool Call
```

如果推理过程不连贯，例如：

* 忽略观察信息
* 工具调用与思考不匹配

说明 Agent 的规划逻辑存在问题。

因此本实验使用 **LLM 评估方法** 判断每一步推理是否合理。

---

### 1.5 No Dead Loop

Agent 在执行过程中可能会陷入 **循环调用工具的问题**，例如：

```
search_products → search_products → search_products
```

该问题会导致 Agent 无法结束任务。

因此设计该指标检测是否存在连续重复的工具调用。

---

### 1.6 Goal Attainment

该指标用于评估 **Agent 是否最终完成任务目标**。

由于任务结果通常是自然语言描述，因此采用 **LLM 评估方法** 判断：

```
final_answer 是否满足 ground_truth
```

该方法类似于 Ragas 中的 **Answer Relevancy / Faithfulness** 指标。

---

# 2. 指标实现过程

评估程序实现于 `main.py`，整体流程如下：

```
加载数据集
      ↓
遍历每个样本
      ↓
计算6个指标
      ↓
统计平均分
      ↓
生成 evaluation_report.json
```

数据集文件为：

```
eval_dataset.json
```

每个样本包含：

* Agent 执行步骤
* 期望执行步骤
* 最终回答

---

## 2.1 Goal Attainment 实现

该指标使用 **LLM 作为评估器**。

实现流程：

1. 提取

```
ground_truth
final_answer
```

2. 构造评估 prompt：

```
Ground Truth: ...
Final Answer: ...

如果最终回答满足所有要求输出1，否则输出0
```

3. 调用 **glm-4-flash API** 获取评分。

最终输出：

```
1 -> 任务完成
0 -> 任务未完成
```

---

## 2.2 Tool Name Accuracy 实现

该指标为 **规则方法（rule-based）**。

实现方法：

1. 遍历 Agent 实际步骤 `steps`
2. 对比期望步骤 `expected_steps`
3. 统计工具名称匹配数量

计算公式：

```
accuracy = matches / len(expected_steps)
```

其中：

```
matches = steps[i].tool_call == expected_steps[i].tool_call
```

---

## 2.3 Input Parameter Accuracy 实现

该指标用于评估工具输入参数。

实现方法：

1. 比较：

```
steps[i].input
expected_steps[i].input
```

2. 若 JSON 字符串完全一致则计为匹配。

计算方式：

```
accuracy = matches / len(expected_steps)
```

---

## 2.4 Trajectory Efficiency 实现

该指标评估执行轨迹长度是否合理。

设：

```
len_steps = 实际执行步骤数
len_expected = 期望步骤数
```

计算公式：

```
score = min(len_steps / len_expected, len_expected / len_steps)
```

该公式可以同时惩罚：

* 冗余步骤
* 步骤缺失

理想情况为：

```
score = 1
```

---

## 2.5 Logic Consistency 实现

该指标使用 **LLM 评估每一步推理逻辑**。

评估信息包括：

```
上一轮 observation
当前 thought
当前 tool_call
```

LLM 判断：

```
thought 是否合理利用 observation
tool_call 是否由 thought 推导得到
```

评分方式：

```
1 -> 合理
0 -> 不合理
```

最终结果为所有步骤评分的平均值。

---

## 2.6 No Dead Loop 实现

该指标使用 **规则方法检测循环调用**。

实现方法：

1. 提取工具调用序列：

```
tool_sequence = [tool_call1, tool_call2, ...]
```

2. 检测是否存在连续重复：

```
tool_sequence[i] == tool_sequence[i+1]
```

若存在，则认为可能出现死循环。

评分规则：

```
无死循环 -> 1
存在死循环 -> 0
```

---

# 3. 评估结果分析

评估程序对整个数据集计算平均指标，结果如下：

| 指标                       | 平均分       |
| ------------------------ | --------- |
| Goal Attainment          | **0.926** |
| Tool Name Accuracy       | **0.793** |
| Input Parameter Accuracy | **0.599** |
| Trajectory Efficiency    | **0.872** |
| Logic Consistency        | **0.991** |
| No Dead Loop             | **0.852** |

---

## 3.1 任务完成度分析

任务完成度达到 **0.926**，说明大多数任务能够成功完成。

这表明 Agent 在整体任务执行方面具有较好的能力。

但仍有少数任务未成功完成，可能原因包括：

* 工具调用顺序错误
* 参数错误导致任务失败

---

## 3.2 工具调用准确率分析

工具名称准确率为 **0.793**。

说明 Agent 在大部分情况下能够选择正确工具，但仍存在以下问题：

* 工具选择错误
* 执行顺序偏差

例如：

* 未先查询餐厅就尝试下单
* 在不需要的情况下重复查询

---

## 3.3 参数准确率分析

输入参数准确率为 **0.599**，明显低于工具名称准确率。

这说明 Agent 在 **参数构造方面存在较大问题**，例如：

* 参数值不正确
* 参数缺失
* 参数格式错误

例如：

```
restaurant_id错误
food_name错误
数量错误
```

---

## 3.4 规划效率分析

Trajectory Efficiency 为 **0.872**。

说明 Agent 的规划步骤总体接近期望轨迹，但仍存在：

* 冗余步骤
* 缺失步骤

部分样本出现：

```
重复搜索餐厅
重复查询商品
```

---

## 3.5 逻辑一致性分析

Logic Consistency 达到 **0.991**，说明 Agent 的推理链条整体较合理。

大部分步骤能够做到：

```
Observation → Thought → Tool
```

逻辑连贯。

---

## 3.6 死循环问题分析

No Dead Loop 得分为 **0.852**。

说明少量样本存在循环调用问题，例如：

```
search_products → search_products
```

该问题通常发生在：

* Agent 未正确更新状态
* 推理未正确终止

---

# 4. 总结

本实验复现了一套 **Agent 评估指标体系**，从多个维度对外卖 Agent 的行为进行评估。

实验结果表明：

* Agent 在 **任务完成度与推理逻辑方面表现较好**
* 在 **工具参数构造方面仍存在明显不足**
* 部分情况下出现 **冗余步骤或循环调用**

这些评估结果能够帮助分析 Agent 系统的能力和局限，为后续优化提供依据。

---
