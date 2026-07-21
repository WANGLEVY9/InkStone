import { useState, useEffect } from 'react';
import { Row, Col, Button } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { useAppMessage, useAppModal } from '@/hooks/useAppMessage';
import { worldApi } from '@/api/world';
import WorldCard from '@/components/cards/WorldCard';
import PageHeader from '@/components/common/PageHeader';
import EmptyState from '@/components/common/EmptyState';
import type { WorldSetting } from '@/types';
import PageContainer from '@/components/common/PageContainer';

const WorldList = () => {
  const { id: projectId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { message } = useAppMessage();
  const modal = useAppModal();
  const [worlds, setWorlds] = useState<WorldSetting[]>([]);
  const [loading, setLoading] = useState(true);

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
      const res = await worldApi.create(projectId, {
        name: '未命名设定',
        content: '',
      });
      message.success('世界观创建成功');
      navigate(`/projects/${projectId}/world/${res.data.id}`);
    } catch {
      message.error('创建失败');
    }
  };

  const handleDelete = (worldId: string) => {
    if (!projectId) return;
    modal.confirm({
      title: '确认删除',
      content: '删除后无法恢复，确认吗？',
      okText: '删除',
      okButtonProps: { danger: true },
      cancelText: '取消',
      onOk: async () => {
        try {
          await worldApi.delete(projectId, worldId);
          setWorlds(prev => prev.filter(w => w.id !== worldId));
          message.success('已删除');
        } catch {
          message.error('删除失败');
        }
      },
    });
  };

  return (
    <PageContainer>
    <div>
      <PageHeader
        dataTour="world-header"
        title="世界观设定"
        subtitle="打造独特的世界观与设定"
        extra={
          <Button data-tour-world-create type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建设定
          </Button>
        }
      />

      <div data-tour-world-list>
      {worlds.length === 0 && !loading ? (
        <EmptyState
          description="暂无世界观设定"
          actionText="新建设定"
          onAction={handleCreate}
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
                <Button
                  type="text"
                  danger
                  size="small"
                  icon={<DeleteOutlined />}
                  style={{ position: 'absolute', bottom: 8, left: 8 }}
                  onClick={() => handleDelete(world.id)}
                />
              </div>
            </Col>
          ))}
        </Row>
      )}
      </div>
    </div>
    </PageContainer>
  );
};

export default WorldList;
