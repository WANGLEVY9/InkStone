# 角色一致性检测数据集

## 概述

用于评估 AI 小说写作 Agent 的角色一致性能力。包含角色设定描述 + 多条台词/行为，判断每条是否符合人设。

## 规模

- **总计目标**: 50 个角色, 500+ 条台词
- **首批种子**: 5 个角色, 50+ 条台词 + 10 条负面样例
- **类型**: 仙侠、都市、西方奇幻、玄幻

## 数据格式

每行一个 JSON 对象（JSONL）包含角色设定 + utterances 数组，详见 `schema.json`。

## 评估维度

| 维度 | 权重 | 说明 |
|------|------|------|
| character_fidelity | 0.35 | 角色 fidelity（核心） |
| world_consistency | 0.15 | 世界观一致性 |
| genre_fidelity | 0.10 | 类型忠实度 |
| faithfulness | 0.10 | 忠实性 |
| hallucination | 0.20 | 幻觉检测 |
| context_recall | 0.10 | 知识召回率 |

## 错误类型

| 标签 | 说明 |
|------|------|
| character_derailment | 言行完全偏离人设 |
| personality_flip | 性格前后矛盾 |
| knowledge_mismatch | 角色知道不应知道的事 |
| speech_style_break | 说话风格不一致 |
| power_level_inconsistency | 实力忽高忽低 |
