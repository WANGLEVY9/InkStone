# Vditor Markdown Editor Replacement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `@uiw/react-md-editor` with Vditor, providing IR/WYSIWYG modes and outline navigation while keeping the same `MarkdownEditor` component interface.

**Architecture:** A `useVditor` custom hook manages the imperative Vditor lifecycle (init, destroy, value sync, mode switching). The `MarkdownEditor` component delegates to this hook. The ref-based sync guard prevents `setValue → onChange → setValue` feedback loops.

**Tech Stack:** Vditor (TypeScript, MIT), React 18 hooks

---

## File Structure

| File | Responsibility |
|------|---------------|
| `frontend/src/hooks/useVditor.ts` | **New** — Vditor lifecycle hook (init, destroy, value sync, mode management) |
| `frontend/src/components/common/MarkdownEditor.tsx` | **Rewrite** — public component wrapping useVditor |
| `frontend/package.json` | Swap `@uiw/react-md-editor` → `vditor` |

No changes to WorldEdit.tsx, CharacterEdit.tsx, or ChapterEdit.tsx — the interface is unchanged.

---

### Task 1: Swap Dependencies

**Files:**
- Modify: `frontend/package.json:15`

- [ ] **Step 1: Remove old editor, install Vditor**

```bash
cd frontend && npm uninstall @uiw/react-md-editor && npm install vditor
```

- [ ] **Step 2: Verify installation**

```bash
cd frontend && node -e "const v = require('vditor/package.json'); console.log(v.version)"
```

Expected: prints a version number (e.g. `3.10.x`)

- [ ] **Step 3: Commit**

```bash
cd frontend && git add package.json package-lock.json
git commit -m "deps: replace @uiw/react-md-editor with vditor"
```

---

### Task 2: Create `useVditor` Hook

**Files:**
- Create: `frontend/src/hooks/useVditor.ts`

This hook manages the full Vditor lifecycle: init on mount, destroy on unmount, value sync with ref guard, debounced onChange, and mode switching via destroy+recreate.

- [ ] **Step 1: Create the hook file**

Create `frontend/src/hooks/useVditor.ts`:

```typescript
import { useEffect, useRef, useCallback, type RefObject } from 'react';
import Vditor from 'vditor';
import 'vditor/dist/index.css';

export type VditorMode = 'ir' | 'wysiwyg';

interface UseVditorOptions {
  containerRef: RefObject<HTMLDivElement | null>;
  value: string;
  onChange: (value: string) => void;
  height?: number;
  placeholder?: string;
  mode?: VditorMode;
}

export function useVditor({
  containerRef,
  value,
  onChange,
  height = 400,
  placeholder,
  mode = 'ir',
}: UseVditorOptions) {
  const vdRef = useRef<Vditor | null>(null);
  const internalChangeRef = useRef(false);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout>>();

  const destroyVditor = useCallback(() => {
    if (vdRef.current) {
      vdRef.current.destroy();
      vdRef.current = null;
    }
  }, []);

  const initVditor = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;

    destroyVditor();

    const vd = new Vditor(container, {
      mode: mode,
      icon: 'ant',
      outline: { enable: true, position: 'right' },
      cache: { enable: false },
      height,
      value,
      placeholder,
      toolbar: [
        'emoji', 'headings', 'bold', 'italic', 'strike', '|',
        'line', 'quote', 'list', 'ordered-list', 'check', '|',
        'code', 'inline-code', 'table', '|',
        'undo', 'redo', '|',
        'edit-mode', 'fullscreen', 'outline',
      ],
      toolbarConfig: { hide: false },
      input: (val) => {
        if (internalChangeRef.current) {
          internalChangeRef.current = false;
          return;
        }
        clearTimeout(debounceTimerRef.current);
        debounceTimerRef.current = setTimeout(() => {
          onChange(val);
        }, 200);
      },
      after: () => {
        vdRef.current = vd;
      },
    });
  }, [containerRef, mode, height, value, placeholder, onChange, destroyVditor]);

  // Init on mount, destroy on unmount
  useEffect(() => {
    initVditor();
    return () => {
      clearTimeout(debounceTimerRef.current);
      destroyVditor();
    };
  }, [initVditor, destroyVditor]);

  // Sync external value changes into Vditor
  useEffect(() => {
    const vd = vdRef.current;
    if (!vd) return;
    const currentValue = vd.getValue();
    if (currentValue !== value) {
      internalChangeRef.current = true;
      vd.setValue(value);
    }
  }, [value]);

}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit src/hooks/useVditor.ts
```

Expected: no errors (may warn about unused imports if not consumed yet, that's fine)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useVditor.ts
git commit -m "feat: add useVditor hook for Vditor lifecycle management"
```

---

### Task 3: Rewrite `MarkdownEditor` Component

**Files:**
- Modify: `frontend/src/components/common/MarkdownEditor.tsx`

- [ ] **Step 1: Rewrite MarkdownEditor.tsx**

Replace the entire contents of `frontend/src/components/common/MarkdownEditor.tsx`:

```typescript
import { useRef } from 'react';
import { useVditor, type VditorMode } from '@/hooks/useVditor';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  height?: number;
  placeholder?: string;
  mode?: VditorMode;
}

const MarkdownEditor = ({ value, onChange, height = 400, placeholder, mode }: MarkdownEditorProps) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useVditor({ containerRef, value, onChange, height, placeholder, mode });

  return <div ref={containerRef} className="vditor-wrapper" />;
};

export default MarkdownEditor;
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors

- [ ] **Step 3: Verify ESLint passes**

```bash
cd frontend && npx eslint src/components/common/MarkdownEditor.tsx src/hooks/useVditor.ts
```

Expected: no errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/common/MarkdownEditor.tsx
git commit -m "feat: rewrite MarkdownEditor to use Vditor via useVditor hook"
```

---

### Task 4: Manual Verification

Vditor is an imperative DOM library — browser verification is the appropriate test strategy.

- [ ] **Step 1: Start the dev server**

```bash
cd frontend && npm run dev
```

- [ ] **Step 2: Verify WorldEdit page**

Navigate to any project's world setting editor. Confirm:
- Editor renders with IR mode (text renders inline as you type)
- Toolbar is visible with Ant Design icons
- Outline sidebar is visible on the right
- Editing content and saving works
- No style leakage into antd components (buttons, inputs, menus look normal)

- [ ] **Step 3: Verify CharacterEdit page**

Navigate to any project's character editor. Confirm same as above.

- [ ] **Step 4: Verify ChapterEdit page**

Navigate to any project's chapter editor. Confirm:
- Editor renders correctly
- Fullscreen toggle button works — editor height changes dynamically
- Word count still displays correctly
- Content persists after save

- [ ] **Step 5: Verify mode switching**

In any editor page, click the `edit-mode` toolbar button. Confirm:
- Can switch between IR and WYSIWYG modes
- Content is preserved after mode switch
- Editor re-renders correctly in new mode

- [ ] **Step 6: Commit (if any fixes needed)**

If manual verification revealed issues that required fixes, commit them:

```bash
git add -A
git commit -m "fix: address Vditor integration issues from manual testing"
```
