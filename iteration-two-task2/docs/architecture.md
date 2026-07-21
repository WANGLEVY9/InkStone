# 系统架构说明

## 1. 项目目录结构

```
iteration-two-task2/
├── backend/                      # FastAPI 后端
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置管理 (Pydantic Settings)
│   │   ├── database.py          # 数据库连接 (MySQL + MongoDB)
│   │   ├── api/v1/
│   │   │   ├── router.py        # 路由聚合
│   │   │   └── endpoints/       # 各资源 API
│   │   ├── models/              # SQLAlchemy 数据模型
│   │   ├── schemas/             # Pydantic 请求/响应模型
│   │   ├── services/            # 业务服务层
│   │   ├── core/                # 核心基础设施 (Celery, 异常处理)
│   │   └── plugins/             # 维度插件扩展
│   ├── tests/                   # 后端单元/集成测试
│   ├── alembic/                 # 数据库迁移
│   └── Dockerfile
├── frontend/                    # Vue 3 前端
│   ├── src/
│   │   ├── api/                # API 客户端封装
│   │   ├── components/         # 通用组件
│   │   ├── composables/        # 组合式函数
│   │   ├── stores/             # Pinia 状态管理
│   │   └── views/              # 页面视图
│   └── package.json
├── deploy/nginx/                # Nginx 反向代理配置
├── test/                        # 跨项目集成/合同测试
├── scripts/                     # 工具脚本
├── docs/                        # 文档
└── docker-compose.yml           # Docker Compose 编排
```

## 2. 技术栈

### 后端

| 组件 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI | 异步高性能 API，自动生成 OpenAPI 文档 |
| ORM | SQLAlchemy 2.0 | 声明式映射，支持 MySQL/SQLite |
| 任务队列 | Celery | 异步评测任务调度 |
| 消息代理 | Redis | Celery Broker / Result Backend |
| 主数据库 | MySQL 8.0 | 结构化数据持久化（任务、结果、模型数据） |
| 配置库 | MongoDB | 评估配置与过程日志（不可用时降级为内存存储） |
| 验证 | Pydantic v2 | 请求/响应数据校验 |
| 迁移 | Alembic | 数据库 Schema 版本管理 |

### 前端

| 组件 | 技术 | 说明 |
|------|------|------|
| 框架 | Vue 3 (Composition API) | 渐进式前端框架 |
| 语言 | TypeScript | 类型安全 |
| UI 库 | Element Plus | 企业级组件库 |
| 状态管理 | Pinia | Vue 3 官方状态管理 |
| 图表 | ECharts + vue-echarts | 数据可视化 |
| 路由 | Vue Router 4 | 前端路由 |
| HTTP | Axios | HTTP 客户端 |
| 构建 | Vite | 快速开发/构建工具 |

### 基础设施

| 服务 | 镜像 | 用途 |
|------|------|------|
| MySQL | mysql:8.0 | 主数据库 |
| Redis | redis:7 | 缓存 / Celery 消息队列 |
| Backend | 自构建 | FastAPI 应用 |
| Worker | 自构建 | Celery 异步 Worker |
| Frontend | node:20-alpine | Vue 3 开发/预览服务 |
| Nginx | nginx:1.27-alpine | 反向代理、统一入口 |

## 3. 数据模型

### 3.1 实体关系

```
Agent ── 1:N ── AgentVersion
                       │
EvaluationTask ── N:1 ─┤
      │ N:1             │
DatasetAsset ───────────┘
      │
      └── 评测结果 (EvaluationResult)
```

### 3.2 核心表

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| `agents` | Agent 配置 | endpoint, auth_type, auth_config, timeout_ms |
| `agent_versions` | Agent 版本快照 | agent_id, version, config_snap |
| `dataset_assets` | 数据集资产 | dataset_id, file_path, parser_summary |
| `evaluation_tasks` | 评测任务 | mode, method, dimension, status, config, metrics, progress |
| `evaluation_results` | 每条样本的评测结果 | task_id, sample_id, metrics_scores, scores, raw_data |
| `metric_definitions` | 自定义指标定义 | name, metric_type, logic_type, ragas_config |
| `metric_templates` | 指标模板 | type, prompt_template, webhook_url, score_range |
| `evaluation_strategies` | 评估策略 | strategy_id, name, weights |

### 3.3 任务状态机

```
draft ──► pending ──► running ──► completed
                │                    │
                └──────► failed ◄────┘
                              │
                              ▼
                          cancelled
```

## 4. 核心模块

### 4.1 API 层 (`app/api/v1/endpoints/`)

| 端点文件 | 路由前缀 | 功能 |
|---------|---------|------|
| `health.py` | `/health` | 健康检查 |
| `agents.py` | `/agents` | Agent CRUD + 连通性测试 |
| `tasks.py` | `/tasks` | 任务 CRUD + 执行/取消/克隆/对比/导出 + WebSocket |
| `results.py` | `/results` | 结果查询 + 人工标注 |
| `metrics.py` | `/metrics` | 指标定义管理 |
| `metric_templates.py` | `/metrics/templates` | 指标模板管理 |
| `strategies.py` | `/strategies` | 策略管理 |
| `datasets.py` | `/datasets` | 数据集上传/预览/分析/删除 |
| `mode_realtime.py` | `/mode-realtime` | 实时评测模式 |
| `mode_offline.py` | `/mode-offline` | 离线追踪模式 |
| `mode_batch.py` | `/mode-batch` | 批量评测模式 |
| `seed.py` | `/demo` | 演示数据填充 |

### 4.2 服务层 (`app/services/`)

| 服务 | 职责 |
|------|------|
| `evaluation_engine.py` | 评测执行引擎：调度各评分模块、聚合结果 |
| `task_service.py` | 任务 CRUD 逻辑 |
| `dataset_parser_service.py` | 数据集文件解析、上传、预览 |
| `analysis_service.py` | 多任务结果对比分析 |
| `strategy_service.py` | 策略查询与管理 |
| `metric_registry.py` | 内置指标注册表 |
| `mode_eval_service.py` | 三种评测模式的业务逻辑 |

### 4.3 评估引擎架构

评估引擎 (`EvaluationEngine`) 按以下顺序处理评测：

```
input_payload
      │
      ├── 1. 显式指标 (Builtin) ─── response_time_ms, token_usage, tool_call_accuracy 等
      ├── 2. 自定义指标 (Custom) ── 从 MetricDefinition 中查找并取值
      ├── 3. Ragas 指标 ────────── answer_relevancy, faithfulness, context_recall
      │       (需要 ragas + datasets 库，否则回退基线分)
      ├── 4. LLM-as-a-Judge ────── reasoning, safety, hallucination, interaction
      │       (需要 OPENAI_API_KEY，否则回退启发式评分)
      ├── 5. 维度插件 (Dimension) ─ 按 effectiveness/safety/performance 计算维度分
      └── 6. 策略加权 (Strategy) ── 按策略权重计算综合分
               │
               ▼
          EvaluationResult
```

### 4.4 评测模式与维度

**模式 (mode)**：
- `result` — 面向结果，关注输入/输出质量，使用 Ragas 评估
- `process` — 面向过程，关注中间步骤、工具调用链
- `result_and_process` — 两者兼顾

**方法 (method)**：
- `explicit` — 仅计算显式指标
- `fuzzy` — 额外执行 LLM-as-a-Judge 模糊评估

**维度 (dimension)**：
- `effectiveness` — 效果维度
- `safety` — 安全维度  
- `performance` — 性能维度

## 5. 数据流

### 任务创建与执行

```
前端 → POST /api/v1/tasks → 创建任务 (status=draft)
  │
  ▼
前端 → POST /api/v1/tasks/{id}/execute
  │
  ├── use_celery=true  ──→ Celery Worker 异步执行
  └── use_celery=false ──→ 同步执行
          │
          ▼
  EvaluationEngine.execute()
          │
          ├── 遍历所有样本
          ├── 计算各维度评分
          ├── 写入 EvaluationResult
          └── WebSocket 广播进度
          │
          ▼
  前端实时展示进度与结果
```

### WebSocket 实时推送

```
客户端 → WS /api/v1/tasks/{task_id}/ws
  │
  ├── 服务器发送 task_init (当前任务状态)
  ├── 服务器发送 task_queued / task_started / task_progress
  ├── 服务器发送 task_completed / task_failed / task_cancelled
  └── 客户端发送 {"type": "ping"} → 服务器回复 {"event": "pong"}
```

## 6. 部署架构

```
用户浏览器
    │
    ▼
Nginx (:8081)
    ├── /api/* → Backend (:8000)
    └── /*     → Frontend (:4173)
                    │
                    ▼
               Backend ←── MySQL (:3306)
                  │   ←── Redis (:6379)
                  │   ←── MongoDB (:27017, 可选)
                  │
                  ▼
              Celery Worker (异步任务)
```

### 端口映射

| 服务 | 容器端口 | 主机端口 |
|------|---------|---------|
| Nginx | 80 | 8081 |
| Backend | 8000 | 8000 |
| Frontend | 4173 | —（内部） |
| MySQL | 3306 | 3307 |
| Redis | 6379 | 6379 |
