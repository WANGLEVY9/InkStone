import { useState, useEffect } from 'react';
import { Button, Input, Tag, Spin, Breadcrumb } from 'antd';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAppMessage } from '@/hooks/useAppMessage';
import { chaptersApi } from '@/api/chapters';
import MarkdownEditor from '@/components/common/MarkdownEditor';
import { countWords } from '@/utils/format';
import type { Chapter } from '@/types';
import PageContainer from '@/components/common/PageContainer';

const ChapterEdit = () => {
  const { id: projectId, chapterId } = useParams<{ id: string; chapterId: string }>();
  const navigate = useNavigate();
  const { message } = useAppMessage();
  const [chapter, setChapter] = useState<Chapter | null>(null);
  const [title, setTitle] = useState('');
  const [summary, setSummary] = useState('');
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!projectId || !chapterId) return;
    chaptersApi.get(projectId, chapterId).then(res => {
      setChapter(res.data);
      setTitle(res.data.title);
      setSummary(res.data.summary || '');
      setContent(res.data.content || '');
      setLoading(false);
    }).catch(() => {
      message.error('加载失败');
      navigate(`/projects/${projectId}/chapters`);
    });
  }, [projectId, chapterId]);

  const handleSave = async () => {
    if (!projectId || !chapterId) return;
    setSaving(true);
    try {
      await chaptersApi.update(projectId, chapterId, {
        title,
        summary,
        content,
        word_count: countWords(content),
      });
      message.success('保存成功');
    } catch {
      message.error('保存失败');
    }
    setSaving(false);
  };

  if (loading || !chapter) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    );
  }

  const wordCount = countWords(content);

  return (
    <PageContainer>
    <div>
      <Breadcrumb
        style={{ marginBottom: 12, fontFamily: 'var(--font-display)', letterSpacing: '0.04em' }}
        items={[
          { title: <Link to={`/projects/${projectId}/chapters`}>章节</Link> },
          { title: chapter.title },
        ]}
      />
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, marginBottom: 4 }}>
          <Input
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="章节标题"
            className="literati-title-input"
            style={{ flex: 1 }}
          />
          <Button onClick={() => navigate(`/projects/${projectId}/chapters`)}>返回</Button>
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
          <Input
            value={summary}
            onChange={e => setSummary(e.target.value)}
            placeholder="添加题记..."
            className="literati-summary-input"
            style={{ flex: 1 }}
          />
          <Tag className="seal-tag">
            <span style={{ opacity: 0.7, marginRight: 2 }}>凡</span>
            {wordCount.toLocaleString()} 字
          </Tag>
        </div>
      </div>

      <MarkdownEditor value={content} onChange={setContent} />
    </div>
    </PageContainer>
  );
};

export default ChapterEdit;
