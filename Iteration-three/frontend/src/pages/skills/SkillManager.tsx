import { useState, useEffect, useMemo } from 'react';
import {
  Tabs, Row, Col, Button, Input, Card,
} from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAppMessage, useAppModal } from '@/hooks/useAppMessage';
import { skillsApi } from '@/api/skills';
import PageHeader from '@/components/common/PageHeader';
import EmptyState from '@/components/common/EmptyState';
import PageContainer from '@/components/common/PageContainer';
import type { Skill } from '@/types';

const DOMAIN_LABELS: Record<string, string> = {
  global: '全局',
  world: '世界观',
  character: '角色',
  plot: '剧情',
  chapter: '章节',
  review: '审校',
};

const DOMAIN_ORDER = ['global', 'world', 'character', 'plot', 'chapter', 'review'];

const SkillCard = ({ skill, onEdit, onDelete }: {
  skill: Skill;
  onEdit: () => void;
  onDelete: () => void;
}) => {
  const [hovered, setHovered] = useState(false);

  return (
    <Card
      hoverable
      onClick={onEdit}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        borderRadius: 'var(--radius-lg)',
        position: 'relative',
        overflow: 'hidden',
      }}
      styles={{ body: { padding: '14px 14px 14px 46px' } }}
    >
      <div
        className="seal-stamp"
        style={{
          position: 'absolute',
          top: 12,
          left: 12,
          width: 24,
          height: 24,
          fontSize: 13,
        }}
        aria-hidden="true"
      >
        技
      </div>

      <div
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: 14,
          fontWeight: 600,
          color: 'var(--ink-heavy)',
          letterSpacing: '0.04em',
          marginBottom: 6,
        }}
      >
        {skill.name}
      </div>

      <div
        style={{
          fontFamily: 'var(--font-body)',
          fontSize: 12,
          color: 'var(--ink-medium)',
          lineHeight: 1.7,
          height: 41,
          overflow: 'hidden',
          marginBottom: 10,
        }}
      >
        {skill.description || '暂无描述'}
      </div>

      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
        {skill.tags.map(tag => (
          <span
            key={tag}
            style={{
              fontSize: 10,
              fontFamily: 'var(--font-display)',
              color: 'var(--ink-light)',
              background: 'var(--paper-sunken)',
              padding: '0 5px',
              lineHeight: '16px',
              borderRadius: 'var(--radius-sm)',
              letterSpacing: '0.03em',
            }}
          >
            {tag}
          </span>
        ))}
        {skill.tags.length === 0 && (
          <span
            style={{
              fontSize: 10,
              color: 'var(--ink-light)',
              fontFamily: 'var(--font-display)',
              letterSpacing: '0.05em',
            }}
          >
            无标签
          </span>
        )}
      </div>

      <Button
        type="text"
        danger
        size="small"
        icon={<DeleteOutlined />}
        style={{ position: 'absolute', bottom: 8, left: 8 }}
        onClick={e => {
          e.stopPropagation();
          onDelete();
        }}
      />

      <div
        className="seal-stamp"
        style={{
          position: 'absolute',
          right: 10,
          bottom: 10,
          width: 22,
          height: 22,
          fontSize: 11,
          opacity: hovered ? 0.6 : 0,
          transition: 'opacity 0.25s ease',
          pointerEvents: 'none',
        }}
        aria-hidden="true"
      >
        编
      </div>
    </Card>
  );
};

const SkillManager = () => {
  const navigate = useNavigate();
  const { message } = useAppMessage();
  const modal = useAppModal();
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    skillsApi.list()
      .then(res => setSkills(res.data))
      .catch(() => message.error('加载技能列表失败'))
      .finally(() => setLoading(false));
  }, []);

  const grouped = useMemo(() => {
    const map: Record<string, Skill[]> = {};
    for (const d of DOMAIN_ORDER) map[d] = [];
    for (const s of skills) {
      const d = s.domain || 'global';
      if (!map[d]) map[d] = [];
      map[d].push(s);
    }
    return map;
  }, [skills]);

  const filteredGroups = useMemo(() => {
    if (!search.trim()) return grouped;
    const term = search.trim().toLowerCase();
    const result: Record<string, Skill[]> = {};
    for (const d of DOMAIN_ORDER) {
      result[d] = grouped[d].filter(s =>
        s.name.toLowerCase().includes(term) ||
        s.description.toLowerCase().includes(term) ||
        s.tags.some(t => t.toLowerCase().includes(term))
      );
    }
    return result;
  }, [grouped, search]);

  const handleDelete = (skill: Skill) => {
    modal.confirm({
      title: '确认删除',
      content: `删除技能「${skill.name}」后无法恢复，确认吗？`,
      okText: '删除',
      okButtonProps: { danger: true },
      cancelText: '取消',
      onOk: async () => {
        try {
          await skillsApi.delete(skill.name);
          setSkills(prev => prev.filter(s => s.name !== skill.name));
          message.success('已删除');
        } catch {
          message.error('删除失败');
        }
      },
    });
  };

  if (loading) {
    return (
      <PageContainer>
        <div style={{ textAlign: 'center', paddingTop: 120 }}>
          <span
            style={{
              color: 'var(--ink-light)',
              fontFamily: 'var(--font-display)',
              letterSpacing: '0.06em',
            }}
          >
            展卷中…
          </span>
        </div>
      </PageContainer>
    );
  }

  if (skills.length === 0) {
    return (
      <PageContainer>
        <PageHeader
          title="技能库"
          subtitle="管理 AI 助手的专长技能"
          extra={
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => navigate('/skills/new')}
            >
              新建技能
            </Button>
          }
        />
        <EmptyState
          description="暂无技能"
          actionText="新建技能"
          onAction={() => navigate('/skills/new')}
        />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <PageHeader
        title="技能库"
        subtitle="管理 AI 助手的专长技能"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate('/skills/new')}
          >
            新建技能
          </Button>
        }
      />

      <Input.Search
        placeholder="搜索技能名称、描述或标签..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        style={{ marginBottom: 24, maxWidth: 400 }}
        allowClear
      />

      <Tabs
        items={DOMAIN_ORDER.map(domain => {
          const list = filteredGroups[domain] || [];
          return {
            key: domain,
            label: `${DOMAIN_LABELS[domain]} (${list.length})`,
            children: list.length === 0 ? (
              <div
                style={{
                  color: 'var(--ink-light)',
                  fontFamily: 'var(--font-display)',
                  fontSize: 13,
                  letterSpacing: '0.05em',
                  padding: '40px 0',
                  textAlign: 'center',
                }}
              >
                {search.trim() ? '未找到匹配的技能' : '该领域暂无技能'}
              </div>
            ) : (
              <Row gutter={[16, 16]}>
                {list.map(skill => (
                  <Col key={skill.name} xs={24} sm={12} md={8} lg={6}>
                    <SkillCard
                      skill={skill}
                      onEdit={() => navigate(`/skills/${skill.name}/edit`)}
                      onDelete={() => handleDelete(skill)}
                    />
                  </Col>
                ))}
              </Row>
            ),
          };
        })}
      />
    </PageContainer>
  );
};

export default SkillManager;
