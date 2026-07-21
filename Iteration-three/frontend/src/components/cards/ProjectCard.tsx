import { Card, Tag } from 'antd';
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

interface ProjectCardProps {
  project: Project;
  onClick: () => void;
}

const ProjectCard = ({ project, onClick }: ProjectCardProps) => {
  const palette = SILK_HEAD[project.name.length % SILK_HEAD.length];

  return (
    <Card
      hoverable
      onClick={onClick}
      style={{ overflow: 'hidden', borderRadius: 'var(--radius-md)' }}
      cover={
        <div
          style={{
            height: 80,
            background: `radial-gradient(ellipse at 30% 20%, ${palette.base} 0%, ${palette.deep} 90%)`,
            display: 'flex',
            alignItems: 'flex-end',
            padding: '12px 14px',
          }}
        >
          <span
            style={{
              color: 'var(--paper-base)',
              fontSize: 14,
              fontWeight: 600,
              fontFamily: 'var(--font-display)',
              letterSpacing: '0.04em',
            }}
          >
            {project.name}
          </span>
        </div>
      }
      styles={{ body: { padding: 14 } }}
    >
      <div
        style={{
          fontSize: 11,
          color: 'var(--ink-light)',
          marginBottom: 8,
          height: 36,
          overflow: 'hidden',
          fontFamily: 'var(--font-body)',
          lineHeight: 1.6,
        }}
      >
        {project.description || '暂无题记'}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Tag className="seal-tag">{project.word_count.toLocaleString()} 字</Tag>
        <span
          style={{
            fontSize: 10,
            color: 'var(--ink-light)',
            fontFamily: 'var(--font-display)',
            letterSpacing: '0.05em',
          }}
        >
          {formatDate(project.updated_at)}
        </span>
      </div>
    </Card>
  );
};

export default ProjectCard;
