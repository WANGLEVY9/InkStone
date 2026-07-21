# PowerShell 脚本：导入测试数据到 MySQL
# 使用方法：.\import_data.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Agent 评估平台测试数据导入工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 配置
$sqlFile = "backups\docker-pre-uninstall-20260424-144444\mysql_agent_eval_sample.sql"
$mysqlUser = "agent"
$mysqlPassword = "agent123"
$mysqlDatabase = "agent_eval"
$mysqlHost = "localhost"
$mysqlPort = "3307"

# 检查 SQL 文件是否存在
if (-not (Test-Path $sqlFile)) {
    Write-Host "错误：找不到 SQL 文件：$sqlFile" -ForegroundColor Red
    Write-Host "请确保在正确的目录运行此脚本" -ForegroundColor Yellow
    exit 1
}

Write-Host "SQL 文件：$sqlFile" -ForegroundColor Green
Write-Host "数据库：$mysqlDatabase" -ForegroundColor Green
Write-Host "主机：$mysqlHost:$mysqlPort" -ForegroundColor Green
Write-Host ""

# 检查 Docker 容器
Write-Host "正在检查 MySQL 容器..." -ForegroundColor Yellow
$containerName = docker compose ps --format json | ConvertFrom-Json | Where-Object { $_.Service -eq "mysql" } | Select-Object -First 1 -ExpandProperty Name

if (-not $containerName) {
    Write-Host "错误：未找到 MySQL 容器！" -ForegroundColor Red
    Write-Host "请先运行：docker compose up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "找到 MySQL 容器：$containerName" -ForegroundColor Green
Write-Host ""

# 导入数据
Write-Host "正在导入数据..." -ForegroundColor Yellow
Write-Host ""

try {
    # 使用 docker exec 和 Get-Content 导入
    Get-Content $sqlFile | docker exec -i $containerName mysql -u $mysqlUser "-p$mysqlPassword" $mysqlDatabase
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ 数据导入成功！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    # 验证数据
    Write-Host "验证数据..." -ForegroundColor Yellow
    docker exec $containerName mysql -u $mysqlUser "-p$mysqlPassword" $mysqlDatabase -e "
        SELECT 'dataset_assets' as table_name, COUNT(*) as count FROM dataset_assets
        UNION ALL
        SELECT 'evaluation_strategies', COUNT(*) FROM evaluation_strategies
        UNION ALL
        SELECT 'metric_definitions', COUNT(*) FROM metric_definitions
        UNION ALL
        SELECT 'evaluation_tasks', COUNT(*) FROM evaluation_tasks
        UNION ALL
        SELECT 'evaluation_results', COUNT(*) FROM evaluation_results;
    "
    
    Write-Host ""
    Write-Host "完成！" -ForegroundColor Green
    
} catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "✗ 数据导入失败！" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "错误信息：$_" -ForegroundColor Red
    Write-Host ""
    Write-Host "可能的原因：" -ForegroundColor Yellow
    Write-Host "1. MySQL 容器未启动" -ForegroundColor Yellow
    Write-Host "2. 数据库不存在" -ForegroundColor Yellow
    Write-Host "3. SQL 文件格式错误" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
