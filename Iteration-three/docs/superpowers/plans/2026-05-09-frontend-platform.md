# 前端平台实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建基于 React + Vite + TypeScript + Ant Design 的 AI 小说创作平台前端，包含项目管理、内容编辑、AI 对话功能。

**Architecture:** 经典侧边栏布局（Layout + Sider + Menu），内容管理使用 Markdown 编辑器，AI 对话使用 FloatButton + Drawer 悬浮面板，SSE 流式输出参考 agent-tester 实现。

**Tech Stack:** React 18, TypeScript, Vite, Ant Design 5, Axios, React Router v6, @uiw/react-md-editor, gray-matter

**Spec:** `docs/superpowers/specs/2026-05-09-frontend-platform-design.md`

**参考:** `agent-tester/index.html` (SSE 流式对话实现)

---

## File Structure

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── vite.config.ts
├── .env.development
├── public/
│   └── vite.svg
├── src/
│   ├── main.tsx                    # 入口，挂载 App
│   ├── App.tsx                     # ConfigProvider + Router
│   ├── vite-env.d.ts
│   ├── types/
│   │   └── index.ts                # 所有 TypeScript 类型定义
│   ├── api/
│   │   ├── client.ts               # Axios 实例
│   │   ├── projects.ts             # 项目 API
│   │   ├── world.ts                # 世界观 API
│   │   ├── characters.ts           # 角色 API
│   │   ├── outlines.ts             # 大纲 API
│   │   ├── chapters.ts             # 章节 API
│   │   ├── reviews.ts              # 评审 API
│   │   └── sessions.ts             # 会话 API
│   ├── contexts/
│   │   └── ProjectContext.tsx       # 当前项目上下文
│   ├── hooks/
│   │   ├── useProject.ts           # 项目数据 hook
│   │   └── useSSE.ts              # SSE 流式 hook
│   ├── utils/
│   │   ├── format.ts               # 格式化工具
│   │   └── frontmatter.ts          # YAML frontmatter 解析
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppLayout.tsx        # 整体布局
│   │   │   ├── IconSidebar.tsx      # 左侧图标栏
│   │   │   └── SecondaryNav.tsx     # 二级导航
│   │   ├── common/
│   │   │   ├── PageHeader.tsx       # 页面头部
│   │   │   ├── EmptyState.tsx       # 空状态
│   │   │   └── MarkdownEditor.tsx   # Markdown 编辑器封装
│   │   ├── cards/
│   │   │   ├── ProjectCard.tsx      # 项目卡片
│   │   │   ├── WorldCard.tsx        # 世界观卡片
│   │   │   └── CharacterCard.tsx    # 角色卡片
│   │   └── ai/
│   │       ├── AIFab.tsx            # 悬浮球入口
│   │       ├── ChatPanel.tsx        # 聊天面板
│   │       ├── MessageBubble.tsx    # 消息气泡
│   │       └── ThinkingBlock.tsx    # Thinking 折叠块
│   └── pages/
│       ├── Dashboard.tsx            # 项目仪表盘
│       ├── world/
│       │   ├── WorldList.tsx        # 世界观列表
│       │   └── WorldEdit.tsx        # 世界观编辑
│       ├── characters/
│       │   ├── CharacterList.tsx    # 角色列表
│       │   └── CharacterEdit.tsx    # 角色编辑
│       ├── outline/
│       │   └── OutlineEditor.tsx    # 大纲编辑
│       ├── chapters/
│       │   ├── ChapterList.tsx      # 章节列表
│       │   └── ChapterEdit.tsx      # 章节编辑
│       ├── reviews/
│       │   └── ReviewList.tsx       # 评审列表
│       └── settings/
│           └── ProjectSettings.tsx  # 项目设置
```

---

## Task 1: 项目初始化

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.app.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/vite-env.d.ts`
- Create: `frontend/.env.development`
- Create: `frontend/.gitignore`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "novel-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "type-check": "tsc -b --noEmit",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
  },
  "dependencies": {
    "antd": "^5.21.0",
    "@ant-design/icons": "^5.5.0",
    "axios": "^1.7.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.26.0",
    "@uiw/react-md-editor": "^4.0.0",
    "gray-matter": "^4.0.3",
    "marked": "^14.0.0",
    "dompurify": "^3.1.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@types/dompurify": "^3.0.5",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.5.0",
    "vite": "^5.4.0",
    "eslint": "^8.57.0",
    "@typescript-eslint/eslint-plugin": "^7.0.0",
    "@typescript-eslint/parser": "^7.0.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.0"
  }
}
```

- [ ] **Step 2: 创建 tsconfig.json**

```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

- [ ] **Step 3: 创建 tsconfig.app.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"]
}
```

- [ ] **Step 4: 创建 tsconfig.node.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 5: 创建 vite.config.ts**

```ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

- [ ] **Step 6: 创建 index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AI 小说创作平台</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 7: 创建 src/vite-env.d.ts**

```ts
/// <reference types="vite/client" />
```

- [ ] **Step 8: 创建 .env.development**

```
VITE_API_BASE_URL=/api/v1
VITE_APP_TITLE=AI 小说创作平台
```

- [ ] **Step 9: 创建 .gitignore**

```
node_modules
dist
.env.local
.env.*.local
*.tsbuildinfo
```

- [ ] **Step 10: 创建 src/main.tsx**

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

- [ ] **Step 11: 创建 src/App.tsx**

```tsx
import { ConfigProvider } from 'antd';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

const App = () => {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#6366f1',
          borderRadius: 6,
        },
      }}
    >
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<div>Home</div>} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;
```

- [ ] **Step 12: 安装依赖并验证**

Run: `cd frontend && npm install`
Expected: 安装成功无报错

Run: `npm run type-check`
Expected: 无类型错误

- [ ] **Step 13: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): initialize React + Vite + TypeScript project"
```

---

## Task 2: TypeScript 类型定义

**Files:**
- Create: `frontend/src/types/index.ts`

- [ ] **Step 1: 创建类型定义文件**

```ts
// src/types/index.ts

// ── Project ──
export interface Project {
  id: string;
  name: string;
  description: string | null;
  cover_image: string | null;
  status: string;
  word_count: number;
  created_at: string;
  updated_at: string;
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
  cover_image?: string;
}

export interface UpdateProjectRequest {
  name?: string;
  status?: string;
  description?: string;
  cover_image?: string;
  word_count?: number;
}

// ── World ──
export interface WorldSetting {
  id: string;
  project_id: string;
  name: string;
  summary: string | null;
  file_path: string;
  created_at: string;
  updated_at: string;
  content?: string;
}

export interface CreateWorldRequest {
  name: string;
  content: string;
  summary?: string;
}

export interface UpdateWorldRequest {
  name?: string;
  content?: string;
  summary?: string;
}

// ── Character ──
export interface Character {
  id: string;
  project_id: string;
  name: string;
  summary: string | null;
  file_path: string;
  created_at: string;
  updated_at: string;
  content?: string;
}

export interface CharacterMeta {
  tags: string[];
  type: string;
  age: string;
  content: string;
}

export interface CreateCharacterRequest {
  name: string;
  content: string;
  summary?: string;
}

export interface UpdateCharacterRequest {
  name?: string;
  content?: string;
  summary?: string;
}

// ── Outline ──
export interface Outline {
  id: string;
  project_id: string;
  parent_id: string | null;
  title: string;
  type: string;
  sort_order: number;
  file_path: string;
  created_at: string;
  updated_at: string;
  content?: string;
  children?: Outline[];
}

export interface CreateOutlineRequest {
  title: string;
  content: string;
  type?: string;
  parent_id?: string;
  sort_order?: number;
}

export interface UpdateOutlineRequest {
  title?: string;
  content?: string;
  type?: string;
  parent_id?: string;
  sort_order?: number;
}

// ── Chapter ──
export interface Chapter {
  id: string;
  project_id: string;
  title: string;
  word_count: number;
  status: string;
  chapter_number: number;
  summary: string | null;
  published_at: string | null;
  file_path: string;
  created_at: string;
  updated_at: string;
  content?: string;
}

export interface CreateChapterRequest {
  title: string;
  content: string;
  word_count?: number;
  chapter_number?: number;
  summary?: string;
}

export interface UpdateChapterRequest {
  title?: string;
  content?: string;
  word_count?: number;
  status?: string;
  chapter_number?: number;
  summary?: string;
}

// ── Review ──
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

// ── Session / Chat ──
export interface Session {
  id: string;
  project_id: string;
  title: string | null;
  created_at: string;
  last_active_at: string;
}

export interface CreateSessionRequest {
  title?: string;
}

export interface ChatRequest {
  message: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'tool' | 'system';
  content: string;
  thinking_content?: string;
  tool_calls?: ToolCall[];
  tool_call_id?: string;
}

export interface ToolCall {
  id: string;
  name: string;
  arguments: string;
}

// ── SSE Events ──
export interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
}

// ── Tree Node (for Ant Design Tree) ──
export interface TreeNodeData {
  key: string;
  title: string;
  children?: TreeNodeData[];
  type?: string;
  content?: string;
  isLeaf?: boolean;
}
```

- [ ] **Step 2: 类型检查**

Run: `cd frontend && npm run type-check`
Expected: 无错误

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/
git commit -m "feat(frontend): add TypeScript type definitions"
```

---

## Task 3: API 客户端

**Files:**
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/projects.ts`
- Create: `frontend/src/api/world.ts`
- Create: `frontend/src/api/characters.ts`
- Create: `frontend/src/api/outlines.ts`
- Create: `frontend/src/api/chapters.ts`
- Create: `frontend/src/api/reviews.ts`
- Create: `frontend/src/api/sessions.ts`

- [ ] **Step 1: 创建 Axios 实例**

```ts
// src/api/client.ts
import axios from 'axios';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default client;
```

- [ ] **Step 2: 创建 projects.ts**

```ts
// src/api/projects.ts
import client from './client';
import type { Project, CreateProjectRequest, UpdateProjectRequest } from '@/types';

export const projectsApi = {
  list: (limit = 100, offset = 0) =>
    client.get<Project[]>('/projects/', { params: { limit, offset } }),

  get: (id: string) =>
    client.get<Project>(`/projects/${id}`),

  create: (data: CreateProjectRequest) =>
    client.post<Project>('/projects/', data),

  update: (id: string, data: UpdateProjectRequest) =>
    client.patch<Project>(`/projects/${id}`, data),

  delete: (id: string) =>
    client.delete(`/projects/${id}`),
};
```

- [ ] **Step 3: 创建 world.ts**

```ts
// src/api/world.ts
import client from './client';
import type { WorldSetting, CreateWorldRequest, UpdateWorldRequest } from '@/types';

export const worldApi = {
  list: (projectId: string) =>
    client.get<WorldSetting[]>(`/projects/${projectId}/world/`),

  get: (projectId: string, worldId: string) =>
    client.get<WorldSetting>(`/projects/${projectId}/world/${worldId}`),

  create: (projectId: string, data: CreateWorldRequest) =>
    client.post<WorldSetting>(`/projects/${projectId}/world/`, data),

  update: (projectId: string, worldId: string, data: UpdateWorldRequest) =>
    client.post<WorldSetting>(`/projects/${projectId}/world/${worldId}/update`, data),

  delete: (projectId: string, worldId: string) =>
    client.post(`/projects/${projectId}/world/${worldId}/delete`),
};
```

- [ ] **Step 4: 创建 characters.ts**

```ts
// src/api/characters.ts
import client from './client';
import type { Character, CreateCharacterRequest, UpdateCharacterRequest } from '@/types';

export const charactersApi = {
  list: (projectId: string) =>
    client.get<Character[]>(`/projects/${projectId}/characters/`),

  get: (projectId: string, characterId: string) =>
    client.get<Character>(`/projects/${projectId}/characters/${characterId}`),

  create: (projectId: string, data: CreateCharacterRequest) =>
    client.post<Character>(`/projects/${projectId}/characters/`, data),

  update: (projectId: string, characterId: string, data: UpdateCharacterRequest) =>
    client.post<Character>(`/projects/${projectId}/characters/${characterId}/update`, data),

  delete: (projectId: string, characterId: string) =>
    client.post(`/projects/${projectId}/characters/${characterId}/delete`),
};
```

- [ ] **Step 5: 创建 outlines.ts**

```ts
// src/api/outlines.ts
import client from './client';
import type { Outline, CreateOutlineRequest, UpdateOutlineRequest } from '@/types';

export const outlinesApi = {
  getRoot: (projectId: string) =>
    client.get<Outline>(`/projects/${projectId}/outlines/`),

  get: (projectId: string, outlineId: string) =>
    client.get<Outline>(`/projects/${projectId}/outlines/${outlineId}`),

  getChildren: (projectId: string, outlineId: string) =>
    client.get<Outline[]>(`/projects/${projectId}/outlines/${outlineId}/children`),

  getTree: (projectId: string, outlineId: string) =>
    client.get<Outline>(`/projects/${projectId}/outlines/${outlineId}/tree`),

  create: (projectId: string, data: CreateOutlineRequest) =>
    client.post<Outline>(`/projects/${projectId}/outlines/`, data),

  update: (projectId: string, outlineId: string, data: UpdateOutlineRequest) =>
    client.post<Outline>(`/projects/${projectId}/outlines/${outlineId}/update`, data),

  delete: (projectId: string, outlineId: string) =>
    client.post(`/projects/${projectId}/outlines/${outlineId}/delete`),
};
```

- [ ] **Step 6: 创建 chapters.ts**

```ts
// src/api/chapters.ts
import client from './client';
import type { Chapter, CreateChapterRequest, UpdateChapterRequest } from '@/types';

export const chaptersApi = {
  list: (projectId: string) =>
    client.get<Chapter[]>(`/projects/${projectId}/chapters/`),

  get: (projectId: string, chapterId: string) =>
    client.get<Chapter>(`/projects/${projectId}/chapters/${chapterId}`),

  create: (projectId: string, data: CreateChapterRequest) =>
    client.post<Chapter>(`/projects/${projectId}/chapters/`, data),

  update: (projectId: string, chapterId: string, data: UpdateChapterRequest) =>
    client.post<Chapter>(`/projects/${projectId}/chapters/${chapterId}/update`, data),

  delete: (projectId: string, chapterId: string) =>
    client.post(`/projects/${projectId}/chapters/${chapterId}/delete`),
};
```

- [ ] **Step 7: 创建 reviews.ts**

```ts
// src/api/reviews.ts
import client from './client';
import type { Review, CreateReviewRequest } from '@/types';

export const reviewsApi = {
  list: (projectId: string) =>
    client.get<Review[]>(`/projects/${projectId}/reviews/`),

  get: (projectId: string, reviewId: string) =>
    client.get<Review>(`/projects/${projectId}/reviews/${reviewId}`),

  create: (projectId: string, data: CreateReviewRequest) =>
    client.post<Review>(`/projects/${projectId}/reviews/`, data),
};
```

- [ ] **Step 8: 创建 sessions.ts**

```ts
// src/api/sessions.ts
import client from './client';
import type { Session, CreateSessionRequest } from '@/types';

export const sessionsApi = {
  list: (projectId: string, limit = 50, offset = 0) =>
    client.get<Session[]>(`/projects/${projectId}/sessions/`, { params: { limit, offset } }),

  create: (projectId: string, data?: CreateSessionRequest) =>
    client.post<Session>(`/projects/${projectId}/sessions/`, data),

  delete: (projectId: string, sessionId: string) =>
    client.delete(`/projects/${projectId}/sessions/${sessionId}`),

  getHistory: (projectId: string, sessionId: string) =>
    client.get(`/projects/${projectId}/sessions/${sessionId}/history`),

  stream: async (projectId: string, sessionId: string, message: string, onEvent: (event: string, data: Record<string, unknown>) => void) => {
    const response = await fetch(`/api/v1/projects/${projectId}/sessions/${sessionId}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let currentEventType = '';

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
            const parsed = JSON.parse(raw);
            onEvent(currentEventType, parsed);
          } catch { /* ignore malformed JSON */ }
        }
      }
    }
  },
};
```

- [ ] **Step 9: 类型检查**

Run: `cd frontend && npm run type-check`
Expected: 无错误

- [ ] **Step 10: Commit**

```bash
git add frontend/src/api/
git commit -m "feat(frontend): add API client layer for all endpoints"
```

---

## Task 4: 工具函数

**Files:**
- Create: `frontend/src/utils/format.ts`
- Create: `frontend/src/utils/frontmatter.ts`

- [ ] **Step 1: 创建 format.ts**

```ts
// src/utils/format.ts

export const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return '刚刚';
  if (diffMins < 60) return `${diffMins} 分钟前`;
  if (diffHours < 24) return `${diffHours} 小时前`;
  if (diffDays < 7) return `${diffDays} 天前`;

  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
  });
};

export const formatWordCount = (count: number): string => {
  if (count < 1000) return `${count} 字`;
  return `${(count / 1000).toFixed(1)}k 字`;
};

export const countWords = (text: string): number => {
  // 简单字数统计：中文按字符，英文按空格分词
  const chineseChars = (text.match(/[一-鿿]/g) || []).length;
  const englishWords = text.replace(/[一-鿿]/g, '').split(/\s+/).filter(Boolean).length;
  return chineseChars + englishWords;
};
```

- [ ] **Step 2: 创建 frontmatter.ts**

```ts
// src/utils/frontmatter.ts
import matter from 'gray-matter';

export interface FrontmatterData {
  [key: string]: unknown;
}

export const parseFrontmatter = (content: string): { data: FrontmatterData; body: string } => {
  const { data, content: body } = matter(content);
  return { data, body };
};

export const serializeWithFrontmatter = (data: FrontmatterData, body: string): string => {
  return matter.stringify(body, data);
};

export const parseCharacterMeta = (content: string) => {
  const { data, body } = parseFrontmatter(content);
  return {
    tags: (data.tags as string[]) || [],
    type: (data.type as string) || '',
    age: (data.age as string) || '',
    content: body,
  };
};
```

- [ ] **Step 3: 类型检查**

Run: `cd frontend && npm run type-check`
Expected: 无错误

- [ ] **Step 4: Commit**

```bash
git add frontend/src/utils/
git commit -m "feat(frontend): add utility functions and frontmatter parser"
```

---

## Task 5: 布局组件

**Files:**
- Create: `frontend/src/components/layout/AppLayout.tsx`
- Create: `frontend/src/components/layout/IconSidebar.tsx`
- Create: `frontend/src/components/layout/SecondaryNav.tsx`
- Create: `frontend/src/contexts/ProjectContext.tsx`

- [ ] **Step 1: 创建 ProjectContext**

```tsx
// src/contexts/ProjectContext.tsx
import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import type { Project } from '@/types';

interface ProjectContextType {
  currentProject: Project | null;
  setCurrentProject: (project: Project | null) => void;
}

const ProjectContext = createContext<ProjectContextType>({
  currentProject: null,
  setCurrentProject: () => {},
});

export const useProjectContext = () => useContext(ProjectContext);

export const ProjectProvider = ({ children }: { children: ReactNode }) => {
  const [currentProject, setCurrentProject] = useState<Project | null>(null);

  const handleSetProject = useCallback((project: Project | null) => {
    setCurrentProject(project);
  }, []);

  return (
    <ProjectContext.Provider value={{ currentProject, setCurrentProject: handleSetProject }}>
      {children}
    </ProjectContext.Provider>
  );
};
```

- [ ] **Step 2: 创建 IconSidebar**

```tsx
// src/components/layout/IconSidebar.tsx
import { Layout, Menu } from 'antd';
import {
  HomeOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useProjectContext } from '@/contexts/ProjectContext';

const { Sider } = Layout;

const IconSidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { currentProject } = useProjectContext();

  const isDashboard = location.pathname === '/';

  const items = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: '首页',
    },
  ];

  if (currentProject) {
    items.push({
      key: `/projects/${currentProject.id}/settings`,
      icon: <SettingOutlined />,
      label: '设置',
    });
  }

  return (
    <Sider
      width={64}
      theme="dark"
      collapsed={true}
      style={{
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        zIndex: 100,
      }}
    >
      <div style={{
        height: 48,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#fff',
        fontWeight: 700,
        fontSize: 18,
      }}>
        N
      </div>
      <Menu
        mode="inline"
        theme="dark"
        selectedKeys={[isDashboard ? '/' : '']}
        items={items}
        onClick={({ key }) => navigate(key)}
        style={{ borderRight: 0 }}
      />
    </Sider>
  );
};

export default IconSidebar;
```

- [ ] **Step 3: 创建 SecondaryNav**

```tsx
// src/components/layout/SecondaryNav.tsx
import { Layout, Menu } from 'antd';
import {
  GlobalOutlined,
  UserOutlined,
  OrderedListOutlined,
  BookOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useProjectContext } from '@/contexts/ProjectContext';

const { Sider } = Layout;

const SecondaryNav = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { currentProject } = useProjectContext();

  if (!currentProject) return null;

  const basePath = `/projects/${currentProject.id}`;

  const items = [
    {
      key: `${basePath}/world`,
      icon: <GlobalOutlined />,
      label: '世界观',
    },
    {
      key: `${basePath}/characters`,
      icon: <UserOutlined />,
      label: '角色',
    },
    {
      key: `${basePath}/outline`,
      icon: <OrderedListOutlined />,
      label: '大纲',
    },
    {
      key: `${basePath}/chapters`,
      icon: <BookOutlined />,
      label: '章节',
    },
    {
      key: `${basePath}/reviews`,
      icon: <FileTextOutlined />,
      label: '评审',
    },
  ];

  // Find selected key by matching prefix
  const selectedKey = items.find(item => location.pathname.startsWith(item.key))?.key || '';

  return (
    <Sider
      width={200}
      theme="light"
      style={{
        height: '100vh',
        position: 'fixed',
        left: 64,
        top: 0,
        bottom: 0,
        borderRight: '1px solid #f0f0f0',
        overflow: 'auto',
      }}
    >
      <div style={{
        padding: '16px 12px 8px',
        fontSize: 11,
        color: '#999',
        textTransform: 'uppercase',
        letterSpacing: 0.5,
        fontWeight: 600,
      }}>
        {currentProject.name}
      </div>
      <Menu
        mode="inline"
        selectedKeys={[selectedKey]}
        items={items}
        onClick={({ key }) => navigate(key)}
        style={{ borderRight: 0 }}
      />
    </Sider>
  );
};

export default SecondaryNav;
```

- [ ] **Step 4: 创建 AppLayout**

```tsx
// src/components/layout/AppLayout.tsx
import { Layout, theme } from 'antd';
import { Outlet } from 'react-router-dom';
import IconSidebar from './IconSidebar';
import SecondaryNav from './SecondaryNav';
import AIFab from '@/components/ai/AIFab';

const { Content } = Layout;

const AppLayout = () => {
  const { token: { colorBgContainer, borderRadiusLG } } = theme.useToken();

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
          <div style={{
            maxWidth: 1200,
            margin: '0 auto',
          }}>
            <Outlet />
          </div>
        </Content>
      </Layout>
      <AIFab />
    </Layout>
  );
};

export default AppLayout;
```

- [ ] **Step 5: 创建 Dashboard 布局（无二级导航）**

```tsx
// src/components/layout/DashboardLayout.tsx
import { Layout, theme } from 'antd';
import { Outlet } from 'react-router-dom';
import IconSidebar from './IconSidebar';

const { Content } = Layout;

const DashboardLayout = () => {
  const { token: { colorBgContainer } } = theme.useToken();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <IconSidebar />
      <Layout style={{ marginLeft: 64 }}>
        <Content style={{
          padding: 24,
          background: colorBgContainer,
          minHeight: '100vh',
        }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default DashboardLayout;
```

- [ ] **Step 6: 更新 App.tsx 添加路由**

```tsx
// src/App.tsx
import { ConfigProvider } from 'antd';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ProjectProvider } from '@/contexts/ProjectContext';
import DashboardLayout from '@/components/layout/DashboardLayout';
import AppLayout from '@/components/layout/AppLayout';
import Dashboard from '@/pages/Dashboard';

const App = () => {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#6366f1',
          borderRadius: 6,
        },
      }}
    >
      <ProjectProvider>
        <BrowserRouter>
          <Routes>
            {/* Dashboard - 无二级导航 */}
            <Route element={<DashboardLayout />}>
              <Route path="/" element={<Dashboard />} />
            </Route>

            {/* 项目页面 - 有二级导航 */}
            <Route element={<AppLayout />}>
              <Route path="/projects/:id/world" element={<div>World</div>} />
              <Route path="/projects/:id/characters" element={<div>Characters</div>} />
              <Route path="/projects/:id/outline" element={<div>Outline</div>} />
              <Route path="/projects/:id/chapters" element={<div>Chapters</div>} />
              <Route path="/projects/:id/reviews" element={<div>Reviews</div>} />
              <Route path="/projects/:id/settings" element={<div>Settings</div>} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ProjectProvider>
    </ConfigProvider>
  );
};

export default App;
```

- [ ] **Step 7: 创建占位 Dashboard 页面**

```tsx
// src/pages/Dashboard.tsx
const Dashboard = () => {
  return <div>Dashboard - TODO</div>;
};

export default Dashboard;
```

- [ ] **Step 8: 创建占位 AIFab 组件**

```tsx
// src/components/ai/AIFab.tsx
const AIFab = () => {
  return null; // TODO: Task 14
};

export default AIFab;
```

- [ ] **Step 9: 类型检查**

Run: `cd frontend && npm run type-check`
Expected: 无错误

- [ ] **Step 10: Commit**

```bash
git add frontend/src/
git commit -m "feat(frontend): add layout components and routing"
```

---

## Task 6: 项目仪表盘

**Files:**
- Create: `frontend/src/components/cards/ProjectCard.tsx`
- Modify: `frontend/src/pages/Dashboard.tsx`

- [ ] **Step 1: 创建 ProjectCard**

```tsx
// src/components/cards/ProjectCard.tsx
import { Card, Tag } from 'antd';
import type { Project } from '@/types';
import { formatDate } from '@/utils/format';

const GRADIENTS = [
  'linear-gradient(135deg, #667eea, #764ba2)',
  'linear-gradient(135deg, #f093fb, #f5576c)',
  'linear-gradient(135deg, #4facfe, #00f2fe)',
  'linear-gradient(135deg, #43e97b, #38f9d7)',
  'linear-gradient(135deg, #fa709a, #fee140)',
];

interface ProjectCardProps {
  project: Project;
  onClick: () => void;
}

const ProjectCard = ({ project, onClick }: ProjectCardProps) => {
  const gradient = GRADIENTS[project.name.length % GRADIENTS.length];

  return (
    <Card
      hoverable
      onClick={onClick}
      style={{ overflow: 'hidden', borderRadius: 12 }}
      cover={
        <div style={{
          height: 80,
          background: gradient,
          display: 'flex',
          alignItems: 'flex-end',
          padding: '12px 14px',
        }}>
          <span style={{
            color: '#fff',
            fontSize: 14,
            fontWeight: 600,
          }}>
            {project.name}
          </span>
        </div>
      }
      styles={{ body: { padding: 14 } }}
    >
      <div style={{ fontSize: 11, color: '#999', marginBottom: 8, height: 36, overflow: 'hidden' }}>
        {project.description || '暂无描述'}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Tag color="blue">{project.word_count.toLocaleString()} 字</Tag>
        <span style={{ fontSize: 10, color: '#999' }}>{formatDate(project.updated_at)}</span>
      </div>
    </Card>
  );
};

export default ProjectCard;
```

- [ ] **Step 2: 实现 Dashboard 页面**

```tsx
// src/pages/Dashboard.tsx
import { useState, useEffect } from 'react';
import { Row, Col, Card, Button, Input, Modal, Form, message, Statistic } from 'antd';
import { PlusOutlined, SearchOutlined, ProjectOutlined, EditOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { projectsApi } from '@/api/projects';
import ProjectCard from '@/components/cards/ProjectCard';
import type { Project } from '@/types';

const Dashboard = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [form] = Form.useForm();

  const loadProjects = async () => {
    setLoading(true);
    try {
      const res = await projectsApi.list();
      setProjects(res.data);
    } catch {
      message.error('加载项目列表失败');
    }
    setLoading(false);
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      const res = await projectsApi.create(values);
      setProjects(prev => [...prev, res.data]);
      setCreateModalOpen(false);
      form.resetFields();
      message.success('项目创建成功');
    } catch {
      // validation error
    }
  };

  const filtered = projects.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase())
  );

  const totalWords = projects.reduce((sum, p) => sum + p.word_count, 0);

  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic title="总项目数" value={projects.length} prefix={<ProjectOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="总字数" value={totalWords} prefix={<EditOutlined />} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="活跃项目" value={projects.filter(p => p.status === 'active').length} />
          </Card>
        </Col>
      </Row>

      {/* 搜索 + 新建 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Input
          placeholder="搜索项目..."
          prefix={<SearchOutlined />}
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ width: 300 }}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
          新建项目
        </Button>
      </div>

      {/* 项目网格 */}
      <Row gutter={[16, 16]}>
        {filtered.map(project => (
          <Col key={project.id} xs={24} sm={12} md={8} lg={6}>
            <ProjectCard
              project={project}
              onClick={() => navigate(`/projects/${project.id}/world`)}
            />
          </Col>
        ))}
        <Col xs={24} sm={12} md={8} lg={6}>
          <Card
            hoverable
            style={{
              borderRadius: 12,
              border: '2px dashed #e0e0e0',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: 180,
            }}
            onClick={() => setCreateModalOpen(true)}
          >
            <div style={{ textAlign: 'center' }}>
              <PlusOutlined style={{ fontSize: 24, color: '#999', marginBottom: 8 }} />
              <div style={{ color: '#999', fontSize: 12 }}>创建新项目</div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 创建项目弹窗 */}
      <Modal
        title="新建项目"
        open={createModalOpen}
        onOk={handleCreate}
        onCancel={() => setCreateModalOpen(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }]}>
            <Input placeholder="输入项目名称" />
          </Form.Item>
          <Form.Item name="description" label="项目描述">
            <Input.TextArea placeholder="输入项目描述（可选）" rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Dashboard;
```

- [ ] **Step 3: 类型检查**

Run: `cd frontend && npm run type-check`
Expected: 无错误

- [ ] **Step 4: Commit**

```bash
git add frontend/src/
git commit -m "feat(frontend): implement project dashboard with CRUD"
```

---

## Task 7: Markdown 编辑器组件

**Files:**
- Create: `frontend/src/components/common/MarkdownEditor.tsx`
- Create: `frontend/src/components/common/PageHeader.tsx`
- Create: `frontend/src/components/common/EmptyState.tsx`

- [ ] **Step 1: 创建 MarkdownEditor**

```tsx
// src/components/common/MarkdownEditor.tsx
import MDEditor from '@uiw/react-md-editor';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  height?: number;
  placeholder?: string;
}

const MarkdownEditor = ({ value, onChange, height = 400, placeholder }: MarkdownEditorProps) => {
  return (
    <div data-color-mode="light">
      <MDEditor
        value={value}
        onChange={(val) => onChange(val || '')}
        height={height}
        preview="live"
      />
    </div>
  );
};

export default MarkdownEditor;
```

- [ ] **Step 2: 创建 PageHeader**

```tsx
// src/components/common/PageHeader.tsx
import { Breadcrumb, Button, Space } from 'antd';

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
            title: item.path ? <a href={item.path}>{item.title}</a> : item.title,
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

- [ ] **Step 3: 创建 EmptyState**

```tsx
// src/components/common/EmptyState.tsx
import { Empty, Button } from 'antd';

interface EmptyStateProps {
  description?: string;
  actionText?: string;
  onAction?: () => void;
}

const EmptyState = ({ description = '暂无数据', actionText, onAction }: EmptyStateProps) => {
  return (
    <div style={{ textAlign: 'center', padding: '60px 0' }}>
      <Empty description={description}>
        {actionText && onAction && (
          <Button type="primary" onClick={onAction}>{actionText}</Button>
        )}
      </Empty>
    </div>
  );
};

export default EmptyState;
```

- [ ] **Step 4: 类型检查**

Run: `cd frontend && npm run type-check`
Expected: 无错误

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/common/
git commit -m "feat(frontend): add common components (MarkdownEditor, PageHeader, EmptyState)"
```

---

## Task 8: 世界观管理

**Files:**
- Create: `frontend/src/components/cards/WorldCard.tsx`
- Create: `frontend/src/pages/world/WorldList.tsx`
- Create: `frontend/src/pages/world/WorldEdit.tsx`

- [ ] **Step 1: 创建 WorldCard**

```tsx
// src/components/cards/WorldCard.tsx
import { Card, Tag } from 'antd';
import type { WorldSetting } from '@/types';
import { formatDate } from '@/utils/format';

interface WorldCardProps {
  world: WorldSetting;
  onClick: () => void;
}

const WorldCard = ({ world, onClick }: WorldCardProps) => {
  return (
    <Card
      hoverable
      onClick={onClick}
      style={{ borderRadius: 10 }}
      styles={{ body: { padding: 14 } }}
    >
      <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>{world.name}</div>
      <div style={{ fontSize: 11, color: '#666', lineHeight: 1.6, height: 36, overflow: 'hidden', marginBottom: 10 }}>
        {world.summary || '暂无摘要'}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Tag color="purple">世界观</Tag>
        <span style={{ fontSize: 10, color: '#999' }}>{formatDate(world.updated_at)}</span>
      </div>
    </Card>
  );
};

export default WorldCard;
```

- [ ] **Step 2: 实现 WorldList 页面**

```tsx
// src/pages/world/WorldList.tsx
import { useState, useEffect } from 'react';
import { Row, Col, Button, Modal, Form, Input, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
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
              <WorldCard
                world={world}
                onClick={() => navigate(`/projects/${projectId}/world/${world.id}`)}
              />
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

- [ ] **Step 3: 实现 WorldEdit 页面**

```tsx
// src/pages/world/WorldEdit.tsx
import { useState, useEffect } from 'react';
import { Button, Input, message, Space } from 'antd';
import { useParams, useNavigate } from 'react-router-dom';
import { worldApi } from '@/api/world';
import PageHeader from '@/components/common/PageHeader';
import MarkdownEditor from '@/components/common/MarkdownEditor';
import type { WorldSetting } from '@/types';

const WorldEdit = () => {
  const { id: projectId, worldId } = useParams<{ id: string; worldId: string }>();
  const navigate = useNavigate();
  const [world, setWorld] = useState<WorldSetting | null>(null);
  const [name, setName] = useState('');
  const [summary, setSummary] = useState('');
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!projectId || !worldId) return;
    worldApi.get(projectId, worldId).then(res => {
      setWorld(res.data);
      setName(res.data.name);
      setSummary(res.data.summary || '');
      setContent(res.data.content || '');
      setLoading(false);
    }).catch(() => {
      message.error('加载失败');
      navigate(`/projects/${projectId}/world`);
    });
  }, [projectId, worldId]);

  const handleSave = async () => {
    if (!projectId || !worldId) return;
    setSaving(true);
    try {
      await worldApi.update(projectId, worldId, { name, summary, content });
      message.success('保存成功');
    } catch {
      message.error('保存失败');
    }
    setSaving(false);
  };

  if (loading || !world) return null;

  return (
    <div>
      <PageHeader
        title={world.name}
        breadcrumbs={[
          { title: '世界观', path: `/projects/${projectId}/world` },
          { title: world.name },
        ]}
        extra={
          <Space>
            <Button onClick={() => navigate(`/projects/${projectId}/world`)}>返回</Button>
            <Button type="primary" loading={saving} onClick={handleSave}>保存</Button>
          </Space>
        }
      />

      <div style={{ marginBottom: 16 }}>
        <Input
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="设定名称"
          style={{ fontSize: 18, fontWeight: 600, border: 'none', padding: 0, marginBottom: 8 }}
        />
        <Input
          value={summary}
          onChange={e => setSummary(e.target.value)}
          placeholder="添加摘要..."
          style={{ border: 'none', padding: 0, color: '#999' }}
        />
      </div>

      <MarkdownEditor value={content} onChange={setContent} height={500} />
    </div>
  );
};

export default WorldEdit;
```

- [ ] **Step 4: 更新 App.tsx 路由**

```tsx
// 在 App.tsx 的 AppLayout Route 中添加：
import WorldList from '@/pages/world/WorldList';
import WorldEdit from '@/pages/world/WorldEdit';

// Route 配置：
<Route path="/projects/:id/world" element={<WorldList />} />
<Route path="/projects/:id/world/:worldId" element={<WorldEdit />} />
```

- [ ] **Step 5: 类型检查**

Run: `cd frontend && npm run type-check`
Expected: 无错误

- [ ] **Step 6: Commit**

```bash
git add frontend/src/
git commit -m "feat(frontend): implement world settings management"
```

---

## Task 9: 角色管理

**Files:**
- Create: `frontend/src/components/cards/CharacterCard.tsx`
- Create: `frontend/src/pages/characters/CharacterList.tsx`
- Create: `frontend/src/pages/characters/CharacterEdit.tsx`

- [ ] **Step 1: 创建 CharacterCard**

```tsx
// src/components/cards/CharacterCard.tsx
import { Card, Tag, Avatar } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import type { Character } from '@/types';
import { formatDate } from '@/utils/format';
import { parseCharacterMeta } from '@/utils/frontmatter';

const GRADIENTS = [
  'linear-gradient(135deg, #667eea, #764ba2)',
  'linear-gradient(135deg, #f093fb, #f5576c)',
  'linear-gradient(135deg, #4facfe, #00f2fe)',
  'linear-gradient(135deg, #43e97b, #38f9d7)',
];

interface CharacterCardProps {
  character: Character;
  onClick: () => void;
}

const CharacterCard = ({ character, onClick }: CharacterCardProps) => {
  const gradient = GRADIENTS[character.name.length % GRADIENTS.length];
  const meta = character.content ? parseCharacterMeta(character.content) : null;

  return (
    <Card
      hoverable
      onClick={onClick}
      style={{ borderRadius: 12, overflow: 'hidden' }}
      styles={{ body: { padding: 0 } }}
    >
      <div style={{
        height: 120,
        background: gradient,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
      }}>
        <Avatar size={64} icon={<UserOutlined />} style={{
          backgroundColor: 'rgba(255,255,255,0.2)',
          border: '3px solid rgba(255,255,255,0.5)',
        }} />
        {meta?.type && (
          <Tag style={{ position: 'absolute', top: 10, right: 10, margin: 0 }}>{meta.type}</Tag>
        )}
      </div>
      <div style={{ padding: 14 }}>
        <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>{character.name}</div>
        <div style={{ fontSize: 11, color: '#666', lineHeight: 1.6, height: 36, overflow: 'hidden', marginBottom: 10 }}>
          {character.summary || '暂无简介'}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: 4 }}>
            {meta?.tags?.slice(0, 2).map(tag => (
              <Tag key={tag} color="blue">{tag}</Tag>
            ))}
          </div>
          <span style={{ fontSize: 10, color: '#999' }}>{formatDate(character.updated_at)}</span>
        </div>
      </div>
    </Card>
  );
};

export default CharacterCard;
```

- [ ] **Step 2: 实现 CharacterList 页面**

```tsx
// src/pages/characters/CharacterList.tsx
import { useState, useEffect } from 'react';
import { Row, Col, Button, Modal, Form, Input, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { charactersApi } from '@/api/characters';
import CharacterCard from '@/components/cards/CharacterCard';
import PageHeader from '@/components/common/PageHeader';
import EmptyState from '@/components/common/EmptyState';
import type { Character } from '@/types';

const CharacterList = () => {
  const { id: projectId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [form] = Form.useForm();

  const loadCharacters = async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const res = await charactersApi.list(projectId);
      setCharacters(res.data);
    } catch {
      message.error('加载角色列表失败');
    }
    setLoading(false);
  };

  useEffect(() => {
    loadCharacters();
  }, [projectId]);

  const handleCreate = async () => {
    if (!projectId) return;
    try {
      const values = await form.validateFields();
      const res = await charactersApi.create(projectId, values);
      setCharacters(prev => [...prev, res.data]);
      setCreateModalOpen(false);
      form.resetFields();
      message.success('角色创建成功');
    } catch {
      // validation error
    }
  };

  return (
    <div>
      <PageHeader
        title="角色档案"
        subtitle="管理你的故事角色"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
            新建角色
          </Button>
        }
      />

      {characters.length === 0 && !loading ? (
        <EmptyState
          description="暂无角色"
          actionText="新建角色"
          onAction={() => setCreateModalOpen(true)}
        />
      ) : (
        <Row gutter={[16, 16]}>
          {characters.map(character => (
            <Col key={character.id} xs={24} sm={12} md={8} lg={6}>
              <CharacterCard
                character={character}
                onClick={() => navigate(`/projects/${projectId}/characters/${character.id}`)}
              />
            </Col>
          ))}
        </Row>
      )}

      <Modal
        title="新建角色"
        open={createModalOpen}
        onOk={handleCreate}
        onCancel={() => setCreateModalOpen(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="角色名称" rules={[{ required: true, message: '请输入角色名称' }]}>
            <Input placeholder="输入角色名称" />
          </Form.Item>
          <Form.Item name="summary" label="简介">
            <Input placeholder="简短描述（可选）" />
          </Form.Item>
          <Form.Item name="content" label="详细档案" rules={[{ required: true, message: '请输入内容' }]}>
            <Input.TextArea rows={6} placeholder="使用 Markdown 格式编写..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default CharacterList;
```

- [ ] **Step 3: 实现 CharacterEdit 页面**

```tsx
// src/pages/characters/CharacterEdit.tsx
import { useState, useEffect } from 'react';
import { Button, Input, Tag, message, Space } from 'antd';
import { useParams, useNavigate } from 'react-router-dom';
import { charactersApi } from '@/api/characters';
import PageHeader from '@/components/common/PageHeader';
import MarkdownEditor from '@/components/common/MarkdownEditor';
import { parseCharacterMeta, serializeWithFrontmatter } from '@/utils/frontmatter';
import type { Character } from '@/types';

const CharacterEdit = () => {
  const { id: projectId, charId } = useParams<{ id: string; charId: string }>();
  const navigate = useNavigate();
  const [character, setCharacter] = useState<Character | null>(null);
  const [name, setName] = useState('');
  const [summary, setSummary] = useState('');
  const [content, setContent] = useState('');
  const [tags, setTags] = useState<string[]>([]);
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
      const fullContent = serializeWithFrontmatter({ tags }, content);
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

  if (loading || !character) return null;

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

- [ ] **Step 4: 更新 App.tsx 路由**

```tsx
import CharacterList from '@/pages/characters/CharacterList';
import CharacterEdit from '@/pages/characters/CharacterEdit';

// Route 配置：
<Route path="/projects/:id/characters" element={<CharacterList />} />
<Route path="/projects/:id/characters/:charId" element={<CharacterEdit />} />
```

- [ ] **Step 5: 类型检查 + Commit**

```bash
cd frontend && npm run type-check
git add frontend/src/
git commit -m "feat(frontend): implement character management with tags"
```

---

## Task 10: 大纲编辑器

**Files:**
- Create: `frontend/src/pages/outline/OutlineEditor.tsx`

- [ ] **Step 1: 实现 OutlineEditor**

```tsx
// src/pages/outline/OutlineEditor.tsx
import { useState, useEffect } from 'react';
import { Tree, Button, Modal, Form, Input, Select, message, Space, Dropdown } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, MoreOutlined } from '@ant-design/icons';
import { useParams } from 'react-router-dom';
import { outlinesApi } from '@/api/outlines';
import PageHeader from '@/components/common/PageHeader';
import MarkdownEditor from '@/components/common/MarkdownEditor';
import EmptyState from '@/components/common/EmptyState';
import type { Outline, TreeNodeData } from '@/types';

const OutlineEditor = () => {
  const { id: projectId } = useParams<{ id: string }>();
  const [treeData, setTreeData] = useState<TreeNodeData[]>([]);
  const [rootOutline, setRootOutline] = useState<Outline | null>(null);
  const [loading, setLoading] = useState(true);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingNode, setEditingNode] = useState<Outline | null>(null);
  const [parentId, setParentId] = useState<string | null>(null);
  const [form] = Form.useForm();

  const loadTree = async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const rootRes = await outlinesApi.getRoot(projectId);
      if (rootRes.data && rootRes.data.id) {
        setRootOutline(rootRes.data);
        const treeRes = await outlinesApi.getTree(projectId, rootRes.data.id);
        setTreeData(treeRes.data.children ? convertToTreeData(treeRes.data.children) : []);
      }
    } catch {
      message.error('加载大纲失败');
    }
    setLoading(false);
  };

  useEffect(() => {
    loadTree();
  }, [projectId]);

  const convertToTreeData = (outlines: Outline[]): TreeNodeData[] => {
    return outlines.map(o => ({
      key: o.id,
      title: o.title,
      type: o.type,
      content: o.content,
      children: o.children ? convertToTreeData(o.children) : [],
    }));
  };

  const handleCreate = async (pId: string | null) => {
    if (!projectId) return;
    setEditingNode(null);
    setParentId(pId);
    form.resetFields();
    setEditModalOpen(true);
  };

  const handleEdit = async (nodeKey: string) => {
    if (!projectId) return;
    try {
      const res = await outlinesApi.get(projectId, nodeKey);
      setEditingNode(res.data);
      setParentId(res.data.parent_id);
      form.setFieldsValue({
        title: res.data.title,
        content: res.data.content,
        type: res.data.type,
      });
      setEditModalOpen(true);
    } catch {
      message.error('加载节点失败');
    }
  };

  const handleDelete = async (nodeKey: string) => {
    if (!projectId) return;
    Modal.confirm({
      title: '确认删除',
      content: '删除后子节点也会被删除，确认吗？',
      onOk: async () => {
        try {
          await outlinesApi.delete(projectId, nodeKey);
          message.success('删除成功');
          loadTree();
        } catch {
          message.error('删除失败');
        }
      },
    });
  };

  const handleSave = async () => {
    if (!projectId) return;
    try {
      const values = await form.validateFields();
      if (editingNode) {
        await outlinesApi.update(projectId, editingNode.id, values);
        message.success('更新成功');
      } else {
        await outlinesApi.create(projectId, { ...values, parent_id: parentId || undefined });
        message.success('创建成功');
      }
      setEditModalOpen(false);
      loadTree();
    } catch {
      // validation error
    }
  };

  const titleRender = (nodeData: TreeNodeData) => (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
      <span>{nodeData.title}</span>
      <Dropdown
        menu={{
          items: [
            { key: 'edit', icon: <EditOutlined />, label: '编辑', onClick: () => handleEdit(nodeData.key) },
            { key: 'add', icon: <PlusOutlined />, label: '添加子节点', onClick: () => handleCreate(nodeData.key) },
            { key: 'delete', icon: <DeleteOutlined />, label: '删除', danger: true, onClick: () => handleDelete(nodeData.key) },
          ],
        }}
        trigger={['click']}
      >
        <Button type="text" size="small" icon={<MoreOutlined />} onClick={e => e.stopPropagation()} />
      </Dropdown>
    </div>
  );

  return (
    <div>
      <PageHeader
        title="故事大纲"
        subtitle="管理你的故事结构"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => handleCreate(null)}>
            新建节点
          </Button>
        }
      />

      {treeData.length === 0 && !loading ? (
        <EmptyState
          description="暂无大纲"
          actionText="新建根节点"
          onAction={() => handleCreate(null)}
        />
      ) : (
        <Tree
          showLine={{ showLeafIcon: false }}
          defaultExpandAll
          treeData={treeData}
          titleRender={titleRender}
        />
      )}

      <Modal
        title={editingNode ? '编辑节点' : '新建节点'}
        open={editModalOpen}
        onOk={handleSave}
        onCancel={() => setEditModalOpen(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="title" label="标题" rules={[{ required: true, message: '请输入标题' }]}>
            <Input placeholder="节点标题" />
          </Form.Item>
          <Form.Item name="type" label="类型">
            <Select placeholder="选择类型" allowClear>
              <Select.Option value="part">篇</Select.Option>
              <Select.Option value="volume">卷</Select.Option>
              <Select.Option value="chapter">章</Select.Option>
              <Select.Option value="section">节</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="content" label="内容">
            <Input.TextArea rows={4} placeholder="节点内容描述..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default OutlineEditor;
```

- [ ] **Step 2: 更新 App.tsx 路由 + 类型检查 + Commit**

```bash
# 更新 App.tsx 添加：
# import OutlineEditor from '@/pages/outline/OutlineEditor';
# <Route path="/projects/:id/outline" element={<OutlineEditor />} />

cd frontend && npm run type-check
git add frontend/src/
git commit -m "feat(frontend): implement outline tree editor"
```

---

## Task 11: 章节管理

**Files:**
- Create: `frontend/src/pages/chapters/ChapterList.tsx`
- Create: `frontend/src/pages/chapters/ChapterEdit.tsx`

- [ ] **Step 1: 实现 ChapterList**

```tsx
// src/pages/chapters/ChapterList.tsx
import { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, InputNumber, message, Tag, Space } from 'antd';
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
      const res = await chaptersApi.create(projectId, {
        ...values,
        chapter_number: chapters.length + 1,
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
          setChapters(prev => prev.filter(c => c.id !== chapterId));
          message.success('删除成功');
        } catch {
          message.error('删除失败');
        }
      },
    });
  };

  const columns = [
    {
      title: '#',
      dataIndex: 'chapter_number',
      width: 60,
    },
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

- [ ] **Step 2: 实现 ChapterEdit**

```tsx
// src/pages/chapters/ChapterEdit.tsx
import { useState, useEffect } from 'react';
import { Button, Input, Tag, message, Space, Tooltip } from 'antd';
import { FullscreenOutlined, FullscreenExitOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { chaptersApi } from '@/api/chapters';
import PageHeader from '@/components/common/PageHeader';
import MarkdownEditor from '@/components/common/MarkdownEditor';
import { countWords } from '@/utils/format';
import type { Chapter } from '@/types';

const ChapterEdit = () => {
  const { id: projectId, chapterId } = useParams<{ id: string; chapterId: string }>();
  const navigate = useNavigate();
  const [chapter, setChapter] = useState<Chapter | null>(null);
  const [title, setTitle] = useState('');
  const [summary, setSummary] = useState('');
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);

  useEffect(() => {
    if (!projectId || !chapterId) return;
    chaptersApi.get(projectId, chapterId).then(res => {
      setChapter(res.data);
      setTitle(res.data.title);
      setSummary(res.data.summary || '');
      setContent(res.data.content || '');
      setLoading(false);
    }).catch(() => {
      message.error('加载失败');
      navigate(`/projects/${projectId}/chapters`);
    });
  }, [projectId, chapterId]);

  const handleSave = async () => {
    if (!projectId || !chapterId) return;
    setSaving(true);
    try {
      await chaptersApi.update(projectId, chapterId, {
        title,
        summary,
        content,
        word_count: countWords(content),
      });
      message.success('保存成功');
    } catch {
      message.error('保存失败');
    }
    setSaving(false);
  };

  if (loading || !chapter) return null;

  const wordCount = countWords(content);

  return (
    <div>
      <PageHeader
        title={chapter.title}
        breadcrumbs={[
          { title: '章节', path: `/projects/${projectId}/chapters` },
          { title: chapter.title },
        ]}
        extra={
          <Space>
            <Tooltip title={fullscreen ? '退出全屏' : '全屏写作'}>
              <Button icon={fullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />} onClick={() => setFullscreen(!fullscreen)} />
            </Tooltip>
            <Button onClick={() => navigate(`/projects/${projectId}/chapters`)}>返回</Button>
            <Button type="primary" loading={saving} onClick={handleSave}>保存</Button>
          </Space>
        }
      />

      <div style={{ marginBottom: 16, display: 'flex', gap: 16, alignItems: 'center' }}>
        <Input
          value={title}
          onChange={e => setTitle(e.target.value)}
          placeholder="章节标题"
          style={{ fontSize: 18, fontWeight: 600, border: 'none', padding: 0, flex: 1 }}
        />
        <Tag color="blue">{wordCount.toLocaleString()} 字</Tag>
      </div>

      <Input
        value={summary}
        onChange={e => setSummary(e.target.value)}
        placeholder="添加摘要..."
        style={{ border: 'none', padding: 0, color: '#999', marginBottom: 16 }}
      />

      <MarkdownEditor
        value={content}
        onChange={setContent}
        height={fullscreen ? window.innerHeight - 200 : 500}
      />
    </div>
  );
};

export default ChapterEdit;
```

- [ ] **Step 3: 更新路由 + 类型检查 + Commit**

```bash
cd frontend && npm run type-check
git add frontend/src/
git commit -m "feat(frontend): implement chapter management and editor"
```

---

## Task 12: 评审报告 + 项目设置

**Files:**
- Create: `frontend/src/pages/reviews/ReviewList.tsx`
- Create: `frontend/src/pages/settings/ProjectSettings.tsx`

- [ ] **Step 1: 实现 ReviewList**

```tsx
// src/pages/reviews/ReviewList.tsx
import { useState, useEffect } from 'react';
import { Card, Row, Col, Tag, Progress, message, Collapse } from 'antd';
import { useParams } from 'react-router-dom';
import { reviewsApi } from '@/api/reviews';
import PageHeader from '@/components/common/PageHeader';
import EmptyState from '@/components/common/EmptyState';
import { formatDate } from '@/utils/format';
import type { Review } from '@/types';

const ReviewList = () => {
  const { id: projectId } = useParams<{ id: string }>();
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!projectId) return;
    reviewsApi.list(projectId).then(res => {
      setReviews(res.data);
      setLoading(false);
    }).catch(() => {
      message.error('加载评审列表失败');
      setLoading(false);
    });
  }, [projectId]);

  return (
    <div>
      <PageHeader title="评审报告" subtitle="查看内容质量评审" />

      {reviews.length === 0 && !loading ? (
        <EmptyState description="暂无评审报告" />
      ) : (
        <Row gutter={[16, 16]}>
          {reviews.map(review => (
            <Col key={review.id} xs={24} sm={12} md={8}>
              <Card style={{ borderRadius: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <Tag color={review.content_type === 'chapter' ? 'blue' : 'purple'}>
                    {review.content_type === 'chapter' ? '章节' : review.content_type}
                  </Tag>
                  <span style={{ fontSize: 10, color: '#999' }}>{formatDate(review.created_at)}</span>
                </div>

                {review.overall_score != null && (
                  <div style={{ textAlign: 'center', marginBottom: 12 }}>
                    <Progress
                      type="circle"
                      percent={Math.round(review.overall_score * 100)}
                      size={80}
                      format={p => `${p}%`}
                    />
                  </div>
                )}

                <Collapse
                  size="small"
                  items={[
                    ...(review.issues?.length ? [{
                      key: 'issues',
                      label: `问题 (${review.issues.length})`,
                      children: (
                        <ul style={{ margin: 0, paddingLeft: 16 }}>
                          {review.issues.map((issue, i) => <li key={i}>{issue}</li>)}
                        </ul>
                      ),
                    }] : []),
                    ...(review.suggestions?.length ? [{
                      key: 'suggestions',
                      label: `建议 (${review.suggestions.length})`,
                      children: (
                        <ul style={{ margin: 0, paddingLeft: 16 }}>
                          {review.suggestions.map((s, i) => <li key={i}>{s}</li>)}
                        </ul>
                      ),
                    }] : []),
                  ]}
                />
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </div>
  );
};

export default ReviewList;
```

- [ ] **Step 2: 实现 ProjectSettings**

```tsx
// src/pages/settings/ProjectSettings.tsx
import { useState, useEffect } from 'react';
import { Form, Input, Button, message, Modal, Space } from 'antd';
import { useParams, useNavigate } from 'react-router-dom';
import { projectsApi } from '@/api/projects';
import { useProjectContext } from '@/contexts/ProjectContext';
import PageHeader from '@/components/common/PageHeader';
import type { Project } from '@/types';

const ProjectSettings = () => {
  const { id: projectId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { setCurrentProject } = useProjectContext();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    if (!projectId) return;
    projectsApi.get(projectId).then(res => {
      setProject(res.data);
      form.setFieldsValue({
        name: res.data.name,
        description: res.data.description,
      });
      setLoading(false);
    }).catch(() => {
      message.error('加载项目失败');
      navigate('/');
    });
  }, [projectId]);

  const handleSave = async () => {
    if (!projectId) return;
    setSaving(true);
    try {
      const values = await form.validateFields();
      const res = await projectsApi.update(projectId, values);
      setProject(res.data);
      setCurrentProject(res.data);
      message.success('保存成功');
    } catch {
      // validation error
    }
    setSaving(false);
  };

  const handleDelete = () => {
    if (!projectId) return;
    Modal.confirm({
      title: '确认删除项目',
      content: '删除后无法恢复，所有内容都将被删除。确认吗？',
      okText: '确认删除',
      okType: 'danger',
      onOk: async () => {
        try {
          await projectsApi.delete(projectId);
          setCurrentProject(null);
          message.success('项目已删除');
          navigate('/');
        } catch {
          message.error('删除失败');
        }
      },
    });
  };

  if (loading || !project) return null;

  return (
    <div>
      <PageHeader
        title="项目设置"
        subtitle={project.name}
      />

      <Form form={form} layout="vertical" style={{ maxWidth: 600 }}>
        <Form.Item name="name" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }]}>
          <Input />
        </Form.Item>
        <Form.Item name="description" label="项目描述">
          <Input.TextArea rows={4} />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" loading={saving} onClick={handleSave}>保存</Button>
            <Button onClick={() => navigate('/')}>返回</Button>
          </Space>
        </Form.Item>
      </Form>

      <div style={{ marginTop: 48, padding: 24, border: '1px solid #ffccc7', borderRadius: 8 }}>
        <h3 style={{ color: '#cf1322', marginBottom: 8 }}>危险操作</h3>
        <p style={{ color: '#666', marginBottom: 16 }}>删除项目后，所有世界观、角色、大纲、章节内容都将被永久删除。</p>
        <Button danger onClick={handleDelete}>删除项目</Button>
      </div>
    </div>
  );
};

export default ProjectSettings;
```

- [ ] **Step 3: 更新路由 + 类型检查 + Commit**

```bash
cd frontend && npm run type-check
git add frontend/src/
git commit -m "feat(frontend): implement reviews and project settings"
```

---

## Task 13: ProjectContext 自动加载 + 路由守卫

**Files:**
- Modify: `frontend/src/contexts/ProjectContext.tsx`
- Modify: `frontend/src/components/layout/SecondaryNav.tsx`

- [ ] **Step 1: 更新 ProjectContext 支持自动加载项目**

```tsx
// src/contexts/ProjectContext.tsx
import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import { useParams } from 'react-router-dom';
import { projectsApi } from '@/api/projects';
import type { Project } from '@/types';

interface ProjectContextType {
  currentProject: Project | null;
  setCurrentProject: (project: Project | null) => void;
  loading: boolean;
}

const ProjectContext = createContext<ProjectContextType>({
  currentProject: null,
  setCurrentProject: () => {},
  loading: false,
});

export const useProjectContext = () => useContext(ProjectContext);

export const ProjectProvider = ({ children }: { children: ReactNode }) => {
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(false);

  return (
    <ProjectContext.Provider value={{ currentProject, setCurrentProject, loading }}>
      {children}
    </ProjectContext.Provider>
  );
};

// 项目路由的子组件，自动加载项目
export const ProjectLoader = ({ children }: { children: ReactNode }) => {
  const { id } = useParams<{ id: string }>();
  const { currentProject, setCurrentProject } = useProjectContext();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!id) return;
    if (currentProject?.id === id) return;

    setLoading(true);
    projectsApi.get(id).then(res => {
      setCurrentProject(res.data);
      setLoading(false);
    }).catch(() => {
      setCurrentProject(null);
      setLoading(false);
    });
  }, [id, currentProject?.id]);

  if (loading) return <div style={{ padding: 24, textAlign: 'center' }}>加载中...</div>;

  return <>{children}</>;
};
```

- [ ] **Step 2: 更新 AppLayout 包裹 ProjectLoader**

```tsx
// src/components/layout/AppLayout.tsx
import { Layout, theme } from 'antd';
import { Outlet } from 'react-router-dom';
import IconSidebar from './IconSidebar';
import SecondaryNav from './SecondaryNav';
import { ProjectLoader } from '@/contexts/ProjectContext';
import AIFab from '@/components/ai/AIFab';

const { Content } = Layout;

const AppLayout = () => {
  const { token: { colorBgContainer, borderRadiusLG } } = theme.useToken();

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
          <div style={{ maxWidth: 1200, margin: '0 auto' }}>
            <ProjectLoader>
              <Outlet />
            </ProjectLoader>
          </div>
        </Content>
      </Layout>
      <AIFab />
    </Layout>
  );
};

export default AppLayout;
```

- [ ] **Step 3: 类型检查 + Commit**

```bash
cd frontend && npm run type-check
git add frontend/src/
git commit -m "feat(frontend): add project auto-loading for project routes"
```

---

## Task 14: AI 悬浮球 + 聊天面板

**Files:**
- Modify: `frontend/src/components/ai/AIFab.tsx`
- Create: `frontend/src/components/ai/ChatPanel.tsx`
- Create: `frontend/src/components/ai/MessageBubble.tsx`
- Create: `frontend/src/components/ai/ThinkingBlock.tsx`
- Create: `frontend/src/hooks/useSSE.ts`

- [ ] **Step 1: 创建 useSSE hook**

```ts
// src/hooks/useSSE.ts
import { useState, useCallback, useRef } from 'react';

interface SSEMessage {
  type: 'user' | 'agent' | 'system';
  content: string;
  agent?: string;
  thinking?: string;
  streaming?: boolean;
  timeline?: TimelineEvent[];
}

interface TimelineEvent {
  type: 'text' | 'thinking' | 'tool' | 'system' | 'error';
  content?: string;
  name?: string;
  status?: 'running' | 'completed';
  result?: unknown;
  isDelegate?: boolean;
  subTimeline?: TimelineEvent[];
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
  ) => {
    setIsLoading(true);

    // Add user message
    setMessages(prev => [...prev, { type: 'user', content: message }]);

    // Create agent message placeholder
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
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let currentEventType = '';

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

      // Finalize
      setMessages(prev => {
        const last = prev[prev.length - 1];
        if (last?.type === 'agent') {
          return [...prev.slice(0, -1), { ...last, streaming: false }];
        }
        return prev;
      });
    } catch (e) {
      setMessages(prev => [...prev, { type: 'system', content: `Error: ${(e as Error).message}` }]);
    }

    setIsLoading(false);
  }, []);

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
                timeline[i] = { ...timeline[i], status: 'completed', result: data.result };
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

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return { messages, isLoading, sendMessage, clearMessages };
};
```

- [ ] **Step 2: 创建 ThinkingBlock**

```tsx
// src/components/ai/ThinkingBlock.tsx
import { useState } from 'react';
import { Collapse } from 'antd';

interface ThinkingBlockProps {
  content: string;
}

const ThinkingBlock = ({ content }: ThinkingBlockProps) => {
  return (
    <Collapse
      size="small"
      items={[{
        key: '1',
        label: <span style={{ color: '#7c3aed', fontSize: 11 }}>Thinking...</span>,
        children: (
          <pre style={{
            margin: 0,
            fontSize: 11,
            color: '#666',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            maxHeight: 200,
            overflow: 'auto',
          }}>
            {content}
          </pre>
        ),
      }]}
      style={{ marginBottom: 8 }}
    />
  );
};

export default ThinkingBlock;
```

- [ ] **Step 3: 创建 MessageBubble**

```tsx
// src/components/ai/MessageBubble.tsx
import { Avatar, Tag } from 'antd';
import { UserOutlined, RobotOutlined } from '@ant-design/icons';
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
}

const MessageBubble = ({ type, content, agent, timeline }: MessageBubbleProps) => {
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

  // Agent message
  return (
    <div style={{ display: 'flex', gap: 10, marginBottom: 12, alignItems: 'flex-start' }}>
      <Avatar icon={<RobotOutlined />} size={32} style={{ backgroundColor: '#6366f1', flexShrink: 0 }} />
      <div style={{ flex: 1 }}>
        {agent && (
          <Tag color="blue" style={{ marginBottom: 6 }}>{agent}</Tag>
        )}
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
        {content && (
          <div style={{
            padding: '10px 14px',
            background: '#f5f5f5',
            borderRadius: '4px 14px 14px 14px',
            fontSize: 13,
            lineHeight: 1.7,
            whiteSpace: 'pre-wrap',
          }}>
            {content}
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;
```

- [ ] **Step 4: 创建 ChatPanel**

```tsx
// src/components/ai/ChatPanel.tsx
import { useState, useEffect, useRef } from 'react';
import { Input, Button, Select, message, Space } from 'antd';
import { SendOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { useProjectContext } from '@/contexts/ProjectContext';
import { sessionsApi } from '@/api/sessions';
import { useSSE } from '@/hooks/useSSE';
import MessageBubble from './MessageBubble';
import type { Session } from '@/types';

const ChatPanel = () => {
  const { currentProject } = useProjectContext();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<Session | null>(null);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages, isLoading, sendMessage, clearMessages } = useSSE();

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

  const handleDeleteSession = async (sessionId: string) => {
    if (!currentProject) return;
    try {
      await sessionsApi.delete(currentProject.id, sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        clearMessages();
      }
    } catch {
      message.error('删除会话失败');
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
      {/* Session selector */}
      <div style={{ padding: '10px 12px', borderBottom: '1px solid #f0f0f0', display: 'flex', gap: 8, alignItems: 'center' }}>
        <Select
          value={currentSession?.id}
          onChange={(val) => {
            const session = sessions.find(s => s.id === val);
            setCurrentSession(session || null);
            clearMessages();
          }}
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

      {/* Messages */}
      <div style={{ flex: 1, overflow: 'auto', padding: 12 }}>
        {messages.map((msg, i) => (
          <MessageBubble key={i} {...msg} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={{ padding: 12, borderTop: '1px solid #f0f0f0' }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <Input.TextArea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入消息... (Enter 发送)"
            autoSize={{ minRows: 1, maxRows: 4 }}
            disabled={!currentSession}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={isLoading}
            disabled={!currentSession || !input.trim()}
          />
        </div>
      </div>
    </div>
  );
};

export default ChatPanel;
```

- [ ] **Step 5: 更新 AIFab**

```tsx
// src/components/ai/AIFab.tsx
import { useState } from 'react';
import { FloatButton, Badge, Drawer } from 'antd';
import { MessageOutlined } from '@ant-design/icons';
import ChatPanel from './ChatPanel';
import { useProjectContext } from '@/contexts/ProjectContext';

const AIFab = () => {
  const [open, setOpen] = useState(false);
  const { currentProject } = useProjectContext();

  // Don't show on dashboard
  if (!currentProject) return null;

  return (
    <>
      <FloatButton.Group shape="circle" style={{ insetInlineEnd: 24, bottom: 24 }}>
        <Badge size="small">
          <FloatButton
            icon={<MessageOutlined />}
            type="primary"
            onClick={() => setOpen(true)}
            tooltip="AI 助手"
          />
        </Badge>
      </FloatButton.Group>

      <Drawer
        title="AI 助手"
        placement="right"
        width={400}
        open={open}
        onClose={() => setOpen(false)}
        styles={{ body: { padding: 0, display: 'flex', flexDirection: 'column' } }}
      >
        <ChatPanel />
      </Drawer>
    </>
  );
};

export default AIFab;
```

- [ ] **Step 6: 类型检查 + Commit**

```bash
cd frontend && npm run type-check
git add frontend/src/
git commit -m "feat(frontend): implement AI chat with floating button and SSE streaming"
```

---

## Task 15: 快捷键 + 全局样式

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/ai/AIFab.tsx`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: 添加全局样式**

```tsx
// src/main.tsx - 在顶部添加
import 'antd/dist/reset.css';
```

- [ ] **Step 2: 更新 AIFab 支持快捷键**

```tsx
// src/components/ai/AIFab.tsx - 添加 useEffect
import { useState, useEffect } from 'react';

// 在组件内部添加：
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    // Ctrl/Cmd + J toggle
    if ((e.ctrlKey || e.metaKey) && e.key === 'j') {
      e.preventDefault();
      setOpen(prev => !prev);
    }
    // Esc close
    if (e.key === 'Escape' && open) {
      setOpen(false);
    }
  };

  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, [open]);
```

- [ ] **Step 3: 类型检查 + Commit**

```bash
cd frontend && npm run type-check
git add frontend/src/
git commit -m "feat(frontend): add keyboard shortcuts and global styles"
```

---

## Task 16: 最终验证

- [ ] **Step 1: 完整类型检查**

Run: `cd frontend && npm run type-check`
Expected: 无错误

- [ ] **Step 2: 构建验证**

Run: `cd frontend && npm run build`
Expected: 构建成功

- [ ] **Step 3: 开发服务器验证**

Run: `cd frontend && npm run dev`
Expected: 服务器启动在 http://localhost:5173

- [ ] **Step 4: 最终 Commit**

```bash
git add frontend/
git commit -m "feat(frontend): complete frontend platform implementation"
```

---

## Self-Review Checklist

- [x] **Spec coverage:** 所有 spec 中的页面和功能都有对应 task
- [x] **Placeholder scan:** 无 TBD/TODO 占位符
- [x] **Type consistency:** 类型名称在所有 task 中一致
- [x] **API consistency:** API 路径与后端 OpenAPI spec 一致
- [x] **Skills excluded:** 已排除 Skills API
