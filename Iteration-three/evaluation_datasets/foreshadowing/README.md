# 伏笔回收检测数据集

## 概述

用于评估 AI 小说写作 Agent 的伏笔管理能力。包含伏笔句+回收句对，判断是否形成有效回收。

## 规模

- **总计目标**: 500 对
- **首批种子**: 75 对（60 正例 + 15 负面样例）
- **类型**: 仙侠、都市、西方奇幻、玄幻

## 数据格式

每行一个 JSON 对象（JSONL），详见 `schema.json`。

## 评估维度

| 维度 | 权重 | 说明 |
|------|------|------|
| foreshadowing_resolution | 0.35 | 伏笔回收（核心） |
| plot_continuity | 0.20 | 情节连续性 |
| context_recall | 0.20 | 知识召回率 |
| hallucination | 0.25 | 幻觉检测 |

## 错误类型

| 标签 | 说明 |
|------|------|
| unresolved_foreshadowing | 埋下伏笔后未回收 |
| false_release | 伏笔回收牵强 |
| orphan_foreshadowing | 回收从未埋下的伏笔 |
| overly_telegraphed | 伏笔过于明显 |
| retcon_contradiction | 回收修改了伏笔原意 |
