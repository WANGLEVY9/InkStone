import { useState, useEffect } from 'react';
import { Button, Input, Tag, Spin, Breadcrumb } from 'antd';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAppMessage } from '@/hooks/useAppMessage';
import { charactersApi } from '@/api/characters';
import MarkdownEditor from '@/components/common/MarkdownEditor';
import { parseCharacterMeta, serializeWithFrontmatter } from '@/utils/frontmatter';
import type { Character } from '@/types';
import type { FrontmatterData } from '@/utils/frontmatter';
import PageContainer from '@/components/common/PageContainer';

const CharacterEdit = () => {
  const { id: projectId, charId } = useParams<{ id: string; charId: string }>();
  const navigate = useNavigate();
  const { message } = useAppMessage();
  const [character, setCharacter] = useState<Character | null>(null);
  const [name, setName] = useState('');
  const [summary, setSummary] = useState('');
  const [content, setContent] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [characterMeta, setCharacterMeta] = useState<FrontmatterData>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!projectId || !charId) return;
    charactersApi.get(projectId, charId).then(res => {
      setCharacter(res.data);
      setName(res.data.name);
      setSummary(res.data.summary || '');
      const meta = parseCharacterMeta(res.data.content || '');
      setContent(meta.content);
      setTags(meta.tags);
      const { tags: _, content: __, ...rest } = meta;
      setCharacterMeta(rest);
      setLoading(false);
    }).catch(() => {
      message.error('加载失败');
      navigate(`/projects/${projectId}/characters`);
    });
  }, [projectId, charId]);

  const handleSave = async () => {
    if (!projectId || !charId) return;
    setSaving(true);
    try {
      const fullContent = serializeWithFrontmatter({ ...characterMeta, tags }, content);
      await charactersApi.update(projectId, charId, { name, summary, content: fullContent });
      message.success('保存成功');
    } catch {
      message.error('保存失败');
    }
    setSaving(false);
  };

  const handleRemoveTag = (tag: string) => {
    setTags(prev => prev.filter(t => t !== tag));
  };

  const handleAddTag = (e: React.KeyboardEvent<HTMLInputElement>) => {
    const input = e.currentTarget;
    if (input.value.trim()) {
      setTags(prev => [...prev, input.value.trim()]);
      input.value = '';
    }
  };

  if (loading || !character) {
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
          { title: <Link to={`/projects/${projectId}/characters`}>角色</Link> },
          { title: character.name },
        ]}
      />
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, marginBottom: 4 }}>
          <Input
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="角色名称"
            className="literati-title-input"
            style={{ flex: 1 }}
          />
          <Button onClick={() => navigate(`/projects/${projectId}/characters`)}>返回</Button>
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
          placeholder="添加小传..."
          className="literati-summary-input"
        />
        <div style={{ display: 'flex', gap: 6, marginTop: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          {tags.map(tag => (
            <Tag key={tag} className="seal-tag-bamboo" closable onClose={() => handleRemoveTag(tag)}>{tag}</Tag>
          ))}
          <Input
            placeholder="添加标签回车"
            size="small"
            style={{ width: 100, fontFamily: 'var(--font-display)' }}
            onPressEnter={handleAddTag}
          />
        </div>
      </div>

      <MarkdownEditor value={content} onChange={setContent} />
    </div>
    </PageContainer>
  );
};

export default CharacterEdit;
