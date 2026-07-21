import { useMemo, useState } from 'react';
import type { Project } from '@/types';
import ActivityHeatmap from './ActivityHeatmap';
import AIInsight from './AIInsight';

const WRITING_QUOTES = [
  { text: '读书破万卷，下笔如有神。', author: '杜甫' },
  { text: '文章千古事，得失寸心知。', author: '杜甫' },
  { text: '两句三年得，一吟双泪流。', author: '贾岛' },
  { text: '文章本天成，妙手偶得之。', author: '陆游' },
  { text: '操千曲而后晓声，观千剑而后识器。', author: '刘勰《文心雕龙》' },
  { text: '感人心者，莫先乎情。', author: '白居易' },
  { text: '博观而约取，厚积而薄发。', author: '苏轼' },
  { text: '盖文章，经国之大业，不朽之盛事。', author: '曹丕《典论·论文》' },
  { text: '看似寻常最奇崛，成如容易却艰辛。', author: '王安石' },
  { text: '其实地上本没有路，走的人多了，也便成了路。', author: '鲁迅' },
  { text: '究天人之际，通古今之变，成一家之言。', author: '司马迁' },
  { text: '一个人只拥有此生此世是不够的，他还应该拥有诗意的世界。', author: '王小波' },
];

interface LeftPanelProps {
  projects: Project[];
}

const cardBase: React.CSSProperties = {
  background: 'var(--paper-elevated)',
  borderRadius: 'var(--radius-lg)',
  padding: 14,
  borderWidth: 1,
  borderStyle: 'solid',
  borderColor: 'rgba(224, 213, 194, 0.35)',
  boxShadow: 'var(--shadow-sm)',
  transition: 'transform 0.2s ease, box-shadow 0.2s ease',
  cursor: 'default',
};

const cardHover: React.CSSProperties = {
  transform: 'translateY(-4px)',
  boxShadow: 'var(--shadow-md)',
};

const labelStyle: React.CSSProperties = {
  color: 'var(--ink-light)',
  fontSize: 11,
  marginBottom: 6,
  fontFamily: 'var(--font-display)',
  letterSpacing: '0.1em',
};

const numberStyle: React.CSSProperties = {
  color: 'var(--ink-heavy)',
  fontSize: 28,
  fontWeight: 700,
  lineHeight: 1,
  fontFamily: 'var(--font-display)',
};

const LeftPanel = ({ projects }: LeftPanelProps) => {
  const totalWords = projects.reduce((sum, p) => sum + p.word_count, 0);
  const activeCount = projects.filter((p) => p.status === 'active').length;
  const [hovered, setHovered] = useState<string | null>(null);

  const dailyQuote = useMemo(() => {
    const today = new Date();
    const dayIndex = today.getFullYear() * 366 + today.getMonth() * 31 + today.getDate();
    return WRITING_QUOTES[dayIndex % WRITING_QUOTES.length];
  }, []);

  const getCardStyle = (key: string, extra?: React.CSSProperties): React.CSSProperties => ({
    ...cardBase,
    ...(hovered === key ? cardHover : {}),
    ...extra,
  });

  return (
    <div
      style={{
        width: '35%',
        flexShrink: 0,
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 14,
        alignContent: 'start',
        overflowY: 'auto',
      }}
    >
      <div
        style={getCardStyle('heatmap', { gridColumn: '1 / 3' })}
        onMouseEnter={() => setHovered('heatmap')}
        onMouseLeave={() => setHovered(null)}
      >
        <ActivityHeatmap />
      </div>

      <div
        style={getCardStyle('projects')}
        onMouseEnter={() => setHovered('projects')}
        onMouseLeave={() => setHovered(null)}
      >
        <div style={labelStyle}>总卷宗</div>
        <div style={numberStyle}>{projects.length}</div>
      </div>

      <div
        style={getCardStyle('words')}
        onMouseEnter={() => setHovered('words')}
        onMouseLeave={() => setHovered(null)}
      >
        <div style={labelStyle}>总字数</div>
        <div style={numberStyle}>
          {totalWords >= 10000 ? `${(totalWords / 10000).toFixed(1)}` : totalWords.toLocaleString()}
          {totalWords >= 10000 && (
            <span
              style={{
                fontSize: 14,
                color: 'var(--ink-light)',
                fontWeight: 400,
                marginLeft: 4,
              }}
            >
              万
            </span>
          )}
        </div>
      </div>

      <div
        style={{
          ...getCardStyle('active', { gridColumn: '1 / 3' }),
          background:
            'linear-gradient(135deg, var(--vermilion-bg) 0%, var(--paper-elevated) 70%)',
        }}
        onMouseEnter={() => setHovered('active')}
        onMouseLeave={() => setHovered(null)}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <div style={labelStyle}>活跃卷宗</div>
            <div
              style={{
                ...numberStyle,
                color: 'var(--vermilion)',
              }}
            >
              {activeCount}
            </div>
          </div>
          <div
            className="seal-stamp"
            style={{
              width: 36,
              height: 36,
              fontSize: 18,
            }}
            title="活"
          >
            活
          </div>
        </div>
      </div>

      <div style={{ gridColumn: '1 / 3' }}>
        <AIInsight projects={projects} />
      </div>

      <div
        style={{
          ...getCardStyle('quote', { gridColumn: '1 / 3' }),
          borderLeft: '3px solid var(--vermilion)',
          paddingLeft: 18,
        }}
        onMouseEnter={() => setHovered('quote')}
        onMouseLeave={() => setHovered(null)}
      >
        <div style={{ ...labelStyle, marginBottom: 8, fontWeight: 700 }}>每日格言</div>
        <div
          style={{
            color: 'var(--ink-heavy)',
            fontSize: 14,
            lineHeight: 1.75,
            fontFamily: 'var(--font-body)',
          }}
        >
          <span
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 22,
              color: 'var(--vermilion)',
              marginRight: 2,
              verticalAlign: '-2px',
            }}
          >
            「
          </span>
          {dailyQuote.text}
          <span
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 22,
              color: 'var(--vermilion)',
              marginLeft: 2,
              verticalAlign: '-2px',
            }}
          >
            」
          </span>
        </div>
        <div
          style={{
            color: 'var(--ink-light)',
            fontSize: 12,
            marginTop: 8,
            textAlign: 'right',
            fontFamily: 'var(--font-display)',
            letterSpacing: '0.05em',
          }}
        >
          — {dailyQuote.author}
        </div>
      </div>
    </div>
  );
};

export default LeftPanel;
