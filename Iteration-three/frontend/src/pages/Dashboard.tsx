import { useState, useEffect, useCallback, useMemo } from 'react';
import { Modal, Form, Input, Spin, theme } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useAppMessage } from '@/hooks/useAppMessage';
import { projectsApi } from '@/api/projects';
import type { Project } from '@/types';
import LeftPanel from '@/components/dashboard/LeftPanel';
import RightPanel from '@/components/dashboard/RightPanel';
import type { SortOption, FilterOption, ViewMode } from '@/components/dashboard/ControlBar';

const VIEW_MODE_KEY = 'dashboard-view-mode';

const Dashboard = () => {
  const { message } = useAppMessage();
  const navigate = useNavigate();
  const { token } = theme.useToken();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState<SortOption>('updated_at');
  const [filter, setFilter] = useState<FilterOption>('all');
  const [viewMode, setViewMode] = useState<ViewMode>(
    () => (localStorage.getItem(VIEW_MODE_KEY) as ViewMode) || 'bookshelf'
  );
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [managementMode, setManagementMode] = useState(false);
  const [selectedProjectIds, setSelectedProjectIds] = useState<Set<string>>(() => new Set());
  const [form] = Form.useForm();

  const greeting = useMemo(() => {
    const hour = new Date().getHours();
    if (hour < 6) return '夜深了，注意休息';
    if (hour < 12) return '早上好';
    if (hour < 14) return '中午好';
    if (hour < 18) return '下午好';
    return '晚上好';
  }, []);

  const today = useMemo(() => {
    const d = new Date();
    const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
    return `${d.getMonth() + 1}月${d.getDate()}日 星期${weekdays[d.getDay()]}`;
  }, []);

  const loadProjects = useCallback(async () => {
    try {
      setLoading(true);
      const res = await projectsApi.list();
      setProjects(res.data);
    } catch {
      message.error('加载项目列表失败');
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const handleViewModeChange = (mode: ViewMode) => {
    setViewMode(mode);
    localStorage.setItem(VIEW_MODE_KEY, mode);
  };

  const handleTogglePin = async (projectId: string) => {
    const project = projects.find((p) => p.id === projectId);
    if (!project) return;

    try {
      const res = await projectsApi.update(projectId, { is_pinned: !project.is_pinned });
      setProjects((prev) => prev.map((p) => (p.id === projectId ? res.data : p)));
    } catch {
      message.error('更新标注失败');
    }
  };

  const handleManageToggle = () => {
    setManagementMode((prev) => !prev);
    setSelectedProjectIds(new Set());
  };

  const handleToggleSelectProject = (projectId: string) => {
    setSelectedProjectIds((prev) => {
      const next = new Set(prev);
      if (next.has(projectId)) {
        next.delete(projectId);
      } else {
        next.add(projectId);
      }
      return next;
    });
  };

  const handleSelectAll = () => {
    setSelectedProjectIds(new Set(processed.map((project) => project.id)));
  };

  const handleClearSelection = () => {
    setSelectedProjectIds(new Set());
  };

  const handleBatchDelete = async () => {
    const ids = [...selectedProjectIds];
    if (ids.length === 0) return;

    try {
      await Promise.all(ids.map((id) => projectsApi.delete(id)));
      setProjects((prev) => prev.filter((project) => !selectedProjectIds.has(project.id)));
      setSelectedProjectIds(new Set());
      message.success('已删除选中卷宗');
    } catch {
      message.error('删除卷宗失败');
    }
  };

  const handleBatchPin = async (isPinned: boolean) => {
    const ids = [...selectedProjectIds];
    if (ids.length === 0) return;

    try {
      const results = await Promise.all(ids.map((id) => projectsApi.update(id, { is_pinned: isPinned })));
      const updatedMap = new Map(results.map((res) => [res.data.id, res.data]));
      setProjects((prev) => prev.map((project) => updatedMap.get(project.id) || project));
      message.success(isPinned ? '已标注选中卷宗' : '已取消标注选中卷宗');
    } catch {
      message.error('批量标注失败');
    }
  };

  const handleCreate = async (values: { name: string; description?: string }) => {
    try {
      const res = await projectsApi.create(values);
      setProjects((prev) => [res.data, ...prev]);
      setCreateModalOpen(false);
      form.resetFields();
      navigate(`/projects/${res.data.id}/world`);
    } catch {
      message.error('创建项目失败');
    }
  };

  const openCreateModal = () => {
    setCreateModalOpen(true);
  };

  const processed = [...projects]
    .filter((p) => {
      if (filter === 'active') return p.status === 'active';
      if (filter === 'archived') return p.status === 'archived';
      return true;
    })
    .filter((p) => p.name.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      if (a.is_pinned !== b.is_pinned) return a.is_pinned ? -1 : 1;
      switch (sort) {
        case 'updated_at':
          return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
        case 'created_at':
          return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        case 'name':
          return a.name.localeCompare(b.name, 'zh');
        case 'word_count':
          return b.word_count - a.word_count;
        default:
          return 0;
      }
    });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      <div style={{ marginBottom: 22, flexShrink: 0 }}>
        <div
          style={{
            fontSize: 26,
            fontWeight: 700,
            color: token.colorText,
            fontFamily: 'var(--font-display)',
            letterSpacing: '0.04em',
          }}
        >
          {greeting}，欢迎回到砚台
        </div>
        <div
          style={{
            fontSize: 12,
            color: token.colorTextSecondary,
            marginTop: 6,
            fontFamily: 'var(--font-display)',
            letterSpacing: '0.08em',
          }}
        >
          {today}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 16, flex: 1, minHeight: 0, overflow: 'hidden', position: 'relative' }}>
        {loading && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(245, 239, 227, 0.5)', zIndex: 10, borderRadius: 12 }}>
            <Spin />
          </div>
        )}
        <LeftPanel projects={projects} />
        <RightPanel
          projects={processed}
          search={search}
          onSearchChange={setSearch}
          sort={sort}
          onSortChange={setSort}
          filter={filter}
          onFilterChange={setFilter}
          viewMode={viewMode}
          onViewModeChange={handleViewModeChange}
          onCreate={openCreateModal}
          onTogglePin={handleTogglePin}
          managementMode={managementMode}
          selectedProjectIds={selectedProjectIds}
          onManageToggle={handleManageToggle}
          onSelectAll={handleSelectAll}
          onClearSelection={handleClearSelection}
          onToggleSelectProject={handleToggleSelectProject}
          onBatchDelete={handleBatchDelete}
          onBatchPin={handleBatchPin}
        />
      </div>
      <Modal
        title="新建项目"
        open={createModalOpen}
        onCancel={() => setCreateModalOpen(false)}
        onOk={() => form.submit()}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item
            name="name"
            label="项目名称"
            rules={[{ required: true, message: '请输入项目名称' }]}
          >
            <Input placeholder="请输入项目名称" />
          </Form.Item>
          <Form.Item name="description" label="项目描述">
            <Input.TextArea placeholder="请输入项目描述（可选）" rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Dashboard;
