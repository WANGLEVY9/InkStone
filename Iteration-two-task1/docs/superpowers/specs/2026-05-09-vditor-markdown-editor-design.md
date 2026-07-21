# Vditor Markdown Editor Replacement

## Summary

Replace `@uiw/react-md-editor` with Vditor in the frontend. Vditor provides a richer editing experience (IR mode, WYSIWYG, outline navigation, Ant Design icons) while maintaining the same external `MarkdownEditor` component interface.

## Motivation

- Current `@uiw/react-md-editor` only supports split-screen (SV) mode
- Vditor offers IR (instant rendering, Typora-like) and WYSIWYG modes, plus outline navigation
- Vditor has native Ant Design icon support (`icon: "ant"`) for visual consistency
- Better toolbar customization and built-in features (code highlighting, outline, etc.)

## Scope

Replace the markdown editor component used in 3 pages:
- `WorldEdit.tsx` — world setting editor
- `CharacterEdit.tsx` — character editor
- `ChapterEdit.tsx` — chapter editor (with fullscreen support)

Out of scope (deferred):
- Internal link autocomplete (`[[` linking to project entities)

## Design

### Component Interface

`MarkdownEditor` keeps the exact same public API. Callers do not change:

```typescript
interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  height?: number;
  placeholder?: string;
}
```

An optional `mode` prop is added for mode switching (`"ir"` | `"wysiwyg"`, default: `"ir"`). Existing callers don't pass it and get the default IR mode.

### Architecture

```
MarkdownEditor.tsx           # Public component, same interface
  └── useVditor.ts           # Custom hook: init, destroy, value sync, mode management
        └── Vditor instance  # Imperative API
```

**`useVditor` hook** (`frontend/src/hooks/useVditor.ts`):

- Input: `{ containerRef, value, onChange, height, mode }`
- Output: `{ vd, setMode }`
- Manages Vditor lifecycle (init on mount, destroy on unmount)
- Handles value synchronization using a ref to avoid `setValue → onChange → setValue` loops (same pattern as the SSE ref tracking in the project)
- On mode change: destroys and re-creates the Vditor instance (Vditor doesn't support hot mode switching)

### Vditor Configuration

```typescript
new Vditor(containerId, {
  mode: 'ir',
  icon: 'ant',                    // Ant Design icons
  outline: { enable: true, position: 'right' },
  cache: { enable: false },
  height: height,
  value: value,
  placeholder: placeholder,
  input: (val) => onChange(val),
  toolbar: [
    'emoji', 'headings', 'bold', 'italic', 'strike', '|',
    'line', 'quote', 'list', 'ordered-list', 'check', '|',
    'code', 'inline-code', 'table', '|',
    'undo', 'redo', '|',
    'edit-mode', 'fullscreen', 'outline', '|',
    'preview', 'devtools',
  ],
  toolbarConfig: { hide: false },
})
```

### Mode Switching

A mode toggle is exposed in the toolbar via Vditor's built-in `edit-mode` toolbar item. When the user switches mode, the hook destroys and re-creates the Vditor instance with the new mode.

### CSS

Import `vditor/dist/index.css` in `MarkdownEditor.tsx`. The Vditor container is scoped with a wrapper class to prevent style leakage into the rest of the app.

### Files Changed

| File | Action |
|------|--------|
| `frontend/src/hooks/useVditor.ts` | **New** — custom hook for Vditor lifecycle |
| `frontend/src/components/common/MarkdownEditor.tsx` | **Rewrite** — use Vditor via useVditor hook |
| `frontend/package.json` | Remove `@uiw/react-md-editor`, add `vditor` |
| `frontend/package-lock.json` | Updated by npm install |
| WorldEdit.tsx | No changes |
| CharacterEdit.tsx | No changes |
| ChapterEdit.tsx | No changes |

### Error Handling

- Vditor's `input` callback fires on every keystroke. We debounce the propagation to React `onChange` (200ms) to avoid excessive re-renders during rapid typing.
- The ref-based value sync guard (same pattern as `useSSE`) prevents the `setValue → onChange → setValue` feedback loop.

## Dependencies

- **Add**: `vditor` (latest, ~250KB, MIT license)
- **Remove**: `@uiw/react-md-editor` (~180KB)

## Testing

- Verify editor renders in all 3 pages (World, Character, Chapter)
- Verify `value` → editor content sync (controlled component)
- Verify editor changes propagate back via `onChange`
- Verify outline sidebar displays correctly
- Verify mode switching (IR ↔ WYSIWYG) preserves content
- Verify fullscreen mode in ChapterEdit still works
- Verify no style leakage from Vditor CSS into antd components
