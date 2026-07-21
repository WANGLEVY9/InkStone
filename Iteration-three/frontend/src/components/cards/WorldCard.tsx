import { useState } from 'react';
import { Card } from 'antd';
import type { WorldSetting } from '@/types';
import { formatDate } from '@/utils/format';

interface WorldCardProps {
  world: WorldSetting;
  onClick: () => void;
}

const WorldCard = ({ world, onClick }: WorldCardProps) => {
  const [hovered, setHovered] = useState(false);

  return (
    <Card
      hoverable
      onClick={onClick}
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
        卷
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
        {world.name}
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
        {world.summary || '暂无题记'}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
        <span
          style={{
            fontSize: 10,
            color: 'var(--ink-light)',
            fontFamily: 'var(--font-display)',
            letterSpacing: '0.05em',
          }}
        >
          {formatDate(world.updated_at)}
        </span>
      </div>

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
        阅
      </div>
    </Card>
  );
};

export default WorldCard;
