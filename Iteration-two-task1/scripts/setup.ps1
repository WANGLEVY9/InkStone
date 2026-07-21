# Windows PowerShell 环境初始化脚本
# 使用方式: .\scripts\setup.ps1
# （或双击此文件）

$ErrorActionPreference = "Stop"

Write-Host ">>> 安装后端依赖..." -ForegroundColor Cyan
Set-Location backend
uv sync
Set-Location ..

Write-Host ">>> 完成！开始开发前请先阅读 CLAUDE.md" -ForegroundColor Green
