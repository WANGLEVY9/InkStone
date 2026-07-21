# Ant Design X AI Copilot Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the custom AI chat implementation (MessageBubble, ChatPanel, useSSE) with Ant Design X components (Bubble, Sender, ThoughtChain, Conversations, Welcome), adding both drawer and full-page chat modes.

**Architecture:** Shared `ChatCore` component renders the chat UI using Ant Design X components. A custom `useProjectChat` hook manages sessions, messages, and SSE streaming (migrated from `useSSE.ts`). `ChatContext` shares state between drawer and page modes. The backend SSE protocol is non-standard and uses dynamic URLs (`sessionId` in path), so we use a custom hook instead of `AbstractChatProvider`/`useXChat`.

**Tech Stack:** React 18, TypeScript, `@ant-design/x` (Bubble, Sender, ThoughtChain, Conversations, Welcome, Prompts, XProvider), `@ant-design/x-markdown` (XMarkdown), antd 6

---

## File Structure

### New Files
| File | Responsibility |
|------|---------------|
| `frontend/src/contexts/ChatContext.tsx` | Shared chat state between drawer/page; provides `useProjectChat` data |
| `frontend/src/hooks/useProjectChat.ts` | Session CRUD, message state, SSE streaming (replaces useSSE.ts + ChatPanel logic) |
| `frontend/src/components/ai/ChatCore.tsx` | Core chat UI: Conversations sidebar + Bubble.List + Sender + Welcome |
| `frontend/src/components/ai/DrawerChat.tsx` | FloatButton + Drawer shell (replaces AIFab.tsx) |
| `frontend/src/components/ai/WelcomeScreen.tsx` | Welcome + Prompts for empty state |
| `frontend/src/pages/chat/ChatPage.tsx` | Full-page chat route component |

### Modified Files
| File | Changes |
|------|---------|
| `frontend/package.json` | Add `@ant-design/x`, `@ant-design/x-markdown` |
| `frontend/src/App.tsx` | Add `/projects/:id/chat` routes |
| `frontend/src/components/layout/AppLayout.tsx` | Replace AIFab with DrawerChat, wrap with ChatContext |
| `frontend/src/components/layout/IconSidebar.tsx` | Add Chat navigation item |
| `frontend/src/types/index.ts` | Add `ChatBubbleMessage`, `ThoughtChainItemData` types |

### Removed Files
| File | Reason |
|------|--------|
| `frontend/src/components/ai/AIFab.tsx` | Replaced by DrawerChat.tsx |
| `frontend/src/components/ai/ChatPanel.tsx` | Replaced by ChatCore.tsx |
| `frontend/src/components/ai/MessageBubble.tsx` | Replaced by Bubble.List |
| `frontend/src/components/ai/ThinkingBlock.tsx` | Orphaned file, replaced by ThoughtChain |
| `frontend/src/hooks/useSSE.ts` | SSE logic moved to useProjectChat.ts |
| `frontend/src/api/sessions.ts` → `stream()` method | Dead code, never called |

---

## Task 1: Install Dependencies

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: Install @ant-design/x and @ant-design/x-markdown**

```bash
cd frontend && npm install @ant-design/x @ant-design/x-markdown
```

- [ ] **Step 2: Verify installation**

```bash
cd frontend && npm ls @ant-design/x @ant-design/x-markdown
```

Expected: Both packages listed without errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "deps: add @ant-design/x and @ant-design/x-markdown"
```

---

## Task 2: Add Types

**Files:**
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: Add ChatBubbleMessage and ThoughtChainItemData types**

Append to `frontend/src/types/index.ts`:

```typescript
// ── Ant Design X Chat Types ──

export interface ThoughtChainItemData {
  key: string;
  title: string;
  description?: string;
  status: 'loading' | 'success' | 'error' | 'abort';
  icon?: React.ReactNode;
  content?: React.ReactNode;
  collapsible?: boolean;
  blink?: boolean;
}

export interface ChatBubbleMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  agent?: string;
  streaming?: boolean;
  thinking?: string;
  thoughtChainItems?: ThoughtChainItemData[];
  status: 'local' | 'loading' | 'updating' | 'success' | 'error';
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/index.ts
git commit -m "feat(types): add ChatBubbleMessage and ThoughtChainItemData types"
```

---

## Task 3: Create useProjectChat Hook

**Files:**
- Create: `frontend/src/hooks/useProjectChat.ts`

This hook replaces `useSSE.ts` + session management from `ChatPanel.tsx`. It manages sessions, messages, and SSE streaming, outputting data in a format compatible with `Bubble.List`.

- [ ] **Step 1: Create useProjectChat.ts with session management**

```typescript
import { useState, useCallback, useRef, useEffect } from 'react';
import { sessionsApi } from '@/api/sessions';
import { useAppMessage } from '@/hooks/useAppMessage';
import type { Session, ChatMessage, ChatBubbleMessage, ThoughtChainItemData } from '@/types';

const DELEGATE_TOOLS = new Set([
  'delegate_to_world_builder',
  'delegate_to_character',
  'delegate_to_plot',
  'delegate_to_chapter',
  'delegate_to_review',
]);

const READ_ONLY_TOOLS = new Set([
  'list_world_settings',
  'list_characters',
  'get_story_outline',
  'list_chapters',
  'load_skill',
  'query_content',
  'get_content',
  'get_outline_tree',
]);

let messageIdCounter = 0;
const genId = () => `msg-${++messageIdCounter}-${Date.now()}`;

export function useProjectChat(projectId: string) {
  const { message: messageApi } = useAppMessage();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatBubbleMessage[]>([]);
  const [isRequesting, setIsRequesting] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const messagesRef = useRef<ChatBubbleMessage[]>([]);

  messagesRef.current = messages;

  // Load sessions on mount
  useEffect(() => {
    if (!projectId) return;
    sessionsApi.list(projectId).then(res => {
      setSessions(res.data);
      if (res.data.length > 0 && !activeKey) {
        setActiveKey(res.data[0].id);
      }
    }).catch(() => {
      messageApi.error('加载会话列表失败');
    });
  }, [projectId]);

  // Load history when activeKey changes
  useEffect(() => {
    if (!activeKey || !projectId) return;
    setLoadingHistory(true);
    sessionsApi.getHistory(projectId, activeKey).then(res => {
      const history: ChatMessage[] = res.data;
      const converted: ChatBubbleMessage[] = history.map(msg => ({
        id: genId(),
        role: msg.role === 'assistant' ? 'assistant' : msg.role as 'user' | 'system',
        content: msg.content,
        status: 'success' as const,
      }));
      setMessages(converted);
      messagesRef.current = converted;
    }).catch(() => {
      messageApi.error('加载会话历史失败');
    }).finally(() => {
      setLoadingHistory(false);
    });
  }, [activeKey, projectId]);

  const createSession = useCallback(async () => {
    try {
      const res = await sessionsApi.create(projectId);
      setSessions(prev => [res.data, ...prev]);
      setActiveKey(res.data.id);
      setMessages([]);
      messagesRef.current = [];
      return res.data;
    } catch {
      messageApi.error('创建会话失败');
      return null;
    }
  }, [projectId]);

  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      await sessionsApi.delete(projectId, sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (activeKey === sessionId) {
        const remaining = sessions.filter(s => s.id !== sessionId);
        setActiveKey(remaining.length > 0 ? remaining[0].id : null);
        setMessages([]);
        messagesRef.current = [];
      }
    } catch {
      messageApi.error('删除会话失败');
    }
  }, [projectId, activeKey, sessions]);

  const renameSession = useCallback(async (sessionId: string, newTitle: string) => {
    // Optimistic update
    setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, title: newTitle } : s));
    // Note: Backend may not have a rename endpoint yet. If it fails, the optimistic update stays.
    // This is acceptable since the title is just metadata.
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (!activeKey || !content.trim() || isRequesting) return;

    setIsRequesting(true);
    const controller = new AbortController();
    abortRef.current = controller;

    const userMsg: ChatBubbleMessage = {
      id: genId(),
      role: 'user',
      content: content.trim(),
      status: 'success',
    };
    const agentMsg: ChatBubbleMessage = {
      id: genId(),
      role: 'assistant',
      content: '',
      agent: '',
      streaming: true,
      thinking: '',
      thoughtChainItems: [],
      status: 'loading',
    };

    const newMessages = [...messagesRef.current, userMsg, agentMsg];
    messagesRef.current = newMessages;
    setMessages(newMessages);

    try {
      const response = await fetch(
        `/api/v1/projects/${projectId}/sessions/${activeKey}/chat/stream`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: content.trim() }),
          signal: controller.signal,
        },
      );

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      if (!response.body) throw new Error('Streaming not supported');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let currentEventType = '';

      const getCurrentAgentMsg = (): ChatBubbleMessage => {
        const msgs = messagesRef.current;
        const last = msgs[msgs.length - 1];
        if (last && last.role === 'assistant' && last.streaming) return last;
        const newMsg: ChatBubbleMessage = {
          id: genId(),
          role: 'assistant',
          content: '',
          agent: '',
          streaming: true,
          thinking: '',
          thoughtChainItems: [],
          status: 'updating',
        };
        msgs.push(newMsg);
        return newMsg;
      };

      const processEvent = (eventType: string, data: Record<string, unknown>) => {
        const agentMsg = getCurrentAgentMsg();
        if (!agentMsg.thoughtChainItems) agentMsg.thoughtChainItems = [];
        const tcItems = agentMsg.thoughtChainItems;

        switch (eventType) {
          case 'messages': {
            const source = data.source as string | undefined;
            const isSubAgent = source && source !== 'orchestrator';

            // Route sub-agent tokens to delegate's ThoughtChain content
            if (isSubAgent) {
              const delegateToolName = 'delegate_to_' + source;
              for (let i = tcItems.length - 1; i >= 0; i--) {
                const item = tcItems[i];
                if (item.key.startsWith(delegateToolName) && item.status === 'loading') {
                  // Append to delegate's content
                  const existing = (item.content as string) || '';
                  if (data.token) {
                    item.content = existing + (data.token as string);
                  }
                  if (data.thinking) {
                    // Store thinking in description
                    item.description = ((item.description as string) || '') + (data.thinking as string);
                  }
                  break;
                }
              }
            } else {
              // Orchestrator message
              if (source === 'orchestrator') {
                agentMsg.agent = 'Orchestrator';
              }
              if (data.thinking) {
                agentMsg.thinking = (agentMsg.thinking || '') + (data.thinking as string);
              }
              if (data.token) {
                agentMsg.content = (agentMsg.content || '') + (data.token as string);
                agentMsg.status = 'updating';
              }
            }
            break;
          }

          case 'updates': {
            if (data.type === 'tool_start') {
              const toolName = data.tool as string;
              if (!toolName) break;
              const isDelegate = DELEGATE_TOOLS.has(toolName);
              const isReadOnly = READ_ONLY_TOOLS.has(toolName);
              const toolId = (data.tool_call_id as string) || `tool-${Date.now()}`;

              const tcItem: ThoughtChainItemData = {
                key: toolId,
                title: toolName,
                description: isDelegate ? '' : (isReadOnly ? '只读' : '写入'),
                status: 'loading',
                blink: true,
                content: isDelegate ? '' : undefined,
                collapsible: true,
              };

              // Check if we're inside a delegate's sub-chain
              let lastDelegate: ThoughtChainItemData | null = null;
              for (let i = tcItems.length - 1; i >= 0; i--) {
                if (tcItems[i].status === 'loading' && DELEGATE_TOOLS.has(tcItems[i].title)) {
                  lastDelegate = tcItems[i];
                  break;
                }
              }

              if (lastDelegate) {
                // Append to delegate's content as nested ThoughtChain reference
                // For simplicity, add to top-level but mark as sub-item
                tcItems.push(tcItem);
              } else {
                tcItems.push(tcItem);
              }
            } else if (data.type === 'tool_end') {
              const toolName = data.tool as string;
              if (!toolName) break;
              // Find the last running tool with this name
              for (let i = tcItems.length - 1; i >= 0; i--) {
                if (tcItems[i].title === toolName && tcItems[i].status === 'loading') {
                  tcItems[i].status = 'success';
                  tcItems[i].blink = false;
                  if (data.result != null) {
                    const resultStr = typeof data.result === 'string'
                      ? data.result
                      : JSON.stringify(data.result, null, 2);
                    tcItems[i].content = resultStr;
                  }
                  break;
                }
              }
            }
            break;
          }

          case 'error': {
            const errorItem: ThoughtChainItemData = {
              key: `error-${Date.now()}`,
              title: 'Error',
              description: data.message as string,
              status: 'error',
            };
            tcItems.push(errorItem);
            break;
          }
        }

        agentMsg.status = 'updating';
        setMessages([...messagesRef.current]);
      };

      // Read SSE stream
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEventType = line.slice(7).trim();
          }
          if (line.startsWith('data: ')) {
            const raw = line.slice(6).trim();
            if (!raw) continue;
            try {
              const data = JSON.parse(raw);
              processEvent(currentEventType, data);
            } catch { /* ignore malformed JSON */ }
          }
        }
      }

      // Finalize
      const last = messagesRef.current[messagesRef.current.length - 1];
      if (last?.role === 'assistant') {
        last.streaming = false;
        last.status = 'success';
        setMessages([...messagesRef.current]);
      }
    } catch (e) {
      if ((e as Error).name === 'AbortError') {
        const last = messagesRef.current[messagesRef.current.length - 1];
        if (last?.role === 'assistant') {
          last.streaming = false;
          last.status = 'success';
          setMessages([...messagesRef.current]);
        }
      } else {
        const errorMsg: ChatBubbleMessage = {
          id: genId(),
          role: 'system',
          content: `Error: ${(e as Error).message}`,
          status: 'error',
        };
        messagesRef.current.push(errorMsg);
        setMessages([...messagesRef.current]);
      }
    }

    abortRef.current = null;
    setIsRequesting(false);
  }, [activeKey, projectId, isRequesting]);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const clearMessages = useCallback(() => {
    messagesRef.current = [];
    setMessages([]);
  }, []);

  return {
    sessions,
    activeKey,
    setActiveKey,
    messages,
    isRequesting,
    loadingHistory,
    sendMessage,
    cancel,
    clearMessages,
    createSession,
    deleteSession,
    renameSession,
  };
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit --pretty 2>&1 | head -30
```

Expected: No errors from `useProjectChat.ts`. Other files may have errors (expected at this stage).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useProjectChat.ts
git commit -m "feat(hooks): add useProjectChat hook with SSE streaming and session management"
```

---

## Task 4: Create ChatContext

**Files:**
- Create: `frontend/src/contexts/ChatContext.tsx`

- [ ] **Step 1: Create ChatContext.tsx**

```typescript
import { createContext, useContext, type ReactNode } from 'react';
import { useProjectChat } from '@/hooks/useProjectChat';
import { useProjectContext } from '@/contexts/ProjectContext';

type ChatState = ReturnType<typeof useProjectChat>;

const ChatContext = createContext<ChatState | null>(null);

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const { currentProject } = useProjectContext();
  const chatState = useProjectChat(currentProject?.id || '');

  // Only provide state when project is loaded
  if (!currentProject) {
    return <>{children}</>;
  }

  return (
    <ChatContext.Provider value={chatState}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChatContext = (): ChatState | null => {
  return useContext(ChatContext);
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/contexts/ChatContext.tsx
git commit -m "feat(context): add ChatContext for shared chat state between drawer and page"
```

---

## Task 5: Create WelcomeScreen Component

**Files:**
- Create: `frontend/src/components/ai/WelcomeScreen.tsx`

- [ ] **Step 1: Create WelcomeScreen.tsx**

```tsx
import { Welcome, Prompts } from '@ant-design/x';
import {
  RobotOutlined,
  GlobalOutlined,
  UserOutlined,
  BranchesOutlined,
  EditOutlined,
} from '@ant-design/icons';

interface WelcomeScreenProps {
  onSend: (message: string) => void;
}

const PROMPT_ITEMS = [
  { key: 'world', icon: <GlobalOutlined style={{ color: '#10b981' }} />, label: '帮我构建世界观', description: '创建地理、文化、历史等世界设定' },
  { key: 'character', icon: <UserOutlined style={{ color: '#f43f5e' }} />, label: '设计一个新角色', description: '创建角色档案、性格、关系' },
  { key: 'plot', icon: <BranchesOutlined style={{ color: '#f59e0b' }} />, label: '规划故事大纲', description: '设计章节结构和情节走向' },
  { key: 'chapter', icon: <EditOutlined style={{ color: '#8b5cf6' }} />, label: '撰写一个章节', description: '基于大纲生成小说正文' },
];

const WelcomeScreen = ({ onSend }: WelcomeScreenProps) => {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flex: 1, padding: 24 }}>
      <Welcome
        icon={<RobotOutlined style={{ fontSize: 48, color: '#6366f1' }} />}
        title="AI 写作助手"
        description="我可以帮你构建世界观、设计角色、规划大纲、撰写章节"
        variant="filled"
        extra={
          <Prompts
            items={PROMPT_ITEMS}
            wrap
            onItemClick={({ data }) => onSend(data.label as string)}
          />
        }
      />
    </div>
  );
};

export default WelcomeScreen;
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ai/WelcomeScreen.tsx
git commit -m "feat(ai): add WelcomeScreen component with Welcome and Prompts"
```

---

## Task 6: Create ChatCore Component

**Files:**
- Create: `frontend/src/components/ai/ChatCore.tsx`

This is the core chat UI component. It uses Bubble.List, Sender, ThoughtChain, Conversations, and WelcomeScreen.

- [ ] **Step 1: Create ChatCore.tsx**

```tsx
import { useState, useMemo } from 'react';
import { Bubble, Sender, Conversations, ThoughtChain, Actions, XProvider } from '@ant-design/x';
import { XMarkdown } from '@ant-design/x-markdown';
import {
  RobotOutlined,
  UserOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  MessageOutlined,
  RedoOutlined,
} from '@ant-design/icons';
import { Typography, Collapse, Alert, message, theme } from 'antd';
import { useChatContext } from '@/contexts/ChatContext';
import WelcomeScreen from './WelcomeScreen';
import type { ChatBubbleMessage } from '@/types';

interface ChatCoreProps {
  mode: 'drawer' | 'page';
}

const ChatCore = ({ mode }: ChatCoreProps) => {
  const chat = useChatContext();
  const { token } = theme.useToken();
  const [sidebarOpen, setSidebarOpen] = useState(mode === 'page');

  if (!chat) return null;

  const {
    sessions, activeKey, setActiveKey, messages, isRequesting, loadingHistory,
    sendMessage, cancel, createSession, deleteSession, renameSession,
  } = chat;

  // Convert sessions to Conversations items
  const conversationItems = useMemo(() =>
    sessions.map(s => ({
      key: s.id,
      label: s.title || `会话 ${s.id.substring(0, 8)}...`,
      icon: <MessageOutlined />,
    })),
    [sessions],
  );

  // Conversations menu config
  const conversationMenu = (conversation: { key: string }) => ({
    items: [
      { key: 'rename', label: '重命名', icon: <EditOutlined /> },
      { key: 'delete', label: '删除', icon: <DeleteOutlined />, danger: true },
    ],
    onClick: ({ key }: { key: string }) => {
      if (key === 'delete') {
        deleteSession(conversation.key);
      } else if (key === 'rename') {
        const newTitle = prompt('请输入新名称:');
        if (newTitle?.trim()) {
          renameSession(conversation.key, newTitle.trim());
        }
      }
    },
  });

  // Role config for Bubble.List
  const roleConfig = useMemo(() => ({
    user: {
      placement: 'end' as const,
      avatar: <UserOutlined />,
      variant: 'filled' as const,
    },
    assistant: {
      placement: 'start' as const,
      avatar: <RobotOutlined />,
      variant: mode === 'drawer' ? 'borderless' as const : 'filled' as const,
      contentRender: (content: string) => {
        if (!content) return null;
        return <XMarkdown>{content}</XMarkdown>;
      },
    },
    system: {
      placement: 'center' as const,
      variant: 'borderless' as const,
    },
  }), [mode]);

  // Helper: build action items for assistant messages
  const makeActionItems = (msg: ChatBubbleMessage) => [
    {
      key: 'copy',
      actionRender: () => <Actions.Copy text={msg.content} onSuccess={() => message.success('已复制')} />,
    },
    {
      key: 'feedback',
      actionRender: () => <Actions.Feedback />,
    },
    {
      key: 'retry',
      icon: <RedoOutlined />,
      label: '重新生成',
      onItemClick: () => sendMessage(msg.content),
    },
  ];

  // Convert messages to Bubble.List items
  const bubbleItems = useMemo(() =>
    messages.map((msg: ChatBubbleMessage) => {
      const base = {
        key: msg.id,
        role: msg.role,
        content: msg.content,
        loading: msg.status === 'loading' && !msg.content,
        streaming: msg.streaming,
      };

      // Assistant messages: combine ThoughtChain + thinking + actions in footer
      if (msg.role === 'assistant') {
        const hasThoughtChain = msg.thoughtChainItems && msg.thoughtChainItems.length > 0;
        const hasThinking = !!msg.thinking;
        const isComplete = msg.status === 'success' && !msg.streaming;

        const footerContent = (
          <>
            {hasThoughtChain && (
              <ThoughtChain
                items={msg.thoughtChainItems!}
                line="dashed"
              />
            )}
            {hasThinking && (
              <Collapse
                size="small"
                items={[{
                  key: 'thinking',
                  label: <span style={{ color: '#8b5cf6', fontSize: 12 }}>Thinking</span>,
                  children: (
                    <Typography>
                      <pre style={{
                        margin: 0,
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                        fontSize: 12,
                        color: '#666',
                        maxHeight: 200,
                        overflow: 'auto',
                      }}>
                        {msg.thinking}
                      </pre>
                    </Typography>
                  ),
                }]}
                style={{ background: '#faf5ff', borderColor: '#e9d5ff', marginBottom: 8 }}
              />
            )}
            {isComplete && msg.content && (
              <Actions items={makeActionItems(msg)} variant="borderless" fadeIn />
            )}
          </>
        );

        return {
          ...base,
          footer: (hasThoughtChain || hasThinking || isComplete) ? footerContent : undefined,
        };
      }

      // System messages rendered as alerts
      if (msg.role === 'system') {
        return {
          ...base,
          content: <Alert message={msg.content} type="warning" showIcon banner />,
        };
      }

      return base;
    }),
    [messages, sendMessage],
  );

  const showWelcome = messages.length === 0 && !loadingHistory;

  const sidebarContent = (
    <div style={{
      width: mode === 'page' ? 250 : 280,
      borderRight: `1px solid ${token.colorBorderSecondary}`,
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      background: token.colorBgContainer,
    }}>
      <Conversations
        items={conversationItems}
        activeKey={activeKey || undefined}
        onActiveChange={(key) => {
          setActiveKey(key);
        }}
        menu={conversationMenu}
        creation={{
          icon: <PlusOutlined />,
          label: '新建会话',
          onClick: () => createSession(),
        }}
        style={{ flex: 1, overflow: 'auto' }}
      />
    </div>
  );

  return (
    <XProvider>
      <div style={{
        display: 'flex',
        height: '100%',
        overflow: 'hidden',
        background: token.colorBgContainer,
      }}>
        {/* Sidebar - always visible in page mode, overlay in drawer mode */}
        {mode === 'page' && sidebarContent}

        {/* Drawer mode: sidebar toggle */}
        {mode === 'drawer' && sidebarOpen && (
          <div style={{
            position: 'absolute',
            left: 0,
            top: 0,
            bottom: 0,
            zIndex: 10,
            boxShadow: '2px 0 8px rgba(0,0,0,0.1)',
          }}>
            {sidebarContent}
          </div>
        )}

        {/* Main chat area */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Header with session toggle for drawer mode */}
          {mode === 'drawer' && (
            <div style={{
              padding: '8px 12px',
              borderBottom: `1px solid ${token.colorBorderSecondary}`,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}>
              <a
                onClick={() => setSidebarOpen(!sidebarOpen)}
                style={{ fontSize: 12, color: token.colorPrimary, cursor: 'pointer' }}
              >
                {sidebarOpen ? '隐藏会话列表' : '显示会话列表'}
              </a>
            </div>
          )}

          {/* Messages area */}
          <div style={{ flex: 1, overflow: 'auto', padding: mode === 'drawer' ? 12 : 24 }}>
            {loadingHistory ? (
              <div style={{ textAlign: 'center', padding: 40, color: token.colorTextSecondary }}>
                加载中...
              </div>
            ) : showWelcome ? (
              <WelcomeScreen onSend={sendMessage} />
            ) : (
              <Bubble.List
                items={bubbleItems}
                role={roleConfig}
                autoScroll
                style={{ height: '100%' }}
              />
            )}
          </div>

          {/* Sender */}
          <div style={{ padding: mode === 'drawer' ? '8px 12px' : '12px 24px', borderTop: `1px solid ${token.colorBorderSecondary}` }}>
            <Sender
              loading={isRequesting}
              onCancel={cancel}
              onSubmit={(msg) => sendMessage(msg)}
              placeholder={activeKey ? '输入消息... (Enter 发送)' : '请先创建或选择会话'}
              disabled={!activeKey}
              autoSize={mode === 'drawer' ? { maxRows: 4 } : { maxRows: 8 }}
            />
          </div>
        </div>
      </div>
    </XProvider>
  );
};

export default ChatCore;
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit --pretty 2>&1 | head -30
```

Expected: No errors from ChatCore.tsx.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ai/ChatCore.tsx
git commit -m "feat(ai): add ChatCore component with Bubble, Sender, ThoughtChain, Conversations"
```

---

## Task 7: Create DrawerChat Component

**Files:**
- Create: `frontend/src/components/ai/DrawerChat.tsx`
- Delete: `frontend/src/components/ai/AIFab.tsx` (in a later cleanup task)

- [ ] **Step 1: Create DrawerChat.tsx**

```tsx
import { useState, useEffect } from 'react';
import { FloatButton, Badge, Drawer } from 'antd';
import { MessageOutlined } from '@ant-design/icons';
import { useLocation } from 'react-router-dom';
import { useProjectContext } from '@/contexts/ProjectContext';
import ChatCore from './ChatCore';

const DrawerChat = () => {
  const [open, setOpen] = useState(false);
  const { currentProject } = useProjectContext();
  const location = useLocation();

  // Auto-close drawer when chat page is active
  const isChatPage = location.pathname.includes('/chat');
  useEffect(() => {
    if (isChatPage && open) {
      setOpen(false);
    }
  }, [isChatPage]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'j') {
        e.preventDefault();
        setOpen(prev => !prev);
      }
      if (e.key === 'Escape' && open) {
        setOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open]);

  if (!currentProject) return null;

  return (
    <>
      <FloatButton.Group shape="circle" style={{ insetInlineEnd: 24, bottom: 24 }}>
        <Badge size="small">
          <FloatButton
            icon={<MessageOutlined />}
            type="primary"
            onClick={() => setOpen(true)}
            tooltip="AI 助手 (Ctrl+J)"
          />
        </Badge>
      </FloatButton.Group>

      <Drawer
        title="AI 助手"
        placement="right"
        size={480}
        resizable
        maxSize={800}
        open={open}
        onClose={() => setOpen(false)}
        destroyOnClose={false}
        styles={{ body: { padding: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden' } }}
      >
        <ChatCore mode="drawer" />
      </Drawer>
    </>
  );
};

export default DrawerChat;
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ai/DrawerChat.tsx
git commit -m "feat(ai): add DrawerChat component with persistent state (destroyOnClose=false)"
```

---

## Task 8: Create ChatPage

**Files:**
- Create: `frontend/src/pages/chat/ChatPage.tsx`

- [ ] **Step 1: Create ChatPage.tsx**

```tsx
import ChatCore from '@/components/ai/ChatCore';

const ChatPage = () => {
  return <ChatCore mode="page" />;
};

export default ChatPage;
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/chat/ChatPage.tsx
git commit -m "feat(pages): add ChatPage for full-page chat route"
```

---

## Task 9: Wire Up Routes, Layout, and Navigation

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/layout/AppLayout.tsx`
- Modify: `frontend/src/components/layout/IconSidebar.tsx`

- [ ] **Step 1: Add chat routes to App.tsx**

Add import and route in `frontend/src/App.tsx`:

```typescript
// Add import after existing page imports
import ChatPage from '@/pages/chat/ChatPage';
```

Add route inside the `<Route element={<AppLayout />}>` block:

```tsx
<Route path="/projects/:id/chat" element={<ChatPage />} />
<Route path="/projects/:id/chat/:sessionId" element={<ChatPage />} />
```

- [ ] **Step 2: Update AppLayout.tsx to use DrawerChat and ChatContext**

Replace the AIFab import and add ChatContext:

```tsx
import { Layout, theme } from 'antd';
import { Outlet } from 'react-router-dom';
import IconSidebar from './IconSidebar';
import SecondaryNav from './SecondaryNav';
import { ProjectLoader } from '@/contexts/ProjectContext';
import { ChatProvider } from '@/contexts/ChatContext';
import DrawerChat from '@/components/ai/DrawerChat';

const { Content } = Layout;

const AppLayout = () => {
  const { token: { colorBgContainer } } = theme.useToken();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <IconSidebar />
      <SecondaryNav />
      <Layout style={{ marginLeft: 264 }}>
        <Content style={{
          padding: 24,
          background: colorBgContainer,
          minHeight: '100vh',
        }}>
          <ProjectLoader>
            <ChatProvider>
              <Outlet />
            </ChatProvider>
          </ProjectLoader>
        </Content>
      </Layout>
      <DrawerChat />
    </Layout>
  );
};

export default AppLayout;
```

- [ ] **Step 3: Add Chat navigation to IconSidebar.tsx**

Add `MessageOutlined` to imports and add the chat menu item:

```tsx
import { HomeOutlined, SettingOutlined, MessageOutlined } from '@ant-design/icons';
```

Add the chat item inside the `if (currentProject)` block:

```typescript
if (currentProject) {
  items.push({
    key: `/projects/${currentProject.id}/chat`,
    icon: <MessageOutlined />,
    label: 'AI',
  });
  items.push({
    key: `/projects/${currentProject.id}/settings`,
    icon: <SettingOutlined />,
    label: '设置',
  });
}
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit --pretty 2>&1 | head -30
```

Expected: No type errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx frontend/src/components/layout/AppLayout.tsx frontend/src/components/layout/IconSidebar.tsx
git commit -m "feat: wire up chat routes, layout, and navigation"
```

---

## Task 10: Clean Up Old Files

**Files:**
- Delete: `frontend/src/components/ai/AIFab.tsx`
- Delete: `frontend/src/components/ai/ChatPanel.tsx`
- Delete: `frontend/src/components/ai/MessageBubble.tsx`
- Delete: `frontend/src/components/ai/ThinkingBlock.tsx`
- Delete: `frontend/src/hooks/useSSE.ts`
- Modify: `frontend/src/api/sessions.ts` (remove dead `stream()` method)

- [ ] **Step 1: Delete old component files**

```bash
rm frontend/src/components/ai/AIFab.tsx
rm frontend/src/components/ai/ChatPanel.tsx
rm frontend/src/components/ai/MessageBubble.tsx
rm frontend/src/components/ai/ThinkingBlock.tsx
rm frontend/src/hooks/useSSE.ts
```

- [ ] **Step 2: Remove dead `stream()` method from sessions.ts**

Edit `frontend/src/api/sessions.ts` and remove the `stream` method (lines that implement the unused SSE client):

Remove this block from the `sessionsApi` object:
```typescript
stream: async (projectId: string, sessionId: string, message: string, onEvent: (event: string, data: Record<string, unknown>) => void) => {
  // ... entire method body
},
```

- [ ] **Step 3: Verify no remaining imports of deleted files**

```bash
cd frontend && grep -r "AIFab\|ChatPanel\|MessageBubble\|ThinkingBlock\|useSSE" src/ --include="*.ts" --include="*.tsx"
```

Expected: No matches (all references should be gone).

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit --pretty 2>&1 | head -30
```

Expected: No type errors.

- [ ] **Step 5: Verify lint passes**

```bash
cd frontend && npm run lint
```

Expected: No errors.

- [ ] **Step 6: Commit**

```bash
git add -A frontend/src/
git commit -m "refactor: remove old AI chat files (AIFab, ChatPanel, MessageBubble, ThinkingBlock, useSSE)"
```

---

## Task 11: Final Verification

- [ ] **Step 1: Run type-check**

```bash
cd frontend && npm run type-check
```

Expected: Pass with no errors.

- [ ] **Step 2: Run lint**

```bash
cd frontend && npm run lint
```

Expected: Pass with no errors.

- [ ] **Step 3: Run build**

```bash
cd frontend && npm run build
```

Expected: Build succeeds.

- [ ] **Step 4: Verify dev server starts**

```bash
cd frontend && npm run dev &
sleep 5
curl -s http://localhost:5173/ | head -20
```

Expected: HTML response with the app.

- [ ] **Step 5: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "fix: address type-check and lint issues from chat refactor"
```
