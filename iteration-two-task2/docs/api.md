# API 文档

## 1. 基础信息

- **基础路径**: `http://localhost:8000/api/v1`
- **OpenAPI 文档**: http://localhost:8000/docs
- **响应格式**: JSON

### 统一响应格式

成功响应直接返回对应 Schema（Pydantic 模型）的 JSON，不包裹额外信封。

### 统一错误响应

```json
{
  "code": "HTTP_ERROR | VALIDATION_ERROR | INTERNAL_ERROR | <业务错误码>",
  "message": "错误说明",
  "detail": {},
  "request_id": "uuid"
}
```

| 字段 | 说明 |
|------|------|
| `code` | 错误类型或业务错误码 |
| `message` | 可读错误信息 |
| `detail` | 校验错误详情或上下文 |
| `request_id` | 请求追踪 ID |

---

## 2. 端点总览

| 分组 | 路由前缀 | 说明 |
|------|---------|------|
| 健康检查 | `GET /health/` | 服务可用性检测 |
| Agent 管理 | `/agents` | 注册、查询、更新、删除 Agent |
| 评测任务 | `/tasks` | 评测任务的完整生命周期管理 |
| 评测结果 | `/results` | 结果查询与人工标注 |
| 指标定义 | `/metrics` | 内置/自定义指标管理 |
| 指标模板 | `/metrics/templates` | LLM-Judge 提示词模板与 Webhook 模板 |
| 评估策略 | `/strategies` | 评估策略配置 |
| 数据集 | `/datasets` | 数据集上传、预览、分析 |
| 评测模式 | `/mode-realtime`, `/mode-offline`, `/mode-batch` | 三种评测模式 |
| 演示数据 | `/demo` | 填充演示数据 |

---

## 3. 健康检查

### `GET /health/`

```json
// 响应
{"status": "ok", "database": {"mysql": "up", "mongo": "up"}}
```

---

## 4. Agent 管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/agents` | 获取 Agent 列表 |
| POST | `/agents` | 创建 Agent |
| GET | `/agents/{agent_id}` | 获取 Agent 详情 |
| PUT | `/agents/{agent_id}` | 更新 Agent |
| DELETE | `/agents/{agent_id}` | 删除 Agent |
| POST | `/agents/{agent_id}/test` | 测试 Agent 连通性 |

### `POST /agents`

```json
{
  "name": "客服 Agent",
  "description": "在线客服对话机器人",
  "endpoint": "https://api.example.com/agent/chat",
  "auth_type": "bearer",
  "auth_config": {"token": "sk-xxx"},
  "timeout_ms": 30000,
  "metadata": {"version": "v2.1", "team": "AI"}
}
```

### `POST /agents/{agent_id}/test`

响应：
```json
{
  "ok": true,
  "message": "reachable",
  "status_code": 200
}
```

---

## 5. 评测任务

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/tasks` | 获取任务列表（分页/筛选） |
| POST | `/tasks` | 创建任务 |
| GET | `/tasks/{task_id}` | 获取任务详情 |
| PUT | `/tasks/{task_id}` | 更新任务（draft 状态） |
| DELETE | `/tasks/{task_id}` | 删除任务（软删除） |
| POST | `/tasks/{task_id}/execute` | 执行任务 |
| POST | `/tasks/{task_id}/run` | 执行任务（等价） |
| POST | `/tasks/{task_id}/cancel` | 取消运行中的任务 |
| POST | `/tasks/{task_id}/clone` | 克隆任务 |
| GET | `/tasks/{task_id}/stats` | 获取任务统计摘要 |
| GET | `/tasks/{task_id}/results` | 获取任务结果列表（分页） |
| GET | `/tasks/{task_id}/results/export` | 导出结果（CSV） |
| POST | `/tasks/compare` | 多任务对比 |
| WS | `/tasks/{task_id}/ws` | 任务执行实时进度 |

### 任务状态枚举

```
draft → pending → running → completed
              ↘ failed → cancelled
```

### 评测模式与维度

| 参数 | 可选值 | 说明 |
|------|--------|------|
| `mode` | `result`, `process`, `result_and_process` | 评估模式 |
| `method` | `explicit`, `fuzzy` | 评估方法（fuzzy 启用 LLM-Judge） |
| `dimension` | `effectiveness`, `safety`, `performance` | 评估维度 |

### `POST /tasks`

```json
{
  "name": "客服 Agent v2.1 综合评测",
  "description": "对比基线效果",
  "agent_id": 1,
  "agent_version": "v2.1",
  "dataset_id": "ds_rag_benchmark_v1",
  "mode": "result",
  "method": "fuzzy",
  "dimension": "effectiveness",
  "config": {
    "metrics": ["response_time", "token_usage", "task_success"],
    "strategy": "quality_first",
    "enable_process_trace": true
  },
  "input_payload": {
    "question": "RAG 是什么？",
    "answer": "RAG 是检索增强生成技术...",
    "ground_truth": "RAG 即 Retrieval-Augmented Generation...",
    "contexts": ["RAG combines retrieval and generation."],
    "response_time_ms": 420,
    "token_usage": 980,
    "tool_calls_total": 8,
    "tool_calls_success": 7,
    "task_success": true
  },
  "judge_config": {
    "model": "gpt-4o-mini"
  },
  "run_config": {
    "concurrent_calls": 5,
    "timeout_ms": 30000
  }
}
```

### `GET /tasks?page=1&page_size=10&status=completed`

支持筛选参数：`status`, `method`, `start_time`, `end_time`

### `GET /tasks/{task_id}/stats`

```json
{
  "task_id": 1,
  "result_count": 20,
  "status": "completed",
  "progress": 100,
  "avg_scores": {
    "faithfulness": 0.85,
    "answer_relevancy": 0.91,
    "response_time": 420.5
  }
}
```

### `POST /tasks/compare`

```json
// 请求
{"task_ids": [1, 2, 3]}

// 响应
{
  "summary": {"task_1": {...}, "task_2": {...}},
  "by_metric": {
    "faithfulness": {"task_1": 0.85, "task_2": 0.82},
    "response_time": {"task_1": 420, "task_2": 510}
  }
}
```

### WebSocket 协议

**连接**: `WS /api/v1/tasks/{task_id}/ws`

**服务端推送事件**:

| 事件 | 触发时机 | 数据内容 |
|------|---------|---------|
| `task_init` | 连接建立 | 当前任务完整状态 |
| `task_queued` | 任务入队 | task_id, status=pending |
| `task_started` | 开始执行 | task_id, status=running, progress |
| `task_progress` | 每处理一条样本 | progress, completed_samples, failed_samples |
| `task_completed` | 完成 | task_id, status=completed |
| `task_failed` | 失败 | task_id, status=failed, error_message |
| `task_cancelled` | 取消 | task_id, status=cancelled |

**客户端消息**:
```json
{"type": "ping"}
```
服务端回复: `{"event": "pong"}`

---

## 6. 评测结果

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/results/task/{task_id}` | 获取任务的所有结果 |
| GET | `/results/{result_id}` | 获取单条结果详情 |
| PATCH | `/results/{result_id}/label` | 更新人工标注 |
| POST | `/results/compare` | 多结果对比（兼容旧接口） |

### `PATCH /results/{result_id}/label`

```json
{
  "human_label": {
    "passed": true,
    "note": "人工复核通过",
    "rating": 4
  }
}
```

---

## 7. 指标管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/metrics` | 获取指标列表 |
| POST | `/metrics` | 创建自定义指标 |
| DELETE | `/metrics/{metric_id}` | 删除指标 |

### `POST /metrics`

```json
{
  "name": "my_custom_metric",
  "metric_type": "explicit",
  "logic_type": "builtin",
  "ragas_config": {},
  "description": "示例自定义指标"
}
```

## 8. 指标模板

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/metrics/templates` | 模板列表 |
| POST | `/metrics/templates` | 创建模板 |
| GET | `/metrics/templates/{id}` | 模板详情 |
| PUT | `/metrics/templates/{id}` | 更新模板 |
| DELETE | `/metrics/templates/{id}` | 删除模板 |

## 9. 评估策略

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/strategies` | 策略列表 |
| POST | `/strategies` | 保存策略 |

### `POST /strategies`

```json
{
  "name": "quality_first",
  "weights": {
    "faithfulness": 0.3,
    "answer_relevancy": 0.3,
    "task_success": 0.25,
    "response_time": 0.15
  },
  "metrics": ["faithfulness", "answer_relevancy", "task_success", "response_time"],
  "description": "质量优先策略"
}
```

## 10. 数据集

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/datasets` | 数据集列表 |
| POST | `/datasets/upload` | 上传数据集文件 |
| GET | `/datasets/{dataset_id}` | 数据集详情 |
| GET | `/datasets/{dataset_id}/preview` | 预览前 N 条（默认 20） |
| GET | `/datasets/{dataset_id}/analysis` | 实时分析 |
| DELETE | `/datasets/{dataset_id}` | 删除数据集 |

### `POST /datasets/upload`

- Content-Type: `multipart/form-data`
- 支持格式: `.json`, `.jsonl`, `.csv`
- 响应包含解析后的指标推荐

## 11. 评测引擎输入规范

### `input_payload` 字段说明

| 字段 | 类型 | 说明 | 对应指标 |
|------|------|------|---------|
| `question` | string | 用户输入问题 | Ragas / LLM-Judge |
| `answer` | string | Agent 回答 | Ragas / LLM-Judge |
| `ground_truth` | string | 参考答案 | Ragas / 对比指标 |
| `contexts` | string[] | 检索上下文 | Ragas (context_precision/recall) |
| `response_time_ms` | int | 响应耗时 | response_time |
| `token_usage` | int | Token 消耗 | token_usage |
| `tool_calls_total` | int | 工具调用总数 | tool_call 相关 |
| `tool_calls_success` | int | 成功工具调用数 | tool_call_accuracy |
| `task_success` | bool | 任务是否成功 | task_success |
| `trace` | object[] | 中间步骤追踪 | 运行时指标 |
| `ragas_samples` | object[] | 批量 Ragas 样本 | Ragas 批量评估 |
| `samples` | object[] | 批量样本（每条单独评分） | — |

## 12. 前端 API 封装

前端 API 客户端位于 `frontend/src/api/`：

| 文件 | 主要封装 |
|------|---------|
| `client.ts` | Axios 实例配置 |
| `task.ts` | `listTasks`, `createTask`, `updateTask`, `deleteTask`, `executeTask`, `compareResults` |
| `result.ts` | 结果查询相关 |
| `dataset.ts` | 数据集相关 |
