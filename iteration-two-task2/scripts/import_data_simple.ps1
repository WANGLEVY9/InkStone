# PowerShell 脚本：导入测试数据到 MySQL（简单版本）
# 使用方法：.\import_data_simple.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Agent 评估平台测试数据导入" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 配置
$sqlFile = "backups\docker-pre-uninstall-20260424-144444\mysql_agent_eval_sample.sql"
$mysqlUser = "agent"
$mysqlPassword = "agent123"
$mysqlDatabase = "agent_eval"
$mysqlHost = "localhost"
$mysqlPort = "3307"

# 检查 SQL 文件
if (-not (Test-Path $sqlFile)) {
    Write-Host "错误：找不到 SQL 文件：$sqlFile" -ForegroundColor Red
    exit 1
}

Write-Host "SQL 文件：$sqlFile" -ForegroundColor Green
Write-Host "目标数据库：$mysqlDatabase@$mysqlHost:$mysqlPort" -ForegroundColor Green
Write-Host ""

# 方法 1: 使用 mysql 命令行工具（如果已安装）
Write-Host "尝试使用 mysql 命令行工具..." -ForegroundColor Yellow

try {
    # 读取 SQL 文件内容
    $sqlContent = Get-Content $sqlFile -Raw -Encoding UTF8
    
    # 构建连接字符串
    $connectionString = "Server=$mysqlHost;Port=$mysqlPort;Database=$mysqlDatabase;User Id=$mysqlUser;Password=$mysqlPassword;"
    
    # 使用 MySQL .NET Connector 导入（如果可用）
    Add-Type -Assembly "MySql.Data" -ErrorAction Stop
    
    $connection = New-Object MySql.Data.MySqlClient.MySqlConnection
    $connection.ConnectionString = $connectionString
    $connection.Open()
    
    Write-Host "✓ 数据库连接成功" -ForegroundColor Green
    
    # 分割 SQL 语句
    $statements = $sqlContent -split '(?m)^;\s*$'
    
    $count = 0
    foreach ($stmt in $statements) {
        if ($stmt.Trim() -ne "") {
            try {
                $command = $connection.CreateCommand()
                $command.CommandText = $stmt
                $command.ExecuteNonQuery() | Out-Null
                $count++
            } catch {
                # 忽略单个语句错误
            }
        }
    }
    
    $connection.Close()
    
    Write-Host "✓ 导入完成！执行了 $count 个 SQL 语句" -ForegroundColor Green
    Write-Host ""
    
} catch {
    Write-Host "✗ mysql 命令行工具不可用，尝试其他方法..." -ForegroundColor Yellow
    Write-Host ""
    
    # 方法 2: 使用 docker exec
    Write-Host "尝试使用 Docker 导入..." -ForegroundColor Yellow
    
    $containerName = docker ps --filter "name=mysql" --format "{{.Names}}" | Select-Object -First 1
    
    if ($containerName) {
        Write-Host "找到 MySQL 容器：$containerName" -ForegroundColor Green
        
        try {
            Get-Content $sqlFile | docker exec -i $containerName mysql -u $mysqlUser "-p$mysqlPassword" $mysqlDatabase
            Write-Host "✓ 数据导入成功！" -ForegroundColor Green
        } catch {
            Write-Host "✗ Docker 导入失败：$_" -ForegroundColor Red
            Write-Host ""
            Write-Host "请手动执行以下命令：" -ForegroundColor Yellow
            Write-Host "Get-Content $sqlFile | docker exec -i $containerName mysql -u $mysqlUser '-p$mysqlPassword' $mysqlDatabase" -ForegroundColor Cyan
            exit 1
        }
    } else {
        Write-Host "✗ 未找到 MySQL 容器" -ForegroundColor Red
        Write-Host ""
        Write-Host "请先启动 Docker 容器：" -ForegroundColor Yellow
        Write-Host "docker compose up -d" -ForegroundColor Cyan
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "导入完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
