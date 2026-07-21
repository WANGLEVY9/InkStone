# 前端平台设计文档

**日期:** 2026-05-09
**状态:** 待审核

## 概述

基于现有后端 API，构建一个全新的 AI 网络小说创作平台前端。采用 React + Vite + TypeScript + Ant Design 技术栈，提供项目管理、内容编辑、AI 对话等功能。

## 技术栈

| 层级 | 技术 |
|------|------|
| 框架 | React 18 + TypeScript |
| 构建工具 | Vite |
| UI 组件库 | Ant Design 5 |
| 路由 | React Router v6 |
| HTTP 客户端 | Axios |
| Markdown 编辑器 | @uiw/react-md-editor 或类似方案 |
| Frontmatter 解析 | gray-matter |
| 状态管理 | React Context + useReducer（轻量级） |

## 整体布局

采用 **经典侧边栏布局**，使用 Ant Design 的 `Layout` + `Sider` + `Menu` 组件：

```
┌─────────────────────────────────────────────────────────────┐
│  ┌────┐ ┌──────────┐ ┌────────────────────────────────────┐ │
│  │    │ │          │ │                                    │ │
│  │ Sider│ │  Sider   │ │         Content                   │ │
│  │ (dark)│ │ (light)  │ │                                    │ │
│  │ 64px │ │  200px   │ │                                    │ │
│  │      │ │          │ │                                    │ │
│  │ Icon │ │ Menu     │ │                                    │ │
│  │ Menu │ │ items    │ │                                    │ │
│  │      │ │          │ │                                    │ │
│  └────┘ └──────────┘ └────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  FloatButton     │
                    │  (AI 悬浮球)      │
                    └──────────────────┘
```

### Ant Design 组件映射

| 需求 | 推荐组件 | 说明 |
|------|----------|------|
| 整体布局 | `Layout` + `Layout.Sider` | 使用 `collapsible` 支持侧边栏收起 |
| 图标导航栏 | `Menu` (mode="inline", theme="dark") | 左侧深色图标菜单 |
| 功能导航 | `Menu` (mode="inline", theme="light") | 右侧浅色功能菜单 |
| 面包屑 | `Breadcrumb` | 使用 `items` 属性 (>=5.3.0) |
| 项目卡片 | `Card` (hoverable) | 使用 `cover` 渐变背景 |
| 内容列表 | `List` + `List.Item` | 或 `Row` + `Col` 网格 |
| 大纲树 | `Tree` (draggable) | 内置拖拽支持 |
| AI 悬浮球 | `FloatButton` | 使用 `badge` 显示未读消息 |
| 表单 | `Form` + `Input` + `Button` | 标准表单组件 |
| 弹窗 | `Modal` | 确认删除等操作 |
| 消息提示 | `message` / `notification` | 操作反馈 |

### 布局代码结构

```tsx
import { Layout, Menu, theme } from 'antd';

const { Header, Sider, Content } = Layout;

const App = () => {
  const { token: { colorBgContainer, borderRadiusLG } } = theme.useToken();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 左侧图标导航栏 - 深色主题 */}
      <Sider width={64} theme="dark" collapsed={true}>
        <Menu mode="inline" theme="dark" items={iconMenuItems} />
      </Sider>

      {/* 二级功能导航 - 浅色主题 */}
      <Sider width={200} theme="light">
        <Menu mode="inline" defaultSelectedKeys={['world']} items={navItems} />
      </Sider>

      {/* 主内容区 */}
      <Layout>
        <Content style={{ padding: 24, background: colorBgContainer }}>
          <Breadcrumb items={[...]} />
          {/* 页面内容 */}
        </Content>
      </Layout>
    </Layout>
  );
};
```

## 页面路由

| 路径 | 页面 | 描述 |
|------|------|------|
| `/` | Dashboard | 项目仪表盘 |
| `/projects/:id` | ProjectRedirect | 重定向到 `/projects/:id/world` |
| `/projects/:id/world` | WorldList | 世界观管理 |
| `/projects/:id/world/:worldId` | WorldEdit | 世界观编辑 |
| `/projects/:id/characters` | CharacterList | 角色管理 |
| `/projects/:id/characters/:charId` | CharacterEdit | 角色编辑 |
| `/projects/:id/outline` | OutlineEditor | 大纲编辑 |
| `/projects/:id/chapters` | ChapterList | 章节管理 |
| `/projects/:id/chapters/:chapterId` | ChapterEdit | 章节编辑 |
| `/projects/:id/reviews` | ReviewList | 评审报告 |
| `/projects/:id/settings` | ProjectSettings | 项目设置 |

> Note: Skills API (`/api/v1/skills/`) 不在本次前端实现范围内。

## 页面设计

### 1. 项目仪表盘 (`/`)

**布局：** 全宽，无二级导航

**功能：**
- 顶部统计卡片：总项目数、总字数、活跃项目数
- 项目卡片网格（3 列）：
  - 渐变封面背景（默认）或自定义图片
  - 项目名称、描述
  - 统计标签：章节数、角色数
  - 最后编辑时间
- 新建项目卡片（虚线边框 + 加号）
- 搜索框

**API 调用：**
- `GET /api/v1/projects/` - 获取项目列表
- `POST /api/v1/projects/` - 创建项目

### 2. 世界观管理 (`/projects/:id/world`)

**布局：** 标准三栏布局（图标栏 + 二级导航 + 内容区）

**功能：**
- 卡片列表展示所有世界观设定
- 每张卡片显示：名称、摘要、字数、状态标签
- 点击卡片进入编辑页
- 新建设定按钮
- 排序/筛选功能

**API 调用：**
- `GET /api/v1/projects/:id/world/` - 获取世界观列表
- `POST /api/v1/projects/:id/world/` - 创建世界观
- `POST /api/v1/projects/:id/world/:worldId/delete` - 删除世界观

### 3. 世界观编辑 (`/projects/:id/world/:worldId`)

**布局：** 标准三栏布局

**功能：**
- 面包屑导航：世界观 / {名称}
- 标题输入框
- 摘要输入框
- Markdown 工具栏（加粗、斜体、标题、列表等）
- Markdown 编辑器
- 自动保存 / 手动保存按钮

**API 调用：**
- `GET /api/v1/projects/:id/world/:worldId` - 获取详情
- `POST /api/v1/projects/:id/world/:worldId/update` - 更新

### 4. 角色管理 (`/projects/:id/characters`)

**功能：**
- 卡片列表展示角色
- 头像占位符、姓名、简介
- 点击进入编辑页

**API 调用：**
- `GET /api/v1/projects/:id/characters/` - 获取角色列表
- `POST /api/v1/projects/:id/characters/` - 创建角色

### 5. 角色编辑 (`/projects/:id/characters/:charId`)

**功能：**
- 面包屑导航
- 角色名称、简介输入
- Markdown 编辑器编写详细档案
- 保存按钮

**Tags 实现方案：从 Markdown 内容解析**

角色的 tags 存储在 Markdown 内容的 YAML frontmatter 中：

```markdown
---
tags: [主角, 火系, 修仙]
type: 主角
age: 16
---

# 角色名称

角色的详细描述...
```

前端解析逻辑：
```tsx
import matter from 'gray-matter';

const parseCharacterContent = (content: string) => {
  const { data, content: body } = matter(content);
  return {
    tags: data.tags || [],
    type: data.type || '',
    age: data.age || '',
    content: body,
  };
};

// 编辑时重新组装
const serializeCharacterContent = (meta: object, content: string) => {
  return matter.stringify(content, meta);
};
```

**依赖包：**
- `gray-matter` - 解析/序列化 YAML frontmatter

**API 调用：**
- `GET /api/v1/projects/:id/characters/:charId` - 获取详情
- `POST /api/v1/projects/:id/characters/:charId/update` - 更新

### 6. 大纲编辑 (`/projects/:id/outline`)

**功能：**
- 树形结构展示大纲层级
- 拖拽排序（使用 Ant Design `Tree` 组件内置 `draggable`）
- 节点展开/折叠
- 点击节点进入编辑
- 新建节点按钮

**Ant Design Tree 实现：**

```tsx
import { Tree, Button, Dropdown } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';

const OutlineEditor = ({ treeData, onSelect, onDrop }) => {
  // treeData 格式: [{ key, title, children, type, content }]

  const titleRender = (nodeData) => (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <span>{nodeData.title}</span>
      <Dropdown menu={{ items: [
        { key: 'edit', icon: <EditOutlined />, label: '编辑' },
        { key: 'add', icon: <PlusOutlined />, label: '添加子节点' },
        { key: 'delete', icon: <DeleteOutlined />, label: '删除', danger: true },
      ]}}>
        <Button type="text" size="small" icon={<MoreOutlined />} />
      </Dropdown>
    </div>
  );

  return (
    <Tree
      showLine={{ showLeafIcon: false }}
      draggable
      defaultExpandAll
      treeData={treeData}
      titleRender={titleRender}
      onSelect={onSelect}
      onDrop={onDrop}
    />
  );
};
```

**API 调用：**
- `GET /api/v1/projects/:id/outlines/` - 获取根大纲
- `GET /api/v1/projects/:id/outlines/:id/tree` - 获取树结构
- `POST /api/v1/projects/:id/outlines/` - 创建大纲节点
- `POST /api/v1/projects/:id/outlines/:id/update` - 更新
- `POST /api/v1/projects/:id/outlines/:id/delete` - 删除

### 7. 章节管理 (`/projects/:id/chapters`)

**功能：**
- 章节列表（序号、标题、字数、状态）
- 点击进入编辑
- 新建章节

**API 调用：**
- `GET /api/v1/projects/:id/chapters/` - 获取章节列表
- `POST /api/v1/projects/:id/chapters/` - 创建章节

### 8. 章节编辑 (`/projects/:id/chapters/:chapterId`)

**功能：**
- 面包屑导航
- 标题、摘要输入
- 字数统计（实时）
- Markdown 编辑器
- 全屏写作模式切换
- 保存按钮

**API 调用：**
- `GET /api/v1/projects/:id/chapters/:chapterId` - 获取详情
- `POST /api/v1/projects/:id/chapters/:chapterId/update` - 更新

### 9. 评审报告 (`/projects/:id/reviews`)

**功能：**
- 卡片列表展示评审
- 显示：评分、问题数、建议数
- 点击查看详情

**API 调用：**
- `GET /api/v1/projects/:id/reviews/` - 获取评审列表

### 10. 项目设置 (`/projects/:id/settings`)

**功能：**
- 项目名称编辑
- 项目描述编辑
- 封面图上传
- 删除项目（危险操作，需确认）

**API 调用：**
- `GET /api/v1/projects/:id` - 获取项目详情
- `PATCH /api/v1/projects/:id` - 更新项目
- `DELETE /api/v1/projects/:id` - 删除项目

## AI 悬浮球组件 (AIFab)

### Ant Design 实现方案

使用 `FloatButton.Group` + `Popover` 或自定义 Drawer 实现：

```tsx
import { FloatButton, Badge, Drawer } from 'antd';
import { MessageOutlined, CloseOutlined } from '@ant-design/icons';

const AIFab = () => {
  const [open, setOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  return (
    <>
      {/* 悬浮球 */}
      <FloatButton.Group shape="circle" style={{ insetInlineEnd: 24, bottom: 24 }}>
        <Badge count={unreadCount} size="small">
          <FloatButton
            icon={<MessageOutlined />}
            type="primary"
            onClick={() => setOpen(true)}
            tooltip="AI 助手"
          />
        </Badge>
      </FloatButton.Group>

      {/* 聊天面板 - 使用 Drawer 从右侧滑出 */}
      <Drawer
        title="AI 助手"
        placement="right"
        width={400}
        open={open}
        onClose={() => setOpen(false)}
        closable={{ closeIcon: <CloseOutlined /> }}
        styles={{ body: { padding: 0, display: 'flex', flexDirection: 'column' } }}
      >
        {/* 会话选择 */}
        {/* 消息列表 */}
        {/* 输入区 */}
      </Drawer>
    </>
  );
};
```

### 交互设计

**收起状态：**
- 使用 `FloatButton` 组件（Ant Design 内置）
- `type="primary"` 使用主题色
- `badge` 属性显示未读消息数
- `tooltip` 显示"AI 助手"提示

**展开状态：**
- 使用 `Drawer` 组件从右侧滑出（width=400）
- 或使用 `Popover` 弹出面板（更轻量）
- 渐变头部：使用 `Card` 或自定义样式
- 会话选择：`Tabs` 或 `Select` 组件
- 消息列表：`List` + `Comment` 组件
- 输入区：`Input.TextArea` + `Button`

### 消息组件参考

```tsx
import { Comment, Avatar, Collapse, Tag } from 'antd';

// AI 消息
<Comment
  author={<span>AI 助手</span>}
  avatar={<Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#6366f1' }} />}
  content={<div>{message.content}</div>}
  datetime={<span>{time}</span>}
/>

// 用户消息 - 右对齐
<div style={{ display: 'flex', justifyContent: 'flex-end' }}>
  <div className="user-bubble">{message.content}</div>
</div>

// Thinking 折叠块
<Collapse
  size="small"
  items={[{ key: '1', label: 'Thinking...', children: <pre>{thinking}</pre> }]}
/>
```

### 快捷键

- `Ctrl/Cmd + J` - 切换 AI 面板显示
- `Esc` - 收起面板
- `Enter` - 发送消息
- `Shift + Enter` - 换行

### API 调用

- `POST /api/v1/projects/:id/sessions/` - 创建会话
- `GET /api/v1/projects/:id/sessions/` - 获取会话列表
- `DELETE /api/v1/projects/:id/sessions/:sessionId` - 删除会话
- `GET /api/v1/projects/:id/sessions/:sessionId/history` - 获取历史
- `POST /api/v1/projects/:id/sessions/:sessionId/chat/stream` - SSE 流式对话

### 上下文感知

AI 对话时自动携带当前项目上下文：
- 当前项目 ID
- 当前页面类型（世界观/角色/大纲/章节）
- 当前编辑的内容 ID（如有）

## 项目结构

```
frontend/
├── public/
├── src/
│   ├── api/                    # API 客户端
│   │   ├── client.ts           # Axios 实例配置
│   │   ├── projects.ts         # 项目 API
│   │   ├── world.ts            # 世界观 API
│   │   ├── characters.ts       # 角色 API
│   │   ├── outlines.ts         # 大纲 API
│   │   ├── chapters.ts         # 章节 API
│   │   ├── reviews.ts          # 评审 API
│   │   └── sessions.ts         # 会话 API
│   ├── components/             # 通用组件
│   │   ├── layout/
│   │   │   ├── AppLayout.tsx
│   │   │   ├── IconSidebar.tsx
│   │   │   └── SecondaryNav.tsx
│   │   ├── ai/
│   │   │   ├── AIFab.tsx
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   └── ThinkingBlock.tsx
│   │   ├── common/
│   │   │   ├── MarkdownEditor.tsx
│   │   │   ├── PageHeader.tsx
│   │   │   └── EmptyState.tsx
│   │   └── cards/
│   │       ├── ProjectCard.tsx
│   │       ├── WorldCard.tsx
│   │       └── CharacterCard.tsx
│   ├── pages/                  # 页面组件
│   │   ├── Dashboard.tsx
│   │   ├── world/
│   │   │   ├── WorldList.tsx
│   │   │   └── WorldEdit.tsx
│   │   ├── characters/
│   │   │   ├── CharacterList.tsx
│   │   │   └── CharacterEdit.tsx
│   │   ├── outline/
│   │   │   └── OutlineEditor.tsx
│   │   ├── chapters/
│   │   │   ├── ChapterList.tsx
│   │   │   └── ChapterEdit.tsx
│   │   ├── reviews/
│   │   │   └── ReviewList.tsx
│   │   └── settings/
│   │       └── ProjectSettings.tsx
│   ├── hooks/                  # 自定义 Hooks
│   │   ├── useProject.ts
│   │   ├── useAIChat.ts
│   │   └── useSSE.ts
│   ├── contexts/               # Context
│   │   ├── ProjectContext.tsx
│   │   └── AIContext.tsx
│   ├── types/                  # TypeScript 类型
│   │   └── index.ts
│   ├── utils/                  # 工具函数
│   │   ├── format.ts
│   │   └── constants.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── .env.development
```

## 环境变量

```env
# .env.development
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=AI 小说创作平台
```

## 开发命令

```bash
# 安装依赖
npm install

# 开发服务器
npm run dev

# 构建
npm run build

# 类型检查
npm run type-check

# 代码检查
npm run lint
```

## 实现阶段

### Phase 1: 基础框架
- [ ] 项目初始化（Vite + React + TypeScript）
- [ ] Ant Design 集成
- [ ] 基础布局组件（AppLayout, IconSidebar, SecondaryNav）
- [ ] 路由配置
- [ ] API 客户端封装

### Phase 2: 项目管理
- [ ] 项目仪表盘页面
- [ ] 项目创建/编辑/删除
- [ ] 项目卡片组件

### Phase 3: 内容管理
- [ ] 世界观管理页 + 编辑器
- [ ] 角色管理页 + 编辑器
- [ ] 大纲编辑器（树形结构）
- [ ] 章节管理页 + 编辑器
- [ ] 评审报告页

### Phase 4: AI 对话
- [ ] AI 悬浮球组件
- [ ] 聊天面板
- [ ] SSE 流式对话
- [ ] 会话管理
- [ ] 快捷键支持

### Phase 5: 优化完善
- [ ] 响应式适配
- [ ] 错误处理
- [ ] Loading 状态
- [ ] 自动保存
- [ ] 性能优化

## 设计规范

### Ant Design Token 配置

使用 Ant Design 5 的 Design Token 系统，通过 `ConfigProvider` 全局配置：

```tsx
import { ConfigProvider, theme } from 'antd';

const App = () => (
  <ConfigProvider
    theme={{
      token: {
        // 品牌色
        colorPrimary: '#6366f1',
        colorSuccess: '#10b981',
        colorWarning: '#f59e0b',
        colorError: '#ef4444',
        colorInfo: '#6366f1',

        // 文字
        colorTextBase: '#1a1a2e',

        // 圆角
        borderRadius: 6,
        borderRadiusLG: 12,
        borderRadiusSM: 4,

        // 字体
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
        fontFamilyCode: "'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace",

        // 尺寸
        controlHeight: 36,
        fontSize: 14,

        // 动画
        motion: true,
      },
      components: {
        Layout: {
          siderBg: '#1a1a2e',
          headerBg: '#ffffff',
        },
        Menu: {
          darkItemBg: '#1a1a2e',
          darkItemSelectedBg: '#6366f1',
        },
        Card: {
          paddingLG: 16,
        },
      },
    }}
  >
    <AppRoutes />
  </ConfigProvider>
);
```

### 在组件中使用 Token

```tsx
import { theme } from 'antd';

const MyComponent = () => {
  const { token: {
    colorPrimary,
    colorBgContainer,
    borderRadiusLG,
    colorText,
    colorTextSecondary,
  }} = theme.useToken();

  return (
    <div style={{
      background: colorBgContainer,
      borderRadius: borderRadiusLG,
      color: colorText,
    }}>
      内容
    </div>
  );
};
```

### Token 映射表

| 用途 | Token 名称 | 默认值 |
|------|-----------|--------|
| 主色/品牌色 | `colorPrimary` | `#6366f1` |
| 成功状态 | `colorSuccess` | `#10b981` |
| 警告状态 | `colorWarning` | `#f59e0b` |
| 错误状态 | `colorError` | `#ef4444` |
| 容器背景 | `colorBgContainer` | `#ffffff` |
| 布局背景 | `colorBgLayout` | `#f5f5f5` |
| 主文字色 | `colorText` | `rgba(0,0,0,0.88)` |
| 次文字色 | `colorTextSecondary` | `rgba(0,0,0,0.65)` |
| 弱文字色 | `colorTextQuaternary` | `rgba(0,0,0,0.25)` |
| 边框色 | `colorBorder` | `#d9d9d9` |
| 圆角 | `borderRadius` | `6` |
| 大圆角 | `borderRadiusLG` | `12` |
| 小圆角 | `borderRadiusSM` | `4` |

## 注意事项

1. **无认证系统** - 后端没有 JWT 认证，前端直接调用 API
2. **Markdown 内容** - 所有内容字段都是 Markdown 格式
3. **SSE 流式** - AI 对话使用 SSE，需要正确处理 EventSource 或 fetch + ReadableStream
4. **大纲树结构** - 大纲是嵌套树结构，需要递归渲染
5. **文件存储** - 内容存储为 Markdown 文件，前端只处理 API 调用

## 参考资源

- 后端 API 文档：`docs/API.md`
- Agent Tester 参考：`agent-tester/index.html`（SSE 对话实现）
- Ant Design 文档：https://ant.design/
