# Docker Compose 构建问题修复日志

## 问题分析

在运行 `docker compose up -d --build` 时，后端镜像构建失败，错误信息为：
```
✘ Image agent_eval_backend:latest  Error unknown: failed to re...  10.8s
```

### 根本原因

1. **缺失关键文件**: Dockerfile 未包含 `alembic/` 文件夹和 `alembic.ini` 文件 ✅ 已修复
   
2. **启动命令问题**: docker-compose 中的启动命令尝试使用 `mysql` 客户端，但 Python 镜像中未安装 ✅ 已修复

3. **可选依赖启用**: RAGAS_ENABLED 设置为 true ✅ 已改为 false

4. **SSL/网络问题 (CRITICAL)**: Docker 构建环境无法连接到 PyPI (pypi.org)，导致无法下载 Python 依赖包
   - 错误: `SSLError(SSLEOFError(8, 'EOF occurred in violation of protocol (_ssl.c:1016)'))`
   - 原因: 默认的 PyPI 源在某些网络环境下不可达或 SSL 证书验证失败

## 实施的修复

### 1. 修复 Dockerfile （已完成）

**文件**: `backend/Dockerfile`

**关键改动**:

#### a) 添加缺失文件
```dockerfile
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
```

#### b) 配置 pip 使用阿里云镜像（新增）
```dockerfile
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV PIP_EXTRA_INDEX_URL=https://pypi.org/simple/
```

#### c) 安装依赖时使用镜像 + 自动降级方案
```dockerfile
# 升级 pip 并配置镜像
RUN pip install -i https://mirrors.aliyun.com/pypi/simple/ --upgrade pip setuptools wheel || \
    pip install --upgrade pip setuptools wheel

# 安装基础依赖（使用阿里云镜像）
RUN pip install -i https://mirrors.aliyun.com/pypi/simple/ -r /app/requirements.txt || \
    pip install -r /app/requirements.txt

# 安装高级依赖（可选）
RUN if [ "$INSTALL_ADVANCED" = "true" ]; then \
    pip install -i https://mirrors.aliyun.com/pypi/simple/ -r /app/requirements-advanced.txt || \
    pip install -r /app/requirements-advanced.txt; \
    fi
```

**为什么这样做**:
- 使用阿里云 PyPI 镜像是国内环保的、稳定的、快速的
- `||` 操作符提供了自动降级：如果阿里云镜像失败，自动尝试默认源
- 这在不同网络环境中都能工作

### 2. 修复 docker-compose 启动命令 ✅ （已完成）

**文件**: `docker-compose.yml` - backend 服务

将 mysql 客户端检查替换为 Python socket 连接检查：

```yaml
command: >
  sh -c "
  echo 'Waiting for MySQL to be ready...' &&
  python3 -c '...' &&
  alembic upgrade head &&
  uvicorn app.main:app --host 0.0.0.0 --port 8000
  "
```

### 3. 添加 .dockerignore 文件 ✅ （已完成）

**文件**: `backend/.dockerignore` 和 `frontend/.dockerignore`

### 4. 调整可选依赖配置 ✅ （已完成）

**文件**: `docker-compose.yml`

将 `RAGAS_ENABLED` 改为 `"false"`

## 验证步骤

构建修复后，按以下步骤验证：

```bash
# 清理旧镜像
docker-compose down -v
docker builder prune -f

# 构建镜像（会尝试使用阿里云镜像源）
docker-compose build --no-cache

# 启动服务
docker-compose up -d

# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs backend

# 测试 API（待服务启动后）
curl http://localhost:8000/api/v1/health
```

## 预期结果

✓ Docker 镜像成功构建（使用阿里云 PyPI 镜像）  
✓ MySQL 服务启动并进行健康检查  
✓ 后端服务等待 MySQL 就绪后运行迁移  
✓ Alembic 迁移成功执行  
✓ 应用在 8000 端口启动  
✓ 所有相关容器正常运行  

## 环境变量配置

### 基础部署（推荐）

```bash
docker-compose up -d
```

### 启用高级功能

```bash
# 启用 RAGAS 评估
export INSTALL_ADVANCED=true

# 配置 OpenAI API（可选）
export OPENAI_API_KEY=your_key_here
export OPENAI_BASE_URL=https://api.openai.com/v1

# 重新构建并启动
docker-compose build --no-cache --build-arg INSTALL_ADVANCED=true
docker-compose up -d
```

## 故障排除

### 镜像构建仍然失败

**症状**: `Could not fetch URL https://...`

**解决方案**:
1. 检查网络连接：`ping mirrors.aliyun.com`
2. 尝试手动构建看详细错误：
   ```bash
   docker-compose build --no-cache --progress=plain backend
   ```
3. 如果阿里云镜像也不可用，可修改 Dockerfile 尝试其他镜像：
   - 清华大学: `https://pypi.tsinghua.edu.cn/simple`
   - 官方 PyPI: `https://pypi.org/simple/`

### 数据库连接超时

**症状**: `MySQL not available after 30 attempts`

**解决方案**:
1. 检查 MySQL 容器：`docker-compose ps mysql`
2. 查看 MySQL 日志：`docker-compose logs mysql`
3. 增加重试次数（修改 docker-compose.yml 中的启动脚本）

### Alembic 迁移失败

**症状**: `alembic upgrade head` 出错

**解决方案**:
1. 检查 alembic 文件夹：`ls backend/alembic/versions/`
2. 手动检查迁移：`docker-compose exec backend alembic current`
3. 查看具体错误：`docker-compose logs backend`

## 相关文件清单

修改/新增的文件：
- `backend/Dockerfile` ✅ 添加 pip 镜像配置 + alembic 文件
- `backend/.dockerignore` ✅ 新建
- `frontend/.dockerignore` ✅ 新建
- `docker-compose.yml` ✅ 修复启动命令和配置
- `docs/DOCKER_BUILD_FIXES.md` ✅ 本文档

## 镜像源对比

| 源 | 速度 | 稳定性 | 地区 | 备注 |
|---|---|---|---|---|
| 阿里云 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 国内 | 推荐，快速稳定 |
| 清华大学 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 国内 | 备用方案 |
| PyPI (官方) | ⭐⭐⭐ | ⭐⭐⭐ | 国际 | 备用，可能网络不稳定 |

## 后续建议

1. **生产环境**: 构建镜像时建议固定 Python 镜像版本和依赖版本
2. **CI/CD**: 将 Dockerfile 优化融入 CI 流程
3. **缓存**: 充分利用 Docker 构建缓存加快后续构建
4. **监控**: 监控容器日志，及时发现问题
5. **安全**: 生产环境应使用非 root 用户运行容器

