# Skill 系统前端设计文档

## 背景

后端已实现完整的 skill 系统（`SkillService` + `/skills` API + `load_skill` 工具）。本设计覆盖前端两个需求：

1. **Skill 管理页面**：全局管理技能的增删改查
2. **聊天中 skill 加载展示**：优化 `load_skill` 工具调用在时间线中的渲染

---

## 1. 路由与导航

### 路由

| 路径 | 组件 | 说明 |
|------|------|------|
| `/skills` | `SkillManager` | skill 列表管理页 |
| `/skills/new` | `SkillEdit` | 新建 skill |
| `/skills/:skillName/edit` | `SkillEdit` | 编辑 skill |

所有路由为全局路由，不依赖 `ProjectContext`。

### IconSidebar 新增导航项

在首页下方新增一个导航项：
- 图标：`BookOutlined`
- 标签："技能"
- 激活条件：`location.pathname === '/skills' || location.pathname.startsWith('/skills/')`
- 位置：首页下方，系统设置上方

### 布局

使用 `SystemLayout`（与系统设置相同：左侧 `IconSidebar` + 右侧主内容区）。

---

## 2. Skill 管理页面（`SkillManager`）

### 页面结构

```
PageContainer
├── PageHeader（标题"技能库" + 副标题 + 右上角"新建技能"按钮）
├── Tabs（按 domain 分组）
│   ├── global
│   ├── world
│   ├── character
│   ├── plot
│   ├── chapter
│   └── review
└── 每个 Tab 内：Row/Col 响应式卡片网格
```

### Tabs

使用 Ant Design `Tabs`，tab 顺序固定为：

| domain | 中文名 |
|--------|--------|
| `global` | 全局 |
| `world` | 世界观 |
| `character` | 角色 |
| `plot` | 剧情 |
| `chapter` | 章节 |
| `review` | 审校 |

每个 tab label 显示 domain 中文名 + skill 数量（如 `世界观 (3)`）。

### Skill 卡片

每张卡片显示：
- **标题**：`skill.name`
- **描述**：`skill.description`，2 行截断
- **标签**：`skill.tags` 用 `Tag` 组件展示
- **Domain 徽章**：若 domain 非 `global`，显示小型文本徽章
- **Hover 操作**：编辑（跳转 `/skills/:name/edit`）、删除（触发确认弹窗）

### 空状态

某 domain 下无 skill 时，显示 `Empty` 组件 + "该领域暂无技能"提示。

### 数据获取

页面 mount 时一次性调用 `skillsApi.list()`（不传 domain，获取全部），前端按 `domain` 分组缓存。后续增删改后本地更新列表，不重新请求。

---

## 3. Skill 编辑页面（`SkillEdit`）

### 布局

类似 `ChapterEdit`：独立页面，非弹窗。

```
PageContainer
├── Breadcrumb（技能库 > 新建/编辑）
├── 元数据区
│   ├── name（Input，新建可编辑，编辑 disabled）
│   ├── description（Input.TextArea，2 行）
│   ├── domain（Select）
│   └── tags（Select mode="tags"）
└── MarkdownEditor（vditor，编辑 content）
```

### 元数据字段

| 字段 | 组件 | 校验规则 |
|------|------|----------|
| `name` | `Input` | 必填，kebab-case（`^[a-z0-9]+(-[a-z0-9]+)*$`），编辑时 disabled |
| `description` | `Input.TextArea` | 必填，摘要描述 |
| `domain` | `Select` | 选项：`global` / `world` / `character` / `plot` / `chapter` / `review`，默认 `global` |
| `tags` | `Select` mode="tags" | 可自由输入，支持中文 |

### Content 编辑

使用 `MarkdownEditor`（vditor）编辑 `content`。

### 操作

- **保存**：调用 `skillsApi.create` 或 `skillsApi.update`，成功后 `message.success('保存成功')` 并返回列表
- **返回**：返回 `/skills`

### 新建 vs 编辑

- 新建：`name` 可编辑，页面标题为"新建技能"
- 编辑：`name` 只读，页面标题为技能名，先调用 `skillsApi.get(name)` 加载数据

---

## 4. 聊天中 skill 加载展示

### 当前行为

`load_skill` 属于 `READ_ONLY_TOOLS`，在时间线中显示为"阅"标签 + `<pre>` 纯文本结果。

### 改进

在 `ChatCore.tsx` 的 `TimelineView` 中，对 `load_skill` 工具事件做特殊处理：

**解析**：
```ts
const match = result.match(/^Loaded skill: ([^\n]+)\n\n([\s\S]*)$/);
```

**渲染**：
- 若解析成功：
  - 折叠面板内容第一行显示 skill 名称（`code` 样式高亮）
  - 下方用 `XMarkdown` 组件渲染 skill 内容（Markdown）
  - 保持 `maxHeight: 300` + `overflow: auto`
- 若解析失败：回退到现有 `<pre>` 纯文本展示

**标签不变**：仍显示"阅"标签，保持工具事件一致性。

---

## 5. API Client 与类型

### 新增类型

```ts
export interface Skill {
  name: string;
  description: string;
  domain: string | null;
  tags: string[];
  content?: string;
}

export interface CreateSkillRequest {
  name: string;
  description: string;
  content: string;
  domain?: string | null;
  tags?: string[];
}

export interface UpdateSkillRequest {
  description?: string;
  content?: string;
  domain?: string | null;
  tags?: string[];
}
```

### 新增 API Client

`frontend/src/api/skills.ts`：

```ts
import client from './client';
import type { Skill, CreateSkillRequest, UpdateSkillRequest } from '@/types';

export const skillsApi = {
  list: () => client.get<Skill[]>('/skills/'),
  get: (name: string) => client.get<Skill>(`/skills/${name}`),
  create: (data: CreateSkillRequest) => client.post<Skill>('/skills/', data),
  update: (name: string, data: UpdateSkillRequest) =>
    client.post<Skill>(`/skills/${name}/update`, data),
  delete: (name: string) => client.post(`/skills/${name}/delete`),
};
```

---

## 6. 错误处理

| 场景 | 行为 |
|------|------|
| 列表获取失败 | `message.error('加载技能列表失败')`，显示空状态 |
| 加载 skill 失败 | `message.error('加载技能失败')`，返回列表页 |
| 创建/更新失败 | `message.error('保存失败')`；409 冲突时显示具体错误信息 |
| 删除确认 | `Modal.confirm`："确定要删除技能 `{name}` 吗？此操作不可恢复。" |
| 删除失败 | `message.error('删除失败')` |
| name 格式校验 | 前端正则校验，不合法时提示"名称只能包含小写字母、数字和连字符" |
| 聊天中解析失败 | 静默回退到 `<pre>` 纯文本，不报错 |

---

## 7. 文件清单

### 新增文件

| 文件 | 说明 |
|------|------|
| `frontend/src/api/skills.ts` | Skill API client |
| `frontend/src/pages/skills/SkillManager.tsx` | Skill 列表管理页 |
| `frontend/src/pages/skills/SkillEdit.tsx` | Skill 新建/编辑页 |

### 修改文件

| 文件 | 修改内容 |
|------|----------|
| `frontend/src/types/index.ts` | 新增 `Skill`、`CreateSkillRequest`、`UpdateSkillRequest` |
| `frontend/src/App.tsx` | 新增 `/skills`、 `/skills/new`、 `/skills/:skillName/edit` 路由 |
| `frontend/src/components/layout/IconSidebar.tsx` | 新增"技能"导航项 |
| `frontend/src/components/ai/ChatCore.tsx` | `TimelineView` 中 `load_skill` 特殊渲染 |
