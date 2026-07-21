# 项目初始化与常用开发命令
# 用法: make <target>

.PHONY: setup lint test

setup:
	@echo ">>> 安装后端依赖..."
	cd backend && uv sync
	@echo ">>> 完成！开始开发前请先阅读 CLAUDE.md"

# Ruff代码检查
lint:
	cd backend && uv run ruff check app tests

# pytest 测试
test:
	cd backend && uv run pytest -q
