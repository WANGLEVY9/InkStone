# 系统配置页面设计（LLM 密钥与模型参数配置）

Date: 2026-05-15

## Problem

当前 LLM 配置（`ANTHROPIC_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL` 等）完全依赖后端 `.env` 文件，用户无法通过前端界面查看或修改。这带来几个问题：

1. 部署后修改配置需要直接编辑服务器上的 `.env` 文件并重启服务
2. 密钥是否已设置、当前使用的模型是什么，用户无从知晓
3. 错误配置（如填错 URL 或 API Key）只能在实际生成内容时才发现

## Goals

1. 提供一个独立的系统配置页面，支持配置以下 6 个字段：
   - `LLM_BASE_URL` — LLM 服务基础 URL
   - `ANTHROPIC_API_KEY` — Anthropic API 密钥
   - `LANGSMITH_API_KEY` — LangSmith API 密钥（可选）
   - `LANGSMITH_TRACING` — 是否启用 LangSmith 追踪
   - `LLM_MODEL` — 模型名称
   - `LLM_MAX_TOKENS` — 最大 token 数
2. 配置保存在 SQLite 数据库中，修改后立即生效（运行时热更新），无需重启服务
3. API 密钥在前端以密码框显示，后端返回时做脱敏处理
4. 提供「测试连接」功能，让用户在保存后验证配置是否正确
5. 当 LLM 调用因配置缺失而失败时，前端给出清晰的引导提示

## Key Decisions

| 决策 | 选择 | 说明 |
|------|------|------|
| 配置范围 | 全局 | 不绑定到项目，所有项目共用同一套 LLM 配置 |
| 持久化方式 | SQLite | `app_config` 表存储 key-value，运行时热更新 |
| 配置来源 | 数据库唯一 | 不再读取 `.env` 作为 fallback；未配置时后端抛异常，前端引导用户去设置 |
| 前端入口 | IconSidebar 底部 | 在项目设置按钮下方新增「系统设置」图标，始终可见 |
| 页面布局 | SystemLayout | 不复用 AppLayout，但风格保持一致（IconSidebar + Content） |
| 安全策略 | B（密码框 + 脱敏返回） | GET 返回 `sk-a...xyz`，前端 placeholder 提示已设置；留空提交则保留原值 |
| 更新 API 方法 | POST | 复用项目现有风格（`POST /{resource}/update`） |

## Backend Design

### Database Schema

在 `backend/app/db/schema.sql` 新增表：

```sql
CREATE TABLE IF NOT EXISTS app_config (
    key   TEXT PRIMARY KEY NOT NULL,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

6 个 key 固定：
- `llm_base_url`
- `anthropic_api_key`
- `langsmith_api_key`
- `langsmith_tracing` — 存 `"true"` 或 `"false"`
- `llm_model`
- `llm_max_tokens` — 存字符串形式的数字

value 统一 TEXT 存储，读取时按 key 做类型转换。

### API Routes

新增 `backend/app/api/v1/config.py`：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/v1/config` | 返回全部配置，敏感字段脱敏 |
| POST | `/api/v1/config/update` | 批量更新；字段传 `__KEEP_EXISTING__` 表示不更新 |
| POST | `/api/v1/config/test` | 用当前数据库配置发一个轻量 LLM 请求，返回连通性结果 |

### Pydantic Models

```python
class ConfigItem(BaseModel):
    key: str
    value: str | int | bool  # 根据 key 转换类型

class ConfigResponse(BaseModel):
    items: list[ConfigItem]

class ConfigUpdateRequest(BaseModel):
    llm_base_url: str | None = None
    anthropic_api_key: str | None = None
    langsmith_api_key: str | None = None
    langsmith_tracing: bool | None = None
    llm_model: str | None = None
    llm_max_tokens: int | None = None

class ConfigTestResponse(BaseModel):
    success: bool
    model: str | None = None
    latency_ms: int | None = None
    error_code: str | None = None
    message: str | None = None
```

### ConfigService

新增 `backend/app/services/config.py`：

- `async get_config(key: str) -> str` — 读取单个配置
- `async get_all_config() -> dict[str, str]` — 读取全部
- `async update_config(updates: dict[str, str]) -> None` — 批量写入 SQLite
- `get_anthropic_api_key() -> str` — 专为 LLM 调用封装，缺失时抛 `ConfigNotSetError`
- 内部维护一个字段类型映射表，用于 `get_all_config()` 时做类型转换

### LLM Client 集成

修改 `backend/app/services/llm.py` 的 `create_llm_client()`：

1. 不再直接读 `os.getenv`，改为调用 `ConfigService`
2. 每次调用都读最新数据库值，实现热更新
3. `api_key` 为空或缺失时，抛 `ConfigNotSetError`
4. `LLM_TIMEOUT`、`LLM_MAX_TOKENS` 等原先从环境变量读的字段，统一改为从 `ConfigService` 读

### 脱敏处理

在 API 响应中，对 `anthropic_api_key` 和 `langsmith_api_key` 做脱敏：

- 值长度小于 8 位时返回 `***`
- 否则返回前缀 4 位 + `...` + 后缀 4 位（如 `sk-a...xyz`）

### 错误分类

新增错误码：

- `config_not_set` — 配置项未设置（HTTP 422）
- `config_test_failed` — 测试连接失败（HTTP 422），错误详情在响应 body 中

## Frontend Design

### 路由与布局

- 新路由 `/settings`
- 新建 `frontend/src/components/layout/SystemLayout.tsx`，结构参考 `AppLayout` 但精简：
  - 只保留 `IconSidebar`
  - 去掉 `SecondaryNav`、`ProjectLoader`、`ChatProvider`、`DrawerChat`
  - Content `marginLeft` 为 64（仅 IconSidebar 宽度）
- `App.tsx` 注册：

```tsx
<Route element={<SystemLayout />}>
  <Route path="/settings" element={<SystemSettings />} />
</Route>
```

### IconSidebar 修改

`frontend/src/components/layout/IconSidebar.tsx`：

- 在底部新增「系统设置」按钮（使用 `ToolOutlined` 或 `ApiOutlined` 图标），**始终可见**
- 位置在项目设置按钮**下方**（更靠近底部）
- 点击跳转 `/settings`
- 需确保 `useProjectContext` 在无 Provider 时能优雅降级（`currentProject` 返回 `null`），因为 `SystemLayout` 不提供 `ProjectContext`

### 页面结构

新建 `frontend/src/pages/settings/SystemSettings.tsx`，风格与 `ProjectSettings` 保持一致：

- 使用 `PageContainer` 包裹
- 使用 `PageHeader title="系统设置" subtitle="LLM 配置"`
- Ant Design `Form` 垂直布局，`maxWidth: 600`
- 6 个字段按下方表格渲染

| 字段 | 组件 | 校验规则 |
|------|------|----------|
| LLM Base URL | Input | required, URL 格式 |
| Anthropic API Key | Input.Password | required |
| LangSmith API Key | Input.Password | — |
| LangSmith Tracing | Switch | — |
| LLM Model | Input | required |
| LLM Max Tokens | InputNumber | required, min=1 |

- 底部按钮组：`保存`（primary）+ `测试连接` + `返回`
- 无「危险操作」分区

### 脱敏交互

- GET 接口返回脱敏值（如 `sk-a...xyz`）
- 密码输入框 placeholder 显示 `"已设置 (sk-a...xyz)"`，框内初始为空字符串
- 用户留空提交 → 前端将该字段替换为 `__KEEP_EXISTING__` 后 POST
- 用户输入新值 → 传新值
- 非敏感字段正常显示和编辑

### 测试连接

- 「测试连接」按钮在表单有未保存修改时 **disabled**
- 点击后调用 `POST /api/v1/config/test`
- 成功：绿色 message.success，显示「连接成功，延迟 xxx ms」
- 失败：红色 message.error，显示后端返回的 message（如「API key 无效」「URL 不可达」等）

### 未配置引导

- 业务页面（如 Chat、Generate）在收到 `config_not_set` 错误时
- 前端拦截，显示提示：「LLM 配置不完整，请先配置 API 密钥」
- 提供「前往系统设置」按钮，点击跳转到 `/settings`

## Data Flow

### 加载

```
SystemSettings mount
  → GET /api/v1/config
  → 后端读取 app_config 表
  → 敏感字段脱敏 → 非敏感字段原样
  → 前端 form.setFieldsValue()
  → 密码框 placeholder = "已设置 (脱敏值)"
```

### 保存

```
用户点击「保存」
  → form.validateFields()
  → 密码字段为空 → 替换为 __KEEP_EXISTING__
  → POST /api/v1/config/update
  → 后端：__KEEP_EXISTING__ 跳过，其余写入 SQLite
  → 返回更新后的配置（再次脱敏）
  → message.success
```

### 测试连接

```
用户点击「测试连接」（仅在已保存时可用）
  → POST /api/v1/config/test
  → 后端读取数据库 → create_llm_client → 轻量请求
  → 成功/失败 → 返回 ConfigTestResponse
  → 前端 message.success / message.error
```

## Testing

### 后端测试（新建 `backend/tests/test_config_api.py`）

| 测试名 | 验证内容 |
|--------|---------|
| `test_get_config_returns_masked_keys` | 敏感字段脱敏，非敏感原样 |
| `test_get_config_empty_initially` | 空表时返回空值，不报错 |
| `test_update_config_persists_values` | 写入后数据库正确 |
| `test_update_config_keep_existing` | `__KEEP_EXISTING__` 跳过 |
| `test_update_config_partial` | 部分字段更新，其余不变 |
| `test_llm_client_reads_from_db` | 修改数据库后 create_llm_client 读最新值 |
| `test_llm_client_raises_when_unconfigured` | 缺失时抛 ConfigNotSetError |
| `test_test_endpoint_success` | mock LLM 成功返回 success |
| `test_test_endpoint_auth_failure` | mock 401 返回对应 error_code |

### 前端

- TypeScript 类型检查通过
- 手动验证关键交互：加载、保存、脱敏显示、占位符行为、测试连接、校验提示

## Risks & Notes

1. **IconSidebar 与 ProjectContext**：`SystemLayout` 不提供 `ProjectContext`，需确保 `IconSidebar` 中 `useProjectContext()` 在缺失 Provider 时不抛异常（可通过给 hook 加默认值实现）。
2. **ConfigService 初始化**：首次启动时 `app_config` 表为空。业务代码读取不到时抛 `ConfigNotSetError`，由前端引导用户去设置页面。无需预填充默认值。
3. **LangSmith 集成**：`LANGSMITH_API_KEY` 和 `LANGSMITH_TRACING` 当前后端代码中可能没有直接读取（LangChain 可能通过环境变量自动发现）。需要在配置更新后，通过代码显式设置 `langsmith` SDK 或环境变量，确保追踪功能正确开启/关闭。
4. **测试连接开销**：测试请求发送轻量 prompt（如 `"ping"`，`max_tokens=1`），开销极小。
