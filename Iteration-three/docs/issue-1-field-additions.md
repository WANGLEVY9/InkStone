# Issue #1 后端字段补全说明

本文档面向前端开发者，列出本次后端字段补全的受理与拒绝清单，并为被拒字段提供等价的现有 API 替代方案，便于前端从 mock 切换到真实后端数据。

---

## 受理 / 拒绝清单一览

| 状态 | 表 | 字段 | 对应前端 TS 字段 |
|------|----|------|-----------------|
| 受理 | `projects` | `description` | `Project.description` |
| 受理 | `projects` | `cover_image` | `Project.cover_image` |
| 受理 | `projects` | `word_count` | `Project.word_count` |
| 受理 | `chat_sessions` | `title` | `AgentSession.title` |
| 受理 | `chapters_meta` | `chapter_number` | `Chapter.chapter_number` |
| 受理 | `chapters_meta` | `summary` | `Chapter.summary` |
| 受理 | `chapters_meta` | `published_at` | `Chapter.published_at` |
| 拒绝 | `projects` | `world_setting` | `Project.world_setting` |
| 拒绝 | `world_settings_meta` | `content`（列表项内联） | — |
| 拒绝 | `chapters_meta` | `content`（列表项内联） | — |
| 拒绝 | `characters_meta` | `data` | `Character.data` |

---

## 新增字段详情

### projects 表

#### `description` (TEXT, 默认 `NULL`)
- **对应前端字段**：`Project.description`
- **用途**：项目简介，展示在项目卡片与详情页。
- **写入**：
  - `POST /api/v1/projects/` 请求体可传 `description`。
  - `PATCH /api/v1/projects/{project_id}` 请求体可传 `description`，省略则不变。
- **读取**：`GET /api/v1/projects/{project_id}` 与 `GET /api/v1/projects/` 响应均直接返回 `description` 字段。

#### `cover_image` (TEXT, 默认 `NULL`)
- **对应前端字段**：`Project.cover_image`
- **用途**：封面图 URL 或资源路径，由前端渲染。
- **写入**：仅 `PATCH /api/v1/projects/{project_id}` 可更新（创建时通常无封面）。
- **读取**：单查与列表响应均返回。

#### `word_count` (INTEGER, 默认 `0`)
- **对应前端字段**：`Project.word_count`
- **用途**：项目累计字数，便于前端列表展示。
- **写入**：建议由后端基于 `chapters_meta.word_count` 聚合维护；前端通常**只读**，不在 PATCH 请求中传入。
- **读取**：单查与列表响应均返回。

### chat_sessions 表

#### `title` (TEXT, 默认 `NULL`)
- **对应前端字段**：`AgentSession.title`
- **用途**：会话标题（如「第 3 章修订」），用于会话列表展示。
- **写入**：
  - `POST /api/v1/projects/{project_id}/sessions/` 请求体可传 `title`。
  - 后续若需重命名，使用会话的 PATCH 接口（如未提供则按需新增）。
- **读取**：`GET /api/v1/projects/{project_id}/sessions/` 列表响应中每条会话包含 `title`。

### chapters_meta 表

#### `chapter_number` (INTEGER, 默认 `NULL`)
- **对应前端字段**：`Chapter.chapter_number`
- **用途**：章节顺序号，前端按此排序显示。
- **写入**：
  - `POST /api/v1/projects/{project_id}/chapters/` 请求体可传 `chapter_number`。
  - `POST /api/v1/projects/{project_id}/chapters/{chapter_id}/update` 请求体可传 `chapter_number`。
- **读取**：列表与单查响应均返回。

#### `summary` (TEXT, 默认 `NULL`)
- **对应前端字段**：`Chapter.summary`
- **用途**：章节摘要，列表预览用。
- **写入**：与 `chapter_number` 同样在 create/update 请求体中可选传入。
- **读取**：列表与单查响应均返回。

#### `published_at` (TIMESTAMP, 默认 `NULL`)
- **对应前端字段**：`Chapter.published_at`
- **用途**：章节发布时间。
- **写入**：当章节由 `draft` 转为 `published` 时，前端在 `update` 请求体里显式传入 ISO 8601 时间戳（如 `"2026-05-02T10:00:00"`）。后端目前不会自动填写；如未来需要自动填充，请单独提 issue。
- **读取**：列表与单查响应均返回，未发布章节为 `null`。

### characters_meta（新增 API 端点）

character 模块此前仅存在底层 `ContentService` 与 `characters_meta` 表，缺少 REST API 路由文件 `backend/app/api/v1/characters.py`，本次予以补齐，**风格完全镜像 `world.py`**（POST `/{id}/update` / POST `/{id}/delete`，非 PATCH/DELETE）。

| Method | Path | 用途 |
|---|---|---|
| GET | `/api/v1/projects/{project_id}/characters/` | 列出该项目所有角色（仅元数据，不含 `content`） |
| POST | `/api/v1/projects/{project_id}/characters/` | 创建新角色 |
| GET | `/api/v1/projects/{project_id}/characters/{character_id}` | 取角色详情（含 Markdown `content`） |
| POST | `/api/v1/projects/{project_id}/characters/{character_id}/update` | 更新角色（部分字段） |
| POST | `/api/v1/projects/{project_id}/characters/{character_id}/delete` | 删除角色及其 Markdown 文件 |

#### 请求体字段

- **CreateCharacterRequest**：`name` (str, 必填)、`content` (str, 必填，Markdown 全文)、`summary` (str, 可选，默认空串)。
- **UpdateCharacterRequest**：`name?`、`content?`、`summary?`（皆可选，按 `world.py` 同样的语义——只有提供的字段被更新；`content` 缺省时会被改写为空串，需谨慎）。

#### 响应结构

返回 `characters_meta` 行 + `content` 字段（list 接口除外，list 不返回 `content`）。具体列：`id, project_id, name, file_path, summary, created_at, updated_at, content`。

#### 与前端 `Character` TS 类型的差异

- `Character.id` ← `id`
- `Character.project_id` ← `project_id`
- `Character.name` ← `name`
- `Character.created_at` / `Character.updated_at` ← 同名字段
- `Character.avatar` —— **后端不返回**，本次未引入此列
- `Character.data` —— **后端不返回**，理由参见下文「拒绝的字段：`characters_meta.data`」

#### Markdown 内容存储位置

`backend/data/{project_id}/characters/{character_id}.md`（由 `ContentService.create_character` 自动写入；文件路径回写到 `characters_meta.file_path` 列）。

---

## 拒绝的字段（含替代方案）

### `projects.world_setting`

**为什么拒绝**：`world_settings_meta` 与 `projects` 是 1-to-many 关系（一个项目可有多个世界观）。在 `projects` 表上塞 `world_setting` 列会破坏多世界观语义；且世界观为 Markdown 长文本，应走文件存储而非 DB 列。

**替代方案**：使用现有世界观 API。

```bash
PID=<your_project_id>

# 列出该项目所有世界观（仅元数据，不含 content）
curl http://localhost:8000/api/v1/projects/$PID/world

# 取某个世界观的完整内容
WORLD_ID=<world_id>
curl http://localhost:8000/api/v1/projects/$PID/world/$WORLD_ID
# 响应包含 content 字段（Markdown 全文）
```

> 后续若业务需要「主世界观」概念，可由后端另加 `projects.primary_world_id` 外键解决，请单独提 issue。

### `world_settings_meta.content`（列表内联）

**为什么拒绝**：把 Markdown 内容复制到 DB 列违反「内容存文件、元数据存 DB」的项目架构（参见 `backend/app/services/content.py`，content 是从 `data/{project_id}/...md` 读出再拼到响应里）。

**替代方案**：单条 GET 已包含 `content`。

```bash
curl http://localhost:8000/api/v1/projects/$PID/world/$WORLD_ID
# {
#   "id": "...",
#   "name": "...",
#   "summary": "...",
#   "file_path": "...",
#   "content": "# 阿斯特利亚大陆\n\n地理：..."   ← Markdown 全文
# }
```

### `chapters_meta.content`（列表内联）

**为什么拒绝**：同上，章节正文存放于文件，列表只返回元数据以减小响应体积。

**替代方案**：单条 GET 已包含 `content`。

```bash
CHAPTER_ID=<chapter_id>
curl http://localhost:8000/api/v1/projects/$PID/chapters/$CHAPTER_ID
# 响应里的 content 字段即 Markdown 全文
```

### `characters_meta.data`

**为什么仍然拒绝**：character 模块的 REST API 已于本次落地（参见上方「新增字段详情 → characters_meta（新增 API 端点）」章节），但 `Character.data` 内的结构化字段（age / gender / role / personality / appearance / background / motivation / relationships）涉及独立的 schema 设计与 JSON 列存储；character 内容当前继续以 Markdown 文件形式承载，结构化拆分推迟至专项 issue。

**当前替代方案**：

- **写入**：把 `Character.data` 中的关键文本拼成 Markdown 写到 `content` 字段，例如：

  ```markdown
  # 角色档案
  - **年龄**：19
  - **性别**：女
  - **角色定位**：protagonist

  ## 性格
  冷静、黑客、核心枢纽

  ## 背景
  出生于一个极客家庭...

  ## 动机
  寻找父母在赛博世界留下的指纹
  ```

- **读取**：前端可对约定的小节标题（`## 性格` / `## 背景` / `## 动机` 等）做轻量解析；或临时维持 `Character.data` 的本地 mock 数据，等结构化 schema 上线后再切换真实数据。
- **新增结构化需求**：请另开 issue 跟踪（如 `Character.data.relationships` 关系图、`Character.avatar` 头像 URL 等）。

---

## 验证示例（端到端 curl 脚本）

以下脚本可被前端复制后逐步执行，用于自验各新字段在创建、更新、读取链路上是否端到端连通。

```bash
# 0. 准备
BASE=http://localhost:8000/api/v1

# 1. 创建项目（带 description）
PID=$(curl -s -X POST $BASE/projects/ \
  -H 'Content-Type: application/json' \
  -d '{"name":"测试项目","description":"用于验证 issue #1 新字段"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "项目 ID: $PID"

# 2. PATCH 更新 cover_image
curl -s -X PATCH $BASE/projects/$PID \
  -H 'Content-Type: application/json' \
  -d '{"cover_image":"https://example.com/cover.png"}'

# 3. GET 项目，确认 description / cover_image / word_count 都在响应里
curl -s $BASE/projects/$PID

# 4. 创建带 title 的会话
SID=$(curl -s -X POST $BASE/projects/$PID/sessions/ \
  -H 'Content-Type: application/json' \
  -d '{"title":"第 1 章修订会话"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "会话 ID: $SID"

# 5. 列出会话，确认 title 字段
curl -s $BASE/projects/$PID/sessions/

# 6. 创建带 chapter_number / summary 的章节
CID=$(curl -s -X POST $BASE/projects/$PID/chapters/ \
  -H 'Content-Type: application/json' \
  -d '{"title":"第一章 启程","content":"# 第一章\n\n少年踏上旅途...","chapter_number":1,"summary":"少年离家","word_count":120}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "章节 ID: $CID"

# 7. 列出章节，确认 chapter_number / summary / published_at(null) 字段
curl -s $BASE/projects/$PID/chapters/

# 8. 发布章节并显式设置 published_at（后端不会自动填充）
curl -s -X POST $BASE/projects/$PID/chapters/$CID/update \
  -H 'Content-Type: application/json' \
  -d '{"status":"published","published_at":"2026-05-02T10:00:00"}'

# 9. 再次 GET，确认 status 与 published_at 都已更新
curl -s $BASE/projects/$PID/chapters/$CID

# 10. 创建角色（仅 name/content/summary）
CHAR_ID=$(curl -s -X POST $BASE/projects/$PID/characters/ \
  -H 'Content-Type: application/json' \
  -d '{"name":"测试角色","content":"# 角色档案\n\n19 岁,主角","summary":"主角"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "角色 ID: $CHAR_ID"

# 11. 列出角色（不含 content）
curl -s $BASE/projects/$PID/characters/

# 12. 取角色单条详情（含 content）
curl -s $BASE/projects/$PID/characters/$CHAR_ID

# 13. 更新角色 summary
curl -s -X POST $BASE/projects/$PID/characters/$CHAR_ID/update \
  -H 'Content-Type: application/json' \
  -d '{"summary":"主角(更新版)"}'

# 14. 删除角色
curl -s -X POST $BASE/projects/$PID/characters/$CHAR_ID/delete
```

---