# 测试套件说明

## 1. 测试结构

```
backend/tests/              # 后端单元测试与集成测试
├── conftest.py             # Pytest 配置与 fixtures
├── test_health.py          # 健康检查端点测试
├── test_task_flow.py       # 任务创建→执行→结果完整流程
├── test_dataset_upload.py  # 数据集上传与解析测试
├── test_analysis_service.py        # 分析服务测试
├── test_strategy_metric_endpoints.py  # 策略与指标端点测试
├── test_dimension_scoring.py       # 维度插件评分测试
├── test_phase1_api_alignment.py    # Phase 1 API 对齐测试
├── test_phase2_engine_and_task_contract.py  # Phase 2 引擎与任务契约
└── test_task_websocket.py          # WebSocket 实时推送测试

test/                       # 跨项目集成测试与合同测试
├── conftest.py             # 共享测试配置
├── backend/                # 后端集成测试
│   ├── test_api_end_to_end.py              # API 端到端流程
│   ├── test_dataset_parser_service.py      # 数据集解析服务
│   ├── test_evaluation_engine_helpers.py   # 评估引擎辅助函数
│   ├── test_metric_registry_parametric.py  # 指标注册表参数化测试
│   └── test_mode_eval_service_branches.py  # 三种评测模式分支测试
└── contracts/              # 合同测试
    ├── test_ci_pipeline_contract.py   # CI/CD 流水线契约
    └── test_frontend_contract.py      # 前后端接口契约
```

---

## 2. 运行测试

### 全部测试

```bash
# 在项目根目录
pytest -q test backend/tests
```

### 按目录

```bash
# 仅后端测试
pytest -q backend/tests

# 仅集成测试
pytest -q test

# 仅合同测试
pytest -q test/contracts
```

### 带覆盖率

```bash
pytest -q test backend/tests --cov=backend/app --cov-branch --cov-report=term-missing
```

### HTML 覆盖率报告

```bash
pytest -q test backend/tests --cov=backend/app --cov-report=html
# Windows: start htmlcov/index.html
# macOS:   open htmlcov/index.html
```

---

## 3. 测试分类说明

### 后端测试 (`backend/tests/`)

| 测试文件 | 类型 | 测试内容 |
|---------|------|---------|
| `test_health.py` | 单元 | 健康检查端点返回 `{"status":"ok"}` |
| `test_task_flow.py` | 集成 | 任务创建 → 更新 → 删除完整 CRUD 流程 |
| `test_dataset_upload.py` | 集成 | 数据集文件上传、解析、查询 |
| `test_analysis_service.py` | 单元 | 多结果对比分析的聚合逻辑 |
| `test_strategy_metric_endpoints.py` | 集成 | 策略与指标的 API 端点 |
| `test_dimension_scoring.py` | 单元 | 三个维度插件的评分公式 |
| `test_phase1_api_alignment.py` | 合同 | Phase 1 Agent/指标模板 API 对齐 |
| `test_phase2_engine_and_task_contract.py` | 合同 | Phase 2 评估引擎与任务契约 |
| `test_task_websocket.py` | 集成 | WebSocket 连接、事件推送、心跳 |

### 集成测试 (`test/backend/`)

| 测试文件 | 测试内容 |
|---------|---------|
| `test_api_end_to_end.py` | 完整的 API 调用链路（策略→任务→执行→结果） |
| `test_dataset_parser_service.py` | 多种格式数据集解析与字段映射 |
| `test_evaluation_engine_helpers.py` | 引擎内部辅助函数（`_compute_trace_runtime_scores` 等） |
| `test_metric_registry_parametric.py` | 指标注册表的多种输入组合 |
| `test_mode_eval_service_branches.py` | 三种评测模式（实时/离线/批量）的分支逻辑 |

### 合同测试 (`test/contracts/`)

| 测试文件 | 测试内容 |
|---------|---------|
| `test_ci_pipeline_contract.py` | CI/CD 流水线的输入输出契约 |
| `test_frontend_contract.py` | 前后端 API 接口结构对齐 |

---

## 4. 测试技术细节

### 数据库

- 测试使用 **SQLite 内存数据库**（`conftest.py` 中配置）
- 每次测试独立事务，测试结束后自动回滚
- MongoDB 不可用时自动降级为内存存储

### Fixtures 共享

`conftest.py` 提供：
- `db_session` — SQLAlchemy 数据库会话
- `client` — FastAPI TestClient
- 各模型的基础测试数据

### 依赖安装

```bash
pip install pytest pytest-cov
cd backend && pip install -r requirements.txt
```

---

## 5. 测试覆盖目标

| 模块 | 建议覆盖率 |
|------|-----------|
| `evaluation_engine.py` | ≥ 90% |
| `task_service.py` | ≥ 85% |
| `strategy_service.py` | ≥ 85% |
| `metric_registry.py` | ≥ 85% |
| `dataset_parser_service.py` | ≥ 80% |
| `analysis_service.py` | ≥ 80% |
