# 评估模式 DSL 规范

说明：此文档定义平台在不同评估模式下对 Agent 输出的严格 DSL（契约）以及平台须追踪的指标（含计算方法、聚合和预警阈值）。保存路径：docs/evaluation_metrics_dsl.md。

约定：
- 所有时间采用 ISO8601 UTC 字符串。
- 所有数值度量统一为浮点数（若为整数须仍以数值类型传输）。
- 所有字段标注为 REQUIRED / OPTIONAL。

--------

## 一、评估模式（mode）清单
- realtime
- offline_trace
- batch_dataset
- process (multi-step workflows)
- multi_turn_conversation

--------

## 二、数据类型定义

基本类型：
- string
- number (float)
- integer
- boolean
- object
- array
- timestamp (ISO8601 string)

特定别名：
- milliseconds: number（表示毫秒）
- tokens: integer

--------

## 三、总体样本输出（SampleOutput） EBNF

SampleOutput ::= Object {
  sample_id: string REQUIRED,
  input: Object REQUIRED,            # 原始输入（question/input/prompt）
  output: Object REQUIRED,           # Agent 返回（text/structured）
  reference: Object OPTIONAL,       # 参考答案/标注
  runtime: RuntimeInfo OPTIONAL,
  tools: ToolsInfo OPTIONAL,
  trace: TraceInfo OPTIONAL,
  human_label: HumanLabel OPTIONAL,
  metadata: object OPTIONAL
}

RuntimeInfo ::= Object {
  response_time_ms: milliseconds OPTIONAL,
  tokens_input: tokens OPTIONAL,
  tokens_output: tokens OPTIONAL,
  cost_usd: number OPTIONAL,
  success: boolean OPTIONAL,
  error: string OPTIONAL
}

ToolsInfo ::= Object {
  tool_calls: array[ToolCall] OPTIONAL,
  tool_summary: object OPTIONAL
}

ToolCall ::= Object {
  name: string REQUIRED,
  success: boolean OPTIONAL,
  latency_ms: milliseconds OPTIONAL,
  result: object OPTIONAL
}

TraceInfo ::= Object {
  steps: array[TraceStep] OPTIONAL,
  reasoning_trace: string OPTIONAL
}

TraceStep ::= Object {
  step_index: integer REQUIRED,
  step_name: string OPTIONAL,
  latency_ms: milliseconds OPTIONAL,
  token_usage: tokens OPTIONAL,
  success: boolean OPTIONAL,
  note: string OPTIONAL
}

HumanLabel ::= Object {
  labeler_id: string OPTIONAL,
  label: object REQUIRED,
  labeled_at: timestamp OPTIONAL
}

--------

## 四、按模式必需/推荐字段

1) realtime
- REQUIRED: sample_id, input, output
- RECOMMENDED: runtime.response_time_ms, runtime.tokens_output, trace.steps (实时每步)
- PURPOSE: 平台用于实时看板（延迟、成功率、每步耗时）

2) offline_trace
- REQUIRED: sample_id, input, output, trace.steps
- RECOMMENDED: runtime.* , tools.tool_calls
- PURPOSE: 回放评估、轨迹对齐、LLM-judge 输入

3) batch_dataset
- REQUIRED: sample_id, input, output
- RECOMMENDED: runtime.*, tools.*, human_label
- PURPOSE: 批量统计（平均/分位/指标分布）

4) process
- REQUIRED: sample_id, input, trace.steps
- RECOMMENDED: runtime.*, tools.*
- PURPOSE: 多步骤流程成功率、步骤耗时、工具稳定性

5) multi_turn_conversation
- REQUIRED: sample_id, input (包含 turns), output (包含 turns)
- RECOMMENDED: trace.steps, runtime.* (可按 turn 记录)
- PURPOSE: 多轮一致性、上下文召回、连贯度评估

--------

## 五、平台需追踪的核心指标（Metrics）与计算方法

说明：每个指标区分两级：Sample-level（单样本计算）与 Task-level（聚合计算）。

1. response_time_ms
- 描述：Agent 响应总耗时（毫秒）。
- sample: runtime.response_time_ms
- task aggregation: avg, median, p95
- formula: avg = mean(runtime.response_time_ms)
- 单位：ms

2. token_usage
- 描述：tokens_input / tokens_output / total_tokens
- sample: runtime.tokens_input, runtime.tokens_output
- task aggregation: sum, avg

3. success_rate
- 描述：成功率（binary或定义的成功判定）
- sample: runtime.success (1/0)
- task aggregation: success_rate = sum(success)/N

4. error_rate
- 描述：有 error 字段的样本占比
- sample: boolean(runtime.error != null)
- task aggregation: error_rate = sum(has_error)/N

5. process_step_count (process 模式)
- sample: len(trace.steps)
- task aggregation: avg, max

6. tool_call_success_rate
- sample: fraction of tool_calls where success == true
- task aggregation: avg(tool_call_success_rate)

7. answer_relevancy / faithfulness / context_recall (RAG & LLM-judge 输出)
- sample: judge 返回的数值（0-1 或 0-5，平台需归一化到 0-1）
- aggregation: avg, std, p-value vs baseline
- 说明：若judge返回0-5，normalize = value/5

8. llm_judge_* 系列（若启用 LLM 评估）
- 描述：包括 reasoning, safety, hallucination 等子指标
- sample: raw scores 与 normalized_scores
- aggregation: avg, median, confidence interval

9. cost_usd
- sample: runtime.cost_usd
- task aggregation: sum, avg

10. custom metrics
- 平台允许自定义指标（metric_templates），需在任务 config 中声明并指出来源键或脚本计算方法

--------

## 六、指标聚合与报告输出格式（Task-level）

TaskReport ::= Object {
  task_id: integer,
  total_samples: integer,
  completed_samples: integer,
  failed_samples: integer,
  metrics: { metric_name: MetricAggregate },
  timeline: array[Timepoint],
  findings: array[string]
}

MetricAggregate ::= Object {
  avg: number,
  median: number OPTIONAL,
  p95: number OPTIONAL,
  sum: number OPTIONAL,
  std: number OPTIONAL
}

Timepoint ::= Object {
  timestamp: timestamp,
  progress: number (0-100),
  live_metrics: object
}

--------

## 七、预警规则（示例 DSL）

AlertRule ::= Object {
  id: string,
  metric: string REQUIRED,
  comparator: enum( ">", "<", ">=", "<=", "==" ) REQUIRED,
  threshold: number REQUIRED,
  window: integer OPTIONAL,   # 以样本数或分钟为单位
  action: string OPTIONAL     # 如: notify/email/webhook
}

默认建议：
- avg_response_time_ms > 1500 -> WARN
- success_rate < 0.80 -> CRITICAL
- error_rate > 0.20 -> CRITICAL

--------

## 八、示例：Batch 样本 JSON（符合 DSL）

{
  "sample_id": "s_0001",
  "input": {"question": "RAG 是什么？"},
  "output": {"text": "RAG = Retrieval-Augmented Generation"},
  "reference": {"text": "Retrieval-Augmented Generation"},
  "runtime": {"response_time_ms": 321, "tokens_input": 12, "tokens_output": 34, "success": true},
  "tools": {"tool_calls": [{"name":"search","success":true,"latency_ms":45}]},
  "trace": {"steps": [{"step_index":1,"step_name":"retrieve","latency_ms":45}]}
}

--------

## 九、Best practices
- Agent 输出应优先保证结构化字段（sample_id/runtime/output），这样平台能自动落库与计算。
- 对于 LLM-judge 或自定义指标，返回原始分数同时提供归一化分数或说明归一化规则。
- 对于多轮对话，建议在 input/output 中包含 turns 数组，且每个 turn 带有响应时间与 token 使用量。
- 批量上传数据时使用 `samples` 数组，Platform 会按样本逐条评估并生成独立 result 记录。

--------

## 十、向后兼容与扩展
- 所有新增字段应为 OPTIONAL，避免破坏旧 Agent 输出。
- 平台将尽量从 `raw_data` 字段中回退找关键键（如 response_time_ms / tokens），但推荐遵守 DSL。

--------

文档结束。