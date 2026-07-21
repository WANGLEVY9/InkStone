import { useState, useEffect } from 'react';
import { Button, Input, Spin, Breadcrumb } from 'antd';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAppMessage } from '@/hooks/useAppMessage';
import { worldApi } from '@/api/world';
import MarkdownEditor from '@/components/common/MarkdownEditor';
import type { WorldSetting } from '@/types';
import PageContainer from '@/components/common/PageContainer';

const WorldEdit = () => {
  const { id: projectId, worldId } = useParams<{ id: string; worldId: string }>();
  const navigate = useNavigate();
  const { message } = useAppMessage();
  const [world, setWorld] = useState<WorldSetting | null>(null);
  const [name, setName] = useState('');
  const [summary, setSummary] = useState('');
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!projectId || !worldId) return;
    worldApi.get(projectId, worldId).then(res => {
      setWorld(res.data);
      setName(res.data.name);
      setSummary(res.data.summary || '');
      setContent(res.data.content || '');
      setLoading(false);
    }).catch(() => {
      message.error('加载失败');
      navigate(`/projects/${projectId}/world`);
    });
  }, [projectId, worldId]);

  const handleSave = async () => {
    if (!projectId || !worldId) return;
    setSaving(true);
    try {
      await worldApi.update(projectId, worldId, { name, summary, content });
      message.success('保存成功');
    } catch {
      message.error('保存失败');
    }
    setSaving(false);
  };

  if (loading || !world) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
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
          { title: <Link to={`/projects/${projectId}/world`}>世界观</Link> },
          { title: world.name },
        ]}
      />
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, marginBottom: 4 }}>
          <Input
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="设定名称"
            className="literati-title-input"
            style={{ flex: 1 }}
          />
          <Button onClick={() => navigate(`/projects/${projectId}/world`)}>返回</Button>
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
          value={summary}
          onChange={e => setSummary(e.target.value)}
          placeholder="添加题记..."
          className="literati-summary-input"
        />
      </div>

      <MarkdownEditor value={content} onChange={setContent} />
    </div>
    </PageContainer>
  );
};

export default WorldEdit;
