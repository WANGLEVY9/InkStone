# Outline Editor Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite OutlineEditor.tsx from a flat Tree+Modal layout to a left-tree + right-editor split panel, aligned with WorldEdit/CharacterEdit/ChapterEdit patterns, making the root outline visible and editable.

**Architecture:** Single-file complete rewrite of `OutlineEditor.tsx`. Left panel (260px) shows the full outline tree including root node. Right panel (flex) shows an editor matching the compact edit-page pattern (editable title Input + type Tag + MarkdownEditor). Note: the `Outline` type has no `summary` field, so unlike WorldEdit/CharacterEdit/ChapterEdit, there is no summary row. No backend changes, no new files.

**Tech Stack:** React 18, TypeScript, Ant Design 5 (Tree, Button, Input, Tag, Breadcrumb, Modal, Form, Select, Dropdown, Spin), MarkdownEditor (Vditor wrapper), React Router v6

---

### Task 1: Rewrite OutlineEditor with split-panel layout

**Files:**
- Modify: `frontend/src/pages/outline/OutlineEditor.tsx` (complete rewrite)

- [ ] **Step 1: Write the complete new OutlineEditor component**

Replace the entire file with the following implementation. The component uses a `Layout`-style split panel: left tree (260px, fixed) + right editor (flex). The root node is included in the tree. Clicking a node loads its content into the right panel editor. The editor matches WorldEdit/CharacterEdit/ChapterEdit pattern.

```tsx
import { useState, useEffect, useCallback } from 'react';
import { Tree, Button, Modal, Form, Input, Select, Dropdown, Tag, Spin, Breadcrumb } from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  MoreOutlined,
  BookOutlined,
  FolderOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { useParams, Link } from 'react-router-dom';
import { useAppMessage, useAppModal } from '@/hooks/useAppMessage';
import { outlinesApi } from '@/api/outlines';
import MarkdownEditor from '@/components/common/MarkdownEditor';
import EmptyState from '@/components/common/EmptyState';
import type { Outline, TreeNodeData } from '@/types';

const TYPE_LABELS: Record<string, string> = {
  root: '总纲',
  volume: '卷',
  chapter: '章',
  part: '篇',
  section: '节',
};

const TYPE_ICONS: Record<string, React.ReactNode> = {
  root: <BookOutlined />,
  volume: <FolderOutlined />,
  chapter: <FileTextOutlined />,
  part: <FolderOutlined />,
  section: <FileTextOutlined />,
};

const OutlineEditor = () => {
  const { id: projectId } = useParams<{ id: string }>();
  const { message } = useAppMessage();
  const modal = useAppModal();

  // Tree state
  const [treeData, setTreeData] = useState<TreeNodeData[]>([]);
  const [rootNode, setRootNode] = useState<Outline | null>(null);
  const [loading, setLoading] = useState(true);

  // Selection state
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<Outline | null>(null);
  const [loadingNode, setLoadingNode] = useState(false);

  // Editor state
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [saving, setSaving] = useState(false);

  // Create modal state
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createParentId, setCreateParentId] = useState<string | null>(null);
  const [form] = Form.useForm();

  // --- Data loading ---

  const loadTree = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const rootRes = await outlinesApi.getRoot(projectId);
      if (rootRes.data && rootRes.data.id) {
        setRootNode(rootRes.data);
        const treeRes = await outlinesApi.getTree(projectId, rootRes.data.id);
        // Include root as the top-level node in the tree
        const rootTreeNode: TreeNodeData = {
          key: rootRes.data.id,
          title: rootRes.data.title,
          type: rootRes.data.type,
          children: treeRes.data.children ? convertToTreeData(treeRes.data.children) : [],
        };
        setTreeData([rootTreeNode]);
      }
    } catch (e) {
      if ((e as { response?: { status?: number } })?.response?.status === 404) {
        setTreeData([]);
        setRootNode(null);
      } else {
        message.error('加载大纲失败');
      }
    }
    setLoading(false);
  }, [projectId]);

  useEffect(() => {
    loadTree();
  }, [loadTree]);

  const convertToTreeData = (outlines: Outline[]): TreeNodeData[] => {
    return outlines.map(o => ({
      key: o.id,
      title: o.title,
      type: o.type,
      children: o.children ? convertToTreeData(o.children) : [],
    }));
  };

  // --- Node selection ---

  const handleSelectNode = useCallback(async (nodeId: string) => {
    if (!projectId) return;
    setSelectedNodeId(nodeId);
    setLoadingNode(true);
    try {
      const res = await outlinesApi.get(projectId, nodeId);
      setSelectedNode(res.data);
      setEditTitle(res.data.title);
      setEditContent(res.data.content || '');
    } catch {
      message.error('加载节点失败');
    }
    setLoadingNode(false);
  }, [projectId]);

  const handleDeselect = () => {
    setSelectedNodeId(null);
    setSelectedNode(null);
    setEditTitle('');
    setEditContent('');
  };

  // --- Save ---

  const handleSave = async () => {
    if (!projectId || !selectedNodeId) return;
    setSaving(true);
    try {
      await outlinesApi.update(projectId, selectedNodeId, {
        title: editTitle,
        content: editContent,
      });
      message.success('保存成功');
      loadTree(); // refresh tree in case title changed
    } catch {
      message.error('保存失败');
    }
    setSaving(false);
  };

  // --- Create child node ---

  const handleOpenCreate = (parentId: string | null) => {
    setCreateParentId(parentId);
    form.resetFields();
    setCreateModalOpen(true);
  };

  const handleConfirmCreate = async () => {
    if (!projectId) return;
    try {
      const values = await form.validateFields();
      const res = await outlinesApi.create(projectId, {
        title: values.title,
        content: '',
        type: values.type,
        parent_id: createParentId || undefined,
      });
      message.success('创建成功');
      setCreateModalOpen(false);
      await loadTree();
      // Auto-select the newly created node
      if (res.data?.id) {
        handleSelectNode(res.data.id);
      }
    } catch {
      // validation error
    }
  };

  // --- Delete ---

  const handleDelete = (nodeKey: string) => {
    if (!projectId) return;
    modal.confirm({
      title: '确认删除',
      content: '删除后子节点也会被删除，确认吗？',
      onOk: async () => {
        try {
          await outlinesApi.delete(projectId, nodeKey);
          message.success('删除成功');
          if (selectedNodeId === nodeKey) {
            handleDeselect();
          }
          loadTree();
        } catch {
          message.error('删除失败');
        }
      },
    });
  };

  // --- Tree node rendering ---

  const titleRender = (nodeData: TreeNodeData) => (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
      <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
        {TYPE_ICONS[nodeData.type || ''] || <FileTextOutlined />}
        <span>{nodeData.title}</span>
      </span>
      <Dropdown
        menu={{
          items: [
            { key: 'add', icon: <PlusOutlined />, label: '新建子节点', onClick: () => handleOpenCreate(nodeData.key) },
            { key: 'delete', icon: <DeleteOutlined />, label: '删除', danger: true, onClick: () => handleDelete(nodeData.key) },
          ],
        }}
        trigger={['click']}
      >
        <Button type="text" size="small" icon={<MoreOutlined />} onClick={e => e.stopPropagation()} />
      </Dropdown>
    </div>
  );

  // --- Render ---

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    );
  }

  // No outline exists yet — show empty state with create button
  if (treeData.length === 0) {
    return (
      <div>
        <Breadcrumb style={{ marginBottom: 12 }} items={[{ title: '大纲' }]} />
        <EmptyState
          description="暂无大纲"
          actionText="新建根节点"
          onAction={() => handleOpenCreate(null)}
        />
        <CreateNodeModal
          open={createModalOpen}
          form={form}
          onOk={handleConfirmCreate}
          onCancel={() => setCreateModalOpen(false)}
        />
      </div>
    );
  }

  return (
    <div>
      <Breadcrumb
        style={{ marginBottom: 12 }}
        items={[
          { title: <Link to={`/projects/${projectId}/outline`}>大纲</Link> },
          ...(selectedNode ? [{ title: selectedNode.title }] : []),
        ]}
      />

      <div style={{ display: 'flex', gap: 16, minHeight: 'calc(100vh - 200px)' }}>
        {/* Left: Tree panel */}
        <div
          style={{
            width: 260,
            flexShrink: 0,
            borderRight: '1px solid #f0f0f0',
            paddingRight: 16,
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div style={{ flex: 1, overflow: 'auto' }}>
            <Tree
              showLine={{ showLeafIcon: false }}
              defaultExpandAll
              selectedKeys={selectedNodeId ? [selectedNodeId] : []}
              treeData={treeData}
              titleRender={titleRender}
              onSelect={(keys) => {
                if (keys.length > 0) {
                  handleSelectNode(keys[0] as string);
                }
              }}
            />
          </div>
          <Button
            block
            icon={<PlusOutlined />}
            style={{ marginTop: 8 }}
            onClick={() => handleOpenCreate(selectedNodeId || rootNode?.id || null)}
          >
            新建子节点
          </Button>
        </div>

        {/* Right: Editor panel */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {!selectedNode ? (
            <EmptyState description="选择一个节点开始编辑" />
          ) : loadingNode ? (
            <div style={{ textAlign: 'center', padding: 100 }}>
              <Spin size="large" />
            </div>
          ) : (
            <div>
              <div style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <Input
                    value={editTitle}
                    onChange={e => setEditTitle(e.target.value)}
                    placeholder="节点标题"
                    style={{ fontSize: 18, fontWeight: 600, border: 'none', padding: 0, flex: 1 }}
                  />
                  <Button onClick={handleDeselect}>返回</Button>
                  <Button type="primary" loading={saving} onClick={handleSave}>保存</Button>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  {selectedNode.type && (
                    <Tag>{TYPE_LABELS[selectedNode.type] || selectedNode.type}</Tag>
                  )}
                </div>
              </div>

              <MarkdownEditor value={editContent} onChange={setEditContent} />
            </div>
          )}
        </div>
      </div>

      <CreateNodeModal
        open={createModalOpen}
        form={form}
        onOk={handleConfirmCreate}
        onCancel={() => setCreateModalOpen(false)}
      />
    </div>
  );
};

// --- Create Node Modal (extracted for clarity) ---

interface CreateNodeModalProps {
  open: boolean;
  form: ReturnType<typeof Form.useForm>[0];
  onOk: () => void;
  onCancel: () => void;
}

const CreateNodeModal = ({ open, form, onOk, onCancel }: CreateNodeModalProps) => (
  <Modal title="新建节点" open={open} onOk={onOk} onCancel={onCancel} width={480}>
    <Form form={form} layout="vertical">
      <Form.Item name="title" label="标题" rules={[{ required: true, message: '请输入标题' }]}>
        <Input placeholder="节点标题" />
      </Form.Item>
      <Form.Item name="type" label="类型" initialValue="chapter">
        <Select
          options={[
            { value: 'volume', label: '卷' },
            { value: 'chapter', label: '章' },
          ]}
        />
      </Form.Item>
    </Form>
  </Modal>
);

export default OutlineEditor;
```

- [ ] **Step 2: Run TypeScript type-check**

Run: `cd frontend && npm run type-check`
Expected: No errors (exit code 0)

- [ ] **Step 3: Run ESLint**

Run: `cd frontend && npm run lint`
Expected: No errors (exit code 0). Fix any warnings if present.

- [ ] **Step 4: Start dev server and verify in browser**

Run: `cd frontend && npm run dev`
Then open `http://localhost:5173/projects/<projectId>/outline` and verify:
1. Left tree shows the root node (全书大纲) as the first item
2. Clicking any node loads its content in the right panel
3. Right panel shows editable title + type tag + MarkdownEditor (matching WorldEdit pattern)
4. "返回" button deselects the node, returns to EmptyState
5. "保存" button saves changes and refreshes the tree title
6. "新建子节点" opens modal, creates child, auto-selects it
7. "删除" with confirmation, cascading delete, deselects if deleted node was selected
8. When no outline exists, shows EmptyState with "新建根节点" button

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/outline/OutlineEditor.tsx
git commit -m "feat(frontend): redesign outline editor as left-tree + right-editor split panel

Root outline node is now visible and editable. Layout aligned with
WorldEdit/CharacterEdit/ChapterEdit patterns (Breadcrumb + editable
title + summary + MarkdownEditor)."
```
