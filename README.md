# InkStone — 砚台 · AI 辅助网络小说创作平台

> **南京大学 · 软件工程综合实践 III（2026 年春）课程项目**

**InkStone（砚台）** 是一个基于多智能体协作的中文网络小说辅助创作平台，覆盖世界观设定、角色塑造、大纲设计、章节撰写与内容审阅的完整创作流程。项目经历三次迭代，从开源评估到全栈平台再到 Agent 创作能力深度优化，逐步演进。

---

## 项目概览

| 迭代 | 时间 | 核心内容 |
|------|------|---------|
| **迭代一** | 2026.03 | 开源项目分析与评估体系建设（Ragas 框架） |
| **迭代二** | 2026.04–05 | Agent 评估平台全栈开发 + 系统设计文档 |
| **迭代三** | 2026.05–06 | AI 小说创作平台后端（FastAPI + LangGraph）+ Agent 创作能力 12 轮优化 |

---

## 迭代一：开源项目分析与评估

> 目录：`iteration-task-one/`

以 Ragas 开源项目为分析对象，完成：
- **开源软件泛读与标注**：代码结构、架构风格、社区活跃度分析
- **评估指标体系建设**：设计并实现两个评估指标，对目标项目进行量化评估

评估脚本位于 `Part2-evaluation/`，包含两个评估指标的 Python 实现。

---

## 迭代二：Agent 评估平台

> 目录：`Iteration-two-task1/`（平台代码）、`iteration-two-task2/`（迭代二任务二）、`document/迭代二/`（设计文档）

### 评估平台（Iteration-two-task1）

基于 Vue 3 + TypeScript + Vite 的评估平台前端，支持：
- **实时评估模式**：WebSocket 驱动的实时 Agent 评估交互
- **离线追踪模式**：批量提交评估任务的异步处理
- **数据集批量评测**：大规模数据集的自动化评测管道
- **结果可视化**：评估报告的聚合与展示

### 系统设计

`document/迭代二/` 包含完整的设计文档：
- [Agent 系统设计文档](document/迭代二/Agent-系统设计文档.pdf)
- [Agent 需求分析文档](document/迭代二/Agent-需求分析文档.pdf)
- [评估平台文档](document/迭代二/评估平台文档.pdf)
- [CICD 文档](document/迭代二/CICD文档.pdf)

---

## 迭代三：AI 小说创作平台（InkStone / 砚台）

> 目录：`Iteration-three/`

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Vite + Ant Design 6 |
| 后端 | Python 3.13 + FastAPI + Uvicorn |
| Agent 框架 | LangChain + LangGraph |
| LLM | Anthropic Claude |
| 持久化 | SQLite (aiosqlite) + Markdown |
| 包管理 | uv (Python) / npm (Node) |

### 多 Agent 架构

采用 **Orchestrator + 5 个专业子 Agent** 的编排模式：

| Agent | 职责 |
|-------|------|
| **world_builder** | 世界观、地理、文化、力量体系 |
| **character** | 角色档案、关系网、性格弧光 |
| **plot** | 情节大纲、章节目录、细纲设计 |
| **chapter** | 正文撰写、润色、续写 |
| **review** | 质量审阅、一致性检查 |

所有工具通过闭包绑定 `project_id`，确保项目级数据隔离。

### Agent 创作能力优化（12 轮迭代）

> 详见 [Agent 优化文档](document/迭代三/Agent优化文档.md)

2026 年 5 月 10 日至 6 月 18 日，针对 Agent 在**情节连贯性、角色一致性、伏笔与悬念**三大维度上进行了 12 轮系统优化：

| 指标 | 基线 (v0.1) | 最终 (v1.0) | 提升 |
|------|:----------:|:-----------:|:----:|
| task_success | 76.7% | **96.1%** | +19.4% |
| faithfulness | 0.58 | **0.82** | +0.24 |
| context_recall | 0.55 | **0.85** | +0.30 |
| safety | 3.8 | **4.5** | +0.7 |
| response_time | 2,104 ms | **1,590 ms** | -24.4% |

评估数据集规模约 1,180 条评估单元，覆盖 8 种网络小说类型，含 3 个自有数据集（情节连贯性 520 条、角色一致性 290+ 条、伏笔与悬念 370 条）。

### 快速开始

```bash
# 后端
cd backend
cp .env.example .env   # 填入 ANTHROPIC_API_KEY
uv sync
uv run uvicorn app.main:app --reload    # http://localhost:8000

# 前端
cd frontend
npm install
npm run dev                             # http://localhost:5173

# 一键启动
python start-dev.py
```

---

## 文档目录

```
document/
├── 迭代一/          # 开源分析报告（Ragas 源码阅读）
├── 迭代二/          # 需求分析、系统设计、评估平台、CICD 文档
└── 迭代三/          # Agent 优化文档、需求分析、详细设计、会议纪要
```

---

## 致谢

感谢以下同学在本课程项目中的贡献与协作（排名不分先后）：

- **蒋晨俊**（Jiang Chenjun）
- **张斌驰**（Zhang Binchi）
- **叶朝阳**（Ye Chaoyang）

以及所有为本项目提供支持与指导的老师与助教。

---

*南京大学 · 软件工程综合实践 III · 2026 年春*
