# 操作指南

## 1. 快速启动

### 前置条件

- Docker Desktop（已安装并运行）
- Git

验证环境：
```bash
docker version
docker compose version
```

### 一键启动

在项目根目录执行：

```bash
docker compose up -d --build
```

等待所有服务启动后，访问：

| 入口 | URL | 说明 |
|------|-----|------|
| 前端界面 | http://localhost:8081 | 主应用入口 |
| API 文档 | http://localhost:8000/docs | OpenAPI Swagger |
| 健康检查 | http://localhost:8000/api/v1/health/ | 后端可用性 |

### 服务组成

| 服务 | 容器名 | 主机端口 | 说明 |
|------|--------|---------|------|
| mysql | agent_eval_mysql | 3307 | MySQL 8.0 数据库 |
| redis | agent_eval_redis | 6379 | 缓存与消息队列 |
| backend | agent_eval_backend | 8000 | FastAPI 后端 |
| worker | agent_eval_worker | — | Celery 异步 Worker |
| frontend | agent_eval_frontend | — (内部 4173) | Vue 3 开发服务器 |
| nginx | agent_eval_nginx | 8081 | 反向代理统一入口 |

---

## 2. 数据库连接信息

| 项目 | 值 |
|------|-----|
| 主机 | localhost (主机) / mysql (容器内) |
| 端口 | 3307 (主机) / 3306 (容器内) |
| 用户名 | agent |
| 密码 | agent123 |
| 数据库 | agent_eval |
| Root 密码 | root123 |

---

## 3. 配置说明

### 环境变量

通过 `.env` 文件或 `docker-compose.yml` 中的 `environment` 段配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `APP_NAME` | `agent-eval-platform` | 应用名称 |
| `ENV` | `dev` | 运行环境 |
| `API_PREFIX` | `/api/v1` | API 路由前缀 |
| `MYSQL_HOST` | `mysql` | MySQL 主机 |
| `MYSQL_PORT` | `3306` | MySQL 端口 |
| `MYSQL_DB` | `agent_eval` | 数据库名 |
| `MYSQL_USER` | `agent` | 数据库用户 |
| `MYSQL_PASSWORD` | `agent123` | 数据库密码 |
| `REDIS_URL` | `redis://redis:6379/0` | Redis 连接 |
| `CELERY_BROKER_URL` | `redis://redis:6379/1` | Celery 消息队列 |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/2` | Celery 结果后端 |
| `CORS_ORIGINS` | `http://localhost:8081,http://localhost:5173` | 跨域白名单 |
| `USE_CELERY` | `false` | 启用 Celery 异步执行 |
| `RAGAS_ENABLED` | `true` | 启用 Ragas 评估 |
| `OPENAI_API_KEY` | — | OpenAI API 密钥（LLM-Judge 用） |
| `OPENAI_BASE_URL` | — | OpenAI 代理地址（可选） |
| `LLM_JUDGE_MODEL` | `gpt-4o-mini` | LLM 评估模型 |

---

## 4. 高级评测能力

### 启用 Ragas + LLM-as-a-Judge

默认镜像为轻量模式，不安装 `ragas`、`datasets` 等高级依赖。要启用高级评估：

```bash
# Windows PowerShell
$env:INSTALL_ADVANCED = "true"
docker compose up -d --build backend worker

# Linux/macOS
export INSTALL_ADVANCED=true
docker compose up -d --build backend worker
```

同时配置 OpenAI API 密钥：

```bash
# 方式一：.env 文件
echo "OPENAI_API_KEY=sk-xxx" >> .env
echo "OPENAI_BASE_URL=https://api.openai.com/v1" >> .env

# 方式二：环境变量
export OPENAI_API_KEY=sk-xxx
```

### 评分降级机制

| 场景 | 行为 |
|------|------|
| 未安装 `ragas`/`datasets` | Ragas 指标返回固定基线分 |
| 未配置 `OPENAI_API_KEY` | LLM-Judge 使用启发式规则评分 |
| MongoDB 不可用 | 自动降级为内存存储 |

---

## 5. 日常运维

### 查看日志

```bash
docker compose logs -f backend    # 后端日志
docker compose logs -f worker     # Worker 日志
docker compose logs -f nginx      # Nginx 日志
docker compose logs -f mysql      # MySQL 日志
```

### 服务管理

```bash
# 重启单个服务
docker compose restart backend

# 重新构建并启动
docker compose up -d --build backend worker

# 查看所有服务状态
docker compose ps
```

### 停止与清理

```bash
# 停止（保留数据卷）
docker compose down

# 停止并删除数据卷（⚠️ 清空数据库）
docker compose down -v
```

### 数据库迁移

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
```

迁移脚本位于 `backend/alembic/versions/`。

---

## 6. 演示数据

### 初始化演示数据

```bash
# 通过 API 填充演示数据
curl -X POST http://localhost:8000/api/v1/demo/seed
```

### 功能验收流程

1. 打开前端 http://localhost:8081
2. 在"任务管理"页面创建评测任务
3. 配置数据集、评估模式和指标
4. 点击执行，观察任务状态变化
5. 在"结果分析"页面查看评估图表和评分

---

## 7. 常见问题

### Q1: 服务启动失败 / 端口冲突

```bash
# 检查端口是否被占用
netstat -ano | findstr :3306
netstat -ano | findstr :8081

# 修改 docker-compose.yml 中对应的端口映射
```

### Q2: MySQL 长时间 health: starting

首次启动 MySQL 需要初始化数据，等待 1-3 分钟。仍异常时可尝试：
```bash
docker compose down -v
docker compose up -d --build
```

### Q3: 后端无法访问

```bash
docker compose ps            # 确认 backend 是 Up 状态
docker compose logs backend  # 查看启动日志
```

常见原因：MySQL 未就绪（等 MySQL healthy 后再启动 backend）。

### Q4: Nginx 启动失败

```bash
docker compose logs nginx
```

确认 `deploy/nginx/default.conf` 中 `proxy_pass` 指向可达地址。

### Q5: Celery 任务不执行

```bash
docker compose logs worker   # 查看 Worker 日志
docker compose restart redis worker
```

### Q6: Ragas / LLM-Judge 未生效

```bash
# 确认已启用高级依赖
$env:INSTALL_ADVANCED = "true"
docker compose up -d --build backend worker

# 检查 API Key 是否配置
docker compose logs backend | grep "openai"
```

评分返回基线分表示高级评估未生效。

### Q7: 前端空白或 404

```bash
docker compose up -d --build frontend nginx
# 清理浏览器缓存后重试
```

---

## 8. 快速恢复策略

当状态混乱时，按以下顺序恢复：

```bash
docker compose down                    # 停止所有服务
docker compose up -d --build           # 重新构建并启动
docker compose ps                      # 确认所有服务 Up
# 验证
curl http://localhost:8000/api/v1/health/
curl http://localhost:8081/api/v1/health/
```
