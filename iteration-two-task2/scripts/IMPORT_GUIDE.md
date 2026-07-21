# PowerShell 导入数据指南

## 问题说明

PowerShell 不支持 Linux bash 的 `<` 重定向语法，需要使用不同的方法导入 SQL 文件。

## 解决方法

### 方法 1: 使用 PowerShell 管道（推荐）

```powershell
# 1. 找到 MySQL 容器名称
$containerName = docker ps --filter "name=mysql" --format "{{.Names}}" | Select-Object -First 1

# 2. 导入数据
Get-Content backups\docker-pre-uninstall-20260424-144444\mysql_agent_eval_sample.sql | 
  docker exec -i $containerName mysql -u agent -pagent123 agent_eval
```

### 方法 2: 使用导入脚本（最简单）

```powershell
# 在项目根目录运行
cd scripts
.\import_data_simple.ps1
```

### 方法 3: 手动一行命令

```powershell
Get-Content backups\docker-pre-uninstall-20260424-144444\mysql_agent_eval_sample.sql | docker exec -i (docker ps --filter "name=mysql" --format "{{.Names}}" | Select-Object -First 1) mysql -u agent -pagent123 agent_eval
```

### 方法 4: 使用 mysql 命令行工具（如果已安装）

```powershell
# 如果本地安装了 MySQL 客户端
mysql -h localhost -P 3307 -u agent -pagent123 agent_eval < backups\docker-pre-uninstall-20260424-144444\mysql_agent_eval_sample.sql
```

## 验证导入

```powershell
# 验证数据
docker exec -it (docker ps --filter "name=mysql" --format "{{.Names}}" | Select-Object -First 1) mysql -u agent -pagent123 agent_eval -e "
  SELECT 'datasets' as type, COUNT(*) as count FROM dataset_assets
  UNION ALL
  SELECT 'strategies', COUNT(*) FROM evaluation_strategies
  UNION ALL
  SELECT 'metrics', COUNT(*) FROM metric_definitions
  UNION ALL
  SELECT 'tasks', COUNT(*) FROM evaluation_tasks
  UNION ALL
  SELECT 'results', COUNT(*) FROM evaluation_results;
"
```

## 常见错误

### 错误 1: 容器未找到
```
Error response from daemon: No such container
```
**解决**: 确保 Docker 容器已启动
```powershell
docker compose up -d
```

### 错误 2: 数据库不存在
```
ERROR 1049 (42000): Unknown database 'agent_eval'
```
**解决**: 创建数据库
```powershell
docker exec -it mysql mysql -u agent -pagent123 -e "CREATE DATABASE agent_eval CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### 错误 3: 权限拒绝
```
ERROR 1045 (28000): Access denied
```
**解决**: 检查用户名密码是否正确

## 完整导入流程

```powershell
# 1. 确保容器运行
docker compose up -d

# 2. 等待 MySQL 启动（约 30 秒）
Start-Sleep -Seconds 30

# 3. 检查容器状态
docker ps

# 4. 导入数据
Get-Content backups\docker-pre-uninstall-20260424-144444\mysql_agent_eval_sample.sql | 
  docker exec -i (docker ps --filter "name=mysql" --format "{{.Names}}" | Select-Object -First 1) mysql -u agent -pagent123 agent_eval

# 5. 验证
docker exec -it (docker ps --filter "name=mysql" --format "{{.Names}}" | Select-Object -First 1) mysql -u agent -pagent123 agent_eval -e "SHOW TABLES;"
```

## 导入完整数据

```powershell
# 生成完整数据
cd scripts
python generate_full_test_data.py

# 导入
Get-Content mysql_agent_eval_full.sql | 
  docker exec -i (docker ps --filter "name=mysql" --format "{{.Names}}" | Select-Object -First 1) mysql -u agent -pagent123 agent_eval
```

## 清理数据（重新导入前）

```powershell
docker exec -it (docker ps --filter "name=mysql" --format "{{.Names}}" | Select-Object -First 1) mysql -u agent -pagent123 agent_eval -e "
  SET FOREIGN_KEY_CHECKS = 0;
  TRUNCATE TABLE evaluation_results;
  TRUNCATE TABLE evaluation_tasks;
  TRUNCATE TABLE metric_definitions;
  TRUNCATE TABLE evaluation_strategies;
  TRUNCATE TABLE dataset_assets;
  SET FOREIGN_KEY_CHECKS = 1;
"
```
