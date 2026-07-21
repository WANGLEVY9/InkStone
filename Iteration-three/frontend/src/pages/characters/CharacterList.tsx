import { useState, useEffect } from 'react';
import { Row, Col, Button, Pagination } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { useAppMessage, useAppModal } from '@/hooks/useAppMessage';
import { charactersApi } from '@/api/characters';
import CharacterCard from '@/components/cards/CharacterCard';
import PageHeader from '@/components/common/PageHeader';
import EmptyState from '@/components/common/EmptyState';
import type { Character } from '@/types';
import PageContainer from '@/components/common/PageContainer';

const PAGE_SIZE = 8;

const CharacterList = () => {
  const { id: projectId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { message } = useAppMessage();
  const modal = useAppModal();
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

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

  const handleDelete = (charId: string) => {
    if (!projectId) return;
    modal.confirm({
      title: '确认删除',
      content: '删除后无法恢复，确认吗？',
      okText: '删除',
      okButtonProps: { danger: true },
      cancelText: '取消',
      onOk: async () => {
        try {
          await charactersApi.delete(projectId, charId);
          setCharacters(prev => prev.filter(c => c.id !== charId));
          message.success('已删除');
        } catch {
          message.error('删除失败');
        }
      },
    });
  };

  const handleCreate = async () => {
    if (!projectId) return;
    try {
      const res = await charactersApi.create(projectId, {
        name: '未命名角色',
        content: '',
      });
      message.success('角色创建成功');
      navigate(`/projects/${projectId}/characters/${res.data.id}`);
    } catch {
      message.error('创建失败');
    }
  };

  return (
    <PageContainer>
    <div>
      <PageHeader
        dataTour="characters-header"
        title="角色档案"
        subtitle="塑造鲜活的人物群像"
        extra={
          <Button data-tour-characters-create type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建角色
          </Button>
        }
      />

      <div data-tour-characters-list>
      {characters.length === 0 && !loading ? (
        <div data-tour-characters-edit-hint>
        <EmptyState
          description="暂无角色"
          actionText="新建角色"
          onAction={handleCreate}
        />
        </div>
      ) : (
        <>
          <Row data-tour-characters-edit-hint gutter={[16, 16]}>
            {characters.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE).map(character => (
              <Col key={character.id} xs={24} sm={12} md={8} lg={6}>
                <div style={{ position: 'relative' }}>
                  <CharacterCard
                    character={character}
                    onClick={() => navigate(`/projects/${projectId}/characters/${character.id}`)}
                  />
                  <Button
                    type="text"
                    danger
                    size="small"
                    icon={<DeleteOutlined />}
                    style={{ position: 'absolute', bottom: 8, left: 8 }}
                    onClick={() => handleDelete(character.id)}
                  />
                </div>
              </Col>
            ))}
          </Row>
          {characters.length > PAGE_SIZE && (
            <div style={{ display: 'flex', justifyContent: 'center', marginTop: 24 }}>
              <Pagination
                current={page}
                pageSize={PAGE_SIZE}
                total={characters.length}
                onChange={setPage}
                showSizeChanger={false}
              />
            </div>
          )}
        </>
      )}
      </div>
    </div>
    </PageContainer>
  );
};

export default CharacterList;
