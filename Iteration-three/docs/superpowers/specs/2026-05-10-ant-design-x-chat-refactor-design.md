# Ant Design X AI Copilot 重构设计

## 概述

使用 Ant Design X (`@ant-design/x`) 库重构前端 AI Copilot 聊天功能。将现有的自定义组件（MessageBubble、ChatPanel、useSSE）替换为 Ant Design X 的专业 AI 聊天组件（Bubble、Sender、ThoughtChain、Conversations、Welcome），同时新增全页面聊天入口。

## 动机

当前 AI Copilot 实现存在以下痛点：

- **自定义 SSE 解析**：手动解析 ReadableStream，in-place mutation 模式，违反 React 不可变性
- **重复代码**：`sessionsApi.stream()` 和 `useSSE.ts` 各自实现了完整的 SSE 解析器
- **无流式动画**：文本块到达后直接合并，无逐字/逐词显示效果
- **抽屉关闭丢失状态**：ChatPanel 在 Drawer 关闭时卸载，消息全部丢失
- **会话管理简陋**：只有 Select 下拉框，无搜索、删除、重命名
- **内联样式**：所有组件使用 inline style，难以维护和覆盖
- **TimelineView 复杂**：递归嵌套的自定义渲染逻辑，难以扩展

## 设计决策

### 1. 两种入口模式

| 模式 | 入口 | 用途 |
|------|------|------|
| 抽屉模式 (drawer) | FloatButton → 右侧 Drawer | 快速交互，不离开当前页面 |
| 全页面模式 (page) | 路由 `/projects/:id/chat` | 深度对话，完整功能 |

两种模式共享 `ChatCore` 核心组件，通过 `mode` prop 控制布局差异。

### 2. 自定义 ChatProvider

后端 SSE 格式为自定义协议（`messages`/`updates`/`error` 事件），非 OpenAI 兼容格式。编写自定义 `SSEChatProvider` 实现 `AbstractChatProvider` 接口，桥接后端 SSE 和 `useXChat`。

### 3. ThoughtChain 用于工具链展示

ThoughtChain 仅用于展示 tool 调用链（delegate_to_* 作为可展开节点），text/thinking 内容继续用 Bubble + XMarkdown 渲染。职责清晰：Bubble 负责内容，ThoughtChain 负责过程可视化。

### 4. Conversations 统一会话管理

两种模式都使用 Ant Design X 的 `Conversations` 组件管理会话。抽屉模式下侧边栏默认折叠（点击展开覆盖式），全页面模式下常驻显示。

## 架构

### 组件结构

```
frontend/src/
├── components/
│   └── ai/
│       ├── ChatCore.tsx          # 核心聊天 UI
│       ├── ChatCore.css.ts       # 样式（token-based）
│       ├── DrawerChat.tsx        # 抽屉壳（改造自 AIFab）
│       ├── MessageContent.tsx    # 消息内容渲染
│       └── WelcomeScreen.tsx     # 空状态欢迎页
├── hooks/
│   └── useProjectChat.ts        # 核心 hook
├── providers/
│   └── SSEChatProvider.ts       # 自定义 ChatProvider
├── pages/
│   └── chat/
│       └── ChatPage.tsx          # 全页面聊天页
```

### 数据流

```
useProjectChat(projectId)
├── sessions / activeKey          ← 会话状态
├── messages / parsedMessages     ← useXChat 管理
├── isRequesting / abort          ← 流式请求状态
├── onRequest / onReload          ← 操作方法
└── createSession / deleteSession / renameSession  ← 会话 CRUD

SSEChatProvider
├── implements AbstractChatProvider
├── sendMessage() → fetch SSE → 解析事件 → 回调
└── messages → content, updates → ThoughtChain items, error → Alert
```

### 路由

| 路径 | 组件 | 说明 |
|------|------|------|
| `/projects/:id/chat` | ChatPage | 全页面聊天 |
| `/projects/:id/chat/:sessionId` | ChatPage | 定位到特定 session |

路由挂在项目下，复用 AppLayout，通过 ProjectContext 获取 currentProject。

## 组件设计

### ChatCore

核心聊天组件，通过 `mode` prop 适配两种布局。

```typescript
interface ChatCoreProps {
  mode: 'drawer' | 'page';
  projectId: string;
}
```

布局：
- **左侧**：Conversations 侧边栏（会话列表 + 新建按钮）
- **右侧上方**：无消息时显示 WelcomeScreen，有消息时显示 Bubble.List
- **右侧下方**：Sender 输入区

mode='drawer' 适配：
- Conversations 侧边栏默认折叠，点击展开（覆盖式）
- Bubble variant='borderless'，更紧凑
- Sender autoSize.maxRows=4

mode='page' 适配：
- Conversations 侧边栏常驻（250px）
- Bubble variant='filled'
- Sender autoSize.maxRows=8

### SSEChatProvider

实现 AbstractChatProvider 接口：

```typescript
class SSEChatProvider implements AbstractChatProvider {
  constructor(projectId: string, sessionId: string | null) {}

  async sendMessage(params: {
    messages: ChatMessage[];
    onUpdate: (message: ChatMessage) => void;
    onSuccess: (message: ChatMessage) => void;
    onError: (error: Error) => void;
    signal: AbortSignal;
  }): Promise<void> {
    // 1. fetch POST /api/v1/projects/{pid}/sessions/{sid}/chat/stream
    // 2. 读取 ReadableStream，解析 SSE 事件
    // 3. messages 事件 → 更新 content/thinking
    // 4. updates 事件 → 构建 ThoughtChain items
    // 5. error 事件 → 错误消息
    // 6. 通过回调通知 useXChat
  }
}
```

消息格式：

```typescript
interface ParsedMessage {
  role: 'user' | 'assistant';
  content: string;
  thinking?: string;
  thoughtChainItems?: ThoughtChainItem[];
  agent?: string;
  streaming?: boolean;
}
```

### useProjectChat

```typescript
function useProjectChat(projectId: string) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeKey, setActiveKey] = useState<string | null>(null);

  const { messages, onRequest, isRequesting, abort, onReload } = useXChat({
    provider: new SSEChatProvider(projectId, activeKey),
    requestPlaceholder: { role: 'assistant', content: '', status: 'loading' },
    requestFallback: (_, { error }) => ({
      role: 'assistant',
      content: error.name === 'AbortError' ? '已取消' : '发送失败，请重试',
    }),
  });

  return {
    sessions, activeKey, setActiveKey,
    messages, onRequest, isRequesting, abort, onReload,
    createSession, deleteSession, renameSession,
  };
}
```

### Bubble 角色配置

```typescript
const roles = {
  user: {
    placement: 'end',
    variant: 'filled',
    avatar: <Avatar icon={<UserOutlined />} />,
  },
  assistant: {
    placement: 'start',
    variant: 'filled',
    avatar: <Avatar icon={<RobotOutlined />} />,
    contentRender: (content) => <XMarkdown>{content}</XMarkdown>,
  },
};
```

ThoughtChain 通过 Bubble 的 footer 渲染：

```typescript
// parser 将 ParsedMessage 转换为 Bubble items
{
  role: message.role,
  content: message.content,
  footer: message.thoughtChainItems?.length
    ? <ThoughtChain items={message.thoughtChainItems} />
    : undefined,
  extra: message.thinking
    ? <Collapse items={[{ key: 'thinking', label: '思考过程', children: message.thinking }]} />
    : undefined,
  streaming: message.streaming,
}
```

### WelcomeScreen

```typescript
<Welcome
  icon={<RobotOutlined />}
  title="AI 写作助手"
  description="我可以帮你构建世界观、设计角色、规划大纲、撰写章节"
  extra={
    <Prompts
      items={[
        { key: 'world', icon: <GlobalOutlined />, label: '帮我构建世界观' },
        { key: 'character', icon: <UserOutlined />, label: '设计一个新角色' },
        { key: 'plot', icon: <BranchesOutlined />, label: '规划故事大纲' },
        { key: 'chapter', icon: <EditOutlined />, label: '撰写一个章节' },
      ]}
      onItemClick={({ data }) => onSend(data.label)}
    />
  }
/>
```

### DrawerChat（改造 AIFab）

- 保持 FloatButton + Drawer 入口
- Drawer `destroyOnClose={false}`，ChatCore 保持挂载
- Drawer 宽度：默认 480px，可拖拽至 800px
- 快捷键：`Ctrl/Cmd+J` 切换，`Escape` 关闭

### ChatPage

```typescript
function ChatPage() {
  const { id } = useParams();
  return <ChatCore mode="page" projectId={id!} />;
}
```

## 错误处理

| 场景 | 处理 |
|------|------|
| SSE 连接断开 | 显示"连接中断"提示 + 重试按钮 |
| 后端 error 事件 | 消息中显示红色 Alert |
| 用户取消 (abort) | 保留已接收内容，标记为已取消 |
| 无 session | 显示"创建新会话"引导 |
| 有 session 无消息 | 显示 WelcomeScreen |
| 加载历史中 | 显示 Skeleton |

## 消息操作

通过 Bubble footer/extra 提供：
- **复制**：Actions.Copy
- **重新生成**：自定义按钮，调用 onReload
- **反馈**：Actions.Feedback（点赞/踩）

## 会话操作

Conversations menu 右键菜单：
- 重命名
- 删除（二次确认）

## 移除的文件

| 文件 | 原因 |
|------|------|
| `components/ai/MessageBubble.tsx` | 被 Bubble.List + MessageContent 替代 |
| `components/ai/ThinkingBlock.tsx` | 孤立文件，功能被 ThoughtChain 替代 |
| `components/ai/ChatPanel.tsx` | 被 ChatCore 替代 |
| `hooks/useSSE.ts` | SSE 逻辑移入 SSEChatProvider |
| `api/sessions.ts` 中的 `stream()` | 死代码，从未被调用 |

## 保留并改造

| 文件 | 改造 |
|------|------|
| `components/ai/AIFab.tsx` | 重命名为 DrawerChat.tsx，内部改用 ChatCore |
| `api/sessions.ts` | 保留 REST API 调用 |
| `types/index.ts` | 新增 ParsedMessage、ThoughtChain 相关类型 |

## 新增依赖

```json
{
  "@ant-design/x": "^1.5.0",
  "@ant-design/x-markdown": "^1.0.0"
}
```

不需要 `@ant-design/x-sdk`（自定义 ChatProvider 替代 OpenAIChatProvider）。

## 抽屉与全页面模式的互斥关系

抽屉和全页面**不会同时处于活跃状态**：

- 用户在任意页面时，可通过 FloatButton 打开抽屉进行快速对话
- 用户导航到 `/projects/:id/chat` 时，抽屉自动关闭（如果打开的话），全页面接管
- 从全页面返回其他页面时，抽屉可以重新打开，共享同一个 useProjectChat 状态

两种模式共享同一个 `useProjectChat` 实例（通过 ChatContext 提供），确保会话和消息状态一致。

## 迁移策略

渐进式迁移，每步可独立验证：

1. 安装依赖，创建 SSEChatProvider 和 useProjectChat
2. 实现 ChatCore + WelcomeScreen
3. 改造 DrawerChat（AIFab），保持抽屉入口不变
4. 新增 ChatPage 全页面路由
5. 添加左侧导航 Chat 入口（IconSidebar）
6. 清理旧代码（MessageBubble、ThinkingBlock、useSSE）

## 验收标准

- [ ] 抽屉模式：FloatButton 打开 Drawer，ChatCore 正常渲染
- [ ] 抽屉模式：关闭 Drawer 后消息不丢失，重新打开恢复状态
- [ ] 全页面模式：`/projects/:id/chat` 正常渲染完整布局
- [ ] 全页面模式：Conversations 侧边栏常驻，会话可切换
- [ ] 消息发送：SSE 流式传输正常，Bubble 显示流式动画
- [ ] ThoughtChain：工具调用链正确渲染，delegate 可展开
- [ ] WelcomeScreen：无消息时显示欢迎页 + 快捷提示
- [ ] 会话管理：新建、重命名、删除会话正常
- [ ] 历史加载：切换 session 自动加载历史
- [ ] 错误处理：SSE 断连、abort、后端错误均有适当 UI 反馈
- [ ] TypeScript：`npm run type-check` 通过
- [ ] ESLint：`npm run lint` 通过
