# 情节连贯性评估数据集

## 概述

用于评估 AI 小说写作 Agent 的情节连贯性能力。包含前文+续写对，由人工标注连贯性评分（1-5分）。

## 规模

- **总计目标**: 1150 对
- **首批种子**: 100 对（80 正例 + 20 负面样例）
- **类型**: 仙侠、都市、西方奇幻、玄幻
- **难度**: easy / medium / hard

## 数据格式

每行一个 JSON 对象（JSONL），详见 `schema.json`。

## 评估维度

| 维度 | 权重 | 说明 |
|------|------|------|
| narrative_coherence | 0.25 | 叙事连贯性（核心） |
| plot_continuity | 0.20 | 情节连续性（核心） |
| world_consistency | 0.15 | 世界观一致性 |
| genre_fidelity | 0.10 | 类型忠实度 |
| faithfulness | 0.15 | 忠实性（RAGAS） |
| hallucination | 0.15 | 幻觉检测 |

## 错误类型

| 标签 | 说明 |
|------|------|
| direct_contradiction | 与前文直接矛盾 |
| world_rule_violation | 违反世界观规则 |
| temporal_inconsistency | 时间线矛盾 |
| character_derailment | 角色行为不符合已知性格 |
| causal_break | 因果链断裂 |
| genre_drift | 偏离所属类型特征 |

## 使用方式

1. 将 `platform_input.json` 中的 samples 数组传入迭代二评估系统
2. 使用 `eval_strategy.json` 配置评估策略
3. 系统输出各维度评分及综合报告
