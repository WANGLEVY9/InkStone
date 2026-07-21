import { useMemo, useState } from 'react';
import type { Project } from '@/types';

interface AIInsightProps {
  projects: Project[];
}

const generateInsight = (projects: Project[]): string => {
  const active = projects.filter((p) => p.status === 'active');
  if (active.length === 0) return '尚无活跃卷宗，新立一卷以启文思。';
  if (active.length === 1) return `仅《${active[0].name}》一卷在手，宜专心推之。`;

  const now = Date.now();
  const DAY = 86400000;

  const sorted = [...active].sort(
    (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  );
  const freshest = sorted[0];
  const stalest = sorted[sorted.length - 1];
  const staleDays = Math.floor((now - new Date(stalest.updated_at).getTime()) / DAY);

  const wordLeader = [...active].sort((a, b) => b.word_count - a.word_count)[0];

  if (staleDays >= 3 && active.length >= 2) {
    return `《${stalest.name}》已搁笔 ${staleDays} 日，而《${freshest.name}》文思正盛——今日宜先续后者。`;
  }

  if (wordLeader.word_count > 0 && active.length >= 2) {
    const second = sorted.find((p) => p.id !== wordLeader.id);
    if (second && wordLeader.word_count > second.word_count * 2) {
      return `《${wordLeader.name}》已逾 ${(wordLeader.word_count / 10000).toFixed(1)} 万字，远超他卷。可分笔润《${second.name}》。`;
    }
  }

  if (freshest.word_count < 1000) {
    return `《${freshest.name}》初成卷轴，趁兴多书几行。`;
  }

  return `${active.length} 卷并行，《${freshest.name}》近时着墨最勤，节奏可继。`;
};

const AIInsight = ({ projects }: AIInsightProps) => {
  const insight = useMemo(() => generateInsight(projects), [projects]);
  const [hovered, setHovered] = useState(false);

  return (
    <div
      style={{
        background:
          'linear-gradient(135deg, var(--vermilion-bg) 0%, var(--paper-elevated) 70%)',
        borderRadius: 'var(--radius-lg)',
        padding: 16,
        border: `1px solid ${hovered ? 'var(--vermilion)' : 'var(--silk-line-strong)'}`,
        boxShadow: hovered ? 'var(--shadow-md)' : 'var(--shadow-sm)',
        transform: hovered ? 'translateY(-2px)' : 'none',
        transition: 'transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease',
        cursor: 'default',
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span
          className="seal-stamp"
          style={{
            width: 22,
            height: 22,
            fontSize: 12,
          }}
        >
          签
        </span>
        <span
          style={{
            color: 'var(--vermilion)',
            fontSize: 12,
            fontWeight: 700,
            fontFamily: 'var(--font-display)',
            letterSpacing: '0.1em',
          }}
        >
          砚台批语
        </span>
      </div>
      <div
        style={{
          color: 'var(--ink-heavy)',
          fontSize: 13,
          lineHeight: 1.85,
          fontFamily: 'var(--font-body)',
        }}
      >
        {insight}
      </div>
    </div>
  );
};

export default AIInsight;
