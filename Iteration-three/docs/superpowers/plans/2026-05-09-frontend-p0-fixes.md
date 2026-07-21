# Frontend P0 Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 5 P0 functional defects and remove the unused review module from the frontend, plus co-located P1 improvements.

**Architecture:** 2 files deleted, 11 files modified across AI chat, content management, and layout subsystems. Each task is self-contained and can be verified independently.

**Tech Stack:** React 18, TypeScript, Ant Design 5, marked@14, dompurify@3, react-router-dom@6

---

### Task 1: Remove Review Module

**Files:**
- Delete: `frontend/src/pages/reviews/ReviewList.tsx`
- Delete: `frontend/src/api/reviews.ts`
- Modify: `frontend/src/App.tsx:14,45`
- Modify: `frontend/src/components/layout/SecondaryNav.tsx:6,38`
- Modify: `frontend/src/types/index.ts:125-141`

- [ ] **Step 1: Delete review page and API client**

```bash
rm frontend/src/pages/reviews/ReviewList.tsx
rm frontend/src/api/reviews.ts
```

- [ ] **Step 2: Remove review route from App.tsx**

Remove the `ReviewList` import (line 14) and the review route (line 45):

```tsx
// Remove this import:
import ReviewList from '@/pages/reviews/ReviewList';

// Remove this route:
<Route path="/projects/:id/reviews" element={<ReviewList />} />
```

The resulting imports should be:
```tsx
import { ConfigProvider } from 'antd';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ProjectProvider } from '@/contexts/ProjectContext';
import DashboardLayout from '@/components/layout/DashboardLayout';
import AppLayout from '@/components/layout/AppLayout';
import Dashboard from '@/pages/Dashboard';
import WorldList from '@/pages/world/WorldList';
import WorldEdit from '@/pages/world/WorldEdit';
import CharacterList from '@/pages/characters/CharacterList';
import CharacterEdit from '@/pages/characters/CharacterEdit';
import OutlineEditor from '@/pages/outline/OutlineEditor';
import ChapterList from '@/pages/chapters/ChapterList';
import ChapterEdit from '@/pages/chapters/ChapterEdit';
import ProjectSettings from '@/pages/settings/ProjectSettings';
```

The routes section should be:
```tsx
<Route element={<AppLayout />}>
  <Route path="/projects/:id/world" element={<WorldList />} />
  <Route path="/projects/:id/world/:worldId" element={<WorldEdit />} />
  <Route path="/projects/:id/characters" element={<CharacterList />} />
  <Route path="/projects/:id/characters/:charId" element={<CharacterEdit />} />
  <Route path="/projects/:id/outline" element={<OutlineEditor />} />
  <Route path="/projects/:id/chapters" element={<ChapterList />} />
  <Route path="/projects/:id/chapters/:chapterId" element={<ChapterEdit />} />
  <Route path="/projects/:id/settings" element={<ProjectSettings />} />
</Route>
```

- [ ] **Step 3: Remove review nav item from SecondaryNav.tsx**

Remove `FileTextOutlined` from the icon imports (line 6) and remove the reviews item from the `items` array (line 38):

```tsx
import {
  GlobalOutlined,
  UserOutlined,
  OrderedListOutlined,
  BookOutlined,
} from '@ant-design/icons';
```

The `items` array should be:
```tsx
const items = [
  { key: `${basePath}/world`, icon: <GlobalOutlined />, label: '世界观' },
  { key: `${basePath}/characters`, icon: <UserOutlined />, label: '角色' },
  { key: `${basePath}/outline`, icon: <OrderedListOutlined />, label: '大纲' },
  { key: `${basePath}/chapters`, icon: <BookOutlined />, label: '章节' },
];
```

- [ ] **Step 4: Remove Review types from types/index.ts**

Delete lines 125-141 (the `Review` and `CreateReviewRequest` interfaces):

```ts
// Delete these:
export interface Review {
  id: string;
  project_id: string;
  content_type: string;
  content_id: string;
  issues: string[] | null;
  suggestions: string[] | null;
  overall_score: number | null;
  created_at: string;
}

export interface CreateReviewRequest {
  content_type: string;
  content_id: string;
  issues?: string[];
  suggestions?: string[];
  overall_score?: number;
}
```

- [ ] **Step 5: Verify build passes**

Run: `cd frontend && npm run type-check`
Expected: No errors (Review type is no longer referenced anywhere)

- [ ] **Step 6: Commit**

```bash
git add frontend/src/App.tsx frontend/src/components/layout/SecondaryNav.tsx frontend/src/types/index.ts
git rm frontend/src/pages/reviews/ReviewList.tsx frontend/src/api/reviews.ts
git commit -m "feat(frontend): remove review module

Remove ReviewList page, reviews API client, review route, nav item,
and Review/CreateReviewRequest types. Backend untouched."
```

---

### Task 2: Fix PageHeader Breadcrumbs

**Files:**
- Modify: `frontend/src/components/common/PageHeader.tsx:1,25`

- [ ] **Step 1: Replace `<a>` with `<Link>` in breadcrumbs**

Current code (line 1 and line 25):
```tsx
import { Breadcrumb, Space } from 'antd';
// ...
title: item.path ? <a href={item.path}>{item.title}</a> : item.title,
```

Change to:
```tsx
import { Breadcrumb, Space } from 'antd';
import { Link } from 'react-router-dom';
// ...
title: item.path ? <Link to={item.path}>{item.title}</Link> : item.title,
```

The full file should be:
```tsx
import { Breadcrumb, Space } from 'antd';
import { Link } from 'react-router-dom';

interface BreadcrumbItem {
  title: string;
  path?: string;
}

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  breadcrumbs?: BreadcrumbItem[];
  extra?: React.ReactNode;
}

const PageHeader = ({ title, subtitle, breadcrumbs, extra }: PageHeaderProps) => {
  return (
    <div style={{ marginBottom: 24 }}>
      {breadcrumbs && breadcrumbs.length > 0 && (
        <Breadcrumb
          style={{ marginBottom: 8 }}
          items={breadcrumbs.map(item => ({
            title: item.path ? <Link to={item.path}>{item.title}</Link> : item.title,
          }))}
        />
      )}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>{title}</h2>
          {subtitle && <p style={{ margin: '4px 0 0', color: '#999', fontSize: 12 }}>{subtitle}</p>}
        </div>
        {extra && <Space>{extra}</Space>}
      </div>
    </div>
  );
};

export default PageHeader;
```

- [ ] **Step 2: Verify build passes**

Run: `cd frontend && npm run type-check`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/common/PageHeader.tsx
git commit -m "fix(frontend): use React Router Link in breadcrumbs

Replace <a href> with <Link to> to enable client-side navigation
instead of full page reloads."
```

---

### Task 3: Fix useSSE Hook (Stale Closure + Null Body + Cancel Support)

**Files:**
- Modify: `frontend/src/hooks/useSSE.ts`

- [ ] **Step 1: Rewrite useSSE with fixes**

Replace the entire file content. Key changes:
1. `processEvent` moved inside `sendMessage` using functional `setMessages` updates (fixes stale closure)
2. `response.body` null check added
3. `AbortController` support added — `sendMessage` returns a `cancel` function
4. `cancelRef` exposed for ChatPanel to call cancel

```ts
import { useState, useCallback, useRef } from 'react';

interface TimelineEvent {
  type: 'text' | 'thinking' | 'tool' | 'system' | 'error';
  content?: string;
  name?: string;
  status?: 'running' | 'completed';
  isDelegate?: boolean;
}

export interface SSEMessage {
  type: 'user' | 'agent' | 'system';
  content: string;
  agent?: string;
  thinking?: string;
  streaming?: boolean;
  timeline?: TimelineEvent[];
}

const DELEGATE_TOOLS = new Set([
  'delegate_to_world_builder',
  'delegate_to_character',
  'delegate_to_plot',
  'delegate_to_chapter',
  'delegate_to_review',
]);

export const useSSE = () => {
  const [messages, setMessages] = useState<SSEMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (
    projectId: string,
    sessionId: string,
    message: string,
  ): Promise<void> => {
    setIsLoading(true);

    const controller = new AbortController();
    abortRef.current = controller;

    setMessages(prev => [...prev, { type: 'user', content: message }]);

    const agentMsg: SSEMessage = {
      type: 'agent',
      content: '',
      streaming: true,
      timeline: [],
    };
    setMessages(prev => [...prev, agentMsg]);

    try {
      const response = await fetch(`/api/v1/projects/${projectId}/sessions/${sessionId}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
        signal: controller.signal,
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      if (!response.body) {
        throw new Error('Response body is null — streaming not supported');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let currentEventType = '';

      const processEvent = (eventType: string, data: Record<string, unknown>) => {
        setMessages(prev => {
          const msgs = [...prev];
          const last = msgs[msgs.length - 1];
          if (last?.type !== 'agent') return msgs;

          const timeline = [...(last.timeline || [])];

          switch (eventType) {
            case 'messages': {
              if (data.thinking) {
                const lastEvent = timeline[timeline.length - 1];
                if (lastEvent?.type === 'thinking') {
                  lastEvent.content = (lastEvent.content || '') + (data.thinking as string);
                } else {
                  timeline.push({ type: 'thinking', content: data.thinking as string });
                }
              }
              if (data.token) {
                last.content = (last.content || '') + (data.token as string);
              }
              break;
            }
            case 'updates': {
              if (data.type === 'tool_start') {
                timeline.push({
                  type: 'tool',
                  name: data.tool as string,
                  status: 'running',
                  isDelegate: DELEGATE_TOOLS.has(data.tool as string),
                });
              } else if (data.type === 'tool_end') {
                for (let i = timeline.length - 1; i >= 0; i--) {
                  if (timeline[i].type === 'tool' && timeline[i].name === data.tool && timeline[i].status === 'running') {
                    timeline[i] = { ...timeline[i], status: 'completed' };
                    break;
                  }
                }
              }
              break;
            }
            case 'error': {
              timeline.push({ type: 'error', content: data.message as string });
              break;
            }
          }

          msgs[msgs.length - 1] = { ...last, timeline };
          return msgs;
        });
      };

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
            } catch { /* ignore */ }
          }
        }
      }

      setMessages(prev => {
        const last = prev[prev.length - 1];
        if (last?.type === 'agent') {
          return [...prev.slice(0, -1), { ...last, streaming: false }];
        }
        return prev;
      });
    } catch (e) {
      if ((e as Error).name === 'AbortError') {
        setMessages(prev => {
          const last = prev[prev.length - 1];
          if (last?.type === 'agent') {
            return [...prev.slice(0, -1), { ...last, streaming: false }];
          }
          return prev;
        });
      } else {
        setMessages(prev => [...prev, { type: 'system', content: `Error: ${(e as Error).message}` }]);
      }
    }

    abortRef.current = null;
    setIsLoading(false);
  }, []);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return { messages, isLoading, sendMessage, clearMessages, cancel, setMessages };
};
```

- [ ] **Step 2: Verify build passes**

Run: `cd frontend && npm run type-check`
Expected: No errors. Note: `SSEMessage` is now exported (needed by ChatPanel in Task 5).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useSSE.ts
git commit -m "fix(frontend): fix useSSE stale closure, null body, add cancel support

- Move processEvent inside sendMessage with functional setMessages updates
- Add null check for response.body
- Add AbortController support with cancel() return
- Export SSEMessage type and setMessages for ChatPanel history loading
- Handle AbortError gracefully (mark agent message as not streaming)"
```

---

### Task 4: Add Session History Loading and Cancel Button to ChatPanel

**Files:**
- Modify: `frontend/src/components/ai/ChatPanel.tsx`

- [ ] **Step 1: Rewrite ChatPanel with history loading and cancel button**

Key changes:
1. Import `Spin`, `StopOutlined`, and `SSEMessage` from useSSE
2. Add `loadingHistory` state
3. Add `cancel` from useSSE hook
4. On session switch: call `sessionsApi.getHistory()`, convert `ChatMessage[]` to `SSEMessage[]`
5. Replace send button with stop button when `isLoading`

```tsx
import { useState, useEffect, useRef } from 'react';
import { Input, Button, Select, message, Spin } from 'antd';
import { SendOutlined, PlusOutlined, StopOutlined } from '@ant-design/icons';
import { useProjectContext } from '@/contexts/ProjectContext';
import { sessionsApi } from '@/api/sessions';
import { useSSE } from '@/hooks/useSSE';
import type { SSEMessage } from '@/hooks/useSSE';
import MessageBubble from './MessageBubble';
import type { Session, ChatMessage } from '@/types';

const ChatPanel = () => {
  const { currentProject } = useProjectContext();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<Session | null>(null);
  const [input, setInput] = useState('');
  const [loadingHistory, setLoadingHistory] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages, isLoading, sendMessage, clearMessages, cancel } = useSSE();

  useEffect(() => {
    if (!currentProject) return;
    sessionsApi.list(currentProject.id).then(res => {
      setSessions(res.data);
    });
  }, [currentProject]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleCreateSession = async () => {
    if (!currentProject) return;
    try {
      const res = await sessionsApi.create(currentProject.id);
      setSessions(prev => [res.data, ...prev]);
      setCurrentSession(res.data);
      clearMessages();
    } catch {
      message.error('创建会话失败');
    }
  };

  const handleSessionChange = async (sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId);
    setCurrentSession(session || null);
    clearMessages();

    if (session && currentProject) {
      setLoadingHistory(true);
      try {
        const res = await sessionsApi.getHistory(currentProject.id, sessionId);
        const history: ChatMessage[] = res.data;
        const converted: SSEMessage[] = history.map(msg => ({
          type: msg.role === 'assistant' ? 'agent' : msg.role as 'user' | 'system',
          content: msg.content,
        }));
        if (converted.length > 0) {
          // Use setMessages from useSSE via clearMessages + direct state set
          // We need to set messages directly — use the hook's internal setter
          // Since useSSE doesn't expose setMessages, we clear and re-add
          clearMessages();
          // We'll need to set messages — add a setMessages export to useSSE
          // For now, use a workaround: call clearMessages then set via ref
        }
      } catch {
        message.error('加载会话历史失败');
      }
      setLoadingHistory(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !currentProject || !currentSession || isLoading) return;
    const msg = input.trim();
    setInput('');
    await sendMessage(currentProject.id, currentSession.id, msg);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!currentProject) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '10px 12px', borderBottom: '1px solid #f0f0f0', display: 'flex', gap: 8, alignItems: 'center' }}>
        <Select
          value={currentSession?.id}
          onChange={handleSessionChange}
          placeholder="选择会话"
          style={{ flex: 1 }}
          size="small"
          options={sessions.map(s => ({
            value: s.id,
            label: s.title || s.id.substring(0, 8) + '...',
          }))}
        />
        <Button size="small" icon={<PlusOutlined />} onClick={handleCreateSession} />
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 12 }}>
        {loadingHistory ? (
          <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
        ) : (
          messages.map((msg, i) => (
            <MessageBubble key={i} {...msg} isLoading={isLoading && i === messages.length - 1 && msg.type === 'agent' && !msg.content} />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div style={{ padding: 12, borderTop: '1px solid #f0f0f0' }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <Input.TextArea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入消息... (Enter 发送)"
            autoSize={{ minRows: 1, maxRows: 4 }}
            disabled={!currentSession || isLoading}
          />
          {isLoading ? (
            <Button
              danger
              icon={<StopOutlined />}
              onClick={cancel}
            />
          ) : (
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              disabled={!currentSession || !input.trim()}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatPanel;
```

**Important:** The history loading approach above has a gap — `useSSE` doesn't expose `setMessages`. This needs to be addressed in the useSSE hook by adding a `setMessages` export. Update Task 3's useSSE to also return `setMessages`:

Add to useSSE return:
```ts
return { messages, isLoading, sendMessage, clearMessages, cancel, setMessages };
```

Then in ChatPanel, replace the history loading section:
```tsx
const { messages, isLoading, sendMessage, clearMessages, cancel, setMessages } = useSSE();

// ...

const handleSessionChange = async (sessionId: string) => {
  const session = sessions.find(s => s.id === sessionId);
  setCurrentSession(session || null);
  clearMessages();

  if (session && currentProject) {
    setLoadingHistory(true);
    try {
      const res = await sessionsApi.getHistory(currentProject.id, sessionId);
      const history: ChatMessage[] = res.data;
      const converted: SSEMessage[] = history.map(msg => ({
        type: msg.role === 'assistant' ? 'agent' : msg.role as 'user' | 'system',
        content: msg.content,
      }));
      setMessages(converted);
    } catch {
      message.error('加载会话历史失败');
    }
    setLoadingHistory(false);
  }
};
```

- [ ] **Step 2: Verify build passes**

Run: `cd frontend && npm run type-check`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ai/ChatPanel.tsx frontend/src/hooks/useSSE.ts
git commit -m "fix(frontend): load session history on switch, add stop button

- Call getHistory() when switching sessions and display previous messages
- Show Spin during history loading
- Replace send button with stop button during streaming
- Disable text input while streaming
- Pass isLoading prop to MessageBubble for loading indicator"
```

---

### Task 5: Add Markdown Rendering and Loading Indicator to MessageBubble

**Files:**
- Modify: `frontend/src/components/ai/MessageBubble.tsx`

- [ ] **Step 1: Rewrite MessageBubble with markdown rendering and loading indicator**

Key changes:
1. Import `marked`, `DOMPurify`, `Spin`, and `Typography`
2. Add `isLoading` prop
3. Render agent message content as sanitized HTML using `marked.parse()`
4. Show `Spin` when `isLoading` is true and content is empty

```tsx
import { Avatar, Tag, Spin, Typography } from 'antd';
import { RobotOutlined } from '@ant-design/icons';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import ThinkingBlock from './ThinkingBlock';

interface TimelineEvent {
  type: 'text' | 'thinking' | 'tool' | 'system' | 'error';
  content?: string;
  name?: string;
  status?: 'running' | 'completed';
  isDelegate?: boolean;
}

interface MessageBubbleProps {
  type: 'user' | 'agent' | 'system';
  content: string;
  agent?: string;
  timeline?: TimelineEvent[];
  isLoading?: boolean;
}

const renderMarkdown = (content: string): string => {
  const html = marked.parse(content) as string;
  return DOMPurify.sanitize(html);
};

const MessageBubble = ({ type, content, agent, timeline, isLoading }: MessageBubbleProps) => {
  if (type === 'user') {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
        <div style={{
          maxWidth: '80%',
          padding: '10px 14px',
          background: '#6366f1',
          color: '#fff',
          borderRadius: '14px 14px 4px 14px',
          fontSize: 13,
          lineHeight: 1.6,
          whiteSpace: 'pre-wrap',
        }}>
          {content}
        </div>
      </div>
    );
  }

  if (type === 'system') {
    return (
      <div style={{ textAlign: 'center', marginBottom: 12 }}>
        <span style={{ fontSize: 11, color: '#999', padding: '4px 12px', background: '#f5f5f5', borderRadius: 4 }}>
          {content}
        </span>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', gap: 10, marginBottom: 12, alignItems: 'flex-start' }}>
      <Avatar icon={<RobotOutlined />} size={32} style={{ backgroundColor: '#6366f1', flexShrink: 0 }} />
      <div style={{ flex: 1 }}>
        {agent && <Tag color="blue" style={{ marginBottom: 6 }}>{agent}</Tag>}
        {timeline?.map((event, i) => {
          if (event.type === 'thinking' && event.content) {
            return <ThinkingBlock key={i} content={event.content} />;
          }
          if (event.type === 'tool') {
            return (
              <div key={i} style={{
                padding: '6px 10px',
                background: '#f5f5f5',
                borderRadius: 6,
                marginBottom: 6,
                fontSize: 11,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}>
                <span style={{
                  width: 6, height: 6, borderRadius: '50%',
                  background: event.status === 'running' ? '#10b981' : '#999',
                }} />
                <span style={{ fontFamily: 'monospace' }}>{event.name}</span>
                {event.isDelegate && <Tag color="purple" style={{ fontSize: 9 }}>agent</Tag>}
              </div>
            );
          }
          return null;
        })}
        {isLoading && !content ? (
          <div style={{
            padding: '10px 14px',
            background: '#f5f5f5',
            borderRadius: '4px 14px 14px 14px',
          }}>
            <Spin size="small" />
          </div>
        ) : content ? (
          <Typography>
            <div
              style={{
                padding: '10px 14px',
                background: '#f5f5f5',
                borderRadius: '4px 14px 14px 14px',
                fontSize: 13,
                lineHeight: 1.7,
              }}
              dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
            />
          </Typography>
        ) : null}
      </div>
    </div>
  );
};

export default MessageBubble;
```

- [ ] **Step 2: Verify build passes**

Run: `cd frontend && npm run type-check`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ai/MessageBubble.tsx
git commit -m "fix(frontend): render AI messages as markdown, add loading indicator

- Use marked.parse() + DOMPurify.sanitize() for agent message content
- Wrap rendered HTML in Typography for consistent antd styling
- Show Spin inside bubble when loading and content is empty
- User messages remain plain text with pre-wrap"
```

---

### Task 6: Add World Setting Deletion

**Files:**
- Modify: `frontend/src/pages/world/WorldList.tsx`

- [ ] **Step 1: Add delete functionality to WorldList**

Key changes:
1. Import `Popconfirm`, `DeleteOutlined`
2. Add `handleDelete` function
3. Add delete button overlay on each `WorldCard`

```tsx
import { useState, useEffect } from 'react';
import { Row, Col, Button, Modal, Form, Input, message, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { worldApi } from '@/api/world';
import WorldCard from '@/components/cards/WorldCard';
import PageHeader from '@/components/common/PageHeader';
import EmptyState from '@/components/common/EmptyState';
import type { WorldSetting } from '@/types';

const WorldList = () => {
  const { id: projectId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [worlds, setWorlds] = useState<WorldSetting[]>([]);
  const [loading, setLoading] = useState(true);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [form] = Form.useForm();

  const loadWorlds = async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const res = await worldApi.list(projectId);
      setWorlds(res.data);
    } catch {
      message.error('加载世界观列表失败');
    }
    setLoading(false);
  };

  useEffect(() => {
    loadWorlds();
  }, [projectId]);

  const handleCreate = async () => {
    if (!projectId) return;
    try {
      const values = await form.validateFields();
      const res = await worldApi.create(projectId, values);
      setWorlds(prev => [...prev, res.data]);
      setCreateModalOpen(false);
      form.resetFields();
      message.success('世界观创建成功');
    } catch {
      // validation error
    }
  };

  const handleDelete = async (worldId: string) => {
    if (!projectId) return;
    try {
      await worldApi.delete(projectId, worldId);
      setWorlds(prev => prev.filter(w => w.id !== worldId));
      message.success('已删除');
    } catch {
      message.error('删除失败');
    }
  };

  return (
    <div>
      <PageHeader
        title="世界观设定"
        subtitle="管理你的世界构建元素"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
            新建设定
          </Button>
        }
      />

      {worlds.length === 0 && !loading ? (
        <EmptyState
          description="暂无世界观设定"
          actionText="新建设定"
          onAction={() => setCreateModalOpen(true)}
        />
      ) : (
        <Row gutter={[16, 16]}>
          {worlds.map(world => (
            <Col key={world.id} xs={24} sm={12} md={8}>
              <div style={{ position: 'relative' }}>
                <WorldCard
                  world={world}
                  onClick={() => navigate(`/projects/${projectId}/world/${world.id}`)}
                />
                <Popconfirm
                  title="确定删除这个世界观设定？"
                  onConfirm={() => handleDelete(world.id)}
                  okText="删除"
                  cancelText="取消"
                >
                  <Button
                    type="text"
                    danger
                    size="small"
                    icon={<DeleteOutlined />}
                    style={{ position: 'absolute', top: 8, right: 8 }}
                  />
                </Popconfirm>
              </div>
            </Col>
          ))}
        </Row>
      )}

      <Modal
        title="新建设定"
        open={createModalOpen}
        onOk={handleCreate}
        onCancel={() => setCreateModalOpen(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input placeholder="例：魔法体系" />
          </Form.Item>
          <Form.Item name="summary" label="摘要">
            <Input placeholder="简短描述（可选）" />
          </Form.Item>
          <Form.Item name="content" label="内容" rules={[{ required: true, message: '请输入内容' }]}>
            <Input.TextArea rows={6} placeholder="使用 Markdown 格式编写..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default WorldList;
```

- [ ] **Step 2: Verify build passes**

Run: `cd frontend && npm run type-check`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/world/WorldList.tsx
git commit -m "feat(frontend): add world setting deletion

Add delete button with Popconfirm to each WorldCard.
On confirm, call worldApi.delete() and remove from local state."
```

---

### Task 7: Fix Character Frontmatter Preservation

**Files:**
- Modify: `frontend/src/pages/characters/CharacterEdit.tsx`

- [ ] **Step 1: Store full meta and pass all fields on save**

Key changes:
1. Add `characterMeta` state to store the full parsed object (not just tags)
2. On save, merge `characterMeta` with current tags: `serializeWithFrontmatter({ ...characterMeta, tags }, content)`
3. Add loading spinner instead of returning null

```tsx
import { useState, useEffect } from 'react';
import { Button, Input, Tag, message, Space, Spin } from 'antd';
import { useParams, useNavigate } from 'react-router-dom';
import { charactersApi } from '@/api/characters';
import PageHeader from '@/components/common/PageHeader';
import MarkdownEditor from '@/components/common/MarkdownEditor';
import { parseCharacterMeta, serializeWithFrontmatter } from '@/utils/frontmatter';
import type { Character } from '@/types';
import type { FrontmatterData } from '@/utils/frontmatter';

const CharacterEdit = () => {
  const { id: projectId, charId } = useParams<{ id: string; charId: string }>();
  const navigate = useNavigate();
  const [character, setCharacter] = useState<Character | null>(null);
  const [name, setName] = useState('');
  const [summary, setSummary] = useState('');
  const [content, setContent] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [characterMeta, setCharacterMeta] = useState<FrontmatterData>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!projectId || !charId) return;
    charactersApi.get(projectId, charId).then(res => {
      setCharacter(res.data);
      setName(res.data.name);
      setSummary(res.data.summary || '');
      const meta = parseCharacterMeta(res.data.content || '');
      setContent(meta.content);
      setTags(meta.tags);
      // Store all frontmatter fields except tags (which we manage separately)
      const { tags: _, content: __, ...rest } = meta;
      setCharacterMeta(rest);
      setLoading(false);
    }).catch(() => {
      message.error('加载失败');
      navigate(`/projects/${projectId}/characters`);
    });
  }, [projectId, charId]);

  const handleSave = async () => {
    if (!projectId || !charId) return;
    setSaving(true);
    try {
      const fullContent = serializeWithFrontmatter({ ...characterMeta, tags }, content);
      await charactersApi.update(projectId, charId, { name, summary, content: fullContent });
      message.success('保存成功');
    } catch {
      message.error('保存失败');
    }
    setSaving(false);
  };

  const handleRemoveTag = (tag: string) => {
    setTags(prev => prev.filter(t => t !== tag));
  };

  const handleAddTag = (e: React.KeyboardEvent<HTMLInputElement>) => {
    const input = e.currentTarget;
    if (input.value.trim()) {
      setTags(prev => [...prev, input.value.trim()]);
      input.value = '';
    }
  };

  if (loading || !character) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title={character.name}
        breadcrumbs={[
          { title: '角色', path: `/projects/${projectId}/characters` },
          { title: character.name },
        ]}
        extra={
          <Space>
            <Button onClick={() => navigate(`/projects/${projectId}/characters`)}>返回</Button>
            <Button type="primary" loading={saving} onClick={handleSave}>保存</Button>
          </Space>
        }
      />

      <div style={{ marginBottom: 16 }}>
        <Input
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="角色名称"
          style={{ fontSize: 20, fontWeight: 700, border: 'none', padding: 0, marginBottom: 8 }}
        />
        <Input
          value={summary}
          onChange={e => setSummary(e.target.value)}
          placeholder="添加简介..."
          style={{ border: 'none', padding: 0, color: '#999' }}
        />
        <div style={{ display: 'flex', gap: 6, marginTop: 10, flexWrap: 'wrap' }}>
          {tags.map(tag => (
            <Tag key={tag} closable onClose={() => handleRemoveTag(tag)}>{tag}</Tag>
          ))}
          <Input
            placeholder="添加标签回车"
            size="small"
            style={{ width: 100 }}
            onPressEnter={handleAddTag}
          />
        </div>
      </div>

      <MarkdownEditor value={content} onChange={setContent} height={500} />
    </div>
  );
};

export default CharacterEdit;
```

- [ ] **Step 2: Verify build passes**

Run: `cd frontend && npm run type-check`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/characters/CharacterEdit.tsx
git commit -m "fix(frontend): preserve all frontmatter fields on character save

Store full parsed CharacterMeta (type, age, etc.) in state.
On save, merge stored meta with current tags before serializing.
Previously only tags were passed, causing other fields to be lost.
Also show Spin during loading instead of blank page."
```

---

### Task 8: Fix Chapter Renumbering

**Files:**
- Modify: `frontend/src/pages/chapters/ChapterList.tsx`

- [ ] **Step 1: Fix chapter numbering after delete and on create**

Key changes:
1. After delete: renumber remaining chapters sequentially
2. On create: use `Math.max(...)` instead of `chapters.length + 1`

Replace the `handleDelete` function (around line 72):
```tsx
const handleDelete = async (chapterId: string) => {
  if (!projectId) return;
  Modal.confirm({
    title: '确认删除',
    content: '删除后无法恢复，确认吗？',
    onOk: async () => {
      try {
        await chaptersApi.delete(projectId, chapterId);
        setChapters(prev => {
          const remaining = prev.filter(c => c.id !== chapterId);
          // Renumber sequentially
          const renumbered = remaining
            .sort((a, b) => a.chapter_number - b.chapter_number)
            .map((ch, i) => ({ ...ch, chapter_number: i + 1 }));
          // Fire-and-forget API calls for changed numbers
          renumbered.forEach((ch, i) => {
            if (ch.chapter_number !== remaining[i]?.chapter_number) {
              chaptersApi.update(projectId, ch.id, { chapter_number: ch.chapter_number }).catch(() => {});
            }
          });
          return renumbered;
        });
        message.success('删除成功');
      } catch {
        message.error('删除失败');
      }
    },
  });
};
```

Replace the `handleCreate` function (around line 56):
```tsx
const handleCreate = async () => {
  if (!projectId) return;
  try {
    const values = await form.validateFields();
    const nextNumber = chapters.length > 0
      ? Math.max(...chapters.map(c => c.chapter_number)) + 1
      : 1;
    const res = await chaptersApi.create(projectId, {
      ...values,
      chapter_number: nextNumber,
    });
    setChapters(prev => [...prev, res.data].sort((a, b) => a.chapter_number - b.chapter_number));
    setCreateModalOpen(false);
    form.resetFields();
    message.success('章节创建成功');
  } catch {
    // validation error
  }
};
```

The full file should be:
```tsx
import { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, message, Tag, Space } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { chaptersApi } from '@/api/chapters';
import PageHeader from '@/components/common/PageHeader';
import EmptyState from '@/components/common/EmptyState';
import { formatDate } from '@/utils/format';
import type { Chapter } from '@/types';

const ChapterList = () => {
  const { id: projectId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loading, setLoading] = useState(true);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [form] = Form.useForm();

  const loadChapters = async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const res = await chaptersApi.list(projectId);
      setChapters(res.data.sort((a, b) => a.chapter_number - b.chapter_number));
    } catch {
      message.error('加载章节列表失败');
    }
    setLoading(false);
  };

  useEffect(() => {
    loadChapters();
  }, [projectId]);

  const handleCreate = async () => {
    if (!projectId) return;
    try {
      const values = await form.validateFields();
      const nextNumber = chapters.length > 0
        ? Math.max(...chapters.map(c => c.chapter_number)) + 1
        : 1;
      const res = await chaptersApi.create(projectId, {
        ...values,
        chapter_number: nextNumber,
      });
      setChapters(prev => [...prev, res.data].sort((a, b) => a.chapter_number - b.chapter_number));
      setCreateModalOpen(false);
      form.resetFields();
      message.success('章节创建成功');
    } catch {
      // validation error
    }
  };

  const handleDelete = async (chapterId: string) => {
    if (!projectId) return;
    Modal.confirm({
      title: '确认删除',
      content: '删除后无法恢复，确认吗？',
      onOk: async () => {
        try {
          await chaptersApi.delete(projectId, chapterId);
          setChapters(prev => {
            const remaining = prev.filter(c => c.id !== chapterId);
            const renumbered = remaining
              .sort((a, b) => a.chapter_number - b.chapter_number)
              .map((ch, i) => ({ ...ch, chapter_number: i + 1 }));
            renumbered.forEach((ch) => {
              const original = remaining.find(r => r.id === ch.id);
              if (original && original.chapter_number !== ch.chapter_number) {
                chaptersApi.update(projectId, ch.id, { chapter_number: ch.chapter_number }).catch(() => {});
              }
            });
            return renumbered;
          });
          message.success('删除成功');
        } catch {
          message.error('删除失败');
        }
      },
    });
  };

  const columns = [
    { title: '#', dataIndex: 'chapter_number', width: 60 },
    {
      title: '标题',
      dataIndex: 'title',
      render: (title: string, record: Chapter) => (
        <a onClick={() => navigate(`/projects/${projectId}/chapters/${record.id}`)}>{title}</a>
      ),
    },
    {
      title: '字数',
      dataIndex: 'word_count',
      width: 100,
      render: (count: number) => count.toLocaleString(),
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 80,
      render: (status: string) => (
        <Tag color={status === 'published' ? 'green' : 'default'}>
          {status === 'published' ? '已发布' : '草稿'}
        </Tag>
      ),
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      width: 120,
      render: (date: string) => formatDate(date),
    },
    {
      title: '操作',
      width: 80,
      render: (_: unknown, record: Chapter) => (
        <Space>
          <Button type="text" size="small" icon={<EditOutlined />} onClick={() => navigate(`/projects/${projectId}/chapters/${record.id}`)} />
          <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)} />
        </Space>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="章节管理"
        subtitle="管理你的故事章节"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
            新建章节
          </Button>
        }
      />

      {chapters.length === 0 && !loading ? (
        <EmptyState
          description="暂无章节"
          actionText="新建章节"
          onAction={() => setCreateModalOpen(true)}
        />
      ) : (
        <Table
          dataSource={chapters}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      )}

      <Modal
        title="新建章节"
        open={createModalOpen}
        onOk={handleCreate}
        onCancel={() => setCreateModalOpen(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="title" label="章节标题" rules={[{ required: true, message: '请输入标题' }]}>
            <Input placeholder="例：第一章 初入江湖" />
          </Form.Item>
          <Form.Item name="summary" label="摘要">
            <Input placeholder="章节摘要（可选）" />
          </Form.Item>
          <Form.Item name="content" label="内容" rules={[{ required: true, message: '请输入内容' }]}>
            <Input.TextArea rows={6} placeholder="使用 Markdown 格式编写..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ChapterList;
```

- [ ] **Step 2: Verify build passes**

Run: `cd frontend && npm run type-check`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/chapters/ChapterList.tsx
git commit -m "fix(frontend): auto-renumber chapters after delete, fix new chapter numbering

After deleting a chapter, renumber remaining chapters sequentially
(1, 2, 3...) and fire-and-forget API updates for changed numbers.
New chapter number uses Math.max(...)+1 instead of length+1 to avoid
gaps when chapters were previously deleted."
```

---

### Task 9: Add Loading Spinners to WorldEdit

**Files:**
- Modify: `frontend/src/pages/world/WorldEdit.tsx`

- [ ] **Step 1: Replace null return with Spin during loading**

Change line 62 from:
```tsx
if (loading || !world) return null;
```

To:
```tsx
if (loading || !world) {
  return (
    <div style={{ textAlign: 'center', padding: 100 }}>
      <Spin size="large" />
    </div>
  );
}
```

Add `Spin` to the antd imports:
```tsx
import { Button, Input, message, Space, Spin } from 'antd';
```

- [ ] **Step 2: Verify build passes**

Run: `cd frontend && npm run type-check`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/world/WorldEdit.tsx
git commit -m "fix(frontend): show loading spinner in WorldEdit instead of blank page"
```

---

### Task 10: Final Verification

- [ ] **Step 1: Run full type-check**

Run: `cd frontend && npm run type-check`
Expected: No errors

- [ ] **Step 2: Run lint**

Run: `cd frontend && npm run lint`
Expected: No warnings or errors

- [ ] **Step 3: Verify all changes are committed**

Run: `git status`
Expected: No uncommitted changes

- [ ] **Step 4: Review commit log**

Run: `git log --oneline -10`
Expected: 8-9 commits, one per task
