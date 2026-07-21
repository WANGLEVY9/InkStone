import { useState, useEffect } from 'react';
import { Table, Button, Tag, Space } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { useAppMessage, useAppModal } from '@/hooks/useAppMessage';
import { chaptersApi } from '@/api/chapters';
import PageHeader from '@/components/common/PageHeader';
import EmptyState from '@/components/common/EmptyState';
import { formatDate } from '@/utils/format';
import type { Chapter } from '@/types';
import PageContainer from '@/components/common/PageContainer';

const ChapterList = () => {
  const { id: projectId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { message } = useAppMessage();
  const modal = useAppModal();
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loading, setLoading] = useState(true);

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
      const nextNumber = chapters.length > 0
        ? Math.max(...chapters.map(c => c.chapter_number)) + 1
        : 1;
      const res = await chaptersApi.create(projectId, {
        title: `第${nextNumber}章`,
        content: '',
        chapter_number: nextNumber,
      });
      message.success('章节创建成功');
      navigate(`/projects/${projectId}/chapters/${res.data.id}`);
    } catch {
      message.error('创建失败');
    }
  };

  const handleDelete = async (chapterId: string) => {
    if (!projectId) return;
    modal.confirm({
      title: '确认删除',
      content: '删除后无法恢复，确认吗？',
      okText: '删除',
      okButtonProps: { danger: true },
      cancelText: '取消',
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
    <PageContainer>
    <div>
      <PageHeader
        title="章节管理"
        subtitle="编织精彩的故事情节"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建章节
          </Button>
        }
      />

      {chapters.length === 0 && !loading ? (
        <EmptyState
          description="暂无章节"
          actionText="新建章节"
          onAction={handleCreate}
        />
      ) : (
        <div style={{ height: 'calc(100vh - 280px)', display: 'flex', flexDirection: 'column' }}>
          <Table
            dataSource={chapters}
            columns={columns}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 10, showSizeChanger: false }}
            style={{ flex: 1 }}
          />
        </div>
      )}
    </div>
    </PageContainer>
  );
};

export default ChapterList;
