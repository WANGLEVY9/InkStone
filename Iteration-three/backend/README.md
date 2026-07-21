# Backend - Novel Generator API

基于 FastAPI 的网络小说生成平台后端，使用 langchain/langgraph 实现多 Agent 编排。

## 快速开始

```bash
# 安装依赖
uv sync

# 运行开发服务器
uv run uvicorn app.main:app --reload

# 指定端口
uv run uvicorn app.main:app --reload --port 8000
```

## 项目结构

```
backend/app/
├── main.py              # FastAPI 入口
├── config.py            # 配置（从环境变量读取）
├── api/                 # REST API 路由
│   └── v1/              # API 版本 1
│       ├── chat.py      # 聊天 API
│       └── projects.py   # 项目 API
├── core/                # 核心业务逻辑
│   ├── agent/           # Agent 工具注册表
│   │   └── tools/       # 各 Agent 工具实现
│   ├── graph/           # LangGraph 工作流
│   └── prompts/         # Prompt 模板
├── services/            # 非 Agent 服务
│   ├── content.py      # 内容存储服务
│   ├── llm.py          # LLM 客户端
│   ├── chat_history_repository.py
│   ├── session_repository.py
│   └── project_repository.py
└── db/                  # SQLite 数据库配置
```

## 多 Agent 架构

6 个专用 Agent 协同完成小说生成：

| Agent | 职责 |
|-------|------|
| WorldBuilderAgent | 世界观设定（地理、文化、魔法体系） |
| CharacterAgent | 角色创建、关系图谱、性格一致性 |
| PlotAgent | 故事线、大纲、章节规划 |
| ChapterAgent | 实际写作 |
| ReviewAgent | 质量评估 |
| EditorAgent | 内容修订 |

## 环境变量

```bash
# 必需
DATABASE_URL=sqlite+aiosqlite:///./novel.db
ANTHROPIC_API_KEY=sk-ant-...

# 可选
SECRET_KEY=your-secret-key  # JWT 签名密钥
DEBUG=false
```

## 常用命令

```bash
# 开发
uv run uvicorn app.main:app --reload

# 测试
uv run pytest

# 类型检查
uv run mypy .

# 代码检查 & 格式化
uv run ruff check .
uv run ruff format .
```
