import { Tag } from 'antd';
import { useNavigate } from 'react-router-dom';
import type { Project } from '@/types';
import { formatDate } from '@/utils/format';

const SILK_HEAD: ReadonlyArray<{ base: string; deep: string }> = [
  { base: '#D4B96E', deep: '#B89A4E' },
  { base: '#5A6D7A', deep: '#3F4F5C' },
  { base: '#7A5C46', deep: '#5C3F2E' },
  { base: '#5C4A6E', deep: '#3F2D52' },
  { base: '#4A6657', deep: '#2A4537' },
  { base: '#8A4A3D', deep: '#5C2E22' },
];

const hashStr = (s: string): number => {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h);
};

interface ListViewProps {
  projects: Project[];
  onTogglePin: (projectId: string) => void;
}

const ListView = ({ projects, onTogglePin }: ListViewProps) => {
  const navigate = useNavigate();

  return (
    <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
      {projects.map((project) => {
        const palette = SILK_HEAD[hashStr(project.id) % SILK_HEAD.length];
        return (
          <div
            key={project.id}
            onClick={() => navigate(`/projects/${project.id}/world`)}
            style={{
              display: 'flex',
              alignItems: 'center',
              cursor: 'pointer',
              padding: '12px 16px',
              borderBottom: '1px solid var(--silk-line)',
              transition: 'background 0.15s ease',
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLDivElement).style.background = 'var(--paper-sunken)';
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLDivElement).style.background = 'transparent';
            }}
          >
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: 'var(--radius-sm)',
                background: `radial-gradient(ellipse at 30% 20%, ${palette.base} 0%, ${palette.deep} 90%)`,
                flexShrink: 0,
                marginRight: 12,
                boxShadow: 'inset 0 0 0 1px rgba(0, 0, 0, 0.10)',
              }}
            />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  fontFamily: 'var(--font-display)',
                  fontWeight: 600,
                  color: 'var(--ink-heavy)',
                  letterSpacing: '0.04em',
                  fontSize: 14,
                  marginBottom: 2,
                }}
              >
                {project.name}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Tag className="seal-tag" style={{ fontSize: 10 }}>
                  {project.word_count.toLocaleString()} 字
                </Tag>
                <span
                  style={{
                    color: 'var(--ink-light)',
                    fontSize: 11,
                    fontFamily: 'var(--font-display)',
                    letterSpacing: '0.05em',
                  }}
                >
                  {formatDate(project.updated_at)}
                </span>
              </div>
            </div>
            {project.is_pinned && (
              <div
                className="seal-stamp"
                style={{
                  width: 22,
                  height: 22,
                  fontSize: 11,
                  flexShrink: 0,
                  marginLeft: 8,
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  onTogglePin(project.id);
                }}
                title="已收藏 · 点击取消"
              >
                藏
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default ListView;
