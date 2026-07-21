import { useState, useEffect } from 'react';
import { Button, Input, Select, Breadcrumb, Spin } from 'antd';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAppMessage } from '@/hooks/useAppMessage';
import { skillsApi } from '@/api/skills';
import MarkdownEditor from '@/components/common/MarkdownEditor';
import PageContainer from '@/components/common/PageContainer';
import type { Skill } from '@/types';

const DOMAIN_OPTIONS = [
  { value: 'global', label: '全局' },
  { value: 'world', label: '世界观' },
  { value: 'character', label: '角色' },
  { value: 'plot', label: '剧情' },
  { value: 'chapter', label: '章节' },
  { value: 'review', label: '审校' },
];

const NAME_PATTERN = /^[a-z0-9]+(-[a-z0-9]+)*$/;

const SkillEdit = () => {
  const { skillName } = useParams<{ skillName: string }>();
  const navigate = useNavigate();
  const { message } = useAppMessage();

  const isNew = !skillName;
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [domain, setDomain] = useState('global');
  const [tags, setTags] = useState<string[]>([]);
  const [content, setContent] = useState('');

  useEffect(() => {
    if (isNew) {
      setLoading(false);
      return;
    }
    skillsApi.get(skillName)
      .then(res => {
        const data: Skill = res.data;
        setName(data.name);
        setDescription(data.description || '');
        setDomain(data.domain || 'global');
        setTags(data.tags || []);
        setContent(data.content || '');
        setLoading(false);
      })
      .catch(() => {
        message.error('加载技能失败');
        navigate('/skills');
      });
  }, [skillName]);

  const handleSave = async () => {
    if (!name.trim()) {
      message.error('请输入技能名称');
      return;
    }
    if (!NAME_PATTERN.test(name)) {
      message.error('名称只能包含小写字母、数字和连字符');
      return;
    }
    if (!description.trim()) {
      message.error('请输入描述');
      return;
    }
    if (!content.trim()) {
      message.error('请输入技能内容');
      return;
    }

    setSaving(true);
    try {
      const payload = {
        description,
        content,
        domain: domain === 'global' ? null : domain,
        tags,
      };

      if (isNew) {
        await skillsApi.create({ name, ...payload });
      } else {
        await skillsApi.update(skillName!, payload);
      }

      message.success('保存成功');
      navigate('/skills');
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
        if (axiosErr.response?.status === 409) {
          message.error(axiosErr.response.data?.detail || '技能名称已存在');
        } else {
          message.error('保存失败');
        }
      } else {
        message.error('保存失败');
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', paddingTop: 120 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <PageContainer>
      <div>
        <Breadcrumb
          style={{ marginBottom: 12, fontFamily: 'var(--font-display)', letterSpacing: '0.04em' }}
          items={[
            { title: <Link to="/skills">技能库</Link> },
            { title: isNew ? '新建技能' : skillName },
          ]}
        />

        <div style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, marginBottom: 4 }}>
            <Input
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="技能名称（如 my-writing-style）"
              className="literati-title-input"
              style={{ flex: 1 }}
              disabled={!isNew}
            />
            <Button onClick={() => navigate('/skills')}>返回</Button>
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
          <Input
            value={description}
            onChange={e => setDescription(e.target.value)}
            placeholder="一句话描述这个技能的用途..."
            className="literati-summary-input"
          />
        </div>

        <div style={{ display: 'flex', gap: 16, marginBottom: 16, flexWrap: 'wrap' }}>
          <div style={{ minWidth: 160 }}>
            <div
              style={{
                fontSize: 11,
                color: 'var(--ink-light)',
                fontFamily: 'var(--font-display)',
                letterSpacing: '0.06em',
                marginBottom: 4,
              }}
            >
              领域
            </div>
            <Select
              value={domain}
              onChange={setDomain}
              options={DOMAIN_OPTIONS}
              style={{ width: 160 }}
              size="small"
            />
          </div>
          <div style={{ flex: 1, minWidth: 200 }}>
            <div
              style={{
                fontSize: 11,
                color: 'var(--ink-light)',
                fontFamily: 'var(--font-display)',
                letterSpacing: '0.06em',
                marginBottom: 4,
              }}
            >
              标签
            </div>
            <Select
              mode="tags"
              value={tags}
              onChange={setTags}
              placeholder="输入标签后按回车"
              style={{ width: '100%' }}
              size="small"
            />
          </div>
        </div>

        <MarkdownEditor value={content} onChange={setContent} />
      </div>
    </PageContainer>
  );
};

export default SkillEdit;
