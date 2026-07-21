import { useState, useEffect, useCallback } from 'react';
import { Tree, Button, Dropdown, Tag, Spin } from 'antd';
import { PlusOutlined, DeleteOutlined, MoreOutlined } from '@ant-design/icons';
import { useParams } from 'react-router-dom';
import { useAppMessage, useAppModal } from '@/hooks/useAppMessage';
import { outlinesApi } from '@/api/outlines';
import MarkdownEditor from '@/components/common/MarkdownEditor';
import EmptyState from '@/components/common/EmptyState';
import PageHeader from '@/components/common/PageHeader';
import PageContainer from '@/components/common/PageContainer';
import type { Outline, TreeNodeData } from '@/types';

const TYPE_LABELS: Record<string, string> = {
  root: '总纲',
  volume: '卷',
  chapter: '章',
  part: '篇',
  section: '节',
};

const InkIcon = ({ children }: { children: React.ReactNode }) => (
  <svg
    width="12"
    height="12"
    viewBox="0 0 12 12"
    fill="none"
    stroke="var(--ink-medium)"
    strokeWidth="1"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    {children}
  </svg>
);

const RootIcon = () => (
  <InkIcon>
    <rect x="2" y="2" width="8" height="8" />
    <line x1="2" y1="5" x2="10" y2="5" />
    <line x1="2" y1="8" x2="10" y2="8" />
  </InkIcon>
);

const VolumeIcon = () => (
  <InkIcon>
    <line x1="2.5" y1="2" x2="2.5" y2="10" />
    <line x1="9.5" y1="2" x2="9.5" y2="10" />
    <line x1="2.5" y1="6" x2="9.5" y2="6" />
  </InkIcon>
);

const ChapterIcon = () => (
  <InkIcon>
    <line x1="3" y1="3.5" x2="9" y2="3.5" />
    <line x1="3" y1="6.5" x2="9" y2="6.5" />
    <line x1="3" y1="9.5" x2="7" y2="9.5" />
  </InkIcon>
);

const TYPE_ICONS: Record<string, React.ReactNode> = {
  root: <RootIcon />,
  volume: <VolumeIcon />,
  chapter: <ChapterIcon />,
  part: <VolumeIcon />,
  section: <ChapterIcon />,
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

  // --- Data loading ---

  const loadTree = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const rootRes = await outlinesApi.getRoot(projectId);
      if (rootRes.data && rootRes.data.id) {
        setRootNode(rootRes.data);
        const treeRes = await outlinesApi.getTree(projectId, rootRes.data.id);
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
      loadTree();
    } catch {
      message.error('保存失败');
    }
    setSaving(false);
  };

  // --- Create child node ---

  const getParentType = (parentId: string | null): string | null => {
    if (!parentId) return null;
    const findType = (nodes: TreeNodeData[]): string | null => {
      for (const n of nodes) {
        if (n.key === parentId) return n.type || null;
        if (n.children) {
          const found = findType(n.children);
          if (found) return found;
        }
      }
      return null;
    };
    return findType(treeData);
  };

  const getAvailableTypes = (parentType: string | null): string[] => {
    if (!parentType) {
      return rootNode ? [] : ['root'];
    }
    if (parentType === 'root') return ['volume'];
    if (parentType === 'volume') return ['chapter'];
    return [];
  };

  const getTypeForParent = (parentType: string | null): string => {
    if (!parentType) return 'root';
    if (parentType === 'root') return 'volume';
    if (parentType === 'volume') return 'chapter';
    return '';
  };

  const TYPE_DEFAULT_NAMES: Record<string, string> = {
    root: '总纲',
    volume: '新卷',
    chapter: '新章',
  };

  const handleCreate = async (parentId: string | null) => {
    if (!projectId) return;
    const parentType = getParentType(parentId);
    const available = getAvailableTypes(parentType);
    if (available.length === 0) {
      message.warning('该节点不支持新建子节点');
      return;
    }
    const nodeType = getTypeForParent(parentType);
    if (!nodeType) return;
    try {
      const res = await outlinesApi.create(projectId, {
        title: TYPE_DEFAULT_NAMES[nodeType] || '新节点',
        content: '',
        type: nodeType,
        parent_id: parentId ?? undefined,
      });
      message.success('创建成功');
      await loadTree();
      if (res.data?.id) {
        handleSelectNode(res.data.id);
      }
    } catch {
      message.error('创建失败');
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
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        width: '100%',
        fontFamily: 'var(--font-display)',
        letterSpacing: '0.04em',
      }}
    >
      <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        {TYPE_ICONS[nodeData.type || ''] || <ChapterIcon />}
        <span>{nodeData.title}</span>
      </span>
      <Dropdown
        menu={{
          items: [
            ...(nodeData.type !== 'chapter'
              ? [{ key: 'add', icon: <PlusOutlined />, label: '新建子节点', onClick: () => handleCreate(nodeData.key) }]
              : []),
            { key: 'delete', icon: <DeleteOutlined />, label: '删除', danger: true, onClick: () => handleDelete(nodeData.key) },
          ],
        }}
        trigger={['click']}
      >
        <Button type="text" size="small" icon={<MoreOutlined />} data-tour-outline-add onClick={e => e.stopPropagation()} />
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

  if (treeData.length === 0) {
    return (
      <div>
        <PageContainer>
          <PageHeader dataTour="outline-header" title="大纲编辑" subtitle="规划故事的起承转合" />
        </PageContainer>
        <EmptyState
          description="尚未立纲"
          actionText="新立总纲"
          onAction={() => handleCreate(null)}
        />
      </div>
    );
  }

  return (
    <div>
      <PageContainer>
        <PageHeader dataTour="outline-header" title="大纲编辑" subtitle="规划故事的起承转合" />
      </PageContainer>

      <div style={{ display: 'flex', gap: 16, height: 'calc(100vh - 200px)' }}>
        {/* Left: Tree panel */}
        <div
          data-tour-outline-tree
          style={{
            width: 300,
            flexShrink: 0,
            borderRight: '1px solid var(--silk-line)',
            paddingRight: 16,
            overflow: 'auto',
          }}
        >
          <Tree
            showLine={false}
            defaultExpandAll
            selectedKeys={selectedNodeId ? [selectedNodeId] : []}
            treeData={treeData}
            titleRender={titleRender}
            style={{ fontSize: 13, background: 'transparent' }}
            onSelect={(keys) => {
              if (keys.length > 0) {
                handleSelectNode(keys[0] as string);
              }
            }}
          />
        </div>

        {/* Right: Editor panel */}
        <div data-tour-outline-editor style={{ flex: 1, minWidth: 0 }}>
          {!selectedNode ? (
            <EmptyState description="选一节起笔" />
          ) : loadingNode ? (
            <div style={{ textAlign: 'center', padding: 100 }}>
              <Spin size="large" />
            </div>
          ) : (
            <div>
              <div style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, marginBottom: 4 }}>
                  <input
                    value={editTitle}
                    onChange={e => setEditTitle(e.target.value)}
                    placeholder="节点标题"
                    className="literati-title-input"
                    style={{ flex: 1, width: '100%' }}
                  />
                  <Button onClick={handleDeselect}>返回</Button>
                  <Button type="primary" loading={saving} onClick={handleSave}>保存</Button>
                </div>
                <div
                  style={{
                    height: 1,
                    width: 32,
                    background: 'var(--vermilion)',
                    marginBottom: 12,
                  }}
                />
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  {selectedNode.type && (
                    <Tag className="seal-tag-gold">{TYPE_LABELS[selectedNode.type] || selectedNode.type}</Tag>
                  )}
                </div>
              </div>

              <MarkdownEditor value={editContent} onChange={setEditContent} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OutlineEditor;
