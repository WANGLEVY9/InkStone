# Agent 评估平台 — 文档索引

Agent 评估平台是一个前后端分离的通用 Agent 质量评估系统，支持对各类型 Agent（对话型、工具调用型、RAG 型等）进行系统化、自动化的批量评测与多维分析。

---

## 文档清单

| # | 文档 | 说明 |
|---|------|------|
| 1 | [架构说明](architecture.md) | 系统架构、技术栈、数据模型、核心模块、数据流 |
| 2 | [API 文档](api.md) | 全部 REST 接口、WebSocket 协议、请求/响应契约 |
| 3 | [操作指南](guide.md) | 快速启动、Docker Compose 部署、配置、运维、排障 |
| 4 | [测试套件](tests.md) | 测试结构、运行方式、测试数据说明 |

---

## 快速导航

| 目标 | 入口 |
|------|------|
| 了解项目整体架构 | → [架构说明](architecture.md) |
| 启动开发环境 | → [操作指南 → 快速启动](guide.md#快速启动) |
| 查看所有 API 接口 | → [API 文档](api.md) |
| 运行测试 | → [测试套件](tests.md) |
| 查看项目概况 | → [README.md](../README.md) |

---

## 项目概览

| 项目 | 说明 |
|------|------|
| **定位** | 通用 Agent 评估平台 |
| **架构** | 前后端分离 Web 项目 |
| **后端** | Python FastAPI + SQLAlchemy + Celery |
| **前端** | Vue 3 + TypeScript + Element Plus + Pinia |
| **数据库** | MySQL 8.0（主）、Redis（缓存/队列）、MongoDB（配置，可选） |
| **部署** | Docker Compose（6 个服务） |
| **评估能力** | 显式指标 / Ragas / LLM-as-a-Judge / 维度插件 / 策略加权 |

---

## 常用链接

- **前端入口**: http://localhost:8081
- **API 基础路径**: http://localhost:8000/api/v1
- **OpenAPI 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/v1/health/
