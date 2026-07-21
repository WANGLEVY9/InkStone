# antd 升级 + Drawer Resizable 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 升级 antd 5.x → 6.3.7，迁移所有 deprecated API，启用 AI 聊天 Drawer 的 resizable 功能

**Architecture:** 采用 antd 6 推荐的 `App.useApp()` 模式替换静态 `message.*()` / `Modal.confirm()` 调用。在 `App.tsx` 中用 `<App>` 组件包裹应用，各页面通过 hook 获取 message/modal 实例。Drawer 组件添加 `resizable` 属性。

**Tech Stack:** React 18, TypeScript, antd 6.3.7, @ant-design/icons, Vite

---

### Task 1: 升级 antd 和 @ant-design/icons 包

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: 升级依赖**

```bash
cd frontend && npm install antd@6.3.7 @ant-design/icons@latest
```

- [ ] **Step 2: 检查安装是否成功**

```bash
cd frontend && npm ls antd @ant-design/icons
```

Expected: antd@6.3.7, @ant-design/icons 最新版本

- [ ] **Step 3: 运行 type-check 看有哪些类型错误**

```bash
cd frontend && npm run type-check
```

Expected: 会有一批类型错误，记录下来供后续 task 修复

- [ ] **Step 4: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "chore(deps): upgrade antd to 6.3.7 and @ant-design/icons to latest"
```

---

### Task 2: 用 `<App>` 包裹应用根组件

antd 6 要求使用 `App.useApp()` 获取 message/modal/notification 实例。第一步是在根组件用 `<App>` 包裹。

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 修改 App.tsx，用 `<App>` 包裹 ConfigProvider 的 children**

当前 `App.tsx` 结构大致为：

```tsx
<ConfigProvider theme={...}>
  <RouterProvider router={router} />
</ConfigProvider>
```

改为：

```tsx
<ConfigProvider theme={...}>
  <App>
    <RouterProvider router={router} />
  </App>
</ConfigProvider>
```

需要从 antd 导入 `App` 组件。

- [ ] **Step 2: 运行 type-check 确认 App 包裹没有引入新错误**

```bash
cd frontend && npm run type-check
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: wrap app root with antd App component for useApp hook"
```

---

### Task 3: 创建 useMessage/useModal 自定义 hook

为了避免在每个页面都写 `const { message } = App.useApp()`，创建一个轻量 hook 统一导出。

**Files:**
- Create: `frontend/src/hooks/useAppMessage.ts`

- [ ] **Step 1: 创建 useAppMessage hook**

```typescript
import { App } from 'antd';

export function useAppMessage() {
  const { message, notification } = App.useApp();
  return { message, notification };
}

export function useAppModal() {
  const { modal } = App.useApp();
  return modal;
}
```

- [ ] **Step 2: 运行 type-check**

```bash
cd frontend && npm run type-check
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useAppMessage.ts
git commit -m "feat: add useAppMessage and useAppModal hooks"
```

---

### Task 4: 迁移页面中的静态 message.*() 调用

将所有 `import { message } from 'antd'` 的静态调用改为使用 `useAppMessage` hook。

**Files (11 个文件，按顺序处理):**

1. `frontend/src/pages/Dashboard.tsx`
2. `frontend/src/pages/world/WorldList.tsx`
3. `frontend/src/pages/world/WorldEdit.tsx`
4. `frontend/src/pages/characters/CharacterList.tsx`
5. `frontend/src/pages/characters/CharacterEdit.tsx`
6. `frontend/src/pages/outline/OutlineEditor.tsx`
7. `frontend/src/pages/chapters/ChapterList.tsx`
8. `frontend/src/pages/chapters/ChapterEdit.tsx`
9. `frontend/src/pages/settings/ProjectSettings.tsx`
10. `frontend/src/components/ai/ChatPanel.tsx`

- [ ] **Step 1: 迁移 Dashboard.tsx**

移除 import 中的 `message`，添加 `import { useAppMessage } from '../../hooks/useAppMessage'`。
在组件函数顶部添加 `const { message } = useAppMessage()`。
所有 `message.success()` / `message.error()` 调用保持不变（API 相同）。

- [ ] **Step 2: 迁移 WorldList.tsx**

同上模式。同时处理此文件中的 `Popconfirm`（无需改动，只是确认）。

- [ ] **Step 3: 迁移 WorldEdit.tsx**

同上模式。

- [ ] **Step 4: 迁移 CharacterList.tsx**

同上模式。

- [ ] **Step 5: 迁移 CharacterEdit.tsx**

同上模式。

- [ ] **Step 6: 迁移 OutlineEditor.tsx**

同上模式。此文件还有 `Modal.confirm` 和 `Select.Option`，在 Task 5 和 Task 6 中处理。

- [ ] **Step 7: 迁移 ChapterList.tsx**

同上模式。此文件还有 `Modal.confirm`，在 Task 5 中处理。

- [ ] **Step 8: 迁移 ChapterEdit.tsx**

同上模式。

- [ ] **Step 9: 迁移 ProjectSettings.tsx**

同上模式。此文件还有 `Modal.confirm`，在 Task 5 中处理。

- [ ] **Step 10: 迁移 ChatPanel.tsx**

同上模式。

- [ ] **Step 11: 运行 type-check**

```bash
cd frontend && npm run type-check
```

- [ ] **Step 12: Commit**

```bash
git add frontend/src/pages/ frontend/src/components/ai/ChatPanel.tsx
git commit -m "refactor: migrate static message.*() calls to App.useApp() hook"
```

---

### Task 5: 迁移静态 Modal.confirm() 调用

**Files:**
- `frontend/src/pages/outline/OutlineEditor.tsx`
- `frontend/src/pages/chapters/ChapterList.tsx`
- `frontend/src/pages/settings/ProjectSettings.tsx`

- [ ] **Step 1: 迁移 OutlineEditor.tsx 中的 Modal.confirm**

移除 import 中的 `Modal`（如果只用于 confirm），添加 `import { useAppModal } from '../../hooks/useAppMessage'`。
在组件函数顶部添加 `const modal = useAppModal()`。
将 `Modal.confirm({...})` 改为 `modal.confirm({...})`。

- [ ] **Step 2: 迁移 ChapterList.tsx 中的 Modal.confirm**

同上模式。

- [ ] **Step 3: 迁移 ProjectSettings.tsx 中的 Modal.confirm**

同上模式。

- [ ] **Step 4: 运行 type-check**

```bash
cd frontend && npm run type-check
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/outline/OutlineEditor.tsx frontend/src/pages/chapters/ChapterList.tsx frontend/src/pages/settings/ProjectSettings.tsx
git commit -m "refactor: migrate static Modal.confirm() calls to useAppModal hook"
```

---

### Task 6: 修复 Select.Option 和其他 breaking changes

**Files:**
- `frontend/src/pages/outline/OutlineEditor.tsx`

- [ ] **Step 1: 将 Select.Option 子元素模式改为 options prop**

当前代码（约 line 171-174）：

```tsx
<Select>
  <Select.Option value="...">...</Select.Option>
</Select>
```

改为：

```tsx
<Select options={[{ value: '...', label: '...' }]} />
```

- [ ] **Step 2: 检查 Tree titleRender 是否仍可用**

运行 type-check 看 `titleRender` 是否报错。如果 antd 6 改了 prop 名，按错误信息修复。

- [ ] **Step 3: 运行 type-check 处理所有剩余类型错误**

```bash
cd frontend && npm run type-check
```

逐一修复所有剩余错误。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/
git commit -m "fix: resolve remaining antd 6 breaking changes"
```

---

### Task 7: 启用 Drawer resizable

**Files:**
- Modify: `frontend/src/components/ai/AIFab.tsx`

- [ ] **Step 1: 在 Drawer 上添加 resizable 属性**

当前代码：

```tsx
<Drawer
  title="AI 助手"
  placement="right"
  width={400}
  open={open}
  onClose={() => setOpen(false)}
  styles={{ body: { padding: 0, display: 'flex', flexDirection: 'column' } }}
>
```

改为：

```tsx
<Drawer
  title="AI 助手"
  placement="right"
  width={400}
  resizable
  minSize={300}
  maxSize={800}
  open={open}
  onClose={() => setOpen(false)}
  styles={{ body: { padding: 0, display: 'flex', flexDirection: 'column' } }}
>
```

- [ ] **Step 2: 运行 type-check 确认 resizable 类型正确**

```bash
cd frontend && npm run type-check
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ai/AIFab.tsx
git commit -m "feat: enable Drawer resizable for AI chat panel"
```

---

### Task 8: 最终验证

- [ ] **Step 1: 运行完整 type-check**

```bash
cd frontend && npm run type-check
```

Expected: 0 errors

- [ ] **Step 2: 运行 lint**

```bash
cd frontend && npm run lint
```

Expected: 0 errors

- [ ] **Step 3: 运行 build**

```bash
cd frontend && npm run build
```

Expected: build succeeds

- [ ] **Step 4: 手动验证**

启动 dev server (`npm run dev`)，验证：
- AI 聊天 Drawer 可以正常打开/关闭
- Drawer 左侧边缘可以拖拽调整宽度
- 最小宽度 300px，最大宽度 800px
- Ctrl+J 快捷键仍然工作
- 各页面的 message 提示正常显示
- Modal.confirm 对话框正常工作

- [ ] **Step 5: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "fix: final adjustments after antd 6 migration verification"
```
