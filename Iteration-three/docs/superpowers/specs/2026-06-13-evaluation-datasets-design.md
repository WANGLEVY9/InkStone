# 自有评估数据集设计文档

## 概述

本文档定义了用于评估 AI 小说写作 Agent 质量的自有数据集体系。包含三个核心数据集（情节连贯性、角色一致性、伏笔回收检测），覆盖八种网文类型（仙侠、都市、西方奇幻、玄幻、历史、科幻、悬疑推理、轻小说游戏），总计约 1180 条样本单元。数据集与迭代二评估平台格式兼容，可导入进行自动化评估并生成优化建议。

## 架构概览

```
evaluation_datasets/
├── _shared/                      # 共享定义
│   ├── genre_taxonomy.json       # 类型分类体系
│   ├── dimension_definitions.json # 13个评估维度
│   └── scoring_rubrics.json      # 1-5分评分细则
├── plot_coherence/               # 📚 情节连贯性数据集
├── character_consistency/        # 🎭 角色一致性数据集
└── foreshadowing/                # 🔍 伏笔回收检测数据集
```

## 1. 共享维度体系

### 1.1 类型分类

| 类型标签 | 名称 | 特征关键词 |
|---------|------|-----------|
| `xianxia` | 仙侠/修仙 | 筑基、金丹、元婴、灵根、法宝、渡劫、宗门 |
| `urban` | 都市/现代 | 职场、校园、商战、现实社会、都市 |
| `western_fantasy` | 西方奇幻 | 魔法、骑士、龙、精灵、矮人、剑与魔法 |
| `xuanhuan` | 玄幻/架空 | 异界、系统、升级、血脉、神秘力量 |
| `historical` | 历史/架空历史 | 三国、大明、大唐、穿越、朝堂、争霸 |
| `sci_fi` | 科幻 | 星际、赛博朋克、末世、AI、基因改造 |
| `mystery` | 悬疑/推理 | 推理、刑侦、密室、连环案、灵异 |
| `light_novel` | 轻小说/游戏 | 系统、二次元、电竞、面板、异世界 |

### 1.2 评估维度

| 维度ID | 名称 | 说明 | 归一化 |
|--------|------|------|--------|
| `narrative_coherence` | 叙事连贯性 | 前后情节逻辑是否通顺、因果链是否完整 | raw 1-5 → 0-1 |
| `character_fidelity` | 角色 fidelity | 角色的言行是否符合设定人设 | raw 1-5 → 0-1 |
| `plot_continuity` | 情节连续性 | 事件顺序、时间线是否自洽 | raw 1-5 → 0-1 |
| `foreshadowing_resolution` | 伏笔回收 | 伏笔是否得到有效回收 | 0/1 |
| `world_consistency` | 世界观一致性 | 设定是否前后统一（修为体系、魔法规则不矛盾） | raw 1-5 → 0-1 |
| `genre_fidelity` | 类型忠实度 | 内容是否符合所属类型的核心特征 | raw 1-5 → 0-1 |
| `faithfulness` | 忠实性 | 输出是否忠实于给定上下文/设定 | RAGAS 0-1 |
| `answer_relevancy` | 响应相关性 | 回答是否与问题直接相关 | RAGAS 0-1 |
| `context_recall` | 知识召回率 | 是否成功用到了知识库中的相关设定信息 | RAGAS 0-1 |
| `instruction_following` | 指令遵循度 | 是否准确遵循用户指令中的具体要求 | raw 1-5 → 0-1 |
| `hallucination` | 幻觉检测 | 是否生成了与已有设定冲突的内容 | Agent 0-1 |
| `tool_efficiency` | 工具使用效率 | 工具调用次数是否合理 | Agent raw |
| `reasoning_quality` | 推理质量 | Agent 规划与推理链是否清晰合理 | raw 1-5 → 0-1 |

### 1.3 维度与数据集映射

| 维度 | 情节连贯性 | 角色一致性 | 伏笔回收 |
|------|:---------:|:---------:|:--------:|
| narrative_coherence | ★ 核心 | | |
| character_fidelity | | ★ 核心 | |
| plot_continuity | ★ 核心 | | ★ |
| foreshadowing_resolution | | | ★ 核心 |
| world_consistency | ★ | ★ | |
| genre_fidelity | ★ | ★ | |
| faithfulness | ★ | ★ | |
| context_recall | ★ | ★ | ★ |
| hallucination | ★ | ★ | |
| answer_relevancy | | | |
| instruction_following | | | |
| tool_efficiency | | | |
| reasoning_quality | | | |

### 1.4 评分细则

| 分值 | 标签 | 含义 |
|------|------|------|
| 5 | 优秀 | 完全符合预期，无明显瑕疵 |
| 4 | 良好 | 基本符合，有微小但不影响整体的问题 |
| 3 | 及格 | 存在明显但可接受的不足 |
| 2 | 较差 | 有严重问题，影响阅读体验 |
| 1 | 很差 | 完全不合理或前后矛盾 |

## 2. 数据集一：情节连贯性

### 2.1 实际规模

| 类型 | 正例 | 负面样例 | 小计 |
|------|:---:|:-------:|:----:|
| 仙侠 | 110 | 20 | 130 |
| 都市 | 60 | 20 | 80 |
| 西方奇幻 | 60 | 20 | 80 |
| 玄幻 | 50 | 20 | 70 |
| 历史/架空历史 | 40 | — | 40 |
| 科幻 | 40 | — | 40 |
| 悬疑/推理 | 40 | — | 40 |
| 轻小说/游戏 | 40 | — | 40 |
| 跨类型负面 | — | 40 | 40 |
| **总计** | **440** | **80** | **520** |

### 2.2 Schema

```json
{
  "sample_id": "coherence_{genre}_{id}",
  "genre": "xianxia|urban|western_fantasy|xuanhuan|historical|sci_fi|mystery|light_novel",
  "difficulty": "easy|medium|hard",
  "input": {
    "preceding_context": "string — 前文设定",
    "user_request": "string — 用户指令"
  },
  "output": { "text": "string — Agent 续写内容" },
  "reference": {
    "coherence_score": "int 1-5 — 连贯性评分",
    "rationale": "string — 评分理由",
    "contradiction_types": ["string — 矛盾类型"],
    "expected_behavior": "string — 预期正确行为"
  },
  "evaluation": {
    "narrative_coherence": "int 1-5",
    "plot_continuity": "int 1-5",
    "world_consistency": "int 1-5",
    "genre_fidelity": "int 1-5",
    "faithfulness": "float 0-1",
    "hallucination": "float 0-1",
    "context_recall": "float 0-1"
  },
  "negative_sample": "bool",
  "error_type": "string — 错误类型标签（负面样例专用）"
}
```

### 2.3 错误类型

| 错误类型 | 说明 | 示例 |
|---------|------|------|
| `direct_contradiction` | 与前文直接矛盾 | 前文说不能动武→立刻大战 |
| `world_rule_violation` | 违反世界观规则 | 修仙世界出现现代枪械 |
| `temporal_inconsistency` | 时间线矛盾 | 角色死而复生无合理解释 |
| `character_derailment` | 角色行为不符合已知性格 | 谨慎的主角突然莽撞 |
| `causal_break` | 因果链断裂 | 前因后果缺乏逻辑关联 |
| `genre_drift` | 偏离所属类型特征 | 仙侠文突然变成科幻 |
| `deus_ex_machina` | 机械降神，缺乏合理铺垫 | 必败时突然天降神力解决一切 |
| `plot_hole` | 情节漏洞，逻辑无法自圆其说 | 主角被困密室却凭空出现在城外 |
| `emotional_inconsistency` | 情感反应与场景不符 | 战友牺牲时主角无动于衷 |
| `pacing_issue` | 节奏失调，关键情节仓促或拖沓 | 决战一章结束，日常描写十章 |
| `information_asymmetry` | 信息不对称，角色知道不应知道的信息 | 主角预知尚未发生的阴谋 |
| `dangling_thread` | 剧情线悬而未决 | 副线剧情展开后无交代 |

### 2.4 评估策略权重

```json
{
  "weights": {
    "narrative_coherence": 0.25,
    "plot_continuity": 0.20,
    "world_consistency": 0.15,
    "genre_fidelity": 0.10,
    "faithfulness": 0.15,
    "hallucination": 0.15
  }
}
```

## 3. 数据集二：角色一致性

### 3.1 实际规模

每个角色档案包含 10 条台词/行为，每条标注是否符合人设及理由。

| 类型 | 角色数量 | 台词/行为数量 | 负面样例 |
|------|:-------:|:------------:|:-------:|
| 仙侠 | 3 | 30 | — |
| 都市 | 3 | 30 | — |
| 西方奇幻 | 2 | 20 | — |
| 玄幻 | 3 | 30 | — |
| 历史/架空历史 | 3 | 30 | — |
| 科幻 | 3 | 30 | — |
| 悬疑/推理 | 3 | 30 | — |
| 轻小说/游戏 | 3 | 30 | — |
| 独立负面 | — | — | 50 |
| **总计** | **23** | **230** | **50** |

> **注**：每条 profile JSONL 行包含 10 句台词嵌入在一个 profile 对象中，因此 23 个 profile = 230 条台词 + 50 条独立负面 = 290 条内容单元。

### 3.2 Schema

```json
{
  "sample_id": "char_{genre}_{id}",
  "genre": "xianxia|urban|western_fantasy|xuanhuan|historical|sci_fi|mystery|light_novel",
  "character_profile": {
    "name": "string — 角色名",
    "age": "int",
    "identity": "string — 身份/修为/职业",
    "personality": "string — 性格描述",
    "background": "string — 背景故事",
    "speaking_style": "string — 说话风格",
    "core_traits": ["string — 核心特质列表"],
    "relationships": { "entity": "关系描述" }
  },
  "utterances": [
    {
      "utterance_id": "string",
      "context": "string — 发言情境",
      "text": "string — 台词/行为",
      "is_consistent": "bool — 是否符合人设",
      "rationale": "string — 判断理由",
      "error_type": "string — 错误类型（负面样例专用）"
    }
  ],
  "evaluation_summary": {
    "character_fidelity": "float — 平均分",
    "world_consistency": "float",
    "hallucination": "float",
    "consistency_rate": "float — 符合人设比例"
  }
}
```

### 3.3 错误类型

| 错误类型 | 说明 | 示例 |
|---------|------|------|
| `character_derailment` | 言行完全偏离人设 | 清冷角色突然话痨 |
| `personality_flip` | 性格前后矛盾 | 谨慎角色突然冒进 |
| `knowledge_mismatch` | 角色知道不应该知道的事 | 从不下山的角色知道凡间流行 |
| `speech_style_break` | 说话风格不一致 | 古风角色突然蹦出网络用语 |
| `power_level_inconsistency` | 实力忽高忽低 | 筑基期打败元婴期 |
| `motivation_gap` | 行为动机缺失或矛盾 | 角色突然背叛但毫无心理铺垫 |
| `relationship_inconsistency` | 人际关系前后矛盾 | 宿敌转眼成了盟友无合理解释 |
| `emotional_flattening` | 情感反应过于平淡，缺乏层次 | 面对至亲离世毫无情绪波动 |
| `character_obsolescence` | 角色功能性边缘化或被遗忘 | 前期核心配角中期后完全消失 |
| `backstory_contradiction` | 背景故事前后不一致 | 角色出身从孤儿变为名门之后 |

### 3.4 评估策略权重

```json
{
  "weights": {
    "character_fidelity": 0.35,
    "world_consistency": 0.15,
    "genre_fidelity": 0.10,
    "faithfulness": 0.10,
    "hallucination": 0.20,
    "context_recall": 0.10
  }
}
```

## 4. 数据集三：伏笔回收检测

### 4.1 实际规模

| 类型 | 正例 | 负面样例 | 小计 |
|------|:---:|:-------:|:----:|
| 仙侠 | 35 | — | 35 |
| 都市 | 35 | — | 35 |
| 西方奇幻 | 35 | — | 35 |
| 玄幻 | 35 | — | 35 |
| 历史/架空历史 | 35 | — | 35 |
| 科幻 | 35 | — | 35 |
| 悬疑/推理 | 35 | — | 35 |
| 轻小说/游戏 | 35 | — | 35 |
| 原始种子样本 | 60 | 15 | 75 |
| 负面混合 | — | 75 | 75 |
| **总计** | **340** | **90** | **430** |

### 4.2 Schema

```json
{
  "sample_id": "foreshadow_{genre}_{id}",
  "genre": "xianxia|urban|western_fantasy|xuanhuan|historical|sci_fi|mystery|light_novel",
  "pair_type": "valid_release|unresolved|false_release|orphan_foreshadowing",
  "foreshadowing": {
    "chapter_number": "int — 埋下章节",
    "text": "string — 伏笔句",
    "context": "string — 情境",
    "foreshadowing_type": "object_plot_device|character_secret|lore_mystery|prophecy",
    "subtlety_level": "low|medium|high"
  },
  "resolution": {
    "chapter_number": "int 或 null（未回收）",
    "text": "string — 回收句 或 空",
    "context": "string",
    "resolution_type": "power_up|reveal|callback|none",
    "satisfaction": "int 1-5"
  },
  "evaluation": {
    "foreshadowing_resolution": "0 或 1",
    "plot_continuity": "int 1-5",
    "context_recall": "float 0-1",
    "hallucination": "float 0-1",
    "is_valid_pair": "bool",
    "gap_chapters": "int 或 null",
    "error_type": "string（负面样例专用）"
  }
}
```

### 4.3 错误类型

| 错误类型 | 说明 |
|---------|------|
| `unresolved_foreshadowing` | 埋下伏笔后全本未回收 |
| `false_release` | 伏笔回收牵强附会 |
| `orphan_foreshadowing` | 回收了一个从未埋下的伏笔 |
| `overly_telegraphed` | 伏笔过于明显，失去悬念 |
| `retcon_contradiction` | 回收时修改了伏笔原意 |
| `mistimed_release` | 回收时机不当，过早或过晚 |
| `underutilized_payoff` | 伏笔回收效果不足，与铺垫不匹配 |
| `fake_tension` | 虚假紧张，制造悬念但无实质风险 |
| `contradictory_payoff` | 回收结果与伏笔暗示方向矛盾 |
| `repetitive_foreshadowing` | 同一伏笔反复暗示过度重复 |

### 4.4 评估策略权重

```json
{
  "weights": {
    "foreshadowing_resolution": 0.35,
    "plot_continuity": 0.20,
    "context_recall": 0.20,
    "hallucination": 0.25
  }
}
```

## 5. 文件结构

```
Iteration-three/evaluation_datasets/
├── _shared/
│   ├── genre_taxonomy.json
│   ├── dimension_definitions.json
│   └── scoring_rubrics.json
│
├── plot_coherence/
│   ├── README.md
│   ├── schema.json
│   ├── eval_strategy.json
│   ├── platform_input.json
│   ├── samples/
│   │   ├── 01_xianxia_easy.jsonl       # 20
│   │   ├── 02_xianxia_medium.jsonl      # 20
│   │   ├── 03_missing.jsonl             # 40 (种子样本)
│   │   ├── 04_urban.jsonl               # 40 (含追加)
│   │   ├── 05_fantasy.jsonl             # 40 (含追加)
│   │   ├── 06_missing.jsonl             # 20 (种子)
│   │   ├── historical.jsonl             # 40
│   │   ├── light_novel.jsonl            # 40
│   │   ├── mystery.jsonl                # 40
│   │   ├── sci_fi.jsonl                 # 40
│   │   ├── urban_append.jsonl           # 20
│   │   ├── western_fantasy_append.jsonl # 20
│   │   ├── xianxia_append.jsonl         # 30
│   │   └── xuanhuan.jsonl               # 50
│   └── negative/
│       ├── 01_xianxia_negative.jsonl    # 20
│       └── 02_mixed_negatives.jsonl     # 80
│
├── character_consistency/
│   ├── README.md
│   ├── schema.json
│   ├── eval_strategy.json
│   ├── platform_input.json
│   ├── profiles/
│   │   ├── 01_xianxia_profiles.jsonl    # 2 profiles
│   │   ├── 02_urban_profiles.jsonl      # 1 profile
│   │   ├── 03_fantasy_profiles.jsonl    # 1 profile
│   │   ├── 04_xuanhuan_profiles.jsonl   # 1 profile
│   │   ├── 05_historical_profiles.jsonl # 3 profiles
│   │   ├── 06_sci_fi_profiles.jsonl     # 3 profiles
│   │   ├── 07_mystery_profiles.jsonl    # 3 profiles
│   │   ├── 08_light_novel_profiles.jsonl# 3 profiles
│   │   ├── 09_xianxia_append.jsonl      # 1 profile
│   │   ├── 10_urban_append.jsonl        # 1 profile
│   │   ├── 11_fantasy_append.jsonl      # 1 profile
│   │   ├── 12_xuanhuan_append.jsonl     # 1 profile
│   │   ├── 13_urban_fill.jsonl          # 1 profile
│   │   ├── 14_fantasy_fill.jsonl        # 1 profile
│   │   └── 15_xuanhuan_fill.jsonl       # 1 profile
│   └── negative/
│       ├── character_negative.jsonl     # 10
│       └── character_negative_02.jsonl  # 40
│
└── foreshadowing/
    ├── README.md
    ├── schema.json
    ├── eval_strategy.json
    ├── platform_input.json
    ├── samples/
    │   ├── 01_xianxia_valid.jsonl       # 15 (种子)
    │   ├── 02_urban_valid.jsonl         # 15 (种子)
    │   ├── 03_fantasy_valid.jsonl       # 15 (种子)
    │   ├── 04_xuanhuan_valid.jsonl      # 15 (种子)
    │   ├── 05_xianxia_append.jsonl      # 20
    │   ├── 06_urban_append.jsonl        # 20
    │   ├── 07_fantasy_append.jsonl      # 20
    │   ├── 08_xuanhuan_append.jsonl     # 20
    │   ├── 09_historical.jsonl          # 35
    │   ├── 10_sci_fi.jsonl              # 35
    │   ├── 11_mystery.jsonl             # 35
    │   └── 12_light_novel.jsonl         # 35
    └── negative/
        ├── 01_unresolved.jsonl          # 5 (种子)
        ├── 02_false_release.jsonl       # 5 (种子)
        ├── 03_orphan.jsonl              # 5 (种子)
        └── 04_mixed_negatives.jsonl     # 75
```

## 6. 评估闭环流程

```
数据集 → 迭代二评估系统 → 评估报告
                              ↓
                          LLM Judge 综合评估
                              ↓
                       优化建议（优劣分析）
                              ↓
                    ┌─ 用户选择 ───────────┐
                    ↓                      ↓
              手动调整Agent        全自动闭环（后续）
                    ↓                      ↓
              再评估 ←────────────── 再评估
```

## 7. 约定与规范

1. 所有时间采用 ISO8601 UTC 字符串
2. 所有数值度量统一为浮点数
3. 所有 `sample_id` 全局唯一，格式：`{dataset}_{genre}_{id}`
4. 每个样本的 `reference` 字段包含人工标注，`evaluation` 字段为各维度评分
5. 负面样例须标注 `error_type`，用于后续自动分类
6. 每条记录为独立 JSON 行（JSONL），每行一个完整样本
