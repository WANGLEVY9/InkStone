# Outline Editor Redesign

## Problem

1. **Root outline content is invisible**: `OutlineEditor.loadTree()` fetches the root node, then fetches its tree, but only renders `treeRes.data.children` — the root node's title and content are never displayed. The "全书大纲" (full book outline) at the root level cannot be seen or edited.

2. **Layout inconsistent with other edit pages**: WorldEdit, CharacterEdit, and ChapterEdit all use a compact pattern: `Breadcrumb + editable Input title + Back/Save buttons + MarkdownEditor`. OutlineEditor uses a completely different pattern: `PageHeader (static title) + Tree component + Modal for editing`.

## Design

### Layout: Left Tree + Right Editor (Split Panel)

```
┌─────────────────────────────────────────────────────────┐
│ Breadcrumb: 大纲 > [选中的节点标题]                       │
├──────────────┬──────────────────────────────────────────┤
│  大纲树      │  [未选中时: EmptyState]                   │
│  ──────────  │                                          │
│  📖 全书大纲  │  [选中节点后:]                            │
│  ├ 📕 卷一    │  节点标题 (可编辑 Input)     [返回] [保存] │
│  │ ├ 第1章   │  类型: 卷                                 │
│  │ └ 第2章   │                                          │
│  └ 📕 卷二    │  ┌──────────────────────────────────┐   │
│    ├ 第3章   │  │  MarkdownEditor                  │   │
│    └ 第4章   │  │                                  │   │
│              │  └──────────────────────────────────┘   │
│  [+ 新建子节点]                                          │
└──────────────┴──────────────────────────────────────────┘
```

- **Left tree panel**: Fixed width ~260px, shows full tree including root node. Each node displays a type icon for visual distinction.
- **Right editor panel**: Flex-fill. Displays editing UI for the selected tree node.
- **Default state**: No node selected. Right panel shows EmptyState.
- **Breadcrumb**: Shows "大纲" as the list-level crumb, and the selected node's title as the current crumb. When no node is selected, only "大纲" is shown.

### Left Panel: Tree

- Uses Ant Design `Tree` with `showLine` and `titleRender` (same as current).
- **Root node is visible** as the first item in the tree — solves problem #1.
- Type icons: `BookOutlined` for root, `FolderOutlined` for volume, `FileTextOutlined` for chapter (or similar differentiating icons).
- **Node click**: Selects the node, loads its content into the right panel.
- **Context actions** (via Dropdown on each node, same pattern as current):
  - "新建子节点" — opens a small Modal to input title + select type (volume/chapter), creates the child, auto-selects it.
  - "删除" — confirmation Modal, cascading delete (existing behavior).
- **"新建子节点" button** at the bottom of the tree panel — creates a child under the currently selected node (or root if none selected).
- Selected node is highlighted via Tree's `selectedKeys`.

### Right Panel: Editor

When a node is selected, the right panel mirrors the WorldEdit/CharacterEdit/ChapterEdit pattern:

1. **Title row**: Editable `<Input>` with `border: 'none'`, `fontSize: 18`, `fontWeight: 600`. Inline with "返回" and "保存" buttons.
2. **Metadata row**: Type `<Tag>` (e.g., "总纲", "卷", "章").
3. **Body**: `<MarkdownEditor>` for editing the node's content.

Note: Unlike WorldEdit/CharacterEdit/ChapterEdit, there is no summary row because the `Outline` data model has no `summary` field.

When no node is selected: `<EmptyState description="选择一个节点开始编辑" />`.

**"返回" button behavior**: Deselects the current node, returns to EmptyState. Does NOT navigate away from the page (unlike other edit pages where "返回" goes to the list page — outlines don't have a separate list page).

**"保存" button**: Calls `outlinesApi.update()` with the current title, content, and type. Shows loading state while saving. Matches the manual-save pattern of other edit pages.

### Data Flow

1. Page loads → fetch root via `outlinesApi.getRoot(projectId)` → fetch tree via `outlinesApi.getTree(projectId, rootId)` → store tree data + root node data.
2. User clicks a node → fetch full node via `outlinesApi.get(projectId, nodeId)` → populate right panel fields.
3. User edits and clicks "保存" → `outlinesApi.update(projectId, nodeId, { title, content })` → refresh tree (title may have changed).
4. User creates child node → `outlinesApi.create(projectId, { title, type, parent_id })` → refresh tree → auto-select new node.
5. User deletes node → confirmation → `outlinesApi.delete(projectId, nodeId)` → refresh tree → deselect if deleted node was selected.

### API Changes

None. The existing backend API is sufficient:
- `getRoot` — get root node
- `getTree` — get full tree structure
- `get` — get single node with content
- `create` / `update` / `delete` — CRUD operations

### Files to Modify

| File | Change |
|------|--------|
| `frontend/src/pages/outline/OutlineEditor.tsx` | Complete rewrite: split-panel layout, tree + editor |
| No new files needed | All changes are within the existing OutlineEditor component |

### Out of Scope

- Drag-and-drop reordering (Tree's `draggable` — complex interaction, defer to future iteration)
- Auto-save (inconsistent with other edit pages)
- Backend API changes (existing API is sufficient)
- Separate OutlineList page (the tree serves as both list and navigation)
