# 脚本工具说明

本目录包含 Agent 评估平台的各类工具脚本。

## 📁 目录结构

```
scripts/
├── 导入工具/              # 数据导入相关工具
│   ├── create_correct_sql.py      # 生成正确的 SQL 文件
│   ├── do_import.py               # 标准导入脚本
│   ├── fix_and_import.py          # 修复并导入脚本
│   ├── import_correct.py          # 导入正确文件
│   ├── import_data.bat            # Windows 批处理导入
│   ├── import_mysql_data.ps1      # PowerShell 导入
│   ├── import_now.ps1             # PowerShell 一键导入
│   ├── import_sql.py              # SQL 导入工具
│   ├── run_docker.ps1             # Docker 启动脚本
│   ├── simple_import.py           # 简单导入脚本
│   └── verify_import.py           # 导入验证工具
├── generate_test_data.py          # 生成测试数据
├── generate_full_test_data.py     # 生成完整测试数据
├── import_test_data.py            # API 方式导入数据
└── post_rebuild_validation.py     # 重建后验证工具
```

---

## 🚀 快速使用

### 导入测试数据（推荐）

```bash
# 方法 1: 使用 Python 导入工具
python scripts/导入工具/import_correct.py

# 方法 2: 使用 PowerShell
.\scripts\导入工具\import_mysql_data.ps1

# 方法 3: 使用批处理（Windows）
.\scripts\导入工具\import_data.bat
```

### 生成测试数据

```bash
# 生成基础测试数据
python scripts/generate_test_data.py

# 生成完整测试数据（40 个任务）
python scripts/generate_full_test_data.py
```

---

## 📋 脚本详细说明

### 导入工具

#### Python 脚本

| 脚本 | 功能 | 使用场景 |
|------|------|----------|
| `import_correct.py` | 导入正确的 UTF-8 SQL 文件 | ⭐ 推荐使用 |
| `do_import.py` | 标准导入流程 | 常规导入 |
| `simple_import.py` | 简化版导入 | 快速导入 |
| `fix_and_import.py` | 自动修复编码问题并导入 | 编码错误时使用 |
| `create_correct_sql.py` | 生成正确的 SQL 文件 | 数据生成 |
| `verify_import.py` | 验证导入结果 | 导入后验证 |
| `import_sql.py` | SQL 文件导入 | 通用导入 |

#### PowerShell 脚本

| 脚本 | 功能 | 使用场景 |
|------|------|----------|
| `import_mysql_data.ps1` | MySQL 数据导入 | ⭐ 推荐 PowerShell 用户 |
| `import_now.ps1` | 一键导入 | 快速导入 |
| `run_docker.ps1` | 启动 Docker 容器 | 环境准备 |

#### 批处理脚本

| 脚本 | 功能 | 使用场景 |
|------|------|----------|
| `import_data.bat` | Windows 批处理导入 | Windows 用户 |

### 数据生成

| 脚本 | 功能 | 输出 |
|------|------|------|
| `generate_test_data.py` | 生成基础测试数据 | 8 数据集 +6 策略 +7 指标 |
| `generate_full_test_data.py` | 生成完整测试数据 | 40 个任务 +40 个结果 |
| `import_test_data.py` | 通过 API 导入数据 | 使用后端 API 创建 |

### 验证工具

| 脚本 | 功能 |
|------|------|
| `post_rebuild_validation.py` | 重建后联调验证 |

---

## 🔧 使用示例

### 示例 1: 完整导入流程

```bash
# 1. 启动 Docker 容器
python scripts/导入工具/run_docker.py

# 2. 导入数据
python scripts/导入工具/import_correct.py

# 3. 验证结果
python scripts/导入工具/verify_import.py
```

### 示例 2: PowerShell 一键导入

```powershell
# 使用 PowerShell 脚本一键完成
.\scripts\导入工具\import_mysql_data.ps1
```

### 示例 3: 生成并导入完整数据

```bash
# 1. 生成完整 SQL 文件
python scripts/generate_full_test_data.py

# 2. 导入数据
python scripts/导入工具/import_correct.py

# 3. 验证
python scripts/导入工具/verify_import.py
```

---

## 📖 相关文档

- **数据导入指南**: [docs/导入指南/数据导入指南.md](../docs/导入指南/数据导入指南.md)
- **测试数据说明**: [docs/测试数据/测试数据说明.md](../docs/测试数据/测试数据说明.md)
- **快速启动**: [docs/操作指南/快速启动.md](../docs/操作指南/快速启动.md)

---

## ⚠️ 注意事项

### 1. 编码问题

如果遇到编码错误，请使用：
```bash
python scripts/导入工具/fix_and_import.py
```

### 2. Docker 容器

确保 Docker 容器已启动：
```bash
docker compose up -d
```

### 3. 数据库连接

默认数据库配置：
- 主机：localhost
- 端口：3307 (容器内 3306)
- 用户名：agent
- 密码：agent123
- 数据库：agent_eval

---

## 🆘 故障排查

### 问题 1: 导入失败

**解决**:
1. 检查 Docker 容器状态：`docker compose ps`
2. 查看 MySQL 日志：`docker compose logs mysql`
3. 使用修复脚本：`python scripts/导入工具/fix_and_import.py`

### 问题 2: 找不到容器

**解决**:
```bash
# 启动容器
docker compose up -d

# 等待 15 秒
Start-Sleep -Seconds 15  # PowerShell
sleep 15  # Linux/macOS
```

### 问题 3: 权限错误

**解决**: 以管理员身份运行 PowerShell 或命令提示符

---

## 📚 高级用法

### 自定义导入

可以修改导入脚本中的参数：

```python
# scripts/导入工具/import_correct.py
sql_file = "backups/docker-pre-uninstall-20260424-144444/mysql_agent_eval_correct.sql"
```

### 批量导入

可以编写脚本批量导入多个 SQL 文件：

```python
import subprocess
from pathlib import Path

sql_files = list(Path("backups").glob("*.sql"))
for sql_file in sql_files:
    subprocess.run(f"Get-Content {sql_file} | docker exec -i $container mysql -u agent -pagent123 agent_eval", shell=True)
```

---

**文档版本**: v1.0  
**更新时间**: 2026-04-25  
**状态**: ✅ 可用
