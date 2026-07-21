import { Card, Tag, Avatar } from 'antd';
import type { Character } from '@/types';
import { formatDate } from '@/utils/format';
import { parseCharacterMeta } from '@/utils/frontmatter';

const FAN_PALETTES: ReadonlyArray<{ base: string; wash: string }> = [
  { base: '#F5ECD7', wash: 'rgba(184, 146, 74, 0.20)' }, // 淡米黄
  { base: '#E0EBE6', wash: 'rgba(46, 90, 77, 0.18)' },   // 淡青
  { base: '#EBE2EE', wash: 'rgba(92, 74, 110, 0.18)' },  // 淡紫
  { base: '#F8E8E5', wash: 'rgba(200, 50, 61, 0.16)' },  // 淡粉
];

const hashStr = (s: string): number => {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h);
};

const getDisplayChar = (name: string): string => {
  const chars = [...name];
  if (chars.length === 0) return '？';
  const isAllChinese = chars.every(c => /[一-鿿]/.test(c));
  if (isAllChinese && chars.length > 1) {
    return chars[chars.length - 1];
  }
  return chars[0];
};

const getTypeSeal = (type: string): string | null => {
  if (!type) return null;
  if (/主|protag/i.test(type)) return '主';
  if (/配|support/i.test(type)) return '配';
  if (/反|antag|敌/i.test(type)) return '反';
  if (/客|串/i.test(type)) return '客';
  return [...type][0];
};

interface CharacterCardProps {
  character: Character;
  onClick: () => void;
}

const CharacterCard = ({ character, onClick }: CharacterCardProps) => {
  const palette = FAN_PALETTES[hashStr(character.name) % FAN_PALETTES.length];
  const meta = character.content ? parseCharacterMeta(character.content) : null;
  const seal = meta?.type ? getTypeSeal(meta.type) : null;
  const displayChar = getDisplayChar(character.name);

  return (
    <Card
      hoverable
      onClick={onClick}
      style={{ borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}
      styles={{ body: { padding: 0 } }}
    >
      <div
        style={{
          height: 180,
          position: 'relative',
          background: `
            radial-gradient(ellipse at 75% 25%, ${palette.wash} 0%, transparent 55%),
            linear-gradient(160deg, ${palette.base} 0%, var(--paper-elevated) 100%)
          `,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Avatar
          size={72}
          style={{
            backgroundColor: 'var(--ink-heavy)',
            color: 'var(--paper-base)',
            fontFamily: 'var(--font-display)',
            fontSize: 28,
            fontWeight: 600,
            letterSpacing: 0,
            boxShadow: '0 2px 6px rgba(31, 26, 23, 0.25)',
          }}
        >
          {displayChar}
        </Avatar>
        {seal && (
          <div
            className="seal-stamp"
            style={{
              position: 'absolute',
              top: 12,
              right: 12,
              width: 24,
              height: 24,
              fontSize: 13,
            }}
            title={meta?.type}
          >
            {seal}
          </div>
        )}
      </div>
      <div style={{ padding: 14 }}>
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
          {character.name}
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
          {character.summary || '暂无小传'}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
          <div style={{ display: 'flex', gap: 4, flex: 1, overflow: 'hidden' }}>
            {meta?.tags?.slice(0, 2).map(tag => (
              <Tag key={tag} className="seal-tag-bamboo">{tag}</Tag>
            ))}
          </div>
          <span
            style={{
              fontSize: 10,
              color: 'var(--ink-light)',
              fontFamily: 'var(--font-display)',
              letterSpacing: '0.05em',
              flexShrink: 0,
            }}
          >
            {formatDate(character.updated_at)}
          </span>
        </div>
      </div>
    </Card>
  );
};

export default CharacterCard;
