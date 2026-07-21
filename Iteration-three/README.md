# 砚台 — AI 网络小说生成平台

基于 LangChain/LangGraph 多智能体协作的中文网络小说辅助创作平台，覆盖世界观设定、角色塑造、大纲设计、章节撰写与内容审阅的完整创作流程。

> **项目演示视频**：https://box.nju.edu.cn/f/70810fe4d5f74223a3b2/

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Vite + Ant Design 6 |
| 后端 | Python 3.13 + FastAPI + Uvicorn |
| Agent 框架 | LangChain + LangGraph |
| LLM | Anthropic Claude（当前唯一支持） |
| 持久化 | SQLite (aiosqlite) 元数据 + Markdown 文件内容 |
| Checkpoint | langgraph-checkpoint-sqlite (AsyncSqliteSaver) |
| 包管理 | uv (Python) / npm (Node) |

## 多 Agent 架构

系统采用 **Orchestrator + 5 个专业子 Agent** 的编排模式，Orchestrator 自动识别用户意图并委托给对应子 Agent：

| Agent | 职责 | 核心工具 |
|-------|------|----------|
| world_builder | 世界观、地理、文化、力量体系 | 创建/编辑/删除设定，查询内容 |
| character | 角色档案、关系网、性格弧光 | 创建/编辑/删除角色，查询内容 |
| plot | 情节大纲、章节目录、细纲设计 | 创建/编辑/删除大纲节点，获取大纲树 |
| chapter | 正文撰写、润色、续写 | 创建/编辑/删除章节，查询内容 |
| review | 质量审阅、一致性检查 | 创建审阅记录，查询内容 |

所有工具通过闭包绑定 `project_id`，确保项目级数据隔离。

## 项目结构

```
├── backend/                # Python/FastAPI 后端
│   ├── app/
│   │   ├── api/v1/         # REST API 路由 (projects, chat, world, characters, outlines, chapters, reviews)
│   │   ├── core/
│   │   │   ├── agent/      # 子 Agent 工厂 + 工具工厂 (tool_factory.py, langchain_subagents.py)
│   │   │   ├── graph/      # LangGraph 编排器 (builder.py, state.py)
│   │   │   ├── prompts/    # 系统提示词模板
│   │   │   ├── errors.py   # AIError 异常分类
│   │   │   └── retry.py    # 指数退避重试
│   │   ├── services/       # 业务服务层 (content, storage, llm, *_repository)
│   │   └── db/             # SQLite 连接管理 + Schema + Checkpointer
│   ├── tests/              # pytest 测试套件
│   └── data/               # 项目创作内容 (Markdown 文件)
├── frontend/               # React 18 前端
│   └── src/
│       ├── api/            # Axios API 客户端
│       ├── components/     # 布局/AI 聊天/通用/卡片组件
│       ├── pages/          # 路由页面 (Dashboard, World, Character, Outline, Chapter, Review)
│       ├── hooks/          # 自定义 Hooks (useProjectChat - SSE 流式处理)
│       ├── contexts/       # React Context (ProjectContext, ChatContext)
│       └── utils/          # 工具函数
├── docs/                   # 项目文档 (需求规格、系统设计、视频脚本)
├── openspec/               # OpenSpec 变更管理
├── start-dev.py            # 一键启动后端 + 前端
└── CLAUDE.md               # Claude Code 开发规范
```

## 快速开始

### 前置要求

- Python 3.13+
- Node.js 20+
- uv（Python 包管理器）
- Anthropic API Key

### 后端

```bash
cd backend
cp .env.example .env          # 填入 ANTHROPIC_API_KEY
uv sync                       # 安装依赖
uv run uvicorn app.main:app --reload   # 启动开发服务器 (localhost:8000)
```

### 前端

```bash
cd frontend
npm install
npm run dev                   # 启动开发服务器 (localhost:5173)
```

前端开发服务器通过 Vite proxy 将 `/api` 请求转发到后端 `localhost:8000`。

### 一键启动（后端 + 前端）

```bash
python start-dev.py           # 后端 (8000) + 前端 (5173)
```

### 运行测试

```bash
cd backend
uv run pytest                           # 全部测试
uv run pytest --cov=app --cov-report=term  # 含覆盖率
uv run mypy app                         # 类型检查
uv run ruff check app tests             # 代码规范
```

## 部署

系统采用**单机部署**，详见 [docs/system-design.md](docs/system-design.md) 第 8 节。

```bash
# 后端
cd backend && uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端构建
cd frontend && npm install && npm run build
# 将 dist/ 交由 Nginx 托管，或由后端直接serve
```

## 相关文档

- [软件需求规格说明书](docs/requirements.md)
- [系统详细设计文档](docs/system-design.md)
- [CLAUDE.md](CLAUDE.md) — 开发规范与架构约束
